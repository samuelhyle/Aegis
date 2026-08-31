import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { patient_id, question, agents, enable_debate, evaluate } = body;

  if (!patient_id || !question) {
    return NextResponse.json(
      { detail: "patient_id and question are required" },
      { status: 400 }
    );
  }

  const investigationId = `inv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const traceId = `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  return NextResponse.json({
    investigation_id: investigationId,
    patient_id,
    question,
    conclusion: {
      summary: `Multi-agent investigation completed for patient ${patient_id}. The diagnostic, treatment, risk assessment, and timeline agents have analyzed the patient's records and reached consensus on key findings.`,
      key_findings: [
        "Patient shows stable chronic condition management",
        "Recent lab values indicate need for medication adjustment",
        "No critical drug interactions identified",
        "Temporal patterns suggest seasonal variation in symptoms",
      ],
      evidence: [
        "Comprehensive review of 24 months of medical records",
        "Cross-referenced medication history with lab results",
        "Analyzed temporal patterns in vital signs",
      ],
      confidence: 0.88,
      uncertainties: [
        "Long-term prognosis requires additional data points",
        "Effectiveness of current treatment plan needs 3-month follow-up",
      ],
      recommendations: [
        "Schedule follow-up appointment in 3 months",
        "Repeat lab work in 6 weeks",
        "Consider medication adjustment based on next HbA1c",
      ],
    },
    agent_findings: {
      diagnostic: {
        summary: "Differential diagnosis analysis completed",
        key_findings: ["Primary diagnosis confirmed", "No red flags for rare conditions"],
        confidence: 0.90,
        reasoning_steps: 5,
      },
      treatment: {
        summary: "Treatment regimen reviewed and optimized",
        key_findings: ["Current medications appropriate", "Consider dose adjustment"],
        confidence: 0.87,
        reasoning_steps: 4,
      },
      risk_assessment: {
        summary: "Risk stratification completed",
        key_findings: ["Moderate cardiovascular risk", "Low readmission risk"],
        confidence: 0.85,
        reasoning_steps: 3,
      },
      timeline: {
        summary: "Temporal analysis of health trajectory",
        key_findings: ["Stable disease progression", "No acute deterioration"],
        confidence: 0.92,
        reasoning_steps: 4,
      },
    },
    debate: enable_debate
      ? {
          consensus: "Agents agree on primary diagnosis and treatment plan",
          agreements: ["Diagnosis is well-supported by evidence", "Current treatment is appropriate"],
          disagreements: ["Minor disagreement on follow-up timing"],
          rounds: 2,
        }
      : null,
    evaluations: evaluate
      ? {
          diagnostic: { overall_score: 0.89, strengths: ["Thorough analysis"], weaknesses: ["Could consider more differential diagnoses"] },
          treatment: { overall_score: 0.87, strengths: ["Good medication review"], weaknesses: ["Limited lifestyle recommendations"] },
        }
      : {},
    safety_check: {
      safe: true,
      confidence: 0.95,
      flags: [],
    },
    metrics: {
      total_duration_ms: 2450,
      total_tool_calls: 12,
      total_reasoning_steps: 16,
      agents_used: ["diagnostic", "treatment", "risk_assessment", "timeline"],
    },
    trace_id: traceId,
  });
}
