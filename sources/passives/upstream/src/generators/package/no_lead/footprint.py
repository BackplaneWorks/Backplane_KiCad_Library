import logging
import os

from generators.tools.footprint.declarative_def_tools import (
    ast_evaluator,
    rule_area_properties,
)
from generators.tools.footprint.ipc_pad_size_calculators import (
    ipc_body_edge_inside_pull_back,
    ipc_pad_center_plus_size,
)
from generators.tools.footprint.nodes.layouts.dual_and_quad_pad_array_layout import (
    DualAndQuadPadArrayLayout,
)
from generators.tools.footprint.quad_dual_pad_border import (
    create_dual_or_quad_pad_border,  # type: ignore
)
from generators.tools.footprint.save_footprint import write_footprint
from KicadModTree import (
    ExposedPad,
    Footprint,
    FootprintType,
)
from KicadModTree.nodes.specialized.PadArray import get_pad_radius_from_arrays
from kilibs.config import ipc_rules
from kilibs.config.global_config import GLOBAL_CONFIG
from kilibs.geom import Vector2D

from ..config import PACKAGE_CONFIG
from ..ep_handling_utils import getEpRoundRadiusParams
from .spec import NoLeadSpec

category = "NoLead"

DEFAULT_PASTE_COVERAGE = 0.65
DEFAULT_VIA_PASTE_CLEARANCE = 0.15
DEFAULT_MIN_ANNULAR_RING = 0.15

SILK_MIN_LEN = 0.1


def create_footprints(spec: NoLeadSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The no lead specification.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    if spec.has_fp_data:
        if spec.has_ep and "thermal_vias" in spec.spec:
            _create_footprint_variant(spec, True, generator_name)
            num_fps_generated += 1
        _create_footprint_variant(spec, False, generator_name)
        num_fps_generated += 1
    return num_fps_generated


def calc_pad_details(
    config: NoLeadSpec,
    EP_size: Vector2D,
    ipc_offsets: ipc_rules.Offsets,
    ipc_round_base: ipc_rules.Roundoff,
) -> dict[str, dict[str, list[float]]]:
    # Zmax = Lmin + 2JT + √(CL^2 + F^2 + P^2)
    # Gmin = Smax − 2JH − √(CS^2 + F^2 + P^2)
    # Xmax = Wmin + 2JS + √(CW^2 + F^2 + P^2)

    # Some manufacturers do not list the terminal spacing (S) in their datasheet but list the terminal length (T)
    # Then one can calculate
    # Stol(RMS) = √(Ltol^2 + 2*^2)
    # Smin = Lmin - 2*Tmax
    # Smax(RMS) = Smin + Stol(RMS)

    manf_tol = ipc_rules.ManufacturingTolerance(
        manufacturing_tolerance=PACKAGE_CONFIG.get("manufacturing_tolerance", 0.1),
        placement_tolerance=PACKAGE_CONFIG.get("placement_tolerance", 0.05),
    )

    if "heel_reduction" in config.spec:
        logging.warning(
            "The use of manual heel reduction is deprecated. It is automatically "
            "calculated from the minimum EP to pad clearance (ipc config file)."
        )

    if config.lead_center_pos_x.nominal or config.lead_center_pos_y.nominal:
        Gmin_x, Zmax_x, Xmax_x = ipc_pad_center_plus_size(
            ipc_offsets,
            ipc_round_base,
            manf_tol,
            center_position=config.lead_center_pos_x,
            lead_length=config.lead_len_h,
            lead_width=config.lead_width_h,
        )

        Gmin_y, Zmax_y, Xmax_y = ipc_pad_center_plus_size(
            ipc_offsets,
            ipc_round_base,
            manf_tol,
            center_position=config.lead_center_pos_y,
            lead_length=config.lead_len_v,
            lead_width=config.lead_width_v,
        )
    else:
        Gmin_x, Zmax_x, Xmax_x = ipc_body_edge_inside_pull_back(
            ipc_offsets,
            ipc_round_base,
            manf_tol,
            body_size=config.body_size_x,
            lead_width=config.lead_width_h,
            lead_len=config.lead_len_h,
            heel_reduction=config.spec.get("heel_reduction", 0),
            pull_back=config.lead_to_edge,
        )

        Gmin_y, Zmax_y, Xmax_y = ipc_body_edge_inside_pull_back(
            ipc_offsets,
            ipc_round_base,
            manf_tol,
            body_size=config.body_size_y,
            lead_width=config.lead_width_v,
            lead_len=config.lead_len_v,
            heel_reduction=config.spec.get("heel_reduction", 0),
            pull_back=config.lead_to_edge,
        )

    min_ep_to_pad_clearance = ipc_rules.DEFAULT_IPC_RULES.min_ep_to_pad_clearance
    assert min_ep_to_pad_clearance is not None
    heel_reduction_max = 0

    if EP_size["x"] > 0 and Gmin_x - 2 * min_ep_to_pad_clearance < EP_size["x"]:
        heel_reduction_max = (EP_size["x"] + 2 * min_ep_to_pad_clearance - Gmin_x) / 2
        # print('{}, {}, {}'.format(Gmin_x, EP_size['x'], min_ep_to_pad_clearance))
        Gmin_x = EP_size["x"] + 2 * min_ep_to_pad_clearance
    if EP_size["y"] > 0 and Gmin_y - 2 * min_ep_to_pad_clearance < EP_size["y"]:
        heel_reduction = (EP_size["y"] + 2 * min_ep_to_pad_clearance - Gmin_y) / 2
        if heel_reduction > heel_reduction_max:
            heel_reduction_max = heel_reduction
        Gmin_y = EP_size["y"] + 2 * min_ep_to_pad_clearance

    heel_reduction_max += config.spec.get("heel_reduction", 0)  # include legacy stuff
    if heel_reduction_max > 0:
        logging.info(
            f"Heel reduced by {heel_reduction_max:.4f} to reach minimum EP to pad clearances"
        )

    pad: dict[str, dict[str, list[float]]] = {}
    pad["left"] = {
        "center": [-(Zmax_x + Gmin_x) / 4, 0.0],
        "size": [(Zmax_x - Gmin_x) / 2, Xmax_x],
    }
    pad["right"] = {
        "center": [(Zmax_x + Gmin_x) / 4, 0.0],
        "size": [(Zmax_x - Gmin_x) / 2, Xmax_x],
    }
    pad["top"] = {
        "center": [0.0, -(Zmax_y + Gmin_y) / 4],
        "size": [Xmax_y, (Zmax_y - Gmin_y) / 2],
    }
    pad["bottom"] = {
        "center": [0.0, (Zmax_y + Gmin_y) / 4],
        "size": [Xmax_y, (Zmax_y - Gmin_y) / 2],
    }

    return pad


def _create_footprint_variant(
    device_config: NoLeadSpec, with_thermal_vias: bool, generator_name: str
) -> None:
    # Pull out the old-style raw data
    spec = device_config.spec
    tsh = device_config.toleranced_size_handler

    if device_config.lead_to_edge.nominal != 0.0:
        default_ipc_config = "qfn_pull_back"
    else:
        default_ipc_config = "qfn"
    if spec.get("ipc_class", default_ipc_config) == "qfn_pull_back":
        ipc_reference = "ipc_spec_flat_no_lead_pull_back"
    else:
        ipc_reference = "ipc_spec_flat_no_lead"

    ipc_offsets = ipc_rules.DEFAULT_IPC_RULES.get_class(ipc_reference).get_offsets(
        device_config.ipc_density
    )
    ipc_round_base = ipc_rules.DEFAULT_IPC_RULES.get_class(ipc_reference).roundoff

    if device_config.has_ep:
        if "EP_size_x_overwrite" in spec:
            EP_size = Vector2D(spec["EP_size_x_overwrite"], spec["EP_size_y_overwrite"])
        else:
            EP_size = Vector2D(
                device_config.ep_size_x.nominal,
                device_config.ep_size_y.nominal,
            )
        EP_center = Vector2D(
            device_config.ep_offset_x.nominal,
            device_config.ep_offset_y.nominal,
        )
    else:
        EP_size = Vector2D.zero()

    KEYS = "pad_width", "pad_length", "pad_center_to_center_x", "pad_center_to_center_y"
    if num_matching_keys := sum(key in KEYS for key in spec.keys()):
        if num_matching_keys < 3:
            raise KeyError(
                "When using a 'pad_*' parameter to explicitly define a pad dimension, "
                "both 'pad_width' and 'pad_length' and at least one of "
                "'pad_center_to_center_x' or 'pad_center_to_center_y' must be provided."
            )
        pad_width = tsh.get("pad_width", 0.0).nominal
        pad_length = tsh.get("pad_length", 0.0).nominal
        pad_pos_x = tsh.get("pad_center_to_center_x", 0.0).nominal / 2
        pad_pos_y = tsh.get("pad_center_to_center_y", 0.0).nominal / 2
        pad_details = {}
        pad_details["left"] = {
            "center": [-pad_pos_x, 0],
            "size": [pad_length, pad_width],
        }
        pad_details["right"] = {
            "center": [pad_pos_x, 0],
            "size": [pad_length, pad_width],
        }
        pad_details["top"] = {
            "center": [0, -pad_pos_y],
            "size": [pad_width, pad_length],
        }
        pad_details["bottom"] = {
            "center": [0, pad_pos_y],
            "size": [pad_width, pad_length],
        }
    else:
        pad_details = calc_pad_details(
            device_config, EP_size, ipc_offsets, ipc_round_base
        )

    fp_ast_evaluator = ast_evaluator.ASTevaluator()

    if with_thermal_vias:
        fp_name = device_config.fp_name_with_vias
    else:
        fp_name = device_config.fp_name_without_vias

    kicad_mod = Footprint(fp_name, FootprintType.SMD)
    if "mask_margin" in spec:
        kicad_mod.setMaskMargin(spec["mask_margin"])
    if "paste_margin" in spec:
        kicad_mod.setPasteMargin(spec["paste_margin"])
    if "paste_ratio" in spec:
        kicad_mod.setPasteMarginRatio(spec["paste_ratio"])

    # init kicad footprint
    kicad_mod.setDescription(
        "{manufacturer} {mpn} {package}, {pincount} Pin ({datasheet})".format(
            manufacturer=device_config.metadata.manufacturer or "",
            package=spec["device_type"],
            mpn=device_config.metadata.part_number or "",
            pincount=device_config.pincount_real,
            datasheet=device_config.metadata.datasheet,
            scriptname=os.path.basename(
                "ipc_noLead_generator.py"
            ),  # For zero-diff. Replace with generator_name later.
        ).lstrip()
    )

    kicad_mod.tags = (
        PACKAGE_CONFIG["keyword_fp_string"]
        .format(
            man=device_config.metadata.manufacturer or "",
            package=spec["device_type"],
            category=category,
        )
        .lstrip()
        .split()
    )

    kicad_mod.tags += device_config.metadata.compatible_mpns
    kicad_mod.tags += device_config.metadata.additional_tags

    pad_arrays = create_dual_or_quad_pad_border(
        GLOBAL_CONFIG,
        pad_details,
        spec,
        pad_overrides=device_config.pad_overrides,
    )
    pad_radius = get_pad_radius_from_arrays(pad_arrays)

    if device_config.has_ep:
        pad_shape_details = getEpRoundRadiusParams(spec, GLOBAL_CONFIG, pad_radius)
        ep_pad_number = spec.get("EP_pin_number", device_config.pincount_full + 1)
        if with_thermal_vias:
            thermals = spec["thermal_vias"]
            paste_coverage = thermals.get(
                "EP_paste_coverage",
                spec.get("EP_paste_coverage", DEFAULT_PASTE_COVERAGE),
            )

            # Override the via avoid setting in the YAML to avoid broken paste
            # aperture spacing.
            # See the same reasoning in the gullwing generator for more background.
            # (https://gitlab.com/kicad/libraries/kicad-footprint-generator/-/issues/674)
            paste_via_avoid = False

            exposed_pad = ExposedPad(
                number=ep_pad_number,
                size=EP_size,
                at=EP_center,  # type: ignore
                paste_layout=thermals.get(
                    "EP_num_paste_pads", spec.get("EP_num_paste_pads", 1)
                ),
                paste_coverage=paste_coverage,
                via_layout=thermals.get("count", 0),
                paste_between_vias=thermals.get("paste_between_vias"),
                paste_rings_outside=thermals.get("paste_rings_outside"),
                via_drill=thermals.get("drill", 0.3),
                via_grid=thermals.get("grid"),
                remove_corner_vias=thermals.get("remove_corner_vias"),
                paste_avoid_via=paste_via_avoid,
                via_paste_clarance=thermals.get(
                    "paste_via_clearance", DEFAULT_VIA_PASTE_CLEARANCE
                ),
                min_annular_ring=thermals.get(
                    "min_annular_ring", DEFAULT_MIN_ANNULAR_RING
                ),
                bottom_pad_min_size=thermals.get("bottom_min_size", 0),
                **pad_shape_details,
            )
        else:
            exposed_pad = ExposedPad(
                number=ep_pad_number,
                size=EP_size,
                at=EP_center,  # type: ignore
                paste_layout=spec.get("EP_num_paste_pads", 1),
                paste_coverage=spec.get("EP_paste_coverage", DEFAULT_PASTE_COVERAGE),
                **pad_shape_details,
            )
    else:
        exposed_pad = None

    ###  Rule Areas  ###############################################################
    zones = rule_area_properties.create_rule_area_zones(  # type: ignore
        device_config.rule_areas, fp_ast_evaluator
    )
    kicad_mod.extend(zones)

    ###  Layout  ###################################################################

    size_x = device_config.body_size_x.nominal
    size_y = device_config.body_size_y.nominal
    layout = DualAndQuadPadArrayLayout(
        global_config=GLOBAL_CONFIG,
        courtyard_offset_body=ipc_offsets.courtyard,
        courtyard_offset_pads=ipc_offsets.courtyard,
        pad_arrays=pad_arrays,
        exposed_pad=exposed_pad,
        body_size=Vector2D.from_floats(size_x, size_y),
        footprint_name=kicad_mod.name,
    )
    kicad_mod += layout

    ###  3D Model  #################################################################
    kicad_mod.add_standard_3d_model_to_footprint(
        device_config.lib_name, device_config.model_name
    )

    ###  Save Footprint  ###########################################################
    write_footprint(kicad_mod, device_config.lib_name, generator_name)
