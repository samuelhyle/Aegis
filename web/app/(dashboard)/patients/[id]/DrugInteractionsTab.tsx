"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ScrollArea } from "@/components/ui/ScrollArea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { cn, getRiskLabel } from "@/lib/utils";
import { AlertTriangle, Pill, Shield, ChevronDown, ChevronUp } from "lucide-react";
import type { DrugInteraction } from "@/types";
import { useState } from "react";

interface DrugInteractionsTabProps {
  interactions: any;
}

export function DrugInteractionsTab({ interactions }: DrugInteractionsTabProps) {
  const interactionList = interactions?.interactions || [];
  const recommendations = interactions?.recommendations || [];
  const riskLevel = interactions?.risk_level || "low";
  const medicationCount = interactions?.medication_count || 0;

  if (interactionList.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Pill className="h-12 w-12 mx-auto text-neutral-300 dark:text-neutral-600" />
          <h3 className="mt-4 text-lg font-medium text-neutral-900 dark:text-white">No Drug Interactions Detected</h3>
          <p className="mt-2 text-neutral-500">No significant drug interactions found for this patient&apos;s current medications</p>
        </CardContent>
      </Card>
    );
  }

  const severeInteractions = interactionList.filter((i: DrugInteraction) => i.severity === "severe" || i.severity === "major");
  const moderateInteractions = interactionList.filter((i: DrugInteraction) => i.severity === "moderate");
  const minorInteractions = interactionList.filter((i: DrugInteraction) => i.severity === "minor");

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-4">
        <StatCard
          title="Total Medications"
          value={medicationCount}
          icon={Pill}
          color="text-blue-600 bg-blue-100"
        />
        <StatCard
          title="Total Interactions"
          value={interactionList.length}
          icon={AlertTriangle}
          color="text-orange-600 bg-orange-100"
        />
        <StatCard
          title="Severe/Major"
          value={severeInteractions.length}
          icon={AlertTriangle}
          color="text-red-600 bg-red-100"
        />
        <StatCard
          title="Risk Level"
          value={getRiskLabel(riskLevel)}
          icon={Shield}
          color={riskLevel === "high" || riskLevel === "very_high" || riskLevel === "critical" ? "text-red-600 bg-red-100" : "text-yellow-600 bg-yellow-100"}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Drug Interactions ({interactionList.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">All ({interactionList.length})</TabsTrigger>
              <TabsTrigger value="severe">Severe ({severeInteractions.length})</TabsTrigger>
              <TabsTrigger value="moderate">Moderate ({moderateInteractions.length})</TabsTrigger>
              <TabsTrigger value="minor">Minor ({minorInteractions.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-4">
              <InteractionList interactions={interactionList} />
            </TabsContent>
            <TabsContent value="severe" className="mt-4">
              <InteractionList interactions={severeInteractions} />
            </TabsContent>
            <TabsContent value="moderate" className="mt-4">
              <InteractionList interactions={moderateInteractions} />
            </TabsContent>
            <TabsContent value="minor" className="mt-4">
              <InteractionList interactions={minorInteractions} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {recommendations.map((rec: string, i: number) => (
                <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                  <Shield className="h-5 w-5 text-primary-600 shrink-0 mt-0.5" />
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">{rec}</p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color }: { title: string; value: number | string; icon: React.ComponentType<{ className?: string }>; color: string }) {
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

function InteractionList({ interactions }: { interactions: DrugInteraction[] }) {
  if (interactions.length === 0) {
    return (
      <div className="py-8 text-center text-neutral-500">
        No interactions in this category
      </div>
    );
  }

  return (
    <ScrollArea className="max-h-96">
      <div className="space-y-3">
        {interactions.map((interaction, i) => (
          <InteractionCard key={i} interaction={interaction} />
        ))}
      </div>
    </ScrollArea>
  );
}

function InteractionCard({ interaction }: { interaction: DrugInteraction }) {
  const [expanded, setExpanded] = useState(false);

  const severityColors: Record<string, string> = {
    severe: "bg-red-100 text-red-800 border-red-200",
    major: "bg-red-100 text-red-800 border-red-200",
    moderate: "bg-yellow-100 text-yellow-800 border-yellow-200",
    minor: "bg-green-100 text-green-800 border-green-200",
  };

  const severityIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    severe: AlertTriangle,
    major: AlertTriangle,
    moderate: AlertTriangle,
    minor: Shield,
  };

  const SeverityIcon = severityIcons[interaction.severity] || AlertTriangle;

  return (
    <Card className={cn("border-neutral-200 dark:border-neutral-800", severityColors[interaction.severity]?.replace("bg-", "border-"))}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h4 className="font-medium text-neutral-900 dark:text-white">
                {interaction.drug1} + {interaction.drug2}
              </h4>
              <Badge className={cn(severityColors[interaction.severity] || "bg-gray-100 text-gray-800")}>
                <SeverityIcon className="h-3 w-3 mr-1" />
                {interaction.severity}
              </Badge>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">{interaction.description}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setExpanded(!expanded)}
            className="h-8 w-8 shrink-0"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>

        {expanded && (
          <div className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-800 space-y-3">
            <div>
              <p className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">Management</p>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">{interaction.management}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
