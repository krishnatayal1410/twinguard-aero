const configuredOrigin = (import.meta.env.VITE_TWINGUARD_API_ORIGIN || "").replace(/\/$/, "");
export const apiBase = `${configuredOrigin}/api/v1`;
export const isDemo = () =>
  typeof window !== "undefined" &&
  (import.meta.env.VITE_TWINGUARD_DEMO_MODE === "1" ||
    (import.meta.env.VITE_TWINGUARD_DEMO_MODE !== "0" &&
      !configuredOrigin &&
      window.location.hostname.endsWith(".vercel.app")));
export function twinSocketUrl(token: string) {
  const url = new URL(`${apiBase}/ws/twin/ENGINE-01`, window.location.origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.searchParams.set("token", token);
  return url.toString();
}
