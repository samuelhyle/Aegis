"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { ScrollArea } from "@/components/ui/ScrollArea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { cn, formatRelativeTime } from "@/lib/utils";
import { Search, Loader2, Eye, FileText, CheckCircle, XCircle, AlertCircle, Clock, Brain } from "lucide-react";
import { useInvestigations, useRunInvestigation, useRunInvestigationV2 } from "@/lib/hooks/useQueries";
import { useInvestigationStream } from "@/lib/hooks/useInvestigationStream";
import type { InvestigationReport } from "@/types";

interface InvestigationsTabProps {
  patientId: string;
}

export function InvestigationsTab({ patientId }: InvestigationsTabProps) {
  const [question, setQuestion] = useState("");
  const [streamingReport, setStreamingReport] = useState<InvestigationReport | null>(null);

  const { data: investigationsData, isLoading, refetch } = useInvestigations(patientId);
  const runInvestigation = useRunInvestigation();
  const runInvestigationV2 = useRunInvestigationV2();

  const { events, currentAgent, agentsCompleted, isStreaming, report: streamReport, startStream, cancelStream } = useInvestigationStream();

  const handleInvestigate = async (useV2 = false) => {
    if (!question.trim()) return;

    setStreamingReport(null);

    if (useV2) {
      await runInvestigationV2.mutateAsync({
        patient_id: patientId,
        question,
        agents: ["diagnostic", "treatment", "risk_assessment", "timeline"],
        enable_debate: true,
        evaluate: true,
      });
    } else {
      await startStream(patientId, question);
    }

    setQuestion("");
    refetch();
  };

  const investigations = investigationsData?.traces || [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Run Investigation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a clinical question about this patient..."
            rows={3}
            className="font-mono text-sm"
          />
          <div className="flex items-center gap-3">
            <Button
              onClick={() => handleInvestigate(false)}
              disabled={runInvestigation.isPending || !question.trim()}
              className="flex-1 sm:flex-none"
            >
              <Search className="h-4 w-4 mr-2" />
              {runInvestigation.isPending ? "Investigating..." : "Run Investigation"}
            </Button>
            <Button
              variant="outline"
              onClick={() => handleInvestigate(true)}
              disabled={runInvestigationV2.isPending || !question.trim()}
              className="flex-1 sm:flex-none"
            >
              <Brain className="h-4 w-4 mr-2" />
              {runInvestigationV2.isPending ? "Multi-Agent..." : "Multi-Agent v2"}
            </Button>
          </div>

          {(runInvestigation.isPending || runInvestigationV2.isPending || isStreaming) && (
            <div className="p-4 rounded-lg bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800">
              <div className="flex items-center gap-3 mb-2">
                <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
                <span className="font-medium">Investigation in progress...</span>
                {isStreaming && (
                  <Button variant="ghost" size="sm" onClick={cancelStream}>
                    Cancel
                  </Button>
                )}
              </div>
              <div className="space-y-1 text-sm text-neutral-600 dark:text-neutral-400">
                {currentAgent && (
                  <div className="flex items-center gap-2">
                    <span className="text-primary-600">•</span>
                    <span>Running: {currentAgent.replace("_", " ")}</span>
                  </div>
                )}
                {agentsCompleted > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-green-600">•</span>
                    <span>{agentsCompleted} agent{agentsCompleted !== 1 ? "s" : ""} completed</span>
                  </div>
                )}
                {events.slice(-5).map((event, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-primary-600">•</span>
                    <span>
                      {event.type === "agent_started" && `Agent started: ${event.agent}`}
                      {event.type === "agent_completed" && `Agent completed: ${event.agent}`}
                      {event.type === "agent_failed" && `Agent failed: ${event.agent}`}
                      {event.type === "investigation_completed" && "Investigation completed"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(streamReport || streamingReport) && (
            <Card className="border-green-200 dark:border-green-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-green-800 dark:text-green-400">Investigation Complete</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setStreamingReport(null)}>
                  <XCircle className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <p className="font-medium">{streamReport?.conclusion || streamingReport?.conclusion}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <ConfidenceBadge confidence={streamReport?.confidence || streamingReport?.confidence || 0} />
                    <Badge variant="outline">{streamReport?.agent_results?.length || 0} agents</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Investigation History ({investigations.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" /></div>
          ) : investigations.length === 0 ? (
            <p className="text-neutral-500 py-8 text-center">No investigations yet</p>
          ) : (
            <Tabs defaultValue="all" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="all">All ({investigations.length})</TabsTrigger>
                <TabsTrigger value="completed">Completed</TabsTrigger>
                <TabsTrigger value="pending_review">Pending Review</TabsTrigger>
                <TabsTrigger value="reviewed">Reviewed</TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="mt-4">
                <InvestigationList investigations={investigations} />
              </TabsContent>
              <TabsContent value="completed" className="mt-4">
                <InvestigationList investigations={investigations.filter(i => !i.review_required && !i.reviewed)} />
              </TabsContent>
              <TabsContent value="pending_review" className="mt-4">
                <InvestigationList investigations={investigations.filter(i => i.review_required && !i.reviewed)} />
              </TabsContent>
              <TabsContent value="reviewed" className="mt-4">
                <InvestigationList investigations={investigations.filter(i => i.reviewed)} />
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function InvestigationList({ investigations }: { investigations: InvestigationReport[] }) {
  return (
    <ScrollArea className="max-h-96">
      <div className="space-y-3">
        {investigations.map((inv) => (
          <InvestigationCard key={inv.trace_id} investigation={inv} />
        ))}
      </div>
    </ScrollArea>
  );
}

function InvestigationCard({ investigation }: { investigation: InvestigationReport }) {
  const isReviewed = investigation.reviewed;
  const needsReview = investigation.review_required && !isReviewed;

  return (
    <Card className={cn(needsReview && "border-yellow-200 dark:border-yellow-800 bg-yellow-50/50 dark:bg-yellow-900/10")}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <p className="font-medium text-neutral-900 dark:text-white truncate">{investigation.question}</p>
              {needsReview && (
                <Badge variant="warning"><AlertCircle className="h-3 w-3 mr-1" />Needs Review</Badge>
              )}
              {isReviewed && investigation.review_decision === "approved" && (
                <Badge variant="success"><CheckCircle className="h-3 w-3 mr-1" />Approved</Badge>
              )}
              {isReviewed && investigation.review_decision === "rejected" && (
                <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>
              )}
              {!needsReview && !isReviewed && (
                <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Complete</Badge>
              )}
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2">{investigation.conclusion}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-neutral-500">
              <span>Confidence: {Math.round((investigation.confidence || 0) * 100)}%</span>
              <span>{investigation.agent_results?.length || 0} agents</span>
              <span>{formatRelativeTime(investigation.generated_at)}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Eye className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <FileText className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const percentage = Math.round(confidence * 100);
  const variant = confidence >= 0.8 ? "success" : confidence >= 0.6 ? "warning" : "destructive";
  return <Badge variant={variant}>{percentage}% confidence</Badge>;
}
