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

export type ViewName="command"|"diagnostics"|"mission"|"replay"|"maintenance"|"settings";

export interface TwinState{
  engine_id:string;
  timestamp:string;
  telemetry:Record<string,number|string>;
  expected:Record<string,number>;
  residuals:Record<string,number>;
  trends?:Record<string,number>;
  sensor_trust:Record<string,number>;
  data_quality:Record<string,number|string>;
  health:{
    thermal:number;
    lubrication:number;
    mechanical:number;
    combustion:number;
    electrical:number;
    sensor:number;
    overall:number;
  };
  ai:{
    anomaly:boolean;
    anomaly_score:number;
    probable_fault:string;
    fault_confidence:number;
    fault_probabilities:Record<string,number>;
    rul_hours:number;
    evidence:Array<{feature:string;weight:number;value:number}>;
    model_state:string;
    validation_scope?:string;
    rul_basis?:string;
    feature_contract?:string;
    anomaly_persistence_samples?:number;
    model_warning?:string|null;
  };
  confidence:{
    ai:number;
    sensor:number;
    physics_agreement:number;
    data_quality:number;
    temporal_persistence?:number;
    decision:number;
  };
  maintenance:{
    priority:string;
    affected_subsystem:string;
    recommended_checks:string[];
    reason:string;
    next_mission_suitability:string;
    validation_scope?:string;
  };
  readiness:{status:string;label:string;reason:string};
  twin_meta?:{
    physics_model?:string;
    telemetry_source?:string;
    validation_scope?:string;
  };
}

export interface MissionResult{
  overall_risk:string;
  decision:string;
  stress_index:number;
  thermal_risk:string;
  mechanical_risk:string;
  lubrication_risk:string;
  current_health:number;
  post_mission_health:number;
  current_rul_hours:number;
  post_mission_rul_hours:number;
  lower_stress_alternative:{
    cruise_altitude_m:number;
    duration_hours:number;
    average_throttle_pct:number;
  };
  explanation:string;
  mission_feasibility_index?:number;
  rul_margin_ratio?:number;
  risk_factors?:string[];
  validation_scope?:string;
}

export interface ReplayMission{
  id:number;
  engine_id:string;
  label:string;
  status:string;
  started_at:string;
  ended_at?:string;
  summary?:Record<string,unknown>;
}

export interface SystemStatus{
  service:string;
  version:string;
  environment:string;
  engine_id:string;
  database:string;
  models:{anomaly:boolean;fault:boolean;rul:boolean};
  integrations:{mqtt:boolean;unreal_udp:boolean;can:boolean};
  telemetry:{available:boolean;age_seconds:number|null};
  security:{
    cors_origins:string[];
    trusted_hosts:string[];
    ingest_key_required:boolean;
    authentication?:boolean;
  };
}

export interface AuthUser{id:number;name:string;email:string;role:string}
export interface AuthResponse{token:string;user:AuthUser}
