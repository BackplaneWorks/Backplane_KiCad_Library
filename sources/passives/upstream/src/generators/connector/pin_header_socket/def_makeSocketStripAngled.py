#!/usr/bin/env python

from math import sqrt

from KicadModTree import (
    Footprint,
    Line,
    Model,
    Pad,
    PolygonLine,
    Property,
    Rectangle,
    Text,
)
from kilibs.geom import Vec2DCompatible, Vector2D, GeomLine
from .spec import FPconfiguration
import generators.tools.footprint.drawing_tools as DT
from .temp_tools import Pad2DArrayFromPads, DrawPinArray, chamferRect
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


# THT Angled (Horizontal) PinSocket:
#####################################
# <--------------------------------------> body_width
#                                             <- ------> row_pitch
#                                          <-> body_offset
# +---------------------------------------+            ---+
# |                                       |  OOO      OOO |    ^
# |                                       |  OOO ==== OOO | ^  pin_width
# |                                       |  OOO      OOO   |  v
# +---------------------------------------+                 pin_pitch
# |                                       |  OOO      OOO   |
# |                                       |  OOO ==== OOO   v
# |                                       |  OOO      OOO
# +---------------------------------------+
#
def makeSocketStripAngled(cfg: FPconfiguration, generator_name: str):
    # Abbreviations: fab, slk and crt for fabrication, silk and coutryard.
    # fabb/fabp and slkb/slkp for drawing body and pins (b or p after fab/slk).
    # _h, _w, _t, _b, _l, _r, _c for height, width, top, bottom, left, right, center (vector)
    gc = GC.GLOBAL_CONFIG

    # assemble library and footprint name:
    cfg.lib_name = cfg.getLibraryName()
    cfg.footpr_name = cfg.getFootprintName()

    # --- Settings:
    newBehaviourDatasheet = False
    oldBehaviorCanvas = cfg.isSocket
	
    txt_offset = 1 # similar to text_edge_offset = size / 2 + 0.2 in addTextFields()->_getTextFieldDetails()
    # fab_text properties (fab_txt_size, fab_txt_thick) are calculated/clamped further down.
    silk_pad_offset = gc.silk_pad_offset # = clearance + line_width/2 = 0.2 + 0.06
    silk_fab_offset = gc.silk_fab_offset # 0.11
    silk_grid = 1e-6
    fab_grid = 1e-3
    crt_offset = gc.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR) # 0.5
    crt_grid = gc.courtyard_grid # 0.01
    # Overrides:
    if oldBehaviorCanvas:
        #txt_offset = 0.5
        silk_fab_offset = gc.silk_line_width/2.0 # 0.06
		# canvas.py method: silk canvas offset is not set, 
		# but through __init__->auto_offset->setLineWidth() it is set to self.line_width / 2.0 (0.12/2=0.06)
        crt_grid	= 0.05
    else: # current standard behavior:
        silk_pad_offset = gc.silk_pad_clearance + gc.silk_fab_offset # 0.2 + 0.11
        # This is further out than normal, not quite clear why:
        # gc.silk_fab_offset + silk_line_width/2.0 should be enough to stay clear of pads.

    # --- init kicad footprint (SMD origin at center, THT at pin 1):
    kicad_mod = Footprint(cfg.footpr_name, cfg.footpr_type)
    kicad_mod.description = cfg.getDescription()
    if cfg.isSocket and cfg.datasheet != None and not newBehaviourDatasheet:
        kicad_mod.description += " (" + cfg.datasheet + "), script generated"
    kicad_mod.tags = cfg.getBaseTags()

    # --- Calculate pads center and pin1 offset from origin:
    half_rows_x = (cfg.row_count - 1) / 2 * cfg.row_pitch
    half_posn_y = (cfg.pos_count - 1) / 2 * cfg.pin_pitch
    pad = Vector2D(cfg.pads_length, cfg.pads_width) # x=length, y=width

    # if cfg.mount_type == "SMD" and cfg.pin1_left:
    #     p1offset = Vector2D(-half_rows_x, -half_posn_y)
    #     pads_c = Vector2D(0, 0)
    # elif cfg.mount_type == "SMD" and not cfg.pin1_left:
    #     p1offset = Vector2D(half_rows_x, -half_posn_y)
    #     pads_c = Vector2D(0, 0)
    if cfg.pin1_left: # THT
        p1offset = Vector2D(0, 0)
        pads_c = Vector2D(half_rows_x, half_posn_y)
    else: # THT
        p1offset = Vector2D(0, 0)
        pads_c = Vector2D(-half_rows_x, half_posn_y)

    # --- Calculate body, fabrication, silk and courtyard dimensions/positions:
    # anchor for SMD-footprints is in the center, for THT-footprints at pin1
    # See Abbreviations at the top.

    fabb_h = cfg.pos_count * cfg.pin_pitch #+ cfg.body_overlength
    fabb_w = cfg.body_width
    fabb_t = -(cfg.pin_pitch / 2) - (cfg.body_overlength / 2)
    fabb_l = -(cfg.row_count - 1) * cfg.row_pitch - cfg.body_offset - cfg.body_width # should this not be row_count-1.5?
    fabb_b = fabb_t + fabb_h
    fabb_r = fabb_l + cfg.body_width
    fabb_c = Vector2D(fabb_l + (fabb_w / 2), fabb_t + (fabb_h / 2))
	
    fabp_t = -cfg.pins_width / 2

    slkb_h = fabb_h + 2 * silk_fab_offset
    slkb_w = fabb_w + 2 * silk_fab_offset
    slkb_t = fabb_t - silk_fab_offset
    slkb_l = fabb_l - silk_fab_offset
    slkb_b = fabb_b + silk_fab_offset
    slkb_r = fabb_r + silk_fab_offset

    slkp_t = fabp_t - silk_fab_offset
    slkp_r = slkb_r - slkb_w # the same as slkb_l

    crt_h = fabb_h + 2 * crt_offset
    crt_w = (cfg.row_count - 1) * cfg.row_pitch + 2 * crt_offset
    crt_w = crt_w + cfg.row_pitch / 2 + cfg.body_offset + cfg.body_width
    crt_t = -cfg.pin_pitch / 2 - crt_offset
    crt_b = crt_t + crt_h
    crt_l = -crt_w + cfg.row_pitch / 2 + crt_offset 
    crt_r = crt_l + crt_w
    crt_c = Vector2D(crt_l + crt_w / 2, crt_t + crt_h / 2)

    # --- Create pads:
    pad_1 = Pad(type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_THT, at=[0, 0], size=pad, drill=cfg.pins_drill)
    pad_n = Pad(type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT, at=[0, 0], size=pad, drill=cfg.pins_drill)

    padlist = Pad2DArrayFromPads(p1offset, cfg.pos_count, cfg.row_count, cfg.pin_pitch, pad_n, pad_1,
        pads_offset=cfg.pads_offset, pin1_left=cfg.pin1_left, staggered=cfg.isStaggered
    )
    kicad_mod.extend(padlist)
    keepouts_silk = DT.getKeepoutsForPads(pads=padlist, clearance=silk_pad_offset) # ToDo: gc.silk_pad_clearance should be enough

    # --- set general values
    kicad_mod.append(
        Property(name=Property.REFERENCE, text='REF**', at=[crt_c.x, crt_t - txt_offset], layer='F.SilkS'))
    refr = 0 if cfg.pos_count == 1 else 90
    kicad_mod.append(
        Text(text='${REFERENCE}', at=[fabb_c.x, fabb_c.y], rotation=refr, layer='F.Fab'))
    kicad_mod.append(
        Property(name=Property.VALUE, text=cfg.footpr_name, at=[crt_c.x, crt_b + txt_offset], layer='F.Fab'))
    if cfg.datasheet and newBehaviourDatasheet:
        kicad_modg.append(
            Property(name=Property.DATASHEET, text=cfg.datasheet, hide=True, at=[0, 0], layer='F.Fab'))

    # --- create FAB-layer
    if oldBehaviorCanvas:
        chamfer = min(min(1.0, min(fabb_w, fabb_h)/ 4), (cfg.pin_pitch / 2 - cfg.pins_width / 2) )
        # bevel = min(Layer.getBevel(h_fab, abs(w_fab)), param.pin_pitch / 2.0 - param.pin_width / 2.0)
        if cfg.pin1_left:
            rect = chamferRect(start=[fabb_l, fabb_t], size=[fabb_w, fabb_h], chamf=(chamfer, 0.0, 0.0, 0.0), grid=fab_grid, normalize=False)
            DT.addLinesToLayer(kicad_mod,layer='F.Fab',lines=rect,width=gc.fab_line_width, roun=fab_grid)
        else:
            rect = chamferRect(start=[fabb_l, fabb_t], size=[fabb_w, fabb_h], chamf=(0.0, chamfer, 0.0, 0.0), grid=fab_grid, normalize=False)
            DT.addLinesToLayer(kicad_mod,layer='F.Fab',lines=rect,width=gc.fab_line_width, roun=fab_grid)
        x1 = fabb_r
        yp1 = fabp_t
        yp2 = fabp_t + cfg.pins_width
        for pos in range(1, cfg.pos_count + 1):
            rect = chamferRect(start=[0, yp1], end=[fabb_r, yp2], draw=(True, False, True, True), grid=fab_grid, normalize=False)
            DT.addLinesToLayer(kicad_mod,layer='F.Fab',lines=rect,width=gc.fab_line_width, roun=fab_grid)
            yp1 = yp1 + cfg.pin_pitch
            yp2 = yp2 + cfg.pin_pitch

    else:
        y1 = fabb_t
        yp = fabp_t
        for pos in range(1, cfg.pos_count + 1):
            kicad_mod.append(Rectangle(start=[fabb_r, y1], end=[fabb_l, y1 + cfg.pin_pitch], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(
                Rectangle(start=[0, yp], end=[fabb_r , yp + cfg.pins_width], layer='F.Fab', width=gc.fab_line_width))
            y1 = y1 + cfg.pin_pitch
            yp = yp + cfg.pin_pitch

    # --- create SILKSCREEN-layer + pin1 marker
    slk_half_pad_x_canv = pad.x / 2 + silk_fab_offset # wrong, but used by canvas
    slk_half_pad_x = pad.x / 2 + silk_pad_offset
    slk_half_pad_y = pad.y / 2 + silk_pad_offset
    # print(f'slk_half_pad_x: {slk_half_pad_x}, slk_half_pad_y: {slk_half_pad_y}, slk_half_pad_x_canv: {slk_half_pad_x_canv}')

    # skip applyKeepouts() if not needed:
    slk_pads_l = -(cfg.row_count - 1) * cfg.row_pitch - slk_half_pad_x_canv
    isBodyOnPads = True if slk_pads_l < slkb_r else False
    #slk_pads_r = slk_half_pad_x

    # Do not use RectLine (based on PolygonLine) or Rectangle because half of the lines are not top-bottom and left-right.
    lines = []
    lines += [GeomLine(start=[slkb_l, slkb_t], end=[slkb_l, slkb_b])]
    lines += [GeomLine(start=[slkb_l, slkb_t], end=[slkb_r, slkb_t])]
    lines += [GeomLine(start=[slkb_r, slkb_t], end=[slkb_r, slkb_b])]
    lines += [GeomLine(start=[slkb_l, slkb_b], end=[slkb_r, slkb_b])]
    if isBodyOnPads:
        lines = DT.applyKeepouts(lines, keepouts_silk)
    DT.addLinesToSilk(kicad_mod, lines, gc.silk_line_width, silk_grid)

    # Y coordinate for socket position bottom, pin position top and bottom
    ys_b = slkb_t + cfg.pin_pitch+ silk_fab_offset
    yp_t = slkp_t
    yp_b = slkp_t + cfg.pins_width + 2 * silk_fab_offset
    for pos in range(1, cfg.pos_count + 1):
        lines = []
        if pos == 1:
            # fill the rectangle:
            y = slkb_t + gc.silk_line_width
            y_end = ys_b + (0 if oldBehaviorCanvas and cfg.pos_count != 1 else silk_fab_offset)
            if oldBehaviorCanvas:
                # .jump(0.0, -t_slk - rmh)\   # jump(0.0, +silk.offset) = center
                # .fillrect(-w_slk, param.pin_pitch + silk.offset + (silk.offset if param.num_pins == 1 else 0.0))\
                # fillrect():   h = self._align(h - self.line_width)
                #               l = math.ceil(h / self.line_width)
                #               h = h / l
                import math
                h = (y_end - y)/ math.ceil((y_end - y) / gc.silk_line_width)
                # print(f'y: {y}, y_end: {y_end} y_end-y:{y_end-y} h:{h}')
                while not(math.isclose(y_end - y,0, abs_tol=silk_grid)):
                    lines += [GeomLine(start=[slkb_l, y], end=[slkb_r, y])]
                    y = y + h
            else:
                while y < y_end:
                    lines += [GeomLine(start=[slkb_r, y], end=[slkb_l, y])]
                    y = y + gc.silk_line_width
        if pos != cfg.pos_count: # for 1 and 2 pos, the above code is enough for the socket body
            lines += [GeomLine(start=[slkb_l, ys_b], end=[slkb_r, ys_b])]
        if isBodyOnPads:
            lines = DT.applyKeepouts(lines, keepouts_silk)
        DT.addLinesToSilk(kicad_mod, lines, gc.silk_line_width, silk_grid)

        # pin markings
        segments = DT.applyKeepouts([GeomLine(start=[slkb_r, yp_t], end=[0, yp_t])], keepouts_silk)
        segments += DT.applyKeepouts([GeomLine(start=[slkb_r, yp_b], end=[0, yp_b])], keepouts_silk)
        DT.addLinesToSilk(kicad_mod, segments, gc.silk_line_width, silk_grid)

        ys_b = ys_b + cfg.pin_pitch
        yp_t = yp_t + cfg.pin_pitch
        yp_b = yp_b + cfg.pin_pitch

    # Pin 1 marker
    if oldBehaviorCanvas:
        y1 = -max(cfg.pin_pitch / 2 + silk_fab_offset, slk_half_pad_y)
        kicad_mod.append(Line(start=[slk_half_pad_x, y1], end=[slk_half_pad_x, 0], layer='F.SilkS', width=gc.silk_line_width))
        kicad_mod.append(Line(start=[0, y1], end=[slk_half_pad_x, y1], layer='F.SilkS', width=gc.silk_line_width))
    else:
        kicad_mod.append(PolygonLine(shape=[[0, -cfg.pin_pitch / 2], [cfg.pin_pitch / 2, -cfg.pin_pitch / 2], [cfg.pin_pitch / 2, 0]], layer='F.SilkS', width=gc.silk_line_width))

	# --- create courtyard:
    if oldBehaviorCanvas:
        rect = chamferRect(start=[crt_r, crt_t], size=[-crt_w, crt_h], grid=crt_grid, normalize=False)
        DT.addLinesToLayer(kicad_mod,layer='F.CrtYd',lines=rect,width=gc.courtyard_line_width, roun=crt_grid)
    else:
        kicad_mod.append(
            Rectangle(
                start=[DT.roundCrt(crt_r), DT.roundCrt(crt_t)],
                end=[DT.roundCrt(crt_l), DT.roundCrt(crt_b)],
                layer='F.CrtYd',
                width=gc.courtyard_line_width
            )
        )

    # --- add model
    kicad_mod.append(
        Model(
            filename=gc.model_3d_prefix
            + cfg.lib_name
            + ".3dshapes/"
            + cfg.footpr_name
            + gc.model_3d_suffix
        )
    )

    write_footprint(kicad_mod, cfg.lib_name, generator_name)

