FEATURE_COLUMNS = [
    "rpm",
    "throttle",
    "altitude",
    "ambient_temp",
    "cht",
    "egt",
    "oil_pressure",
    "oil_temp",
    "fuel_flow",
    "vibration",
    "battery_voltage",
    "cht_residual",
    "egt_residual",
    "oil_pressure_residual",
    "fuel_flow_residual",
]


def select_features(df):
    return df[FEATURE_COLUMNS].copy()
