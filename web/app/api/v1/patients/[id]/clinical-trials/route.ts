import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  return NextResponse.json({
    patient_id: id,
    matches: [
      {
        nct_id: "NCT01234567",
        title: "Study of New Diabetes Medication",
        status: "Recruiting",
        conditions: ["Type 2 Diabetes"],
        match_score: 0.85,
        eligibility_met: ["Age appropriate", "Diagnosis confirmed"],
        eligibility_not_met: ["HbA1c too high"],
        url: "https://clinicaltrials.gov/study/NCT01234567",
      },
      {
        nct_id: "NCT02345678",
        title: "Hypertension Management Study",
        status: "Recruiting",
        conditions: ["Essential Hypertension"],
        match_score: 0.72,
        eligibility_met: ["Age appropriate", "Blood pressure criteria"],
        eligibility_not_met: [],
        url: "https://clinicaltrials.gov/study/NCT02345678",
      },
    ],
  });
}
