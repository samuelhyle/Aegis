"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Select } from "@/components/ui/Input";
import { AvatarWithFallback } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { usePatients } from "@/lib/hooks/useQueries";
import { calculateAge } from "@/lib/utils";
import { Search, UserPlus } from "lucide-react";
import Link from "next/link";

export default function PatientsPage() {
  const [search, setSearch] = useState("");
  const [genderFilter, setGenderFilter] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const { data, isLoading } = usePatients(pageSize, page * pageSize);

  const filteredPatients = data?.patients.filter((p) => {
    const matchesSearch = `${p.first_name} ${p.last_name}`.toLowerCase().includes(search.toLowerCase()) ||
      p.patient_id.toLowerCase().includes(search.toLowerCase());
    const matchesGender = !genderFilter || p.gender === genderFilter;
    return matchesSearch && matchesGender;
  }) || [];

  const canGoNext = data?.has_more;
  const canGoPrev = page > 0;

  return (
    <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">Patients</h1>
            <p className="text-neutral-500 dark:text-neutral-400">
              {data?.total || 0} patients • {filteredPatients.length} showing
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm">
              <UserPlus className="h-4 w-4 mr-2" />
              Add Patient
            </Button>
            <Button>
              <Search className="h-4 w-4 mr-2" />
              Advanced Search
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Patient List</CardTitle>
            <div className="flex items-center gap-2">
              <Select
                value={genderFilter}
                onValueChange={setGenderFilter}
                options={[
                  { value: "", label: "All Genders" },
                  { value: "M", label: "Male" },
                  { value: "F", label: "Female" },
                  { value: "O", label: "Other" },
                ]}
                className="w-40"
              />
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
                <input
                  type="search"
                  placeholder="Search patients..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="h-10 w-64 rounded-lg border border-neutral-200 bg-white px-10 py-2 text-sm placeholder:text-neutral-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 dark:border-neutral-700 dark:bg-neutral-900"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-8 space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 animate-pulse bg-neutral-200 dark:bg-neutral-800 rounded-lg" />
                ))}
              </div>
            ) : filteredPatients.length === 0 ? (
              <div className="p-8 text-center text-neutral-500">
                No patients found matching your criteria
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full" role="table">
                  <thead>
                    <tr className="border-b border-neutral-200 dark:border-neutral-800">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">Patient</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">Gender</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">Age</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">Location</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">ID</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                    {filteredPatients.map((patient) => (
                      <tr key={patient.patient_id} className="hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors">
                        <td className="px-4 py-4">
                          <Link href={`/patients/${patient.patient_id}`} className="flex items-center gap-3">
                            <AvatarWithFallback firstName={patient.first_name} lastName={patient.last_name} size="md" />
                            <div>
                              <p className="font-medium text-neutral-900 dark:text-white">
                                {patient.first_name} {patient.last_name}
                              </p>
                            </div>
                          </Link>
                        </td>
                        <td className="px-4 py-4 text-neutral-700 dark:text-neutral-300">
                          {patient.gender === "M" ? "Male" : patient.gender === "F" ? "Female" : patient.gender}
                        </td>
                        <td className="px-4 py-4 text-neutral-700 dark:text-neutral-300">
                          {patient.birthdate ? calculateAge(patient.birthdate) : "—"}
                        </td>
                        <td className="px-4 py-4 text-neutral-700 dark:text-neutral-300">
                          {patient.city && patient.state ? `${patient.city}, ${patient.state}` : "—"}
                        </td>
                        <td className="px-4 py-4 font-mono text-xs text-neutral-500 dark:text-neutral-400">
                          {patient.patient_id.slice(0, 8)}...
                        </td>
                        <td className="px-4 py-4 text-right">
                          <Link
                            href={`/patients/${patient.patient_id}`}
                            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

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
          </CardContent>
        </Card>
      </div>
  );
}