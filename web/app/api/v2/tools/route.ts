import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const category = searchParams.get("category");

  const tools = [
    {
      name: "get_patient_conditions",
      description: "Retrieve all conditions for a patient",
      category: "data_retrieval",
      parameters: [
        { name: "patient_id", type: "string", description: "Patient identifier", required: true },
      ],
      returns: "List of patient conditions",
    },
    {
      name: "get_patient_medications",
      description: "Retrieve all medications for a patient",
      category: "data_retrieval",
      parameters: [
        { name: "patient_id", type: "string", description: "Patient identifier", required: true },
      ],
      returns: "List of patient medications",
    },
    {
      name: "get_patient_observations",
      description: "Retrieve lab results and observations for a patient",
      category: "data_retrieval",
      parameters: [
        { name: "patient_id", type: "string", description: "Patient identifier", required: true },
      ],
      returns: "List of patient observations",
    },
    {
      name: "search_medical_literature",
      description: "Search medical literature for relevant information",
      category: "knowledge",
      parameters: [
        { name: "query", type: "string", description: "Search query", required: true },
      ],
      returns: "Search results from medical literature",
    },
    {
      name: "calculate_risk_score",
      description: "Calculate risk scores for various conditions",
      category: "analysis",
      parameters: [
        { name: "patient_id", type: "string", description: "Patient identifier", required: true },
        { name: "risk_type", type: "string", description: "Type of risk to calculate", required: true },
      ],
      returns: "Risk score and factors",
    },
  ];

  const filtered = category
    ? tools.filter((t) => t.category === category)
    : tools;

  return NextResponse.json({
    tools: filtered,
    total: filtered.length,
  });
}
