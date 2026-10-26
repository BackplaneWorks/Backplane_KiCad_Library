#!/usr/bin/env python3

import argparse
import importlib
import os
from sys import argv

import cadquery as cq

# The amount (in mm) that a model is allowed to deviate before failing
tolerance = 0.01


def main():
    parser = argparse.ArgumentParser(
        description="Audits the generated KiCAD 3D models against known STEP files."
    )
    parser.add_argument(
        "--new_step_dir",
        dest="new_step_dir",
        required=True,
        help="Sets the directory where the new generated STEP files have been placed.",
    )
    parser.add_argument(
        "--ref_step_dir",
        dest="ref_step_dir",
        required=True,
        help="Sets the directory where the reference STEP files have been placed.",
    )
    parser.add_argument(
        "--library",
        dest="library",
        required=False,
        help="Selects a specific library to generate models for.",
    )
    parser.add_argument(
        "--error_on_non_matching",
        dest="error_on_non_matching",
        required=False,
        help="Whether or not to show errors related to new files not having matching original refrence files.",
    )
    args = parser.parse_args()

    # Get a list of the package directories so that we can work through them
    new_dir_list = [dir_name for dir_name in os.listdir(args.new_step_dir)]
    ref_dir_list = [dir_name for dir_name in os.listdir(args.ref_step_dir)]

    # Check the bounding box of the new file against the bounding box of the matching old file
    for nd in new_dir_list:
        if nd not in ref_dir_list:
            print(
                "Directory {} exists in the new STEP directory, but not in the reference STEP directory.".format(
                    nd
                )
            )
            continue
        else:
            # Step through all the new files so they can be compared to the originals
            new_files = [
                dir_name for dir_name in os.listdir(os.path.join(args.new_step_dir, nd))
            ]
            for new_file in new_files:
                if new_file.endswith("step"):
                    # Make sure the matching reference file exists
                    ref_step_path = os.path.join(args.ref_step_dir, nd, new_file)
                    if not os.path.exists(ref_step_path):
                        if (
                            args.error_on_non_matching != None
                            and args.error_on_non_matching == "true"
                        ):
                            print(
                                "New STEP file {} does not have a matching reference STEP file.".format(
                                    new_file
                                )
                            )
                        continue

                    # Import the reference and new STEP files
                    new_step = cq.importers.importStep(
                        os.path.join(args.new_step_dir, nd, new_file)
                    )
                    ref_step = cq.importers.importStep(ref_step_path)

                    # If there is more than one solid in the new STEP, we must combine the bounding boxes
                    new_step_bb = new_step.solids().all()[0].val().BoundingBox()
                    if len(new_step.solids().all()) > 1:
                        # Work through all the solids, adding their bounding boxes together
                        for solid in new_step.solids().all()[1:-1]:
                            new_step_bb.add(solid.val().BoundingBox())

                    # If there is more than one solid in the reference STEP, we must combine the bounding boxes
                    ref_step_bb = ref_step.solids().all()[0].val().BoundingBox()
                    if len(ref_step.solids().all()) > 1:
                        # Work through all the solids, adding their bounding boxes together
                        for solid in ref_step.solids().all()[1:-1]:
                            ref_step_bb.add(solid.val().BoundingBox())

                    # Check the bounding boxes
                    ref_x_len = ref_step_bb.xlen
                    new_x_len = new_step_bb.xlen
                    ref_y_len = ref_step_bb.ylen
                    new_y_len = new_step_bb.ylen
                    ref_z_len = ref_step_bb.zlen
                    new_z_len = new_step_bb.zlen
                    if (
                        abs(ref_x_len - new_x_len) >= tolerance
                        or abs(ref_y_len - new_y_len) >= tolerance
                        or (ref_z_len - new_z_len) >= tolerance
                    ):
                        print(
                            "File {} has a bounding box that does not match between the reference and new STEP files: ref_xlen {} vs new_xlen {}, ref_ylen {} vs new_ylen {}, ref_zlen {} vs new_zlen {}.".format(
                                ref_step_path,
                                format(ref_x_len, ".5f"),
                                format(new_x_len, ".5f"),
                                format(ref_y_len, ".5f"),
                                format(new_y_len, ".5f"),
                                format(ref_z_len, ".5f"),
                                format(new_z_len, ".5f"),
                            )
                        )

                    # Compare the centers of the bounding boxes to make sure there is no part drift
                    ref_bb_center_x = ref_step_bb.center.x
                    new_bb_center_x = new_step_bb.center.x
                    ref_bb_center_y = ref_step_bb.center.y
                    new_bb_center_y = new_step_bb.center.y
                    ref_bb_center_z = ref_step_bb.center.z
                    new_bb_center_z = new_step_bb.center.z
                    if (
                        abs(ref_bb_center_x - new_bb_center_x) >= tolerance
                        or abs(ref_bb_center_y - new_bb_center_y) >= tolerance
                        or abs(ref_bb_center_z - new_bb_center_z) >= tolerance
                    ):
                        print(
                            "File {} has a bounding box center that does not match between the reference and new STEP files: Centers - Ref X: {} vs New X: {}, Ref Y: {} vs New Y: {}, Ref Z: {} vs New Z: {}".format(
                                ref_step_path,
                                format(ref_bb_center_x, ".5f"),
                                format(new_bb_center_x, ".5f"),
                                format(ref_bb_center_y, ".5f"),
                                format(new_bb_center_y, ".5f"),
                                format(ref_bb_center_z, ".5f"),
                                format(new_bb_center_z, ".5f"),
                            )
                        )


if __name__ == "__main__":
    main()
