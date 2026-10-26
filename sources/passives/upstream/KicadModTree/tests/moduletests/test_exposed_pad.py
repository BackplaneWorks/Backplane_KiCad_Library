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

from KicadModTree import *
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest
from KicadModTree.util import corner_handling

DEFAULT_CU_RAD_HANDLER = corner_handling.RoundRadiusHandler(
    radius_ratio=0, maximum_radius=0.25
)
DEFAULT_PASTE_RAD_HANDLER = corner_handling.RoundRadiusHandler(
    radius_ratio=0, maximum_radius=0.25
)


class TestExposedPads(SerialisationTest):

    def testSimpleExposedPad(self):
        kicad_mod = Footprint("exposedpad_simple", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, at=Vector2D(0, 1), size=Vector2D(2.1, 3),
            mask_size=Vector2D(2.1, 2.1), paste_layout=[2, 3], via_layout=[3, 2],
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, 'exposedpad_simple.kicad_mod')

    def testSimpleExposedPadNoRounding(self):
        kicad_mod = Footprint("exposedpad_no_rounding", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, at=Vector2D(0, 1), size=Vector2D(2.1, 3),
            mask_size=Vector2D(2.1, 2.1), paste_layout=[2, 3], via_layout=[3, 2],
            grid_round_base=None, size_round_base=0,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, 'exposedpad_no_rounding.kicad_mod')

    def testSimpleExposedMinimal(self):
        kicad_mod = Footprint("exposedpad_minimal", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=[2.1, 3], paste_layout=2, via_layout=3,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, 'exposedpad_minimal.kicad_mod')

    def testExposedPasteAutogenInner(self):
        kicad_mod = Footprint("exposedpad_autogen_inner", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=[5, 5], paste_layout=3, via_layout=2,
            paste_avoid_via=True,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, 'exposedpad_autogen_inner.kicad_mod')

    def testExposedPasteAutogenInner2(self):
        kicad_mod = Footprint("exposedpad_autogen_inner2", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=[5, 5], paste_layout=6, via_layout=4,
            paste_avoid_via=True, paste_coverage=0.5,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, 'exposedpad_autogen_inner2.kicad_mod')

    def testExposedPasteAutogenInnerAndOuter(self):
        kicad_mod = Footprint("exposedpad_autogen_inner_outer", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(12, 8), paste_between_vias=2,
            paste_rings_outside=2, via_layout=3,
            paste_avoid_via=True, paste_coverage=0.7, via_grid=[3, 2],
            via_paste_clarance=0.25, min_annular_ring=0.25, at=Vector2D(7, 5),
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, 'exposedpad_autogen_inner_outer.kicad_mod')

    def testExposedPasteAutogenInnerYonlyAndOuter(self):
        kicad_mod = Footprint("exposedpad_autogen_inner_y_and_outer", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=[3, 5], paste_between_vias=2, paste_rings_outside=[2, 1], via_layout=[1, 3],
            paste_avoid_via=True, paste_coverage=0.65, via_grid=2, via_paste_clarance=0.15,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, "exposedpad_autogen_inner_y_and_outer.kicad_mod")

    def testExposedPasteAutogenInnerXonlyAndOuther(self):
        kicad_mod = Footprint("exposedpad_autogen_inner_x_and_outer", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=[4, 3], paste_between_vias=2, paste_rings_outside=[1, 2], via_layout=[3, 1],
            paste_avoid_via=True, paste_coverage=0.65, via_grid=1, via_paste_clarance=0.0,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, "exposedpad_autogen_inner_x_and_outer.kicad_mod")

    def testExposedPasteAutogenOnlyOuter(self):
        kicad_mod = Footprint("exposedpad_autogen_only_outer", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=[2, 2], paste_between_vias=0, paste_rings_outside=[1, 1], via_layout=[1, 1],
            paste_avoid_via=True, paste_coverage=0.65, via_grid=1.5,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, "exposedpad_autogen_only_outer.kicad_mod")

    def testExposedPasteBottomPadTests(self):
        kicad_mod = Footprint("exposedpad_autogen_bottom_pad", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(2, 2), via_layout=[1, 1], at=Vector2D(-2, -2),
            paste_coverage=0.65, via_grid=1, bottom_pad_layers=None,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(2, 2), via_layout=[1, 1], at=Vector2D(2, -2),
            paste_coverage=0.65, via_grid=1, bottom_pad_layers=['B.Cu', 'B.Mask'],
            bottom_pad_min_size=[3, 3],
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, "exposedpad_autogen_bottom_pad.kicad_mod")

    def testExposed4x4paste(self):
        kicad_mod = Footprint("exposedpad_autogen_4x4", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=33, size=[3.55, 3.55],
            paste_layout=[3, 3],
            paste_between_vias=1,
            paste_rings_outside=1,
            paste_coverage=0.6,
            via_layout=[3, 3],
            via_drill=0.2,
            via_grid=[1, 1],
            paste_avoid_via=True,
            via_paste_clarance=0.1,
            min_annular_ring=0.15,
            bottom_pad_min_size=[0, 0],
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, "exposedpad_autogen_4x4.kicad_mod")

    def testExposedPadEdgeCase1(self):
        kicad_mod = Footprint("exposedpad_autogen_edgecase1", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(2, 2), via_layout=[2, 1], at=Vector2D(-2, -2),
            paste_coverage=0.65, paste_layout=[1, 2],
            paste_avoid_via=True,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(2, 2), via_layout=[2, 1], at=Vector2D(2, -2),
            paste_coverage=0.65, paste_layout=[1, 2],
            paste_avoid_via=True,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(3, 3), via_layout=[2, 1], at=Vector2D(0, 3),
            paste_coverage=0.65, paste_layout=[1, 2], mask_size=[2, 2],
            paste_avoid_via=True,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, "exposedpad_autogen_edgecase1.kicad_mod")

    def testExposedPasteViaTented(self):
        kicad_mod = Footprint("exposedpad_via_tented", FootprintType.SMD)

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(3, 3), via_layout=[2, 1], at=Vector2D(-2, -2),
            paste_coverage=0.65, paste_layout=[1, 2], mask_size=[2, 2],
            paste_avoid_via=True, via_tented=ExposedPad.VIA_NOT_TENTED,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(3, 3), via_layout=[2, 1], at=Vector2D(2, -2),
            paste_coverage=0.65, paste_layout=[1, 2], mask_size=[2, 2],
            paste_avoid_via=True, via_tented=ExposedPad.VIA_TENTED_BOTTOM_ONLY,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(3, 3), via_layout=[2, 1], at=Vector2D(-2, 2),
            paste_coverage=0.65, paste_layout=[1, 2], mask_size=[2, 2],
            paste_avoid_via=True, via_tented=ExposedPad.VIA_TENTED_TOP_ONLY,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        kicad_mod.append(ExposedPad(
            number=3, size=Vector2D(3, 3), via_layout=[2, 1], at=Vector2D(2, 2),
            paste_coverage=0.65, paste_layout=[1, 2], mask_size=[2, 2],
            paste_avoid_via=True, via_tented=ExposedPad.VIA_TENTED,
            round_radius_handler=DEFAULT_CU_RAD_HANDLER,
            paste_radius_handler=DEFAULT_PASTE_RAD_HANDLER,
        ))

        self.assert_serialises_as(kicad_mod, "exposedpad_via_tented.kicad_mod")
