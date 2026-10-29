"""Rebuild the dishwasher clip from the Params sheet and export FCStd/STEP/STL.

Headless:   freecadcmd build_clip.py
            (reads Params from the dishwasher_clip.FCStd next to this file)
FreeCAD:    open dishwasher_clip.FCStd, edit the Params sheet, then run this
            file from Macro > Macros...
"""
import os
import sys

import FreeCAD as App

sys.dont_write_bytecode = True  # keep the project folder free of __pycache__
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # some macro runners don't define __file__
    _doc = App.ActiveDocument
    HERE = os.path.dirname(_doc.FileName) if _doc is not None and _doc.FileName else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import dishwasher_clip  # noqa: E402

FCSTD = os.path.join(HERE, "dishwasher_clip.FCStd")

doc = App.ActiveDocument if App.GuiUp else None
if doc is None or doc.getObject(dishwasher_clip.SHEET) is None:
    doc = App.openDocument(FCSTD) if os.path.exists(FCSTD) else None
dishwasher_clip.export_all(os.environ.get("CLIP_OUT", HERE), doc)
if App.GuiUp:
    import FreeCADGui as Gui
    Gui.SendMsgToActiveView("ViewFit")
