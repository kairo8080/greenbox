# Greenbox voxel collectibles

Nine original 3D collectible assets in the shared Greenbox Garden art direction. Every piece uses actual occupied cubic cells, the exact canonical 256-entry indexed Greenbox palette and a 0.05 meter grid. The source `.vox` is editable in MagicaVoxel. GLBs contain greedy exposed surfaces with flat normals and a shared nearest-sampled palette atlas. Preview lights, cameras and ground are excluded from game exports.

| ID | Asset | Dimensions in cells (X/Y/Z) | Triangles |
| --- | --- | --- | ---: |
| `grower_toybox` | Teal open-front toy display and Garden grower | 32 / 29 / 48 | 644 |
| `mystery_standard` | Teal and cream mystery box | 28 / 29 / 29 | 346 |
| `mystery_420_founder` | Dark and gold 420 Founder mystery box | 28 / 29 / 29 | 628 |
| `booster_common` | Lime Common booster pack / watering can | 26 / 10 / 38 | 662 |
| `booster_rare` | Blue Rare booster pack / grow light | 26 / 10 / 38 | 780 |
| `booster_epic` | Raspberry Epic booster pack / greenhouse key | 26 / 10 / 38 | 682 |
| `card_common` | Common watering can item card | 26 / 5 / 38 | 510 |
| `card_rare` | Rare grow light item card | 26 / 5 / 38 | 628 |
| `card_epic` | Epic greenhouse key item card | 26 / 5 / 38 | 530 |

Total: **101,432 occupied cells / 5,410 triangles**. All nine assets are one connected component each.

Each ID folder includes `<id>.vox`, `<id>.json`, `<id>.glb`, `<id>.blend`, `rendered.png`, the canonical `palette.png`, Garden presentation `preview_palette.png`, source manifest and mesh report. `assets.json` is a portable relative-path catalog with IDs, labels, rarity, dimensions, pitch, pivots, counts and actual file hashes. `collectibles_contact_sheet.png` combines the actual Blender geometry renders.

The grower toybox has an actual empty front window, with no transparent plane. The bundled existing Greenbox Garden grower retains its exact 7,318 original occupied cells and RGBA indices, translated onto the floor inside the box. This collectible is a static surfaced union. For body movement use the separate six-part character in `garden_cast/rasta_grower` from the full Greenbox library.

Cards and wrapper symbols are one-cell raised voxel relief, including the GB glyphs, rarity marks, watering can, grow light and greenhouse key. There are no screenshot textures or image planes. Cards and packs are deliberately enlarged for art inspection: at the source pitch the card is 1.3 meters wide and 1.9 meters high. Uniformly scale a game instance down for a hand-held or inventory object; for example `0.1` makes it 13 centimeters wide. GLBs use **Y up / front +Z**, centered X/Z and resting at Y = 0. Native sources use **Z up / front -Y**, with normalized bounds recorded in the source manifest. All single-model source dimensions stay below 256.

The canonical source palette remains unchanged. `preview_theme.json` is a portable snapshot of the effective Garden colors. Exporters write the canonical GLB first, then use this snapshot for the actual preview and `.blend` presentation. The full Greenbox viewer can apply the shared Garden palette toggle to these canonical meshes.

Rebuild and verify from any copy of this folder using Python 3 and Blender 5.1:

```powershell
python tools/build_collectibles.py
blender --background --disable-autoexec --python-exit-code 1 --python tools/export_collectibles.py -- --samples 12
python tools/verify_collectibles.py
python tools/verify_reproducibility.py
python tools/contact_sheet.py
```

The contact sheet requires Pillow. Native source creation and independent checks otherwise use only Python's standard library; export/render runs in Blender's bundled Python.

`pack_validation.json` independently parses the actual VOX and GLB files and clips every mesh triangle against original exposed cube faces, checking exact coverage, outward flat normals, source colors, all 256 atlas texels, pivots and bounds. It also checks the preserved grower, real front opening, image headers/pixel variation and Blender container header. Blender scene internals are not decoded by the independent verifier. `reproducibility.json` confirms all 27 native source/manifest files rebuild byte for byte using only this folder's tools and bundled inputs.

These are reusable game art assets. Booster opening, inventory rules, trading and item effects belong to gameplay systems.
