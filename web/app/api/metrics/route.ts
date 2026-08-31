import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    counters: {
      investigations_total: 25,
      reviews_total: 10,
      api_requests_total: 1500,
    },
    gauges: {
      active_investigations: 2,
      pending_reviews: 1,
    },
    histograms: {
      investigation_duration_ms: {
        count: 25,
        sum: 30000,
        avg: 1200,
      },
    },
  });
}
