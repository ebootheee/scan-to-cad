# Blender headless: clean the scan, align it to the FreeCAD model frame by PCA + trimmed ICP,
# export aligned scan + deviation stats.
import bpy, bmesh, sys, itertools, numpy as np
from mathutils.bvhtree import BVHTree
args = sys.argv[sys.argv.index("--") + 1:]
scan_path, cad_path, out_dir = args

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=scan_path)
scan = bpy.context.selected_objects[0]; scan.name = "scan"
bpy.ops.wm.stl_import(filepath=cad_path)
cad = bpy.context.selected_objects[0]; cad.name = "cad"

# --- clean: keep only the largest island
bm = bmesh.new(); bm.from_mesh(scan.data); bm.verts.ensure_lookup_table()
seen, islands = set(), []
for vert in bm.verts:
    if vert.index in seen: continue
    stack, isl = [vert], []
    seen.add(vert.index)
    while stack:
        a = stack.pop(); isl.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen: seen.add(b.index); stack.append(b)
    islands.append(isl)
islands.sort(key=len, reverse=True)
bmesh.ops.delete(bm, geom=[v for isl in islands[1:] for v in isl], context='VERTS')
bm.to_mesh(scan.data); bm.free()
print("kept main island, removed", len(islands) - 1)

V = np.array([v.co[:] for v in scan.data.vertices])
bmc = bmesh.new(); bmc.from_mesh(cad.data); cad_bvh = BVHTree.FromBMesh(bmc)
C = np.array([v.co[:] for v in cad.data.vertices])

def nearest(P):
    out = np.empty_like(P)
    for i, p in enumerate(P):
        out[i] = cad_bvh.find_nearest(p)[0][:]
    return out

def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0)
    U, S, Wt = np.linalg.svd((A - ca).T @ (B - cb))
    d = np.sign(np.linalg.det(Wt.T @ U.T))
    R = Wt.T @ np.diag([1, 1, d]) @ U.T
    return R, cb - R @ ca

def icp(P, R, t, iters=40, keep=0.85):
    for _ in range(iters):
        Q = P @ R.T + t
        N = nearest(Q)
        d = np.linalg.norm(Q - N, axis=1)
        m = d <= np.quantile(d, keep)
        dR, dt = kabsch(Q[m], N[m])
        R, t = dR @ R, dR @ t + dt
    Q = P @ R.T + t
    d = np.linalg.norm(Q - nearest(Q), axis=1)
    return R, t, np.sqrt(np.mean(d[d <= np.quantile(d, keep)] ** 2))

def pca(X):
    c = X.mean(0); w, vec = np.linalg.eigh(np.cov((X - c).T))
    return c, vec[:, ::-1]          # major -> minor

rng = np.random.default_rng(0)
P = V[rng.choice(len(V), 2500, replace=False)]
cs, As = pca(V); cc, Ac = pca(C)
best = None
for perm in itertools.permutations(range(3)):
    for signs in itertools.product((1, -1), repeat=3):
        A = As[:, perm] * np.array(signs)
        if np.linalg.det(A) * np.linalg.det(Ac) < 0: continue
        R0 = Ac @ A.T
        t0 = cc - R0 @ cs
        R, t, rms = icp(P, R0, t0, iters=12)
        if best is None or rms < best[2]: best = (R, t, rms)
print("coarse best rms %.3f" % best[2])
P = V[rng.choice(len(V), 8000, replace=False)]
R, t, rms = icp(P, best[0], best[1], iters=60)
print("fine rms (best 85%%) %.3f mm" % rms)

Va = V @ R.T + t
for i, v in enumerate(scan.data.vertices): v.co = Va[i]
scan.data.update()
np.save(out_dir + "/scan_aligned_verts.npy", Va)
np.save(out_dir + "/scan_faces.npy", np.array([p.vertices[:] for p in scan.data.polygons]))
np.save(out_dir + "/scan_R_t.npy", np.hstack([R, t[:, None]]))

# signed deviation scan -> CAD (positive = scan outside CAD)
bmc.verts.ensure_lookup_table()
dev = np.empty(len(Va))
for i, p in enumerate(Va):
    loc, nrm, idx, dist = cad_bvh.find_nearest(p)
    dev[i] = dist * np.sign(np.dot(np.array(p) - np.array(loc[:]), np.array(nrm[:])))
np.save(out_dir + "/dev.npy", dev)
print("deviation mm: median %.2f  p05 %.2f  p95 %.2f  |dev|>0.5: %.0f%%"
      % (np.median(dev), np.quantile(dev, .05), np.quantile(dev, .95), 100 * np.mean(np.abs(dev) > .5)))
print("aligned scan bbox", Va.min(0).round(2), Va.max(0).round(2))
print("cad bbox", C.min(0).round(2), C.max(0).round(2))

bpy.ops.object.select_all(action='DESELECT'); scan.select_set(True)
bpy.context.view_layer.objects.active = scan
bpy.ops.wm.stl_export(filepath=out_dir + "/scan_aligned.stl", export_selected_objects=True, apply_modifiers=True)
bpy.ops.wm.save_as_mainfile(filepath=out_dir + "/scan_vs_cad.blend")
