import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "aegis",
    version: "0.4.0",
    timestamp: new Date().toISOString(),
    deployment: "vercel",
  });
}
