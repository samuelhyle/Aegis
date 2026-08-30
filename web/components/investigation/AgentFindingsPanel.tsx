"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import {
  Stethoscope,
  Pill,
  AlertTriangle,
  Clock,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  Loader2,
  Brain,
  FileText,
} from "lucide-react";

interface AgentFinding {
  agent: string;
  status: string;
  summary: string;
  key_findings?: string[];
  evidence?: string[];
  confidence: number;
  reasoning_steps?: number;
  duration_ms?: number;
}

interface AgentFindingsPanelProps {
  findings: Record<string, AgentFinding>;
  className?: string;
}

const AGENT_CONFIG: Record<
  string,
  { name: string; icon: any; color: string; bg: string }
> = {
  diagnostic: {
    name: "Diagnostic Agent",
    icon: Stethoscope,
    color: "text-blue-600",
    bg: "bg-blue-100 dark:bg-blue-900/30",
  },
  treatment: {
    name: "Treatment Agent",
    icon: Pill,
    color: "text-green-600",
    bg: "bg-green-100 dark:bg-green-900/30",
  },
  risk_assessment: {
    name: "Risk Assessment Agent",
    icon: AlertTriangle,
    color: "text-red-600",
    bg: "bg-red-100 dark:bg-red-900/30",
  },
  timeline: {
    name: "Timeline Agent",
    icon: Clock,
    color: "text-purple-600",
    bg: "bg-purple-100 dark:bg-purple-900/30",
  },
};

function AgentCard({ finding }: { finding: AgentFinding }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const config = AGENT_CONFIG[finding.agent] || {
    name: finding.agent,
    icon: Brain,
    color: "text-neutral-600",
    bg: "bg-neutral-100 dark:bg-neutral-900/30",
  };

  const confidenceColor =
    finding.confidence >= 0.8
      ? "text-green-600"
      : finding.confidence >= 0.6
      ? "text-yellow-600"
      : "text-red-600";

  const statusIcon =
    finding.status === "completed" ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : finding.status === "failed" ? (
      <XCircle className="h-4 w-4 text-red-600" />
    ) : (
      <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
    );

  return (
    <Card className="overflow-hidden">
      <button
        className="w-full text-left"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className={cn("p-2 rounded-lg", config.bg, config.color)}>
              <config.icon className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-neutral-900 dark:text-white">
                    {config.name}
                  </h3>
                  {statusIcon}
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn("text-sm font-medium", confidenceColor)}>
                    {Math.round(finding.confidence * 100)}%
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-neutral-400" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-neutral-400" />
                  )}
                </div>
              </div>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1 line-clamp-2">
                {finding.summary}
              </p>
              {finding.reasoning_steps !== undefined && (
                <div className="flex items-center gap-4 mt-2 text-xs text-neutral-500">
                  <span className="flex items-center gap-1">
                    <Brain className="h-3 w-3" />
                    {finding.reasoning_steps} reasoning steps
                  </span>
                  {finding.duration_ms !== undefined && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {(finding.duration_ms / 1000).toFixed(1)}s
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </button>

      {isExpanded && (
        <div className="border-t border-neutral-200 dark:border-neutral-800">
          {/* Key Findings */}
          {finding.key_findings && finding.key_findings.length > 0 && (
            <div className="p-4 border-b border-neutral-200 dark:border-neutral-800">
              <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2 flex items-center gap-1">
                <FileText className="h-3 w-3" />
                Key Findings
              </h4>
              <ul className="space-y-1">
                {finding.key_findings.map((item, i) => (
                  <li
                    key={i}
                    className="text-sm text-neutral-600 dark:text-neutral-400 flex items-start gap-2"
                  >
                    <span className="text-blue-500 mt-1">•</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Evidence */}
          {finding.evidence && finding.evidence.length > 0 && (
            <div className="p-4">
              <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Evidence
              </h4>
              <div className="flex flex-wrap gap-2">
                {finding.evidence.map((item, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export function AgentFindingsPanel({ findings, className }: AgentFindingsPanelProps) {
  const agentNames = Object.keys(findings);

  if (agentNames.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <Brain className="h-12 w-12 mx-auto text-neutral-400 mb-4" />
          <p className="text-neutral-500">No agent findings yet</p>
          <p className="text-sm text-neutral-400 mt-1">
            Run an investigation to see agent results
          </p>
        </CardContent>
      </Card>
    );
  }

  // Calculate overall confidence
  const avgConfidence =
    agentNames.reduce((sum, name) => sum + findings[name].confidence, 0) / agentNames.length;

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
          Agent Findings
        </h2>
        <div className="flex items-center gap-2">
          <Badge
            variant={avgConfidence >= 0.8 ? "success" : avgConfidence >= 0.6 ? "warning" : "destructive"}
          >
            {Math.round(avgConfidence * 100)}% avg confidence
          </Badge>
          <Badge variant="secondary">
            {agentNames.length} agent{agentNames.length !== 1 ? "s" : ""}
          </Badge>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {agentNames.map((name) => (
          <AgentCard key={name} finding={findings[name]} />
        ))}
      </div>
    </div>
  );
}
