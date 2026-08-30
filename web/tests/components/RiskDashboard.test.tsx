import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RiskDashboard } from "@/app/(dashboard)/patients/[id]/RiskDashboard";

const mockRiskAssessment = [
  {
    risk_type: "cardiovascular",
    score: 0.75,
    risk_level: "high",
    factors: ["Age > 60", "Hypertension"],
    recommendations: ["Monitor BP regularly"],
    confidence: 0.85,
  },
  {
    risk_type: "diabetes",
    score: 0.3,
    risk_level: "moderate",
    factors: ["Family history"],
    recommendations: ["Annual screening"],
    confidence: 0.7,
  },
];

const mockJourney = {
  upcoming_risks: [
    {
      condition: "Stroke",
      probability: 0.15,
      horizon_days: 365,
    },
  ],
  state_projections: [],
};

const mockTemporalAnalysis = {
  predictions: {},
};

describe("RiskDashboard", () => {
  it("renders risk cards", () => {
    render(
      <RiskDashboard
        riskAssessment={mockRiskAssessment}
        journey={mockJourney}
        temporalAnalysis={mockTemporalAnalysis}
      />
    );
    expect(screen.getByText(/cardiovascular/i)).toBeInTheDocument();
    expect(screen.getByText(/diabetes/i)).toBeInTheDocument();
  });

  it("renders risk levels", () => {
    render(
      <RiskDashboard
        riskAssessment={mockRiskAssessment}
        journey={mockJourney}
        temporalAnalysis={mockTemporalAnalysis}
      />
    );
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Moderate")).toBeInTheDocument();
  });

  it("renders risk factors", () => {
    render(
      <RiskDashboard
        riskAssessment={mockRiskAssessment}
        journey={mockJourney}
        temporalAnalysis={mockTemporalAnalysis}
      />
    );
    expect(screen.getByText("Age > 60")).toBeInTheDocument();
    expect(screen.getByText("Hypertension")).toBeInTheDocument();
  });

  it("renders recommendations", () => {
    render(
      <RiskDashboard
        riskAssessment={mockRiskAssessment}
        journey={mockJourney}
        temporalAnalysis={mockTemporalAnalysis}
      />
    );
    expect(screen.getByText("Monitor BP regularly")).toBeInTheDocument();
  });

  it("renders upcoming risks", () => {
    render(
      <RiskDashboard
        riskAssessment={mockRiskAssessment}
        journey={mockJourney}
        temporalAnalysis={mockTemporalAnalysis}
      />
    );
    expect(screen.getByText(/Stroke/)).toBeInTheDocument();
  });

  it("renders stat summary cards", () => {
    render(
      <RiskDashboard
        riskAssessment={mockRiskAssessment}
        journey={mockJourney}
        temporalAnalysis={mockTemporalAnalysis}
      />
    );
    expect(screen.getByText("Critical Risks")).toBeInTheDocument();
    expect(screen.getByText("High Risks")).toBeInTheDocument();
    expect(screen.getByText("Moderate Risks")).toBeInTheDocument();
    expect(screen.getByText("Low Risks")).toBeInTheDocument();
  });

  it("renders empty state when no risks", () => {
    render(
      <RiskDashboard
        riskAssessment={[]}
        journey={mockJourney}
        temporalAnalysis={mockTemporalAnalysis}
      />
    );
    expect(screen.getByText("No risk assessment data available")).toBeInTheDocument();
  });
});
