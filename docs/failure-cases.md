# Failure Cases

RepoPilot is not expected to solve every software engineering task.

Known limitations:

- Large repositories may exceed indexing, clone, retrieval, or free-hosting runtime limits.
- Free deterministic static rules catch narrower issues than a strong cloud LLM.
- JS/TS/TSX parsing uses tree-sitter where available and falls back to regex, so unsupported syntax can still produce partial symbols.
- The Qdrant integration is represented by an in-memory compatible boundary in the free MVP.
- Real GitHub PR creation is opt-in only. Without a token, explicit confirmation, owner/repo metadata, and file changes, the app returns a mocked demo response.
- Generated patch drafts require human review before use.
- The public demo should not receive sensitive repositories, private tokens, or secrets.

These limitations are deliberate for the first portfolio version. They keep the system honest, demoable, and explainable in interviews.
