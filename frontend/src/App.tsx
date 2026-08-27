
import { useEffect, useMemo, useRef, useState } from 'react'

type TwinState = {
  engine_id?: string
  status: string
  telemetry?: Record<string, number | string | null> | null
  expected?: Record<string, number> | null
  residuals?: Record<string, number> | null
  sensor_trust?: Record<string, number> | null
  health?: Record<string, number> | null
  ai?: {
    anomaly?: boolean
    anomaly_score?: number
    fault?: string
    fault_probability?: number
    fault_probabilities?: Record<string, number>
    rul_hours?: number | null
  }
  maintenance?: {
    priority?: string
    message?: string
  } | null
}

type MetricKey =
  | 'rpm'
  | 'cht'
  | 'egt'
  | 'oil_pressure'
  | 'oil_temp'
  | 'vibration'
  | 'altitude'
  | 'battery_voltage'

type History = Record<MetricKey, number[]>

const API = 'http://127.0.0.1:8000'
const WS = 'ws://127.0.0.1:8000/ws/telemetry'

const EMPTY_HISTORY: History = {
  rpm: [],
  cht: [],
  egt: [],
  oil_pressure: [],
  oil_temp: [],
  vibration: [],
  altitude: [],
  battery_voltage: [],
}

const metricMeta: Record<
  MetricKey,
  { label: string; unit: string; decimals: number; short: string }
> = {
  rpm: { label: 'Engine Speed', unit: 'RPM', decimals: 0, short: 'RPM' },
  cht: { label: 'Cylinder Head', unit: '°C', decimals: 1, short: 'CHT' },
  egt: { label: 'Exhaust Gas', unit: '°C', decimals: 1, short: 'EGT' },
  oil_pressure: { label: 'Oil Pressure', unit: 'bar', decimals: 2, short: 'OIL P' },
  oil_temp: { label: 'Oil Temperature', unit: '°C', decimals: 1, short: 'OIL T' },
  vibration: { label: 'Vibration', unit: 'g', decimals: 3, short: 'VIB' },
  altitude: { label: 'Altitude', unit: 'm', decimals: 0, short: 'ALT' },
  battery_voltage: { label: 'Electrical', unit: 'V', decimals: 1, short: 'BATT' },
}

function numberFrom(value: number | string | null | undefined, fallback = 0) {
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : fallback
  }
  return fallback
}

function Sparkline({
  values,
  width = 150,
  height = 42,
}: {
  values: number[]
  width?: number
  height?: number
}) {
  if (values.length < 2) {
    return <div className="sparkline-empty" />
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = Math.max(max - min, 0.0001)
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width
      const y = height - ((value - min) / range) * (height - 6) - 3
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline points={points} fill="none" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

function MetricCard({
  metric,
  value,
  values,
}: {
  metric: MetricKey
  value: number
  values: number[]
}) {
  const meta = metricMeta[metric]
  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <div>
          <span className="metric-kicker">{meta.short}</span>
          <h3>{meta.label}</h3>
        </div>
        <span className="metric-live-dot" />
      </div>
      <div className="metric-value-row">
        <strong>{value.toFixed(meta.decimals)}</strong>
        <span>{meta.unit}</span>
      </div>
      <Sparkline values={values} />
    </article>
  )
}

function HealthRing({ value }: { value: number }) {
  const safe = Math.max(0, Math.min(100, value))
  const tone = safe >= 80 ? 'healthy' : safe >= 60 ? 'warning' : 'danger'
  return (
    <div className={`health-ring ${tone}`} style={{ '--health': `${safe * 3.6}deg` } as React.CSSProperties}>
      <div className="health-ring-inner">
        <strong>{safe.toFixed(0)}%</strong>
        <span>Overall health</span>
      </div>
    </div>
  )
}

function ProgressBar({
  label,
  value,
  suffix = '%',
}: {
  label: string
  value: number
  suffix?: string
}) {
  const safe = Math.max(0, Math.min(100, value))
  return (
    <div className="progress-row">
      <div className="progress-label">
        <span>{label}</span>
        <strong>{safe.toFixed(0)}{suffix}</strong>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${safe}%` }} />
      </div>
    </div>
  )
}

function App() {
  const [state, setState] = useState<TwinState>({ status: 'connecting' })
  const [connection, setConnection] = useState<'connecting' | 'live' | 'offline'>('connecting')
  const [activeMetric, setActiveMetric] = useState<MetricKey>('cht')
  const [history, setHistory] = useState<History>(EMPTY_HISTORY)
  const [activeView, setActiveView] = useState('Command Center')
  const [simulationFault, setSimulationFault] = useState('normal')
  const [simulationSeverity, setSimulationSeverity] = useState(70)
  const [simulationBusy, setSimulationBusy] = useState(false)
  const [simulationMessage, setSimulationMessage] = useState('Healthy baseline active')
  const socketRef = useRef<WebSocket | null>(null)

  const applyState = (next: TwinState) => {
    setState(next)
    const t = next.telemetry ?? {}
    setHistory(prev => {
      const updated = { ...prev }
      ;(Object.keys(metricMeta) as MetricKey[]).forEach(key => {
        const value = numberFrom(t[key])
        const prior = prev[key] ?? []
        updated[key] = [...prior, value].slice(-48)
      })
      return updated
    })
  }


  const sendSimulationControl = async (
    fault: string,
    severity: number,
  ) => {
    setSimulationBusy(true)

    try {
      const response = await fetch(`${API}/simulation/control`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fault,
          severity: fault === 'normal' ? 0 : severity / 100,
        }),
      })

      if (!response.ok) {
        throw new Error(`Simulation control failed: ${response.status}`)
      }

      const control = await response.json()
      setSimulationFault(control.fault || fault)

      if (control.fault === 'normal') {
        setSimulationMessage('Healthy baseline active')
      } else {
        setSimulationMessage(
          `${String(control.fault).replaceAll('_', ' ')} injected at ${Math.round(
            Number(control.severity || 0) * 100,
          )}% severity`,
        )
      }
    } catch (error) {
      console.error(error)
      setSimulationMessage('Could not reach simulation control API')
    } finally {
      setSimulationBusy(false)
    }
  }

  useEffect(() => {
    fetch(`${API}/state`)
      .then(res => res.json())
      .then(applyState)
      .catch(() => {})

    const ws = new WebSocket(WS)
    socketRef.current = ws

    ws.onopen = () => {
      setConnection('live')
      ws.send('hello')
    }
    ws.onmessage = event => {
      try {
        applyState(JSON.parse(event.data))
      } catch {
        // Ignore malformed development messages.
      }
    }
    ws.onerror = () => setConnection('offline')
    ws.onclose = () => setConnection('offline')

    const keepalive = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping')
    }, 15000)

    return () => {
      window.clearInterval(keepalive)
      ws.close()
    }
  }, [])

  const t = state.telemetry ?? {}
  const h = state.health ?? {}
  const trust = state.sensor_trust ?? {}
  const residuals = state.residuals ?? {}
  const ai = state.ai ?? {}

  const overallHealth = numberFrom(h.overall, 0)
  const missionReady = overallHealth >= 75 && !ai.anomaly
  const faultConfidence = numberFrom(ai.fault_probability) * 100
  const faultName = (ai.fault || 'model not trained').replaceAll('_', ' ')
  const rul = ai.rul_hours

  const metricValues = useMemo(() => {
    const out = {} as Record<MetricKey, number>
    ;(Object.keys(metricMeta) as MetricKey[]).forEach(key => {
      out[key] = numberFrom(t[key])
    })
    return out
  }, [t])

  const activeMeta = metricMeta[activeMetric]
  const activeSeries = history[activeMetric]
  const activeValue = metricValues[activeMetric]

  const residualEntries = Object.entries(residuals)
  const maxResidual = Math.max(1, ...residualEntries.map(([, value]) => Math.abs(numberFrom(value))))

  const subsystemEntries = [
    ['Thermal', numberFrom(h.thermal)],
    ['Lubrication', numberFrom(h.lubrication)],
    ['Mechanical', numberFrom(h.mechanical)],
    ['Electrical', numberFrom(h.electrical)],
  ] as const

  const trustEntries = Object.entries(trust)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">TG</div>
          <div>
            <strong>TwinGuard</strong>
            <span>Aero</span>
          </div>
        </div>

        <nav className="nav-list">
          {['Command Center', 'Diagnostics', 'Mission Lab', 'Mission Replay', 'Maintenance'].map(item => (
            <button
              key={item}
              className={activeView === item ? 'nav-item active' : 'nav-item'}
              onClick={() => setActiveView(item)}
            >
              <span className="nav-icon">
                {item === 'Command Center' ? '◫' :
                 item === 'Diagnostics' ? '⌁' :
                 item === 'Mission Lab' ? '△' :
                 item === 'Mission Replay' ? '↺' : '◇'}
              </span>
              {item}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="engine-mini">
            <span className={`status-dot ${connection}`} />
            <div>
              <strong>{state.engine_id || 'ENGINE-01'}</strong>
              <span>{connection === 'live' ? 'Telemetry linked' : 'Link offline'}</span>
            </div>
          </div>
          <div className="prototype-tag">MVP / SYNTHETIC DATA</div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <div className="eyebrow">UAV PROPULSION DIGITAL TWIN</div>
            <h1>{activeView}</h1>
          </div>
          <div className="topbar-actions">
            <div className="engine-id">
              <span>ENGINE</span>
              <strong>{state.engine_id || 'ENGINE-01'}</strong>
            </div>
            <div className={`live-pill ${connection}`}>
              <span className="pulse-dot" />
              {connection === 'live' ? 'LIVE TELEMETRY' : connection.toUpperCase()}
            </div>
          </div>
        </header>

        <section className="hero-grid">
          <article className="hero-card health-card">
            <div className="section-heading">
              <div>
                <span className="section-kicker">DIGITAL TWIN STATE</span>
                <h2>Engine Health</h2>
              </div>
              <span className="tiny-status">{state.status || 'waiting'}</span>
            </div>

            <div className="health-content">
              <HealthRing value={overallHealth} />
              <div className="health-summary">
                <div className="summary-row">
                  <span>Mission readiness</span>
                  <strong className={missionReady ? 'text-good' : 'text-warn'}>
                    {missionReady ? 'READY' : 'REVIEW'}
                  </strong>
                </div>
                <div className="summary-row">
                  <span>Current anomaly</span>
                  <strong className={ai.anomaly ? 'text-danger' : 'text-good'}>
                    {ai.anomaly ? 'DETECTED' : 'NONE'}
                  </strong>
                </div>
                <div className="summary-row">
                  <span>RUL estimate</span>
                  <strong>{rul != null ? `${Number(rul).toFixed(1)} h` : 'Pending model'}</strong>
                </div>
              </div>
            </div>
          </article>

          <article className={`hero-card readiness-card ${missionReady ? 'ready' : 'review'}`}>
            <div className="readiness-glow" />
            <div className="section-heading">
              <div>
                <span className="section-kicker">OPERATIONAL DECISION</span>
                <h2>Mission Readiness</h2>
              </div>
              <span className="readiness-badge">{missionReady ? 'GO' : 'REVIEW'}</span>
            </div>

            <div className="readiness-main">
              <strong>{missionReady ? 'Engine available for nominal mission profile' : 'Engineering review recommended'}</strong>
              <p>
                {state.maintenance?.message ||
                  'TwinGuard is evaluating current condition and mission suitability.'}
              </p>
            </div>

            <div className="readiness-footer">
              <span>Maintenance priority</span>
              <strong>{state.maintenance?.priority || 'MONITOR'}</strong>
            </div>
          </article>
        </section>

        <section className="simulation-panel panel">
          <div className="section-heading">
            <div>
              <span className="section-kicker">DEVELOPMENT TEST CONTROLS</span>
              <h2>Simulation Control</h2>
            </div>
            <span className={simulationFault === 'normal' ? 'signal good' : 'signal danger'}>
              {simulationFault === 'normal' ? 'NORMAL' : 'FAULT ACTIVE'}
            </span>
          </div>

          <div className="simulation-control-grid">
            <label className="control-field">
              <span>Fault scenario</span>
              <select
                value={simulationFault}
                onChange={event => setSimulationFault(event.target.value)}
                disabled={simulationBusy}
              >
                <option value="normal">Normal / Healthy</option>
                <option value="lubrication">Lubrication degradation</option>
                <option value="overheating">Overheating</option>
                <option value="vibration">Abnormal vibration</option>
                <option value="sensor_drift">Sensor drift</option>
              </select>
            </label>

            <label className="control-field severity-field">
              <span>
                Severity
                <strong>{simulationFault === 'normal' ? '0%' : `${simulationSeverity}%`}</strong>
              </span>
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={simulationSeverity}
                disabled={simulationBusy || simulationFault === 'normal'}
                onChange={event => setSimulationSeverity(Number(event.target.value))}
              />
              <div className="range-scale">
                <span>Low</span>
                <span>Moderate</span>
                <span>Severe</span>
              </div>
            </label>

            <div className="simulation-actions">
              <button
                className="control-button inject"
                disabled={simulationBusy || simulationFault === 'normal'}
                onClick={() =>
                  sendSimulationControl(simulationFault, simulationSeverity)
                }
              >
                {simulationBusy ? 'APPLYING…' : 'INJECT FAULT'}
              </button>

              <button
                className="control-button reset"
                disabled={simulationBusy}
                onClick={() => {
                  setSimulationFault('normal')
                  sendSimulationControl('normal', 0)
                }}
              >
                RESET HEALTHY
              </button>
            </div>
          </div>

          <div className="simulation-status-line">
            <span className={simulationFault === 'normal' ? 'status-dot live' : 'status-dot offline'} />
            <span>{simulationMessage}</span>
            <span className="simulation-disclaimer">
              Synthetic test control · not a physical engine command
            </span>
          </div>
        </section>

        <section className="metrics-grid">
          {(Object.keys(metricMeta) as MetricKey[]).map(metric => (
            <MetricCard
              key={metric}
              metric={metric}
              value={metricValues[metric]}
              values={history[metric]}
            />
          ))}
        </section>

        <section className="content-grid">
          <article className="panel trend-panel">
            <div className="section-heading">
              <div>
                <span className="section-kicker">LIVE TELEMETRY TREND</span>
                <h2>{activeMeta.label}</h2>
              </div>
              <div className="trend-current">
                <strong>{activeValue.toFixed(activeMeta.decimals)}</strong>
                <span>{activeMeta.unit}</span>
              </div>
            </div>

            <div className="metric-tabs">
              {(Object.keys(metricMeta) as MetricKey[]).map(key => (
                <button
                  key={key}
                  className={key === activeMetric ? 'metric-tab active' : 'metric-tab'}
                  onClick={() => setActiveMetric(key)}
                >
                  {metricMeta[key].short}
                </button>
              ))}
            </div>

            <div className="big-chart">
              <div className="chart-grid-lines">
                <span /><span /><span /><span /><span />
              </div>
              <Sparkline values={activeSeries} width={760} height={230} />
              <div className="chart-caption">
                <span>Last {activeSeries.length} samples</span>
                <span>Streaming at ~1 Hz</span>
              </div>
            </div>
          </article>

          <article className="panel diagnostics-panel">
            <div className="section-heading">
              <div>
                <span className="section-kicker">AI / PHM LAYER</span>
                <h2>Diagnostics</h2>
              </div>
              <span className={ai.anomaly ? 'signal danger' : 'signal good'}>
                {ai.anomaly ? 'ANOMALY' : 'NORMAL'}
              </span>
            </div>

            <div className="diagnostic-focus">
              <span>Probable condition</span>
              <strong>{faultName}</strong>
              <div className="confidence-row">
                <div className="confidence-track">
                  <div style={{ width: `${Math.max(2, faultConfidence)}%` }} />
                </div>
                <span>{faultConfidence.toFixed(0)}%</span>
              </div>
            </div>

            <div className="diagnostic-stat-grid">
              <div>
                <span>Anomaly score</span>
                <strong>{numberFrom(ai.anomaly_score).toFixed(3)}</strong>
              </div>
              <div>
                <span>RUL</span>
                <strong>{rul != null ? `${Number(rul).toFixed(1)} h` : '—'}</strong>
              </div>
              <div>
                <span>Model state</span>
                <strong>{ai.fault === 'model_not_trained' ? 'TRAINING NEEDED' : 'ACTIVE'}</strong>
              </div>
            </div>
          </article>
        </section>

        <section className="lower-grid">
          <article className="panel">
            <div className="section-heading">
              <div>
                <span className="section-kicker">HEALTH DECOMPOSITION</span>
                <h2>Subsystem Health</h2>
              </div>
            </div>
            <div className="progress-list">
              {subsystemEntries.map(([label, value]) => (
                <ProgressBar key={label} label={label} value={value} />
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="section-heading">
              <div>
                <span className="section-kicker">INPUT CONFIDENCE</span>
                <h2>Sensor Trust</h2>
              </div>
            </div>
            <div className="progress-list">
              {trustEntries.length ? trustEntries.map(([label, value]) => (
                <ProgressBar
                  key={label}
                  label={label.replaceAll('_', ' ')}
                  value={numberFrom(value)}
                />
              )) : <div className="empty-state">Waiting for sensor confidence.</div>}
            </div>
          </article>

          <article className="panel residual-panel">
            <div className="section-heading">
              <div>
                <span className="section-kicker">PHYSICS-RESIDUAL TWIN</span>
                <h2>Actual vs Expected</h2>
              </div>
            </div>
            <div className="residual-list">
              {residualEntries.length ? residualEntries.map(([label, raw]) => {
                const value = numberFrom(raw)
                const magnitude = Math.min(100, Math.abs(value) / maxResidual * 100)
                return (
                  <div className="residual-row" key={label}>
                    <div className="residual-label">
                      <span>{label.replace('_residual', '').replaceAll('_', ' ')}</span>
                      <strong className={value > 0 ? 'positive' : value < 0 ? 'negative' : ''}>
                        {value > 0 ? '+' : ''}{value.toFixed(2)}
                      </strong>
                    </div>
                    <div className="residual-track">
                      <div className="residual-center" />
                      <div
                        className={value >= 0 ? 'residual-fill positive' : 'residual-fill negative'}
                        style={{
                          width: `${magnitude / 2}%`,
                          left: value >= 0 ? '50%' : `${50 - magnitude / 2}%`,
                        }}
                      />
                    </div>
                  </div>
                )
              }) : <div className="empty-state">Waiting for physics residuals.</div>}
            </div>
          </article>
        </section>

        <footer className="footer-note">
          <span>TWINGUARD AERO · DEVELOPMENT BUILD</span>
          <span>Synthetic telemetry / simplified physics / not for flight-critical use</span>
        </footer>
      </main>
    </div>
  )
}

export default App

