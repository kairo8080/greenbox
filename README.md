# Greenbox

A small desktop-first voxel grow-room game, with a Unity 6000.2.6f1 project and the original Godot 4.7.2 demo. Walk around a furnished bedroom, care for fictional game plants, harvest for cash and XP, and unlock extra pots and equipment.

**[Play the Unity browser game](https://greenbox-pi.vercel.app/unity/)** · [Original Godot demo](https://greenbox-pi.vercel.app) · [Vercel project](https://vercel.com/kairo8080/greenbox)

The new **[Greenbox Unity project](unity/README.md)** lives in `unity/Greenbox/`, using Unity 6000.2.6f1 and Web Build Support. It imports the same optimized voxel assets with Unity glTFast and has passed a real browser build and gameplay check, including a full harvest and saved progress after reloading. MagicaVoxel remains the editable asset source; Blender exports meshes, and Unity supplies the playable game.

The **[voxel character cast](voxel_sources/character_cast/README.md)** adds a corporate boss, robot, chef, blonde lady, party woman, and skeleton, plus the existing grower with a 45° right-facing pose and lower preview camera. Each includes editable VOX sources, six movable body parts, a neutral GLB, Blender scene, previews, and verification records. The bundled tools reproduce all six new source designs; import the models into Unity to expand the cast.

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
- `public/`: committed Godot browser build, with the Unity export at `public/unity/`, served by Vercel.
- `web/godot-shell.html`: editable browser launcher used during export.
- `docs/`: asset provenance and validation records.
- `scripts/`: Web export and deployment-build verification tools.

Vercel serves `public/` as a static site and runs `npm run build` for verification. The connected [GitHub repository](https://github.com/kairo8080/greenbox) triggers deployments when changes are pushed; production follows the configured production branch. Godot does not need to be installed on Vercel. Threadless export needs no cross-origin isolation headers. Saves remain browser-local.

Game rules and growth timings are fictional prototype mechanics. Asset origins and modifications are recorded in `docs/` and `voxel_sources/`; retain their license files when reusing them. Godot's license and third-party notices are included in `GODOT_LICENSE.txt` and `GODOT_THIRD_PARTY_NOTICES.txt`.
