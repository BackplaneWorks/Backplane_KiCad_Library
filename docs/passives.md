# Passive footprint libraries

Three real KiCad footprint libraries contain 44 package IDs at three
material levels: 18 resistor, 14 capacitor, and 12 chip-inductor packages each.
Least also retains the original local 0806 inductor pattern, for final counts
of **45 least / 44 nominal / 44 most**, 133 footprints total. The names describe the **amount of land material**:
least is the compact option and most has the largest lands and courtyards.

| Library ID | Example full footprint ID |
| --- | --- |
| `Backplane_Passives_Least` | `Backplane_Passives_Least:R_0603_1608Metric` |
| `Backplane_Passives_Nominal` | `Backplane_Passives_Nominal:R_0603_1608Metric` |
| `Backplane_Passives_Most` | `Backplane_Passives_Most:R_0603_1608Metric` |

The libraries live in `libraries/<library ID>.pretty/`. Each density uses the
same footprint basename so applications can switch the library nickname
without rewriting package names. These are generator-derived choices, not
IPC certification or an assertion that every component with a matching
package code will fit. Verify the actual manufacturer's dimensions and
assembly process before choosing a land pattern.

## Recovery and provenance

The existing user's outputs were recovered from
`/home/h/.local/share/kicad/10.0/3rdparty/American_Embedded_KiCad_Library/footprints/`.
The installed `fp-lib-table` names `amemb-Resistor_SMD.pretty`,
`amemb-Capacitor_SMD.pretty`, and `amemb-Inductor_SMD.pretty`. Existing `_L`
footprints explicitly describe the least material choice; the inductor `_M`
footprints explicitly describe most. All 145 original passive output files (including 88 historical hand-solder files
and the additional local 0806 inductor) are retained under
`sources/passives/recovered/`, with origin paths and SHA256 hashes in
`original-outputs.json`. Hand-solder footprints in the installed library are
separate elongated-pad variants and are not relabeled as density levels.

Official generator checkouts were found at:

- `/home/h/Documents/i2cjak/T3CAD_Example/tools/kicad-library-tools`, commit
  `cb7f08bddfd922d9f2f1f476cf01962874156434` (selected).
- `/home/h/Documents/i2cjak/SMU_Business_Card/extra/references/kicad-library-tools`,
  commit `36d1ed208379d7c4127661ac384118cc6837392b` (corroborating copy).

The selected checkout was clean. Its origin is the official
[KiCad Library Tools repository](https://gitlab.com/kicad/libraries/kicad-library-tools).
The tracked source tree, all licenses and original attribution, package YAML,
IPC rule YAML, global style configuration, scripts, pinned Python requirements,
and source/config SHA256 manifests are bundled in `sources/passives/`.
The snapshot contains 1,579 tracked files, without `.git` or a virtual environment.
The historical source library at `/home/h/Documents/KiCad_Library/` also
contains those nominal hand-solder outputs byte-for-byte and its table names
the same three passive families. The exact historical generation command/commit
is not asserted: this
recovered official commit reproduces every matching generated original's copper-pad and courtyard geometry exactly
(56 generator comparisons, zero differences), plus preserves the 57th local
0806 pattern unchanged geometrically.

Generation calls the existing `SMD_2terminal_chip_molded` generator with its
original size data and `ipc7351B_2terminal` rule table. No new generator or
post-generation pad scaling was introduced. Local changes select groups,
output library names, descriptions, and density; postprocessing only redirects
3D references or removes an unavailable model reference. Source projects,
global tables, and Git configuration were not changed.

## Coverage

Imperial codes are listed below; the exact metric codes are in the stable IDs
and the bundled YAML. This preserves the recovered generator's package
coverage, including its existing wide-body resistor types. It adds no new
package dimensions. The additional original `L_0806_2016Metric_LegacyLocal` is
retained in Least only: its original description calls it a local least land
pattern. No body/termination tolerance YAML was recovered, so nominal and most
variants cannot be derived responsibly. Its original pads are 0.8 × 1.7 mm
at X = ±0.65 mm; the courtyard is 2.6 × 2.2 mm. This exception is excluded from
the 44 density-triple comparisons and from the generator-derived counts below.

| Type | Package codes | Per library |
| --- | --- | ---: |
| Resistor | 01005, 0201, 0402, 0508, 0603, 0612, 0805, 0815, 1020, 1206, 1210, 1218, 1225, 1812, 2010, 2512, 2816, 4020 | 18 |
| Capacitor | 01005, 0201, 0402, 0504, 0603, 0805, 1206, 1210, 1808, 1812, 1825, 2220, 2225, 3640 | 14 |
| Chip inductor | 01005, 0201, 0402, 0603, 0805, 1008, 1206, 1210, 1806, 1812, 2010, 2512 | 12 |

These are generic two-terminal rectangular packages. Tantalum capacitors,
electrolytics, power-inductor vendor packages, arrays, and hand-solder variants
are outside these three libraries. Inductors are included because the existing
generator and original installed outputs already cover them.

## Density settings and measured deltas

The recovered rule table uses these toe, heel, side, and courtyard goals in mm.
The original generator applies dimensional tolerances with root-sum-square
calculations and rounds using the rule table; these are not uniform scale
factors. Placement tolerance is 0.05 mm and manufacturing tolerance 0.10 mm.

| Rule class | Material | Toe | Heel | Side | Courtyard |
| --- | --- | ---: | ---: | ---: | ---: |
| Below 0603 | Least | 0.10 | 0 | -0.05 | 0.10 |
| Below 0603 | Nominal | 0.20 | 0 | 0 | 0.15 |
| Below 0603 | Most | 0.30 | 0 | 0.05 | 0.20 |
| 0603 and larger | Least | 0.15 | 0 | -0.05 | 0.10 |
| 0603 and larger | Nominal | 0.35 | 0 | 0 | 0.25 |
| 0603 and larger | Most | 0.55 | 0 | 0.05 | 0.50 |

Individual package YAML can override the class: for example 0402 uses the
smaller class even though it is in the main resistor/capacitor group. The
01005/0201 paste-only apertures retain the original relative reduction and
heel adjustment. Mask openings follow the copper pads with no local expansion
override; actual mask clearance also depends on board/fab settings.

Example measurements from the saved R_0603_1608Metric footprints:

| Material | Pad X × Y (mm) | Center spacing (mm) | Inner gap (mm) | Courtyard X × Y (mm) |
| --- | --- | ---: | ---: | --- |
| Least | 0.60 × 0.85 | 1.45 | 0.85 | 2.26 × 1.06 |
| Nominal | 0.80 × 0.95 | 1.65 | 0.85 | 2.96 × 1.46 |
| Most | 1.00 × 1.05 | 1.85 | 0.85 | 3.86 × 2.06 |

All 44 package triples have increasing pad X, pad Y, center spacing, outer
span, and courtyard X/Y. The inner copper gap and body fabrication rectangle
remain unchanged. Full measurements and adjacent-level deltas are in
`verification/passives/measurements.csv` and `density-deltas.csv`.

## Portable 3D bodies

Set the KiCad path variable **`BACKPLANE_KICAD_LIBRARY`** to the absolute root
of the installed Backplane library. Every model reference uses:

```text
${BACKPLANE_KICAD_LIBRARY}/3dmodels/<family>.3dshapes/<package>.step
```

Set this installation variable manually in KiCad for destination projects.
The bundled catalogue instances instead use `${KIPRJMOD}/../../3dmodels/`
to resolve their models without global configuration. The reusable library
entries retain the installation-variable references.
No global path variables or library tables were changed here.

41 exact-name generic STEP models are bundled once and reused by all three
material levels, plus the original local 0806 pattern's referenced
`L_Changjiang_FTC201612S.step`: **42 STEP files total**. All use identity scale,
rotation, and offset. They came from the local
`kicad-packages3d` package `10.0.7~ubuntu26.04.1`; source paths and SHA256 hashes
are in `3dmodels/passives-provenance.json`. Its license and family credits are
retained. No corresponding WRL files were available in that source.

R_0508_1220Metric, R_1225_3264Metric, and C_0504_1310Metric have no exact-name
available STEP body. Their nine footprints intentionally contain no model
reference. Generic bodies are visualization aids: heights and end-terminal
geometry do not establish a vendor-specific mechanical fit.

All 42 STEP files load in FreeCAD and have valid non-null shapes; measured
bounding boxes, volumes, and solid counts are in
`verification/passives/model-validation.json`. Representative resistor,
capacitor, and inductor 0603 models were rendered through Backplane's renderer
and visually inspected. For example R_0603 is 1.6 × 0.8 × 0.45 mm, and C/L_0603
are 1.6 × 0.8 × 0.8 mm. These are measured model dimensions, not guaranteed part
heights.

## Rebuild and verification

See `sources/passives/README.md` for `uv` setup and exact commands. Runtime
requirements are pinned; optional upstream 3D-generation requirements are
provided separately. Dependencies and intermediate rebuilds belong in
`sources/passives/build/`, excluded from source/release assets.

The recorded validation uses Backplane KiCad 10.99.0-bp.4's selected CLI
(`/home/h/.backplane-bend/kicad/10.99.0-bp.4/bin/kicad-cli`; version output
`10.99.0`). `fp export svg` loaded every saved footprint and produced 133
nonempty, XML-parseable SVGs. Logs and SVGs are in `verification/passives/`.
Representative R_0603 SVGs at all levels were rasterized and visually inspected.
Independent saved-file checks verify IDs, two symmetric copper pads, layer
membership, positive dimensions, courtyard containment, model path resolution,
identity transforms, and the density/body invariants described above.
A fresh-directory rebuild reproduces all 133 footprint files byte for byte;
`report.json` includes their SHA256 hashes. Source/config hashes and recovered
original/model hashes also pass. The final run used a clean `uv` environment
installed solely from the bundled requirements and compared against the
bundled original footprint snapshots, without depending on a source checkout
or the installed original library.

This validates loading, geometry, and reproducibility. It is not an electrical
DRC, assembly qualification, IPC certification, or exhaustive KLC certification.
The original generic package tolerance assumptions, tiny-package paste
apertures, and upstream silkscreen widths remain unchanged. In particular the
upstream 0.12 mm silk may need fab-specific checking for a process requiring
0.15 mm silk. Choose the actual component and process before production use.

Generator source remains under the bundled upstream GPL/LGPL/MIT licenses;
library assets and 3D bodies retain the KiCad CC-BY-SA 4.0 license with its
design-use exception (`3dmodels/LICENSE.md`). Preserve these notices when
redistributing the collection.
