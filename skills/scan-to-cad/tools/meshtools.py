# Shared helpers for measuring the aligned scan (and any candidate STL) with plain numpy.
# The scan is $SCAN (STL or binary PLY), default scan_aligned.stl in the current folder.
# Any python with numpy (and matplotlib for slices) works, e.g. FreeCAD's bundled python:
#   python meshtools.py probe  "y x=3 z=5" "z x=5.9 y=4"
#   python meshtools.py slice out.png "X:9.5" [--box x0,x1,y0,y1] [--cad file.stl]
import struct, sys, os, numpy as np

SCAN = os.environ.get("SCAN", "scan_aligned.stl")
AX = "xyz"


def read_stl(p):
    b = open(p, "rb").read()
    if b[:5] == b"solid" and b"facet" in b[:400]:            # ascii
        pts = [list(map(float, l.split()[1:4])) for l in b.decode().splitlines() if l.strip().startswith("vertex")]
        return np.array(pts).reshape(-1, 3, 3)
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(float)


_PLY = {"char": "i1", "uchar": "u1", "short": "i2", "ushort": "u2", "int": "i4", "uint": "u4",
        "float": "f4", "double": "f8", "int8": "i1", "uint8": "u1", "int16": "i2", "uint16": "u2",
        "int32": "i4", "uint32": "u4", "float32": "f4", "float64": "f8"}


def read_ply(p):
    """Triangles (n, 3, 3) from a binary little-endian PLY with x/y/z vertices and triangle faces."""
    b = open(p, "rb").read()
    end = b.index(b"\n", b.index(b"end_header")) + 1
    head = b[:end].decode("ascii").splitlines()
    if "format binary_little_endian 1.0" not in head:
        raise ValueError("%s: only binary little-endian PLY is supported" % p)
    elems = []
    for line in head:
        w = line.split()
        if w[:1] == ["element"]: elems.append((w[1], int(w[2]), []))
        elif w[:1] == ["property"]: elems[-1][2].append(w[1:])
    off, V, F = end, None, None
    for name, n, props in elems:
        if name == "vertex" and all(pr[0] != "list" for pr in props):
            dt = np.dtype([(pr[-1], "<" + _PLY[pr[0]]) for pr in props])
            V = np.frombuffer(b, dt, n, off); off += n * dt.itemsize
        elif name == "face" and len(props) == 1 and props[0][0] == "list":
            dt = np.dtype([("n", "<" + _PLY[props[0][1]]), ("i", "<" + _PLY[props[0][2]], 3)])
            F = np.frombuffer(b, dt, n, off); off += n * dt.itemsize
            if (F["n"] != 3).any(): raise ValueError("%s: faces must all be triangles" % p)
        elif V is None or F is None:
            raise ValueError("%s: unsupported PLY element %r" % (p, name))
    xyz = np.stack([V["x"], V["y"], V["z"]], 1).astype(float)
    return xyz[F["i"].astype(np.int64)]


def read_mesh(p):
    return read_ply(p) if p.lower().endswith(".ply") else read_stl(p)


def ray_hits(T, axis, fixed):
    """Coordinates along `axis` where the infinite line (other two coords fixed) crosses the mesh."""
    a = AX.index(axis)
    o = [i for i in range(3) if i != a]
    P = T[:, :, o]                                            # project triangles onto the fixed plane
    q = np.array([fixed[AX[o[0]]], fixed[AX[o[1]]]])
    v0, v1, v2 = P[:, 0], P[:, 1], P[:, 2]
    d = (v1[:, 0] - v0[:, 0]) * (v2[:, 1] - v0[:, 1]) - (v2[:, 0] - v0[:, 0]) * (v1[:, 1] - v0[:, 1])
    ok = np.abs(d) > 1e-12
    w1 = ((q[0] - v0[:, 0]) * (v2[:, 1] - v0[:, 1]) - (v2[:, 0] - v0[:, 0]) * (q[1] - v0[:, 1])) / np.where(ok, d, 1)
    w2 = ((v1[:, 0] - v0[:, 0]) * (q[1] - v0[:, 1]) - (q[0] - v0[:, 0]) * (v1[:, 1] - v0[:, 1])) / np.where(ok, d, 1)
    w0 = 1 - w1 - w2
    m = ok & (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    h = w0[m] * T[m, 0, a] + w1[m] * T[m, 1, a] + w2[m] * T[m, 2, a]
    h = np.sort(h)
    if len(h):                                                # drop duplicate hits on shared edges
        h = h[np.concatenate([[True], np.diff(h) > 1e-4])]
    return h


def slice_segs(T, ax, val):
    s = T[:, :, ax] - val
    m = (s.min(1) < 0) & (s.max(1) > 0)
    segs = []
    for tri, sd in zip(T[m], s[m]):
        pts = []
        for i in range(3):
            a, b = i, (i + 1) % 3
            if (sd[a] < 0) != (sd[b] < 0):
                u = sd[a] / (sd[a] - sd[b]); pts.append(tri[a] + u * (tri[b] - tri[a]))
        if len(pts) == 2: segs.append(pts)
    return np.array(segs)


def plot_slices(out, cuts, cad=None, box=None):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.ticker import MultipleLocator
    S = read_mesh(SCAN); C = read_mesh(cad) if cad else None
    fig, axs = plt.subplots(1, len(cuts), figsize=(6.5 * len(cuts), 6.5))
    axs = np.atleast_1d(axs)
    for axp, cut in zip(axs, cuts):
        a, v = cut.split(":"); ai = "XYZ".index(a); v = float(v)
        keep = [i for i in range(3) if i != ai]
        for T, col, lw, lab in ((C, "#777", 2.0, os.path.basename(cad or "")), (S, "#d62728", 0.9, "scan")):
            if T is None: continue
            sg = slice_segs(T, ai, v)
            if len(sg): axp.add_collection(LineCollection(sg[:, :, keep], colors=col, linewidths=lw, label=lab))
        axp.set_aspect("equal"); axp.autoscale()
        if box: axp.set_xlim(box[0], box[1]); axp.set_ylim(box[2], box[3])
        axp.xaxis.set_major_locator(MultipleLocator(1)); axp.yaxis.set_major_locator(MultipleLocator(1))
        axp.xaxis.set_minor_locator(MultipleLocator(0.25)); axp.yaxis.set_minor_locator(MultipleLocator(0.25))
        axp.grid(which="major", alpha=.45); axp.grid(which="minor", alpha=.12)
        axp.tick_params(labelsize=7)
        axp.set_xlabel("XYZ"[keep[0]]); axp.set_ylabel("XYZ"[keep[1]])
        axp.set_title(cut); axp.legend(fontsize=7, loc="upper right")
    plt.tight_layout(); plt.savefig(out, dpi=100); plt.close(fig)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "probe":
        T = read_mesh(SCAN)
        for spec in sys.argv[2:]:
            parts = spec.split()
            fixed = {k: float(x) for k, x in (p.split("=") for p in parts[1:])}
            print("%-22s" % spec, " ".join("%.2f" % h for h in ray_hits(T, parts[0], fixed)))
    elif cmd == "slice":
        out, cuts = sys.argv[2], sys.argv[3].split(",")
        cad = box = None
        if "--cad" in sys.argv: cad = sys.argv[sys.argv.index("--cad") + 1]
        if "--box" in sys.argv: box = [float(x) for x in sys.argv[sys.argv.index("--box") + 1].split(",")]
        plot_slices(out, cuts, cad, box)
