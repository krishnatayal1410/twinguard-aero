# TwinGuard Aero — Exact Screenshot Dashboard Final

This is the complete standalone TwinGuard Aero project built around `docs/MASTER_UI_REFERENCE.png`.

The Command Center deliberately follows that reference composition: the same light white/blue visual system, left navigation rail, top telemetry bar, large exploded turboshaft hero, UAV System View, AI Decision Center, seven telemetry cards, Mission Lab, Mission Replay, Diagnostics / Explainability and the bottom Simulator strip.

## Frontend
- React [TypeScript]
- Vite [JavaScript/TypeScript]
- Three.js [JavaScript/TypeScript]
- React Three Fiber [TypeScript]
- Drei [TypeScript]
- Framer Motion [TypeScript/JavaScript]
- Plotly.js [JavaScript/TypeScript]
- Zustand [TypeScript]
- Axios [TypeScript/JavaScript]

The 3D engine uses an original generic turboshaft GLB with hundreds of independently addressable parts. The dashboard initially matches the supplied reference visual; touching Rotate / Explode / X-Ray / fullscreen switches the hero into the fully interactive WebGL model.

3D features:
- Rotate / orbit / zoom
- Explode / assemble
- X-ray
- Fullscreen
- Fan, compressor, combustor, turbine and exhaust modules
- Animated rotor stages
- Blue energy rings
- Component clicking
- Health-dependent state coloring
- Live telemetry-driven condition visualization

## Backend / Digital Twin
- FastAPI [Python]
- Pydantic [Python]
- SQLAlchemy [Python]
- synthetic engine simulator [Python]
- simplified physics / residual model [Python]
- Sensor Trust [Python]
- Data Quality [Python]
- health engine [Python]
- confidence fusion [Python]
- Isolation Forest [Python/scikit-learn]
- XGBoost fault classifier [Python/C++]
- XGBoost RUL regressor [Python/C++]
- explainability / evidence engine [Python]
- predictive maintenance [Python]
- Mission Lab / mission-aware RUL [Python]
- counterfactual mission planning [Python]
- Mission Replay and event timeline [Python]

The model pack includes the dashboard simulator scenario `turbine_blade_degradation` in addition to lubrication, overheating, vibration, sensor drift, injector and misfire scenarios.

## Data / integrations
- SQLite [SQL] local runtime
- PostgreSQL [SQL] deployment
- TimescaleDB [SQL/PostgreSQL extension] deployment
- MQTT / Eclipse Mosquitto [C] / Paho MQTT [Python]
- CAN / SocketCAN [Linux/C] / python-can [Python] / cantools [Python]
- Unreal Engine UDP JSON + WebSocket bridge

## Deployment
- Docker
- Docker Compose [YAML]
- Nginx
- local macOS launcher
- debugging and security scripts

## Start on macOS

Extract the folder to Desktop, then:

```bash
cd ~/Desktop/TwinGuard_Aero_Exact_Screenshot_Final
chmod +x START_TWINGUARD.command scripts/*.sh
./START_TWINGUARD.command
```

Open:
- Dashboard: `http://localhost:5173`
- Backend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

Do not press `Ctrl+C` during the first dependency installation.

## Verify the system

```bash
cd ~/Desktop/TwinGuard_Aero_Exact_Screenshot_Final
source .venv/bin/activate
export PYTHONPATH="$PWD/backend"
export TWINGUARD_INGEST_KEY="$(cat .runtime/ingest.key)"
python scripts/verify_system.py
```

The verifier checks backend state, Digital Twin state, diagnostics, system status, maintenance, Mission Lab, turbine-blade-degradation simulation and Mission Replay.

## Debug

```bash
bash scripts/doctor.sh
```

Logs are stored in:
- `.runtime/logs/backend.log`
- `.runtime/logs/frontend.log`
- `.runtime/logs/simulator.log`

## Security

```bash
bash scripts/security_check.sh
```

Included defaults:
- explicit CORS allowlist
- trusted-host validation
- telemetry ingest key
- strict Pydantic validation
- request-size cap
- Nginx Content Security Policy
- loopback-only local service binding
- no embedded private keys / real CAN IDs

Automated checks cannot prove that a system has zero vulnerabilities. Before internet-facing or real-engine operation, add organizational authentication/authorization, TLS/mTLS, managed secrets, network segmentation, dependency CVE scans, SAST/DAST, penetration testing, audit logging and an appropriate aerospace cybersecurity review.

## Important engineering limitation

The included telemetry, physics equations, AI metrics, RUL and maintenance outputs are synthetic proof-of-concept outputs. The 3D model is an original generic visualization, not proprietary manufacturer/DRDO CAD. Engine-specific calibration and authorized test-rig validation are required before operational use.


## True-3D corrections

This final build removes the old image-to-model swap. The engine is WebGL from the first frame and remains the same object while rotating, exploding, assembling, zooming, entering X-Ray mode or fullscreen. The UAV System View and Mission Replay previews are also live 3D scenes.

## Final visible-3D + authentication update

This build removes the black 3D rendering issue seen on Safari by replacing reflection-dependent physical materials with a lit Phong material pipeline, DoubleSide rendering and explicit ambient/key/fill lights. Rotate, Explode/Assemble, X-Ray, zoom, reset and fullscreen continue to operate on the same engine object.

Authentication is now built in:
- Sign Up
- Sign In
- Sign Out
- persistent local operator sessions
- first registered account receives `admin`; later accounts receive `operator`
- PBKDF2-SHA256 password hashing
- random server-side session tokens
- 7-day session expiration
- authenticated Digital Twin, Diagnostics, Mission Lab, Replay, Simulation, Maintenance and System Status endpoints

The telemetry ingest API remains separate and requires the TwinGuard ingest key.


## Pro Visible 3D Final Pass

This build specifically fixes the black-engine / black-UAV rendering seen on Safari.

### Rendering changes
- The engine and UAV now use bundled **matcap shading textures**.
- Matcap shading does not depend on HDR environment maps, browser reflections, or Safari lighting behavior.
- The same WebGL engine remains on screen for Rotate, Explode/Assemble, Zoom, Reset, X-Ray and Fullscreen.
- The UAV System View remains a real interactive 3D model.
- The UAV landing gear is hidden in the flight-context view to keep the aircraft silhouette clean.
- Engine and UAV geometry are forced to DoubleSide and have vertex normals recomputed at runtime.
- No screenshot overlay is used for the engine or UAV.

### Readability changes
- Larger sidebar/navigation.
- Larger top-bar controls.
- Larger engine and UAV viewports.
- Larger telemetry values.
- Larger simulator controls.
- Larger Diagnostics, Mission Lab, Replay, Maintenance and Settings typography.

### Authentication
The existing local account system remains enabled:
- Sign Up
- Sign In
- Sign Out
- operator/admin profile menu
- PBKDF2-SHA256 password hashing
- expiring server-side sessions
- protected Digital Twin / mission / replay / maintenance APIs

## Start

```bash
cd ~/Desktop/TwinGuard_Aero_ProVisible3D_Final
chmod +x START_TWINGUARD.command scripts/*.sh
./START_TWINGUARD.command
```

Wait until the terminal prints `TwinGuard Aero is running`, then open `http://localhost:5173`.
