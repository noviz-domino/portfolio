"""키 없이 개발·테스트가 가능한 결정론적 LLM 백엔드.

같은 입력에는 항상 같은 출력을 반환해야 테스트가 안정적이므로,
입력 텍스트를 해시해 고정된 응답 목록 중 하나를 결정론적으로 고른다.
"""

from __future__ import annotations

import hashlib

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage


class FakeChatModel(GenericFakeChatModel):
    """입력을 해시해 결정론적인 답변을 생성하는 fake 백엔드.

    `GenericFakeChatModel`은 messages 제너레이터를 요구하므로, 실제 응답은
    `messages` 인자를 오버라이드해 요청 내용에 따라 매번 새로 만든다.
    """

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs):
        prompt = "\n".join(str(m.content) for m in messages)
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]
        content = f"[fake 응답 {digest}] 입력을 확인했습니다: {prompt[:200]}"
        from langchain_core.outputs import ChatGeneration, ChatResult

        message = AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=message)])


def build_fake_chat_model() -> FakeChatModel:
    """FakeChatModel 인스턴스를 생성한다."""
    return FakeChatModel(messages=iter([]))
