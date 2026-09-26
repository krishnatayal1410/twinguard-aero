"""Read-only CAN adapter. Vendor DBC and explicit signal/unit mapping are required."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from ..core import settings
from ..schemas import Telemetry

log = logging.getLogger("twinguard.can")
REQUIRED = {name for name, field in Telemetry.model_fields.items() if field.is_required()}


class SignalAssembler:
    def __init__(self, mapping, max_age_seconds=2.0):
        if max_age_seconds <= 0:
            raise ValueError("Signal freshness window must be positive")
        if not REQUIRED.issubset(mapping):
            raise ValueError(f"Missing canonical signals: {sorted(REQUIRED - mapping.keys())}")
        if set(mapping) - (Telemetry.model_fields.keys() - {"timestamp", "engine_id"}):
            raise ValueError("Mapping contains unknown telemetry fields")
        self.mapping = mapping
        self.max_age = max_age_seconds
        self.values = {}

    def update(self, decoded, now=None):
        now = time.monotonic() if now is None else now
        changed = False
        for canonical, spec in self.mapping.items():
            signal = spec["signal"]
            if signal in decoded:
                self.values[canonical] = (
                    float(decoded[signal]) * float(spec.get("scale", 1)) + float(spec.get("offset", 0)),
                    now,
                )
                changed = True
        if not changed or any(
            name not in self.values or now - self.values[name][1] > self.max_age for name in self.mapping
        ):
            return None
        values = {name: value for name, (value, _) in self.values.items()}
        return Telemetry.model_validate(
            dict(values, engine_id=settings.engine_id, timestamp=datetime.now(UTC))
        ).model_dump()


def run_can_bridge(channel, dbc_path, mapping, on_telemetry, interface="socketcan"):
    import can
    import cantools

    if not dbc_path or not on_telemetry:
        raise ValueError("DBC path and telemetry callback are required")
    db = cantools.database.load_file(dbc_path)
    assembler = SignalAssembler(mapping)
    with can.Bus(channel=channel, interface=interface, receive_own_messages=False) as bus:
        for message in bus:
            if message.is_error_frame or message.is_remote_frame:
                continue
            try:
                decoded = db.decode_message(message.arbitration_id, message.data, decode_choices=False)
                telemetry = assembler.update(decoded)
                if telemetry:
                    on_telemetry(telemetry)
            except (KeyError, TypeError, ValueError) as exc:
                log.warning("Rejected CAN frame 0x%x: %s", message.arbitration_id, type(exc).__name__)
