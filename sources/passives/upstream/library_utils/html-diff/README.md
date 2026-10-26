# Visual Library Diff

This directory contains a script that produces HTML-formatted diffs between two symbol or footprint libraries. For every
footprint or for every symbol it generates a single HTML file that contains:

* A textual diff of the library item's S-Expression source code.
* A render generated using `kicad-cli`.
* A visual diff between old and new version.
* For footprints, a slightly inaccurate preview with selectable layer visibility.

All renders are draggable and zoomable.

## Command-line usage

For complete command line usage, run:

```bash
python html_diff.py --help
```

### Example usage

One of the more command line usages is to compare the current working tree of a
git repository with the HEAD of the current branch. For example to regenerate
a batch of footprints and then compare the new versions with the old versions:

Regenerate the footprints:

```bash
python <path_to_kfg>/src/generator/generate.py -f <path_to_footprint_library> -g <generator_name>
```

Now the footprints are updated in the working tree. To compare the new versions with the old versions, run:

```bash
python html_diff.py --repo <path_to_footprint_library>
```