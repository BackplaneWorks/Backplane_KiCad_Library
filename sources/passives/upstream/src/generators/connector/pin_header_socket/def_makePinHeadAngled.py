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
from kilibs.geom import Vec2DCompatible, Vector2D
from .spec import FPconfiguration
import generators.tools.footprint.drawing_tools as DT
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC

# THT Angled (Horizontal) Pinheader:
#####################################
#                 <-------> body_width
#    <--------> row_pitch  <------------------------------> pin_length
#              <-> body_offset
# +---            +-------+
# | OOO      OOO  |       +-------------------------------+            ^
# | OOO ==== OOO  |       |                               +    ^       pin_width
#   OOO      OOO  |       +-------------------------------+    |       v
#                 +-------+                                    pin_pitch
#   OOO      OOO  |       +-------------------------------+    |
#   OOO ==== OOO  |       |                               +    v
#   OOO      OOO  |       +-------------------------------+
#                 +-------+
#
def makePinHeadAngled(cfg: FPconfiguration, generator_name: str):
    # Abbreviations: fab, slk and crt for fabrication, silk and coutryard.
    # fabb/fabp and slkb/slkp for drawing body and pins (b or p after fab/slk).
    # _h, _w, _t, _b, _l, _r, _c for height, width, top, bottom, left, right, center (vector)
    gc = GC.GLOBAL_CONFIG

    # assemble library and footprint name:
    cfg.lib_name = cfg.getLibraryName()
    cfg.footpr_name = cfg.getFootprintName()

    # --- Settings:
    txt_offset = 1 # similar to text_edge_offset = size / 2 + 0.2 in addTextFields()->_getTextFieldDetails()
    # fab_text properties (fab_txt_size, fab_txt_thick) are calculated/clamped further down.
    # silk_pad_offset = gc.silk_pad_offset # = clearance + line_width/2 = 0.2 + 0.06
    silk_pad_offset = gc.silk_pad_clearance + gc.silk_fab_offset # 0.2 + 0.11
    # This is set a bit further out than normal, not quite clear why.
    silk_fab_offset = gc.silk_fab_offset # 0.11
    crt_offset = gc.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR) # 0.5

    # --- init kicad footprint (SMD origin at center, THT at pin 1):
    kicad_mod = Footprint(cfg.footpr_name, cfg.footpr_type)
    kicad_mod.description = cfg.getDescription()
    # if cfg.datasheet != None:
    #     kicad_mod.description += ", " + cfg.datasheet
    kicad_mod.tags = cfg.getBaseTags()

    # --- Calculate pads center and pin1 offset from origin:
    half_rows_x = (cfg.row_count - 1) / 2 * cfg.row_pitch
    half_posn_y = (cfg.pos_count - 1) / 2 * cfg.pin_pitch
    pad = Vector2D(cfg.pads_length, cfg.pads_width) # x=length, y=width

    #if cfg.pin1_left: # THT
    # This works only for THT pinheaders
    pads_c = Vector2D(half_rows_x, half_posn_y)
    #elif isSocket: # THT
    #    pads_c = Vector2D(-half_rows_x, half_posn_y)

    # --- Calculate body, fabrication, silk and courtyard dimensions/positions:
    # anchor for SMD-footprints is in the center, for THT-footprints at pin1
    # See Abbreviations at the top.

    fabb_h = (cfg.pos_count - 1) * cfg.pin_pitch + cfg.pin_pitch / 2 + cfg.pin_pitch / 2
    fabb_w = cfg.body_width
    fabb_t = -(cfg.pin_pitch / 2) - cfg.body_overlength
    fabb_l = (cfg.row_count - 1) * cfg.row_pitch + cfg.body_offset # should this not be row_count-1.5?
    fabb_b = fabb_t + fabb_h
    fabb_r = fabb_l + cfg.body_width
    fabb_c = Vector2D(fabb_l + (fabb_w / 2), fabb_t + (fabb_h / 2))
	
    fabp_t = -cfg.pins_width / 2
    fabp_l = fabb_l + fabb_w

    fab_text_props = gc.get_text_properties_for_layer("F.Fab")
    fab_txt_size, fab_txt_thick = fab_text_props.clamp_size(fabb_w * 0.6)
    # That causes diffs for 1.00mm headers/sockets, 
	# use the old unrounded calc for now.
    fab_txt_thick = fab_txt_size.y * 0.15

    slkb_h = fabb_h + 2 * silk_fab_offset
    slkb_w = fabb_w + 2 * silk_fab_offset
    slkb_t = fabb_t - silk_fab_offset
    slkb_l = fabb_l - silk_fab_offset
    slkb_b = fabb_b + silk_fab_offset
    slkb_r = fabb_r + silk_fab_offset

    slkp_l = slkb_r
    slk_t = -cfg.pin_pitch / 2
    slk_l = -cfg.row_pitch / 2
    body_lines_y = False

    crt_h = fabb_h + 2 * crt_offset
    crt_w = (cfg.row_count - 1) * cfg.row_pitch + 2 * crt_offset
    crt_w = crt_w + cfg.row_pitch / 2 + cfg.body_offset + cfg.body_width + cfg.pins_length
    crt_t = -cfg.pin_pitch / 2 - crt_offset
    crt_b = crt_t + crt_h
    crt_l = -cfg.row_pitch / 2 - crt_offset
    crt_r = crt_l + crt_w
    crt_c = Vector2D(crt_l + crt_w / 2, crt_t + crt_h / 2)

    # --- Create pads:
    x1 = 0
    y1 = 0

    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_RECT
    pad_shapeother = Pad.SHAPE_OVAL
    pad_layers = Pad.LAYERS_THT

    p = 1
    for pos in range(1, cfg.pos_count + 1):
        x1 = 0
        for row in range(1, cfg.row_count + 1):
            if p == 1:
                kicad_mod.append(Pad(number=p, type=pad_type, shape=pad_shape1, at=[x1, y1], size=pad, drill=cfg.pins_drill,
                                      layers=pad_layers))
            else:
                kicad_mod.append(
                    Pad(number=p, type=pad_type, shape=pad_shapeother, at=[x1, y1], size=pad, drill=cfg.pins_drill,
                        layers=pad_layers))

            p += 1
            x1 += cfg.row_pitch

        y1 += cfg.pin_pitch

    # --- set general values
    kicad_mod.append(
        Property(name=Property.REFERENCE, text='REF**', at=[crt_c.x, crt_t + crt_offset - txt_offset], layer='F.SilkS'))
    kicad_mod.append(
        Text(text='${REFERENCE}', at=[fabb_c.x, fabb_c.y], rotation=90, layer='F.Fab', size=fab_txt_size, thickness=fab_txt_thick))
    kicad_mod.append(
        Property(name=Property.VALUE, text=cfg.footpr_name, at=[crt_c.x, crt_b + crt_offset], layer='F.Fab'))

    # --- create FAB-layer
    chamfer = fabb_w/4
    kicad_mod.append(Line(start=[fabb_l + chamfer, fabb_t], end=[fabb_r, fabb_t], layer='F.Fab', width=gc.fab_line_width))
    kicad_mod.append(Line(start=[fabb_r, fabb_t], end=[fabb_r, fabb_b], layer='F.Fab', width=gc.fab_line_width))
    kicad_mod.append(Line(start=[fabb_r, fabb_b], end=[fabb_l, fabb_b], layer='F.Fab', width=gc.fab_line_width))
    kicad_mod.append(Line(start=[fabb_l, fabb_b], end=[fabb_l, fabb_t+chamfer], layer='F.Fab', width=gc.fab_line_width))
    kicad_mod.append(Line(start=[fabb_l, fabb_t+chamfer], end=[fabb_l + chamfer, fabb_t], layer='F.Fab', width=gc.fab_line_width))
    y1 = fabb_t
    yp = fabp_t
    for pos in range(1, cfg.pos_count + 1):
        kicad_mod.append(Line(start=[-cfg.pins_width/2, yp], end=[fabb_l, yp], layer='F.Fab', width=gc.fab_line_width))
        kicad_mod.append(Line(start=[-cfg.pins_width/2, yp], end=[-cfg.pins_width/2, yp + cfg.pins_width], layer='F.Fab', width=gc.fab_line_width))
        kicad_mod.append(Line(start=[-cfg.pins_width/2, yp + cfg.pins_width], end=[fabb_l, yp + cfg.pins_width], layer='F.Fab', width=gc.fab_line_width))

        kicad_mod.append(Line(start=[fabb_r, yp], end=[fabp_l + cfg.pins_length, yp], layer='F.Fab', width=gc.fab_line_width))
        kicad_mod.append(Line(start=[fabp_l + cfg.pins_length, yp], end=[fabp_l + cfg.pins_length, yp + cfg.pins_width], layer='F.Fab', width=gc.fab_line_width))
        kicad_mod.append(Line(start=[fabb_r, yp + cfg.pins_width], end=[fabp_l + cfg.pins_length, yp + cfg.pins_width], layer='F.Fab', width=gc.fab_line_width))

        y1 = y1 + cfg.pin_pitch
        yp = yp + cfg.pin_pitch

    # --- create SILKSCREEN-layer + pin1 marker
    # Silkscreen body
    body_min_x_square = pad.x / 2 + silk_pad_offset
    body_min_y_square = pad.y / 2 + silk_pad_offset
    body_min_y_sqpin = cfg.pin_pitch / 2 + silk_fab_offset

    # calculate point to avoid collision with pad clearance
    pin_line_x = sqrt((body_min_x_square * body_min_x_square - (cfg.pins_width/2+silk_fab_offset) * (cfg.pins_width/2+silk_fab_offset)))
    if cfg.pin_pitch/2 < body_min_y_square:
        body_min_x_round = sqrt(((body_min_x_square * body_min_x_square) - (cfg.pin_pitch/2 * cfg.pin_pitch/2)))
        if slkb_l > body_min_x_round + (cfg.row_count-1)*cfg.row_pitch and slkb_l < body_min_x_square +(cfg.row_count-1)*cfg.row_pitch:
            body_lines_y = sqrt(((body_min_x_square * body_min_x_square) - ((slkb_l-(cfg.row_count-1)*cfg.row_pitch) * (slkb_l-(cfg.row_count-1)*cfg.row_pitch))))
    else:
        body_min_x_round  = 0
    if body_min_y_sqpin < body_min_y_square:
        bodyend_min_x_round = sqrt(((body_min_x_square * body_min_x_square) - (body_min_y_sqpin * body_min_y_sqpin)))
    else:
        bodyend_min_x_round = 0
    # if body is starting outside the pads
    if slkb_l-silk_fab_offset > pad.x/2 + gc.silk_pad_clearance + (cfg.row_count-1)*cfg.row_pitch:
        kicad_mod.append(Rectangle(start=[slkb_l, slkb_t], end=[slkp_l, slkb_b], layer='F.SilkS', width=gc.silk_line_width))
    else:
        if slkb_l < body_min_x_square + (cfg.row_count-1)*cfg.row_pitch and slkb_t-silk_fab_offset > -(body_min_y_square + (cfg.row_count-1)*cfg.row_pitch):
            if cfg.row_count == 1:
                upper_body_x = body_min_x_square
            else:
                upper_body_x = bodyend_min_x_round + (cfg.row_count-1)*cfg.row_pitch
        else:
            upper_body_x = slkb_l
        if cfg.pos_count == 1 and cfg.row_count == 1:
            lower_body_x = body_min_x_square  + (cfg.row_count-1)*cfg.row_pitch
        elif slkb_l < bodyend_min_x_round + (cfg.row_count-1)*cfg.row_pitch and slkb_t-silk_fab_offset > -(body_min_y_square + (cfg.row_count-1)*cfg.row_pitch):
            lower_body_x = bodyend_min_x_round + (cfg.row_count-1)*cfg.row_pitch
        else:
            lower_body_x = slkb_l
        if body_lines_y != False:
            if cfg.row_count == 1:
                kicad_mod.append(PolygonLine(shape=[[upper_body_x, slkb_t], [slkp_l, slkb_t], [slkp_l, slkb_b],
                                                        [lower_body_x, slkb_b], [lower_body_x, slkb_b - gc.silk_fab_offset - cfg.pin_pitch/2 + body_lines_y]], layer='F.SilkS', width=gc.silk_line_width))
            else:
                kicad_mod.append(PolygonLine(shape=[[upper_body_x, -body_lines_y], [upper_body_x, slkb_t], [slkp_l, slkb_t], [slkp_l, slkb_b],
                                                        [lower_body_x, slkb_b], [lower_body_x, slkb_b - gc.silk_fab_offset - cfg.pin_pitch/2 + body_lines_y]], layer='F.SilkS', width=gc.silk_line_width))
        else:
            kicad_mod.append(PolygonLine(shape=[[upper_body_x, slkb_t], [slkp_l, slkb_t], [slkp_l, slkb_b],
                                                    [lower_body_x, slkb_b]], layer='F.SilkS', width=gc.silk_line_width))

    for pos in range(0, cfg.pos_count):
        if pos != 0:
            if pos == 1 and cfg.pin_pitch / 2 < body_min_y_square and cfg.row_count == 1:
                if slkb_l < body_min_x_square:
                    kicad_mod.append(Line(start=[body_min_x_square, (pos-1)*cfg.pin_pitch+cfg.pin_pitch/2], end=[slkp_l, (pos-1)*cfg.pin_pitch+cfg.pin_pitch/2], layer='F.SilkS',width=gc.silk_line_width))
                else:
                    kicad_mod.append(Line(start=[slkb_l, (pos-1)*cfg.pin_pitch+cfg.pin_pitch/2], end=[slkp_l, (pos-1)*cfg.pin_pitch+cfg.pin_pitch/2], layer='F.SilkS',width=gc.silk_line_width))
            else:
                # add line between rows
                if slkb_l < body_min_x_round + (cfg.row_count-1)*cfg.row_pitch:
                    kicad_mod.append(Line(start=[body_min_x_round+ (cfg.row_count-1)*cfg.row_pitch, (pos-1)*cfg.pin_pitch+cfg.pin_pitch/2], end=[slkp_l, (pos-1)*cfg.pin_pitch+cfg.pin_pitch/2], layer='F.SilkS',width=gc.silk_line_width))
                else:
                    kicad_mod.append(Line(start=[slkb_l, (pos-1)*cfg.pin_pitch+cfg.pin_pitch/2], end=[slkp_l, (pos-1)*cfg.pin_pitch+cfg.pin_pitch/2], layer='F.SilkS',width=gc.silk_line_width))
                    if body_lines_y != False:
                        kicad_mod.append(Line(start=[slkb_l, (pos-1)*cfg.pin_pitch+body_lines_y], end=[slkb_l, (pos)*cfg.pin_pitch-body_lines_y], layer='F.SilkS',width=gc.silk_line_width))

        # pin outline
        if pos != 0:
            kicad_mod.append(
                PolygonLine(
                    shape=[
                        [slkp_l, pos * cfg.pin_pitch - cfg.pins_width / 2 - silk_fab_offset],
                        [slkp_l + cfg.pins_length, pos * cfg.pin_pitch - cfg.pins_width / 2 - silk_fab_offset],
                        [slkp_l + cfg.pins_length, pos * cfg.pin_pitch + cfg.pins_width / 2 + silk_fab_offset],
                        [slkp_l, pos * cfg.pin_pitch + cfg.pins_width / 2 + silk_fab_offset],
                    ],
                    layer="F.SilkS",
                    width=gc.silk_line_width,
                )
            )
        else:
            # color the first pin
            kicad_mod.append(
                Rectangle(
                    start=Vector2D(slkp_l, -cfg.pins_width / 2 - silk_fab_offset),
                    end=Vector2D(slkp_l + cfg.pins_length, cfg.pins_width / 2 + silk_fab_offset),
                    layer="F.SilkS",
                    width=gc.silk_line_width,
                    fill=True,
                )
            )

        # if body is starting at the pads
        if slkb_l-silk_fab_offset > pad.x/2 + gc.silk_pad_clearance + (cfg.row_count-1)*cfg.row_pitch:
            if pos == 0 and cfg.row_count == 1:
                # add the lines between pads and silkscreenbody
                kicad_mod.append(Line(start=[body_min_x_square, pos*cfg.pin_pitch-cfg.pins_width/2-silk_fab_offset],
                    end=[slkb_l, pos*cfg.pin_pitch-cfg.pins_width/2-silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                kicad_mod.append(Line(start=[body_min_x_square, pos*cfg.pin_pitch+cfg.pins_width/2+silk_fab_offset],
                    end=[slkb_l, pos*cfg.pin_pitch+cfg.pins_width/2+silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
            else:
                # add the lines between pads and silkscreenbody
                kicad_mod.append(Line(start=[(cfg.row_count-1)*cfg.row_pitch + pin_line_x, pos*cfg.pin_pitch-cfg.pins_width/2-silk_fab_offset],
                    end=[slkb_l, pos*cfg.pin_pitch-cfg.pins_width/2-silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                kicad_mod.append(Line(start=[(cfg.row_count-1)*cfg.row_pitch + pin_line_x, pos*cfg.pin_pitch+cfg.pins_width/2+silk_fab_offset],
                    end=[slkb_l, pos*cfg.pin_pitch+cfg.pins_width/2+silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))

        if cfg.row_count > 1:
            for row in range(1, cfg.row_count):
                # add the lines between pads
                start_point_x = (row - 1) * cfg.row_pitch + pin_line_x
                end_point_x = row * cfg.row_pitch - pin_line_x
                if start_point_x < end_point_x - gc.silk_line_width:
                    if pos == 0 and row == 1:
                        kicad_mod.append(Line(start=[body_min_x_square, pos*cfg.pin_pitch-cfg.pins_width/2-silk_fab_offset],
                            end=[end_point_x, pos*cfg.pin_pitch-cfg.pins_width/2-silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                        kicad_mod.append(Line(start=[body_min_x_square, pos*cfg.pin_pitch+cfg.pins_width/2+silk_fab_offset],
                            end=[end_point_x, pos*cfg.pin_pitch+cfg.pins_width/2+silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                    else:
                        kicad_mod.append(Line(start=[start_point_x, pos*cfg.pin_pitch-cfg.pins_width/2-silk_fab_offset],
                        end=[end_point_x, pos*cfg.pin_pitch-cfg.pins_width/2-silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))
                        kicad_mod.append(Line(start=[start_point_x, pos*cfg.pin_pitch+cfg.pins_width/2+silk_fab_offset],
                        end=[end_point_x, pos*cfg.pin_pitch+cfg.pins_width/2+silk_fab_offset], layer='F.SilkS', width=gc.silk_line_width))

    # pin 1 marker
    pin1_min = -(pad.x / 2 + silk_pad_offset)
    if pin1_min < slk_l:
        pin1_x = pin1_min
    else:
        pin1_x = slk_l
    if pin1_min < slk_t:
        pin1_y = pin1_min
    else:
        pin1_y = slk_t
    kicad_mod.append(PolygonLine(shape=[[pin1_x, 0], [pin1_x, pin1_y], [0, pin1_y]], layer='F.SilkS', width=gc.silk_line_width))

	# --- create courtyard:
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
