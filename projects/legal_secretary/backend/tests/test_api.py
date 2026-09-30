import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rag.retrieval import RetrievedChunk


class _StubRetriever:
    """실제 임베딩 모델 없이 검색 결과를 흉내 내는 테스트용 스텁."""

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


_SAMPLE_CHUNKS = [
    RetrievedChunk(
        chunk_id="testpdf.pdf:p3:0",
        text="제56조(연장근로) 사용자는 연장근로에 대하여 통상임금의 100분의 50 이상을 가산하여 지급하여야 한다.",
        source="testpdf.pdf",
        page=3,
        article="제56조",
    )
]


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


@pytest.mark.anyio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["backend"] == "fake"


@pytest.mark.anyio
async def test_ask_schema_and_citations_filled(client):
    response = await client.post("/api/ask", json={"question": "테스트"})
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"answer", "citations", "backend"}
    assert isinstance(body["answer"], str)
    assert len(body["citations"]) >= 1
    citation = body["citations"][0]
    assert set(citation.keys()) == {"source", "page", "article", "snippet"}
    assert citation["source"] == "testpdf.pdf"
    assert citation["page"] == 3
    assert citation["article"] == "제56조"
    assert body["backend"] == "fake"


@pytest.mark.anyio
async def test_ask_is_deterministic(client):
    r1 = await client.post("/api/ask", json={"question": "동일 질문"})
    r2 = await client.post("/api/ask", json={"question": "동일 질문"})
    assert r1.json()["answer"] == r2.json()["answer"]


@pytest.mark.anyio
async def test_ask_returns_clear_error_when_vector_store_empty(empty_client):
    response = await empty_client.post("/api/ask", json={"question": "테스트"})
    assert response.status_code == 503
    assert "ingest" in response.json()["detail"]


@pytest.mark.anyio
async def test_ask_extracts_text_from_block_content(monkeypatch):
    """content가 블록 리스트인 백엔드에서도 answer는 평문이어야 한다.

    Gemini는 [{"type": "text", "text": ...,  "extras": {...}}] 형태를 돌려준다.
    str(content)로 처리하면 리스트 repr과 내부 서명 필드까지 응답에 노출된다.
    """
    from langchain_core.messages import AIMessage

    class _BlockContentModel:
        async def ainvoke(self, prompt):
            return AIMessage(
                content=[
                    {"type": "text", "text": "앞부분", "extras": {"signature": "SECRET"}},
                    {"type": "text", "text": " 뒷부분"},
                ]
            )

    monkeypatch.setattr(
        "app.services.get_retriever", lambda: _StubRetriever(_SAMPLE_CHUNKS)
    )
    monkeypatch.setattr(
        "app.services.build_chat_model", lambda settings: _BlockContentModel()
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/ask", json={"question": "테스트"})

    answer = response.json()["answer"]
    assert answer == "앞부분 뒷부분"
    assert "SECRET" not in answer
    assert not answer.startswith("[")


@pytest.fixture
def anyio_backend():
    return "asyncio"
