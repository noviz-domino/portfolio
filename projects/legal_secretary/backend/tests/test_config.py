from app.config import Settings


def test_default_backend_is_fake():
    settings = Settings(_env_file=None)
    assert settings.llm_backend == "fake"


def test_backend_switch_via_env(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "self_hosted")
    settings = Settings(_env_file=None)
    assert settings.llm_backend == "self_hosted"


def test_backend_switch_to_api(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "anthropic")
    settings = Settings(_env_file=None)
    assert settings.llm_backend == "anthropic"
