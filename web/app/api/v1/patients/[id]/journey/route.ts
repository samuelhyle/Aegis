import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  return NextResponse.json({
    patient_id: id,
    journey: {
      states: [
        { timestamp: "2018-06-20", state: "Diagnosis", description: "Essential hypertension diagnosed" },
        { timestamp: "2019-03-10", state: "Diagnosis", description: "Hyperlipidemia diagnosed" },
        { timestamp: "2020-01-15", state: "Diagnosis", description: "Type 2 diabetes mellitus diagnosed" },
        { timestamp: "2024-01-15", state: "Monitoring", description: "Routine follow-up and lab work" },
      ],
      transitions: [
        { from: "Healthy", to: "At Risk", timestamp: "2018-01-01" },
        { from: "At Risk", to: "Chronic", timestamp: "2018-06-20" },
        { from: "Chronic", to: "Managed", timestamp: "2020-02-01" },
      ],
      current_state: "Managed",
      duration_days: 2100,
    },
  });
}
