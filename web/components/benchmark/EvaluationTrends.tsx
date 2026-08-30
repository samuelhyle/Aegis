"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { TrendingUp, TrendingDown, Minus, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

interface EvaluationTrendsProps {
  trends: {
    trend_direction?: "improving" | "declining" | "stable";
    average_improvement?: number;
    total_reports?: number;
    recent_scores?: Array<{
      date: string;
      score: number;
      agent?: string;
    }>;
    score_history?: Array<{
      timestamp: string;
      overall_score: number;
      accuracy: number;
      completeness: number;
      grounding: number;
    }>;
  };
  className?: string;
}

export function EvaluationTrends({ trends, className }: EvaluationTrendsProps) {
  const TrendIcon =
    trends.trend_direction === "improving"
      ? TrendingUp
      : trends.trend_direction === "declining"
      ? TrendingDown
      : Minus;

  const trendColor =
    trends.trend_direction === "improving"
      ? "text-green-600"
      : trends.trend_direction === "declining"
      ? "text-red-600"
      : "text-neutral-600";

  // Transform score history for chart
  const chartData = (trends.score_history || []).map((item) => ({
    date: new Date(item.timestamp).toLocaleDateString(),
    Overall: Math.round(item.overall_score * 100),
    Accuracy: Math.round(item.accuracy * 100),
    Completeness: Math.round(item.completeness * 100),
    Grounding: Math.round(item.grounding * 100),
  }));

  return (
    <div className={cn("space-y-6", className)}>
      {/* Trend Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendIcon className={cn("h-5 w-5", trendColor)} />
            Performance Trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-sm text-neutral-500">Direction</p>
              <div className="flex items-center justify-center gap-2">
                <TrendIcon className={cn("h-5 w-5", trendColor)} />
                <p className="text-lg font-medium capitalize">
                  {trends.trend_direction || "Unknown"}
                </p>
              </div>
            </div>
            <div className="text-center">
              <p className="text-sm text-neutral-500">Avg Improvement</p>
              <p className="text-lg font-medium">
                {trends.average_improvement !== undefined
                  ? `${trends.average_improvement >= 0 ? "+" : ""}${Math.round(
                      trends.average_improvement * 100
                    )}%`
                  : "N/A"}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-neutral-500">Total Reports</p>
              <p className="text-lg font-medium">{trends.total_reports || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Score History Chart */}
      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Score History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: number) => [`${value}%`]} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="Overall"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="Accuracy"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="Completeness"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="Grounding"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Recent Scores */}
      {trends.recent_scores && trends.recent_scores.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {trends.recent_scores.slice(0, 10).map((score, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full",
                        score.score >= 0.8
                          ? "bg-green-500"
                          : score.score >= 0.6
                          ? "bg-yellow-500"
                          : "bg-red-500"
                      )}
                    />
                    <div>
                      <p className="text-sm font-medium text-neutral-900 dark:text-white">
                        {score.agent || "Evaluation"}
                      </p>
                      <p className="text-xs text-neutral-500">
                        {new Date(score.date).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant={
                      score.score >= 0.8
                        ? "success"
                        : score.score >= 0.6
                        ? "warning"
                        : "destructive"
                    }
                  >
                    {Math.round(score.score * 100)}%
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Data */}
      {chartData.length === 0 && (!trends.recent_scores || trends.recent_scores.length === 0) && (
        <Card>
          <CardContent className="p-8 text-center">
            <Minus className="h-12 w-12 mx-auto text-neutral-400 mb-4" />
            <p className="text-neutral-500">No trend data available</p>
            <p className="text-sm text-neutral-400 mt-1">
              Run more evaluations to see performance trends
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
