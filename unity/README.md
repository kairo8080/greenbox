# Greenbox — Unity browser game

Open the **Greenbox** folder in Unity **6000.2.6f1**, with **Web Build Support** installed and an active Unity license. This is a separate Unity project inside the existing Greenbox repository. Its local save is separate from the previously published Godot game.

**[Play Greenbox in Unity Web](https://greenbox-pi.vercel.app/unity/)**. The installed editor and Web module have successfully imported the voxel assets, created the bedroom scene, and exported this playable browser build.

On the first successful import, the editor creates `Assets/Scenes/Bedroom.unity`. Open that scene and press **Play**. The **Greenbox → Prepare Bedroom Scene** menu repeats setup if needed.

`./unity/open-project.ps1` opens the project directly. If your network inspects HTTPS and package downloads report certificate errors, pass `-CaBundle` with a PEM bundle of CA certificates already trusted on your computer. The launcher and build script pass it to Unity's package downloader with `NODE_EXTRA_CA_CERTS`; HTTPS verification remains enabled. Keep machine-specific certificates outside the repository.

The room uses the existing true voxel bedroom, six-part Rasta character, pots, and plant stages. WASD/arrows move the character, **1–3** select a pot, **E** plants/waters/harvests a nearby pot, **L** toggles the grow light, and **Space/Escape** pauses. The on-screen panel shows cash, XP, care controls, and equipment upgrades. Progress saves locally; growth pauses when the game is hidden.

## MagicaVoxel connection

MagicaVoxel edits `.vox` occupancy and palettes. Unity provides movement, collisions, game rules, UI, and browser export. Blender is already available to export the optimized flat voxel meshes as GLB, retaining separate character limbs. A Unity MCP is optional for editor automation; it is not required for file import.

The authoritative editable sources and license records remain in `../voxel_sources/`. Imported game meshes come from `../game/assets/`, at **0.05 meters per voxel**. Unity's official **glTFast 6.15.0** importer creates native prefabs, meshes, and materials in the Editor. There is no per-voxel GameObject hierarchy or runtime GLB download. glTFast mirrors X; gameplay positions apply the same conversion.

After updating the GLB exports, run from this repository:

```powershell
./unity/sync-voxel-assets.ps1
```

Unity reimports the changed meshes. Keep object/joint names intact. Run **Greenbox → Validate Voxel Imports**, then check silhouettes, scale, lamp materials, and character movement in Play mode before exporting.

## Browser build

```powershell
./unity/build-web.ps1
npm run sync:unity
npm run build
```

Pass `-UnityEditor` if your editor is installed elsewhere. The script exports to `../unity-build/`, with the complete browser launcher and Build files. The editor menu **Greenbox → Build Browser Game** runs the same build. `sync:unity` validates and copies the complete export to `public/unity/`, adapting its URLs for that mount. `npm run build` verifies both committed exports. Rebuild and sync after gameplay or asset edits, test in a browser, then commit the source and published files together.

Use an HTTP server to preview the export. Opening it through `file://` will not work. The target is desktop browsers with WebGL 2 and WebAssembly. This starter uses the built-in renderer, one character, reused combined voxel meshes, simple collision boxes, single-threaded WebAssembly, and small action effects. Check actual frame time on target devices before adding heavier effects. Mobile controls are not implemented yet.

The Web build leaves Unity's internal compression disabled so an HTTP host can compress responses normally, avoiding special `.br` or `.gz` routing. Its included `vercel.json` supplies the WASM MIME type. The repository publishes the complete Unity export at `/unity/`; the original Godot demo remains at `/`.

## Verification

The pure C# gameplay model has a standalone test suite at `tests/SimStateTests.cs`; run `./unity/run-domain-tests.ps1` from the repository on Windows. A successful domain test run alone does not verify the Unity build.

Validated on 2026-10-03: 78 gameplay checks passed; Unity imported all three GLBs as native prefabs and exported Web successfully. The voxel meshes contain 13,424 triangles. The browser export is about 19.1 MiB before HTTP compression. Browser testing completed walking to a pot, planting, switching the lamp, watering, growth, harvesting, Level 2 progression, and reload persistence. No browser error or warning was observed during that session. Mobile controls and performance across other hardware remain unverified.
