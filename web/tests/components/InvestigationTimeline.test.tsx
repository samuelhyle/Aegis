import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { InvestigationTimeline } from "@/components/investigation/InvestigationTimeline";

const mockEvents = [
  {
    type: "investigation_started",
    timestamp: "2024-01-15T12:00:00Z",
  },
  {
    type: "agent_started",
    agent: "diagnostic",
    timestamp: "2024-01-15T12:00:01Z",
  },
  {
    type: "agent_completed",
    agent: "diagnostic",
    timestamp: "2024-01-15T12:00:05Z",
    result: {
      agent: "diagnostic",
      status: "completed",
      summary: "Found issues",
      confidence: 0.85,
    },
  },
];

describe("InvestigationTimeline", () => {
  it("renders timeline events", () => {
    render(<InvestigationTimeline events={mockEvents} />);
    expect(screen.getByText("Investigation started")).toBeInTheDocument();
  });

  it("renders agent started event", () => {
    render(<InvestigationTimeline events={mockEvents} />);
    expect(screen.getByText(/Agent started: diagnostic/)).toBeInTheDocument();
  });

  it("renders agent completed event", () => {
    render(<InvestigationTimeline events={mockEvents} />);
    expect(screen.getByText(/Agent completed: diagnostic/)).toBeInTheDocument();
  });

  it("renders empty state when no events", () => {
    render(<InvestigationTimeline events={[]} />);
    expect(screen.getByText("No events yet")).toBeInTheDocument();
  });

  it("displays timestamps", () => {
    render(<InvestigationTimeline events={mockEvents} />);
    expect(screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/).length).toBeGreaterThan(0);
  });

  it("renders confidence bar for completed events", () => {
    render(<InvestigationTimeline events={mockEvents} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
  });
});
