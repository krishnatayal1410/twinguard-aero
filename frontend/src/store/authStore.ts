import { create } from "zustand";
import type { AuthUser } from "../types/twin";
import { AUTH_KEY, readStoredSession } from "../services/authApi";
interface State {
  token?: string;
  user?: AuthUser;
  ready: boolean;
  setSession: (token: string, user: AuthUser) => void;
  clear: () => void;
  setReady: (v: boolean) => void;
}
const cached = readStoredSession();
export const useAuthStore = create<State>((set) => ({
  token: cached?.token,
  user: cached?.user,
  ready: false,
  setSession: (token, user) => {
    try {
      localStorage.setItem(AUTH_KEY, JSON.stringify({ token, user }));
    } catch {
      throw new Error("Could not save your session. Enable browser storage or free space and try again.");
    }
    set({ token, user, ready: true });
  },
  clear: () => {
    try {
      localStorage.removeItem(AUTH_KEY);
    } catch {
      /* Sign-out still clears the in-memory session if storage is unavailable. */
    }
    set({ token: undefined, user: undefined, ready: true });
  },
  setReady: (ready) => set({ ready }),
}));
