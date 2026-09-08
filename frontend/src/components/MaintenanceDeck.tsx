import { CalendarCheck, CheckCircle2, Download, Printer, ShieldCheck, Wrench } from "lucide-react";
import { useTwinStore } from "../store/twinStore";
import { download, fmt, pretty } from "./ui";
import { EngineeringReadout, PageHeader, Panel, PanelTitle, StatusPill } from "./ReferenceUI";

export default function MaintenanceDeck() {
  const twin = useTwinStore((s) => s.twin),
    setView = useTwinStore((s) => s.setView);
  if (!twin) return <div className="empty-screen">Waiting for synchronized telemetry…</div>;
  const current = { generated_at: new Date().toISOString(), engine_id: twin.engine_id, twin };
  const csv = [
    ["field", "value"],
    ...Object.entries(twin.telemetry).map(([k, v]) => [`telemetry.${k}`, v]),
    ...Object.entries(twin.health).map(([k, v]) => [`health.${k}`, v]),
    ...Object.entries(twin.sensor_trust).map(([k, v]) => [`sensor_trust.${k}`, v]),
    ["probable_fault", twin.ai.probable_fault],
    ["rul_hours", twin.ai.rul_hours],
    ["maintenance_priority", twin.maintenance.priority],
  ]
    .map((r) => r.map((x) => `"${String(x).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const interval = twin.ai.rul_interval_hours,
    priority = twin.maintenance.priority,
    nextSuitability = twin.maintenance.next_mission_suitability;
  return (
    <div className="ref-page maintenance-page">
      <PageHeader
        title="Predictive Maintenance"
        subtitle={`${twin.engine_id} · condition-based maintenance guidance generated from the current synchronized Twin state`}
      />
      <div className="maintenance-grid">
        <Panel>
          <PanelTitle title="Current Condition" />
          <div className="diagnosis-card">
            <span>Probable condition</span>
            <b>{pretty(twin.ai.anomaly ? twin.ai.probable_fault : "normal operation")}</b>
          </div>
          <div className="engineering-grid">
            <EngineeringReadout label="RUL Estimate" value={fmt(twin.ai.rul_hours, 2)} unit="h" />
            <EngineeringReadout
              label="RUL Lower Bound"
              value={interval ? fmt(interval.lower, 2) : "--"}
              unit="h"
            />
            <EngineeringReadout
              label="RUL Upper Bound"
              value={interval ? fmt(interval.upper, 2) : "--"}
              unit="h"
            />
            <EngineeringReadout label="Overall Health" value={fmt(twin.health.overall, 1)} unit="/100" />
            <EngineeringReadout
              label="Decision Confidence"
              value={fmt(twin.confidence.decision, 1)}
              unit="%"
            />
            <EngineeringReadout
              label="Oil Pressure"
              value={fmt(twin.telemetry.oil_pressure * 100, 1)}
              unit="kPa"
            />
            <EngineeringReadout label="CHT" value={fmt(twin.telemetry.cht, 1)} unit="°C" />
            <EngineeringReadout label="Vibration" value={fmt(twin.telemetry.vibration, 3)} unit="g" />
          </div>
        </Panel>
        <Panel>
          <PanelTitle
            title="Maintenance Decision"
            right={
              <StatusPill tone={priority === "ROUTINE" ? "green" : priority === "MONITOR" ? "orange" : "red"}>
                {pretty(priority)}
              </StatusPill>
            }
          />
          <p>{twin.maintenance.reason}</p>
          <div className="model-detail-grid">
            <div>
              <span>Affected subsystem</span>
              <b>{pretty(twin.maintenance.affected_subsystem)}</b>
            </div>
            <div>
              <span>Next mission suitability</span>
              <b>{pretty(nextSuitability)}</b>
            </div>
            <div>
              <span>Readiness</span>
              <b>{pretty(twin.readiness.label)}</b>
            </div>
            <div>
              <span>Validation scope</span>
              <b>
                {pretty(
                  twin.maintenance.validation_scope ??
                    twin.ai.validation_scope ??
                    "synthetic proof of concept",
                )}
              </b>
            </div>
          </div>
          <button className="ref-primary" onClick={() => setView("mission")}>
            <ShieldCheck size={15} />
            Evaluate next mission profile
          </button>
        </Panel>
      </div>
      <Panel>
        <PanelTitle
          title="Recommended Checks"
          subtitle="Engineering verification actions based on the current Twin evidence"
        />
        <div className="inspection-list">
          {twin.maintenance.recommended_checks.map((x, i) => (
            <div key={x}>
              <i>{i + 1}</i>
              <div>
                <strong>{x}</strong>
                <p>
                  Verify against authorized maintenance procedures, sensor context and physical inspection
                  before operational use.
                </p>
              </div>
              <CheckCircle2 size={18} />
            </div>
          ))}
        </div>
      </Panel>
      <Panel className="report-card">
        <PanelTitle
          title="Maintenance & Condition Report"
          subtitle="Export the exact current Twin state for review or documentation"
        />
        <div className="report-actions">
          <button
            className="ref-primary"
            onClick={() =>
              download("twinguard-current-report.json", JSON.stringify(current, null, 2), "application/json")
            }
          >
            <Download size={14} />
            JSON Report
          </button>
          <button
            className="ref-outline"
            onClick={() => download("twinguard-current-report.csv", csv, "text/csv")}
          >
            <Download size={14} />
            CSV Report
          </button>
          <button className="ref-outline" onClick={() => window.print()}>
            <Printer size={14} />
            Print / Save PDF
          </button>
        </div>
        <div className="next-check">
          <CalendarCheck size={28} />
          <div>
            <span>Maintenance posture</span>
            <strong>
              {priority === "ROUTINE"
                ? "Continue scheduled monitoring"
                : "Review before next mission decision"}
            </strong>
          </div>
          <Wrench size={24} />
        </div>
      </Panel>
    </div>
  );
}
