# -*- coding: utf8 -*-
#!/usr/bin/python
#
# This was originaly derived from a cadquery script for generating PDIP models in X3D format
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#
# Adapted by easyw for step and vrlm export
# See https://github.com/easyw/kicad-3d-models-in-freecad

## requirements
## cadquery FreeCAD plugin
##   https://github.com/jmwright/cadquery-freecad-module

## to run the script just do: freecad scriptName modelName
## e.g. FreeCAD export_conn_jst_xh.py all

## the script will generate STEP and VRML parametric models
## to be used with kicad StepUp script

# * These are FreeCAD & cadquery tools                                       *
# * to export generated models in STEP & VRML format.                        *
# *                                                                          *
# * cadquery script for generating JST-XH models in STEP AP214               *
# *   Copyright (c) 2016                                                     *
# * Rene Poeschl https://github.com/poeschlr                                 *
# * All trademarks within this guide belong to their legitimate owners.      *
# *                                                                          *
# *   This program is free software; you can redistribute it and/or modify   *
# *   it under the terms of the GNU General Public License (GPL)             *
# *   as published by the Free Software Foundation; either version 2 of      *
# *   the License, or (at your option) any later version.                    *
# *   for detail see the LICENCE text file.                                  *
# *                                                                          *
# *   This program is distributed in the hope that it will be useful,        *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
# *   GNU Library General Public License for more details.                   *
# *                                                                          *
# *   You should have received a copy of the GNU Library General Public      *
# *   License along with this program; if not, write to the Free Software    *
# *   Foundation, Inc.,                                                      *
# *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA           *
# *                                                                          *
# ****************************************************************************

import cadquery as cq

thread_minor_diameter = {"M1.6": 1.22, "M2": 1.57, "M2.5": 2.01, "M3": 2.46, "M4": 3.24}

# ext_thread = {
#       'od': 'M3',
#       'L': 6,
#       'undercut':{
#         'od': 2.2,
#         'L': [0.5, 1.25],
#         'r': 0.2
#         }
#     }

def generate(series_params, part):  # **kwargs):
    id = series_params["mechanical"].get("id")
    od = series_params["mechanical"]["od"]
    od1 = series_params["mechanical"].get("od1")
    h1 = series_params["parts"][part].get("h1", series_params["mechanical"].get("h1", 0))
    thread_depth = series_params["parts"][part].get("thread_depth")
    drill_depth = series_params["parts"][part].get("drill_depth")
    id1 = series_params["mechanical"].get("id1")
    t1 = series_params["mechanical"].get("t1", 0)
    h = series_params["parts"][part].get("h", series_params["mechanical"].get("h"))
    ext_thread = series_params["mechanical"].get("ext_thread")

    body = cq.Workplane("XY").circle(od / 2).extrude(h)
    if od1 is not None:
        body = (
            body.faces("<Z")
            .workplane(centerOption="CenterOfMass")
            .circle(od1 / 2)
            .extrude(h1)
        )

    if ext_thread is not None:
        od = float(ext_thread["od"][1:])
        thread = (
            cq.Workplane("XY")
            .workplane(h + ext_thread["undercut"]["L"][0], centerOption="CenterOfMass")
            .circle(od / 2)
            .extrude(ext_thread["L"] - ext_thread["undercut"]["L"][0])
        )

        thread = thread.faces("<Z").chamfer(
            ext_thread["undercut"]["L"][1] - ext_thread["undercut"]["L"][0],
            (od - ext_thread["undercut"]["od"]) / 2,
        )
        thread = thread.faces(">Z").chamfer(
            (od - thread_minor_diameter[ext_thread["od"]]) / 2
        )
        thread = (
            thread.faces("<Z")
            .workplane(centerOption="CenterOfMass")
            .circle(ext_thread["undercut"]["od"] / 2)
            .extrude(ext_thread["undercut"]["L"][0] + 0.1)
        )

        body = body.union(thread)
        body = body.edges(
            cq.selectors.BoxSelector(
                [
                    -ext_thread["undercut"]["od"] / 2 - 0.1,
                    -ext_thread["undercut"]["od"] / 2 - 0.1,
                    h - 0.1,
                ],
                [
                    ext_thread["undercut"]["od"] / 2 + 0.1,
                    ext_thread["undercut"]["od"] / 2 + 0.1,
                    h + 0.1,
                ],
                boundingbox=True,
            )
        ).fillet(ext_thread["undercut"]["r"])

    if id is not None:
        if id in thread_minor_diameter:
            idf = thread_minor_diameter[id]
            ch = (float(id[1:]) - idf) / 2
        else:
            idf = float(id)
            ch = 0

        cut_thread_hole = ext_thread is None
        if cut_thread_hole:
            body = (
                body.faces(">Z")
                .workplane(-t1, centerOption="CenterOfMass")
                .circle(idf / 2)
            )
            if thread_depth is None:
                # cut through the full body
                body = body.cutBlind(-(h + h1) + t1)
            else:
                # cut only as deep as the thread_depth
                body = body.cutBlind(-thread_depth + t1)

            # as well as a bit deeper with a marginally smaller diameter
            # (used together with thread_depth)
            if drill_depth is not None:
                body = (
                    body.faces(">Z")
                    .workplane(-t1, centerOption="CenterOfMass")
                    .circle(idf / 2 - 0.01)
                    .cutBlind(-drill_depth + t1)
                )

            if ch > 0:
                body = body.edges(
                    cq.selectors.BoxSelector(
                        [-idf / 2 - 0.1, -idf / 2 - 0.1, h - 0.1],
                        [idf / 2 + 0.1, idf / 2 + 0.1, h + 0.1],
                        boundingbox=True,
                    )
                ).chamfer(ch)

        if id1 is not None:
            body = (
                body.faces(">Z")
                .workplane(centerOption="CenterOfMass")
                .circle(id1 / 2)
                .cutBlind(-(t1))
            )
    return body
