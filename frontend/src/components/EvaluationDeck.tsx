import { useEffect, useState } from "react";
import {
  ArrowRight,
  Check,
  ClipboardCheck,
  Download,
  FileCheck2,
  FlaskConical,
  GitCompareArrows,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import { getDemoScenario, isHostedDemo } from "../demo/demoRuntime";
import { getTwin, resetFault, setFault } from "../services/twinApi";
import { useTwinStore } from "../store/twinStore";
import type { FaultName, TwinState } from "../types/twin";
import { pageHref } from "../utils/navigation";
import { fmt, pretty } from "./ui";
import { PageHeader, Panel, PanelTitle, StatusPill } from "./ReferenceUI";

type Injection = { fault: FaultName; severity: number; started_at: string };
type Capture = {
  id: string;
  captured_at: string;
  label: string;
  source: string;
  twin: TwinState;
  injection?: Injection;
};
// Tab memory deliberately avoids persisting potential backend telemetry in browser storage.
let evidenceSession: {
  baseline?: Capture;
  captures: Capture[];
  selected: FaultName;
  severity: number;
  injection?: Injection;
  started_at: string;
} = { captures: [], selected: "lubrication", severity: 65, started_at: new Date().toISOString() };
const scenarios: Array<{ fault: FaultName; title: string; detail: string; inspect: string }> = [
  {
    fault: "lubrication",
    title: "Lubrication loss",
    detail: "Falling oil pressure with rising temperature and vibration.",
    inspect: "Oil-pressure residual, lubrication health and remaining-life interval",
  },
  {
    fault: "cooling_degradation",
    title: "Cooling degradation",
    detail: "Thermal deterioration under a sustained operating load.",
    inspect: "CHT residual, thermal health and maintenance explanation",
  },
  {
    fault: "sensor_drift",
    title: "Sensor disagreement",
    detail: "A biased CHT reading tests whether sensor trust changes.",
    inspect: "CHT trust, data quality and diagnostic uncertainty",
  },
  {
    fault: "alternator_degradation",
    title: "Electrical degradation",
    detail: "Reduced charging voltage exposes an electrical fault pattern.",
    inspect: "Alternator voltage residual and electrical health",
  },
];
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));

export default function EvaluationDeck() {
  const demo = isHostedDemo();
  const twin = useTwinStore((s) => s.twin),
    runtime = useTwinStore((s) => s.runtimeValidity),
    online = useTwinStore((s) => s.online);
  const [sessionStartedAt, setSessionStartedAt] = useState(evidenceSession.started_at);
  const [baseline, setBaseline] = useState<Capture | undefined>(evidenceSession.baseline);
  const [captures, setCaptures] = useState<Capture[]>(evidenceSession.captures);
  const [selected, setSelected] = useState<FaultName>(evidenceSession.selected);
  const [severity, setSeverity] = useState(evidenceSession.severity);
  const [injection, setInjection] = useState<Injection | undefined>(evidenceSession.injection);
  const [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  useEffect(() => {
    evidenceSession = { baseline, captures, selected, severity, injection, started_at: sessionStartedAt };
  }, [baseline, captures, selected, severity, injection, sessionStartedAt]);
  useEffect(() => {
    if (!demo || !baseline) return;
    const active = getDemoScenario();
    if (active.fault === "normal") {
      if (injection) setInjection(undefined);
    } else if (active.started_at !== injection?.started_at || active.fault !== injection?.fault) {
      setInjection(active);
      setNotice(
        `Active simulator scenario is ${pretty(active.fault)}. Captures use the current scenario, including changes made in Settings.`,
      );
    }
  }, [demo, baseline, twin?.timestamp, injection]);
  const currentScenario = scenarios.find((s) => s.fault === selected)!;
  const eligible = online && runtime?.decision_eligible === true;
  const capture = (state: TwinState, label: string): Capture => ({
    id: crypto.randomUUID(),
    captured_at: new Date().toISOString(),
    label,
    source: demo
      ? "browser synthetic demonstrator"
      : (state.twin_meta?.telemetry_source ?? "backend-reported source unknown"),
    twin: clone(state),
    injection: demo ? getDemoScenario() : undefined,
  });
  async function execute(action: () => Promise<void>) {
    setBusy(true);
    setNotice("");
    try {
      await action();
    } catch (error) {
      setNotice(
        error instanceof Error ? error.message : "Unable to complete action. Check the connection and retry.",
      );
    } finally {
      setBusy(false);
    }
  }
  const begin = () =>
    execute(async () => {
      await resetFault();
      const state = await getTwin();
      useTwinStore.getState().setTwin(state);
      setBaseline(capture(state, "Healthy synthetic baseline"));
      setSessionStartedAt(new Date().toISOString());
      setCaptures([]);
      setInjection(undefined);
      setNotice(
        "Healthy baseline captured. Choose a fault to begin the comparison. This starts a new evidence session.",
      );
    });
  const inject = () =>
    execute(async () => {
      await setFault(selected, severity / 100);
      setInjection(getDemoScenario());
      setNotice(
        `${pretty(selected)} applied at ${severity}% intensity. Watch the progressive change for about 30 seconds, then capture the evidence.`,
      );
    });
  const save = () =>
    execute(async () => {
      const state = demo ? await getTwin() : twin;
      if (!state || !(demo ? state.runtime_validity?.decision_eligible : eligible))
        throw new Error("Fresh, eligible telemetry is required before capturing evidence.");
      const active = demo ? getDemoScenario() : undefined;
      const item = capture(
        state,
        active
          ? `${pretty(active.fault)} / ${Math.round(active.severity * 100)}% intensity`
          : "Current observation",
      );
      setCaptures((items) => [...items, item].slice(-12));
      setNotice(
        "Observation captured with its timestamp and complete twin state. The most recent 12 observations are retained in this session.",
      );
    });
  const exportEvidence = () =>
    execute(async () => {
      if (!twin) throw new Error("Wait for telemetry before exporting.");
      const state = demo ? await getTwin() : twin;
      const current = capture(state, "State at export");
      const payload = {
        schema: "twinguard-evaluation/1",
        generated_at: new Date().toISOString(),
        session_started_at: sessionStartedAt,
        problem_statement: "SIH26054",
        validation_scope: demo
          ? "Synthetic browser demonstration; scenario-conditioned outputs are not independent classifier validation."
          : "Backend observation; hardware provenance and predictive accuracy require separate validation.",
        limits: [
          "Not certified for flight decisions",
          "RUL interval is an engineering sensitivity range, not a calibrated confidence interval",
          "Mission feasibility is a model score, not a probability",
          "This checksum checks file integrity; it is not an authenticity signature",
        ],
        telemetry_units: {
          oil_pressure: "bar",
          oil_pressure_display: "kPa (bar × 100)",
          cht: "deg C",
          egt: "deg C",
          vibration: "g RMS",
          fuel_flow: "L/h surrogate",
        },
        injection: current.injection ?? null,
        baseline: baseline ?? null,
        observations: captures,
        current,
        runtime_validity_at_export: state.runtime_validity ?? runtime ?? null,
        mission_runs: clone(
          useTwinStore.getState().missionRuns.filter((run) => run.recorded_at >= sessionStartedAt),
        ),
      };
      const payloadText = JSON.stringify(payload);
      const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(payloadText));
      const sha256 = Array.from(new Uint8Array(hash), (b) => b.toString(16).padStart(2, "0")).join("");
      const text = JSON.stringify(
        { integrity: { algorithm: "SHA-256", encoding: "UTF-8 JSON.stringify(payload)", sha256 }, payload },
        null,
        2,
      );
      const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `TwinGuard-evidence-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice(
        "Evidence report downloaded with full state, units, provenance and a SHA-256 integrity checksum.",
      );
    });
  const rows = twin
    ? [
        {
          label: "Overall health",
          unit: "points / 100",
          previous: baseline?.twin.health.overall,
          value: twin.health.overall,
          digits: 1,
        },
        {
          label: "Oil-pressure residual",
          unit: "kPa",
          previous: baseline ? baseline.twin.residuals.oil_pressure_residual * 100 : undefined,
          value: twin.residuals.oil_pressure_residual * 100,
          digits: 1,
        },
        {
          label: "CHT residual",
          unit: "°C",
          previous: baseline?.twin.residuals.cht_residual,
          value: twin.residuals.cht_residual,
          digits: 1,
        },
        {
          label: "Vibration residual",
          unit: "g",
          previous: baseline?.twin.residuals.vibration_residual,
          value: twin.residuals.vibration_residual,
          digits: 3,
        },
        {
          label: "Sensor confidence",
          unit: "points / 100",
          previous: baseline?.twin.confidence.sensor,
          value: twin.confidence.sensor,
          digits: 1,
        },
        {
          label: "RUL estimate",
          unit: "hours",
          previous: baseline?.twin.ai.rul_hours,
          value: twin.ai.rul_hours,
          digits: 1,
        },
      ]
    : [];
  return (
    <div className="ref-page evaluation-page">
      <PageHeader
        title="Evaluation Center"
        subtitle="A repeatable demonstration, with the evidence behind every change."
      />
      <div className="eval-hero">
        <div>
          <span className="eval-eyebrow">SIH26054 / ENGINEERING DEMONSTRATOR</span>
          <h2>From a reading to a reason.</h2>
          <p>
            Establish the healthy state, introduce a controlled fault, inspect the residuals and evaluate the
            mission. Export what you observed.
          </p>
          <div className="eval-hero-tags">
            <span>
              <FlaskConical size={14} />
              {demo ? "Synthetic data" : "Backend observation"}
            </span>
            <span>
              <ShieldCheck size={14} />
              Traceable evidence
            </span>
            <span>
              <FileCheck2 size={14} />
              Human review
            </span>
          </div>
        </div>
        <div className="eval-hero-status">
          <span>DATA READINESS</span>
          <strong>{eligible ? "Ready to inspect" : "Waiting for data"}</strong>
          <small>{demo ? "No physical engine connected" : "Check source in Model Configuration"}</small>
          <a href={pageHref("settings", "model")}>
            View model details <ArrowRight size={14} />
          </a>
        </div>
      </div>
      <ol className="eval-steps" aria-label="Evaluation workflow">
        <li className={baseline ? "done" : ""}>
          <span>{baseline ? <Check size={17} /> : "01"}</span>
          <div>
            <b>Capture baseline</b>
            <small>Start from a known healthy state</small>
          </div>
        </li>
        <li className={injection ? "done" : ""}>
          <span>{injection ? <Check size={17} /> : "02"}</span>
          <div>
            <b>Introduce a fault</b>
            <small>Observe progressive degradation</small>
          </div>
        </li>
        <li className={captures.length ? "done" : ""}>
          <span>{captures.length ? <Check size={17} /> : "03"}</span>
          <div>
            <b>Inspect & export</b>
            <small>Keep a reproducible evidence record</small>
          </div>
        </li>
      </ol>
      {notice && (
        <div className="eval-notice" role="status">
          {notice}
        </div>
      )}
      <div className="eval-grid">
        <Panel className="eval-controls">
          <PanelTitle
            icon={<FlaskConical />}
            title="Controlled scenario"
            subtitle={
              demo
                ? "Changes the browser simulator only"
                : "Scenario controls are available in hosted demo mode"
            }
          />
          <button className="ref-outline full" onClick={begin} disabled={busy || !demo}>
            <RotateCcw size={16} />
            {baseline ? "Restart healthy baseline" : "Start healthy baseline"}
          </button>
          <div className="eval-scenarios" role="group" aria-label="Fault scenario">
            {scenarios.map((s) => (
              <button
                key={s.fault}
                aria-pressed={selected === s.fault}
                className={selected === s.fault ? "selected" : ""}
                onClick={() => setSelected(s.fault)}
                disabled={busy || !demo}
              >
                <b>{s.title}</b>
                <small>{s.detail}</small>
              </button>
            ))}
          </div>
          <label className="eval-range">
            Fault intensity <strong>{severity}%</strong>
            <input
              aria-label="Fault intensity"
              type="range"
              min={20}
              max={100}
              step={5}
              value={severity}
              onChange={(event) => setSeverity(Number(event.target.value))}
              disabled={busy || !demo}
            />
          </label>
          <button className="ref-primary full" onClick={inject} disabled={busy || !demo || !baseline}>
            Apply selected fault <ArrowRight size={16} />
          </button>
          <p className="eval-helper">
            <b>What to inspect:</b> {currentScenario.inspect}.
          </p>
        </Panel>
        <Panel className="eval-comparison">
          <PanelTitle
            icon={<GitCompareArrows />}
            title="Baseline vs current state"
            subtitle={
              baseline
                ? `Baseline captured ${new Date(baseline.captured_at).toLocaleTimeString()}`
                : "Capture a healthy baseline to enable the comparison"
            }
            right={
              <StatusPill tone={eligible ? "green" : "orange"}>
                {eligible ? "Fresh data" : "Data hold"}
              </StatusPill>
            }
          />
          <div className="eval-table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Signal</th>
                  <th scope="col">Baseline</th>
                  <th scope="col">Current</th>
                  <th scope="col">Change</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">
                      {row.label}
                      <small>{row.unit}</small>
                    </th>
                    <td>{row.previous === undefined ? "—" : fmt(row.previous, row.digits)}</td>
                    <td>{fmt(row.value, row.digits)}</td>
                    <td>
                      {row.previous === undefined
                        ? "—"
                        : `${row.value - row.previous > 0 ? "+" : ""}${fmt(row.value - row.previous, row.digits)}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!twin && <p className="eval-helper">Waiting for the first synchronized engine sample…</p>}
          <div className="eval-diagnosis">
            <span>CURRENT DIAGNOSTIC HYPOTHESIS</span>
            <b>{twin ? pretty(twin.ai.probable_fault) : "Waiting for telemetry"}</b>
            <p>{twin?.maintenance.reason ?? "Connect a source to inspect the evidence."}</p>
          </div>
          <div className="eval-actions">
            <button className="ref-primary" onClick={save} disabled={busy || !eligible}>
              <ClipboardCheck size={16} />
              Capture observation
            </button>
            <button className="ref-outline" onClick={exportEvidence} disabled={busy || !twin}>
              <Download size={16} />
              Export evidence
            </button>
          </div>
        </Panel>
      </div>
      <Panel className="eval-observations">
        <PanelTitle
          title="Session evidence"
          subtitle={`${captures.length} of 12 observations · kept across navigation until page reload`}
          right={
            <a className="eval-link" href={pageHref("mission")}>
              Evaluate mission impact <ArrowRight size={15} />
            </a>
          }
        />
        {captures.length ? (
          <ul>
            {captures.map((item) => (
              <li key={item.id}>
                <Check size={16} />
                <div>
                  <b>{item.label}</b>
                  <small>
                    {new Date(item.captured_at).toLocaleTimeString()} · {item.twin.engine_id} ·{" "}
                    {pretty(item.twin.ai.probable_fault)}
                  </small>
                </div>
                <span>{fmt(item.twin.health.overall, 1)} health</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="eval-helper">
            Your captured observations will appear here. Each includes the complete twin state and its source
            timestamp.
          </p>
        )}
      </Panel>
      <div className="eval-grid eval-bottom">
        <Panel>
          <PanelTitle
            title="What this prototype demonstrates"
            subtitle="Follow the complete reasoning chain"
          />
          <div className="eval-capabilities">
            {[
              [
                "01",
                "Synchronized state",
                "Telemetry, expected healthy behavior and unit-aware residuals.",
                "digitalTwin",
              ],
              [
                "02",
                "Explainable diagnosis",
                "Subsystem health, sensor trust and maintenance evidence.",
                "diagnostics",
              ],
              [
                "03",
                "Mission impact",
                "Profile-sensitive risk, engineering reserve and lower-stress alternatives.",
                "mission",
              ],
              ["04", "Recorded evidence", "Persisted samples and timeline playback for review.", "replay"],
            ].map(([n, title, detail, view]) => (
              <a key={n} href={pageHref(view as "digitalTwin" | "diagnostics" | "mission" | "replay")}>
                <span>{n}</span>
                <div>
                  <b>{title}</b>
                  <small>{detail}</small>
                </div>
                <ArrowRight size={16} />
              </a>
            ))}
          </div>
        </Panel>
        <Panel className="eval-boundary">
          <PanelTitle
            icon={<ShieldCheck />}
            title="Model & validation boundary"
            subtitle="Engineering transparency"
          />
          <dl>
            <div>
              <dt>Current runtime</dt>
              <dd>{pretty(twin?.ai.model_state ?? "Waiting")}</dd>
            </div>
            <div>
              <dt>Evidence scope</dt>
              <dd>
                {demo
                  ? "Scenario-conditioned browser simulation"
                  : (twin?.ai.validation_scope ?? "Source validation required")}
              </dd>
            </div>
            <div>
              <dt>RUL</dt>
              <dd>Engineering estimate; sensitivity interval is not calibrated confidence.</dd>
            </div>
            <div>
              <dt>Mission score</dt>
              <dd>Decision-support index, not a measured success probability.</dd>
            </div>
          </dl>
          <p>
            Independent validation requires held-out engine recordings, calibration records and verified fault
            / life labels. The browser demonstration does not establish predictive accuracy or airworthiness.
          </p>
          <a
            className="eval-link"
            href="https://github.com/krishnatayal1410/twinguard-aero"
            target="_blank"
            rel="noreferrer"
          >
            Inspect the source & validation tools <ArrowRight size={15} />
          </a>
        </Panel>
      </div>
    </div>
  );
}
