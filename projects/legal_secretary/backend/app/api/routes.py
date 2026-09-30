"""엔드포인트 정의."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import AskRequest, AskResponse, HealthResponse
from app.config import Settings, get_settings
from app.services import RagNotReadyError, answer_question, stream_answer

router = APIRouter()

SettingsDep = Annotated[Settings, Depends(get_settings)]


def _format_sse(event: str, data: dict) -> str:
    """표준 SSE 프레임(`event: ...\\ndata: ...\\n\\n`)을 만든다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/health", response_model=HealthResponse)
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(status="ok", backend=settings.llm_backend)


@router.post("/api/ask", response_model=AskResponse)
async def ask(request: AskRequest, settings: SettingsDep) -> AskResponse:
    try:
        return await answer_question(request.question, settings)
    except RagNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/ask/stream")
async def ask_stream(request: AskRequest, settings: SettingsDep) -> StreamingResponse:
    """SSE로 답변을 스트리밍한다.

    이벤트 순서: status(retrieving) -> citations -> status(generating) -> token* -> done.
    실패 시(벡터스토어 비어있음, 타임아웃 등)는 `error` 이벤트를 보내고
    스트림을 정상 종료한다(HTTP 예외로 연결을 끊지 않는다).
    """

    async def event_stream():
        async for event, data in stream_answer(request.question, settings):
            yield _format_sse(event, data)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
