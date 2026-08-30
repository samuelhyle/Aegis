"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ScrollArea } from "@/components/ui/ScrollArea";
import { cn } from "@/lib/utils";
import { FlaskConical, CheckCircle, XCircle, AlertCircle, ExternalLink, FileText } from "lucide-react";
import type { ClinicalTrialMatch } from "@/types";

interface ClinicalTrialsTabProps {
  trials: ClinicalTrialMatch[];
}

export function ClinicalTrialsTab({ trials }: ClinicalTrialsTabProps) {
  if (trials.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <FlaskConical className="h-12 w-12 mx-auto text-neutral-300 dark:text-neutral-600" />
          <h3 className="mt-4 text-lg font-medium text-neutral-900 dark:text-white">No Clinical Trial Matches</h3>
          <p className="mt-2 text-neutral-500">No matching clinical trials found for this patient</p>
        </CardContent>
      </Card>
    );
  }

  const eligibleTrials = trials.filter((t) => t.eligibility_status === "eligible" || t.eligibility_status === "potentially_eligible");
  const ineligibleTrials = trials.filter((t) => t.eligibility_status === "ineligible");

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard title="Total Matches" value={trials.length} icon={FlaskConical} color="text-blue-600 bg-blue-100" />
        <StatCard title="Eligible" value={eligibleTrials.length} icon={CheckCircle} color="text-green-600 bg-green-100" />
        <StatCard title="Ineligible" value={ineligibleTrials.length} icon={XCircle} color="text-red-600 bg-red-100" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Clinical Trial Matches</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="max-h-[600px]">
            <div className="space-y-4">
              {trials.map((trial) => (
                <TrialCard key={trial.trial_id} trial={trial} />
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color }: { title: string; value: number; icon: React.ComponentType<{ className?: string }>; color: string }) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-neutral-500">{title}</p>
            <p className="text-3xl font-bold text-neutral-900 dark:text-white">{value}</p>
          </div>
          <div className={cn("p-3 rounded-xl", color)}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TrialCard({ trial }: { trial: ClinicalTrialMatch }) {
  const statusColors: Record<string, string> = {
    eligible: "bg-green-100 text-green-800",
    potentially_eligible: "bg-yellow-100 text-yellow-800",
    ineligible: "bg-red-100 text-red-800",
    unknown: "bg-gray-100 text-gray-800",
  };

  const statusIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    eligible: CheckCircle,
    potentially_eligible: AlertCircle,
    ineligible: XCircle,
    unknown: AlertCircle,
  };

  const StatusIcon = statusIcons[trial.eligibility_status] || AlertCircle;

  return (
    <Card className="border-neutral-200 dark:border-neutral-800">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h4 className="font-medium text-neutral-900 dark:text-white truncate">{trial.title}</h4>
              <Badge className={cn(statusColors[trial.eligibility_status] || "bg-gray-100 text-gray-800")}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {trial.eligibility_status.replace("_", " ")}
              </Badge>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">{trial.condition}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-neutral-500">
              <span className="flex items-center gap-1">
                <FlaskConical className="h-3 w-3" />
                Phase {trial.phase}
              </span>
              <span>Confidence: {Math.round(trial.confidence * 100)}%</span>
              <span>Trial ID: {trial.trial_id}</span>
            </div>

            {trial.match_reasons.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">Match Reasons</p>
                <div className="flex flex-wrap gap-1">
                  {trial.match_reasons.slice(0, 3).map((reason, i) => (
                    <Badge key={i} variant="outline" className="text-xs">{reason}</Badge>
                  ))}
                </div>
              </div>
            )}

            {trial.exclusion_reasons.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">Exclusion Reasons</p>
                <div className="flex flex-wrap gap-1">
                  {trial.exclusion_reasons.slice(0, 3).map((reason, i) => (
                    <Badge key={i} variant="destructive" className="text-xs">{reason}</Badge>
                  ))}
                </div>
              </div>
            )}

            {trial.recommendations.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">Recommendations</p>
                <ul className="space-y-1 text-xs text-neutral-600 dark:text-neutral-400">
                  {trial.recommendations.slice(0, 2).map((rec, i) => (
                    <li key={i} className="flex items-start gap-1">
                      <span className="text-primary-600">→</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-1" />
              View Details
            </Button>
            <Button variant="ghost" size="sm">
              <FileText className="h-4 w-4 mr-1" />
              Export
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}