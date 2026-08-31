import { NextRequest, NextResponse } from "next/server";

const MOCK_TRACE_DETAILS: Record<string, unknown> = {
  "trace-001": {
    trace_id: "trace-001",
    patient_id: "patient-001",
    question: "Summarize this patient's longitudinal health record and identify important changes.",
    conclusion: "The patient has Type 2 diabetes managed with Metformin, hypertension controlled with Lisinopril, and hyperlipidemia treated with Atorvastatin. Recent HbA1c of 7.2% indicates suboptimal glycemic control. Blood pressure is slightly above target.",
    evidence: ["HbA1c trending upward over past 6 months", "Blood pressure consistently elevated", "Cholesterol levels improving with statin therapy"],
    confidence: 0.87,
    review_required: true,
    reviewed: false,
    agent_results: [
      {
        agent: "timeline",
        status: "completed",
        summary: "Analyzed patient's temporal health patterns",
        evidence: ["Identified 3 major health events in the past 2 years"],
        confidence: 0.88,
      },
      {
        agent: "medication",
        status: "completed",
        summary: "Reviewed medication regimen and interactions",
        evidence: ["No critical drug interactions detected"],
        confidence: 0.92,
      },
      {
        agent: "evidence",
        status: "completed",
        summary: "Gathered supporting evidence from patient records",
        evidence: ["Found 12 relevant clinical notes"],
        confidence: 0.85,
      },
    ],
    generated_at: "2024-01-15T10:30:00Z",
  },
  "trace-002": {
    trace_id: "trace-002",
    patient_id: "patient-002",
    question: "What are the key risk factors for this patient's asthma management?",
    conclusion: "Patient has well-controlled asthma with occasional exacerbations triggered by seasonal allergens. Current inhaler regimen is appropriate. Recommend continued monitoring of peak flow readings.",
    evidence: ["Peak expiratory flow within normal range", "No ER visits for asthma in past year", "Allergy season shows mild increase in symptoms"],
    confidence: 0.91,
    review_required: true,
    reviewed: true,
    reviewed_at: "2024-02-25T14:00:00Z",
    agent_results: [
      {
        agent: "timeline",
        status: "completed",
        summary: "Mapped asthma exacerbation timeline",
        evidence: ["Seasonal pattern identified"],
        confidence: 0.90,
      },
      {
        agent: "risk_assessment",
        status: "completed",
        summary: "Assessed asthma control level",
        evidence: ["Well-controlled per GINA guidelines"],
        confidence: 0.88,
      },
    ],
    generated_at: "2024-02-20T09:15:00Z",
  },
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ traceId: string }> }
) {
  const { traceId } = await params;
  const trace = MOCK_TRACE_DETAILS[traceId];

  if (!trace) {
    return NextResponse.json({ detail: "Trace not found" }, { status: 404 });
  }

  return NextResponse.json(trace);
}
