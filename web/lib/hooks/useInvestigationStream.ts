"use client";

import { useState, useCallback, useRef } from "react";
import { apiClient } from "@/lib/api/client";

interface StreamEvent {
  type: string;
  trace_id?: string;
  patient_id?: string;
  question?: string;
  agent?: string;
  result?: {
    agent: string;
    status: string;
    summary: string;
    evidence: string[];
    confidence: number;
  };
  error?: string;
  report?: any;
  total_duration_ms?: number;
  timestamp?: string;
}

interface StreamState {
  isStreaming: boolean;
  events: StreamEvent[];
  currentAgent: string | null;
  agentsCompleted: number;
  totalAgents: number;
  error: string | null;
  report: any | null;
}

export function useInvestigationStream() {
  const [state, setState] = useState<StreamState>({
    isStreaming: false,
    events: [],
    currentAgent: null,
    agentsCompleted: 0,
    totalAgents: 0,
    error: null,
    report: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(async (patientId: string, question: string) => {
    // Reset state
    setState({
      isStreaming: true,
      events: [],
      currentAgent: null,
      agentsCompleted: 0,
      totalAgents: 0,
      error: null,
      report: null,
    });

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/v1/investigations/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ patient_id: patientId, question }),
          signal: abortControllerRef.current.signal,
        }
      );

      if (!response.ok) {
        throw new Error(`Stream error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No reader available");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const data = line.slice(6);
            try {
              const event: StreamEvent = JSON.parse(data);
              event.type = eventType || event.type;

              setState((prev) => {
                const newEvents = [...prev.events, event];

                switch (event.type) {
                  case "investigation_started":
                    return { ...prev, events: newEvents };

                  case "agent_started":
                    return {
                      ...prev,
                      events: newEvents,
                      currentAgent: event.agent || null,
                    };

                  case "agent_completed":
                    return {
                      ...prev,
                      events: newEvents,
                      agentsCompleted: prev.agentsCompleted + 1,
                      currentAgent: null,
                    };

                  case "agent_failed":
                    return {
                      ...prev,
                      events: newEvents,
                      agentsCompleted: prev.agentsCompleted + 1,
                      currentAgent: null,
                    };

                  case "investigation_completed":
                    return {
                      ...prev,
                      events: newEvents,
                      isStreaming: false,
                      report: event.report,
                    };

                  default:
                    return { ...prev, events: newEvents };
                }
              });
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: "Stream cancelled",
        }));
      } else {
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: (err as Error).message,
        }));
      }
    }
  }, []);

  const cancelStream = useCallback(() => {
    abortControllerRef.current?.abort();
    setState((prev) => ({
      ...prev,
      isStreaming: false,
      error: "Stream cancelled",
    }));
  }, []);

  return {
    ...state,
    startStream,
    cancelStream,
  };
}
