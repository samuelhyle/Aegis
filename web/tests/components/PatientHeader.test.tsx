import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PatientHeader } from "@/components/patient/PatientHeader";

const mockPatient = {
  patient_id: "p1",
  first_name: "John",
  last_name: "Doe",
  gender: "M",
  birthdate: "1990-01-15",
  city: "Boston",
  state: "MA",
};

describe("PatientHeader", () => {
  it("renders patient name", () => {
    render(<PatientHeader patient={mockPatient} />);
    expect(screen.getByText("John Doe")).toBeInTheDocument();
  });

  it("renders truncated patient ID", () => {
    render(<PatientHeader patient={mockPatient} />);
    expect(screen.getByText("p1...")).toBeInTheDocument();
  });

  it("renders gender", () => {
    render(<PatientHeader patient={mockPatient} />);
    expect(screen.getByText("M")).toBeInTheDocument();
  });

  it("renders location", () => {
    render(<PatientHeader patient={mockPatient} />);
    expect(screen.getByText(/Boston/)).toBeInTheDocument();
    expect(screen.getByText(/MA/)).toBeInTheDocument();
  });

  it("renders with action button when onAction and actionLabel provided", () => {
    render(
      <PatientHeader
        patient={mockPatient}
        onAction={() => {}}
        actionLabel="Investigate"
      />
    );
    expect(screen.getByText("Investigate")).toBeInTheDocument();
  });

  it("does not render action button without onAction", () => {
    render(<PatientHeader patient={mockPatient} />);
    expect(screen.queryByText("Investigate")).not.toBeInTheDocument();
  });
});
