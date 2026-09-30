"""라우트에서 분리한 서비스 로직.

02단계: 하이브리드 검색 -> (선택) 리랭킹 -> 컨텍스트 구성 -> LLM 호출 ->
답변 + 인용을 반환한다.
03단계: 검색/컨텍스트 구성 로직을 `_retrieve` 로 공유하고, `/api/ask/stream`을
위한 `stream_answer` 제너레이터를 추가했다. `answer_question`(비스트리밍)과
동일한 검색 경로를 쓰므로 두 엔드포인트의 인용·컨텍스트는 항상 일치한다.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from app.api.schemas import AskResponse, Citation
from app.config import Settings
from app.llm.factory import build_chat_model
from app.rag.rerank import rerank
from app.rag.retrieval import RetrievedChunk, get_retriever

_PROMPT_PATH = Path(__file__).parent / "prompts" / "legal_qa.txt"

# 인용 스니펫 길이. 너무 길면 응답이 비대해지므로 앞부분만 잘라 보여준다.
_SNIPPET_LENGTH = 200

# 스트리밍 이벤트: (event_name, data) 튜플.
StreamEvent = tuple[str, dict[str, Any]]


class RagNotReadyError(RuntimeError):
    """벡터스토어가 비어 있어(인제스트 전) 검색을 수행할 수 없을 때."""


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_context(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        article_part = f" {chunk.article}" if chunk.article else ""
        parts.append(
            f"[{i}]{article_part} ({chunk.source} p.{chunk.page})\n{chunk.text}"
        )
    return "\n\n".join(parts)


def _to_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            source=chunk.source,
            page=chunk.page,
            article=chunk.article,
            snippet=chunk.text[:_SNIPPET_LENGTH],
        )
        for chunk in chunks
    ]


def _retrieve(question: str, settings: Settings) -> list[RetrievedChunk]:
    """`/api/ask`와 `/api/ask/stream`이 공유하는 검색 단계.

    벡터스토어가 비어 있으면 `RagNotReadyError`를 던진다. 호출부(스트리밍
    라우트)는 이를 잡아 `error` 이벤트로 변환해야 하며, 그대로 흘려보내
    예외로 연결을 끊으면 안 된다.
    """
    retriever = get_retriever()
    if retriever.is_empty():
        raise RagNotReadyError(
            "벡터스토어가 비어 있습니다. "
            "`uv run python -m app.rag.ingest` 를 먼저 실행하세요."
        )

    chunks = retriever.retrieve(question, top_k=settings.retrieval_k)
    return rerank(question, chunks, settings)


async def answer_question(question: str, settings: Settings) -> AskResponse:
    """질의 -> 하이브리드 검색 -> (선택)리랭킹 -> LLM 호출 -> 답변+인용."""
    chunks = _retrieve(question, settings)

    prompt = _load_prompt_template().format(
        context=_build_context(chunks), question=question
    )

    chat_model = build_chat_model(settings)
    result = await chat_model.ainvoke(prompt)

    # content는 백엔드에 따라 문자열이거나 구조화된 블록 리스트다(Gemini는 후자).
    # str(content)를 쓰면 리스트 repr이 그대로 나가고 서명 등 내부 필드까지
    # 노출되므로, 텍스트만 뽑아주는 .text 프로퍼티를 쓴다.
    return AskResponse(
        answer=result.text,
        citations=_to_citations(chunks),
        backend=settings.llm_backend,
    )


async def stream_answer(question: str, settings: Settings) -> AsyncIterator[StreamEvent]:
    """SSE용 이벤트 제너레이터.

    순서: status(retrieving) -> citations -> status(generating) -> token* -> done.
    검색이 끝나기 전(0~2초 구간)에도 클라이언트가 진행 상태를 표시할 수 있도록,
    스트림을 열자마자 `status: retrieving`을 가장 먼저 보낸다.
    실패 시(벡터스토어 비어있음, 타임아웃, 기타 예외) `error` 이벤트를 내보내고
    정상적으로 제너레이터를 종료한다. 예외를 밖으로 던지지 않는다 —
    그러면 SSE 연결이 그냥 끊겨 클라이언트가 원인을 알 수 없다.
    """
    start = time.monotonic()

    yield ("status", {"state": "retrieving"})

    try:
        # 검색은 임베딩 추론을 포함해 1초 이상 걸리는 동기 작업이다. 이벤트 루프에서
        # 그대로 실행하면 바로 위에서 yield한 retrieving 이벤트조차 소켓으로
        # 나가지 못한 채 붙잡힌다(실측: 첫 이벤트가 2.2초에 도착). 별도 스레드로
        # 넘겨 루프가 즉시 flush할 수 있게 한다.
        chunks = await asyncio.to_thread(_retrieve, question, settings)
    except RagNotReadyError as exc:
        yield ("error", {"message": str(exc), "retryable": True})
        return
    except Exception as exc:  # noqa: BLE001 - 스트림은 예외를 error 이벤트로 흡수해야 함
        yield ("error", {"message": f"검색 중 오류가 발생했습니다: {exc}", "retryable": True})
        return

    citations = [c.model_dump() for c in _to_citations(chunks)]
    yield ("citations", {"citations": citations})
    yield ("status", {"state": "generating"})

    prompt = _load_prompt_template().format(
        context=_build_context(chunks), question=question
    )

    try:
        chat_model = build_chat_model(settings)
        agen = chat_model.astream(prompt).__aiter__()

        # 하트비트에 asyncio.wait_for를 쓰면 안 된다. 타임아웃 시 대기 중인
        # __anext__() 코루틴을 취소해버리는데, 그러면 비동기 제너레이터가 망가져
        # 다음 호출에서 곧바로 StopAsyncIteration이 난다. 첫 토큰이 하트비트
        # 간격보다 늦게 오는 순간 스트림이 통째로 끊긴다(실측으로 확인).
        # asyncio.wait는 타임아웃이 나도 태스크를 pending으로 남겨두므로,
        # 같은 태스크를 계속 기다리면서 그 사이에 하트비트만 내보낼 수 있다.
        pending_next = asyncio.ensure_future(agen.__anext__())
        try:
            while True:
                done, _ = await asyncio.wait(
                    {pending_next}, timeout=settings.stream_heartbeat_seconds
                )
                elapsed = time.monotonic() - start

                if not done:
                    if elapsed >= settings.stream_timeout_seconds:
                        pending_next.cancel()
                        yield (
                            "error",
                            {"message": "응답 생성 시간이 초과되었습니다.", "retryable": True},
                        )
                        return
                    yield ("status", {"state": "waiting", "elapsed": round(elapsed, 1)})
                    continue

                try:
                    chunk = pending_next.result()
                except StopAsyncIteration:
                    break

                text = chunk.text
                if text:
                    yield ("token", {"text": text})

                if elapsed >= settings.stream_timeout_seconds:
                    yield (
                        "error",
                        {"message": "응답 생성 시간이 초과되었습니다.", "retryable": True},
                    )
                    return

                pending_next = asyncio.ensure_future(agen.__anext__())
        finally:
            if not pending_next.done():
                pending_next.cancel()
    except Exception as exc:  # noqa: BLE001 - 생성 중 오류도 error 이벤트로 전달
        yield ("error", {"message": f"응답 생성 중 오류가 발생했습니다: {exc}", "retryable": True})
        return

    yield (
        "done",
        {"backend": settings.llm_backend, "elapsed": round(time.monotonic() - start, 2)},
    )
