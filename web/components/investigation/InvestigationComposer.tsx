"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import {
  Search,
  Play,
  Loader2,
  Brain,
  Stethoscope,
  Pill,
  AlertTriangle,
  Clock,
  Zap,
} from "lucide-react";

interface InvestigationComposerProps {
  patients: Array<{ patient_id: string; first_name: string; last_name: string }>;
  onSubmit: (request: InvestigationRequest) => void;
  isLoading?: boolean;
}

interface InvestigationRequest {
  patient_id: string;
  question: string;
  agents: string[];
  enable_debate: boolean;
  evaluate: boolean;
}

const AVAILABLE_AGENTS = [
  {
    id: "diagnostic",
    name: "Diagnostic",
    description: "Diagnostic reasoning and differential diagnosis",
    icon: Stethoscope,
    color: "text-blue-600",
    bg: "bg-blue-100 dark:bg-blue-900/30",
  },
  {
    id: "treatment",
    name: "Treatment",
    description: "Treatment analysis and medication review",
    icon: Pill,
    color: "text-green-600",
    bg: "bg-green-100 dark:bg-green-900/30",
  },
  {
    id: "risk_assessment",
    name: "Risk Assessment",
    description: "Risk stratification and outcome prediction",
    icon: AlertTriangle,
    color: "text-red-600",
    bg: "bg-red-100 dark:bg-red-900/30",
  },
  {
    id: "timeline",
    name: "Timeline",
    description: "Temporal pattern analysis",
    icon: Clock,
    color: "text-purple-600",
    bg: "bg-purple-100 dark:bg-purple-900/30",
  },
];

const EXAMPLE_QUESTIONS = [
  "What are the main health conditions for this patient?",
  "Analyze the medication history and identify any drug interactions.",
  "What is the patient's health trajectory over the past year?",
  "Identify risk factors and predict potential complications.",
  "Summarize the patient's clinical journey and key milestones.",
];

export function InvestigationComposer({
  patients,
  onSubmit,
  isLoading = false,
}: InvestigationComposerProps) {
  const [selectedPatient, setSelectedPatient] = useState("");
  const [question, setQuestion] = useState("");
  const [selectedAgents, setSelectedAgents] = useState<string[]>(["diagnostic"]);
  const [enableDebate, setEnableDebate] = useState(true);
  const [enableEvaluation, setEnableEvaluation] = useState(true);
  const [showPatientSearch, setShowPatientSearch] = useState(false);
  const [patientSearch, setPatientSearch] = useState("");

  const filteredPatients = patients.filter(
    (p) =>
      p.first_name.toLowerCase().includes(patientSearch.toLowerCase()) ||
      p.last_name.toLowerCase().includes(patientSearch.toLowerCase()) ||
      p.patient_id.toLowerCase().includes(patientSearch.toLowerCase())
  );

  const selectedPatientData = patients.find((p) => p.patient_id === selectedPatient);

  const toggleAgent = (agentId: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agentId) ? prev.filter((id) => id !== agentId) : [...prev, agentId]
    );
  };

  const handleSubmit = () => {
    if (!selectedPatient || !question.trim()) return;

    onSubmit({
      patient_id: selectedPatient,
      question: question.trim(),
      agents: selectedAgents,
      enable_debate: enableDebate,
      evaluate: enableEvaluation,
    });
  };

  const isValid = selectedPatient && question.trim() && selectedAgents.length > 0;

  return (
    <Card className="border-2 border-neutral-200 dark:border-neutral-800">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-blue-600" />
          New Investigation
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Patient Selector */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            Patient
          </label>
          <div className="relative">
            <Button
              variant="outline"
              className="w-full justify-start text-left font-normal"
              onClick={() => setShowPatientSearch(!showPatientSearch)}
            >
              {selectedPatientData ? (
                <span>
                  {selectedPatientData.first_name} {selectedPatientData.last_name}
                  <span className="ml-2 text-neutral-500">
                    ({selectedPatientData.patient_id.slice(0, 8)}...)
                  </span>
                </span>
              ) : (
                <span className="text-neutral-500">Select a patient...</span>
              )}
            </Button>

            {showPatientSearch && (
              <div className="absolute z-10 w-full mt-1 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg shadow-lg">
                <div className="p-2 border-b border-neutral-200 dark:border-neutral-800">
                  <Input
                    placeholder="Search patients..."
                    value={patientSearch}
                    onChange={(e) => setPatientSearch(e.target.value)}
                    className="h-8"
                    autoFocus
                  />
                </div>
                <div className="max-h-60 overflow-y-auto">
                  {filteredPatients.length === 0 ? (
                    <div className="p-4 text-center text-neutral-500">No patients found</div>
                  ) : (
                    filteredPatients.map((patient) => (
                      <button
                        key={patient.patient_id}
                        className={cn(
                          "w-full px-4 py-2 text-left hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors",
                          selectedPatient === patient.patient_id &&
                            "bg-blue-50 dark:bg-blue-900/20"
                        )}
                        onClick={() => {
                          setSelectedPatient(patient.patient_id);
                          setShowPatientSearch(false);
                          setPatientSearch("");
                        }}
                      >
                        <div className="font-medium text-neutral-900 dark:text-white">
                          {patient.first_name} {patient.last_name}
                        </div>
                        <div className="text-xs text-neutral-500">
                          {patient.patient_id.slice(0, 16)}...
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Question Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            Investigation Question
          </label>
          <textarea
            className="w-full min-h-[100px] px-3 py-2 text-sm border border-neutral-200 dark:border-neutral-800 rounded-lg bg-white dark:bg-neutral-950 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="What would you like to investigate about this patient?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_QUESTIONS.map((example, i) => (
              <button
                key={i}
                className="text-xs px-2 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                onClick={() => setQuestion(example)}
              >
                {example.slice(0, 40)}...
              </button>
            ))}
          </div>
        </div>

        {/* Agent Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            Agents
          </label>
          <div className="grid grid-cols-2 gap-3">
            {AVAILABLE_AGENTS.map((agent) => {
              const isSelected = selectedAgents.includes(agent.id);
              return (
                <button
                  key={agent.id}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg border-2 transition-all text-left",
                    isSelected
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700"
                  )}
                  onClick={() => toggleAgent(agent.id)}
                >
                  <div className={cn("p-2 rounded-lg", agent.bg, agent.color)}>
                    <agent.icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-neutral-900 dark:text-white text-sm">
                      {agent.name}
                    </div>
                    <div className="text-xs text-neutral-500 mt-0.5">{agent.description}</div>
                  </div>
                  {isSelected && (
                    <Badge variant="default" className="ml-auto">
                      Selected
                    </Badge>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Options */}
        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enableDebate}
              onChange={(e) => setEnableDebate(e.target.checked)}
              className="h-4 w-4 rounded border-neutral-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-neutral-700 dark:text-neutral-300">
              Enable Multi-Agent Debate
            </span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enableEvaluation}
              onChange={(e) => setEnableEvaluation(e.target.checked)}
              className="h-4 w-4 rounded border-neutral-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-neutral-700 dark:text-neutral-300">
              Run Evaluation
            </span>
          </label>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-between pt-4 border-t border-neutral-200 dark:border-neutral-800">
          <div className="text-sm text-neutral-500">
            {selectedAgents.length} agent{selectedAgents.length !== 1 ? "s" : ""} selected
            {enableDebate && " • Debate enabled"}
            {enableEvaluation && " • Evaluation enabled"}
          </div>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isLoading}
            className="gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Running Investigation...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                Run Investigation
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
