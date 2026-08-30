"use client";

import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys, queryConfig } from "@/lib/query/keys";
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
} from "@/types";

export function usePatients(limit = 50, offset = 0) {
  return useQuery({
    queryKey: queryKeys.patients.list(limit, offset),
    queryFn: () => apiClient.listPatients(limit, offset),
    ...queryConfig,
  });
}

export function useInfinitePatients(limit = 50) {
  return useInfiniteQuery({
    queryKey: queryKeys.patients.all,
    queryFn: ({ pageParam = 0 }) => apiClient.listPatients(limit, pageParam * limit),
    getNextPageParam: (lastPage) => (lastPage.has_more ? (lastPage.total - lastPage.total % limit) / limit + 1 : undefined),
    initialPageParam: 0,
    ...queryConfig,
  });
}

export function usePatient(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.detail(patientId),
    queryFn: () => apiClient.getPatient(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function usePatientConditions(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.conditions(patientId),
    queryFn: () => apiClient.getPatientConditions(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function usePatientMedications(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.medications(patientId),
    queryFn: () => apiClient.getPatientMedications(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function usePatientObservations(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.observations(patientId),
    queryFn: () => apiClient.getPatientObservations(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function usePatientEncounters(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.encounters(patientId),
    queryFn: () => apiClient.getPatientEncounters(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function usePatientJourney(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.journey(patientId),
    queryFn: () => apiClient.getPatientJourney(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useRiskAssessment(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.riskAssessment(patientId),
    queryFn: () => apiClient.getRiskAssessment(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useDrugInteractions(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.drugInteractions(patientId),
    queryFn: () => apiClient.getDrugInteractions(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useClinicalTrials(patientId: string) {
  return useQuery({
    queryKey: queryKeys.patients.clinicalTrials(patientId),
    queryFn: () => apiClient.getClinicalTrials(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useInvestigations(patientId?: string, reviewed?: boolean, limit = 50, offset = 0) {
  return useQuery({
    queryKey: queryKeys.investigations.list(patientId, reviewed, limit, offset),
    queryFn: () => apiClient.listTraces(patientId, reviewed, limit, offset),
    ...queryConfig,
  });
}

export function useInfiniteInvestigations(patientId?: string, reviewed?: boolean, limit = 50) {
  return useInfiniteQuery({
    queryKey: queryKeys.investigations.all,
    queryFn: ({ pageParam = 0 }) => apiClient.listTraces(patientId, reviewed, limit, pageParam * limit),
    getNextPageParam: (lastPage) => (lastPage.has_more ? (lastPage.total - lastPage.total % limit) / limit + 1 : undefined),
    initialPageParam: 0,
    ...queryConfig,
  });
}

export function useInvestigation(traceId: string) {
  return useQuery({
    queryKey: queryKeys.investigations.detail(traceId),
    queryFn: () => apiClient.getTrace(traceId),
    enabled: !!traceId,
    ...queryConfig,
  });
}

export function useRunInvestigation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ patientId, question }: { patientId: string; question: string }) =>
      apiClient.runInvestigation(patientId, question),
    onSuccess: (report) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.investigations.all });
      queryClient.setQueryData(queryKeys.investigations.detail(report.trace_id), report);
    },
  });
}

export function useRunInvestigationV2() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: MultiAgentInvestigationRequest) => apiClient.runInvestigationV2(request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.investigations.all });
      if (data.trace_id) {
        queryClient.setQueryData(queryKeys.investigations.detail(data.trace_id), data);
      }
    },
  });
}

export function useReviewInvestigation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      traceId,
      decision,
      reviewerId,
      notes,
    }: {
      traceId: string;
      decision: "approved" | "rejected" | "needs_modification";
      reviewerId: string;
      notes?: string;
    }) => apiClient.reviewTrace(traceId, decision, reviewerId, notes),
    onSuccess: (report) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.investigations.all });
      queryClient.setQueryData(queryKeys.investigations.detail(report.trace_id), report);
    },
  });
}

export function useGraphRAGEvidence(patientId: string, query: string) {
  return useQuery({
    queryKey: queryKeys.analytics.graphRag.evidence(patientId, query),
    queryFn: () => apiClient.getGraphRAGEvidence(patientId, query),
    enabled: !!patientId && !!query,
    ...queryConfig,
  });
}

export function usePatientPatterns(patientId: string) {
  return useQuery({
    queryKey: queryKeys.analytics.graphRag.patterns(patientId),
    queryFn: () => apiClient.getPatientPatterns(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useCausalChains(patientId: string) {
  return useQuery({
    queryKey: queryKeys.analytics.graphRag.causalChains(patientId),
    queryFn: () => apiClient.getCausalChains(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function usePatientCommunities(patientId: string) {
  return useQuery({
    queryKey: queryKeys.analytics.graphRag.communities(patientId),
    queryFn: () => apiClient.getPatientCommunities(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useGraphCentrality(patientId: string) {
  return useQuery({
    queryKey: queryKeys.analytics.graphRag.centrality(patientId),
    queryFn: () => apiClient.getGraphCentrality(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useTemporalAnalysis(patientId: string) {
  return useQuery({
    queryKey: queryKeys.analytics.temporal.analysis(patientId),
    queryFn: () => apiClient.getTemporalAnalysis(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useTemporalAnomalies(patientId: string, labName?: string) {
  return useQuery({
    queryKey: queryKeys.analytics.temporal.anomalies(patientId, labName),
    queryFn: () => apiClient.getTemporalAnomalies(patientId, labName),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useTrajectoryPredictions(patientId: string, labName: string = "glucose", horizonDays = 90) {
  return useQuery({
    queryKey: queryKeys.analytics.temporal.predictions(patientId, labName, horizonDays),
    queryFn: () => apiClient.getTrajectoryPredictions(patientId, labName, horizonDays),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useDiseaseProgression(patientId: string, condition: string, horizonDays = 365) {
  return useQuery({
    queryKey: queryKeys.analytics.temporal.progression(patientId, condition, horizonDays),
    queryFn: () => apiClient.getDiseaseProgression(patientId, condition, horizonDays),
    enabled: !!patientId && !!condition,
    ...queryConfig,
  });
}

export function usePatientTimeline(patientId: string) {
  return useQuery({
    queryKey: queryKeys.analytics.temporal.timeline(patientId),
    queryFn: () => apiClient.getPatientTimeline(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useHealthTrajectories(patientId: string) {
  return useQuery({
    queryKey: queryKeys.analytics.temporal.trajectories(patientId),
    queryFn: () => apiClient.getHealthTrajectories(patientId),
    enabled: !!patientId,
    ...queryConfig,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: queryKeys.system.health(),
    queryFn: () => apiClient.getHealth(),
    ...queryConfig,
    refetchInterval: 30000,
  });
}

export function useSystemStats() {
  return useQuery({
    queryKey: queryKeys.system.stats(),
    queryFn: () => apiClient.getSystemStats(),
    ...queryConfig,
  });
}

export function useComplianceReport() {
  return useQuery({
    queryKey: queryKeys.system.compliance(),
    queryFn: () => apiClient.getComplianceReport(),
    ...queryConfig,
  });
}

export function useVectorSearch(query: string, patientId?: string, sourceTypes?: string[], topK = 10) {
  return useQuery({
    queryKey: ["search", "vectors", query, patientId, sourceTypes, topK],
    queryFn: () => apiClient.searchVectors(query, patientId, sourceTypes, topK),
    enabled: !!query && query.length >= 3,
    ...queryConfig,
  });
}

export function useBenchmarkResults() {
  return useQuery({
    queryKey: ["benchmark", "results"],
    queryFn: () => apiClient.getBenchmarkResults(),
    ...queryConfig,
  });
}

export function useRunBenchmark() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (questions?: string[]) => apiClient.runBenchmark(questions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["benchmark"] });
    },
  });
}

// Observability hooks
export function useAgentMetrics() {
  return useQuery({
    queryKey: ["system", "agentMetrics"],
    queryFn: () => apiClient.getAgentMetrics(),
    ...queryConfig,
    refetchInterval: 30000,
  });
}

// Agent hooks
export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: () => apiClient.listAgents(),
    ...queryConfig,
  });
}

export function useTools(category?: string) {
  return useQuery({
    queryKey: ["tools", category],
    queryFn: () => apiClient.listTools(category),
    ...queryConfig,
  });
}

// Graph RAG - Treatment Pathways
export function useTreatmentPathways(condition: string) {
  return useQuery({
    queryKey: ["treatmentPathways", condition],
    queryFn: () => apiClient.getTreatmentPathways(condition),
    enabled: !!condition,
    ...queryConfig,
  });
}

export function useRelatedConditions(condition: string) {
  return useQuery({
    queryKey: ["relatedConditions", condition],
    queryFn: () => apiClient.getRelatedConditions(condition),
    enabled: !!condition,
    ...queryConfig,
  });
}

// Evaluation framework hooks (v2)
export function useEvaluationBenchmark() {
  return useQuery({
    queryKey: ["evaluation", "benchmark"],
    queryFn: () => apiClient.getEvaluationBenchmark(),
    ...queryConfig,
  });
}

export function useEvaluationMetrics() {
  return useQuery({
    queryKey: ["evaluation", "metrics"],
    queryFn: () => apiClient.getEvaluationMetrics(),
    ...queryConfig,
  });
}

export function useRunEvaluation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentName, config }: { agentName: string; config?: any }) =>
      apiClient.runEvaluation(agentName, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluation"] });
    },
  });
}

export function useCompareEvaluations(reportId1: string, reportId2: string) {
  return useQuery({
    queryKey: ["evaluation", "compare", reportId1, reportId2],
    queryFn: () => apiClient.compareEvaluations(reportId1, reportId2),
    enabled: !!reportId1 && !!reportId2,
    ...queryConfig,
  });
}