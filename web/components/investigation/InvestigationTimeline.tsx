"use client";

import { cn } from "@/lib/utils";
import {
  Play,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  AlertTriangle,
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
  timestamp?: string;
}

interface InvestigationTimelineProps {
  events: StreamEvent[];
  className?: string;
}

const EVENT_CONFIG: Record<
  string,
  { icon: any; color: string; bg: string; label: (event: StreamEvent) => string }
> = {
  investigation_started: {
    icon: Play,
    color: "text-blue-600",
    bg: "bg-blue-100 dark:bg-blue-900/30",
    label: () => "Investigation started",
  },
  agent_started: {
    icon: Loader2,
    color: "text-yellow-600",
    bg: "bg-yellow-100 dark:bg-yellow-900/30",
    label: (e) => `Agent started: ${e.agent?.replace("_", " ") || "unknown"}`,
  },
  agent_completed: {
    icon: CheckCircle,
    color: "text-green-600",
    bg: "bg-green-100 dark:bg-green-900/30",
    label: (e) => `Agent completed: ${e.agent?.replace("_", " ") || "unknown"}`,
  },
  agent_failed: {
    icon: XCircle,
    color: "text-red-600",
    bg: "bg-red-100 dark:bg-red-900/30",
    label: (e) => `Agent failed: ${e.agent?.replace("_", " ") || "unknown"}`,
  },
  investigation_completed: {
    icon: CheckCircle,
    color: "text-green-600",
    bg: "bg-green-100 dark:bg-green-900/30",
    label: () => "Investigation completed",
  },
  error: {
    icon: AlertTriangle,
    color: "text-red-600",
    bg: "bg-red-100 dark:bg-red-900/30",
    label: () => "Error occurred",
  },
};

export function InvestigationTimeline({ events, className }: InvestigationTimelineProps) {
  if (events.length === 0) {
    return (
      <div className={cn("text-center py-8 text-neutral-500", className)}>
        <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No events yet</p>
      </div>
    );
  }

  return (
    <div className={cn("relative", className)}>
      {/* Timeline line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-neutral-200 dark:bg-neutral-800" />

      <div className="space-y-4">
        {events.map((event, i) => {
          const config = EVENT_CONFIG[event.type] || EVENT_CONFIG.error;
          const Icon = config.icon;
          const label = config.label(event);
          const isLast = i === events.length - 1;

          return (
            <div key={i} className="relative flex items-start gap-4 pl-10">
              {/* Timeline dot */}
              <div
                className={cn(
                  "absolute left-2 top-1 w-5 h-5 rounded-full flex items-center justify-center",
                  config.bg,
                  isLast && event.type === "agent_started" && "ring-2 ring-yellow-500 ring-offset-2"
                )}
              >
                <Icon
                  className={cn(
                    "h-3 w-3",
                    config.color,
                    event.type === "agent_started" && "animate-spin"
                  )}
                />
              </div>

              {/* Event content */}
              <div
                className={cn(
                  "flex-1 p-3 rounded-lg border transition-all",
                  config.bg,
                  "border-transparent"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className={cn("text-sm font-medium", config.color)}>
                    {label}
                  </span>
                  {event.timestamp && (
                    <span className="text-xs text-neutral-500">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>

                {/* Confidence for completed agents */}
                {event.type === "agent_completed" && event.result?.confidence !== undefined && (
                  <div className="mt-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-neutral-500">Confidence:</span>
                      <div className="flex-1 h-1.5 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden max-w-[100px]">
                        <div
                          className={cn(
                            "h-full rounded-full",
                            event.result.confidence >= 0.8
                              ? "bg-green-500"
                              : event.result.confidence >= 0.6
                              ? "bg-yellow-500"
                              : "bg-red-500"
                          )}
                          style={{ width: `${event.result.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-neutral-500">
                        {Math.round(event.result.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                )}

                {/* Error message */}
                {event.type === "agent_failed" && event.error && (
                  <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                    {event.error}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
