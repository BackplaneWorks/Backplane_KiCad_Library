import pytest

from generators.tools.footprint.declarative_def_tools import ast_evaluator
from generators.tools.footprint.declarative_def_tools import fp_additional_drawing as AD
from tests.generators.test_utils import node_test_utils
from tests.generators.test_utils.node_test_utils import testing_global_config


def test_basic(testing_global_config):

    spec = {
        "additional_drawings": {
            "port_inner": {
                "type": "circle",
                "layer": "mechanical",
                "width": 0.1,
                "center": [0, 0],
                "diameter": 3.0,
            },
            "port_outer": {
                "type": "circle",
                "layer": "mechanical",
                "width": 0.1,
                "center": ["$(FooVar + 1)", 0],
                "diameter": 1.0,
            },
        }
    }

    # This creates the AdditionalDrawing objects from the spec
    # which we will later resolve into actual drawing nodes with
    # the AST evaluator and other parameters.
    ads = AD.FPAdditionalDrawing.from_standard_yaml(spec)

    assert len(ads) == 2

    # From this high level (FPAdditionalDrawing) the only interface we get
    # (or need!) is the one that returns the nodes to draw. We don't care,
    # and aren't told, about the details of how the shapes are configured.

    eval_symbols = {
        "FooVar": 42,
    }

    evaluator = ast_evaluator.ASTevaluator(symbols=eval_symbols)

    nodes = AD.create_additional_drawings(ads, testing_global_config, evaluator)

    assert len(nodes) == 2

    c1 = node_test_utils.find_circles(nodes, radius=1.5)[0]
    c2 = node_test_utils.find_circles(nodes, radius=0.5)[0]

    assert c1.layer == "Cmts.User"
    assert c1.width == 0.1
    assert c1.center.x == 0
    assert c1.center.y == 0

    assert c2.layer == "Cmts.User"
    assert c2.width == 0.1
    assert c2.center.x == pytest.approx(43)  # FooVar + 1
    assert c2.center.y == 0
