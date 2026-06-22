"use client";

import { GitBranch, Github } from "lucide-react";
import { FormEvent, useState } from "react";

type Props = {
  busy: boolean;
  onSubmit: (url: string, branch: string) => Promise<void>;
};

export function RepoInput({ busy, onSubmit }: Props) {
  const [url, setUrl] = useState("https://github.com/coding-jhj/RepoPilot");
  const [branch, setBranch] = useState("main");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await onSubmit(url, branch);
  }

  return (
    <form className="toolbar" onSubmit={handleSubmit}>
      <label>
        <span><Github size={16} /> Repository</span>
        <input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://github.com/owner/repo" />
      </label>
      <label className="branch">
        <span><GitBranch size={16} /> Branch</span>
        <input value={branch} onChange={(event) => setBranch(event.target.value)} placeholder="main" />
      </label>
      <button disabled={busy}>{busy ? "Importing" : "Import & Index"}</button>
    </form>
  );
}
