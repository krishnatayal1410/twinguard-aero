import{useEffect}from"react";
import type{ReactNode}from"react";
import{currentUser}from"../services/authApi";
import{useAuthStore}from"../store/authStore";
import AuthScreen from"./AuthScreen";
export default function AuthGate({children}:{children:ReactNode}){
 const token=useAuthStore(s=>s.token),user=useAuthStore(s=>s.user),ready=useAuthStore(s=>s.ready),setSession=useAuthStore(s=>s.setSession),clear=useAuthStore(s=>s.clear),setReady=useAuthStore(s=>s.setReady);
 useEffect(()=>{let live=true;(async()=>{if(!token){if(live)setReady(true);return}try{const u=await currentUser(token);if(live)setSession(token,u)}catch{if(live)clear()}})();return()=>{live=false}},[token,setSession,clear,setReady]);
 if(!ready)return <div className="auth-loading"><img src="/assets/twinguard-mark.svg" alt=""/><strong>TwinGuard Aero</strong><span>Securing operator session…</span></div>;
 if(!token||!user)return <AuthScreen/>;
 return <>{children}</>
}