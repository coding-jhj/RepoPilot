# Agent Flow

The current agent graph is implemented as sequential nodes with a LangGraph-compatible state shape.

```txt
Planner
  -> RepoReader
  -> CodeSearcher
  -> ArchitectureAnalyzer
  -> BugDetector
  -> TestWriter
  -> PatchWriter
  -> Reviewer
```

Every finding must cite retrieved evidence. This is the core quality rule: RepoPilot should not claim a file-level issue without a file path and line range from retrieval.

Future LangGraph integration can replace the simple runner in `RepoPilotAgent` without changing API response shapes.
