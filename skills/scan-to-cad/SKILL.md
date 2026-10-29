---
name: scan-to-cad
description: Rebuild a small molded part (clip, bracket, knob, latch) from a 3D scan as a clean, symmetric, parametric FreeCAD model that prints and fits. Use when the user has a scan mesh (PLY, STL, OBJ) of a physical part and wants editable CAD, a replacement print, or the scan "cleaned up", or when scoring a CAD model against a scan.
---

# Scan to CAD

The goal is the part's design intent, not a copy of the scan. A scan is a soft
first draft: sharp edges come out rounded, small features blur, and wear,
scanner noise and how the part sat on the turntable are all baked in. Recover
the clean geometry the mold maker started from, and prove it with numbers.

Do every step as a script run headless, and keep the scripts. The user should
be able to rerun the whole chain on the next part.

## Setup

- **FreeCAD 1.1, headless:** `freecadcmd script.py`. It bundles numpy, scipy
  and matplotlib, so analysis scripts can run inside it too.
- **Blender 5, headless** (tested on 5.0.1 and 5.2.2):
  `blender -b --factory-startup --python script.py -- <args>`, for mesh
  cleanup, alignment, deviation maps and renders.
- Plain Python with numpy, scipy and matplotlib works for analysis.
- Prefer headless scripts to driving a GUI over MCP. Scripts are repeatable;
  clicks are not.
- Work in millimetres throughout. Keep the scan, the scripts and an `out/`
  folder together.

## Tools

The `tools/` folder next to this file has working versions of the scripts
this workflow needs, from a real project. Copy them into the project and
adapt them.

| Script | Runs in | What it does |
| --- | --- | --- |
| `analyze.py` | Blender | Mesh check of a PLY: counts, bounding box, principal axes, non-manifold and boundary edges, islands, volume. |
| `align.py` | Blender | Keeps the largest island, then aligns the scan (PLY) to a CAD STL: principal axes in all 24 orientations, then trimmed ICP. Writes `scan_aligned.stl` and the per-vertex deviation. |
| `symfit.py` | Python | Fits the scan's mirror plane and re-frames it so the plane is y = 0 and x = 0 at the min-x end. |
| `meshtools.py` | Python | `probe` fires ray probes; `slice` plots cuts on a 0.25 mm grid with an optional CAD overlay. Importable: `read_mesh`, `ray_hits`, `slice_segs`. |
| `wallmap.py` | Python | Height map of the two side walls (outermost \|y\|) on a 0.2 mm grid. |
| `compare.py` | Blender | The scorer: signed distances both ways, RMS, share within 0.1, 0.2 and 0.3 mm, the worst 1 mm cubes, and deviation-coloured renders. |
| `render_views.py` | Blender | Eight shaded orthographic views of one or two meshes. |

```bash
blender -b --factory-startup --python tools/analyze.py -- scan.ply
blender -b --factory-startup --python tools/align.py -- scan.ply guess.stl out
python tools/symfit.py out/scan_aligned.stl scan_sym.stl
export SCAN=scan_sym.stl
python tools/meshtools.py probe "y x=15.5 z=4" "z x=28.7 y=0"
python tools/meshtools.py slice cuts.png "Y:3.6,Y:5.0" --cad model.stl
python tools/wallmap.py out/wall
blender -b --factory-startup --python tools/compare.py -- scan_sym.stl model.stl out/score
blender -b --factory-startup --python tools/render_views.py -- out/views scan_sym.stl model.stl
```

- "Python" means any interpreter with numpy, scipy and matplotlib. FreeCAD's
  bundled `python` has all three.
- Meshes can be STL or binary little-endian PLY, except that `analyze.py`
  and `align.py` read the scan as PLY.
- A probe spec is `"<axis> <k>=<v> <k>=<v>"`: a line along `<axis>` with the
  other two coordinates fixed. It prints every crossing, sorted.
- Tuned to a 30 mm part: the camera target (15, 0, 8) and ortho scales in
  `compare.py` and `render_views.py`, and the 0.4 mm colour range in
  `compare.py`. Edit them for other parts. In `render_views.py`, the
  `side_pos`, `leg_end` and `hook_end` views come out rotated.
- There is no shape-fitting script. Fit circles, lines and planes to probe
  output directly with least squares.
- `examples/tine-clip` in the source repo has a cleaned scan and its fitted
  model in the same frame. Use them to check the tools work before trusting
  them on a new part.

## Workflow

### 1. Measure what you can first

Before touching the scan, ask the user for caliper numbers: overall size,
hole and wire diameters, and the mating parts (the bar or wire the part grabs).
Tag every dimension with its source and keep the tags in the model script:
`(M)` measured, `(P)` scaled from a photo, `(G)` guessed, `(S)` from the scan.
The tags tell you which numbers to distrust later.

### 2. Check the mesh before trusting it

Report (`analyze.py` covers most of this): vertex and face count, watertight
or not, open-edge count, loose islands, duplicate internal surfaces, and the
bounding box against the caliper length. Scan quality varies a lot. One clean
scan needed only three specks deleted; another had 286 loose fragments, about
6,900 open edges and duplicate internal surfaces. Delete islands. For many
holes, use a winding-number reconstruction rather than local hole filling.
Treat duplicate surfaces as noise.

### 3. Align in two passes

1. **Rough** (`align.py`): match the scan's principal axes to your
   best-guess model (or to a sensible frame) in all 24 axis orientations,
   refine each with ICP, and keep the best. About 0.3 mm RMS is enough to
   compare.
2. **Mirror plane** (`symfit.py`): if the part is symmetric, reflect the
   scan onto itself and solve for the plane where left matches right. Put
   that plane at y = 0, which `wallmap.py` assumes, and report the yaw and
   roll you corrected. Real scans were 1° to 4° off.

Do not skip pass 2. Without it, the two halves measure differently and you
will faithfully model an asymmetry that is only how the part sat on the
scanner. After it, report the scan's own left/right mismatch (median). That
number is the accuracy floor: you cannot score better than the scan agrees
with itself.

### 4. Measure the mesh

A mesh is triangles, not dimensions. Three tools turn it into numbers; use
them constantly.

- **Slices** (`meshtools.py slice`): cut with a plane and plot the outline
  on a 0.25 mm grid with the CAD model overlaid. The fastest way to see what
  a feature really is.
- **Ray probes** (`meshtools.py probe`): fire a line through the mesh and
  report every crossing. Fire in batches of 100 to 200 and average left
  against right.
- **Height maps** (`wallmap.py`): sweep probes over a face on a 0.2 mm grid
  and colour the result. This finds small ribs, dimples and slits that
  slices miss.

### 5. Fit simple shapes

Fit radii, lines, angles and planes to the probe points. If the points fit
within about 0.1 mm, it is a design feature: use the fitted value. If they
wobble around the shape, it is smoothing: model the shape they wobble around.

### 6. Decide what is design

Ask the user for the governing rules early, in one line each, for example
"exactly symmetric" and "replace smoothing curves with clean geometry". Then
apply them to every feature and show the decisions as a table the user can
check: *the scan showed / decision / why*.

| Test | Design | Not design |
| --- | --- | --- |
| Fits a simple shape cleanly? | Yes: keep the fitted shape | Wobbles: smoothing |
| Mirrored on both sides? | Yes | One side only: wear or noise. Point-symmetric only: likely a molding artifact |
| Affects fit or function? | Snap lips, seats, lead-in chamfers, sizeable rounds | Molding draft (about 2°), hairline rounds: model them square |

### 7. Write the model as a script

- Named parameters, grouped by feature (legs, box, hook, lips...), each with
  a comment and a source tag. Fit-critical dimensions (wire seats, snap
  throats, hook openings) get one parameter each, so a fit fix is one number.
- Build one side and mirror it, so symmetry is exact by construction.
- Build features as 2D profiles carried across a band and mirrored.
- Cut fit-critical bores and seats as exact circles in one final boolean, so
  they can be tuned without touching the outlines around them.
- OpenCascade, FreeCAD's kernel, often refuses fillets on this kind of
  geometry. Build rounds as a rounded profile swept or lofted along the edge
  instead: a ruled loft through sections pulled in by the exact arc offset at
  each station. Rebuilds become robust.
- FreeCAD 1.1 will not restore FeaturePython objects from modules that are not
  installed add-ons. Store the solid as a plain `Part::Feature` plus a
  `Params` spreadsheet, and rebuild with a script that reads the sheet back.
- Export STEP, and tessellate the STL in a loop over deflection settings until
  the mesh is closed and manifold.

### 8. Score every build

After every change, run the scorer (`compare.py`) and put the results in a
table, one row per pass:

- Distance from every scan point to the CAD surface, and from CAD back to the
  scan (one direction alone hides missing or extra material).
- RMS error, and the share of points within 0.2 mm and 0.3 mm.
- The worst 1 mm cubes ranked by error. That list is the next pass's to-do.

Also run sanity checks on every build: exactly one solid, `isValid()`, volume,
and bounding box against the scan's. Then look at slices anyway, because a
score can hide a bad cut.

What good looked like on a 30 mm clip: 0.12 mm RMS, 91% within 0.2 mm and
98% within 0.3 mm after four passes. The first pass scored 0.14 mm.

### 9. Settle conflicts before printing

Where the scan and the calipers disagree, the scan cannot tell you which is
right. Show both numbers to the user, ask which to trust, and keep the result
in one named parameter.

### 10. Print

- Material for the environment: ASA, ABS or PETG for anything hot and wet
  like a dishwasher. PLA softens and creeps.
- Thin walls: 100% infill.
- Orientation: small snap fits break along layer lines. Tilt the part so no
  hook or flex panel bends straight across the layers. A 45° tilt on
  two axes worked; so does laying a hook flat so its curve stays within
  layers.
- ASA and ABS can be acetone vapor-smoothed afterwards, which fuses the outer
  layers and improves layer bonding.
- Printed holes come out 0.1 to 0.2 mm undersize. Print one, test-fit, then
  tune the seat parameters.

## Gotchas

- **A mirror helper flipped a wall upside down instead of left to right.** The
  build came out as three solids, 25 mm tall instead of about 16 mm. A
  bounding-box check found it in seconds; run one on every build.
- **A swept rounding profile that was too shallow silently cut the bottoms off
  the legs.** The score barely moved; a side slice made it obvious.
- **Averaging halves thins features where one half of the scan has holes.**
  Trust the better side, or the user's photos, for those features.
- **Scanned parts can be bowed** 0.2 to 0.4 mm. Averaging the halves splits
  the difference, which is usually right.
- **Small scanner artifacts look like features.** A groove that alternates
  sides, a ring seen only in photos: check them against the mirror and the
  height map before modelling them.

## Working with the user

- Read your own plots (slices, deviation maps, height maps) and say what you
  see. Many real features are found this way, not by the user pointing.
- Keep the user's rules short and apply them everywhere, showing the decision
  table.
- Report each pass as: what changed, RMS, within 0.2 mm, within 0.3 mm, worst
  regions.
- When the model is done, tell the user which three things to check at the
  test fit: does it snap on and stay on, does it seat on the wire, does it
  flex without whitening.
