from __future__ import annotations


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, float(value)))


class MissionEngine:
    """Mission-aware decision-support model for the synthetic TwinGuard POC.

    The output is a transparent engineering index, not a certified probability
    of mission success or an autonomous flight-release decision.
    """

    @staticmethod
    def label(value):
        return "HIGH" if value >= .90 else "MEDIUM" if value >= .55 else "LOW"

    def _components(self, state, duration, altitude, temperature, throttle):
        health = state["health"]
        overall = float(health["overall"])
        duration_n = clamp(duration / 12, 0, 1.7)
        altitude_n = clamp(altitude / 8000, 0, 1.5)
        heat_n = clamp((temperature - 15) / 35, 0, 1.5)
        load_n = clamp((throttle - 45) / 50, 0, 1.4)
        health_penalty = clamp((100 - overall) / 35, 0, 1.5)
        degradation_rate = max(0.0, -float(state.get("trends", {}).get("health_index_per_min", 0.0)))
        trend_penalty = clamp(degradation_rate / 20, 0, 1.4)
        persistence = float(state.get("ai", {}).get("anomaly_persistence_samples", 0))
        persistence_penalty = clamp(persistence / 25, 0, 1.2) if state["ai"].get("anomaly") else 0.0
        rul = max(.1, float(state["ai"]["rul_hours"]))
        rul_margin = rul / max(.25, duration)
        rul_penalty = clamp((2.5 - rul_margin) / 2.0, 0, 1.5)

        stress = clamp(
            .24 * duration_n
            + .18 * altitude_n
            + .15 * heat_n
            + .22 * load_n
            + .18 * health_penalty
            + .12 * trend_penalty
            + .10 * persistence_penalty
            + .22 * rul_penalty,
            0,
            1.7,
        )
        thermal = clamp(.34 * load_n + .29 * heat_n + .18 * altitude_n + .29 * (100 - health["thermal"]) / 40, 0, 1.7)
        mechanical = clamp(.38 * load_n + .20 * duration_n + .31 * (100 - health["mechanical"]) / 40 + .12 * trend_penalty, 0, 1.7)
        lubrication = clamp(.27 * load_n + .21 * duration_n + .39 * (100 - health["lubrication"]) / 40 + .15 * trend_penalty, 0, 1.7)
        combustion = clamp(.28 * load_n + .18 * altitude_n + .20 * heat_n + .36 * (100 - health.get("combustion", 100)) / 40, 0, 1.7)
        electrical = clamp(.24 * duration_n + .42 * (100 - health["electrical"]) / 40, 0, 1.7)
        return {
            "stress": stress,
            "thermal": thermal,
            "mechanical": mechanical,
            "lubrication": lubrication,
            "combustion": combustion,
            "electrical": electrical,
            "rul_margin": rul_margin,
            "degradation_rate": degradation_rate,
            "rul": rul,
        }

    def analyze(self, state, req):
        h = float(state["health"]["overall"])
        dur = float(req.duration_hours)
        alt = float(req.cruise_altitude_m)
        temp = float(req.ambient_temp_c)
        thr = float(req.average_throttle_pct)
        comp = self._components(state, dur, alt, temp, thr)

        max_risk = max(comp["stress"], comp["thermal"], comp["mechanical"], comp["lubrication"], comp["combustion"], comp["electrical"])
        loss = 2.2 + 7.5 * comp["stress"] + max(0, 100 - h) * .05 + min(10, comp["degradation_rate"] * .22)
        post_h = max(12.0, h - loss)
        rul_loss = dur * (1 + .75 * comp["stress"]) + 7 * max(0, comp["stress"] - .75) + .10 * (100 - h)
        post_r = max(0.0, comp["rul"] - rul_loss)

        if max_risk >= .95 or post_h < 67 or comp["rul_margin"] < 1.15 or post_r < dur * .25:
            risk = "HIGH"
            decision = "REPLAN / ENGINEERING REVIEW"
        elif max_risk >= .60 or post_h < 86 or comp["rul_margin"] < 2.0:
            risk = "MEDIUM"
            decision = "PROCEED WITH CAUTION IN SIMULATION"
        else:
            risk = "LOW"
            decision = "LOW-RISK POC PROFILE"

        risk_factors = []
        if comp["rul_margin"] < 2.0:
            risk_factors.append(f"RUL margin is {comp['rul_margin']:.2f}× planned mission duration")
        if comp["degradation_rate"] > 2:
            risk_factors.append(f"Health index is declining at {comp['degradation_rate']:.1f} points/min in the current trend window")
        for name in ("thermal", "mechanical", "lubrication", "combustion", "electrical"):
            if comp[name] >= .55:
                risk_factors.append(f"{name.title()} stress is {self.label(comp[name]).lower()}")
        if state["ai"].get("anomaly"):
            risk_factors.append(f"Active diagnostic condition: {state['ai'].get('probable_fault','unknown').replace('_',' ')}")
        if not risk_factors:
            risk_factors.append("No dominant mission-risk contributor in the current synthetic envelope")

        feasibility = clamp(100 - 46 * max_risk - max(0, 82 - post_h) * .55 - max(0, 1.8 - comp["rul_margin"]) * 14, 0, 100)

        alt2 = max(2500.0, alt - 800)
        dur2 = max(.5, dur * .82)
        thr2 = max(52.0, thr - 10)
        alternative = self._components(state, dur2, alt2, temp, thr2)
        alternative_max = max(alternative["stress"], alternative["thermal"], alternative["mechanical"], alternative["lubrication"], alternative["combustion"], alternative["electrical"])

        return {
            "overall_risk": risk,
            "decision": decision,
            "stress_index": comp["stress"],
            "thermal_risk": self.label(comp["thermal"]),
            "mechanical_risk": self.label(comp["mechanical"]),
            "lubrication_risk": self.label(comp["lubrication"]),
            "combustion_risk": self.label(comp["combustion"]),
            "electrical_risk": self.label(comp["electrical"]),
            "current_health": h,
            "post_mission_health": post_h,
            "current_rul_hours": comp["rul"],
            "post_mission_rul_hours": post_r,
            "rul_margin_ratio": comp["rul_margin"],
            "mission_feasibility_index": feasibility,
            "risk_factors": risk_factors,
            "lower_stress_alternative": {
                "cruise_altitude_m": alt2,
                "duration_hours": round(dur2, 2),
                "average_throttle_pct": thr2,
                "projected_stress_index": alternative["stress"],
                "projected_risk": self.label(alternative_max),
            },
            "explanation": "Mission assessment combines the current synchronized Twin state, subsystem health, temporal degradation, simulation-derived RUL margin, planned duration, altitude, ambient temperature and average load.",
            "validation_scope": "SYNTHETIC_DECISION_SUPPORT_INDEX_NOT_CERTIFIED_PROBABILITY",
        }
