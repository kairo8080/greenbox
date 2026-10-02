ORIGINAL VOXEL AVATAR

home_grower_character.vox is the assembled editable MagicaVoxel source.
The six additional .vox files are independently editable rigid body parts.
Their normalized canvases omit their original placement; source_manifest.json
records each source offset and joint pivot for reassembly.

The avatar has 2,007 occupied cubes, one connected assembled component,
no overlapping body-part cells, and a 14 x 11 x 34 voxel bounding canvas.
Grid pitch is 0.05 meters: 0.70 x 0.55 meters wide/deep, 1.70 meters tall.
The existing 33-color palette remains exact; six colors are appended at 34–39.

The game GLB is assets/rasta_character.glb. Its root is RastaAvatar; its
direct child meshes are torso, head, arm_left, arm_right, leg_left, leg_right.
GLB is Y-up, facing +Z, with a centered ground root. Joint translations:
torso       ( 0.000, 0.650, 0.000)
head        ( 0.000, 1.150, 0.000)
arm_left    (-0.225, 1.100, 0.000)
arm_right   ( 0.225, 1.100, 0.000)
leg_left    (-0.100, 0.650, 0.000)
leg_right   ( 0.100, 0.650, 0.000)
Each mesh's vertices are local to its joint. Rotate limbs around local X
for walking or care actions. Neutral part rotations are zero.
Rigid touching parts deliberately retain hidden contact faces for animation.
There is no armature or authored animation clip.

rasta_character.blend preserves the six rigid meshes and preview setup.
The front and back PNGs are rendered from this actual cubic geometry.
Camera, lights, and studio ground are excluded from the game GLB.
mesh_validation.json records the 842-triangle, one-material export checks.

This is original artwork for this project, with warm brown skin, dark locs,
a knitted red/gold/green tam, cream striped tee, jeans, and sneakers.
No external character likeness or third-party character asset was used.
