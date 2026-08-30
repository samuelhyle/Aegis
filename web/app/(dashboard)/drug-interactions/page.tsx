"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useDrugInteractions } from "@/lib/hooks/useQueries";
import { AlertTriangle, Shield, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

export default function DrugInteractionsPage() {
  const [patientId, setPatientId] = useState("");
  const { data, isLoading } = useDrugInteractions(patientId);

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
      case "severe":
        return "destructive";
      case "moderate":
      case "medium":
        return "warning";
      case "low":
      case "mild":
        return "default";
      default:
        return "outline";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
      case "severe":
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
      case "moderate":
      case "medium":
        return <AlertCircle className="h-5 w-5 text-yellow-600" />;
      case "low":
      case "mild":
        return <Info className="h-5 w-5 text-blue-600" />;
      default:
        return <Info className="h-5 w-5 text-neutral-500" />;
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "high":
        return "text-red-600 bg-red-100 dark:bg-red-900/30";
      case "moderate":
        return "text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30";
      case "low":
        return "text-green-600 bg-green-100 dark:bg-green-900/30";
      default:
        return "text-neutral-600 bg-neutral-100 dark:bg-neutral-800";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Drug Interactions</h1>
          <p className="text-neutral-500 dark:text-neutral-400">Analyze medication interactions for patients</p>
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
            Enter a patient ID to view drug interactions
          </CardContent>
        </Card>
      ) : !data ? (
        <Card>
          <CardContent className="p-12 text-center text-neutral-500">
            No drug interaction data available for this patient
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Summary Stats */}
          <div className="grid gap-4 sm:grid-cols-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Medications</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-white">{data.medication_count}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                    <Shield className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Interactions Found</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-white">{data.interactions.length}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-orange-100 dark:bg-orange-900/30">
                    <AlertTriangle className="h-6 w-6 text-orange-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Risk Level</p>
                    <p className={cn("text-3xl font-bold capitalize", getRiskLevelColor(data.risk_level).split(" ")[0])}>
                      {data.risk_level}
                    </p>
                  </div>
                  <div className={cn("p-3 rounded-xl", getRiskLevelColor(data.risk_level))}>
                    <AlertCircle className="h-6 w-6" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Risk Score</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-white">{Math.round(data.risk_score * 100)}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Interactions List */}
          {data.interactions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Drug Interactions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.interactions.map((interaction, i) => (
                    <div key={i} className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-700">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          {getSeverityIcon(interaction.severity)}
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-neutral-900 dark:text-white">
                                {interaction.drug1}
                              </span>
                              <span className="text-neutral-400">+</span>
                              <span className="font-medium text-neutral-900 dark:text-white">
                                {interaction.drug2}
                              </span>
                            </div>
                            <Badge variant={getSeverityColor(interaction.severity)} className="mt-1">
                              {interaction.severity}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <p className="mt-3 text-sm text-neutral-600 dark:text-neutral-400">
                        {interaction.description}
                      </p>
                      {interaction.management && (
                        <div className="mt-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800">
                          <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Management:</p>
                          <p className="text-sm text-blue-700 dark:text-blue-300">{interaction.management}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recommendations */}
          {data.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {data.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                      <Shield className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
