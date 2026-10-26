# Shoggoth artwork provenance and size variants

The source is the completed local artifact at
`/home/h/.backplane-bend/bots/b1790292962-8017/artifacts/shoggoth-badge/`, owned
by completed thread `t1793030485-604459`. Its two `.kicad_mod` files, raster,
editable vectors, original generator, original README and bundled font/license
are retained under `sources/shoggoth/original/`. The supplied raster's SHA256 is
`e5aaeef5fd9e0da4ccfe248fdb40e9ad5923e230ab9f6ce43a027e7c1ee8c30e`.
No image regeneration or redrawing was used.

`scripts/build_shoggoth.py` reads the original vector polygons and uses the
original polygon writer. It preserves both 35 mm library files byte for byte.
For 50 mm it scales the vectors, including the caption. The nominal 25 mm
variant only subtracts from the scaled original ink and copper: it applies a
0.15 mm diameter morphological opening to remove thin positive ink details,
enlarges three tiny negative eye details to at least 0.15 mm short caliper,
and restores the silk-to-mask gap in physical units. No ink is added to source
green/white areas. Cleanup removes approximately 5.27% of mascot ink area
(3.77% including badge lettering), mostly fine tips and raster-edge details.
The actual 25 mm width after cleanup is 24.9794 mm.

Both F.Cu and F.Mask use the same face polygons, with three enclosed holes for
the two eyes and smile. The 25 mm gap is about 0.11084 mm, original 35 mm gap
0.10952 mm and 50 mm gap 0.15645 mm. There is no F.Paste, pad, drill or net.
These are board-only footprints excluded from BOM and placement output.
Mask and copper outside the face are absent. The badge caption is outlined
geometry, so font installation is unnecessary.

Rounded tapered contours do not have one guaranteed minimum printable stroke.
The 0.15 mm morphology screen is not physical-process qualification. Review
the small eyes and tips in plotted output with the intended fab process. The
35 mm original retains its smallest enclosed negative detail, about 0.17995 mm.
Do not infer a finish from the illustrative gold face in the previews.

New-size polygons are rounded to KiCad's 1 nm coordinate grid, then repaired
if rounding would introduce a self-touching ring. This removes no meaningful
art detail; the fixed pieces are asserted to preserve area within 0.00001 mm²
per piece. The original 35 mm files bypass this derivation unchanged.

Rebuild and check on a host with system libpotrace and the pinned original
`sources/shoggoth/original/source/requirements.txt` installed:

```sh
uv run --no-project --python /usr/bin/python3 scripts/build_shoggoth.py
uv run --no-project --python /usr/bin/python3 scripts/verify_shoggoth.py
```

The local recorded run uses the system Python packages matching those pinned
versions. The verification script loads all six footprints through KiCad,
upgrades disposable copies, compares native roundtrip layer geometry, runs
DRC on individual experimental boards and plots Cu/Mask/Silk/Paste for each.
Cu and Mask rasters must match and Paste must be blank. It also checks that
derived artwork stays inside the scaled original within a 2 nm rounding
allowance. Actual measured differences are retained, rather than hidden by
that allowance, in `verification/shoggoth/verification-report.json`.
