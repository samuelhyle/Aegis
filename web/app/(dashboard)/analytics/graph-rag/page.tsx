"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useGraphRAGEvidence, usePatientPatterns, usePatientCommunities, useGraphCentrality } from "@/lib/hooks/useQueries";
import { GitGraph, Search, Database, FileText, Layers } from "lucide-react";
import type { GraphRAGEvidenceItem, GraphRAGPattern } from "@/types";

export default function GraphRAGAnalyticsPage() {
  const [patientId, setPatientId] = useState("");
  const [query, setQuery] = useState("");
  const { data: evidence, isLoading: isLoadingEvidence } = useGraphRAGEvidence(patientId, query);
  const { data: patterns } = usePatientPatterns(patientId);
  const { data: communities } = usePatientCommunities(patientId);
  const { data: centrality } = useGraphCentrality(patientId);

  const evidenceItems = evidence?.evidence;
  const patternItems = patterns?.patterns;
  const communityItems = communities?.communities;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Graph RAG Analytics</h1>
          <p className="text-neutral-500 dark:text-neutral-400">Knowledge graph exploration and semantic search</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Patterns</p>
                <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                  {patternItems?.length || 0}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-blue-100">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Communities</p>
                <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                  {communityItems?.length || 0}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-green-100">
                <GitGraph className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">Centrality Nodes</p>
                <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                  {centrality?.centrality_scores?.length || 0}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-purple-100">
                <FileText className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Semantic Search
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Patient ID"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="w-48 px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg"
            />
            <input
              type="text"
              placeholder="Search knowledge graph..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg"
            />
            <Button disabled={!patientId || !query}>
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
          </div>
          {isLoadingEvidence && <p className="text-sm text-neutral-500">Loading...</p>}
          {evidenceItems && evidenceItems.length > 0 && (
            <div className="space-y-3">
              {evidenceItems.map((item: GraphRAGEvidenceItem, i: number) => (
                <div key={i} className="p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900">
                  <p className="font-medium text-neutral-900 dark:text-white">{item.description}</p>
                  <p className="text-sm text-neutral-500 mt-1">{item.node_type}</p>
                  {item.relevance_score && (
                    <p className="text-xs text-neutral-400 mt-1">Relevance: {Math.round(item.relevance_score * 100)}%</p>
                  )}
                </div>
              ))}
            </div>
          )}
          {evidence && !evidence.evidence?.length && !isLoadingEvidence && patientId && query && (
            <p className="text-sm text-neutral-500">No evidence found. Try a different query.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Knowledge Graph Context
          </CardTitle>
        </CardHeader>
        <CardContent>
          {evidenceItems && evidenceItems.length > 0 || patternItems && patternItems.length > 0 || communityItems && communityItems.length > 0 ? (
            <div className="h-96 relative border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden bg-neutral-50 dark:bg-neutral-900">
              <svg width="100%" height="100%" viewBox="0 0 800 400">
                {/* Render nodes from evidence */}
                {evidenceItems?.slice(0, 10).map((item: GraphRAGEvidenceItem, i: number) => {
                  const x = 100 + (i % 5) * 140;
                  const y = 80 + Math.floor(i / 5) * 120;
                  return (
                    <g key={`evidence-${i}`}>
                      <circle
                        cx={x}
                        cy={y}
                        r={20}
                        fill="#6366f1"
                        opacity={0.8}
                        className="cursor-pointer hover:opacity-100 transition-opacity"
                      />
                      <text
                        x={x}
                        y={y + 35}
                        textAnchor="middle"
                        className="fill-neutral-600 dark:fill-neutral-400 text-[10px]"
                      >
                        {(item.description || "Node").slice(0, 15)}
                      </text>
                    </g>
                  );
                })}
                {/* Render pattern nodes */}
                {patternItems?.slice(0, 5).map((pattern: GraphRAGPattern, i: number) => {
                  const x = 150 + i * 120;
                  const y = 280;
                  return (
                    <g key={`pattern-${i}`}>
                      <rect
                        x={x - 25}
                        y={y - 15}
                        width={50}
                        height={30}
                        rx={4}
                        fill="#22c55e"
                        opacity={0.8}
                        className="cursor-pointer hover:opacity-100 transition-opacity"
                      />
                      <text
                        x={x}
                        y={y + 30}
                        textAnchor="middle"
                        className="fill-neutral-600 dark:fill-neutral-400 text-[10px]"
                      >
                        Pattern {i + 1}
                      </text>
                    </g>
                  );
                })}
                {/* Render edges */}
                {evidenceItems?.slice(0, 8).map((_item: GraphRAGEvidenceItem, i: number) => {
                  if (i === 0) return null;
                  const x1 = 100 + ((i - 1) % 5) * 140;
                  const y1 = 80 + Math.floor((i - 1) / 5) * 120;
                  const x2 = 100 + (i % 5) * 140;
                  const y2 = 80 + Math.floor(i / 5) * 120;
                  return (
                    <line
                      key={`edge-${i}`}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke="#94a3b8"
                      strokeWidth={1}
                      opacity={0.5}
                    />
                  );
                })}
              </svg>
              <div className="absolute bottom-2 left-2 flex gap-4 text-xs text-neutral-500">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-indigo-500" />
                  Evidence
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-green-500" />
                  Patterns
                </div>
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-neutral-500">
              <div className="text-center">
                <GitGraph className="h-12 w-12 mx-auto mb-4 text-neutral-400" />
                <p>Enter a patient ID to view knowledge graph</p>
                <p className="text-sm">Graph will display evidence and pattern nodes</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}