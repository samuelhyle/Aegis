"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import {
  Loader2,
  CheckCircle,
  XCircle,
  Brain,
  Clock,
  X,
  Zap,
} from "lucide-react";

interface StreamEvent {
  type: string;
  agent?: string;
  result?: {
    agent: string;
    status: string;
    summary: string;
    confidence: number;
  };
  error?: string;
  total_duration_ms?: number;
}

interface LiveInvestigationProps {
  isStreaming: boolean;
  events: StreamEvent[];
  currentAgent: string | null;
  agentsCompleted: number;
  error: string | null;
  onCancel: () => void;
  className?: string;
}

const AGENT_COLORS: Record<string, { bg: string; text: string }> = {
  diagnostic: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-700 dark:text-blue-300" },
  treatment: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-700 dark:text-green-300" },
  risk_assessment: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-700 dark:text-red-300" },
  timeline: { bg: "bg-purple-100 dark:bg-purple-900/30", text: "text-purple-700 dark:text-purple-300" },
};

export function LiveInvestigation({
  isStreaming,
  events,
  currentAgent,
  agentsCompleted,
  error,
  onCancel,
  className,
}: LiveInvestigationProps) {
  // Count agents from events
  const agentStartedEvents = events.filter((e) => e.type === "agent_started");
  const totalAgents = agentStartedEvents.length;
  const progress = totalAgents > 0 ? (agentsCompleted / totalAgents) * 100 : 0;

  // Get agent status map
  const agentStatuses: Record<string, "running" | "completed" | "failed"> = {};
  for (const event of events) {
    if (event.type === "agent_started" && event.agent) {
      agentStatuses[event.agent] = "running";
    } else if (event.type === "agent_completed" && event.agent) {
      agentStatuses[event.agent] = "completed";
    } else if (event.type === "agent_failed" && event.agent) {
      agentStatuses[event.agent] = "failed";
    }
  }

  if (!isStreaming && events.length === 0) {
    return null;
  }

  return (
    <Card className={cn("border-2", isStreaming ? "border-blue-200 dark:border-blue-800" : "border-neutral-200 dark:border-neutral-800", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {isStreaming ? (
              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
            ) : (
              <CheckCircle className="h-5 w-5 text-green-600" />
            )}
            {isStreaming ? "Investigation in Progress" : "Investigation Complete"}
          </CardTitle>
          {isStreaming && (
            <Button variant="outline" size="sm" onClick={onCancel}>
              <X className="h-4 w-4 mr-1" />
              Cancel
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-neutral-600 dark:text-neutral-400">
              {agentsCompleted} agent{agentsCompleted !== 1 ? "s" : ""} completed
            </span>
            <span className="text-neutral-600 dark:text-neutral-400">
              {Math.round(progress)}%
            </span>
          </div>
          <div className="h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Agent Status Cards */}
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(agentStatuses).map(([agent, status]) => {
            const colors = AGENT_COLORS[agent] || {
              bg: "bg-neutral-100 dark:bg-neutral-800",
              text: "text-neutral-700 dark:text-neutral-300",
            };

            return (
              <div
                key={agent}
                className={cn(
                  "p-3 rounded-lg border transition-all",
                  colors.bg,
                  status === "running" && "ring-2 ring-blue-500 ring-offset-2"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className={cn("text-sm font-medium", colors.text)}>
                    {agent.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </span>
                  {status === "completed" && <CheckCircle className="h-4 w-4 text-green-600" />}
                  {status === "failed" && <XCircle className="h-4 w-4 text-red-600" />}
                  {status === "running" && <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />}
                </div>
              </div>
            );
          })}
        </div>

        {/* Current Agent */}
        {currentAgent && (
          <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
              <span className="text-sm text-blue-700 dark:text-blue-300">
                Running: {currentAgent.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-600" />
              <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
            </div>
          </div>
        )}

        {/* Event Log */}
        {events.length > 0 && (
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {events.map((event, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-xs text-neutral-500 py-1"
              >
                <Clock className="h-3 w-3 shrink-0" />
                <span className="truncate">
                  {event.type === "investigation_started" && "Investigation started"}
                  {event.type === "agent_started" && `Agent started: ${event.agent}`}
                  {event.type === "agent_completed" && `Agent completed: ${event.agent}`}
                  {event.type === "agent_failed" && `Agent failed: ${event.agent} - ${event.error}`}
                  {event.type === "investigation_completed" && "Investigation completed"}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
