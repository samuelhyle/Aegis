"use client";

import { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { Search, X, Filter, Loader2 } from "lucide-react";

interface VectorSearchBarProps {
  onSearch: (query: string, patientId?: string, sourceTypes?: string[]) => void;
  isLoading?: boolean;
  patients?: Array<{ patient_id: string; first_name: string; last_name: string }>;
  className?: string;
}

const SOURCE_TYPES = [
  { id: "condition", label: "Conditions" },
  { id: "medication", label: "Medications" },
  { id: "observation", label: "Observations" },
  { id: "encounter", label: "Encounters" },
];

export function VectorSearchBar({
  onSearch,
  isLoading = false,
  patients = [],
  className,
}: VectorSearchBarProps) {
  const [query, setQuery] = useState("");
  const [patientId, setPatientId] = useState<string | undefined>();
  const [selectedSourceTypes, setSelectedSourceTypes] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [patientSearch, setPatientSearch] = useState("");

  const filteredPatients = patients.filter(
    (p) =>
      p.first_name.toLowerCase().includes(patientSearch.toLowerCase()) ||
      p.last_name.toLowerCase().includes(patientSearch.toLowerCase()) ||
      p.patient_id.toLowerCase().includes(patientSearch.toLowerCase())
  );

  const selectedPatient = patients.find((p) => p.patient_id === patientId);

  const handleSearch = useCallback(() => {
    if (!query.trim()) return;
    onSearch(
      query.trim(),
      patientId,
      selectedSourceTypes.length > 0 ? selectedSourceTypes : undefined
    );
  }, [query, patientId, selectedSourceTypes, onSearch]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const toggleSourceType = (type: string) => {
    setSelectedSourceTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const clearFilters = () => {
    setPatientId(undefined);
    setSelectedSourceTypes([]);
  };

  const hasFilters = patientId || selectedSourceTypes.length > 0;

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardContent className="p-4">
        {/* Search Input */}
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search clinical evidence... (e.g., 'diabetes medications', 'high blood pressure')"
              className="pl-10 pr-4"
              disabled={isLoading}
            />
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowFilters(!showFilters)}
            className={cn(showFilters && "bg-neutral-100 dark:bg-neutral-800")}
          >
            <Filter className="h-4 w-4" />
          </Button>
          <Button onClick={handleSearch} disabled={isLoading || !query.trim()}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Search"
            )}
          </Button>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-800 space-y-4">
            {/* Patient Filter */}
            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2 block">
                Patient
              </label>
              <div className="relative">
                <Input
                  placeholder="Search patients..."
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                  className="mb-2"
                />
                <div className="max-h-40 overflow-y-auto space-y-1">
                  {filteredPatients.slice(0, 10).map((patient) => (
                    <button
                      key={patient.patient_id}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded-lg text-sm transition-colors",
                        patientId === patient.patient_id
                          ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                          : "hover:bg-neutral-100 dark:hover:bg-neutral-800"
                      )}
                      onClick={() => {
                        setPatientId(
                          patientId === patient.patient_id
                            ? undefined
                            : patient.patient_id
                        );
                        setPatientSearch("");
                      }}
                    >
                      {patient.first_name} {patient.last_name}
                      <span className="text-neutral-500 ml-2">
                        ({patient.patient_id.slice(0, 8)}...)
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Source Type Filter */}
            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2 block">
                Source Types
              </label>
              <div className="flex flex-wrap gap-2">
                {SOURCE_TYPES.map((type) => (
                  <button
                    key={type.id}
                    className={cn(
                      "px-3 py-1.5 rounded-full text-sm transition-colors",
                      selectedSourceTypes.includes(type.id)
                        ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-300 dark:border-blue-700"
                        : "bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-transparent"
                    )}
                    onClick={() => toggleSourceType(type.id)}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Clear Filters */}
            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="h-4 w-4 mr-1" />
                Clear Filters
              </Button>
            )}
          </div>
        )}

        {/* Active Filters */}
        {hasFilters && !showFilters && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-neutral-500">Filters:</span>
            {selectedPatient && (
              <Badge variant="secondary" className="text-xs">
                {selectedPatient.first_name} {selectedPatient.last_name}
              </Badge>
            )}
            {selectedSourceTypes.map((type) => (
              <Badge key={type} variant="secondary" className="text-xs">
                {SOURCE_TYPES.find((t) => t.id === type)?.label}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
