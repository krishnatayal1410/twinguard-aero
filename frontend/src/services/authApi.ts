import { apiBase, isDemo } from "./runtimeConfig";
import axios from "axios";
import type { AuthResponse, AuthUser } from "../types/twin";

export const AUTH_KEY = "twinguard_session";
const DEMO_ACCOUNTS = "twinguard_demo_accounts";

type DemoAccount = AuthUser & { passwordHash: string; passwordSalt?: string };

export function isAuthUser(value: unknown): value is AuthUser {
  if (!value || typeof value !== "object") return false;
  const user = value as Partial<AuthUser>;
  return (
    Number.isSafeInteger(user.id) &&
    typeof user.name === "string" &&
    user.name.trim().length >= 2 &&
    typeof user.email === "string" &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(user.email) &&
    typeof user.role === "string"
  );
}

export function readStoredSession(): AuthResponse | null {
  try {
    const saved = JSON.parse(localStorage.getItem(AUTH_KEY) || "null");
    return typeof saved?.token === "string" && saved.token.length > 0 && isAuthUser(saved.user)
      ? { token: saved.token, user: saved.user }
      : null;
  } catch {
    return null;
  }
}

export function storedToken() {
  return readStoredSession()?.token;
}

const authHttp = axios.create({
  baseURL: apiBase,
  timeout: 6000,
  headers: { "X-Requested-With": "TwinGuard-Aero" },
});
const hostedDemo = isDemo;

function accounts(): DemoAccount[] {
  try {
    const saved = JSON.parse(localStorage.getItem(DEMO_ACCOUNTS) || "[]");
    return Array.isArray(saved)
      ? saved.filter(
          (account: Partial<DemoAccount>): account is DemoAccount =>
            typeof account?.passwordHash === "string" &&
            /^[0-9a-f]{64}$/.test(account.passwordHash) &&
            (account.passwordSalt === undefined || /^[0-9a-f]{32}$/.test(account.passwordSalt)) &&
            isAuthUser(account),
        )
      : [];
  } catch {
    return [];
  }
}

function validateCredentials(email: string, password: string, name?: string) {
  if (email.length > 255 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    throw new Error("Enter a valid email address.");
  if (!password.length || password.length > 128)
    throw new Error("Password must contain between 1 and 128 characters.");
  if (name === undefined) return;
  if (name.length < 2 || name.length > 120)
    throw new Error("Full name must contain between 2 and 120 characters.");
  if (password.length < 10) throw new Error("Password must be at least 10 characters.");
  if (!/[A-Z]/.test(password)) throw new Error("Password needs an uppercase letter.");
  if (!/[a-z]/.test(password)) throw new Error("Password needs a lowercase letter.");
  if (!/\d/.test(password)) throw new Error("Password needs a number.");
}

function secureCrypto() {
  if (!globalThis.crypto?.subtle)
    throw new Error("Local profiles require HTTPS or localhost. Open the secure TwinGuard deployment.");
  return globalThis.crypto;
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
  return toHex(await secureCrypto().subtle.digest("SHA-256", new TextEncoder().encode(value)));
}

async function derivePassword(password: string, salt: string) {
  const crypto = secureCrypto();
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
  name = name.trim();
  email = email.trim().toLowerCase();
  validateCredentials(email, password, name);
  if (!hostedDemo())
    return (await authHttp.post<AuthResponse>("/auth/signup", { name, email, password })).data;
  const passwordSalt = toHex(secureCrypto().getRandomValues(new Uint8Array(16)).buffer);
  const passwordHash = await derivePassword(password, passwordSalt);
  // Read after derivation so concurrent submissions in this tab cannot overwrite
  // an account created while Web Crypto was working.
  const saved = accounts();
  if (saved.some((account) => account.email.toLowerCase() === email))
    throw new Error("An account with this email already exists.");
  const id = saved.reduce((next, account) => Math.max(next, account.id + 1), Date.now());
  const user: AuthUser = { id, name, email, role: "demo_operator" };
  saved.push({ ...user, passwordSalt, passwordHash });
  try {
    localStorage.setItem(DEMO_ACCOUNTS, JSON.stringify(saved));
  } catch {
    throw new Error("Could not save this local profile. Enable browser storage or free space and try again.");
  }
  return { token: `demo:${user.id}:${email}`, user };
}

export async function signIn(email: string, password: string): Promise<AuthResponse> {
  email = email.trim().toLowerCase();
  validateCredentials(email, password);
  if (!hostedDemo()) return (await authHttp.post<AuthResponse>("/auth/signin", { email, password })).data;
  const user = accounts().find((account) => account.email.toLowerCase() === email);
  const passwordHash = user?.passwordSalt
    ? await derivePassword(password, user.passwordSalt)
    : await legacyDigest(password);
  if (!user || user.passwordHash !== passwordHash) throw new Error("Email or password is incorrect.");
  const { passwordHash: _passwordHash, passwordSalt: _passwordSalt, ...publicUser } = user;
  return { token: `demo:${user.id}:${user.email}`, user: publicUser };
}

export async function currentUser(token: string): Promise<AuthUser> {
  if (!hostedDemo())
    return (await authHttp.get<AuthUser>("/auth/me", { headers: { Authorization: `Bearer ${token}` } })).data;
  const [kind, rawId, ...emailParts] = token.split(":");
  const email = emailParts.join(":");
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
