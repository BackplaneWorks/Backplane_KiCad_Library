
from kilibs.geom import CornerSelection


def test_corner_selection():

    cs = CornerSelection(corner_selection=None)

    assert cs.is_any_selected() is False

    cs = CornerSelection(corner_selection={CornerSelection.TOP_LEFT: True})

    assert cs.is_any_selected() is True

    cs.clear_all()

    assert cs.is_any_selected() is False
