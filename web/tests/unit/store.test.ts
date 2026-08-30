import { describe, it, expect, beforeEach } from "vitest";
import { usePatientStore } from "@/lib/store/patient";

describe("usePatientStore", () => {
  beforeEach(() => {
    usePatientStore.getState().clearActivePatient();
  });

  it("has initial state", () => {
    const state = usePatientStore.getState();
    expect(state.activePatientId).toBeNull();
    expect(state.activePatient).toBeNull();
  });

  it("sets active patient", () => {
    const patient = {
      patient_id: "p1",
      first_name: "John",
      last_name: "Doe",
      gender: "M",
      birthdate: "1990-01-01",
    };
    usePatientStore.getState().setActivePatient(patient);
    const state = usePatientStore.getState();
    expect(state.activePatientId).toBe("p1");
    expect(state.activePatient).toEqual(patient);
  });

  it("clears active patient", () => {
    usePatientStore.getState().setActivePatient({
      patient_id: "p1",
      first_name: "John",
      last_name: "Doe",
      gender: "M",
      birthdate: "1990-01-01",
    });
    usePatientStore.getState().clearActivePatient();
    const state = usePatientStore.getState();
    expect(state.activePatientId).toBeNull();
    expect(state.activePatient).toBeNull();
  });

  it("updates patient when setting a new one", () => {
    usePatientStore.getState().setActivePatient({
      patient_id: "p1",
      first_name: "John",
      last_name: "Doe",
      gender: "M",
      birthdate: "1990-01-01",
    });
    usePatientStore.getState().setActivePatient({
      patient_id: "p2",
      first_name: "Jane",
      last_name: "Doe",
      gender: "F",
      birthdate: "1992-01-01",
    });
    const state = usePatientStore.getState();
    expect(state.activePatientId).toBe("p2");
    expect(state.activePatient?.first_name).toBe("Jane");
  });
});
