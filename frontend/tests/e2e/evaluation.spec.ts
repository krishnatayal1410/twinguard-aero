import { test, expect } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

test("evaluation evidence survives navigation and exports a verifiable payload", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/#/evaluation");
  await expect(page.getByRole("heading", { name: "Evaluation Center", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Apply selected fault", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Start healthy baseline", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Healthy baseline captured");
  await page.getByRole("button", { name: "Apply selected fault", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Lubrication applied at 65%");
  await page.getByRole("button", { name: "Capture observation", exact: true }).click();
  await expect(page.getByText("1 of 12 observations", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Mission Lab", exact: true }).click();
  await page.getByRole("button", { name: "Run Mission Analysis", exact: true }).click();
  await expect(page.getByText("Mission Analysis Result", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Evaluation Center", exact: true }).click();
  await expect(page.getByText("1 of 12 observations", { exact: false })).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export evidence", exact: true }).click();
  const download = await downloadPromise;
  const report = JSON.parse(await readFile((await download.path())!, "utf8"));
  expect(report.payload.problem_statement).toBe("SIH26054");
  expect(report.payload.baseline.twin.ai.probable_fault).toBe("normal");
  expect(report.payload.observations).toHaveLength(1);
  expect(report.payload.observations[0].injection.fault).toBe("lubrication");
  expect(report.payload.mission_runs).toHaveLength(1);
  expect(report.payload.telemetry_units.oil_pressure).toBe("bar");
  expect(report.integrity.sha256).toBe(
    createHash("sha256").update(JSON.stringify(report.payload)).digest("hex"),
  );
  await page.getByRole("button", { name: "Restart healthy baseline", exact: true }).click();
  const freshDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export evidence", exact: true }).click();
  const fresh = JSON.parse(await readFile((await (await freshDownload).path())!, "utf8"));
  expect(fresh.payload.mission_runs).toEqual([]);
  expect(fresh.payload.observations).toEqual([]);
  expect(fresh.payload.injection.fault).toBe("normal");
  expect(errors).toEqual([]);
});

for (const width of [390, 679, 1024, 1440]) {
  test(`evaluation navigation and content fit ${width}px viewport`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/#/evaluation");
    await expect(page.getByRole("heading", { name: "Evaluation Center", exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(
      true,
    );
    const nav = page.getByRole("navigation", { name: "Engineering", exact: true });
    await nav.getByRole("button", { name: "Settings", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Settings & System", exact: true })).toBeVisible();
    await nav.getByRole("button", { name: "Evaluation Center", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Evaluation Center", exact: true })).toBeVisible();
    await page.screenshot({ path: `test-results/evaluation-${width}.png`, fullPage: true });
  });
}

test("evidence captures the actual scenario after a change in Settings", async ({ page }) => {
  await page.goto("/#/evaluation");
  await page.getByRole("button", { name: "Start healthy baseline", exact: true }).click();
  await page.getByRole("button", { name: "Apply selected fault", exact: true }).click();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page.getByRole("button", { name: "Simulator", exact: true }).click();
  await page.locator("select").first().selectOption("alternator_degradation");
  await page.getByRole("button", { name: "Apply Scenario", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Alternator Degradation applied");
  await page.getByRole("button", { name: "Evaluation Center", exact: true }).click();
  await page.getByRole("button", { name: "Capture observation", exact: true }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export evidence", exact: true }).click();
  const report = JSON.parse(await readFile((await (await downloadPromise).path())!, "utf8"));
  expect(report.payload.injection.fault).toBe("alternator_degradation");
  expect(report.payload.observations[0].injection.fault).toBe("alternator_degradation");
  expect(report.payload.observations[0].label).toContain("Alternator Degradation");
});
