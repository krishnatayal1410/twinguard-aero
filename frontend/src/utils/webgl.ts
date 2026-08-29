let cached:boolean|undefined;
export function supportsWebGL(){
 if(cached!==undefined)return cached;
 try{
  const c=document.createElement("canvas");
  const gl=c.getContext("webgl2",{failIfMajorPerformanceCaveat:false})||c.getContext("webgl",{failIfMajorPerformanceCaveat:false});
  cached=!!gl;
  const ext=(gl as WebGLRenderingContext|null)?.getExtension?.("WEBGL_lose_context");
  ext?.loseContext?.();
  return cached;
 }catch{return cached=false}
}