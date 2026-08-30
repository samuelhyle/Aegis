"use client";

import { useParams } from "next/navigation";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { usePatient, usePatientConditions, usePatientMedications, usePatientObservations, usePatientEncounters, usePatientJourney, useRiskAssessment, useDrugInteractions, useClinicalTrials, usePatientTimeline, useTemporalAnalysis } from "@/lib/hooks/useQueries";
import { PatientHeader } from "@/components/patient/PatientHeader";
import {
  HeartPulse,
  Calendar,
  Activity,
  Pill,
  TrendingUp,
  AlertTriangle,
  Brain,
  FlaskConical,
  FileText,
  Microscope,
} from "lucide-react";
import { TabPanels } from "./TabPanels";

const tabs = [
  { value: "overview", label: "Overview", icon: HeartPulse },
  { value: "timeline", label: "Timeline", icon: Calendar },
  { value: "conditions", label: "Conditions", icon: Activity },
  { value: "medications", label: "Medications", icon: Pill },
  { value: "labs", label: "Labs & Vitals", icon: TrendingUp },
  { value: "risk", label: "Risk", icon: AlertTriangle },
  { value: "graph-rag", label: "Graph RAG", icon: Brain },
  { value: "investigations", label: "Investigations", icon: FileText },
  { value: "trials", label: "Clinical Trials", icon: FlaskConical },
  { value: "interactions", label: "Drug Interactions", icon: Microscope },
];

export default function PatientDetailPage() {
  const params = useParams();
  const patientId = params.id as string;

  const { data: patient, isLoading: patientLoading } = usePatient(patientId);
  const { data: conditions } = usePatientConditions(patientId);
  const { data: medications } = usePatientMedications(patientId);
  const { data: observations } = usePatientObservations(patientId);
  const { data: encounters } = usePatientEncounters(patientId);
  const { data: journey } = usePatientJourney(patientId);
  const { data: riskAssessment } = useRiskAssessment(patientId);
  const { data: drugInteractions } = useDrugInteractions(patientId);
  const { data: clinicalTrials } = useClinicalTrials(patientId);
  const { data: timeline } = usePatientTimeline(patientId);
  const { data: temporalAnalysis } = useTemporalAnalysis(patientId);

  if (patientLoading) {
    return (
      <div className="space-y-6 animate-pulse">
          <div className="h-32 bg-neutral-200 dark:bg-neutral-800 rounded-xl" />
          <div className="grid gap-4 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => <div key={i} className="h-40 bg-neutral-200 dark:bg-neutral-800 rounded-xl" />)}
        </div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">Patient not found</h1>
        </div>
    );
  }

  return (
    <>
      <PatientHeader patient={patient} />

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="flex w-full overflow-x-auto scrollbar-hide lg:grid lg:grid-cols-10">
          {tabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className="whitespace-nowrap shrink-0">
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabPanels
          patient={patient}
          conditions={conditions?.conditions || []}
          medications={medications?.medications || []}
          observations={observations?.observations || []}
          journey={journey || null}
          riskAssessment={riskAssessment?.risks || []}
          drugInteractions={drugInteractions}
          clinicalTrials={clinicalTrials?.matches || []}
          timeline={timeline?.events || []}
          temporalAnalysis={temporalAnalysis}
        />
      </Tabs>
    </>
  );
}