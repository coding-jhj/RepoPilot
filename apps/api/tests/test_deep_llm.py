from dataclasses import dataclass

from app.agents.graph import RepoPilotAgent
from app.core.llm import FakeLLMProvider, LLMError, build_llm_provider


@dataclass
class StubLLM:
    enabled: bool = True
    payload: str = '{"title": "SQL injection risk", "severity": "high", "summary": "User input is concatenated into a query."}'

    def complete(self, system: str, prompt: str) -> str:
        return self.payload


CHUNK = {
    "path": "app/db.py",
    "start_line": 10,
    "end_line": 14,
    "content": "def get(uid):\n    return run('SELECT * FROM u WHERE id=' + uid)\n",
}


def test_deep_scan_adds_llm_finding_when_enabled():
    agent = RepoPilotAgent(llm=StubLLM())

    result = agent.run(repo_id="r1", task="bug_scan", retrieved_chunks=[CHUNK], deep=True)

    assert any(f.severity == "high" and "SQL" in f.title for f in result.findings)
    assert any("LLM-reasoned" in step.summary for step in result.timeline)
    assert result.summary  # reviewer produced an LLM summary


def test_deep_flag_off_skips_llm():
    agent = RepoPilotAgent(llm=StubLLM())

    result = agent.run(repo_id="r1", task="bug_scan", retrieved_chunks=[CHUNK], deep=False)

    assert not any("LLM-reasoned" in step.summary for step in result.timeline)


def test_fake_provider_stays_static_even_in_deep_mode():
    agent = RepoPilotAgent(llm=FakeLLMProvider())

    result = agent.run(repo_id="r1", task="bug_scan", retrieved_chunks=[CHUNK], deep=True)

    assert not any("LLM-reasoned" in step.summary for step in result.timeline)


def test_build_llm_provider_without_key_falls_back_to_fake():
    provider = build_llm_provider("gemini", api_key=None)
    assert getattr(provider, "enabled", False) is False


def test_gemini_provider_raises_llm_error_on_bad_key():
    provider = build_llm_provider("gemini", api_key="invalid-key", model="gemini-3.5-flash")
    assert provider.enabled is True
    try:
        provider.complete("system", "hi")
    except LLMError:
        return
    raise AssertionError("expected LLMError for an invalid key")
