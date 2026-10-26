import pytest

from KicadModTree.util.corner_handling import ChamferSizeHandler
from kilibs.geom import Vector2D


class TestChamferHandler:

    def test_non_square(self):
        # For now, the ChamferSizeHandler only supports square chamfers
        # (and ChamferedPad does its own thing)
        with pytest.raises(ValueError):
            ChamferSizeHandler(
                chamfer_size=Vector2D(0.1, 0.2)
            )

    def test_chamfer_size(self):

        chamfer_handler = ChamferSizeHandler(
            chamfer_size=Vector2D(0.1, 0.1)
        )

        assert chamfer_handler.chamfer_requested()

        # Computed values
        assert chamfer_handler.get_chamfer_ratio(2) == 0.05
        assert chamfer_handler.get_chamfer_size(2) == 0.1

    def test_chamfer_exact(self):

        chamfer_handler = ChamferSizeHandler(
            chamfer_exact=0.1
        )

        assert chamfer_handler.chamfer_requested()

        # Computed values

        # Size on the limit of the maximums kicking in
        assert chamfer_handler.get_chamfer_ratio(0.2) == 0.1 / 0.2
        assert chamfer_handler.get_chamfer_size(0.2) == 0.1

        # Can't make a ratio larger than the size
        with pytest.raises(ValueError):
            chamfer_handler.get_chamfer_ratio(0.1)
