#!/usr/bin/env python
import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def emit_changed_generator_invocations(
    prev_hash: str, cur_hash: str, verbose: bool = False
):
    extra_params = ""
    if verbose:
        print(f"Comparing changes from {prev_hash} to {cur_hash}")
        extra_params = " -v"
    with tempfile.TemporaryDirectory() as tmpdirname:
        basedir = (
            subprocess.check_output("git rev-parse --show-toplevel", shell=True)
            .strip()
            .decode("utf-8")
        )

        # Load the module "compare_spec" from the "footprint-generator" repo:
        sys.path.insert(0, basedir + "/src")
        module_path = basedir + "/src/generators/tools/spec/compare_specs.py"
        spec = importlib.util.spec_from_file_location("compare_specs", module_path)
        assert spec is not None
        compare_spec = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(compare_spec)

        changed_files = set(
            subprocess.check_output(
                f"git diff-tree --diff-filter=ADM --no-commit-id --oneline --name-only -r {prev_hash} {cur_hash}",
                shell=True,
            )
            .decode("utf-8")
            .split("\n")
        )
        changed_files.remove("")
        changed_generators: set[str] = {
            os.path.dirname(g).split("/", 1)[1]
            for g in changed_files
            if g.startswith("data")
        }
        if verbose:
            print(f"Modified files: {list(changed_files)}")
            print(f"Affected generators: {list(changed_generators)}")
        subprocess.run(
            f"git --work-tree={tmpdirname} checkout {prev_hash} -- data", shell=True
        )
        invocations: list[str] = []
        for g in changed_generators:
            if verbose:
                print(f"Checking changes for generator: {g}")
            diff = compare_spec.compare_specs_of_generator(
                generator_name=g,
                folder_new=Path(basedir) / "data",
                folder_old=Path(tmpdirname) / "data",
            )
            if verbose:
                print("Compare output:")
                if diff.new_ids:
                    print(f"{len(diff.modified_ids)} added definitions:")
                    for id in diff.new_ids:
                        print("  " + id)
                if diff.modified_ids:
                    print(f"{len(diff.modified_ids)} modified definitions:")
                    for id in diff.modified_ids:
                        print("  " + id)
                if diff.deleted_ids:
                    print(f"{len(diff.deleted_ids)} deleted definitions:")
                    for id in diff.deleted_ids:
                        print("  " + id)
                if diff.identical_ids:
                    print(f"{len(diff.identical_ids)} identical definitions.")
            ids_to_regenerate = diff.new_ids + diff.modified_ids
            if ids_to_regenerate:
                invocation = (
                    f"python generate.py -g {g} "
                    f"-p {' '.join(ids_to_regenerate)}{extra_params}"
                )
                invocations.append(invocation)
        return invocations


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find modified yamls in 3d generator data and emit generator invocations."
    )
    parser.add_argument(
        "--prev", "-p", type=str, help="old commit hash", default="HEAD~1"
    )
    parser.add_argument("--cur", "-c", type=str, help="new commit hash", default="HEAD")
    parser.add_argument(
        "--output", "-o", type=str, help="output directory for 3d models", required=True
    )
    parser.add_argument(
        "--isolated", "-i", action="store_true", help="run in isolated shell"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="provide detailed output"
    )

    args = parser.parse_args()
    basedir = (
        subprocess.check_output("git rev-parse --show-toplevel", shell=True)
        .strip()
        .decode("utf-8")
    )
    if args.verbose:
        print(f"Basedir is {basedir}")
    invocations = emit_changed_generator_invocations(
        args.prev, args.cur, verbose=args.verbose
    )
    os.chdir(os.path.join(basedir, "src/generators"))
    if args.verbose:
        print(f"Found {len(invocations)} generator invocations.")
    for i in invocations:
        command = f"{i} -m {os.path.realpath(args.output)}"

        if args.isolated:
            command = f'env -i HOME="$HOME" bash -l -c "{command}"'
        print(f"Running {command}")
        subprocess.run(command, shell=True)
