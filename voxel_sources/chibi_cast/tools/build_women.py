"""Two original Greenbox women with clean, chunky chibi voxel proportions."""
from chibi_common import (
    head_base, soft_box, torso_base, arm_base, leg_base, save_character,
)


def calm_face(head):
    """Small graphic features on a broad cubic face; no anime eye highlights."""
    head.box(5, 0, 21, 7, 2, 23, 'ink')
    head.box(13, 0, 21, 15, 2, 23, 'ink')
    head.box(5, 0, 24, 8, 2, 25, 'hair_blonde_shadow')
    head.box(12, 0, 24, 15, 2, 25, 'hair_blonde_shadow')
    head.box(9, 0, 19, 11, 2, 21, 'skin_pale')
    head.box(9, 0, 18, 11, 2, 19, 'lip')
    return head


def bob_hair(head, main, shade):
    # A single connected cap, stepped side panels and a generous back silhouette.
    head.box(2, 1, 26, 18, 13, 29, main)
    soft_box(head, 1, 0, 27, 19, 14, 30, main)
    head.box(1, 2, 16, 3, 13, 28, main)
    head.box(17, 2, 16, 19, 13, 28, main)
    head.box(3, 11, 16, 17, 14, 28, shade)
    head.box(2, 10, 17, 18, 14, 28, main)
    head.box(1, 3, 15, 4, 12, 18, shade)
    head.box(16, 3, 15, 19, 12, 18, shade)
    # Offset fringe gives the two square heads an authored silhouette.
    head.box(3, 0, 25, 8, 2, 28, main)
    head.box(8, 0, 26, 12, 2, 28, main)
    head.box(12, 0, 27, 17, 2, 29, main)
    return head


def blonde_lady():
    head = calm_face(head_base('skin_pale'))
    bob_hair(head, 'hair_blonde', 'hair_blonde_shadow')
    # The visible side surface uses two deliberate broad color blocks.
    head.box(1, 2, 21, 2, 11, 28, 'hair_blonde_shadow')
    head.box(18, 2, 21, 19, 11, 28, 'hair_blonde_shadow')
    head.box(17, 1, 24, 19, 3, 26, 'white')
    torso = torso_base('teal')
    torso.box(8, 3, 8, 12, 5, 14, 'white')
    torso.box(6, 3, 9, 8, 5, 14, 'teal_light')
    torso.box(12, 3, 9, 14, 5, 14, 'teal_light')
    torso.box(7, 3, 12, 9, 5, 14, 'teal')
    torso.box(11, 3, 12, 13, 5, 14, 'teal')
    torso.box(6, 4, 7, 14, 10, 8, 'navy')
    left_arm = arm_base(True, 'teal', 'skin_pale')
    right_arm = arm_base(False, 'teal', 'skin_pale')
    for arm, x in ((left_arm, 3), (right_arm, 14)):
        arm.box(x, 3, 10, x + 3, 5, 13, 'teal_light')
        arm.box(x, 4, 9, x + 3, 10, 10, 'white')
    left_leg = leg_base(True, 'navy', 'white')
    right_leg = leg_base(False, 'navy', 'white')
    for leg, x in ((left_leg, 5), (right_leg, 10)):
        leg.box(x, 2, 0, x + 5, 11, 1, 'teal')
        leg.box(x + 1, 2, 1, x + 4, 4, 2, 'linen')
    return save_character(
        'blonde_lady',
        [torso, head, left_arm, right_arm, left_leg, right_leg],
        'Original adult blonde woman: broad golden bob with white barrette, '
        'simple dark eyes, teal jacket over a white shirt, compact navy legs '
        'and white sneakers. Two-head chibi proportions and stepped full cubes '
        'take visual inspiration from the chunky, clean palette of The Touryst.',
    )


def party_woman():
    head = calm_face(head_base('skin_pale'))
    head.box(5, 0, 24, 8, 2, 25, 'hair_auburn')
    head.box(12, 0, 24, 15, 2, 25, 'hair_auburn')
    bob_hair(head, 'hair_auburn', 'hair_brown')
    # Auburn, side-parted bob and a small violet barrette make her distinct.
    head.box(3, 0, 24, 5, 2, 28, 'hair_auburn')
    head.box(17, 1, 24, 19, 3, 26, 'dress_violet')
    head.box(3, 0, 18, 4, 2, 20, 'gold')
    head.box(16, 0, 18, 17, 2, 20, 'gold')
    torso = torso_base('dress_pink')
    torso.box(6, 3, 7, 14, 5, 12, 'dress_violet')
    torso.box(7, 3, 12, 13, 5, 14, 'dress_pink')
    torso.box(8, 3, 13, 12, 5, 14, 'skin_pale')
    torso.box(8, 3, 12, 12, 4, 13, 'gold')
    torso.box(9, 3, 11, 11, 4, 12, 'gold')
    torso.box(6, 3, 8, 14, 4, 9, 'dress_pink')
    left_arm = arm_base(True, 'dress_pink', 'skin_pale')
    right_arm = arm_base(False, 'dress_pink', 'skin_pale')
    for arm, x in ((left_arm, 3), (right_arm, 14)):
        arm.box(x, 4, 9, x + 3, 10, 10, 'dress_violet')
    right_arm.box(14, 4, 7, 17, 9, 8, 'gold')
    # The clutch is attached to the left hand and belongs to its rigid mesh.
    left_arm.box(2, 1, 5, 6, 4, 8, 'dress_violet')
    left_arm.box(2, 1, 5, 6, 2, 6, 'heel_dark')
    left_arm.box(2, 1, 7, 6, 2, 8, 'gold')
    left_arm.box(3, 1, 6, 5, 2, 7, 'dress_pink')
    left_leg = leg_base(True, 'dress_violet', 'heel_dark')
    right_leg = leg_base(False, 'dress_violet', 'heel_dark')
    for leg, x in ((left_leg, 5), (right_leg, 10)):
        leg.box(x + 1, 2, 2, x + 4, 5, 3, 'dress_pink')
    return save_character(
        'party_woman',
        [torso, head, left_arm, right_arm, left_leg, right_leg],
        'Original adult party woman: broad auburn bob with violet barrette, '
        'simple dark eyes, modest pink and violet coordinated outfit, square '
        'gold necklace and bracelet, dark shoes and an attached violet clutch. '
        'Two-head chibi proportions and stepped full cubes take visual '
        'inspiration from the clean chunky art direction of The Touryst.',
    )


if __name__ == '__main__':
    blonde_lady()
    party_woman()
