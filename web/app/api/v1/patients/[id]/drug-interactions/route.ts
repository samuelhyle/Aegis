import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  return NextResponse.json({
    patient_id: id,
    medication_count: 3,
    risk_level: "low",
    risk_score: 0.2,
    interactions: [
      {
        drug1: "Metformin",
        drug2: "Lisinopril",
        severity: "minor",
        description: "May increase risk of lactic acidosis",
        management: "Monitor renal function regularly",
      },
    ],
    recommendations: [
      "Continue current medications",
      "Regular monitoring of renal function",
      "Report any unusual symptoms",
    ],
  });
}
