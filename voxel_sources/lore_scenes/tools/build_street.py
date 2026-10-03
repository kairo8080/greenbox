"""Original ROOTS district street, authored as discrete occupied voxel cubes."""
from lore_common import ROOT, Asset, COL, PALETTE, SceneBuilder, text, leaf_motif


def pavement():
    a = Asset('district_pavement')
    a.box(0, 0, 0, 170, 125, 2, 'slate')
    a.box(0, 36, 2, 170, 125, 4, 'trim')
    a.box(0, 34, 1, 170, 37, 3, 'metal')
    # Paving joints are recessed-color cells, not a texture or a smooth mesh.
    for x in range(0, 170, 12):
        a.box(x, 37, 3, x + 1, 125, 4, 'wall_shadow')
    for y in range(38, 125, 12):
        a.box(0, y, 3, 170, y + 1, 4, 'wall_shadow')
    for x in range(10, 165, 26):
        a.box(x, 15, 1, min(x + 12, 170), 17, 2, 'yellow')
    a.box(0, 0, 0, 170, 2, 2, 'ink')
    a.box(0, 123, 2, 170, 125, 4, 'wall_shadow')
    return a


def roots_shop():
    a = Asset('roots_shop')
    # White masonry and a flat red/gold/green fascia around two open displays.
    a.box(7, 83, 4, 81, 120, 7, 'rasta_green')
    a.box(7, 116, 7, 81, 120, 56, 'wall')
    a.box(7, 83, 7, 11, 117, 56, 'wall')
    a.box(77, 83, 7, 81, 117, 56, 'wall')
    a.box(7, 83, 7, 81, 87, 11, 'wall')
    a.box(7, 83, 40, 81, 87, 56, 'wall')
    # Mullions leave a broad plant display, a central door and seed shelves.
    for x0, x1 in ((38, 43), (55, 60)):
        a.box(x0, 83, 10, x1, 87, 41, 'wall')
    a.box(12, 109, 7, 38, 111, 40, 'blue')
    a.box(60, 109, 7, 77, 111, 40, 'blue')
    a.box(12, 106, 12, 38, 109, 14, 'screen')
    a.box(60, 106, 12, 77, 109, 14, 'screen')
    # Low display sills and narrow stepped window frames.
    for x0, x1 in ((11, 39), (59, 78)):
        a.box(x0, 80, 8, x1, 87, 11, 'rasta_gold')
        a.box(x0, 81, 39, x1, 86, 41, 'rasta_gold')
        a.box(x0, 81, 10, x0 + 1, 86, 40, 'rasta_gold')
        a.box(x1 - 1, 81, 10, x1, 86, 40, 'rasta_gold')
    a.box(43, 85, 7, 55, 88, 40, 'teal')
    a.box(45, 83, 12, 53, 85, 37, 'water')
    a.box(52, 81, 19, 53, 84, 22, 'gold')
    a.box(42, 80, 4, 56, 88, 7, 'rasta_green')
    a.box(7, 79, 41, 81, 84, 57, 'ink')
    a.box(5, 80, 56, 83, 122, 58, 'rasta_green')
    a.box(5, 78, 57, 83, 82, 59, 'rasta_gold')
    a.box(5, 78, 59, 83, 82, 61, 'rasta_red')
    a.box(7, 82, 58, 81, 120, 60, 'rasta_green')
    a.box(7, 118, 60, 81, 120, 62, 'rasta_gold')
    # Seed packets on a real stepped wooden rack in the second window.
    a.box(13, 85, 7, 38, 101, 11, 'wood_light')
    a.box(61, 85, 11, 76, 100, 13, 'wood')
    a.box(61, 88, 13, 76, 100, 15, 'wood_light')
    for x in (62, 68, 73):
        a.box(x, 84, 13, x + 3, 87, 20, 'linen')
        a.box(x + 1, 83, 15, x + 2, 85, 19, 'leaf')
        a.box(x, 83, 17, x + 3, 85, 18, 'leaf')
    return a


def greenbox_shop():
    a = Asset('greenbox_social_corner')
    a.box(89, 85, 4, 162, 120, 7, 'teal')
    a.box(89, 116, 7, 162, 120, 53, 'linen')
    a.box(89, 85, 7, 93, 117, 53, 'linen')
    a.box(158, 85, 7, 162, 117, 53, 'linen')
    a.box(89, 85, 7, 162, 89, 11, 'linen')
    a.box(89, 85, 38, 162, 89, 53, 'linen')
    a.box(112, 85, 10, 119, 89, 39, 'linen')
    a.box(93, 85, 7, 112, 88, 38, 'teal')
    a.box(97, 83, 12, 108, 85, 35, 'water')
    a.box(107, 81, 19, 109, 84, 22, 'gold')
    a.box(93, 82, 4, 113, 89, 7, 'teal')
    a.box(119, 110, 7, 157, 112, 38, 'blue')
    a.box(120, 108, 12, 156, 110, 14, 'screen')
    a.box(118, 82, 8, 159, 89, 11, 'teal')
    a.box(118, 83, 37, 159, 87, 39, 'teal')
    a.box(118, 83, 10, 120, 87, 38, 'teal')
    a.box(157, 83, 10, 159, 87, 38, 'teal')
    a.box(137, 84, 10, 139, 88, 38, 'teal')
    # A small front-visible arcade display gives the corner a social identity.
    a.box(123, 91, 7, 133, 99, 24, 'ink')
    a.box(122, 93, 24, 134, 101, 33, 'violet')
    a.box(124, 90, 25, 132, 94, 31, 'screen')
    a.box(124, 89, 26, 127, 91, 28, 'warm_light')
    a.box(128, 89, 28, 131, 91, 30, 'dress_pink')
    a.box(121, 87, 20, 135, 94, 22, 'teal')
    a.box(123, 86, 22, 124, 89, 24, 'rasta_red')
    a.box(129, 86, 22, 132, 89, 23, 'rasta_gold')
    a.box(136, 90, 7, 157, 105, 11, 'wood_light')
    a.box(89, 81, 39, 162, 86, 54, 'teal')
    a.box(87, 81, 53, 164, 122, 55, 'teal_light')
    a.box(87, 79, 54, 164, 84, 57, 'rasta_gold')
    a.box(89, 118, 55, 162, 120, 57, 'teal')
    # Simple warm wall fixtures are true luminous-color cubes.
    for x in (91, 155):
        a.box(x, 79, 35, x + 3, 86, 37, 'metal')
        a.box(x, 78, 36, x + 3, 81, 38, 'warm_light')
    return a


def bench():
    a = Asset('district_bench')
    for x in (1, 19):
        a.box(x, 2, 0, x + 2, 10, 9, 'ink')
        a.box(x, 9, 7, x + 2, 11, 16, 'ink')
    for y in (2, 5, 8):
        a.box(0, y, 7, 23, y + 2, 9, 'wood_light')
    for z in (10, 13):
        a.box(0, 9, z, 23, 11, z + 2, 'wood_light')
    return a


def lamppost():
    a = Asset('district_lamppost')
    a.box(0, 0, 0, 6, 6, 2, 'ink')
    a.box(2, 2, 2, 4, 4, 39, 'metal')
    a.box(1, 1, 33, 5, 5, 35, 'rasta_gold')
    a.box(0, 0, 38, 6, 6, 40, 'ink')
    a.box(1, 1, 40, 5, 5, 46, 'warm_light')
    a.box(0, 0, 45, 6, 6, 47, 'ink')
    a.box(2, 2, 47, 4, 4, 49, 'rasta_gold')
    return a


def sandwich_board():
    a = Asset('roots_sandwich_board')
    a.box(0, 1, 0, 2, 9, 25, 'wood')
    a.box(27, 1, 0, 29, 9, 25, 'wood')
    a.box(0, 1, 24, 29, 9, 26, 'wood_light')
    a.box(1, 0, 3, 28, 3, 24, 'ink')
    text(a, 'GROW', 3, -1, 5, 'rasta_gold', scale=1, depth=2)
    leaf_motif(a, 14, -1, 14, color='leaf_light')
    return a


def decorative_palm():
    a = Asset('urban_palm')
    a.box(11, 11, 0, 19, 19, 5, 'clay')
    a.box(12, 12, 5, 18, 18, 7, 'soil')
    a.box(14, 14, 7, 16, 16, 35, 'wood')
    for z in range(10, 33, 5):
        a.box(13, 13, z, 17, 17, z + 1, 'wood_light')
    a.box(12, 12, 34, 18, 18, 38, 'leaf_dark')
    # Broad angular fronds curve downward in exact one-cell steps.
    for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        dx, dy = direction
        for distance in range(0, 13):
            cx, cy = 15 + dx * distance, 15 + dy * distance
            z = 36 - max(0, distance - 4) // 2
            if dx:
                a.box(cx - 1, cy - 2, z, cx + 2, cy + 3, z + 2, 'leaf')
                a.box(cx - 1, cy, z + 1, cx + 2, cy + 1, z + 2, 'leaf_light')
            else:
                a.box(cx - 2, cy - 1, z, cx + 3, cy + 2, z + 2, 'leaf')
                a.box(cx, cy - 1, z + 1, cx + 1, cy + 2, z + 2, 'leaf_light')
    return a


def litter_bin():
    a = Asset('district_recycling_bin')
    a.box(0, 0, 0, 8, 8, 10, 'teal')
    a.box(1, 0, 2, 7, 1, 8, 'teal_light')
    a.box(0, 0, 10, 8, 8, 12, 'ink')
    a.box(2, 0, 10, 6, 2, 11, 'metal')
    return a


def main():
    scene = SceneBuilder('roots_street')
    scene.add(pavement())

    roots = roots_shop()
    text(roots, 'ROOTS', 15, 77, 43, 'rasta_gold', scale=2, depth=2)
    scene.add(roots)
    corner = greenbox_shop()
    text(corner, 'GREENBOX', 101, 79, 45, 'white', scale=1, depth=2)
    scene.add(corner)

    scene.add(bench(), (79, 57, 4))
    scene.add(lamppost(), (82, 74, 4))
    scene.add(sandwich_board(), (7, 57, 4))
    palm = decorative_palm()
    scene.add(palm, (-1, 55, 4), name='left_urban_palm')
    scene.add(palm, (139, 49, 4), name='right_urban_palm')
    scene.add(litter_bin(), (105, 66, 4))

    plant = scene.import_asset(ROOT / 'work' / 'bedroom' / 'scene.json',
        asset_name='cannabis_plant_small', alias='cc0_derived_small_plant')
    scene.add(plant, (15, 86, 11), name='roots_display_plant')
    scene.add(plant, (2, 39, 4), name='left_curb_planter')
    scene.add(plant, (146, 39, 4), name='right_curb_planter')
    scene.add(plant, (136, 91, 11), name='greenbox_display_plant')

    grower = scene.import_asset(ROOT / 'outputs' / 'greenbox-chibi-pack' /
        'rasta_grower' / 'rasta_grower.json', alias='chibi_rasta_grower')
    blonde = scene.import_asset(ROOT / 'outputs' / 'greenbox-chibi-pack' /
        'blonde_lady' / 'blonde_lady.json', alias='chibi_blonde_neighbour')
    scene.add(grower, (42, 53, 4), name='grower_at_roots')
    scene.add(blonde, (121, 50, 4), name='neighbour_at_greenbox')

    description = (
        'Original ROOTS district street: a seed and grow-supply co-op beside '
        'the GREENBOX social arcade corner. Raised voxel ROOTS/GREENBOX/GROW '
        'lettering, restrained red/gold/green trims, blue recessed displays, '
        'actual reused CC0-leaf-derived voxel plants, tiled pavement, angular '
        'urban palms, bench, recycling bin, lamppost and two original chibi '
        'neighbours. Inspired by clean compact daytime voxel environments; '
        'all signs, architecture, characters and decorative graphics are '
        'original Greenbox artwork. Fictional game setting without cultivation '
        'recipes. Exact 0.05 m occupied-cube grid and collection palette.'
    )
    scene.save(description, lights=[
        {'source_voxels': [42, 76, 51], 'color': '#ffc136', 'day': 0.35,
         'night': 4.0, 'range': 3.0},
        {'source_voxels': [125, 77, 49], 'color': '#64dfd8', 'day': 0.35,
         'night': 3.5, 'range': 3.0},
        {'source_voxels': [85, 77, 47], 'color': '#ffd987', 'day': 0.3,
         'night': 4.5, 'range': 3.4},
        {'source_voxels': [130, 91, 29], 'color': '#b66cff', 'day': 0.2,
         'night': 2.0, 'range': 1.8},
    ])


if __name__ == '__main__':
    main()
