# Verification record

Selected runtime: Backplane KiCad **10.99.0-bp.4**, source commit
`5dbc22d292704d02b609d5b7a0edc971f1b7f08b`, upstream
`fe761fb867a1c26e301c57d6da360867717757c7`. CLI version output is `10.99.0`.
All validation was performed locally; nothing was uploaded to a fab.

| Area | Recorded result | Evidence |
| --- | --- | --- |
| Footprint loading | All 199 entries loaded and exported as nonempty SVG by the selected CLI | `verification/holes/footprint-load/`, `verification/passives/svg/`, `verification/shoggoth/footprint-load/` |
| Original holes | 60 source hashes preserved, 60/60 exact regeneration with both original and bundled tools | `sources/holes/manifest.json`, `verification/holes/regeneration.json` |
| Hole behavior | 152 assertions across six saved 2/4-layer positive, negative and ablated-control boards | `verification/holes/results.json` |
| Hole copper | Tracks, vias, pads and filled zones checked on outer and internal layers; positive clearances pass and deliberately prohibited probes fail | `verification/holes/*.drc.json`, `*.cases.json` |
| Hole silk | Front/back mask-opening collisions detected in the tested runtime; documented as mask DRC behavior, not a silk keepout flag | `docs/holes.md` |
| Passives | 133 CLI loads, 133 byte-identical fresh rebuilds, 57 recovered original copper/courtyard geometry comparisons with no differences | `verification/passives/report.json` |
| IPC material settings | 44 complete triples have measured increasing pad/courtyard dimensions and stable inner gaps/body geometry | `verification/passives/measurements.csv`, `density-deltas.csv` |
| 3D bodies | 42 STEP models load with valid shapes in FreeCAD; bounding boxes/volumes measured; representative bodies rendered and inspected | `verification/passives/model-validation.json`, `3dmodels/` |
| Artwork | Six footprints load, native upgrade/roundtrip has zero layer geometry difference, all individual boards have zero DRC violations/unconnected items | `verification/shoggoth/verification-report.json` |
| Artwork layers | Six separate Cu/Mask/Silk/Paste plot sets; Cu/Mask raster equality and blank paste; three preserved face-mask holes | `verification/shoggoth/layers/`, `geometry-report.json` |
| Logos | 24 footprints load and plot; native upgrade roundtrip has zero geometry difference; every polygon simple and hole-free; no ink or gap under 0.15 mm; all parts and letter counters kept; Cu = Mask; back = mirrored front; one true-scale board with all 24 has zero DRC violations (KiCad 10.99.0-bp.12.1) | `verification/logo/verification-report.json`, `build-report.json`, `previews/logo/logo-sheet.png` |
| Saved catalogue | 56 top-level items imported through IPC, all `ISC_OK`, committed and saved at the canonical path; 4 copper layers read back | `verification/catalogue-ipc-save.json` |
| Catalogue DRC | Zero violations and zero unconnected items | `verification/catalogue-drc.json` |
| Catalogue schematic | Documentation-only schematic successfully exported by KiCad | `verification/catalogue-schematic/library_catalogue.svg` |
| Model resolution | All nine catalogue passive instances resolve their relative STEP paths in an actual component-inclusive KiCad STEP export | `verification/catalogue-step-export.log`, `catalogue-model-paths.json` |
| Local release | ZIP decompression and each archived file's SHA256 checked against the source files | `SHA256SUMS`, `release/*.sha256` |

No-net catalogue pads and floating artwork do not form a circuit; zero
unconnected items does not certify connectivity or electrical safety. Deliberate
hole test cells retain separately reported connectivity findings. Production
integration requires DRC with the destination board's rules and layer stack.
There is no IPC certification, fab approval, full KLC certification or physical
process qualification implied by these checks.

The initial small-artwork check caught one grid-rounded self-intersection,
which was repaired in the writer. The final reports are the passing runs.
All 35 mm artwork originals remain byte-identical. For the 50 mm trace, the
reported raw area outside an ideal scaled boundary is about 0.0001603 mm² of
silk, entirely within the 2 nm coordinate-rounding allowance; no meaningful
ink was added to protected colours. Curves and tips still need process review.

The catalogue bootstrap was a new empty file. Contents were imported from an
explicit disposable staging board through native `GetItems`/`CreateItems`,
wrapped in `BeginCommit`/`EndCommit`, followed by `SaveDocument`. The runtime's
`ParseAndCreateItemsFromString` returned no items and its library-content query
was unhandled, so neither was treated as a successful import. Fresh item IDs
permit atomic catalogue refreshes while old items await commit deletion.
Saved board bytes and path are read back; `viewer_show` uses that same canonical
path. Backplane's existing history and companion metadata are preserved.
`catalogue-viewer-history.json` records matching saved-board and history hashes.
The documentation-only schematic's Backplane history snapshot remains older
than the saved sheet, despite an explicit IPC commit/save and `viewer_show`.
The saved canonical schematic and its current CLI SVG show the final contents;
the ZIP includes those current files. This history mismatch is recorded rather
than silently assuming a refresh. Existing Backplane history was left intact.
The catalogue's nine model references use `${KIPRJMOD}/../../3dmodels/`; project
text variables alone did not resolve the reusable installation-variable paths
in KiCad's STEP exporter, so the instance references were corrected through
native IPC and saved. Library entries retain their documented installation
variable. No global path configuration was changed.

## Reproduce local integration

Installing the library needs no Python. For source rebuilds, use `uv`:

```sh
uv venv build/venv
uv pip install --python build/venv/bin/python -r scripts/requirements.txt
build/venv/bin/python scripts/build_shoggoth.py
build/venv/bin/python scripts/verify_shoggoth.py
```

System libpotrace and Cairo are also required by the original artwork tools.
Passive generation has its separate pinned environment and instructions in
`sources/passives/README.md`; hole tests use the standard library and selected
CLI. Generators and verification scripts default to the selected runtime's
local absolute path, so adapt that path on another host.

`build_catalogue.py` generates a disposable staging board only.
`ipc_catalogue.py` imports it into the canonical saved board with the project's
Backplane server running. It uses the selected runtime's own API descriptor
and the current workspace socket, so its socket path must be adapted when
rebuilding in a different workspace. `make_previews.py` uses saved CLI plots;
`package_library.py` excludes caches, virtual environments, intermediate builds,
history and release ZIPs, and never publishes anything.
