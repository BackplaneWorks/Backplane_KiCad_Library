# Reproducible passive libraries

The unmodified `upstream/` tree is a tracked-file snapshot of official KiCad
Library Tools commit `cb7f08bddfd922d9f2f1f476cf01962874156434`, recovered
from the user's `T3CAD_Example/tools/kicad-library-tools` checkout. It has no
`.git` directory. Licenses and original attribution are retained there.

`configs/sizes/` contains byte-for-byte copies of the original package YAML;
`global.yaml`, `package.yaml`, and `ipc7351B_2terminal.yaml` are also exact
copies from that commit. The three density YAML files select only resistor,
capacitor, and inductor groups without hand-solder pad extensions. They set
library IDs and descriptions, leaving original dimensions, paste rules, and
IPC references unchanged. Keeping the YAML here avoids modifying the upstream
snapshot. Do not install into or edit the recovered source projects.

From the library repository root:

```sh
uv venv sources/passives/build/venv
uv pip install --python sources/passives/build/venv/bin/python -r sources/passives/requirements.txt
sources/passives/build/venv/bin/python sources/passives/build_bundle.py
sources/passives/build/venv/bin/python sources/passives/verify_bundle.py --original sources/passives/recovered
```

The scripts import `upstream/src` and `upstream/KicadModTree` directly, so no
editable install or dependency build files belong in the source snapshot.
CPython 3.14.3 was used for the recorded generation. `build/` is disposable
and excluded. Run `verify_bundle.py --help` to select a different CLI path or
provide the optional recovered library directory for baseline comparison.

`build_bundle.py --output <directory>` generates into a separate directory.
Postprocessing changes only model references, or removes a model reference
when an exact-name body is unavailable. No pad, mask, paste, or courtyard
geometry is postprocessed. The same body STEP is shared across densities. The additional original local
0806 is copied geometrically unchanged into Least only, with a LegacyLocal ID;
`configs/legacy-local.yaml` records its source and model. It has no supported
nominal/most counterparts, yielding final counts 45/44/44 (133 total).

No model regeneration is required: the available STEP files, hashes,
attribution, and library license are bundled in `../../3dmodels`. Optional
upstream CadQuery dependencies are pinned separately in `requirements-3d.txt`
(resolved for CPython 3.11; `requirements-3d.in` records the upstream constraints).
A separate `uv venv --python 3.11 sources/passives/build/venv-3d` can be used with
that requirements file for future upstream model work. This delivery copies
existing models and does not claim to regenerate their historical STEP bytes.

Full package coverage, model limitations, installation variable, and measured
validation results are in `../../docs/passives.md`. SHA256 source, config,
and model manifests are retained for audit. Redistribution preserves upstream
GPL/LGPL/MIT notices for generator code and the KiCad CC-BY-SA 4.0 library
license with its design-use exception for library assets. Local integration
and verification scripts use GPL-3.0-or-later; see `upstream/LICENSE.GPL`.
