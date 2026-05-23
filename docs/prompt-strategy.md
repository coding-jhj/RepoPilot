# Prompt Strategy

RepoPilot is free-first, so prompts are not part of the required core path. The default agent should rely on local repository indexing, retrieval, deterministic static rules, and patch validation.

When an optional LLM provider is enabled, RepoPilot should use small, scoped prompts. The model should receive:

- task intent
- retrieved chunks
- file path and line metadata
- allowed output format
- explicit instruction to avoid claims without evidence

Recommended routing:

- overview: cheaper model
- architecture: stronger model when repo structure is complex
- bug scan: stronger model
- test generation: stronger model
- patch generation: strongest configured coding model
- reviewer: cheaper model plus deterministic patch checks

The current `FakeLLMProvider` exists so tests and UI development do not consume API budget. Paid providers must remain optional.
