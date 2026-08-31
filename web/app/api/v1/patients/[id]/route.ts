import { NextRequest, NextResponse } from "next/server";

const MOCK_PATIENT_DETAILS: Record<string, unknown> = {
  "patient-001": {
    patient_id: "patient-001",
    first_name: "John",
    last_name: "Smith",
    gender: "M",
    birthdate: "1985-03-15",
    race: "White",
    ethnicity: "Non-Hispanic",
    address: "123 Main St, Boston, MA 02101",
    phone: "(555) 123-4567",
    conditions: [
      { code: "E11.9", description: "Type 2 diabetes mellitus", onset: "2020-01-15", status: "active" },
      { code: "I10", description: "Essential hypertension", onset: "2018-06-20", status: "active" },
    ],
    medications: [
      { code: "500mg", description: "Metformin", prescribed: "2020-02-01", status: "active" },
      { code: "10mg", description: "Lisinopril", prescribed: "2018-07-01", status: "active" },
    ],
  },
  "patient-002": {
    patient_id: "patient-002",
    first_name: "Sarah",
    last_name: "Johnson",
    gender: "F",
    birthdate: "1990-07-22",
    race: "Black",
    ethnicity: "Non-Hispanic",
    address: "456 Oak Ave, Cambridge, MA 02139",
    phone: "(555) 987-6543",
    conditions: [
      { code: "J45.909", description: "Unspecified asthma", onset: "2015-03-10", status: "active" },
    ],
    medications: [
      { code: "90mcg", description: "Albuterol inhaler", prescribed: "2015-04-01", status: "active" },
    ],
  },
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const patient = MOCK_PATIENT_DETAILS[id];

  if (!patient) {
    return NextResponse.json({ detail: "Patient not found" }, { status: 404 });
  }

  return NextResponse.json(patient);
}
