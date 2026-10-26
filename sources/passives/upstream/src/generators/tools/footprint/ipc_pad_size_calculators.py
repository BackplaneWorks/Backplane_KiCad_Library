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

from __future__ import division
import math

from kilibs.config import ipc_rules
from kilibs.util.toleranced_size import TolerancedSize


def roundToBase(value: float, base: float) -> float:
    return round(value / base) * base


def ipc_body_edge_inside(
    ipc_offsets: ipc_rules.Offsets,
    ipc_round_base: ipc_rules.Roundoff,
    manf_tol: ipc_rules.ManufacturingTolerance,
    body_size: TolerancedSize,
    lead_width: TolerancedSize,
    lead_len: TolerancedSize | None = None,
    lead_inside: TolerancedSize | None = None,
    heel_reduction: float = 0,
) -> tuple[float, float, float]:
    pull_back = TolerancedSize(nominal=0)

    return ipc_body_edge_inside_pull_back(
        ipc_offsets,
        ipc_round_base,
        manf_tol,
        body_size,
        lead_width,
        lead_len=lead_len,
        lead_inside=lead_inside,
        pull_back=pull_back,
        heel_reduction=heel_reduction,
    )


def ipc_body_edge_inside_pull_back(
    ipc_offsets: ipc_rules.Offsets,
    ipc_round_base: ipc_rules.Roundoff,
    manf_tol: ipc_rules.ManufacturingTolerance,
    body_size: TolerancedSize,
    lead_width: TolerancedSize,
    lead_len: TolerancedSize | None = None,
    lead_inside: TolerancedSize | None = None,
    body_to_inside_lead_edge: TolerancedSize | None = None,
    pull_back: TolerancedSize | None = None,
    lead_outside: TolerancedSize | None = None,
    heel_reduction: float = 0,
) -> tuple[float, float, float]:
    # Zmax = Lmin + 2JT + √(CL^2 + F^2 + P^2)
    # Gmin = Smax − 2JH − √(CS^2 + F^2 + P^2)
    # Xmax = Wmin + 2JS + √(CW^2 + F^2 + P^2)

    # Some manufacturers do not list the terminal spacing (S) in their datasheet but list the terminal length (T)
    # Then one can calculate
    # Stol(RMS) = √(Ltol^2 + 2*^2)
    # Smin = Lmin - 2*Tmax
    # Smax(RMS) = Smin + Stol(RMS)

    f = manf_tol.manufacturing_tolerance
    p = manf_tol.placement_tolerance

    if lead_outside is None:
        if pull_back is None:
            raise KeyError("Either lead outside or pull back distance must be given")
        lead_outside = body_size - pull_back * 2

    if lead_inside is not None:
        s = lead_inside
    elif lead_len is not None:
        s = lead_outside - lead_len * 2
    elif body_to_inside_lead_edge is not None:
        s = body_size - body_to_inside_lead_edge * 2
    else:
        raise KeyError("either lead inside distance, lead to body edge or lead length must be given")

    Gmin = s.maximum_RMS - 2 * ipc_offsets.heel + 2 * heel_reduction - math.sqrt(s.ipc_tol_RMS**2 + f**2 + p**2)

    Zmax = lead_outside.minimum_RMS + 2 * ipc_offsets.toe + math.sqrt(lead_outside.ipc_tol_RMS**2 + f**2 + p**2)
    Xmax = lead_width.minimum_RMS + 2 * ipc_offsets.side + math.sqrt(lead_width.ipc_tol_RMS**2 + f**2 + p**2)

    Zmax = roundToBase(Zmax, ipc_round_base.toe)
    Gmin = roundToBase(Gmin, ipc_round_base.heel)
    Xmax = roundToBase(Xmax, ipc_round_base.side)

    return Gmin, Zmax, Xmax


def ipc_gull_wing(
    ipc_offsets: ipc_rules.Offsets,
    ipc_round_base: ipc_rules.Roundoff,
    manf_tol: ipc_rules.ManufacturingTolerance,
    lead_width: TolerancedSize,
    lead_outside: TolerancedSize,
    lead_len: TolerancedSize | None = None,
    lead_inside: TolerancedSize | None = None,
    heel_reduction: float = 0,
) -> tuple[float, float, float]:

    # Zmax = Lmin + 2JT + √(CL^2 + F^2 + P^2)
    # Gmin = Smax − 2JH − √(CS^2 + F^2 + P^2)
    # Xmax = Wmin + 2JS + √(CW^2 + F^2 + P^2)

    # Some manufacturers do not list the terminal spacing (S) in their datasheet but list the terminal length (T)
    # Then one can calculate
    # Stol(RMS) = √(Ltol^2 + 2*^2)
    # Smin = Lmin - 2*Tmax
    # Smax(RMS) = Smin + Stol(RMS)

    f = manf_tol.manufacturing_tolerance
    p = manf_tol.placement_tolerance

    if lead_inside is not None:
        s = lead_inside
    elif lead_len is not None:
        s = lead_outside - lead_len * 2
    else:
        raise KeyError("either lead inside distance or lead length must be given")

    Gmin = s.maximum_RMS - 2 * ipc_offsets.heel + 2 * heel_reduction - math.sqrt(s.ipc_tol_RMS**2 + f**2 + p**2)

    Zmax = lead_outside.minimum_RMS + 2 * ipc_offsets.toe + math.sqrt(lead_outside.ipc_tol_RMS**2 + f**2 + p**2)
    Xmax = lead_width.minimum_RMS + 2 * ipc_offsets.side + math.sqrt(lead_width.ipc_tol_RMS**2 + f**2 + p**2)

    Zmax = roundToBase(Zmax, ipc_round_base.toe)
    Gmin = roundToBase(Gmin, ipc_round_base.heel)
    Xmax = roundToBase(Xmax, ipc_round_base.side)

    return Gmin, Zmax, Xmax


def ipc_pad_center_plus_size(
    ipc_offsets: ipc_rules.Offsets,
    ipc_round_base: ipc_rules.Roundoff,
    manf_tol: ipc_rules.ManufacturingTolerance,
    center_position: TolerancedSize,
    lead_length: TolerancedSize,
    lead_width: TolerancedSize,
) -> tuple[float, float, float]:

    f = manf_tol.manufacturing_tolerance
    p = manf_tol.placement_tolerance

    s = center_position * 2 - lead_length
    lead_outside = center_position * 2 + lead_length

    Gmin = s.maximum_RMS - 2 * ipc_offsets.heel - math.sqrt(s.ipc_tol_RMS**2 + f**2 + p**2)
    Zmax = lead_outside.minimum_RMS + 2 * ipc_offsets.toe + math.sqrt(lead_outside.ipc_tol_RMS**2 + f**2 + p**2)

    Xmax = lead_width.minimum_RMS + 2 * ipc_offsets.side + math.sqrt(lead_width.ipc_tol_RMS**2 + f**2 + p**2)

    Zmax = roundToBase(Zmax, ipc_round_base.toe)
    Gmin = roundToBase(Gmin, ipc_round_base.heel)
    Xmax = roundToBase(Xmax, ipc_round_base.side)

    return Gmin, Zmax, Xmax


def ipc_ball_get_pad_size(
    ball_rules: ipc_rules.IpcBallRules,
    density: ipc_rules.IpcDensity,
    ball_type: ipc_rules.BallType,
    ball_diameter: float,
) -> float:
    """Calculate the pad diameter for a BGA ball.

    Based on IPC-7352 Table 3-11.

    Args:
        ball_rules: The IPC ball-rules provider.
        density: The IPC density.
        ball_type: The type of the ball in question.
        ball_diameter: The diameter of the ball in mm.

    Returns:
        The pad diameter in mm.
    """
    pad_data = ball_rules.get_pad_data(density)
    if ball_type is ipc_rules.BallType.COLLAPSIBLE:
        ratio = pad_data.collapsible_ratio
    else:
        ratio = pad_data.non_collapsible_ratio

    return roundToBase((1 + ratio) * ball_diameter, pad_data.roundoff)
