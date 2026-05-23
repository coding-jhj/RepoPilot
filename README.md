# RepoPilot

> 무료로 실행 가능한 local-first AI Software Engineer Agent

[English README](README.en.md)

RepoPilot은 GitHub 저장소를 분석하고, 근거 기반 코드 리뷰와 패치 초안을 생성하는 개발자용 AI Agent입니다. 핵심 방향은 **돈이 들지 않는 무료 실행**입니다.

OpenAI/Claude 같은 유료 API 없이도 저장소를 가져오고, 코드를 인덱싱하고, 정적 분석 규칙으로 위험 후보를 찾고, 파일/라인 근거가 있는 finding과 patch draft를 보여주는 구조입니다. 유료 LLM은 나중에 품질을 높이기 위한 선택 옵션일 뿐, 기본 실행 조건이 아닙니다.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![Agent](https://img.shields.io/badge/Agent-Free--first-1c6dd0?style=flat-square)
![Status](https://img.shields.io/badge/Status-MVP%20Scaffold-f59e0b?style=flat-square)

## 왜 만들었나

요즘 개발 조직은 단순히 LLM API를 호출하는 개발자보다, AI를 이용해 개발 생산성을 실제로 높일 수 있는 엔지니어를 더 중요하게 봅니다.

RepoPilot은 그 방향을 보여주기 위해 다음 요소를 담았습니다.

- GitHub 저장소 가져오기와 인덱싱
- 정적 코드 분석
- local retrieval 기반 코드 검색
- multi-step agent workflow
- 파일/라인 근거가 있는 분석 결과
- patch diff 생성과 scope 검증
- 비용 없는 static rule 기반 분석
- API 비용 없이 개발 가능한 fake provider

## 현재 구현 수준

현재는 “동작하는 1차 MVP 수직 슬라이스” 수준입니다.

- FastAPI 백엔드
- Next.js 대시보드
- public GitHub repo import API
- repo indexing API
- Python, JavaScript, TypeScript, Markdown 파일 인덱싱
- Python AST 기반 symbol/import 추출
- JS/TS regex 기반 parsing scaffold
- in-memory retrieval layer
- LangGraph 스타일 agent node graph
- hardcoded secret, bare except, eval 같은 무료 정적 분석 규칙
- evidence 기반 finding
- patch draft 생성
- patch scope validation
- mock PR workflow
- 테스트와 문서

실제 고성능 분석을 위한 OpenAI/Claude 호출은 선택 옵션입니다. 기본 목표는 돈이 들지 않는 local-first agent이며, Qdrant 저장과 tree-sitter parsing은 무료 품질을 높이는 다음 단계입니다.

## 데모 흐름

```txt
GitHub 저장소 URL 입력
  -> 안전한 public repo import
  -> 코드 인덱싱
  -> symbol/import/file metadata 추출
  -> 파일/라인 근거 기반 local retrieval
  -> agent timeline 실행
  -> static rule 기반 grounded finding 생성
  -> scoped patch draft 생성
  -> PR workflow boundary
```

## Architecture

```mermaid
flowchart TD
    A["GitHub Repository URL"] --> B["RepoService"]
    B --> C["Isolated Workspace"]
    C --> D["IndexingService"]
    D --> E["CodeParser"]
    D --> F["CodeChunker"]
    F --> G["Retriever / Qdrant Boundary"]
    G --> H["RepoPilotAgent"]
    H --> I["Evidence-backed Findings"]
    I --> J["PatchService"]
    J --> K["Diff Review UI"]
    K --> L["GitHub PR Boundary"]
```

## Agent Workflow

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

핵심 규칙:

> RepoPilot은 retrieved code evidence 없이 파일 단위 문제를 주장하지 않는다.

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| Backend | FastAPI, Pydantic |
| Frontend | Next.js, React, TypeScript |
| Agent Boundary | LangGraph-style stateful node graph |
| Retrieval | In-memory MVP, Qdrant-ready boundary |
| Code Analysis | Python AST, JS/TS regex scaffold, tree-sitter 예정 |
| Static Rules | hardcoded secret, bare except, eval 탐지 |
| LLM | 기본 불필요, 이후 선택적 OpenAI/Claude adapter |
| DevOps | Docker Compose |
| Testing | pytest, Next.js build validation |

## 비용 전략

RepoPilot은 기본적으로 돈이 들지 않는 구조를 우선합니다.

- local/test용 fake provider
- LLM 없이 동작하는 static rule analyzer
- local retrieval 기반 evidence 수집
- 기본은 shallow analysis
- deep analysis는 명시적 toggle
- indexing file count limit
- file size limit
- patch 생성은 별도 action
- PR 생성은 confirmation 필요

유료 LLM은 optional upgrade입니다. 돈 걱정 없이 보여줄 수 있는 기본 데모는 정적 분석, retrieval, patch validation 중심으로 동작합니다.

## 실행 방법

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

브라우저에서 접속:

```txt
http://localhost:3000
```

Docker:

```bash
docker compose up
```

## 테스트

Backend tests:

```bash
cd apps/api
python -m pytest tests
```

Frontend build:

```bash
cd apps/web
npm install
npm run build
```

현재 MVP 검증 결과:

- backend tests: `12 passed`
- Python compile check 통과
- Next.js production build 통과
- API health endpoint: `ok`
- web dev server: HTTP `200`

## 환경 변수

기본 무료 개발 모드:

```txt
REPOPILOT_LLM_PROVIDER=fake
```

선택적 고품질 분석 모드:

```txt
REPOPILOT_LLM_PROVIDER=openai
REPOPILOT_OPENAI_API_KEY=...
```

또는:

```txt
REPOPILOT_LLM_PROVIDER=anthropic
REPOPILOT_ANTHROPIC_API_KEY=...
```

## Roadmap

- [ ] 정적 분석 rule set 확장
- [ ] Qdrant 기반 local vector retrieval 추가
- [ ] JS/TS regex parsing을 tree-sitter로 교체
- [ ] commit SHA / file hash 기반 cache 추가
- [ ] dependency graph 기반 위험 탐지 추가
- [ ] 선택한 finding에 대한 test generation 구현
- [ ] isolated branch에서 patch apply
- [ ] 실제 GitHub Pull Request 생성
- [ ] 선택적 OpenAI/Claude adapter 추가
- [ ] demo GIF와 benchmark case 추가

## 한계

RepoPilot은 의도적으로 scope를 제한한 프로젝트입니다. 현재 목표는 “유료 API로 대형 production system을 완전 자동으로 고치는 Agent”가 아니라, 무료로 실행되면서 코드베이스 이해, 근거 기반 리뷰, 테스트 제안, 작은 patch draft 생성을 보여주는 AI Software Engineer Agent입니다.

자세한 한계와 실패 케이스는 [docs/failure-cases.md](docs/failure-cases.md)에 정리했습니다.
