import type { AnalysisResponse, AnalysisTask, PatchResponse, RepoImportResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init.headers ?? {})
    }
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function importRepo(url: string, branch: string): Promise<RepoImportResponse> {
  return request<RepoImportResponse>("/repos/import", {
    method: "POST",
    body: JSON.stringify({ url, branch })
  });
}

export async function indexRepo(repoId: string): Promise<{ files_indexed: number; chunks_indexed: number }> {
  return request(`/repos/${repoId}/index`, { method: "POST", body: "{}" });
}

export async function runAnalysis(repoId: string, task: AnalysisTask, deep: boolean): Promise<AnalysisResponse> {
  return request<AnalysisResponse>("/analyses", {
    method: "POST",
    body: JSON.stringify({ repo_id: repoId, task, deep })
  });
}

export async function createPatch(repoId: string, instruction: string, approvedPaths: string[]): Promise<PatchResponse> {
  return request<PatchResponse>("/patches", {
    method: "POST",
    body: JSON.stringify({
      repo_id: repoId,
      instruction,
      approved_paths: approvedPaths
    })
  });
}
