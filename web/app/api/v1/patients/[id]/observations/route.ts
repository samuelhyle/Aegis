import { NextRequest, NextResponse } from "next/server";

const MOCK_OBSERVATIONS: Record<string, unknown[]> = {
  "patient-001": [
    { date: "2024-01-15", description: "Hemoglobin A1c", value: "7.2", unit: "%", code: "4548-4" },
    { date: "2024-01-15", description: "Blood Pressure", value: "138/88", unit: "mmHg", code: "85354-9" },
    { date: "2024-01-15", description: "Total Cholesterol", value: "210", unit: "mg/dL", code: "2093-3" },
    { date: "2024-01-15", description: "Glucose", value: "142", unit: "mg/dL", code: "2345-7" },
  ],
  "patient-002": [
    { date: "2024-02-20", description: "Peak Expiratory Flow", value: "380", unit: "L/min", code: "19934-1" },
    { date: "2024-02-20", description: "Oxygen Saturation", value: "98", unit: "%", code: "2708-6" },
  ],
  "patient-003": [
    { date: "2024-03-10", description: "Body Mass Index", value: "28.5", unit: "kg/m2", code: "39156-5" },
    { date: "2024-03-10", description: "Pain Score", value: "6", unit: "{score}", code: "72514-3" },
  ],
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const observations = MOCK_OBSERVATIONS[id] || [];

  return NextResponse.json({
    patient_id: id,
    observations,
    total: observations.length,
  });
}
