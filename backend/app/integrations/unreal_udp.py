from __future__ import annotations
import json,socket
from ..core import settings
def send_to_unreal(state):
    if not settings.unreal_udp_enabled:return
    try:
        payload=json.dumps(state,separators=(",",":")).encode()
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.sendto(payload,(settings.unreal_udp_host,settings.unreal_udp_port));sock.close()
    except OSError: pass
