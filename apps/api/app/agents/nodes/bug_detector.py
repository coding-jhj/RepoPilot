from __future__ import annotations

import json

from app.agents.state import AgentState
from app.code.rules import StaticRuleAnalyzer
from app.core.llm import LLMError, LLMProvider
from app.domain.models import AgentStep, Evidence, Finding

# Title of the fallback finding emitted when no static rule or LLM finding fires.
# Exported so the eval harness can exclude it when counting substantive detections
# (a title change here must not silently corrupt the metrics).
MANUAL_REVIEW_TITLE = "Manual review candidate from selected code"

_SEVERITIES = {"info", "low", "medium", "high"}
_LLM_SYSTEM = (
    "You are a senior software engineer reviewing a single code chunk for real bugs, "
    "security risks, or risky patterns. Only report issues you can justify from the code "
    "shown. Reply with strict JSON and nothing else: either "
    '{"none": true} when there is nothing notable, or '
    '{"title": "...", "severity": "info|low|medium|high", "summary": "one or two sentences"}.'
)
_MAX_LLM_CHUNKS = 3


class BugDetectorNode:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm
        self.static_rules = StaticRuleAnalyzer()

    def run(self, state: AgentState) -> AgentState:
        if "bug" not in state.task and "patch" not in state.task:
            state.timeline.append(
                AgentStep(node="bug_detector", summary="Skipped bug scan for this task.")
            )
            return state
        if not state.retrieved_chunks:
            return state

        rule_findings: list[Finding] = []
        for chunk in state.retrieved_chunks:
            rule_findings.extend(self.static_rules.analyze_chunk(chunk))
        if rule_findings:
            state.findings.extend(rule_findings)
            state.timeline.append(
                AgentStep(
                    node="bug_detector",
                    summary=f"Added {len(rule_findings)} free static-analysis findings.",
                )
            )

        llm_findings: list[Finding] = []
        if state.deep and getattr(self.llm, "enabled", False):
            llm_findings = self._deep_scan(state)

        if rule_findings or llm_findings:
            return state

        chunk = state.retrieved_chunks[0]
        state.findings.append(
            Finding(
                title=MANUAL_REVIEW_TITLE,
                summary=(
                    "No built-in static rule matched this evidence. Review the selected "
                    "code path manually or enable deep analysis with a Gemini key for LLM reasoning."
                ),
                severity="info",
                evidence=[
                    Evidence(
                        path=chunk["path"],
                        start_line=chunk["start_line"],
                        end_line=chunk["end_line"],
                    )
                ],
            )
        )
        state.timeline.append(
            AgentStep(node="bug_detector", summary="Added one evidence-backed manual review candidate.")
        )
        return state

    def _deep_scan(self, state: AgentState) -> list[Finding]:
        findings: list[Finding] = []
        for chunk in state.retrieved_chunks[:_MAX_LLM_CHUNKS]:
            prompt = (
                f"File: {chunk['path']} (lines {chunk['start_line']}-{chunk['end_line']})\n\n"
                f"```\n{chunk['content']}\n```"
            )
            try:
                raw = self.llm.complete(_LLM_SYSTEM, prompt)
            except LLMError as exc:
                state.timeline.append(
                    AgentStep(node="bug_detector", summary=f"Deep LLM analysis unavailable: {exc}")
                )
                break
            parsed = self._parse(raw)
            if not parsed:
                continue
            findings.append(
                Finding(
                    title=parsed["title"],
                    summary=parsed["summary"],
                    severity=parsed["severity"],
                    evidence=[
                        Evidence(
                            path=chunk["path"],
                            start_line=chunk["start_line"],
                            end_line=chunk["end_line"],
                        )
                    ],
                )
            )
        if findings:
            state.findings.extend(findings)
            state.timeline.append(
                AgentStep(
                    node="bug_detector",
                    summary=f"Added {len(findings)} LLM-reasoned findings (Gemini deep analysis).",
                )
            )
        return findings

    @staticmethod
    def _parse(raw: str) -> dict | None:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        if data.get("none") or not data.get("title") or not data.get("summary"):
            return None
        severity = str(data.get("severity", "info")).lower()
        return {
            "title": str(data["title"])[:120],
            "summary": str(data["summary"]),
            "severity": severity if severity in _SEVERITIES else "info",
        }
