"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { cn, formatRelativeTime } from "@/lib/utils";
import { Eye, FileText, CheckCircle, XCircle, AlertCircle, Clock } from "lucide-react";
import Link from "next/link";
import { useInvestigations, useReviewInvestigation } from "@/lib/hooks/useQueries";
import type { InvestigationReport } from "@/types";
import { useState } from "react";

export default function InvestigationsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const { data, isLoading } = useInvestigations(undefined, undefined, pageSize, page * pageSize);
  const reviewMutation = useReviewInvestigation();

  const investigations = data?.traces || [];
  const canGoNext = data?.has_more;
  const canGoPrev = page > 0;

  const filteredInvestigations = investigations.filter((inv) => {
    const matchesSearch = inv.question.toLowerCase().includes(search.toLowerCase()) ||
      inv.patient_id.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" ||
      (statusFilter === "reviewed" && inv.reviewed) ||
      (statusFilter === "pending" && inv.review_required && !inv.reviewed) ||
      (statusFilter === "completed" && !inv.review_required && !inv.reviewed);
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Investigations</h1>
            <p className="text-neutral-500 dark:text-neutral-400">
              {data?.total || 0} total • {filteredInvestigations.length} showing
            </p>
          </div>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Investigation History</CardTitle>
            <div className="flex items-center gap-2">
              <Input
                placeholder="Search investigations..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-64"
              />
              <Select value={statusFilter} onValueChange={setStatusFilter} options={[
                { value: "all", label: "All Status" },
                { value: "reviewed", label: "Reviewed" },
                { value: "pending", label: "Pending Review" },
                { value: "completed", label: "Completed" },
              ]} className="w-40" />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-8 space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-20 animate-pulse bg-neutral-200 dark:bg-neutral-800 rounded-lg" />
                ))}
              </div>
            ) : filteredInvestigations.length === 0 ? (
              <div className="p-8 text-center text-neutral-500">
                No investigations found matching your criteria
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full" role="table">
                    <thead>
                      <tr className="border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900">
                        <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Question</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Patient</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Confidence</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Agents</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Date</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-neutral-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                      {filteredInvestigations.map((inv) => (
                        <InvestigationRow key={inv.trace_id} investigation={inv} reviewMutation={reviewMutation} />
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="p-4 border-t border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
                  <Button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={!canGoPrev}
                    variant="outline"
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-neutral-500">
                    {page * pageSize + 1}–{Math.min((page + 1) * pageSize, data?.total || 0)} of {data?.total || 0}
                  </span>
                  <Button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!canGoNext}
                    variant="outline"
                  >
                    Next
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
  );
}

function InvestigationRow({ investigation, reviewMutation }: { investigation: InvestigationReport; reviewMutation: any }) {
  const isReviewed = investigation.reviewed;
  const needsReview = investigation.review_required && !isReviewed;
  const [showReview, setShowReview] = useState(false);
  const [reviewDecision, setReviewDecision] = useState<"approved" | "rejected" | "needs_modification">("approved");
  const [reviewNotes, setReviewNotes] = useState("");

  const handleReview = (decision: "approved" | "rejected" | "needs_modification") => {
    reviewMutation.mutate({
      traceId: investigation.trace_id,
      decision,
      reviewerId: "current-user", // Would come from auth context
      notes: reviewNotes,
    });
    setShowReview(false);
    setReviewNotes("");
  };

  return (
    <tr className={cn("hover:bg-neutral-50 dark:hover:bg-neutral-900/50", needsReview && "bg-yellow-50/50 dark:bg-yellow-900/10")}>
      <td className="px-4 py-3">
        <p className="font-medium text-neutral-900 dark:text-white truncate max-w-md">{investigation.question}</p>
      </td>
      <td className="px-4 py-3 font-mono text-sm text-neutral-600 dark:text-neutral-400">
        {investigation.patient_id.slice(0, 8)}...
      </td>
      <td className="px-4 py-3">
        {needsReview && (
          <Badge variant="warning" className="gap-1">
            <AlertCircle className="h-3 w-3" /> Pending Review
          </Badge>
        )}
        {isReviewed && investigation.review_decision === "approved" && (
          <Badge variant="success" className="gap-1">
            <CheckCircle className="h-3 w-3" /> Approved
          </Badge>
        )}
        {isReviewed && investigation.review_decision === "rejected" && (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" /> Rejected
          </Badge>
        )}
        {!needsReview && !isReviewed && (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" /> Complete
          </Badge>
        )}
      </td>
      <td className="px-4 py-3">
        <Badge variant={investigation.confidence >= 0.8 ? "success" : investigation.confidence >= 0.6 ? "warning" : "destructive"}>
          {Math.round((investigation.confidence || 0) * 100)}%
        </Badge>
      </td>
      <td className="px-4 py-3 text-neutral-600 dark:text-neutral-400">{investigation.agent_results?.length || 0}</td>
      <td className="px-4 py-3 text-neutral-600 dark:text-neutral-400">{formatRelativeTime(investigation.generated_at)}</td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-1">
          <Link href={`/investigations/${investigation.trace_id}`}>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Eye className="h-4 w-4" />
            </Button>
          </Link>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <FileText className="h-4 w-4" />
          </Button>
          {needsReview && !showReview && (
            <Button variant="outline" size="sm" onClick={() => setShowReview(true)}>Review</Button>
          )}
          {needsReview && showReview && (
            <div className="flex items-center gap-2">
              <Select
                value={reviewDecision}
                onValueChange={(v) => setReviewDecision(v as "approved" | "rejected" | "needs_modification")}
                options={[
                  { value: "approved", label: "Approve" },
                  { value: "rejected", label: "Reject" },
                  { value: "needs_modification", label: "Needs Modification" },
                ]}
                className="w-40"
              />
              <Input
                placeholder="Notes (optional)"
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                className="w-40"
              />
              <Button size="sm" onClick={() => handleReview(reviewDecision)}>Submit</Button>
              <Button variant="ghost" size="sm" onClick={() => setShowReview(false)}>Cancel</Button>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}