# Cost Control

RepoPilot assumes cloud LLMs are required for high-quality code reasoning, so it controls cost by limiting how often and how much context reaches the model.

Implemented controls:

- public HTTPS repo URL validation
- safe isolated workspaces
- max indexed file count
- max indexed file size
- retrieval before agent analysis
- shallow analysis by default
- explicit deep analysis toggle
- patch generation as a separate user action
- PR creation blocked unless confirmed

Planned controls:

- embedding cache by file hash
- summary cache by commit SHA
- per-step token budgets
- provider-specific model routing
- cheap model for classification, strong model for patch generation
