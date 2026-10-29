# Find the scan's own mirror plane and re-frame it so that plane is exactly y = 0
# and x = 0 at the scan's min-x end. Prints the correction applied.
#   python symfit.py <scan.stl|.ply> <out.stl>
import struct, sys, numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import minimize
from meshtools import read_mesh

scan_p, out_p = sys.argv[1:3]
T = read_mesh(scan_p)
P = np.unique(T.reshape(-1, 3).round(5), axis=0)
tree = cKDTree(P)
rng = np.random.default_rng(1)
Q = P[rng.choice(len(P), 6000, replace=False)]


def plane(p):
    n = np.array([p[0], 1.0, p[1]]); n /= np.linalg.norm(n)
    return n, p[2]


def cost(p):
    n, c = plane(p)
    R = Q - 2 * ((Q @ n) - c)[:, None] * n
    d, _ = tree.query(R)
    return np.mean(np.minimum(d, 0.6) ** 2)          # robust (truncated) error


best = min((minimize(cost, x0, method="Nelder-Mead", options={"xatol": 1e-5, "fatol": 1e-8, "maxiter": 4000})
            for x0 in ([0, 0, 0], [0.03, 0, 0.1], [-0.03, 0.02, -0.1])), key=lambda r: r.fun)
n, c = plane(best.x)
print("mirror plane normal", n.round(4), "offset %.3f" % c, "rms %.3f" % np.sqrt(best.fun))

# rotation taking n -> +Y (Rodrigues), then shift plane to y=0
y = np.array([0, 1.0, 0]); v = np.cross(n, y); s = np.linalg.norm(v); cth = n @ y
K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
R = np.eye(3) + K + K @ K * ((1 - cth) / s ** 2) if s > 1e-12 else np.eye(3)
print("yaw %.2f deg, roll %.2f deg" % (np.degrees(np.arctan2(n[0], n[1])), np.degrees(np.arctan2(n[2], n[1]))))
T2 = T @ R.T
T2[:, :, 1] -= c
# x = 0 at the min-x end (the leg tips on the tine clip), keep z as is
T2[:, :, 0] -= T2[:, :, 0].min()

V = T2.reshape(-1, 3); Vm = V * [1, -1, 1]
d, _ = cKDTree(V).query(Vm[::7])
print("after: mirror deviation median %.3f p95 %.3f" % (np.median(d), np.quantile(d, .95)))
print("bbox", V.min(0).round(2), V.max(0).round(2))

with open(out_p, "wb") as f:
    f.write(b"scan re-framed on its mirror plane (y = 0)".ljust(80, b" "))
    f.write(struct.pack("<I", len(T2)))
    for tri in T2:
        nrm = np.cross(tri[1] - tri[0], tri[2] - tri[0]); nrm /= (np.linalg.norm(nrm) or 1)
        f.write(struct.pack("<12fH", *nrm, *tri.ravel(), 0))
