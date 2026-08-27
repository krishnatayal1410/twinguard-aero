def estimate_placeholder_rul(health: float, operating_hours: float) -> float:
    # Synthetic proof-of-concept only.
    return max(0.0, (health/100.0)*180 - 0.05*operating_hours)
