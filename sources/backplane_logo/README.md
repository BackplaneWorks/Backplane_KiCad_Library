# Backplane logo sources

Paths only: no font and no live text. `scripts/build_logo.py` reads nothing else.

| File | From |
| --- | --- |
| `backplane-mark.svg` | `Backplane.Works/brand/backplane-mark.svg`, unchanged (same path as `static/backplane.svg` and the app's `assets/icon/mark.svg`) |
| `backplane-lockup-horizontal.svg` | The horizontal lockup of `Backplane.Works/brand/backplane-x-banner.html`, outlined by `outline_wordmark.py` |

The banner sets "backplane" in Berkeley Mono (the site's own
`static/fonts/berkeley-mono-variable.woff2`) at weight 500, 150 px, line-height 1,
letter-spacing -0.055em, 44 px right of a 210 px mark, vertically centred.
`outline_wordmark.py` instances that font at wght 500 / wdth 100 / slnt 0 and
writes each glyph as a path with the same layout. Overlaid on
`brand/backplane-x-banner.png` the outlines land within 1 px of the brand
rendering (ink box 273–1242 × 159–336 vs 160–335 px).

The font is not redistributed. Rerun only if the brand lockup changes:

```sh
python3 sources/backplane_logo/outline_wordmark.py <berkeley-mono-variable.woff2> sources/backplane_logo/backplane-mark.svg
```

(needs `fonttools` and `brotli`.) The brand has no stacked lockup, so none is generated.
