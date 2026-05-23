import type { AgentStep } from "../lib/types";

export function AgentTimeline({ steps }: { steps: AgentStep[] }) {
  return (
    <ol className="timeline">
      {steps.map((step) => (
        <li key={`${step.node}-${step.summary}`}>
          <strong>{step.node}</strong>
          <span>{step.summary}</span>
        </li>
      ))}
    </ol>
  );
}
