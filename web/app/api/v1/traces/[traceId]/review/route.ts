import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ traceId: string }> }
) {
  const { traceId } = await params;
  const body = await request.json();
  const { decision, reviewer_id, notes } = body;

  if (!decision || !reviewer_id) {
    return NextResponse.json(
      { detail: "decision and reviewer_id are required" },
      { status: 400 }
    );
  }

  return NextResponse.json({
    trace_id: traceId,
    reviewed: true,
    review_decision: decision,
    reviewer_id,
    review_notes: notes || "",
    reviewed_at: new Date().toISOString(),
    review_required: decision === "approved" ? false : true,
  });
}
