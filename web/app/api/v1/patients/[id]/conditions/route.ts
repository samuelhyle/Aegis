import { NextRequest, NextResponse } from "next/server";

const MOCK_CONDITIONS: Record<string, unknown[]> = {
  "patient-001": [
    { code: "E11.9", description: "Type 2 diabetes mellitus", onset: "2020-01-15", status: "active" },
    { code: "I10", description: "Essential hypertension", onset: "2018-06-20", status: "active" },
    { code: "E78.5", description: "Hyperlipidemia, unspecified", onset: "2019-03-10", status: "active" },
  ],
  "patient-002": [
    { code: "J45.909", description: "Unspecified asthma", onset: "2015-03-10", status: "active" },
    { code: "J30.1", description: "Allergic rhinitis due to pollen", onset: "2016-05-15", status: "active" },
  ],
  "patient-003": [
    { code: "M54.5", description: "Low back pain", onset: "2021-08-20", status: "active" },
    { code: "K21.0", description: "Gastro-esophageal reflux disease with esophagitis", onset: "2020-02-15", status: "active" },
  ],
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const conditions = MOCK_CONDITIONS[id] || [];

  return NextResponse.json({
    patient_id: id,
    conditions,
    total: conditions.length,
  });
}
