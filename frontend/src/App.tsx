import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'

type TwinState = {
  status: string
  telemetry?: Record<string, number | string> | null
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
  maintenance?: { priority?: string; message?: string } | null
}

const API = 'http://localhost:8000'
const WS = 'ws://localhost:8000/ws/telemetry'

function Card({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="card">
      <div className="label">{title}</div>
      <div className="value">{value}</div>
    </div>
  )
}

export default function App() {
  const [state, setState] = useState<TwinState>({ status: 'loading' })
  const [connection, setConnection] = useState('connecting')

  useEffect(() => {
    axios.get(`${API}/state`).then(r => setState(r.data)).catch(() => {})

    const ws = new WebSocket(WS)
    ws.onopen = () => {
      setConnection('live')
      ws.send('hello')
    }
    ws.onmessage = event => setState(JSON.parse(event.data))
    ws.onerror = () => setConnection('websocket error')
    ws.onclose = () => setConnection('offline')

    const keepalive = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping')
    }, 15000)

    return () => {
      clearInterval(keepalive)
      ws.close()
    }
  }, [])

  const t = state.telemetry ?? {}
  const h = state.health ?? {}
  const faultPct = useMemo(() => {
    const p = state.ai?.fault_probability
    return p == null ? '--' : `${Math.round(p * 100)}%`
  }, [state.ai?.fault_probability])

  return (
    <main>
      <header>
        <div>
          <div className="eyebrow">UAV Engine Digital Twin Prototype</div>
          <h1>TwinGuard Aero</h1>
        </div>
        <div className="status">{connection} · {state.status}</div>
      </header>

      <section className="grid">
        <Card title="Overall Health" value={h.overall != null ? `${h.overall}%` : '--'} />
        <Card title="RPM" value={t.rpm ?? '--'} />
        <Card title="CHT" value={t.cht != null ? `${t.cht} °C` : '--'} />
        <Card title="EGT" value={t.egt != null ? `${t.egt} °C` : '--'} />
        <Card title="Oil Pressure" value={t.oil_pressure != null ? `${t.oil_pressure} bar` : '--'} />
        <Card title="Oil Temp" value={t.oil_temp != null ? `${t.oil_temp} °C` : '--'} />
        <Card title="Vibration" value={t.vibration ?? '--'} />
        <Card title="Altitude" value={t.altitude != null ? `${t.altitude} m` : '--'} />
      </section>

      <section className="panel">
        <h2>AI Diagnostics</h2>
        <div className="diagnostic-grid">
          <p><strong>Anomaly:</strong> {state.ai?.anomaly ? 'Detected' : 'No / model unavailable'}</p>
          <p><strong>Probable fault:</strong> {state.ai?.fault ?? 'unknown'}</p>
          <p><strong>Fault confidence:</strong> {faultPct}</p>
          <p><strong>RUL:</strong> {state.ai?.rul_hours != null ? `${state.ai.rul_hours} h` : 'model not trained'}</p>
        </div>
      </section>

      <section className="panel">
        <h2>Maintenance</h2>
        <p><strong>{state.maintenance?.priority ?? 'WAITING'}</strong></p>
        <p>{state.maintenance?.message ?? 'Waiting for telemetry.'}</p>
      </section>

      <section className="two-col">
        <div className="panel">
          <h2>Physics Residuals</h2>
          <pre>{JSON.stringify(state.residuals, null, 2)}</pre>
        </div>
        <div className="panel">
          <h2>Sensor Trust</h2>
          <pre>{JSON.stringify(state.sensor_trust, null, 2)}</pre>
        </div>
      </section>
    </main>
  )
}
