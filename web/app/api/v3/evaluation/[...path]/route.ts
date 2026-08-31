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
    case "history":
      return NextResponse.json({
        reports: [
          {
            report_id: "eval-v3-001",
            agent_name: searchParams.get("agent_name") || "diagnostic",
            overall_score: 0.89,
            total_cases: 15,
            completed_cases: 15,
            generated_at: "2024-01-20T14:00:00Z",
          },
        ],
        total: 1,
      });

    case "trends":
      return NextResponse.json({
        trends: [
          { date: "2024-01-01", score: 0.84 },
          { date: "2024-01-15", score: 0.87 },
          { date: "2024-01-20", score: 0.89 },
        ],
        direction: "improving",
      });

    case "report":
      if (path[1]) {
        return NextResponse.json({
          report_id: path[1],
          agent_name: "diagnostic",
          overall_score: 0.89,
          total_cases: 15,
          completed_cases: 15,
          generated_at: "2024-01-20T14:00:00Z",
          scores: [
            { metric: "accuracy", score: 0.88, explanation: "High diagnostic accuracy" },
            { metric: "completeness", score: 0.92, explanation: "Comprehensive analysis" },
            { metric: "grounding", score: 0.87, explanation: "Well-supported conclusions" },
          ],
          strengths: ["Thorough analysis", "Good evidence gathering"],
          weaknesses: ["Could improve differential diagnosis"],
        });
      }
      return NextResponse.json({ detail: "Report ID required" }, { status: 400 });

    default:
      return NextResponse.json({ detail: "Unknown endpoint" }, { status: 404 });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;

  if (path[0] === "synthetic-benchmark") {
    return NextResponse.json({
      cases_generated: 5,
      categories: ["diabetes", "cardiology", "pulmonology"],
      difficulties: ["easy", "medium", "hard"],
      cases: [
        { case_id: "syn-001", patient_id: "patient-001...", question: "Analyze diabetes management", category: "diabetes", difficulty: "medium" },
      ],
    });
  }

  if (path[0] === "extended-metrics") {
    const body = await request.json().catch(() => ({}));
    return NextResponse.json({
      conclusion: body.conclusion || "",
      metrics: {
        grounding_score: 0.85,
        completeness_score: 0.90,
        relevance_score: 0.88,
        safety_score: 0.95,
      },
      overall_score: 0.89,
    });
  }

  return NextResponse.json({ detail: "Unknown endpoint" }, { status: 404 });
}
