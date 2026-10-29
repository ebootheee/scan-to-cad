# Thermador DWHD640JPR/93 lower-rack flip-tine pivot clip - parametric replica (v5, fitted to 3D scan)
# Run headless:  freecadcmd tine_clip_v5.py
# Or in FreeCAD GUI: Macro > Macros... > Execute.
#
# Coordinate frame (as the clip sits on the rack):
#   X = length   (x=0 is the tip of the two LEGS, +X toward the J HOOK)
#   Y = width    (mirror-symmetric about y=0)
#   Z = up       (z=0 is the underside of the legs / leg-end wall)
# mm throughout. (S) = fitted to the Revopoint scan (scan_aligned.ply in this folder, same frame),
# (M) = calipers. Scan-smoothed edges are replaced by the clean design geometry they imply.

import math, os
import FreeCAD as App
import Part, Mesh
from FreeCAD import Vector as V

# ---------------------------------------------------------------- parameters
# two legs (flat plates, upturned tips, U slot cradles a rack wire running along Y)
LEG_TOP      = 11.15  # (S) top of the leg tips
LEG_YO0      = 4.97   # (S) outer half-width at the leg tip
LEG_YO1      = 4.65   # (S) outer half-width where the legs meet the leg-end wall (plates converge)
LEG_T        = 2.15   # (S) plate thickness
LEG_TIP_EDGE_R  = 0.4  # (S) side-view round: tip face to top
LEG_SLOT_EDGE_R = 0.8  # (S) side-view round: top to slot wall
LEG_TOP_R    = 1.6    # (S) round along the outer top edge of each leg (tip and slot flank)
LEG_Z0       = 2.62   # (S) underside of the leg tips
LEG_TIP_R    = 4.3    # (S) big radius from the tip face round into the underside
LEG_STEP_X0  = 6.1    # (S) underside steps down from LEG_Z0 here ...
LEG_STEP_X1  = 8.37   # (S) ... to z=0 here (straight ramp)
LEG_STEP_R0  = 2.0    # (S) fillet at the top of the ramp
LEG_STEP_R1  = 1.0    # (S) fillet at the bottom of the ramp
LEG_SLOT_X0  = 3.5    # (S) vertical tip-side wall of the U slot
LEG_SLOT_X   = 6.0    # (S) centre of the slot's bottom arc
LEG_SLOT_Z   = 6.65   # (S) bottom of the slot
LEG_SLOT_R   = 2.9    # (S) radius of the slot's bottom arc
LEG_FLANK    = 60.0   # (S) box-side wall of the slot: straight flank at this angle, tangent to the arc

# leg-end wall + bridge over the bar arch
LE_X0        = 8.45   # (S) leg-side face of the bridge
LE_X1        = 11.5   # (S) inside face (box cavity starts here)
LE_TOP       = 11.05  # (S) top of the bridge on the centreline
BRIDGE_HW    = 3.0    # (S) half-width of the bridge between the slot flanks
BRIDGE_CAP_R = 4.5    # (S) end-view crown radius of that bridge
LE_OUT_R     = 0.8    # (S) side-view round on the bridge's leg-side top edge
LE_IN_R      = 1.2    # (S) side-view round on the bridge's box-side top edge
FLARE_R0     = 0.5    # (S) plan-view fillet where the leg plates step out to the box ...
FLARE_R1     = 0.6    # (S) ... and on the outer corner of that step
BOX_X0       = 9.45   # (S) where the box side faces begin

# both end bridges: top is flat across the middle, rounded down to the sides
DOME_R       = 4.0    # (S) corner radius in end view (flat top = W - 2*DOME_R)
END_BOT_R    = 1.3    # (S) end-view round on the bottom outer edges of both end walls

# box
W            = 11.6   # (S) outside width of the box
WALL         = 1.5    # (S) side-wall thickness
WALL_TOP     = 9.45   # (S) top of the side walls
WALL_TOP_R   = 1.3    # (S) outer top edge round
WALL_IN_R    = 0.15   # (S) inner top edge round

# bar arches through both end walls (the 3.5 mm bar runs along X under the bridges)
ARCH_HW      = 2.3    # (S) half-width where the lead-in flare ends
ARCH_MOUTH   = 3.2    # (S) half-width at z=0 (lead-in flare)
ARCH_FLARE_Z = 4.5    # (S) flare ends here; sides then run straight into the round top
ARCH_TOP_LEG = 9.1    # (S) top of the arch through the leg-end wall
ARCH_R_LEG   = 2.1    # (S) radius of its round top
ARCH_TOP_HOOK = 9.35  # (S) top of the arch through the hook-end wall
ARCH_R_HOOK  = 2.35   # (S) radius of its round top

# flex panels (side wall between the slits) carrying the snap lips
PANEL_X0     = 12.65  # (S) slit 1 = LE_X1 .. PANEL_X0
PANEL_X1     = 19.1   # (S) slit 2 = PANEL_X1 .. HE_X0
SLIT_TOP     = 5.4    # (S) slits are open from below up to here (round top)
PANEL_Z0     = 0.2    # (S) panel underside (just above the leg-end wall underside)
PANEL_BOT_R  = 2.0    # (S) outer bottom edge round of the panel (end view)
PANEL_END_R  = 1.2    # (S) bottom corners of the panel (side view) - flares the slit mouths
LIP_TIP_Y    = 1.2    # (S) half-gap between the lip tips (throat = 2 * this)
LIP_TIP_Z    = 4.4    # (S) bottom of the vertical tip face
LIP_FACE_Y   = 1.97   # (S) inner lead-in face reaches z=PANEL_Z0 here (before rounding)
LIP_BOT_R    = 2.0    # (S) round between the lead-in face and the underside
LIP_TOP_IN   = 4.98   # (S) lip top at the tip ...
LIP_TOP_OUT  = 4.2    # (S) ... sloping down to here at the wall
LIP_TIP_R    = 0.3    # (S)
LIP_ROOT_R   = 0.4    # (S) fillet where the lip top meets the wall
# lead-in chamfer under the leg end of each lip: plane z = LEAD_Z0 - LEAD_KX*(x-PANEL_X0) - LEAD_KY*(|y|-LIP_TIP_Y)
LEAD_Z0      = 4.56   # (S)
LEAD_KX      = 0.80   # (S)
LEAD_KY      = 1.81   # (S)

# vertical ribs on the outside of each flex panel
RIB_X        = (13.8, 17.8)  # (S)
RIB_PROUD    = 0.27   # (S)
RIB_R        = 2.1    # (S) radius of the rib's rounded face
RIB_Z0       = 2.2    # (S) (= where the panel's bottom round ends)
RIB_Z1       = 8.2    # (S)

# hook-end wall + J hook (drops over a rack wire running along Y)
HE_X0        = 20.05  # (S) inside face of the hook-end wall
HE_Z0        = 0.3    # (S) underside of the hook-end wall
HE_TOP       = 11.7   # (S) top of the full-width part of the hook-end wall (the hook rises out of it)
HE_BOT_R     = 1.3    # (S) round on the bottom edge of the wall's inside face
STEM_X0      = 21.55  # (S) full box width ends here
HOOK_ID      = 5.03   # (S) inside diameter (calipers said 5.3)
HOOK_T       = 1.8    # (S) wall thickness -> top of part at 16.0 (M ~16)
HOOK_CZ      = 11.68  # (S) height of hook hole centre
HOOK_X_IN    = 22.75  # (S) inside face of the J's inner leg
HOOK_FLANK   = 72.0   # (S) outer flank from the hook-end wall up to the J, tangent to the J
HOOK_TIP_Z   = 7.45   # (S) bottom of the J's outer leg (at the edges of the notch)
HOOK_HW0     = 4.12   # (S) half-width of the hook from the wall to HOOK_TX0
HOOK_HW1     = 2.82   # (S) half-width from HOOK_TX1 to the tip
HOOK_TX0     = 22.0   # (S) plan taper start
HOOK_TX1     = 27.8   # (S) plan taper end
HOOK_EDGE_R  = 1.0    # (S) round on the hook's side edges along the flank
NOTCH_R      = 2.53   # (S) half-moon notch cut up into the outer leg tip
NOTCH_TOP    = 9.76   # (S)

OUT_DIR      = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
NAME         = "tine_clip_v5"

# ---------------------------------------------------------------- derived + helpers
YW, YI = W / 2, W / 2 - WALL
BIG = 50
ri, ro = HOOK_ID / 2, HOOK_ID / 2 + HOOK_T
hcx = HOOK_X_IN + ri


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _pt(plane, u, v, c):
    return {"XZ": V(u, c, v), "YZ": V(c, u, v), "XY": V(u, v, c)}[plane]


def profile(plane, items, c=0.0):
    """Closed 2D profile -> Part.Face.  items: (u, v[, r]) vertices, r = fillet radius at that
    vertex (both neighbours must be lines); ("arc", um, vm) makes the edge from the previous vertex
    to the next one a 3-point arc through (um, vm)."""
    verts, arcs = [], {}
    for it in items:
        if it[0] == "arc":
            arcs[len(verts) - 1] = (it[1], it[2])
        else:
            verts.append((it[0], it[1], it[2] if len(it) > 2 else 0.0))
    n = len(verts)
    P = [V(u, v, 0) for u, v, _ in verts]
    ends = []                                   # (start-of-corner, end-of-corner, fillet arc or None)
    for i in range(n):
        r = verts[i][2]
        if r <= 0:
            ends.append((P[i], P[i], None)); continue
        a, b = P[i - 1], P[(i + 1) % n]
        d1 = (P[i] - a); d1.normalize()
        d2 = (b - P[i]); d2.normalize()
        th = math.acos(max(-1, min(1, (-d1).dot(d2))))
        t = r / math.tan(th / 2)
        t1, t2 = P[i] - d1 * t, P[i] + d2 * t
        bis = (d2 - d1); bis.normalize()
        mid = P[i] + bis * (r / math.sin(th / 2) - r)
        ends.append((t1, t2, mid))
    to3 = lambda p: _pt(plane, p.x, p.y, c)
    edges = []
    for i in range(n):
        s, e, mid = ends[i]
        if mid is not None:
            edges.append(Part.Arc(to3(s), to3(mid), to3(e)).toShape())
        nxt = ends[(i + 1) % n][0]
        if i in arcs:
            edges.append(Part.Arc(to3(e), _pt(plane, arcs[i][0], arcs[i][1], c), to3(nxt)).toShape())
        elif (e - nxt).Length > 1e-7:
            edges.append(Part.LineSegment(to3(e), to3(nxt)).toShape())
    return Part.Face(Part.Wire(Part.__sortEdges__(edges)))


def prism(plane, items, c0, c1):
    d = {"XZ": V(0, c1 - c0, 0), "YZ": V(c1 - c0, 0, 0), "XY": V(0, 0, c1 - c0)}[plane]
    return profile(plane, items, c0).extrude(d)


def mirror_y(pts):
    return [(-u, v) + tuple(r) for u, v, *r in reversed(pts)]


def dome(x0, x1, top, z0):
    """End-wall envelope (end view): flat top, DOME_R corners down to the box sides, END_BOT_R at the bottom."""
    return prism("YZ", [(-YW, z0, END_BOT_R), (YW, z0, END_BOT_R), (YW, top, DOME_R), (-YW, top, DOME_R)], x0, x1)


def arch(x0, x1, top, r):
    m, f, c = ARCH_MOUTH, ARCH_FLARE_Z, top - r
    return prism("YZ", [(-m, -1), (m, -1), (m, 0), (ARCH_HW, f), (r, c), ("arc", 0, top),
                        (-r, c), (-ARCH_HW, f), (-m, 0)], x0, x1)


def trim(shape, x0, x1, env):
    """Intersect only the x0..x1 slab of shape with env."""
    return shape.cut(box(x0, x1, -BIG, BIG, -BIG, BIG)).fuse(shape.common(box(x0, x1, -BIG, BIG, -BIG, BIG)).common(env))


# ---------------------------------------------------------------- legs (side view profile)
sa = math.radians(LEG_FLANK)
scz = LEG_SLOT_Z + LEG_SLOT_R
tan_pt = (LEG_SLOT_X + LEG_SLOT_R * math.sin(sa), scz - LEG_SLOT_R * math.cos(sa))
z_wall = scz - math.sqrt(LEG_SLOT_R ** 2 - (LEG_SLOT_X - LEG_SLOT_X0) ** 2)
x_flank_top = tan_pt[0] + (13 - tan_pt[1]) / math.tan(sa)
tip_cz = LEG_Z0 + LEG_TIP_R
leg_xz = [(0, tip_cz), (0, LEG_TOP, LEG_TIP_EDGE_R), (LEG_SLOT_X0, LEG_TOP, LEG_SLOT_EDGE_R),
          (LEG_SLOT_X0, z_wall), ("arc", LEG_SLOT_X, LEG_SLOT_Z), tan_pt, (x_flank_top, 13),
          (LE_X1, 13), (LE_X1, 0), (LEG_STEP_X1, 0, LEG_STEP_R1), (LEG_STEP_X0, LEG_Z0, LEG_STEP_R0),
          (LEG_TIP_R, LEG_Z0), ("arc", LEG_TIP_R * (1 - math.sqrt(.5)), tip_cz - LEG_TIP_R * math.sqrt(.5))]
leg_side = prism("XZ", leg_xz, -BIG, BIG)

legs = None
for s in (-1, 1):
    plan = [(0, s * (LEG_YO0 - LEG_T)), (0, s * LEG_YO0), (LE_X1, s * LEG_YO1), (LE_X1, s * (LEG_YO1 - LEG_T))]
    plate = leg_side.common(prism("XY", plan if s > 0 else plan[::-1], -1, 14))
    # round the outer top edge of the tip: end-view profile swept along the plate's plan taper
    rnd = [(-s * 1.0, -1), (s * LEG_YO0, -1), (s * LEG_YO0, LEG_TOP, LEG_TOP_R), (-s * 1.0, LEG_TOP)]
    env = profile("YZ", rnd if s > 0 else rnd[::-1], 0).extrude(V(LE_X1, -s * (LEG_YO0 - LEG_YO1), 0))
    plate = trim(plate, -1, LEG_SLOT_X, env)
    legs = plate if legs is None else legs.fuse(plate)

# ---------------------------------------------------------------- leg-end wall + bridge
le_plan = [(LE_X0, -LEG_YO1), (BOX_X0, -LEG_YO1, FLARE_R0), (BOX_X0, -YW, FLARE_R1), (LE_X1, -YW),
           (LE_X1, YW), (BOX_X0, YW, FLARE_R1), (BOX_X0, LEG_YO1, FLARE_R0), (LE_X0, LEG_YO1)]
le = prism("XY", le_plan, 0, 13)
cap = Part.makeCylinder(BRIDGE_CAP_R, LE_X1 - LE_X0 + 2, V(LE_X0 - 1, 0, LE_TOP - BRIDGE_CAP_R), V(1, 0, 0))
cap = cap.fuse(box(LE_X0 - 1, LE_X1 + 1, -BRIDGE_CAP_R, BRIDGE_CAP_R, -1, LE_TOP - BRIDGE_CAP_R))
le = le.common(leg_side.fuse(box(LE_X0 - 1, LE_X1 + 1, -BRIDGE_HW, BRIDGE_HW, -1, 14).common(cap)))
body = legs.fuse(le)

# ---------------------------------------------------------------- box side walls + flex panels
wall_yz = [(YI, 0), (YI, WALL_TOP, WALL_IN_R), (YW, WALL_TOP, WALL_TOP_R), (YW, 0)]
panel_yz = [(LIP_TIP_Y, LIP_TIP_Z), (LIP_TIP_Y, LIP_TOP_IN, LIP_TIP_R), (YI, LIP_TOP_OUT, LIP_ROOT_R),
            (YI, WALL_TOP, WALL_IN_R), (YW, WALL_TOP, WALL_TOP_R), (YW, PANEL_Z0, PANEL_BOT_R),
            (LIP_FACE_Y, PANEL_Z0, LIP_BOT_R)]
panel_side = prism("XZ", [(PANEL_X0, PANEL_Z0, PANEL_END_R), (PANEL_X1, PANEL_Z0, PANEL_END_R),
                          (PANEL_X1, 12), (PANEL_X0, 12)], -BIG, BIG)
for s in (-1, 1):
    m = (lambda p: p) if s > 0 else mirror_y
    for x0, x1 in ((LE_X1, PANEL_X0), (PANEL_X1, HE_X0)):            # above the slits
        w = prism("YZ", m(wall_yz), x0, x1)
        body = body.fuse(w.cut(box(x0 - 1, x1 + 1, -BIG, BIG, -1, SLIT_TOP)))
    panel = prism("YZ", m(panel_yz), PANEL_X0, PANEL_X1)
    body = body.fuse(panel.common(panel_side))
    for x0, x1 in ((LE_X1, PANEL_X0), (PANEL_X1, HE_X0)):            # round tops of the slits
        r = (x1 - x0) / 2
        fill = box(x0, x1, -BIG, BIG, SLIT_TOP - r, SLIT_TOP).cut(
            Part.makeCylinder(r, 2 * BIG, V(x0 + r, -BIG, SLIT_TOP - r), V(0, 1, 0)))
        body = body.fuse(fill.common(prism("YZ", m(wall_yz), x0, x1)))
    for xr in RIB_X:
        rib = Part.makeCylinder(RIB_R, RIB_Z1 - RIB_Z0, V(xr, s * (YW + RIB_PROUD - RIB_R), RIB_Z0))
        body = body.fuse(rib.common(box(xr - 3, xr + 3, *sorted((s * (YW - 0.01), s * (YW + 1))), 0, 10)))

# ---------------------------------------------------------------- hook-end wall + J hook (side profile)
fa = math.radians(HOOK_FLANK)
tp = (hcx - ro * math.sin(fa), HOOK_CZ + ro * math.cos(fa))
z_flank = tp[1] - (tp[0] - HE_X0) * math.tan(fa)
ma = (fa + math.pi / 2) / 2                                         # mid-angle of the outer arc
hook_xz = [(HE_X0, HE_Z0, HE_BOT_R), (HE_X0, z_flank), tp,
           ("arc", hcx + ro * math.cos(ma), HOOK_CZ + ro * math.sin(ma)),
           (hcx + ro, HOOK_CZ), (hcx + ro, HOOK_TIP_Z), (hcx + ri, HOOK_TIP_Z), (hcx + ri, HOOK_CZ),
           ("arc", hcx, HOOK_CZ + ri), (hcx - ri, HOOK_CZ), (hcx - ri, HE_Z0)]
hook_plan = [(HE_X0 - 1, -HOOK_HW0), (HOOK_TX0, -HOOK_HW0), (HOOK_TX1, -HOOK_HW1), (hcx + ro + 1, -HOOK_HW1),
             (hcx + ro + 1, HOOK_HW1), (HOOK_TX1, HOOK_HW1), (HOOK_TX0, HOOK_HW0), (HE_X0 - 1, HOOK_HW0)]
hook_side = prism("XZ", hook_xz, -BIG, BIG)
hook = hook_side.common(prism("XY", hook_plan, -1, 20))
# round the hook's side edges along the flank: end-view profile swept up the flank
fe = [(-HOOK_HW0, -25), (HOOK_HW0, -25), (HOOK_HW0, 0, HOOK_EDGE_R), (-HOOK_HW0, 0, HOOK_EDGE_R)]
fe_env = profile("YZ", [(u, v + z_flank) + tuple(r) for u, v, *r in fe], HE_X0).extrude(
    V(math.cos(fa), 0, math.sin(fa)) * ((tp[0] - HE_X0) / math.cos(fa) + 0.5))
hook = trim(hook, HE_X0, tp[0], fe_env)
he_wall = hook_side.common(box(HE_X0 - 1, STEM_X0, -YW, YW, -1, 20)).common(dome(HE_X0 - 1, STEM_X0, HE_TOP, HE_Z0))
notch = prism("YZ", [(-NOTCH_R, -1), (NOTCH_R, -1), (NOTCH_R, NOTCH_TOP - NOTCH_R), ("arc", 0, NOTCH_TOP),
                     (-NOTCH_R, NOTCH_TOP - NOTCH_R)], hcx + ri - 0.5, hcx + ro + 1)
body = body.fuse(he_wall).fuse(hook.cut(notch))

# ---------------------------------------------------------------- leg-end bridge top, flank rounds, lip lead-ins
le_side = prism("XZ", [(LE_X0 - 1.1, -1), (LE_X1 + 0.01, -1), (LE_X1 + 0.01, LE_TOP, LE_IN_R),
                       (LE_X0, LE_TOP, LE_OUT_R), (LE_X0, 9.0), (LE_X0 - 1.1, 9.0)], -BIG, BIG)
body = trim(body, LE_X0 - 1, LE_X1, dome(LE_X0 - 1.1, LE_X1 + 0.01, LE_TOP, 0).common(le_side))

# round on the outer top edge of the legs along the slot flank (end-view profile swept up the flank)
yo = LEG_YO1 + 0.1
fl = [(-yo, -25), (yo, -25), (yo, 0, LEG_TOP_R), (BRIDGE_HW, 0), (BRIDGE_HW, 12), (-BRIDGE_HW, 12),
      (-BRIDGE_HW, 0), (-yo, 0, LEG_TOP_R)]
fl_env = profile("YZ", [(u, v + tan_pt[1]) + tuple(r) for u, v, *r in fl], tan_pt[0]).extrude(
    V(math.cos(sa), 0, math.sin(sa)) * 4)
body = trim(body, tan_pt[0], BOX_X0, fl_env)

# lead-in chamfer under the leg end of each lip
n = V(LEAD_KX, LEAD_KY, 1); n.normalize()
for s in (-1, 1):
    ns = V(n.x, s * n.y, n.z)
    half = Part.makeBox(60, 60, 30, V(-30, -30, -30))
    half.Placement = App.Placement(V(PANEL_X0, s * LIP_TIP_Y, LEAD_Z0), App.Rotation(V(0, 0, 1), ns))
    body = body.cut(half.common(box(PANEL_X0 - 0.5, PANEL_X1, *sorted((0, s * (YI - 0.01))), -1, 10)))

# ---------------------------------------------------------------- bar arches through both end walls
body = body.cut(arch(LE_X0 - 1, LE_X1 + 0.01, ARCH_TOP_LEG, ARCH_R_LEG))
body = body.cut(arch(HE_X0 - 0.01, hcx, ARCH_TOP_HOOK, ARCH_R_HOOK))
body = body.removeSplitter()

# ---------------------------------------------------------------- export
doc = App.newDocument(NAME)
doc.addObject("Part::Feature", "TineClip").Shape = body
doc.recompute()
doc.saveAs(os.path.join(OUT_DIR, NAME + ".FCStd"))
body.exportStep(os.path.join(OUT_DIR, NAME + ".step"))
Mesh.Mesh(body.tessellate(0.02)).write(os.path.join(OUT_DIR, NAME + ".stl"))

# print orientation: lying on its side - flex panels and hooks bend within the layers
printed = body.copy()
printed.rotate(V(0, 0, 0), V(1, 0, 0), 90)
bb = printed.BoundBox
printed.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
Mesh.Mesh(printed.tessellate(0.02)).write(os.path.join(OUT_DIR, NAME + "_print_on_side.stl"))

bb = body.BoundBox
print("valid:", body.isValid(), " solids:", len(body.Solids), " volume mm3: %.0f" % body.Volume)
print("size L x W x H: %.2f x %.2f x %.2f" % (bb.XLength, bb.YLength, bb.ZLength))
print("throat %.2f, J centre x %.2f, flank meets wall at z %.2f" % (2 * LIP_TIP_Y, hcx, z_flank))
