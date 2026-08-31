import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    agents: [
      {
        name: "diagnostic",
        role: "diagnostician",
        description: "Analyzes patient data to identify and evaluate potential diagnoses",
        capabilities: [
          "Differential diagnosis reasoning",
          "Evidence-based diagnostic evaluation",
          "Diagnostic confidence assessment",
        ],
      },
      {
        name: "treatment",
        role: "clinical pharmacologist",
        description: "Analyzes treatment plans, medications, and therapeutic effectiveness",
        capabilities: [
          "Medication review and optimization",
          "Drug interaction analysis",
          "Treatment effectiveness assessment",
        ],
      },
      {
        name: "risk_assessment",
        role: "risk stratification specialist",
        description: "Assesses patient risks and predicts outcomes",
        capabilities: [
          "Disease risk scoring",
          "Readmission risk prediction",
          "Complication risk assessment",
        ],
      },
      {
        name: "timeline",
        role: "clinical timeline analyst",
        description: "Analyzes temporal patterns in patient health data",
        capabilities: [
          "Disease progression analysis",
          "Treatment timeline mapping",
          "Temporal pattern detection",
        ],
      },
    ],
  });
}
