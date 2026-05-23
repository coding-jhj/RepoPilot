export type AnalysisTask =
  | "overview"
  | "architecture"
  | "bug_scan"
  | "refactor_plan"
  | "test_generation"
  | "patch_generation";

export type Evidence = {
  path: string;
  start_line: number;
  end_line: number;
};

export type Finding = {
  title: string;
  summary: string;
  severity: string;
  evidence: Evidence[];
};

export type AgentStep = {
  node: string;
  summary: string;
};

export type AnalysisResponse = {
  status: string;
  summary: string;
  findings: Finding[];
  timeline: AgentStep[];
};

export type RepoImportResponse = {
  repo_id: string;
  owner: string;
  name: string;
  clone_url: string;
  status: string;
};

export type PatchResponse = {
  diff: string;
  valid: boolean;
  touched_paths: string[];
  messages: string[];
};
