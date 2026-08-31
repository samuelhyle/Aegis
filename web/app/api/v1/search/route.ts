import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get("query") || "";
  const patientId = searchParams.get("patient_id");
  const topK = parseInt(searchParams.get("top_k") || "10");

  // Mock search results
  const results = [
    {
      id: "result-001",
      type: "condition",
      patient_id: "patient-001",
      content: "Type 2 diabetes mellitus - diagnosed 2020-01-15",
      score: 0.95,
      metadata: { code: "E11.9", onset: "2020-01-15" },
    },
    {
      id: "result-002",
      type: "medication",
      patient_id: "patient-001",
      content: "Metformin 500mg - prescribed for diabetes management",
      score: 0.88,
      metadata: { prescribed: "2020-02-01" },
    },
    {
      id: "result-003",
      type: "observation",
      patient_id: "patient-001",
      content: "HbA1c: 7.2% - suboptimal glycemic control",
      score: 0.82,
      metadata: { date: "2024-01-15", value: "7.2" },
    },
  ];

  const filtered = patientId
    ? results.filter((r) => r.patient_id === patientId)
    : results;

  return NextResponse.json({
    query,
    results: filtered.slice(0, topK),
    total: filtered.length,
  });
}
