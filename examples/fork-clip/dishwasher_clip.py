"""
Dishwasher rack clip - parametric FreeCAD reconstruction of a Revopoint scan
(the scan is not included).

Coordinate frame (scan re-aligned to it):
    X  across the clip; the part is mirror-symmetric about the YZ plane (X = 0)
    Y  along the clip: fork hook at -Y, C-hook / E-hook at +Y
    Z  up; Z = 0 is the bottom of the C-hook

Construction: every feature is a YZ profile carried across an X band
[x0, x1] and mirrored to -X, so the model is exactly symmetric. Rounded edges
are built as ruled lofts through X-sections whose outline is pulled in by the
exact arc offset at each station (no OCC fillets, so rebuilds are robust):
  - channel: the U-shaped spine, outer loft with a rounded bottom and rounded
    wall tops, minus a rounded cavity, minus the floor window. Under the fork
    wings the cavity runs up beneath a ~1 mm lip (the snap groove in the scan).
  - fork tines (2 bands; the hook lip runs the full tine width), collar,
    overhang tabs (with flex slits to the collar), E/C side plates, C-hook core
  - strap: the U under the hook end (block, elliptical underside, inner U)
  - relief between the side plates, C-hook taper toward its tip
  - wire seats: fork bore (U-slot), C-hook bore and E-hook seat are exact
    circles driven by PARAMS, so wire fit can be tuned without the outlines.

Scan holes, duplicate scan surfaces and noisy patches were filled/ignored;
the part was rebuilt from the average of its left and right halves (the
scanned part is bowed ~0.2-0.4 mm sideways; the model splits the difference).

Usage
  Edit values in the "Params" spreadsheet of dishwasher_clip.FCStd (or the
  PARAMS defaults below), then rebuild with build_clip.py:
      freecadcmd build_clip.py           headless; reads the saved FCStd's sheet
      FreeCAD: Macro > Macros... > build_clip.py   (rebuilds the open document)
  Both rewrite dishwasher_clip.FCStd / .step / .stl next to this file.
"""

import math
import os

import FreeCAD as App
import Part

V = App.Vector

# ---------------------------------------------------------------- parameters
# Lengths in mm. Feature bands are [x0, x1] on the +X side (mirrored to -X).
PARAMS = {
    # channel (U-shaped spine between the fork and the hook end)
    "chan_half_w": 4.5,       # outer half-width
    "chan_wall": 1.5,         # side-wall thickness -> cavity half-width
    "chan_r_out": 4.0,        # outer bottom round (normal to the floor)
    "chan_r_out_end": 1.2,    # ... tapering to this at the trough end
    "chan_r_taper_y": (-4.0, 0.0),  # Y range of that taper
    "chan_r_in": 2.6,         # inner bottom round
    "chan_r_top": 0.75,       # round on both top edges of the walls
    "chan_back_y": -14.35,    # saddle back face
    "win_half_w": 1.8,        # floor window half-width (stadium)
    "win_y0": -10.35,         # floor window extent along Y
    "win_y1": -4.45,

    # feature bands [x0, x1] and edge rounds on their outer / inner faces
    "tine_r_x": (2.2, 5.3),   # fork tine, inner band (full hook)
    "tine_k_x": (5.2, 6.75),  # fork tine, outer band (wing, hook lip runs full width)
    "tine_round": 0.6,        # round on the tine inner face and outer wing face
    "collar_x": (4.25, 6.1),  # side collar joining channel to hook end
    "collar_round": 1.2,      # round on the collar outer face edges
    "box_x": (1.2, 4.6),      # overhang block above the frame window
    "box_r_top": (2.6, 4.2),  # elliptical round on the overhang's inner top edge (x, z)
    "tab_gap_x": (3.1, 4.3),  # flex slit between overhang tab and collar wall (0 width = off)
    "tab_gap_y": (3.6, 10.95),  # ... its length (whole tab)
    "tab_gap_z0": 14.8,       # ... open from below this height
    "tab_hinge": 1.5,         # ... material left above it, joining tab to collar
    "ec_x": (1.9, 4.45),      # E-hook / C-hook side plates
    "ec_round_out": 1.0,      # round on their outer face edges
    "ec_round_in": 0.5,       # round on their inner face edges (E tines)
    "cc_half_w": 4.4,         # C-hook core half-width (centre profile, full width)
    "relief_half_w": 2.25,    # gap between the side plates behind the E tines
    "c_taper_z": 9.5,         # the C-hook taper applies below this height
    # C-hook half-width along Y (it narrows toward the tip)
    "c_taper": ((15.0, 4.4), (16.0, 4.2), (17.0, 3.95), (18.0, 3.8), (19.0, 3.7), (20.0, 3.6), (22.5, 3.5)),
    "strap_half_w": 6.3,      # U strap under the hook end: half-width
    "strap_top": 14.6,        # ... top of its side walls
    "strap_ell_a": 6.5,       # ... elliptical underside: half-width
    # ... and its depth along Y (deepens where the strap meets the C-hook shank)
    "strap_depth": ((9.3, 4.5), (10.25, 5.0), (11.0, 5.5), (11.75, 9.0), (12.15, 10.0)),
    "strap_y": (9.3, 12.15),   # Y range of the strap underside round
    "strap_block_y0": 9.55,   # front face of the strap block
    "strap_in_r": 3.8,        # inner round of the strap U (pocket between the plates)
    "strap_in_z": 10.4,       # ... its floor height
    "strap_in_y": (9.55, 12.0),
    "strap_in_ztop": 15.0,    # ... and its top (just under the overhang block)

    "refine": 0.0,            # 1 = merge coplanar faces (cosmetic, adds ~90 s)

    # wire seats (circle fits to the scan)
    "fork_bore_c": (-16.53, 28.93), "fork_bore_d": 5.12, "fork_tip_z": 28.05,
    "c_bore_c": (16.90, 6.05),      "c_bore_d": 5.67,
    "e_seat_c": (16.85, 16.23),     "e_seat_d": 3.60,
}

# Facet size of the polyline sections and steps per quarter-round. 0.5 mm
# facets keep chord error < 0.03 mm on a 1 mm round; finer only slows booleans.
RES = {"seg": 0.5, "steps": 6}

# As-scanned wire-seat sizes; the outlines below already contain these, so
# shrinking a seat below its scanned size adds material back first.
SCAN_SEATS = {"fork_bore_d": 5.12, "c_bore_d": 5.67, "e_seat_d": 3.60}

# ------------------------------------------------------------------ profiles
# (Y, Z) outline points traced from the symmetrised, hole-filled scan and
# lightly cleaned. Sections are fine polylines through them (see RES).
PROFILES = {
    "tine_r": [
        (-9.60, 32.30), (-9.60, 32.95), (-12.75, 34.04), (-16.62, 35.09), (-18.25, 35.66), (-20.12, 36.17),
        (-20.52, 36.12), (-20.62, 35.60), (-20.76, 34.38),
        (-21.88, 29.75), (-21.89, 29.12), (-21.75, 28.84), (-21.25, 28.44), (-20.38, 28.12), (-19.88, 28.06),
        (-19.54, 28.12), (-19.41, 28.25), (-19.23, 28.62), (-18.65, 30.38), (-18.45, 30.75), (-17.38, 31.30),
        (-16.88, 31.39), (-16.00, 31.30), (-15.25, 31.05), (-14.88, 30.82), (-14.50, 30.52), (-14.20, 30.12),
        (-13.76, 29.00), (-13.25, 29.00), (-12.90, 32.30),
    ],
    "tine_k": [
        (-6.64, 30.75), (-7.25, 31.51), (-8.25, 32.29), (-9.62, 33.02), (-11.12, 33.55), (-16.75, 35.09),
        (-18.50, 35.67), (-20.00, 35.96), (-20.32, 35.80), (-20.45, 35.20), (-20.55, 34.00), (-20.60, 32.00),
        (-20.50, 30.50), (-20.20, 29.85), (-19.60, 29.50), (-19.25, 29.55), (-18.60, 30.50),
        (-18.00, 31.10), (-17.38, 31.43), (-16.75, 31.54), (-15.75, 31.42), (-13.00, 30.47), (-8.88, 29.33),
        (-7.90, 29.55), (-6.90, 30.10), (-6.55, 30.45),
    ],
    "collar_k": [
        (13.45, 19.25), (13.00, 19.43), (12.75, 19.36), (12.67, 19.25), (12.56, 18.50), (11.75, 16.99),
        (11.50, 16.05), (10.99, 15.25), (10.96, 14.75), (10.75, 14.56), (10.38, 14.59), (10.00, 14.90),
        (9.85, 15.25), (9.95, 16.00), (10.58, 18.50), (10.58, 19.25), (10.35, 19.75), (10.25, 19.88),
        (9.88, 20.07), (8.62, 20.08), (7.75, 20.34), (6.12, 21.26), (5.50, 21.21), (5.09, 20.75),
        (4.84, 20.12), (4.81, 19.50), (4.62, 19.00), (4.00, 17.83), (3.80, 17.25), (3.50, 16.95),
        (3.12, 16.95), (2.85, 17.12), (2.73, 17.50), (2.81, 18.12), (2.69, 18.38), (2.38, 18.61),
        (1.62, 18.88), (1.25, 18.93), (0.88, 18.92), (0.67, 18.75), (0.34, 17.38), (0.35, 16.75),
        (-0.17, 15.25), (-0.29, 14.38), (-0.27, 12.75), (-0.12, 12.26), (0.25, 11.97), (0.75, 11.87),
        (2.12, 12.19), (2.50, 12.19), (5.25, 11.34), (6.12, 11.15), (6.88, 10.84), (7.62, 10.65),
        (8.38, 10.29), (9.12, 9.64), (9.50, 9.15), (9.75, 8.98), (10.12, 8.87), (10.50, 8.97),
        (10.75, 9.26), (11.17, 10.12), (11.80, 11.88), (12.32, 12.88), (12.57, 13.75), (13.43, 15.75),
        (13.83, 17.38), (13.79, 18.88),
    ],
    "ec_r": [
        (21.68, 20.38), (21.12, 20.66), (18.38, 21.55), (17.25, 21.81), (15.62, 21.79), (14.38, 21.41),
        (13.38, 20.90), (13.10, 20.62), (12.60, 19.38), (11.40, 15.50), (11.15, 14.88), (10.52, 13.75),
        (10.06, 13.25), (9.31, 9.88), (9.36, 9.00), (9.56, 8.12), (9.75, 7.87), (10.12, 7.75),
        (11.25, 8.10), (11.62, 8.04), (12.06, 7.75), (12.26, 7.38), (12.40, 6.75), (12.32, 3.88),
        (12.71, 2.62), (13.07, 2.00), (13.62, 1.34), (14.62, 0.71), (15.62, 0.33), (16.50, 0.27),
        (17.38, 0.39), (18.28, 0.75), (18.76, 1.12), (19.03, 1.50), (19.22, 2.12), (20.25, 3.34),
        (20.59, 4.25), (20.88, 4.75), (21.27, 6.00), (21.30, 6.75), (21.41, 7.38), (21.36, 7.50),
        (21.00, 7.56), (20.65, 7.50), (20.38, 7.33), (20.04, 6.75), (19.69, 5.25), (19.45, 4.62),
        (18.75, 3.79), (18.10, 3.38), (17.62, 3.19), (16.88, 3.09), (16.12, 3.21), (15.38, 3.50),
        (14.91, 3.88), (14.60, 4.25), (14.31, 4.75), (14.08, 5.38), (14.02, 6.12), (14.22, 7.00),
        (14.70, 8.25), (15.51, 11.00), (15.62, 11.14), (15.75, 11.15), (16.88, 10.89), (17.75, 10.99),
        (18.88, 11.59), (19.18, 11.88), (19.28, 12.12), (19.30, 12.70), (19.31, 13.25), (19.31, 13.50),
        (19.18, 13.75), (18.62, 14.29), (17.00, 14.33), (16.12, 14.70), (15.62, 15.12), (15.33, 15.50),
        (15.08, 16.00), (14.97, 16.88), (15.25, 17.55), (15.88, 17.63), (17.00, 17.98), (17.62, 17.98),
        (18.25, 17.82), (19.75, 16.91), (20.50, 16.91), (21.00, 17.09), (21.35, 17.38), (21.51, 17.75),
        (21.81, 19.25), (21.79, 20.25),
    ],
    "cc_c": [
        (21.62, 6.29), (21.12, 6.79), (20.75, 6.93), (20.12, 6.91), (19.86, 6.50), (19.66, 5.62),
        (19.29, 4.62), (19.00, 4.20), (18.50, 3.69), (17.50, 3.21), (16.38, 3.21), (15.50, 3.59),
        (15.00, 3.94), (14.59, 4.50), (14.34, 5.00), (14.19, 5.62), (14.19, 6.38), (14.81, 8.38),
        (14.81, 8.88), (14.69, 9.12), (14.50, 9.28), (13.88, 9.53), (12.25, 9.98), (11.25, 10.36),
        (10.38, 10.80), (10.25, 10.78), (10.00, 10.54), (9.61, 9.75), (9.31, 8.50), (9.34, 7.88),
        (9.70, 7.50), (10.00, 7.34), (10.88, 7.16), (11.50, 6.91), (12.00, 6.43), (12.19, 6.00),
        (12.19, 3.88), (12.46, 2.88), (12.84, 2.12), (13.19, 1.62), (13.95, 0.88), (14.62, 0.47),
        (15.25, 0.21), (15.88, 0.07), (17.62, 0.09), (18.12, 0.21), (19.12, 0.71), (19.88, 1.31),
        (20.41, 2.00), (20.79, 2.75), (20.97, 3.62), (21.16, 3.88), (21.40, 4.62), (21.45, 5.25),
        (21.66, 6.00),
    ],
    # overhang block: straight-sided polygon so its top edge can be rounded
    "box": [(3.86, 17.38), (9.38, 15.24), (9.92, 15.75), (10.91, 19.62), (10.25, 20.25), (7.0, 21.4), (5.62, 21.36)],
    # channel outer outline, as open chains (back -> front along the top,
    # then front end, then bottom front -> back)
    "chan_top": [
        (-13.97, 34.45), (-12.0, 33.75), (-10.0, 33.12), (-8.0, 32.0), (-7.0, 31.25), (-6.0, 30.12),
        (-5.0, 28.75), (-4.0, 26.88), (-3.0, 25.0), (-2.0, 23.25), (-1.0, 21.4), (-0.5, 20.55),
        (0.0, 19.9), (0.5, 19.45), (1.5, 18.95), (2.5, 18.55), (2.85, 18.3),
    ],
    "chan_end": [(2.85, 18.3), (2.92, 17.0), (2.75, 15.2), (2.0, 13.5), (1.05, 11.7)],
    "chan_bot": [
        (1.05, 11.7), (0.5, 10.95), (0.0, 10.65), (-1.0, 10.9), (-2.0, 11.35), (-3.0, 11.95),
        (-4.0, 12.6), (-5.0, 14.1), (-7.0, 17.4), (-9.0, 20.75), (-11.0, 24.05), (-12.5, 25.75),
        (-13.4, 26.5), (-13.97, 26.9),
    ],
    # cavity floor (top of the channel floor), back -> front, overshooting both ends
    "cav_floor": [
        (-15.5, 29.3), (-14.0, 29.3), (-13.5, 29.6), (-13.0, 29.6), (-12.5, 29.4), (-12.0, 29.0),
        (-11.5, 28.5), (-11.0, 28.0), (-10.5, 27.3), (-8.0, 22.6), (-6.0, 18.8), (-4.5, 16.0),
        (-3.5, 15.3), (-2.5, 14.75), (-1.5, 14.2), (-0.5, 13.95), (0.5, 13.75), (1.2, 13.4),
        (2.2, 12.0), (3.5, 10.5),
    ],
    # relief pocket between the side plates (above the C-hook core)
    "relief": [
        (10.3, 10.95), (11.25, 10.5), (12.25, 10.1), (13.88, 9.65), (14.69, 9.25), (14.9, 9.25),
        (14.9, 23.0), (11.2, 23.0), (11.2, 15.0), (10.3, 15.0),
    ],
    # centre bottom of the U strap under the hook end
    "strap_bottom": [
        (9.3, 8.6), (9.5, 7.9), (10.0, 7.38), (10.5, 7.25), (11.0, 7.12), (11.5, 6.95),
        (12.0, 6.45), (12.15, 6.2),
    ],
}


# ------------------------------------------------------------------- helpers
def _pts(yz, x):
    return [V(x, y, z) for y, z in yz]


def _densify(yz, step=0.3, closed=True):
    """Insert points along long segments (even facets, clean lofts)."""
    out = []
    n = len(yz)
    for i in range(n if closed else n - 1):
        (ay, az), (by, bz) = yz[i], yz[(i + 1) % n]
        k = max(1, int(math.ceil(math.hypot(by - ay, bz - az) / step)))
        out += [(ay + (by - ay) * j / k, az + (bz - az) * j / k) for j in range(k)]
    if not closed:
        out.append(yz[-1])
    return out


def _closed_poly(yz, x):
    """Closed polyline section. Outlines are densified to <= 0.25-0.4 mm, so the
    chord error on the tightest rounds is < 0.01 mm (far below print resolution);
    polylines loft exactly, where interpolating splines can loop at corners."""
    return Part.makePolygon(_pts(yz, x) + [V(x, *yz[0])])


def _mirrored(s):
    return s.fuse(s.mirror(V(0, 0, 0), V(1, 0, 0)))


def _signed_area(yz):
    return 0.5 * sum(yz[i - 1][0] * yz[i][1] - yz[i][0] * yz[i - 1][1] for i in range(len(yz)))


def _resample(yz, n):
    """n points evenly spaced by arc length around a closed polygon."""
    seg = [math.hypot(yz[(i + 1) % len(yz)][0] - yz[i][0], yz[(i + 1) % len(yz)][1] - yz[i][1])
           for i in range(len(yz))]
    total = sum(seg)
    out, i, acc = [], 0, 0.0
    for k in range(n):
        t = total * k / n
        while acc + seg[i] < t:
            acc += seg[i]
            i += 1
        f = (t - acc) / seg[i] if seg[i] else 0.0
        a, b = yz[i], yz[(i + 1) % len(yz)]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def _inset(yz, d, n):
    """Closed outline pulled in by d (exact 2D offset), resampled to n points,
    starting nearest yz[0] and with yz's orientation, so sections loft cleanly."""
    if d > 1e-4:
        from shapely.geometry import Polygon  # bundled with FreeCAD
        g = Polygon(yz).buffer(-d, quad_segs=16)
        if g.geom_type != "Polygon":
            g = max(g.geoms, key=lambda q: q.area)
        poly = list(g.exterior.coords)[:-1]
    else:
        poly = list(yz)
    if (_signed_area(poly) > 0) != (_signed_area(yz) > 0):
        poly.reverse()
    pts = _resample(poly, n)
    k = min(range(n), key=lambda i: (pts[i][0] - yz[0][0]) ** 2 + (pts[i][1] - yz[0][1]) ** 2)
    return pts[k:] + pts[:k]


def _quarter(steps):
    return [i * math.pi / 2 / steps for i in range(steps + 1)]


def _band_stations(x0, x1, r_in, r_out, steps=None):
    """(x, inset) stations: quarter-round of r_in at the x0 face and of r_out
    at the x1 face, flat in between."""
    steps = steps or RES["steps"]
    w = x1 - x0
    if r_in + r_out > w:
        s = w / (r_in + r_out)
        r_in, r_out = r_in * s, r_out * s
    st = []
    if r_in > 0:
        st += [(x0 + r_in - r_in * math.cos(t), r_in - r_in * math.sin(t)) for t in _quarter(steps)]
    else:
        st.append((x0, 0.0))
    if r_out > 0:
        tail = [(x1 - r_out + r_out * math.sin(t), r_out - r_out * math.cos(t)) for t in _quarter(steps)]
        if tail[0][0] - st[-1][0] < 1e-6:
            tail = tail[1:]
        st += tail
    else:
        st.append((x1, 0.0))
    return st


def _rounded_band(yz, x0, x1, r_in=0.0, r_out=0.0):
    """Profile carried across [x0, x1] with rounded edges on either face."""
    base = _densify(yz, RES["seg"])
    if r_in <= 0 and r_out <= 0:
        return Part.Face(_closed_poly(base, x0)).extrude(V(x1 - x0, 0, 0))
    n = max(60, int(sum(math.hypot(base[i][0] - base[i - 1][0], base[i][1] - base[i - 1][1])
                        for i in range(len(base))) / RES["seg"]))
    wires = [_closed_poly(_inset(base, d, n), x) for x, d in _band_stations(x0, x1, r_in, r_out)]
    return Part.makeLoft(wires, True, True)


def _poly_face(yz, x):
    return Part.Face(Part.makePolygon(_pts(yz, x) + [V(x, *yz[0])]))


def _hull(yz):
    pts = sorted(set(yz))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def _yz_box(y0, y1, z0, z1, x0, x1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _cyl_x(cy, cz, r, x0, x1):
    return Part.makeCylinder(r, x1 - x0, V(x0, cy, cz), V(1, 0, 0))


def _arc_drop(x, half_w, r):
    """How far a quarter-round of radius r at |x| = half_w pulls the edge in."""
    u = abs(x) - (half_w - r)
    if u <= 0 or r <= 0:
        return 0.0
    return r - math.sqrt(max(r * r - u * u, 0.0))


def _interp(chain, y):
    """z on a chain of (y, z) points at y (chain monotonic in y, any direction)."""
    c = sorted(chain)
    if y <= c[0][0]:
        return c[0][1]
    for (ya, za), (yb, zb) in zip(c, c[1:]):
        if y <= yb:
            return za + (zb - za) * (y - ya) / (yb - ya)
    return c[-1][1]


def _stretch(chain, i, cap=2.2):
    """1/cos(slope) at chain[i]: turns a normal offset into a vertical one."""
    a, b = chain[max(i - 1, 0)], chain[min(i + 1, len(chain) - 1)]
    s = (b[1] - a[1]) / (b[0] - a[0]) if b[0] != a[0] else 1e9
    return min(math.sqrt(1 + s * s), cap)


# --------------------------------------------------------------- wire seats
def _fork_slot(p, d, x0, x1):
    cy, cz = p["fork_bore_c"]
    r = d / 2
    return _cyl_x(cy, cz, r, x0, x1).fuse(_yz_box(cy - r, cy + r, p["fork_tip_z"] - 3.0, cz, x0, x1))


def _c_bore(p, d, x0, x1):
    cy, cz = p["c_bore_c"]
    return _cyl_x(cy, cz, d / 2, x0, x1)


def _e_seat(p, d, x0, x1):
    cy, cz = p["e_seat_c"]
    return _cyl_x(cy, cz, d / 2, x0, x1)


def _refill(solid, profile_yz, band, seat_fn, p, key, mirror=True):
    """If a seat is set smaller than scanned, add back material inside the
    profile's convex hull before the seat is re-cut."""
    if p[key] >= SCAN_SEATS[key] - 1e-6:
        return solid
    x0, x1 = band
    hull = _poly_face(_hull(profile_yz), x0).extrude(V(x1 - x0, 0, 0))
    fill = seat_fn(p, SCAN_SEATS[key], x0, x1).common(hull)
    return solid.fuse(_mirrored(fill) if mirror else fill)


# --------------------------------------------------------------- features
def build_channel(p):
    hw = p["chan_half_w"]
    back = p["chan_back_y"]
    top = _densify([(back, PROFILES["chan_top"][0][1])] + PROFILES["chan_top"][1:], RES["seg"], closed=False)
    bot = _densify(PROFILES["chan_bot"][:-1] + [(back, PROFILES["chan_bot"][-1][1])], RES["seg"], closed=False)
    end = PROFILES["chan_end"]
    r_out, r_end, r_top = p["chan_r_out"], p["chan_r_out_end"], p["chan_r_top"]
    y_taper = p["chan_r_taper_y"]

    def r_at(y):
        if y <= y_taper[0]:
            return r_out
        f = min((y - y_taper[0]) / (y_taper[1] - y_taper[0]), 1.0)
        return r_out + (r_end - r_out) * f

    ci = hw - p["chan_wall"]
    r_top = min(r_top, (hw - ci) / 2)

    def top_drop(x):
        u = ci + r_top - abs(x)       # inner edge of the wall top
        inner = r_top if u >= r_top else (r_top - math.sqrt(r_top * r_top - u * u) if u > 0 else 0.0)
        return max(_arc_drop(x, hw, r_top), inner)

    def outer_section(x, _):
        tz = [(y, z - top_drop(x) * _stretch(top, i, 1.4)) for i, (y, z) in enumerate(top)]
        bz = []
        for i, (y, z) in enumerate(bot):
            dz = _arc_drop(x, hw, min(r_at(y), hw - 0.05)) * _stretch(bot, i, 1.4)
            bz.append((y, min(z + dz, _interp(tz, y) - 1.0)))
        z_t, z_b = end[0][1], end[-1][1]
        dz_t, dz_b = tz[-1][1] - top[-1][1], bz[0][1] - bot[0][1]
        ez = [(y, z + dz_t + (dz_b - dz_t) * (z_t - z) / (z_t - z_b)) for y, z in end]
        return _closed_poly(tz + ez[1:-1] + bz, x)

    xs = {round(s * (hw - r_out + r_out * math.sin(t)), 6) for t in _quarter(2 * RES["steps"]) for s in (-1, 1)}
    xs |= {round(s * (hw - r_top + r_top * math.sin(t)), 6) for t in _quarter(RES["steps"] // 2) for s in (-1, 1)}
    xs |= {round(s * (ci + r_top - r_top * math.cos(t)), 6) for t in _quarter(RES["steps"] // 2) for s in (-1, 1)}
    outer = Part.makeLoft([outer_section(x, 0) for x in sorted(xs)], True, True)

    ri = min(p["chan_r_in"], ci - 0.05)
    fl = _densify(PROFILES["cav_floor"], RES["seg"], closed=False)
    zt = 40.0

    def cav_section(x):
        f = [(y, z + _arc_drop(x, ci, ri) * _stretch(fl, i, 1.2)) for i, (y, z) in enumerate(fl)]
        return _closed_poly(f + [(f[-1][0], zt), (f[0][0], zt)], x)

    xs = sorted({round(s * (ci - ri + ri * math.sin(t)), 6) for t in _quarter(2 * RES["steps"]) for s in (-1, 1)})
    cav = Part.makeLoft([cav_section(x) for x in xs], True, True)
    chan = outer.cut(cav)

    # floor window: vertical stadium through the slanted floor
    w = p["win_half_w"]
    ya, yb = p["win_y0"] + w, p["win_y1"] - w
    win = Part.makeCylinder(w, 30, V(0, ya, 8), V(0, 0, 1))
    win = win.fuse(Part.makeCylinder(w, 30, V(0, yb, 8), V(0, 0, 1)))
    win = win.fuse(Part.makeBox(2 * w, yb - ya, 30, V(-w, ya, 8)))
    return chan.cut(win)


def build_box(p):
    x0, x1 = p["box_x"]
    yz = PROFILES["box"]
    rx, rz = p["box_r_top"]
    rx = min(rx, x1 - x0)

    def section(x, dz):
        # round the inner (x0) top edge: the top points (3..6) drop by dz
        pts = [(y, z - dz) if i >= 3 else (y, z) for i, (y, z) in enumerate(yz)]
        return Part.makePolygon(_pts(pts, x) + [V(x, *pts[0])])

    if rx <= 0 or rz <= 0:
        return _mirrored(_poly_face(yz, x0).extrude(V(x1 - x0, 0, 0)))
    st = [(x0 + rx - rx * math.cos(t), rz - rz * math.sin(t)) for t in _quarter(2 * RES["steps"])]
    if x1 > st[-1][0] + 1e-6:
        st.append((x1, 0.0))
    return _mirrored(Part.makeLoft([section(x, dz) for x, dz in st], True, True))


def build_strap(p):
    """Block for the U strap under the hook end (shaped by the cutters)."""
    y0, y1 = p["strap_block_y0"], p["strap_y"][1]
    hw = p["strap_half_w"]
    return Part.makeBox(2 * hw, y1 - y0, p["strap_top"] - 5.0, V(-hw, y0, 5.0))


def build_strap_cutter(p):
    """Material below the strap's elliptical underside."""
    y0, y1 = p["strap_y"]
    a = p["strap_ell_a"]
    zb = [(y, z) for y, z in _densify(PROFILES["strap_bottom"], 0.25, closed=False) if y0 <= y <= y1]

    def drop(x, y):
        u = min(abs(x) / a, 1.0)
        return _interp(p["strap_depth"], y) * (1 - math.sqrt(1 - u * u))

    def section(x):
        top = [(y, z + drop(x, y)) for y, z in zb]
        return Part.makePolygon(_pts([(y0, -2.0), (y1, -2.0)] + top[::-1], x) + [V(x, y0, -2.0)])

    xs = sorted({round(s * a * math.sin(t), 6) for t in _quarter(2 * RES["steps"]) for s in (-1, 1)})
    xs = [-a - 1.0] + xs + [a + 1.0]
    return Part.makeLoft([section(x) for x in xs], True, True)


def build_hook_cutters(p):
    """Relief between the side plates behind the E tines, the C-hook taper,
    the flex slits beside the overhang tabs, and the inner U of the strap."""
    cutters = []
    w = p["relief_half_w"]
    relief = _poly_face(PROFILES["relief"], -w).extrude(V(2 * w, 0, 0))
    edge = list(p["c_taper"])
    ring = [(x, y) for y, x in edge] + [(8.0, edge[-1][0]), (8.0, edge[0][0])]
    taper = Part.Face(Part.makePolygon([V(x, y, -1.0) for x, y in ring] + [V(ring[0][0], ring[0][1], -1.0)]))
    taper = _mirrored(taper.extrude(V(0, 0, p["c_taper_z"] + 1.0)))
    # flex slit between each overhang tab and the collar wall, open from
    # below; the tab stays joined to the collar only by a hinge along its top
    x0, x1 = p["tab_gap_x"]
    if x1 - x0 > 1e-3:
        y0, y1 = p["tab_gap_y"]
        z0, hinge = p["tab_gap_z0"], p["tab_hinge"]
        bx = PROFILES["box"]
        top = [bx[0], bx[6], bx[5], bx[4], bx[3]]          # box top edge, back -> front
        ys = [y0 + (y1 - y0) * i / 40.0 for i in range(41)]
        roof = [(y, max(_interp(top, y) - hinge, z0 + 0.3)) for y in ys]
        ring = [(y0, z0), (y1, z0)] + roof[::-1]
        slit = Part.Face(Part.makePolygon([V(x0, y, z) for y, z in ring] + [V(x0, *ring[0])]))
        cutters.append(_mirrored(slit.extrude(V(x1 - x0, 0, 0))))
    # inner U of the strap under the overhang block
    r, z0 = p["strap_in_r"], p["strap_in_z"]
    y0, y1 = p["strap_in_y"]
    arc = [(r * math.sin(t), z0 + r - r * math.cos(t)) for t in
           (math.pi / 2 * (i / 12.0) for i in range(-12, 13))]
    ztop = p["strap_in_ztop"]
    ring = arc + [(r, ztop), (-r, ztop)]
    strap_in = Part.Face(Part.makePolygon([V(x, y0, z) for x, z in ring] + [V(ring[0][0], y0, ring[0][1])]))
    strap_in = strap_in.extrude(V(0, y1 - y0, 0))
    return cutters + [relief, taper, strap_in]


def build(p=None):
    p = dict(PARAMS, **(p or {}))
    tr = p["tine_round"]
    parts = [build_channel(p)]

    tine_r = _mirrored(_rounded_band(PROFILES["tine_r"], *p["tine_r_x"], r_in=tr))
    tine_k = _mirrored(_rounded_band(PROFILES["tine_k"], *p["tine_k_x"], r_out=tr))
    tine_r = _refill(tine_r, PROFILES["tine_r"], p["tine_r_x"], _fork_slot, p, "fork_bore_d")
    tine_k = _refill(tine_k, PROFILES["tine_k"], p["tine_k_x"], _fork_slot, p, "fork_bore_d")
    parts += [tine_r, tine_k]

    parts.append(_mirrored(_rounded_band(PROFILES["collar_k"], *p["collar_x"], r_out=p["collar_round"])))
    parts.append(build_box(p))

    ec = _mirrored(_rounded_band(PROFILES["ec_r"], *p["ec_x"], r_in=p["ec_round_in"], r_out=p["ec_round_out"]))
    ec = _refill(ec, PROFILES["ec_r"], p["ec_x"], _c_bore, p, "c_bore_d")
    ec = _refill(ec, PROFILES["ec_r"], p["ec_x"], _e_seat, p, "e_seat_d")
    parts.append(ec)
    cc = _mirrored(_rounded_band(PROFILES["cc_c"], 0.0, p["cc_half_w"], r_out=p["ec_round_out"]))
    cc = _refill(cc, PROFILES["cc_c"], (0.0, p["cc_half_w"]), _c_bore, p, "c_bore_d")
    parts.append(cc)
    parts.append(build_strap(p))

    shape = parts[0].multiFuse(parts[1:])
    # strap underside, hook-end cutters and wire seats (re-cut exactly), in one boolean
    X = 8.0
    cy, cz = p["fork_bore_c"]
    shape = shape.cut([
        build_strap_cutter(p),
        *build_hook_cutters(p),
        _cyl_x(cy, cz, p["fork_bore_d"] / 2, -X, X),
        _mirrored(_fork_slot(p, p["fork_bore_d"], p["tine_r_x"][0], X)),
        _c_bore(p, p["c_bore_d"], -X, X),
        _e_seat(p, p["e_seat_d"], -X, X),
    ])
    if p.get("refine"):
        shape = shape.removeSplitter()  # merges coplanar facets; slow (~90 s)
    solids = sorted(shape.Solids, key=lambda s: -s.Volume)
    if len(solids) > 1:
        App.Console.PrintWarning("DishwasherClip: %d separate solids\n" % len(solids))
        return Part.makeCompound(solids)
    return solids[0]


# ------------------------------------------------------- FreeCAD integration
# The document keeps the solid as a plain Part::Feature plus a "Params"
# spreadsheet. FreeCAD 1.1 refuses to restore Python feature objects from
# modules that are not installed add-ons, so instead of a FeaturePython the
# rebuild is driven by build_clip.py, which reads the sheet back in.
SHEET = "Params"
CLIP = "DishwasherClip"


def _param_notes():
    """Comments next to each PARAMS entry, for the sheet's notes column."""
    import re
    notes = {}
    try:
        for line in open(__file__, encoding="utf-8"):
            m = re.match(r'\s*"(\w+)":.*?#\s*(.*)$', line)
            if m:
                notes[m.group(1)] = m.group(2).strip()
    except OSError:
        pass
    return notes


def _fmt(v):
    if isinstance(v, tuple) and v and isinstance(v[0], tuple):
        return "'" + ", ".join("%g:%g" % pair for pair in v)
    if isinstance(v, tuple):
        return "'" + ", ".join("%g" % c for c in v)
    return "%g" % v


def _parse(text, like):
    if not isinstance(like, tuple):
        return float(text)
    text = str(text).lstrip("'")
    if like and isinstance(like[0], tuple):
        return tuple(tuple(float(c) for c in item.split(":")) for item in text.split(","))
    return tuple(float(c) for c in text.split(","))


def write_params(doc, p):
    sheet = doc.getObject(SHEET) or doc.addObject("Spreadsheet::Sheet", SHEET)
    notes = _param_notes()
    for row in range(2, 200):           # drop rows left over from older parameter sets
        for col in "ABC":
            if sheet.getContents("%s%d" % (col, row)):
                sheet.clear("%s%d" % (col, row))
    sheet.set("A1", "parameter")
    sheet.set("B1", "value (mm)")
    sheet.set("C1", "notes - edit column B, then run build_clip.py")
    for row, (k, v) in enumerate(PARAMS.items(), start=2):
        sheet.set("A%d" % row, k)
        sheet.set("B%d" % row, _fmt(p.get(k, v)))
        sheet.set("C%d" % row, notes.get(k, ""))
    sheet.setColumnWidth("A", 150)
    sheet.setColumnWidth("B", 260)
    sheet.setColumnWidth("C", 480)
    return sheet


def read_params(doc):
    """PARAMS overridden by whatever is in the document's Params sheet."""
    p = dict(PARAMS)
    sheet = doc.getObject(SHEET)
    if sheet is None:
        return p
    row = 2
    while True:
        try:
            key = sheet.get("A%d" % row)
        except ValueError:
            break
        if key in PARAMS:
            try:
                p[key] = _parse(sheet.get("B%d" % row), PARAMS[key])
            except (ValueError, TypeError):
                App.Console.PrintWarning("Params: could not read %s, using default\n" % key)
        row += 1
    return p


def rebuild(doc, p=None):
    """(Re)build the clip solid in `doc` from `p` (default: its Params sheet)."""
    p = read_params(doc) if p is None else dict(PARAMS, **p)
    write_params(doc, p)
    obj = doc.getObject(CLIP) or doc.addObject("Part::Feature", CLIP)
    obj.Shape = build(p)
    doc.recompute()
    return obj


def export_all(outdir, doc=None):
    """Rebuild and write dishwasher_clip.FCStd / .step / .stl into outdir."""
    import MeshPart
    if doc is None:
        doc = App.newDocument("DishwasherClip")
    shape = rebuild(doc).Shape
    doc.saveAs(os.path.join(outdir, "dishwasher_clip.FCStd"))
    shape.exportStep(os.path.join(outdir, "dishwasher_clip.step"))
    # tessellate until the mesh is closed and manifold (slicer-ready)
    for lin, ang in ((0.02, 0.1), (0.015, 0.08), (0.03, 0.12), (0.01, 0.06), (0.04, 0.15)):
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=lin, AngularDeflection=ang, Relative=False)
        if mesh.hasNonManifolds():
            mesh.removeNonManifolds()
        if mesh.isSolid() and not mesh.hasNonManifolds():
            break
    print("stl: %d facets, closed=%s, non-manifold=%s" % (mesh.CountFacets, mesh.isSolid(), mesh.hasNonManifolds()))
    mesh.write(os.path.join(outdir, "dishwasher_clip.stl"))
    print("valid=%s solids=%d volume=%.1f mm3 bbox=%s" % (
        shape.isValid(), len(shape.Solids), shape.Volume, shape.BoundBox))
    return shape
