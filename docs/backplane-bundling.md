# Backplane bundle contract

Repository: `BackplaneWorks/Backplane_KiCad_Library`.
Tagged releases automatically publish a platform-independent runtime payload:

```text
https://github.com/BackplaneWorks/Backplane_KiCad_Library/releases/download/v2026.10.26/backplane-kicad-library-2026.10.26.tar.gz
```

The adjacent `.sha256` contains the archive checksum. Pin both the library
release/source commit and its checksum in Backplane's runtime manifest, beside
the selected Backplane_KiCad runtime. A library update is an explicit pin
change; installers must not download an unpinned `main` or silently accept a
checksum failure.

The archive has one root, `Backplane_KiCad_Library/`, containing `libraries/`,
`3dmodels/`, original notices, documentation, the catalogue image, and
`BUNDLE_MANIFEST.json`. The latter records the source commit, counts, library
nicknames, required path variable and per-file SHA256 hashes. It contains only
the usable library payload, not the generator dependency trees, test boards,
virtual environments or build intermediates. Complete editable sources remain
in the repository and the full library ZIP.

At install/runtime setup:

1. Verify the archive checksum, reject unsafe extraction paths and verify
   `BUNDLE_MANIFEST.json` before activating the extracted directory.
2. Point the KiCad process environment's `BACKPLANE_KICAD_LIBRARY` at the
   absolute extracted root. Project text variables alone do not resolve these
   model references in the tested STEP exporter.
3. Register the five `.pretty` directories in Backplane's managed KiCad library
   configuration, using the nicknames in the manifest. Preserve existing
   project/user entries. Do not overwrite the user's global KiCad tables or
   edit existing board instances to install a library.
4. Cover desktop packaging and headless/CLI/IPC launches on Linux, macOS and
   Windows, so all use the same managed library and resolve the same models.
5. Smoke-test a hole, each Shoggoth size and each passive density, plus a STEP
   export that actually includes a passive model. Assert all 199 entries and
   42 models are present; a CLI exit code alone is insufficient when its output
   reports missing models.

Validated KiCad runtime: `10.99.0-bp.4`, source
`5dbc22d292704d02b609d5b7a0edc971f1b7f08b`. The passive and original hole files
use native footprint version `20260206`; do not assume an older 10.0.6 runtime
can consume the entire collection. The catalogue board itself uses the newer
runtime's native board format and is not part of the runtime payload.

The original 35 mm Shoggoth remains exact. The nominal 25 mm artwork is adapted
for fine-detail screening. Hole silk exclusion uses enlarged mask openings and
the relevant DRC/plotting settings, not a universal silkscreen keepout flag.
The Least-only local 0806 is outside the 44 complete density triples. Preserve
these documented limitations and all upstream notices when shipping.
