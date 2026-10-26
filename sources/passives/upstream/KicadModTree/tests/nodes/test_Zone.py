import pytest

from KicadModTree.nodes import Footprint, FootprintType
from KicadModTree.nodes.base.Zone import Hatch, Keepouts, PadConnection, Zone, ZoneFill
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest
from kilibs.geom import Vector2D

DEFAULT_TEST_POLYGON = [
        Vector2D(0, 0),
        Vector2D(0, 1),
        Vector2D(1, 1),
        Vector2D(1, 0),
    ]

DEFAULT_HATCH = Hatch(Hatch.EDGE, 0.5)


class TestZoneSerialisation(SerialisationTest):

    RESULTS_DIR_NAME = 'data'

    def test_basic(self):
        ko = Keepouts(
            tracks=Keepouts.ALLOW,
            vias=Keepouts.DENY,
        )

        z = Zone(
            net=1,
            net_name="GND",
            hatch=DEFAULT_HATCH,
            shape=DEFAULT_TEST_POLYGON,
            priority=1,
            keepouts=ko,
            fill=None,  # test that no fill is OK
        )

        # Test that the basic properties are set correctly via the constructor
        assert z.net == 1
        assert z.net_name == "GND"
        assert z.hatch.style == Hatch.EDGE
        assert z.hatch.pitch == 0.5
        assert z.priority == 1
        assert z.keepouts.tracks == Keepouts.ALLOW
        assert z.keepouts.vias == Keepouts.DENY

        assert z.connect_pads.type == PadConnection.THERMAL_RELIEF
        assert z.connect_pads.clearance == 0

        assert z.fill.fill == ZoneFill.FILL_NONE

        kicad_mod = Footprint("zonetest", FootprintType.UNSPECIFIED)
        kicad_mod.append(z)

        self.assert_serialises_as(kicad_mod, 'zone_basic.kicad_mod')

    def test_fill(self):
        zf = ZoneFill(
            fill=ZoneFill.FILL_SOLID,
            smoothing=ZoneFill.SMOOTHING_FILLET,
            island_removal_mode=ZoneFill.ISLAND_REMOVAL_REMOVE,
        )

        # Test that the properties are set correctly via the constructor
        assert zf.fill == ZoneFill.FILL_SOLID
        assert zf.smoothing == ZoneFill.SMOOTHING_FILLET
        assert zf.island_removal_mode == ZoneFill.ISLAND_REMOVAL_REMOVE

        assert zf.island_area_min is None

        z = Zone(
            hatch=DEFAULT_HATCH,
            shape=DEFAULT_TEST_POLYGON,
            fill=zf,
        )

        kicad_mod = Footprint("filltest", FootprintType.UNSPECIFIED)
        kicad_mod.append(z)

        self.assert_serialises_as(kicad_mod, 'zone_with_fill.kicad_mod')

    def test_island_removal_area_min(self):

        # Test that island_area_min is required when island_removal_mode is
        with pytest.raises(ValueError):
            zf = ZoneFill(
                island_removal_mode=ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA,
                island_area_min=None,
            )

        # Test that island_area_min only works with the correct island_removal_mode
        with pytest.raises(ValueError):
            zf = ZoneFill(
                island_removal_mode=ZoneFill.ISLAND_REMOVAL_REMOVE,
                island_area_min=0.1,
            )

        zf = ZoneFill(
            island_removal_mode=ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA,
            island_area_min=0.1,
        )

        assert zf.island_removal_mode == ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA
        assert zf.island_area_min == 0.1

        z = Zone(
            hatch=DEFAULT_HATCH,
            shape=DEFAULT_TEST_POLYGON,
            fill=zf,
        )

        kicad_mod = Footprint("island_min", FootprintType.UNSPECIFIED)
        kicad_mod.append(z)

        self.assert_serialises_as(kicad_mod, 'zone_island_min.kicad_mod')
