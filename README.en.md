# RepoPilot

> Free deployed GitHub repository analysis agent

Live Demo: [https://jeonghwanju-repopilot.hf.space](https://jeonghwanju-repopilot.hf.space/)

RepoPilot is a free web demo that imports a public GitHub repository, indexes source files, runs local analysis, and shows evidence-backed findings and patch drafts. It does not require OpenAI, Claude, paid inference APIs, hosted databases, or paid vector databases.

For a detailed walkthrough of the project structure and code, see the rendered [RepoPilot Code Guide](https://coding-jhj.github.io/RepoPilot/repopilot-code-guide.html).

## What Works Today

- import a public GitHub repository URL
- clone into a temporary workspace
- index Python, JavaScript, TypeScript, and Markdown files
- extract Python classes/functions/imports with AST
- extract lightweight JS/TS symbols/imports
- retrieve relevant code chunks locally
- show an agent timeline
- show findings with file/line evidence
- run free static-analysis rules
  - hardcoded secret candidates
  - bare `except:`
  - `eval()` usage
- generate patch drafts for selected evidence paths
- validate patch scope
- serve the static Next.js UI from FastAPI
- deploy for free on Hugging Face Spaces CPU Basic

## What Does Not Work Yet

- deep LLM-based bug reasoning
- real GitHub Pull Request creation
- applying patches directly to the source repository
- full analysis of large repositories
- tree-sitter precision parsing
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
| Code Analysis | Python AST, JS/TS regex scaffold |
| Retrieval | In-memory chunk search |
| Static Rules | hardcoded secret, bare except, eval detection |
| LLM | Not required by default |
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

- backend tests: `17 passed`
- Next.js static export build passed
- Hugging Face Space `/health` responded successfully
- Hugging Face Space web page returned HTTP `200`

## Limitations

The free deployment has CPU, disk, network, and runtime limits. RepoPilot is optimized for small public repositories. Current findings are deterministic static-rule results, not LLM reasoning.
