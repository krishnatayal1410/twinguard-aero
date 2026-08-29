from __future__ import annotations
import json,threading
from ..core import settings
def start_mqtt(on_telemetry):
    if not settings.mqtt_enabled:return None
    try: import paho.mqtt.client as mqtt
    except ImportError:return None
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    def connect(c,u,f,rc,p=None): c.subscribe(settings.mqtt_topic)
    def message(c,u,msg):
        try:on_telemetry(json.loads(msg.payload.decode()))
        except Exception:pass
    client.on_connect=connect;client.on_message=message;client.connect(settings.mqtt_host,settings.mqtt_port,60)
    threading.Thread(target=client.loop_forever,daemon=True).start();return client
