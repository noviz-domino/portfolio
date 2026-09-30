"""pydantic-settings 기반 설정.

환경변수와 저장소 루트의 `.env` 파일을 읽는다. 모든 값은 기본값을 가지므로
API 키 없이도 (LLM_BACKEND=fake) 애플리케이션이 동작한다.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# 실행 디렉토리가 저장소 루트든 backend/든 같은 파일을 가리켜야 하므로
# 이 파일 위치를 기준으로 루트를 고정한다.
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_backend: Literal["gemini", "anthropic", "self_hosted", "fake"] = "fake"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    # 무료 티어는 용량 부족 시 503을 간헐적으로 반환한다. 실측상 실패는 3초 내
    # 즉시 거절되므로 같은 모델로 재시도하면 대체로 성공한다.
    gemini_max_retries: int = 4

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "benedict/linkbricks-llama3.1-korean:8b"

    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"

    vector_store_path: str = "data/vector_store"
    pdf_dir: str = "data/pdf"

    retrieval_k: int = 3
    rerank_enabled: bool = False

    chunk_size: int = 500
    chunk_overlap: int = 100

    # SSE 스트리밍(/api/ask/stream) 관련 설정.
    # 초 단위. 소수점을 허용해 테스트에서 짧은 간격으로 하트비트 경로를
    # 검증할 수 있게 한다.
    stream_timeout_seconds: float = 180
    stream_heartbeat_seconds: float = 10

    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None

    @property
    def vector_store_dir(self) -> Path:
        return self._resolve(self.vector_store_path)

    @property
    def pdf_path(self) -> Path:
        return self._resolve(self.pdf_dir)

    @staticmethod
    def _resolve(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else REPO_ROOT / path


@lru_cache
def get_settings() -> Settings:
    """설정을 한 번만 로드해 캐시한다."""
    return Settings()
