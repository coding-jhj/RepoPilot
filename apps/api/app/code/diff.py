"""Low-level unified-diff helpers shared by the patch writer and patch eval.

``build_git_diff`` is the single diff assembler (used by both ``PatchWriterNode``
and ``PatchService.draft_patch``) so there is exactly one place that knows the
git-diff wire format. ``patch_applies`` is a dependency-free appliability check:
it verifies every hunk's context/removed lines actually match the source at the
claimed offsets, which is the real bar for "valid diff" — a well-formed
``diff --git`` header proves nothing about whether the patch lands.
"""

from __future__ import annotations

import difflib
import re

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _ensure_nl(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def build_git_diff(path: str, original: str, new: str) -> str:
    """Assemble a unified git diff transforming ``original`` into ``new``.

    Both sides are newline-terminated first so difflib never emits a
    "No newline at end of file" marker. Returns "" when the two are identical
    (an empty diff is not a patch).
    """
    original, new = _ensure_nl(original), _ensure_nl(new)
    body = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )
    if not body:
        return ""
    return f"diff --git a/{path} b/{path}\n{body}"


def _files(diff: str) -> dict[str, list[str]]:
    """Split a diff into {path: body lines} keyed by the b/ path of each file."""
    files: dict[str, list[str]] = {}
    path: str | None = None
    for line in diff.splitlines():
        header = re.match(r"^diff --git a/(.+?) b/(.+?)$", line)
        if header:
            path = header.group(2)
            files[path] = []
        elif path is not None:
            files[path].append(line)
    return files


def patch_applies(diff: str, sources: dict[str, str]) -> bool:
    """True iff every hunk's context/removed lines match ``sources`` exactly.

    This is a clean-apply check, not a fuzzy one: a single mismatched context or
    removed line (the symptom of a hand-rolled hunk with wrong offsets) fails it.
    """
    files = _files(diff)
    if not files:
        return False
    for path, body in files.items():
        if path not in sources:
            return False
        src = _ensure_nl(sources[path]).splitlines()
        i = 0
        for line in body:
            hunk = _HUNK.match(line)
            if hunk:
                i = int(hunk.group(1)) - 1  # old-side start, 0-based
                continue
            if line.startswith(("---", "+++")):
                continue
            tag, text = line[:1], line[1:]
            if tag in (" ", "-"):
                if i >= len(src) or src[i] != text:
                    return False
                i += 1
            # '+' lines exist only on the new side; they do not advance src
    return True
