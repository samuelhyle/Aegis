"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from "recharts";
import { Brain, TrendingUp, TrendingDown, Minus, RefreshCw } from "lucide-react";

const METRIC_LABELS: Record<string, string> = {
  accuracy: "Accuracy",
  completeness: "Completeness",
  grounding: "Grounding",
  relevance: "Relevance",
  confidence_calibration: "Calibration",
  reasoning_quality: "Reasoning",
  safety: "Safety",
  tool_efficiency: "Tool Efficiency",
  latency: "Latency",
};

export default function EvaluationDashboardPage() {
  const {
    data: historyData,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ["evaluation-history"],
    queryFn: () => apiClient.getEvaluationHistory(undefined, 50),
  });

  const { data: trendsData, isLoading: trendsLoading } = useQuery({
    queryKey: ["evaluation-trends"],
    queryFn: () => apiClient.getEvaluationTrends(),
  });

  const reports = historyData?.reports ?? [];
  const trends = trendsData && typeof trendsData === "object" && "reports" in trendsData ? trendsData as { reports: any[]; trend?: string; change?: number } : null;

  const latestReport = reports[0];

  const metricBarData = latestReport?.metric_scores
    ? Object.entries(JSON.parse(latestReport.metric_scores)).map(
        ([key, value]) => ({
          name: METRIC_LABELS[key] || key,
          score: Number(value),
        })
      )
    : [];

  const trendLineData = trends?.reports
    ? trends.reports.map((r: any, i: number) => ({
        run: i + 1,
        score: r.overall_score,
        date: new Date(r.generated_at).toLocaleDateString(),
      }))
    : [];

  const trendDirection = trends?.trend ?? "stable";
  const TrendIcon =
    trendDirection === "improving"
      ? TrendingUp
      : trendDirection === "declining"
        ? TrendingDown
        : Minus;

  if (historyLoading || trendsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Evaluation Dashboard</h1>
          <p className="text-muted-foreground">
            Agent performance metrics and evaluation history
          </p>
        </div>
        <Button variant="outline" onClick={() => refetchHistory()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Evaluations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{reports.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Latest Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {latestReport
                ? `${(latestReport.overall_score * 100).toFixed(1)}%`
                : "N/A"}
            </div>
            {latestReport && (
              <p className="text-xs text-muted-foreground mt-1">
                {latestReport.completed_cases}/{latestReport.total_cases} cases
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <TrendIcon
                className={`h-5 w-5 ${
                  trendDirection === "improving"
                    ? "text-green-500"
                    : trendDirection === "declining"
                      ? "text-red-500"
                      : "text-muted-foreground"
                }`}
              />
              <span className="text-2xl font-bold capitalize">
                {trendDirection}
              </span>
            </div>
            {trends && typeof trends.change === "number" && (
              <p className="text-xs text-muted-foreground mt-1">
                Change: {(trends.change * 100).toFixed(1)}%
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Mean Latency
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {latestReport?.latency_stats
                ? `${JSON.parse(latestReport.latency_stats).mean?.toFixed(0) ?? "N/A"}ms`
                : "N/A"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Metric Scores Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Latest Metric Scores
            </CardTitle>
          </CardHeader>
          <CardContent>
            {metricBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={metricBarData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
                  <Bar dataKey="score" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No evaluation data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Trend Line Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Performance Over Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            {trendLineData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendLineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="run" />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#6366f1"
                    strokeWidth={2}
                    name="Overall Score"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                Run at least 2 evaluations to see trends
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Reports Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Evaluations</CardTitle>
        </CardHeader>
        <CardContent>
          {reports.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Report ID</th>
                    <th className="text-left p-2">Agent</th>
                    <th className="text-left p-2">Score</th>
                    <th className="text-left p-2">Cases</th>
                    <th className="text-left p-2">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r: any) => (
                    <tr key={r.report_id} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-mono text-xs">{r.report_id}</td>
                      <td className="p-2">
                        <Badge variant="outline">{r.agent_name}</Badge>
                      </td>
                      <td className="p-2 font-bold">
                        {(r.overall_score * 100).toFixed(1)}%
                      </td>
                      <td className="p-2">
                        {r.completed_cases}/{r.total_cases}
                      </td>
                      <td className="p-2 text-muted-foreground">
                        {new Date(r.generated_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No evaluations yet. Run an evaluation to see results here.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
