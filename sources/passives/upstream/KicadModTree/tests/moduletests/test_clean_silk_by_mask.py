from KicadModTree import *
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest


def gen_footprint():
    kicad_mod = Footprint("test", FootprintType.SMD)

    # add a shape on Silk and Fab
    for layer, width in [("F.SilkS", 0.12), ("F.Fab", 0.1)]:
        kicad_mod.append(Line(start=[-5, -2], end=[4.5, -2], layer=layer, width=width))
        kicad_mod.append(Arc(start=[4.5, -2], center=[4.5, -1.5], angle=180, layer=layer, width=width))
        kicad_mod.append(Arc(start=[4.5, -1], center=[4.5, -0.5], angle=-90, layer=layer, width=width))
        kicad_mod.append(Line(start=[4, -0.5], end=[4, 0.5], layer=layer, width=width))
        kicad_mod.append(Arc(start=[4, 0.5], center=[4.5, 0.5], angle=-90, layer=layer, width=width))
        kicad_mod.append(Arc(start=[4.5, 1], center=[4.5, 1.5], angle=180, layer=layer, width=width))
        kicad_mod.append(Line(start=[4.5, 2], end=[-4, 2], layer=layer, width=width))
        kicad_mod.append(Line(start=[-4, 2], end=[-5, 1], layer=layer, width=width))
        kicad_mod.append(Line(start=[-5, 1], end=[-5, -2], layer=layer, width=width))
        for r in range(3):
            kicad_mod.append(Circle(center=[0, 0], radius=0.75 + 0.5 * r, layer=layer, width=width))
        for x in [-3, 3]:
            for y in [-1, 1]:
                kicad_mod.append(Circle(center=[x, y], radius=0.375, layer=layer, width=width))
        # add a polygon line
        kicad_mod.append(Rectangle(start=[-5.2, -2.2], end=[5.2, 2.2], layer=layer, width=width))
    # add some SMT pads
    round_radius_handler = RoundRadiusHandler(radius_ratio=0.25)
    for x in range(-3, 4):
        for y in range(-1, 2, 2):
            pad = Pad(
                at=[x, y],
                shape=Pad.SHAPE_ROUNDRECT,
                type=Pad.TYPE_SMT,
                size=[0.5, 1.0],
                layers=Pad.LAYERS_SMT,
                round_radius_handler=round_radius_handler,
            )
            kicad_mod.append(pad)

    # add some THT Pads
    for x in [-4.75, -1.0, 1.0, 3.75]:
        kicad_mod.append(Pad(at=[x, 0], shape=Pad.SHAPE_CIRCLE, type=Pad.TYPE_THT,
                             drill=0.25, size=[0.5, 0.5], layers=Pad.LAYERS_THT))
    for s in [-1, 1]:
        kicad_mod.append(Pad(at=[-4.5, 1.5 * s], shape=Pad.SHAPE_RECT, type=Pad.TYPE_THT,
                             drill=0.4, size=[1, 1], rotation=20 * s, layers=Pad.LAYERS_THT))
    kicad_mod.append(Pad(at=[5.0, 0], shape=Pad.SHAPE_OVAL, type=Pad.TYPE_THT,
                         drill=0.25, size=[0.5, 0.75], layers=Pad.LAYERS_THT, rotation=90))
    # add some holes
    for n, pos in enumerate([(5.15, -1.85), (5.15, -1.15), (4.0, -1.0)]):
        for s in [-1, 1]:
            kicad_mod.append(Pad(at=Vector2D(pos) * Vector2D(1, s), shape=Pad.SHAPE_CIRCLE,
                                 type=Pad.TYPE_NPTH, drill=0.5, size=[0.5, 0.5], layers=Pad.LAYERS_NPTH))

    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0, -3], layer='F.SilkS'))
    kicad_mod.append(Text(text='${REFERENCE}', at=[0, -3], layer='F.Fab'))
    kicad_mod.append(Property(name=Property.VALUE, text="test", at=[0, 3], layer='F.Fab'))

    return kicad_mod


class TestCleanSilkByMask(SerialisationTest):

    def test_clean_over_smd_rect(self):

        kicad_mod = gen_footprint()

        kicad_mod.clean_silk_mask_overlap(silk_pad_clearance=0.0, silk_line_width=0.12)

        self.assert_serialises_as(kicad_mod, 'test_clean_silk_by_mask.test_clean_over_smd_rect.kicad_mod')
