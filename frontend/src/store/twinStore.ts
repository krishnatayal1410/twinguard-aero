import { create } from "zustand";
import type {
  MissionResult,
  ReplayMission,
  RuntimeValidity,
  TelemetryState,
  TwinState,
  ViewName,
} from "../types/twin";

interface Store {
  twin?: TwinState;
  online: boolean;
  runtimeValidity?: RuntimeValidity;
  view: ViewName;
  focus: string;
  history: Record<HistoryKey, number[]>;
  missionRuns: Array<{ fault: string; result: MissionResult }>;
  missions: ReplayMission[];
  setTwin: (x: TwinState) => void;
  setOnline: (x: boolean) => void;
  setRuntimeValidity: (x: RuntimeValidity) => void;
  setView: (x: ViewName) => void;
  setFocus: (x: string) => void;
  addMission: (fault: string, r: MissionResult) => void;
  setMissions: (m: ReplayMission[]) => void;
}

type HistoryKey =
  "rpm" | "cht" | "egt" | "oil_pressure" | "oil_temperature" | "vibration" | "altitude" | "battery_voltage";
const keys: HistoryKey[] = [
  "rpm",
  "cht",
  "egt",
  "oil_pressure",
  "oil_temperature",
  "vibration",
  "altitude",
  "battery_voltage",
];
const readTelemetry = (x: TelemetryState, key: HistoryKey) => Number(x[key]);
const emptyHistory = (): Record<HistoryKey, number[]> => ({
  rpm: [],
  cht: [],
  egt: [],
  oil_pressure: [],
  oil_temperature: [],
  vibration: [],
  altitude: [],
  battery_voltage: [],
});

export const useTwinStore = create<Store>((set) => ({
  online: false,
  view: "command",
  focus: "all",
  history: emptyHistory(),
  missionRuns: [],
  missions: [],
  setTwin: (x) =>
    set((s) => {
      const h = { ...s.history };
      for (const k of keys) h[k] = [...(h[k] ?? []), readTelemetry(x.telemetry, k)].slice(-90);
      return { twin: x, history: h, runtimeValidity: x.runtime_validity ?? s.runtimeValidity };
    }),
  setOnline: (online) => set({ online }),
  setRuntimeValidity: (runtimeValidity) => set({ runtimeValidity }),
  setView: (view) => set({ view }),
  setFocus: (focus) => set({ focus }),
  addMission: (fault, result) =>
    set((s) => ({ missionRuns: [...s.missionRuns, { fault, result }].slice(-8) })),
  setMissions: (missions) => set({ missions }),
}));
