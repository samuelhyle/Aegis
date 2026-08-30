"use client";

import { cn } from "@/lib/utils";
import { getStateColor, getStateLabel, getRiskColor, getRiskLabel } from "@/lib/utils";

interface StateBadgeProps {
  state: string;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

export function StateBadge({ state, size = "md", showLabel = true, className }: StateBadgeProps) {
  const colorClass = getStateColor(state);
  const label = getStateLabel(state);
  const initial = label.charAt(0);

  const sizes = {
    sm: "w-6 h-6 text-xs",
    md: "w-8 h-8 text-sm",
    lg: "w-10 h-10 text-base",
  };

  return (
    <div className={cn("inline-flex items-center gap-1.5", className)}>
      <div
        className={cn(
          "inline-flex items-center justify-center rounded-full font-semibold text-white",
          colorClass,
          sizes[size]
        )}
        aria-label={label}
      >
        {initial}
      </div>
      {showLabel && <span className="font-medium text-neutral-700 dark:text-neutral-300">{label}</span>}
    </div>
  );
}

interface RiskBadgeProps {
  level: string;
  showLabel?: boolean;
  className?: string;
}

export function RiskBadge({ level, showLabel = true, className }: RiskBadgeProps) {
  const colorClass = getRiskColor(level);
  const label = getRiskLabel(level);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        colorClass,
        className
      )}
    >
      {showLabel && label}
    </span>
  );
}

interface ConfidenceBadgeProps {
  confidence: number;
  className?: string;
}

export function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  const percentage = Math.round(confidence * 100);
  const colorClass = confidence >= 0.8 ? "bg-green-100 text-green-800" : confidence >= 0.6 ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800";

  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium", colorClass, className)}>
      {percentage}% confidence
    </span>
  );
}