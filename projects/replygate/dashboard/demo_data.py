# -*- coding: utf-8 -*-
"""데모 모드용 가짜 `문의` 시트 데이터.

용도는 두 가지다.

1. **리허설** — 서비스 계정 키나 네트워크 없이 화면을 띄워 발표 동선을 연습한다.
2. **화면 검증** — 상태·배지 조합을 모두 깔아두어 UI가 깨지지 않는지 본다.

`REPLYGATE_DEMO=1` 일 때만 쓰인다. 실제 운영 경로에는 영향이 없다.
"""

import io
import os
from datetime import timedelta

from sheets import now_kst

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 시트 헤더와 같은 키를 쓴다. 실제 경로와 같은 코드를 타야 검증이 의미가 있다.
_SPEC = [
    # (분전, 이름, category, sentiment, needs_lookup, summary, cited, insuf, status, revisions)
    (0,   "이서준", "",           "",     False, "",                              "",                "FALSE", "접수됨",   0),
    (1,   "박지훈", "배송",       "일반", True,  "주문 상품 배송 현황 문의",       "",                "FALSE", "분석중",   0),
    (3,   "김민석", "환불",       "불만", True,  "반품 후 환불 지연 문의",         "RF-09,RF-02,RF-13", "FALSE", "승인대기", 0),
    (6,   "최유나", "회원적립금", "일반", False, "적립금 사용 조건 문의",          "MB-06",           "FALSE", "승인대기", 0),
    (9,   "정하람", "기타",       "불만", True,  "정기구독 해지 위약금 관련 불만", "",                "TRUE",  "승인대기", 0),
    (12,  "오세훈", "불량AS",     "불만", False, "동일 제품 반복 고장 환불 요구",  "AS-09,EX-12",     "FALSE", "수정중",   2),
    (18,  "한지우", "교환반품",   "일반", True,  "사이즈 교환 기한과 배송비 문의", "EX-01,EX-03",     "FALSE", "발송완료", 0),
    (31,  "윤가온", "배송",       "일반", False, "도서산간 추가 배송비 문의",      "DL-03",           "FALSE", "발송완료", 0),
    (47,  "서도윤", "환불",       "일반", False, "무통장 입금 환불 계좌 문의",     "RF-03",           "FALSE", "발송완료", 1),
    (64,  "강예린", "불량AS",     "일반", True,  "전자제품 보증 기간 문의",        "AS-05,AS-07,AS-06", "FALSE", "발송완료", 0),
    (88,  "노아인", "회원적립금", "일반", False, "리뷰 작성 적립금 문의",          "MB-10",           "FALSE", "발송완료", 0),
    (120, "임하늘", "기타",       "일반", False, "개인정보 열람·삭제 절차 문의",   "PI-04,PI-05",     "FALSE", "발송완료", 0),
]


def rows():
    now = now_kst()
    out = []
    for i, (mins, name, cat, sen, lookup, summary, cited, insuf, status, rev) in enumerate(_SPEC, 1):
        moved = now - timedelta(minutes=mins)
        # 접수 시각은 상태 진입보다 조금 앞선다. 발송 건일수록 간격이 크다.
        received = moved - timedelta(minutes=(4 if status == "발송완료" else 1))
        out.append({
            "타임스탬프": received.isoformat(),
            "이름": name,
            "이메일": "demo{}@example.com".format(i),
            "주문번호": "",
            "문의내용": summary or "문의 내용",
            "개인정보 수집 동의": "동의합니다",
            "inquiry_id": "INQ-DEMO-{:03d}".format(i),
            "category": cat,
            "sentiment": sen,
            "needs_lookup": "TRUE" if lookup else "FALSE",
            "summary": summary,
            "search_query": summary,
            "cited_clauses": cited,
            "insufficient_info": insuf,
            "draft_id": "r{}".format(1000 + i),
            "revision_count": str(rev),
            "status": status,
            "status_at": moved.isoformat(),
            "sent_at": moved.isoformat() if status == "발송완료" else "",
            "final_body": "",
            "handler_note": "",
        })
    return out


def _parse_policy_md():
    """데모 모드의 조항 원문은 `data/정책문서.md` 에서 읽는다.

    시트를 못 읽는 상태에서도 상세 화면의 "근거 조항 원문"을 그대로 보여줄 수 있다.
    조항 시트는 애초에 이 문서를 옮겨 담은 것이라 내용이 같다.
    """
    path = os.path.join(ROOT, "data", "정책문서.md")
    if not os.path.exists(path):
        return {}

    out, doc, cid, title, buf = {}, "", None, "", []

    def flush():
        if cid:
            out[cid] = {"doc": doc, "title": title,
                        "text": " ".join(buf).strip()}

    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("## 부록"):
                break
            if line.startswith("# "):                       # 문서 구분: "# 1. 환불 정책 (RF)"
                flush(); cid, buf = None, []
                doc = line[2:].strip()
                if ". " in doc:
                    doc = doc.split(". ", 1)[1]
                doc = doc.split(" (")[0].strip()
            elif line.startswith("### "):                   # 조항: "### RF-01 · 환불 신청 기한"
                flush(); buf = []
                head = line[4:].strip()
                cid, title = (head.split("·", 1) + [""])[:2] if "·" in head else (head, "")
                cid, title = cid.strip(), title.strip()
            elif cid and line.strip() and not line.startswith(">"):
                buf.append(line.lstrip("- ").replace("**", "").strip())
    flush()
    return out


class DemoSource:
    """SheetSource 와 같은 인터페이스. app.py 가 구분 없이 쓸 수 있다."""

    def __init__(self):
        self.last_error = None
        self.fetch_count = 0
        self._clauses = None

    def refresh(self):
        self.fetch_count += 1
        return True

    def snapshot(self):
        return rows(), now_kst(), None

    def clauses(self):
        if self._clauses is None:
            self._clauses = _parse_policy_md()
        return self._clauses
