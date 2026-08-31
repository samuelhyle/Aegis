import { NextRequest, NextResponse } from "next/server";

const MOCK_MEDICATIONS: Record<string, unknown[]> = {
  "patient-001": [
    { code: "500mg", description: "Metformin", prescribed: "2020-02-01", status: "active" },
    { code: "10mg", description: "Lisinopril", prescribed: "2018-07-01", status: "active" },
    { code: "20mg", description: "Atorvastatin", prescribed: "2019-04-01", status: "active" },
  ],
  "patient-002": [
    { code: "90mcg", description: "Albuterol inhaler", prescribed: "2015-04-01", status: "active" },
    { code: "10mg", description: "Cetirizine", prescribed: "2016-06-01", status: "active" },
  ],
  "patient-003": [
    { code: "500mg", description: "Acetaminophen", prescribed: "2021-09-01", status: "active" },
    { code: "20mg", description: "Omeprazole", prescribed: "2020-03-01", status: "active" },
  ],
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const medications = MOCK_MEDICATIONS[id] || [];

  return NextResponse.json({
    patient_id: id,
    medications,
    total: medications.length,
  });
}
