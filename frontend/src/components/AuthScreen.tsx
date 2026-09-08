import { useState } from "react";
import type { FormEvent } from "react";
import {
  Activity,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";
import { signIn, signUp } from "../services/authApi";
import { useAuthStore } from "../store/authStore";
import { isHostedDemo } from "../demo/demoRuntime";

export default function AuthScreen({
  initialMode = "signin",
  onClose,
}: {
  initialMode?: "signin" | "signup";
  onClose?: () => void;
}) {
  const demo = isHostedDemo();
  const setSession = useAuthStore((s) => s.setSession),
    [mode, setMode] = useState<"signin" | "signup">(initialMode),
    [name, setName] = useState(""),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [show, setShow] = useState(false),
    [loading, setLoading] = useState(false),
    [error, setError] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const r = mode === "signup" ? await signUp(name, email, password) : await signIn(email, password);
      setSession(r.token, r.user);
      onClose?.();
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Could not authenticate. Check your details and try again.",
      );
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="auth-shell">
      {onClose && (
        <button className="auth-close" aria-label="Close account dialog" onClick={onClose}>
          <X />
        </button>
      )}
      <div className="auth-orbit auth-orbit-a" />
      <div className="auth-orbit auth-orbit-b" />
      <section className="auth-story">
        <div className="auth-brand">
          <img src="/assets/twinguard-mark.svg" alt="" />
          <strong>
            TwinGuard <span>Aero</span>
          </strong>
        </div>
        <div className="auth-story-copy">
          <span className="auth-kicker">AI-ENABLED DIGITAL TWIN</span>
          <h1>Mission intelligence for the engine that cannot fail.</h1>
          <p>
            Live engine telemetry, physics residuals, anomaly detection, mission-aware RUL, predictive
            maintenance and 3D system context in one operator platform.
          </p>
        </div>
        <div className="auth-feature-grid">
          <div>
            <Activity />
            <b>Live Digital Twin</b>
            <span>Telemetry and physics synchronized in real time.</span>
          </div>
          <div>
            <ShieldCheck />
            <b>Decision Support</b>
            <span>Health, RUL, mission readiness and maintenance.</span>
          </div>
        </div>
        <div className="auth-footnote">
          Engineering demonstrator · Engine-specific calibration required for operational use.
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-card-head">
            <div className="auth-mini-mark">
              <LockKeyhole />
            </div>
            <span>{demo ? "LOCAL DEMO PROFILE" : "OPERATOR ACCESS"}</span>
            <h2>{mode === "signin" ? "Welcome back" : "Create operator account"}</h2>
            <p>
              {mode === "signin"
                ? "Sign in to save your TwinGuard workspace."
                : demo
                  ? "Create a local demo profile stored on this device."
                  : "Create an authenticated operator account."}
            </p>
          </div>
          <div className="auth-tabs">
            <button
              type="button"
              className={mode === "signin" ? "active" : ""}
              onClick={() => {
                setMode("signin");
                setError("");
              }}
            >
              Sign in
            </button>
            <button
              type="button"
              className={mode === "signup" ? "active" : ""}
              onClick={() => {
                setMode("signup");
                setError("");
              }}
            >
              Create account
            </button>
          </div>
          <form onSubmit={submit}>
            {mode === "signup" && (
              <label>
                <span>Full name</span>
                <div>
                  <UserRound />
                  <input
                    required
                    minLength={2}
                    maxLength={120}
                    autoComplete="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Systems Operator"
                  />
                </div>
              </label>
            )}
            <label>
              <span>Email</span>
              <div>
                <Mail />
                <input
                  required
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="operator@example.com"
                />
              </div>
            </label>
            <label>
              <span>Password</span>
              <div>
                <LockKeyhole />
                <input
                  required
                  minLength={mode === "signup" ? 10 : 1}
                  type={show ? "text" : "password"}
                  autoComplete={mode === "signup" ? "new-password" : "current-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "signup" ? "10+ characters" : "Your password"}
                />
                <button
                  type="button"
                  className="auth-eye"
                  aria-label={show ? "Hide password" : "Show password"}
                  onClick={() => setShow((v) => !v)}
                >
                  {show ? <EyeOff /> : <Eye />}
                </button>
              </div>
            </label>
            {mode === "signup" && (
              <small className="password-hint">
                Use 10+ characters with uppercase, lowercase and a number.
              </small>
            )}
            {error && <div className="auth-error">{error}</div>}
            <button className="auth-submit" disabled={loading}>
              {loading ? "Please wait…" : mode === "signin" ? "Sign in" : "Create account"}
              <ArrowRight />
            </button>
          </form>
          <div className="auth-security">
            <ShieldCheck />
            <span>
              {demo
                ? "This local demo profile is device-specific and is not a production identity."
                : "Your operator session is authenticated by the TwinGuard backend."}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
