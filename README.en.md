# RepoPilot

> Free deployed GitHub repository analysis agent

Live Demo: [https://jeonghwanju-repopilot.hf.space](https://jeonghwanju-repopilot.hf.space/)

RepoPilot is a free web demo that imports a public GitHub repository, indexes source files, runs local analysis, and shows evidence-backed findings and patch drafts. It does not require OpenAI, Claude, paid inference APIs, hosted databases, or paid vector databases. The default path is deterministic static analysis; turning on **deep analysis** with a free Gemini key (BYO-key) adds LLM reasoning on top of the same evidence.

For a detailed walkthrough of the project structure and code, see the rendered [RepoPilot Code Guide](https://coding-jhj.github.io/RepoPilot/repopilot-code-guide.html).

## What Works Today

- import a public GitHub repository URL
- clone into a temporary workspace
- index Python, JavaScript, TypeScript, and Markdown files
- extract Python classes/functions/imports with AST
- extract JS/TS/TSX symbols/imports with tree-sitter (regex fallback)
- retrieve relevant code chunks locally (keyword by default, opt-in MiniLM embedding semantic search via `REPOPILOT_USE_EMBEDDINGS=true`)
- show an agent timeline
- show findings with file/line evidence
- run free static-analysis rules
  - hardcoded secret candidates
  - bare `except:`
  - `eval()` usage
- **deep analysis (optional)**: with a free Gemini key, add LLM-reasoned findings + summary on top of the retrieved evidence (default `gemini-3.5-flash`; static-only without a key)
- generate patch drafts for selected evidence paths
- validate patch scope
- create real GitHub Pull Requests (opt-in token: branch -> commit -> open PR; mock without a token)
- serve the static Next.js UI from FastAPI
- deploy for free on Hugging Face Spaces CPU Basic
- **two eval harnesses** (evals over vibes): retrieval (recall@k/MRR) and bug-finding (precision/recall/F1), pinning a deterministic baseline

## What Does Not Work Yet

- a server-side default LLM (deep analysis needs the user's own free Gemini key)
- automatic unified-diff application (real PRs take explicit file contents)
- full analysis of large repositories
- persistent user history or storage

This is not a Devin clone. It is a free-first MVP that shows how much of a practical software-engineering agent can be built without paid services.

## Flow

```txt
GitHub URL
  -> repo clone
  -> file indexing
  -> local code chunk retrieval
  -> agent workflow
  -> evidence-backed findings
  -> patch draft
  -> scope validation
```

## Stack

| Area | Stack |
| --- | --- |
| Backend | FastAPI, Pydantic |
| Frontend | Next.js static export, React, TypeScript |
| Deployment | Hugging Face Spaces Docker |
| Code Analysis | Python AST, JS/TS/TSX tree-sitter (regex fallback) |
| Retrieval | In-memory chunk search (keyword + opt-in MiniLM embedding semantic search) |
| Static Rules | hardcoded secret, bare except, eval detection |
| GitHub | real PR creation (opt-in token, httpx REST) |
| LLM | Not required by default (deep analysis is BYO Gemini key) |
| Eval | retrieval (recall@k/MRR) and bug-finding (precision/recall/F1) harnesses |
| Tests | pytest, Next.js build |

## Local Run

Backend:

```bash
cd apps/api
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Docker:

```bash
docker build -t repopilot .
docker run --rm -p 7860:7860 repopilot
```

## Verification

```bash
cd apps/api
python -m pytest tests
```

```bash
cd apps/web
npm install
npm run build
```

Current verification:

- backend tests: `33 passed, 2 skipped`
- tree-sitter JS/TS parsing + real PR flow regression tests included
- eval harness unit tests (dataset split assertion, deterministic baseline) included
- Next.js static export build passed
- Hugging Face Space `/health` responded successfully
- Hugging Face Space web page returned HTTP `200`

## Evaluation

"Evals over vibes" — core features are checked with numbers, not feelings. Only the
deterministic offline baseline is pinned as fact; live-LLM results are not reproducible,
so they are reported as opt-in sample runs.

```bash
cd apps/api
REPOPILOT_USE_EMBEDDINGS=true python -m eval.retrieval_run
# keyword-only recall@3=0.50 / semantic recall@3=1.00

python -m eval.bug_run
# static baseline  precision=1.00 recall=0.38 f1=0.55  (tp=3 fp=0 fn=5, n=12)
# set REPOPILOT_GEMINI_API_KEY to add the deep (Gemini) arm — a sample run, not pinned
```

## Limitations

The free deployment has CPU, disk, network, and runtime limits. RepoPilot is optimized for small public repositories. Default findings are deterministic static-rule results; enabling deep analysis (BYO Gemini key) adds LLM-reasoned findings on top of the same evidence.
