import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    total_patients: 5,
    active_investigations: 2,
    high_risk_alerts: 1,
    pending_reviews: 1,
    total_encounters: 7,
    total_observations: 10,
    system_uptime: "99.9%",
    last_updated: new Date().toISOString(),
  });
}
