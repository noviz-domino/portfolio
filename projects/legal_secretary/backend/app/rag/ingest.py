"""PDF -> 청크 -> 임베딩 -> Chroma 저장.

재실행 안전성: 매 실행마다 기존 벡터스토어 디렉토리를 지우고 새로 만든다
(전체 재적재 방식). 문서 몇 개 규모에서는 증분 적재의 복잡도(중복 판별, 삭제된
문서 정리)를 감수할 이유가 없어서 택한 단순한 방식이다. 상세 이유는
docs/작업일지.md 참고.

CLI 실행: `uv run python -m app.rag.ingest`
"""

from __future__ import annotations

import shutil
import time

import pymupdf as fitz
from langchain_chroma import Chroma

from app.config import Settings, get_settings
from app.rag.chunking import Chunk, SourceDocument, chunk_documents
from app.rag.retrieval import build_embeddings


def load_pdf_pages(pdf_path) -> list[SourceDocument]:
    """PDF 파일 하나를 페이지 단위 SourceDocument 목록으로 변환한다."""
    docs: list[SourceDocument] = []
    with fitz.open(pdf_path) as pdf:
        for page_index in range(len(pdf)):
            text = pdf[page_index].get_text()
            if not text.strip():
                continue
            docs.append(
                SourceDocument(
                    text=text,
                    source=pdf_path.name,
                    page=page_index + 1,
                )
            )
    return docs


def load_all_pdfs(pdf_dir) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    for pdf_file in sorted(pdf_dir.glob("*.pdf")):
        docs.extend(load_pdf_pages(pdf_file))
    return docs


def _chunk_to_langchain_document(chunk: Chunk):
    from langchain_core.documents import Document

    return Document(
        page_content=chunk.text,
        metadata={
            "source": chunk.source,
            "page": chunk.page,
            "article": chunk.article,
            "chunk_id": chunk.chunk_id,
        },
        id=chunk.chunk_id,
    )


def ingest(settings: Settings | None = None) -> int:
    """PDF들을 인제스트하고 생성된 청크 수를 반환한다."""
    settings = settings or get_settings()
    pdf_dir = settings.pdf_path
    store_dir = settings.vector_store_dir

    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF 디렉토리를 찾을 수 없습니다: {pdf_dir}")

    # 재실행 안전성: 기존 벡터스토어를 통째로 지우고 새로 만든다.
    if store_dir.exists():
        shutil.rmtree(store_dir)
    store_dir.mkdir(parents=True, exist_ok=True)

    documents = load_all_pdfs(pdf_dir)
    chunks = chunk_documents(
        documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    if not chunks:
        return 0

    embeddings = build_embeddings(settings)
    lc_docs = [_chunk_to_langchain_document(c) for c in chunks]
    ids = [c.chunk_id for c in chunks]

    Chroma.from_documents(
        documents=lc_docs,
        embedding=embeddings,
        ids=ids,
        persist_directory=str(store_dir),
    )
    return len(chunks)


def main() -> None:
    start = time.perf_counter()
    settings = get_settings()
    count = ingest(settings)
    elapsed = time.perf_counter() - start
    print(f"인제스트 완료: 청크 {count}개, 소요 시간 {elapsed:.1f}초")


if __name__ == "__main__":
    main()
