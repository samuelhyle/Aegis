"use client";

import { TabsContent } from "@/components/ui/Tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ScrollArea } from "@/components/ui/ScrollArea";
import { Button } from "@/components/ui/Button";
import { formatDate } from "@/lib/utils";
import { StateBadge, RiskBadge } from "@/components/patient/Badges";
import { Download, Activity, Pill, TrendingUp, AlertTriangle } from "lucide-react";
import type { Condition, Medication, Observation, PatientJourney, RiskScore, ClinicalTrialMatch } from "@/types";
import { PatientTimeline } from "./PatientTimeline";
import { LabsChart } from "./LabsChart";
import { RiskDashboard } from "./RiskDashboard";
import { GraphRAGExplorer } from "./GraphRAGExplorer";
import { InvestigationsTab } from "./InvestigationsTab";
import { ClinicalTrialsTab } from "./ClinicalTrialsTab";
import { DrugInteractionsTab } from "./DrugInteractionsTab";

interface TabPanelsProps {
  patient: any;
  conditions: Condition[];
  medications: Medication[];
  observations: Observation[];
  journey: PatientJourney | null;
  riskAssessment: RiskScore[];
  drugInteractions: any;
  clinicalTrials: ClinicalTrialMatch[];
  timeline: any[];
  temporalAnalysis: any;
}

export function TabPanels(props: TabPanelsProps) {
  const {
    patient,
    conditions,
    medications,
    observations,
    journey,
    riskAssessment,
    drugInteractions,
    clinicalTrials,
    timeline,
    temporalAnalysis,
  } = props;

  return (
    <>
      <TabsContent value="overview">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Current Health State</CardTitle>
              </CardHeader>
              <CardContent>
                {journey ? (
                  <div className="flex items-center gap-4">
                    <StateBadge state={journey.current_state} size="lg" />
                    <div>
                      <p className="text-neutral-500 dark:text-neutral-400">Current state since</p>
                      <p className="font-medium">{formatDate(journey.current_state_since)}</p>
                    </div>
                    <div className="ml-auto">
                      {journey.upcoming_risks.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-neutral-900 dark:text-white">Top Upcoming Risk</p>
                          <RiskBadge level={journey.upcoming_risks[0].probability > 0.7 ? "high" : "moderate"} />
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="text-neutral-500">No journey data available</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Active Conditions</CardTitle>
                <Button variant="ghost" size="sm">View All</Button>
              </CardHeader>
              <CardContent>
                <ScrollArea className="max-h-64">
                  {conditions.length === 0 ? (
                    <p className="text-neutral-500 py-4">No active conditions</p>
                  ) : (
                    <div className="space-y-3">
                      {conditions.slice(0, 5).map((cond) => (
                        <div key={cond.Id} className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-neutral-900 dark:text-white truncate">{cond.DESCRIPTION}</p>
                            <p className="text-sm text-neutral-500 dark:text-neutral-400">
                              Onset: {formatDate(cond.START)} {cond.STOP ? `• Resolved: ${formatDate(cond.STOP)}` : "• Active"}
                            </p>
                          </div>
                          <Badge variant={cond.STOP ? "secondary" : "default"}>{cond.STOP ? "Resolved" : "Active"}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                      <Activity className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">Conditions</p>
                      <p className="font-bold text-neutral-900 dark:text-white">{conditions.length}</p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400">
                      <Pill className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">Medications</p>
                      <p className="font-bold text-neutral-900 dark:text-white">{medications.length}</p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400">
                      <TrendingUp className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">Lab Results</p>
                      <p className="font-bold text-neutral-900 dark:text-white">{observations.length}</p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400">
                      <AlertTriangle className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">Risk Alerts</p>
                      <p className="font-bold text-neutral-900 dark:text-white">{riskAssessment.filter(r => r.risk_level === "high" || r.risk_level === "very_high" || r.risk_level === "critical").length}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Upcoming Risks</CardTitle>
              </CardHeader>
              <CardContent>
                {journey?.upcoming_risks.length ? (
                  <div className="space-y-3">
                    {journey.upcoming_risks.slice(0, 3).map((risk, i) => (
                      <div key={i} className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-neutral-900 dark:text-white">{risk.condition}</p>
                          <RiskBadge level={risk.probability > 0.7 ? "high" : risk.probability > 0.4 ? "moderate" : "low"} />
                        </div>
                        <div className="mt-1 flex items-center justify-between text-sm text-neutral-500">
                          <span>Probability: {Math.round(risk.probability * 100)}%</span>
                          <span>Horizon: {risk.horizon_days} days</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-neutral-500">No upcoming risks identified</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </TabsContent>

      <TabsContent value="timeline">
        <PatientTimeline events={timeline} />
      </TabsContent>

      <TabsContent value="conditions">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">All Conditions ({conditions.length})</h2>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Condition</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Onset</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Resolved</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Code</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                    {conditions.map((cond) => (
                      <tr key={cond.Id} className="hover:bg-neutral-50 dark:hover:bg-neutral-900/50">
                        <td className="px-4 py-3 font-medium">{cond.DESCRIPTION}</td>
                        <td className="px-4 py-3">
                          <Badge variant={cond.STOP ? "secondary" : "default"}>{cond.STOP ? "Resolved" : "Active"}</Badge>
                        </td>
                        <td className="px-4 py-3">{formatDate(cond.START)}</td>
                        <td className="px-4 py-3">{cond.STOP ? formatDate(cond.STOP) : "—"}</td>
                        <td className="px-4 py-3 font-mono text-sm text-neutral-500">{cond.CODE}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="medications">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">All Medications ({medications.length})</h2>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Medication</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Reason</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Start</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Stop</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                    {medications.map((med) => (
                      <tr key={med.Id} className="hover:bg-neutral-50 dark:hover:bg-neutral-900/50">
                        <td className="px-4 py-3 font-medium">{med.DESCRIPTION}</td>
                        <td className="px-4 py-3 text-neutral-600 dark:text-neutral-400 max-w-xs truncate">{med.REASONDESCRIPTION || "—"}</td>
                        <td className="px-4 py-3">{formatDate(med.START)}</td>
                        <td className="px-4 py-3">{med.STOP ? formatDate(med.STOP) : "—"}</td>
                        <td className="px-4 py-3">
                          <Badge variant={med.STOP ? "secondary" : "success"}>{med.STOP ? "Discontinued" : "Active"}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="labs">
        <LabsChart observations={observations} />
      </TabsContent>

      <TabsContent value="risk">
        <RiskDashboard riskAssessment={riskAssessment} journey={journey} temporalAnalysis={temporalAnalysis} />
      </TabsContent>

      <TabsContent value="graph-rag">
        <GraphRAGExplorer patientId={patient.patient_id} />
      </TabsContent>

      <TabsContent value="investigations">
        <InvestigationsTab patientId={patient.patient_id} />
      </TabsContent>

      <TabsContent value="trials">
        <ClinicalTrialsTab trials={clinicalTrials} />
      </TabsContent>

      <TabsContent value="interactions">
        <DrugInteractionsTab interactions={drugInteractions} />
      </TabsContent>
    </>
  );
}