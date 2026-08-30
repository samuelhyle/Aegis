"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useClinicalTrials } from "@/lib/hooks/useQueries";
import { FlaskConical, CheckCircle, XCircle, Clock } from "lucide-react";

export default function ClinicalTrialsPage() {
  const [patientId, setPatientId] = useState("");
  const { data, isLoading } = useClinicalTrials(patientId);
  const trials = data?.matches || [];

  const getEligibilityColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "eligible":
        return "success";
      case "ineligible":
        return "destructive";
      case "pending":
        return "warning";
      default:
        return "default";
    }
  };

  const getEligibilityIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "eligible":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "ineligible":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Clinical Trials</h1>
          <p className="text-neutral-500 dark:text-neutral-400">Find matching clinical trials for patients</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Enter patient ID"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 animate-pulse bg-neutral-200 dark:bg-neutral-800 rounded-xl" />
          ))}
        </div>
      ) : !patientId ? (
        <Card>
          <CardContent className="p-12 text-center text-neutral-500">
            Enter a patient ID to view matching clinical trials
          </CardContent>
        </Card>
      ) : trials.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-neutral-500">
            No clinical trials found for this patient
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Summary */}
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Total Matches</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-white">{trials.length}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                    <FlaskConical className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Eligible</p>
                    <p className="text-3xl font-bold text-green-600">
                      {trials.filter((t) => t.eligibility_status.toLowerCase() === "eligible").length}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-green-100 dark:bg-green-900/30">
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Ineligible</p>
                    <p className="text-3xl font-bold text-red-600">
                      {trials.filter((t) => t.eligibility_status.toLowerCase() === "ineligible").length}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-red-100 dark:bg-red-900/30">
                    <XCircle className="h-6 w-6 text-red-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Trial Cards */}
          <div className="space-y-4">
            {trials.map((trial) => (
              <Card key={trial.trial_id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-neutral-900 dark:text-white">{trial.title}</h3>
                        <Badge variant="outline">{trial.phase}</Badge>
                      </div>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
                        Condition: {trial.condition}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        {getEligibilityIcon(trial.eligibility_status)}
                        <Badge variant={getEligibilityColor(trial.eligibility_status)}>
                          {trial.eligibility_status}
                        </Badge>
                        <span className="text-sm text-neutral-500">
                          Match: {Math.round(trial.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-neutral-400">ID: {trial.trial_id}</p>
                    </div>
                  </div>

                  {/* Match Reasons */}
                  {trial.match_reasons.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Match Reasons:</p>
                      <ul className="mt-1 space-y-1">
                        {trial.match_reasons.map((reason, i) => (
                          <li key={i} className="text-sm text-neutral-600 dark:text-neutral-400 flex items-start gap-2">
                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                            {reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Exclusion Reasons */}
                  {trial.exclusion_reasons.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Exclusion Criteria:</p>
                      <ul className="mt-1 space-y-1">
                        {trial.exclusion_reasons.map((reason, i) => (
                          <li key={i} className="text-sm text-neutral-600 dark:text-neutral-400 flex items-start gap-2">
                            <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                            {reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recommendations */}
                  {trial.recommendations.length > 0 && (
                    <div className="mt-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800">
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Recommendations:</p>
                      <ul className="mt-1 space-y-1">
                        {trial.recommendations.map((rec, i) => (
                          <li key={i} className="text-sm text-blue-700 dark:text-blue-300">
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
