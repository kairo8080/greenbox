"""Original compact Greenbox starter loft, authored as real occupied cubes.

The plants reuse the existing CC0-derived leaf assets. The chibi grower reuses
the current Greenbox character. All architectural motifs and lettering here
are original; the Touryst reference informs the compact, colorful diorama feel.
"""
from copy import deepcopy
from lore_common import ROOT, Asset, COL, SceneBuilder, text, leaf_motif


def floor():
    a = Asset('loft_oak_floor')
    a.box(0, 0, 0, 112, 100, 3, 'wood')
    a.box(0, 0, 3, 112, 100, 4, 'floor')
    for x in range(3, 110):
        for y in range(3, 98):
            plank = x // 8
            stagger = (plank % 2) * 13
            segment = (y + stagger) // 26
            color = ['floor', 'floor_light', 'floor', 'floor_dark'][(plank + segment * 3) % 4]
            if x % 8 == 0 or (y + stagger) % 26 == 0:
                color = 'wood'
            a.set(x, y, 3, color)
    a.box(0, 0, 3, 112, 2, 4, 'wood_light')
    a.box(110, 0, 3, 112, 100, 4, 'wood_light')
    a.box(1, 0, 1, 111, 1, 2, 'navy')
    a.box(1, 0, 2, 111, 1, 3, 'teal')
    a.meta = {'description': 'Warm staggered oak planks with dark seams and a thick diorama edge.'}
    return a


def back_wall():
    # Native y=7 is the inner structural wall. The shelf occupies y=0..7.
    a = Asset('loft_back_wall_neon_window_shelf')
    a.box(0, 7, 0, 112, 10, 54, 'navy')
    a.box(0, 7, 0, 112, 8, 4, 'ink')
    a.box(0, 7, 51, 112, 10, 54, 'teal')
    for x in range(7, 112, 14):
        a.box(x, 6, 5, x + 1, 8, 51, 'suit_light')
    # Night window: raised chunky frame, cyan panes and original city pixels.
    a.box(9, 5, 21, 39, 8, 45, 'wood')
    a.box(11, 4, 23, 37, 6, 43, 'ink')
    a.box(12, 4, 24, 36, 5, 42, 'blue')
    a.box(12, 4, 24, 36, 5, 30, 'navy')
    a.box(12, 4, 30, 36, 5, 35, 'teal')
    for x, height in ((14, 5), (19, 8), (25, 4), (30, 6)):
        a.box(x, 3, 24, x + 3, 5, 24 + height, 'suit')
        a.set(x + 1, 3, 26, 'warm_light')
    a.box(23, 3, 23, 25, 6, 43, 'trim')
    a.box(11, 3, 32, 37, 6, 34, 'trim')
    a.box(8, 3, 20, 40, 8, 22, 'wood_light')
    a.box(7, 4, 23, 10, 7, 45, 'rasta_gold')
    a.box(38, 4, 23, 41, 7, 45, 'rasta_gold')
    a.box(6, 4, 45, 42, 7, 47, 'wood_light')
    a.box(30, 4, 37, 34, 5, 41, 'warm_light')
    # A raised, original Greenbox wordmark uses occupied cube lettering.
    a.box(46, 5, 41, 106, 8, 53, 'ink')
    a.box(46, 4, 41, 106, 6, 43, 'pink_light')
    text(a, 'GREENBOX', 51, 4, 44, 'cyan')
    a.box(45, 5, 43, 47, 7, 51, 'teal_light')
    a.box(105, 5, 43, 107, 7, 51, 'teal_light')
    # Shelf and an intentionally tiny collection of books, radio and mug.
    a.box(43, 0, 27, 72, 8, 29, 'wood_light')
    a.box(44, 4, 23, 46, 8, 28, 'wood')
    a.box(69, 4, 23, 71, 8, 28, 'wood')
    for x, height, color in ((45, 7, 'rasta_red'), (49, 8, 'rasta_gold'), (53, 6, 'rasta_green')):
        a.box(x, 1, 29, x + 3, 6, 29 + height, color)
        a.box(x, 0, 31, x + 2, 2, 32, 'linen')
    a.box(58, 1, 29, 67, 6, 34, 'ink')
    a.box(59, 0, 30, 64, 2, 33, 'slate')
    for x in (59, 61, 63):
        a.box(x, 0, 30, x + 1, 1, 33, 'metal')
    a.set(65, 0, 31, 'rasta_gold')
    a.box(68, 2, 29, 71, 5, 33, 'clay_light')
    a.meta = {'description': 'Dark blue back wall with a night-city window, gold curtains, cube neon wordmark and wall shelf.'}
    return a


def left_wall():
    a = Asset('loft_teal_left_wall_door_xp')
    a.box(0, 0, 0, 3, 97, 54, 'teal')
    a.box(2, 0, 0, 3, 97, 4, 'ink')
    a.box(0, 0, 51, 3, 97, 54, 'navy')
    for y in range(0, 97, 12):
        a.box(2, y, 4, 3, y + 1, 51, 'teal_light')
    # Low-budget bedroom door with two inset panels and a square gold handle.
    a.box(3, 12, 0, 5, 37, 42, 'wood')
    a.box(4, 14, 2, 5, 35, 40, 'wood_light')
    a.box(4, 16, 5, 5, 33, 18, 'wood')
    a.box(4, 16, 23, 5, 33, 37, 'wood')
    a.box(5, 31, 19, 6, 34, 21, 'gold')
    # Wall plaque reads XP 01 along Y/Z, raised from the room-facing +X wall.
    plaque = Asset('plaque_glyphs')
    text(plaque, 'XP 01', 0, 0, 0, 'warm_light')
    a.box(3, 44, 32, 5, 78, 44, 'ink')
    a.box(4, 44, 32, 5, 78, 34, 'rasta_red')
    a.box(4, 44, 34, 5, 78, 35, 'rasta_gold')
    a.box(4, 44, 35, 5, 78, 36, 'rasta_green')
    for (x, y, z), color in plaque.v.items():
        a.set(5, 46 + x, 37 + z, color)
    # Original leaf picture above the foot of the bed, also facing +X.
    motif = Asset('original_leaf_picture')
    motif.box(0, 0, 0, 19, 1, 20, 'wood_light')
    motif.box(1, 0, 1, 18, 1, 19, 'linen')
    leaf_motif(motif, 9, 0, 5, 'leaf_dark')
    a.box(3, 69, 13, 4, 88, 33, 'wood')
    for (x, y, z), color in motif.v.items():
        a.set(4, 69 + x, 13 + z, color)
    a.meta = {'description': 'Teal slatted wall, closed wooden bedroom door, raised XP 01 plaque and original leaf picture.', 'player_level': 1}
    return a


def rug():
    a = Asset('loft_original_leaf_rug')
    a.box(0, 0, 0, 36, 28, 1, 'navy')
    a.box(1, 1, 0, 35, 27, 1, 'linen')
    a.box(3, 3, 0, 33, 25, 1, 'teal')
    for x in range(3, 33):
        for y in (2, 25):
            a.set(x, y, 0, ['rasta_red', 'rasta_gold', 'rasta_green'][(x // 4) % 3])
    for y in range(3, 25):
        for x in (2, 33):
            a.set(x, y, 0, ['rasta_red', 'rasta_gold', 'rasta_green'][(y // 4) % 3])
    leaf_motif(a, 18, 9, 0, 'leaf_light', scale=1, plane='xy')
    # Wider seven-lobe stitched shape keeps the emblem visible at room scale.
    for end in ((11, 13, 0), (12, 17, 0), (15, 20, 0), (18, 22, 0), (21, 20, 0), (24, 17, 0), (25, 13, 0)):
        a.line((18, 11, 0), end, 'rasta_green', radius=0)
    a.line((18, 5, 0), (18, 15, 0), 'rasta_gold')
    for x in (6, 29):
        for y in (6, 21):
            a.box(x, y, 0, x + 2, y + 2, 1, 'rasta_gold')
    a.meta = {'description': 'Original seven-lobe leaf rug with a red, gold and green stitched border. Icon is original decoration, not a source leaf substitute.'}
    return a


def starter_rack():
    a = Asset('loft_budget_three_pot_light_rack')
    for x in (0, 50):
        for y in (0, 34):
            a.box(x, y, 0, x + 2, y + 2, 43, 'metal')
            a.box(x, y, 0, x + 2, y + 2, 2, 'ink')
    # Open access at the front; side braces sit above the pots' floor zone.
    for x in (0, 50):
        a.box(x, 0, 39, x + 2, 36, 43, 'slate')
        a.box(x, 0, 2, x + 2, 36, 4, 'slate')
    for y in (0, 34):
        a.box(0, y, 40, 52, y + 2, 43, 'slate')
    a.box(0, 21, 41, 52, 23, 43, 'metal')
    # Two practical boards hanging on a common top bar, with visible leads.
    for x in (5, 29):
        a.box(x, 9, 39, x + 18, 34, 41, 'metal')
        a.box(x + 7, 21, 40, x + 9, 23, 43, 'ink')
        a.box(x + 1, 10, 38, x + 17, 13, 39, 'pink_light')
        a.box(x + 1, 20, 38, x + 17, 23, 39, 'cyan')
        a.box(x + 1, 30, 38, x + 17, 33, 39, 'violet')
    a.box(47, 0, 24, 52, 4, 32, 'ink')
    a.box(48, 0, 28, 51, 1, 31, 'screen')
    a.set(48, 0, 26, 'pink_light')
    a.set(50, 0, 26, 'white')
    # A cyan cable follows the back post, as a geometric painted strip.
    a.box(50, 35, 5, 51, 36, 35, 'cyan')
    a.box(2, 34, 0, 14, 36, 3, 'ink')
    a.meta = {'description': 'Low-budget open metal rack holding two flat LED boards, a tiny controller and an exposed cyan cable.', 'category': 'starter_equipment', 'gameplay_level': 1}
    return a


def dresser():
    a = Asset('loft_low_dresser_and_radio')
    for x in (1, 18):
        for y in (1, 12):
            a.box(x, y, 0, x + 2, y + 2, 3, 'wood')
    a.box(0, 0, 3, 21, 15, 15, 'wood')
    a.box(0, 0, 15, 21, 15, 17, 'wood_light')
    for z in (4, 9):
        a.box(1, 0, z, 20, 1, z + 4, 'wood_light')
        a.box(9, 0, z + 1, 12, 1, z + 2, 'gold')
    a.box(2, 5, 17, 12, 13, 23, 'ink')
    a.box(3, 4, 18, 9, 6, 22, 'metal')
    for x in (3, 5, 7):
        a.box(x, 4, 18, x + 1, 5, 22, 'slate')
    a.set(10, 4, 20, 'rasta_gold')
    a.box(13, 7, 17, 19, 13, 18, 'rasta_red')
    a.box(13, 7, 18, 19, 13, 19, 'linen')
    a.box(13, 7, 19, 19, 13, 20, 'rasta_green')
    a.meta = {'description': 'Low oak drawer chest with a small retro speaker and stacked paper notebooks.'}
    return a


def shoe_box():
    a = Asset('loft_reused_cardboard_storage')
    a.box(0, 0, 0, 12, 10, 7, 'floor_light')
    a.box(0, 0, 7, 12, 10, 8, 'wood_light')
    a.box(5, 0, 0, 7, 10, 8, 'linen')
    a.box(2, 0, 3, 4, 1, 5, 'ink')
    a.box(8, 0, 3, 10, 1, 5, 'ink')
    a.meta = {'description': 'Reused small cardboard box with tape and hand-drawn square storage marks.'}
    return a


def main():
    scene = SceneBuilder('starter_loft')
    scene.add(floor())
    scene.add(back_wall(), (0, 90, 4))
    scene.add(left_wall(), (0, 0, 4))
    source = ROOT / 'work' / 'bedroom' / 'scene.json'
    # Borrow the original bed geometry and author a new broad Rasta blanket.
    bed = scene.import_asset(source, 'teal_single_bed', alias='loft_rasta_single_bed')
    before = deepcopy(bed['voxels'])
    for cell in bed['voxels']:
        x, y, z, color = cell
        if 1 <= x < 28 and 1 <= y < 29 and 12 <= z < 17:
            if y < 9:
                cell[3] = COL['rasta_red']
            elif y < 17:
                cell[3] = COL['rasta_gold']
            else:
                cell[3] = COL['rasta_green']
    bed.setdefault('metadata', {})['modifications'] = 'Existing cubic bed geometry retained; blanket recolored into broad original red/gold/green bands.'
    assert [[*cell[:3]] for cell in before] == [[*cell[:3]] for cell in bed['voxels']]
    scene.add(bed, (9, 44, 4))
    scene.add(scene.import_asset(source, 'bedside_table', alias='loft_warm_bedside_table'), (39, 73, 4))
    scene.add(scene.import_asset(source, 'slippers', alias='loft_slippers'), (15, 33, 4))
    scene.add(scene.import_asset(source, 'desk', alias='loft_work_desk'), (77, 15, 4))
    chair = scene.import_asset(source, 'chair', alias='loft_desk_chair')
    dx, dy, dz = chair['dimensions']
    chair['voxels'] = [[dx - 1 - x, dy - 1 - y, z, c] for x, y, z, c in chair['voxels']]
    chair['metadata']['modifications'] = 'Rotated 180 degrees on the same integer grid to face the desk.'
    scene.add(chair, (85, 3, 4))
    scene.add(dresser(), (9, 10, 4))
    scene.add(shoe_box(), (96, 33, 4))
    scene.add(rug(), (39, 24, 4))
    scene.add(starter_rack(), (58, 53, 4))
    # Source-derived geometry and full licensing/projection metadata are retained.
    scene.add(scene.import_asset(source, 'cannabis_plant_small', alias='loft_plant_small_cc0_leaf'), (62, 57, 4))
    scene.add(scene.import_asset(source, 'cannabis_plant_medium', alias='loft_plant_medium_cc0_leaf'), (86, 57, 4))
    scene.add(scene.import_asset(source, 'cannabis_plant_bushy', alias='loft_plant_bushy_cc0_leaf'), (74, 76, 4))
    scene.add(scene.import_asset(source, 'watering_can', alias='loft_watering_can'), (77, 37, 4))
    scene.add(scene.import_asset(source, 'small_fan', alias='loft_air_fan'), (46, 88, 4))
    grower = scene.import_asset(ROOT / 'outputs' / 'greenbox-chibi-pack' / 'rasta_grower' / 'rasta_grower.json', alias='loft_level_one_chibi_grower')
    grower['metadata']['player_level'] = 1
    scene.add(grower, (47, 31, 5))
    # Placement checks inspect real occupied cells, including the broad chibi head.
    models = {asset['name']: asset for asset in scene.assets}
    placed = {}
    character_cells = set()
    for instance in scene.instances:
        cells = {
            (x + instance['offset'][0], y + instance['offset'][1], z + instance['offset'][2])
            for x, y, z, color in models[instance['asset']]['voxels']
        }
        if instance['name'] == 'loft_level_one_chibi_grower':
            character_cells = cells
        placed[instance['name']] = cells
    intersections = {name: len(cells & character_cells) for name, cells in placed.items() if name != 'loft_level_one_chibi_grower' and cells & character_cells}
    assert not intersections, f'Grower intersects scenery: {intersections}'
    scene.save(
        'Original Greenbox XP 01 starter bedroom loft: an open 5.6 by 5.0 meter '
        'voxel diorama with dark navy/teal walls, oak floor, warm Rasta-striped '
        'sleep nook, original leaf rug and raised GREENBOX sign, modest desk, '
        'books/radio/storage details, three preserved CC0-leaf-derived plant '
        'props, a budget light rack, watering can and fan. A current chibi '
        'grower stands on the rug with no prop intersections. Cozy compact '
        'arcade-diorama composition takes inspiration from The Touryst while '
        'using original architecture and graphics. Game-art stages only; no '
        'real cultivation parameters or gameplay implementation.',
        lights=[
            {'name': 'warm_bedside', 'source_voxels': [44, 78, 24], 'color': '#ffd987', 'day': 1.0, 'night': 3.5, 'range': 2.8},
            {'name': 'magenta_starter_lights', 'source_voxels': [73, 70, 41], 'color': '#ff6dcc', 'day': 0.8, 'night': 3.0, 'range': 2.8},
            {'name': 'cyan_starter_lights', 'source_voxels': [96, 74, 41], 'color': '#4ddfe0', 'day': 0.7, 'night': 2.8, 'range': 2.8},
            {'name': 'window_cool_fill', 'source_voxels': [24, 94, 35], 'color': '#6ab7e0', 'day': 0.6, 'night': 1.6, 'range': 2.4},
            {'name': 'neon_wordmark', 'source_voxels': [76, 94, 52], 'color': '#4ddfe0', 'day': 0.3, 'night': 1.2, 'range': 2.0},
        ],
    )


if __name__ == '__main__':
    main()
