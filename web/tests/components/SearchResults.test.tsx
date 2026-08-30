import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SearchResults } from "@/components/search/SearchResults";

const mockResults = [
  {
    id: "r1",
    patient_id: "patient-123",
    source_type: "condition",
    source_id: "c1",
    chunk_text: "Patient has type 2 diabetes mellitus",
    similarity: 0.92,
    metadata: { description: "Diabetes" },
  },
  {
    id: "r2",
    patient_id: "patient-123",
    source_type: "medication",
    source_id: "m1",
    chunk_text: "Metformin 500mg twice daily",
    similarity: 0.85,
    metadata: { description: "Metformin" },
  },
];

describe("SearchResults", () => {
  it("renders search results", () => {
    render(<SearchResults results={mockResults} total={2} query="diabetes" />);
    expect(screen.getByText(/diabetes mellitus/i)).toBeInTheDocument();
    expect(screen.getByText(/Metformin 500mg/)).toBeInTheDocument();
  });

  it("shows similarity scores", () => {
    render(<SearchResults results={mockResults} total={2} query="diabetes" />);
    expect(screen.getByText("92% match")).toBeInTheDocument();
    expect(screen.getByText("85% match")).toBeInTheDocument();
  });

  it("shows source type badges", () => {
    render(<SearchResults results={mockResults} total={2} query="diabetes" />);
    expect(screen.getByText("Condition")).toBeInTheDocument();
    expect(screen.getByText("Medication")).toBeInTheDocument();
  });

  it("shows result count", () => {
    render(<SearchResults results={mockResults} total={2} query="diabetes" />);
    expect(screen.getByText("2 results")).toBeInTheDocument();
  });

  it("renders empty state when no results", () => {
    render(<SearchResults results={[]} total={0} query="test" />);
    expect(screen.getByText("No results found")).toBeInTheDocument();
    expect(screen.getByText("Try a different query or adjust filters")).toBeInTheDocument();
  });

  it("shows patient ID", () => {
    render(<SearchResults results={mockResults} total={2} query="diabetes" />);
    expect(screen.getAllByText(/patient-123/).length).toBeGreaterThan(0);
  });

  it("renders result header", () => {
    render(<SearchResults results={mockResults} total={2} query="diabetes" />);
    expect(screen.getByText("Search Results")).toBeInTheDocument();
  });
});
