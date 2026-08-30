import type {
  Patient,
  PatientDetails,
  Condition,
  Medication,
  Observation,
  Encounter,
  PatientJourney,
  InvestigationReport,
  RiskScore,
  DrugInteraction,
  ClinicalTrialMatch,
  TemporalAnalysis,
  MultiAgentInvestigationRequest,
  InvestigationV2Response,
  GraphRAGEvidenceResponse,
  PatientPatternsResponse,
  CausalChainsResponse,
  PatientCommunitiesResponse,
  GraphCentralityResponse,
  TemporalAnomaliesResponse,
  TrajectoryPredictionsResponse,
  DiseaseProgressionResponse,
  PatientTimelineResponse,
  HealthTrajectoriesResponse,
  ComplianceReportResponse,
  SystemStatsResponse,
  EvaluationHistoryResponse,
  EvaluationTrendsResponse,
  EvaluationReportDetail,
  SyntheticBenchmarkResponse,
  ExtendedMetricsResponse,
  SearchVectorsResponse,
  AgentMetricsResponse,
  ListAgentsResponse,
  ListToolsResponse,
  TreatmentPathwaysResponse,
  RelatedConditionsResponse,
  EvaluationBenchmarkResponse,
  EvaluationMetricsResponse,
  RunEvaluationResponse,
  EvaluationHistoryV2Response,
  EvaluationTrendsV2Response,
  CompareEvaluationsResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;
  private apiKey: string | null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.apiKey = null;
  }

  setApiKey(key: string) {
    this.apiKey = key;
  }

  private async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.detail || error.message || `API error: ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async getHealth() {
    return this.fetch<{ status: string; service: string; version: string }>("/health");
  }

  async listPatients(limit = 50, offset = 0) {
    return this.fetch<{ patients: Patient[]; total: number; has_more: boolean }>(
      `/v1/patients?limit=${limit}&offset=${offset}`
    );
  }

  async getPatient(patientId: string) {
    return this.fetch<PatientDetails>(`/v1/patients/${patientId}`);
  }

  async getPatientConditions(patientId: string) {
    return this.fetch<{ conditions: Condition[]; total: number }>(`/v1/patients/${patientId}/conditions`);
  }

  async getPatientMedications(patientId: string) {
    return this.fetch<{ medications: Medication[]; total: number }>(`/v1/patients/${patientId}/medications`);
  }

  async getPatientObservations(patientId: string) {
    return this.fetch<{ observations: Observation[]; total: number }>(`/v1/patients/${patientId}/observations`);
  }

  async getPatientEncounters(patientId: string) {
    return this.fetch<{ encounters: Encounter[]; total: number }>(`/v1/patients/${patientId}/encounters`);
  }

  async getPatientJourney(patientId: string) {
    return this.fetch<PatientJourney>(`/v1/patients/${patientId}/journey`);
  }

  async runInvestigation(patientId: string, question: string) {
    return this.fetch<InvestigationReport>("/v1/investigations", {
      method: "POST",
      body: JSON.stringify({ patient_id: patientId, question }),
    });
  }

  async runInvestigationV2(request: MultiAgentInvestigationRequest) {
    return this.fetch<InvestigationV2Response>("/v2/investigations", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async streamInvestigation(patientId: string, question: string) {
    const response = await fetch(`${this.baseUrl}/v1/investigations/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.apiKey ? { "X-API-Key": this.apiKey } : {}),
      },
      body: JSON.stringify({ patient_id: patientId, question }),
    });

    if (!response.ok) {
      throw new Error(`Stream error: ${response.status}`);
    }

    return response.body?.getReader();
  }

  async listTraces(patientId?: string, reviewed?: boolean, limit = 50, offset = 0) {
    const params = new URLSearchParams();
    if (patientId) params.set("patient_id", patientId);
    if (reviewed !== undefined) params.set("reviewed", String(reviewed));
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    return this.fetch<{ traces: InvestigationReport[]; total: number; has_more: boolean }>(
      `/v1/traces?${params.toString()}`
    );
  }

  async getTrace(traceId: string) {
    return this.fetch<InvestigationReport>(`/v1/traces/${traceId}`);
  }

  async reviewTrace(traceId: string, decision: "approved" | "rejected" | "needs_modification", reviewerId: string, notes = "") {
    return this.fetch<InvestigationReport>(`/v1/traces/${traceId}/review`, {
      method: "POST",
      body: JSON.stringify({ decision, reviewer_id: reviewerId, notes }),
    });
  }

  async getRiskAssessment(patientId: string) {
    return this.fetch<{ risks: RiskScore[] }>(`/v1/patients/${patientId}/risk-assessment`);
  }

  async getDrugInteractions(patientId: string) {
    return this.fetch<{
      medication_count: number;
      risk_level: string;
      risk_score: number;
      interactions: DrugInteraction[];
      recommendations: string[];
    }>(`/v1/patients/${patientId}/drug-interactions`);
  }

  async getClinicalTrials(patientId: string) {
    return this.fetch<{ matches: ClinicalTrialMatch[] }>(`/v1/patients/${patientId}/clinical-trials`);
  }

  async getGraphRAGEvidence(patientId: string, query: string) {
    return this.fetch<GraphRAGEvidenceResponse>(`/v2/graph-rag/${patientId}?query=${encodeURIComponent(query)}`);
  }

  async getPatientPatterns(patientId: string) {
    return this.fetch<PatientPatternsResponse>(`/v2/graph-rag/${patientId}/patterns`);
  }

  async getCausalChains(patientId: string) {
    return this.fetch<CausalChainsResponse>(`/v2/graph-rag/${patientId}/causal-chains`);
  }

  async getPatientCommunities(patientId: string) {
    return this.fetch<PatientCommunitiesResponse>(`/v2/graph-rag/${patientId}/communities`);
  }

  async getGraphCentrality(patientId: string) {
    return this.fetch<GraphCentralityResponse>(`/v2/graph-rag/${patientId}/centrality`);
  }

  async getTemporalAnalysis(patientId: string) {
    return this.fetch<TemporalAnalysis>(`/v2/temporal/${patientId}`);
  }

  async getTemporalAnomalies(patientId: string, labName?: string) {
    const params = labName ? `?lab_name=${encodeURIComponent(labName)}` : "";
    return this.fetch<TemporalAnomaliesResponse>(`/v2/temporal/${patientId}/anomalies${params}`);
  }

  async getTrajectoryPredictions(patientId: string, labName: string = "glucose", horizonDays = 90) {
    return this.fetch<TrajectoryPredictionsResponse>(`/v2/temporal/${patientId}/predictions?lab_name=${encodeURIComponent(labName)}&horizon_days=${horizonDays}`);
  }

  async getDiseaseProgression(patientId: string, condition: string, horizonDays = 365) {
    return this.fetch<DiseaseProgressionResponse>(`/v2/temporal/${patientId}/progression/${encodeURIComponent(condition)}?horizon_days=${horizonDays}`);
  }

  async getPatientTimeline(patientId: string) {
    return this.fetch<PatientTimelineResponse>(`/v2/temporal/${patientId}/timeline`);
  }

  async getHealthTrajectories(patientId: string) {
    return this.fetch<HealthTrajectoriesResponse>(`/v2/temporal/${patientId}/trajectories`);
  }

  async getComplianceReport() {
    return this.fetch<ComplianceReportResponse>("/v1/compliance");
  }

  async getSystemStats() {
    return this.fetch<SystemStatsResponse>("/v1/stats");
  }

  // Extended evaluation endpoints (v3)
  async getEvaluationHistory(agentName?: string, limit = 20) {
    const params = new URLSearchParams();
    if (agentName) params.set("agent_name", agentName);
    params.set("limit", String(limit));
    return this.fetch<EvaluationHistoryResponse>(`/v3/evaluation/history?${params.toString()}`);
  }

  async getEvaluationTrends(agentName?: string) {
    const params = agentName ? `?agent_name=${agentName}` : "";
    return this.fetch<EvaluationTrendsResponse>(`/v3/evaluation/trends${params}`);
  }

  async getEvaluationReport(reportId: string) {
    return this.fetch<EvaluationReportDetail>(`/v3/evaluation/report/${reportId}`);
  }

  async generateSyntheticBenchmark(maxPatients = 10) {
    return this.fetch<SyntheticBenchmarkResponse>("/v3/evaluation/synthetic-benchmark", {
      method: "POST",
      body: JSON.stringify({ max_patients: maxPatients }),
    });
  }

  async calculateExtendedMetrics(conclusion: string, evidence: string[]) {
    return this.fetch<ExtendedMetricsResponse>("/v3/evaluation/extended-metrics", {
      method: "POST",
      body: JSON.stringify({ conclusion, evidence: evidence.join(", ") }),
    });
  }

  async searchVectors(query: string, patientId?: string, sourceTypes?: string[], topK = 10) {
    const params = new URLSearchParams({ query, top_k: String(topK) });
    if (patientId) params.set("patient_id", patientId);
    if (sourceTypes) params.set("source_types", sourceTypes.join(","));
    return this.fetch<SearchVectorsResponse>(`/v1/search?${params.toString()}`);
  }

  async getBenchmarkResults() {
    return this.fetch<unknown>("/v1/benchmark/results");
  }

  async runBenchmark(questions?: string[]) {
    return this.fetch<unknown>("/v1/benchmark/run", {
      method: "POST",
      body: JSON.stringify({ questions }),
    });
  }

  // Observability endpoints
  async getMetrics() {
    return this.fetch<string>("/metrics");
  }

  async getAgentMetrics() {
    return this.fetch<AgentMetricsResponse>("/metrics/agents");
  }

  // Agent endpoints
  async listAgents() {
    return this.fetch<ListAgentsResponse>("/v2/agents");
  }

  async listTools(category?: string) {
    const params = category ? `?category=${encodeURIComponent(category)}` : "";
    return this.fetch<ListToolsResponse>(`/v2/tools${params}`);
  }

  // Graph RAG - Treatment Pathways
  async getTreatmentPathways(condition: string) {
    return this.fetch<TreatmentPathwaysResponse>(`/v2/graph-rag/treatment-pathways/${encodeURIComponent(condition)}`);
  }

  async getRelatedConditions(condition: string) {
    return this.fetch<RelatedConditionsResponse>(`/v2/graph-rag/related-conditions/${encodeURIComponent(condition)}`);
  }

  // Evaluation framework (v2)
  async getEvaluationBenchmark() {
    return this.fetch<EvaluationBenchmarkResponse>("/v2/evaluation/benchmark");
  }

  async getEvaluationMetrics() {
    return this.fetch<EvaluationMetricsResponse>("/v2/evaluation/metrics");
  }

  async runEvaluation(agentName: string, config?: Record<string, unknown>) {
    return this.fetch<RunEvaluationResponse>("/v2/evaluation/run", {
      method: "POST",
      body: JSON.stringify({ agent_name: agentName, ...config }),
    });
  }

  async getEvaluationHistoryV2(agentName?: string, limit = 20) {
    const params = new URLSearchParams();
    if (agentName) params.set("agent_name", agentName);
    params.set("limit", String(limit));
    return this.fetch<EvaluationHistoryV2Response>(`/v2/evaluation/history?${params.toString()}`);
  }

  async getEvaluationReportV2(reportId: string) {
    return this.fetch<RunEvaluationResponse>(`/v2/evaluation/report/${reportId}`);
  }

  async getEvaluationTrendsV2(agentName?: string) {
    const params = agentName ? `?agent_name=${agentName}` : "";
    return this.fetch<EvaluationTrendsV2Response>(`/v2/evaluation/trends${params}`);
  }

  async compareEvaluations(reportId1: string, reportId2: string) {
    return this.fetch<CompareEvaluationsResponse>(`/v2/evaluation/compare?report1=${reportId1}&report2=${reportId2}`);
  }
}

export const apiClient = new ApiClient();

export function getApiClient() {
  return apiClient;
}