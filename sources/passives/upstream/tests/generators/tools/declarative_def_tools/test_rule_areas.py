import yaml

from generators.tools.footprint.declarative_def_tools import rule_area_properties as RAP
from generators.tools.footprint.declarative_def_tools import shape_properties as SP


def test_basic():

    spec = """
name: test
layers: F.Cu
keepouts:
    vias: allow
    tracks: deny
shapes:
    - type: rect
      corners: [[a,b], [c,1]]
"""
    spec_yaml = yaml.safe_load(spec)

    kp = RAP.RuleAreaProperties(spec_yaml)

    assert kp.name == "test"

    assert kp.layers == ["F.Cu"]

    assert kp.keepouts.vias == RAP.KeepoutProperties.ALLOW
    assert kp.keepouts.tracks == RAP.KeepoutProperties.DENY

    assert len(kp.shapes) == 1

    rect = kp.shapes[0]

    # Make sure we decoded to the right shape
    assert isinstance(rect, SP.RectProperties)


def test_multilayer():

    spec = """
name: test
layers: [F.Cu, B.Cu]
keepouts:
    tracks: deny
shapes:
    - type: rect
      corners: [[a,b], [c,1]]
"""
    spec_yaml = yaml.safe_load(spec)

    kp = RAP.RuleAreaProperties(spec_yaml)

    assert kp.name == "test"

    assert kp.layers == ["F.Cu", "B.Cu"]
