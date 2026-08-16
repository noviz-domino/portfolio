# -*- coding: utf-8 -*-
"""ReplyGate 지표 대시보드 + 실시간 상황판.

읽기 전용이다. 이 서버는 구글 시트를 읽기만 하고 n8n 과 직접 통신하지 않는다.
그래서 공개 URL(ngrok 등)이 필요 없고, 이 서버가 죽어도 파이프라인은 그대로 돈다.

실행:
    set REPLYGATE_SHEET_ID=<스프레드시트 ID>
    set REPLYGATE_SA_KEY=<서비스계정 키 json 경로>
    python dashboard/app.py
"""

import asyncio
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from fastapi import FastAPI                                  # noqa: E402
from fastapi.responses import (FileResponse, JSONResponse,   # noqa: E402
                               StreamingResponse)
from fastapi.staticfiles import StaticFiles                  # noqa: E402

import metrics                                               # noqa: E402
from sheets import ConfigError, Poller, SheetSource, now_kst  # noqa: E402

STATIC = os.path.join(HERE, "static")
POLL_SECONDS = float(os.environ.get("REPLYGATE_POLL_SECONDS", "2"))
PUSH_SECONDS = float(os.environ.get("REPLYGATE_PUSH_SECONDS", "1"))
HEARTBEAT_SECONDS = 15.0

state = {"source": None, "poller": None, "config_error": None}


def _startup():
    # 데모 모드: 서비스 계정 키도 네트워크도 없이 화면을 띄운다. 리허설용.
    if os.environ.get("REPLYGATE_DEMO", "").strip() in ("1", "true", "TRUE", "yes"):
        from demo_data import DemoSource
        state["source"] = DemoSource()
        print("[demo mode] 가짜 데이터로 실행합니다. 실제 시트를 읽지 않습니다.")
        return

    try:
        src = SheetSource()
    except ConfigError as e:
        # 설정이 없어도 서버는 뜬다. 화면에 무엇이 빠졌는지 띄우는 편이
        # 콘솔 트레이스백보다 낫다.
        state["config_error"] = str(e)
        return
    state["source"] = src
    state["poller"] = Poller(src, interval=POLL_SECONDS)
    state["poller"].start()


def _shutdown():
    if state["poller"]:
        state["poller"].stop()


app = FastAPI(title="ReplyGate Dashboard", docs_url=None, redoc_url=None,
              on_startup=[_startup], on_shutdown=[_shutdown])


# ------------------------------------------------------------------ 페이로드
def _source_status():
    if state["config_error"]:
        return {"ok": False, "config_error": state["config_error"],
                "last_ok_at": None, "stale_seconds": None, "error": None}
    _, last_ok, err = state["source"].snapshot()
    stale = int((now_kst() - last_ok).total_seconds()) if last_ok else None
    return {
        "ok": err is None and last_ok is not None,
        "config_error": None,
        "last_ok_at": last_ok.isoformat() if last_ok else None,
        "stale_seconds": stale,
        "error": err,
    }


def _payload():
    """화면 한 장을 그리는 데 필요한 전부."""
    if state["config_error"]:
        rows = []
    else:
        rows, _, _ = state["source"].snapshot()
    return {
        "operational": metrics.operational(rows),
        "board": metrics.board(rows),
        "experiment": metrics.experiment(),
        "source": _source_status(),
        "served_at": now_kst().isoformat(),
    }


# ------------------------------------------------------------------ 라우트
@app.get("/api/metrics")
def api_metrics():
    p = _payload()
    return JSONResponse({"operational": p["operational"],
                         "experiment": p["experiment"],
                         "source": p["source"]})


@app.get("/api/board")
def api_board():
    p = _payload()
    return JSONResponse({"board": p["board"], "source": p["source"]})


@app.get("/api/clauses")
def api_clauses():
    """근거 조항 원문 70개. 스냅샷마다 실어보내기엔 크고 거의 바뀌지 않아
    별도 엔드포인트로 두고 브라우저가 한 번만 받아 캐시한다."""
    if state["config_error"] or not state["source"]:
        return JSONResponse({"clauses": {}})
    return JSONResponse({"clauses": state["source"].clauses()})


@app.get("/api/health")
def api_health():
    return JSONResponse(_source_status())


def _change_key(p):
    """변경 감지용 지문. **시간에 따라 저절로 변하는 값은 뺀다.**

    이걸 빼지 않으면 `served_at`(현재 시각)과 `age_seconds`(경과 초) 때문에
    지문이 매초 달라져 "바뀔 때만 보낸다"가 무력화된다. 실제로 그렇게 만들었다가
    초당 한 번씩 전송돼 화면이 깜박였다. 경과 시간 표시는 브라우저가
    `moved_at`(절대 시각)으로 직접 계산한다.
    """
    q = {
        "operational": p["operational"],
        "experiment": p["experiment"],
        "board": [{k: v for k, v in c.items() if k != "age_seconds"} for c in p["board"]],
        "source": {k: v for k, v in p["source"].items()
                   if k not in ("stale_seconds", "last_ok_at")},
    }
    return json.dumps(q, ensure_ascii=False, sort_keys=True, default=str)


@app.get("/api/stream")
async def api_stream():
    """SSE. 내용이 바뀔 때만 밀어준다.

    폴링은 백그라운드 스레드 한 곳에서만 한다. 연결마다 시트를 읽으면
    탭을 두 개 여는 것만으로 API 호출이 배가 된다.
    """
    async def gen():
        last_hash = None
        idle = 0.0
        # 연결 직후 한 번은 무조건 보낸다.
        while True:
            payload = _payload()
            body = json.dumps(payload, ensure_ascii=False, default=str)
            digest = hashlib.md5(_change_key(payload).encode("utf-8")).hexdigest()
            if digest != last_hash:
                last_hash = digest
                idle = 0.0
                yield "event: snapshot\ndata: {}\n\n".format(body)
            else:
                idle += PUSH_SECONDS
                if idle >= HEARTBEAT_SECONDS:
                    idle = 0.0
                    yield ": keep-alive\n\n"       # 프록시가 연결을 끊지 않게
            await asyncio.sleep(PUSH_SECONDS)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                 "Connection": "keep-alive"},
    )


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("REPLYGATE_PORT", "8000"))
    print("ReplyGate dashboard -> http://127.0.0.1:{}".format(port))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
