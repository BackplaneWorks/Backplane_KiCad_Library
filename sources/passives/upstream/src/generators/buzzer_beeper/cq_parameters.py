#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating QFP/GullWings models in X3D format.
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#

## file of parametric definitions

## base parametes & model
import collections
from collections import namedtuple

# Import cad_tools
import cq_cad_tools
import Draft
import exportPartToVRML as expVRML
import FreeCAD
import FreeCADGui
import FreeCADGui as Gui
import ImportGui
import shaderColors

# Reload tools
from cq_cad_tools import reload_lib

reload_lib(cq_cad_tools)
# Explicitly load all needed functions
from cq_cad_tools import (
    Color_Objects,
    CutObjs_wColors,
    FuseObjs_wColors,
    GetListOfObjects,
    checkRequirements,
    close_CQ_Example,
    exportSTEP,
    exportVRML,
    restore_Main_Tools,
    saveFCdoc,
    z_RotateObject,
)

# Sphinx workaround #1
try:
    QtGui
except NameError:
    QtGui = None
#

try:
    # Gui.SendMsgToActiveView("Run")
    #    from Gui.Command import *
    Gui.activateWorkbench("CadQueryWorkbench")
    import cadquery

    cq = cadquery
    from Helpers import show

    # CadQuery Gui
except:  # catch *all* exceptions
    msg = "missing CadQuery 0.3.0 or later Module!\r\n\r\n"
    msg += "https://github.com/jmwright/cadquery-freecad-module/wiki\n"
    if QtGui is not None:
        reply = QtGui.QMessageBox.information(None, "Info ...", msg)
    # maui end

# checking requirements
checkRequirements(cq)
