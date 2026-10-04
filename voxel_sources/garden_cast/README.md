# Greenbox Garden chibi cast

Created 2026-10-04. Seven original Greenbox characters use oversized clean cubic heads, tiny torsos, very short legs, layered hat and hair panels, bold square eyes, and sparse colored corner chips. The four voxel art images supplied in chat informed the broad proportions and art direction. No image pixels, models, game characters, logos or branded cabinet details were imported or traced.

This is a third independent style. Original and earlier chibi sources remain separate. Every preview renders the real occupied-cell geometry; the contact sheet combines those renders.

| Character | Occupied cubes | Surface triangles | Height |
| --- | ---: | ---: | ---: |
| Rasta grower | 7,318 | 376 | 1.55 m |
| Corporate boss | 6,114 | 408 | 1.45 m |
| Helper robot | 6,192 | 374 | 1.65 m |
| Chef | 7,224 | 334 | 1.65 m |
| Blonde neighbor | 6,948 | 340 | 1.50 m |
| Party neighbor | 6,984 | 406 | 1.50 m |
| Skeleton | 5,556 | 334 | 1.35 m |

The complete cast has 46,336 occupied cubes and 2,572 exported surface triangles. Counts come from independently parsed source and GLB bytes in `pack_validation.json`.

## Sources, palette and scale

Each character folder contains its assembled single-model `.vox`, six part `.vox` files, authoritative JSON, source manifest, neutral `.glb`, `.blend`, 800×1000 preview, canonical atlas and separate preview atlas.

The exact original 256-entry indexed RGBA palette remains in every native source and canonical GLB. Its SHA-256 is `09cb38d6cb39613d53228591ed2d7cdefc47a98cbdb81f78ab19b65dd3c36293`. Slot zero is transparent air; occupied cells use indices 1–255. Every cell measures 0.05 m. `palette.png` is a 16×16 atlas where source index N samples texel N−1 with nearest filtering.

`preview_theme.json` is a portable snapshot of the shared Greenbox Garden theme. The exporter creates and verifies the canonical GLB first, then applies that theme to the separate `garden_preview_palette.png` used by Blender previews. It changes no cell indices, geometry or game atlas. The browser viewer applies the same theme globally and can export recolored assets.

## Rigid movement and coordinates

Native coordinates are X/Y horizontal, Z up, front −Y. GLB uses Y up, front +Z, with centered ground root `CharacterRoot`. Six rigid mesh children are named `torso`, `head`, `arm_left`, `arm_right`, `leg_left`, `leg_right`. The root is source `[11,10,0]`. Head pivot `[11,10,9]`, shoulders `[7,10,8]` and `[15,10,8]`, hips `[8.5,10,4]` and `[13.5,10,4]`, and torso root `[11,10,4]` are documented in each JSON.

Each part has one six-neighbor connected component; every assembled character is connected with zero overlapping part cells. Hidden faces within a part are removed and flat coplanar faces combined. Contact faces between movable parts remain. GLBs contain a neutral pose, no embedded animation clips or skeleton skin, and no preview lights, ground or cameras. A game can rotate the rigid children around their pivots. This asset pack does not implement gameplay or motion clips.

## Regenerate

From this pack directory, use Python 3 to generate authoritative native sources:

```text
python tools/build_garden.py
python tools/verify_garden.py --sources-only
python tools/verify_reproducibility.py
```

Generation overwrites the seven generated source folders; preserve manual edits first. Blender 5.1.2 produced the derived game exports and previews. Rebuild any named character from this pack directory:

```text
blender --background --disable-autoexec --python-exit-code 1 --python tools/export_cast.py -- rasta_grower --samples 16
python tools/verify_garden.py
python tools/contact_sheet.py
```

Pass all seven folder names to the Blender command for one batch. The contact sheet helper requires Pillow; source generation and independent validation use Python's standard library.

The independent verifier does not import authoring or exporter modules. It parses native VOX chunks, actual GLB binary accessors and PNG pixels. It verifies unique cell occupancy, dimensions, exact palette, all source hashes, part connectivity and placement, actual proportions, transformed cubic boundaries, flat outward normals, joints, neutral hierarchy, and exact exposed source-face coverage/color for every exported triangle. It checks nonempty supported Blender container headers; it does not decode saved Blender scene blocks.
