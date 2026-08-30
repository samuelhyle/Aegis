"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Select } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";
import type { Observation } from "@/types";
import { formatDate } from "@/lib/utils";

interface LabsChartProps {
  observations: Observation[];
}

export function LabsChart({ observations }: LabsChartProps) {
  const labTypes = [...new Set(observations.map((o) => o.DESCRIPTION))];
  const [selectedLab, setSelectedLab] = useState(labTypes[0] || "");

  const labData = observations
    .filter((o) => o.DESCRIPTION === selectedLab)
    .map((o) => ({
      date: formatDate(o.DATE),
      value: parseFloat(o.VALUE),
      unit: o.UNITS,
      timestamp: o.DATE,
    }))
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  const referenceRange = getReferenceRange(selectedLab);

  if (!selectedLab || labData.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-neutral-500">No lab data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Lab Trends</CardTitle>
          <Select
            value={selectedLab}
            onValueChange={setSelectedLab}
            options={labTypes.map((t) => ({ value: t, label: t }))}
            className="w-64"
          />
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={labData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#737373", fontSize: 12 }}
                  axisLine={{ stroke: "#e5e5e5" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#737373", fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                  domain={["auto", "auto"]}
                />
                {referenceRange && (
                  <ReferenceArea
                    y1={referenceRange.low}
                    y2={referenceRange.high}
                    fill="#22c55e"
                    fillOpacity={0.1}
                    stroke="#22c55e"
                    strokeOpacity={0.3}
                    strokeDasharray="5 5"
                  />
                )}
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e5e5e5",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                  labelFormatter={(value) => `Date: ${value}`}
                  formatter={(value: number, name: string) => [value, name]}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#3b82f6", strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: "#3b82f6" }}
                  name={`${selectedLab} (${labData[0]?.unit || ""})`}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex items-center gap-4 text-sm text-neutral-500">
            {referenceRange && (
              <>
                <span>Reference Range: {referenceRange.low} - {referenceRange.high} {labData[0]?.unit}</span>
                <Badge variant="outline" className="text-xs">Normal</Badge>
              </>
            )}
            <span>Data points: {labData.length}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Lab Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-200 dark:border-neutral-800">
                  <th className="px-4 py-2 text-left text-xs font-semibold text-neutral-500 uppercase">Test</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-neutral-500 uppercase">Value</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-neutral-500 uppercase">Unit</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-neutral-500 uppercase">Date</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-neutral-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                {observations
                  .sort((a, b) => new Date(b.DATE).getTime() - new Date(a.DATE).getTime())
                  .slice(0, 20)
                  .map((obs) => {
                    const ref = getReferenceRange(obs.DESCRIPTION);
                    const value = parseFloat(obs.VALUE);
                    let status: "normal" | "high" | "low" = "normal";
                    if (ref && value > ref.high) status = "high";
                    if (ref && value < ref.low) status = "low";

                    return (
                      <tr key={obs.Id} className="hover:bg-neutral-50 dark:hover:bg-neutral-900/50">
                        <td className="px-4 py-2 font-medium">{obs.DESCRIPTION}</td>
                        <td className="px-4 py-2 font-mono">{obs.VALUE}</td>
                        <td className="px-4 py-2">{obs.UNITS}</td>
                        <td className="px-4 py-2">{formatDate(obs.DATE)}</td>
                        <td className="px-4 py-2">
                          <Badge
                            variant={
                              status === "normal" ? "success" :
                              status === "high" ? "destructive" :
                              "warning"
                            }
                          >
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { useState } from "react";

function getReferenceRange(labName: string): { low: number; high: number } | null {
  const commonRanges: Record<string, { low: number; high: number }> = {
    "Glucose": { low: 70, high: 100 },
    "Hemoglobin A1c": { low: 4, high: 5.6 },
    "Creatinine": { low: 0.6, high: 1.3 },
    "BUN": { low: 7, high: 20 },
    "Potassium": { low: 3.5, high: 5.0 },
    "Sodium": { low: 135, high: 145 },
    "Chloride": { low: 98, high: 107 },
    "CO2": { low: 22, high: 29 },
    "Calcium": { low: 8.5, high: 10.2 },
    "Magnesium": { low: 1.7, high: 2.2 },
    "Phosphorus": { low: 2.5, high: 4.5 },
    "ALT": { low: 7, high: 56 },
    "AST": { low: 10, high: 40 },
    "ALP": { low: 44, high: 147 },
    "Bilirubin": { low: 0.1, high: 1.2 },
    "Albumin": { low: 3.5, high: 5.0 },
    "Total Protein": { low: 6.0, high: 8.3 },
    "WBC": { low: 4.5, high: 11.0 },
    "RBC": { low: 4.2, high: 5.9 },
    "Hemoglobin": { low: 12.0, high: 17.5 },
    "Hematocrit": { low: 36, high: 50 },
    "Platelets": { low: 150, high: 450 },
    "Troponin": { low: 0, high: 0.04 },
    "BNP": { low: 0, high: 100 },
    "LDL": { low: 0, high: 100 },
    "HDL": { low: 40, high: 100 },
    "Triglycerides": { low: 0, high: 150 },
    "Total Cholesterol": { low: 0, high: 200 },
  };

  return commonRanges[labName] || null;
}