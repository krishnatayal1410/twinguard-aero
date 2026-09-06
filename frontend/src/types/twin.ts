export type FaultName=
  |"normal"
  |"lubrication"
  |"overheating"
  |"cooling_degradation"
  |"vibration"
  |"sensor_drift"
  |"injector"
  |"misfire"
  |"combustion_instability"
  |"alternator_degradation";

export type ViewName="command"|"digitalTwin"|"healthFaults"|"diagnostics"|"mission"|"replay"|"maintenance"|"settings";
export type MissionType="endurance"|"high_altitude"|"hot_weather"|"rapid_throttle"|"patrol";

export interface RulInterval{
  lower:number;
  estimate:number;
  upper:number;
  basis?:string;
  calibrated_probability_interval?:boolean;
}

export interface RuntimeValidity{
  telemetry_age_seconds:number|null;
  stale:boolean;
  freshness_limit_seconds?:number;
  data_quality?:number;
  minimum_data_quality?:number;
  decision_eligible:boolean;
}

export interface TelemetryState{
  engine_id:string;
  timestamp:string;
  rpm:number;
  throttle:number;
  cht:number;
  egt:number;
  oil_pressure:number;
  oil_temperature:number;
  fuel_flow:number;
  vibration:number;
  battery_voltage:number;
  alternator_voltage:number;
  altitude:number;
  ambient_temperature:number;
  injection_timing:number;
  operating_hours:number;
}

export interface ExpectedState{
  cht:number;
  egt:number;
  oil_pressure:number;
  oil_temperature:number;
  fuel_flow:number;
  vibration:number;
  battery_voltage:number;
  alternator_voltage:number;
  injection_timing:number;
}

export interface ResidualState{
  cht_residual:number;
  egt_residual:number;
  oil_pressure_residual:number;
  oil_temperature_residual:number;
  fuel_flow_residual:number;
  vibration_residual:number;
  battery_voltage_residual:number;
  alternator_voltage_residual:number;
  injection_timing_residual:number;
}

export interface TrendState{
  oil_pressure_per_min:number;
  oil_temperature_per_min:number;
  cht_per_min:number;
  egt_per_min:number;
  vibration_per_min:number;
  battery_voltage_per_min:number;
  alternator_voltage_per_min:number;
  health_index_per_min:number;
}

export interface TwinEvent{
  timestamp:string;
  type:string;
  severity:"info"|"warning"|"critical"|"success";
  message:string;
}

export interface TwinState{
  engine_id:string;
  timestamp:string;
  telemetry:TelemetryState;
  expected:ExpectedState;
  residuals:ResidualState;
  trends:TrendState;
  events:TwinEvent[];
  sensor_trust:Record<string,number>;
  data_quality:Record<string,number|string>;
  runtime_validity?:RuntimeValidity;
  health:{thermal:number;lubrication:number;mechanical:number;combustion:number;electrical:number;sensor:number;overall:number};
  ai:{
    anomaly:boolean;anomaly_score:number;probable_fault:string;fault_confidence:number;fault_probabilities:Record<string,number>;
    rul_hours:number;rul_interval_hours?:RulInterval;rul_uncertainty_hours?:number;evidence:Array<{feature:string;weight:number;value:number}>;
    model_state:string;validation_scope?:string;rul_basis?:string;rul_interval_basis?:string;feature_contract?:string;
    anomaly_persistence_samples?:number;model_warning?:string|null;
  };
  confidence:{ai:number;sensor:number;physics_agreement:number;data_quality:number;temporal_persistence?:number;decision:number};
  maintenance:{priority:string;affected_subsystem:string;recommended_checks:string[];reason:string;next_mission_suitability:string;validation_scope?:string};
  readiness:{status:string;label:string;reason:string};
  twin_meta?:{physics_model?:string;telemetry_source?:string;validation_scope?:string;freshness_gate_seconds?:number;mission_min_data_quality?:number};
}

export interface MissionResult{
  mission_type?:MissionType;profile_modifier_description?:string;profile_modifiers?:Record<string,number>;
  overall_risk:string;decision:string;stress_index:number;thermal_risk:string;mechanical_risk:string;lubrication_risk:string;combustion_risk?:string;electrical_risk?:string;
  current_health:number;post_mission_health:number;current_rul_hours:number;current_rul_interval_hours?:RulInterval;post_mission_rul_hours:number;post_mission_rul_interval_hours?:RulInterval;
  rul_margin_ratio?:number;conservative_rul_margin_ratio?:number;projected_profile_endurance_hours?:number;mission_margin_hours?:number;engineering_reserve_hours?:number;
  decision_horizon_hours?:number;decision_horizon_status?:string;
  lower_stress_alternative:{cruise_altitude_m:number;duration_hours:number;average_throttle_pct:number;projected_stress_index?:number;projected_risk?:string;projected_profile_endurance_hours?:number;mission_margin_hours?:number;decision_horizon_hours?:number;engineering_reserve_hours?:number};
  explanation:string;mission_feasibility_index?:number;risk_factors?:string[];validation_scope?:string;
}

export interface ReplayMission{id:number;engine_id:string;label:string;status:string;started_at:string;ended_at?:string;summary?:Record<string,unknown>}
export interface ReplaySample{
  timestamp:string;
  health:number;
  rul:number;
  cht:number;
  oil_pressure:number;
  vibration:number;
  anomaly:boolean;
  fault:string;
  maintenance:string;
}

export interface SystemStatus{
  service:string;version:string;environment:string;engine_id:string;database:string;
  models:{anomaly:boolean;fault:boolean;rul:boolean};integrations:{mqtt:boolean;unreal_udp:boolean;can:boolean};
  telemetry:{available:boolean;age_seconds:number|null;stale?:boolean;freshness_limit_seconds?:number;data_quality?:number;minimum_data_quality?:number;decision_eligible?:boolean};
  security:{cors_origins:string[];trusted_hosts:string[];ingest_key_required:boolean;authentication?:boolean};
}

export interface AuthUser{id:number;name:string;email:string;role:string}
export interface AuthResponse{token:string;user:AuthUser}
