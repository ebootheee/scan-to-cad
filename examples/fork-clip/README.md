# Fork clip: parametric rebuild of a dishwasher rack clip

A clean, exactly symmetric CAD model of a 44 mm dishwasher rack clip, rebuilt
from a Revopoint MetroX scan. The scan itself isn't included.

| File | What it is |
|---|---|
| `dishwasher_clip.py` | The parametric generator: all dimensions, profiles and build steps. |
| `build_clip.py` | Builds the FCStd, STEP and STL into this folder. |
| `preview.png` | Rendered views. |

Build it first:

```bash
freecadcmd build_clip.py
```

That writes `dishwasher_clip.stl` (print this: watertight, one body),
`dishwasher_clip.step`, and `dishwasher_clip.FCStd` (the solid plus a
**Params** spreadsheet). It takes about 20 s. Set `CLIP_OUT` to write the files
somewhere else.

Overall size is 13.5 × 43.7 × 36.1 mm and the volume is 2.34 cm³. The part is mirror-symmetric about x = 0.

## Changing it

1. Open `dishwasher_clip.FCStd` in FreeCAD and edit column **B** of the **Params** sheet. Column C describes each value.
2. Run `build_clip.py` from **Macro ▸ Macros…**, or headless with `freecadcmd build_clip.py`. Either way it rewrites the FCStd, STEP and STL in this folder.

The values you're most likely to change are the wire seats. Each one is an exact circle, measured from the scan:

| Param | Scanned | Meaning |
|---|---|---|
| `fork_bore_d` | 5.12 | Wire seat under the fork end (−Y). It's a U-slot, open downward. |
| `c_bore_d` | 5.67 | The big C-hook at the bottom of the +Y end. |
| `e_seat_d` | 3.60 | The upper E-hook seat. Its jaws narrow to about 3.0 mm at the mouth, which acts as a snap detent. |

Making a seat smaller adds material back, and making it larger cuts deeper.

The overhang tabs inside the frame flex to let a rack wire snap past them. Each tab is separated from the collar wall by a slit that's open from below, and stays attached only by a thin hinge along its top:

| Param | Default | Meaning |
|---|---|---|
| `tab_gap_x` | 3.1, 4.3 | Slit position across X. Widen the range for more clearance, or set both values equal to turn the slit off. |
| `tab_hinge` | 1.5 | Material left above the slit. Thinner makes the tab more flexible. |
| `tab_gap_z0`, `tab_gap_y` | 14.8; 3.6, 10.95 | Height and length of the slit. |

Other parameters cover:
- the X extent of each feature band (`*_x`),
- the edge rounds,
- the channel wall and round sizes,
- the C-hook taper,
- the strap under the hook end.

Tuple values are written as `a, b`. Tables are written as `y:value, y:value`.

## How it was rebuilt from the scan

- **Alignment:** I fitted the scan's mirror plane (it was tilted about 4°) and set the frame so x = 0 is the mirror plane.
- **Defects accounted for:** the scan had 286 loose fragments, about 6,900 open edges (holes, mostly between the rails and inside the hook end), duplicate internal surfaces, and noisy patches. I filled the holes with a winding-number reconstruction, ignored the duplicates and smoothed the noise.
- **Symmetry:** the scanned part is bowed about 0.2 to 0.4 mm sideways toward the hook end. The model averages the left and right halves, so it is exactly symmetric.
- **Rev 2 (after the first test print):** the fork hook's front lip now runs across the full tine width, so the outer wing is no longer a separate floating tab. I also added the flex slits beside the frame tabs.
- **Kept on purpose:** the floor window, the undercut groove under the fork-wing lips, the collar notches, the relief between the hook plates, the C-hook taper, and the E-hook mouth lips.

## Accuracy

| Measure | Value |
|---|---|
| Median deviation, model vs. symmetrized scan | 0.16 mm |
| Points within 0.5 mm | 87% |
| Scan's own left/right mismatch (for scale) | 0.13 mm median |

The largest local differences (0.5 to 0.7 mm) are on the lower channel walls, which have a slight draft that isn't modelled, and in areas where the scan has duplicate surfaces.

## Printing notes

- **Orientation:** print it on its side (X axis vertical), so every hook curve lies within the layers. Upright, the C-hook and E-hook would bend across layer lines and snap. Use tree supports.
- **Material:** dishwashers run hot and wet, so use ASA, ABS or PETG. PLA will soften and creep.
- **Strength:** the walls are thin (1.5 mm), so use 100% infill or enough perimeters to fill them.
- **Test first:** printed holes usually come out 0.1 to 0.2 mm undersize. Print one, test the snap on the rack wires, then adjust the seat parameters.
