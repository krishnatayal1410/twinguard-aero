import { Canvas, useFrame } from "@react-three/fiber";
import { Html, OrbitControls, useGLTF } from "@react-three/drei";
import { Box, Crosshair, Focus, Maximize2, Minimize2, Moon, Move3d, RotateCcw, Scan, Sun, Tags, ZoomIn, ZoomOut } from "lucide-react";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { Object3D } from "three";
import { useTwinStore } from "../store/twinStore";
import { supportsWebGL } from "../utils/webgl";
import { fmt, pretty } from "./ui";

type Props = { compact?: boolean; explode?: boolean; xray?: boolean; focus?: string; autoRotate?: boolean; zoom?: number; resetToken?: number; onFocus?: (s: string) => void };
type ViewMode = "assembled" | "exploded" | "xray";
type ModuleName = "core" | "cylinders" | "injection" | "turbo" | "cooling" | "lubrication" | "internals";

const MODULES: ModuleName[] = ["core", "cylinders", "injection", "turbo", "cooling", "lubrication", "internals"];
const OFFSETS: Record<ModuleName, [number, number, number]> = {
  core: [0, 0, 0], cylinders: [.95, .1, 0], injection: [0, .85, .08], turbo: [0, -.15, 1], cooling: [-.75, .45, -.3], lubrication: [0, -.75, -.1], internals: [-.85, -.05, .15],
};
const LABEL_POSITIONS: Record<ModuleName, [number, number, number]> = {
  core: [0, .25, -.55], cylinders: [1.55, .75, .1], injection: [.2, 1.7, .25], turbo: [.5, .35, 1.65], cooling: [-1.55, 1.15, -.55], lubrication: [.1, -1.45, -.2], internals: [-1.55, -.35, .5],
};
const LABELS: Record<ModuleName, string> = { core: "Crankcase", cylinders: "Cylinder banks", injection: "Fuel injection", turbo: "Turbocharger", cooling: "Cooling circuit", lubrication: "Lubrication", internals: "Internal drive" };

function healthFor(module: ModuleName, twin: any) {
  if (!twin) return 96;
  if (module === "cylinders" || module === "cooling") return Number(twin.health?.thermal ?? 96);
  if (module === "lubrication") return Number(twin.health?.lubrication ?? 96);
  if (module === "injection" || module === "turbo") return Number(twin.health?.combustion ?? 96);
  return Number(twin.health?.mechanical ?? 96);
}

function faultModule(fault?: string): ModuleName {
  const value = (fault || "").toLowerCase();
  if (value.includes("oil") || value.includes("lubric")) return "lubrication";
  if (value.includes("cool") || value.includes("heat") || value.includes("thermal")) return "cooling";
  if (value.includes("inject") || value.includes("combust") || value.includes("misfire")) return "injection";
  if (value.includes("turbo")) return "turbo";
  if (value.includes("vibr") || value.includes("mechan")) return "internals";
  return "core";
}

function EngineAsset({ mode, opacity, focus, explodeAmount, wireframe, onFocus }: { mode: ViewMode; opacity: number; focus: string; explodeAmount: number; wireframe: boolean; onFocus: (m: string) => void }) {
  const gltf = useGLTF("/assets/engine/twinguard-rotax-915-production.glb");
  const root = useMemo(() => gltf.scene.clone(true), [gltf.scene]);
  const modules = useRef<Array<{ name: ModuleName; object: Object3D; base: THREE.Vector3 }>>([]);
  useEffect(() => {
    modules.current = [];
    root.traverse((object) => {
      const name = object.name.toLowerCase() as ModuleName;
      if (MODULES.includes(name)) {
        if (!object.userData.tgBase) object.userData.tgBase = object.position.clone();
        modules.current.push({ name, object, base: object.userData.tgBase.clone() });
      }
      if ((object as THREE.Mesh).isMesh) {
        const mesh = object as THREE.Mesh;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.material = Array.isArray(mesh.material) ? mesh.material.map((material) => material.clone()) : mesh.material.clone();
      }
    });
  }, [root]);
  useEffect(() => {
    root.traverse((object) => {
      if (!(object as THREE.Mesh).isMesh) return;
      const mesh = object as THREE.Mesh;
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      const owner = MODULES.find((module) => {
        let parent: Object3D | null = object;
        while (parent) { if (parent.name.toLowerCase() === module) return true; parent = parent.parent; }
        return false;
      });
      const hasSelection = focus !== "all";
      const selected = hasSelection && owner === focus;
      for (const source of materials) {
        const material = source as THREE.MeshStandardMaterial;
        const visibleOpacity = mode === "xray" ? selected ? Math.max(.64, opacity) : Math.min(.26, opacity) : hasSelection ? selected ? opacity : .12 : opacity;
        material.transparent = visibleOpacity < .99;
        material.opacity = visibleOpacity;
        material.depthWrite = visibleOpacity > .55;
        material.wireframe = wireframe;
        material.needsUpdate = true;
      }
    });
  }, [root, mode, opacity, focus, wireframe]);
  useFrame((_, delta) => {
    const smoothing = 1 - Math.exp(-delta * 5.5);
    for (const item of modules.current) {
      const offset: [number, number, number] = mode === "exploded" ? OFFSETS[item.name] : [0, 0, 0];
      const scale = explodeAmount / 100;
      const target = item.base.clone().add(new THREE.Vector3(offset[0] * scale, offset[1] * scale, offset[2] * scale));
      item.object.position.lerp(target, smoothing);
    }
  });
  return <group rotation={[.08, -.48, .02]} scale={1.12} onDoubleClick={(event) => {
    event.stopPropagation();
    let parent: Object3D | null = event.object;
    while (parent && !MODULES.includes(parent.name.toLowerCase() as ModuleName)) parent = parent.parent;
    onFocus(parent?.name.toLowerCase() || "all");
  }}><primitive object={root} /></group>;
}

function ModelLabels({ visible, mode, explodeAmount }: { visible: boolean; mode: ViewMode; explodeAmount: number }) {
  if (!visible) return null;
  return <>{MODULES.map((module) => {
    const base = LABEL_POSITIONS[module];
    const offset: [number, number, number] = mode === "exploded" ? OFFSETS[module] : [0, 0, 0];
    const scale = explodeAmount / 100;
    const position: [number, number, number] = [base[0] + offset[0] * scale, base[1] + offset[1] * scale, base[2] + offset[2] * scale];
    return <Html key={module} position={position} center distanceFactor={9}><div className="engine-part-label">{LABELS[module]}</div></Html>;
  })}</>;
}

function FaultMarker({ module, active }: { module: ModuleName; active: boolean }) {
  if (!active) return null;
  const position = LABEL_POSITIONS[module];
  return <group position={[position[0] * .45, position[1] * .45, position[2] * .45]}><mesh><sphereGeometry args={[.12, 24, 24]} /><meshBasicMaterial color="#ef4444" toneMapped={false} /></mesh><Html center distanceFactor={8}><div className="engine-fault-label"><i />FAULT LOCATION</div></Html></group>;
}
function Loader() { return <Html center><div className="engine-loader"><i /><span>Loading engineering model…</span></div></Html>; }

function Scene({ mode, opacity, focus, autoRotate, resetToken, explodeAmount, wireframe, labels, darkStage, onFocus, fault }: { mode: ViewMode; opacity: number; focus: string; autoRotate: boolean; resetToken: number; explodeAmount: number; wireframe: boolean; labels: boolean; darkStage: boolean; onFocus: (m: string) => void; fault: ModuleName }) {
  const controls = useRef<any>();
  useEffect(() => { controls.current?.reset(); }, [resetToken]);
  return <><color attach="background" args={[darkStage ? "#081b2a" : "#f4f8fb"]} /><hemisphereLight args={[darkStage ? "#cce7ff" : "#ffffff", darkStage ? "#06111b" : "#b9cad6", darkStage ? 1.8 : 2.4]} /><directionalLight position={[5, 8, 6]} intensity={3.2} castShadow /><directionalLight position={[-6, 2, -4]} intensity={darkStage ? 2.2 : 1.6} color="#60a5fa" /><Suspense fallback={<Loader />}><EngineAsset mode={mode} opacity={opacity} focus={focus} explodeAmount={explodeAmount} wireframe={wireframe} onFocus={onFocus} /><ModelLabels visible={labels} mode={mode} explodeAmount={explodeAmount} /><FaultMarker module={fault} active={mode === "xray"} /></Suspense><gridHelper args={[16, 32, darkStage ? "#1c5576" : "#c7d8e5", darkStage ? "#102f43" : "#e5edf3"]} position={[0, -2.25, 0]} /><OrbitControls ref={controls} makeDefault target={[0, 0, 0]} enableDamping dampingFactor={.07} minDistance={4} maxDistance={14} autoRotate={autoRotate} autoRotateSpeed={.6} /></>;
}

export default function EngineTwin({ compact = false, explode = false, xray = false, focus: externalFocus = "all", autoRotate: externalRotate = false, resetToken = 0, onFocus }: Props) {
  const twin = useTwinStore((state) => state.twin);
  const host = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<ViewMode>(xray ? "xray" : explode ? "exploded" : "assembled");
  const [opacity, setOpacity] = useState(100), [focus, setFocus] = useState(externalFocus), [autoRotate, setAutoRotate] = useState(externalRotate), [fullscreen, setFullscreen] = useState(false), [reset, setReset] = useState(0);
  const [explodeAmount, setExplodeAmount] = useState(110), [wireframe, setWireframe] = useState(false), [labels, setLabels] = useState(false), [darkStage, setDarkStage] = useState(false);
  useEffect(() => setFocus(externalFocus), [externalFocus]);
  useEffect(() => setMode(xray ? "xray" : explode ? "exploded" : "assembled"), [xray, explode]);
  useEffect(() => { const sync = () => setFullscreen(document.fullscreenElement === host.current); document.addEventListener("fullscreenchange", sync); return () => document.removeEventListener("fullscreenchange", sync); }, []);
  if (typeof document !== "undefined" && !supportsWebGL()) return <div className="webgl-fallback"><strong>3D engine viewer unavailable</strong><span>Enable browser hardware acceleration and reload.</span></div>;
  const fault = faultModule(twin?.ai.probable_fault);
  const setSelected = (module: string) => { setFocus(module); onFocus?.(module); };
  const locateFault = () => { setMode("xray"); setOpacity(26); setFocus(fault); setLabels(true); };
  const toggleFull = async () => { if (!host.current) return; if (document.fullscreenElement) await document.exitFullscreen(); else await host.current.requestFullscreen(); };
  return <div ref={host} className={`engine-viewer ${compact ? "compact " : ""}${fullscreen ? "fullscreen " : ""}${darkStage ? "dark-stage" : ""}`}>
    <div className="engine-toolbar" role="toolbar" aria-label="3D engine controls"><div className="engine-mode-switch"><button className={mode === "assembled" ? "active" : ""} onClick={() => setMode("assembled")}>Assembled</button><button className={mode === "exploded" ? "active" : ""} onClick={() => setMode("exploded")}><Move3d /> Exploded</button><button className={mode === "xray" ? "active" : ""} onClick={() => setMode("xray")}><Scan /> X-ray</button></div><div className="engine-tool-actions"><button className="fault-locate" onClick={locateFault} title="Locate predicted fault"><Crosshair /><span>Locate fault</span></button><button aria-pressed={labels} className={labels ? "active" : ""} onClick={() => setLabels((value) => !value)} title="Toggle component labels"><Tags /></button><button aria-pressed={wireframe} className={wireframe ? "active" : ""} onClick={() => setWireframe((value) => !value)} title="Toggle wireframe"><Box /></button><button aria-pressed={darkStage} className={darkStage ? "active" : ""} onClick={() => setDarkStage((value) => !value)} title="Toggle inspection stage">{darkStage ? <Sun /> : <Moon />}</button><button aria-pressed={autoRotate} className={autoRotate ? "active" : ""} onClick={() => setAutoRotate((value) => !value)} title="Auto rotate"><RotateCcw /></button><button onClick={() => setReset((value) => value + 1)} title="Reset camera"><Focus /></button><button onClick={toggleFull} title={fullscreen ? "Exit full screen" : "Full screen"}>{fullscreen ? <Minimize2 /> : <Maximize2 />}</button></div></div>
    <div className="engine-canvas"><Canvas shadows dpr={[1, 1.6]} camera={{ position: [6.8, 3.6, 8.6], fov: 32, near: .1, far: 100 }} gl={{ antialias: true, powerPreference: "high-performance" }}><Scene mode={mode} opacity={opacity / 100} focus={focus} autoRotate={autoRotate} resetToken={reset + resetToken} explodeAmount={explodeAmount} wireframe={wireframe} labels={labels} darkStage={darkStage} onFocus={setSelected} fault={fault} /></Canvas></div>
    <div className="engine-sliders"><div className="engine-opacity"><ZoomOut /><label><span>Casing opacity</span><input aria-label="Engine casing opacity" type="range" min="8" max="100" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /></label><b>{opacity}%</b><ZoomIn /></div>{mode === "exploded" && <div className="engine-opacity engine-explode-range"><Move3d /><label><span>Explode distance</span><input aria-label="Explode distance" type="range" min="45" max="180" value={explodeAmount} onChange={(event) => setExplodeAmount(Number(event.target.value))} /></label><b>{explodeAmount}%</b></div>}</div>
    {!compact && <div className="engine-parts"><div className="engine-parts-head"><span>COMPONENT INSPECTOR</span>{focus !== "all" && <button onClick={() => setSelected("all")}>Show all</button>}</div>{MODULES.map((module) => <button key={module} className={focus === module ? "active" : ""} onClick={() => setSelected(focus === module ? "all" : module)}><i style={{ background: healthFor(module, twin) < 86 ? "#f59e0b" : "#20a47b" }} /><span>{LABELS[module]}</span><b>{fmt(healthFor(module, twin), 0)}%</b></button>)}</div>}
    {fullscreen && <aside className="engine-diagnostic-drawer"><small>LIVE DIAGNOSTIC</small><h3>{twin?.ai.anomaly ? pretty(twin.ai.probable_fault) : "Engine operating normally"}</h3><button className="drawer-locate" onClick={locateFault}><Crosshair /> Reveal predicted fault</button><div className="engine-health-ring"><b>{fmt(twin?.health.overall, 0)}%</b><span>overall health</span></div><dl><div><dt>RPM</dt><dd>{fmt(twin?.telemetry.rpm, 0)}</dd></div><div><dt>Oil pressure</dt><dd>{fmt(Number(twin?.telemetry.oil_pressure || 0) * 100, 1)} kPa</dd></div><div><dt>CHT</dt><dd>{fmt(twin?.telemetry.cht, 1)} °C</dd></div><div><dt>RUL</dt><dd>{fmt(twin?.ai.rul_hours, 1)} h</dd></div></dl><p>{mode === "xray" ? "Fault marker stays visible through the transparent casing." : "Use Reveal predicted fault to isolate the affected subsystem."}</p></aside>}
  </div>;
}
useGLTF.preload("/assets/engine/twinguard-rotax-915-production.glb");
