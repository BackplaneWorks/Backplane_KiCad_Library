# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

from dataclasses import dataclass
from typing import List, Union, Callable
# remove after Python 3.11 is required
from typing_extensions import Self

from KicadModTree import Zone, Hatch, Keepouts
from kilibs.util import dict_tools
from . import utils, shape_properties, ast_evaluator

@dataclass
class KeepoutProperties():

    DENY = True
    ALLOW = False

    # Store the rules as booleans, the "allow"/"not_allowed" syntax
    # is only a s-expr format detail that might change in the future
    tracks: bool
    vias: bool
    copperpour: bool
    pads: bool
    footprints: bool

    def __init__(self, keepout_spec):
        self.tracks = self._get_keepout('tracks', keepout_spec)
        self.vias = self._get_keepout('vias', keepout_spec)
        self.copperpour = self._get_keepout('copperpour', keepout_spec)
        self.pads = self._get_keepout('pads', keepout_spec)
        self.footprints = self._get_keepout('footprints', keepout_spec)

    def _get_keepout(self, keepout_name, keepout_spec):
        """
        Get the value of a keepout rule. The default is to allow everything.
        """
        value = keepout_spec.get(keepout_name, 'allow')

        if value not in ['allow', 'deny']:
            raise ValueError(f"Rule {keepout_name} must be either 'allow' or 'deny'")

        return self.DENY if value == 'deny' else self.ALLOW

@dataclass
class RuleAreaProperties():
    """
    The properties for a single keepout definition, as defined in the YAML file.

    One of these definitions defines one or more physical keepout areas.
    """
    name: str
    layers: list

    # A list of rules that define the keepout area)
    keepouts: dict

    # A list of the shapes that define the keepout area(s)
    shapes: list

    def __init__(self, rule_area_spec):
        self.name = self._get_rule_area_name(rule_area_spec)
        self.layers = self._get_rule_area_layers(rule_area_spec)
        self.keepouts = KeepoutProperties(rule_area_spec.get('keepouts', {}))
        self.shapes = self._get_rule_area_shapes(rule_area_spec)

    def _get_rule_area_name(self, rule_area_spec):
        """
        Get the name of the keepout area.

        This is the name of the keepout area as defined in the YAML file.

        It is allowed to have multiple keepout areas with the same name,
        and also keepout areas with no name at all: they're just strings.
        """
        return rule_area_spec.get('name', None)

    def _get_rule_area_layers(self, rule_area_spec):

        layers = rule_area_spec.get('layers', [])

        if not layers:
            raise ValueError('Must specify at least one layer for keepout area')

        return utils.as_list(layers)

    def _get_rule_area_shapes(self, rule_area_spec):
        """
        Get the shapes that define the keepout area.
        """
        shapes_spec = rule_area_spec.get('shapes', [])

        if not shapes_spec:
            raise ValueError('Must specify at least one shape for keepout area')

        shapes = []

        for shape_spec in shapes_spec:
            shape = shape_properties.construct_shape(shape_spec)
            shapes.append(shape)

        return shapes

    def from_standard_yaml(parent_spec: dict, key: str="rule_areas") -> List[Self]:

        rule_areas = []
        rule_area_specs = parent_spec.get(key, None)
        if rule_area_specs is not None:

            # process inheritance of the rule area definitions
            dict_tools.dict_inherit(rule_area_specs)

            for _, rule_area_spec in rule_area_specs.items():
                rule_area = RuleAreaProperties(rule_area_spec)
                rule_areas.append(rule_area)

        return rule_areas


def create_rule_area_zones(rule_areas: Union[RuleAreaProperties, List[RuleAreaProperties]],
                           expr_evaluator: Callable) -> List[Zone]:
    """
    Create the zones from the given rule area properties, after evaulating any expressions
    in the rule area shapes.
    """

    if not isinstance(rule_areas, list):
        rule_areas = [rule_areas]

    zones = []

    for rule_area in rule_areas:
        # create the shapes
        for shape in rule_area.shapes:

            # First construct the rule area polygon from the shape definition
            if isinstance(shape, shape_properties.RectProperties):
                rect = shape.evaluate(expr_evaluator)
                layers = rule_area.layers

                # Map spec keepout rules to the KicadModTree format
                keepouts = Keepouts(
                    tracks=rule_area.keepouts.tracks,
                    vias=rule_area.keepouts.vias,
                    pads=rule_area.keepouts.pads,
                    copperpour=rule_area.keepouts.copperpour,
                    footprints=rule_area.keepouts.footprints,
                )

                zone = Zone(shape=rect,
                            layers=layers,
                            hatch=Hatch(Hatch.EDGE, 0.5),
                            net=0,
                            net_name="",
                            name=rule_area.name,
                            keepouts=keepouts,
                )
                zones.append(zone)
            else:
                raise ValueError(f"Unsupported shape type {shape}")

    return zones
