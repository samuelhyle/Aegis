"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { ScrollArea } from "@/components/ui/ScrollArea";
import { Brain, GitGraph, Users, Link2, Zap, Loader2 } from "lucide-react";
import { useGraphRAGEvidence, usePatientPatterns, useCausalChains, usePatientCommunities, useGraphCentrality } from "@/lib/hooks/useQueries";
import type { GraphRAGEvidenceItem, GraphRAGPattern, GraphRAGPath, PatientCommunity, GraphCentralityScore } from "@/types";

interface GraphRAGExplorerProps {
  patientId: string;
}

export function GraphRAGExplorer({ patientId }: GraphRAGExplorerProps) {
  const [query, setQuery] = useState("");

  const { data: evidenceData, isLoading: evidenceLoading } = useGraphRAGEvidence(patientId, query);
  const { data: patternsData, isLoading: patternsLoading } = usePatientPatterns(patientId);
  const { data: causalData, isLoading: causalLoading } = useCausalChains(patientId);
  const { data: communitiesData, isLoading: communitiesLoading } = usePatientCommunities(patientId);
  const { data: centralityData, isLoading: centralityLoading } = useGraphCentrality(patientId);

  const evidence = evidenceData?.evidence;
  const patterns = patternsData?.patterns;
  const causalChains = causalData?.causal_chains;
  const communities = communitiesData?.communities;
  const centralityScores = centralityData?.centrality_scores;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Graph RAG Explorer</CardTitle>
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search patient knowledge graph..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-80"
            />
            {evidenceLoading && <Loader2 className="h-4 w-4 animate-spin text-neutral-500" />}
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="evidence" className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="evidence"><Brain className="h-4 w-4 mr-2" />Evidence</TabsTrigger>
              <TabsTrigger value="patterns"><GitGraph className="h-4 w-4 mr-2" />Patterns</TabsTrigger>
              <TabsTrigger value="causal"><Zap className="h-4 w-4 mr-2" />Causal Chains</TabsTrigger>
              <TabsTrigger value="communities"><Users className="h-4 w-4 mr-2" />Communities</TabsTrigger>
              <TabsTrigger value="centrality"><Link2 className="h-4 w-4 mr-2" />Centrality</TabsTrigger>
            </TabsList>

            <TabsContent value="evidence" className="mt-4">
              {evidenceLoading ? (
                <div className="py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" /></div>
              ) : evidence && evidence.length > 0 ? (
                <ScrollArea className="max-h-96">
                  <div className="space-y-3">
                    {evidence.map((item: GraphRAGEvidenceItem, i: number) => (
                      <div key={i} className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-800">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-neutral-900 dark:text-white">{item.description}</p>
                            <div className="mt-1 flex items-center gap-2 text-xs text-neutral-500">
                              <Badge variant="outline">{item.node_type}</Badge>
                              <span>Relevance: {Math.round(item.relevance_score * 100)}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-neutral-500 py-8 text-center">No evidence found. Try a different query.</p>
              )}
            </TabsContent>

            <TabsContent value="patterns" className="mt-4">
              {patternsLoading ? (
                <div className="py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" /></div>
              ) : patterns && patterns.length > 0 ? (
                <ScrollArea className="max-h-96">
                  <div className="space-y-3">
                    {patterns.map((pattern: GraphRAGPattern, i: number) => (
                      <div key={i} className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-800">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-neutral-900 dark:text-white capitalize">{pattern.pattern_type}</p>
                            <p className="text-sm text-neutral-500">{pattern.description}</p>
                          </div>
                          <Badge variant="outline">{Math.round(pattern.confidence * 100)}% confidence</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-neutral-500 py-8 text-center">No patterns discovered</p>
              )}
            </TabsContent>

            <TabsContent value="causal" className="mt-4">
              {causalLoading ? (
                <div className="py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" /></div>
              ) : causalChains && causalChains.length > 0 ? (
                <ScrollArea className="max-h-96">
                  <div className="space-y-3">
                    {causalChains.map((chain: GraphRAGPath, i: number) => (
                      <div key={i} className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-800">
                        <p className="font-medium text-neutral-900 dark:text-white">{chain.relationship_chain?.join(" → ") || "Causal chain"}</p>
                        <div className="mt-2 flex items-center gap-2 text-sm text-neutral-500">
                          {chain.nodes?.map((node: string, j: number) => (
                            <span key={j} className="flex items-center gap-1">
                              {j > 0 && <span className="text-neutral-300">→</span>}
                              <code className="px-2 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800">{node}</code>
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-neutral-500 py-8 text-center">No causal chains found</p>
              )}
            </TabsContent>

            <TabsContent value="communities" className="mt-4">
              {communitiesLoading ? (
                <div className="py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" /></div>
              ) : communities && communities.length > 0 ? (
                <ScrollArea className="max-h-96">
                  <div className="space-y-3">
                    {communities.map((community: PatientCommunity, i: number) => (
                      <div key={i} className="p-4 rounded-lg border border-neutral-200 dark:border-neutral-800">
                        <p className="font-medium text-neutral-900 dark:text-white">Community {i + 1}</p>
                        <p className="text-sm text-neutral-500">{community.nodes?.length} nodes • {community.cohesion_score?.toFixed(3)} cohesion</p>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {community.nodes?.slice(0, 5).map((node: string, j: number) => (
                            <Badge key={j} variant="outline" className="text-xs">{node}</Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-neutral-500 py-8 text-center">No communities detected</p>
              )}
            </TabsContent>

            <TabsContent value="centrality" className="mt-4">
              {centralityLoading ? (
                <div className="py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" /></div>
              ) : centralityScores && centralityScores.length > 0 ? (
                <ScrollArea className="max-h-96">
                  <div className="space-y-2">
                    {centralityScores.map((item: GraphCentralityScore, i: number) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                        <div className="flex-1">
                          <p className="font-medium text-neutral-900 dark:text-white">{item.description || item.node_id}</p>
                          <p className="text-xs text-neutral-500">{item.node_id}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-mono text-lg font-bold text-primary-600">{item.score.toFixed(3)}</p>
                          <p className="text-xs text-neutral-500">Centrality</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-neutral-500 py-8 text-center">No centrality data</p>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}