import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const searchParams = request.nextUrl.searchParams;

  if (path.length === 0) {
    return NextResponse.json({ detail: "Endpoint required" }, { status: 400 });
  }

  const endpoint = path[0];

  switch (endpoint) {
    case "benchmark":
      return NextResponse.json({
        cases: [
          {
            case_id: "bench-001",
            patient_id: "patient-001",
            question: "Summarize this patient's diabetes management",
            category: "diabetes",
            difficulty: "medium",
            expected_findings: ["HbA1c levels", "Medication adherence", "Complications"],
            expected_confidence_range: [0.7, 0.9],
          },
        ],
        total: 1,
        categories: ["diabetes", "cardiology", "pulmonology"],
        difficulties: ["easy", "medium", "hard"],
      });

    case "metrics":
      return NextResponse.json({
        metrics: [
          { name: "accuracy", description: "How well findings match expected results" },
          { name: "completeness", description: "Coverage of expected findings" },
          { name: "grounding", description: "How well conclusions are supported by evidence" },
          { name: "relevance", description: "How relevant findings are to the question" },
          { name: "confidence_calibration", description: "How well confidence matches expected range" },
          { name: "reasoning_quality", description: "Quality of the reasoning chain" },
          { name: "tool_efficiency", description: "Efficiency of tool usage" },
          { name: "latency", description: "Response time performance" },
          { name: "safety", description: "Safety and compliance of outputs" },
        ],
      });

    case "history":
      return NextResponse.json({
        reports: [
          {
            report_id: "eval-001",
            agent_name: "diagnostic",
            overall_score: 0.87,
            total_cases: 10,
            completed_cases: 10,
            generated_at: "2024-01-15T10:00:00Z",
          },
        ],
        total: 1,
      });

    case "trends":
      return NextResponse.json({
        trends: [
          { date: "2024-01-01", score: 0.82 },
          { date: "2024-01-15", score: 0.87 },
        ],
        direction: "improving",
      });

    case "compare":
      return NextResponse.json({
        report1: { id: searchParams.get("report1"), score: 0.82 },
        report2: { id: searchParams.get("report2"), score: 0.87 },
        difference: 0.05,
        significant: true,
      });

    default:
      return NextResponse.json({ detail: "Unknown endpoint" }, { status: 404 });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;

  if (path[0] === "run") {
    return NextResponse.json({
      report_id: `eval-${Date.now()}`,
      agent_name: "diagnostic",
      overall_score: 0.87,
      total_cases: 10,
      completed_cases: 10,
      generated_at: new Date().toISOString(),
      scores: [
        { metric: "accuracy", score: 0.85, explanation: "Good diagnostic accuracy" },
        { metric: "completeness", score: 0.90, explanation: "Comprehensive findings" },
      ],
    });
  }

  return NextResponse.json({ detail: "Unknown endpoint" }, { status: 404 });
}
