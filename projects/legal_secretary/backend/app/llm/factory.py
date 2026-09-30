"""설정을 보고 적절한 `BaseChatModel` 구현을 반환하는 팩토리.

LangChain의 `BaseChatModel`이 이미 공통 인터페이스 역할을 하므로 별도의
추상 클래스를 만들지 않는다.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings
from app.llm.fake import build_fake_chat_model


def build_chat_model(settings: Settings) -> BaseChatModel:
    """`settings.llm_backend`에 따라 채팅 모델 인스턴스를 생성한다."""
    match settings.llm_backend:
        case "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
                # 무료 티어의 간헐적 503을 지수 백오프로 흡수한다.
                max_retries=settings.gemini_max_retries,
            )
        case "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=settings.anthropic_model,
                api_key=settings.anthropic_api_key,
            )
        case "self_hosted":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
            )
        case "fake":
            return build_fake_chat_model()
        case _:
            raise ValueError(f"알 수 없는 LLM_BACKEND: {settings.llm_backend}")
