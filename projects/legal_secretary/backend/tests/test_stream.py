"""03단계 — SSE 스트리밍(/api/ask/stream) 테스트.

전부 `fake` 백엔드로, 외부 API 호출 없이 동작해야 한다.
"""

from __future__ import annotations

import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rag.retrieval import RetrievedChunk

_SAMPLE_CHUNKS = [
    RetrievedChunk(
        chunk_id="testpdf.pdf:p3:0",
        text="제56조(연장근로) 사용자는 연장근로에 대하여 통상임금의 100분의 50 이상을 가산하여 지급하여야 한다.",
        source="testpdf.pdf",
        page=3,
        article="제56조",
    )
]


class _StubRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    def is_empty(self) -> bool:
        return False

    def retrieve(self, query: str, top_k: int | None = None):
        return self._chunks[:top_k] if top_k else self._chunks


class _EmptyRetriever:
    def is_empty(self) -> bool:
        return True

    def retrieve(self, query: str, top_k: int | None = None):
        return []


@pytest.fixture
async def client(monkeypatch):
    monkeypatch.setattr(
        "app.services.get_retriever", lambda: _StubRetriever(_SAMPLE_CHUNKS)
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def empty_client(monkeypatch):
    monkeypatch.setattr("app.services.get_retriever", lambda: _EmptyRetriever())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _parse_sse(raw_text: str) -> list[tuple[str, dict]]:
    """SSE 텍스트를 (event, data) 목록으로 파싱한다."""
    events: list[tuple[str, dict]] = []
    for block in raw_text.strip("\n").split("\n\n"):
        if not block.strip():
            continue
        event_name = None
        data_line = None
        for line in block.splitlines():
            if line.startswith("event: "):
                event_name = line[len("event: ") :]
            elif line.startswith("data: "):
                data_line = line[len("data: ") :]
        assert event_name is not None
        assert data_line is not None
        events.append((event_name, json.loads(data_line)))
    return events


@pytest.mark.anyio
async def test_stream_event_order_and_citations_first(client):
    async with client.stream(
        "POST", "/api/ask/stream", json={"question": "연장근로 수당은?"}
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        raw = ""
        async for chunk in response.aiter_text():
            raw += chunk

    events = _parse_sse(raw)
    event_names = [name for name, _ in events]

    # status(retrieving)가 스트림 시작 즉시 가장 먼저 오고, 그 다음이
    # citations다 (검색 완료 후 확정, 이 단계의 핵심).
    assert event_names[0] == "status"
    assert events[0][1]["state"] == "retrieving"
    assert event_names[1] == "citations"
    assert event_names[2] == "status"
    assert events[2][1]["state"] == "generating"
    assert event_names[-1] == "done"
    assert "token" in event_names

    citations = events[1][1]["citations"]
    assert citations[0]["source"] == "testpdf.pdf"
    assert citations[0]["article"] == "제56조"

    done_data = events[-1][1]
    assert done_data["backend"] == "fake"
    assert "elapsed" in done_data


@pytest.mark.anyio
async def test_stream_tokens_split_into_multiple_events(client):
    async with client.stream(
        "POST", "/api/ask/stream", json={"question": "연장근로 수당은?"}
    ) as response:
        raw = ""
        async for chunk in response.aiter_text():
            raw += chunk
    events = _parse_sse(raw)
    token_events = [data for name, data in events if name == "token"]
    # 여러 토큰으로 나뉘어 도착해야 한다(한 번에 다 오면 안 됨).
    assert len(token_events) > 1


@pytest.mark.anyio
async def test_stream_concatenated_tokens_match_non_streaming_answer(client):
    question = "연장근로 수당은 어떻게 계산하나요?"

    async with client.stream(
        "POST", "/api/ask/stream", json={"question": question}
    ) as response:
        raw = ""
        async for chunk in response.aiter_text():
            raw += chunk
    events = _parse_sse(raw)
    streamed_answer = "".join(
        data["text"] for name, data in events if name == "token"
    )

    ask_response = await client.post("/api/ask", json={"question": question})
    assert ask_response.status_code == 200
    non_streaming_answer = ask_response.json()["answer"]

    assert streamed_answer == non_streaming_answer


@pytest.mark.anyio
async def test_stream_empty_vector_store_emits_error_event_not_exception(
    empty_client,
):
    async with empty_client.stream(
        "POST", "/api/ask/stream", json={"question": "테스트"}
    ) as response:
        assert response.status_code == 200
        raw = ""
        async for chunk in response.aiter_text():
            raw += chunk

    events = _parse_sse(raw)
    assert len(events) == 2
    assert events[0] == ("status", {"state": "retrieving"})
    event_name, data = events[1]
    assert event_name == "error"
    assert "retryable" in data
    assert "ingest" in data["message"]


@pytest.mark.anyio
async def test_stream_survives_heartbeat_when_first_token_is_slow(monkeypatch):
    """첫 토큰이 하트비트 간격보다 늦게 와도 스트림이 끊기면 안 된다.

    asyncio.wait_for로 __anext__()를 감싸면 타임아웃 시 코루틴이 취소되어
    비동기 제너레이터가 망가지고, 다음 호출에서 StopAsyncIteration이 나면서
    토큰을 하나도 받지 못한 채 done으로 끝난다. 실제 Gemini 무료 티어에서
    첫 토큰이 10초 넘게 걸려 이 버그가 발생했다.
    """
    import asyncio

    from langchain_core.messages import AIMessageChunk

    class _SlowFirstTokenModel:
        async def astream(self, prompt):
            # 하트비트(0.05초)보다 확실히 늦게 첫 토큰을 내보낸다.
            await asyncio.sleep(0.2)
            yield AIMessageChunk(content=[{"type": "text", "text": "느린"}])
            yield AIMessageChunk(content=[{"type": "text", "text": " 첫토큰"}])

    from app.config import Settings, get_settings

    monkeypatch.setattr(
        "app.services.get_retriever", lambda: _StubRetriever(_SAMPLE_CHUNKS)
    )
    monkeypatch.setattr(
        "app.services.build_chat_model", lambda settings: _SlowFirstTokenModel()
    )

    # 설정은 FastAPI 의존성으로 주입되므로 dependency_overrides로 갈아끼워야
    # 실제로 하트비트 경로를 탄다. monkeypatch로는 반영되지 않는다.
    app.dependency_overrides[get_settings] = lambda: Settings(
        stream_heartbeat_seconds=0.05, stream_timeout_seconds=30
    )
    try:
        transport = ASGITransport(app=app)
        async with (
            AsyncClient(transport=transport, base_url="http://test") as ac,
            ac.stream("POST", "/api/ask/stream", json={"question": "테스트"}) as response,
        ):
            raw = ""
            async for chunk in response.aiter_text():
                raw += chunk
    finally:
        app.dependency_overrides.pop(get_settings, None)

    events = _parse_sse(raw)
    names = [n for n, _ in events]

    # 하트비트가 실제로 발생했는지 먼저 확인한다. 이게 없으면 이 테스트는
    # 버그를 검증하지 못한 채 통과하는 무의미한 테스트가 된다.
    assert any(
        n == "status" and d.get("state") == "waiting" for n, d in events
    ), f"하트비트가 발생하지 않아 검증이 무의미하다. 수신 이벤트: {names}"

    # 하트비트가 발생했더라도 토큰이 정상 수신되고 done으로 끝나야 한다.
    tokens = "".join(d["text"] for n, d in events if n == "token")
    assert tokens == "느린 첫토큰", f"토큰 유실. 수신 이벤트: {names}"
    assert names[-1] == "done"


@pytest.fixture
def anyio_backend():
    return "asyncio"
