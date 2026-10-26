#!/usr/bin/env python
import argparse
import glob
import os.path

"""
Rough check of symbols vs footprints for Neutrik audio connectors:
    - all symbols have a matching footprint
    - all footprints have a matching symbol
    - correct footprint is assigned to each symbol
    - footprint pads match symbol pins
    - symbol datasheet url matches the one in the footprint description
    - symbol description matches footprint description
    - symbol keywords contain "neutrik"
    - parts with auxiliary switch have "spdt switch" in the symbol keywords

Usage: check_neutrik_connectors.py
        <path to directory containing the .kicad_sym library>
        <path to directory containing the .pretty library>
"""


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Perform basic checks of Neutrik audio connector "
            "symbols against footprints"
        )
    )
    parser.add_argument(
        "sym_lib_path",
        type=str,
        help="path to symbol libraries: contains Connector_Audio.kicad_sym",
    )
    parser.add_argument(
        "fp_lib_path",
        type=str,
        help="path to footprint libraries: contains Connector_Audio.pretty",
    )
    args = parser.parse_args()

    symbol_path = os.path.join(
        os.path.abspath(args.sym_lib_path), "Connector_Audio.kicad_sym"
    )
    fp_path = os.path.join(os.path.abspath(args.fp_lib_path), "Connector_Audio.pretty")

    symbols = {}
    footprints = {}

    # parse the symbols
    with open(symbol_path, "r") as s:
        for line in s:
            if "(symbol" in line and "(in_bom" in line:
                sym_name = line.split()[1].strip('"')
                symbols[sym_name] = {"base": True, "pins": set()}
            if "(symbol" in line and "(extends" in line:
                sym_name = line.split()[1].strip('"')
                parent_name = line.split()[3].strip('")')
                symbols[sym_name] = {
                    "base": False,
                    "pins": symbols[parent_name]["pins"],
                }
            if "(number" in line:
                pin_num = line.split()[1].strip('"')
                symbols[sym_name]["pins"].add(pin_num)
            if '(property "Footprint"' in line:
                footprint = line.split()[2].strip('"')
                symbols[sym_name]["footprint"] = footprint
            if '(property "Datasheet' in line:
                datasheet = line.split()[2].strip('"')
                symbols[sym_name]["datasheet"] = datasheet
            if '(property "ki_keywords' in line:
                keywords = line.split('"')[3]
                symbols[sym_name]["keywords"] = keywords
            if '(property "ki_description' in line:
                description = line.split('"')[3]
                symbols[sym_name]["description"] = description

    # parse the footprints
    for fp in glob.glob(fp_path + "/*.kicad_mod"):
        if "Neutrik" in fp:
            fp_split = fp.split("_")
            fp_shortname = fp_split[fp_split.index("Neutrik") + 1]
            fp_name = "Connector_Audio:" + os.path.basename(fp).replace(
                ".kicad_mod", ""
            )
            footprints[fp_shortname] = {"fp": fp_name, "pads": set()}
            with open(fp, "r") as f:
                for line in f:
                    if "(pad " in line:
                        pad_name = line.split()[1].strip('"')
                        if pad_name:  # skip mechanical holes
                            footprints[fp_shortname]["pads"].add(pad_name)
                    if "(descr" in line:
                        description = line.split('"')[1]
                        footprints[fp_shortname]["description"] = description

    # now check the symbols are correct
    derived_symbols = {k: v for k, v in symbols.items() if not v["base"]}
    for s in derived_symbols:
        # all the neutrik parts should have "neutrik" added to the keywords
        if "neutrik" not in derived_symbols[s]["keywords"]:
            print(
                f"ERROR: symbol {s} does not have 'neutrik' in its keywords: "
                f"{derived_symbols[s]['keywords']}"
            )

        # the parts with SPDT switches should have "spdt switch" added to the keywords
        if "SW" in s and "spdt switch" not in derived_symbols[s]["keywords"]:
            print(
                f"ERROR: symbol {s} has an SPDT switch but does not have "
                f"'spdt switch' in its keywords: {derived_symbols[s]['keywords']}"
            )

        # check there's a footprint with the same PN as the symbol
        if s in footprints.keys():
            sym = derived_symbols[s]

            # check correct footprint is assigned
            if sym["footprint"] != footprints[s]["fp"]:
                print(
                    f"ERROR: symbol {s} does not have the correct "
                    f"footprint assigned (should be {footprints[s]['fp']}, "
                    f"is {sym['footprint']})"
                )

            # check pads match
            if sym["pins"] != footprints[s]["pads"]:
                print(
                    f"ERROR: symbol {s}'s pins don't match the footprint. "
                    f"Symbol pins: {sym['pins']}, "
                    f"footprint pads: {footprints[s]['pads']}"
                )

            # check description + datasheet in symbol matches footprint description
            reconstructed_fp_description = sym["description"] + ", " + sym["datasheet"]
            if reconstructed_fp_description != footprints[s]["description"]:
                print(
                    f"ERROR: symbol {s}'s description and URL don't match the footprint. "
                    f"Symbol description:    '{sym['description']}'\n"
                    f"Symbol datasheet:      '{sym['datasheet']}'\n"
                    f"Footprint description: '{footprints[s]['description']}'"
                )

        else:
            print(
                f"ERROR: symbol {s} does not have a matching footprint in the footprint library"
            )

    # check that I added a derived symbol for each footprint
    for f in footprints:
        if f not in derived_symbols.keys():
            print(f"ERROR: footprint {f} does not have a matching symbol")


if __name__ == "__main__":
    main()
