# Blender asset workflow

The repository ships with a working GLB generated procedurally so the dashboard does not depend on Blender.

If Blender is installed, run:

```bash
blender --background --python tools/blender/postprocess_engine.py
```

This creates `engine_blender.glb` with smoother shading and micro-bevels.

For a real UAV engine, the preferred workflow is:
1. obtain an authorized CAD model,
2. remove proprietary/unneeded internals,
3. reduce polygon count,
4. create separate named objects for THERMAL / LUBRICATION / MECHANICAL / ELECTRICAL subsystems,
5. author PBR materials in Blender,
6. export GLB,
7. replace the runtime asset and update the subsystem mapping if needed.

The current included engine is an original generic flat-four aero-piston visualization, not a real manufacturer/DRDO CAD model.
