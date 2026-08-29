from __future__ import annotations
import argparse, math, os, random, time, json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

API=os.getenv("TWINGUARD_API","http://127.0.0.1:8000")
ENGINE=os.getenv("TWINGUARD_ENGINE_ID","ENGINE-01")

class EngineSimulator:
    def __init__(self):
        self.hours=42.0
        self.phase=0.0
    def config(self):
        try:
            with urlopen(API+"/api/v1/simulation/config",timeout=1.5) as r:
                return json.loads(r.read().decode())
        except Exception:
            return {"fault":"normal","severity":0.0}
    def sample(self):
        cfg=self.config();fault=cfg.get("fault","normal");s=float(cfg.get("severity",0))
        self.phase+=.08; self.hours+=1/3600
        throttle=70+5*math.sin(self.phase*.35)+random.gauss(0,1.4)
        altitude=4300+380*math.sin(self.phase*.12)+random.gauss(0,18)
        ambient=35+1.2*math.sin(self.phase*.08)+random.gauss(0,.25)
        rpm=4050+260*math.sin(self.phase*.55)+random.gauss(0,45)
        density=max(.58,1-altitude/21000)
        cht=ambient+105+58*(throttle/100)+.0048*(rpm-2500)+10*(1-density)+random.gauss(0,2.2)
        egt=500+250*(throttle/100)+.015*(rpm-2500)+16*(1-density)+random.gauss(0,7)
        oil_t=ambient+48+46*(throttle/100)+.002*(rpm-2500)+random.gauss(0,1.5)
        oil_p=3+.00046*rpm-.018*max(oil_t-85,0)+random.gauss(0,.045)
        fuel=5.2+.0022*rpm+7.2*(throttle/100)/density+random.gauss(0,.18)
        vib=.16+abs(rpm-3900)/11000+.07*(throttle/100)+random.gauss(0,.012)
        battery=27.6+.25*min(1,rpm/2500)+random.gauss(0,.06)
        if fault=="lubrication":
            oil_p-=1.45*s; oil_t+=25*s; vib+=.26*s
        elif fault=="overheating":
            cht+=45*s; egt+=66*s; oil_t+=17*s
        elif fault=="vibration":
            vib+=.78*s
        elif fault=="sensor_drift":
            oil_p+=.85*s + .25*s*math.sin(self.phase*.08)
        elif fault=="injector":
            fuel+=2.4*s; egt+=75*s
        elif fault=="misfire":
            rpm+=random.gauss(0,300*s);egt+=random.gauss(0,55*s);vib+=.3*s
        elif fault=="turbine_blade_degradation":
            rpm-=120*s; egt+=42*s; vib+=.46*s; fuel+=1.1*s
        return {
          "engine_id":ENGINE,"timestamp":datetime.now(timezone.utc).isoformat(),
          "rpm":rpm,"throttle":throttle,"cht":cht,"egt":egt,
          "oil_pressure":oil_p,"oil_temperature":oil_t,"fuel_flow":fuel,
          "vibration":max(.05,vib),"battery_voltage":battery,"alternator_voltage":28.1,
          "altitude":altitude,"ambient_temperature":ambient,
          "injection_timing":18+1.2*math.sin(self.phase*.15),"operating_hours":self.hours
        }

def post_json(url,data):
    payload=json.dumps(data).encode()
    headers={"Content-Type":"application/json"}
    if key:=os.getenv("TWINGUARD_INGEST_KEY"):headers["X-TwinGuard-Ingest-Key"]=key
    req=Request(url,data=payload,method="POST",headers=headers)
    with urlopen(req,timeout=2) as r:return json.loads(r.read().decode())

def run_http(rate):
    sim=EngineSimulator()
    print("TwinGuard simulator →",API)
    while True:
        try:
            state=post_json(API+"/api/v1/telemetry",sim.sample())
            print(f"\rhealth {state['health']['overall']:5.1f}% | {state['ai']['probable_fault']:<13} | RUL {state['ai']['rul_hours']:6.1f} h",end="",flush=True)
        except Exception as e:
            print("\nwaiting for backend:",e)
        time.sleep(1/rate)

def run_mqtt(rate):
    try: import paho.mqtt.client as mqtt
    except ImportError: raise SystemExit("Install paho-mqtt first")
    host=os.getenv("MQTT_HOST","127.0.0.1");port=int(os.getenv("MQTT_PORT","1883"))
    topic=f"twinguard/engine/{ENGINE}/telemetry"
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2);client.connect(host,port,60);client.loop_start()
    sim=EngineSimulator()
    while True:
        client.publish(topic,json.dumps(sim.sample()),qos=0);time.sleep(1/rate)

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--transport",choices=["http","mqtt"],default=os.getenv("SIM_TRANSPORT","http"));ap.add_argument("--rate",type=float,default=1.0);args=ap.parse_args()
    (run_mqtt if args.transport=="mqtt" else run_http)(args.rate)
