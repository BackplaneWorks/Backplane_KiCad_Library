#SPDX-License-Identifier: GPL-3.0-or-later
#Copyright (c) 2024, Lothar Felten <lothar.felten@gmail.com>
"""
dec_card 
DEC card edge footprint generator script for KiCad
Generates PCB card egdes for DEC (Digital Equipent Corporation)
card slots. Typically used for flip-chip modules or Qbus, Unibus or Omnibus cards.
DEC has a special pad naming scheme: 
The pads have letters, omitting G, I, O, Q.
The finger prefix is 'A' to 'C'.
The side postfix is '1' for the component top side, bottom side prefix is 2.
Early boards have no side prefix as both sides carry the same signal.
Supported finger types: single, double, quad
Supported height types: short, long
"""
import math

from KicadModTree import *
from generators.tools.footprint.footprint_text_fields import addTextFields
from ..config import CONNECTOR_CONFIG
from generators.tools.footprint.save_footprint import write_footprint


lib_name = "Connector_PCBEdge"
description  = "DEC card edge connectors"
datasheet1 = "http://www.bitsavers.org/pdf/dec/handbooks/Digital_Logic_Handbook_1975-76.pdf page 10 (24) (bottom view)"
datasheet2 = "http://www.bitsavers.org/pdf/dec/pdp8/pdp8e/PDP-8E_Engineering_Drawings_Dec72.pdf page 70 (bottom view)"
widthTypes = ['single', 'double', 'quad']
heightTypes = ['short', 'long']
padNames = ['V','U','T','S','R','P','N','M','L','K','J','H','F','E','D','C','B','A']
fingerNames = ['A','B','C','D']

#all dimensions in mil, 1 mil = 0.0254 mm
def mil(x):
    return x * 0.0254
    
padWidth = mil(80)
padHeight = mil(563)
padOffset = 0.5
padSize = [padWidth, padHeight]
padToPad = mil(125)
padPositions = [mil(156), mil(2906), mil(5406), mil(8156)]
radius_handler = RoundRadiusHandler(
   radius_ratio=0.2,
)
pcbWidths = {'single':mil(2437), 'double':mil(5187), 'quad':mil(10457)}
pcbHeights = {'short':mil(4930), 'long':mil(8430)}
padText = mil(650)
fingerCount = {'single':1, 'double':2, 'quad':4}
chamferLength = 0.3
padRadiusRatio = 0.2
notchHeight = mil(625)
notchDeepHeight = mil(725)
notchDeepWidth = mil(140)
notchNarrowWidth = mil(258)
notchWideWidth = mil(510)
fingerPositions = [mil(100), mil(2850), mil(5348), mil(8097)]
fingerWidth = mil(2240)
cutWidth = 0.2
handleHoleOffsetX = mil(219)
handleHoleOffsetY = mil(-180) 
handleHolePositions = [mil(0), mil(2750), mil(5250), mil(8000)]
handleHoleDistance = mil(2000)
handleHoleDiameter = mil(128)
layers_top = ['F.Cu', 'F.Mask']
layers_bottom = ['B.Cu', 'B.Mask']

def generate_footprint(heightType, widthType, configuration, generator_name: str) -> None:
    height = pcbHeights.get(heightType)
    width = pcbWidths.get(widthType)
    footprint_name = "DEC_" + str(widthType) + "_" + str(heightType)
    f = Footprint(footprint_name, FootprintType.UNSPECIFIED)
    f.setDescription(description +  ", " + datasheet1 + ", " + datasheet2)
    f.setTags("Connector PCBEdge "+footprint_name)
    f.excludeFromBOM = True
    f.excludeFromPositionFiles = True

        
    fingers = fingerCount.get(widthType)
    for finger in range (0, fingers):
        # pads
        i=0
        for pad in padNames:
            y = -((padHeight/2) + padOffset)
            x = padPositions[finger] + (padToPad * i)
            f.append(Pad(number=fingerNames[fingers-1-finger]+padNames[i]+'1', type=Pad.TYPE_CONNECT, shape=Pad.SHAPE_ROUNDRECT,
                 at=[x, y], size=padSize, layers=layers_top, round_radius_handler=radius_handler))
            f.append(Pad(number=fingerNames[fingers-1-finger]+padNames[i]+'2', type=Pad.TYPE_CONNECT, shape=Pad.SHAPE_ROUNDRECT,
                 at=[x, y], size=padSize, layers=layers_bottom, round_radius_handler=radius_handler))
            #silkscreen
            f.append(Text(text=fingerNames[fingers-1-finger]+padNames[i]+'1', 
                at=[x, -padText], rotation=90, layer="F.SilkS", size=[1,1], thickness=0.15))
            f.append(Text(text=fingerNames[fingers-1-finger]+padNames[i]+'2', 
                at=[x, -padText], rotation=90, mirror=True, layer="B.SilkS", size=[1,1], thickness=0.15))
            i=i+1
        #edge cuts finger
        f.append(PolygonLine(shape=[
            [fingerPositions[finger],-notchHeight],
            [fingerPositions[finger], 0],
            [fingerPositions[finger] + fingerWidth, 0],
            [fingerPositions[finger] + fingerWidth, -notchHeight]],
            layer="Edge.Cuts", width=cutWidth))
        # chamfer
        f.append(PolygonLine(shape=[[fingerPositions[finger], -chamferLength],
            [fingerPositions[finger]+fingerWidth, -chamferLength]],
            layer="Dwgs.User", width=cutWidth))
        #holes for handles, 2 per finger
        f.append(Pad(number='H', type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
            at=[handleHoleOffsetX+handleHolePositions[finger], -(height+handleHoleOffsetY)],
            size=handleHoleDiameter+mil(100), layers=Pad.LAYERS_THT, drill=handleHoleDiameter))
        f.append(Pad(number='H', type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
            at=[handleHoleOffsetX+handleHolePositions[finger]+handleHoleDistance, -(height+handleHoleOffsetY)],
            size=handleHoleDiameter+mil(100), layers=Pad.LAYERS_THT, drill=handleHoleDiameter))

    #edge cut notches
    f.append(PolygonLine(shape=[
        [0, -notchDeepHeight],
        [fingerPositions[0], -notchDeepHeight],
        [fingerPositions[0], -notchHeight]],
        layer="Edge.Cuts", width=cutWidth))
    for notch in range (0, fingers-1):
        # notches
        f.append(PolygonLine(shape=[
            [fingerPositions[notch]+fingerWidth,-notchHeight],
            [fingerPositions[notch+1]-notchDeepWidth,-notchHeight],
            [fingerPositions[notch+1]-notchDeepWidth,-notchDeepHeight],
            [fingerPositions[notch+1],-notchDeepHeight],
            [fingerPositions[notch+1],-notchHeight]],
            layer="Edge.Cuts", width=cutWidth))
    f.append(PolygonLine(shape=[
        [fingerPositions[fingers-1]+fingerWidth, -notchHeight],
        [width, -notchHeight],
        [width, -notchDeepHeight]],
        layer="Edge.Cuts", width=cutWidth))
    #edge cuts sides
    f.append(PolygonLine(shape=[
        [0, -notchDeepHeight],
        [0 , -height],
        [width, -height],
        [width, -notchDeepHeight]],
        layer="Edge.Cuts", width=cutWidth))

    #courtyard
    f.append(Rectangle(start=[0, 0],
        end=[math.floor(width*100)/100, math.floor(-notchDeepHeight*100)/100],
        layer="F.CrtYd"))

    #text
    f.append(Text(text="Chamfer 30 degree 1 mm", at=[15, 2],
        layer="Cmts.User"))
    f.append(Text(text="PCB thickness 1.6 mm", at=[15, 4],
        layer="Cmts.User"))

    body_edge={'left':0, 'right':width, 'top':-height, 'bottom':-notchDeepHeight}
    courtyard={'top':-notchDeepHeight, 'bottom':0}
    addTextFields(kicad_mod=f, configuration=configuration, body_edges=body_edge,
    courtyard=courtyard, fp_name=footprint_name, text_y_inside_position='center', allow_rotation=True)

    write_footprint(f, lib_name, generator_name)


def generate_all(generator_name: str) -> int:
    num_fps_generated = 0
    generate_footprint('short','single',CONNECTOR_CONFIG, generator_name)
    num_fps_generated += 1
    generate_footprint('short','double',CONNECTOR_CONFIG, generator_name)
    num_fps_generated += 1
    generate_footprint('short','quad',CONNECTOR_CONFIG, generator_name)
    num_fps_generated += 1
    generate_footprint('long','single',CONNECTOR_CONFIG, generator_name)
    num_fps_generated += 1
    generate_footprint('long','double',CONNECTOR_CONFIG, generator_name)
    num_fps_generated += 1
    generate_footprint('long','quad',CONNECTOR_CONFIG, generator_name)
    num_fps_generated += 1
    return num_fps_generated
