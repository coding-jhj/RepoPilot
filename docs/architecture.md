# Architecture

RepoPilot is split into a FastAPI backend and a Next.js frontend.

The backend owns repository ingestion, indexing, retrieval, agent orchestration, patch validation, and GitHub integration. The frontend presents the workflow as an IDE-like review surface with import controls, analysis results, evidence, timeline, and diff review.

## Backend Boundaries

- `RepoService`: validates GitHub URLs, creates stable repo IDs, owns safe workspace paths, and clones public repositories.
- `IndexingService`: walks a repo with hard limits, parses supported files, chunks content, and writes chunks to the retrieval store.
- `CodeParser`: extracts lightweight symbols and imports from Python and JS/TS.
- `InMemoryRetriever` / `LocalQdrantLikeStore`: local stand-in for the Qdrant boundary.
- `RepoPilotAgent`: runs deterministic agent nodes over retrieved evidence.
- `PatchService`: drafts and validates unified diffs against approved paths.
- `GitHubService`: currently mocked; later creates branches, commits, pushes, and PRs.

## Frontend Boundaries

- `RepoInput`: imports and indexes a repo.
- `AnalysisDashboard`: shows findings and file/line evidence.
- `AgentTimeline`: shows graph execution steps.
- `DiffViewer`: shows patch validity and diff content.

The UI is intentionally dense and workflow-oriented because this is a developer tool, not a marketing page.
