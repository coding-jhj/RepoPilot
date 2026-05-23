export function CodeViewer() {
  return (
    <section className="panel compact">
      <h2>Cost Controls</h2>
      <ul>
        <li>Scoped retrieval before LLM calls</li>
        <li>Deep analysis requires confirmation</li>
        <li>Patch generation is approval-gated</li>
        <li>Cloud LLM primary, Ollama fallback optional</li>
      </ul>
    </section>
  );
}
