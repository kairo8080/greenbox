"""Original cubic chef and friendly anatomical skeleton for Greenbox.

Every character has six rigid connected parts. Front is native -Y; Z is up.
The source grid is preserved, including the skeleton's real empty rib spaces.
"""

from __future__ import annotations

import math
from character_common import Asset, save_character, DEFAULT_JOINTS, COL, RGB, PALETTE


def ellipsoid(asset, center, radii, color):
    """Finite occupied cubes sampled at cell centers; no mesh smoothing."""
    for x in range(math.floor(center[0] - radii[0]), math.ceil(center[0] + radii[0])):
        for y in range(math.floor(center[1] - radii[1]), math.ceil(center[1] + radii[1])):
            for z in range(math.floor(center[2] - radii[2]), math.ceil(center[2] + radii[2])):
                if sum(((p + .5 - center[i]) / radii[i]) ** 2
                       for i, p in enumerate((x, y, z))) <= 1:
                    asset.set(x, y, z, color)


def chef_torso():
    a = Asset('torso')
    # The jacket wraps around the whole body, with the apron sitting in front.
    a.box(4, 3, 13, 12, 8, 23, 'chef_white')
    a.box(4, 7, 13, 12, 8, 14, 'linen')
    a.box(11, 7, 14, 12, 8, 21, 'linen')
    # Front apron: broad skirt, narrower bib, waist tie visibly wraps the back.
    a.box(5, 2, 10, 11, 3, 19, 'linen')
    a.box(6, 2, 19, 10, 3, 22, 'linen')
    a.box(4, 3, 18, 12, 8, 19, 'linen')
    a.box(6, 1, 14, 10, 2, 15, 'chef_white')
    a.box(6, 1, 14, 7, 2, 17, 'chef_white')
    a.box(9, 1, 14, 10, 2, 17, 'chef_white')
    a.box(7, 1, 16, 9, 2, 17, 'chef_white')
    # Two independent rows read as a double-breasted chef jacket.
    for x in (5, 10):
        for z in (17, 20, 22):
            a.set(x, 2, z, 'ink')
    a.box(5, 2, 21, 7, 3, 23, 'chef_white')
    a.box(9, 2, 21, 11, 3, 23, 'chef_white')
    # The neckerchief has a raised knot and two finite folded tails.
    a.box(6, 2, 22, 10, 3, 23, 'tie_red')
    a.box(7, 1, 21, 9, 2, 23, 'rasta_red')
    a.box(7, 1, 19, 8, 2, 22, 'tie_red')
    a.box(8, 1, 20, 9, 2, 22, 'rasta_red')
    return a


def chef_head():
    a = Asset('head')
    a.box(6, 4, 23, 10, 7, 25, 'skin_pale')
    a.box(4, 2, 24, 12, 9, 30, 'skin_pale')
    a.box(5, 1, 24, 11, 2, 29, 'skin_pale')
    a.box(3, 4, 26, 4, 7, 28, 'skin_pale')
    a.box(12, 4, 26, 13, 7, 28, 'skin_pale')
    a.box(4, 8, 27, 12, 9, 30, 'hair_brown')
    a.box(4, 2, 28, 5, 9, 30, 'hair_brown')
    a.box(11, 2, 28, 12, 9, 30, 'hair_brown')
    # An adult fictional face with small eyebrows and a friendly short moustache.
    a.set(5, 1, 27, 'ink')
    a.set(10, 1, 27, 'ink')
    a.box(5, 1, 28, 7, 2, 29, 'hair_brown')
    a.box(9, 1, 28, 11, 2, 29, 'hair_brown')
    a.box(7, 0, 26, 9, 2, 28, 'skin_pale')
    a.box(6, 1, 25, 10, 2, 26, 'hair_brown')
    a.box(7, 1, 24, 9, 2, 25, 'lip')
    a.set(5, 1, 26, 'blush')
    a.set(10, 1, 26, 'blush')
    # Toque band and tall pleated column, then five stepped crown puffs.
    a.cylinder(8, 5.5, 30, 32, 4.8, 'linen')
    a.cylinder(8, 5.5, 31, 36, 4.2, 'chef_white')
    for x, y in ((5, 2), (8, 1), (10, 2), (4, 5), (11, 5), (7, 9)):
        for z in range(32, 36):
            if (x, y, z) in a.v:
                a.set(x, y, z, 'linen')
    ellipsoid(a, (8, 5.5, 36), (5.3, 4.2, 2.4), 'chef_white')
    ellipsoid(a, (4.8, 4.5, 37), (2.8, 2.8, 2.8), 'chef_white')
    ellipsoid(a, (11.2, 4.5, 37), (2.8, 2.8, 2.8), 'chef_white')
    ellipsoid(a, (8, 5.7, 38), (3.2, 3.0, 3.0), 'chef_white')
    ellipsoid(a, (5.8, 8, 37), (2.4, 2.4, 2.5), 'chef_white')
    ellipsoid(a, (10.2, 8, 37), (2.4, 2.4, 2.5), 'chef_white')
    return a


def chef_arm(left):
    a = Asset('arm_left' if left else 'arm_right')
    x = 1 if left else 12
    a.box(x, 3, 15, x + 3, 7, 23, 'chef_white')
    a.box(x, 3, 15, x + 3, 7, 17, 'linen')
    a.box(x, 3, 12, x + 3, 7, 15, 'skin_pale')
    a.box(x, 2, 12, x + 3, 3, 14, 'skin_pale')
    a.box(x, 6, 16, x + 1, 7, 21, 'linen')
    if not left:
        # The spoon is part of the right hand's rigid mesh and meets it by faces.
        a.box(14, 3, 13, 17, 5, 14, 'skin_pale')
        a.box(16, 3, 13, 17, 5, 23, 'wood_light')
        ellipsoid(a, (16.5, 4, 24), (2.0, 1.15, 3.0), 'wood_light')
        a.box(16, 3, 24, 17, 4, 26, 'floor_light')
    return a


def chef_leg(left):
    a = Asset('leg_left' if left else 'leg_right')
    x = 4 if left else 9
    a.box(x, 3, 3, x + 3, 7, 13, 'suit')
    a.box(x, 3, 4, x + 1, 4, 11, 'suit_light')
    shoe = 3 if left else 9
    a.box(shoe, 1, 0, shoe + 4, 8, 3, 'ink')
    a.box(shoe, 1, 0, shoe + 4, 8, 1, 'slate')
    a.box(shoe + 1, 2, 2, shoe + 3, 4, 3, 'slate')
    return a


def rib_path(asset, z, narrow=False):
    # Chamfered closed ring in XY. Every segment follows a face-adjacent path.
    if narrow:
        points = [(6, 2), (9, 2), (9, 3), (10, 3), (10, 6), (9, 6),
                  (9, 7), (6, 7), (6, 6), (5, 6), (5, 3), (6, 3), (6, 2)]
    else:
        points = [(5, 2), (10, 2), (10, 3), (11, 3), (11, 6), (10, 6),
                  (10, 7), (5, 7), (5, 6), (4, 6), (4, 3), (5, 3), (5, 2)]
    for start, end in zip(points, points[1:]):
        for x in range(min(start[0], end[0]), max(start[0], end[0]) + 1):
            for y in range(min(start[1], end[1]), max(start[1], end[1]) + 1):
                asset.set(x, y, z, 'bone_shadow' if y == 7 else 'bone')


def skeleton_torso():
    a = Asset('torso')
    # The spine and sternum join real rings; the intervals are entirely empty.
    a.box(7, 6, 13, 9, 8, 23, 'bone_shadow')
    a.box(7, 2, 16, 9, 3, 23, 'bone')
    for z in (17, 19, 21):
        rib_path(a, z, narrow=z == 17)
    # Shoulder blades and clavicles also join the humerus parts by hidden faces.
    a.box(4, 4, 22, 12, 7, 23, 'bone')
    a.box(4, 3, 22, 12, 4, 23, 'bone')
    a.box(5, 6, 20, 7, 7, 23, 'bone_shadow')
    a.box(9, 6, 20, 11, 7, 23, 'bone_shadow')
    # A finite pelvis cup with an open center rather than a filled cuboid.
    a.box(4, 3, 13, 6, 8, 16, 'bone')
    a.box(10, 3, 13, 12, 8, 16, 'bone')
    a.box(5, 6, 13, 11, 8, 16, 'bone_shadow')
    a.box(5, 2, 13, 11, 4, 14, 'bone')
    a.box(6, 3, 14, 10, 4, 15, 'bone')
    # Sacrum links the pelvis to the sternum while leaving the abdomen open.
    a.box(7, 5, 14, 9, 7, 17, 'bone_shadow')
    a.box(7, 3, 16, 9, 6, 17, 'bone_shadow')
    return a


def skeleton_head():
    a = Asset('head')
    a.box(7, 5, 23, 9, 7, 26, 'bone_shadow')
    # Stepped skull dome, cheekbones, and an actual lower jaw volume.
    a.box(4, 2, 25, 12, 9, 31, 'bone')
    a.box(5, 2, 31, 11, 8, 32, 'bone')
    a.box(6, 3, 32, 10, 7, 33, 'bone')
    a.box(5, 1, 26, 11, 2, 31, 'bone')
    a.box(5, 2, 24, 11, 7, 26, 'bone')
    a.box(4, 3, 24, 5, 7, 27, 'bone_shadow')
    a.box(11, 3, 24, 12, 7, 27, 'bone_shadow')
    # The sockets are carved several cells deep. Dark rear cells give them depth
    # while the hole's front and side faces remain explicitly empty occupancy.
    for x0 in (5, 9):
        a.erase(x0, 0, 28, x0 + 2, 5, 30)
        a.box(x0, 5, 28, x0 + 2, 6, 30, 'ink')
    a.erase(7, 0, 27, 9, 4, 28)
    a.box(7, 4, 27, 9, 5, 28, 'ink')
    # Open mouth, raised individual incisors, and a separate continuous chin.
    a.erase(5, 0, 25, 11, 4, 26)
    a.box(5, 4, 25, 11, 5, 26, 'bone_shadow')
    for x in (5, 7, 8, 10):
        a.box(x, 1, 25, x + 1, 4, 26, 'chef_white')
    a.box(5, 2, 24, 11, 4, 25, 'bone')
    # Temple shading follows the skull's back surface, never fills the sockets.
    a.box(4, 7, 26, 5, 9, 30, 'bone_shadow')
    a.box(11, 7, 26, 12, 9, 30, 'bone_shadow')
    return a


def skeleton_arm(left):
    a = Asset('arm_left' if left else 'arm_right')
    x = 1 if left else 12
    a.box(x, 4, 21, x + 3, 7, 23, 'bone')
    a.box(x + 1, 4, 17, x + 2, 6, 22, 'bone')
    a.box(x, 3, 16, x + 3, 6, 18, 'bone_shadow')
    # Two lower-arm rods with real air between them, joined at elbow and palm.
    a.box(x, 4, 13, x + 1, 5, 17, 'bone')
    a.box(x + 2, 4, 13, x + 3, 5, 17, 'bone')
    a.box(x, 3, 11, x + 3, 5, 14, 'bone')
    for dx in (0, 2):
        a.box(x + dx, 2, 11, x + dx + 1, 3, 13, 'bone')
    a.set(x + 1, 2, 12, 'bone_shadow')
    return a


def skeleton_leg(left):
    a = Asset('leg_left' if left else 'leg_right')
    x = 4 if left else 9
    a.box(x + 1, 4, 7, x + 3, 6, 13, 'bone')
    a.box(x, 3, 6, x + 4, 7, 8, 'bone_shadow')
    a.box(x + 1, 2, 6, x + 3, 3, 8, 'bone')
    # Slim paired shin bones meet the broad knee and tarsals.
    a.box(x + 1, 4, 2, x + 2, 6, 7, 'bone')
    a.box(x + 3, 5, 2, x + 4, 6, 7, 'bone_shadow')
    a.box(x, 3, 0, x + 4, 7, 2, 'bone')
    a.box(x, 1, 0, x + 1, 4, 2, 'bone')
    a.box(x + 2, 1, 0, x + 4, 4, 2, 'bone')
    a.box(x, 0, 0, x + 1, 2, 1, 'bone_shadow')
    a.box(x + 2, 0, 0, x + 4, 2, 1, 'bone_shadow')
    return a


def build():
    chef_parts = [chef_torso(), chef_head(), chef_arm(True), chef_arm(False),
                  chef_leg(True), chef_leg(False)]
    save_character('chef', chef_parts,
                   'Original adult fictional chef: tall pleated white toque with stepped crown puffs; '
                   'double-breasted white jacket with two dark button rows, cream apron and pocket, '
                   'red knotted neckerchief, dark trousers and shoes, held dimensional wooden spoon. '
                   'Six connected rigid voxel parts, native -Y front, .05m cubic pitch.',
                   joints=dict(DEFAULT_JOINTS))
    skeleton_parts = [skeleton_torso(), skeleton_head(), skeleton_arm(True),
                      skeleton_arm(False), skeleton_leg(True), skeleton_leg(False)]
    save_character('skeleton', skeleton_parts,
                   'Original friendly cream skeleton with carved deep eye and nose sockets, separated teeth, '
                   'three finite rib rings with real air gaps, connected sternum and spine, open pelvis cup, '
                   'paired slim forearm and shin bones, large knobbly knees and split-toe feet. '
                   'Six connected rigid voxel parts, native -Y front, .05m cubic pitch.',
                   joints=dict(DEFAULT_JOINTS))


if __name__ == '__main__':
    build()
