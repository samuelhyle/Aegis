import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { patient_id, question } = body;

  if (!patient_id || !question) {
    return NextResponse.json(
      { detail: "patient_id and question are required" },
      { status: 400 }
    );
  }

  // Generate a mock investigation report
  const traceId = `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  return NextResponse.json({
    trace_id: traceId,
    patient_id,
    question,
    conclusion: `Investigation completed for patient ${patient_id}. Based on the analysis of the patient's health records, several key findings were identified. The patient's condition requires ongoing monitoring and follow-up.`,
    evidence: [
      "Patient has a history of chronic conditions requiring ongoing management",
      "Recent lab results show stable but elevated markers",
      "Medication adherence appears consistent based on prescription records",
    ],
    confidence: 0.85,
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
    generated_at: new Date().toISOString(),
  });
}
