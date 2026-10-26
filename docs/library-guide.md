# Backplane KiCad Library

A portable, project-local collection of **199 reusable footprints in five libraries**.
Open `boards/library_catalogue/library_catalogue.kicad_pro` for a saved visual
showcase. The catalogue has no circuit and is not intended for manufacture.
No symbol library is needed for these footprints.

| Library nickname | Contents | Count |
| --- | --- | ---: |
| `Backplane_MountingHole` | Original exposed-substrate NPTH holes; 20 named sizes × center/edge/corner | 60 |
| `Backplane_Shoggoth` | Mascot and caption badge, nominal 25/35/50 mm | 6 |
| `Backplane_Passives_Least` | 18 resistor, 14 capacitor, 12 chip-inductor packages + original local 0806 | 45 |
| `Backplane_Passives_Nominal` | Same packages, nominal material settings | 44 |
| `Backplane_Passives_Most` | Same packages, most material settings | 44 |

## Install

1. Extract the release ZIP to a permanent folder; keep `libraries/` and
   `3dmodels/` together.
2. In KiCad, use **Preferences → Configure Paths** to define
   `BACKPLANE_KICAD_LIBRARY` as that folder's absolute path. This resolves the
   passive STEP bodies. The bundled catalogue uses paths relative to its own project
   folder and requires no global changes.
3. In **Manage Footprint Libraries → Project Specific Libraries**, add each
   desired `.pretty` folder from `libraries/`, using the nicknames above.
   Alternatively merge the entries from `fp-lib-table.example` into the
   destination project's table. Preserve that project's existing entries.
4. Place, for example,
   `Backplane_MountingHole:MountingHole_3.2mm_M3_ExposedSubstrate_Corner`,
   `Backplane_Shoggoth:Shoggoth_Badge_35mm`, or
   `Backplane_Passives_Least:R_0603_1608Metric`.

Changing the passive library nickname selects another density while preserving
the package basename. Check the actual component dimensions before choosing a
land pattern. Existing board instances do not update themselves when a library
file changes; use KiCad's normal update-from-library workflow.

The delivered footprints use KiCad 8-era artwork syntax or the original
20260206 generator syntax. The complete collection was tested in **Backplane
KiCad 10.99.0-bp.4**, source `5dbc22d292704d02b609d5b7a0edc971f1b7f08b`.
The saved catalogue uses that runtime's newer native format; older KiCad
versions are not asserted compatible with the complete bundle.

## What the holes keep clear

The original hole files are byte-identical imports, including their names.
An unnamed NPTH with local clearance excludes copper around the circular
opening on enabled copper layers. Edge/corner versions add an explicit
`*.Cu` rule-area extension prohibiting tracks, vias, pads and copper pours.
Their enlarged front/back mask openings expose the substrate.

There is **no universal silkscreen keepout flag**. Mask-opening collisions are
detected by the tested runtime's enabled silkscreen DRC, and plotting can clip
silk with **Subtract soldermask from silkscreen**. Comment and courtyard outlines
do not enforce a silk prohibition. Keep the relevant DRC checks enabled and
inspect plotted output. See [the hole guide](holes.md) for the measured
clearances, orientations and two-/four-layer negative/control experiments.

## Shoggoth artwork

Original black regions map to F.SilkS. The yellow face maps to F.Cu and an
identical F.Mask opening; mask islands remain under its facial silk. Source
green and white regions get no added geometry. There is no paste or electrical
pad. The caption is exactly **THIS PCB WAS DESIGNED BY AN EVIL SHOGGOTH**.

The original 35 mm files are preserved byte for byte. The 50 mm versions are
derived from those vectors. The nominal 25 mm version has 0.15 mm detail
screening and enlarged tiny eye openings; cleanup makes its actual width
approximately **24.979 mm**. It is deliberately not a blind scale reduction.
All sizes retain at least 0.109 mm silk-to-mask clearance. Tapered artwork still
needs process-specific review. See [artwork details](shoggoth.md).

The face copper is floating decorative artwork. Keep it clear of real circuit
copper and check DRC in the destination design.

## Passive density and 3D models

The official generator's IPC-7351B rule table calculates each density from the
same source package tolerances. These are genuine generator settings, not
scaled pads or IPC certification. Existing recovered copper/courtyard geometry
was matched where originals were available. The original 0.12 mm silk and
small-package paste choices are retained and require assembly-process review.

**42 shared STEP bodies** cover 124 of the 133 passive footprints. Exact-name
bodies were unavailable for `R_0508_1220Metric`, `R_1225_3264Metric`, and
`C_0504_1310Metric`; those nine density entries have no model reference.
The original local 0806 inductor is retained in Least only as
`L_0806_2016Metric_LegacyLocal`; nominal/most settings have no proven source
and are not invented. Generic models illustrate the package and do not establish a vendor-specific
height or fit. See [coverage, measured deltas and rebuild commands](passives.md).

## Browse, rebuild, verify

- `previews/catalogue.png`: overview; `previews/footprint-index.png`: full visual index.
- `CATALOGUE.csv` and `manifest.json`: stable IDs, counts and saved-file hashes.
- `boards/library_catalogue/`: canonical saved showcase, local library table and
  relative model references; this is a reference, not an orderable PCB.
- `sources/`: original artwork/generators, recovered outputs, YAML, configs,
  pinned dependencies, provenance and retained licenses.
- `scripts/`: artwork derivation, catalogue staging/import, verification and packaging.
- `verification/`: native KiCad exports, DRC experiments and numerical reports.

Read [verification results](verification.md) and [license boundaries](../LICENSES.md).
No global library tables or source boards were changed. The repository is published under BackplaneWorks for distribution with
Backplane. No manufacturing order or fab upload is part of this project.
