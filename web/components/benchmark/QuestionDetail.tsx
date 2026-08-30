"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Brain,
  Target,
} from "lucide-react";

interface QuestionDetailProps {
  question: {
    case_id: string;
    patient_id: string;
    question: string;
    category: string;
    difficulty: string;
    expected_findings: string[];
    expected_confidence_range: [number, number];
  };
  result?: {
    actual_findings: string[];
    actual_confidence: number;
    score: number;
    missing: string[];
    extra: string[];
  };
  className?: string;
}

const DIFFICULTY_COLORS: Record<string, { bg: string; text: string }> = {
  easy: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-700 dark:text-green-300" },
  medium: { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-700 dark:text-yellow-300" },
  hard: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-700 dark:text-red-300" },
};

export function QuestionDetail({ question, result, className }: QuestionDetailProps) {
  const difficultyColors = DIFFICULTY_COLORS[question.difficulty] || DIFFICULTY_COLORS.medium;

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="bg-neutral-50 dark:bg-neutral-900">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className={cn(difficultyColors.bg, difficultyColors.text)}>
                {question.difficulty}
              </Badge>
              <Badge variant="secondary">{question.category}</Badge>
            </div>
            <CardTitle className="text-lg">{question.question}</CardTitle>
            <p className="text-sm text-neutral-500 mt-1">
              Patient: {question.patient_id.slice(0, 16)}...
            </p>
          </div>
          {result && (
            <div className="text-right">
              <div
                className={cn(
                  "text-3xl font-bold",
                  result.score >= 0.8
                    ? "text-green-600"
                    : result.score >= 0.6
                    ? "text-yellow-600"
                    : "text-red-600"
                )}
              >
                {Math.round(result.score * 100)}%
              </div>
              <p className="text-sm text-neutral-500">Match Score</p>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-6 space-y-4">
        {/* Expected Findings */}
        <div>
          <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2 flex items-center gap-1">
            <Target className="h-4 w-4" />
            Expected Findings
          </h4>
          <div className="space-y-1">
            {question.expected_findings.map((finding, i) => {
              const isFound = result?.actual_findings.some(
                (af) => af.toLowerCase().includes(finding.toLowerCase()) || finding.toLowerCase().includes(af.toLowerCase())
              );
              const isMissing = result?.missing.some(
                (m) => m.toLowerCase().includes(finding.toLowerCase()) || finding.toLowerCase().includes(m.toLowerCase())
              );

              return (
                <div
                  key={i}
                  className={cn(
                    "flex items-center gap-2 p-2 rounded text-sm",
                    isFound
                      ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300"
                      : isMissing
                      ? "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300"
                      : "bg-neutral-50 dark:bg-neutral-900"
                  )}
                >
                  {isFound ? (
                    <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
                  ) : isMissing ? (
                    <XCircle className="h-4 w-4 text-red-600 shrink-0" />
                  ) : (
                    <div className="h-4 w-4 rounded-full border-2 border-neutral-300 dark:border-neutral-600 shrink-0" />
                  )}
                  <span>{finding}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Actual Findings */}
        {result && (
          <div>
            <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2 flex items-center gap-1">
              <Brain className="h-4 w-4" />
              Actual Findings
            </h4>
            <div className="space-y-1">
              {result.actual_findings.map((finding, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 p-2 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-sm"
                >
                  <CheckCircle className="h-4 w-4 text-blue-600 shrink-0" />
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Missing Findings */}
        {result && result.missing.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-red-700 dark:text-red-300 mb-2 flex items-center gap-1">
              <AlertTriangle className="h-4 w-4" />
              Missing Findings ({result.missing.length})
            </h4>
            <div className="space-y-1">
              {result.missing.map((finding, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm"
                >
                  <XCircle className="h-4 w-4 text-red-600 shrink-0" />
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Extra Findings */}
        {result && result.extra.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-yellow-700 dark:text-yellow-300 mb-2 flex items-center gap-1">
              <FileText className="h-4 w-4" />
              Extra Findings ({result.extra.length})
            </h4>
            <div className="space-y-1">
              {result.extra.map((finding, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 p-2 rounded bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 text-sm"
                >
                  <span className="text-yellow-600">+</span>
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Confidence Range */}
        {result && (
          <div className="pt-4 border-t border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center justify-between text-sm">
              <span className="text-neutral-500">Expected Confidence Range</span>
              <span className="font-medium">
                {Math.round(question.expected_confidence_range[0] * 100)}% -{" "}
                {Math.round(question.expected_confidence_range[1] * 100)}%
              </span>
            </div>
            <div className="flex items-center justify-between text-sm mt-1">
              <span className="text-neutral-500">Actual Confidence</span>
              <span
                className={cn(
                  "font-medium",
                  result.actual_confidence >= question.expected_confidence_range[0] &&
                    result.actual_confidence <= question.expected_confidence_range[1]
                    ? "text-green-600"
                    : "text-yellow-600"
                )}
              >
                {Math.round(result.actual_confidence * 100)}%
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
