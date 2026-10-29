# Blender headless: deviation between the aligned scan and a CAD STL (same frame), both directions,
# binned by region, plus deviation-coloured renders of the scan.
# blender -b --factory-startup --python compare.py -- scan.stl|.ply cad.stl out_prefix
import bpy, bmesh, sys, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
scan_p, cad_p, out = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
obs = []
for p in (scan_p, cad_p):  # STL or PLY
    (bpy.ops.wm.ply_import if p.lower().endswith(".ply") else bpy.ops.wm.stl_import)(filepath=p)
    obs.append(bpy.context.selected_objects[0])
scan, cad = obs


def bvh(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); return BVHTree.FromBMesh(bm)


def signed(points, tree):
    d = np.empty(len(points))
    for i, p in enumerate(points):
        loc, nrm, _, dist = tree.find_nearest(p)
        d[i] = dist * (1 if (Vector(p) - loc).dot(nrm) >= 0 else -1)
    return d


S = np.array([v.co[:] for v in scan.data.vertices]); C = np.array([v.co[:] for v in cad.data.vertices])
ts, tc = bvh(scan), bvh(cad)
ds = signed(S, tc)                       # + = scan outside CAD (CAD too small there)
rng = np.random.default_rng(0)
Ci = C[rng.choice(len(C), min(len(C), 40000), replace=False)]
dc = signed(Ci, ts)                      # + = CAD outside scan (CAD too big there)
q = lambda a: "med %+.3f  |p90| %.3f  |p99| %.3f  rms %.3f" % (np.median(a), np.quantile(abs(a), .9), np.quantile(abs(a), .99), np.sqrt(np.mean(a ** 2)))
print("scan->CAD:", q(ds)); print("CAD->scan:", q(dc))
print("scan pts within 0.1/0.2/0.3 mm: %.0f%% / %.0f%% / %.0f%%" % tuple(100 * np.mean(abs(ds) < t) for t in (.1, .2, .3)))
print("\nworst regions (scan->CAD, 1 mm cells, |dev| mean, n>=15):")
cells = {}
for p, d in zip(S, ds):
    cells.setdefault(tuple(np.floor(p).astype(int)), []).append(d)
rows = sorted(((np.mean(np.abs(v)), np.mean(v), k, len(v)) for k, v in cells.items() if len(v) >= 15), reverse=True)
for m, sm, k, n in rows[:25]:
    print("  x%3d y%3d z%3d  mean|d| %.2f  signed %+.2f  n=%d" % (*k, m, sm, n))
cellc = {}
for p, d in zip(Ci, dc):
    cellc.setdefault(tuple(np.floor(p).astype(int)), []).append(d)
rows = sorted(((np.mean(np.abs(v)), np.mean(v), k, len(v)) for k, v in cellc.items() if len(v) >= 15), reverse=True)
print("\nworst regions (CAD->scan):")
for m, sm, k, n in rows[:15]:
    print("  x%3d y%3d z%3d  mean|d| %.2f  signed %+.2f  n=%d" % (*k, m, sm, n))

# deviation-coloured renders of the scan
me = scan.data
attr = me.color_attributes.new("dev", 'FLOAT_COLOR', 'POINT')
for i, x in enumerate(ds):
    u = max(-1, min(1, x / 0.4))
    attr.data[i].color = ((1, 1 - u, 1 - u) if u > 0 else (1 + u, 1 + u, 1)) + (1,)
cad.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.color_type = 'VERTEX'; sh.light = 'STUDIO'; sh.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 900, 600
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 33
for n, dvec in {"side": (0, -1, 0), "top": (0, 0, 1), "bottom": (0, 0, -1), "iso": (0.7, -1, 0.8),
                "iso_under": (-0.7, 1, -0.9), "ends": (-1, -0.35, 0.3)}.items():
    v = Vector(dvec).normalized(); t = Vector((15, 0, 8))
    cam.location = t + v * 80
    cam.rotation_euler = (-v).to_track_quat('-Z', 'Y' if abs(v.z) > 0.99 else 'Z').to_euler()
    sc.render.filepath = out + "_" + n + ".png"
    bpy.ops.render.render(write_still=True)
