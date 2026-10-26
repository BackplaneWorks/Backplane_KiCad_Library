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

from typing import Dict, Optional, Tuple
from dataclasses import dataclass

# Common key for generic additional tags
PAD_OVERRIDES_KEY = 'pad_overrides'

# None is used to indicate that the (sub-)value should be ignored.
XYCoordinates = Tuple[Optional[float], Optional[float]]
SizeXY = Tuple[Optional[float], Optional[float]]

@dataclass
class SinglePadOverride:
    """
    Represents overrideable options for a single pad.
    """
    # Move this pad by given X/Y coordinates
    move: Optional[XYCoordinates]

    # Position the pad at given X/Y coordinates.
    # This overrides any move command.
    at: Optional[XYCoordinates]

    # Increase (or decrease) the pad size
    size_increase: Optional[SizeXY]

    # Set the pad size (absolute).
    # This overrides any size_increase command.
    size: Optional[SizeXY]

    # Override the lead width
    lead_width: Optional[str]  # TODO Which type?

    # Override the lead length
    lead_len: Optional[str]  # TODO Which type?

    # Override the pad number
    override_number: Optional[str]

@dataclass
class PadOverrides:
    """
    Class that reads "pad_overrides" out of standard
    YAML spec files.
    """
    _overrides: Dict[int | str, SinglePadOverride]

    def __init__(self, overrides: Dict[int, SinglePadOverride] | None = None) -> None:
        self._overrides = {}

        for number, override in (overrides or {}).items():
            self._overrides[number] = SinglePadOverride(
                move=override.get('move'),
                at=override.get('at'),
                size_increase=override.get('size_increase'),
                size=override.get('size'),
                lead_width=override.get('lead_width'),
                lead_len=override.get('lead_len'),
                override_number=override.get('override_number'),
            )

    @property
    def overrides(self) -> Dict[int | str, SinglePadOverride]:
        return self._overrides
    
    def __bool__(self) -> bool:
        return True if self._overrides else False
