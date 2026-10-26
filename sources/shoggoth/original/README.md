# Shoggoth PCB artwork

Standalone decorative KiCad footprint library, vector-traced from the supplied
mascot raster. The silhouette, tentacles, eyes and smile come from the original
image, not an AI redraw. The supplied board badge guides the bold caption style;
its other marks are not included.

The caption is exactly:

**THIS PCB WAS DESIGNED BY AN EVIL SHOGGOTH**

It appears as two lines of outlined bold lettering, with 1.850 mm capital height.

## Included footprints

| Library entry | Artwork width | Artwork height |
|---|---:|---:|
| `ShoggothBadge:Shoggoth_Badge_35mm` | 35.000 mm | 33.909244 mm |
| `ShoggothBadge:Shoggoth_Mascot_35mm` | 35.000 mm | 28.759244 mm |

These dimensions exclude hidden reference/value text. Both use the mascot's
centre as their origin. In the complete badge, the caption extends downward.
There is no 25 mm variant: reducing the smallest retained details further would
make their reproduction less reliable.

## Layers and geometry

- **F.SilkS:** all original black regions, plus the complete badge's caption.
  The ink colour comes from the board's silkscreen process. The PCB previews use
  light ink to match the reference board's appearance.
- **F.Cu:** only the inset yellow face, as real filled copper graphics.
- **F.Mask:** exactly the same shape as F.Cu, creating the face opening. Three
  holes preserve solder-mask islands beneath its two black eyes and smile.
  Measured silk-to-opening clearance is at least 0.1095 mm.
- **Green body and white source areas:** no art geometry, copper or mask opening.
  The PCB's existing solder mask shows through. The footprint does not paint a
  green body or a background rectangle. Traced ink is clipped to the original
  classified black pixel cells to prevent colour-boundary overshoot.
- **F.Paste:** no geometry. No pads, pins, nets, drills or courtyard are present.
  Reference and value are hidden on F.Fab. The footprint is board-only and is
  excluded from the BOM and placement files.

The yellow source colour means exposed metal, whose actual colour depends on
the chosen board finish. A gold-coloured preview does not specify that finish.
The face copper is deliberately electrically unconnected artwork. It has no net
assignment or automatic keepout; maintain clearance from actual board copper.

KiCad filled polygons use simple contours. Enclosed holes are preserved by
decomposing those shapes into adjacent simple polygons, with their union checked
against the original traced geometry. No overlapping fill is used to fake a hole.
Some SVG rasterizers show hairline antialias seams between touching pieces; those
shared boundaries are not designed slots in the copper or ink.

## Import into KiCad

1. Extract the ZIP and keep `ShoggothBadge.pretty` together as a folder.
2. In the PCB Editor, open **Preferences → Manage Footprint Libraries**.
3. On **Project Specific Libraries**, add the existing `ShoggothBadge.pretty`
   folder and use the nickname `ShoggothBadge`.
4. Use **Place Footprint** and select `Shoggoth_Badge_35mm` or
   `Shoggoth_Mascot_35mm`. Place it on the front of the board.
5. Inspect F.SilkS, F.Cu and F.Mask, and run DRC on the destination board.

The `.kicad_mod` files are also directly openable in KiCad's Footprint Editor.
No global library table or existing user project was modified to create this
bundle. The disposable boards under `verification/` are examples for inspection,
not manufacturing designs.

## Verification and practical limits

Verified with the selected Backplane KiCad **10.99.0-unknown-bp.4** runtime.
The deliverable footprints use stable **20240108** native syntax. KiCad loaded
both footprints, exported them, saved disposable round-trip copies and reloaded
those copies. Layer geometry was compared numerically across the round trip.
The newer-format temporary copies were then removed; the delivered library's
format and hashes remained unchanged.

Both disposable boards have **zero reported DRC violations and zero unconnected
items**. The latter does not mean that the decorative copper has been connected
to a net. Geometry checks confirm three face holes, identical copper/mask shapes,
no copper outside the yellow face, no silk/opening intersection and no paste.
The actual KiCad copper and mask raster exports are pixel-identical.

The smallest enclosed negative eye detail has a short caliper of approximately
**0.17995 mm**. Curved edges and tapered tips do not have one guaranteed minimum
stroke width. They were retained for fidelity, and a morphological 0.15 mm
feature screen is recorded in `verification/verification-report.json`.
DRC does not certify these filled artwork details for a particular printing
process. Confirm reproduction of the fine eyes, tapered tips and narrow gaps
with the fab when integrating the badge. This bundle is not a physical process
qualification or an order-ready circuit board.

The final source-pixel screen checks 373,737 body-green pixel centres and 786,368
white pixel centres against the delivered mascot geometry: **zero intrusions**
in either set. This screen excludes the caption, which sits below the mascot.

## Files and editable sources

- `ShoggothBadge.pretty/`: the two importable `.kicad_mod` files.
- `source/Shoggoth_Badge_35mm.svg` and `source/Shoggoth_Mascot_35mm.svg`:
  editable millimetre-scale vectors, with separated copper, mask and silk groups.
  The duplicate mask group is hidden for comfortable editing. Caption outlines
  do not require font installation.
- `source/generate_badge.py`: deterministic raster classification, Potrace curve
  tracing, outline lettering and KiCad generation.
- `source/verify_badge.py`: supported KiCad CLI load/export/round-trip checks,
  parsed geometry checks and preview generation.
- `source/parameters.json`: exact caption, scale, trace parameters and input hash.
- `source/mascot-original.png`, `source/style-reference.png`: supplied references.
- `source/caption-font.ttf` and `source/caption-font-LICENSE.txt`: exact font and
  its original license notices for reproducible regeneration.
- `previews/Shoggoth_Badge_35mm-kicad-composite.png`: actual KiCad layer exports
  composited in illustrative PCB colours, explicitly labelled as a preview.
- `verification/layers/*.svg` and `previews/*-F_*.png`: actual KiCad per-layer
  plots and their rasterizations. The blank F.Paste plot is intentional.
- `previews/actual-size-proof.pdf`: physical-size artwork and a 10 mm scale.
  Print at **100%**, with page fitting disabled. Screen display size varies.
- `verification/`: disposable test boards/projects, CLI logs, DRC reports,
  original/round-trip footprint SVGs and measured geometry reports.

To rebuild on a host with the same tools:

```sh
uv run --no-project --python /usr/bin/python3 source/generate_badge.py
uv run --no-project --python /usr/bin/python3 source/verify_badge.py
```

Dependencies are the system `libpotrace`, Pillow, Shapely 2.1+, NumPy, fontTools
and CairoSVG, plus the KiCad CLI path named in `source/verify_badge.py`.
The bundled raster and font sources allow regeneration without the original
attachment paths. Editing SVG paths alone does not automatically update the
footprint; the generator and geometry checks are included for controlled changes.
