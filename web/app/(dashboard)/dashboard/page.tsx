"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton, CardSkeleton } from "@/components/ui/Skeleton";
import { usePatients, useInvestigations, useSystemStats } from "@/lib/hooks/useQueries";
import { PatientCard } from "@/components/patient/PatientHeader";
import { ScrollArea } from "@/components/ui/ScrollArea";
import { cn } from "@/lib/utils";
import { Users, Activity, TrendingUp, AlertTriangle, Plus, Search, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";

export default function OverviewPage() {
  const router = useRouter();
  const { data: patientsData, isLoading: patientsLoading } = usePatients(10, 0);
  const { data: investigationsData, isLoading: investigationsLoading } = useInvestigations(undefined, undefined, 10, 0);
  const { data: statsData, isLoading: statsLoading, refetch: refetchStats } = useSystemStats();

  const highRiskAlerts = statsData?.high_risk_alerts ?? 0;

  const stats = [
    {
      label: "Total Patients",
      value: patientsData?.total || 0,
      icon: Users,
      color: "text-blue-600",
      bg: "bg-blue-100 dark:bg-blue-900/30",
    },
    {
      label: "Active Investigations",
      value: statsData?.active_investigations || 0,
      icon: Activity,
      color: "text-green-600",
      bg: "bg-green-100 dark:bg-green-900/30",
    },
    {
      label: "High Risk Alerts",
      value: statsData?.high_risk_alerts || 0,
      icon: AlertTriangle,
      color: "text-red-600",
      bg: "bg-red-100 dark:bg-red-900/30",
    },
    {
      label: "Pending Reviews",
      value: statsData?.pending_reviews || 0,
      icon: TrendingUp,
      color: "text-yellow-600",
      bg: "bg-yellow-100 dark:bg-yellow-900/30",
    },
  ];

  const recentInvestigations = investigationsData?.traces?.slice(0, 5) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Dashboard Overview</h1>
          <p className="text-neutral-500 dark:text-neutral-400">Real-time patient journey monitoring & clinical intelligence</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => refetchStats()}>
            <RefreshCw className={cn("h-4 w-4 mr-2", statsLoading && "animate-spin")} />
            Refresh
          </Button>
          <Button onClick={() => router.push("/patients")}>
            <Plus className="h-4 w-4 mr-2" />
            New Investigation
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))
        ) : (
          stats.map((stat) => (
            <Card key={stat.label} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">{stat.label}</p>
                    <p className="text-3xl font-bold text-neutral-900 dark:text-white">{stat.value}</p>
                  </div>
                  <div className={cn("p-3 rounded-xl", stat.bg, stat.color)}>
                    <stat.icon className="h-6 w-6" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-7">
        <Card className="lg:col-span-4">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Patients</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => router.push("/patients")}>
              <Search className="h-4 w-4 mr-1" />
              View All
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="max-h-96">
              {patientsLoading ? (
                <div className="p-4 space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full rounded-lg" />
                  ))}
                </div>
              ) : patientsData?.patients.length === 0 ? (
                <div className="p-8 text-center text-neutral-500">No patients found</div>
              ) : (
                <div className="divide-y divide-neutral-200 dark:divide-neutral-800">
                  {patientsData?.patients.map((patient) => (
                    <PatientCard key={patient.patient_id} patient={patient} />
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        <div className="space-y-4 lg:col-span-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>High Risk Alerts</CardTitle>
              {highRiskAlerts > 0 && (
                <Badge variant="destructive">{highRiskAlerts} Active</Badge>
              )}
            </CardHeader>
            <CardContent className="space-y-3">
              {statsLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full rounded-lg" />
                ))
              ) : highRiskAlerts > 0 ? (
                <p className="text-sm text-neutral-500 dark:text-neutral-400 text-center py-4">
                  {highRiskAlerts} patients require immediate attention
                </p>
              ) : (
                <div className="text-center py-4">
                  <p className="text-sm text-neutral-500 dark:text-neutral-400">No active high risk alerts</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Recent Investigations</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => router.push("/investigations")}>
                View All
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {investigationsLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full rounded-lg" />
                ))
              ) : recentInvestigations.length === 0 ? (
                <div className="p-4 text-center text-neutral-500">No recent investigations</div>
              ) : (
                recentInvestigations.map((inv) => (
                  <div
                    key={inv.trace_id}
                    className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 hover:bg-neutral-100 dark:hover:bg-neutral-800 cursor-pointer transition-colors"
                    onClick={() => router.push(`/investigations/${inv.trace_id}`)}
                  >
                    <p className="font-medium text-neutral-900 dark:text-white truncate">{inv.question}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-neutral-500">
                      <span>Patient {inv.patient_id.slice(0, 8)}</span>
                      <Badge variant={inv.reviewed ? "success" : inv.review_required ? "warning" : "default"}>
                        {inv.reviewed ? "completed" : inv.review_required ? "pending review" : "in_progress"}
                      </Badge>
                      {inv.confidence && (
                        <span className="text-green-600">{Math.round(inv.confidence * 100)}% confidence</span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" className="h-24 flex-col gap-2" onClick={() => router.push("/patients")}>
              <Users className="h-6 w-6" />
              <span>Browse Patients</span>
            </Button>
            <Button variant="outline" className="h-24 flex-col gap-2" onClick={() => router.push("/investigations")}>
              <Search className="h-6 w-6" />
              <span>New Investigation</span>
            </Button>
            <Button variant="outline" className="h-24 flex-col gap-2" onClick={() => router.push("/analytics/risk")}>
              <AlertTriangle className="h-6 w-6" />
              <span>Risk Analytics</span>
            </Button>
            <Button variant="outline" className="h-24 flex-col gap-2" onClick={() => router.push("/analytics/evaluation")}>
              <TrendingUp className="h-6 w-6" />
              <span>View Evaluations</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
