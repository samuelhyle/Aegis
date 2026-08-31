import { NextRequest, NextResponse } from "next/server";

const MOCK_ENCOUNTERS: Record<string, unknown[]> = {
  "patient-001": [
    { id: "enc-001", date: "2024-01-15", type: "Office Visit", provider: "Dr. Smith", reason: "Diabetes follow-up" },
    { id: "enc-002", date: "2023-10-20", type: "Lab Work", provider: "Lab Corp", reason: "Routine blood work" },
    { id: "enc-003", date: "2023-07-10", type: "Office Visit", provider: "Dr. Smith", reason: "Hypertension check" },
  ],
  "patient-002": [
    { id: "enc-004", date: "2024-02-20", type: "Office Visit", provider: "Dr. Johnson", reason: "Asthma review" },
    { id: "enc-005", date: "2023-11-15", type: "Urgent Care", provider: "City Clinic", reason: "Allergic reaction" },
  ],
  "patient-003": [
    { id: "enc-006", date: "2024-03-10", type: "Physical Therapy", provider: "PT Associates", reason: "Back pain treatment" },
    { id: "enc-007", date: "2024-01-05", type: "Office Visit", provider: "Dr. Williams", reason: "GERD follow-up" },
  ],
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const encounters = MOCK_ENCOUNTERS[id] || [];

  return NextResponse.json({
    patient_id: id,
    encounters,
    total: encounters.length,
  });
}
