# Research and Design Basis

This build was redesigned after reviewing current aircraft/industrial Digital Twin work and modern 3D visualization patterns.

## Findings applied to TwinGuard

### Digital Twin is more than the 3D scene
Aircraft-engine Digital Twin literature describes a system that links the physical engine, a digital model, physical/digital data, virtual-real interaction and a 3D scene. The 3D view is a service that displays state and predictions; it is not the entire twin.

Source:
https://link.springer.com/article/10.1007/s40747-025-02027-z

### Combine structural, performance and system views
Aircraft-engine maintenance literature separates structural twin, performance twin and system twin concerns. TwinGuard therefore keeps the 3D structural view connected to physics/AI performance estimates and mission/maintenance system decisions.

Source:
https://link.springer.com/chapter/10.1007/978-981-95-0942-3_8

### Physics + data-driven models
Recent aero-engine research combines physical knowledge with spatiotemporal/data-driven modeling. TwinGuard's MVP uses a simpler explainable version of that principle: an expected physics surrogate plus residual features plus ML.

Sources:
https://www.sciencedirect.com/science/article/pii/S1474034625009322
https://www.sciencedirect.com/science/article/pii/S0952197626000199

### Predictive-maintenance twin architecture should be modular
Reference-architecture work emphasizes integration and multiple architectural views for Digital Twin predictive maintenance systems. TwinGuard separates telemetry, twin synchronization, physics, AI, trust, health, mission, replay and visualization services.

Source:
https://www.sciencedirect.com/science/article/pii/S0360835223001237

### 3D should explain the engineering context
An aircraft-engine predictive-maintenance visualization case study notes that raw graphs can be difficult for non-engineers to interpret; the 3D representation helps connect abnormal readings to physical components. This directly informed TwinGuard's subsystem isolation and callout design.

Source:
https://www.creativedatastudio.com/projects/aircraft-digital-twin

### Use glTF/GLB for web runtime assets
Three.js recommends glTF where possible because it is designed for runtime delivery and supports materials, animation and scene data. TwinGuard therefore ships the engine as GLB.

Source:
https://threejs.org/manual/en/loading-3d-models.html

### Bloom/postprocessing should be restrained
Three.js provides an Unreal Bloom postprocessing workflow. TwinGuard uses a low-intensity bloom and vignette around emissive health states rather than making the whole interface glow.

Source:
https://threejs.org/examples/webgl_postprocessing_unreal_bloom.html

### Game-engine integration is a valid Digital Twin pathway
Recent work demonstrates Digital Twin predictive-maintenance architecture combining game engines, MQTT and ML. TwinGuard exposes MQTT plus a UDP/WebSocket state contract so an Unreal scene can consume the same state used by the web dashboard.

Source:
https://www.sciencedirect.com/science/article/pii/S0360835226001154

## Visual direction

The new dashboard intentionally avoids:
- generic admin sidebar layouts,
- a collection of unrelated cards,
- treating a spinning 3D object as the Digital Twin,
- excessive neon decoration.

The main visual hierarchy is:
1. engine,
2. state/health,
3. operational decision,
4. engineering evidence,
5. history/mission context.
