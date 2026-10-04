# Greenbox voxel viewer

Explore three Greenbox lore scenes, seven characters in Garden chibi, Chibi, and Original proportions, the original bedroom, and grow props: 26 embedded models in one 3D viewer. A shared indexed palette keeps color changes consistent across the cast and scenery. The lore locations are static art previews; the playable Unity and Godot prototypes are separate.

## Open or build

Open the [hosted viewer](https://greenbox-pi.vercel.app/viewer/). It starts at **Greenbox lore scenes → Seedling garden → Day**, with **Garden chibi** selected for the character collection and **Greenbox Garden** as the shared palette. [Compare the new cast](https://greenbox-pi.vercel.app/viewer/?collection=characters&style=garden&palette=garden), or [open ROOTS in daylight](https://greenbox-pi.vercel.app/viewer/?collection=lore&location=roots_street&lighting=day).

The built `public/viewer/index.html` and workspace copy `outputs/greenbox-character-viewer.html` are single portable HTML files. All models, colors, and runtime code are embedded for offline use, with no CDN or runtime asset fetch. Direct `file://` opening has not been browser-tested in this environment; browser interaction checks used the served viewer.

To rebuild from the `greenbox` repository root:

```sh
npm install --prefix viewer
npm run build:viewer
```

## Inspect assets

- Choose **Greenbox lore scenes**, **Character collection**, **Bedroom scene**, or **Grow props**.
- Lore scenes offer **Seedling garden**, **Level-one bedroom**, and **ROOTS district**, each with **Day** or **Night** lighting. Warm lamps, cyan/magenta accents, soft shadows, and bloom establish the scene's mood; bloom is stronger at night.
- **Character style** switches all seven between **Garden chibi** (the default), **Chibi**, and **Original**. The selected character and global color edits persist across the switch.
- Characters support **Compare all seven**, **Solo**, and **Lineup**, with **Full body** or **Portrait** framing.
- Drag to orbit, scroll to zoom, and right-drag to pan. Use **Front**, **Right**, **Left**, and **Back** for repeatable views.
- **Reset view** restores Garden chibi characters to a 45° view at 14° elevation, showing the stepped hats and hair. Earlier characters retain their low 4° elevation. Lore scenes and the original bedroom use 28°; props use 15°. **Sync cameras across views** keeps comparison views aligned.
- **Turntable** orbits the camera around the asset. It does not animate a character's walking pose.

The characters are Rasta grower, Corporate boss, Robot, Chef, Blonde lady, Party woman, and Skeleton. The viewer changes camera framing and colors; it does not edit meshes or poses.

The chibi cast and lore scenes take broad art direction from the supplied [The Touryst references](https://thetouryst.shinen.com/deluxe/): chunky silhouettes, clean color blocks, and expressive lighting. They are original Greenbox artwork; no game assets, characters, or textures were copied. The scenes reuse the existing Greenbox cast and CC0-derived cannabis plants.

| Lore scene | Occupied cubes | Mesh triangles |
| --- | ---: | ---: |
| ROOTS district | 220,120 | 11,646 |
| Level-one bedroom | 124,615 | 13,324 |
| Total | 344,735 | 24,970 |

Both use a 0.05 m voxel grid and the same canonical palette. [Editable lore sources and provenance](../voxel_sources/lore_scenes/README.md) document the modular assets, placements, and exports. The chibi cast totals 4,030 triangles and the original cast 5,954; mesh counts alone do not establish a frame rate.

The new [Garden chibi cast](../voxel_sources/garden_cast/README.md) follows the four newer user references with larger cube heads, tiny bodies, layered hair and hats, and sparse corner accents. Its seven characters total 46,336 occupied cubes and 2,572 surfaced triangles, with six movable rigid parts each. The [Seedling garden](../voxel_sources/garden_scenes/README.md) adds lime trees, layered soil, turquoise water, fish, flowers, the new grower, and source-derived potted plants: 259,449 occupied cubes and 7,050 triangles. The water is opaque voxel geometry. [Garden art direction](../docs/garden-art-direction.md) records the palette and shape rules.

## Use one palette everywhere

Choose **Greenbox Garden**, **Original**, **Island**, **Pastel**, **Neon**, or **Monochrome**, then edit any of the 63 color swatches. Each swatch represents a stable role and index shared by characters, lore scenes, room, and props. A color edit applies to every model that uses that index. The Garden theme maps citrus greens, turquoise, cream, warm soil, and restrained raspberry accents to the same source indices.

**Protect identity colors** is enabled by default. It preserves the original skin, hair, eye, lip, and blush colors, plus the robot's visor and skeleton's bone colors. Some protected slots also appear on props. Turn protection off to recolor those slots with the theme. An explicit swatch edit always takes precedence over protection.

Slot 0 remains transparent air. Slots 1–63 hold the current collection's colors; the catalog includes all 256 slots for reliable export. [palettes.json](palettes.json) stores the original colors, named roles, identity slots, and six explicit themes. [palette-core.mjs](palette-core.mjs) applies themes and writes recolored files.

## Export

- **.VOX** creates a download for the selected character, lore location, or original bedroom with the current palette and unchanged voxel occupancy, coordinates, scene chunks, and palette indices.
- **.GLB** creates a download for the selected character, lore location, bedroom, or aggregate props with the current colors. Geometry, node hierarchy, and part pivots remain intact.
- **Download palette** saves the current palette as JSON for reuse with the same index mapping.

Props export as the original GLB library, with its source node placements preserved. The viewer spaces them out for inspection. Editable individual prop VOX templates remain in `voxel_sources/`; the combined props preview is not a new VOX template.

Each export also leaves a **Save** link below the download buttons. Link generation was verified in the in-app browser; saving those files to disk was not verified there.

Exports start from the embedded source assets and create new download files. The original source files remain available for voxel or mesh editing in the appropriate editor.

## Validation

Palette/export checks cover both seven-character casts across five themes, the original bedroom, and props. They verify stable color indices, immutable inputs, preserved VOX occupancy and unknown chunks, and preserved GLB geometry, hierarchy, and pivots. Each chibi and lore GLB is independently compared against its exact source cube surfaces and canonical palette atlas. Lore checks also verify the modular placement union, source provenance, emissive roles, world bounds, and both day/night preview images.

`npm run build` checks the committed viewer's v4 schema, all 26 embedded models, declared mesh/voxel counts and lore heights, required controls and defaults, embedded palette pixels, and inline script syntax. Garden character exports are bound to independently verified source hashes and counts. These static checks do not establish browser performance or successful disk downloads.
