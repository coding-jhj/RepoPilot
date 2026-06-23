"""Lexical-gap retrieval benchmark.

Every query is written to share a *meaning* with its target chunk but **no
tokens**. That gap is deliberate: keyword search can only match overlapping
words, so a corpus where the answer has no word overlap with the question is
exactly where semantic embeddings should win. If the queries shared tokens with
their targets, keyword search would tie and the comparison would prove nothing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    target_path: str


# One small repo's worth of chunks. Each query below points at exactly one of
# these; the rest act as distractors.
CORPUS: list[dict] = [
    {
        "path": "auth.py",
        "start_line": 1,
        "end_line": 3,
        "content": (
            "def login(credentials):\n"
            "    if verify_password(credentials):\n"
            "        return issue_session_token(credentials)"
        ),
    },
    {
        "path": "cache.py",
        "start_line": 1,
        "end_line": 4,
        "content": (
            "class BoundedStore:\n"
            "    def put(self, key, value):\n"
            "        if self._is_full():\n"
            "            self._evict_least_recently_used()"
        ),
    },
    {
        "path": "retry.py",
        "start_line": 1,
        "end_line": 5,
        "content": (
            "def with_backoff(operation):\n"
            "    for attempt in range(max_tries):\n"
            "        try:\n"
            "            return operation()\n"
            "        except TransientError:\n"
            "            sleep(2 ** attempt)"
        ),
    },
    {
        "path": "db.py",
        "start_line": 1,
        "end_line": 2,
        "content": (
            "def open_pool():\n"
            "    return psycopg.connect(POSTGRES_DSN, pool_size=10)"
        ),
    },
    {
        "path": "email.py",
        "start_line": 1,
        "end_line": 2,
        "content": (
            "def notify_recipient(address, body):\n"
            "    smtp_client.deliver(address, body)"
        ),
    },
    {
        "path": "parse.py",
        "start_line": 1,
        "end_line": 2,
        "content": "def tokenize(source):\n    return split_into_lexemes(source)",
    },
]


CASES: list[RetrievalCase] = [
    RetrievalCase("how does a user sign in to their account", "auth.py"),
    RetrievalCase("what drops old entries when memory runs out", "cache.py"),
    RetrievalCase("how are failing requests repeated automatically", "retry.py"),
    RetrievalCase("where is the persistent data store accessed", "db.py"),
    RetrievalCase("how do we send mail to a person", "email.py"),
    RetrievalCase("how is code text broken into small units", "parse.py"),
]
