import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ClinicalTrialsTab } from "@/app/(dashboard)/patients/[id]/ClinicalTrialsTab";

const mockTrials = [
  {
    trial_id: "NCT001",
    title: "Diabetes Treatment Study",
    condition: "Type 2 Diabetes",
    phase: "Phase 3",
    confidence: 0.88,
    eligibility_status: "eligible",
    match_reasons: ["Has T2D diagnosis", "HbA1c > 7%"],
    exclusion_reasons: [],
    recommendations: ["Enroll patient"],
  },
  {
    trial_id: "NCT002",
    title: "Hypertension Trial",
    condition: "Hypertension",
    phase: "Phase 2",
    confidence: 0.65,
    eligibility_status: "ineligible",
    match_reasons: ["Has hypertension"],
    exclusion_reasons: ["Age criteria not met"],
    recommendations: [],
  },
];

describe("ClinicalTrialsTab", () => {
  it("renders trial matches", () => {
    render(<ClinicalTrialsTab trials={mockTrials} patient={{}} />);
    expect(screen.getByText("Diabetes Treatment Study")).toBeInTheDocument();
    expect(screen.getByText("Hypertension Trial")).toBeInTheDocument();
  });

  it("renders eligibility status", () => {
    render(<ClinicalTrialsTab trials={mockTrials} patient={{}} />);
    expect(screen.getAllByText(/eligible/).length).toBeGreaterThan(0);
  });

  it("renders trial phases", () => {
    render(<ClinicalTrialsTab trials={mockTrials} patient={{}} />);
    expect(screen.getByText(/Phase 3/)).toBeInTheDocument();
    expect(screen.getByText(/Phase 2/)).toBeInTheDocument();
  });

  it("renders match reasons", () => {
    render(<ClinicalTrialsTab trials={mockTrials} patient={{}} />);
    expect(screen.getByText("Has T2D diagnosis")).toBeInTheDocument();
  });

  it("renders exclusion reasons", () => {
    render(<ClinicalTrialsTab trials={mockTrials} patient={{}} />);
    expect(screen.getByText("Age criteria not met")).toBeInTheDocument();
  });

  it("renders recommendations", () => {
    render(<ClinicalTrialsTab trials={mockTrials} patient={{}} />);
    expect(screen.getByText("Enroll patient")).toBeInTheDocument();
  });

  it("renders stat summary", () => {
    render(<ClinicalTrialsTab trials={mockTrials} patient={{}} />);
    expect(screen.getByText("Total Matches")).toBeInTheDocument();
    expect(screen.getByText("Eligible")).toBeInTheDocument();
    expect(screen.getByText("Ineligible")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<ClinicalTrialsTab trials={[]} patient={{}} />);
    expect(screen.getByText("No Clinical Trial Matches")).toBeInTheDocument();
  });
});
