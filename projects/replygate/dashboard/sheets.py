# -*- coding: utf-8 -*-
"""구글 시트 읽기 전용 어댑터.

설계 원칙 두 가지.

1. **n8n과 직접 통신하지 않는다.** 시트를 공용 저장소로 두고 여기서는 읽기만 한다.
   덕분에 ngrok 같은 공개 URL이 필요 없고, 대시보드가 죽어도 파이프라인은 돌아간다.
2. **마지막 성공 응답을 계속 들고 있는다.** 조회가 실패해도 화면이 비지 않는다.
   발표 도중 네트워크가 한 번 끊겨도 직전 값으로 계속 그린다.
"""

import os
import threading
import time
from datetime import datetime, timezone, timedelta

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleAuthRequest

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
API = "https://sheets.googleapis.com/v4/spreadsheets"
KST = timezone(timedelta(hours=9))

# 시트에서 읽어올 범위. 문의 시트는 U열(needs_lookup)까지 열어둔다.
# 컬럼이 없어도 헤더 기준으로 매핑하므로 빈 값으로 처리된다.
INQUIRY_RANGE = "문의!A:U"

# 조항은 워크플로우 00 이 한 번 적재하면 바뀌지 않는다. 매번 읽을 이유가 없다.
CLAUSE_RANGE = "조항!A:D"
CLAUSE_TTL_SECONDS = 600


class ConfigError(RuntimeError):
    pass


def _env(name, required=True):
    v = os.environ.get(name, "").strip()
    if required and not v:
        raise ConfigError(
            "환경변수 {}이(가) 없습니다. dashboard/README.md 의 준비 절차를 확인하세요.".format(name)
        )
    return v


class SheetSource:
    """서비스 계정으로 시트를 읽고 결과를 메모리에 캐시한다."""

    def __init__(self, spreadsheet_id=None, key_path=None):
        self.spreadsheet_id = spreadsheet_id or _env("REPLYGATE_SHEET_ID")
        self.key_path = key_path or _env("REPLYGATE_SA_KEY")
        if not os.path.exists(self.key_path):
            raise ConfigError("서비스 계정 키 파일을 찾을 수 없습니다: {}".format(self.key_path))

        self._creds = service_account.Credentials.from_service_account_file(
            self.key_path, scopes=SCOPES
        )
        self._lock = threading.Lock()

        # 캐시. 조회에 실패해도 이 값으로 계속 응답한다.
        self.rows = []
        self.last_ok_at = None      # 마지막으로 시트를 실제로 읽은 시각
        self.last_error = None      # 마지막 실패 사유 (성공하면 None)
        self.fetch_count = 0

        self._clauses = {}          # clause_id -> {doc, title, text}
        self._clauses_at = None

    # ------------------------------------------------------------------ 인증
    def _token(self):
        if not self._creds.valid:
            self._creds.refresh(GoogleAuthRequest())
        return self._creds.token

    @property
    def service_account_email(self):
        return getattr(self._creds, "service_account_email", "")

    # ------------------------------------------------------------------ 조회
    def _get_values(self, rng):
        url = "{}/{}/values/{}".format(API, self.spreadsheet_id, requests.utils.quote(rng, safe=""))
        r = requests.get(
            url,
            headers={"Authorization": "Bearer {}".format(self._token())},
            params={"valueRenderOption": "UNFORMATTED_VALUE",
                    "dateTimeRenderOption": "FORMATTED_STRING"},
            timeout=10,
        )
        if r.status_code == 403:
            raise RuntimeError(
                "시트 접근이 거부됐습니다(403). 스프레드시트를 서비스 계정 {} 에 "
                "뷰어로 공유했는지 확인하세요.".format(self.service_account_email)
            )
        if r.status_code == 404:
            raise RuntimeError("스프레드시트를 찾을 수 없습니다(404). REPLYGATE_SHEET_ID 를 확인하세요.")
        r.raise_for_status()
        return r.json().get("values", [])

    def refresh(self):
        """시트를 한 번 읽어 캐시를 갱신한다. 실패해도 예외를 밖으로 던지지 않는다."""
        try:
            values = self._get_values(INQUIRY_RANGE)
            rows = _to_dicts(values)
            with self._lock:
                self.rows = rows
                self.last_ok_at = datetime.now(KST)
                self.last_error = None
                self.fetch_count += 1
            return True
        except Exception as e:                      # noqa: BLE001 - 화면을 살리는 것이 우선
            with self._lock:
                self.last_error = str(e)
            return False

    def snapshot(self):
        with self._lock:
            return list(self.rows), self.last_ok_at, self.last_error

    # ------------------------------------------------------------------ 조항
    def clauses(self):
        """근거 조항 원문. 담당자가 인용을 검증하려면 이게 있어야 한다.

        조항은 워크플로우 00 이 한 번 적재하면 바뀌지 않으므로 길게 캐시한다.
        실패하면 마지막 성공분을 그대로 돌려준다 — 여기서 예외를 던지면
        상세 화면 전체가 열리지 않는다.
        """
        with self._lock:
            fresh = (self._clauses_at is not None
                     and (now_kst() - self._clauses_at).total_seconds() < CLAUSE_TTL_SECONDS)
            if self._clauses and fresh:
                return dict(self._clauses)

        try:
            values = self._get_values(CLAUSE_RANGE)
            out = {}
            for row in _to_dicts(values):
                cid = (row.get("clause_id") or "").strip()
                if cid:
                    out[cid] = {"doc": row.get("doc", ""),
                                "title": row.get("title", ""),
                                "text": row.get("text", "")}
            if out:
                with self._lock:
                    self._clauses = out
                    self._clauses_at = now_kst()
        except Exception:                            # noqa: BLE001
            pass

        with self._lock:
            return dict(self._clauses)


def _to_dicts(values):
    """시트 2차원 배열을 헤더 기준 dict 목록으로 바꾼다.

    헤더에 없는 컬럼(needs_lookup 등)은 그냥 빠진다. 행 길이가 헤더보다 짧아도
    빈 문자열로 채워 KeyError 가 나지 않게 한다.
    """
    if not values:
        return []
    header = [str(h).strip() for h in values[0]]
    out = []
    for raw in values[1:]:
        if not any(str(c).strip() for c in raw):
            continue                                # 완전히 빈 행은 건너뛴다
        row = {}
        for i, key in enumerate(header):
            if not key:
                continue
            row[key] = str(raw[i]).strip() if i < len(raw) else ""
        out.append(row)
    return out


# ---------------------------------------------------------------- 시각 파싱
def parse_ts(s):
    """시트에 섞여 들어오는 여러 시각 표기를 datetime 으로 바꾼다.

    - n8n 이 쓴 값: `2026-08-01T12:34:56.789Z` (ISO, UTC)
    - 구글 폼이 쓴 값: `2026. 8. 1 오후 3:24:10` (한국어 로케일)
    파싱에 실패하면 None 을 돌려주고, 호출부에서 평균 계산에서 제외한다.
    """
    if not s:
        return None
    s = str(s).strip()
    if not s:
        return None

    # ISO 8601
    try:
        iso = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        return dt.astimezone(KST)
    except ValueError:
        pass

    # 구글 폼 한국어 로케일: "2026. 8. 1 오후 3:24:10"
    try:
        txt = s.replace(".", " ")
        parts = txt.split()
        y, mo, d = int(parts[0]), int(parts[1]), int(parts[2])
        ampm, clock = "", ""
        for p in parts[3:]:
            if p in ("오전", "오후", "AM", "PM"):
                ampm = p
            elif ":" in p:
                clock = p
        hh, mm, ss = (list(map(int, clock.split(":"))) + [0, 0])[:3] if clock else (0, 0, 0)
        if ampm in ("오후", "PM") and hh < 12:
            hh += 12
        if ampm in ("오전", "AM") and hh == 12:
            hh = 0
        return datetime(y, mo, d, hh, mm, ss, tzinfo=KST)
    except (ValueError, IndexError):
        return None


def now_kst():
    return datetime.now(KST)


class Poller:
    """백그라운드에서 주기적으로 시트를 읽는다.

    SSE 연결마다 시트를 읽으면 탭을 두 개만 열어도 API 호출이 배로 늘어난다.
    폴링은 여기 한 곳에서만 하고, 모든 응답은 캐시를 본다.
    """

    def __init__(self, source, interval=2.0):
        self.source = source
        self.interval = interval
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread:
            return
        self.source.refresh()                       # 첫 화면을 위해 한 번은 동기로 읽는다
        self._thread = threading.Thread(target=self._loop, daemon=True, name="sheet-poller")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _loop(self):
        while not self._stop.wait(self.interval):
            self.source.refresh()
