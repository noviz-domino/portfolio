"""FastAPI 진입점."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.rag.retrieval import get_retriever

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 임베딩 모델 적재는 라즈베리파이 CPU에서 1분 이상 걸린다. 첫 요청에서
    # 하면 그 요청이 통째로 지연되므로 기동 시 미리 준비한다. 실패해도 서버는
    # 뜨게 두고 개별 요청에서 오류를 처리한다(인제스트 전 상태 등).
    try:
        await asyncio.to_thread(get_retriever)
        logger.info("리트리버 준비 완료")
    except Exception:
        logger.exception("리트리버 사전 적재 실패. 첫 요청 시 다시 시도한다.")
    yield


app = FastAPI(title="법률 RAG 챗봇 API", lifespan=lifespan)
app.include_router(router)
