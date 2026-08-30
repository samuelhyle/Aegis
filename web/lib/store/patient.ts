"use client";

import { create } from "zustand";
import type { Patient } from "@/types";

interface PatientState {
  activePatientId: string | null;
  activePatient: Patient | null;
  setActivePatient: (patient: Patient | null) => void;
  clearActivePatient: () => void;
}

export const usePatientStore = create<PatientState>((set) => ({
  activePatientId: null,
  activePatient: null,
  setActivePatient: (patient) =>
    set({
      activePatientId: patient?.patient_id ?? null,
      activePatient: patient,
    }),
  clearActivePatient: () =>
    set({
      activePatientId: null,
      activePatient: null,
    }),
}));
