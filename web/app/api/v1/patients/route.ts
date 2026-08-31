import { NextRequest, NextResponse } from "next/server";

const MOCK_PATIENTS = [
  {
    patient_id: "patient-001",
    first_name: "John",
    last_name: "Smith",
    gender: "M",
    birthdate: "1985-03-15",
  },
  {
    patient_id: "patient-002",
    first_name: "Sarah",
    last_name: "Johnson",
    gender: "F",
    birthdate: "1990-07-22",
  },
  {
    patient_id: "patient-003",
    first_name: "Michael",
    last_name: "Williams",
    gender: "M",
    birthdate: "1978-11-08",
  },
  {
    patient_id: "patient-004",
    first_name: "Emily",
    last_name: "Brown",
    gender: "F",
    birthdate: "1995-01-30",
  },
  {
    patient_id: "patient-005",
    first_name: "David",
    last_name: "Jones",
    gender: "M",
    birthdate: "1982-09-12",
  },
];

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const limit = parseInt(searchParams.get("limit") || "50");
  const offset = parseInt(searchParams.get("offset") || "0");

  const paginated = MOCK_PATIENTS.slice(offset, offset + limit);

  return NextResponse.json({
    patients: paginated,
    total: MOCK_PATIENTS.length,
    limit,
    offset,
    has_more: offset + limit < MOCK_PATIENTS.length,
  });
}
