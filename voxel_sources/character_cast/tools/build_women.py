"""Original blonde and party-going adult women for Greenbox's cubic avatar cast.

Only authors the two owned character folders through character_common. Every
avatar uses exactly six disjoint, face-connected rigid voxel parts. Native Z is
up and the face looks toward -Y; the palette and .05 m grid are shared.
"""

from character_common import Asset, save_character, DEFAULT_JOINTS, COL, RGB, PALETTE


def blonde_torso():
    a = Asset("torso")
    # A softly fitted teal jacket over a light blouse: narrower waist, modest
    # shoulder width, open center, lapels, hem and two small front pockets.
    a.box(5, 3, 13, 11, 8, 19, "teal")
    a.box(4, 3, 18, 12, 8, 23, "teal")
    a.box(5, 2, 14, 11, 3, 22, "teal")
    a.box(7, 2, 16, 9, 3, 23, "linen")
    a.box(6, 2, 20, 7, 3, 23, "teal_light")
    a.box(9, 2, 20, 10, 3, 23, "teal_light")
    a.box(4, 2, 20, 5, 3, 23, "teal_light")
    a.box(11, 2, 20, 12, 3, 23, "teal_light")
    a.box(5, 2, 15, 7, 3, 16, "teal_light")
    a.box(9, 2, 15, 11, 3, 16, "teal_light")
    a.box(5, 3, 13, 11, 8, 14, "navy")
    a.set(8, 2, 18, "gold")
    return a


def blonde_head():
    a = Asset("head")
    a.box(6, 4, 23, 10, 7, 26, "skin_pale")
    a.box(5, 2, 25, 11, 9, 31, "skin_pale")
    a.box(5, 1, 26, 11, 2, 30, "skin_pale")
    # Golden shoulder-length bob, visibly deeper at the back and stepped at
    # the crown. Side pieces stop above the arm geometry; no shared cells.
    a.box(4, 8, 23, 12, 10, 32, "hair_blonde_shadow")
    a.box(3, 4, 24, 5, 9, 32, "hair_blonde_shadow")
    a.box(11, 4, 24, 13, 9, 32, "hair_blonde_shadow")
    a.box(4, 1, 30, 12, 10, 32, "hair_blonde")
    a.box(4, 2, 32, 12, 9, 33, "hair_blonde")
    a.box(5, 3, 33, 11, 8, 34, "hair_blonde")
    a.box(4, 1, 28, 5, 5, 32, "hair_blonde")
    a.box(5, 1, 30, 7, 3, 32, "hair_blonde")
    a.box(7, 1, 31, 11, 3, 32, "hair_blonde")
    a.box(3, 5, 25, 4, 8, 31, "hair_blonde")
    a.box(12, 5, 25, 13, 8, 31, "hair_blonde")
    a.box(5, 9, 24, 6, 10, 32, "hair_blonde")
    a.box(9, 9, 24, 10, 10, 32, "hair_blonde")
    a.box(7, 3, 32, 8, 8, 34, "hair_blonde_shadow")
    # A calm adult fictional face; blue eyes, tiny brows, blush and lip color.
    a.set(6, 1, 28, "eye_blue")
    a.set(9, 1, 28, "eye_blue")
    a.set(6, 1, 29, "hair_blonde_shadow")
    a.set(9, 1, 29, "hair_blonde_shadow")
    a.box(7, 0, 27, 9, 2, 28, "skin_pale")
    a.box(7, 1, 26, 9, 2, 27, "lip")
    a.set(5, 1, 27, "blush")
    a.set(10, 1, 27, "blush")
    return a


def blonde_arm(left):
    a = Asset("arm_left" if left else "arm_right")
    x = 1 if left else 12
    a.box(x, 3, 16, x + 3, 7, 23, "teal")
    a.box(x, 3, 15, x + 3, 7, 17, "teal_light")
    a.box(x, 3, 12, x + 3, 7, 15, "skin_pale")
    a.box(x + (1 if left else 0), 2, 12, x + (3 if left else 2), 3, 14, "skin_pale")
    a.set(x + 1, 2, 13, "blush")
    return a


def blonde_leg(left):
    a = Asset("leg_left" if left else "leg_right")
    x = 5 if left else 9
    a.box(x, 3, 3, x + 3, 7, 13, "navy")
    a.box(x, 3, 4, x + 1, 4, 12, "slate")
    shoe_x = 4 if left else 9
    a.box(shoe_x, 1, 0, shoe_x + 4, 8, 1, "white")
    a.box(shoe_x, 1, 1, shoe_x + 4, 8, 3, "linen")
    a.box(shoe_x, 1, 1, shoe_x + 4, 3, 3, "white")
    a.box(shoe_x + 1, 3, 2, shoe_x + 3, 4, 3, "white")
    return a


def party_torso():
    a = Asset("torso")
    a.box(4, 2, 13, 12, 8, 16, "dress_violet")
    a.box(5, 2, 15, 11, 8, 21, "dress_violet")
    a.box(4, 3, 20, 12, 8, 23, "dress_violet")
    # A knee-length flared skirt is a connected shell belonging to torso.
    # Its interior intentionally leaves the two leg shafts entirely disjoint.
    a.box(3, 1, 9, 14, 3, 13, "dress_violet")
    a.box(3, 7, 9, 14, 9, 13, "dress_violet")
    a.box(3, 3, 9, 5, 7, 13, "dress_violet")
    a.box(12, 3, 9, 14, 7, 13, "dress_violet")
    # Contrasting pink hem, modest waist sash and asymmetrical front pleat.
    a.box(3, 1, 9, 14, 3, 10, "dress_pink")
    a.box(3, 7, 9, 14, 9, 10, "dress_pink")
    a.box(3, 3, 9, 5, 7, 10, "dress_pink")
    a.box(12, 3, 9, 14, 7, 10, "dress_pink")
    a.box(4, 2, 15, 12, 3, 16, "dress_pink")
    a.box(5, 1, 10, 7, 2, 13, "dress_pink")
    a.box(6, 2, 20, 10, 3, 23, "skin_tan")
    a.box(7, 1, 21, 9, 2, 23, "skin_tan")
    # Gold necklace remains attached to the actual blouse/neckline cubes.
    for x, z in [(6, 21), (9, 21), (7, 20), (8, 20), (7, 19)]:
        a.set(x, 1, z, "gold")
    a.set(8, 2, 15, "gold")
    return a


def party_head():
    a = Asset("head")
    a.box(6, 4, 23, 10, 7, 26, "skin_tan")
    a.box(5, 2, 25, 11, 9, 31, "skin_tan")
    a.box(5, 1, 26, 11, 2, 30, "skin_tan")
    a.box(4, 3, 26, 5, 6, 29, "skin_tan")
    a.box(11, 3, 26, 12, 6, 29, "skin_tan")
    # Auburn waves with a darker underside, broader and taller than the bob.
    a.box(4, 8, 23, 12, 11, 32, "hair_brown")
    a.box(3, 5, 24, 5, 10, 33, "hair_brown")
    a.box(11, 5, 24, 13, 10, 33, "hair_brown")
    a.box(3, 2, 30, 13, 11, 33, "hair_auburn")
    a.box(4, 3, 33, 12, 10, 34, "hair_auburn")
    a.box(5, 4, 34, 11, 9, 35, "hair_auburn")
    a.box(2, 4, 27, 4, 9, 32, "hair_auburn")
    a.box(12, 4, 27, 14, 9, 32, "hair_auburn")
    a.box(3, 3, 26, 4, 7, 30, "hair_auburn")
    a.box(12, 3, 26, 13, 7, 30, "hair_auburn")
    a.box(4, 2, 28, 5, 5, 32, "hair_auburn")
    a.box(5, 1, 30, 8, 3, 32, "hair_auburn")
    a.box(8, 1, 31, 11, 3, 33, "hair_auburn")
    a.box(5, 10, 24, 6, 11, 32, "hair_auburn")
    a.box(9, 10, 24, 10, 11, 32, "hair_auburn")
    a.box(7, 4, 33, 8, 9, 35, "hair_brown")
    # Earrings touch ear cubes, never float separately from the head part.
    a.set(4, 2, 26, "gold")
    a.set(11, 2, 26, "gold")
    a.set(6, 1, 28, "hair_brown")
    a.set(9, 1, 28, "hair_brown")
    a.set(6, 1, 29, "hair_auburn")
    a.set(9, 1, 29, "hair_auburn")
    a.box(7, 0, 27, 9, 2, 28, "skin_tan")
    a.box(7, 1, 26, 9, 2, 27, "lip")
    a.set(5, 1, 27, "blush")
    a.set(10, 1, 27, "blush")
    return a


def party_arm(left):
    a = Asset("arm_left" if left else "arm_right")
    x = 1 if left else 12
    a.box(x, 3, 13, x + 3, 7, 23, "skin_tan")
    a.box(x, 3, 21, x + 3, 7, 23, "dress_violet")
    a.box(x, 2, 14, x + 3, 3, 15, "gold")
    if not left:
        # One small ordinary clutch, carried as part of the rigid right hand.
        a.box(14, 1, 13, 18, 4, 16, "dress_pink")
        a.box(14, 1, 13, 18, 2, 14, "heel_dark")
        a.box(15, 1, 16, 17, 4, 17, "gold")
        a.set(16, 0, 15, "gold")
    return a


def party_leg(left):
    a = Asset("leg_left" if left else "leg_right")
    x = 5 if left else 9
    a.box(x, 3, 4, x + 3, 7, 13, "skin_tan")
    shoe_x = 4 if left else 9
    # Cubic ankle boots with solid uppers, a short block heel and toe contact.
    a.box(shoe_x, 1, 1, shoe_x + 4, 8, 4, "heel_dark")
    a.box(x, 3, 3, x + 3, 7, 6, "heel_dark")
    a.box(shoe_x, 1, 0, shoe_x + 4, 3, 1, "heel_dark")
    a.box(shoe_x + 1, 6, 0, shoe_x + 3, 8, 1, "heel_dark")
    a.box(x, 2, 5, x + 3, 3, 6, "gold")
    return a


def build():
    blonde = [blonde_torso(), blonde_head(), blonde_arm(True), blonde_arm(False),
              blonde_leg(True), blonde_leg(False)]
    blonde_joints = dict(DEFAULT_JOINTS)
    blonde_joints.update(leg_left=(6.5, 5.5, 13), leg_right=(10.5, 5.5, 13))
    save_character(
        "blonde_lady", blonde,
        "Original fictional adult woman with a golden shoulder-length bob, blue eyes, teal jacket over a light blouse, navy trousers and white sneakers",
        joints=blonde_joints,
    )
    party = [party_torso(), party_head(), party_arm(True), party_arm(False),
             party_leg(True), party_leg(False)]
    party_joints = dict(DEFAULT_JOINTS)
    party_joints.update(leg_left=(6.5, 5.5, 13), leg_right=(10.5, 5.5, 13))
    save_character(
        "party_woman", party,
        "Original fictional adult woman with voluminous auburn waves, a violet knee-length dress with pink sash and hem, gold necklace and earrings, block-heeled ankle boots and a small pink clutch",
        joints=party_joints,
    )


if __name__ == "__main__":
    build()
