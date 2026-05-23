from __future__ import annotations

import re

from app.domain.models import PatchValidationReport


class PatchService:
    def validate(self, diff: str, allowed_paths: list[str]) -> PatchValidationReport:
        touched_paths = self._extract_touched_paths(diff)
        messages: list[str] = []

        if not diff.strip().startswith("diff --git"):
            messages.append("Patch must be a unified git diff.")
        for path in touched_paths:
            if path not in allowed_paths:
                messages.append(f"{path} is outside approved scope.")

        return PatchValidationReport(
            valid=not messages and bool(touched_paths),
            touched_paths=touched_paths,
            messages=messages or ["Patch is scoped to approved files."],
        )

    def draft_patch(self, instruction: str, approved_paths: list[str]) -> str:
        target = approved_paths[0] if approved_paths else "README.md"
        note = instruction.replace("\n", " ")[:120]
        return (
            f"diff --git a/{target} b/{target}\n"
            f"--- a/{target}\n"
            f"+++ b/{target}\n"
            "@@ -1,1 +1,2 @@\n"
            " Existing content\n"
            f"+RepoPilot suggestion: {note}\n"
        )

    def _extract_touched_paths(self, diff: str) -> list[str]:
        paths: list[str] = []
        for match in re.finditer(r"^diff --git a/(.+?) b/(.+?)$", diff, re.MULTILINE):
            left, right = match.groups()
            if left != right:
                paths.extend([left, right])
            else:
                paths.append(left)
        return list(dict.fromkeys(paths))
