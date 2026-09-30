from app.rag.chunking import SourceDocument, chunk_documents, split_by_article


def test_split_by_article_finds_boundaries():
    text = (
        "제1조(목적) 이 법은 목적을 정한다.\n"
        "제2조(정의) 이 법에서 용어의 정의는 다음과 같다.\n"
        "제2조의2(적용범위) 이 조는 적용범위를 정한다."
    )
    segments = split_by_article(text)
    articles = [a for a, _ in segments]
    assert articles == ["제1조", "제2조", "제2조의2"]


def test_split_by_article_no_boundary_returns_single_segment():
    text = "이것은 일반 문서입니다. 조문 번호가 전혀 없습니다."
    segments = split_by_article(text)
    assert segments == [(None, text)]


def test_split_by_article_preserves_preamble():
    text = "전문입니다.\n제1조(목적) 본문."
    segments = split_by_article(text)
    assert segments[0][0] is None
    assert "전문" in segments[0][1]
    assert segments[1][0] == "제1조"


def test_chunk_documents_attaches_metadata():
    text = "제1조(목적) 이 법은 목적을 정한다.\n제2조(정의) 정의는 다음과 같다."
    doc = SourceDocument(text=text, source="test.pdf", page=1)
    chunks = chunk_documents([doc], chunk_size=500, chunk_overlap=100)

    assert len(chunks) == 2
    assert {c.article for c in chunks} == {"제1조", "제2조"}
    for c in chunks:
        assert c.source == "test.pdf"
        assert c.page == 1
        assert c.chunk_id


def test_chunk_documents_splits_long_article_keeping_article_metadata():
    long_body = "가" * 1200
    text = f"제56조(연장근로) {long_body}"
    doc = SourceDocument(text=text, source="test.pdf", page=3)
    chunks = chunk_documents([doc], chunk_size=500, chunk_overlap=100)

    assert len(chunks) > 1
    assert all(c.article == "제56조" for c in chunks)


def test_chunk_documents_without_article_boundary_still_chunks():
    text = "일반 " * 400
    doc = SourceDocument(text=text, source="general.pdf", page=1)
    chunks = chunk_documents([doc], chunk_size=500, chunk_overlap=100)

    assert len(chunks) >= 1
    assert all(c.article is None for c in chunks)
