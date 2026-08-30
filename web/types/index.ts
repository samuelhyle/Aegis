export interface Patient {
  patient_id: string;
  first_name: string;
  last_name: string;
  gender: string;
  birthdate: string;
  race?: string;
  ethnicity?: string;
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
}

export interface PatientDetails extends Patient {
  Id: string;
  FIRST: string;
  LAST: string;
  GENDER: string;
  BIRTHDATE: string;
  RACE: string;
  ETHNICITY: string;
  ADDRESS: string;
  CITY: string;
  STATE: string;
  ZIP: string;
}

export interface Condition {
  Id: string;
  PATIENT: string;
  CODE: string;
  DESCRIPTION: string;
  START: string;
  STOP: string;
}

export interface Medication {
  Id: string;
  PATIENT: string;
  CODE: string;
  DESCRIPTION: string;
  START: string;
  STOP: string;
  REASONCODE: string;
  REASONDESCRIPTION: string;
}

export interface Observation {
  Id: string;
  PATIENT: string;
  CODE: string;
  DESCRIPTION: string;
  VALUE: string;
  UNITS: string;
  DATE: string;
}

export interface Encounter {
  Id: string;
  PATIENT: string;
  CODE: string;
  DESCRIPTION: string;
  START: string;
  STOP: string;
  ENCOUNTERCLASS: string;
}

export interface AgentResult {
  agent: string;
  status: string;
  summary: string;
  evidence: string[];
  confidence: number;
  duration_ms: number;
}

export interface InvestigationReport {
  patient_id: string;
  question: string;
  conclusion: string;
  evidence: string[];
  confidence: number;
  review_required: boolean;
  trace_id: string;
  generated_at: string;
  agent_results: AgentResult[];
  reviewed: boolean;
  review_decision: string | null;
  reviewer_id: string | null;
  review_notes: string | null;
  reviewed_at: string | null;
}

export interface RiskScore {
  risk_type: string;
  score: number;
  risk_level: string;
  factors: string[];
  recommendations: string[];
  confidence: number;
}

export interface DrugInteraction {
  drug1: string;
  drug2: string;
  severity: string;
  description: string;
  management: string;
}

export interface ClinicalTrialMatch {
  trial_id: string;
  title: string;
  condition: string;
  phase: string;
  confidence: number;
  eligibility_status: string;
  match_reasons: string[];
  exclusion_reasons: string[];
  recommendations: string[];
}

export interface StateTransition {
  state: string;
  timestamp: string;
  evidence_ids: string[];
  relevance_scores: Record<string, number>;
}

export interface UpcomingRisk {
  condition: string;
  probability: number;
  horizon_days: number;
}

export interface StateProjection {
  from_state: string;
  to_state: string;
  probability: number;
  horizon_days: number;
  confidence: number;
  description: string;
}

export interface PatientJourney {
  patient_id: string;
  current_state: string;
  current_state_since: string;
  state_transitions: StateTransition[];
  upcoming_risks: UpcomingRisk[];
  state_projections: StateProjection[];
  generated_at: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface InvestigationRequest {
  patient_id: string;
  question: string;
}

export interface ReviewRequest {
  decision: "approved" | "rejected" | "needs_modification";
  reviewer_id: string;
  notes?: string;
}

export interface MultiAgentInvestigationRequest extends InvestigationRequest {
  agents?: string[];
  enable_debate?: boolean;
  evaluate?: boolean;
}

export interface GraphRAGResult {
  evidence: Array<{
    source_id: string;
    content: string;
    relevance_score: number;
    node_type: string;
    properties: Record<string, unknown>;
  }>;
  paths: Array<{
    nodes: string[];
    edges: string[];
    score: number;
  }>;
  patterns: Array<{
    pattern_type: string;
    nodes: string[];
    confidence: number;
    description: string;
  }>;
}

export interface TemporalAnalysis {
  timeline: Array<{
    type: string;
    date: string;
    description: string;
    status: string;
    value?: string;
    unit?: string;
  }>;
  trajectories: Record<string, {
    current_state: string;
    states: Array<{ timestamp: string; state: string }>;
    transitions: Array<{ timestamp: string; from: string; to: string }>;
    durations: Record<string, number>;
  }>;
  anomalies: Array<{
    type: string;
    description: string;
    severity: number;
    timestamp: string;
    value: number;
    expected_range: [number, number];
    confidence: number;
  }>;
  predictions: Record<string, {
    lab_name: string;
    current_value: number;
    predicted_values: Array<{ date: string; value: number; confidence: number }>;
    trend: "increasing" | "decreasing" | "stable";
  }>;
}

export interface WebSocketEvent {
  type: string;
  payload: unknown;
  timestamp: string;
}

export interface InvestigationStreamEvent extends WebSocketEvent {
  type: "agent_start" | "agent_complete" | "tool_call" | "reasoning_step" | "debate_round" | "investigation_completed" | "error";
  payload: {
    agent?: string;
    tool?: string;
    input?: unknown;
    output?: unknown;
    reasoning?: string;
    confidence?: number;
    round?: number;
    consensus?: string;
    agreements?: string[];
    disagreements?: string[];
    report?: InvestigationReport;
    message?: string;
  };
}

// --- V2 Investigation Response ---

export interface InvestigationV2Conclusion {
  summary: string;
  key_findings: string[];
  evidence: string[];
  confidence: number;
  uncertainties: string[];
  recommendations: string[];
}

export interface InvestigationV2AgentFinding {
  summary: string;
  key_findings: string[];
  confidence: number;
  reasoning_steps: number;
}

export interface InvestigationV2Debate {
  consensus: string | null;
  agreements: string[];
  disagreements: string[];
  rounds: number;
}

export interface InvestigationV2EvaluationScore {
  metric: string;
  score: number;
  explanation: string;
}

export interface InvestigationV2Evaluation {
  overall_score: number;
  scores: InvestigationV2EvaluationScore[];
  strengths: string[];
  weaknesses: string[];
}

export interface InvestigationV2Metrics {
  total_duration_ms: number;
  total_tool_calls: number;
  total_reasoning_steps: number;
  agents_used: string[];
}

export interface InvestigationV2Response {
  investigation_id: string;
  patient_id: string;
  question: string;
  conclusion: InvestigationV2Conclusion;
  agent_findings: Record<string, InvestigationV2AgentFinding>;
  debate: InvestigationV2Debate | null;
  evaluations: Record<string, InvestigationV2Evaluation>;
  safety_check: Record<string, unknown>;
  metrics: InvestigationV2Metrics;
  trace_id: string;
}

// --- Graph RAG Responses ---

export interface GraphRAGEvidenceItem {
  node_id: string;
  node_type: string;
  description: string;
  relevance_score: number;
  path_from_query: string[];
  relationship_context: string[];
  properties: Record<string, unknown>;
}

export interface GraphRAGPath {
  nodes: string[];
  edges: string[];
  length: number;
  weight: number;
  relationship_chain: string[];
}

export interface GraphRAGCommunity {
  pattern_type: string;
  description: string;
  nodes_involved: string[];
  edges_involved: string[];
  confidence: number;
  evidence: string[];
}

export interface GraphRAGPattern {
  pattern_type: string;
  description: string;
  nodes_involved: string[];
  edges_involved: string[];
  confidence: number;
  evidence: string[];
}

export interface GraphRAGStats {
  total_nodes: number;
  total_edges: number;
  evidence_count: number;
  paths_found: number;
  patterns_found: number;
}

export interface GraphRAGEvidenceResponse {
  query: string;
  evidence: GraphRAGEvidenceItem[];
  paths: GraphRAGPath[];
  communities: GraphRAGCommunity[];
  patterns: GraphRAGPattern[];
  graph_stats: GraphRAGStats;
}

export interface PatientPatternsResponse {
  patient_id: string;
  patterns: GraphRAGPattern[];
  pattern_count: number;
}

export interface CausalChainsResponse {
  patient_id: string;
  causal_chains: GraphRAGPath[];
  chain_count: number;
}

export interface PatientCommunity {
  community_id: string;
  nodes: string[];
  node_types: Record<string, number>;
  central_node: string;
  cohesion_score: number;
}

export interface PatientCommunitiesResponse {
  patient_id: string;
  communities: PatientCommunity[];
  community_count: number;
}

export interface GraphCentralityScore {
  node_id: string;
  score: number;
  description: string;
}

export interface GraphCentralityResponse {
  patient_id: string;
  centrality_scores: GraphCentralityScore[];
}

export interface TreatmentPathwaysResponse {
  condition: string;
  pathways: GraphRAGPath[];
  pathway_count: number;
}

export interface RelatedCondition {
  condition: string;
  relationship: string;
  patient_id: string;
}

export interface RelatedConditionsResponse {
  query_condition: string;
  matching_conditions: string[];
  related_conditions: RelatedCondition[];
}

// --- Temporal Responses ---

export type AnomalyType = "sudden_change" | "trend_break" | "out_of_range" | "missing_data" | "unusual_sequence";
export type AnomalySeverity = "low" | "medium" | "high" | "critical";

export interface TemporalAnomaly {
  type: AnomalyType;
  description: string;
  severity: AnomalySeverity;
  timestamp: string;
  value: number;
  expected_range: [number, number];
  confidence: number;
}

export interface TemporalAnomaliesResponse {
  patient_id: string;
  anomalies: TemporalAnomaly[];
  anomaly_count: number;
}

export interface TrajectoryPrediction {
  date: string;
  value: number;
  days_ahead: number;
}

export interface ReferenceRange {
  low: number | null;
  high: number | null;
}

export interface TrajectoryPredictionsResponse {
  patient_id: string;
  lab_name: string;
  current_value: number | null;
  trend: "improving" | "stable" | "worsening" | "volatile" | "unknown";
  predictions: TrajectoryPrediction[];
  confidence: number;
  data_points: number;
  reference_range: ReferenceRange;
}

export type HealthStateType = "healthy" | "at_risk" | "acute" | "chronic" | "recovery" | "remission" | "relapse" | "end_stage";

export interface ProgressionPrediction {
  day: number;
  state: string;
  probability: number;
}

export interface DiseaseProgressionResponse {
  patient_id: string;
  condition: string;
  current_state: HealthStateType;
  horizon_days: number;
  predictions: ProgressionPrediction[];
  model_confidence: number;
}

export interface TimelineEvent {
  type: "condition" | "medication" | "observation";
  date: string;
  description: string;
  status?: string;
  value?: string;
  unit?: string;
}

export interface PatientTimelineResponse {
  patient_id: string;
  events: TimelineEvent[];
  event_count: number;
}

export interface HealthStateData {
  current_state: string;
  states: Array<{ timestamp: string; state: string }>;
  transitions: Array<{ timestamp: string; from: string; to: string }>;
  durations: Record<string, number>;
}

export interface HealthTrajectoriesResponse {
  patient_id: string;
  trajectories: Record<string, HealthStateData>;
}

// --- Compliance ---

export type ComplianceStatus = "compliant" | "partially_compliant" | "non_compliant" | "not_applicable";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface ComplianceCheck {
  check_id: string;
  name: string;
  category: string;
  status: ComplianceStatus;
  risk_level: RiskLevel;
  description: string;
  findings: string[];
  recommendations: string[];
}

export interface ComplianceReportResponse {
  report_id: string;
  generated_at: string;
  overall_status: ComplianceStatus;
  risk_summary: Record<string, number>;
  checks: ComplianceCheck[];
  recommendations: string[];
}

// --- System Stats ---
// Note: Frontend uses these field names; backend may return different shapes.
// The API response is adapted at the hook level or the backend should be updated.
export interface SystemStatsResponse {
  total_patients: number;
  active_investigations: number;
  high_risk_alerts: number;
  pending_reviews: number;
  patients?: number;
  table_stats?: Record<string, unknown>;
  traces?: {
    total: number;
    reviewed: number;
    pending_review: number;
  };
  metrics?: Record<string, unknown>;
}

// --- Evaluation (v2) ---

export type MetricTypeName = "accuracy" | "completeness" | "grounding" | "relevance" | "confidence_calibration" | "reasoning_quality" | "tool_efficiency" | "latency" | "safety";

export interface EvaluationCase {
  case_id: string;
  patient_id: string;
  question: string;
  category: string;
  difficulty: string;
  expected_findings: string[];
  expected_confidence_range: [number, number];
}

export interface EvaluationBenchmarkResponse {
  cases: EvaluationCase[];
  total: number;
  categories: string[];
  difficulties: string[];
}

export interface EvaluationMetricInfo {
  name: string;
  description: string;
}

export interface EvaluationMetricsResponse {
  metrics: EvaluationMetricInfo[];
}

export interface EvaluationScoreDetail {
  metric: string;
  score: number;
  explanation: string;
}

export interface EvaluationResultDetail {
  case_id: string;
  agent_name: string;
  status: string;
  overall_score: number;
  latency_ms: number;
  scores: EvaluationScoreDetail[];
  errors: string[];
}

export interface EvaluationLatencyStats {
  mean: number;
  median: number;
  p95: number;
  min: number;
  max: number;
}

export interface RunEvaluationResponse {
  report_id: string;
  benchmark_name: string;
  agent_name: string;
  generated_at: string;
  summary: {
    total_cases: number;
    completed_cases: number;
    failed_cases: number;
    overall_score: number;
  };
  metric_scores: Record<string, number>;
  category_scores: Record<string, number>;
  difficulty_scores: Record<string, number>;
  latency_stats: EvaluationLatencyStats;
  results: EvaluationResultDetail[];
}

export interface EvaluationHistoryV2Report {
  report_id: string;
  agent_name: string;
  overall_score: number;
  total_cases: number;
  completed_cases: number;
  generated_at: string;
}

export interface EvaluationHistoryV2Response {
  reports: EvaluationHistoryV2Report[];
  total: number;
}

export interface EvaluationTrendsV2Response {
  overall_scores: number[];
  metric_trends: Record<string, {
    scores: number[];
    trend: "improving" | "declining";
    change: number;
  }>;
}

export interface CompareEvaluationsResponse {
  report1_id: string;
  report2_id: string;
  overall_change: number;
  metric_changes: Record<string, { before: number; after: number; change: number }>;
  category_changes: Record<string, { before: number; after: number; change: number }>;
}

// --- Evaluation (v3) ---

export interface EvaluationHistoryReport {
  report_id: string;
  agent_name: string;
  benchmark_name: string | null;
  overall_score: number;
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  metric_scores: string;
  category_scores: string;
  difficulty_scores: string;
  latency_stats: string;
  generated_at: string;
  metadata: string;
}

export interface EvaluationHistoryResponse {
  reports: EvaluationHistoryReport[];
  total: number;
}

export interface EvaluationTrendsReport {
  report_id: string;
  overall_score: number;
  generated_at: string;
}

export interface EvaluationTrendsResponse {
  reports: EvaluationTrendsReport[];
  trend: "improving" | "declining";
  change: number;
  mean: number;
  min: number;
  max: number;
  trend_direction?: string;
  average_improvement?: number;
  total_reports?: number;
}

export interface EvaluationReportDetail {
  report_id: string;
  agent_name: string;
  benchmark_name: string | null;
  overall_score: number;
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  metric_scores: string;
  category_scores: string;
  difficulty_scores: string;
  latency_stats: string;
  generated_at: string;
  metadata: string;
}

export interface SyntheticBenchmarkCase {
  case_id: string;
  patient_id: string;
  question: string;
  category: string;
  difficulty: string;
}

export interface SyntheticBenchmarkResponse {
  cases_generated: number;
  categories: string[];
  difficulties: string[];
  cases: SyntheticBenchmarkCase[];
}

export interface ExtendedMetricScore {
  score: number;
  details: Record<string, unknown>;
}

export interface ExtendedMetricsResponse {
  factuality: ExtendedMetricScore;
  hallucination_rate: ExtendedMetricScore;
  citation_correctness: ExtendedMetricScore;
  clinical_safety: ExtendedMetricScore;
  token_efficiency?: ExtendedMetricScore;
  cost_efficiency?: ExtendedMetricScore;
}

// --- Search ---

export interface VectorSearchResult {
  id: string;
  patient_id: string;
  source_type: string;
  source_id: string;
  chunk_text: string;
  similarity: number;
  metadata: Record<string, unknown>;
}

export interface SearchVectorsResponse {
  results: VectorSearchResult[];
  total: number;
  query: string;
}

// --- Agent Metrics ---

export interface AgentMetricSummary {
  agent: string;
  invocations: number;
  successes: number;
  failures: number;
  success_rate: number;
  avg_duration_ms: number;
  p50_duration_ms: number;
  p95_duration_ms: number;
  total_retries: number;
  active: number;
  error_types: Record<string, number>;
}

export type AgentMetricsResponse = Record<string, AgentMetricSummary>;

// --- Agent & Tool Listings ---

export interface AgentInfo {
  name: string;
  role: string;
  description: string;
  capabilities: string[];
}

export interface ListAgentsResponse {
  agents: AgentInfo[];
}

export type ToolCategory = "data_access" | "knowledge_graph" | "evidence_retrieval" | "clinical_reasoning" | "visualization" | "external";

export interface ToolParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
}

export interface ToolInfo {
  name: string;
  description: string;
  category: ToolCategory;
  parameters: ToolParameter[];
  returns: string;
}

export interface ListToolsResponse {
  tools: ToolInfo[];
  total: number;
}