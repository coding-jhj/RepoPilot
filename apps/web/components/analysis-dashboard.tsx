import type { AnalysisResponse } from "../lib/types";
import { AgentTimeline } from "./agent-timeline";

export function AnalysisDashboard({ analysis }: { analysis: AnalysisResponse | null }) {
  if (!analysis) {
    return <section className="empty">Run an analysis to see grounded findings.</section>;
  }

  return (
    <section className="panel">
      <header>
        <h2>Analysis</h2>
        <span className="status">{analysis.status}</span>
      </header>
      <p className="summary">{analysis.summary}</p>
      <div className="findings">
        {analysis.findings.map((finding) => (
          <article key={finding.title} className="finding">
            <div>
              <strong>{finding.title}</strong>
              <span>{finding.severity}</span>
            </div>
            <p>{finding.summary}</p>
            {finding.evidence.map((item) => (
              <code key={`${item.path}-${item.start_line}`}>
                {item.path}:{item.start_line}-{item.end_line}
              </code>
            ))}
          </article>
        ))}
      </div>
      <AgentTimeline steps={analysis.timeline} />
    </section>
  );
}
