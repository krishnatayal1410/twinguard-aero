export function validateMission(payload: Record<string, unknown>): string | undefined {
  const types = ["endurance", "high_altitude", "hot_weather", "rapid_throttle", "patrol"];
  if (!types.includes(String(payload.mission_type))) return "Choose a supported mission profile.";
  const limits = [
    ["duration_hours", "Duration", 0.25, 48, "hours"],
    ["cruise_altitude_m", "Altitude", 0, 12000, "m"],
    ["ambient_temp_c", "Ambient temperature", -50, 70, "°C"],
    ["average_throttle_pct", "Throttle", 10, 100, "%"],
  ] as const;
  for (const [key, label, min, max, unit] of limits) {
    const value = payload[key];
    if (typeof value !== "number" || !Number.isFinite(value) || value < min || value > max)
      return `${label} must be between ${min} and ${max} ${unit}.`;
  }
}
