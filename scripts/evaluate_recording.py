"""Evaluate canonical CSV telemetry offline; never publish old samples as live data.

Requires explicit timestamps and ENGINE-01-compatible canonical units. Optional
fault_label and rul_hours_label columns enable evaluation against supplied labels.
No reference labels are inferred from model predictions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path


def evaluate(path: Path, source: str):
    # Isolate all pipeline writes from the user's operational database.
    with tempfile.TemporaryDirectory() as directory:
        os.environ["DATABASE_URL"] = f"sqlite:///{directory}/evaluation.db"
        from app.schemas import Telemetry
        from app.services.twin_manager import TwinManager

        twin = TwinManager()
        total = 0
        labeled = 0
        correct = 0
        errors = []
        confusion = {}
        previous = None
        with path.open(newline="") as file:
            for row_number, row in enumerate(csv.DictReader(file), 2):
                if not row.get("timestamp"):
                    raise ValueError(f"Row {row_number}: explicit timestamp required")
                sample = Telemetry.model_validate(
                    {k: v for k, v in row.items() if k in Telemetry.model_fields and v != ""}
                )
                if sample.timestamp.tzinfo is None or (previous and sample.timestamp <= previous):
                    raise ValueError(f"Row {row_number}: timestamps must be timezone-aware and increasing")
                if sample.engine_id != twin.replay.engine_id:
                    raise ValueError(f"Row {row_number}: wrong engine identity")
                previous = sample.timestamp
                state = twin.ingest(sample.model_dump())
                total += 1
                label = row.get("fault_label", "").strip()
                if label:
                    labeled += 1
                    predicted = state["ai"]["probable_fault"]
                    correct += predicted == label
                    key = f"{label} -> {predicted}"
                    confusion[key] = confusion.get(key, 0) + 1
                if row.get("rul_hours_label"):
                    truth = float(row["rul_hours_label"])
                    if not math.isfinite(truth) or truth < 0:
                        raise ValueError(f"Row {row_number}: invalid RUL reference label")
                    errors.append(float(state["ai"]["rul_hours"]) - truth)
        if not total:
            raise ValueError("Recording has no telemetry rows")
        return {
            "source": source,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "samples": total,
            "labeled_fault_samples": labeled,
            "fault_accuracy": correct / labeled if labeled else None,
            "confusion": confusion,
            "labeled_rul_samples": len(errors),
            "rul_mae_hours": sum(map(abs, errors)) / len(errors) if errors else None,
            "rul_rmse_hours": math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else None,
            "scope": "Offline evaluation of supplied recording; source and reference labels require independent verification. Does not establish airworthiness or mission-outcome accuracy.",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.recording, args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
