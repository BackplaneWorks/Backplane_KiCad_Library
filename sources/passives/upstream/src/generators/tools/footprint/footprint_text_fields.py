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

from kilibs.geom import BoundingBox, GeomRectangle
from KicadModTree import Text, Property, Vector2D

from kilibs.config.global_config import GlobalConfig, FieldProperties, FieldPosition


def _roundToBase(value, base):
    return round(value/base) * base


def _getTextFieldDetails(
    global_config: GlobalConfig,
    field_definition: FieldProperties,
    body_edges: BoundingBox,
    courtyard: BoundingBox,
    text_y_inside_position: float | str="center",
    allow_rotation=False,
):
    body_size = body_edges.size
    body_center = body_edges.center

    # Pull out the layer config for the field
    layer_config = global_config.get_text_properties_for_layer(field_definition.layer)

    # We have some internal options like "inside left/right", so use a string
    position_y: str = field_definition.position_y.value
    at = Vector2D(body_center)

    if body_size.x < body_size.y and allow_rotation and position_y == FieldPosition.INSIDE.value:
        rotation = 1
    else:
        rotation = 0

    def _get_body_size_for_rotation(r: int):
        return body_size.y if r else body_size.x

    if not field_definition.autosize:
        size = layer_config.size_nom
        fontwidth = layer_config.thickness_ratio * size
    else:
        # We want at least 3 char reference designators space. If we can't fit these we move the reverence to the outside.
        size_max = layer_config.size_max
        size_min = layer_config.size_min

        on_axis_size = _get_body_size_for_rotation(rotation)

        if on_axis_size >= 4 * size_max:

            # We still have space for horizontal text, so do thar
            if body_size.x >= 4 * size_max:
                rotation = 0

            size = size_max
        elif on_axis_size < 4 * size_min:
            size = size_min
            if on_axis_size < 3 * size_min:
                if position_y == FieldPosition.INSIDE.value:
                    rotation = 0
                    position_y = FieldPosition.OUTSIDE_TOP.value
        else:
            fullsize = _roundToBase(_get_body_size_for_rotation(rotation) / 4, 0.01)
            size = fullsize


        cross_axis_space = _get_body_size_for_rotation((rotation + 1) % 2) - 0.2

        if size > cross_axis_space:
            fullsize = max(cross_axis_space, size_min)
            size = fullsize

        fontwidth = _roundToBase(layer_config.thickness_ratio * size, 0.01)

    if position_y == FieldPosition.INSIDE.value:
        if text_y_inside_position == 'top':
            position_y = "inside_top"
        elif text_y_inside_position == 'bottom':
            position_y = "inside_bottom"
        elif text_y_inside_position == 'left':
            position_y = "inside_left"
        elif text_y_inside_position == 'right':
            position_y = "inside_right"
        elif text_y_inside_position == "above":
            position_y = "outside_top"
        elif text_y_inside_position == "below":
            position_y = "outside_bottom"
        elif isinstance(text_y_inside_position, int) or isinstance(text_y_inside_position, float):
            at[1] = text_y_inside_position

    text_edge_offset = size / 2 + 0.2

    if position_y == "outside_top":
        at = [body_center[0], courtyard.top - text_edge_offset]
    elif position_y == "inside_top":
        at = [body_center[0], body_edges.top + text_edge_offset]
    elif position_y == "inside_left":
        at = [body_edges.left + text_edge_offset, body_center[1]]
        rotation = 1
    elif position_y == "inside_right":
        at = [body_edges.right - text_edge_offset, body_center[1]]
        rotation = 1
    elif position_y == "outside_bottom":
        at = [body_center[0], courtyard.bottom + text_edge_offset]
    elif position_y == "inside_bottom":
        at = [body_center[0], body_edges.bottom - text_edge_offset]

    at = [_roundToBase(at[0],0.01), _roundToBase(at[1],0.01)]

    return {
        "at": at,
        "size": Vector2D(size, layer_config.width_ratio * size),
        "layer": field_definition.layer,
        "thickness": fontwidth,
        "rotation": rotation * 90,
    }


def addTextFields(kicad_mod,
                  configuration: dict | GlobalConfig,
                  body_edges: dict | BoundingBox | GeomRectangle,
                  courtyard: dict | BoundingBox | GeomRectangle,
                  fp_name: str,
                  text_y_inside_position: float | str = 'center',
                  allow_rotation = False):
    """
    Automatically add reference and value fields to a footprint, placing them in the body according to the
    GlobalConfig settings.

    :param kicad_mod: The footprint to add the fields to
    :param configuration: The GlobalConfig object or dictionary to use for the field placement
    :param body_edges: The bounding box of the body of the footprint
    :param courtyard: The bounding box of the courtyard of the footprint
    :param fp_name: The name of the footprint
    :param text_y_inside_position: The position of the text inside the body. This can be
        'center', 'top', 'bottom', 'left', 'right', 'above', 'below' or a specific Y position.
    :param allow_rotation: Allow the text to be rotated if it fits better
    """

    if isinstance(configuration, dict):
        # Legacy "direct-configuration" code passing in dictionaries
        # This dictionary IS a GlobalConfig definition, so construct it here. This is a
        # stopgap until generator code is updated to use GlobalConfig directly.
        # Don't write new code that passes in dictionaries.
        global_config = GlobalConfig(configuration)
    else:
        # it's already a GlobalConfig object
        global_config = configuration

    # Make sure we have BoundingBox objects (loads of callers pass dicts here)
    # New code should pass BoundingBox objects directly.
    def _make_bbox(obj):
        if isinstance(obj, BoundingBox):
            return obj

        if isinstance(obj, GeomRectangle):
            return obj.bbox()

        if not ("left" in obj and "right" in obj):
            # Some callers don't provide a full BoundingBox, but only the top and bottom
            obj["left"] = 0
            obj["right"] = 0

        return BoundingBox(
            Vector2D(obj["left"], obj["top"]), Vector2D(obj["right"], obj["bottom"])
        )

    body_edges = _make_bbox(body_edges)
    courtyard = _make_bbox(courtyard)

    kicad_mod.append(Property(name='Reference', text='REF**',
        **_getTextFieldDetails(global_config, global_config.reference_fields[0], body_edges, courtyard, text_y_inside_position, allow_rotation)))

    for additional_ref in global_config.reference_fields[1:]:
        kicad_mod.append(Text(text='${REFERENCE}',
        **_getTextFieldDetails(global_config, additional_ref, body_edges, courtyard, text_y_inside_position, allow_rotation)))

    kicad_mod.append(Property(name='Value', text=fp_name,
        **_getTextFieldDetails(global_config, global_config.value_fields[0], body_edges, courtyard, text_y_inside_position, allow_rotation)))

    for additional_value in global_config.value_fields[1:]:
        kicad_mod.append(Text(text='%V',
            **_getTextFieldDetails(global_config, additional_value, body_edges, courtyard, text_y_inside_position, allow_rotation)))
