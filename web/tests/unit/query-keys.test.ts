import { describe, it, expect } from "vitest";
import { queryKeys, queryConfig } from "@/lib/query/keys";

describe("queryKeys", () => {
  describe("patients", () => {
    it("generates list key", () => {
      const key = queryKeys.patients.list(10, 0);
      expect(key).toEqual(["patients", "list", 10, 0]);
    });

    it("generates detail key", () => {
      const key = queryKeys.patients.detail("p1");
      expect(key).toEqual(["patients", "detail", "p1"]);
    });

    it("generates conditions key", () => {
      const key = queryKeys.patients.conditions("p1");
      expect(key).toEqual(["patients", "detail", "p1", "conditions"]);
    });

    it("generates medications key", () => {
      const key = queryKeys.patients.medications("p1");
      expect(key).toEqual(["patients", "detail", "p1", "medications"]);
    });

    it("generates observations key", () => {
      const key = queryKeys.patients.observations("p1");
      expect(key).toEqual(["patients", "detail", "p1", "observations"]);
    });

    it("generates encounters key", () => {
      const key = queryKeys.patients.encounters("p1");
      expect(key).toEqual(["patients", "detail", "p1", "encounters"]);
    });

    it("generates journey key", () => {
      const key = queryKeys.patients.journey("p1");
      expect(key).toEqual(["patients", "detail", "p1", "journey"]);
    });

    it("generates risk assessment key", () => {
      const key = queryKeys.patients.riskAssessment("p1");
      expect(key).toEqual(["patients", "detail", "p1", "risk-assessment"]);
    });

    it("generates drug interactions key", () => {
      const key = queryKeys.patients.drugInteractions("p1");
      expect(key).toEqual(["patients", "detail", "p1", "drug-interactions"]);
    });

    it("generates clinical trials key", () => {
      const key = queryKeys.patients.clinicalTrials("p1");
      expect(key).toEqual(["patients", "detail", "p1", "clinical-trials"]);
    });
  });

  describe("investigations", () => {
    it("generates list key", () => {
      const key = queryKeys.investigations.list("p1", true, 10, 0);
      expect(key).toEqual(["investigations", "list", "p1", true, 10, 0]);
    });

    it("generates detail key", () => {
      const key = queryKeys.investigations.detail("t1");
      expect(key).toEqual(["investigations", "detail", "t1"]);
    });
  });

  describe("analytics.graphRag", () => {
    it("generates evidence key", () => {
      const key = queryKeys.analytics.graphRag.evidence("p1", "diabetes");
      expect(key).toEqual(["analytics", "graph-rag", "evidence", "p1", "diabetes"]);
    });

    it("generates patterns key", () => {
      const key = queryKeys.analytics.graphRag.patterns("p1");
      expect(key).toEqual(["analytics", "graph-rag", "patterns", "p1"]);
    });

    it("generates causal chains key", () => {
      const key = queryKeys.analytics.graphRag.causalChains("p1");
      expect(key).toEqual(["analytics", "graph-rag", "causal-chains", "p1"]);
    });

    it("generates communities key", () => {
      const key = queryKeys.analytics.graphRag.communities("p1");
      expect(key).toEqual(["analytics", "graph-rag", "communities", "p1"]);
    });

    it("generates centrality key", () => {
      const key = queryKeys.analytics.graphRag.centrality("p1");
      expect(key).toEqual(["analytics", "graph-rag", "centrality", "p1"]);
    });
  });

  describe("analytics.temporal", () => {
    it("generates analysis key", () => {
      const key = queryKeys.analytics.temporal.analysis("p1");
      expect(key).toEqual(["analytics", "temporal", "analysis", "p1"]);
    });

    it("generates anomalies key", () => {
      const key = queryKeys.analytics.temporal.anomalies("p1", "glucose");
      expect(key).toEqual(["analytics", "temporal", "anomalies", "p1", "glucose"]);
    });

    it("generates predictions key", () => {
      const key = queryKeys.analytics.temporal.predictions("p1", "glucose", 90);
      expect(key).toEqual(["analytics", "temporal", "predictions", "p1", "glucose", 90]);
    });

    it("generates progression key", () => {
      const key = queryKeys.analytics.temporal.progression("p1", "diabetes", 365);
      expect(key).toEqual(["analytics", "temporal", "progression", "p1", "diabetes", 365]);
    });

    it("generates timeline key", () => {
      const key = queryKeys.analytics.temporal.timeline("p1");
      expect(key).toEqual(["analytics", "temporal", "timeline", "p1"]);
    });

    it("generates trajectories key", () => {
      const key = queryKeys.analytics.temporal.trajectories("p1");
      expect(key).toEqual(["analytics", "temporal", "trajectories", "p1"]);
    });
  });

  describe("system", () => {
    it("generates health key", () => {
      const key = queryKeys.system.health();
      expect(key).toEqual(["system", "health"]);
    });

    it("generates stats key", () => {
      const key = queryKeys.system.stats();
      expect(key).toEqual(["system", "stats"]);
    });

    it("generates compliance key", () => {
      const key = queryKeys.system.compliance();
      expect(key).toEqual(["system", "compliance"]);
    });
  });
});

describe("queryConfig", () => {
  it("has staleTime", () => {
    expect(queryConfig.staleTime).toBeGreaterThan(0);
  });

  it("has gcTime", () => {
    expect(queryConfig.gcTime).toBeGreaterThan(0);
  });

  it("has retry config as function", () => {
    expect(typeof queryConfig.retry).toBe("function");
  });

  it("has retryDelay config as function", () => {
    expect(typeof queryConfig.retryDelay).toBe("function");
  });

  it("retry returns false for 404 errors", () => {
    const result = queryConfig.retry(1, new Error("404 not found"));
    expect(result).toBe(false);
  });

  it("retry returns false for 401 errors", () => {
    const result = queryConfig.retry(1, new Error("401 unauthorized"));
    expect(result).toBe(false);
  });

  it("retry returns true for other errors under limit", () => {
    const result = queryConfig.retry(1, new Error("500 server error"));
    expect(result).toBe(true);
  });

  it("retry returns false when limit exceeded", () => {
    const result = queryConfig.retry(3, new Error("500 server error"));
    expect(result).toBe(false);
  });

  it("retryDelay returns exponential backoff", () => {
    expect(queryConfig.retryDelay(0)).toBe(1000);
    expect(queryConfig.retryDelay(1)).toBe(2000);
    expect(queryConfig.retryDelay(2)).toBe(4000);
  });

  it("retryDelay caps at 30000", () => {
    expect(queryConfig.retryDelay(10)).toBe(30000);
  });
});
