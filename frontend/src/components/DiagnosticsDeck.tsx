import { Brain, Database, FileText, Gauge, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useTwinStore } from "../store/twinStore";
import { fmt, pretty } from "./ui";
import { Bar, EngineeringReadout, PageHeader, Panel, PanelTitle, StatusPill } from "./ReferenceUI";

type Tab = "why" | "model" | "trust" | "quality" | "system";
export default function DiagnosticsDeck() {
  const twin = useTwinStore((s) => s.twin),
    runtime = useTwinStore((s) => s.runtimeValidity),
    [tab, setTab] = useState<Tab>("why");
  if (!twin) return <div className="empty-screen">Waiting for synchronized telemetry…</div>;
  const ai = twin.ai,
    r = twin.residuals,
    tr = twin.trends,
    trust = twin.sensor_trust,
    t = twin.telemetry,
    fault = ai.anomaly ? pretty(ai.probable_fault) : "Normal Operation",
    confidence = ai.fault_confidence * 100,
    sev = twin.health.overall < 65 ? "HIGH" : twin.health.overall < 86 ? "MODERATE" : "LOW";
  const contrib = ai.evidence?.length
    ? ai.evidence.slice(0, 6)
    : [
        { feature: "oil_pressure_residual", weight: 0.34, value: r.oil_pressure_residual },
        { feature: "oil_pressure_rate", weight: 0.22, value: tr.oil_pressure_per_min },
        { feature: "oil_temperature_residual", weight: 0.18, value: r.oil_temperature_residual },
        { feature: "vibration_residual", weight: 0.14, value: r.vibration_residual },
        { feature: "persistence", weight: 0.08, value: Number(ai.anomaly_persistence_samples ?? 0) },
        { feature: "sensor_trust", weight: 0.04, value: twin.confidence.sensor },
      ];
  const oilResidualKpa = r.oil_pressure_residual * 100;
  const evidence = [
    `Oil-pressure residual is ${oilResidualKpa >= 0 ? "+" : ""}${fmt(oilResidualKpa, 1)} kPa versus the contextual expected state.`,
    `Oil-pressure rate is ${fmt(tr.oil_pressure_per_min * 100, 2)} kPa/min.`,
    `Oil-temperature residual is ${r.oil_temperature_residual >= 0 ? "+" : ""}${fmt(r.oil_temperature_residual, 1)} °C.`,
    `Vibration residual is ${r.vibration_residual >= 0 ? "+" : ""}${fmt(r.vibration_residual, 3)} g.`,
    `Anomaly evidence has persisted for ${Number(ai.anomaly_persistence_samples ?? 0)} samples.`,
  ];
  return (
    <div className="ref-page diagnostics-ref-page">
      <PageHeader
        title="Diagnostics & Explainability"
        subtitle="Exact evidence, model behavior, sensor trust, data quality and runtime status"
      />
      <div className="ref-tabs">
        {[
          ["why", "Why This Diagnosis?"],
          ["model", "Model Analysis"],
          ["trust", "Sensor Trust"],
          ["quality", "Data Quality"],
          ["system", "System Status"],
        ].map(([id, label]) => (
          <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id as Tab)}>
            {label}
          </button>
        ))}
      </div>
      {tab === "why" && (
        <div className="diag-grid">
          <Panel>
            <PanelTitle icon={<FileText />} title="Diagnosis Breakdown" />
            <div className={`diagnosis-card ${ai.anomaly ? "bad" : "good"}`}>
              <span>Current Diagnosis</span>
              <b>{fault}</b>
            </div>
            <div className="diag-pair">
              <div>
                <span>Confidence</span>
                <b>{fmt(confidence, 1)}%</b>
                <Bar value={confidence} color="blue" />
              </div>
              <div>
                <span>Severity</span>
                <StatusPill tone={sev === "LOW" ? "green" : sev === "MODERATE" ? "orange" : "red"}>
                  {sev}
                </StatusPill>
              </div>
            </div>
            <h4>Top Contributing Signals</h4>
            <div className="contrib-list diag-contrib">
              {contrib.map((x) => (
                <div key={x.feature}>
                  <span>{pretty(x.feature)}</span>
                  <Bar value={Math.min(100, Math.max(2, x.weight * 100 * 2.3))} color="blue" />
                  <b>{fmt(x.weight * 100, 1)}%</b>
                </div>
              ))}
            </div>
          </Panel>
          <Panel>
            <PanelTitle title="Evidence Explanation" />
            <div className="numbered-evidence">
              {evidence.map((x, i) => (
                <div key={x}>
                  <i>{i + 1}</i>
                  <p>{x}</p>
                </div>
              ))}
            </div>
            <div className="model-reasoning">
              <Brain />
              <div>
                <b>Model Reasoning</b>
                <p>
                  {ai.anomaly
                    ? "Multiple correlated residuals, temporal persistence and cross-sensor agreement support a developing engine-system degradation rather than a single transient reading."
                    : "Current residuals remain inside the demonstrator's nominal operating envelope with no persistent correlated degradation pattern."}
                </p>
              </div>
            </div>
          </Panel>
          <div className="diag-right">
            <Panel>
              <PanelTitle icon={<Gauge />} title="Exact Diagnostic Snapshot" />
              <div className="engineering-grid one-col">
                <EngineeringReadout
                  label="Oil Pressure"
                  value={fmt(t.oil_pressure * 100, 1)}
                  unit="kPa"
                  residual={`${oilResidualKpa >= 0 ? "+" : ""}${fmt(oilResidualKpa, 1)} kPa`}
                />
                <EngineeringReadout
                  label="CHT"
                  value={fmt(t.cht, 1)}
                  unit="°C"
                  residual={`${r.cht_residual >= 0 ? "+" : ""}${fmt(r.cht_residual, 1)} °C`}
                />
                <EngineeringReadout
                  label="Vibration"
                  value={fmt(t.vibration, 3)}
                  unit="g"
                  residual={`${r.vibration_residual >= 0 ? "+" : ""}${fmt(r.vibration_residual, 3)} g`}
                />
                <EngineeringReadout label="RUL" value={fmt(ai.rul_hours, 2)} unit="h" />
              </div>
            </Panel>
          </div>
        </div>
      )}
      {tab === "model" && (
        <div className="tab-stack">
          <Panel>
            <PanelTitle icon={<Brain />} title="AI / Hybrid Model Analysis" />
            <div className="model-detail-grid">
              <div>
                <span>Anomaly score</span>
                <b>{fmt(ai.anomaly_score * 100, 2)}%</b>
              </div>
              <div>
                <span>Fault confidence</span>
                <b>{fmt(confidence, 2)}%</b>
              </div>
              <div>
                <span>Decision confidence</span>
                <b>{fmt(twin.confidence.decision, 2)}%</b>
              </div>
              <div>
                <span>Physics agreement</span>
                <b>{fmt(twin.confidence.physics_agreement, 2)}%</b>
              </div>
              <div>
                <span>RUL point estimate</span>
                <b>{fmt(ai.rul_hours, 2)} h</b>
              </div>
              <div>
                <span>RUL uncertainty</span>
                <b>
                  {ai.rul_interval_hours
                    ? `${fmt(ai.rul_interval_hours.lower, 2)}–${fmt(ai.rul_interval_hours.upper, 2)} h`
                    : "--"}
                </b>
              </div>
              <div>
                <span>Model state</span>
                <b>{pretty(ai.model_state)}</b>
              </div>
              <div>
                <span>Validation scope</span>
                <b>{pretty(ai.validation_scope ?? "engineering demonstrator")}</b>
              </div>
            </div>
          </Panel>
          <Panel>
            <PanelTitle title="Fault Probability Vector" />
            <div className="probability-grid">
              {Object.entries(ai.fault_probabilities)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([name, v]) => (
                  <div key={name}>
                    <span>{pretty(name)}</span>
                    <Bar
                      value={Number(v) * 100}
                      color={Number(v) > 0.6 ? "red" : Number(v) > 0.3 ? "orange" : "blue"}
                    />
                    <b>{fmt(Number(v) * 100, 2)}%</b>
                  </div>
                ))}
            </div>
          </Panel>
        </div>
      )}
      {tab === "trust" && (
        <div className="tab-stack">
          <Panel>
            <PanelTitle
              icon={<Database />}
              title="Sensor Trust"
              subtitle="Trust percentage plus the exact measured value carried by each channel"
            />
            <div className="sensor-trust-exact">
              {[
                ["RPM", trust.rpm ?? 99, `${fmt(t.rpm, 0)} rpm`],
                ["CHT", trust.cht ?? 97, `${fmt(t.cht, 1)} °C`],
                ["EGT", trust.egt ?? 96, `${fmt(t.egt, 1)} °C`],
                ["Oil Pressure", trust.oil_pressure ?? 92, `${fmt(t.oil_pressure * 100, 1)} kPa`],
                ["Oil Temp", trust.oil_temperature ?? 90, `${fmt(t.oil_temperature, 1)} °C`],
                ["Vibration", trust.vibration ?? 90, `${fmt(t.vibration, 3)} g`],
                ["Battery", trust.battery_voltage ?? 89, `${fmt(t.battery_voltage, 2)} V`],
                ["Alternator", trust.alternator_voltage ?? 89, `${fmt(t.alternator_voltage, 2)} V`],
              ].map(([k, v, raw]) => (
                <div key={String(k)}>
                  <div>
                    <span>{k}</span>
                    <b>{raw}</b>
                  </div>
                  <Bar value={Number(v)} />
                  <strong>{fmt(v, 1)}%</strong>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      )}
      {tab === "quality" && (
        <div className="tab-stack">
          <Panel>
            <PanelTitle icon={<ShieldCheck />} title="Data Quality & Freshness" />
            <div className="model-detail-grid">
              <div>
                <span>Overall data quality</span>
                <b>{fmt(runtime?.data_quality ?? twin.confidence.data_quality, 2)}%</b>
              </div>
              <div>
                <span>Telemetry age</span>
                <b>
                  {runtime?.telemetry_age_seconds == null
                    ? "--"
                    : `${fmt(runtime.telemetry_age_seconds, 2)} s`}
                </b>
              </div>
              <div>
                <span>Freshness limit</span>
                <b>{fmt(runtime?.freshness_limit_seconds ?? twin.twin_meta?.freshness_gate_seconds, 2)} s</b>
              </div>
              <div>
                <span>Minimum quality</span>
                <b>{fmt(runtime?.minimum_data_quality ?? twin.twin_meta?.mission_min_data_quality, 1)}%</b>
              </div>
              <div>
                <span>Decision eligible</span>
                <b className={runtime?.decision_eligible !== false ? "green-text" : "red-text"}>
                  {runtime?.decision_eligible !== false ? "YES" : "NO"}
                </b>
              </div>
              <div>
                <span>Stale</span>
                <b className={runtime?.stale ? "red-text" : "green-text"}>{runtime?.stale ? "YES" : "NO"}</b>
              </div>
            </div>
          </Panel>
        </div>
      )}
      {tab === "system" && (
        <div className="tab-stack">
          <Panel>
            <PanelTitle icon={<ShieldCheck />} title="Runtime Information" />
            <div className="runtime-list system-runtime-grid">
              <div>
                <span>Engine ID</span>
                <b>{twin.engine_id}</b>
              </div>
              <div>
                <span>Model Mode</span>
                <b>{pretty(ai.model_state)}</b>
              </div>
              <div>
                <span>Model Source</span>
                <b>Synthetic training / engineering reference</b>
              </div>
              <div>
                <span>Physics model</span>
                <b>{pretty(twin.twin_meta?.physics_model ?? "healthy reference model")}</b>
              </div>
              <div>
                <span>Telemetry source</span>
                <b>{pretty(twin.twin_meta?.telemetry_source ?? "live simulator")}</b>
              </div>
              <div>
                <span>Validation Scope</span>
                <b>{pretty(ai.validation_scope ?? "engineering demonstrator")}</b>
              </div>
              <div>
                <span>Readiness</span>
                <b>{pretty(twin.readiness.label ?? twin.readiness.status ?? "unknown")}</b>
              </div>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}
