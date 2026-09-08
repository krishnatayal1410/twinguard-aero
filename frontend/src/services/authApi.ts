import axios from "axios";
import type { AuthResponse, AuthUser } from "../types/twin";

export const AUTH_KEY = "twinguard_session";
const DEMO_ACCOUNTS = "twinguard_demo_accounts";

type DemoAccount = AuthUser & { passwordHash: string; passwordSalt?: string };

export function storedToken() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_KEY) || "null")?.token as string | undefined;
  } catch {
    return undefined;
  }
}

const authHttp = axios.create({
  baseURL: "/api/v1",
  timeout: 6000,
  headers: { "X-Requested-With": "TwinGuard-Aero" },
});
const hostedDemo = () =>
  typeof window !== "undefined" &&
  (import.meta.env.VITE_TWINGUARD_DEMO_MODE === "1" || window.location.hostname.endsWith(".vercel.app"));

function accounts(): DemoAccount[] {
  try {
    return JSON.parse(localStorage.getItem(DEMO_ACCOUNTS) || "[]") as DemoAccount[];
  } catch {
    return [];
  }
}

function toHex(value: ArrayBuffer) {
  return Array.from(new Uint8Array(value))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function fromHex(value: string) {
  return Uint8Array.from(value.match(/.{2}/g) ?? [], (byte) => Number.parseInt(byte, 16));
}

async function legacyDigest(value: string) {
  return toHex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
}

async function derivePassword(password: string, salt: string) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, [
    "deriveBits",
  ]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt: fromHex(salt), iterations: 120_000 },
    key,
    256,
  );
  return toHex(bits);
}

export async function signUp(name: string, email: string, password: string): Promise<AuthResponse> {
  if (!hostedDemo())
    return (await authHttp.post<AuthResponse>("/auth/signup", { name, email, password })).data;
  const normalized = email.trim().toLowerCase();
  const saved = accounts();
  if (saved.some((account) => account.email === normalized))
    throw { response: { data: { detail: "An account with this email already exists." } } };
  const user: AuthUser = { id: Date.now(), name: name.trim(), email: normalized, role: "demo_operator" };
  const passwordSalt = toHex(crypto.getRandomValues(new Uint8Array(16)).buffer);
  saved.push({ ...user, passwordSalt, passwordHash: await derivePassword(password, passwordSalt) });
  localStorage.setItem(DEMO_ACCOUNTS, JSON.stringify(saved));
  return { token: `demo:${user.id}:${normalized}`, user };
}

export async function signIn(email: string, password: string): Promise<AuthResponse> {
  if (!hostedDemo()) return (await authHttp.post<AuthResponse>("/auth/signin", { email, password })).data;
  const normalized = email.trim().toLowerCase();
  const user = accounts().find((account) => account.email === normalized);
  const passwordHash = user?.passwordSalt
    ? await derivePassword(password, user.passwordSalt)
    : await legacyDigest(password);
  if (!user || user.passwordHash !== passwordHash)
    throw { response: { data: { detail: "Email or password is incorrect." } } };
  const { passwordHash: _passwordHash, passwordSalt: _passwordSalt, ...publicUser } = user;
  return { token: `demo:${user.id}:${normalized}`, user: publicUser };
}

export async function currentUser(token: string): Promise<AuthUser> {
  if (!hostedDemo())
    return (await authHttp.get<AuthUser>("/auth/me", { headers: { Authorization: `Bearer ${token}` } })).data;
  const [kind, rawId, email] = token.split(":");
  if (kind !== "demo") throw new Error("Invalid demo session");
  const id = Number(rawId);
  const user = accounts().find((account) => account.id === id);
  if (!user || user.email !== email) throw new Error("Demo account not found");
  const { passwordHash: _passwordHash, passwordSalt: _passwordSalt, ...publicUser } = user;
  return publicUser;
}

export async function signOut(token?: string) {
  if (!token || hostedDemo()) return;
  try {
    await authHttp.post("/auth/signout", {}, { headers: { Authorization: `Bearer ${token}` } });
  } catch {
    /* the local session is still cleared by the store */
  }
}
