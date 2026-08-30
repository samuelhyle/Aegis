"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import {
  MessageSquare,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  ArrowRight,
} from "lucide-react";

interface DebateRound {
  round: number;
  agent_positions: Record<string, string>;
  agreements?: string[];
  disagreements?: string[];
}

interface DebateVisualizationProps {
  rounds: DebateRound[];
  consensus?: string;
  className?: string;
}

const AGENT_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  diagnostic: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-700 dark:text-blue-300",
    border: "border-blue-300 dark:border-blue-700",
  },
  treatment: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-700 dark:text-green-300",
    border: "border-green-300 dark:border-green-700",
  },
  risk_assessment: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-700 dark:text-red-300",
    border: "border-red-300 dark:border-red-700",
  },
  timeline: {
    bg: "bg-purple-100 dark:bg-purple-900/30",
    text: "text-purple-700 dark:text-purple-300",
    border: "border-purple-300 dark:border-purple-700",
  },
};

function RoundCard({ round }: { round: DebateRound }) {
  const [isExpanded, setIsExpanded] = useState(round.round === 1);
  const agents = Object.keys(round.agent_positions);

  return (
    <div className="relative">
      {/* Timeline connector */}
      {round.round > 1 && (
        <div className="absolute left-6 -top-4 w-0.5 h-4 bg-neutral-300 dark:bg-neutral-700" />
      )}

      <Card className="overflow-hidden">
        <button
          className="w-full text-left"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                    round.round === agents.length
                      ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                      : "bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300"
                  )}
                >
                  {round.round}
                </div>
                <div>
                  <h3 className="font-semibold text-neutral-900 dark:text-white">
                    Round {round.round}
                  </h3>
                  <p className="text-sm text-neutral-500">
                    {agents.length} agent{agents.length !== 1 ? "s" : ""} participating
                  </p>
                </div>
              </div>
              {isExpanded ? (
                <ChevronUp className="h-5 w-5 text-neutral-400" />
              ) : (
                <ChevronDown className="h-5 w-5 text-neutral-400" />
              )}
            </div>
          </CardContent>
        </button>

        {isExpanded && (
          <div className="border-t border-neutral-200 dark:border-neutral-800">
            {/* Agent Positions */}
            <div className="p-4 space-y-3">
              {agents.map((agent) => {
                const colors = AGENT_COLORS[agent] || {
                  bg: "bg-neutral-100 dark:bg-neutral-800",
                  text: "text-neutral-700 dark:text-neutral-300",
                  border: "border-neutral-300 dark:border-neutral-700",
                };
                return (
                  <div
                    key={agent}
                    className={cn(
                      "p-3 rounded-lg border",
                      colors.bg,
                      colors.border
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline" className={colors.text}>
                        {agent.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                      </Badge>
                    </div>
                    <p className={cn("text-sm", colors.text)}>
                      {round.agent_positions[agent]}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Agreements and Disagreements */}
            {(round.agreements?.length || 0) + (round.disagreements?.length || 0) > 0 && (
              <div className="px-4 pb-4 grid grid-cols-2 gap-4">
                {round.agreements && round.agreements.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-green-700 dark:text-green-300 mb-2 flex items-center gap-1">
                      <CheckCircle className="h-4 w-4" />
                      Agreements
                    </h4>
                    <ul className="space-y-1">
                      {round.agreements.map((item, i) => (
                        <li
                          key={i}
                          className="text-sm text-neutral-600 dark:text-neutral-400 flex items-start gap-2"
                        >
                          <span className="text-green-500 mt-1">✓</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {round.disagreements && round.disagreements.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-red-700 dark:text-red-300 mb-2 flex items-center gap-1">
                      <XCircle className="h-4 w-4" />
                      Disagreements
                    </h4>
                    <ul className="space-y-1">
                      {round.disagreements.map((item, i) => (
                        <li
                          key={i}
                          className="text-sm text-neutral-600 dark:text-neutral-400 flex items-start gap-2"
                        >
                          <span className="text-red-500 mt-1">✗</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

export function DebateVisualization({
  rounds,
  consensus,
  className,
}: DebateVisualizationProps) {
  if (rounds.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <MessageSquare className="h-12 w-12 mx-auto text-neutral-400 mb-4" />
          <p className="text-neutral-500">No debate rounds yet</p>
          <p className="text-sm text-neutral-400 mt-1">
            Enable multi-agent debate to see agent discussions
          </p>
        </CardContent>
      </Card>
    );
  }

  // Collect all agreements and disagreements across rounds
  const allAgreements = rounds.flatMap((r) => r.agreements || []);
  const allDisagreements = rounds.flatMap((r) => r.disagreements || []);

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Multi-Agent Debate
        </h2>
        <Badge variant="secondary">
          {rounds.length} round{rounds.length !== 1 ? "s" : ""}
        </Badge>
      </div>

      {/* Rounds */}
      <div className="space-y-4">
        {rounds.map((round) => (
          <RoundCard key={round.round} round={round} />
        ))}
      </div>

      {/* Consensus */}
      {consensus && (
        <Card className="border-2 border-green-200 dark:border-green-800">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-green-700 dark:text-green-300 mb-1">
                  Final Consensus
                </h3>
                <p className="text-sm text-neutral-700 dark:text-neutral-300">{consensus}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      {(allAgreements.length > 0 || allDisagreements.length > 0) && (
        <Card>
          <CardContent className="p-4">
            <h3 className="font-medium text-neutral-900 dark:text-white mb-3">
              Debate Summary
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {allAgreements.length > 0 && (
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {allAgreements.length}
                  </div>
                  <div className="text-sm text-neutral-500">Agreements</div>
                </div>
              )}
              {allDisagreements.length > 0 && (
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {allDisagreements.length}
                  </div>
                  <div className="text-sm text-neutral-500">Disagreements</div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
