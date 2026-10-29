# scan-to-cad

Turn a 3D scan of a small molded part into a clean, symmetric, parametric
FreeCAD model that prints and fits, with Claude Code writing and running the
scripts.

This is the method and tooling behind
[3D Scan Meshes to Parametric CAD with Claude](https://boothe.io/posts/scan-to-cad-dishwasher-clip).

## What's here

| Path | What it is |
| --- | --- |
| [`skills/scan-to-cad/`](skills/scan-to-cad/SKILL.md) | A Claude Code skill: the whole workflow from caliper measurements to a print, plus the gotchas that cost the most time. |
| [`skills/scan-to-cad/tools/`](skills/scan-to-cad/tools/) | The mesh tools the skill uses: mesh check, alignment, mirror-plane fit, slicer, ray probes, height maps and the scan-vs-CAD scorer. |
| [`examples/tine-clip/`](examples/tine-clip/) | The 30 mm tine clip from the post: a cleaned scan, the v4 caliper model and the v5 model fitted to the scan, which scores 0.12 mm RMS against it. |
| [`examples/fork-clip/`](examples/fork-clip/) | A 44 mm dishwasher rack clip rebuilt as a FreeCAD generator script with a Params sheet. It builds rounds from lofted profiles instead of fillets, re-cuts the wire seats as exact circles, and exports a closed, manifold STL. |

## Using the skill

```bash
cp -r skills/scan-to-cad ~/.claude/skills/
```

Then, in a folder with your scan, ask Claude Code something like "rebuild
this scan as a parametric FreeCAD model I can print".

The tools come with the skill. To check them on a known part first, point
Claude at `examples/tine-clip`.

## Requirements

- FreeCAD 1.1, with `freecadcmd` on your PATH
- Blender 5 (tested on 5.0.1 and 5.2.2), for the mesh check, alignment,
  scorer and renders
- Python with numpy, scipy and matplotlib, for the mirror-plane fit, slicer,
  ray probes and height maps. FreeCAD's bundled Python has all three.
- A scan exported in millimetres. The mesh check and alignment read PLY; the
  other tools also take STL. These parts were scanned with a Revopoint MetroX.

## License

MIT. See [LICENSE](LICENSE).
