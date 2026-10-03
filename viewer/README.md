# Greenbox voxel character viewer

Inspect seven true voxel characters in chibi and original proportions, the bedroom, and grow props in one offline 3D viewer. A shared indexed palette keeps color changes consistent across both casts and the environment.

## Open or build

Open the built `public/viewer/index.html` in a browser. The workspace also contains a portable copy at `outputs/greenbox-character-viewer.html`. Both are single HTML files with embedded models, colors, and viewer code; they work directly through `file://` without a server or CDN.

To rebuild from the `greenbox` repository root:

```sh
npm install --prefix viewer
npm run build:viewer
```

## Inspect assets

- Choose **Character collection**, **Bedroom scene**, or **Grow props**.
- **Character style** switches all seven between **Chibi** (the default) and **Original**. The selected character and global color edits persist across the switch.
- Characters support **Compare all seven**, **Solo**, and **Lineup**, with **Full body** or **Portrait** framing.
- Drag to orbit, scroll to zoom, and right-drag to pan. Use **Front**, **Right**, **Left**, and **Back** for repeatable views.
- **Reset view** restores characters to a 45° view with a low 4° elevation. The bedroom opens from its cutaway side at 28°, and props use 15°. **Sync cameras across views** keeps comparison views aligned.
- **Turntable** orbits the camera around the asset. It does not animate a character's walking pose.

The characters are Rasta grower, Corporate boss, Robot, Chef, Blonde lady, Party woman, and Skeleton. The viewer changes camera framing and colors; it does not edit meshes or poses.

The chibi cast takes broad art direction from [The Touryst](https://thetouryst.shinen.com/deluxe/): broad cube heads, compact silhouettes, clean color blocks, and bright lighting. These are original Greenbox designs. The stage uses a pale sky, warm ground, and cached 512-pixel shadows; shadows are rebuilt when the displayed models change. The chibi collection totals 4,030 triangles and the original collection totals 5,954. These mesh counts do not guarantee a frame rate on every device.

## Use one palette everywhere

Choose **Original**, **Island**, **Pastel**, **Neon**, or **Monochrome**, then edit any of the 63 color swatches. Each swatch represents a stable role and index shared by characters, room, and props. A color edit applies to every model that uses that index.

**Protect identity colors** is enabled by default. It preserves the original skin, hair, eye, lip, and blush colors, plus the robot's visor and skeleton's bone colors. Some protected slots also appear on props. Turn protection off to recolor those slots with the theme. An explicit swatch edit always takes precedence over protection.

Slot 0 remains transparent air. Slots 1–63 hold the current collection's colors; the catalog includes all 256 slots for reliable export. [palettes.json](palettes.json) stores the original colors, named roles, identity slots, and five explicit themes. [palette-core.mjs](palette-core.mjs) applies themes and writes recolored files.

## Export

- **.VOX** downloads the selected character or bedroom with the current palette and unchanged voxel occupancy, coordinates, scene chunks, and palette indices.
- **.GLB** downloads the selected character, bedroom, or aggregate props with the current colors. Geometry, node hierarchy, and part pivots remain intact.
- **Download palette** saves the current palette as JSON for reuse with the same index mapping.

Props export as the original GLB library, with its source node placements preserved. The viewer spaces them out for inspection. Editable individual prop VOX templates remain in `voxel_sources/`; the combined props preview is not a new VOX template.

Each export also leaves a **Save** link below the download buttons. Use it if your browser waits for a second click before saving.

Exports start from the embedded source assets and create new download files. The original source files remain available for voxel or mesh editing in the appropriate editor.

## Validation

Palette/export checks cover both seven-character casts across five themes, the bedroom, and props. They verify stable color indices, immutable inputs, preserved VOX occupancy and unknown chunks, and preserved GLB geometry, hierarchy, and pivots. Additional checks cover multi-model VOX files, missing palette chunks, malformed files, and PNG integrity. Each chibi GLB is independently compared against its exact source cube surfaces and canonical palette atlas. These checks validate export structure; browser interaction and performance require separate viewer testing.
