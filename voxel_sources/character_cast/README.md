# Greenbox voxel character cast

Created 2026-10-03. Seven original true voxel characters, including the existing grower in the requested lower camera view. All previews render actual geometry.

Each character folder contains an assembled MagicaVoxel `.vox`, six independently editable body-part `.vox` files, neutral `.glb`, posed `.blend`, portrait PNG, exact palette, source JSON, and source/mesh verification records. The original grower's occupied cells and palette are preserved.

| Character | Occupied cubes | Export triangles | Total height |
| --- | ---: | ---: | ---: |
| Rasta Grower | 2,007 | 842 | 1.70 m |
| Corporate Boss | 3,719 | 742 | 1.80 m |
| Robot | 2,908 | 910 | 1.95 m |
| Chef | 2,279 | 1,064 | 2.05 m |
| Blonde Lady | 1,794 | 522 | 1.70 m |
| Party Woman | 2,316 | 770 | 1.75 m |
| Skeleton | 1,032 | 1,104 | 1.65 m |

Sources use a 0.05 m cubic grid, native X/Y horizontal and Z up, facing -Y. The GLBs are Y up and face +Z; centered ground root `CharacterRoot` has six named children: torso, head, arm_left, arm_right, leg_left, leg_right. Each retains its shoulder/hip/head pivot. One embedded palette material uses nearest filtering. Hidden faces within parts are removed and coplanar faces combined. Contact faces between movable parts remain intentionally. There are no skeletal skins or embedded animation clips; gameplay rotates rigid parts around their pivots.

The preview `.blend` uses a +45° Z rotation of the whole character and a 70 mm perspective camera at 4° elevation. It faces right in the portrait. The editable cell grid and neutral GLB stay unrotated, so the camera view does not resample the character.

## Edit and export

Open assembled `.vox` in MagicaVoxel to edit the whole silhouette. The six normalized part sources have placement and pivots recorded in the JSON/manifest. For reusable exports, edit those part cells through the authoring scripts or part source JSON; an edit made only to the assembled `.vox` must be synchronized back into its parts before running the part exporter. Open `.blend` in Blender to inspect the existing pose and studio preview.

The `tools/` folder bundles the original authoring scripts and shared grid/palette/greedy mesh exporter. With Python 3, regenerate the six new sources from the pack directory:

```text
python tools/build_boss_robot.py
python tools/build_chef_skeleton.py
python tools/build_women.py
```

These commands intentionally regenerate their named character folders. Preserve manual changes first. Blender 5.1.2 produced the included GLBs and PNGs. To rebuild one export from the source JSON:

```text
blender --background --disable-autoexec --python-exit-code 1 --python tools/export_cast.py -- robot
```

This writes the named character's derived GLB, Blender scene, palette, PNG and mesh report. Native `.vox` files are not rewritten by the mesh exporter. Cameras, studio lighting and backdrop are excluded from game GLBs. Use each imported character's actual height to set collision capsules in Unity.

## Provenance and verification

All six new designs are original artwork for this Greenbox project; no downloaded character assets, external likenesses, or generated raster concepts were used. The existing grower is copied from `greenbox/voxel_sources/rasta_character/`. Source manifests contain SHA-256 hashes. Each assembled character and each rigid part is six-neighbor connected, with no overlapping part cells. MagicaVoxel MCP independently read all seven assembled sources. `pack_validation.json` records independent native file and exported geometry checks.
