from __future__ import annotations

from typing import ClassVar


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, float(value)))


class MissionEngine:
    """Mission-aware decision-support model for the synthetic TwinGuard POC.

    Mission profile names are not decorative labels: each profile applies an
    explicit duty-cycle modifier to the transparent stress components below.
    These modifiers are proof-of-concept engineering assumptions and must be
    calibrated against authorized target-engine/test-rig mission data before
    operational use.
    """

    PROFILE_MODIFIERS: ClassVar[dict[str, dict[str, float | str]]] = {
        "endurance": {
            "stress": 0.05,
            "thermal": 0.01,
            "mechanical": 0.01,
            "lubrication": 0.05,
            "combustion": 0.01,
            "electrical": 0.04,
            "description": "Sustained load and long-duration lubrication/electrical exposure.",
        },
        "high_altitude": {
            "stress": 0.08,
            "thermal": 0.04,
            "mechanical": 0.02,
            "lubrication": 0.03,
            "combustion": 0.10,
            "electrical": 0.02,
            "description": "Reduced-density operation with stronger combustion/mixture sensitivity.",
        },
        "hot_weather": {
            "stress": 0.07,
            "thermal": 0.13,
            "mechanical": 0.01,
            "lubrication": 0.08,
            "combustion": 0.04,
            "electrical": 0.02,
            "description": "Higher cooling and oil-temperature burden in hot ambient conditions.",
        },
        "rapid_throttle": {
            "stress": 0.11,
            "thermal": 0.05,
            "mechanical": 0.12,
            "lubrication": 0.05,
            "combustion": 0.12,
            "electrical": 0.01,
            "description": "Transient load changes emphasize mechanical and combustion stress.",
        },
        "patrol": {
            "stress": 0.04,
            "thermal": 0.02,
            "mechanical": 0.05,
            "lubrication": 0.03,
            "combustion": 0.05,
            "electrical": 0.03,
            "description": "Variable-load patrol duty with moderate transient exposure.",
        },
    }

    @staticmethod
    def label(value):
        return "HIGH" if value >= 0.90 else "MEDIUM" if value >= 0.55 else "LOW"

    def _profile(self, mission_type):
        return self.PROFILE_MODIFIERS.get(str(mission_type), self.PROFILE_MODIFIERS["endurance"])

    def _components(self, state, duration, altitude, temperature, throttle, mission_type="endurance"):
        health = state["health"]
        overall = float(health["overall"])
        profile = self._profile(mission_type)
        duration_n = clamp(duration / 12, 0, 1.7)
        altitude_n = clamp(altitude / 8000, 0, 1.5)
        heat_n = clamp((temperature - 15) / 35, 0, 1.5)
        load_n = clamp((throttle - 45) / 50, 0, 1.4)
        health_penalty = clamp((100 - overall) / 35, 0, 1.5)
        degradation_rate = max(0.0, -float(state.get("trends", {}).get("health_index_per_min", 0.0)))
        trend_penalty = clamp(degradation_rate / 20, 0, 1.4)
        persistence = float(state.get("ai", {}).get("anomaly_persistence_samples", 0))
        persistence_penalty = clamp(persistence / 25, 0, 1.2) if state["ai"].get("anomaly") else 0.0

        rul = max(0.1, float(state["ai"]["rul_hours"]))
        interval = state.get("ai", {}).get("rul_interval_hours") or {}
        conservative_rul = max(0.1, float(interval.get("lower", rul * 0.75)))
        upper_rul = max(rul, float(interval.get("upper", rul * 1.25)))
        rul_margin = rul / max(0.25, duration)
        conservative_rul_margin = conservative_rul / max(0.25, duration)
        rul_penalty = clamp((2.4 - conservative_rul_margin) / 1.9, 0, 1.5)

        stress = clamp(
            0.24 * duration_n
            + 0.18 * altitude_n
            + 0.15 * heat_n
            + 0.22 * load_n
            + 0.18 * health_penalty
            + 0.12 * trend_penalty
            + 0.10 * persistence_penalty
            + 0.22 * rul_penalty
            + profile["stress"],
            0,
            1.7,
        )
        thermal = clamp(
            0.34 * load_n
            + 0.29 * heat_n
            + 0.18 * altitude_n
            + 0.29 * (100 - health["thermal"]) / 40
            + profile["thermal"],
            0,
            1.7,
        )
        mechanical = clamp(
            0.38 * load_n
            + 0.20 * duration_n
            + 0.31 * (100 - health["mechanical"]) / 40
            + 0.12 * trend_penalty
            + profile["mechanical"],
            0,
            1.7,
        )
        lubrication = clamp(
            0.27 * load_n
            + 0.21 * duration_n
            + 0.39 * (100 - health["lubrication"]) / 40
            + 0.15 * trend_penalty
            + profile["lubrication"],
            0,
            1.7,
        )
        combustion = clamp(
            0.28 * load_n
            + 0.18 * altitude_n
            + 0.20 * heat_n
            + 0.36 * (100 - health.get("combustion", 100)) / 40
            + profile["combustion"],
            0,
            1.7,
        )
        electrical = clamp(
            0.24 * duration_n + 0.42 * (100 - health["electrical"]) / 40 + profile["electrical"],
            0,
            1.7,
        )
        return {
            "stress": stress,
            "thermal": thermal,
            "mechanical": mechanical,
            "lubrication": lubrication,
            "combustion": combustion,
            "electrical": electrical,
            "rul_margin": rul_margin,
            "conservative_rul_margin": conservative_rul_margin,
            "degradation_rate": degradation_rate,
            "rul": rul,
            "conservative_rul": conservative_rul,
            "upper_rul": upper_rul,
            "profile": profile,
        }

    @staticmethod
    def _endurance_projection(comp, mission_duration):
        consumption_multiplier = 1.0 + 0.75 * comp["stress"]
        projected_endurance = max(0.0, comp["conservative_rul"] / consumption_multiplier)
        reserve_hours = max(1.0, 0.25 * mission_duration)
        decision_horizon = max(0.0, projected_endurance - reserve_hours)
        mission_margin = projected_endurance - mission_duration
        return projected_endurance, decision_horizon, mission_margin, reserve_hours

    def analyze(self, state, req):
        h = float(state["health"]["overall"])
        dur = float(req.duration_hours)
        alt = float(req.cruise_altitude_m)
        temp = float(req.ambient_temp_c)
        thr = float(req.average_throttle_pct)
        mission_type = str(req.mission_type)
        comp = self._components(state, dur, alt, temp, thr, mission_type)

        max_risk = max(
            comp["stress"],
            comp["thermal"],
            comp["mechanical"],
            comp["lubrication"],
            comp["combustion"],
            comp["electrical"],
        )
        loss = 2.2 + 7.5 * comp["stress"] + max(0, 100 - h) * 0.05 + min(10, comp["degradation_rate"] * 0.22)
        post_h = max(12.0, h - loss)
        rul_loss = dur * (1 + 0.75 * comp["stress"]) + 7 * max(0, comp["stress"] - 0.75) + 0.10 * (100 - h)
        post_r = max(0.0, comp["rul"] - rul_loss)
        post_r_lower = max(0.0, comp["conservative_rul"] - rul_loss)
        post_r_upper = max(0.0, comp["upper_rul"] - rul_loss)
        projected_endurance, decision_horizon, mission_margin, reserve_hours = self._endurance_projection(
            comp, dur
        )

        if (
            max_risk >= 0.95
            or post_h < 67
            or comp["conservative_rul_margin"] < 1.15
            or mission_margin < 0
            or post_r_lower < reserve_hours
        ):
            risk = "HIGH"
            decision = "REPLAN / ENGINEERING REVIEW"
        elif (
            max_risk >= 0.60
            or post_h < 86
            or comp["conservative_rul_margin"] < 2.0
            or mission_margin < reserve_hours
        ):
            risk = "MEDIUM"
            decision = "PROCEED WITH CAUTION IN SIMULATION"
        else:
            risk = "LOW"
            decision = "LOW-RISK POC PROFILE"

        risk_factors = []
        if comp["conservative_rul_margin"] < 2.0:
            risk_factors.append(
                f"Conservative RUL margin is {comp['conservative_rul_margin']:.2f}× planned mission duration"
            )
        if mission_margin < reserve_hours:
            risk_factors.append(
                f"Projected mission endurance margin is {mission_margin:.1f} h with a {reserve_hours:.1f} h engineering reserve target"
            )
        if comp["degradation_rate"] > 2:
            risk_factors.append(
                f"Health index is declining at {comp['degradation_rate']:.1f} points/min in the current trend window"
            )
        for name in (
            "thermal",
            "mechanical",
            "lubrication",
            "combustion",
            "electrical",
        ):
            if comp[name] >= 0.55:
                risk_factors.append(f"{name.title()} stress is {self.label(comp[name]).lower()}")
        if state["ai"].get("anomaly"):
            risk_factors.append(
                f"Active diagnostic condition: {state['ai'].get('probable_fault', 'unknown').replace('_', ' ')}"
            )
        risk_factors.append(f"Mission profile modifier: {comp['profile']['description']}")

        feasibility = clamp(
            100
            - 44 * max_risk
            - max(0, 82 - post_h) * 0.55
            - max(0, 1.8 - comp["conservative_rul_margin"]) * 15
            - max(0, reserve_hours - mission_margin) * 2.0,
            0,
            100,
        )

        alt2 = max(2500.0, alt - 800)
        dur2 = max(0.5, dur * 0.82)
        thr2 = max(52.0, thr - 10)
        alternative = self._components(state, dur2, alt2, temp, thr2, mission_type)
        alternative_max = max(
            alternative["stress"],
            alternative["thermal"],
            alternative["mechanical"],
            alternative["lubrication"],
            alternative["combustion"],
            alternative["electrical"],
        )
        alt_endurance, alt_horizon, alt_margin, alt_reserve = self._endurance_projection(alternative, dur2)

        horizon_status = (
            "INSUFFICIENT"
            if decision_horizon < dur
            else "LIMITED"
            if decision_horizon < dur + reserve_hours
            else "AVAILABLE"
        )
        profile_weights = {k: v for k, v in comp["profile"].items() if k != "description"}

        return {
            "mission_type": mission_type,
            "profile_modifier_description": comp["profile"]["description"],
            "profile_modifiers": profile_weights,
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
            "current_rul_interval_hours": {
                "lower": round(comp["conservative_rul"], 2),
                "estimate": round(comp["rul"], 2),
                "upper": round(comp["upper_rul"], 2),
            },
            "post_mission_rul_hours": post_r,
            "post_mission_rul_interval_hours": {
                "lower": round(post_r_lower, 2),
                "estimate": round(post_r, 2),
                "upper": round(post_r_upper, 2),
            },
            "rul_margin_ratio": comp["rul_margin"],
            "conservative_rul_margin_ratio": comp["conservative_rul_margin"],
            "projected_profile_endurance_hours": round(projected_endurance, 2),
            "mission_margin_hours": round(mission_margin, 2),
            "engineering_reserve_hours": round(reserve_hours, 2),
            "decision_horizon_hours": round(decision_horizon, 2),
            "decision_horizon_status": horizon_status,
            "mission_feasibility_index": feasibility,
            "risk_factors": risk_factors,
            "lower_stress_alternative": {
                "cruise_altitude_m": alt2,
                "duration_hours": round(dur2, 2),
                "average_throttle_pct": thr2,
                "projected_stress_index": alternative["stress"],
                "projected_risk": self.label(alternative_max),
                "projected_profile_endurance_hours": round(alt_endurance, 2),
                "mission_margin_hours": round(alt_margin, 2),
                "decision_horizon_hours": round(alt_horizon, 2),
                "engineering_reserve_hours": round(alt_reserve, 2),
            },
            "explanation": "Mission assessment combines the synchronized Twin state, subsystem health, temporal degradation, uncertainty-aware RUL margin, explicit mission-profile duty-cycle modifiers, planned duration, altitude, ambient temperature and average load.",
            "validation_scope": "SYNTHETIC_DECISION_SUPPORT_INDEX_NOT_CERTIFIED_PROBABILITY",
        }
