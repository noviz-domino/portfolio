"""API 요청·응답 스키마 (설계.md 참고)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class Citation(BaseModel):
    source: str
    page: int
    article: str | None = None
    snippet: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    backend: str


class HealthResponse(BaseModel):
    status: str
    backend: str
