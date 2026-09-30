"""하이브리드 검색: Chroma(dense) + BM25(sparse) 를 RRF로 융합한다."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi

from app.config import Settings, get_settings

# RRF 상수. 값이 클수록 상위 랭크와 하위 랭크의 점수 차이가 완만해진다.
# 원 논문(Cormack et al., 2009)의 관행값 60을 그대로 사용한다.
RRF_K = 60

# 각 경로(dense/sparse)에서 융합 전에 가져오는 후보 수. 최종 반환 개수
# (settings.retrieval_k)보다 넉넉히 뽑아야 융합이 의미가 있다.
CANDIDATE_POOL_SIZE = 20

# 한국어 조사 제거용 매우 단순한 접미사 목록. 형태소 분석기 없이
# "은/는/이/가/을/를/의/에/에서/으로/와/과/도" 같은 흔한 조사만 잘라낸다.
# 완벽하지 않다 — 예: "법률의" -> "법률" 은 되지만 "법률이며" 등은 처리 못함.
_JOSA_SUFFIXES = sorted(
    ["에서부터", "으로부터", "이라는", "에서", "으로", "이며", "이고", "에게",
     "부터", "까지", "만큼", "처럼", "이나", "라는", "와", "과", "은", "는",
     "이", "가", "을", "를", "의", "에", "도", "만", "로"],
    key=len,
    reverse=True,
)


def simple_korean_tokenize(text: str) -> list[str]:
    """공백 분리 + 흔한 조사 제거 수준의 단순 토크나이저.

    형태소 분석기(konlpy 등)를 쓰지 않는다는 설계 결정에 따른 근사치다.
    "제56조" 같은 정확 매칭 토큰은 보존되지만, 복잡한 활용형/조사 조합은
    걸러내지 못하는 한계가 있다 (작업일지 참고).
    """
    raw_tokens = re.findall(r"[가-힣A-Za-z0-9]+", text)
    tokens: list[str] = []
    for tok in raw_tokens:
        stripped = tok
        for suf in _JOSA_SUFFIXES:
            if len(tok) > len(suf) + 1 and tok.endswith(suf):
                stripped = tok[: -len(suf)]
                break
        tokens.append(stripped)
        if stripped != tok:
            tokens.append(tok)
    return tokens


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source: str
    page: int
    article: str | None


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = RRF_K
) -> list[tuple[str, float]]:
    """여러 개의 순위 리스트(문서 id의 순서 있는 목록)를 RRF로 융합한다.

    score(d) = sum_i 1 / (k + rank_i(d))   (rank는 1부터 시작)

    반환값은 (id, score) 목록을 점수 내림차순으로 정렬한 것이다.
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def build_embeddings(settings: Settings) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": settings.embedding_device},
    )


class HybridRetriever:
    """벡터스토어에 저장된 청크 전체를 BM25 인덱스로도 유지하며 하이브리드 검색을 수행."""

    def __init__(self, settings: Settings, embeddings: HuggingFaceEmbeddings | None = None):
        self.settings = settings
        self.embeddings = embeddings or build_embeddings(settings)
        self.vector_store = Chroma(
            persist_directory=str(settings.vector_store_dir),
            embedding_function=self.embeddings,
        )
        self._bm25: BM25Okapi | None = None
        self._bm25_docs: list[dict[str, Any]] = []
        self._load_bm25_corpus()

    def _load_bm25_corpus(self) -> None:
        collection = self.vector_store.get(include=["documents", "metadatas"])
        ids = collection.get("ids", [])
        documents = collection.get("documents", [])
        metadatas = collection.get("metadatas", [])
        self._bm25_docs = [
            {"id": doc_id, "text": text, "metadata": meta or {}}
            for doc_id, text, meta in zip(ids, documents, metadatas, strict=False)
        ]
        if not self._bm25_docs:
            self._bm25 = None
            return
        tokenized = [simple_korean_tokenize(d["text"]) for d in self._bm25_docs]
        self._bm25 = BM25Okapi(tokenized)

    def is_empty(self) -> bool:
        return not self._bm25_docs

    def _dense_ranked_ids(self, query: str, n: int) -> list[str]:
        results = self.vector_store.similarity_search_with_score(query, k=n)
        return [doc.metadata["chunk_id"] for doc, _ in results if "chunk_id" in doc.metadata]

    def _sparse_ranked_ids(self, query: str, n: int) -> list[str]:
        if self._bm25 is None:
            return []
        tokenized_query = simple_korean_tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)
        ranked = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:n]
        return [self._bm25_docs[i]["id"] for i in ranked]

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        if self.is_empty():
            return []
        top_k = top_k or self.settings.retrieval_k
        dense_ids = self._dense_ranked_ids(query, CANDIDATE_POOL_SIZE)
        sparse_ids = self._sparse_ranked_ids(query, CANDIDATE_POOL_SIZE)
        fused = reciprocal_rank_fusion([dense_ids, sparse_ids])

        id_to_doc = {d["id"]: d for d in self._bm25_docs}
        results: list[RetrievedChunk] = []
        for doc_id, _score in fused[:top_k]:
            doc = id_to_doc.get(doc_id)
            if doc is None:
                continue
            meta = doc["metadata"]
            results.append(
                RetrievedChunk(
                    chunk_id=doc_id,
                    text=doc["text"],
                    source=meta.get("source", "unknown"),
                    page=meta.get("page", -1),
                    article=meta.get("article"),
                )
            )
        return results


@lru_cache
def get_retriever() -> HybridRetriever:
    """프로세스당 한 번만 임베딩 모델과 BM25 인덱스를 로드해 재사용한다.

    `get_settings()`와 동일하게 lru_cache를 쓰므로, 런타임 중 설정을 바꾸려면
    프로세스를 재시작해야 한다 (1단계에서 정한 방식과 동일).
    """
    return HybridRetriever(get_settings())
