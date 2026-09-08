import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Command Center" })).toBeVisible();
});

test("all primary screens are reachable", async ({ page }) => {
  const pages = [
    ["Digital Twin", "Digital Twin"],
    ["Health & Faults", "Health & Faults"],
    ["Mission Lab", "Mission Lab"],
    ["Replay", "Mission Replay"],
    ["Diagnostics", "Diagnostics & Explainability"],
    ["Maintenance", "Predictive Maintenance"],
    ["Settings", "Settings & System"],
    ["Command Center", "Command Center"],
  ] as const;
  for (const [button, heading] of pages) {
    await page.getByRole("button", { name: button, exact: true }).click();
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
  }
});

test("command center mode toggle and navigation work", async ({ page }) => {
  await page.getByRole("button", { name: "Locate fault" }).click();
  await expect(page.getByText("FAULT LOCATION", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "X-ray", exact: true })).toHaveClass(/active/);
  await page.getByRole("button", { name: "Digital Twin", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Digital Twin", exact: true })).toBeVisible();
});

test("mission analysis and lower-stress rerun are functional", async ({ page }) => {
  await page.getByRole("button", { name: "Mission Lab", exact: true }).click();
  await page.getByRole("button", { name: "Run Mission Analysis" }).click();
  await expect(page.getByText("Mission Risk", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Mission Margin", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Apply Alternative & Re-run" }).first().click();
  await expect(page.getByText("Mission Analysis Result", { exact: true })).toBeVisible();
});

test("diagnostic tabs expose real engineering values", async ({ page }) => {
  await page.getByRole("button", { name: "Diagnostics", exact: true }).click();
  await page.getByRole("button", { name: "Sensor Trust" }).click();
  await expect(page.getByText("Oil Pressure", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Data Quality" }).click();
  await expect(page.getByText("Telemetry age", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "System Status" }).click();
  await expect(page.getByText("ENGINE-01", { exact: true }).first()).toBeVisible();
});

test("simulator controls and exports are actionable", async ({ page }) => {
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page.getByRole("button", { name: "Simulator", exact: true }).click();
  await page.locator("select").first().selectOption("lubrication");
  await page.getByRole("button", { name: "Apply Scenario" }).click();
  await expect(page.getByText(/Lubrication applied at/i)).toBeVisible();
  await page.getByRole("button", { name: "Data Management", exact: true }).click();
  await expect(page.getByRole("button", { name: /Export Telemetry/ })).toBeEnabled();
  await expect(page.getByRole("button", { name: /Export Full Twin State/ })).toBeEnabled();
});

test("persisted replay sample view loads and plays", async ({ page }) => {
  await page.getByRole("button", { name: "Replay", exact: true }).click();
  await expect(page.getByText("Persisted Telemetry Timeline", { exact: true })).toBeVisible();
  await expect(page.getByText(/Stored samples/)).toBeVisible();
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await page.waitForTimeout(600);
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await expect(page.getByText("Playback Engineering Snapshot", { exact: true })).toBeVisible();
});

test("maintenance page is no longer orphaned", async ({ page }) => {
  await page.getByRole("button", { name: "Maintenance", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Predictive Maintenance" })).toBeVisible();
  await expect(page.getByText("RUL Estimate", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /Evaluate next mission profile/ }).click();
  await expect(page.getByRole("heading", { name: "Mission Lab" })).toBeVisible();
});

test("hosted demo account can be created and opened", async ({ page }) => {
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await page.getByLabel("Full name").fill("Demo Operator");
  await page.getByLabel("Email").fill("demo.operator@example.com");
  await page.locator('input[type="password"]').fill("TwinGuard2026");
  await page.locator("form").getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("button", { name: /Demo Operator/ })).toBeVisible();
  await page.getByRole("button", { name: /Demo Operator/ }).click();
  await expect(page.getByText("demo.operator@example.com", { exact: true })).toBeVisible();
});
