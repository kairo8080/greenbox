# Greenbox Seedling Garden

Created 2026-10-04. An original, true voxel outdoor diorama develops Greenbox's gentler garden identity: bright lime and olive cuboid trees, warm sand and layered soil, a teal pond, small fish, lily pads and reeds, a plank fence, an oak bench, a compact Rasta grower and existing CC0-leaf-derived potted plants. Broad color blocks and sparse corner patches follow the user's new reference direction without copying its composition, logos or characters.

Native dimensions are 120 × 104 × 82 cells at **0.05 meters per cell**: 6 × 5.2 × 4.1 meters. The assembled source contains **259,449 occupied cubes**, 15 reusable asset models and 26 placed instances. The optimized static GLB uses **7,050 triangles**. All modular instances have zero overlapping occupied cells. The complete diorama forms one six-neighbor component through its terrain. The pond is opaque occupied voxel geometry; it does not simulate water.

`seedling_garden/` contains the authoritative assembled `.vox` and `.json`, individually editable `assets/*.vox`, modular `scene.json` with placements, and `flat_scene.json` for the optimized static union export. The GLB has flat exposed cube surfaces, canonical palette material sampling and standard Y-up coordinates. Native assets are Z-up, front -Y; exported GLB faces front +Z. Hidden inter-model faces are removed by exporting the exact union. Preview cameras, lights and backdrop are excluded from the GLB.

The global **Garden** palette is a presentation remap. Source VOX files and exported GLB retain the existing exact 256-entry Greenbox palette. `preview_palette.json` snapshots the Garden theme for repeatable renders; `seedling_garden/preview_palette.png` is used only by the saved Blender scene and 1200 × 900 day/night previews. `palette.png` is the canonical atlas embedded in the GLB. Palette index 0 remains transparent air; occupied indices 1–255 sample index minus one in the 16 × 16 atlas.

This is static game art. The grower embedded in the flattened diorama is static; the companion `garden_cast` pack supplies its separate six-part character for future movement and animation. Garden interaction, crop stages and traversal require game integration.

## Repeatable authoring and verification

From this pack directory, run Python 3:

```text
python tools/build_garden.py
python tools/verify_lore.py --sources-only
blender --background --disable-autoexec --python-exit-code 1 --python tools/export_garden.py -- seedling_garden --samples 16
python tools/verify_lore.py
```

The builder overwrites generated native source files, so preserve hand edits first. `inputs/index.json` maps logical source provenance paths to unchanged SHA-addressed JSON inputs. The plant shape and imported character geometry are preserved exactly, including their indexed RGBA colors; only integer placements change.

`pack_validation.json` independently checks editable VOX chunk data, canonical palette, assembled bounds and count, modular union, source hashes, grid scale, connected components, GLB texture bytes, flat outward normals, and exact triangle coverage of every exposed source cube face. Blender previews render that same surfaced occupancy using the Garden palette. Saved Blender file validation checks its supported container header, not every internal block.

The plant foliage derives from **Cannabis plants**, by **Yughues / Nobiax**, under **CC0 1.0 Universal**. `source_originals/` preserves the original archive, author readme, derived leaf VOX and detailed provenance byte-for-byte. Architecture, scenery, small fauna and character design are original Greenbox artwork. See `LICENSES.md` and `provenance.json` for source records. No external reference images, logos or game assets are included.
