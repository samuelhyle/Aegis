import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LabsChart } from "@/app/(dashboard)/patients/[id]/LabsChart";

const mockObservations = [
  {
    Id: "obs1",
    PATIENT: "p1",
    CODE: "2345-7",
    DESCRIPTION: "Glucose [Mass/volume] in Serum or Plasma",
    VALUE: "120",
    UNITS: "mg/dL",
    DATE: "2024-01-15",
  },
  {
    Id: "obs2",
    PATIENT: "p1",
    CODE: "2345-7",
    DESCRIPTION: "Glucose [Mass/volume] in Serum or Plasma",
    VALUE: "95",
    UNITS: "mg/dL",
    DATE: "2024-02-15",
  },
];

describe("LabsChart", () => {
  it("renders chart with lab title", () => {
    render(<LabsChart observations={mockObservations} />);
    expect(screen.getByText("Lab Trends")).toBeInTheDocument();
  });

  it("renders lab values in table", () => {
    render(<LabsChart observations={mockObservations} />);
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("95")).toBeInTheDocument();
  });

  it("renders formatted dates", () => {
    render(<LabsChart observations={mockObservations} />);
    expect(screen.getByText("Jan 15, 2024")).toBeInTheDocument();
    expect(screen.getByText("Feb 15, 2024")).toBeInTheDocument();
  });

  it("renders data point count", () => {
    render(<LabsChart observations={mockObservations} />);
    expect(screen.getByText("Data points: 2")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<LabsChart observations={[]} />);
    expect(screen.getByText("No lab data available")).toBeInTheDocument();
  });

  it("renders Recent Lab Results section", () => {
    render(<LabsChart observations={mockObservations} />);
    expect(screen.getByText("Recent Lab Results")).toBeInTheDocument();
  });

  it("renders units", () => {
    render(<LabsChart observations={mockObservations} />);
    expect(screen.getAllByText("mg/dL").length).toBeGreaterThan(0);
  });
});
