# KiCad Library Utils

> [!important]
> The content in this directory will be moved or deleted.
> What you see here is the current state of the effort to
> simplify our tooling.
> https://gitlab.com/groups/kicad/libraries/-/work_items/17

This directory contains a variety of tools related to the libraries used in [KiCad](https://kicad.org/):


* symbols
* footprints
* 3D models

These tools can be used for the development of the [official KiCad libraries](https://gitlab.com/kicad/libraries) as well as for custom (internal) libraries.

The tools are currently mainly concerned with quality and style checks (e.g. for CI tests) according to the [KLC rules](https://klc.kicad.org/).

Adding custom (internal) rules for your own libraries is a bit cumbersome at the moment (you need to maintain your private fork of this repository), but their usage is within the targeted scope of these tools.
Your contribution for improving this situation is welcome.

Other tools (beside style and quality checks) are welcome to this repository, too.


# Content

## klc-check directory

**check_symbol.py**: Script for checking [KLC][] compliance of symbol files.

**check_footprint.py**: Script for checking [KLC][] compliance of footprint files.

**check_3d_coverage.py**: Script for checking which KiCad footprints in a `.pretty` library have 3D models. It also shows unused 3D model files.

**comparelibs.py**: Script to compare two versions of the same library. Used as part of the `kicad-symbols` CI.

[KLC]: http://kicad.org/libraries/klc/

### gitlabci directory

Contains helper scripts to run the CI for the following repos
* kicad-symbols
* kicad-footprints

## common directory

Contains various python libraries used by the check scripts and the generators.
* **kicad_mod.py**: A Python module for loading, editing, and saving KiCad footprint files.
* **kicad_sym.py**: A Python module for loading, editing, and saving KiCad symbol libraries.

## symbol-generators

**example-generator.py**: An example on how to create symbols using python
**from_csv_generator.py**: A Python CLI to generate symbols from pinout CSVs.

## tools directory

**compare_sexpr_files.sh**: Normalizes and compares two sexpr files. Those can be `kicad_sym` or `kicad_mod` files.
**count_footprints.py**: Input is a path to the footprint repo directory. Search and report findings for `*.pretty` dirs and `*.kicad_mod` files. Also outputs a file ending with branch name under `/output` dir.


## test directory

**read_write_kicad_sym.sh** Opens `.kicad_sym` files, parses them and writes them to a temp-file. Then the temp-file and original file are normalized and compared. If the reader and writer implementation are correct there should be no differences.

In the future it is planned to run this over the whole library to check if the scripts are working properly.

How to use
==========

## Symbol Library Checker

    # first get into klc-check directory
    cd kicad-library-utils/klc-check

    # run the script passing the files to be checked
    ./check_symbol.py path_to_lib1 path_to_lib2

    # to check a specific component you can use the -c flag
    ./check_symbol.py -c component_name path_to_lib1

    # run the following 'h'elp command to see other options
    ./check_symbol.py -h

## Footprint Checker

    # first get into klc-check directory
    cd kicad-library-utils/klc-check

    # run the script passing the files to be checked
    ./check_footprint.py path_to_fp1.kicad_mod path_to_fp2.kicad_mod

    # Add `-v`, `-vv`, or `-vvv` for extra verbose output. The most useful is `-vv`, which explains in details the violations. Ex:
    ./check_footprint.py path_to_fp1.kicad_mod path_to_fp2.kicad_mod -vv

    # run the following 'h'elp command to see other options
    ./check_footprint.py -h


## 3D Coverage Checker

    # This script will by default assume the following - use options to change this:
    # - Your footprints are in a directory called kicad-footprints
    # - Your models are in a directory called packages3D
    # - Both of those directories are in the same place as kicad-library-utils
    # These assumptions hold if you cloned all three repositories in the same directory

    # To run the coverage checker, first get into klc-check directory
    cd kicad-library-utils/klc-check

    # run the script to check all footprints
    ./check_3d_coverage.py

    # run the script to check only the specified library
    ./check_3d_coverage.py Package_SO

    # run the following 'h'elp command to see other options
    ./check_3d_coverage.py -h

## Compare Symbol Libraries

    # first get into klc-check directory
    cd kicad-library-utils/klc-check

    # run the script passing the libraries to be compared
    ./comparelibs.py --new path_to_new_lib --old path_to_old_lib

    # to also do a KLC check for each new or changed symbol use the --check flag
    ./comparelibs.py --new path_to_new_lib --old path_to_old_lib --check

    # run the following 'h'elp command to see other options
    ./comparelibs.py -h

## Add Symbol/Footprint Test Symbols/Footprints
    `klc-check/test_project` contains a test project which has all `sym_lib_table` to edit the librarys

## Generate Symbols

You can use `./symbol-generators/from_csv_generator.py` to generate KiCad Symbols from pinout CSVs.
For example use:

    python3 ./symbol-generators/from_csv_generator.py pinout.csv --output SYMBOL_NAME.kicad_sym

You can also process a folder of pinout CSVs like this:

    python3 ./symbol-generators/from_csv_generator.py pinout_data --folder --output generated_symbols

For more information see the [corresponding wiki page](https://gitlab.com/groups/kicad/libraries/-/wikis/Spreadsheed-driven-symbol-generator).

# Contributing

Please keep in mind, that this repository is mainly targeted at the [official KiCad libraries](gitlab.com/kicad/libraries/).
Thus you should manage your custom rules outside of this repository.
Reusable infrastructure (e.g. for supporting custom rules) is welcome, of course.

## Python code style

The tools [black](https://black.readthedocs.io/) and [isort](https://pycqa.github.io/isort/) are used for formatting the code.
You should apply this format before committing code:
```shell
make style
```

All python code should follow [PEP8](https://www.python.org/dev/peps/pep-0008/).
This style and many other issues can be tested via [flake8](https://flake8.pycqa.org/en/latest/) (also executed as part of the CI tests):
```shell
make lint
```

Please refrain from using recently introduced features of the Python language, which are not yet supported by the most recent stable release of major distributions (e.g. Debian).

## How to run unit tests

To test the symbol checker code, run:
```
make test-klc-symbols
```

To test the footprint checker code, run:
```
make test-klc-footprints
```

If one of the tests fail, you can run klc-check manually, e.g.
```
./klc-check/check_symbol.py klc-check/test_symbol/CI_Test_S6.x.kicad_sym  -vv -c 'Fail__S6.2__ComaKeywords'
```

## Check before committing

Usually, you commit the footprint (or symbol) and let CI check your job.
You can let git pass the check before actually committing. If it's red,
fix your footprint (or symbol) !

To automate the call, place a hook file in the footprint git's hooks directory,
**/somewhere/kicad/kicad-footprints/.git/hooks** named **pre-commit**
with the following content:
```
#!/bin/bash

ERR=0
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
for F in $STAGED_FILES; do
  if [[ "${F: -10}"  == ".kicad_mod" ]] ; then
    x=$(python3  /somewhere/kicad-library-utils/klc-check/check_footprint.py  -vv "$F")
    echo "$x"
    echo "$x" | grep -q "Violating" &&  ERR=1
  fi
done
exit $ERR
```
diff-filter=ACM stands for Added, Copied, Modified

The script skips non footprint-files. Use **git commit --no-verify** to bypass the hook.

Place the script in the footprint (or symbol) directory, not in the library-utils' git !


Notice
======

The scripts use a different algorithm to generate files in relation to the KiCad saving action. That will result output files with more modified lines than expected, because the line generally are repositioned. However, the file still functional.

Always check the generated files by opening them on KiCad. Additionally, if you are working over a git repository (if not, you should) you can commit your work before proceed with the scripts, this will put you safe of any trouble. Also, you would use git diff to give a look at the modifications.
