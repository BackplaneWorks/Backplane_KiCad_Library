from collections import namedtuple

import generators.tools.model.exportVRML.shaderColors as shaderColors
from generators.tools.model import add_license

# crease_angle=0.5 is a good compromise
crease_angle_default = 0.5

# Define the Mesh named tuple
Mesh = namedtuple("Mesh", ["points", "faces", "color", "transp"])


def shape_to_mesh(shape, color, transparency, scale=None) -> Mesh:
    """
    Tessellates a shape and applies scaling to it, if needed.
    Parameters:
        shape - An OCCT shape object
        color - The color to be applied to the mesh
        transparency - How opaque or transparent the mesh should be
        scale - Allows the meshes to be scaled up or down arbitrarily
    """

    # The smaller the better the quality, 1 coarse; 0.03 good compromise
    mesh_deviation = 0.7

    # Do the shape tessellation
    mesh_data = shape.tessellate(mesh_deviation)

    # Get the mesh points from the mesh data
    points = mesh_data[0]

    # If scaling is to be applied, do that
    if scale != None:
        points = map(lambda p: p * scale, points)

    # Assemble the new mesh
    new_mesh = Mesh(points=points, faces=mesh_data[1], color=color, transp=transparency)

    return new_mesh


def get_colored_meshes(export_parts, scale=None) -> list[Mesh]:
    """
    Extracts the faces from the given objects and saves their tessellated meshes.
    Parameters:
        export_parts - AseemblyParts to be exported to VRML
    """

    # The list that will hold all the face meshes
    meshes: list[Mesh] = []

    # For now, the transparency is locked at opaque
    transparency = 1.0

    # Step through all of the CadQuery shape objects and tessellate the faces
    shape_index = 0
    for part, color_name in export_parts.parts:
        # Get the wrapped OCCT shape from CadQuery
        occt_shape = part.val()  # .wrapped

        # Step through all of the faces in the shape
        for single_face in occt_shape.Faces():
            # Triangulate the face to a mesh and save it
            meshes.append(shape_to_mesh(single_face, color_name, transparency, scale))

        # Moves to the next shape color
        shape_index += 1

    return meshes


def write_VRML_file(meshes: list[Mesh], filepath, licence_info=None):
    """
    Export given list of Mesh objects to a VRML file.
    """
    used_colors = None

    creaseAngle = crease_angle_default

    used_colors: dict[str, shaderColors.shaderColor] = {}
    for mesh in meshes:
        if mesh.color not in used_colors:
            used_colors[mesh.color] = shaderColors.named_colors[mesh.color]

    with open(filepath, "w", newline="\n") as f:
        # Write the standard VRML header
        f.write("#VRML V2.0 utf8\n#kicad StepUp wrl exported\n\n")
        if licence_info is not None:
            for line in licence_info:
                f.write("# " + line + "\n")

        # Stably sort the colors for export
        for shader_color_key in sorted(list(used_colors.keys())):
            shader_color = used_colors[shader_color_key]
            f.write(shader_color.toVRMLdefinition())

        for obj in meshes:
            if creaseAngle == 0:
                f.write("Shape { geometry IndexedFaceSet \n{ coordIndex [")
            else:
                f.write(
                    "Shape { geometry IndexedFaceSet \n{ creaseAngle %.2f coordIndex ["
                    % creaseAngle
                )

            # Write coordinate indexes for each face
            f.write(",".join("%d,%d,%d,-1" % f for f in obj.faces))
            f.write("]\n")  # closes coordIndex
            f.write("coord Coordinate { point [")
            # Write coordinate points for each vertex
            f.write(",".join("%.3f %.3f %.3f" % (p.x, p.y, p.z) for p in obj.points))
            f.write("]\n}")  # closes Coordinate
            f.write("}\n")  # closes points

            if not isinstance(obj.color, str) or isinstance(used_colors, str):
                shape_transparency = obj.transp
                f.write(
                    "appearance Appearance{material Material{diffuseColor %f %f %f\n"
                    % obj.color
                )
                f.write("transparency %f}}" % shape_transparency)
            else:
                f.write(used_colors[obj.color].toVRMLuseColor())
            f.write("}\n")  # closes shape


def export_VRML(output_path, export_parts):
    """
    Exports an array of export objects to a file with their associated colors.
    Parameters:
        output_path - The path to the .wrl file to be written
        export_objects - AssemblyParts containing the parts and colors
    """

    # KiCAD uses this scale for their VRML objects
    scale = 1 / 2.54

    # Get the meshes together with their assigned colors
    colored_meshes = get_colored_meshes(export_parts, scale)

    # Save the meshes to a file
    write_VRML_file(
        colored_meshes, output_path, add_license.LIST_int_license
    )
