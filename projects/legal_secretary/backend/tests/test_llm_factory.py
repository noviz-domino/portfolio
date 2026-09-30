from app.config import Settings
from app.llm.factory import build_chat_model
from app.llm.fake import FakeChatModel


def test_fake_backend_returns_fake_chat_model():
    settings = Settings(_env_file=None, llm_backend="fake")
    model = build_chat_model(settings)
    assert isinstance(model, FakeChatModel)


def test_fake_backend_is_deterministic():
    settings = Settings(_env_file=None, llm_backend="fake")
    model = build_chat_model(settings)
    r1 = model.invoke("동일 질문")
    r2 = model.invoke("동일 질문")
    assert r1.content == r2.content
