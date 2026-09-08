import {
  Database,
  Download,
  Info,
  LogOut,
  RefreshCcw,
  Server,
  ShieldCheck,
  SlidersHorizontal,
  Trash2,
  UserRound,
} from "lucide-react";
import { useEffect, useState } from "react";
import { getSystemStatus, resetFault, setFault } from "../services/twinApi";
import { signOut } from "../services/authApi";
import { useTwinStore } from "../store/twinStore";
import { useAuthStore } from "../store/authStore";
import type { FaultName, SystemStatus } from "../types/twin";
import { fmt, pretty } from "./ui";
import { EngineeringReadout, PageHeader, Panel, PanelTitle, StatusPill } from "./ReferenceUI";
import { isHostedDemo } from "../demo/demoRuntime";

type Tab = "system" | "connections" | "simulator" | "model" | "data" | "user";
export default function SettingsDeck() {
  const demo = isHostedDemo();
  const twin = useTwinStore((s) => s.twin),
    runtime = useTwinStore((s) => s.runtimeValidity),
    user = useAuthStore((s) => s.user),
    token = useAuthStore((s) => s.token),
    clearAuth = useAuthStore((s) => s.clear),
    [tab, setTab] = useState<Tab>(
      () => (sessionStorage.getItem("twinguard-settings-tab") as Tab | null) ?? "system",
    ),
    [status, setStatus] = useState<SystemStatus>(),
    [scenario, setScenario] = useState<FaultName>("normal"),
    [severity, setSeverity] = useState(60),
    [autoReset, setAutoReset] = useState(false),
    [autoResetSeconds, setAutoResetSeconds] = useState(30),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const load = async () => {
    setBusy(true);
    setNotice("");
    try {
      const s = await getSystemStatus();
      setStatus(s);
      setNotice("System status refreshed successfully.");
    } catch (e: any) {
      setStatus(undefined);
      setNotice(e?.message ?? "Unable to reach backend.");
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    getSystemStatus()
      .then(setStatus)
      .catch(() => setStatus(undefined));
  }, []);
  const applyScenario = async () => {
    setBusy(true);
    setNotice("");
    try {
      if (scenario === "normal") await resetFault();
      else await setFault(scenario, severity / 100);
      setNotice(`${pretty(scenario)} applied at ${severity}% intensity.`);
      if (autoReset && scenario !== "normal")
        window.setTimeout(() => resetFault().catch(() => undefined), autoResetSeconds * 1000);
    } catch (e: any) {
      setNotice(e?.response?.data?.detail ?? e?.message ?? "Simulator action failed");
    } finally {
      setBusy(false);
    }
  };
  const exportData = (type: "csv" | "json") => {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const data = twin ?? {};
    const text =
      type === "json"
        ? JSON.stringify(data, null, 2)
        : ["parameter,value", ...Object.entries(twin?.telemetry ?? {}).map(([k, v]) => `${k},${v}`)].join(
            "\n",
          );
    const blob = new Blob([text], { type: type === "json" ? "application/json" : "text/csv" }),
      url = URL.createObjectURL(blob),
      a = document.createElement("a");
    a.href = url;
    a.download = `twinguard-${stamp}.${type}`;
    a.click();
    URL.revokeObjectURL(url);
    setNotice(`${type.toUpperCase()} export created.`);
  };
  const clearLocal = async () => {
    if (!confirm("Clear TwinGuard browser cache/preferences? Your signed-in session will be kept.")) return;
    const keep = "twinguard_session";
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const k = localStorage.key(i);
      if (k && k !== keep && k.toLowerCase().includes("twinguard")) localStorage.removeItem(k);
    }
    await resetFault().catch(() => undefined);
    setNotice("Local TwinGuard cache cleared and simulator reset.");
  };
  const logout = async () => {
    setBusy(true);
    try {
      await signOut(token);
      clearAuth();
      location.reload();
    } finally {
      setBusy(false);
    }
  };
  const dataQuality = Number(runtime?.data_quality ?? twin?.confidence.data_quality ?? 0),
    age = runtime?.telemetry_age_seconds;
  return (
    <div className="ref-page settings-ref-page">
      <PageHeader
        title="Settings & System"
        subtitle="Functional system controls, simulator actions, runtime visibility, exports and account management"
      />
      <div className="ref-tabs settings-tabs">
        {[
          ["system", "System"],
          ["connections", "Connections"],
          ["simulator", "Simulator"],
          ["model", "Model Configuration"],
          ["data", "Data Management"],
          ["user", "User"],
        ].map(([id, label]) => (
          <button
            key={id}
            className={tab === id ? "active" : ""}
            onClick={() => {
              setTab(id as Tab);
              setNotice("");
            }}
          >
            {label}
          </button>
        ))}
      </div>
      {notice && <div className="settings-notice">{notice}</div>}
      {tab === "system" && (
        <>
          <div className="system-status-cards">
            {[
              [
                "Backend",
                status?.service ? "Connected" : "Unavailable",
                Server,
                status?.service ? "green" : "red",
              ],
              ["Simulator", twin ? "Streaming" : "Waiting", RefreshCcw, twin ? "green" : "orange"],
              ["Database", status?.database ?? "Unknown", Database, "green"],
              ["Model Runtime", pretty(twin?.ai.model_state ?? "Unknown"), SlidersHorizontal, "blue"],
              [
                "Data Quality",
                `${fmt(dataQuality, 1)}%`,
                ShieldCheck,
                dataQuality >= 70 ? "green" : "orange",
              ],
              ["System Version", status?.version ?? "--", Info, "blue"],
              ["Environment", pretty(status?.environment ?? "Unknown"), UserRound, "orange"],
            ].map(([k, v, Icon, tone]: any) => (
              <div className="system-status-card" key={k}>
                <Icon />
                <span>{k}</span>
                <b className={`${tone}-text`}>● {v}</b>
              </div>
            ))}
          </div>
          <Panel>
            <PanelTitle
              title="Live Runtime Snapshot"
              right={
                <button className="ref-outline compact-action" onClick={load} disabled={busy}>
                  <RefreshCcw size={14} />
                  {busy ? "Refreshing…" : "Refresh"}
                </button>
              }
            />
            <div className="engineering-grid">
              <EngineeringReadout
                label="Telemetry Age"
                value={age == null ? "--" : fmt(age, 2)}
                unit={age == null ? undefined : "s"}
              />
              <EngineeringReadout
                label="Freshness Limit"
                value={fmt(runtime?.freshness_limit_seconds ?? status?.telemetry.freshness_limit_seconds, 2)}
                unit="s"
              />
              <EngineeringReadout label="Data Quality" value={fmt(dataQuality, 2)} unit="%" />
              <EngineeringReadout
                label="Minimum Quality"
                value={fmt(runtime?.minimum_data_quality ?? status?.telemetry.minimum_data_quality, 1)}
                unit="%"
              />
              <EngineeringReadout
                label="Decision Eligible"
                value={runtime?.decision_eligible !== false ? "YES" : "NO"}
              />
              <EngineeringReadout label="RUL" value={fmt(twin?.ai.rul_hours, 2)} unit="h" />
            </div>
          </Panel>
        </>
      )}
      {tab === "connections" && (
        <div className="settings-columns settings-single">
          <Panel>
            <PanelTitle
              title="Connection Settings"
              subtitle={
                demo
                  ? "This deployment uses the browser-hosted deterministic demonstration runtime."
                  : "Actual local endpoints used by the TwinGuard development stack."
              }
            />
            <label>
              API URL
              <input value={demo ? "Browser-hosted demo runtime" : "http://localhost:8000/api/v1"} readOnly />
            </label>
            <label>
              WebSocket URL
              <input
                value={demo ? "Browser simulation loop" : "ws://localhost:8000/api/v1/ws/twin/ENGINE-01"}
                readOnly
              />
            </label>
            <div className={status?.service ? "connection-ok" : "connection-bad"}>
              <b>● {demo ? "Hosted demo active" : status?.service ? "Connected" : "Not verified"}</b>
              <p>
                {demo
                  ? "Synthetic telemetry and controls run locally in this browser."
                  : status?.service
                    ? `Backend ${status.service} ${status.version} is reachable.`
                    : "Press Test Connection to query /system/status."}
              </p>
            </div>
            <button className="ref-primary" onClick={load} disabled={busy}>
              <Server size={15} />
              {busy ? "Testing…" : demo ? "Refresh Demo Runtime" : "Test Connection"}
            </button>
          </Panel>
          <Panel>
            <PanelTitle title="Integration Status" />
            <div className="model-detail-grid">
              <div>
                <span>MQTT</span>
                <b>{status?.integrations.mqtt ? "Enabled" : "Disabled"}</b>
              </div>
              <div>
                <span>CAN / SocketCAN</span>
                <b>{status?.integrations.can ? "Enabled" : "Disabled"}</b>
              </div>
              <div>
                <span>Unreal UDP</span>
                <b>{status?.integrations.unreal_udp ? "Enabled" : "Disabled"}</b>
              </div>
              <div>
                <span>Authentication</span>
                <b>{status?.security.authentication !== false ? "Enabled" : "Disabled"}</b>
              </div>
              <div>
                <span>Ingest key</span>
                <b>{status?.security.ingest_key_required ? "Required" : "Not required"}</b>
              </div>
            </div>
          </Panel>
        </div>
      )}
      {tab === "simulator" && (
        <div className="settings-columns settings-single">
          <Panel>
            <PanelTitle
              title="Simulator Controls"
              subtitle={
                demo
                  ? "These controls drive the browser-hosted deterministic fault simulator."
                  : "These controls call the backend fault-injection endpoints."
              }
            />
            <label>
              Scenario
              <select value={scenario} onChange={(e) => setScenario(e.target.value as FaultName)}>
                <option value="normal">Healthy</option>
                <option value="lubrication">Lubrication Degradation</option>
                <option value="overheating">Overheating</option>
                <option value="cooling_degradation">Cooling Degradation</option>
                <option value="vibration">Abnormal Vibration</option>
                <option value="sensor_drift">Sensor Drift</option>
                <option value="injector">Injector Abnormality</option>
                <option value="misfire">Misfire</option>
                <option value="combustion_instability">Combustion Instability</option>
                <option value="alternator_degradation">Alternator Degradation</option>
              </select>
            </label>
            <label>
              Fault Intensity <b>{severity}%</b>
              <input
                type="range"
                min="0"
                max="100"
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
              />
            </label>
            <div className="switch-row">
              <span>Auto Reset</span>
              <button
                className={`fake-switch ${autoReset ? "active" : ""}`}
                onClick={() => setAutoReset((v) => !v)}
                aria-pressed={autoReset}
              >
                <i />
              </button>
            </div>
            {autoReset && (
              <label>
                Reset After
                <input
                  type="number"
                  min={5}
                  max={300}
                  value={autoResetSeconds}
                  onChange={(e) => setAutoResetSeconds(Number(e.target.value))}
                />
                <span className="input-unit">s</span>
              </label>
            )}
            <div className="simulator-action-row">
              <button className="ref-primary" onClick={applyScenario} disabled={busy}>
                <RefreshCcw size={15} />
                {busy ? "Applying…" : "Apply Scenario"}
              </button>
              <button
                className="ref-outline"
                onClick={async () => {
                  setBusy(true);
                  try {
                    await resetFault();
                    setScenario("normal");
                    setSeverity(0);
                    setNotice("Simulator reset to healthy state.");
                  } finally {
                    setBusy(false);
                  }
                }}
                disabled={busy}
              >
                Reset Healthy
              </button>
            </div>
          </Panel>
          <Panel>
            <PanelTitle title="Current Exact Engine State" />
            <div className="engineering-grid">
              <EngineeringReadout label="RPM" value={fmt(twin?.telemetry.rpm, 0)} unit="rpm" />
              <EngineeringReadout label="Throttle" value={fmt(twin?.telemetry.throttle, 1)} unit="%" />
              <EngineeringReadout label="CHT" value={fmt(twin?.telemetry.cht, 1)} unit="°C" />
              <EngineeringReadout
                label="Oil Pressure"
                value={fmt(Number(twin?.telemetry.oil_pressure ?? 0) * 100, 1)}
                unit="kPa"
              />
              <EngineeringReadout
                label="Oil Temperature"
                value={fmt(twin?.telemetry.oil_temperature, 1)}
                unit="°C"
              />
              <EngineeringReadout label="Vibration" value={fmt(twin?.telemetry.vibration, 3)} unit="g" />
            </div>
          </Panel>
        </div>
      )}
      {tab === "model" && (
        <div className="settings-columns settings-single">
          <Panel>
            <PanelTitle
              title="Active Model Configuration"
              subtitle="Runtime model selection is established when the backend starts; this screen reports the real active state instead of showing fake switches."
            />
            <div className="model-detail-grid">
              <div>
                <span>Model mode</span>
                <b>{pretty(twin?.ai.model_state ?? "Unknown")}</b>
              </div>
              <div>
                <span>Feature contract</span>
                <b>{pretty(twin?.ai.feature_contract ?? "--")}</b>
              </div>
              <div>
                <span>Validation scope</span>
                <b>{pretty(twin?.ai.validation_scope ?? "Engineering demonstrator")}</b>
              </div>
              <div>
                <span>RUL basis</span>
                <b>{pretty(twin?.ai.rul_basis ?? "Engineering estimate")}</b>
              </div>
              <div>
                <span>Anomaly model active</span>
                <b>{status?.models.anomaly ? "YES" : "NO"}</b>
              </div>
              <div>
                <span>Fault model active</span>
                <b>{status?.models.fault ? "YES" : "Fallback"}</b>
              </div>
              <div>
                <span>RUL model active</span>
                <b>{status?.models.rul ? "YES" : "Fallback"}</b>
              </div>
            </div>
            <button className="ref-outline compact-action" onClick={load} disabled={busy}>
              Refresh Runtime State
            </button>
          </Panel>
        </div>
      )}
      {tab === "data" && (
        <div className="settings-columns settings-single">
          <Panel>
            <PanelTitle
              title="Data Management"
              subtitle="Export the current exact TwinGuard state or clear browser-side cached preferences."
            />
            <button className="settings-action" onClick={() => exportData("csv")}>
              <Download />
              Export Telemetry (CSV)
            </button>
            <button className="settings-action" onClick={() => exportData("json")}>
              <Download />
              Export Full Twin State (JSON)
            </button>
            <button className="settings-action danger" onClick={clearLocal}>
              <Trash2 />
              Clear Local TwinGuard Cache
            </button>
            <div className="settings-info">
              <Info />
              <p>
                The clear action keeps your authentication session, resets the simulator to healthy state and
                removes TwinGuard browser preferences/cache.
              </p>
            </div>
          </Panel>
        </div>
      )}
      {tab === "user" && (
        <div className="settings-columns settings-single">
          <Panel>
            <PanelTitle title="User Account" />
            <div className="user-account-card">
              <div className="large-avatar">
                {(user?.name ?? "KT")
                  .split(" ")
                  .map((x) => x[0])
                  .slice(0, 2)
                  .join("")}
              </div>
              <div>
                <span>Signed in as</span>
                <b>{user?.name ?? "Unknown User"}</b>
                <p>{user?.email ?? ""}</p>
                <StatusPill tone="blue">{pretty(user?.role ?? "user")}</StatusPill>
              </div>
            </div>
            <button className="settings-action danger" onClick={logout} disabled={busy}>
              <LogOut />
              Sign Out
            </button>
          </Panel>
        </div>
      )}
    </div>
  );
}
