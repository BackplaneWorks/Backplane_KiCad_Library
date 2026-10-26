# Rebuild original hole footprints using the bundled tools

The unchanged custom generator and YAML live in `original/`. The YAML records
the historical supporting data revision
`9d5b3f76364cfd307ec06d2137f387d18b6768a0`; the recorded original-checkout
regeneration in `../../verification/holes/regeneration.json` matches all 60 files.

For a completely local rebuild without that external checkout, the bundled
official Library Tools snapshot at `../passives/upstream/`, pinned to
`cb7f08bddfd922d9f2f1f476cf01962874156434`, was independently verified to
produce the same 60 bytestrings. Its serializer and dependency pins are already
bundled for the passive libraries. No second checkout or network access is
required after Python dependencies are installed.

From the library root:

```sh
uv venv build/holes-venv
uv pip install --python build/holes-venv/bin/python -r sources/passives/requirements.txt
build/holes-venv/bin/python sources/holes/original/generate_exposed_substrate_mounting_holes.py \
  --definitions sources/holes/original/mounting_hole_exposed_substrate.yaml \
  --tools sources/passives/upstream \
  --output build/regenerated-holes
```

Compare the output to `libraries/Backplane_MountingHole.pretty/` and the hashes
in `manifest.json` before replacing library files. Keep rebuild outputs in
`build/`; regeneration does not need to edit existing boards or global tables.
The exact local comparison is retained in
`../../verification/holes/bundled-tools-regeneration.json`.

Read `LICENSE-STATUS.md` and `../../docs/holes.md` for provenance, licensing,
layer behavior, mechanical assumptions and experiment results.
