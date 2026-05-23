"use client";

import { Bot, FileDiff, SearchCode } from "lucide-react";
import { useState } from "react";
import { AnalysisDashboard } from "../components/analysis-dashboard";
import { CodeViewer } from "../components/code-viewer";
import { DiffViewer } from "../components/diff-viewer";
import { FileTree } from "../components/file-tree";
import { RepoInput } from "../components/repo-input";
import { createPatch, importRepo, indexRepo, runAnalysis } from "../lib/api";
import type { AnalysisResponse, AnalysisTask, PatchResponse, RepoImportResponse } from "../lib/types";

const TASKS: AnalysisTask[] = ["overview", "architecture", "bug_scan", "test_generation", "patch_generation"];

export default function Home() {
  const [repo, setRepo] = useState<RepoImportResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [patch, setPatch] = useState<PatchResponse | null>(null);
  const [task, setTask] = useState<AnalysisTask>("overview");
  const [deep, setDeep] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleImport(url: string, branch: string) {
    setBusy(true);
    setError(null);
    try {
      const imported = await importRepo(url, branch);
      await indexRepo(imported.repo_id);
      setRepo(imported);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Import failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleAnalysis() {
    if (!repo) return;
    setBusy(true);
    setError(null);
    try {
      setAnalysis(await runAnalysis(repo.repo_id, task, deep));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  }

  async function handlePatch() {
    if (!repo || !analysis?.findings[0]?.evidence[0]) return;
    const evidence = analysis.findings[0].evidence[0];
    setBusy(true);
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
      setBusy(false);
    }
  }

  return (
    <main>
      <header className="topbar">
        <div>
          <h1>RepoPilot</h1>
          <p>Repo-aware AI software engineering agent for scoped analysis, tests, patches, and PR review.</p>
        </div>
        <div className="badges">
          <span>Cloud LLM primary</span>
          <span>Evidence required</span>
          <span>Approval-gated patches</span>
        </div>
      </header>

      <RepoInput busy={busy} onSubmit={handleImport} />
      {error && <div className="error">{error}</div>}

      <section className="controls">
        <label>
          <span><SearchCode size={16} /> Task</span>
          <select value={task} onChange={(event) => setTask(event.target.value as AnalysisTask)}>
            {TASKS.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="toggle">
          <input type="checkbox" checked={deep} onChange={(event) => setDeep(event.target.checked)} />
          Deep analysis
        </label>
        <button disabled={!repo || busy} onClick={handleAnalysis}><Bot size={16} /> Run Analysis</button>
        <button disabled={!analysis || busy} onClick={handlePatch}><FileDiff size={16} /> Generate Patch</button>
      </section>

      {repo && (
        <section className="repo">
          <strong>{repo.owner}/{repo.name}</strong>
          <span>{repo.repo_id}</span>
        </section>
      )}

      <div className="grid">
        <AnalysisDashboard analysis={analysis} />
        <DiffViewer patch={patch} />
        <FileTree />
        <CodeViewer />
      </div>
    </main>
  );
}
