"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useTemporalAnalysis } from "@/lib/hooks/useQueries";
import { Clock, Activity, AlertTriangle, CheckCircle } from "lucide-react";

export default function TemporalAnalyticsPage() {
  const [patientId, setPatientId] = useState("");
  const { data: temporalData, isLoading } = useTemporalAnalysis(patientId);

  const timeline = temporalData?.timeline || [];
  const anomalies = temporalData?.anomalies || [];
  const predictions = temporalData?.predictions ? Object.values(temporalData.predictions) : [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "resolved":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "active":
        return <Activity className="h-4 w-4 text-blue-600" />;
      case "critical":
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-neutral-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "resolved":
        return "success";
      case "active":
        return "info";
      case "critical":
        return "destructive";
      default:
        return "default";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Temporal Analytics</h1>
          <p className="text-neutral-500 dark:text-neutral-400">Patient journey timeline and progression analysis</p>
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
            <div key={i} className="h-24 animate-pulse bg-neutral-200 dark:bg-neutral-800 rounded-xl" />
          ))}
        </div>
      ) : !patientId ? (
        <Card>
          <CardContent className="p-12 text-center text-neutral-500">
            Enter a patient ID to view temporal analysis
          </CardContent>
        </Card>
      ) : timeline.length === 0 && anomalies.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-neutral-500">
            No temporal data for this patient
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Summary Stats */}
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Timeline Events</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-white">{timeline.length}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                    <Activity className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Anomalies Detected</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-white">{anomalies.length}</p>
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
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Predictions</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-white">{predictions.length}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-purple-100 dark:bg-purple-900/30">
                    <Clock className="h-6 w-6 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Journey Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Journey Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-neutral-200 dark:bg-neutral-700" />
                <div className="space-y-6">
                  {timeline.map((event, i) => (
                    <div key={i} className="relative flex items-start gap-4 pl-10">
                      <div className="absolute left-2 top-1 w-5 h-5 rounded-full bg-white dark:bg-neutral-900 border-2 border-neutral-300 dark:border-neutral-600 flex items-center justify-center">
                        {getStatusIcon(event.status)}
                      </div>
                      <div className="flex-1 p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
                        <div className="flex items-center justify-between">
                          <h3 className="font-medium text-neutral-900 dark:text-white">{event.type}</h3>
                          <Badge variant={getStatusColor(event.status)}>{event.status}</Badge>
                        </div>
                        <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
                          {event.description}
                        </p>
                        {event.value && (
                          <p className="text-sm text-neutral-600 dark:text-neutral-300 mt-1">
                            Value: {event.value} {event.unit}
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-2 text-xs text-neutral-400">
                          <Clock className="h-3 w-3" />
                          {event.date}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Anomalies */}
          {anomalies.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Detected Anomalies</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {anomalies.map((anomaly, i) => (
                    <div key={i} className="p-4 rounded-lg bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-800">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-orange-600" />
                        <span className="font-medium text-orange-900 dark:text-orange-100">{anomaly.type}</span>
                      </div>
                      <p className="text-sm text-orange-700 dark:text-orange-300 mt-1">{anomaly.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-orange-600 dark:text-orange-400">
                        <span>Severity: {anomaly.severity}</span>
                        <span>{anomaly.timestamp}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Predictions */}
          {predictions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Trajectory Predictions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {predictions.map((pred, i) => (
                    <div key={i} className="p-4 rounded-lg bg-purple-50 dark:bg-purple-900/10 border border-purple-200 dark:border-purple-800">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-purple-900 dark:text-purple-100">{pred.lab_name}</h3>
                        <Badge variant={pred.trend === "increasing" ? "destructive" : pred.trend === "decreasing" ? "success" : "default"}>
                          {pred.trend}
                        </Badge>
                      </div>
                      <p className="text-sm text-purple-700 dark:text-purple-300 mt-1">
                        Current: {pred.current_value} | Predicted: {pred.predicted_values.length > 0 ? `${pred.predicted_values[pred.predicted_values.length - 1].value}` : "N/A"}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}