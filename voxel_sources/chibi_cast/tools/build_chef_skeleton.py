"""Two original compact Greenbox characters, authored as occupied cubic cells."""
from chibi_common import (
    Asset, head_base, torso_base, arm_base, leg_base, soft_box, save_character,
)


def chef():
    head = head_base('skin_pale')
    # A quiet, adult block face: small solid eyes, square nose and moustache.
    head.box(5, 0, 22, 7, 2, 24, 'ink')
    head.box(13, 0, 22, 15, 2, 24, 'ink')
    head.box(9, 0, 20, 11, 2, 22, 'skin_pale')
    head.box(7, 0, 19, 13, 2, 20, 'hair_brown')
    head.box(8, 0, 18, 12, 2, 19, 'skin_tan')
    # Two small ears and hair at the back keep the head readable in profile.
    head.box(1, 4, 20, 3, 8, 23, 'skin_pale')
    head.box(17, 4, 20, 19, 8, 23, 'skin_pale')
    head.box(3, 11, 18, 17, 13, 23, 'hair_brown')
    head.box(2, 4, 24, 4, 10, 27, 'hair_brown')
    head.box(16, 4, 24, 18, 10, 27, 'hair_brown')
    # The toque consists of stepped blocks rather than a smoothed hat mesh.
    head.box(2, 1, 27, 18, 13, 30, 'chef_white')
    soft_box(head, 3, 2, 30, 9, 12, 34, 'chef_white')
    soft_box(head, 7, 2, 30, 13, 12, 35, 'chef_white')
    soft_box(head, 11, 2, 30, 17, 12, 34, 'chef_white')
    head.box(3, 1, 28, 17, 2, 29, 'linen')

    torso = torso_base('chef_white')
    torso.box(6, 3, 7, 14, 4, 8, 'linen')
    torso.box(8, 3, 12, 12, 4, 14, 'rasta_red')
    torso.box(9, 3, 9, 11, 4, 12, 'rasta_red')
    for z in (9, 11, 13):
        torso.set(7, 3, z, 'ink')
        torso.set(12, 3, z, 'ink')

    left_arm = arm_base(True, 'chef_white', 'skin_pale')
    right_arm = arm_base(False, 'chef_white', 'skin_pale')
    left_arm.box(3, 3, 9, 6, 4, 10, 'linen')
    right_arm.box(14, 3, 9, 17, 4, 10, 'linen')
    # One chunky wooden spoon stays connected to the right hand and clear of
    # the head. It belongs to the arm so the whole utensil can move with it.
    right_arm.box(17, 5, 8, 20, 7, 10, 'wood_light')
    right_arm.box(19, 5, 9, 20, 7, 15, 'wood_light')
    soft_box(right_arm, 18, 4, 14, 22, 8, 18, 'wood_light')
    right_arm.box(19, 4, 15, 21, 5, 17, 'wood')

    legs = [leg_base(True, 'navy', 'ink'), leg_base(False, 'navy', 'ink')]
    save_character('chef', [torso, head, left_arm, right_arm, *legs],
        'Original compact chibi chef: oversized stepped head, tall block toque, '
        'small solid eyes, moustache, red neckerchief, double-button coat and '
        'a connected wooden spoon; short sturdy legs and six movable parts.')


def skeleton():
    head = Asset('head')
    head.box(8, 5, 14, 12, 9, 17, 'bone')
    soft_box(head, 4, 2, 15, 16, 12, 20, 'bone')
    soft_box(head, 2, 1, 18, 18, 13, 28, 'bone')
    # Dark socket cells are part of the actual skull surface, not textures.
    head.box(5, 1, 22, 8, 2, 25, 'ink')
    head.box(12, 1, 22, 15, 2, 25, 'ink')
    head.box(9, 1, 20, 11, 2, 22, 'ink')
    head.box(5, 1, 25, 8, 2, 26, 'bone_shadow')
    head.box(12, 1, 25, 15, 2, 26, 'bone_shadow')
    head.box(6, 2, 16, 14, 3, 18, 'ink')
    for x in (6, 8, 10, 12):
        head.box(x, 2, 17, x + 1, 3, 19, 'bone')
    head.box(3, 4, 18, 4, 10, 21, 'bone_shadow')
    head.box(16, 4, 18, 17, 10, 21, 'bone_shadow')

    torso = Asset('torso')
    torso.box(6, 5, 7, 14, 10, 9, 'bone')
    torso.box(9, 7, 8, 11, 9, 14, 'bone')
    torso.box(9, 4, 9, 11, 6, 14, 'bone')
    torso.box(6, 5, 12, 14, 9, 14, 'bone')
    for z in (9, 11):
        # Each rib is attached both to the sternum and to the spine.
        torso.box(6, 4, z, 14, 6, z + 1, 'bone')
        torso.box(6, 5, z, 8, 10, z + 1, 'bone')
        torso.box(12, 5, z, 14, 10, z + 1, 'bone')
        torso.box(7, 8, z, 13, 10, z + 1, 'bone')
    torso.box(7, 4, 7, 13, 5, 8, 'bone_shadow')

    arms = []
    for left in (True, False):
        x = 3 if left else 14
        arm = Asset('arm_left' if left else 'arm_right')
        arm.box(x, 5, 11, x + 3, 9, 14, 'bone')
        arm.box(x + 1, 6, 8, x + 2, 8, 12, 'bone')
        arm.box(x, 5, 8, x + 3, 9, 10, 'bone_shadow')
        arm.box(x, 4, 6, x + 3, 9, 8, 'bone')
        for dx in (0, 2):
            arm.box(x + dx, 3, 6, x + dx + 1, 5, 7, 'bone')
        arms.append(arm)

    legs = []
    for left in (True, False):
        x = 6 if left else 11
        leg = Asset('leg_left' if left else 'leg_right')
        leg.box(x, 5, 5, x + 3, 9, 7, 'bone')
        leg.box(x + 1, 6, 2, x + 2, 8, 6, 'bone')
        leg.box(x, 5, 3, x + 3, 9, 4, 'bone_shadow')
        leg.box(5 if left else 10, 3, 0,
                10 if left else 15, 10, 3, 'bone')
        legs.append(leg)

    save_character('skeleton', [torso, head, *arms, *legs],
        'Original compact chibi skeleton: oversized cubic skull, solid square '
        'sockets and alternating block teeth, attached open ribcage and spine, '
        'short articulated bone limbs and broad feet; six movable parts.')


if __name__ == '__main__':
    chef()
    skeleton()
