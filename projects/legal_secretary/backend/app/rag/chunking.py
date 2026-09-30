"""조문 단위 청킹.

법률 문서는 조(條)가 의미 단위이므로, 기계적 글자수 분할 전에 먼저
`제N조`/`제N조의M` 경계로 1차 분할한다. 조가 너무 길면 같은 조 소속임을
유지한 채 `RecursiveCharacterTextSplitter`로 2차 분할한다. 조 경계를 전혀
찾지 못하는 문서(법률 문서가 아닌 일반 문서)는 전부 재귀 분할기로 처리한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

# 제56조, 제56조의2 형태의 조문 경계. 줄 시작 위치에서만 매칭해 본문 중
# "제56조에 따라" 같은 인용 표현을 조 경계로 오인하지 않게 한다.
ARTICLE_PATTERN = re.compile(r"^(제\s*\d+\s*조(?:의\s*\d+)?)", re.MULTILINE)

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100


@dataclass
class SourceDocument:
    """청킹 입력 단위. 보통 PDF 한 페이지에 대응한다."""

    text: str
    source: str
    page: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    text: str
    source: str
    page: int
    article: str | None
    chunk_id: str


def _normalize_article(raw: str) -> str:
    return re.sub(r"\s+", "", raw)


def split_by_article(text: str) -> list[tuple[str | None, str]]:
    """텍스트를 (조문 번호 또는 None, 본문) 튜플 목록으로 1차 분할한다.

    조 경계를 하나도 찾지 못하면 [(None, text)] 하나만 반환한다.
    """
    matches = list(ARTICLE_PATTERN.finditer(text))
    if not matches:
        return [(None, text)]

    segments: list[tuple[str | None, str]] = []
    # 첫 조문 경계 이전에 나오는 서두(전문 등)가 있으면 article=None으로 보존.
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            segments.append((None, preamble))

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            segments.append((_normalize_article(m.group(1)), body))

    return segments


def chunk_documents(
    documents: list[SourceDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """문서 목록을 조문 단위 청크 목록으로 변환한다."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks: list[Chunk] = []
    seq = 0
    for doc in documents:
        for article, body in split_by_article(doc.text):
            if len(body) <= chunk_size:
                pieces = [body]
            else:
                pieces = splitter.split_text(body)
            for piece in pieces:
                if not piece.strip():
                    continue
                chunk_id = f"{doc.source}:p{doc.page}:{seq}"
                seq += 1
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        page=doc.page,
                        article=article,
                        chunk_id=chunk_id,
                    )
                )
    return chunks
