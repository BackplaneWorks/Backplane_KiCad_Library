from dataclasses import dataclass
import logging
import os

import cadquery as cq

from kilibs.geom import Vec3DCompatible, Vector3D

from generators.tools.model import cq_color_correct, shaderColors  # type: ignore
from generators.tools.model.exportVRML.export_part_to_VRML import (
    export_VRML,  # type: ignore
)
from generators.tools.model.stepreduce import stepreduce  # type: ignore
from generators.tools.cli_args import CLI_ARGS


class AssemblyParts:
    """
    A group of parts in an assembly, including a colour definition key for each.
    """

    @dataclass
    class Part:
        part: cq.Workplane
        color_key: str

    def __init__(self, parts: list[tuple[cq.Workplane | None, str | None]] = []):
        """
        Construct a list of parts.

        Any entry that has a None part is discarded.
        """
        self.parts: list[AssemblyParts.Part] = []

        for part in parts:
            self.append(part[0], part[1])

    def append(self, part: cq.Workplane | None, color: str | None) -> None:

        if part is None:
            return

        assert color, f"Color must be given if part is given, got {color} for {part}"
        self.parts.append(AssemblyParts.Part(part, color))

    def rotate(
        self,
        angle: float,
        axis_start: Vec3DCompatible = (0, 0, 0),
        axis_end: Vec3DCompatible = (0, 0, 1),
    ) -> None:
        """
        Rotate each part in-place around the given axis.

        The default is to rotate around the z-axis.

        Args:
            angle: the angle to rotate by, in degrees
            axis_start: start of axis vector
            axis_end: end of axis vector
        """
        if angle == 0:
            return

        for part in self.parts:
            part.part = part.part.rotate(
                Vector3D(axis_start).to_tuple(), Vector3D(axis_end).to_tuple(), angle
            )

    def translate(self, translation: Vec3DCompatible) -> None:
        """
        Translate every part in the list by the same amount
        """
        translation = Vector3D(translation)

        if translation.is_nullvec():
            return

        for part in self.parts:
            part.part = part.part.translate(translation.to_tuple())


def export(
    generator_name: str,
    lib_name: str,
    model_name: str,
    parts: AssemblyParts
) -> None:
    """Save the model as STEP and optionally also as a VRML file.

    Args:
        generator_name: The name of the generator.
        lib_name: The library name where the model(s) shall be stored.
        model_name: The name of the model(s).
        parts: The list of parts (e.g. pins, body, pin marker) that shall be added
            to the assembly.
        color_names: The names of the colors of each part.
    """
    logging.info(model_name)

    if CLI_ARGS.dry_run:
        return

    if len(parts.parts) == 0:
        logging.error(
            f"Generator '{generator_name}' called export() for model '{model_name}'"
            "with an empty parts list!"
        )
        return  # Nothing to export

    # Create the output directory if it does not exist:
    if not lib_name.endswith(".3dshapes"):
        lib_name += ".3dshapes"
    if CLI_ARGS.separate_outputs:
        output_dir = str(CLI_ARGS.output_dir_models / generator_name / lib_name)
    else:
        output_dir = str(CLI_ARGS.output_dir_models / lib_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if CLI_ARGS.quick:
        mode = cq.exporters.assembly.ExportModes.DEFAULT  # pyright: ignore
    else:
        mode = cq.exporters.assembly.ExportModes.FUSED  # pyright: ignore

    # Create an assembly in which all parts are wrapped:
    assembly = cq.Assembly(name=model_name)

    # Add the parts to the assembly:
    for part in parts.parts:
        rgb = shaderColors.named_colors[part.color_key].getDiffuseFloat()
        color = cq_color_correct.Color(rgb[0], rgb[1], rgb[2])
        assembly.add(part.part, color=color)

    if not hasattr(assembly, "export"):
        # for backward compatibility with CadQuery < 2.5.0
        assembly.export = assembly.save  # type: ignore

    # Export the assembly to STEP
    assembly.export(  # pyright: ignore
        os.path.join(output_dir, model_name + ".step"),
        cq.exporters.ExportTypes.STEP,
        mode=mode,  # pyright: ignore
        write_pcurves=False,
    )

    if not CLI_ARGS.quick:
        # Check for a proper union:
        check_step_export_union(assembly, output_dir, model_name)

        # Do STEP post-processing:
        postprocess_step(assembly, output_dir, model_name)

        # Update the license
        from generators.tools.model import add_license  # type: ignore

        add_license.addLicenseToStep(  # type: ignore
            output_dir,
            model_name + ".step",
            add_license.LIST_int_license,
            add_license.STR_int_licAuthor,
            add_license.STR_int_licEmail,
            add_license.STR_int_licOrgSys,
            add_license.STR_int_licPreProc,
        )

    if CLI_ARGS.export_vrml:
        export_VRML(
            os.path.join(output_dir, model_name + ".wrl"),
            parts,
        )


def check_step_export_union(
    component: cq.Assembly, output_dir: str, model: str
) -> None:
    # Path to the STEP file to be validated
    cur_path = os.path.join(output_dir, model + ".step")

    # Import the STEP that was exported so that the number of solids can be checked
    union = cq.importers.importStep(cur_path)

    # Our starting tolerance
    tol = 0.001

    # Try multiple fuzzy tolerance values to try to fix
    while union.solids().size() != 1:
        component.export(  # pyright: ignore
            cur_path,
            cq.exporters.ExportTypes.STEP,
            mode=cq.exporters.assembly.ExportModes.FUSED,  # pyright: ignore
            assembly_name=model,
            write_pcurves=False,
            fuzzy_tol=tol,
        )

        # Make the fuse gradually less precise
        tol = tol / 0.5
        print(tol)

        # Escape clause
        if tol > 0.001:
            break

    assert union.solids().size() == 1


def postprocess_step(component: cq.Assembly, output_dir: str, model: str) -> None:
    # Path to the STEP file
    cur_path = os.path.join(output_dir, model + ".step")

    # The stepreduce algorithm seems stable, so disable verification by default
    verify = False

    if verify:
        orig_cmp = cq.Assembly(cq.importers.importStep(cur_path)).toCompound()
        stepreduce(cur_path, cur_path)
        reduced_cmp = cq.Assembly(cq.importers.importStep(cur_path)).toCompound()

        # Check volumes
        orig_volume = orig_cmp.Volume()
        reduced_volume = reduced_cmp.Volume()
        assert (
            orig_volume == reduced_volume
        ), f"Volume mismatch: {orig_volume} != {reduced_volume}"

        # Check center of mass
        orig_center_of_mass = orig_cmp.Center()
        reduced_center_of_mass = reduced_cmp.Center()
        assert (
            orig_center_of_mass == reduced_center_of_mass
        ), f"Center of mass mismatch: {orig_center_of_mass} != {reduced_center_of_mass}"
    else:
        stepreduce(cur_path, cur_path)
