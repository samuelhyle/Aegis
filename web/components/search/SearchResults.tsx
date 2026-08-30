"use client";

import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import {
  FileText,
  Activity,
  Pill,
  Calendar,
  ExternalLink,
  Copy,
  Check,
} from "lucide-react";
import { useState } from "react";

interface SearchResult {
  id: string;
  patient_id: string;
  source_type: string;
  source_id: string;
  chunk_text: string;
  similarity: number;
  metadata?: Record<string, unknown>;
}

interface SearchResultsProps {
  results: SearchResult[];
  total: number;
  query: string;
  className?: string;
}

const SOURCE_TYPE_CONFIG: Record<
  string,
  { icon: any; color: string; bg: string; label: string }
> = {
  condition: {
    icon: Activity,
    color: "text-red-600",
    bg: "bg-red-100 dark:bg-red-900/30",
    label: "Condition",
  },
  medication: {
    icon: Pill,
    color: "text-green-600",
    bg: "bg-green-100 dark:bg-green-900/30",
    label: "Medication",
  },
  observation: {
    icon: FileText,
    color: "text-blue-600",
    bg: "bg-blue-100 dark:bg-blue-900/30",
    label: "Observation",
  },
  encounter: {
    icon: Calendar,
    color: "text-purple-600",
    bg: "bg-purple-100 dark:bg-purple-900/30",
    label: "Encounter",
  },
};

function ResultCard({ result }: { result: SearchResult }) {
  const [copied, setCopied] = useState(false);
  const config = SOURCE_TYPE_CONFIG[result.source_type] || {
    icon: FileText,
    color: "text-neutral-600",
    bg: "bg-neutral-100 dark:bg-neutral-900/30",
    label: result.source_type,
  };

  const Icon = config.icon;

  const similarityPercent = Math.round(result.similarity * 100);
  const similarityColor =
    similarityPercent >= 80
      ? "text-green-600"
      : similarityPercent >= 60
      ? "text-yellow-600"
      : "text-red-600";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.chunk_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="overflow-hidden hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={cn("p-2 rounded-lg shrink-0", config.bg, config.color)}>
            <Icon className="h-4 w-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={cn(config.color)}>
                  {config.label}
                </Badge>
                <span className="text-xs text-neutral-500">
                  Patient: {result.patient_id.slice(0, 12)}...
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className={cn("text-sm font-medium", similarityColor)}>
                  {similarityPercent}% match
                </span>
              </div>
            </div>

            <p className="text-sm text-neutral-700 dark:text-neutral-300 line-clamp-3">
              {result.chunk_text}
            </p>

            {result.metadata && Object.keys(result.metadata).length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {Object.entries(result.metadata).slice(0, 5).map(([key, value]) => (
                  <Badge key={key} variant="secondary" className="text-xs">
                    {key}: {String(value).slice(0, 30)}
                  </Badge>
                ))}
              </div>
            )}

            <div className="mt-3 flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={handleCopy}>
                {copied ? (
                  <Check className="h-3 w-3 mr-1" />
                ) : (
                  <Copy className="h-3 w-3 mr-1" />
                )}
                {copied ? "Copied" : "Copy"}
              </Button>
              <Button variant="ghost" size="sm">
                <ExternalLink className="h-3 w-3 mr-1" />
                View Source
              </Button>
            </div>
          </div>
        </div>

        {/* Similarity Bar */}
        <div className="mt-3">
          <div className="h-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                similarityPercent >= 80
                  ? "bg-green-500"
                  : similarityPercent >= 60
                  ? "bg-yellow-500"
                  : "bg-red-500"
              )}
              style={{ width: `${similarityPercent}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function SearchResults({
  results,
  total,
  query,
  className,
}: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <FileText className="h-12 w-12 mx-auto text-neutral-400 mb-4" />
          <p className="text-neutral-500">No results found</p>
          <p className="text-sm text-neutral-400 mt-1">
            Try a different query or adjust filters
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
          Search Results
        </h2>
        <div className="flex items-center gap-2 text-sm text-neutral-500">
          <span>{total} result{total !== 1 ? "s" : ""}</span>
          <span>for "{query}"</span>
        </div>
      </div>

      <div className="space-y-3">
        {results.map((result) => (
          <ResultCard key={result.id} result={result} />
        ))}
      </div>
    </div>
  );
}
