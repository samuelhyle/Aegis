import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const searchParams = request.nextUrl.searchParams;

  if (path.length === 0) {
    return NextResponse.json({ detail: "Patient ID required" }, { status: 400 });
  }

  const patientId = path[0];

  if (path.length === 1) {
    // /v2/temporal/{patientId} - comprehensive temporal analysis
    return NextResponse.json({
      patient_id: patientId,
      analysis: {
        disease_progression: {
          conditions: [
            {
              name: "Type 2 diabetes",
              onset: "2020-01-15",
              current_status: "managed",
              trend: "stable",
            },
          ],
        },
        lab_trends: [
          {
            name: "HbA1c",
            values: [
              { date: "2023-01-15", value: 6.8 },
              { date: "2023-07-15", value: 7.0 },
              { date: "2024-01-15", value: 7.2 },
            ],
            trend: "increasing",
            prediction: { value: 7.4, confidence: 0.75 },
          },
        ],
        temporal_anomalies: [],
        health_states: [
          { timestamp: "2020-01-15", state: "diagnosed" },
          { timestamp: "2020-02-01", state: "treatment_started" },
          { timestamp: "2024-01-15", state: "monitoring" },
        ],
      },
    });
  }

  const subEndpoint = path[1];

  switch (subEndpoint) {
    case "anomalies": {
      const labName = searchParams.get("lab_name");
      return NextResponse.json({
        patient_id: patientId,
        anomalies: [
          {
            type: "sudden_change",
            description: "HbA1c increased by 0.4% in 6 months",
            severity: "moderate",
            timestamp: "2024-01-15",
            value: 7.2,
            expected_range: [6.0, 7.0],
            confidence: 0.85,
          },
        ],
        anomaly_count: 1,
      });
    }

    case "predictions": {
      const labName = searchParams.get("lab_name") || "glucose";
      const horizonDays = parseInt(searchParams.get("horizon_days") || "90");
      return NextResponse.json({
        patient_id: patientId,
        lab_name: labName,
        predictions: [
          { date: "2024-04-15", predicted_value: 148, confidence_interval: [135, 161] },
          { date: "2024-07-15", predicted_value: 152, confidence_interval: [138, 166] },
        ],
        trend: "increasing",
        confidence: 0.75,
      });
    }

    case "progression": {
      const condition = path[2] || "diabetes";
      const horizonDays = parseInt(searchParams.get("horizon_days") || "365");
      return NextResponse.json({
        patient_id: patientId,
        condition,
        progression: {
          current_stage: "managed",
          predicted_stages: [
            { timeframe: "6 months", stage: "managed", probability: 0.85 },
            { timeframe: "1 year", stage: "managed", probability: 0.75 },
          ],
          risk_factors: ["Suboptimal HbA1c", "Medication adherence"],
          recommendations: ["Optimize medication", "Lifestyle changes"],
        },
      });
    }

    case "timeline":
      return NextResponse.json({
        patient_id: patientId,
        events: [
          { type: "condition", date: "2020-01-15", description: "Type 2 diabetes mellitus", status: "active" },
          { type: "medication", date: "2020-02-01", description: "Metformin", status: "active" },
          { type: "observation", date: "2024-01-15", description: "HbA1c", value: "7.2", unit: "%" },
        ],
        event_count: 3,
      });

    case "trajectories":
      return NextResponse.json({
        patient_id: patientId,
        trajectories: {
          diabetes: {
            current_state: "managed",
            states: [
              { timestamp: "2020-01-15", state: "diagnosed" },
              { timestamp: "2020-02-01", state: "treatment_started" },
              { timestamp: "2024-01-15", state: "managed" },
            ],
            transitions: [
              { timestamp: "2020-02-01", from: "diagnosed", to: "treatment_started" },
              { timestamp: "2020-06-01", from: "treatment_started", to: "managed" },
            ],
            durations: {
              diagnosed: 17,
              treatment_started: 121,
              managed: 1460,
            },
          },
        },
      });

    default:
      return NextResponse.json({ detail: "Unknown endpoint" }, { status: 404 });
  }
}
