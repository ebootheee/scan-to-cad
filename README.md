# scan-to-cad

Turn a 3D scan of a small molded part into a clean, symmetric, parametric
FreeCAD model that prints and fits, with Claude Code writing and running the
scripts.

This is the method and tooling behind
[Scan to CAD: Rebuilding a Dishwasher Clip with a 3D Scanner and Claude](https://boothe.io/posts/scan-to-cad-dishwasher-clip).

## What's here

| Path | What it is |
| --- | --- |
| [`skills/scan-to-cad/`](skills/scan-to-cad/SKILL.md) | A Claude Code skill: the whole workflow from caliper measurements to a print, plus the gotchas that cost the most time. |
| [`examples/fork-clip/`](examples/fork-clip/) | A 44 mm dishwasher rack clip rebuilt as a FreeCAD generator script with a Params sheet. It builds rounds from lofted profiles instead of fillets, re-cuts the wire seats as exact circles, and exports a closed, manifold STL. |
| `tools/` (coming) | The mesh analysis scripts: alignment, slicer, ray probes, height maps and the scan-vs-CAD scorer. |

## Using the skill

```bash
cp -r skills/scan-to-cad ~/.claude/skills/
```

Then, in a folder with your scan, ask Claude Code something like "rebuild
this scan as a parametric FreeCAD model I can print".

## Requirements

- FreeCAD 1.1, with `freecadcmd` on your PATH
- Blender, for renders and deviation maps (optional)
- A scan exported in millimetres as PLY or STL. These parts were scanned with
  a Revopoint MetroX.
