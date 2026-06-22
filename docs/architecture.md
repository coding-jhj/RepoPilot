# Architecture

RepoPilot is split into a FastAPI backend and a Next.js frontend.

The backend owns repository ingestion, indexing, retrieval, agent orchestration, patch validation, and GitHub integration. The frontend presents the workflow as an IDE-like review surface with import controls, analysis results, evidence, timeline, and diff review.

## Backend Boundaries

- `RepoService`: validates GitHub URLs, creates stable repo IDs, owns safe workspace paths, clones public repositories, and creates a fallback demo workspace when clone fails.
- `IndexingService`: walks a repo with file-count and file-size limits, parses supported files, chunks content, and writes chunks to the retrieval store.
- `CodeParser`: dispatches Python parsing to AST and JS/TS/TSX parsing to tree-sitter with regex fallback.
- `LocalQdrantLikeStore`: in-memory stand-in behind the vector-store boundary.
- `RepoPilotAgent`: runs deterministic agent nodes over retrieved evidence.
- `PatchService`: drafts unified diffs and validates touched paths against approved evidence paths.
- `GitHubService`: keeps the public demo safe by returning mocked PRs without a token, and opens real pull requests only when a token, file changes, and explicit confirmation are supplied.
- `GitHubPRService`: executes the REST flow for real PR creation: resolve base SHA, create branch, upsert files, and open PR.

## Frontend Boundaries

- `RepoInput`: accepts repository URL and branch, then imports and indexes the repo.
- `AnalysisDashboard`: shows findings with file/line evidence.
- `AgentTimeline`: shows graph execution steps.
- `DiffViewer`: shows patch validity, validation messages, and diff content.
- `CodeViewer` / `FileTree`: reserved review surfaces for compact repository context.

The UI is intentionally dense and workflow-oriented because this is a developer tool, not a marketing page. The first screen should communicate three guarantees: free-first execution, evidence-required findings, and approval-gated patching.
