from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"


def require(condition: bool, message: str):
    if not condition:
        raise SystemExit(f"RELEASE INTEGRITY FAIL: {message}")


package = json.loads((FRONTEND / "package.json").read_text())
core = (ROOT / "backend/app/core.py").read_text()
match = re.search(r'version:\s*str\s*=\s*"([^"]+)"', core)
require(bool(match), "backend version not found")
require(
    package["version"] == match.group(1),
    f"frontend/backend version mismatch: {package['version']} vs {match.group(1)}",
)

index = (FRONTEND / "index.html").read_text()
for needle in [
    '<meta name="description"',
    '<link rel="canonical"',
    "application/ld+json",
    "og:title",
    "twitter:card",
    "/manifest.webmanifest",
]:
    require(needle in index, f"missing SEO marker {needle}")

for path in [
    FRONTEND / "public/robots.txt",
    FRONTEND / "public/sitemap.xml",
    FRONTEND / "public/manifest.webmanifest",
]:
    require(path.exists(), f"missing SEO file {path.relative_to(ROOT)}")

app = (SRC / "App.tsx").read_text()
require(
    "MaintenanceDeck" in app and re.search(r'\[\s*"maintenance"\s*,\s*"Maintenance"', app) is not None,
    "Maintenance page is not routed",
)
require("ENGINE TG-001" not in app, "legacy engine identifier remains in App")
require('"Endurance Patrol"' not in app, "fake pre-analysis mission label remains in App")

api = (SRC / "services/twinApi.ts").read_text()
require(
    "getReplaySamples" in api and "/samples" in api,
    "persisted replay sample API is not wired",
)

demo = (SRC / "demo/demoRuntime.ts").read_text()
for key in [
    "oil_pressure_residual",
    "oil_temperature_residual",
    "cht_residual",
    "vibration_residual",
    "oil_pressure_per_min",
    "health_index_per_min",
]:
    require(key in demo, f"hosted demo missing canonical key {key}")
for legacy in ["oil_pressure_per_minute", "cht_per_minute", "health_per_minute"]:
    require(legacy not in demo, f"legacy hosted-demo trend key remains: {legacy}")

# Internal oil-pressure telemetry is in bar, while the UI converts rates to kPa/min.
# A -4.1 bar/min demo rate would render as -410 kPa/min, so guard the corrected scale.
require(
    re.search(r"-\s*4\.1\s*\*\s*progress", demo) is None,
    "hosted-demo oil-pressure trend is 100x too large",
)
require(
    re.search(r"-\s*0?\.041\s*\*\s*progress", demo) is not None,
    "hosted-demo oil-pressure trend unit guard is missing",
)

bad_patterns = [
    r"\br\.oil_pressure\b",
    r"\br\.oil_temperature\b",
    r"\br\.cht\b",
    r"\br\.egt\b",
    r"\br\.vibration\b",
    r"\br\[\"oil_pressure\"\]",
    r"\br\[\"cht\"\]",
]
for path in SRC.rglob("*.tsx"):
    text = path.read_text()
    for pattern in bad_patterns:
        require(
            not re.search(pattern, text),
            f"legacy residual access {pattern} in {path.relative_to(ROOT)}",
        )

for path in [
    ROOT / ".runtime/logs/backend.log",
    ROOT / ".runtime/logs/frontend.log",
    ROOT / ".runtime/logs/simulator.log",
]:
    require(
        not path.exists(),
        f"runtime log is tracked in release tree: {path.relative_to(ROOT)}",
    )

print(f"TwinGuard release integrity PASS — version {package['version']}")
