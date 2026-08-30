"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { VectorSearchBar } from "@/components/search/VectorSearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Loader2, Search, Database } from "lucide-react";

export default function SearchPage() {
  const [searchParams, setSearchParams] = useState<{
    query: string;
    patientId?: string;
    sourceTypes?: string[];
  } | null>(null);

  const { data: patientsData } = useQuery({
    queryKey: ["patients"],
    queryFn: () => apiClient.listPatients(100),
  });

  const { data: searchData, isLoading: searchLoading } = useQuery({
    queryKey: ["search", "vectors", searchParams],
    queryFn: () =>
      searchParams
        ? apiClient.searchVectors(
            searchParams.query,
            searchParams.patientId,
            searchParams.sourceTypes
          )
        : null,
    enabled: !!searchParams,
  });

  const patients = patientsData?.patients || [];

  const handleSearch = (
    query: string,
    patientId?: string,
    sourceTypes?: string[]
  ) => {
    setSearchParams({ query, patientId, sourceTypes });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">
          Vector Search
        </h1>
        <p className="text-neutral-500 dark:text-neutral-400">
          Semantic search over clinical evidence using pgvector
        </p>
      </div>

      <VectorSearchBar
        onSearch={handleSearch}
        isLoading={searchLoading}
        patients={patients}
      />

      {searchLoading && (
        <Card>
          <CardContent className="p-8">
            <div className="flex items-center justify-center gap-3">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
              <span className="text-neutral-600 dark:text-neutral-400">
                Searching clinical evidence...
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {!searchLoading && searchData && (
        <SearchResults
          results={searchData.results}
          total={searchData.total}
          query={searchParams?.query || ""}
        />
      )}

      {!searchLoading && !searchData && (
        <Card>
          <CardContent className="p-8 text-center">
            <Search className="h-12 w-12 mx-auto text-neutral-400 mb-4" />
            <p className="text-neutral-500">
              Enter a search query to find similar clinical evidence
            </p>
            <div className="mt-4 max-w-md mx-auto">
              <p className="text-sm text-neutral-400 mb-2">Example queries:</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {[
                  "diabetes medications",
                  "high blood pressure",
                  "cardiac conditions",
                  "anticoagulation therapy",
                ].map((example) => (
                  <button
                    key={example}
                    className="text-xs px-3 py-1.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                    onClick={() => handleSearch(example)}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Search Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900 dark:text-white">
                {patients.length}
              </p>
              <p className="text-sm text-neutral-500">Patients</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900 dark:text-white">
                4
              </p>
              <p className="text-sm text-neutral-500">Source Types</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900 dark:text-white">
                pgvector
              </p>
              <p className="text-sm text-neutral-500">Vector Backend</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
