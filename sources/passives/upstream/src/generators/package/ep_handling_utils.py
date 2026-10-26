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

from KicadModTree.util import corner_handling
from kilibs.config.global_config import GlobalConfig
from typing import Any


def getEpRoundRadiusParams(
    device_params: dict[str, Any], global_config: GlobalConfig, pad_radius: float
) -> dict[str, Any]:
    """
    Construct some parameters for the ExposedPad construction, based on device configs and
    global config.
    """

    pad_shape_details = {}

    pad_shape_details['paste_radius_handler'] = global_config.paste_roundrect_radius_handler

    round_radius_params = {}

    if 'EP_round_radius' in device_params:
        if type(device_params['EP_round_radius']) in [float, int]:
            round_radius_params['round_radius_exact'] = device_params['EP_round_radius']
        elif device_params['EP_round_radius'] == "pad":
            round_radius_params['round_radius_exact'] = pad_radius
        else:
            raise TypeError(
                    "round radius must be a number or 'pad', is {}"
                    .format(type(device_params['EP_round_radius']))
                    )
    elif 'EP_round_radius_ratio' in device_params:
        round_radius_params['radius_ratio'] = device_params['EP_round_radius_ratio']
    else:
        round_radius_params['radius_ratio'] = global_config.ep_roundrect_radius_handler.radius_ratio

    if 'radius_ratio' in round_radius_params and round_radius_params['radius_ratio'] > 0:
        if 'EP_maximum_radius' in device_params:
            round_radius_params['maximum_radius'] = device_params['EP_maximum_radius']
        else:
            round_radius_params['maximum_radius'] = global_config.ep_roundrect_radius_handler.maximum_radius

    pad_shape_details['round_radius_handler'] = corner_handling.RoundRadiusHandler(**round_radius_params)

    return pad_shape_details
