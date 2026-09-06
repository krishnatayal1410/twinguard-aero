import{Canvas,useFrame,useThree}from"@react-three/fiber";
import{OrbitControls,useTexture}from"@react-three/drei";
import{useEffect,useMemo,useRef}from"react";
import*as THREE from"three";
import type{Group}from"three";
import{useTwinStore}from"../store/twinStore";
import{supportsWebGL}from"../utils/webgl";

type Props={compact?:boolean;explode?:boolean;xray?:boolean;focus?:string;autoRotate?:boolean;zoom?:number;resetToken?:number;onFocus?:(s:string)=>void};
type ModuleName="crankcase"|"cylinders"|"lubrication"|"induction"|"exhaust"|"electrical";

const EXPLODE:Record<ModuleName,[number,number,number]>={
 crankcase:[0,0,0],cylinders:[.55,0,0],lubrication:[0,-.45,0],induction:[0,.42,0],exhaust:[0,0,.48],electrical:[-.35,.18,-.32]
};

function healthFor(module:ModuleName,t:any){
 if(!t)return 96;
 if(module==="cylinders")return Math.min(Number(t.health?.thermal??96),Number(t.health?.combustion??96));
 if(module==="lubrication")return Number(t.health?.lubrication??96);
 if(module==="induction")return Number(t.health?.combustion??96);
 if(module==="exhaust")return Number(t.health?.thermal??96);
 if(module==="electrical")return Number(t.health?.electrical??96);
 return Number(t.health?.mechanical??96);
}
function healthColor(h:number){return h<67?"#d35b65":h<86?"#c99545":"#a9bac5"}

function Mat({module,xray,selected}:{module:ModuleName;xray:boolean;selected:boolean}){
 const twin=useTwinStore(s=>s.twin),matcap=useTexture("/assets/materials/aerospace-matcap.png");
 useEffect(()=>{matcap.colorSpace=THREE.SRGBColorSpace},[matcap]);
 const h=healthFor(module,twin),opacity=xray?(selected?.66:.10):(selected?1:.16);
 return <meshMatcapMaterial matcap={matcap} color={healthColor(h)} side={THREE.DoubleSide} transparent={opacity<1} opacity={opacity} depthWrite={opacity>.7}/>;
}

function Module({name,explode,xray,focus,onFocus,children}:{name:ModuleName;explode:boolean;xray:boolean;focus:string;onFocus?:(s:string)=>void;children:React.ReactNode}){
 const group=useRef<Group>(null),target=EXPLODE[name],selected=focus==="all"||focus===name;
 useFrame((_,dt)=>{if(!group.current)return;const k=1-Math.exp(-dt*6),m=explode?1:0;group.current.position.x=THREE.MathUtils.lerp(group.current.position.x,target[0]*m,k);group.current.position.y=THREE.MathUtils.lerp(group.current.position.y,target[1]*m,k);group.current.position.z=THREE.MathUtils.lerp(group.current.position.z,target[2]*m,k)});
 return <group ref={group} onDoubleClick={e=>{e.stopPropagation();onFocus?.(name)}}>{children}{/* invisible hit target keeps module selectable */}<mesh visible={false}><boxGeometry args={[.01,.01,.01]}/><meshBasicMaterial/></mesh></group>;
}

function AeroPistonEngine({explode=false,xray=false,focus="all",onFocus}:Props){
 const twin=useTwinStore(s=>s.twin),rpm=Number(twin?.telemetry?.rpm??3900),shaft=useRef<Group>(null);
 useFrame((_,dt)=>{if(shaft.current)shaft.current.rotation.x+=dt*Math.min(18,Math.max(2,rpm/300))});
 const selected=(m:ModuleName)=>focus==="all"||focus===m;
 const heads=useMemo(()=>[-.62,.62],[]);
 return <group rotation={[.12,-.34,.02]} scale={1.08}>
  <Module name="crankcase" explode={explode} xray={xray} focus={focus} onFocus={onFocus}>
   <mesh scale={[1.55,.86,1.25]}><boxGeometry args={[1,1,1]}/><Mat module="crankcase" xray={xray} selected={selected("crankcase")}/></mesh>
   <group ref={shaft} rotation={[0,0,Math.PI/2]}><mesh><cylinderGeometry args={[.16,.16,2.1,32]}/><meshBasicMaterial color="#5b6b76" transparent opacity={xray?.45:1}/></mesh></group>
   <mesh position={[0,0,1.02]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.48,.38,.48,32]}/><Mat module="crankcase" xray={xray} selected={selected("crankcase")}/></mesh>
  </Module>

  <Module name="cylinders" explode={explode} xray={xray} focus={focus} onFocus={onFocus}>
   {heads.flatMap(z=>[-1,1].map((side,i)=>{const x=side*1.62;return <group key={`${z}-${side}`} position={[x,0,z]}>
    <mesh rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.48,.55,1.35,32,1,true]}/><Mat module="cylinders" xray={xray} selected={selected("cylinders")}/></mesh>
    <mesh position={[side*.72,0,0]} scale={[.42,.78,.78]}><boxGeometry/><Mat module="cylinders" xray={xray} selected={selected("cylinders")}/></mesh>
    {[-.25,0,.25].map(y=><mesh key={y} position={[side*.82,y,0]} rotation={[0,0,Math.PI/2]}><torusGeometry args={[.46,.035,10,40]}/><meshBasicMaterial color="#627785" transparent opacity={xray?.45:1}/></mesh>)}
   </group>}))}
  </Module>

  <Module name="induction" explode={explode} xray={xray} focus={focus} onFocus={onFocus}>
   <mesh position={[0,1.05,0]} scale={[1.55,.30,.45]}><boxGeometry/><Mat module="induction" xray={xray} selected={selected("induction")}/></mesh>
   {[-.72,.72].map(x=><mesh key={x} position={[x,.75,0]}><cylinderGeometry args={[.10,.10,.75,18]}/><meshBasicMaterial color="#5d8aa2" transparent opacity={xray?.45:1}/></mesh>)}
   <mesh position={[0,1.07,.52]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.25,.25,.45,24]}/><Mat module="induction" xray={xray} selected={selected("induction")}/></mesh>
  </Module>

  <Module name="lubrication" explode={explode} xray={xray} focus={focus} onFocus={onFocus}>
   <mesh position={[0,-.92,0]} scale={[1.05,.42,.82]}><boxGeometry/><Mat module="lubrication" xray={xray} selected={selected("lubrication")}/></mesh>
   <mesh position={[1.05,-.83,-.72]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.32,.32,.64,24]}/><Mat module="lubrication" xray={xray} selected={selected("lubrication")}/></mesh>
   <mesh position={[.62,-.72,-.55]} rotation={[0,0,.35]}><cylinderGeometry args={[.055,.055,1.35,12]}/><meshBasicMaterial color="#1d9bcb" transparent opacity={xray?.35:.85}/></mesh>
  </Module>

  <Module name="exhaust" explode={explode} xray={xray} focus={focus} onFocus={onFocus}>
   {[-.62,.62].flatMap(z=>[-1,1].map(side=><group key={`${z}-${side}`} position={[side*1.9,-.45,z]}>
    <mesh rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.10,.12,1.15,16]}/><Mat module="exhaust" xray={xray} selected={selected("exhaust")}/></mesh>
   </group>))}
   <mesh position={[0,-.48,-1.16]} rotation={[Math.PI/2,0,0]}><torusGeometry args={[.54,.13,16,48,Math.PI*1.65]}/><Mat module="exhaust" xray={xray} selected={selected("exhaust")}/></mesh>
  </Module>

  <Module name="electrical" explode={explode} xray={xray} focus={focus} onFocus={onFocus}>
   <mesh position={[-.72,.56,-.88]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.31,.31,.62,24]}/><Mat module="electrical" xray={xray} selected={selected("electrical")}/></mesh>
   <mesh position={[-.72,.56,-1.23]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.10,.10,.18,18]}/><meshBasicMaterial color="#3a708b" transparent opacity={xray?.4:1}/></mesh>
  </Module>
 </group>;
}

function TechFloor(){return <group position={[0,-1.85,0]} rotation={[-Math.PI/2,0,0]}>{[1.6,2.4,3.2,4.0,4.8].map(r=><mesh key={r}><ringGeometry args={[r-.009,r+.009,112]}/><meshBasicMaterial color="#69bee9" transparent opacity={.18} toneMapped={false}/></mesh>)}</group>}
function SceneSetup(){const{gl}=useThree();useEffect(()=>{gl.outputColorSpace=THREE.SRGBColorSpace;gl.toneMapping=THREE.NoToneMapping;gl.setClearColor("#f9fcff",1)},[gl]);return <><color attach="background" args={["#f9fcff"]}/><TechFloor/></>}
function CameraRig({zoom=1,resetToken=0}:{zoom?:number;resetToken?:number}){const{camera}=useThree();useEffect(()=>{camera.position.copy(new THREE.Vector3(7.6,3.4,9.1).multiplyScalar(zoom));camera.lookAt(0,.02,0);camera.updateProjectionMatrix()},[camera,zoom,resetToken]);return null}

export default function EngineTwin({compact=false,explode=false,xray=false,focus="all",autoRotate=false,zoom=1,resetToken=0,onFocus}:Props){
 if(typeof document!=="undefined"&&!supportsWebGL())return <div className="webgl-fallback"><strong>3D Aero-Piston Engine Viewer</strong><span>WebGL is unavailable. Enable hardware acceleration and reload.</span></div>;
 return <Canvas dpr={[1,1.45]} camera={{position:[7.6,3.4,9.1],fov:29,near:.1,far:100}} gl={{antialias:true,alpha:false,powerPreference:"default",preserveDrawingBuffer:false}}>
  <SceneSetup/><CameraRig zoom={zoom} resetToken={resetToken}/>
  <AeroPistonEngine compact={compact} explode={explode} xray={xray} focus={focus} onFocus={onFocus}/>
  <OrbitControls makeDefault enableDamping dampingFactor={.06} minDistance={5.7} maxDistance={16} target={[0,.02,0]} autoRotate={autoRotate} autoRotateSpeed={.55}/>
 </Canvas>;
}
