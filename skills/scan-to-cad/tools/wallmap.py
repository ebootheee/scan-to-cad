# Height map of the outer side-wall surfaces (|y| of the outermost hit) to find pivot bumps / dimples.
#   python wallmap.py <out_prefix> [--box x0,x1,z0,z1] [--clim lo,hi]
# The grid defaults to the scan's x/z extent and the colour range to automatic.
# The tine clip used --box 8.5,22.6,0.2,11.4 --clim 5.0,6.6
import sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from meshtools import read_mesh, ray_hits, SCAN


def opt(name):
    return [float(v) for v in sys.argv[sys.argv.index(name) + 1].split(",")] if name in sys.argv else None


T = read_mesh(SCAN)
box = opt("--box") or [T[:, :, 0].min(), T[:, :, 0].max(), T[:, :, 2].min(), T[:, :, 2].max()]
clim = opt("--clim") or [None, None]
xs = np.arange(box[0], box[1], 0.2); zs = np.arange(box[2], box[3], 0.2)
fig, axs = plt.subplots(1, 2, figsize=(14, 5))
for ax, side in zip(axs, (-1, 1)):
    M = np.full((len(zs), len(xs)), np.nan)
    for i, z in enumerate(zs):
        for j, x in enumerate(xs):
            h = ray_hits(T, "y", {"x": x, "z": z})
            if len(h): M[i, j] = -h[0] if side < 0 else h[-1]
    im = ax.imshow(M, origin="lower", extent=[xs[0], xs[-1], zs[0], zs[-1]], cmap="viridis", vmin=clim[0], vmax=clim[1])
    ax.set_title("outer |y| on %s side" % ("-Y" if side < 0 else "+Y")); ax.set_xlabel("x"); ax.set_ylabel("z")
    ax.set_xticks(np.arange(np.ceil(xs[0]), xs[-1], 1)); ax.set_yticks(np.arange(np.ceil(zs[0]), zs[-1], 1)); ax.grid(alpha=.3)
    plt.colorbar(im, ax=ax)
    np.save(sys.argv[1] + "_%s.npy" % ("neg" if side < 0 else "pos"), M)
plt.tight_layout(); plt.savefig(sys.argv[1] + ".png", dpi=100)
