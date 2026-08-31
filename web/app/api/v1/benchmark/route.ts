import { NextRequest, NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    results: [
      {
        case_id: "bench-001",
        patient_id: "patient-001",
        question: "Summarize patient's diabetes management",
        score: 0.87,
        latency_ms: 1200,
        status: "completed",
      },
      {
        case_id: "bench-002",
        patient_id: "patient-002",
        question: "Assess asthma control level",
        score: 0.91,
        latency_ms: 980,
        status: "completed",
      },
    ],
    summary: {
      total_cases: 2,
      average_score: 0.89,
      average_latency_ms: 1090,
      success_rate: 1.0,
    },
  });
}

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));

  return NextResponse.json({
    run_id: `run-${Date.now()}`,
    status: "started",
    questions: body.questions || ["Default benchmark question"],
    started_at: new Date().toISOString(),
  });
}
