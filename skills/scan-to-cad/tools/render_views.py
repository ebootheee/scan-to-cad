# Blender headless: orthographic shaded close-ups of one or two STLs (scan grey, optional CAD tinted).
# blender -b --factory-startup --python render_views.py -- out_prefix scan.stl [cad.stl]
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out, files = a[0], a[1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
cols = [(0.75, 0.75, 0.75, 1), (0.35, 0.6, 0.95, 1)]
for i, f in enumerate(files):  # STL or PLY
    (bpy.ops.wm.ply_import if f.lower().endswith(".ply") else bpy.ops.wm.stl_import)(filepath=f)
    ob = bpy.context.selected_objects[0]
    ob.color = cols[i]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.color_type = 'OBJECT'; sh.light = 'STUDIO'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
sh.curvature_ridge_factor = 1.5; sh.curvature_valley_factor = 1.5
sc.render.resolution_x, sc.render.resolution_y = 1100, 700
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'
views = {  # name: (direction from target, target, ortho scale)
    "side_neg": ((0, -1, 0), (15, 0, 8), 32), "side_pos": ((0, 1, 0), (15, 0, 8), 32),
    "top": ((0, 0, 1), (15, 0, 8), 32), "bottom": ((0, 0, -1), (15, 0, 8), 32),
    "leg_end": ((-1, 0, 0), (15, 0, 8), 20), "hook_end": ((1, 0, 0), (15, 0, 8), 20),
    "iso": ((0.7, -1, 0.8), (15, 0, 8), 34), "iso_under": ((-0.7, 1, -0.9), (15, 0, 8), 34),
}
for n, (dvec, tgt, scale) in views.items():
    v = Vector(dvec).normalized(); t = Vector(tgt)
    cam.location = t + v * 80; cam.data.ortho_scale = scale
    up = 'Y' if abs(v.z) > 0.99 else 'Z'
    cam.rotation_euler = (-v).to_track_quat('-Z', up).to_euler()
    sc.render.filepath = out + "_" + n + ".png"
    bpy.ops.render.render(write_still=True)
