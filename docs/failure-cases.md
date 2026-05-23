# Failure Cases

RepoPilot is not expected to solve every software engineering task.

Known limitations:

- Large repositories may exceed indexing and retrieval limits.
- Small local models are likely to underperform on bug finding and patch generation.
- Static JS/TS parsing is regex-based in the scaffold and should be replaced with tree-sitter.
- The current Qdrant integration is represented by an in-memory compatible boundary.
- GitHub PR creation is mocked until token handling and branch push flow are implemented.
- Generated patches require human review before use.

These limitations are deliberate for the first portfolio version. They keep the system honest, demoable, and explainable in interviews.
