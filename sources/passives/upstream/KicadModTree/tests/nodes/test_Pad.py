from KicadModTree import Footprint, FootprintType, RoundRadiusHandler
from KicadModTree.nodes.base.Pad import Pad
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest
from kilibs.geom import CornerSelection, Vector2D

# Basic pad test arguments
DEFAULT_FCU_KWARGS = {
    "number": "42",
    "at": Vector2D(0, 0),
    "size": Vector2D(1, 1),
    "drill": 0.5,
    "shape": Pad.SHAPE_RECT,
    "type": Pad.TYPE_THT,
    "layers": ["F.Cu"],
}

# EXample pad with a chamfer, but doesn't specify a size or ratio
PAD_CHAMFER_KWARGS = {
    "number": "42",
    "at": Vector2D(0, 0),
    "size": Vector2D(2, 2),  # not 1 to make sure size != ratio
    "shape": Pad.SHAPE_ROUNDRECT,
    "type": Pad.TYPE_SMT,
    "layers": ["F.Cu"],
    "chamfer_corners": CornerSelection(
        corner_selection={CornerSelection.BOTTOM_LEFT: True}
    ),
    "round_radius_handler": RoundRadiusHandler(
        radius_ratio=0.25,
    ),
}


class TestPadSerialisation(SerialisationTest):

    RESULTS_DIR_NAME = 'data'

    def test_basic(self):

        pad = Pad(**DEFAULT_FCU_KWARGS)

        assert pad.number == "42"
        assert pad.at == Vector2D(0, 0)
        assert pad.size == Vector2D(1, 1)
        assert pad.shape == Pad.SHAPE_RECT
        assert pad.type == Pad.TYPE_THT
        assert pad.layers == ["F.Cu"]

        # Check defaults
        assert pad.fab_property is None
        assert pad.zone_connection == Pad.ZoneConnection.INHERIT

        kicad_mod = Footprint("padtest", FootprintType.SMD)
        kicad_mod.append(pad)
        self.assert_serialises_as(kicad_mod, 'pad_basic.kicad_mod')

    def test_fab_property(self):

        pad = Pad(
            **DEFAULT_FCU_KWARGS,
            fab_property=Pad.FabProperty.HEATSINK,
        )

        kicad_mod = Footprint("padtest", FootprintType.SMD)
        kicad_mod.append(pad)
        self.assert_serialises_as(kicad_mod, 'pad_heatsink.kicad_mod')

    def test_zone_connection(self):

        pad = Pad(
            **DEFAULT_FCU_KWARGS,
            zone_connection=Pad.ZoneConnection.SOLID,
            unconnected_layer_mode=Pad.UnconnectedLayerMode.REMOVE_EXCEPT_START_AND_END,
            thermal_bridge_angle=10,
            clearance=1,
        )

        assert pad.zone_connection == Pad.ZoneConnection.SOLID

        kicad_mod = Footprint("padtest", FootprintType.SMD)
        kicad_mod.append(pad)
        self.assert_serialises_as(kicad_mod, 'pad_zone_connection.kicad_mod')

    def test_basic_chamfer_rounded(self):

        # Copy the default args fo
        pad_kwargs = PAD_CHAMFER_KWARGS.copy()

        # Leave the round radius handler and chamfer size handler as default
        pad = Pad(**pad_kwargs)

        kicad_mod = Footprint("padtest", FootprintType.SMD)
        kicad_mod.append(pad)

        # check the corner and handlers are set
        assert pad.chamfer_size_handler.chamfer_requested()
        assert pad.chamfer_ratio == 0.25
        assert pad.radius_ratio == 0.25
        assert pad.chamfer_corners.bottom_left

        # And we can use this one to test the serialisation
        self.assert_serialises_as(kicad_mod, 'pad_chamfer_basic.kicad_mod')
