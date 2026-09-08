import { lazy, Suspense, useEffect, useState } from "react";
import {
  Bell,
  Box,
  FlaskConical,
  HeartPulse,
  History,
  Home,
  LogIn,
  ScanSearch,
  Settings,
  UserPlus,
  Wrench,
} from "lucide-react";
import { connectTwin, getTwin } from "./services/twinApi";
import { useTwinStore } from "./store/twinStore";
import { useAuthStore } from "./store/authStore";
import type { ViewName } from "./types/twin";
import ErrorBoundary from "./components/ErrorBoundary";
import AuthScreen from "./components/AuthScreen";
import { isHostedDemo } from "./demo/demoRuntime";
import "./styles/reference.css";
import "./styles/functional.css";
import "./styles/interactions.css";
import "./styles/design-v4.css";

const CommandCenter = lazy(() => import("./components/CommandCenter")),
  DigitalTwinDeck = lazy(() => import("./components/DigitalTwinDeck")),
  HealthFaultsDeck = lazy(() => import("./components/HealthFaultsDeck")),
  MissionDeck = lazy(() => import("./components/MissionDeck")),
  ReplayDeck = lazy(() => import("./components/ReplayDeck")),
  DiagnosticsDeck = lazy(() => import("./components/DiagnosticsDeck")),
  MaintenanceDeck = lazy(() => import("./components/MaintenanceDeck")),
  SettingsDeck = lazy(() => import("./components/SettingsDeck"));
const nav: Array<[ViewName, string, any]> = [
  ["command", "Command Center", Home],
  ["digitalTwin", "Digital Twin", Box],
  ["healthFaults", "Health & Faults", HeartPulse],
  ["mission", "Mission Lab", FlaskConical],
  ["replay", "Replay", History],
  ["diagnostics", "Diagnostics", ScanSearch],
  ["maintenance", "Maintenance", Wrench],
  ["settings", "Settings", Settings],
];

export default function App() {
  const demo = isHostedDemo();
  const view = useTwinStore((s) => s.view),
    setView = useTwinStore((s) => s.setView),
    twin = useTwinStore((s) => s.twin),
    online = useTwinStore((s) => s.online),
    runtime = useTwinStore((s) => s.runtimeValidity),
    setTwin = useTwinStore((s) => s.setTwin),
    setOnline = useTwinStore((s) => s.setOnline),
    setRuntime = useTwinStore((s) => s.setRuntimeValidity),
    runs = useTwinStore((s) => s.missionRuns),
    user = useAuthStore((s) => s.user),
    [clock, setClock] = useState(new Date()),
    [authDialog, setAuthDialog] = useState<"signin" | "signup" | null>(null);
  useEffect(() => {
    getTwin()
      .then(setTwin)
      .catch(() => undefined);
    return connectTwin(setTwin, setOnline, setRuntime);
  }, [setTwin, setOnline, setRuntime]);
  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  const openSettings = (tab = "system") => {
      sessionStorage.setItem("twinguard-settings-tab", tab);
      setView("settings");
    },
    decisionEligible = online && runtime?.decision_eligible !== false,
    last = runs.length ? runs[runs.length - 1].result : undefined,
    mission = last?.mission_type ? String(last.mission_type).replace(/_/g, " ") : "Awaiting mission",
    engineId = twin?.engine_id ?? "ENGINE-01";
  const screen =
    view === "command" ? (
      <CommandCenter />
    ) : view === "digitalTwin" ? (
      <DigitalTwinDeck />
    ) : view === "healthFaults" ? (
      <HealthFaultsDeck />
    ) : view === "mission" ? (
      <MissionDeck />
    ) : view === "replay" ? (
      <ReplayDeck />
    ) : view === "diagnostics" ? (
      <DiagnosticsDeck />
    ) : view === "maintenance" ? (
      <MaintenanceDeck />
    ) : (
      <SettingsDeck />
    );
  return (
    <div className="tg-shell">
      <aside className="tg-sidebar">
        <div className="tg-brand">
          <img src="/assets/twinguard-mark.svg" alt="TwinGuard AI logo" />
          <div>
            <strong>TwinGuard AI</strong>
            <small>AEROSPACE DIGITAL TWIN</small>
          </div>
        </div>
        <div className="tg-nav-label">OPERATIONS</div>
        <nav>
          {nav.slice(0, 5).map(([id, label, Icon]) => (
            <button
              key={id}
              className={view === id ? "active" : ""}
              onClick={() => setView(id)}
              title={label}
            >
              <Icon size={19} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="tg-nav-label">ENGINEERING</div>
        <nav>
          {nav.slice(5).map(([id, label, Icon]) => (
            <button
              key={id}
              className={view === id ? "active" : ""}
              onClick={() => (id === "settings" ? openSettings() : setView(id))}
              title={label}
            >
              <Icon size={19} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="tg-sidebar-foot">
          <span className={decisionEligible ? "online" : "hold"}>
            <i /> {decisionEligible ? "ALL SYSTEMS LIVE" : "DATA HOLD"}
          </span>
          <small>TwinGuard v4.0 · SIH Prototype</small>
        </div>
      </aside>
      <main className="tg-main">
        <header className="tg-topbar">
          <div className="tg-engine-id">
            <i />
            <b>{engineId}</b>
            <span className={decisionEligible ? "online" : "hold"}>
              {decisionEligible ? "Online" : "Data hold"}
            </span>
          </div>
          <span className={`tg-runtime-badge ${demo ? "demo" : "live"}`}>
            {demo ? "HOSTED DEMO" : "LIVE BACKEND"}
          </span>
          <div className="tg-top-mission">
            <span>ACTIVE MISSION</span>
            <b>{mission}</b>
          </div>
          <div className="tg-clock">
            {clock.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
              timeZone: "UTC",
            })}{" "}
            UTC
          </div>
          <div className="tg-top-spacer" />
          <button
            className="tg-bell"
            onClick={() => setView("diagnostics")}
            title="Open diagnostics"
            aria-label="Open diagnostics"
          >
            <Bell size={19} />
            {(twin?.ai.anomaly || !decisionEligible) && <i />}
          </button>
          {user ? (
            <button className="tg-user" onClick={() => openSettings("user")} title="Open account settings">
              <div className="avatar">
                {user.name
                  .split(" ")
                  .map((x) => x[0])
                  .slice(0, 2)
                  .join("")}
              </div>
              <span>
                <small>OPERATOR</small>
                <strong>{user.name}</strong>
              </span>
            </button>
          ) : (
            <div className="tg-auth-actions">
              <button onClick={() => setAuthDialog("signin")}>
                <LogIn />
                Sign in
              </button>
              <button className="primary" onClick={() => setAuthDialog("signup")}>
                <UserPlus />
                Create account
              </button>
            </div>
          )}
        </header>
        <section className="tg-content">
          <ErrorBoundary name="TwinGuard page">
            <Suspense fallback={<div className="tg-loading">Loading TwinGuard…</div>}>{screen}</Suspense>
          </ErrorBoundary>
        </section>
      </main>
      {authDialog && (
        <div className="auth-modal" role="dialog" aria-modal="true" aria-label="TwinGuard account">
          <div className="auth-modal-backdrop" onClick={() => setAuthDialog(null)} />
          <AuthScreen initialMode={authDialog} onClose={() => setAuthDialog(null)} />
        </div>
      )}
    </div>
  );
}
