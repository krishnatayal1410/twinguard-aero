"""Read vendor-defined CAN telemetry and post it to the authenticated live API."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import httpx
from app.integrations.can_bridge import run_can_bridge


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dbc", required=True)
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--interface", default="socketcan")
    args = parser.parse_args()
    key = os.environ["TWINGUARD_INGEST_KEY"]
    api = os.environ.get("TWINGUARD_API", "http://127.0.0.1:8000").rstrip("/")
    if not api.startswith("https://") and not api.startswith(("http://127.0.0.1:", "http://localhost:")):
        raise SystemExit("Remote gateways require HTTPS")
    with httpx.Client(timeout=5, headers={"X-TwinGuard-Ingest-Key": key}) as client:

        def publish(sample):
            sample["timestamp"] = sample["timestamp"].isoformat()
            client.post(f"{api}/api/v1/telemetry", json=sample).raise_for_status()

        run_can_bridge(args.channel, args.dbc, json.loads(args.mapping.read_text()), publish, args.interface)


if __name__ == "__main__":
    main()
