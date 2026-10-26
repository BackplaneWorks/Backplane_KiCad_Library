from KicadModTree import *
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest


def gen_footprint(offsets: list):
    kicad_mod = Footprint("test", FootprintType.SMD)

    # add a shape on Silk and Fab
    poly = PolygonLine(
        shape=[
            # left contour
            (-3, 2), (-5, -2),
            # top contour
            (-5, -3), (-4, -3), (-4, -2.5), (4, -2.5), (4, -3), (5, -3),
            # right contour
            (5, -2.5), (6, -2), (6, -1.8), (5, -2),     # 1st ear
            (5, 2), (6, 2), (5, 2.05), (5, 3),
            # bottom contour
            (5, 3), (-4, 3), (-5, 2),
        ], layer="F.Fab", width=0.1)
    kicad_mod.append(poly)
    for offset in offsets:
        poly_copy = poly.copy_with(layer="F.SilkS", width=0.1)
        poly_copy.inflate(amount=offset)
        poly_copy.simplify()
        kicad_mod.append(poly_copy)

    kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[0, -5], layer='F.SilkS'))
    kicad_mod.append(Text(text='${REFERENCE}', at=[0, -5], layer='F.Fab'))
    kicad_mod.append(Property(name=Property.VALUE, text="test", at=[0, 5], layer='F.Fab'))

    return kicad_mod


class TestPolygonOffset(SerialisationTest):

    def test_offset(self):
        kicad_mod = gen_footprint(offsets=[0.2, 0.4, 0.6])
        self.assert_serialises_as(kicad_mod, 'test_offset_polygon.test_offset.kicad_mod')
