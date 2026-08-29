import{Canvas,useFrame,useThree}from"@react-three/fiber";
import{Html,OrbitControls,useGLTF,useTexture}from"@react-three/drei";
import{Suspense,useEffect,useMemo,useRef}from"react";
import*as THREE from"three";
import type{Group,Mesh}from"three";
import{useTwinStore}from"../store/twinStore";
import{fmt,pct,tone}from"./ui";
import{supportsWebGL}from"../utils/webgl";

type Props={compact?:boolean;explode?:boolean;xray?:boolean;focus?:string;autoRotate?:boolean;zoom?:number;resetToken?:number;onFocus?:(s:string)=>void};
type Part={mesh:Mesh;base:THREE.Vector3;target:THREE.Vector3;module:string;name:string;spin:number;phase:number};

const moduleOf=(name:string)=>{const n=name.toUpperCase();if(n.startsWith("FAN_"))return"fan";if(n.startsWith("COMPRESSOR_"))return"compressor";if(n.startsWith("COMBUSTOR_"))return"combustor";if(n.startsWith("TURBINE_"))return"turbine";if(n.startsWith("EXHAUST_"))return"exhaust";if(n.startsWith("ACCESSORY_"))return"accessory";if(n.startsWith("SENSOR_"))return"sensor";return"core"};
const offsets:Record<string,THREE.Vector3>={fan:new THREE.Vector3(-.78,0,0),compressor:new THREE.Vector3(-.34,0,0),combustor:new THREE.Vector3(.05,0,0),turbine:new THREE.Vector3(.48,0,0),exhaust:new THREE.Vector3(.92,0,0),accessory:new THREE.Vector3(-.08,.12,.16),sensor:new THREE.Vector3(0,.14,.15),core:new THREE.Vector3(0,0,0)};
const colors:Record<string,string>={fan:"#d7e0e5",compressor:"#b8c8d2",combustor:"#71808b",turbine:"#aebdc7",exhaust:"#c8d2d8",accessory:"#7a93a5",sensor:"#2ea7df",core:"#9aaab5"};

function moduleHealth(module:string,t:any){if(!t)return 96;if(module==="fan"||module==="compressor")return Number(t.health?.mechanical??96);if(module==="combustor"||module==="exhaust")return Number(t.health?.thermal??96);if(module==="turbine"){const h=Math.min(Number(t.health?.thermal??96),Number(t.health?.mechanical??96));return t.ai?.probable_fault==="turbine_blade_degradation"?Math.min(h,66):h}if(module==="accessory")return Number(t.health?.electrical??96);return Number(t.health?.overall??96)}
function partColor(module:string,h:number,name:string){if(name.includes("GLOW")||name==="SHAFT_CORE")return"#168fe5";if(name.includes("COMBUSTOR_CAN"))return"#b38452";if(name.includes("STATOR")||name.includes("SHAFT")||name.includes("INNER"))return"#5d6a73";if(h<70)return"#d66b70";if(h<86)return"#c6a25e";return colors[module]??"#a9b5bd"}

function EngineModel({explode=false,xray=false,focus="all",onFocus}:Props){
 const{scene}=useGLTF("/assets/engine/engine.glb"),matcap=useTexture("/assets/materials/aerospace-matcap.png"),darkMatcap=useTexture("/assets/materials/aerospace-dark-matcap.png"),twin=useTwinStore(s=>s.twin),root=useMemo(()=>scene.clone(true),[scene]),group=useRef<Group>(null),parts=useRef<Part[]>([]);
 useEffect(()=>{matcap.colorSpace=THREE.SRGBColorSpace;darkMatcap.colorSpace=THREE.SRGBColorSpace},[matcap,darkMatcap]);
 useEffect(()=>{parts.current=[];let i=0;root.traverse(o=>{if(!(o as Mesh).isMesh)return;const mesh=o as Mesh,name=mesh.name||`PART_${i}`,module=moduleOf(name),isGlow=name.includes("GLOW")||name==="SHAFT_CORE",isDark=name.includes("STATOR")||name.includes("SHAFT")||name.includes("INNER")||name.includes("HUB");
   mesh.geometry.computeVertexNormals();
   mesh.material=isGlow?new THREE.MeshBasicMaterial({color:"#1599ec",side:THREE.DoubleSide,toneMapped:false}):new THREE.MeshMatcapMaterial({color:"#becbd3",matcap:isDark?darkMatcap:matcap,side:THREE.DoubleSide,transparent:false,opacity:1});
   mesh.renderOrder=isGlow?3:1;mesh.frustumCulled=false;
   const base=mesh.position.clone(),target=base.clone().add(offsets[module]??offsets.core),spin=/FAN_BLADE|COMPRESSOR_ROTOR|COMPRESSOR_DISK|TURBINE_BLADE|TURBINE_DISK/.test(name)?1:0;parts.current.push({mesh,base,target,module,name,spin,phase:(i++%8)*Math.PI/4})})},[root,matcap,darkMatcap]);
 useEffect(()=>{for(const p of parts.current){const h=moduleHealth(p.module,twin),selected=focus==="all"||focus===p.module,isGlow=p.name.includes("GLOW")||p.name==="SHAFT_CORE",c=partColor(p.module,h,p.name),mat=p.mesh.material as THREE.Material;
   if(isGlow){const m=mat as THREE.MeshBasicMaterial;m.color.set(c);m.transparent=xray||!selected;m.opacity=xray?(selected?0.88:0.14):(selected?1:.16);m.depthWrite=!xray&&selected}
   else{const m=mat as THREE.MeshMatcapMaterial;m.color.set(c);m.transparent=xray||!selected;m.opacity=xray?(selected?0.78:0.09):(selected?1:.14);m.depthWrite=!xray&&selected;m.alphaTest=0;m.needsUpdate=true}
 }},[focus,xray,twin]);
 useFrame((_,dt)=>{const k=1-Math.exp(-dt*6),speed=Math.min(16,Math.max(3.5,Number(twin?.telemetry?.rpm??4200)/340));for(const p of parts.current){const target=explode?p.target:p.base;p.mesh.position.x=THREE.MathUtils.lerp(p.mesh.position.x,target.x,k);if(p.spin){p.phase+=dt*speed*(p.module==="turbine"?0.72:1);const co=Math.cos(p.phase),si=Math.sin(p.phase),y=p.base.y,z=p.base.z;p.mesh.position.y=y*co-z*si;p.mesh.position.z=y*si+z*co;p.mesh.rotation.x=p.phase}else{p.mesh.position.y=THREE.MathUtils.lerp(p.mesh.position.y,target.y,k);p.mesh.position.z=THREE.MathUtils.lerp(p.mesh.position.z,target.z,k)}}});
 return <group ref={group} rotation={[.045,-.22,.012]} scale={1.07} onDoubleClick={e=>{e.stopPropagation();onFocus?.(moduleOf(e.object.name))}}><primitive object={root}/></group>
}
function TechFloor(){return <group position={[0,-1.76,0]} rotation={[-Math.PI/2,0,0]}>{[1.5,2.3,3.1,3.9,4.7].map(r=><mesh key={r}><ringGeometry args={[r-.009,r+.009,112]}/><meshBasicMaterial color="#69bee9" transparent opacity={.20} toneMapped={false}/></mesh>)}{Array.from({length:16},(_,i)=>{const a=i*Math.PI/8;return <mesh key={i} rotation={[0,0,a]} position={[2.45,0,0]}><planeGeometry args={[4.9,.010]}/><meshBasicMaterial color="#9bd4ed" transparent opacity={.11} toneMapped={false}/></mesh>})}</group>}
function CoreGlow(){return <><pointLight position={[-1.4,.2,1.3]} intensity={1.6} color="#40b9ff"/><pointLight position={[1.2,.15,1]} intensity={1.2} color="#46c9ff"/></>}
function SceneSetup(){const{gl}=useThree();useEffect(()=>{gl.outputColorSpace=THREE.SRGBColorSpace;gl.toneMapping=THREE.NoToneMapping;gl.setClearColor("#f9fcff",1)},[gl]);return <><color attach="background" args={["#f9fcff"]}/><TechFloor/><CoreGlow/></>}
const positions:Record<string,[number,number,number]>={fan:[-3.0,1.78,.30],compressor:[-1.5,2.08,.24],combustor:[-.06,2.18,.18],turbine:[1.22,1.84,.18],exhaust:[3.04,-1.02,.20]};
function Callouts({focus}:{focus:string}){const t=useTwinStore(s=>s.twin);if(!t)return null;const data:any={fan:["FAN MODULE",moduleHealth("fan",t),"Temp 52°C"],compressor:["COMPRESSOR",moduleHealth("compressor",t),"Temp 78°C"],combustor:["COMBUSTOR",moduleHealth("combustor",t),`Temp ${fmt(t.telemetry.egt,0)}°C`],turbine:["TURBINE",moduleHealth("turbine",t),`Temp ${fmt(Number(t.telemetry.egt??1000)*.66,0)}°C`],exhaust:["EXHAUST NOZZLE",moduleHealth("exhaust",t),`Pressure ${fmt(t.telemetry.oil_pressure,2)} bar`]};return <>{Object.keys(data).filter(m=>focus==="all"||focus===m).map(m=><Html key={m} position={positions[m]} center distanceFactor={8.8} style={{pointerEvents:"none"}}><div className={`three-callout ${tone(data[m][1])}`}><span>{data[m][0]}</span><strong>{pct(data[m][1])}</strong><small>{data[m][2]}</small></div></Html>)}</>}
function CameraRig({zoom=1,resetToken=0}:{zoom?:number;resetToken?:number}){const{camera}=useThree();useEffect(()=>{camera.position.copy(new THREE.Vector3(8.4,3.2,9.2).multiplyScalar(zoom));camera.lookAt(0,.02,0);camera.updateProjectionMatrix()},[camera,zoom,resetToken]);return null}

export default function EngineTwin({compact=false,explode=false,xray=false,focus="all",autoRotate=false,zoom=1,resetToken=0,onFocus}:Props){
 if(typeof document!=="undefined"&&!supportsWebGL())return <div className="webgl-fallback"><strong>3D Engine Viewer</strong><span>WebGL is unavailable. Enable hardware acceleration and reload.</span></div>;
 return <Canvas dpr={[1,1.45]} camera={{position:[8.4,3.2,9.2],fov:29,near:.1,far:100}} gl={{antialias:true,alpha:false,powerPreference:"default",preserveDrawingBuffer:false}}>
  <SceneSetup/><CameraRig zoom={zoom} resetToken={resetToken}/>
  <Suspense fallback={<Html center><div className="three-loading">Loading 3D engine…</div></Html>}><EngineModel compact={compact} explode={explode} xray={xray} focus={focus} onFocus={onFocus}/>{!compact&&<Callouts focus={focus}/>}</Suspense>
  <OrbitControls makeDefault enableDamping dampingFactor={.06} minDistance={5.9} maxDistance={16} target={[0,.02,0]} autoRotate={autoRotate} autoRotateSpeed={.55}/>
 </Canvas>
}
useGLTF.preload("/assets/engine/engine.glb");
