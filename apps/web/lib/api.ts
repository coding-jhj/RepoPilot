import type {
  AnalysisResponse,
  AnalysisTask,
  PatchResponse,
  PullRequestResult,
  RepoImportResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

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

export async function runAnalysis(
  repoId: string,
  task: AnalysisTask,
  deep: boolean,
  apiKey?: string,
  model?: string
): Promise<AnalysisResponse> {
  return request<AnalysisResponse>("/analyses", {
    method: "POST",
    body: JSON.stringify({
      repo_id: repoId,
      task,
      deep,
      api_key: apiKey || null,
      model: model || null
    })
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

export async function createPullRequestFromPatch(input: {
  repoId: string;
  owner: string;
  repo: string;
  path: string;
  diff: string;
  title: string;
  body: string;
  token: string;
  confirmed: boolean;
  base?: string;
}): Promise<PullRequestResult> {
  return request<PullRequestResult>("/github/pr-from-patch", {
    method: "POST",
    body: JSON.stringify({
      repo_id: input.repoId,
      owner: input.owner,
      repo: input.repo,
      path: input.path,
      diff: input.diff,
      title: input.title,
      body: input.body,
      token: input.token,
      confirmed: input.confirmed,
      base: input.base || "main"
    })
  });
}
