"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { cn, formatPercentage, getRiskLabel } from "@/lib/utils";
import { AlertTriangle, TrendingUp, Target, Shield, Brain, HeartPulse, Activity } from "lucide-react";
import type { RiskScore } from "@/types";

interface RiskDashboardProps {
  riskAssessment: RiskScore[];
  journey: any;
  temporalAnalysis: any;
}

const riskIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  cardiovascular: HeartPulse,
  renal: Activity,
  metabolic: Brain,
  infection: AlertTriangle,
  bleeding: Activity,
  fall: Target,
  readmission: TrendingUp,
  mortality: Shield,
};

export function RiskDashboard({ riskAssessment, journey, temporalAnalysis }: RiskDashboardProps) {
  const moderateRisks = riskAssessment.filter((r) => r.risk_level === "moderate");
  const lowRisks = riskAssessment.filter((r) => r.risk_level === "low");

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Critical Risks"
          value={riskAssessment.filter((r) => r.risk_level === "critical").length}
          icon={AlertTriangle}
          color="text-red-600 bg-red-100"
        />
        <StatCard
          title="High Risks"
          value={riskAssessment.filter((r) => r.risk_level === "high").length}
          icon={AlertTriangle}
          color="text-orange-600 bg-orange-100"
        />
        <StatCard
          title="Moderate Risks"
          value={moderateRisks.length}
          icon={TrendingUp}
          color="text-yellow-600 bg-yellow-100"
        />
        <StatCard
          title="Low Risks"
          value={lowRisks.length}
          icon={Shield}
          color="text-green-600 bg-green-100"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Risk Assessment Details</CardTitle>
        </CardHeader>
        <CardContent>
          {riskAssessment.length === 0 ? (
            <p className="text-neutral-500 py-4">No risk assessment data available</p>
          ) : (
            <div className="space-y-4">
              {riskAssessment.map((risk) => (
                <RiskCard key={risk.risk_type} risk={risk} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {journey?.upcoming_risks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Risk Milestones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {journey.upcoming_risks.map((risk: any, i: number) => (
                <div key={i} className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-neutral-900 dark:text-white">{risk.condition}</p>
                      <p className="text-sm text-neutral-500">
                        Probability: {Math.round(risk.probability * 100)}% • Horizon: {risk.horizon_days} days
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant={risk.probability > 0.7 ? "destructive" : risk.probability > 0.4 ? "warning" : "success"}>
                        {Math.round(risk.probability * 100)}%
                      </Badge>
                    </div>
                  </div>
                  <Progress value={risk.probability * 100} className="mt-2 h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {journey?.state_projections.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>State Transition Projections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {journey.state_projections.map((proj: any, i: number) => (
                <div key={i} className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-neutral-900 dark:text-white">
                        {proj.from_state} → {proj.to_state}
                      </p>
                      <p className="text-sm text-neutral-500">
                        Horizon: {proj.horizon_days} days • Confidence: {proj.confidence}
                      </p>
                    </div>
                    <Badge variant={proj.probability > 0.7 ? "success" : proj.probability > 0.4 ? "warning" : "destructive"}>
                      {Math.round(proj.probability * 100)}%
                    </Badge>
                  </div>
                  <Progress value={proj.probability * 100} className="mt-2 h-2" />
                  <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">{proj.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {temporalAnalysis?.predictions && Object.keys(temporalAnalysis.predictions).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Lab Trajectory Predictions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(temporalAnalysis.predictions).map(([labName, pred]: [string, any]) => (
                <div key={labName} className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-800">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{labName}</h4>
                    <Badge variant={pred.trend === "increasing" ? "destructive" : pred.trend === "decreasing" ? "success" : "secondary"}>
                      {pred.trend}
                    </Badge>
                  </div>
                  <p className="text-sm text-neutral-500">
                    Current: {pred.current_value} → Predicted: {pred.predicted_values[pred.predicted_values.length - 1]?.value?.toFixed(1)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
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

function RiskCard({ risk }: { risk: RiskScore }) {
  const Icon = riskIcons[risk.risk_type] || AlertTriangle;
  const riskColors: Record<string, string> = {
    low: "bg-green-100 text-green-800 border-green-200",
    moderate: "bg-yellow-100 text-yellow-800 border-yellow-200",
    high: "bg-orange-100 text-orange-800 border-orange-200",
    very_high: "bg-red-100 text-red-800 border-red-200",
    critical: "bg-red-100 text-red-800 border-red-200",
  };

  return (
    <div className={cn("p-4 rounded-lg border", riskColors[risk.risk_level] || "border-neutral-200")}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-lg", riskColors[risk.risk_level]?.replace("bg-", "bg-").replace("text-", "bg-").replace("border-", "bg-") + "/20")}>
            <Icon className={cn("h-5 w-5", riskColors[risk.risk_level]?.replace("bg-", "text-"))} />
          </div>
          <div>
            <p className="font-medium text-neutral-900 dark:text-white capitalize">{risk.risk_type.replace("_", " ")}</p>
            <p className="text-sm text-neutral-500">Score: {risk.score.toFixed(2)} • Confidence: {formatPercentage(risk.confidence)}</p>
          </div>
        </div>
        <Badge variant={risk.risk_level === "critical" || risk.risk_level === "very_high" ? "destructive" : risk.risk_level === "high" ? "warning" : risk.risk_level === "moderate" ? "warning" : "success"}>
          {getRiskLabel(risk.risk_level)}
        </Badge>
      </div>

      {risk.factors.length > 0 && (
        <div className="mt-3 pt-3 border-t border-current/20">
          <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Risk Factors</p>
          <div className="flex flex-wrap gap-2">
            {risk.factors.map((factor, i) => (
              <Badge key={i} variant="outline" className="text-xs">{factor}</Badge>
            ))}
          </div>
        </div>
      )}

      {risk.recommendations.length > 0 && (
        <div className="mt-3 pt-3 border-t border-current/20">
          <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Recommendations</p>
          <ul className="space-y-1 text-sm text-neutral-600 dark:text-neutral-400">
            {risk.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-primary-600">→</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}