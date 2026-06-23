"""Bug-finding benchmark for the bug_scan path.

Each case is one code chunk with a ground-truth label. The dataset is split into
three deliberate groups so the eval can tell the deterministic static baseline
apart from the LLM deep-analysis arm:

- ``pattern`` bugs trip one of the three static regex rules (hardcoded secret,
  bare except, dynamic ``eval``). The free static baseline is expected to catch
  these — they are its true positives.
- ``semantic`` bugs are real defects with **no** static-rule signature (SQL
  injection via string-building, null dereference, off-by-one, un-awaited
  coroutine, mutable default argument). Static is expected to MISS every one of
  them; this is the recall gap a reasoning LLM is supposed to close.
- ``clean`` chunks have no bug. They measure precision / false positives — a
  detector that flags these is crying wolf.

The static-only baseline over this set is fully deterministic and offline, so its
numbers are committable as fact. The deep (Gemini) arm is opt-in and illustrative
only — a live LLM is not reproducible, so its numbers are reported as a sample
run, never pinned. See ``bug_harness.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BugGroup = Literal["pattern", "semantic", "clean"]


@dataclass(frozen=True)
class BugCase:
    chunk: dict
    has_bug: bool
    group: BugGroup
    bug_kind: str  # short label of the planted defect, or "" for clean chunks


def _chunk(path: str, content: str) -> dict:
    return {
        "path": path,
        "start_line": 1,
        "end_line": content.count("\n") + 1,
        "content": content,
    }


# --- pattern bugs: the three static rules should fire on these ---
_PATTERN: list[BugCase] = [
    BugCase(
        _chunk(
            "secret.py",
            'def connect():\n    api_key = "sk-live-9f8e7d6c5b4a3210"\n    return Client(api_key)',
        ),
        has_bug=True,
        group="pattern",
        bug_kind="hardcoded_secret",
    ),
    BugCase(
        _chunk(
            "swallow.py",
            "def load(path):\n    try:\n        return read(path)\n    except:\n        return None",
        ),
        has_bug=True,
        group="pattern",
        bug_kind="bare_except",
    ),
    BugCase(
        _chunk(
            "calc.py",
            'def run(expr):\n    return eval(expr)',
        ),
        has_bug=True,
        group="pattern",
        bug_kind="dynamic_eval",
    ),
]


# --- semantic bugs: real defects with no static signature; static should miss all ---
_SEMANTIC: list[BugCase] = [
    BugCase(
        _chunk(
            "users.py",
            'def find_user(uid):\n    sql = "SELECT * FROM users WHERE id = " + uid\n    return db.run(sql)',
        ),
        has_bug=True,
        group="semantic",
        bug_kind="sql_injection",
    ),
    BugCase(
        _chunk(
            "profile.py",
            "def display_name(user):\n    return user.profile.full_name.title()",
        ),
        has_bug=True,
        group="semantic",
        bug_kind="null_dereference",
    ),
    BugCase(
        _chunk(
            "report.py",
            "def total(rows):\n    acc = 0\n    for i in range(len(rows) + 1):\n        acc += rows[i]\n    return acc",
        ),
        has_bug=True,
        group="semantic",
        bug_kind="off_by_one",
    ),
    BugCase(
        _chunk(
            "fetcher.py",
            'async def latest():\n    payload = fetch_remote()\n    return payload["items"][0]',
        ),
        has_bug=True,
        group="semantic",
        bug_kind="missing_await",
    ),
    BugCase(
        _chunk(
            "accumulate.py",
            "def append_item(item, bucket=[]):\n    bucket.append(item)\n    return bucket",
        ),
        has_bug=True,
        group="semantic",
        bug_kind="mutable_default_arg",
    ),
]


# --- clean chunks: no bug; a detector should stay silent ---
_CLEAN: list[BugCase] = [
    BugCase(
        _chunk(
            "safe_query.py",
            'def find_user(uid):\n    return db.run("SELECT * FROM users WHERE id = %s", (uid,))',
        ),
        has_bug=False,
        group="clean",
        bug_kind="",
    ),
    BugCase(
        _chunk(
            "add.py",
            "def add(a, b):\n    return a + b",
        ),
        has_bug=False,
        group="clean",
        bug_kind="",
    ),
    BugCase(
        _chunk(
            "guarded.py",
            "def display_name(user):\n    if user is None:\n        return 'anonymous'\n    return user.name",
        ),
        has_bug=False,
        group="clean",
        bug_kind="",
    ),
    BugCase(
        _chunk(
            "specific_except.py",
            "def load(path):\n    try:\n        return read(path)\n    except FileNotFoundError as err:\n        log(err)\n        raise",
        ),
        has_bug=False,
        group="clean",
        bug_kind="",
    ),
]


CASES: list[BugCase] = _PATTERN + _SEMANTIC + _CLEAN
