"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Activity, GitGraph, TrendingUp, FlaskConical, BarChart3, ArrowRight } from "lucide-react";
import Link from "next/link";

const analyticsPages = [
  {
    name: "Risk Dashboard",
    description: "Patient risk stratification and outcome prediction",
    href: "/analytics/risk",
    icon: Activity,
    color: "text-red-500",
    bgColor: "bg-red-100 dark:bg-red-900/30",
  },
  {
    name: "Temporal Analysis",
    description: "Patient journey timeline and progression analysis",
    href: "/analytics/temporal",
    icon: GitGraph,
    color: "text-blue-500",
    bgColor: "bg-blue-100 dark:bg-blue-900/30",
  },
  {
    name: "Graph RAG Explorer",
    description: "Knowledge graph exploration and semantic search",
    href: "/analytics/graph-rag",
    icon: FlaskConical,
    color: "text-purple-500",
    bgColor: "bg-purple-100 dark:bg-purple-900/30",
  },
  {
    name: "Evaluation Dashboard",
    description: "Agent performance metrics and evaluation history",
    href: "/analytics/evaluation",
    icon: BarChart3,
    color: "text-green-500",
    bgColor: "bg-green-100 dark:bg-green-900/30",
  },
  {
    name: "Benchmark Results",
    description: "Performance evaluation metrics and trends",
    href: "/analytics/benchmark",
    icon: TrendingUp,
    color: "text-amber-500",
    bgColor: "bg-amber-100 dark:bg-amber-900/30",
  },
];

export default function AnalyticsOverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">
          Analytics
        </h1>
        <p className="text-neutral-500 dark:text-neutral-400 mt-1">
          Explore patient data, agent performance, and clinical insights
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {analyticsPages.map((page) => (
          <Link
            key={page.href}
            href={page.href}
            className="group block"
          >
            <Card className="h-full transition-all hover:shadow-lg hover:border-primary-500 cursor:">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className={`p-3 rounded-xl ${page.bgColor}`}>
                    <page.icon className={`h-6 w-6 ${page.color}`} />
                  </div>
                  <ArrowRight className="h-4 w-4 text-neutral-400 transition-transform group-hover:translate-x-1" />
                </div>
                <CardTitle className="mt-4">{page.name}</CardTitle>
                <CardDescription className="mt-2">{page.description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>About AEGIS Analytics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-neutral-600 dark:text-neutral-400">
          <p>
            AEGIS provides multiple analytical views into patient records and agent performance:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li><strong>Risk Dashboard</strong> — Cardiovascular, diabetes, and readmission risk scores per patient</li>
            <li><strong>Temporal Analysis</strong> — Lab value trends, disease progression, anomaly detection</li>
            <li><strong>Graph RAG</strong> — Knowledge graph patterns, causal chains, communities</li>
            <li><strong>Evaluation</strong> — Per-agent accuracy, grounding, confidence calibration</li>
            <li><strong>Benchmark</strong> — Aggregate benchmark scores across runs</li>
          </ul>
          <p className="pt-2">
            All analytics are derived from synthetic Synthea patient data and AI-generated investigation traces.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}