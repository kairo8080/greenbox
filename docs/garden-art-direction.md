# Greenbox Garden art direction

The four references supplied on 2026-10-04 establish a warmer toy-like direction for Greenbox: large readable cubic shapes, compact characters, citrus foliage, turquoise accents and warm sand and soil. The garden scene is the main color guide. The display capsules contribute simple block construction, cream bases and small concentrated color accents.

This is an original Greenbox reinterpretation. Keep the grower, neighbors, seed co-op and beginner grow-room lore. Create Greenbox lettering, leaf icons and equipment shapes ourselves. Do not reproduce the references' characters, logos, cabinet markings, numbered collectible designs or recognizable platform-game motifs. The reference images are private study inputs; their pixels are not included in the public viewer or asset pack.

## Shape language

- Use an oversized cubic head and a short torso, compact hands and short separate legs. Eyes, hair and clothing should read at full-body distance before adding portrait detail.
- Keep planar voxel faces, a consistent integer grid, and matte materials. No bevel or subdivision is needed to convey the style.
- Treat foliage as broad simple stepped masses. Cannabis plants retain their recognizable existing leaf silhouette; use the new green ramp to bring them into the collection.
- Add sparse one-to-three-cell corner chips, stripe fragments and surface flecks. Leave most faces quiet so characters, signs and interaction objects remain easy to read.
- Bedroom furniture and street architecture use the same block sizes and color families as the cast. A warm cream wall or sand-colored plinth gives lime foliage and teal equipment enough contrast.

The existing collection uses 0.05 meters per occupied voxel. Native `.vox` sources are X/Y horizontal and Z up. Game meshes keep flat exposed faces and use GLB's standard Y-up coordinates. Geometry and source palette indices remain authoritative; the Garden preset is a deliberate global recolor rather than an automatic quantization of imported art.

## Color families

| Family | Shadow to highlight | Intended use |
| --- | --- | --- |
| Citrus foliage | `#356206` → `#7eac15` → `#a8d91c` → `#c4e623` | Leaves, grass and playful green signs |
| Turquoise | `#218f89` → `#47d0c5` | Equipment, awnings and selected clothing accents |
| Water | `#61bdaf` | Water accents; opaque voxel source color |
| Sand and floor | `#9b713f` → `#c49a57` → `#e6c97b` | Warm floors, terrain and plinths |
| Soil and wood | `#63452e`, `#5d3929` → `#a36b3d` | Plant soil, furniture and structural wood |
| Clay | `#b76837` → `#e5944a` | Pots and warm equipment details |
| Cream and sage | `#b5c7ab` → `#e7ead8`, `#f5e9bc`, `#fff2d3` | Walls, trim and bedding |
| Sky blue | `#1d5287` → `#3299ca` | Small cool contrasts and blue fabric |
| Raspberry | `#e62c71` → `#ff76af` | Small lamp, poster and fashion accents |
| Gold | `#d9b63a`, `#f4da38`, `#ffe88c` | Badges, lights and selected signs |

Representative unlit-looking patches sampled from the user's images include lime `#c4e623`, olive `#7fad10`, green shadow `#356206`, turquoise `#47d0c5`, sand `#edd78c`, raspberry `#fe538f`, sky blue `#61c5f3` and navy `#1d5287`. The complete preset adapts those families to the existing role system. Raster lighting and shadows affect samples, so these are reference observations rather than claims about the source artists' material palette.

Let green, sand and cream occupy the broad surfaces. Turquoise provides the main cool contrast. Raspberry and bright sky blue are small accents. Preserve useful local contrast between faces, hair, clothes and props.

## Lighting and lore

Default presentation uses soft warm high-key light, contact shadows, a pale neutral environment, matte surfaces and modest highlight intensity. A slight warm key and a cool fill make cubic edges readable. Keep grow-light color localized: restrained pink or mint glow can accent the beginner bedroom without tinting every face or washing out the palette. The existing night view can remain available for mood.

The bedroom is an approachable level-one home-grow scene with a few plants, budget equipment and personal belongings. The ROOTS neighborhood is a community of growers, seed traders and colorful neighbors. Display-capsule inspiration can inform future original Greenbox equipment displays, but capsule art is not a substitute for reusable game characters or modular props.

## Shared indexed palette contract

`viewer/palettes.json` adds preset ID `garden`, labeled **Greenbox Garden**, while preserving the canonical source palette, all role indices and all five earlier presets. Slot 0 remains transparent air. Occupied slots and unused slots retain alpha 255. Slots 64–255 remain unchanged.

All 63 occupied role names are mapped below. Seventeen identity roles keep their exact canonical RGBA values, including natural skin and hair, face ink/white, robot cyan and skeleton bone. Existing identity protection continues to restore those colors after selecting a theme; explicit manual swatch edits take precedence. Shared ink and white also appear in some props, so protection affects those uses as well.

| Index | Existing role | Effective Garden hex | Treatment |
| --- | --- | --- | --- |
| 1 | `ink` | `#1d252a` | Protected identity |
| 2 | `slate` | `#465957` | Garden theme |
| 3 | `wall` | `#e7ead8` | Garden theme |
| 4 | `wall_shadow` | `#b5c7ab` | Garden theme |
| 5 | `trim` | `#f5e9bc` | Garden theme |
| 6 | `floor` | `#c49a57` | Garden theme |
| 7 | `floor_dark` | `#9b713f` | Garden theme |
| 8 | `floor_light` | `#e6c97b` | Garden theme |
| 9 | `wood` | `#5d3929` | Garden theme |
| 10 | `wood_light` | `#a36b3d` | Garden theme |
| 11 | `linen` | `#fff2d3` | Garden theme |
| 12 | `teal` | `#218f89` | Garden theme |
| 13 | `teal_light` | `#47d0c5` | Garden theme |
| 14 | `pink` | `#e62c71` | Garden theme |
| 15 | `pink_light` | `#ff76af` | Garden theme |
| 16 | `warm_light` | `#ffe88c` | Garden theme |
| 17 | `leaf_dark` | `#356206` | Garden theme |
| 18 | `leaf` | `#7eac15` | Garden theme |
| 19 | `leaf_light` | `#a8d91c` | Garden theme |
| 20 | `leaf_tip` | `#c4e623` | Garden theme |
| 21 | `soil` | `#63452e` | Garden theme |
| 22 | `clay` | `#b76837` | Garden theme |
| 23 | `clay_light` | `#e5944a` | Garden theme |
| 24 | `blue` | `#3299ca` | Garden theme |
| 25 | `water` | `#61bdaf` | Garden theme |
| 26 | `white` | `#f6f2dd` | Protected identity |
| 27 | `yellow` | `#f4da38` | Garden theme |
| 28 | `navy` | `#1d5287` | Garden theme |
| 29 | `purple` | `#663569` | Garden theme |
| 30 | `stem` | `#668b21` | Garden theme |
| 31 | `metal` | `#879b95` | Garden theme |
| 32 | `screen` | `#7befbe` | Garden theme |
| 33 | `violet` | `#b565ca` | Garden theme |
| 34 | `rasta_red` | `#e64647` | Garden theme |
| 35 | `rasta_gold` | `#f4d547` | Garden theme |
| 36 | `rasta_green` | `#43822c` | Garden theme |
| 37 | `skin` | `#8e5834` | Protected identity |
| 38 | `locs` | `#271c17` | Protected identity |
| 39 | `skin_light` | `#af7349` | Protected identity |
| 40 | `skin_pale` | `#ebb591` | Protected identity |
| 41 | `skin_tan` | `#bb8254` | Protected identity |
| 42 | `hair_blonde` | `#f3cb5b` | Protected identity |
| 43 | `hair_blonde_shadow` | `#ba8430` | Protected identity |
| 44 | `hair_brown` | `#4a2f22` | Protected identity |
| 45 | `suit` | `#25383a` | Garden theme |
| 46 | `suit_light` | `#496260` | Garden theme |
| 47 | `tie_red` | `#c83657` | Garden theme |
| 48 | `steel` | `#a7c3bd` | Garden theme |
| 49 | `steel_dark` | `#5d7c77` | Garden theme |
| 50 | `chrome` | `#e3f1e6` | Garden theme |
| 51 | `cyan` | `#4ddfe0` | Protected identity |
| 52 | `chef_white` | `#fff8e3` | Garden theme |
| 53 | `bone` | `#e7ddbf` | Protected identity |
| 54 | `bone_shadow` | `#b0a382` | Protected identity |
| 55 | `dress_pink` | `#de3987` | Garden theme |
| 56 | `dress_violet` | `#85418d` | Garden theme |
| 57 | `heel_dark` | `#322333` | Garden theme |
| 58 | `hair_auburn` | `#8b3624` | Protected identity |
| 59 | `lapel` | `#162b2e` | Garden theme |
| 60 | `eye_blue` | `#376486` | Protected identity |
| 61 | `lip` | `#ab3a44` | Protected identity |
| 62 | `gold` | `#d9b63a` | Garden theme |
| 63 | `blush` | `#d47663` | Protected identity |

## Private reference provenance

Study date: **2026-10-04**, using the user's Europe/Chisinau client date. The user supplied these local screenshots; their creator, publication source and redistribution license were not asserted. Only file names, hashes and observations are recorded here. The files were read from `C:/Users/KAIROP~1/AppData/Local/Temp/`; no reference images were copied into the repository or public artifact.

| Reference | Local file | SHA-256 |
| --- | --- | --- |
| Pond garden and turquoise-haired chibi | `codex-clipboard-07a3ffb3-c849-4200-9d15-cfff83d93697.png` | `fb23a1c114fd1192f56a7ab34a339347267e0c087728c2865c97c92c701b5fd3` |
| Raspberry display capsule | `codex-clipboard-41c5c3e7-bc83-4649-9f12-87037fdb584f.png` | `1e02b6e71c3635eae2184758072cd376b2b5b1acf7bbf8a5ade6252356f478c7` |
| Sky-blue display capsule | `codex-clipboard-0740c70f-4a0e-422b-bf73-c22ee4c6263e.png` | `83510d2a4db2acc809c2a7558b6f5b9597455fd43bd321d9c303349d291202b9` |
| Grassy platform and compact character | `codex-clipboard-154c799f-1fbc-4346-8202-ff5b3b80f353.png` | `ec44256981e5ac6041b528711ab45b119ae9b87485f1d750ef3dad8f2527fc5d` |

## Palette validation

The palette update was checked against its pre-edit JSON object: original palette, role definitions, texture mapping, source metadata, identity role/indices/protection fields and all five previous presets are semantically unchanged. The new theme has 256 valid RGBA slots, transparent air, 255 alpha on every non-air slot, all 63 existing occupied roles accounted for, 46 deliberate role changes, 17 protected identity roles preserved and unused slots 64–255 unchanged. The palette JSON was parsed again after writing.
