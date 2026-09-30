"""선택적 크로스 인코더 리랭킹.

`settings.rerank_enabled`가 False면 모델을 로드조차 하지 않는다 (파이 CPU에서는
로딩만으로도 수 초~수십 초가 걸리므로). 기본값은 False.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import Settings
from app.rag.retrieval import RetrievedChunk

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

_RERANK_MODEL_NAME = "BAAI/bge-reranker-v2-m3"

_model_cache: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model_cache
    if _model_cache is None:
        from sentence_transformers import CrossEncoder

        _model_cache = CrossEncoder(_RERANK_MODEL_NAME)
    return _model_cache


def rerank(
    query: str, chunks: list[RetrievedChunk], settings: Settings
) -> list[RetrievedChunk]:
    """rerank_enabled가 False면 그대로 반환한다 (모델 로드 없음)."""
    if not settings.rerank_enabled or not chunks:
        return chunks

    model = _get_model()
    pairs = [(query, c.text) for c in chunks]
    scores = model.predict(pairs)
    order = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    return [chunks[i] for i in order]
