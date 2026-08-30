import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { LiveInvestigation } from "@/components/investigation/LiveInvestigation";

const mockEvents = [
  { type: "agent_started", agent: "diagnostic" },
  { type: "agent_started", agent: "treatment" },
  { type: "agent_completed", agent: "diagnostic" },
];

describe("LiveInvestigation", () => {
  it("renders streaming state", () => {
    render(
      <LiveInvestigation
        isStreaming={true}
        events={mockEvents}
        currentAgent="diagnostic"
        agentsCompleted={1}
        error={null}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText("Investigation in Progress")).toBeInTheDocument();
  });

  it("renders completed state", () => {
    render(
      <LiveInvestigation
        isStreaming={false}
        events={mockEvents}
        currentAgent={null}
        agentsCompleted={2}
        error={null}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText("Investigation Complete")).toBeInTheDocument();
  });

  it("renders error state", () => {
    render(
      <LiveInvestigation
        isStreaming={false}
        events={mockEvents}
        currentAgent={null}
        agentsCompleted={0}
        error="Connection failed"
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText("Connection failed")).toBeInTheDocument();
  });

  it("shows agent count", () => {
    render(
      <LiveInvestigation
        isStreaming={true}
        events={mockEvents}
        currentAgent="treatment"
        agentsCompleted={1}
        error={null}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText("1 agent completed")).toBeInTheDocument();
  });

  it("shows cancel button when streaming", () => {
    render(
      <LiveInvestigation
        isStreaming={true}
        events={[]}
        currentAgent={null}
        agentsCompleted={0}
        error={null}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("shows current agent", () => {
    render(
      <LiveInvestigation
        isStreaming={true}
        events={mockEvents}
        currentAgent="diagnostic"
        agentsCompleted={0}
        error={null}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText(/Running: Diagnostic/)).toBeInTheDocument();
  });
});
