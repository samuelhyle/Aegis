import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DrugInteractionsTab } from "@/app/(dashboard)/patients/[id]/DrugInteractionsTab";

const mockDrugData = {
  medication_count: 3,
  risk_level: "moderate",
  risk_score: 0.45,
  interactions: [
    {
      drug1: "Warfarin",
      drug2: "Aspirin",
      severity: "severe",
      description: "Increased bleeding risk",
      management: "Monitor INR closely",
    },
    {
      drug1: "Metformin",
      drug2: "Lisinopril",
      severity: "minor",
      description: "No significant interaction",
      management: "No action needed",
    },
  ],
  recommendations: ["Review medication list"],
};

describe("DrugInteractionsTab", () => {
  it("renders interaction cards", () => {
    render(<DrugInteractionsTab interactions={mockDrugData} />);
    expect(screen.getByText(/Warfarin \+ Aspirin/)).toBeInTheDocument();
    expect(screen.getByText(/Metformin \+ Lisinopril/)).toBeInTheDocument();
  });

  it("renders severity badges", () => {
    render(<DrugInteractionsTab interactions={mockDrugData} />);
    expect(screen.getByText("severe")).toBeInTheDocument();
    expect(screen.getByText("minor")).toBeInTheDocument();
  });

  it("renders interaction descriptions", () => {
    render(<DrugInteractionsTab interactions={mockDrugData} />);
    expect(screen.getByText("Increased bleeding risk")).toBeInTheDocument();
  });

  it("renders stat summary", () => {
    render(<DrugInteractionsTab interactions={mockDrugData} />);
    expect(screen.getByText("Total Medications")).toBeInTheDocument();
    expect(screen.getByText("Total Interactions")).toBeInTheDocument();
  });

  it("renders recommendations", () => {
    render(<DrugInteractionsTab interactions={mockDrugData} />);
    expect(screen.getByText("Review medication list")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<DrugInteractionsTab interactions={{ interactions: [] }} />);
    expect(screen.getByText("No Drug Interactions Detected")).toBeInTheDocument();
  });
});
