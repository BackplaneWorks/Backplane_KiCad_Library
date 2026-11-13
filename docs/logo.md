# Backplane logo footprints

`Backplane_Logo.pretty` holds the Backplane mark and the mark + "backplane"
wordmark lockup, generated from outlined brand SVGs (`sources/backplane_logo/`).
The wordmark is glyph outlines, never a KiCad text item or font.

| Variant | Widths (mm) | Name |
| --- | --- | --- |
| Mark | 3, 5, 8, 12, 20, 30 | `Backplane_Logo_Mark_<w>mm_<layer>` |
| Mark + wordmark, horizontal | 20, 30 | `Backplane_Logo_Text_<w>mm_<layer>` |

Each comes in three layer versions:

- `_SilkS`: front silkscreen.
- `_SilkS_Back`: back silkscreen, stored mirrored so it reads correctly from
  the back. Place it on the front side; it draws on B.SilkS only.
- `_Cu`: front copper with an identical front mask opening (an exposed-finish,
  e.g. ENIG "gold", logo). The copper floats with no net; keep it clear of
  circuit copper.

The width is the overall ink width. No pads, paste, courtyard or 3D model;
attributes are board-only, excluded from BOM and position files. There is no
schematic symbol: like the rest of this library, these are placed on the board.

## Printability

Every footprint has no ink and no gap narrower than **0.15 mm**: the fab's
free-tier silkscreen minimum line width (`fab_profile` `silk_line_min`,
<https://jlcpcb.com/capabilities/pcb-capabilities>, read 2026-11-13). The same
geometry is used for copper and mask, above their 0.10 mm minimums.
`scripts/build_logo.py` gets there per size, all of it recorded in
`verification/logo/build-report.json`:

1. The mark's edge highlights (thin bars beside a hairline slot) merge back
   into their slabs below about 7 mm, keeping the slab outlines.
2. Thin strokes, e.g. the frame at 3 mm and in the 20 mm lockup, are thickened to 0.15 mm.
3. Ink traps and notches that can be filled without joining parts are filled.
4. The gaps that separate slabs are opened to 0.15 mm by insetting the slabs
   uniformly (0.0675 mm at Mark 3 mm, 0.0525 mm in Text 20 mm).

A size is generated only if every part and letter counter survives and no edge
moves more than 0.45 mm. The lockup fails below about 16 mm: at 12 mm its mark
is under 2 mm wide and letter apertures are under 0.15 mm, so Text 12 is
skipped (recorded in the report). 16 mm passes the checks but its mark loses a
slab corner, so the smallest lockup is 20 mm. Above 7 mm the mark keeps its
highlights; 30 mm and the 30 mm lockup are essentially the unaltered artwork.

## Rebuild and verify

```sh
python3 scripts/build_logo.py          # writes libraries/Backplane_Logo.pretty
python3 scripts/build_logo.py --sizes 16,25   # try sizes in /tmp first
python3 scripts/verify_logo.py         # needs kicad-cli (or BACKPLANE_KICAD_CLI)
```

To add a size, add it to `SIZES` in `build_logo.py`, rebuild, verify and look
at `previews/logo/logo-sheet.png`. Needs `shapely` 2.1+, `numpy`, `cairosvg`, `Pillow`.

`verify_logo.py` loads every footprint through KiCad, upgrades and re-reads
them (zero geometry difference), checks every polygon is simple, hole-free and
on the 1 nm grid, re-checks the 0.15 mm minimum, part and counter counts,
Cu = Mask and back = mirrored front, then places all of them at true scale on
`verification/logo/logo_test.kicad_pcb`, runs DRC (zero violations) and plots
the native layers into the preview sheet.
