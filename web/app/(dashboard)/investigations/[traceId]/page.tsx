"use client";

import { use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Input";
import { AgentFindingsPanel } from "@/components/investigation/AgentFindingsPanel";
import { DebateVisualization } from "@/components/investigation/DebateVisualization";
import { ReasoningChainViewer } from "@/components/investigation/ReasoningChainViewer";
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  FileText,
  Shield,
  Brain,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const statusConfig: Record<
  string,
  { icon: any; color: string; label: string }
> = {
  approved: { icon: CheckCircle, color: "text-green-500", label: "Approved" },
  rejected: { icon: XCircle, color: "text-red-500", label: "Rejected" },
  needs_modification: {
    icon: AlertTriangle,
    color: "text-yellow-500",
    label: "Needs Modification",
  },
  pending: { icon: Clock, color: "text-muted-foreground", label: "Pending" },
};

export default function InvestigationReportPage({
  params,
}: {
  params: Promise<{ traceId: string }>;
}) {
  const { traceId } = use(params);
  const queryClient = useQueryClient();
  const [reviewNotes, setReviewNotes] = useState("");
  const [activeTab, setActiveTab] = useState<"v1" | "v2">("v1");

  const { data: report, isLoading } = useQuery({
    queryKey: ["trace", traceId],
    queryFn: () => apiClient.getTrace(traceId),
  });

  const reviewMutation = useMutation({
    mutationFn: ({
      decision,
      notes,
    }: {
      decision: "approved" | "rejected" | "needs_modification";
      notes: string;
    }) => apiClient.reviewTrace(traceId, decision, "current-user", notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trace", traceId] });
      setReviewNotes("");
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Clock className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Investigation not found</p>
        <Link href="/investigations">
          <Button variant="outline" className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Investigations
          </Button>
        </Link>
      </div>
    );
  }

  const confidence = report.confidence ?? 0;
  const confidenceColor =
    confidence >= 0.8
      ? "text-green-500"
      : confidence >= 0.6
        ? "text-yellow-500"
        : "text-red-500";

  const reviewStatus =
    report.reviewed
      ? "approved"
      : report.review_required
        ? "pending"
        : "approved";
  const ReviewIcon = statusConfig[reviewStatus]?.icon ?? Clock;

  // Extract V2 data from report
  const agentResults = report.agent_results || [];
  const debateRounds = (report as any).debate_rounds || [];
  const consensus = (report as any).consensus || null;
  const reasoningChains = (report as any).reasoning_chains || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            href="/investigations"
            className="text-sm text-muted-foreground hover:text-foreground mb-2 inline-flex items-center gap-1"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Investigations
          </Link>
          <h1 className="text-2xl font-bold mt-2">Investigation Report</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Trace ID: <code className="font-mono">{traceId}</code>
          </p>
        </div>
        <Badge
          variant={
            reviewStatus === "approved"
              ? "success"
              : reviewStatus === "pending"
                ? "warning"
                : "secondary"
          }
        >
          <ReviewIcon className="h-3 w-3 mr-1" />
          {statusConfig[reviewStatus]?.label ?? reviewStatus}
        </Badge>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-4 border-b border-neutral-200 dark:border-neutral-800 pb-4">
        <button
          onClick={() => setActiveTab("v1")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === "v1"
              ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
              : "text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          }`}
        >
          <Zap className="h-4 w-4" />
          V1 Deterministic
        </button>
        <button
          onClick={() => setActiveTab("v2")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === "v2"
              ? "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300"
              : "text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          }`}
        >
          <Brain className="h-4 w-4" />
          V2 LLM-Powered
          {agentResults.length > 0 && (
            <Badge variant="secondary" className="ml-1">
              {agentResults.length}
            </Badge>
          )}
        </button>
      </div>

      {/* Patient & Question */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Investigation Details
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-muted-foreground">Patient ID</span>
              <p className="font-mono text-sm">{report.patient_id}</p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Generated</span>
              <p className="text-sm">
                {new Date(report.generated_at).toLocaleString()}
              </p>
            </div>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Question</span>
            <p className="text-sm mt-1 p-3 bg-muted rounded-md">
              {report.question}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* V1 Content */}
      {activeTab === "v1" && (
        <>
          {/* Conclusion & Confidence */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Conclusion</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {report.conclusion}
                </p>
                {(report as any).uncertainties?.length > 0 && (
                  <div className="mt-4">
                    <span className="text-sm font-medium text-muted-foreground">
                      Uncertainties
                    </span>
                    <ul className="mt-1 space-y-1">
                      {(report as any).uncertainties.map((u: string, i: number) => (
                        <li key={i} className="text-sm text-yellow-600 dark:text-yellow-400">
                          - {u}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {(report as any).recommendations?.length > 0 && (
                  <div className="mt-4">
                    <span className="text-sm font-medium text-muted-foreground">
                      Recommendations
                    </span>
                    <ul className="mt-1 space-y-1">
                      {(report as any).recommendations.map((r: string, i: number) => (
                        <li key={i} className="text-sm text-blue-600 dark:text-blue-400">
                          - {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Confidence
                </CardTitle>
              </CardHeader>
              <CardContent className="text-center py-6">
                <div className={`text-5xl font-bold ${confidenceColor}`}>
                  {(confidence * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  {confidence >= 0.8
                    ? "High confidence"
                    : confidence >= 0.6
                      ? "Moderate confidence"
                      : "Low confidence"}
                </p>
                {report.review_required && (
                  <Badge variant="warning" className="mt-4">
                    Human Review Required
                  </Badge>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Evidence */}
          {report.evidence?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Evidence ({report.evidence.length} items)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {report.evidence.map((e: string, i: number) => (
                    <div
                      key={i}
                      className="p-3 bg-muted rounded-md text-sm flex gap-3"
                    >
                      <Badge variant="outline" className="shrink-0">
                        {i + 1}
                      </Badge>
                      <span>{e}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* V1 Agent Results */}
          {agentResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Agent Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {agentResults.map((agent: any, i: number) => (
                    <div key={i} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{agent.agent ?? `Agent ${i + 1}`}</Badge>
                          {agent.confidence != null && (
                            <span className="text-sm text-muted-foreground">
                              {(agent.confidence * 100).toFixed(1)}%
                            </span>
                          )}
                        </div>
                        {agent.duration_ms != null && (
                          <span className="text-xs text-muted-foreground">
                            {agent.duration_ms.toFixed(0)}ms
                          </span>
                        )}
                      </div>
                      {agent.summary && (
                        <p className="text-sm">{agent.summary}</p>
                      )}
                      {agent.evidence?.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {agent.evidence.slice(0, 3).map((e: string, j: number) => (
                            <Badge key={j} variant="secondary" className="text-xs">
                              {e.substring(0, 50)}
                              {e.length > 50 ? "..." : ""}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* V2 Content */}
      {activeTab === "v2" && (
        <>
          {/* Agent Findings */}
          {Object.keys((report as any).agent_findings || {}).length > 0 ? (
            <AgentFindingsPanel findings={(report as any).agent_findings} />
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Brain className="h-12 w-12 mx-auto text-neutral-400 mb-4" />
                <p className="text-neutral-500">No V2 findings available</p>
                <p className="text-sm text-neutral-400 mt-1">
                  Run a V2 investigation to see LLM-powered agent results
                </p>
              </CardContent>
            </Card>
          )}

          {/* Debate Rounds */}
          {debateRounds.length > 0 && (
            <DebateVisualization
              rounds={debateRounds}
              consensus={consensus}
            />
          )}

          {/* Reasoning Chains */}
          {Object.keys(reasoningChains).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Reasoning Chains
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {Object.entries(reasoningChains).map(
                    ([agent, steps]: [string, any]) => (
                      <ReasoningChainViewer
                        key={agent}
                        agent={agent}
                        steps={steps}
                      />
                    )
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Safety Check */}
      {(report as any).safety_check && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Safety Check
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <span className="text-xs text-muted-foreground">Status</span>
                <p className="font-medium">
                  {(report as any).safety_check.safe ? (
                    <span className="text-green-500">Safe</span>
                  ) : (
                    <span className="text-red-500">Blocked</span>
                  )}
                </p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Tier</span>
                <p className="font-medium capitalize">
                  {(report as any).safety_check.confidence_tier}
                </p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Review</span>
                <p className="font-medium">
                  {(report as any).safety_check.requires_review ? "Required" : "Auto-approved"}
                </p>
              </div>
              {(report as any).safety_check.contradictions && (
                <div>
                  <span className="text-xs text-muted-foreground">Contradictions</span>
                  <p className="font-medium">
                    {(report as any).safety_check.contradictions.count ?? 0}
                  </p>
                </div>
              )}
            </div>
            {(report as any).safety_check.block_reasons?.length > 0 && (
              <div className="mt-4">
                <span className="text-sm font-medium text-red-500">Block Reasons</span>
                <ul className="mt-1 space-y-1">
                  {(report as any).safety_check.block_reasons.map((r: string, i: number) => (
                    <li key={i} className="text-sm text-red-500">
                      - {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Review Section */}
      {report.review_required && !report.reviewed && (
        <Card>
          <CardHeader>
            <CardTitle>Review Investigation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Add review notes (optional)..."
              value={reviewNotes}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                setReviewNotes(e.target.value)
              }
            />
            <div className="flex gap-3">
              <Button
                onClick={() =>
                  reviewMutation.mutate({
                    decision: "approved",
                    notes: reviewNotes,
                  })
                }
                disabled={reviewMutation.isPending}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Approve
              </Button>
              <Button
                variant="destructive"
                onClick={() =>
                  reviewMutation.mutate({
                    decision: "rejected",
                    notes: reviewNotes,
                  })
                }
                disabled={reviewMutation.isPending}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
              <Button
                variant="outline"
                onClick={() =>
                  reviewMutation.mutate({
                    decision: "needs_modification",
                    notes: reviewNotes,
                  })
                }
                disabled={reviewMutation.isPending}
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                Needs Modification
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Review History */}
      {report.reviewed && (
        <Card>
          <CardHeader>
            <CardTitle>Review History</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Decision</span>
                <p className="font-medium">{report.review_decision ?? "N/A"}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Reviewer</span>
                <p className="font-medium">{report.reviewer_id}</p>
              </div>
              {report.reviewed_at && (
                <div>
                  <span className="text-muted-foreground">Reviewed At</span>
                  <p className="font-medium">
                    {new Date(report.reviewed_at).toLocaleString()}
                  </p>
                </div>
              )}
              {report.review_notes && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">Notes</span>
                  <p className="mt-1 p-3 bg-muted rounded-md">{report.review_notes}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
