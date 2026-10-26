# Authored exposed-substrate mounting holes

`Backplane_MountingHole.pretty` contains the 60 existing authored footprints,
copied byte for byte from
`/home/h/Documents/KiCad_Library/footprints/amemb-MountingHole.pretty`.
Original names, description strings, geometry, pad clearances and rule flags are
preserved. This is a reusable library, not an orderable board. No generic hole
has been substituted, and there are no invented sizes.

## Inventory and provenance

The active `~/.config/kicad/10.0/fp-lib-table` delegates to
`/home/h/Documents/KiCad_Library/fp-lib-table`. Its `amemb-MountingHole` entry
resolves to the source directory above. The similarly named installed directory
under `~/.local/share/kicad/10.0/3rdparty/American_Embedded_KiCad_Library/footprints/`
contains only `.gitkeep`, not the authored holes.

The source family has 20 named sizes, each with center, `_Edge`, and `_Corner`
variants (60 files). Both `MountingHole_2.7mm` and `MountingHole_2.7mm_M2.5` are
intentional existing names with the same drill. The sizes in mm are 2, 2.1,
2.2 M2, 2.5, 2.7, 2.7 M2.5, 3, 3.2 M3, 3.5, 3.7, 4, 4.3 M4, 4.5, 5,
5.3 M5, 5.5, 6, 6.4 M6, 6.5 and 8.4 M8.

`sources/holes/manifest.json` records each exact source path, destination,
SHA-256, measured drill, clearance and variant. `inventory.json` records the
235 hole-named footprint candidates found by an ignore-independent scan of
Backplane, i2cjak and the installed library. Six candidates are copies of this
authored family. The current Phaser M2 corner copy is byte-identical to its
source; the GateLatch M2.5 corner is likewise checked against this family.
Other candidates include generic holes, vendor/demo footprints, and unrelated
mounting hardware; they are inventoried but not silently included here.

The source YAML and custom generator are bundled unchanged in
`sources/holes/original/`. The YAML pins the upstream generator data to
`9d5b3f76364cfd307ec06d2137f387d18b6768a0`; the local upstream checkout has
that exact HEAD. `hole_sizes.yaml` is bundled as supporting provenance.
`source-hashes.json` hashes those supporting files. The custom generator, YAML
and all 60 source footprints are **untracked** in the local source repository;
the repository HEAD is not a content revision for them. Hashes identify the
actual imported files.

The source generator was also run against its pinned upstream checkout into
`verification/holes/build/regenerated.pretty`: all 60 regenerated files are
byte-identical to the imported originals (`verification/holes/regeneration.json`).

## Mechanical and layer behavior

For drill diameter `d`, the source has one unnamed circular **NPTH** pad at the
origin, pad size `d × d`, drill `d`, on `*.Cu` and `*.Mask`. There is no plated
barrel, copper annulus or electrical pad number. The footprint excludes itself
from BOM and placement output. Do not convert this to a plated mounting pad.

The circular mask-opening radius is `d` (diameter `2d`), on both `F.Mask` and
`B.Mask`. Filled mask-layer graphics mean **mask openings**, not applied mask.
The local NPTH clearance is `d/2 + 0.2 mm`, producing a circular copper-exclusion
radius `d + 0.2 mm`. In the tested runtime this clearance rejects tracks,
vias and pads and clips zone fills on internal as well as external copper.

Center has no explicit rule-area zone. Edge and corner each add the original
`Copper keepout extension` zone on `*.Cu`, with exactly these flags:

```
(tracks not_allowed)
(vias not_allowed)
(pads not_allowed)
(copperpour not_allowed)
(footprints allowed)
```

Placement is disabled: `(placement (enabled no) (sheetname ""))`. Therefore this
is a copper restriction, not a ban on placing an entire footprint. Its pads can
still violate the copper rule. The NPTH local clearance covers the circular
part and the rule area covers the extension; they work together.

The edge mask region extends toward +X to `d + 5 mm`; the corner extends toward
+X and +Y to `d + 5 mm`. Their copper extensions reach `d + 5.2 mm`.
The original polygon vertices, including arc tessellation and the cutout around
the circular NPTH-clearance region, are retained exactly. Rotate the footprint
to point the extension at the intended edge(s). These footprints do not create
an Edge.Cuts outline or position a hole relative to one.

`*.Cu` follows the enabled copper stack. Do not replace it with a fixed list of
inner layers or assume the native layer numbers are stable between file
versions. The experiments cover F.Cu/B.Cu and F.Cu/In1.Cu/In2.Cu/B.Cu. Additional
layer counts, blind/buried vias and future runtime versions are not asserted as
tested. Refill zones and run DRC after changing a board's stack.

## Silk exclusion: exact mechanism and limits

There is **no silk-specific keepout flag** in these files. `Cmts.User` is an
outline marking the exposed region, not an enforceable silk prohibition.
`F.CrtYd` is the original courtyard and is not a silk keepout either. The visible
reference is positioned outside the circular opening; the generator property
at the origin is hidden. The original names and graphics remain untouched.

The enlarged F.Mask/B.Mask openings provide the useful silk-exclusion mechanism
when the board's silkscreen-to-mask checks are enabled. In Backplane KiCad
10.99.0-bp.4, a 0.15 mm silk line inside the extension, away from the physical
drill, triggers `silk_over_copper` on both sides. Despite that DRC identifier,
the experiment has no copper there: the collision is with the exposed mask
opening. The equivalent outside line passes. See the reports and the separate
front/back silk cases in `verification/holes/`.

This is a tested DRC behavior, not an absolute manufacturing guarantee or a
new no-silk rule. Suppressing that check or using another KiCad version may
change the result. `--subtract-soldermask` is an optional export clipping
operation, distinct from DRC, and must be explicitly selected if desired.
Inspect final silk/mask fabrication output; do not assume comment graphics or
copper keepouts remove silk automatically.

## Verification

Run from the library root:

```
uv run --no-project verification/holes/verify.py
```

The script uses only the Python standard library and the selected CLI at
`/home/h/.backplane-bend/kicad/10.99.0-bp.4/bin/kicad-cli`. It creates standalone
**experimental** boards only under `verification/holes/`; these are not source
boards or canonical projects. A local `fp-lib-table` resolves the preserved
library without changing any global tables. No schematic is implied.

Before bootstrap, both `kicad_ipc_status` and a `GetItems` request were attempted
against the explicit experimental board path. Both refused with
`no KiCad project (.kicad_pro) found`. Because IPC was unavailable for these
standalone experiments, fixture files were generated directly and then
re-read, refilled and saved by the selected CLI. The exact request/error is
recorded in `verification/holes/ipc-check.json`. No project selector or canonical
board was created or changed.

Each 2/4-layer positive and negative board embeds the exact M2 center, edge and
corner geometries. Positive tracks/pads/vias sit outside the exclusion; negative
ones are deliberately inside it. Tracks are connected loops on a real test net
so no-net shortcuts cannot make a clearance test vacuous. Through vias are
tested, and internal pad probes are plated through pads with real internal
copper, not invalid internal-only SMD pads. Independent cells isolate the cases.

Zones are refilled and saved using `pcb drc --refill-zones --save-board`.
Assertions examine the saved fill polygons: the circular region and extension
must be empty while outside copper remains. The two `zone_control` boards are
explicit ablations: they disable the embedded copy's NPTH clearance and remove
its extension rule area. The same samples must then contain copper. Only those
experimental embedded copies are altered; library files remain byte-identical.

The positive boards have zero `violations`. Negative 2-layer probes produce
`items_not_allowed`, `hole_clearance`, and `silk_over_copper`. Negative 4-layer
probes also produce `pth_inside_courtyard` because deliberate internal-layer
pad intrusions are PTH probes. The ablated controls intentionally produce
`lib_footprint_mismatch`, proving that their embedded copies were modified.
No unexpected DRC violation type is accepted by the script.

DRC JSON stores connectivity findings separately under `unconnected_items`:
the independent mechanical test cells deliberately do not form a complete
circuit. Their count is recorded separately and is not claimed to pass circuit
connectivity validation. This is not a production-board release review.

`results.json` contains every assertion and saved-board hash; `*.cases.json`
maps probes to stable UUIDs; full `*.drc.json` and `*.drc.log` files retain the
CLI evidence. `representative-mask.svg` and `.png` show the center, edge and
corner mask regions and were visually inspected. There is no component body
to model: this is NPTH substrate removal, represented by the drill in 3D.
The completed run has 152 passing assertions across six boards.

## License status

No license was found for the original custom generator/YAML/footprints in
`/home/h/Documents/KiCad_Library`, and their untracked status provides no
historical license grant. The project owner has requested publication under BackplaneWorks and bundling
with Backplane. No separate general public license has been selected for this
custom material; the publication request does not replace upstream notices.
Publication and Backplane bundling are explicitly requested by the project
owner; original notices remain intact.

Upstream generator data is GPL-3.0-or-later according to its bundled README;
the upstream GPL, LGPL and MIT notices are preserved in `sources/holes/licenses/`.
The separate KiCad Libraries license/exception notice is also bundled for
provenance, without claiming it automatically licenses the author's custom
work. `sources/holes/LICENSE-STATUS.md` identifies this boundary.
