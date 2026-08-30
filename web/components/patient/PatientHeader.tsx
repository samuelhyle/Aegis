"use client";

import { cn } from "@/lib/utils";
import { formatDate, calculateAge, getInitials } from "@/lib/utils";
import { Avatar, AvatarWithFallback } from "@/components/ui/Avatar";
import { StateBadge } from "./Badges";
import { Badge } from "@/components/ui/Badge";
import type { Patient, PatientDetails } from "@/types";

interface PatientHeaderProps {
  patient: Patient | PatientDetails;
  className?: string;
  onAction?: () => void;
  actionLabel?: string;
}

export function PatientHeader({ patient, className, onAction, actionLabel }: PatientHeaderProps) {
  const age = patient.birthdate ? calculateAge(patient.birthdate) : null;
  const fullName = `${patient.first_name} ${patient.last_name}`.trim();
  const currentState = "current_state" in patient ? (patient as any).current_state : undefined;

  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-center gap-4 p-4", className)}>
      <AvatarWithFallback
        firstName={patient.first_name}
        lastName={patient.last_name}
        size="xl"
        className="shrink-0 bg-neutral-100 dark:bg-neutral-800"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white truncate">{fullName}</h2>
          {patient.patient_id && (
            <Badge variant="outline" className="font-mono text-xs">
              {patient.patient_id.slice(0, 8)}...
            </Badge>
          )}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-4 text-sm text-neutral-500 dark:text-neutral-400">
          {patient.gender && <span>{patient.gender}</span>}
          {age !== null && <span>Age {age}</span>}
          {patient.birthdate && <span>Born {formatDate(patient.birthdate)}</span>}
          {patient.city && patient.state && <span>{patient.city}, {patient.state}</span>}
        </div>
        {currentState && (
          <div className="mt-3">
            <StateBadge state={currentState} size="md" />
          </div>
        )}
      </div>
      {onAction && actionLabel && (
        <div className="shrink-0 sm:ml-auto">
          <button
            onClick={onAction}
            className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
          >
            {actionLabel}
          </button>
        </div>
      )}
    </div>
  );
}

interface PatientCardProps {
  patient: Patient;
  selected?: boolean;
  onClick?: () => void;
  className?: string;
}

export function PatientCard({ patient, selected, onClick, className }: PatientCardProps) {
  const age = patient.birthdate ? calculateAge(patient.birthdate) : null;
  const fullName = `${patient.first_name} ${patient.last_name}`.trim();

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-4 rounded-lg border transition-all",
        selected
          ? "bg-primary-50 border-primary-200 dark:bg-primary-900/20 dark:border-primary-800"
          : "bg-white border-neutral-200 hover:bg-neutral-50 dark:bg-neutral-900 dark:border-neutral-800 dark:hover:bg-neutral-800",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <AvatarWithFallback firstName={patient.first_name} lastName={patient.last_name} size="md" />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-neutral-900 dark:text-white truncate">{fullName}</p>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 truncate">
            {patient.gender} • {age !== null ? `${age} yrs` : patient.birthdate ? formatDate(patient.birthdate) : "Unknown age"}
          </p>
          {patient.city && patient.state && (
            <p className="text-xs text-neutral-400 dark:text-neutral-500 truncate">
              {patient.city}, {patient.state}
            </p>
          )}
        </div>
        {selected && <div className="text-primary-600">✓</div>}
      </div>
    </button>
  );
}