# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team


class Padstack:
    """
    The padstack contains the information about a pad or via on each layer.

    This corresponds to a PADSTACK in KiCad's internal data structures. Every pad has
    one padstack.

    Many properties of the padstack are currently defined in the Pad class itself,
    but could be moved here in the future to also support via padstacks properly and
    to have a cleaner separation between pad properties and padstack properties.
    """

    class MaskLayerProps:
        """
        Properties of a mask layers in a padstack (solder mask and paste)

        Padstacks have one of these per outer layer, i.e. front and back.

        Any of the properties can be `None` if they are inherited from the parent pad/via
        defaults (or from global defaults/rules).
        """

        has_solder_mask: bool | None
        """If `True` the solder mask is defined for this layer."""

        # has_covering (vias only)
        # has_plugging (vias only)
        # mask/paste margin/ratio should also go here in the future

        def __init__(self) -> None:
            """Create mask layer properties."""
            # Instance attributes:
            self.has_solder_mask = None

    def __init__(self) -> None:
        """Create a padstack."""
        # Instance attributes:

        self.front_mask_props: Padstack.MaskLayerProps = Padstack.MaskLayerProps()
        """Properties of the front outer mask layers."""
        self.back_mask_props: Padstack.MaskLayerProps = Padstack.MaskLayerProps()
        """Properties of the back outer mask layers."""
