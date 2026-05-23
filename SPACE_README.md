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

Free deployed GitHub repository analysis agent.

RepoPilot imports a public GitHub repository, indexes source files, runs local static-analysis rules, and shows evidence-backed findings and patch drafts.

This Space does not use paid LLM APIs, paid inference APIs, hosted databases, cloud vector databases, or GPU hardware.

Current capabilities:

- public GitHub repository import
- temporary workspace clone
- Python, JavaScript, TypeScript, and Markdown indexing
- local code chunk retrieval
- static rules for hardcoded secret candidates, bare `except:`, and `eval()`
- evidence-backed findings with file/line references
- scoped patch draft generation
- patch scope validation

Limitations:

- no LLM reasoning
- no real GitHub PR creation
- no persistent user history
- optimized for small public repositories
