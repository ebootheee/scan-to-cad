import bpy, bmesh, sys, numpy as np
path = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=path)
ob = bpy.context.selected_objects[0]
me = ob.data
v = np.array([x.co[:] for x in me.vertices])
print("verts", len(v), "faces", len(me.polygons))
print("bbox min", v.min(0), "max", v.max(0), "size", v.max(0) - v.min(0))
c = v.mean(0)
w, vec = np.linalg.eigh(np.cov((v - c).T))
print("centroid", c)
print("PCA std", np.sqrt(w))
print("PCA axes\n", vec.T)
p = (v - c) @ vec[:, ::-1]
print("extent along PCA (major->minor)", p.max(0) - p.min(0))
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table()
nm = [e for e in bm.edges if not e.is_manifold]
bnd = [e for e in bm.edges if e.is_boundary]
print("non-manifold edges", len(nm), "boundary edges", len(bnd))
# islands
seen = set(); islands = []
for vert in bm.verts:
    if vert.index in seen: continue
    stack = [vert]; seen.add(vert.index); n = 0
    while stack:
        a = stack.pop(); n += 1
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen:
                seen.add(b.index); stack.append(b)
    islands.append(n)
print("islands", sorted(islands, reverse=True)[:10], "count", len(islands))
el = np.array([e.calc_length() for e in bm.edges])
print("edge length median %.3f min %.3f max %.3f" % (np.median(el), el.min(), el.max()))
print("volume", bm.calc_volume() if not bnd else "open")
