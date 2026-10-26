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

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
import enum

from KicadModTree import Pad
from KicadModTree.util.corner_handling import RoundRadiusHandler
from kilibs.config import global_config as GC
from kilibs.geom import Vector2D


class DevicePadType(enum.Enum):
    """The pad type on the PCB side."""

    THT_PIN = enum.auto()
    """Protruding pin that is soldered into a plated hole"""
    MECH_PIN = enum.auto()
    """Protruding pin that is not soldered, e.g. a mechanical peg"""
    SMD_LAND = enum.auto()
    """Flat solderable land, e.g. on a surface-mount device that is
    soldered using paste applied to a counterpart pad on the PCB"""
    SMD_BALL = enum.auto()
    """Solder ball attached to the device, e.g. on a BGA, usually soldered
    to a counterpart land on the PCB"""


@dataclass(frozen=True)
class PadInfo:
    """The fully-resolved data describing a single pad.

    A `PadInfo` is the generic description of a "pad". This may refer to a
    "device pad" (the solderable feature on the device) or a "footprint pad"
    (the solderable feature on the PCB).  Exactly how the pad is defined and
    what it mean is up to the pad factory that produces it.

    Not all attributes are used by all clients. For example, 3D generators are
    unlikely to use the paste options.

    Attributes:
        name: The pad name/number (e.g. "A1").
        position: The pad centre position in mm.
        size: The pad size in mm.
        shape: The pad shape (one of the `Pad.SHAPE_*` strings).
        pad_type: The pad type (one of the `Pad.TYPE_*` strings).
        fab_property: The pad fabrication property, or `None` for none.
        drill: The drill size in mm for through-hole pads, or `None` for
            surface-mount pads.
        mask_size: The solder-mask aperture size in mm, or `None` to inherit
            the footprint-level mask margin.
        paste_shape: The solder-paste opening shape, or `None` to use `shape`
            (in which case no separate paste pad is created).
        paste_margin: The solder-paste margin in mm applied when a separate
            paste pad is created.
    """

    name: str
    position: Vector2D
    size: Vector2D
    shape: str
    fp_pad_type: str
    """The pad type on the PCB side"""
    device_pad_type: DevicePadType
    """The pad type on the device side"""
    fab_property: Pad.FabProperty | None = None
    drill: Vector2D | float | None = None
    """The drill size in mm for through-hole pads, or `None` for SMD pads."""
    mask_size: Vector2D | None = None
    """The solder-mask aperture size in mm, or `None` to inherit the
    footprint-level mask margin."""
    paste_shape: str | None = None
    paste_margin: float = 0.0


class PadFactory(ABC):
    """Abstract base class for pad factories.

    A pad factory is a pluggable strategy that produces the pads of a part. A
    concrete factory implements one pad definition style (e.g. a BGA grid layout
    or an explicit CSV table) and hides that style behind `pads`, so both
    footprint and 3D model generators can consume the pads without being aware
    of the gory details of how they were defined.
    """

    @abstractmethod
    def pads(self) -> Iterator[PadInfo]:
        """Yield the resolved `PadInfo` of every pad of the part."""
        raise NotImplementedError


def pad_info_to_pads(pad_info: PadInfo) -> list[Pad]:
    """Construct the `Pad` nodes for a resolved `PadInfo`.

    Returns the main pad and, additional ancuillary pads. For example:

    * when the pad's paste opening differs from its pad shape, additional
      paste-only pads.

    This is the only place in the generic pad-factory machinery that creates
    KiCad pads.

    You can theoretically implement your own converter if you really need to and
    this function can't provide the right behavior, but consider adding logic
    here.

    Args:
        pad_info: One resolved pad data object.

    Returns:
        The constructed Pad nodes.
    """
    pad_shape = pad_info.shape
    paste_shape = pad_info.paste_shape
    pad_type = pad_info.fp_pad_type

    if pad_type == Pad.TYPE_SMT:
        if paste_shape and paste_shape != pad_shape:
            layers = ["F.Cu", "F.Mask"]
        else:
            layers = Pad.LAYERS_SMT
    elif pad_type == Pad.TYPE_THT:
        layers = Pad.LAYERS_THT
    elif pad_type == Pad.TYPE_NPTH:
        layers = Pad.LAYERS_NPTH
    else:  # Pad.TYPE_CONNECT
        layers = Pad.LAYERS_CONNECT_FRONT

    # Round-rect pads need a radius handler, all other shapes ignore it.
    round_radius_handler = (
        GC.GLOBAL_CONFIG.roundrect_radius_handler
        if pad_shape == Pad.SHAPE_ROUNDRECT
        else None
    )

    # The per-pad solder-mask margin, derived from the explicit mask aperture
    # when one is given. Zero means the footprint-level mask margin applies.
    solder_mask_margin = (
        (pad_info.mask_size.x - pad_info.size.x) / 2.0
        if pad_info.mask_size is not None
        else 0.0
    )

    pads = [
        Pad(
            number=pad_info.name,
            type=pad_type,
            fab_property=pad_info.fab_property,
            shape=pad_shape,
            at=pad_info.position,
            size=pad_info.size,
            layers=layers,
            drill=pad_info.drill,
            round_radius_handler=round_radius_handler,
            solder_mask_margin=solder_mask_margin,
        )
    ]

    if pad_type == Pad.TYPE_SMT and paste_shape and paste_shape != pad_shape:
        # Footgun warning: When pcbnew renders a paste-only pad like this, it actually
        # ignores all paste margin settings both of the pad and of the footprint, and
        # creates a stencil opening of exactly the size of the pad. Thus, we have to
        # pre-compute paste margin here. Note that KiCad implements paste margin with an
        # actual geometric offset, i.e. yielding a rounded rect for square pads. Thus,
        # we have to implement similar offsetting logic here to stay consistent.

        paste_margin = pad_info.paste_margin
        size = [pad_info.size.x, pad_info.size.y]
        corner_ratio = GC.GLOBAL_CONFIG.roundrect_radius_handler.radius_ratio

        if paste_shape == "circle":
            size[0] += 2 * paste_margin
            size[1] += 2 * paste_margin

        elif paste_shape == "rect":
            if paste_margin <= 0:
                size[0] += 2 * paste_margin
                size[1] += 2 * paste_margin

            else:
                corner_ratio = paste_margin / min(size)
                size[0] += 2 * paste_margin
                size[1] += 2 * paste_margin
                paste_shape = "roundrect"

        elif paste_shape == "roundrect":
            corner_radius = min(size) * corner_ratio
            size[0] += 2 * paste_margin
            size[1] += 2 * paste_margin
            corner_radius += paste_margin

            if corner_radius < 0:
                paste_shape = "rect"
            else:
                corner_ratio = corner_radius / min(size)

        paste_radius_handler = RoundRadiusHandler(
            radius_ratio=corner_ratio,
        )

        pads.append(
            Pad(
                number="",
                type=Pad.TYPE_SMT,
                shape=paste_shape,
                at=pad_info.position,
                size=size,  # type: ignore
                layers=["F.Paste"],
                round_radius_handler=paste_radius_handler,
            )
        )

    return pads
