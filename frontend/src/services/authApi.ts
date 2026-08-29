import axios from"axios";
import type{AuthResponse,AuthUser}from"../types/twin";
export const AUTH_KEY="twinguard_session";
export function storedToken(){try{return JSON.parse(localStorage.getItem(AUTH_KEY)||"null")?.token as string|undefined}catch{return undefined}}
const authHttp=axios.create({baseURL:"/api/v1",timeout:6000,headers:{"X-Requested-With":"TwinGuard-Aero"}});
export async function signUp(name:string,email:string,password:string){return(await authHttp.post<AuthResponse>("/auth/signup",{name,email,password})).data}
export async function signIn(email:string,password:string){return(await authHttp.post<AuthResponse>("/auth/signin",{email,password})).data}
export async function currentUser(token:string){return(await authHttp.get<AuthUser>("/auth/me",{headers:{Authorization:`Bearer ${token}`}})).data}
export async function signOut(token?:string){if(!token)return;try{await authHttp.post("/auth/signout",{}, {headers:{Authorization:`Bearer ${token}`}})}catch{}}
