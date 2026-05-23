# Free-First Cost Control

RepoPilot's default path must not require paid APIs. The project should remain useful with local static analysis, repository indexing, retrieval, deterministic rules, and patch validation.

Cloud LLM providers can be added later as optional quality upgrades, but they must not be required for the core demo.

Implemented controls:

- public HTTPS repo URL validation
- safe isolated workspaces
- max indexed file count
- max indexed file size
- local retrieval before agent analysis
- free static-analysis rules for common bug/smell patterns
- shallow analysis by default
- explicit deep analysis toggle
- patch generation as a separate user action
- PR creation blocked unless confirmed

Planned controls:

- embedding cache by file hash
- summary cache by commit SHA
- tree-sitter rules for richer local analysis
- local dependency graph risk checks
- optional provider-specific model routing
- per-step token budgets only when a paid provider is explicitly enabled
