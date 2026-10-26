#!/usr/bin/env python3

import argparse
import math
import sys
import uuid
from pathlib import Path

import yaml


UUID_NAMESPACE = uuid.UUID("a8f904ee-3787-4c45-aeb0-ac55844379f7")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate exposed-substrate NPTH mounting-hole footprints."
    )
    parser.add_argument("--definitions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--tools",
        required=True,
        type=Path,
        help="Path to the kicad-footprint-generator checkout.",
    )
    return parser.parse_args()


def load_kicad_tools(tools_path: Path) -> dict[str, object]:
    sys.path.insert(0, str(tools_path))
    sys.path.insert(0, str(tools_path / "src"))

    from KicadModTree import (  # noqa: PLC0415
        Circle,
        Footprint,
        FootprintType,
        Hatch,
        Keepouts,
        KicadFileHandler,
        Pad,
        Polygon,
        Property,
        Text,
        Zone,
    )

    return locals()


def arc_points(radius: float, start: float, stop: float, segments: int) -> list[list[float]]:
    return [
        [radius * math.cos(math.radians(angle)), radius * math.sin(math.radians(angle))]
        for angle in (start + (stop - start) * index / segments for index in range(segments + 1))
    ]


def region_points(variant: str, radius: float, extension: float) -> list[list[float]]:
    if variant == "Center":
        return arc_points(radius, 0.0, 360.0 - 360.0 / 96.0, 95)

    outer = radius + extension
    if variant == "Edge":
        return [[outer, -radius], [outer, radius]] + arc_points(radius, 90.0, 270.0, 48)

    if variant == "Corner":
        return [
            [outer, -radius],
            [outer, outer],
            [-radius, outer],
            [-radius, 0.0],
        ] + arc_points(radius, 180.0, 270.0, 24)

    raise ValueError(f"Unsupported variant: {variant}")


def extension_keepout_points(variant: str, radius: float, extension: float) -> list[list[float]]:
    outer = radius + extension
    if variant == "Edge":
        return [[outer, -radius], [outer, radius]] + arc_points(radius, 90.0, -90.0, 48)

    if variant == "Corner":
        return [
            [outer, -radius],
            [outer, outer],
            [-radius, outer],
            [-radius, 0.0],
        ] + arc_points(radius, 180.0, -90.0, 72)

    raise ValueError(f"Variant has no extension keepout: {variant}")


def add_region_outline(
    footprint: object,
    classes: dict[str, object],
    variant: str,
    radius: float,
    extension: float,
    layer: str,
    width: float,
) -> None:
    Circle = classes["Circle"]
    Polygon = classes["Polygon"]
    if variant == "Center":
        footprint.append(Circle(center=[0, 0], radius=radius, layer=layer, width=width))
    else:
        footprint.append(
            Polygon(
                shape=region_points(variant, radius, extension),
                layer=layer,
                width=width,
            )
        )


def generate_footprint(
    entry: dict,
    variant: str,
    variant_spec: dict,
    defaults: dict,
    output_path: Path,
    classes: dict[str, object],
) -> Path:
    Circle = classes["Circle"]
    Footprint = classes["Footprint"]
    FootprintType = classes["FootprintType"]
    Hatch = classes["Hatch"]
    Keepouts = classes["Keepouts"]
    KicadFileHandler = classes["KicadFileHandler"]
    Pad = classes["Pad"]
    Polygon = classes["Polygon"]
    Property = classes["Property"]
    Text = classes["Text"]
    Zone = classes["Zone"]

    footprint_name = defaults["footprint_name"].format(
        name=entry["name"], variant_suffix=variant_spec["variant_suffix"]
    )
    drill = float(entry["drill"])
    mask_diameter = float(entry["mask_keepout_diameter"])
    mask_radius = mask_diameter / 2.0
    copper_expansion = float(defaults["copper_keepout"]["expansion_from_mask_boundary"])
    copper_radius = mask_radius + copper_expansion
    extension = float(defaults["edge_extension"])
    courtyard_radius = copper_radius + float(defaults["courtyard_offset"])

    footprint = Footprint(
        footprint_name,
        FootprintType.UNSPECIFIED,
        tstamp_seed=uuid.uuid5(UUID_NAMESPACE, footprint_name),
    )
    footprint.excludeFromBOM = True
    footprint.excludeFromPositionFiles = True
    footprint.description = defaults["description"].format(
        drill=drill, mask_keepout_diameter=mask_diameter
    ) + f", {variant.lower()} variant"
    footprint.tags = defaults["tags"] + [variant.lower()]

    reference_y = -(copper_radius + 1.0)
    footprint.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[0, reference_y],
            layer="F.SilkS",
        )
    )
    footprint.append(
        Property(
            name=Property.VALUE,
            text=footprint_name,
            at=[0, copper_radius + 1.0],
            layer="F.Fab",
            hide=True,
        )
    )
    footprint.append(
        Property(
            name="KiLib_Generator",
            text="scripts/generate_exposed_substrate_mounting_holes.py",
            at=[0, 0],
            layer="F.SilkS",
            hide=True,
        )
    )

    mask_points = region_points(variant, mask_radius, extension)
    for layer in defaults["solder_mask_keepout"]["layers"]:
        if variant == "Center":
            footprint.append(
                Circle(
                    center=[0, 0],
                    radius=mask_radius,
                    layer=layer,
                    width=0.0,
                    fill=True,
                )
            )
        else:
            footprint.append(
                Polygon(shape=mask_points, layer=layer, width=0.0, fill=True)
            )

    footprint.append(
        Pad(
            type=Pad.TYPE_NPTH,
            shape=Pad.SHAPE_CIRCLE,
            at=[0, 0],
            size=drill,
            drill=drill,
            layers=Pad.LAYERS_NPTH,
            clearance=copper_radius - drill / 2.0,
        )
    )

    if variant != "Center":
        deny_copper = Keepouts(
            tracks=Keepouts.DENY,
            vias=Keepouts.DENY,
            pads=Keepouts.DENY,
            copperpour=Keepouts.DENY,
            footprints=Keepouts.ALLOW,
        )
        footprint.append(
            Zone(
                shape=extension_keepout_points(variant, copper_radius, extension),
                hatch=Hatch(Hatch.EDGE, 0.5),
                keepouts=deny_copper,
                layers=["*.Cu"],
                name="Copper keepout extension",
            )
        )

    add_region_outline(
        footprint,
        classes,
        variant,
        mask_radius,
        extension,
        "Cmts.User",
        0.15,
    )
    add_region_outline(
        footprint,
        classes,
        variant,
        courtyard_radius,
        extension,
        "F.CrtYd",
        0.05,
    )
    footprint.append(Text(text="${REFERENCE}", at=[0, 0], layer="F.Fab"))

    output_file = output_path / f"{footprint_name}.kicad_mod"
    KicadFileHandler(footprint).writeFile(output_file)
    return output_file


def main() -> None:
    args = parse_args()
    definitions = yaml.safe_load(args.definitions.read_text(encoding="utf-8"))
    if definitions["schema"] != "amemb.mounting_hole.exposed_substrate.v1":
        raise ValueError(f"Unsupported schema: {definitions['schema']}")

    classes = load_kicad_tools(args.tools.resolve())
    args.output.mkdir(parents=True, exist_ok=True)

    generated = []
    defaults = definitions["default_parameters"]
    for entry in definitions["footprints"]:
        for variant, variant_spec in definitions["variants"].items():
            generated.append(
                generate_footprint(
                    entry,
                    variant,
                    variant_spec,
                    defaults,
                    args.output,
                    classes,
                )
            )

    expected = set(generated)
    stale = set(args.output.glob("*ExposedSubstrate*.kicad_mod")) - expected
    if stale:
        stale_names = ", ".join(sorted(path.name for path in stale))
        raise RuntimeError(f"Stale generated footprints present: {stale_names}")

    print(f"Generated {len(generated)} footprints in {args.output}")


if __name__ == "__main__":
    main()
