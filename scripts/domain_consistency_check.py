from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "backend", ROOT / "frontend" / "src", ROOT / "simulator", ROOT / "ai"]
TEXT_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".json"}

FORBIDDEN = {
    "turbine_blade_degradation": "SIH26054 runtime taxonomy must stay aero-piston specific",
    "UAV Turboshaft Engine": "operator HMI must not identify the monitored asset as a turboshaft",
    "98.6%": "do not reintroduce the old hard-coded mission success claim",
    "120.4 kg": "do not reintroduce the old hard-coded mission fuel-burn claim",
}


def iter_files():
    for base in TARGETS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and "node_modules" not in path.parts:
                yield path


def main():
    failures = []
    checked = 0
    for path in iter_files():
        checked += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for needle, reason in FORBIDDEN.items():
            if needle in text:
                failures.append(f"{path.relative_to(ROOT)} contains {needle!r}: {reason}")

    if failures:
        print("TwinGuard domain consistency: FAIL")
        for failure in failures:
            print(" -", failure)
        raise SystemExit(1)

    print(f"TwinGuard domain consistency: PASS ({checked} source files checked)")
    print("Runtime remains aligned to SIH26054 aero-piston scope and no banned hard-coded mission claims were found.")


if __name__ == "__main__":
    main()
