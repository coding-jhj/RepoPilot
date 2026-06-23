---
title: RepoPilot
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# RepoPilot

Free-first deployed GitHub repository analysis agent.

RepoPilot imports a public GitHub repository, indexes source files, runs local
analysis, and shows evidence-backed findings and patch drafts. It uses no paid
LLM APIs, paid inference APIs, hosted databases, cloud vector databases, or GPU
hardware.

The default path is deterministic static analysis. Toggle **deep analysis** and
bring a free Gemini key (entered in the browser, never stored) to add
LLM-reasoned findings on top of the same evidence.

## Current capabilities

- public GitHub repository import + temporary workspace clone
- Python / JavaScript / TypeScript / Markdown indexing (AST + tree-sitter)
- local code-chunk retrieval with file/line evidence
- free static rules: hardcoded secret candidates, bare `except:`, `eval()`
- evidence-backed findings
- **deep analysis (optional, bring your own Gemini key)**: LLM-reasoned findings + summary
- scope-validated patch drafts — a review scaffold by default; with deep analysis
  the writer can draft an actual fix diff, checked for clean appliability and scope
- four eval harnesses pinning deterministic baselines (retrieval, bug-finding,
  patch, test-scaffold)

## Limitations

- no server-side default LLM — deep analysis needs your own free Gemini key
- embeddings are off on this free deployment (keyword retrieval only)
- real GitHub PR creation exists in the API but is not wired into this demo UI yet
- automatic unified-diff application is not implemented
- optimized for small public repositories; no persistent user history
