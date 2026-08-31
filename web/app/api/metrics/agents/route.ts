import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    agents: {
      diagnostic: {
        total_runs: 15,
        success_rate: 0.93,
        average_latency_ms: 1100,
        average_confidence: 0.87,
      },
      treatment: {
        total_runs: 12,
        success_rate: 0.92,
        average_latency_ms: 950,
        average_confidence: 0.85,
      },
      risk_assessment: {
        total_runs: 10,
        success_rate: 0.90,
        average_latency_ms: 800,
        average_confidence: 0.82,
      },
      timeline: {
        total_runs: 14,
        success_rate: 0.95,
        average_latency_ms: 750,
        average_confidence: 0.88,
      },
    },
    summary: {
      total_agent_runs: 51,
      overall_success_rate: 0.92,
      overall_average_latency_ms: 900,
    },
  });
}
