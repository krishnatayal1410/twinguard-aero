"""Run inside Blender:
blender --background --python tools/blender/postprocess_engine.py

This script imports the generated TwinGuard GLB, applies non-destructive bevel
and smooth-shading improvements, and exports a web-ready GLB.
"""
import bpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/"frontend/public/assets/engine/engine.glb"
out=ROOT/"frontend/public/assets/engine/engine_blender.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))

for obj in bpy.context.scene.objects:
    if obj.type!="MESH":
        continue
    # Auto smooth by normals; use small bevel to catch highlights.
    for poly in obj.data.polygons:
        poly.use_smooth=True
    bevel=obj.modifiers.new(name="TwinGuardMicroBevel",type="BEVEL")
    bevel.width=0.008
    bevel.segments=2
    bevel.limit_method="ANGLE"
    # Preserve explicit subsystem names for Three.js lookup.
    obj.name=obj.name.upper()

# Add a subtle studio world. Lights are still authored in Three.js at runtime.
world=bpy.context.scene.world
world.color=(0.008,0.012,0.016)

bpy.ops.export_scene.gltf(
    filepath=str(out),
    export_format="GLB",
    export_apply=True,
    export_materials="EXPORT",
    export_cameras=False,
    export_lights=False,
)
print("Exported",out)
