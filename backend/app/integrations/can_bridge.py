from __future__ import annotations
"""Configurable CAN/SocketCAN bridge.

Real engine CAN IDs and DBC definitions are intentionally NOT hard-coded.
Provide a vendor/test-rig DBC path and a channel through environment/config.
"""
def run_can_bridge(channel="vcan0", dbc_path=None, on_telemetry=None):
    try:
        import can, cantools
    except ImportError:
        raise RuntimeError("Install python-can and cantools to enable CAN integration")
    db=cantools.database.load_file(dbc_path) if dbc_path else None
    bus=can.interface.Bus(channel=channel,interface="socketcan")
    for msg in bus:
        if db is None: continue
        try:
            decoded=db.decode_message(msg.arbitration_id,msg.data)
            if on_telemetry:on_telemetry(decoded)
        except Exception:
            continue
