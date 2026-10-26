#!/usr/bin/env python
import argparse
import os

import dictdiffer
import yaml


def compare_yamls(file1: str, file2: str):
    with open(file1, "r") as rdr:
        data1_dict = yaml.load(rdr.read(), Loader=yaml.FullLoader)

    with open(file2, "r") as rdr:
        data2_dict = yaml.load(rdr.read(), Loader=yaml.FullLoader)

    if data1_dict != data2_dict:
        additions = set()
        changes = set()
        deletions = set()
        for diff in dictdiffer.diff(data1_dict, data2_dict):
            # for added keys, dictdiffer returns ('add', 'key', [('subkey',values), ('subkey', values)] )
            # for yamls with top-level keys, the key is empty and the subkey is the part number
            # for yamls with non-top-level keys, the key is the part number
            if diff[0] == "add":
                if diff[1] == "":
                    for entry in diff[2]:
                        # extract key name from subkey tuple in form (_. _, [(key, _), (key, _), ...])
                        additions.add(entry[0])
                else:
                    changes.add(diff[1])

            # same structure here as for additions
            elif diff[0] == "remove":
                if diff[1] == "":
                    for entry in diff[2]:
                        # extract key name from subkey tuple in form (_. _, [(key, _), (key, _), ...])
                        deletions.add(entry[0])
                else:
                    changes.add(diff[1])

            # for changes, dictdiffer returns ('change', 'key.subkey', (prev_value,new_value))
            # if the key contains periods, it returns ('change', ['key', subkey], (prev_value,new_value))
            elif diff[0] == "change":
                if isinstance(diff[1], list):
                    keyname = diff[1][0]
                else:
                    keyname = diff[1].split(".")[0]
                changes.add(keyname)
        return additions, changes, deletions
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare semantic equality of two yaml files."
    )
    parser.add_argument("file_paths", type=str, nargs=2, help="paths to yamls")
    args = parser.parse_args()
    missing_file = False
    for i in args.file_paths:
        if not os.path.exists(i):
            print(f"{i} does not exist")
            missing_file = True
    if missing_file:
        exit(-1)

    diff = compare_yamls(args.file_paths[0], args.file_paths[1])
    if diff is not None:
        additions, changes, deletions = diff
        for i in additions:
            print(f"A {i}")
        for i in changes:
            print(f"M {i}")
        for i in deletions:
            print(f"D {i}")
        exit(1)
    else:
        exit(0)
