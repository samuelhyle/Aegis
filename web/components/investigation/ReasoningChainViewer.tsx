"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import {
  Brain,
  Wrench,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Clock,
  ArrowRight,
} from "lucide-react";

interface ReasoningStep {
  step: number;
  thought: string;
  action?: {
    tool: string;
    input: Record<string, unknown>;
    output: Record<string, unknown>;
  };
  observation?: string;
}

interface ReasoningChainViewerProps {
  steps: ReasoningStep[];
  agent?: string;
  className?: string;
}

const STEP_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  thought: {
    bg: "bg-blue-50 dark:bg-blue-900/20",
    border: "border-blue-200 dark:border-blue-800",
    text: "text-blue-700 dark:text-blue-300",
  },
  action: {
    bg: "bg-green-50 dark:bg-green-900/20",
    border: "border-green-200 dark:border-green-800",
    text: "text-green-700 dark:text-green-300",
  },
  observation: {
    bg: "bg-purple-50 dark:bg-purple-900/20",
    border: "border-purple-200 dark:border-purple-800",
    text: "text-purple-700 dark:text-purple-300",
  },
};

function StepCard({ step }: { step: ReasoningStep }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasAction = !!step.action;

  const colors = hasAction ? STEP_COLORS.action : STEP_COLORS.thought;

  return (
    <div className="relative pl-8">
      {/* Timeline connector */}
      <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-neutral-200 dark:bg-neutral-800" />

      {/* Timeline dot */}
      <div
        className={cn(
          "absolute left-0 top-2 w-6 h-6 rounded-full flex items-center justify-center",
          hasAction
            ? "bg-green-100 dark:bg-green-900/30"
            : "bg-blue-100 dark:bg-blue-900/30"
        )}
      >
        {hasAction ? (
          <Wrench className="h-3 w-3 text-green-600 dark:text-green-400" />
        ) : (
          <Brain className="h-3 w-3 text-blue-600 dark:text-blue-400" />
        )}
      </div>

      <Card className={cn("overflow-hidden", colors.border)}>
        <button
          className="w-full text-left"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className={cn("text-xs", colors.text)}>
                    Step {step.step}
                  </Badge>
                  {hasAction && (
                    <Badge variant="secondary" className="text-xs">
                      {step.action!.tool}
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-neutral-700 dark:text-neutral-300 line-clamp-2">
                  {step.thought}
                </p>
              </div>
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-neutral-400 shrink-0" />
              ) : (
                <ChevronDown className="h-4 w-4 text-neutral-400 shrink-0" />
              )}
            </div>
          </CardContent>
        </button>

        {isExpanded && (
          <div className="border-t border-neutral-200 dark:border-neutral-800">
            {/* Thought */}
            <div className={cn("p-4", STEP_COLORS.thought.bg)}>
              <h4 className="text-xs font-medium text-neutral-500 mb-2 flex items-center gap-1">
                <Brain className="h-3 w-3" />
                Thought
              </h4>
              <p className="text-sm text-neutral-700 dark:text-neutral-300 whitespace-pre-wrap">
                {step.thought}
              </p>
            </div>

            {/* Action */}
            {step.action && (
              <div className={cn("p-4", STEP_COLORS.action.bg)}>
                <h4 className="text-xs font-medium text-neutral-500 mb-2 flex items-center gap-1">
                  <Wrench className="h-3 w-3" />
                  Action: {step.action.tool}
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs font-medium text-neutral-500 mb-1">Input</div>
                    <pre className="text-xs bg-white dark:bg-neutral-900 p-2 rounded overflow-x-auto">
                      {JSON.stringify(step.action.input, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-neutral-500 mb-1">Output</div>
                    <pre className="text-xs bg-white dark:bg-neutral-900 p-2 rounded overflow-x-auto">
                      {JSON.stringify(step.action.output, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            {/* Observation */}
            {step.observation && (
              <div className={cn("p-4", STEP_COLORS.observation.bg)}>
                <h4 className="text-xs font-medium text-neutral-500 mb-2 flex items-center gap-1">
                  <MessageSquare className="h-3 w-3" />
                  Observation
                </h4>
                <p className="text-sm text-neutral-700 dark:text-neutral-300 whitespace-pre-wrap">
                  {step.observation}
                </p>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

export function ReasoningChainViewer({
  steps,
  agent,
  className,
}: ReasoningChainViewerProps) {
  if (steps.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <Brain className="h-12 w-12 mx-auto text-neutral-400 mb-4" />
          <p className="text-neutral-500">No reasoning steps yet</p>
          <p className="text-sm text-neutral-400 mt-1">
            The reasoning chain will appear here as agents process
          </p>
        </CardContent>
      </Card>
    );
  }

  // Count action vs thought steps
  const thoughtSteps = steps.filter((s) => !s.action).length;
  const actionSteps = steps.filter((s) => !!s.action).length;

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Reasoning Chain
          {agent && (
            <Badge variant="secondary" className="ml-2">
              {agent}
            </Badge>
          )}
        </h2>
        <div className="flex items-center gap-2 text-sm text-neutral-500">
          <span className="flex items-center gap-1">
            <Brain className="h-3 w-3" />
            {thoughtSteps} thoughts
          </span>
          <span className="flex items-center gap-1">
            <Wrench className="h-3 w-3" />
            {actionSteps} actions
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {steps.map((step) => (
          <StepCard key={step.step} step={step} />
        ))}
      </div>
    </div>
  );
}
