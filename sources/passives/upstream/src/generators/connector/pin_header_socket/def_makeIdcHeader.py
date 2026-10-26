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


def makeIdcHeader(cfg: FPconfiguration, generator_name: str):
    # Abbreviations: fab, slk and crt for fabrication, silk and coutryard.
    # fabb/fabp and slkb/slkp for drawing body and pins (b or p after fab/slk).
    # _h, _w, _t, _b, _l, _r, _c for height, width, top, bottom, left, right, center (vector)
    gc = GC.GLOBAL_CONFIG

    # assemble library and footprint name:
    cfg.lib_name = cfg.getLibraryName()
    cfg.footpr_name = cfg.getFootprintName()

    # --- Settings:
    mh_present = (
        True
        if cfg.mhole_drill > 0
        and cfg.mhole_width > 0
        and cfg.mhole_length > 0
        and cfg.mhole_overlength > 0
        else False
    )

    txt_offset = 1 # similar to text_edge_offset = size / 2 + 0.2 in addTextFields()->_getTextFieldDetails()
    # fab_text properties (fab_txt_size, fab_txt_thick) are calculated/clamped further down.
    # silk_pad_offset = gc.silk_pad_offset # = clearance + line_width/2 = 0.2 + 0.06
    silk_pad_offset = gc.silk_pad_clearance + gc.silk_fab_offset # 0.2 + 0.11
    # This is set a bit further out than normal, not quite clear why.
    silk_fab_offset = gc.silk_fab_offset # 0.11
    crt_offset = gc.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR) # 0.5
    crt_grid = gc.courtyard_grid # 0.01

    # --- init kicad footprint (SMD origin at center, THT at pin 1):
    kicad_mod = Footprint(cfg.footpr_name, cfg.footpr_type)
    kicad_mod.description = cfg.getDescription()
    if cfg.datasheet != None:
        kicad_mod.description += ", " + cfg.datasheet
    kicad_mod.tags = cfg.getBaseTags()

    # --- Calculate pads center and pin1 offset from origin:
    half_rows_x = (cfg.row_count - 1) / 2 * cfg.row_pitch
    half_posn_y = (cfg.pos_count - 1) / 2 * cfg.pin_pitch
    pad = Vector2D(cfg.pads_length, cfg.pads_width) # x=length, y=width
    mhole_pad = Vector2D(cfg.mhole_width, cfg.mhole_length)

    if cfg.mount_type == "SMD" and cfg.pin1_left:
        p1offset = Vector2D(-half_rows_x, -half_posn_y)
        pads_c = Vector2D(0, 0)
    elif cfg.mount_type == "SMD" and not cfg.pin1_left:
        p1offset = Vector2D( half_rows_x, -half_posn_y)
        pads_c = Vector2D(0, 0)
    elif cfg.pin1_left: # THT
        p1offset = Vector2D(0, 0)
        pads_c = Vector2D( half_rows_x, half_posn_y)
    else: # THT
        p1offset = Vector2D(0, 0)
        pads_c = Vector2D(-half_rows_x, half_posn_y)

    # --- Calculate body, fabrication, silk and courtyard dimensions/positions:
    # anchor for SMD-footprints is in the center, for THT-footprints at pin1
    # See Abbreviations at the top.

    # body_overlength is symetrical but keep separated as top/bottom internally.
    overlen_top = cfg.pin_pitch / 2 + cfg.body_overlength
    overlen_bot = cfg.pin_pitch / 2 + cfg.body_overlength

    fabb_h = (cfg.pos_count - 1) * cfg.pin_pitch + overlen_top + overlen_bot
    fabb_w = cfg.body_width
    if cfg.mount_type == "SMD":
        # Body should be centered for SMT footprints
        fabb_t = -half_posn_y - overlen_top
        fabb_l = -cfg.body_width / 2 if cfg.body_offset == 0 else cfg.body_offset
    else:
        fabb_t = -overlen_top
        fabb_l = half_rows_x - (cfg.body_width / 2) if cfg.body_offset == 0 else cfg.body_offset
    fabb_b = fabb_t + fabb_h
    fabb_r = fabb_l + fabb_w
    fabb_c = Vector2D(fabb_l + (fabb_w / 2.0), fabb_t + (fabb_h / 2.0))

    fab_text_props = gc.get_text_properties_for_layer("F.Fab")
    fab_txt_size, fab_txt_thick = fab_text_props.clamp_size(fabb_w * 0.6)

    # these calculations are so tight that new body styles will probably break them
    crt_h = max(max(fabb_h, (cfg.pos_count - 1) * cfg.pin_pitch + pad.y) + 2 * cfg.latch_length, (cfg.pos_count - 1) * cfg.pin_pitch + 2 * cfg.mhole_overlength + mhole_pad.y) + 2 * crt_offset
    crt_w = max(cfg.body_width, cfg.row_pitch * (cfg.row_count - 1) + pad.x) + 2 * crt_offset if cfg.body_offset <= 0 else pad.x / 2 + cfg.body_offset + cfg.body_width + 2 * crt_offset
    if cfg.mount_type == "SMD":
        # Courtyard should be centered for SMT footprints
        crt_t = min(fabb_t - cfg.latch_length, -cfg.mhole_overlength - mhole_pad.y / 2) - crt_offset
        crt_l =  -pad.x / 2 - cfg.row_pitch/2- crt_offset
    else:
        crt_t = min(fabb_t - cfg.latch_length, -cfg.mhole_overlength - mhole_pad.y / 2) - crt_offset
        crt_l = fabb_l - crt_offset if cfg.body_offset <= 0 else -pad.x / 2 - crt_offset
    if mh_present and (cfg.mhole_offset - mhole_pad.x / 2 < fabb_l):
        # horizontal latching with mounting holes is a special case
        crt_l = cfg.mhole_offset - mhole_pad.x / 2 - crt_offset
        crt_w = -crt_l + cfg.body_width + cfg.body_offset + crt_offset

    if cfg.mount_type == "SMD":
        # center is [0, 0] for SMD footprints
        center_fab = Vector2D(0, 0)
        center_fp = Vector2D(0, 0)
    else:
        # center of the body (horizontal: middle pin or the center of the middle pins for vertical)
        center_fab = Vector2D(half_rows_x if cfg.orientation == 'Vertical' else cfg.body_offset + cfg.body_width / 2, fabb_t + fabb_h / 2)
        center_fp = Vector2D(crt_l + crt_w / 2, center_fab.y)

    # --- Create pads: (first the left row then the right row)
    if cfg.mount_type == "SMD":
        pad_type = Pad.TYPE_SMT
        pad_shape = Pad.SHAPE_ROUNDRECT
        pad_layers = Pad.LAYERS_SMT
    else:
        pad_type = Pad.TYPE_THT
        pad_shape = Pad.SHAPE_OVAL
        pad_layers = Pad.LAYERS_THT

    if cfg.mount_type == "SMD":
        # For SMD footprints, pad 1 location is not (0,0)
        for start_pos, initial in zip([-cfg.row_pitch/2, cfg.row_pitch/2], range(1, cfg.row_count + 1)):
            kicad_mod.append(PadArray(pincount=cfg.pos_count, spacing=[0,cfg.pin_pitch], start=[start_pos,-(cfg.pos_count-1)*cfg.pin_pitch/2], initial=initial, increment=cfg.row_count,
                type=pad_type, shape=pad_shape, size=pad, drill=cfg.pins_drill, layers=pad_layers,
                round_radius_handler=gc.roundrect_radius_handler))
    else:
        for start_pos, initial in zip([0, cfg.row_pitch], range(1, cfg.row_count + 1)):
            kicad_mod.append(PadArray(pincount=cfg.pos_count, spacing=[0,cfg.pin_pitch], start=[start_pos,0], initial=initial, increment=cfg.row_count,
                type=pad_type, shape=pad_shape, size=pad, drill=cfg.pins_drill, layers=pad_layers,
                round_radius_handler=gc.roundrect_radius_handler))

    # --- Create mounting hole pads
    mhole_nr = gc.get_pad_name(GC.PadName.MECHANICAL)
    mh_y = Vector2D(-cfg.mhole_overlength, (cfg.pos_count - 1) * cfg.pin_pitch + cfg.mhole_overlength)

    if mh_present:
        for mh_y_offset in mh_y:
            kicad_mod.append(Pad(number=mhole_nr, type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, at=[cfg.mhole_offset, mh_y_offset], size=mhole_pad,
                drill=cfg.mhole_drill, layers=Pad.LAYERS_THT))


    # --- set general values
    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[center_fp.x, crt_t - fab_txt_size.y / 2], layer='F.SilkS'))
    kicad_mod.append(Text(text='${REFERENCE}', at=[center_fab.x, center_fab.y], rotation=90, layer='F.Fab', size=fab_txt_size, thickness=fab_txt_thick))
    kicad_mod.append(Property(name=Property.VALUE, text=cfg.footpr_name, at=[center_fp.x, crt_t + crt_h + fab_txt_size.y / 2], layer='F.Fab'))


    # --- create FAB-layer, SILKSCREEN-layer + pin1 marker
    # for shrouded headers, fab and silk layers have very similar geometry
    # can use the same code to build lines on both layers with slight changes in values between layers
    # zip together lists with fab and then silk layer settings as the list elements so the same code can draw both layers
    for layer, line_width, lyr_offset, chamfer in zip(['F.Fab', 'F.SilkS'], [gc.fab_line_width, gc.silk_line_width], [0, gc.silk_fab_offset], [min(1, fabb_w / 4), 0]):
        # body outline
        if cfg.orientation == "Horizontal" and cfg.latch_enable:
            # body outline taken from existing KiCad footprint
            body_polygon = [
                (cfg.body_offset - lyr_offset, fabb_t - lyr_offset), (fabb_l + 6.98 + lyr_offset, fabb_t - lyr_offset),
                (fabb_l + fabb_w + lyr_offset, fabb_t + 3.17 - lyr_offset), (fabb_l + fabb_w + lyr_offset, fabb_t + 6.99 + lyr_offset),
                (fabb_l + 12.7 + lyr_offset, fabb_t + 9.14 + lyr_offset), (fabb_l + 12.7 + lyr_offset, fabb_t + fabb_h - 9.14 - lyr_offset),
                (fabb_l + fabb_w + lyr_offset, fabb_t + fabb_h - 6.99 - lyr_offset), (fabb_l + fabb_w + lyr_offset, fabb_t + fabb_h - 3.17 + lyr_offset),
                (fabb_l + 6.98 + lyr_offset, fabb_t + fabb_h + lyr_offset), (cfg.body_offset - lyr_offset, fabb_t + fabb_h + lyr_offset)
            ]
            # body outline taken from simplified 3M 3000 model (also modify arguments: cfg.body_offset=-1.24 and cfg.body_width=1.24+15.53)
            # https://www.3m.com/3M/en_US/company-us/all-3m-products/~/3M-Four-Wall-Header-3000-Series/?N=5002385+3290316872&preselect=8709318+8710652+8733900+8734573&rt=rud
            body_polygon = [
                (cfg.body_offset - lyr_offset, fabb_t - lyr_offset), (fabb_l + 7.11 + lyr_offset, fabb_t - lyr_offset),
                (fabb_l + 16.77 + lyr_offset, fabb_t + 3.47 - lyr_offset), (fabb_l + 16.77 + lyr_offset, fabb_t + 7.44 + lyr_offset),
                (fabb_l + 13.21 + lyr_offset, fabb_t + 8.07 + lyr_offset), (fabb_l + 13.21 + lyr_offset, fabb_t + fabb_h - 8.07 - lyr_offset),
                (fabb_l + 16.77 + lyr_offset, fabb_t + fabb_h - 7.44 - lyr_offset), (fabb_l + 16.77 + lyr_offset, fabb_t + fabb_h - 3.47 + lyr_offset),
                (fabb_l + 7.11 + lyr_offset, fabb_t + fabb_h + lyr_offset), (cfg.body_offset - lyr_offset, fabb_t + fabb_h + lyr_offset)
            ]
            kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
            # now draw the left side vertical line, which may be broken on the silk layer around mounting holes
            if layer == 'F.SilkS' and mh_present and mhole_pad.x/2 - cfg.mhole_offset > -cfg.body_offset + gc.silk_fab_offset * 1.5:
                body_polygon = [(cfg.body_offset - lyr_offset, fabb_t - lyr_offset), (cfg.body_offset - lyr_offset, mh_y.x - mhole_pad.x/2)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                body_polygon = [(cfg.body_offset - lyr_offset, mh_y.x + mhole_pad.x/2), (cfg.body_offset - lyr_offset, mh_y.y - mhole_pad.x/2)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                body_polygon = [(cfg.body_offset - lyr_offset, mh_y.y + mhole_pad.x/2), (cfg.body_offset - lyr_offset, fabb_t + fabb_h + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
            else:
                body_polygon = [(cfg.body_offset - lyr_offset, fabb_t + fabb_h + lyr_offset), (cfg.body_offset - lyr_offset, fabb_t - lyr_offset)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
        else:
            # body outline silk lines need to clear the mounting hole on vertical headers
            if mh_present and layer == 'F.SilkS':
                body_polygon = [(cfg.mhole_offset + mhole_pad.x/2 - lyr_offset, fabb_t - lyr_offset), (fabb_l + fabb_w + lyr_offset, fabb_t - lyr_offset),
                    (fabb_l + fabb_w + lyr_offset, fabb_t + fabb_h + lyr_offset), (cfg.mhole_offset + mhole_pad.x/2 - lyr_offset, fabb_t + fabb_h + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                body_polygon = [(cfg.mhole_offset - mhole_pad.x/2 + lyr_offset, fabb_t - lyr_offset), (fabb_l - lyr_offset, fabb_t - lyr_offset),
                    (fabb_l - lyr_offset, fabb_t + fabb_h + lyr_offset), (cfg.mhole_offset - mhole_pad.x/2 + lyr_offset, fabb_t + fabb_h + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
            else:
                if layer == "F.SilkS" and cfg.mount_type == "SMD":
                    # Break silkscreen for SMD pads
                    body_polygon = [(fabb_l - lyr_offset, -((cfg.pos_count-1)*cfg.pin_pitch/2)-pad.y/2-0.5), (fabb_l - lyr_offset, fabb_t - lyr_offset),
                        (fabb_l + fabb_w + lyr_offset, fabb_t - lyr_offset), (fabb_l +fabb_w + lyr_offset, -((cfg.pos_count-1)*cfg.pin_pitch/2)-pad.y/2-0.5)]
                    kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                    body_polygon = [(fabb_l - lyr_offset, ((cfg.pos_count-1)*cfg.pin_pitch/2)+pad.y/2+0.5), (fabb_l - lyr_offset, fabb_t + fabb_h + lyr_offset),
                        (fabb_l + fabb_w + lyr_offset, fabb_t +fabb_h + lyr_offset), (fabb_l +fabb_w + lyr_offset, ((cfg.pos_count-1)*cfg.pin_pitch/2)+pad.y/2+0.5)]
                    kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
                else:
                    body_polygon = [(fabb_l + chamfer - lyr_offset, fabb_t - lyr_offset), (fabb_l + fabb_w + lyr_offset, fabb_t - lyr_offset),
                        (fabb_l + fabb_w + lyr_offset, fabb_t + fabb_h + lyr_offset), (fabb_l - lyr_offset, fabb_t + fabb_h + lyr_offset),
                        (fabb_l - lyr_offset, fabb_t + chamfer - lyr_offset)]
                    kicad_mod.append(PolygonLine(shape=body_polygon, layer=layer, width=line_width))
        if chamfer > 0 and not (cfg.orientation == 'Horizontal' and cfg.latch_enable):
            kicad_mod.append(Line(start=[fabb_l, fabb_t + chamfer], end=[fabb_l + chamfer, fabb_t], layer=layer, width=line_width))

        # vertical mating connector outline (this is the same for both layers)
        if cfg.orientation == "Vertical":
            if cfg.mount_type == "SMD":
                mating_conn_polygon = [(fabb_l - lyr_offset, center_fab.y - cfg.body_notch_width/2), (fabb_l + cfg.body_wall_thick, center_fab.y - cfg.body_notch_width/2),
                    (fabb_l + cfg.body_wall_thick, fabb_t+cfg.body_wall_thick), (fabb_l + fabb_w - cfg.body_wall_thick, fabb_t+cfg.body_wall_thick),
                    (fabb_l + fabb_w - cfg.body_wall_thick, fabb_t+fabb_h-cfg.body_wall_thick), (fabb_l + cfg.body_wall_thick, fabb_t+fabb_h-cfg.body_wall_thick),
                    (fabb_l + cfg.body_wall_thick, center_fab.y + cfg.body_notch_width/2), (fabb_l + cfg.body_wall_thick, center_fab.y + cfg.body_notch_width/2),
                    (fabb_l - lyr_offset, center_fab.y + cfg.body_notch_width/2)]
                if layer == "F.Fab":
                    # Only append mating connector outline in F.Fab for SMD footprints (silkscreen would be on top of pads)
                    kicad_mod.append(PolygonLine(shape=mating_conn_polygon, layer=layer, width=line_width))
            else:
                mating_conn_polygon = [(fabb_l - lyr_offset, center_fab.y - cfg.body_notch_width/2), (fabb_l + cfg.body_wall_thick, center_fab.y - cfg.body_notch_width/2),
                    (fabb_l + cfg.body_wall_thick, -cfg.mating_overlen), (fabb_l + fabb_w - cfg.body_wall_thick, -cfg.mating_overlen),
                    (fabb_l + fabb_w - cfg.body_wall_thick, (cfg.pos_count - 1) * cfg.pin_pitch + cfg.mating_overlen), (fabb_l + cfg.body_wall_thick, (cfg.pos_count - 1) * cfg.pin_pitch + cfg.mating_overlen),
                    (fabb_l + cfg.body_wall_thick, center_fab.y + cfg.body_notch_width/2), (fabb_l + cfg.body_wall_thick, center_fab.y + cfg.body_notch_width/2),
                    (fabb_l - lyr_offset, center_fab.y + cfg.body_notch_width/2)]
                kicad_mod.append(PolygonLine(shape=mating_conn_polygon, layer=layer, width=line_width))

        # horizontal mating connector 'notch' lines
        if cfg.orientation == 'Horizontal' and not cfg.latch_enable:
            kicad_mod.append(Line(start=[cfg.body_offset - lyr_offset, center_fab.y - cfg.body_notch_width / 2], end=[fabb_l + fabb_w + lyr_offset, center_fab.y - cfg.body_notch_width / 2], layer=layer, width=line_width))
            kicad_mod.append(Line(start=[cfg.body_offset - lyr_offset, center_fab.y + cfg.body_notch_width / 2], end=[fabb_l + fabb_w + lyr_offset, center_fab.y + cfg.body_notch_width / 2], layer=layer, width=line_width))

        # vertical latches (horizontal latches are off the PCB and not shown)
        if cfg.orientation == "Vertical" and cfg.latch_enable and cfg.latch_length > 0:
            # body outline silk lines need to clear the mounting hole on vertical headers
            if mh_present and layer == "F.SilkS":
                # top latch
                latch_top_polygon = [(center_fab.x - cfg.latch_width/2 - lyr_offset, mh_y.x - mhole_pad.y/2 + lyr_offset), (center_fab.x - cfg.latch_width/2 - lyr_offset, fabb_t - cfg.latch_length - lyr_offset),
                    (center_fab.x + cfg.latch_width/2 + lyr_offset, fabb_t - cfg.latch_length - lyr_offset), (center_fab.x + cfg.latch_width/2 + lyr_offset, mh_y.x - mhole_pad.y/2 + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=latch_top_polygon, layer=layer, width=line_width))
                # bottom latch
                latch_bottom_polygon = [(center_fab.x - cfg.latch_width/2 - lyr_offset, mh_y.y + mhole_pad.y/2 - lyr_offset), (center_fab.x - cfg.latch_width/2 - lyr_offset, fabb_t + fabb_h + cfg.latch_length + lyr_offset),
                    (center_fab.x + cfg.latch_width/2 + lyr_offset, fabb_t + fabb_h + cfg.latch_length + lyr_offset), (center_fab.x + cfg.latch_width/2 + lyr_offset, mh_y.y + mhole_pad.y/2 - lyr_offset)]
                kicad_mod.append(PolygonLine(shape=latch_bottom_polygon, layer=layer, width=line_width))
            else:
                # top latch
                latch_top_polygon = [(center_fab.x - cfg.latch_width/2 - lyr_offset, fabb_t - lyr_offset), (center_fab.x - cfg.latch_width/2 - lyr_offset, fabb_t - cfg.latch_length - lyr_offset),
                    (center_fab.x + cfg.latch_width/2 + lyr_offset, fabb_t - cfg.latch_length - lyr_offset), (center_fab.x + cfg.latch_width/2 + lyr_offset, fabb_t - lyr_offset)]
                kicad_mod.append(PolygonLine(shape=latch_top_polygon, layer=layer, width=line_width))
                # bottom latch
                latch_bottom_polygon = [(center_fab.x - cfg.latch_width/2 - lyr_offset, fabb_t + fabb_h + lyr_offset), (center_fab.x - cfg.latch_width/2 - lyr_offset, fabb_t + fabb_h + cfg.latch_length + lyr_offset),
                    (center_fab.x + cfg.latch_width/2 + lyr_offset, fabb_t + fabb_h + cfg.latch_length + lyr_offset), (center_fab.x + cfg.latch_width/2 + lyr_offset, fabb_t + fabb_h + lyr_offset)]
                kicad_mod.append(PolygonLine(shape=latch_bottom_polygon, layer=layer, width=line_width))

    # horizontal pin outlines (only applies if the body is right of the leftmost pin row)
    if cfg.body_offset > 0:
        for pos in range(cfg.pos_count):
            horiz_pin_polygon = [(cfg.body_offset, cfg.pin_pitch * pos - cfg.pins_width / 2), (-cfg.pins_width / 2, cfg.pin_pitch * pos - cfg.pins_width / 2),
                (-cfg.pins_width / 2, cfg.pin_pitch * pos + cfg.pins_width / 2), (cfg.body_offset, cfg.pin_pitch * pos + cfg.pins_width / 2)]
            kicad_mod.append(PolygonLine(shape=horiz_pin_polygon, layer='F.Fab', width=gc.fab_line_width))

    # silk pin 1 mark (triangle to the left of pin 1)
    slk_mark_height = 1
    slk_mark_width = 1
    if cfg.mount_type == "SMD":
        slk_polygon = [(fabb_l - gc.silk_fab_offset, -((cfg.pos_count-1)*cfg.pin_pitch/2)-pad.y/2-0.5), (fabb_l - gc.silk_fab_offset-1.5, -((cfg.pos_count-1)*cfg.pin_pitch/2)-pad.y/2-0.5)]
    else:
        slk_mark_tip = min(fabb_l, -pad.x / 2) - 0.5 # offset 0.5mm from pin 1 or the body
        slk_polygon = [(slk_mark_tip, 0), (slk_mark_tip - slk_mark_width, -slk_mark_height / 2),
            (slk_mark_tip - slk_mark_width, slk_mark_height / 2), (slk_mark_tip, 0)]
    kicad_mod.append(PolygonLine(shape=slk_polygon, layer='F.SilkS', width=gc.silk_line_width))

	# --- create courtyard:
    if cfg.mount_type == "SMD" and cfg.orientation == "Vertical" and not cfg.latch_enable:
        #         crt_l =  -pad.x / 2 - cfg.row_pitch/2- crt_offset
        y_outdent_up = -((cfg.pos_count - 1) / 2 * cfg.pin_pitch) - (pad.y / 2) - crt_offset
        y_outdent_down = ((cfg.pos_count - 1) / 2 * cfg.pin_pitch) + (pad.y / 2) + crt_offset
        kicad_mod.append(
            PolygonLine(
                # top left, outdent left (5 coord), bottom, outdent right (5 coord), top
                shape=[
                    (DT.roundCrt(fabb_l - crt_offset), DT.roundCrt(crt_t)), # top left
                    (DT.roundCrt(fabb_l - crt_offset), DT.roundCrt(y_outdent_up)), # outdent left
                    (DT.roundCrt(crt_l), DT.roundCrt(y_outdent_up)),
                    (DT.roundCrt(crt_l), DT.roundCrt(y_outdent_down)),
                    (DT.roundCrt(fabb_l - crt_offset), DT.roundCrt(y_outdent_down)),
                    (DT.roundCrt(fabb_l - crt_offset), DT.roundCrt(-crt_t)), # bottom left
                    (DT.roundCrt(-fabb_l + crt_offset), DT.roundCrt(-crt_t)), # bottom right
                    (DT.roundCrt(-fabb_l + crt_offset), DT.roundCrt(y_outdent_down)), # outdent right
                    (DT.roundCrt(-crt_l), DT.roundCrt(y_outdent_down)),
                    (DT.roundCrt(-crt_l), DT.roundCrt(y_outdent_up)),
                    (DT.roundCrt(-fabb_l + crt_offset), DT.roundCrt(y_outdent_up)),
                    (DT.roundCrt(-fabb_l + crt_offset), DT.roundCrt(crt_t)), # top right
                    (DT.roundCrt(fabb_l - crt_offset), DT.roundCrt(crt_t)), # top left
                ],
                layer="F.CrtYd",
                width=gc.courtyard_line_width,
            )
        )
    else:
        kicad_mod.append(
            Rectangle(
                start=[DT.roundCrt(crt_l), DT.roundCrt(crt_t)],
                end=[DT.roundCrt(crt_l + crt_w), DT.roundCrt(crt_t + crt_h)],
                layer="F.CrtYd",
                width=gc.courtyard_line_width,
            )
        )

    # --- add model (even if there are mounting holes on the footprint do not include that in the 3D model)
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
