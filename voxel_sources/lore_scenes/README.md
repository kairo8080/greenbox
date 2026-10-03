# Greenbox lore voxel environments

Created 2026-10-03. Two original editable voxel dioramas develop the Greenbox setting: the **ROOTS street** supply co-op and social arcade corner, and a **starter loft** with a bed, desk, grower character, plants, water props and colorful accent lighting. Both are built from actual occupied cubic cells. Day and night previews render that real geometry.

The broad style draws inspiration from [The Touryst](https://thetouryst.shinen.com/deluxe/) and the user's supplied reference screenshots: compact dioramas, clean chunky forms, bright color blocks and readable details. All scene architecture, lettering and decorative graphics are original Greenbox artwork. No reference-game assets, textures or screenshot pixels were copied into these models.

| Environment | Occupied cubes | Export triangles | Native X/Y/Z span |
| --- | ---: | ---: | --- |
| Roots Street | 220,120 | 11,646 | 8.5 × 6.25 × 3.1 m |
| Starter Loft | 124,615 | 13,324 | 5.6 × 5 × 2.9 m |

The scenes share the exact Greenbox 256-entry RGBA palette and 0.05 m cubic grid. Both assembled scenes form one connected occupied-cell component and have zero overlapping modular-instance cells. The complete pack contains 344,735 occupied cubes and 24,970 surfaced triangles.

## Files and editing

Each scene folder contains:

- `scene.json`: reusable modular asset cells, instance placement, palette and artistic light records.
- `assets/*.vox`: individually editable MagicaVoxel model sources.
- `<scene>.vox` and `<scene>.json`: the exact assembled occupied-cell union.
- `flat_scene.json`: the authoritative static union used for optimized scene export.
- `<scene>.glb`: the surfaced static composition with flat cubic faces and embedded palette materials.
- `<scene>.blend`: editable Blender preview scene, camera and studio lighting.
- `<scene>_day.png` and `<scene>_night.png`: 1440×1000 renders of the real geometry.
- `source_manifest.json` and `mesh_validation.json`: source and exported-file records.

Open native VOX files in MagicaVoxel to edit cells. Individual model sources use normalized local coordinates; the modular JSON records their placement. An edit made only to the assembled VOX must be synchronized into the modular sources before rebuilding. `flat_scene.json` keeps hidden inter-model faces out of the composed game mesh.

Native source coordinates are X/Y horizontal, Z up and front -Y. GLBs use Y up and front +Z, with scene offsets in meters. The exported compositions are static dioramas. Characters embedded in these scene meshes are static; use the separate existing Greenbox chibi character pack for six-part movable character rigs and gameplay animation. These assets are ready for engine import and inspection; they do not add a new playable level or simulation logic by themselves.

Day/night PNGs include actual Blender preview lights. Preview lights, camera and backdrop are excluded from the GLBs. Emissive palette surfaces remain in the GLBs; an engine or interactive viewer must add its own world lighting, accent lights and bloom to reproduce the mood. The supplied source JSON light records provide artistic positions/colors, not real-world cultivation instructions.

## Portable regeneration and independent checks

`tools/` contains the scene builders, exact-grid helpers, Blender surface exporter and independent verifier. `inputs/index.json` maps original logical provenance paths to byte-identical SHA-addressed JSON inputs. This allows regeneration after moving the pack while retaining the accepted source provenance strings and hashes.

From the pack directory, use Python 3 to regenerate native sources:

```text
python tools/build_street.py
python tools/build_loft.py
python tools/verify_lore.py --sources-only
```

These commands overwrite generated scene source files; preserve manual edits first. They do not rebuild derived GLBs or preview renders. `reproducibility.json` records byte-for-byte comparison of all regenerated scene JSON, manifest and VOX files in an isolated temporary copy, without changing the accepted scene folders.

Blender 5.1 produced the supplied GLBs and previews. Rebuild derived scene exports with:

```text
blender --background --disable-autoexec --python-exit-code 1 --python tools/export_lore.py -- roots_street starter_loft
python tools/verify_lore.py
```

The independent verifier parses actual native VOX files, GLB buffer data, palette images and day/night PNGs. It proves modular placement union, exact source hashes and palette colors, flat axis-aligned cube surfaces, triangle coverage of every exposed source face, scene bounds, emission and exclusion of preview objects. `pack_validation.json` records the accepted complete result. Blender files are checked for nonempty supported container headers; internal saved-scene blocks are not decoded by this verifier.

## Source and license provenance

Existing original Greenbox chibi characters, room props and CC0-derived plants are reused. The plant foliage originally comes from **Cannabis plants**, by **Yughues / Nobiax**, under **CC0 1.0 Universal**. `source_originals/` preserves the original download archive, author readme, derived native leaf VOX and full license/transformation record. `provenance.json` and `LICENSES.md` distinguish project-original artwork, exact reused inputs and the external leaf source. No new license for project-original artwork is inferred.
