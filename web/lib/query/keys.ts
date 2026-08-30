export const queryKeys = {
  patients: {
    all: ["patients"] as const,
    list: (limit: number, offset: number) => [...queryKeys.patients.all, "list", limit, offset] as const,
    detail: (patientId: string) => [...queryKeys.patients.all, "detail", patientId] as const,
    conditions: (patientId: string) => [...queryKeys.patients.detail(patientId), "conditions"] as const,
    medications: (patientId: string) => [...queryKeys.patients.detail(patientId), "medications"] as const,
    observations: (patientId: string) => [...queryKeys.patients.detail(patientId), "observations"] as const,
    encounters: (patientId: string) => [...queryKeys.patients.detail(patientId), "encounters"] as const,
    journey: (patientId: string) => [...queryKeys.patients.detail(patientId), "journey"] as const,
    riskAssessment: (patientId: string) => [...queryKeys.patients.detail(patientId), "risk-assessment"] as const,
    drugInteractions: (patientId: string) => [...queryKeys.patients.detail(patientId), "drug-interactions"] as const,
    clinicalTrials: (patientId: string) => [...queryKeys.patients.detail(patientId), "clinical-trials"] as const,
  },
  investigations: {
    all: ["investigations"] as const,
    list: (patientId?: string, reviewed?: boolean, limit = 50, offset = 0) =>
      [...queryKeys.investigations.all, "list", patientId, reviewed, limit, offset] as const,
    detail: (traceId: string) => [...queryKeys.investigations.all, "detail", traceId] as const,
  },
  analytics: {
    graphRag: {
      evidence: (patientId: string, query: string) => ["analytics", "graph-rag", "evidence", patientId, query] as const,
      patterns: (patientId: string) => ["analytics", "graph-rag", "patterns", patientId] as const,
      causalChains: (patientId: string) => ["analytics", "graph-rag", "causal-chains", patientId] as const,
      communities: (patientId: string) => ["analytics", "graph-rag", "communities", patientId] as const,
      centrality: (patientId: string) => ["analytics", "graph-rag", "centrality", patientId] as const,
    },
    temporal: {
      analysis: (patientId: string) => ["analytics", "temporal", "analysis", patientId] as const,
      anomalies: (patientId: string, labName?: string) => ["analytics", "temporal", "anomalies", patientId, labName] as const,
      predictions: (patientId: string, labName: string, horizonDays: number) =>
        ["analytics", "temporal", "predictions", patientId, labName, horizonDays] as const,
      progression: (patientId: string, condition: string, horizonDays: number) =>
        ["analytics", "temporal", "progression", patientId, condition, horizonDays] as const,
      timeline: (patientId: string) => ["analytics", "temporal", "timeline", patientId] as const,
      trajectories: (patientId: string) => ["analytics", "temporal", "trajectories", patientId] as const,
    },
  },
  system: {
    health: () => ["system", "health"] as const,
    stats: () => ["system", "stats"] as const,
    compliance: () => ["system", "compliance"] as const,
  },
} as const;

export const queryConfig = {
  staleTime: 1000 * 60 * 5,
  gcTime: 1000 * 60 * 30,
  refetchOnWindowFocus: false,
  retry: (failureCount: number, error: Error) => {
    if (error.message.includes("404") || error.message.includes("401")) return false;
    return failureCount < 3;
  },
  retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
} as const;