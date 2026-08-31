import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  return NextResponse.json({
    patient_id: id,
    risks: [
      {
        risk_type: "Cardiovascular",
        score: 0.65,
        risk_level: "moderate",
        factors: ["Hypertension", "Hyperlipidemia", "Family history"],
        recommendations: ["Continue statin therapy", "Monitor blood pressure", "Lifestyle modifications"],
        confidence: 0.88,
      },
      {
        risk_type: "Diabetes Complications",
        score: 0.45,
        risk_level: "moderate",
        factors: ["Suboptimal HbA1c", "Duration of diabetes"],
        recommendations: ["Optimize glycemic control", "Annual eye exam", "Foot examination"],
        confidence: 0.85,
      },
      {
        risk_type: "Readmission",
        score: 0.15,
        risk_level: "low",
        factors: ["Stable condition", "Good medication adherence"],
        recommendations: ["Continue current management"],
        confidence: 0.90,
      },
    ],
  });
}
