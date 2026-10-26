#!/usr/bin/env python

from math import sqrt

from KicadModTree import (
    Footprint,
    FootprintType,
    Line,
    Model,
    Pad,
    PadArray,
    PolygonLine,
    Property,
    Rectangle,
    Text,
)
from kilibs.geom import Vec2DCompatible, Vector2D, GeomLine
from .spec import FPconfiguration
import generators.tools.footprint.drawing_tools as DT
from generators.tools.footprint.save_footprint import write_footprint
from .temp_tools import Pad2DArrayFromPads, DrawPinArray, chamferRect
from kilibs.config import global_config as GC


# THT Straight (Vertical) Pinheader:
#####################################
# <--------------> body_width
#    <--------> row_pitch
# +--------------+
# | OOO      OOO |     ^
# | OOO ==== OOO |  ^  pin_width
# | OOO      OOO |  |  v
# +--------------+  pin_pitch
# | OOO      OOO |  |
# | OOO ==== OOO |  v
# | OOO      OOO |
# +--------------+
#
def makePinHeadStraight(cfg: FPconfiguration, generator_name: str):
    # Abbreviations: fab, slk and crt for fabrication, silk and coutryard.
    # fabb/fabp and slkb/slkp for drawing body and pins (b or p after fab/slk).
    # _h, _w, _t, _b, _l, _r, _c for height, width, top, bottom, left, right, center (vector)
    gc = GC.GLOBAL_CONFIG

    # assemble library and footprint name:
    cfg.lib_name = cfg.getLibraryName()
    cfg.footpr_name = cfg.getFootprintName()

    # --- Settings:
    newBehaviourFabSilkCrt = False # overrides oldBehaviorCanvas
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
        silk_fab_offset = gc.silk_line_width/2.0 # 0.06
		# canvas.py method: silk canvas offset is not set, 
		# but through __init__->auto_offset->setLineWidth() it is set to self.line_width / 2.0 (0.12/2=0.06)
        # crt_grid	= 0.05
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

    # body_overlength is symetrical but keep separated as top/bottom internally.
    overlen_top = cfg.pin_pitch / 2 + cfg.body_overlength / 2
    overlen_bot = cfg.pin_pitch / 2 + cfg.body_overlength / 2

    fabb_h = (cfg.pos_count - 1) * cfg.pin_pitch + overlen_top + overlen_bot
    fabb_w = cfg.body_width
    fabb_t = -(cfg.pin_pitch / 2) - (cfg.body_overlength / 2)
    #if cfg.mount_type == "SMD":
    #    fabb_t = -(h_fab/2.0) # in case top/bot overlength are symmetrical
    #    fabb_l = -(cfg.body_width/2.0) + cfg.body_offset # - body_offset for sockets?
    if cfg.isSocket:
        fabb_l = -(cfg.body_width / 2) - half_rows_x - cfg.body_offset
    else:
        fabb_l = -(cfg.body_width / 2) + half_rows_x + cfg.body_offset
    fabb_b = fabb_t + fabb_h
    fabb_r = fabb_l + fabb_w
    if cfg.isSocket:
        fabb_c = pads_c - [cfg.body_offset, 0] # PinSockets are drawn to the left.
    else:
        fabb_c = pads_c + [cfg.body_offset, 0] # PinHeaders/IDC are drawn to the right.
    # print(f'fabb_h:{fabb_h:.3f} w:{fabb_w:.3f} t:{fabb_t:.3f} l:{fabb_l:.3f} c:{fabb_c} overwidth:{fabb_overwidth} offset:{cfg.body_offset}')

    fab_txt_size, fab_txt_thick = gc.get_text_properties_for_layer("F.Fab").clamp_size(fabb_w * 0.6)
    # That causes diffs for 1.00mm headers/sockets, 
	# use the old unrounded calc for now.
    fab_txt_thick = fab_txt_size.y * 0.15

    slkb_h = fabb_h + 2 * silk_fab_offset
    slkb_w = fabb_w + 2 * silk_fab_offset
    slkb_t = fabb_t - silk_fab_offset
    slkb_l = fabb_l - silk_fab_offset
    slkb_b = fabb_b + silk_fab_offset
    slkb_r = fabb_r + silk_fab_offset

    crt_h = max(fabb_h, (cfg.pos_count - 1) * cfg.pin_pitch + pad.y) + 2 * crt_offset
    crt_w = max(
        cfg.body_width,
        (cfg.row_count - 1) * cfg.row_pitch + pad.x
    ) + 2 * crt_offset
    if oldBehaviorCanvas:
        crt_t = fabb_t - crt_offset
    else:
        crt_t = -(crt_h / 2) + half_posn_y 
    crt_l = fabb_l - crt_offset
    crt_r = crt_l + crt_w
    crt_b = crt_t + crt_h
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
    # according to tools.footprint_text_fields.py-> addTextFields() (reads global config yaml),
    # all fields are x centered on body edges. REF** and footpr_name are 0.7 (text size/2 + 0.2) above and below courtyard.
    yt = crt_t if newBehaviourFabSilkCrt or oldBehaviorCanvas else slkb_t # court top/bottom is default behavior
    yb = crt_b if newBehaviourFabSilkCrt or oldBehaviorCanvas else slkb_b # court top/bottom is default behavior
    if oldBehaviorCanvas:
        # .setTextSize(0.6 * (h_fab if param.num_pins == 1 and param.num_pin_rows <= 2 else w_fab))\
        # .text('${REFERENCE}', rotation=(90 if h_fab >= w_fab else 0))\
        size_base = fabb_h if (cfg.pos_count == 1 and cfg.row_count <= 2) else fabb_w
        refr_size, refr_thick = gc.get_text_properties_for_layer("F.Fab").clamp_size(size_base * 0.6)
        refr_thick = round(refr_thick, 2)
    else:
        refr_size = fab_txt_size
        refr_thick = fab_txt_thick

    kicad_mod.append(
        Property(name=Property.REFERENCE, text='REF**', at=[fabb_c.x, yt - txt_offset], layer='F.SilkS'))
    refr = 0 if (cfg.isSocket and cfg.pos_count == 1) else 90
    kicad_mod.append(
        Text(text='${REFERENCE}', at=[fabb_c.x, crt_c.y], rotation=refr, layer='F.Fab', size=refr_size, thickness=refr_thick))
    kicad_mod.append(
        Property(name=Property.VALUE, text=cfg.footpr_name, at=[fabb_c.x, yb + txt_offset], layer='F.Fab'))
    if cfg.datasheet and newBehaviourDatasheet:
        kicad_modg.append(
            Property(name=Property.DATASHEET, text=cfg.datasheet, hide=True, at=[0, 0], layer='F.Fab'))

    # --- create FAB-layer
    if oldBehaviorCanvas:
        chamfer = min(1.0, min(fabb_w, fabb_h)/ 4)
        if cfg.pin1_left:
            rect = chamferRect(start=[fabb_l, fabb_t], size=[fabb_w, fabb_h], chamf=(chamfer, 0.0, 0.0, 0.0), grid=fab_grid, normalize=False)
            DT.addLinesToLayer(kicad_mod,layer='F.Fab',lines=rect,width=gc.fab_line_width, roun=fab_grid)
        else:
            rect = chamferRect(start=[fabb_l, fabb_t], size=[fabb_w, fabb_h], chamf=(0.0, chamfer, 0.0, 0.0), grid=fab_grid, normalize=False)
            DT.addLinesToLayer(kicad_mod,layer='F.Fab',lines=rect,width=gc.fab_line_width, roun=fab_grid)
    else:
        chamfer = fabb_w/4
        if cfg.pin1_left:
            # DT.bevelRectTL(kicad_mod, [fabb_l, fabb_t], size=[fabb_w, fabb_h], layer='F.Fab', width=gc.fab_line_width, bevel_size=chamfer)
            kicad_mod.append(Line(start=[fabb_l + chamfer, fabb_t], end=[fabb_r, fabb_t], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_r, fabb_t], end=[fabb_r, fabb_b], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_r, fabb_b], end=[fabb_l, fabb_b], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_l, fabb_b], end=[fabb_l, fabb_t+chamfer], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_l, fabb_t+chamfer], end=[fabb_l + chamfer, fabb_t], layer='F.Fab', width=gc.fab_line_width))
        else:
            DT.bevelRectTR(kicad_mod, [fabb_l, fabb_t], size=[fabb_w, fabb_h], layer='F.Fab', width=gc.fab_line_width, bevel_size=chamfer)

    # --- create SILKSCREEN-layer + pin1 marker
    # Silkscreen body
    body_min_x_square = pad.x / 2 + silk_pad_offset
    body_min_y_square = pad.y / 2 + silk_pad_offset

    if not(oldBehaviorCanvas):
        # drawing bottom line:
        if (cfg.pos_count-1)*cfg.pin_pitch + body_min_y_square < slkb_b:
            kicad_mod.append(Line(start=[slkb_l, slkb_b], end=[slkb_r, slkb_b], layer='F.SilkS', width=gc.silk_line_width))
        else:
            if cfg.pos_count == 1:
                kicad_mod.append(Line(start=[slkb_l, body_min_y_square], end=[slkb_r, body_min_y_square], layer='F.SilkS', width=gc.silk_line_width))
            else:
                segments = DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_b], end=[slkb_r, slkb_b])], keepouts_silk)
                DT.addLinesToSilk(kicad_mod, segments, gc.silk_line_width, silk_grid)

        # drawing sidelines
        # calculate top Y position
        if cfg.pin_pitch < body_min_y_square * 2:
            shoulder_y_pos = body_min_y_square
            shoulder_y_lines = 2
        else:
            shoulder_y_pos = cfg.pin_pitch / 2
            shoulder_y_lines = 1
        if cfg.row_pitch < body_min_x_square * 2:
            top_x_pos = body_min_x_square if cfg.pin1_left else -body_min_x_square
            top_x_lines = 2
        else:
            top_x_pos = cfg.row_pitch/2 if cfg.pin1_left else -cfg.row_pitch/2
            top_x_lines = 1
        def printshoulderinfo():
            print(f'pitch: {cfg.pin_pitch} body_min[x:{body_min_x_square:.3f}, y:{body_min_y_square:.3f}] ' +
            f'shoulder lines[x:{top_x_lines} y:{shoulder_y_lines}] pos[x:{top_x_pos:.3f}, y:{shoulder_y_pos:.3f}] ' +
            f'left/top/right:{slkb_l:.3f}/{slkb_t:.3f}/{slkb_r:.3f}')
        # printshoulderinfo()

        if (
            (not(cfg.isSocket) and slkb_r  > body_min_x_square+(cfg.row_count-1)*cfg.row_pitch) or
            (cfg.isSocket and slkb_l  < body_min_x_square-(cfg.row_count-1)*cfg.row_pitch)
        ):
            # left vertical side line: shoulder-bottom
            kicad_mod.append(Line(start=[slkb_l, shoulder_y_pos], end=[slkb_l, slkb_b], layer='F.SilkS', width=gc.silk_line_width))
            if cfg.row_count == 1:
                # right vertical side line: shoulder-bottom
                kicad_mod.append(Line(start=[slkb_r, shoulder_y_pos], end=[slkb_r, slkb_b], layer='F.SilkS', width=gc.silk_line_width))
            else:
                # right vertical side line: top-bottom
                kicad_mod.append(Line(start=[slkb_r, slkb_t], end=[slkb_r, slkb_b], layer='F.SilkS', width=gc.silk_line_width))
        elif cfg.pos_count != 1:
            # left vertical side line: shoulder to bottom
            segments = DT.applyKeepouts([GeomLine(start=[slkb_l, shoulder_y_pos], end=[slkb_l, slkb_b])], keepouts_silk)
            DT.addLinesToSilk(kicad_mod, segments, gc.silk_line_width, silk_grid)
            # slkb_l_adj = slkb_l - (cfg.row_count-1) * cfg.row_pitch if isSocket else 0
            # body_min_y_round = sqrt((body_min_x_square * body_min_x_square - slkb_l * slkb_l))
            # kicad_mod.append(Line(start=[slkb_l, shoulder_y_pos], end=[slkb_l, cfg.pin_pitch-body_min_y_round], layer='F.SilkS', width=silk_line_width))
            # kicad_mod.append(Line(start=[slkb_l, (cfg.pos_count-1)*cfg.pin_pitch+body_min_y_round], end=[slkb_l, slkb_b], layer='F.SilkS', width=silk_line_width))
            if cfg.row_count == 1:
                # right vertical side line: shoulder to bottom
                # kicad_mod.append(Line(start=[slkb_r, shoulder_y_pos], end=[slkb_r, cfg.pin_pitch-body_min_y_round], layer='F.SilkS', width=silk_line_width))
                segments = DT.applyKeepouts([GeomLine(start=[slkb_r, shoulder_y_pos], end=[slkb_r, slkb_b])], keepouts_silk)
                DT.addLinesToSilk(kicad_mod, segments, gc.silk_line_width, silk_grid)
            else:
                # right vertical side line: body_min_y_square to bottom
                # kicad_mod.append(Line(start=[slkb_r, body_min_y_square], end=[slkb_r, cfg.pin_pitch-body_min_y_round], layer='F.SilkS', width=silk_line_width))
                segments = DT.applyKeepouts([GeomLine(start=[slkb_r, body_min_y_square], end=[slkb_r, slkb_b])], keepouts_silk)
                DT.addLinesToSilk(kicad_mod, segments, silk_line_width, silk_grid)
            # kicad_mod.append(Line(start=[slkb_r, (cfg.pos_count-1)*cfg.pin_pitch+body_min_y_round], end=[slkb_r, slkb_b], layer='F.SilkS', width=silk_line_width))
            # for x in range(1, (cfg.pos_count-1)):
            #     kicad_mod.append(Line(start=[slkb_l, x*cfg.pin_pitch+body_min_y_round], end=[slkb_l, (x+1)*cfg.pin_pitch-body_min_y_round], layer='F.SilkS', width=silk_line_width))
            #     kicad_mod.append(Line(start=[slkb_r, x*cfg.pin_pitch+body_min_y_round], end=[slkb_r, (x+1)*cfg.pin_pitch-body_min_y_round], layer='F.SilkS', width=silk_line_width))

        # drawing top
        if cfg.row_count == 1:
            # shoulder horizontal line: left to right
            if shoulder_y_lines == 1:
                kicad_mod.append(Line(start=[slkb_l, shoulder_y_pos], end=[slkb_r, shoulder_y_pos], layer='F.SilkS', width=gc.silk_line_width))
            elif shoulder_y_lines == 2:
                top_x_round = sqrt((body_min_x_square * body_min_x_square - (shoulder_y_pos-cfg.pin_pitch) * (shoulder_y_pos-cfg.pin_pitch)))
                kicad_mod.append(Line(start=[slkb_l, shoulder_y_pos], end=[slkb_l + slkb_w/2-top_x_round, shoulder_y_pos], layer='F.SilkS', width=gc.silk_line_width))
                kicad_mod.append(Line(start=[slkb_l + slkb_w/2 + top_x_round, shoulder_y_pos], end=[slkb_r, shoulder_y_pos], layer='F.SilkS', width=gc.silk_line_width))
        else:
            # shoulder horizontal line: left to top_x_pos
            if shoulder_y_lines == 1:
                kicad_mod.append(Line(start=[slkb_l, shoulder_y_pos], end=[top_x_pos, shoulder_y_pos], layer='F.SilkS', width=gc.silk_line_width))
            elif shoulder_y_lines == 2:
                top_x_round = sqrt((body_min_x_square * body_min_x_square - (shoulder_y_pos-cfg.pin_pitch) * (shoulder_y_pos-cfg.pin_pitch)))
                if cfg.pin1_left and top_x_pos > cfg.row_pitch-top_x_round:
                    top_x_end = cfg.row_pitch-top_x_round
                elif not(cfg.pin1_left) and top_x_pos < -cfg.row_pitch + top_x_round:
                    top_x_end = -cfg.row_pitch - top_x_round # ToDo: check after canvas
                else:
                    top_x_end = top_x_pos
                # printshoulderinfo()
                # print(f'top_x_round: {top_x_round} top_x_end: {top_x_end}')
                if cfg.pin1_left:
                    kicad_mod.append(Line(start=[slkb_l, shoulder_y_pos], end=[-top_x_round, shoulder_y_pos], layer='F.SilkS', width=gc.silk_line_width))
                else:
                    kicad_mod.append(Line(start=[slkb_l, shoulder_y_pos], end=[top_x_end, shoulder_y_pos], layer='F.SilkS', width=gc.silk_line_width))
                if top_x_round*2 + gc.silk_line_width*2 < pad.x:
                    kicad_mod.append(Line(start=[top_x_round, shoulder_y_pos], end=[top_x_end, shoulder_y_pos], layer='F.SilkS', width=gc.silk_line_width))

            # vertical line between row 1 and 2
            if top_x_lines == 1:
                kicad_mod.append(Line(start=[top_x_pos, shoulder_y_pos], end=[top_x_pos, slkb_t], layer='F.SilkS', width=gc.silk_line_width))
            elif top_x_lines == 2:
                if cfg.pin1_left or cfg.row_count == 1: # ToDo: check if can be simplified to just the else
                    shoulder_y_round = sqrt((body_min_x_square * body_min_x_square - (cfg.row_pitch-top_x_pos) * (cfg.row_pitch-top_x_pos)))
                    if shoulder_y_pos > cfg.pin_pitch-shoulder_y_round:
                        shoulder_y_pos = cfg.pin_pitch-shoulder_y_round
                    if shoulder_y_round*2 + gc.silk_line_width*2 < pad.y:
                        kicad_mod.append(Line(start=[top_x_pos, shoulder_y_pos], end=[top_x_pos, shoulder_y_round], layer='F.SilkS', width=gc.silk_line_width))
                        kicad_mod.append(Line(start=[top_x_pos, -shoulder_y_round], end=[top_x_pos, slkb_t], layer='F.SilkS', width=gc.silk_line_width))
                else:
                    shoulder_y_round = sqrt((body_min_x_square * body_min_x_square - (cfg.row_pitch+top_x_pos) * (cfg.row_pitch+top_x_pos)))
                    if shoulder_y_pos < shoulder_y_round:
                        shoulder_y_pos = shoulder_y_round
                    if shoulder_y_round*2 + gc.silk_line_width*2 < pad.y:
                        kicad_mod.append(Line(start=[top_x_pos, shoulder_y_pos], end=[top_x_pos, shoulder_y_round], layer='F.SilkS', width=gc.silk_line_width))
                        kicad_mod.append(Line(start=[top_x_pos, -shoulder_y_round], end=[top_x_pos, slkb_t], layer='F.SilkS', width=gc.silk_line_width))

            # highest horizontal line
            if abs(slkb_t) > body_min_y_square:
                kicad_mod.append(Line(start=[top_x_pos, slkb_t], end=[slkb_r, slkb_t], layer='F.SilkS', width=gc.silk_line_width))
            else:
                top_x_round = sqrt((body_min_x_square * body_min_x_square - (abs(slkb_t)) * (abs(slkb_t))))
                if cfg.pin1_left:
                    if top_x_pos > cfg.row_pitch-top_x_round + 2*gc.silk_line_width:
                        kicad_mod.append(Line(start=[top_x_pos, slkb_t], end=[cfg.row_pitch-top_x_round, slkb_t], layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[cfg.row_pitch+top_x_round, slkb_t], end=[slkb_r, slkb_t], layer='F.SilkS', width=gc.silk_line_width))
                else:
                    if top_x_pos < -(cfg.row_pitch-top_x_round + 2*gc.silk_line_width):
                        kicad_mod.append(Line(start=[top_x_pos, slkb_t], end=[cfg.row_pitch-top_x_round, slkb_t], layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[top_x_round, slkb_t], end=[slkb_r, slkb_t], layer='F.SilkS', width=gc.silk_line_width))
    elif oldBehaviorCanvas:
        segments = []
        y1 = cfg.pin_pitch/2
        if cfg.row_count == 1:
            if cfg.pos_count == 1:
                # silk.jump(w_slk, b_slk) canvas.py: silk.jump(w_slk if isSocket else 0.0, -t_slk + rmh)
                # -t_slk + rmh = param.pin_pitch (2* rmh) + param.body_overlength / 2.0 + silk.offset = b_slk
                # silk.down(silk.offset, draw=False)
                # drawing vertical left stub: .jump(w_slk, silk.line_width)  .up(silk.line_width)
                segments = DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_b-gc.silk_line_width], end=[slkb_l, slkb_b])], keepouts_silk)
                # drawing bottom line: left to right .right(w_slk)
                segments += DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_b], end=[slkb_r, slkb_b])], keepouts_silk)
                # drawing vertical right stub: .up(silk.line_width)
                segments += DT.applyKeepouts([GeomLine(start=[slkb_r, slkb_b-gc.silk_line_width], end=[slkb_r, slkb_b])], keepouts_silk)
                DT.addLinesToSilk(kicad_mod, segments, gc.silk_line_width, silk_grid)
            else:
                # silk.jump(w_slk, shoulder) canvas.py: silk.jump(w_slk if isSocket else 0.0, -t_slk + rmh)
                # -t_slk + rmh = param.pin_pitch (2* rmh) + param.body_overlength / 2.0 + silk.offset = shoulder
                # silk.rect(-w_slk, b_slk - rmh, origin="topLeft")
                # drawing top line: left to right
                segments = DT.applyKeepouts([GeomLine(start=[slkb_l, y1], end=[slkb_r, y1])], keepouts_silk)
                # drawing vertical line left: shoulder to bottom
                segments += DT.applyKeepouts([GeomLine(start=[slkb_l, y1], end=[slkb_l, slkb_b])], keepouts_silk)
                # drawing bottom line: left to right
                segments += DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_b], end=[slkb_r, slkb_b])], keepouts_silk)
                # drawing vertical line right: shoulder to bottom
                segments += DT.applyKeepouts([GeomLine(start=[slkb_r, y1], end=[slkb_r, slkb_b])], keepouts_silk)
                DT.addLinesToSilk(kicad_mod, segments, gc.silk_line_width, silk_grid)
        else: # row_count > 1
            x1 = -cfg.row_pitch/2
            # drawing vertical line left: top to bottom
            segments = DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_t], end=[slkb_l, slkb_b])], keepouts_silk)
            # drawing top line: left to right
            segments += DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_t], end=[x1, slkb_t])], keepouts_silk)
            # drawing bottom line: left to right
            segments += DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_b], end=[slkb_r, slkb_b])], keepouts_silk)
            # drawing shoulder vertical: to top
            segments += DT.applyKeepouts([GeomLine(start=[x1, slkb_t], end=[x1, y1])], keepouts_silk)
            # drawing shoulder line: left to right
            segments += DT.applyKeepouts([GeomLine(start=[x1, y1], end=[slkb_r, y1])], keepouts_silk)
            # drawing vertical line right: shoulder to bottom
            segments += DT.applyKeepouts([GeomLine(start=[slkb_r, y1], end=[slkb_r, slkb_b])], keepouts_silk)
            DT.addLinesToSilk(kicad_mod, segments, gc.silk_line_width, silk_grid)

    # pin 1 marker
    mark_offset = (pad.x/2 + silk_pad_offset)
    if cfg.pin1_left:
        pin1_x = -mark_offset if (mark_offset < slkb_l) else slkb_l
    else:
        pin1_x = mark_offset if (mark_offset > slkb_r) else (slkb_r)
    pin1_y = -mark_offset if (-mark_offset < slkb_t) else slkb_t
    if cfg.pin1_left:
        kicad_mod.append(PolygonLine(shape=[[pin1_x, 0], [pin1_x, pin1_y], [0, pin1_y]], layer='F.SilkS', width=gc.silk_line_width))
    else:
        kicad_mod.append(Line(start=[0, pin1_y], end=[pin1_x, pin1_y], layer='F.SilkS', width=gc.silk_line_width))
        kicad_mod.append(Line(start=[pin1_x, pin1_y], end=[pin1_x, 0], layer='F.SilkS', width=gc.silk_line_width))

	# --- create courtyard:
    if oldBehaviorCanvas:
        rect = chamferRect(start=[crt_l, crt_t], size=[crt_w, crt_h], grid=crt_grid, normalize=False)
        DT.addLinesToLayer(kicad_mod,layer='F.CrtYd',lines=rect,width=gc.courtyard_line_width, roun=crt_grid)
    else:
        kicad_mod.append(
            Rectangle(
                start=[DT.roundCrt(crt_l), DT.roundCrt(crt_t)],
                end=[DT.roundCrt(crt_r), DT.roundCrt(crt_b)],
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
