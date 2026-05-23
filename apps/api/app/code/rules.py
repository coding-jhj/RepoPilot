from __future__ import annotations

import re

from app.domain.models import Evidence, Finding


class StaticRuleAnalyzer:
    """Free local code-review rules that do not require paid LLM calls."""

    def analyze_chunk(self, chunk: dict) -> list[Finding]:
        lines = chunk["content"].splitlines()
        findings: list[Finding] = []

        for offset, line in enumerate(lines):
            absolute_line = chunk["start_line"] + offset
            if self._looks_like_hardcoded_secret(line):
                findings.append(
                    Finding(
                        title="Hardcoded secret candidate",
                        summary=(
                            "A variable name associated with credentials is assigned a "
                            "literal value. Move secrets to environment variables or a "
                            "secret manager before production use."
                        ),
                        severity="high",
                        evidence=[
                            Evidence(
                                path=chunk["path"],
                                start_line=absolute_line,
                                end_line=absolute_line,
                            )
                        ],
                    )
                )
            if re.match(r"^\s*except\s*:\s*$", line):
                findings.append(
                    Finding(
                        title="Bare except hides failures",
                        summary=(
                            "A bare except catches every exception, including programming "
                            "errors. Catch a specific exception and log or re-raise failures."
                        ),
                        severity="medium",
                        evidence=[
                            Evidence(
                                path=chunk["path"],
                                start_line=absolute_line,
                                end_line=absolute_line,
                            )
                        ],
                    )
                )
            if re.search(r"\beval\s*\(", line):
                findings.append(
                    Finding(
                        title="Dynamic eval execution",
                        summary=(
                            "eval executes dynamic code and can become a security risk. "
                            "Replace it with a parser or explicit dispatch table."
                        ),
                        severity="high",
                        evidence=[
                            Evidence(
                                path=chunk["path"],
                                start_line=absolute_line,
                                end_line=absolute_line,
                            )
                        ],
                    )
                )

        return findings

    def _looks_like_hardcoded_secret(self, line: str) -> bool:
        secret_name = re.search(
            r"\b(password|passwd|secret|token|api[_-]?key|access[_-]?key)\b",
            line,
            flags=re.IGNORECASE,
        )
        literal_assignment = re.search(r"=\s*['\"][^'\"]{6,}['\"]", line)
        return bool(secret_name and literal_assignment)
