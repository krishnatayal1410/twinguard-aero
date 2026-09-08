from __future__ import annotations

import json
import logging

from ..core import settings

log = logging.getLogger("twinguard.mqtt")


def start_mqtt(on_telemetry):
    if not settings.mqtt_enabled:
        return None
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        log.error("MQTT is enabled, but paho-mqtt is not installed")
        return None
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def connect(client, _userdata, _flags, reason_code, _properties=None):
        if reason_code == 0:
            client.subscribe(settings.mqtt_topic)
            log.info("Subscribed to MQTT topic %s", settings.mqtt_topic)
        else:
            log.error("MQTT connection rejected with reason %s", reason_code)

    def message(_client, _userdata, msg):
        try:
            on_telemetry(json.loads(msg.payload.decode()))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            log.warning("Rejected invalid MQTT telemetry: %s", exc)

    client.on_connect = connect
    client.on_message = message
    try:
        client.connect(settings.mqtt_host, settings.mqtt_port, 60)
    except OSError as exc:
        log.error("Unable to connect to MQTT broker: %s", exc)
        return None
    client.loop_start()
    return client


def stop_mqtt(client) -> None:
    if client is None:
        return
    client.loop_stop()
    client.disconnect()
