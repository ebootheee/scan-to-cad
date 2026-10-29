# Tine clip: 30 mm dishwasher tine pivot clip

The part from the blog post: the pivot clip that holds the fold-down tines on
the lower rack of a Thermador DWHD640JPR/93. It goes from a caliper-and-photo
model (v4) to one fitted to a Revopoint MetroX scan (v5).

| File | What it is |
| --- | --- |
| `scan_aligned.ply` | The cleaned scan on its own mirror plane: 44,197 vertices, watertight, in mm. It's in v5's frame: x = 0 at the leg tips, y = 0 on the mirror plane, z up. |
| `tine_clip.py` | v4, from calipers, photos and guesses. Each parameter is tagged (M), (P) or (G). |
| `tine_clip_v5.py` | v5, fitted to the scan. About 80 named parameters, each tagged (S) for scan or (M) for calipers. |
| `tile_images.py` | Tiles renders from `render_views.py` and `compare.py` into the post's composite figures. |

## Build and score

```bash
freecadcmd tine_clip_v5.py
blender -b --factory-startup --python ../../skills/scan-to-cad/tools/compare.py -- scan_aligned.ply tine_clip_v5.stl score
```

The build writes `tine_clip_v5.FCStd`, `.step` and `.stl` next to the script.
v5 is one valid solid, 29.58 × 12.14 × 15.99 mm, with a 2.40 mm snap throat.
Against the scan it scores 0.120 mm RMS, with 91% of scan points within
0.2 mm and 98% within 0.3 mm.

The build also writes `tine_clip_v5_print_on_side.stl`, a copy laid on its
side. The clip in the post was printed differently: in ASA at 100% infill,
tilted 45° on the Z and Y axes, then acetone vapor-smoothed.

## Open questions

The scan and the calipers disagree on two numbers, and v5 follows the scan:

| Dimension | Scan | Calipers | Parameter |
| --- | --- | --- | --- |
| Hook inside diameter | 5.03 mm | 5.3 mm | `HOOK_ID` |
| Overall length | 29.58 mm | 30.0 mm | (whole part) |

If a print doesn't seat on the rack wire, `HOOK_ID` is the first thing to
change.

## Not included

The raw scan, the render script for the post's v4 image, and STL, STEP and
FCStd exports, which the scripts rebuild.
