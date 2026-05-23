import type { PatchResponse } from "../lib/types";

export function DiffViewer({ patch }: { patch: PatchResponse | null }) {
  return (
    <section className="panel diff">
      <header>
        <h2>Patch Review</h2>
        {patch && <span className={patch.valid ? "valid" : "invalid"}>{patch.valid ? "valid" : "blocked"}</span>}
      </header>
      {patch ? (
        <>
          <div className="messages">
            {patch.messages.map((message) => (
              <span key={message}>{message}</span>
            ))}
          </div>
          <pre>{patch.diff}</pre>
        </>
      ) : (
        <div className="empty">Generate a patch after reviewing evidence.</div>
      )}
    </section>
  );
}
