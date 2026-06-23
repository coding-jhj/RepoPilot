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


def _reconstruct(body: list[str]) -> tuple[list[str], list[str]]:
    """Rebuild (original_lines, new_lines) from a single file's diff body.

    Context lines belong to both sides; ``-`` lines only to the original, ``+``
    lines only to the new side. Lines are newline-stripped (the body came from
    ``diff.splitlines()`` in :func:`_files`). This is the hunk region only — for
    a small chunk diff that is the whole chunk plus difflib's context, which is
    exactly what anchors a clean splice back into the full file.
    """
    original: list[str] = []
    new: list[str] = []
    for line in body:
        if _HUNK.match(line) or line.startswith(("---", "+++")):
            continue
        tag, text = line[:1], line[1:]
        if tag == " ":
            original.append(text)
            new.append(text)
        elif tag == "-":
            original.append(text)
        elif tag == "+":
            new.append(text)
    return original, new


def _find_block(haystack: list[str], needle: list[str]) -> int:
    """First index where ``needle`` occurs contiguously in ``haystack``, or -1."""
    if not needle:
        return -1
    last = len(haystack) - len(needle)
    for start in range(last + 1):
        if haystack[start : start + len(needle)] == needle:
            return start
    return -1


def apply_patch_to_text(full_text: str, diff: str, path: str) -> str:
    """Apply ``diff``'s change for ``path`` to ``full_text`` and return the result.

    The diff may have been built against a *chunk* of the file (hunk offsets are
    chunk-relative), so this does not trust line numbers. It rebuilds the hunk's
    original region from the diff and locates that exact block of lines in the
    full file, then splices in the new region. Raises ``ValueError`` if the diff
    does not touch ``path`` or the original block is not found verbatim (the file
    drifted from what the patch was built against) — never applies a fuzzy match.
    """
    body = _files(diff).get(path)
    if body is None:
        raise ValueError(f"Diff does not modify {path}.")
    original, new = _reconstruct(body)
    full_lines = _ensure_nl(full_text).splitlines()
    idx = _find_block(full_lines, original)
    if idx == -1:
        raise ValueError(
            f"Patch context not found in {path}; the file has drifted from the patch."
        )
    spliced = full_lines[:idx] + new + full_lines[idx + len(original) :]
    return "\n".join(spliced) + "\n"


def apply_unified_diff(diff: str, sources: dict[str, str]) -> dict[str, str]:
    """Apply every file's hunks in ``diff`` to ``sources`` and return new contents.

    ``sources`` must be the text the diff was built against (e.g. the chunk for a
    chunk-relative diff). Round-trips with :func:`build_git_diff`:
    ``apply_unified_diff(build_git_diff(p, a, b), {p: a}) == {p: _ensure_nl(b)}``.
    Raises ``ValueError`` on a context/removed-line mismatch.
    """
    result: dict[str, str] = {}
    for path, body in _files(diff).items():
        if path not in sources:
            raise ValueError(f"No source provided for {path}.")
        original, new = _reconstruct(body)
        src = _ensure_nl(sources[path]).splitlines()
        idx = _find_block(src, original)
        if idx == -1:
            raise ValueError(f"Patch does not apply cleanly to {path}.")
        spliced = src[:idx] + new + src[idx + len(original) :]
        result[path] = "\n".join(spliced) + "\n"
    return result


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
