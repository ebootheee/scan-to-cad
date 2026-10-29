# Thermador DWHD640JPR/93 lower-rack flip-tine pivot clip - parametric replica (v4)
# Run headless:  freecadcmd tine_clip.py
# Or in FreeCAD GUI: Macro > Macros... > Execute.
#
# Coordinate frame (as the clip sits on the rack):
#   X = length   (x=0 is the tip of the two LEGS, +X toward the J HOOK)
#   Y = width    (centered on y=0)
#   Z = up       (z=0 is the underside of the box)
# mm throughout. (M) = measured with calipers, (P) = scaled from ruler photos, (G) = guess.

import math, os
import FreeCAD as App
import Part, Mesh
from FreeCAD import Vector as V

# ---------------------------------------------------------------- parameters
TOTAL_L    = 30.0   # (M) leg tip to outside of J hook

# J hook (drops over a rack wire running across, along Y) - solid, no notch
HOOK_ID    = 5.3    # (M) inside diameter
HOOK_T     = 2.1    # (P) wall thickness -> top of part at ~16 mm (M)
HOOK_CZ    = 11.2   # (P) height of hook hole centre
HOOK_TIP_Z = 7.2    # (P) height of the tip of the J's outer leg
HOOK_W0    = 8.6    # (P) hook width at the box
HOOK_W1    = 6.6    # (P) hook width at its outer end (tapers in top view)
NOTCH_W    = 3.0    # (P) half-moon notch cut up into the tip of the J's outer leg
NOTCH_TOP  = 12.2   # (P) height of the notch's rounded top (tip is at HOOK_TIP_Z)

# centre box (hook-end face is flush with the inside of the J - no step)
BOX_X0     = 9.9    # (P) leg-end face of the box
BOX_H      = 10.2   # (P) box height
W          = 11.0   # (P) box width (12.0 across the side bumps)
WALL       = 1.3    # (P) wall thickness

# centreline snap: the clip pushes down onto a 3.5 mm bar running lengthwise (along X).
# Bar enters a V lead-in, forces the throat open, and clicks into a round seat.
# The spring is the side-wall panels between the slits (they flex outward).
BAR_D      = 3.5    # (M) bar diameter
THROAT     = 2.6    # (M) narrowest point of the V (raise to ~2.9 if too stiff in PETG)
SEAT_D     = 3.7    # (G) round seat the bar locks into (bar + 0.2)
LEAD_W     = 4.4    # (G) V mouth width at the underside
BAR_Z      = 3.2    # (G) bar centre height above the underside
LIP_TOP    = 5.6    # (G) top of the snap lips (just above the seat)
BAR_CLEAR  = 0.4    # clearance for the bar through the end walls
SLIT_W     = 1.0    # (P) slits that free the flex panels
SLIT_H     = 8.5    # (G) tall slits -> panel hinges on the top 1.7 mm of the wall
PANEL_X0   = 15.4   # (G) leg-end edge of each flex panel (slit is just below this)

# pivot bumps (raised rings) on the solid wall near the leg end, with V dimples
PIV_X      = 12.4   # (P) OEM photos: close to the leg-end wall
PIV_Z      = 7.2    # (P) upper half of the box
PIV_D      = 4.0    # (P) bump diameter
PIV_PROUD  = 0.5    # (M) bump height (12.0 across bumps)
DIMPLE_D   = 2.2    # (M) V dimple diameter
DIMPLE_ANG = 90.0   # (G) included angle of the V

# two legs with upturned tips (cradle under a rack wire running along Y)
LEG_W      = 2.8    # (P) width of each leg (flush with box sides)
LEG_Z0     = 1.0    # (P) underside of legs (sits a bit above box underside)
LEG_TOP    = 10.9   # (P) top of the legs / upturned tips
LEG_SLOT_X = 5.9    # (P) slot centre from leg tip
LEG_SLOT_D = 4.2    # (P) slot width = wire 3.5-4 (M) + clearance
LEG_SLOT_Z = 6.3    # (P) bottom of the round slot seat
LEG_RND    = 4.0    # (P) radius of rounded outer-bottom corner of legs

OUT_DIR    = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
NAME       = "tine_clip"

# ---------------------------------------------------------------- derived + helpers
YW = W / 2
BIG = 50
ri, ro = HOOK_ID / 2, HOOK_ID / 2 + HOOK_T
hcx = TOTAL_L - ro                   # J hole centre X
BOX_X1 = hcx - ri                    # box end flush with inside of J
xi0, xi1 = BOX_X0 + WALL, BOX_X1 - WALL
PANEL_X1 = xi1 - SLIT_W              # hook-end edge of flex panel

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def ycyl(cx, cz, r, y0=-BIG, y1=BIG):
    return Part.makeCylinder(r, y1 - y0, V(cx, y0, cz), V(0, 1, 0))

def xcyl(cy, cz, r, x0, x1):
    return Part.makeCylinder(r, x1 - x0, V(x0, cy, cz), V(1, 0, 0))

def yz_prism(pts, x0, x1):
    w = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))

# ---------------------------------------------------------------- box + flex panels
body = box(BOX_X0, BOX_X1, -YW, YW, 0, BOX_H)
body = body.cut(box(xi0, xi1, -YW + WALL, YW - WALL, -1, BOX_H + 1))

# pivot bumps + V dimples (before slits so nothing overlaps)
for s in (-1, 1):
    y_in, y_out = s * (YW - WALL), s * (YW + PIV_PROUD)
    body = body.fuse(Part.makeCylinder(PIV_D / 2, abs(y_out - y_in), V(PIV_X, min(y_in, y_out), PIV_Z), V(0, 1, 0)))
    dep = (DIMPLE_D / 2) / math.tan(math.radians(DIMPLE_ANG / 2))
    cone = Part.makeCone(DIMPLE_D / 2, 0, dep, V(PIV_X, y_out, PIV_Z), V(0, -s, 0))
    body = body.cut(cone.fuse(Part.makeCylinder(DIMPLE_D / 2, 1, V(PIV_X, y_out, PIV_Z), V(0, s, 0))))

# snap lips on the inside of each flex panel
for s in (-1, 1):
    y0, y1 = sorted((s * 0.5, s * (YW - WALL + 0.01)))
    body = body.fuse(box(PANEL_X0, PANEL_X1, y0, y1, 0, LIP_TOP))

# slits either side of each flex panel, cut up through wall + lips
for s in (-1, 1):
    y0, y1 = sorted((s * 0.5, s * (YW + 1)))
    body = body.cut(box(PANEL_X0 - SLIT_W, PANEL_X0, y0, y1, -1, SLIT_H))
    body = body.cut(box(PANEL_X1, xi1, y0, y1, -1, SLIT_H))

# keyhole along the centreline: V lead-in -> throat -> round seat -> narrow above
rs = SEAT_D / 2
z_throat = BAR_Z - math.sqrt(rs ** 2 - (THROAT / 2) ** 2)
key = yz_prism([(-LEAD_W / 2, -1), (LEAD_W / 2, -1), (LEAD_W / 2, 0), (THROAT / 2, z_throat),
                (-THROAT / 2, z_throat), (-LEAD_W / 2, 0)], PANEL_X0 - 0.1, PANEL_X1 + 0.1)
key = key.fuse(box(PANEL_X0 - 0.1, PANEL_X1 + 0.1, -THROAT / 2, THROAT / 2, -1, LIP_TOP + 1))
key = key.fuse(xcyl(0, BAR_Z, rs, PANEL_X0 - 0.1, PANEL_X1 + 0.1))
body = body.cut(key)

# bar passage through both end walls (clearance, no grip)
rb = BAR_D / 2 + BAR_CLEAR
passage = xcyl(0, BAR_Z, rb, BOX_X0 - 1, BOX_X1 + 1).fuse(box(BOX_X0 - 1, BOX_X1 + 1, -rb, rb, -1, BAR_Z))
passage = passage.fuse(yz_prism([(-LEAD_W / 2 - 0.3, -1), (LEAD_W / 2 + 0.3, -1), (LEAD_W / 2 + 0.3, 0),
                                 (rb, 0.6), (-rb, 0.6), (-LEAD_W / 2 - 0.3, 0)], BOX_X0 - 1, BOX_X1 + 1))
for xa, xb in ((BOX_X0 - 1, xi0), (xi1, BOX_X1 + 1)):
    body = body.cut(passage.common(box(xa, xb, -BIG, BIG, -BIG, BIG)))

# ---------------------------------------------------------------- J hook
ring = ycyl(hcx, HOOK_CZ, ro).cut(ycyl(hcx, HOOK_CZ, ri)).common(
    box(hcx - ro - 1, hcx + ro + 1, -BIG, BIG, HOOK_CZ, HOOK_CZ + ro + 1))
hook = ring.fuse(box(hcx + ri, hcx + ro, -BIG, BIG, HOOK_TIP_Z, HOOK_CZ))      # outer leg
# stem: blends from the end wall (flush outside) up to the full J thickness, no ledge
stem = Part.Face(Part.makePolygon([V(x, -BIG, z) for x, z in
        [(xi1, BOX_H - 2.0), (hcx - ri, BOX_H - 2.0), (hcx - ri, HOOK_CZ + 0.01),
         (hcx - ro, HOOK_CZ + 0.01), (xi1, BOX_H - 2.0)]])).extrude(V(0, 2 * BIG, 0))
hook = hook.fuse(stem)
taper = Part.Face(Part.makePolygon([V(BOX_X1 - 3, -HOOK_W0 / 2, -1), V(TOTAL_L + 1, -HOOK_W1 / 2, -1),
                                    V(TOTAL_L + 1, HOOK_W1 / 2, -1), V(BOX_X1 - 3, HOOK_W0 / 2, -1),
                                    V(BOX_X1 - 3, -HOOK_W0 / 2, -1)])).extrude(V(0, 0, 30))
hook = hook.common(taper)
if NOTCH_W > 0:                                  # half-moon notch in the outer leg tip
    nr = NOTCH_W / 2
    notch = box(hcx, TOTAL_L + 1, -nr, nr, HOOK_TIP_Z - 1, NOTCH_TOP - nr).fuse(
        xcyl(0, NOTCH_TOP - nr, nr, hcx, TOTAL_L + 1))
    hook = hook.cut(notch)
body = body.fuse(hook)

# ---------------------------------------------------------------- legs
sr = LEG_SLOT_D / 2
for s in (-1, 1):
    y0, y1 = sorted((s * YW, s * (YW - LEG_W)))
    leg = box(0, xi0, y0, y1, LEG_Z0, LEG_TOP)
    leg = leg.cut(ycyl(LEG_SLOT_X, LEG_SLOT_Z + sr, sr))
    leg = leg.cut(box(LEG_SLOT_X - sr, LEG_SLOT_X + sr, -BIG, BIG, LEG_SLOT_Z + sr, LEG_TOP + 1))
    corner = box(-1, LEG_RND, -BIG, BIG, LEG_Z0 - 1, LEG_Z0 + LEG_RND).cut(ycyl(LEG_RND, LEG_Z0 + LEG_RND, LEG_RND))
    body = body.fuse(leg.cut(corner))

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
print("size L x W x H: %.1f x %.1f x %.1f" % (bb.XLength, bb.YLength, bb.ZLength))
print("box %.1f..%.1f; flex panel %.1f..%.1f (%.1f long); throat z=%.2f, seat z=%.2f, snap per side %.2f"
      % (BOX_X0, BOX_X1, PANEL_X0, PANEL_X1, PANEL_X1 - PANEL_X0, z_throat, BAR_Z, (BAR_D - THROAT) / 2))
