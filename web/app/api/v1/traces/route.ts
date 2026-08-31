import { NextRequest, NextResponse } from "next/server";

const MOCK_TRACES = [
  {
    trace_id: "trace-001",
    patient_id: "patient-001",
    question: "Summarize this patient's longitudinal health record and identify important changes.",
    conclusion: "The patient has Type 2 diabetes managed with Metformin, hypertension controlled with Lisinopril, and hyperlipidemia treated with Atorvastatin. Recent HbA1c of 7.2% indicates suboptimal glycemic control. Blood pressure is slightly above target.",
    evidence: ["HbA1c trending upward over past 6 months", "Blood pressure consistently elevated", "Cholesterol levels improving with statin therapy"],
    confidence: 0.87,
    review_required: true,
    reviewed: false,
    generated_at: "2024-01-15T10:30:00Z",
  },
  {
    trace_id: "trace-002",
    patient_id: "patient-002",
    question: "What are the key risk factors for this patient's asthma management?",
    conclusion: "Patient has well-controlled asthma with occasional exacerbations triggered by seasonal allergens. Current inhaler regimen is appropriate. Recommend continued monitoring of peak flow readings.",
    evidence: ["Peak expiratory flow within normal range", "No ER visits for asthma in past year", "Allergy season shows mild increase in symptoms"],
    confidence: 0.91,
    review_required: true,
    reviewed: true,
    reviewed_at: "2024-02-25T14:00:00Z",
    generated_at: "2024-02-20T09:15:00Z",
  },
];

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const patientId = searchParams.get("patient_id");
  const limit = parseInt(searchParams.get("limit") || "50");
  const offset = parseInt(searchParams.get("offset") || "0");

  let filtered = MOCK_TRACES;
  if (patientId) {
    filtered = filtered.filter((t) => t.patient_id === patientId);
  }

  const paginated = filtered.slice(offset, offset + limit);

  return NextResponse.json({
    traces: paginated,
    total: filtered.length,
    has_more: offset + limit < filtered.length,
  });
}
