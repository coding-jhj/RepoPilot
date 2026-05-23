from app.agents.graph import RepoPilotAgent
from app.core.llm import FakeLLMProvider
from app.services.patch_service import PatchService


def test_agent_overview_includes_evidence_from_retrieved_code():
    agent = RepoPilotAgent(llm=FakeLLMProvider())

    result = agent.run(
        repo_id="repo_1",
        task="overview",
        retrieved_chunks=[
            {
                "path": "app/main.py",
                "start_line": 1,
                "end_line": 4,
                "content": "from fastapi import FastAPI\napp = FastAPI()",
            }
        ],
    )

    assert result.status == "completed"
    assert result.findings[0].evidence[0].path == "app/main.py"
    assert result.timeline[0].node == "planner"


def test_agent_bug_scan_reports_static_rule_without_paid_llm():
    agent = RepoPilotAgent(llm=FakeLLMProvider())

    result = agent.run(
        repo_id="repo_1",
        task="bug_scan",
        retrieved_chunks=[
            {
                "path": "app/security.py",
                "start_line": 20,
                "end_line": 24,
                "content": "def login(password):\n    if password == 'admin123':\n        return True\n",
            }
        ],
    )

    assert any("Hardcoded secret" in finding.title for finding in result.findings)
    assert result.findings[-1].evidence[0].path == "app/security.py"


def test_patch_validator_accepts_scoped_unified_diff():
    diff = """diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,2 +1,2 @@
-print("hello")
+print("hello repopilot")
"""

    report = PatchService().validate(diff, allowed_paths=["app/main.py"])

    assert report.valid is True
    assert report.touched_paths == ["app/main.py"]


def test_patch_validator_rejects_unrelated_paths():
    diff = """diff --git a/secrets.env b/secrets.env
--- a/secrets.env
+++ b/secrets.env
@@ -1 +1 @@
-A=1
+A=2
"""

    report = PatchService().validate(diff, allowed_paths=["app/main.py"])

    assert report.valid is False
    assert "outside approved scope" in report.messages[0]
