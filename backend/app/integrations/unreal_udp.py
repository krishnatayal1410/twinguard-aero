from __future__ import annotations

import json
import logging
import socket

from ..core import settings

log = logging.getLogger("twinguard.unreal")


def send_to_unreal(state):
    if not settings.unreal_udp_enabled:
        return
    try:
        payload = json.dumps(state, separators=(",", ":")).encode()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(payload, (settings.unreal_udp_host, settings.unreal_udp_port))
    except OSError as exc:
        log.warning("Unable to send Unreal UDP packet: %s", exc)
