from KicadModTree import *
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest


class TestRotation(SerialisationTest):

    def testTextRotation(self):
        kicad_mod = Footprint("test_rotate_text", FootprintType.SMD)

        center = Vector2D(0, 0)
        at = center+Vector2D(2, 0)

        for t in range(0, 360, 45):
            kicad_mod.append(
                Text(text="-1", at=at).rotate(t, origin=center))

        self.assert_serialises_as(kicad_mod, 'rotation_text.kicad_mod')

    def testLineRotation(self):
        kicad_mod = Footprint("test_rotate_line", FootprintType.SMD)

        center = Vector2D(4, 0)
        start = center + Vector2D(2, 0)
        end = start + Vector2D(1, 1)

        for t in range(0, 360, 15):
            kicad_mod.append(
                Line(start=start, end=end).rotate(t, origin=center))

        self.assert_serialises_as(kicad_mod, 'rotation_line.kicad_mod')

    def testArcRotation(self):
        kicad_mod = Footprint("test_rotate_arc", FootprintType.SMD)

        rot_center = Vector2D(4, 0)
        mid = rot_center + Vector2D(2, 0)
        center = rot_center + Vector2D(2, 1)
        angle = 90

        for t in range(0, 360, 15):
            kicad_mod.append(
                Arc(center=center, mid=mid, angle=angle)
                .rotate(angle/3, origin=center)
                .rotate(t, origin=rot_center))

        self.assert_serialises_as(kicad_mod, 'rotation_arc.kicad_mod')

    def testCircleRotation(self):
        kicad_mod = Footprint("test_rotate_circle", FootprintType.SMD)

        rot_center = Vector2D(4, -2)
        center = rot_center + Vector2D(2, 1)
        radius = 1

        for t in range(0, 360, 15):
            kicad_mod.append(
                Circle(center=center, radius=radius).rotate(t, origin=rot_center))

        self.assert_serialises_as(kicad_mod, 'rotation_circle.kicad_mod')

    def testPolygonRotation(self):
        kicad_mod = Footprint("test_rotate_polygon", FootprintType.SMD)

        rot_center = Vector2D(2.1, -1.3)

        points = [(-1, 0), (-1.2, 0.5), (0, 0), (-1.2, -0.5)]

        for t in range(0, 360, 60):
            kicad_mod.append(
                Polygon(shape=points, fill=True, width=None, layer="F.SilkS").rotate(t, origin=rot_center))

        self.assert_serialises_as(kicad_mod, 'rotation_polygon.kicad_mod')

    def testPadRotation(self):
        kicad_mod = Footprint("test_rotate_pad", FootprintType.SMD)

        rot_center = Vector2D(0.35, 0)
        points = [(-1, 0), (-1.2, 0.5), (0, 0), (-1.2, -0.5)]
        prim = Polygon(shape=points, fill=True, width=None, layer=None)
        i = 1
        for t in range(0, 300, 60):
            kicad_mod.append(
                Pad(
                    number=i, type=Pad.TYPE_SMT, shape=Pad.SHAPE_CUSTOM,
                    at=[0, 0], size=[0.2, 0.2], layers=Pad.LAYERS_SMT,
                    primitives=[prim]
                    ).rotate(t, origin=rot_center))
            i += 1

        self.assert_serialises_as(kicad_mod, 'rotation_pad.kicad_mod')
