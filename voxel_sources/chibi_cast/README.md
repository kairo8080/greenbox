# Greenbox chibi voxel cast

Created 2026-10-03. Seven original characters with oversized chunky heads, compact bodies, short sturdy limbs and restrained square facial features. The broad visual direction draws inspiration from [The Touryst](https://thetouryst.shinen.com/deluxe/): simple cubic silhouettes, tropical color blocking and readable details. The pack contains original Greenbox artwork; no game assets, character models or textures were imported or copied.

All preview images render the actual occupied-cube geometry. Each character folder contains an assembled editable MagicaVoxel `.vox`, six independently editable body-part `.vox` files, a neutral `.glb`, a preview `.blend`, portrait PNG, thumbnail, exact palette atlas, authoritative source JSON and source/mesh verification records.

| Character | Occupied cubes | Export triangles | Total height |
| --- | ---: | ---: | ---: |
| Rasta Grower | 4,170 | 576 | 1.60 m |
| Corporate Boss | 3,855 | 586 | 1.50 m |
| Robot | 3,718 | 548 | 1.75 m |
| Chef | 4,456 | 626 | 1.75 m |
| Blonde Lady | 4,504 | 522 | 1.50 m |
| Party Woman | 4,536 | 542 | 1.50 m |
| Skeleton | 2,832 | 630 | 1.40 m |

The complete seven-character cast contains 28,071 occupied cubes and 4,030 exported triangles. Every character uses the same 0.05 m cubic grid and exact 256-entry RGBA palette as the original Greenbox character and environment library. Palette index zero is transparent air. Color roles remain compatible with the viewer's global palette controls.

## Game-ready coordinates and movable parts

Native sources use X/Y horizontal, Z up and front -Y. Game GLBs use Y up and front +Z. The centered ground root `CharacterRoot` contains six named rigid mesh children: `torso`, `head`, `arm_left`, `arm_right`, `leg_left`, `leg_right`. Each has its own recorded head, shoulder or hip pivot. All six parts are connected, assembled characters are connected, and parts do not overlap.

The GLBs retain a neutral pose, with no embedded animation clips or skeletal skins. Animate the rigid parts around their pivots in the game engine. Hidden faces within each part are removed and coplanar faces combined; contact faces between movable parts remain. Each character uses one embedded palette material with nearest filtering. Game GLBs exclude preview cameras, studio lighting and the backdrop.

The preview Blender scene rotates only its character root 45 degrees and uses a low perspective camera at 4 degrees elevation with a 70 mm lens. Editable cell coordinates and neutral GLBs remain on their exact original cubic grid.

## Edit, regenerate and export

Open the assembled `.vox` in MagicaVoxel to edit the full silhouette. The six part files are normalized independently; their placement and pivots are recorded in the source JSON and manifest. For consistent game exports, update the part cells in the authoring scripts or authoritative part JSON. An edit made only to the assembled `.vox` must be synchronized into those parts before exporting.

The `tools/` folder bundles portable Python authoring helpers, the original greedy voxel mesh exporter and an independent file verifier. From this pack directory, regenerate all seven native sources with Python 3:

```text
python tools/build_leads.py
python tools/build_chef_skeleton.py
python tools/build_women.py
python tools/verify_chibi.py --sources-only
```

These commands overwrite their named generated source folders. Preserve any manual source edits first. `reproducibility.json` records byte-for-byte reproduction of every accepted source JSON, manifest and VOX file using isolated copies of these portable tools.

Blender 5.1 produced the included mesh files and previews. From the pack directory, rebuild one character's derived exports with:

```text
blender --background --disable-autoexec --python-exit-code 1 --python tools/export_cast.py -- robot
```

The exporter writes the named character's GLB, Blender scene, palette atlas, PNG and mesh report. It does not rewrite native VOX files. To verify all complete exports and refresh the independent pack report:

```text
python tools/verify_chibi.py
```

## Verification

`pack_validation.json` independently parses the actual native VOX files, GLB geometry buffers and PNG pixels. It checks all source cells, palette colors, normalized placement, connectivity, hierarchy, neutral transforms, joints and cubic grid boundaries. Every exported triangle is checked against the exposed source cube faces and exact palette indices. MagicaVoxel MCP independently read all seven assembled native models with the expected voxel counts. Source manifests record SHA-256 hashes; reproducibility checks compare real output bytes. Saved Blender scenes are checked for nonempty supported containers; their internal saved-scene blocks are not decoded by the independent verifier.

The original proportioned character cast remains a separate asset set. This chibi collection has its own source files, exports and reusable pack.
