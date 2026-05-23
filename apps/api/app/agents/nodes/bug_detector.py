from app.agents.state import AgentState
from app.code.rules import StaticRuleAnalyzer
from app.core.llm import LLMProvider
from app.domain.models import AgentStep, Evidence, Finding


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
            return state

        chunk = state.retrieved_chunks[0]
        state.findings.append(
            Finding(
                title="Manual review candidate from selected code",
                summary=(
                    "No built-in static rule matched this evidence. Review the selected "
                    "code path manually or enable an optional LLM provider for deeper reasoning."
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
