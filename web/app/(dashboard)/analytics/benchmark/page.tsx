"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import {
  Loader2,
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import type { EvaluationTrendsResponse } from "@/types";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function BenchmarkPage() {
  const { data: benchmarkData, isLoading: benchmarkLoading } = useQuery({
    queryKey: ["evaluation", "benchmark"],
    queryFn: () => apiClient.getEvaluationHistory(undefined, 100),
  });

  const { data: trendsData, isLoading: trendsLoading } = useQuery({
    queryKey: ["evaluation", "trends"],
    queryFn: () => apiClient.getEvaluationTrends(),
  });

  const isLoading = benchmarkLoading || trendsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const reports = benchmarkData?.reports || [];
  const trends = trendsData as EvaluationTrendsResponse | undefined;

  // Calculate stats
  const totalCases = reports.length;
  const avgScore =
    reports.length > 0
      ? reports.reduce((sum: number, r: any) => sum + (r.overall_score || 0), 0) / reports.length
      : 0;
  const highScores = reports.filter((r: any) => r.overall_score >= 0.8).length;
  const lowScores = reports.filter((r: any) => r.overall_score < 0.6).length;

  // Group by category
  const categoryScores: Record<string, number[]> = {};
  reports.forEach((r: any) => {
    const cat = r.benchmark_name || "Unknown";
    if (!categoryScores[cat]) categoryScores[cat] = [];
    categoryScores[cat].push(r.overall_score || 0);
  });

  const categoryData = Object.entries(categoryScores).map(([name, scores]) => ({
    name: name.length > 20 ? name.slice(0, 20) + "..." : name,
    score: Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 100),
    count: scores.length,
  }));

  // Group by agent
  const agentScores: Record<string, number[]> = {};
  reports.forEach((r: any) => {
    const agent = r.agent_name || "Unknown";
    if (!agentScores[agent]) agentScores[agent] = [];
    agentScores[agent].push(r.overall_score || 0);
  });

  const agentData = Object.entries(agentScores).map(([name, scores]) => ({
    name,
    score: Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 100),
    count: scores.length,
  }));

  // Score distribution
  const scoreRanges = [
    { label: "Excellent (≥80%)", count: highScores, color: "#10b981" },
    { label: "Good (60-79%)", count: reports.filter((r: any) => r.overall_score >= 0.6 && r.overall_score < 0.8).length, color: "#3b82f6" },
    { label: "Fair (40-59%)", count: reports.filter((r: any) => r.overall_score >= 0.4 && r.overall_score < 0.6).length, color: "#f59e0b" },
    { label: "Poor (<40%)", count: lowScores, color: "#ef4444" },
  ].filter((d) => d.count > 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">
          Benchmark Dashboard
        </h1>
        <p className="text-neutral-500 dark:text-neutral-400">
          Performance evaluation metrics and trends
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                  Total Evaluations
                </p>
                <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                  {totalCases}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                <Target className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                  Average Score
                </p>
                <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                  {Math.round(avgScore * 100)}%
                </p>
              </div>
              <div className="p-3 rounded-xl bg-green-100 dark:bg-green-900/30">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                  High Scores (≥80%)
                </p>
                <p className="text-3xl font-bold text-green-600">{highScores}</p>
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
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                  Low Scores (&lt;60%)
                </p>
                <p className="text-3xl font-bold text-red-600">{lowScores}</p>
              </div>
              <div className="p-3 rounded-xl bg-red-100 dark:bg-red-900/30">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Performance by Category</CardTitle>
          </CardHeader>
          <CardContent>
            {categoryData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-neutral-500">
                No benchmark data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip
                    formatter={(value: number) => [`${value}%`, "Score"]}
                  />
                  <Bar dataKey="score" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                    {categoryData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Agent Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Performance by Agent</CardTitle>
          </CardHeader>
          <CardContent>
            {agentData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-neutral-500">
                No agent data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={agentData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip
                    formatter={(value: number) => [`${value}%`, "Score"]}
                  />
                  <Bar dataKey="score" fill="#10b981" radius={[4, 4, 0, 0]}>
                    {agentData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {scoreRanges.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-neutral-500">
                No distribution data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={scoreRanges}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name} (${(percent * 100).toFixed(0)}%)`
                    }
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {scoreRanges.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Recent Evaluations */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Evaluations</CardTitle>
          </CardHeader>
          <CardContent>
            {reports.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-neutral-500">
                No recent evaluations
              </div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {reports.slice(0, 10).map((report: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">
                        {report.benchmark_name || "Evaluation"}
                      </p>
                      <p className="text-xs text-neutral-500">
                        {report.agent_name || "Unknown agent"} •{" "}
                        {new Date(report.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge
                      variant={
                        (report.overall_score || 0) >= 0.8
                          ? "success"
                          : (report.overall_score || 0) >= 0.6
                          ? "warning"
                          : "destructive"
                      }
                    >
                      {Math.round((report.overall_score || 0) * 100)}%
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trends */}
      {trends?.trend_direction && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Performance Trends
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-neutral-500">Trend Direction</p>
                <p className="text-lg font-medium capitalize">
                  {trends!.trend_direction}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-neutral-500">Avg Improvement</p>
                <p className="text-lg font-medium">
                  {trends!.average_improvement
                    ? `${Math.round(trends!.average_improvement * 100)}%`
                    : "N/A"}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-neutral-500">Total Reports</p>
                <p className="text-lg font-medium">
                  {trends!.total_reports || reports.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
