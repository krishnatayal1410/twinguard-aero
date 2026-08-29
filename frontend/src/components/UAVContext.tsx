import{Canvas,useFrame}from"@react-three/fiber";
import{OrbitControls,useGLTF,useTexture}from"@react-three/drei";
import{Suspense,useEffect,useMemo,useRef}from"react";
import*as THREE from"three";import type{Group,Mesh}from"three";
import{supportsWebGL}from"../utils/webgl";

export function UAVModel({animate=true,scale=.78}:{animate?:boolean;scale?:number}){
 const{scene}=useGLTF("/assets/uav/uav.glb"),matcap=useTexture("/assets/materials/aerospace-matcap.png"),darkMatcap=useTexture("/assets/materials/aerospace-dark-matcap.png"),root=useMemo(()=>scene.clone(true),[scene]),group=useRef<Group>(null),props=useRef<Array<{mesh:Mesh;base:THREE.Vector3}>>([]),propAngle=useRef(0);
 useEffect(()=>{matcap.colorSpace=THREE.SRGBColorSpace;darkMatcap.colorSpace=THREE.SRGBColorSpace},[matcap,darkMatcap]);
 useEffect(()=>{props.current=[];root.traverse(o=>{if(!(o as Mesh).isMesh)return;const m=o as Mesh,n=m.name.toUpperCase();
   if(n.includes("GEAR_")||n.includes("WHEEL_")){m.visible=false;return}
   m.geometry.computeVertexNormals();
   const isGlow=n.includes("GLOW"),isDark=n.includes("PROP_")||n.includes("STRUT")||n.includes("SHAFT")||n.includes("ANTENNA");
   if(isGlow)m.material=new THREE.MeshBasicMaterial({color:"#168fe2",side:THREE.DoubleSide,toneMapped:false});
   else{const mat=new THREE.MeshMatcapMaterial({color:"#d9e5eb",matcap:isDark?darkMatcap:matcap,side:THREE.DoubleSide});if(n.includes("WING"))mat.color.set("#c9d9e3");if(n.includes("FUSELAGE")||n.includes("NOSE"))mat.color.set("#d8e4ea");if(n.includes("NACELLE")||n.includes("SERVICE"))mat.color.set("#aebfca");if(n.includes("LENS"))mat.color.set("#38a8d5");if(n.includes("PROP_"))mat.color.set("#52616c");m.material=mat}
   m.frustumCulled=false;if(n.includes("PROP_BLADE"))props.current.push({mesh:m,base:m.position.clone()})
  })},[root,matcap,darkMatcap]);
 useFrame((_,dt)=>{if(!animate)return;propAngle.current+=dt*9;const a=propAngle.current,co=Math.cos(a),si=Math.sin(a);for(const p of props.current){const y=p.base.y,z=p.base.z;p.mesh.position.y=y*co-z*si;p.mesh.position.z=y*si+z*co;p.mesh.rotation.x=a}if(group.current)group.current.rotation.y+=dt*.008});
 return <group ref={group} rotation={[.12,-.48,.035]} scale={scale}><primitive object={root}/></group>
}
function Airflow(){return <group>{Array.from({length:8},(_,i)=><mesh key={i} position={[0,-.48+i*.13,-1.55+i*.18]} rotation={[0,0,-.015]}><planeGeometry args={[5.4,.012]}/><meshBasicMaterial color="#59b9e9" transparent opacity={.13} toneMapped={false}/></mesh>)}</group>}
export default function UAVContext(){
 if(typeof document!=="undefined"&&!supportsWebGL())return <div className="webgl-fallback compact"><strong>UAV System View</strong><span>WebGL unavailable.</span></div>;
 return <Canvas dpr={[1,1.35]} camera={{position:[6.5,3.5,8.0],fov:31,near:.1,far:80}} gl={{antialias:true,powerPreference:"default",preserveDrawingBuffer:false}}>
  <color attach="background" args={["#f9fcff"]}/><Suspense fallback={null}><UAVModel animate scale={.82}/><Airflow/></Suspense>
  <gridHelper args={[9,18,0xd8e8f1,0xf0f6f9]} position={[0,-1.45,0]}/>
  <OrbitControls enablePan={false} minDistance={5.4} maxDistance={10} target={[0,.08,0]} enableDamping dampingFactor={.07}/>
 </Canvas>
}
useGLTF.preload("/assets/uav/uav.glb");
