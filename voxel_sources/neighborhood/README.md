# Greenbox Neighbor Commons

Created 2026-10-04. An original neighborhood environment develops the Greenbox Garden art direction with four compact toy-like fronts, bright lime trees, a warm sandy courtyard, cream paths, an oak bench, two lamps, two preserved CC0-leaf-derived potted plants, flowers and a tucked-away fictional Night Market collectible stall. Architecture, signs, card blocks and box props are original cubic artwork.

The native source is **240 × 200 × 70 cells** at **0.05 meters per cell**: 12 × 10 × 3.5 meters. It contains **378,972 occupied cubes**, **12 reusable models**, **21 placements**, zero overlapping occupied cells, and one six-neighbor connected terrain union. The optimized static GLB has **6,718 triangles**, one mesh, two shared surface materials and one embedded 16 × 16 exact palette atlas. All hidden inter-model faces are removed by exporting the exact union.

`neighbor_commons/` contains the authoritative `.vox` and `.json`, modular `scene.json`, `flat_scene.json`, individual `assets/*.vox`, source manifest, canonical GLB, editable Blender scene, and actual 1200 × 900 day/night geometry renders. Sources and GLB retain the canonical 256-entry Greenbox palette. The Garden palette in `preview_palette.json` and `preview_palette.png` is a presentation remap for preview renders and the saved Blender scene; it does not change source occupancy or source colors.

The environment contains **no static characters**. The companion `garden_cast` six-part character models provide the player and four neighbors at runtime. This environment is closed decorative exterior scenery; house interiors are not navigable. The fictional Night Market handles in-game collectibles rather than real transactions.

`game_layout.json` is duplicated byte-for-byte at the pack root and inside `neighbor_commons/`. It defines centered GLB meters, a level floor at Y 0.2 m, map bounds, player spawn/radius/speed, four Garden neighbor IDs with original short dialogue, an interaction point for the Night Market, optional display spots, and source-derived obstacle AABBs. Native X/Y are horizontal and Z is up; the native ground root is `[120,100,0]`. Exact export transform:

```text
world X = (native X - 120) × 0.05
world Y = native Z × 0.05
world Z = -(native Y - 100) × 0.05
```

World bounds are X [-6,6], Y [0,3.5], Z [-5,5]. AABB footprints cover every source solid intersecting the 0.2–1.85 m player-height slab. Tree canopies start at Y 1.9 m so all current Garden characters can walk below them. `layout_validation.json` independently checks the coordinate mapping, exact collision footprints, source hashes, floor uniformity, and flood-fill access to all five interaction points with the player's 0.24 m radius. Runtime movement, dialogue, emoji and trade behavior are implemented and tested separately by the game integration.

From this pack directory:

```text
python tools/build_neighborhood.py
python tools/verify_lore.py --sources-only
python tools/verify_layout.py
blender --background --disable-autoexec --python-exit-code 1 --python tools/export_garden.py -- neighbor_commons --samples 8
python tools/verify_lore.py
```

The builder replaces generated native files, so preserve hand edits first. SHA-addressed `inputs/` preserve exact imported plant source bytes; `source_originals/` preserve the source archive, author's readme, derived leaf VOX and detailed conversion provenance. See `LICENSES.md` and `provenance.json`. `pack_validation.json` checks actual editable VOX and GLB bytes independently, including exact coverage of each exposed source cube face, flat outward normals, nearest palette UVs, canonical embedded palette bytes, source scale, tight bounds, source union and preview headers. Blender file verification checks the recognized container header rather than decoding every saved scene block. `reproducibility.json` records byte-for-byte portable regeneration of native source and layout files.
