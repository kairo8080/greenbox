# Greenbox

A small desktop-first voxel grow-room game, with a Unity 6000.2.6f1 project and the original Godot 4.7.2 demo. Walk around a furnished bedroom, care for fictional game plants, harvest for cash and XP, and unlock extra pots and equipment.

**[Play the Unity browser game](https://greenbox-pi.vercel.app/unity/)** · **[Explore the voxel lore viewer](https://greenbox-pi.vercel.app/viewer/)** · [Original Godot demo](https://greenbox-pi.vercel.app) · [Vercel project](https://vercel.com/kairo8080/greenbox)

The **[grow economy prototype](economy/README.md)** ([play](https://greenbox-pi.vercel.app/economy/)) is a plain browser game for play-testing the BigCoin-style mechanics: grow rooms with slots and a power limit, strains with potency and power draw, a halving BUD token split by network share, 75% burns, and a simulated network of rival growers. Its UI is a placeholder.

The new **[Greenbox Unity project](unity/README.md)** lives in `unity/Greenbox/`, using Unity 6000.2.6f1 and Web Build Support. It imports the same optimized voxel assets with Unity glTFast and has passed a real browser build and gameplay check, including a full harvest and saved progress after reloading. MagicaVoxel remains the editable asset source; Blender exports meshes, and Unity supplies the playable game.

The **[voxel character cast](voxel_sources/character_cast/README.md)** adds a corporate boss, robot, chef, blonde lady, party woman, and skeleton, plus the existing grower with a 45° right-facing pose and lower preview camera. Each includes editable VOX sources, six movable body parts, a neutral GLB, Blender scene, previews, and verification records. The bundled tools reproduce all six new source designs; import the models into Unity to expand the cast.

The **[chibi cast](voxel_sources/chibi_cast/README.md)** remakes all seven with broad cube heads, short legs, and compact bodies, taking visual inspiration from [The Touryst](https://thetouryst.shinen.com/deluxe/). These original Greenbox assets retain the exact collection palette, editable VOX sources, and six movable rigid parts. All seven together use 4,030 triangles; the taller original cast remains available.

The **[interactive voxel viewer](viewer/README.md)** now opens at **Greenbox lore scenes → Level-one bedroom → Night**. Switch to **ROOTS district**, choose day or night, and inspect the scenes with orbit, zoom, turntable, soft shadows, and bloom. The 18 embedded models also include both seven-character casts, the original bedroom, and props, with **Chibi / Original** comparison views and five global palette themes. The lore locations are static 3D art previews; gameplay continues in the existing Unity and Godot projects.

The **[editable lore scenes](voxel_sources/lore_scenes/README.md)** apply broad inspiration from the user's Touryst references to original Greenbox artwork, reusing the cast and CC0-derived plants. No game assets or textures were copied. ROOTS uses 220,120 occupied cubes and 11,646 triangles; the level-one bedroom uses 124,615 cubes and 13,324 triangles, for 344,735 cubes and 24,970 triangles total. [Open ROOTS in daylight](https://greenbox-pi.vercel.app/viewer/?collection=lore&location=roots_street&lighting=day).

The viewer provides editable color swatches and recolored VOX/GLB export links. `public/viewer/index.html` is a portable HTML file with all assets and runtime code embedded for offline use; direct `file://` opening has not been browser-tested here. Export link generation was verified in the in-app browser, while saving files to disk was not. Rebuild with `npm install --prefix viewer` and `npm run build:viewer`; the Vercel build verifies the committed viewer.

## Play

The Unity build starts automatically; click **Play** in the original Godot browser launcher. Both versions use:

| Input | Action |
| --- | --- |
| WASD / arrow keys | Move; cancel automatic walking |
| Click a pot | Select it and walk toward it |
| Click the floor | Walk to that spot |
| E | Plant, water, or harvest the nearby selected pot |
| 1 / 2 / 3 | Select a pot |
| Space / Escape | Pause or resume |
| L | Toggle the lamp |
| M | Mute or unmute |
| Mouse wheel | Zoom |

The sidebar care buttons also walk to the selected pot before acting. Progress saves locally in that browser and site; it is not an account or cloud save. Private browsing or blocked site storage can prevent saves. The game pauses when it loses focus and has no offline growth.

The browser version requires WebGL 2 and WebAssembly. Desktop Chrome, Edge, or Firefox is the initial target; mobile controls and broad device performance are not yet validated.

## Develop and export

Open `game/project.godot` in **Godot 4.7.2**. Install the matching **4.7.2 export templates**, including `web_nothreads_release.zip` and `web_nothreads_debug.zip`. The Web preset uses Compatibility rendering, with threads and GDExtensions disabled.

Install Node.js 20 or newer for the dependency-free verification scripts. From this repository:

```powershell
$env:GODOT_BIN = "C:\Tools\Godot\Godot_v4.7.2-stable_win64_console.exe"
npm run export:web
npm run build
```

Alternatively pass `-GodotExecutable` directly to `scripts/export-web.ps1`. Without a parameter or `GODOT_BIN`, the script looks for `godot` on `PATH`. It imports the project and creates `public/index.html` plus its engine/data files. Use an HTTP server to test these files; opening the HTML through `file://` is insufficient.

**Re-export after editing game code or assets, then commit the updated `public/` files.** `npm run build` verifies the committed browser export, configuration, and asset references; it does not run Godot or prove that the export includes your latest edits.

With Godot available as `godot` on `PATH`, run the headless source checks:

```text
godot --headless --path game --script res://tests/test_sim.gd
godot --headless --path game --script res://tests/test_scene_save.gd
godot --headless --path game --script res://tests/test_character_interaction.gd
```

## Repository and hosting

- `game/`: playable Godot project, scripts, tests, and mesh assets.
- `unity/Greenbox/`: playable Unity project, native scene, C# scripts, and imported voxel meshes.
- `voxel_sources/`: editable `.vox` and Blender sources, with original-source/license records.
- `economy/`: grow economy design notes, engine tests, and balance runner; the playable page and engine live in `public/economy/`.
- `viewer/`: source for the lore/character art viewer and shared palette tools.
- `public/`: committed Godot browser build, Unity export at `public/unity/`, and standalone art viewer at `public/viewer/`, served by Vercel.
- `web/godot-shell.html`: editable browser launcher used during export.
- `docs/`: asset provenance and validation records.
- `scripts/`: Web export and deployment-build verification tools.

Vercel serves `public/` as a static site and runs `npm run build` for verification. The connected [GitHub repository](https://github.com/kairo8080/greenbox) triggers deployments when changes are pushed; production follows the configured production branch. Godot does not need to be installed on Vercel. Threadless export needs no cross-origin isolation headers. Saves remain browser-local.

Game rules and growth timings are fictional prototype mechanics. Asset origins and modifications are recorded in `docs/` and `voxel_sources/`; retain their license files when reusing them. Godot's license and third-party notices are included in `GODOT_LICENSE.txt` and `GODOT_THIRD_PARTY_NOTICES.txt`.
