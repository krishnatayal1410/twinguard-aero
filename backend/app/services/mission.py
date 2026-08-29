from __future__ import annotations
def c(v,a=0,b=1): return max(a,min(b,v))
class MissionEngine:
    def analyze(self,state,req):
        h=state["health"]["overall"]; rul=state["ai"]["rul_hours"]
        dur=req.duration_hours; alt=req.cruise_altitude_m; temp=req.ambient_temp_c; thr=req.average_throttle_pct
        duration=c(dur/12,0,1.7); altitude=c(alt/8000,0,1.5); heat=c((temp-15)/35,0,1.5); load=c((thr-45)/50,0,1.4)
        current_penalty=c((100-h)/35,0,1.5)
        fault_penalty=.23 if state["ai"]["anomaly"] else 0
        stress=c(.28*duration+.23*altitude+.18*heat+.25*load+.23*current_penalty+fault_penalty,0,1.7)
        thermal=c(.35*load+.32*heat+.21*altitude+.22*(100-state["health"]["thermal"])/40,0,1.7)
        mech=c(.4*load+.23*duration+.30*(100-state["health"]["mechanical"])/40,0,1.7)
        lube=c(.28*load+.24*duration+.38*(100-state["health"]["lubrication"])/40,0,1.7)
        loss=3.0+8.5*stress+max(0,100-h)*.055
        post_h=max(15,h-loss)
        rul_loss=dur*(1+.85*stress)+9*max(0,stress-.75)+(.12*(100-h))
        post_r=max(0,rul-rul_loss)
        maxrisk=max(stress,thermal,mech,lube)
        risk="HIGH" if maxrisk>=.95 or post_h<68 or post_r<25 else "MEDIUM" if maxrisk>=.62 or post_h<86 else "LOW"
        decision="NO_GO / REPLAN" if risk=="HIGH" else "PROCEED_WITH_CAUTION" if risk=="MEDIUM" else "PROCEED"
        alt2=max(2500,alt-1000); dur2=max(2,dur-2); thr2=max(52,thr-10)
        return {
          "overall_risk":risk,"decision":decision,"stress_index":stress,
          "thermal_risk":self.label(thermal),"mechanical_risk":self.label(mech),"lubrication_risk":self.label(lube),
          "current_health":h,"post_mission_health":post_h,"current_rul_hours":rul,"post_mission_rul_hours":post_r,
          "lower_stress_alternative":{"cruise_altitude_m":alt2,"duration_hours":dur2,"average_throttle_pct":thr2},
          "explanation":"Mission prediction is conditioned on the current Digital Twin state, mission duration, altitude, ambient temperature and average load."
        }
    def label(self,x): return "HIGH" if x>=.9 else "MEDIUM" if x>=.55 else "LOW"
