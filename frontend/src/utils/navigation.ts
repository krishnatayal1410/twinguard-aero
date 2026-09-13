import { useEffect, useState } from "react";
import type { ViewName } from "../types/twin";

export const viewPaths: Record<ViewName, string> = {
  command: "command",
  digitalTwin: "digital-twin",
  healthFaults: "health-faults",
  mission: "mission",
  replay: "replay",
  diagnostics: "diagnostics",
  maintenance: "maintenance",
  settings: "settings",
};
export function readRoute() {
  const [path, query = ""] = location.hash.replace(/^#\/?/, "").split("?");
  const view = (Object.keys(viewPaths) as ViewName[]).find((key) => viewPaths[key] === path) ?? "command";
  return { view, tab: new URLSearchParams(query).get("tab") };
}
export function pageHref(view: ViewName, tab?: string) {
  return `#/${viewPaths[view]}${tab ? `?tab=${encodeURIComponent(tab)}` : ""}`;
}
export function navigate(view: ViewName, tab?: string) {
  const hash = pageHref(view, tab);
  if (location.hash !== hash) location.hash = hash;
}
export function useRouteTab<T extends string>(view: ViewName, options: readonly T[], fallback: T) {
  const read = () => {
    const route = readRoute();
    return route.view === view && options.includes(route.tab as T) ? (route.tab as T) : fallback;
  };
  const [tab, setTab] = useState<T>(read);
  useEffect(() => {
    const sync = () => setTab(read());
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, [view, fallback]);
  const select = (value: T) => {
    setTab(value);
    navigate(view, value);
  };
  return [tab, select] as const;
}
