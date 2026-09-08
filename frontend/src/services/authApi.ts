import axios from "axios";
import type { AuthResponse, AuthUser } from "../types/twin";

export const AUTH_KEY = "twinguard_session";
const DEMO_ACCOUNTS = "twinguard_demo_accounts";

type DemoAccount = AuthUser & { passwordHash: string };

export function storedToken() {
  try { return JSON.parse(localStorage.getItem(AUTH_KEY) || "null")?.token as string | undefined; }
  catch { return undefined; }
}

const authHttp = axios.create({ baseURL: "/api/v1", timeout: 6000, headers: { "X-Requested-With": "TwinGuard-Aero" } });
const hostedDemo = () => typeof window !== "undefined" && (import.meta.env.VITE_TWINGUARD_DEMO_MODE === "1" || window.location.hostname.endsWith(".vercel.app"));

function accounts(): DemoAccount[] {
  try { return JSON.parse(localStorage.getItem(DEMO_ACCOUNTS) || "[]") as DemoAccount[]; }
  catch { return []; }
}

async function digest(value: string) {
  const data = new TextEncoder().encode(value);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function signUp(name: string, email: string, password: string): Promise<AuthResponse> {
  if (!hostedDemo()) return (await authHttp.post<AuthResponse>("/auth/signup", { name, email, password })).data;
  const normalized = email.trim().toLowerCase();
  const saved = accounts();
  if (saved.some((account) => account.email === normalized)) throw { response: { data: { detail: "An account with this email already exists." } } };
  const user: AuthUser = { id: Date.now(), name: name.trim(), email: normalized, role: "demo_operator" };
  saved.push({ ...user, passwordHash: await digest(password) });
  localStorage.setItem(DEMO_ACCOUNTS, JSON.stringify(saved));
  return { token: `demo:${user.id}:${normalized}`, user };
}

export async function signIn(email: string, password: string): Promise<AuthResponse> {
  if (!hostedDemo()) return (await authHttp.post<AuthResponse>("/auth/signin", { email, password })).data;
  const normalized = email.trim().toLowerCase();
  const user = accounts().find((account) => account.email === normalized);
  if (!user || user.passwordHash !== await digest(password)) throw { response: { data: { detail: "Email or password is incorrect." } } };
  const { passwordHash: _passwordHash, ...publicUser } = user;
  return { token: `demo:${user.id}:${normalized}`, user: publicUser };
}

export async function currentUser(token: string): Promise<AuthUser> {
  if (!hostedDemo()) return (await authHttp.get<AuthUser>("/auth/me", { headers: { Authorization: `Bearer ${token}` } })).data;
  const id = Number(token.split(":")[1]);
  const user = accounts().find((account) => account.id === id);
  if (!user) throw new Error("Demo account not found");
  const { passwordHash: _passwordHash, ...publicUser } = user;
  return publicUser;
}

export async function signOut(token?: string) {
  if (!token || hostedDemo()) return;
  try { await authHttp.post("/auth/signout", {}, { headers: { Authorization: `Bearer ${token}` } }); }
  catch { /* the local session is still cleared by the store */ }
}
