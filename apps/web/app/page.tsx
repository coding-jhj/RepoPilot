"use client";

import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Check,
  FileDiff,
  GitPullRequest,
  KeyRound,
  ListChecks,
  Loader2,
  Search,
  Sparkles,
  Wand2,
} from "lucide-react";
import { useState } from "react";
import { createPatch, importRepo, indexRepo, runAnalysis } from "../lib/api";
import type {
  AnalysisResponse,
  AnalysisTask,
  PatchResponse,
  RepoImportResponse,
} from "../lib/types";

const EXAMPLE_REPO = "https://github.com/coding-jhj/AI_AGENT";
const EXAMPLE_BRANCH = "main";
const DEFAULT_MODEL = "gemini-3.5-flash";

const TASKS: { value: AnalysisTask; label: string; hint: string }[] = [
  { value: "overview", label: "Overview", hint: "What the repo is and how it is organized" },
  { value: "architecture", label: "Architecture map", hint: "Modules, layers, and how they connect" },
  { value: "bug_scan", label: "Bug & risk scan", hint: "Static rules + optional LLM reasoning" },
  { value: "refactor_plan", label: "Refactor plan", hint: "Concrete, scoped improvement ideas" },
  { value: "test_generation", label: "Test suggestions", hint: "Where coverage is missing" },
  { value: "patch_generation", label: "Patch generation", hint: "Draft a scoped fix to review" },
];

const STEPS = [
  { icon: Search, title: "Import & index", body: "Clone a public repo, parse Python & JS/TS with AST + tree-sitter." },
  { icon: ListChecks, title: "Analyze", body: "Run free static rules, or add Gemini for grounded LLM reasoning." },
  { icon: FileDiff, title: "Evidence findings", body: "Every finding cites the exact file and line range it came from." },
  { icon: GitPullRequest, title: "Patch & PR", body: "Generate a scope-validated patch draft, optionally open a real PR." },
];

const SEVERITY_RANK: Record<string, number> = { high: 3, medium: 2, low: 1, info: 0 };

export default function Home() {
  const [repo, setRepo] = useState<RepoImportResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [patch, setPatch] = useState<PatchResponse | null>(null);
  const [url, setUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [task, setTask] = useState<AnalysisTask>("bug_scan");
  const [deep, setDeep] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [busy, setBusy] = useState<"" | "import" | "analyze" | "patch">("");
  const [error, setError] = useState<string | null>(null);

  async function handleImport() {
    if (!url.trim()) return;
    setBusy("import");
    setError(null);
    setAnalysis(null);
    setPatch(null);
    try {
      const imported = await importRepo(url.trim(), branch.trim() || "main");
      await indexRepo(imported.repo_id);
      setRepo(imported);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Import failed");
    } finally {
      setBusy("");
    }
  }

  async function handleAnalysis() {
    if (!repo) return;
    setBusy("analyze");
    setError(null);
    try {
      setAnalysis(await runAnalysis(repo.repo_id, task, deep, deep ? apiKey : undefined, model));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Analysis failed");
    } finally {
      setBusy("");
    }
  }

  async function handlePatch() {
    const evidence = analysis?.findings[0]?.evidence[0];
    if (!repo || !analysis || !evidence) return;
    setBusy("patch");
    setError(null);
    try {
      setPatch(
        await createPatch(
          repo.repo_id,
          `Improve the selected finding: ${analysis.findings[0].title}`,
          [evidence.path]
        )
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Patch failed");
    } finally {
      setBusy("");
    }
  }

  function useExample() {
    setUrl(EXAMPLE_REPO);
    setBranch(EXAMPLE_BRANCH);
  }

  const findings = analysis
    ? [...analysis.findings].sort(
        (a, b) => (SEVERITY_RANK[b.severity] ?? 0) - (SEVERITY_RANK[a.severity] ?? 0)
      )
    : [];

  return (
    <main className="page">
      <header className="hero">
        <div className="brand">
          <span className="brand-mark"><Bot size={22} /></span>
          <span className="brand-name">RepoPilot</span>
        </div>
        <h1 className="hero-title">
          Understand any GitHub repo — with <span className="grad">evidence</span>, not vibes.
        </h1>
        <p className="hero-lead">
          Paste a public repository. RepoPilot clones and indexes it, then returns findings tied to
          exact file &amp; line numbers, drafts scope-validated patches, and can open a real pull
          request. Free-first — no paid API required.
        </p>
        <div className="badges">
          <span className="badge"><Check size={13} /> Free-first</span>
          <span className="badge"><Check size={13} /> Evidence-backed</span>
          <span className="badge"><Check size={13} /> Real PRs</span>
          <span className="badge accent"><Sparkles size={13} /> Optional Gemini deep analysis</span>
        </div>
      </header>

      <section className="steps">
        {STEPS.map((step, index) => (
          <div className="step" key={step.title}>
            <div className="step-top">
              <span className="step-icon"><step.icon size={18} /></span>
              <span className="step-num">{index + 1}</span>
            </div>
            <h3>{step.title}</h3>
            <p>{step.body}</p>
          </div>
        ))}
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Try it</h2>
          <button className="link-btn" onClick={useExample} type="button">
            Use example repo <ArrowRight size={14} />
          </button>
        </div>

        <div className="repo-row">
          <label className="field grow">
            <span>Public GitHub repository URL</span>
            <input
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://github.com/owner/name"
              spellCheck={false}
            />
          </label>
          <label className="field branch">
            <span>Branch</span>
            <input value={branch} onChange={(event) => setBranch(event.target.value)} spellCheck={false} />
          </label>
          <button className="btn primary" onClick={handleImport} disabled={busy !== "" || !url.trim()}>
            {busy === "import" ? <Loader2 className="spin" size={16} /> : <Search size={16} />}
            Import &amp; Index
          </button>
        </div>

        {repo && (
          <div className="repo-chip">
            <Check size={14} /> Indexed <strong>{repo.owner}/{repo.name}</strong>
            <span className="muted">{repo.repo_id}</span>
          </div>
        )}

        <div className="controls">
          <label className="field grow">
            <span>Analysis task</span>
            <select value={task} onChange={(event) => setTask(event.target.value as AnalysisTask)}>
              {TASKS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label} — {item.hint}
                </option>
              ))}
            </select>
          </label>
          <label className="switch">
            <input type="checkbox" checked={deep} onChange={(event) => setDeep(event.target.checked)} />
            <span className="track" aria-hidden />
            <span className="switch-label"><Sparkles size={14} /> Deep analysis (Gemini)</span>
          </label>
        </div>

        {deep && (
          <div className="gemini">
            <div className="gemini-head">
              <KeyRound size={15} /> Bring your own free Gemini key — runs LLM reasoning on the evidence.
            </div>
            <div className="gemini-row">
              <input
                type="password"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="AIza... (free key from aistudio.google.com)"
                spellCheck={false}
              />
              <input
                className="model"
                value={model}
                onChange={(event) => setModel(event.target.value)}
                spellCheck={false}
              />
            </div>
            <a className="gemini-hint" href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer">
              Get a free key →
            </a>
          </div>
        )}

        <div className="actions">
          <button className="btn primary" onClick={handleAnalysis} disabled={!repo || busy !== ""}>
            {busy === "analyze" ? <Loader2 className="spin" size={16} /> : <Wand2 size={16} />}
            Run analysis
          </button>
          <button
            className="btn"
            onClick={handlePatch}
            disabled={!analysis || !analysis.findings[0]?.evidence[0] || busy !== ""}
          >
            {busy === "patch" ? <Loader2 className="spin" size={16} /> : <FileDiff size={16} />}
            Generate patch
          </button>
        </div>

        {error && (
          <div className="error"><AlertTriangle size={15} /> {error}</div>
        )}
      </section>

      {analysis && (
        <section className="results">
          {analysis.summary && (
            <div className="card summary">
              <h3><Sparkles size={15} /> Summary</h3>
              <p>{analysis.summary}</p>
            </div>
          )}

          <div className="result-grid">
            <div className="card">
              <h3><ListChecks size={15} /> Findings <span className="count">{findings.length}</span></h3>
              {findings.length === 0 && <p className="muted">No findings for this task.</p>}
              <ul className="findings">
                {findings.map((finding, index) => (
                  <li key={`${finding.title}-${index}`}>
                    <div className="finding-head">
                      <span className={`sev sev-${finding.severity}`}>{finding.severity}</span>
                      <strong>{finding.title}</strong>
                    </div>
                    <p>{finding.summary}</p>
                    {finding.evidence.map((evidence, evidenceIndex) => (
                      <code className="evidence" key={evidenceIndex}>
                        {evidence.path}:{evidence.start_line}-{evidence.end_line}
                      </code>
                    ))}
                  </li>
                ))}
              </ul>
            </div>

            <div className="card">
              <h3><Bot size={15} /> Agent timeline</h3>
              <ol className="timeline">
                {analysis.timeline.map((step, index) => (
                  <li key={index}>
                    <span className="node">{step.node}</span>
                    <span>{step.summary}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          {patch && (
            <div className="card">
              <h3>
                <FileDiff size={15} /> Patch draft
                <span className={patch.valid ? "pill ok" : "pill bad"}>
                  {patch.valid ? "scope-validated" : "rejected"}
                </span>
              </h3>
              {patch.messages.length > 0 && (
                <p className="muted">{patch.messages.join(" · ")}</p>
              )}
              <pre className="diff">{patch.diff}</pre>
            </div>
          )}
        </section>
      )}

      <footer className="foot">
        <span>RepoPilot · FastAPI + Next.js · deployed free on Hugging Face Spaces</span>
        <a href="https://github.com/coding-jhj/RepoPilot" target="_blank" rel="noreferrer">GitHub →</a>
      </footer>
    </main>
  );
}
