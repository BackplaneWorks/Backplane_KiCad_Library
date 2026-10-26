import math

from kicad_sym import mm_to_mil
from rules_symbol.rule import KLCRule


class Rule(KLCRule):
    """Origin is centered on the middle of the symbol"""

    def check(self) -> bool:
        """
        Calculate the 'bounds' of the symbol based on rectangle (if only a
        single filled rectangle is present) or on pin positions.
        """

        # no need to check this for an
        if self.component.extends is not None:
            return False

        # Check units separately
        unit_count = self.component.unit_count

        for unit in range(1, unit_count + 1):
            # If there is only a single filled rectangle, we assume that it is the
            # main symbol outline.
            center_pl = self.component.get_center_rectangle([0, unit])
            if center_pl is not None:
                x, y = center_pl.get_center_of_boundingbox()

                bbox = center_pl.get_boundingbox()
                size = [bbox[0] - bbox[2], bbox[1] - bbox[3]]
            else:
                pins = [pin for pin in self.component.pins if (pin.unit in [unit, 0])]

                # No pins? Ignore check.
                # This can be improved to include graphical items too...
                if not pins:
                    continue
                x_pos = [pin.posx for pin in pins]
                y_pos = [pin.posy for pin in pins]
                x_min = min(x_pos)
                x_max = max(x_pos)
                y_min = min(y_pos)
                y_max = max(y_pos)

                # Center point average
                x = (x_min + x_max) / 2
                y = (y_min + y_max) / 2

                size = [x_max - x_min, y_max - y_min]

            # convert to mil
            x = mm_to_mil(x)
            y = mm_to_mil(y)

            size = [mm_to_mil(size[0]), mm_to_mil(size[1])]

            # Right on the middle!
            if x == 0 and y == 0:
                continue
            elif math.fabs(x) == 50 or math.fabs(y) == 50:
                # Sometimes the symbol is slightly off-center, but it's ok

                def is_bad_offset(axis_offset, axis_size):
                    """
                    An offset is acceptable is it's exactly 50 AND the symbol is "small"
                    """
                    # Symbols smaller than this can be 50 mil off-centre
                    # e.g. for symbols with a even number of 100 mil-spaced pin
                    # The right exact value is subjective.
                    small_symbol_size = 800

                    # Symbol is big enough to need proper centering
                    if axis_size > small_symbol_size:
                        return math.fabs(axis_offset) != 0

                    # Symbol is small enough to allow 50 mil off-center
                    return math.fabs(axis_offset) not in [0, 50]

                if is_bad_offset(x, size[0]) or is_bad_offset(y, size[1]):
                    self.warning(f"Symbol unit {unit} slightly off-center")
                    self.warningExtra(f"  Center calculated @ ({x}, {y})")
            else:
                self.error(f"Symbol unit {unit} not centered on origin")
                self.errorExtra(f"Center calculated @ ({x}, {y})")

        return False

    def fix(self) -> None:
        return
