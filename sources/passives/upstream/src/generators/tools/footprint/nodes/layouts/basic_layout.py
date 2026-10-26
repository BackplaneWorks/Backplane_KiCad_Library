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

from collections.abc import Sequence

from kilibs.config import global_config as GC
from kilibs.geom import GeomShapesClosed, Vector2D

from .footprint_layout import CourtyardStyle, FabStyle, FootprintLayout, Pads, SilkStyle


class BasicLayout(FootprintLayout[GeomShapesClosed, Pads]):
    """
    This the most basic and at the same time generic layout - some pads, and a body
    of any shape (here drawn as rectangle, but can be anything):

    .. aafig::

                +-----------------------+
        +-------|---+               +---|-------+
        |       |   |               |   |       |
        +-------|---+               +---|-------+
                |                       |
        +-------|---+               +---|-------+
        |       |   |               |   |       |
        +-------|---+               +---|-------+
                +-----------------------+

    """

    def __init__(
        self,
        global_config: GC.GlobalConfig,
        body_shape: GeomShapesClosed,
        pads: Sequence[Pads],
        footprint_name: str,
        translation_offset: Vector2D = Vector2D.zero(),
        fab_style: FabStyle = FabStyle.BODY_SHAPE,
        silk_style: SilkStyle = SilkStyle.TIGHT,
        courtyard_style: CourtyardStyle = CourtyardStyle.TIGHT,
    ) -> None:
        """Create an instance of the `BasicLayout`.

        Args:
            global_config: The global config.
            body_shape: The shape of the body.
            pads: The pads of the footprint.
            footprint_name: The name of the footprint. Used for automatic label
                placement.
            translation_offset: The translation offset by which all nodes inside the
                layout are translated. Defaults to zero = no translation.
            fab_style: The style with which the fab outline is drawn.
            silk_style: The style with which the silkscreen is drawn.
            courtyard_style: The style with which the courtyard is drawn.
        """
        super().__init__(
            global_config=global_config,
            body_shape=body_shape,
            pads=pads,
            translation_offset=translation_offset,
        )
        self._add_automatic_fab_outline(fab_style)
        self._add_automatic_silk_outline(silk_style)
        self._add_automatic_courtyard(courtyard_style)
        self._add_automatic_labels(footprint_name)
