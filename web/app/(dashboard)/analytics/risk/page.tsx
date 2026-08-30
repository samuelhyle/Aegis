"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useRiskAssessment } from "@/lib/hooks/useQueries";
import { cn } from "@/lib/utils";
import { AlertTriangle } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { RiskScore } from "@/types";

const RISK_COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  moderate: "#eab308",
  low: "#22c55e",
};

export default function RiskAnalyticsPage() {
  const [patientId, setPatientId] = useState("");
  const { data, isLoading } = useRiskAssessment(patientId);
  const riskAssessment = data?.risks || [];

  const chartData = riskAssessment.map((risk: RiskScore) => ({
    name: risk.risk_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    score: Math.round(risk.score * 100),
    level: risk.risk_level,
    fill: RISK_COLORS[risk.risk_level] || "#6b7280",
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Risk Analytics</h1>
          <p className="text-neutral-500 dark:text-neutral-400">Patient risk assessment and analysis</p>
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
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-40 animate-pulse bg-neutral-200 dark:bg-neutral-800 rounded-xl" />
          ))}
        </div>
      ) : riskAssessment.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-neutral-500">
            {patientId ? "No risk data for this patient" : "Enter a patient ID to view risk assessment"}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {riskAssessment.map((risk: RiskScore) => (
            <Card key={risk.risk_type}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">{risk.risk_type}</p>
                    <p className={cn(
                      "text-3xl font-bold",
                      risk.risk_level === "critical" ? "text-red-600" :
                      risk.risk_level === "high" ? "text-orange-600" :
                      risk.risk_level === "moderate" ? "text-yellow-600" : "text-green-600"
                    )}>
                      {Math.round(risk.score * 100)}%
                    </p>
                  </div>
                  <div className={cn(
                    "p-3 rounded-xl",
                    risk.risk_level === "critical" ? "bg-red-100" :
                    risk.risk_level === "high" ? "bg-orange-100" :
                    risk.risk_level === "moderate" ? "bg-yellow-100" : "bg-green-100"
                  )}>
                    <AlertTriangle className={cn(
                      "h-6 w-6",
                      risk.risk_level === "critical" ? "text-red-600" :
                      risk.risk_level === "high" ? "text-orange-600" :
                      risk.risk_level === "moderate" ? "text-yellow-600" : "text-green-600"
                    )} />
                  </div>
                </div>
                <div className="mt-4">
                  <Badge variant={
                    risk.risk_level === "critical" ? "destructive" :
                    risk.risk_level === "high" ? "warning" : "default"
                  }>
                    {risk.risk_level}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {riskAssessment.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                  <Tooltip formatter={(value: number) => [`${value}%`, "Risk Score"]} />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry: { fill: string }, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-4">
              {Object.entries(RISK_COLORS).map(([level, color]) => (
                <div key={level} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                  <span className="text-xs text-neutral-500 capitalize">{level}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}