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
from .temp_tools import Pad2DArrayFromPads, DrawPinArray, chamferRect
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


# SMD Straight (Vertical) Pinheader:
#####################################
# <----------------------> body_width
#        <--------> row_pitch
#     <--> pads_offset
# +----------------------+
# | OOOOOOO              |     ^
# | OOOOOOO ====         |  ^  pads_width
# | OOOOOOO              |  |  v
# +                      +  pin_pitch
# |              OOOOOOO |  |
# |         ==== OOOOOOO |  v
# |              OOOOOOO |
# +                      +
# | OOOOOOO              |
# | OOOOOOO ====         |
def makePinHeadStraightSMD(cfg: FPconfiguration, generator_name: str):
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

    if cfg.mount_type == "SMD":
        pads_c = Vector2D(0, 0)
        p1offset = (Vector2D(-half_rows_x, -half_posn_y)
                    if cfg.pin1_left else
                    Vector2D(half_rows_x, -half_posn_y)
                    )

    # --- Calculate body, fabrication, silk and courtyard dimensions/positions:
    # anchor for SMD-footprints is in the center, for THT-footprints at pin1
    # See Abbreviations at the top.

    # body_overlength is symetrical but keep separated as top/bottom internally.
    overlen_top = cfg.pin_pitch / 2 + cfg.body_overlength / 2
    overlen_bot = cfg.pin_pitch / 2 + cfg.body_overlength / 2

    fabb_h = (cfg.pos_count - 1) * cfg.pin_pitch + overlen_top + overlen_bot
    fabb_w = cfg.body_width
    fabb_t = -(fabb_h / 2) # in case top/bot overlength are symmetrical
    if cfg.isSocket:
        fabb_l = pads_c.x - (cfg.body_width / 2) - cfg.body_offset # PinSockets are drawn to the left.
    else:
        fabb_l = pads_c.x - (cfg.body_width / 2) + cfg.body_offset # PinHeaders/IDC are drawn to the right.
    
    fabb_b = fabb_t + fabb_h
    fabb_r = fabb_l + fabb_w
    if cfg.isSocket:
        fabb_c = pads_c - [cfg.body_offset, 0] # PinSockets are drawn to the left.
    else:
        fabb_c = pads_c + [cfg.body_offset, 0] # PinHeaders/IDC are drawn to the right.
    # print(f'fabb_h:{fabb_h:.3f} w:{fabb_w:.3f} t:{fabb_t:.3f} l:{fabb_l:.3f} c:{fabb_c} overwidth:{fabb_overwidth} offset:{cfg.body_offset}')

    fab_txt_size, fab_txt_thick = gc.get_text_properties_for_layer("F.Fab").clamp_size(fabb_w * 0.6)

    slkb_h = fabb_h + 2 * silk_fab_offset
    slkb_w = fabb_w + 2 * silk_fab_offset
    slkb_t = fabb_t - silk_fab_offset
    slkb_l = fabb_l - silk_fab_offset
    slkb_b = fabb_b + silk_fab_offset
    slkb_r = fabb_r + silk_fab_offset

    crt_h = max(fabb_h, (cfg.pos_count - 1) * cfg.pin_pitch + pad.y) + 2 * crt_offset
    crt_w = max(
        cfg.body_width,
		(cfg.row_count - 1) * cfg.row_pitch + (2 * cfg.pads_offset) + pad.x + (cfg.row_pitch if cfg.row_count>1 and cfg.class_name == "PinHeader" else 0)
    ) + 2 * crt_offset
    crt_t = pads_c.y - (crt_h / 2)
    crt_l = pads_c.x - crt_w/2
    crt_r = crt_l + crt_w
    crt_b = crt_t + crt_h
    crt_c = Vector2D(crt_l + crt_w / 2, crt_t + crt_h / 2)

    # --- Create pads:
    pad_1 = Pad(type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT, at=[0, 0], size=pad, drill=0)
    pad_n = Pad(type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT, at=[0, 0], size=pad, drill=0)

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
        refr_size = [1,1]
        refr_thick = 0.15

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
        chamfer = (cfg.pin_pitch - cfg.pins_width) / 2
        kicad_mod.append(Line(start=[fabb_r, fabb_b], end=[fabb_l, fabb_b], layer='F.Fab', width=gc.fab_line_width))
        if cfg.pin1_left:
            kicad_mod.append(Line(start=[fabb_l + chamfer, fabb_t], end=[fabb_r, fabb_t], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_l, fabb_b], end=[fabb_l, fabb_t + chamfer], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_l, fabb_t + chamfer], end=[fabb_l + chamfer, fabb_t], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_r, fabb_t], end=[fabb_r, fabb_b], layer='F.Fab', width=gc.fab_line_width))
        else:
            kicad_mod.append(Line(start=[fabb_l, fabb_t], end=[fabb_r - chamfer, fabb_t], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_r, fabb_b], end=[fabb_r, fabb_t + chamfer], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_r, fabb_t + chamfer], end=[fabb_r - chamfer, fabb_t], layer='F.Fab', width=gc.fab_line_width))
            kicad_mod.append(Line(start=[fabb_l, fabb_t], end=[fabb_l, fabb_b], layer='F.Fab', width=gc.fab_line_width))

    # ToDo: body_width/2 component should be removed from pins_smd_length in yaml's:
    # calculate adjusted lenght for sticking out part:
    length_adj = half_rows_x + cfg.pins_smd_length - cfg.body_width / 2 # + cfg.pins_offset
    DrawPinArray(
        kicad_mod, size=[length_adj, cfg.pins_width], count=cfg.pos_count, pitch=cfg.pin_pitch, rows=cfg.row_count,
        start_r=[fabb_r, -half_posn_y], start_l=[fabb_l, -half_posn_y], staggered=True, start_left=cfg.pin1_left,
        layer='F.Fab', linewidth=gc.fab_line_width, grid=0.001, oldBehaviorCanvas=oldBehaviorCanvas
    )

    # --- create SILKSCREEN-layer + pin1 marker
    slk_half_pad = pad.y/2 + silk_pad_offset
    y0 = -half_posn_y - slk_half_pad
    if not(oldBehaviorCanvas):
        kicad_mod.append(Line(start=[slkb_l, slkb_t], end=[slkb_r, slkb_t], layer='F.SilkS', width=gc.silk_line_width))
        kicad_mod.append(Line(start=[slkb_l, slkb_b], end=[slkb_r, slkb_b], layer='F.SilkS', width=gc.silk_line_width))

        posleft = range(0, cfg.pos_count, 2)
        posright = range(1, cfg.pos_count, 2)
        if not cfg.pin1_left:
            posleft = range(1, cfg.pos_count, 2)
            posright = range(0, cfg.pos_count, 2)

        if cfg.row_count == 1:
            for pos in posleft:
                y1 = -half_posn_y + (pos-1) * cfg.pin_pitch + slk_half_pad
                y2 = -half_posn_y + (pos+1) * cfg.pin_pitch - slk_half_pad
                if pos == 0:
                    x2 = -cfg.pads_offset - pad.x/2 + gc.silk_line_width/2 # for pin 1 marker
                    kicad_mod.append(Line(start=[slkb_l , y0], end=[x2, y0], layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[slkb_l , slkb_t], end=[slkb_l, y0], layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[slkb_r, -half_posn_y + (cfg.pos_count-1)*cfg.pin_pitch+slk_half_pad],end=[slkb_r, slkb_b],layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[slkb_r, y0], end=[slkb_r, min(slkb_b, y2)], layer='F.SilkS', width=gc.silk_line_width))
                elif pos == cfg.pos_count-1:
                    kicad_mod.append(Line(start=[slkb_r, max(slkb_t, y1)], end=[slkb_r, slkb_b], layer='F.SilkS', width=gc.silk_line_width))
                else:
                    kicad_mod.append(Line(start=[slkb_r, max(slkb_t, y1)], end=[slkb_r, min(slkb_b, y2)], layer='F.SilkS', width=gc.silk_line_width))
            for pos in posright:
                y1 = -half_posn_y + (pos-1) * cfg.pin_pitch + slk_half_pad
                y2 = -half_posn_y + (pos+1) * cfg.pin_pitch - slk_half_pad
                if pos == 0:
                    x2 = cfg.pads_offset + pad.x/2 - gc.silk_line_width/2 # for pin 1 marker
                    kicad_mod.append(Line(start=[slkb_r, y0],end=[x2, y0],layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[slkb_r, slkb_t],end=[slkb_r, y0],layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[slkb_l, -half_posn_y + (cfg.pos_count-1)*cfg.pin_pitch+slk_half_pad],end=[slkb_l, slkb_b],layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[slkb_l , y0],end=[slkb_l, min(slkb_b, y2)], layer='F.SilkS',width=gc.silk_line_width))
                if pos == cfg.pos_count-1:
                    kicad_mod.append(Line(start=[slkb_l , max(slkb_t, y1)],end=[slkb_l, slkb_b], layer='F.SilkS',width=gc.silk_line_width))
                else:
                    kicad_mod.append(Line(start=[slkb_l , max(slkb_t, y1)],end=[slkb_l, min(slkb_b, y2)], layer='F.SilkS',width=gc.silk_line_width))
        if (cfg.row_count==2):
            if cfg.isSocket:
                x1 = cfg.pads_offset + pad.x/2 + cfg.row_pitch # for pin 1 marker?
                y1 = -half_posn_y - (pad.y / 2 + 2*gc.silk_line_width + silk_fab_offset)
                kicad_mod.append(Line(start=[x1, y1], end=[slkb_r, y1], layer='F.SilkS', width=gc.silk_line_width))
            else:
                # -half_rows_x = -(cfg.row_count-1)*cfg.row_pitch/2
                x1 = -cfg.pads_offset - pad.x/2 - cfg.row_pitch/2 + gc.silk_line_width/2  # for pin 1 marker?
                kicad_mod.append(Line(start=[x1, y0], end=[slkb_l, y0], layer='F.SilkS', width=gc.silk_line_width))
                kicad_mod.append(Line(start=[slkb_l , slkb_t], end=[slkb_l, y0], layer='F.SilkS', width=gc.silk_line_width))
                kicad_mod.append(Line(start=[slkb_r , slkb_t], end=[slkb_r, y0], layer='F.SilkS', width=gc.silk_line_width))
                kicad_mod.append(Line(start=[slkb_l, -half_posn_y + (cfg.pos_count-1)*cfg.pin_pitch+slk_half_pad],end=[slkb_l, slkb_b],layer='F.SilkS', width=gc.silk_line_width))
                kicad_mod.append(Line(start=[slkb_r, -half_posn_y + (cfg.pos_count-1)*cfg.pin_pitch+slk_half_pad],end=[slkb_r, slkb_b],layer='F.SilkS', width=gc.silk_line_width))
            if slk_half_pad*2 < cfg.pin_pitch - gc.silk_line_width*2:
                for pos in range(0,cfg.pos_count-1):
                    y1 = -half_posn_y + pos*cfg.pin_pitch + slk_half_pad
                    y2 = -half_posn_y + (pos+1)*cfg.pin_pitch - slk_half_pad
                    kicad_mod.append(Line(start=[slkb_l, y1],end=[slkb_l, y2],layer='F.SilkS', width=gc.silk_line_width))
                    kicad_mod.append(Line(start=[slkb_r, y1],end=[slkb_r, y2],layer='F.SilkS', width=gc.silk_line_width))

    elif oldBehaviorCanvas:
        segments = []
        # silk.setOrigin(-w_slk / 2.0, -h_slk / 2.0)
        # .rect(w_slk, h_slk, origin = "topLeft")
        # drawing top line: left to right
        segments = DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_t], end=[slkb_r, slkb_t])], keepouts_silk)
        # drawing vertical line left: top to bottom
        segments += DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_t], end=[slkb_l, slkb_b])], keepouts_silk)
        # drawing bottom line: left to right
        segments += DT.applyKeepouts([GeomLine(start=[slkb_l, slkb_b], end=[slkb_r, slkb_b])], keepouts_silk)
        # drawing vertical line right: top to bottom
        segments += DT.applyKeepouts([GeomLine(start=[slkb_r, slkb_t], end=[slkb_r, slkb_b])], keepouts_silk)
        DT.addLinesToSilk(kicad_mod, segments, gc.silk_line_width, silk_grid)

        # pin1 marker:
        x1 = cfg.pads_offset + pad.x/2 + ((cfg.row_count - 1) * cfg.row_pitch/2) - gc.silk_line_width/2
        if cfg.pin1_left:
            x1 = -x1
            kicad_mod.append(Line(start=[x1 , y0], end=[slkb_l, y0], layer='F.SilkS', width=gc.silk_line_width))
        else:
            kicad_mod.append(Line(start=[slkb_r, y0],end=[x1, y0],layer='F.SilkS', width=gc.silk_line_width))


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
