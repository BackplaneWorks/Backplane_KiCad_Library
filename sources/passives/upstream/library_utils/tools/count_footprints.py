#! /usr/bin/env python3

import argparse
import os
import platform
import sys

parser = argparse.ArgumentParser(description="Count number of *.kicad_mod files.")
parser.add_argument(
    "-d",
    "--footprint-directory",
    help="Path to the directory.",
    action="store",
)
parser.add_argument(
    "-v",
    "--verbose",
    help=(
        "Screen verbose. -v Shows basic results, -vv Saves report to a file under"
        " output/ directory, ( Currently NOT WORKING: -vvv Shows extra more, -vvvv"
        " Saves extra more )"
    ),
    action="count",
)
args = parser.parse_args()

# Windoze needs special treatment for paths and dirs
special_host_platform_name = "Windows"

if args.footprint_directory:
    fp_lib_path = args.footprint_directory
else:
    # Set the path to the directory that git clone creates.
    fp_lib_path = input("Enter fp library directory path to search in: ")

# Absolute directory current script is in
script_dir = os.path.dirname(__file__)
common = os.path.abspath(os.path.join(script_dir, os.path.pardir, "common"))

if common not in sys.path:
    sys.path.append(common)

if args.verbose:
    verbose_level = int(args.verbose)
else:
    verbose_level = 0

if verbose_level >= 1:
    from print_color import PrintColor

    printer = PrintColor()

if os.path.isdir(fp_lib_path):
    if verbose_level >= 1:
        printer.green("Folder path is correct!")
else:
    # if there are any errors, print 'fail' for these errors
    if verbose_level >= 1:
        printer.red("Directory:", None, None, True)
        printer.yellow(fp_lib_path, None, None, True)
        printer.red("hasn't found.")
        printer.red("Wrong or missing source directory.")
    else:
        print("Wrong or missing source directory.")
    exit(1)

fp_dir_type_ending = ".pretty"
fp_file_type_ending = ".kicad_mod"

# Output file prefixes
fp_out_rel_path = os.path.join("output", "branch_name__")
fp_out_rel_path_no_git = os.path.join("output", "dir_name__")

fp_out_abs_path = os.path.join(script_dir, fp_out_rel_path)
fp_out_abs_path_no_git = os.path.join(script_dir, fp_out_rel_path_no_git)
path, folder_name = os.path.split(fp_lib_path)
folder_name = folder_name.replace(".pretty", "")

try:
    import git
    from git import Repo
except ImportError:
    if verbose_level >= 1:
        printer.yellow("If missing try: pip install gitpython")
    exit(1)

try:
    fp_search_repo = Repo(fp_lib_path)
    found_repo = True
except git.exc.GitError:
    if verbose_level >= 1:
        printer.yellow("Missing repo.")
    found_repo = False

if platform.system() == special_host_platform_name:
    if verbose_level == 2 or verbose_level == 4:
        try:
            os.mkdir(r"output")
            printer.yellow("output", None, None, True)
            printer.green("directory created.")
        except OSError:
            printer.yellow("output", None, None, True)
            printer.cyan("directory exists.")
            pass

if platform.system() == special_host_platform_name:
    if verbose_level == 2 or verbose_level == 4:
        if found_repo:
            f = open(fp_out_abs_path + fp_search_repo.active_branch.name + ".txt", "w+")
        else:
            f = open(fp_out_abs_path_no_git + folder_name + ".txt", "w+")

totalFiles = 0
totalDir = 0
totalTotalFiles = 0
for base, dirs, files in os.walk(fp_lib_path):
    fps_in_lib = 0
    if base.endswith(fp_dir_type_ending):
        # Check for directories in dirs variable. ln83 above
        totalDir += 1
        str_list = base.replace(fp_lib_path, "")

        for file_inside_pretty in os.listdir(base):
            # check the files which end with specific extension
            if file_inside_pretty.endswith(fp_file_type_ending):
                # TODO correct verbose argument to enable all hidden parts under pretty directories
                # print path name of selected files
                # uncomment next line to verbose all fps inside *.pretty dir.
                # if verbose_level >= 3:
                #    print(os.path.join(r'Footprint: ', file_inside_pretty))
                #    if verbose_level >= 4:
                #        f.write(
                #            "Library: "
                #            + str(str_list)
                #            + " Hosts: "
                #            + str(fps_in_lib)
                #            + " footprints."
                #            + "\n"
                #        )
                totalFiles += 1
                fps_in_lib += 1
        if platform.system() == special_host_platform_name:
            if verbose_level == 2 or verbose_level == 4:
                f.write(
                    "Library: "
                    + str(str_list)
                    + " Hosts: "
                    + str(fps_in_lib)
                    + " footprints."
                    + "\n"
                )
        if verbose_level >= 1:
            print(os.linesep)
            printer.green("Library:", None, None, True)
            printer.yellow(str(str_list))
            printer.green("Hosts:", None, None, True)
            printer.yellow(str(fps_in_lib), None, None, True)
            printer.green("footprints.", None, None, True)
            if verbose_level >= 3:
                print(os.linesep)
    for file_inside_nonpretty in os.listdir(base):
        # check the files which end with specific extension
        if file_inside_nonpretty.endswith(fp_file_type_ending):

            # TODO correct verbose argument to enable all hidden parts under non pretty directories
            if verbose_level >= 3:
                print(os.path.join(r"Footprint: " + file_inside_nonpretty))
                if verbose_level >= 4:
                    f.write("Footprint: " + str(file_inside_nonpretty) + "\n")
            totalTotalFiles += 1

if platform.system() == special_host_platform_name:
    if verbose_level == 2 or verbose_level == 4:
        if found_repo:
            f.write(
                "\n" + "Current active branch: " + fp_search_repo.active_branch.name
            )
        else:
            f.write("\n" + "Current directory: " + fp_lib_path)

        f.write("\n" + "Total Number of footprint libraries: " + str(totalDir))
        f.write(
            "\n"
            + "Number of footprint files under *.pretty/ directories: "
            + str(totalFiles)
        )
        # Obsolete or footprint files in non *.pretty library file
        f.write(
            "\n"
            + "Obsolete footprints under non *.pretty: "
            + str(totalTotalFiles - totalFiles)
        )
        f.write("\n" + "TOTAL number of footprint files: " + str(totalTotalFiles))
        f.close()
if verbose_level >= 1:
    print(os.linesep)
    printer.cyan("Footprint search directory:", None, None, True)
    printer.yellow(fp_lib_path)

if found_repo:
    if verbose_level >= 1:
        printer.cyan("Current active branch:", None, None, True)
        printer.yellow(fp_search_repo.active_branch.name)
        if platform.system() == special_host_platform_name:
            if verbose_level == 2 or verbose_level == 4:
                printer.cyan("Output file directory:", None, None, True)
                printer.yellow(
                    fp_out_abs_path + fp_search_repo.active_branch.name + ".txt"
                )
else:
    if platform.system() == special_host_platform_name:
        if verbose_level == 2 or verbose_level == 4:
            printer.cyan("Output file directory:", None, None, True)
            printer.yellow(fp_out_abs_path_no_git + folder_name + ".txt")

    else:
        if verbose_level >= 1:
            printer.yellow("No repo found.")

if verbose_level >= 1:
    print("\n", end="")
    printer.cyan("Total Number of footprint libraries:", None, None, True)
    printer.yellow(str(totalDir))
    printer.cyan(
        "Number of footprint files under *.pretty/ directories:", None, None, True
    )
    printer.yellow(str(totalFiles))
    # Obsolete or footprint files in non *.pretty library file
    printer.yellow("Obsolete footprints under non *.pretty:", None, None, True)
    printer.red(str((totalTotalFiles - totalFiles)))
    printer.cyan("TOTAL number of footprint files:", None, None, True)
    printer.yellow(str(totalTotalFiles))
    exit(0)
else:
    print(totalTotalFiles)
    exit(0)
