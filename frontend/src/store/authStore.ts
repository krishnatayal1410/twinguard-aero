import{create}from"zustand";
import type{AuthUser}from"../types/twin";
import{AUTH_KEY}from"../services/authApi";
interface State{token?:string;user?:AuthUser;ready:boolean;setSession:(token:string,user:AuthUser)=>void;clear:()=>void;setReady:(v:boolean)=>void}
function load(){try{return JSON.parse(localStorage.getItem(AUTH_KEY)||"null")as{token?:string;user?:AuthUser}|null}catch{return null}}
const cached=typeof localStorage==="undefined"?null:load();
export const useAuthStore=create<State>(set=>({
 token:cached?.token,user:cached?.user,ready:false,
 setSession:(token,user)=>{localStorage.setItem(AUTH_KEY,JSON.stringify({token,user}));set({token,user,ready:true})},
 clear:()=>{localStorage.removeItem(AUTH_KEY);set({token:undefined,user:undefined,ready:true})},
 setReady:ready=>set({ready})
}));
