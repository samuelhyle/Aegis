import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get("query") || "";

  // Handle different graph-rag endpoints
  if (path.length === 1) {
    // /v2/graph-rag/{patientId}
    const patientId = path[0];
    return NextResponse.json({
      patient_id: patientId,
      query,
      evidence: [
        {
          node_id: "condition-001",
          node_type: "condition",
          description: "Type 2 diabetes mellitus",
          relevance_score: 0.95,
          connections: ["medication-001", "observation-001"],
        },
        {
          node_id: "medication-001",
          node_type: "medication",
          description: "Metformin",
          relevance_score: 0.88,
          connections: ["condition-001"],
        },
      ],
      graph_stats: {
        total_nodes: 15,
        total_edges: 22,
        communities: 3,
      },
    });
  }

  if (path.length === 2) {
    const patientId = path[0];
    const subEndpoint = path[1];

    switch (subEndpoint) {
      case "patterns":
        return NextResponse.json({
          patient_id: patientId,
          patterns: [
            {
              pattern_type: "comorbidity",
              description: "Diabetes and hypertension co-occurrence",
              confidence: 0.92,
              entities: ["Type 2 diabetes", "Essential hypertension"],
            },
            {
              pattern_type: "treatment",
              description: "Standard diabetes management protocol",
              confidence: 0.88,
              entities: ["Metformin", "HbA1c monitoring"],
            },
          ],
          pattern_count: 2,
        });

      case "causal-chains":
        return NextResponse.json({
          patient_id: patientId,
          causal_chains: [
            {
              chain: ["Obesity", "Insulin resistance", "Type 2 diabetes", "Metformin prescription"],
              confidence: 0.85,
              length: 4,
            },
          ],
          chain_count: 1,
        });

      case "communities":
        return NextResponse.json({
          patient_id: patientId,
          communities: [
            {
              id: "community-001",
              nodes: ["condition-001", "medication-001", "observation-001"],
              theme: "Diabetes management",
              coherence: 0.90,
            },
          ],
          community_count: 1,
        });

      case "centrality":
        return NextResponse.json({
          patient_id: patientId,
          centrality_scores: [
            { node_id: "condition-001", score: 0.95, description: "Type 2 diabetes mellitus" },
            { node_id: "medication-001", score: 0.82, description: "Metformin" },
            { node_id: "observation-001", score: 0.75, description: "HbA1c" },
          ],
        });

      default:
        return NextResponse.json({ detail: "Unknown endpoint" }, { status: 404 });
    }
  }

  // Handle treatment-pathways and related-conditions
  if (path[0] === "treatment-pathways") {
    const condition = path[1];
    return NextResponse.json({
      condition,
      pathways: [
        {
          pathway: ["Diagnosis", "First-line medication", "Monitoring", "Adjustment"],
          frequency: 0.75,
          outcomes: ["Stable control", "Improved HbA1c"],
        },
      ],
      pathway_count: 1,
    });
  }

  if (path[0] === "related-conditions") {
    const condition = path[1];
    return NextResponse.json({
      query_condition: condition,
      matching_conditions: [condition],
      related_conditions: [
        { condition: "Hypertension", relationship: "co-occurs with", patient_id: "patient-001..." },
        { condition: "Hyperlipidemia", relationship: "co-occurs with", patient_id: "patient-001..." },
      ],
    });
  }

  return NextResponse.json({ detail: "Not found" }, { status: 404 });
}
