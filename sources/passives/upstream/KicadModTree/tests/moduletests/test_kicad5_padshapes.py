# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) 2018 by Rene Poeschl, github @poeschlr

from __future__ import division

import pytest

from KicadModTree import *
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest


class TestKicad5Pads(SerialisationTest):

    def testRoundRectPad(self):
        kicad_mod = Footprint("roundrect_pad", FootprintType.SMD)

        kicad_mod.append(Pad(number=3, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
                             at=[5, 0], rotation=45, size=[1, 1], layers=Pad.LAYERS_SMT,
                             round_radius_handler=RoundRadiusHandler(
                                 radius_ratio=0.1,
                             )))

        kicad_mod.append(Pad(number=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
                             at=[-5, 0], size=[1, 1], layers=Pad.LAYERS_SMT,
                             round_radius_handler=RoundRadiusHandler(
                                 radius_ratio=0.5,
                             )))

        kicad_mod.append(Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
                             at=[0, 0], size=[1, 1], layers=Pad.LAYERS_SMT,
                             round_radius_handler=RoundRadiusHandler(
                                 radius_ratio=0,
                             )))

        self.assert_serialises_as(kicad_mod, 'padshape_roundrect.kicad_mod')

    def testRoundRectPad2(self):
        kicad_mod = Footprint("roundrect_pad2", FootprintType.SMD)

        round_radius_handler = RoundRadiusHandler(
            radius_ratio=0.25, maximum_radius=0.25
        )

        kicad_mod.append(Pad(number=3, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
                             at=[5, 0], rotation=45, size=[1, 1], layers=Pad.LAYERS_SMT,
                             round_radius_handler=round_radius_handler))

        kicad_mod.append(Pad(number=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
                             at=[-5, 0], size=[1, 2], layers=Pad.LAYERS_SMT,
                             round_radius_handler=round_radius_handler))

        kicad_mod.append(Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
                             at=[0, 0], size=[2, 4], layers=Pad.LAYERS_SMT,
                             round_radius_handler=round_radius_handler))

        self.assert_serialises_as(kicad_mod, 'padshape_roundrect2.kicad_mod')

    def testPolygonPad(self):
        kicad_mod = Footprint("polygon_pad", FootprintType.SMD)

        polygon = Polygon(
            shape=[(-1, -1), (2, -1), (1, 1), (-1, 2)],
            fill=True,
            width=0,
        )

        kicad_mod.append(
            Pad(
                number=1,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_CUSTOM,
                at=[0, 0],
                size=[1, 1],
                layers=Pad.LAYERS_SMT,
                primitives=[polygon],
            )
        )

        self.assert_serialises_as(kicad_mod, 'padshape_simple_polygon.kicad_mod')

    def testCustomPadOtherPrimitives(self):
        kicad_mod = Footprint("custom_pad_other", FootprintType.SMD)

        kicad_mod.append(
            Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_CUSTOM,
                at=[0, 0], size=[1, 1], layers=Pad.LAYERS_SMT,
                primitives=[
                     Arc(center=(-1, 0), start=(-1, -0.5), angle=-180, width=0.15),
                     Line(start=(-1, -0.5), end=(1.25, -0.5), width=0.15),
                     Line(start=(1.25, -0.5), end=(1.25, 0.5), width=0.15),
                     Line(start=(1.25, 0.5), end=(-1, 0.5), width=0.15)
                     ]
                ))

        kicad_mod.append(
            Pad(number=2, type=Pad.TYPE_SMT, shape=Pad.SHAPE_CUSTOM,
                at=[0, 3], size=[1, 1], layers=Pad.LAYERS_SMT,
                primitives=[
                     Arc(center=(-1, 0), start=(-1, -0.5), angle=-180, width=0.15),
                     PolygonLine(shape=[(-1, -0.5), (1.25, -0.5), (1.25, 0.5), (-1, 0.5)], width=0.15)
                     ]
                ))

        kicad_mod.append(
            Pad(number=3, type=Pad.TYPE_SMT, shape=Pad.SHAPE_CUSTOM,
                at=[0, -3], size=[1, 1], layers=Pad.LAYERS_SMT,
                primitives=[
                        Circle(center=(0.5, 0.5), radius=0.5, width=0.15)
                     ]
                ))

        self.assert_serialises_as(kicad_mod, 'padshape_other_custom.kicad_mod')

    @pytest.mark.filterwarnings("ignore:No geometry checks")
    def testCutPolygon(self):
        kicad_mod = Footprint("cut_polygon", FootprintType.SMD)

        p1 = Polygon(shape=[(0, 0), (1, 0), (1, 1), (0, 1)], fill=True, width=0, layer=None)
        p2 = Polygon(shape=[(-2, -2), (2, -2), (2, 2), (-2, 2)], fill=True, width=0, layer=None)
        p2.cut_with_polygon(p1)

        kicad_mod.append(Pad(number=1, type=Pad.TYPE_SMT, shape=Pad.SHAPE_CUSTOM,
                             at=[0, 0], size=[0.5, 0.5], layers=Pad.LAYERS_SMT,
                             primitives=[p2]
                             ))

        self.assert_serialises_as(kicad_mod, 'padshape_cut_polygon.kicad_mod')

    def testChamferedPad(self):
        kicad_mod = Footprint("chamfered_pad", FootprintType.SMD)

        radius_handler = RoundRadiusHandler(radius_ratio=0)

        kicad_mod.append(
            ChamferedPad(number=1, type=Pad.TYPE_SMT,
                         at=[0, 0], size=[1, 1], layers=Pad.LAYERS_SMT, chamfer_size=[1/3, 1/3],
                         corner_selection=[1, 1, 1, 1],
                         round_radius_handler=radius_handler))

        kicad_mod.append(
            ChamferedPad(number=1, type=Pad.TYPE_SMT,
                         at=[2, 2], size=[2.1, 3.1], layers=Pad.LAYERS_SMT, chamfer_size=[0.5, 1.05],
                         corner_selection=[1, 1, 1, 1],
                         round_radius_handler=radius_handler))

        self.assert_serialises_as(kicad_mod, 'padshape_chamfered.kicad_mod')

    def testChamferedPadAvoidCircle(self):
        kicad_mod = Footprint("avoid_circle", FootprintType.SMD)

        radius_handler = RoundRadiusHandler(radius_ratio=0)
        at = Vector2D(2, 2.5)
        size = Vector2D(1.75, 2.25)
        c = Vector2D(3, 3.5)
        d = 0.6
        kicad_mod.append(Circle(center=c, radius=d/2, width=0.01))
        chamfer_size = ChamferedPad.get_chamfer_to_avoid_circle(
            center=c, at=at, size=size, diameter=d, clearance=0.005
        )
        pad = ChamferedPad(
                    number=1, type=Pad.TYPE_SMT, at=at,
                    size=size, layers=Pad.LAYERS_SMT, chamfer_size=chamfer_size,
                    corner_selection=[1, 1, 1, 1],
                    round_radius_handler=radius_handler)
        kicad_mod.append(pad)

        self.assert_serialises_as(kicad_mod, 'padshape_chamfered_avoid_circle.kicad_mod')

    def testChamferedPadGrid(self):
        kicad_mod = Footprint("chamfered_grid", FootprintType.SMD)

        radius_handler = RoundRadiusHandler(radius_ratio=0)

        kicad_mod.append(
            ChamferedPadGrid(
                        number=1, type=Pad.TYPE_SMT,
                        center=Vector2D(1.5, 2.5), size=Vector2D(1, 2), layers=Pad.LAYERS_SMT,
                        chamfer_size=Vector2D(0.25, 0.25), chamfer_selection=1,
                        pincount=[3, 4], grid=Vector2D(1.5, 2.5),
                        round_radius_handler=radius_handler))

        self.assert_serialises_as(kicad_mod, 'padshape_chamfered_grid.kicad_mod')

    def testChamferedPadGridCornerOnly(self):
        kicad_mod = Footprint("chamfered_grid_corner_only", FootprintType.SMD)

        radius_handler = RoundRadiusHandler(radius_ratio=0)

        chamfer_select = ChamferSelPadGrid(0)
        chamfer_select.set_corners()

        pad = ChamferedPadGrid(
                        number=1, type=Pad.TYPE_SMT,
                        center=Vector2D(0, 0), size=Vector2D(1, 1), layers=Pad.LAYERS_SMT,
                        chamfer_size=Vector2D(0.25, 0.25), chamfer_selection=chamfer_select,
                        pincount=[3, 4], grid=Vector2D(1.4, 1.4),
                        round_radius_handler=radius_handler)

        c = [2.0, 2.5]
        d = 0.4

        kicad_mod.append(Circle(center=c, radius=d/2, width=0.01))
        pad.get_chamfer_to_avoid_circle(center=c, diameter=d, clearance=0.005)
        kicad_mod.append(pad)

        self.assert_serialises_as(kicad_mod, 'padshape_chamfered_grid_avoid_circle.kicad_mod')

    def testChamferedRoundedPad(self):
        kicad_mod = Footprint("chamfered_round_pad", FootprintType.SMD)

        radius_handler0 = RoundRadiusHandler(radius_ratio=0)
        radius_handler25 = RoundRadiusHandler(radius_ratio=0.25)

        kicad_mod.append(
            ChamferedPad(number=1, type=Pad.TYPE_SMT,
                         at=[0, 0], size=[4, 4], layers=Pad.LAYERS_SMT, chamfer_size=[0.5, 0.5],
                         corner_selection=[1, 1, 1, 1],
                         round_radius_handler=radius_handler0))

        kicad_mod.append(
            ChamferedPad(number=1, type=Pad.TYPE_SMT,
                         at=[0, 0], size=[4, 4], layers=["B.Cu"], chamfer_size=[0.5, 0.5],
                         corner_selection=[1, 1, 1, 1],
                         round_radius_handler=radius_handler25))

        kicad_mod.append(
            ChamferedPad(number=1, type=Pad.TYPE_SMT,
                         at=[0, 5], size=[4, 3], layers=Pad.LAYERS_SMT, chamfer_size=[1, 1],
                         corner_selection=[1, 1, 1, 1],
                         round_radius_handler=radius_handler0))

        kicad_mod.append(
            ChamferedPad(number=1, type=Pad.TYPE_SMT,
                         at=[0, 5], size=[4, 3], layers=["B.Cu"], chamfer_size=[1, 1],
                         corner_selection=[1, 1, 1, 1],
                         round_radius_handler=radius_handler25))

        kicad_mod.append(
            ChamferedPad(number=1, type=Pad.TYPE_SMT,
                         at=[5, 0], size=[4, 3], layers=Pad.LAYERS_SMT, chamfer_size=[1, 1],
                         corner_selection=[1, 0, 1, 0],
                         round_radius_handler=radius_handler0))

        kicad_mod.append(
            ChamferedPad(number=1, type=Pad.TYPE_SMT,
                         at=[5, 0], size=[4, 3], layers=["B.Cu"], chamfer_size=[1, 1],
                         corner_selection=[1, 0, 1, 0],
                         round_radius_handler=radius_handler25))

        self.assert_serialises_as(kicad_mod, 'padshape_chamfered_rounded.kicad_mod')
