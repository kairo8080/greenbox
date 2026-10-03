"""Original full-cube corporate boss and robot for the Greenbox cast.

Only writes these two character source directories. Each avatar has six
nonoverlapping, face-connected rigid parts with explicit animation pivots.
"""
from __future__ import annotations
from character_common import Asset, save_character, DEFAULT_JOINTS, COL, RGB, PALETTE


def boss_torso():
    a=Asset("torso")
    # A noticeably broad jacket; arm pieces meet its outer shoulder faces.
    a.box(2,3,13,14,10,25,"suit")
    a.box(2,3,24,14,10,25,"suit_light")
    a.box(2,3,16,3,10,24,"suit_light")
    a.box(13,7,16,14,10,24,"suit_light")
    # Raised shirt front, angular lapels, collar and a compact red tie.
    a.box(5,2,18,11,3,25,"white")
    for z in range(18,25):
        left=5-(z-18)//3
        a.box(left,1,z,left+2,3,z+1,"lapel")
        a.box(16-left-2,1,z,16-left,3,z+1,"lapel")
    a.box(6,1,24,8,3,25,"white")
    a.box(8,1,24,10,3,25,"white")
    a.box(7,1,22,9,2,24,"tie_red")
    a.box(7,1,17,9,2,22,"tie_red")
    a.set(7,1,17,"suit")
    a.box(10,2,20,13,3,22,"suit_light")
    a.box(11,1,22,13,3,23,"white")
    a.set(8,2,15,"gold")
    a.set(8,2,16,"lapel")
    a.box(3,3,13,13,9,14,"lapel")
    # Center back seam and a faint shoulder fold keep the rear useful too.
    a.box(7,9,15,8,10,24,"lapel")
    return a


def boss_head():
    a=Asset("head")
    a.box(6,4,25,10,8,27,"skin_tan")
    a.box(3,2,26,13,10,34,"skin_tan")
    a.box(4,1,27,12,2,33,"skin_pale")
    # Broad adult face, clear brows, nose and a restrained mouth.
    a.box(4,1,31,7,2,32,"hair_brown")
    a.box(9,1,31,12,2,32,"hair_brown")
    a.set(5,1,30,"ink")
    a.set(10,1,30,"ink")
    a.box(7,0,28,9,2,30,"skin_pale")
    a.box(6,1,27,10,2,28,"hair_brown")
    a.box(3,1,29,4,3,31,"skin_pale")
    a.box(12,1,29,13,3,31,"skin_pale")
    # Original side-parted hairstyle with quiet silver temple streaks.
    a.box(3,2,33,13,10,35,"hair_brown")
    a.box(4,2,35,12,9,36,"hair_brown")
    a.box(3,8,31,13,10,34,"hair_brown")
    a.box(3,2,31,4,9,34,"hair_brown")
    a.box(12,2,31,13,9,34,"hair_brown")
    a.box(3,2,32,4,5,34,"chrome")
    a.box(12,2,32,13,5,34,"chrome")
    a.box(5,2,35,6,8,36,"locs")
    return a


def boss_arm(left):
    a=Asset("arm_left" if left else "arm_right")
    x=-2 if left else 14
    a.box(x,3,14,x+4,9,25,"suit")
    a.box(x,3,24,x+4,9,25,"suit_light")
    a.box(x,3,13,x+4,9,14,"white")
    a.box(x,3,9,x+4,8,13,"skin_tan")
    a.box(x,2,10,x+4,3,13,"skin_pale")
    a.box(x,3,16,x+1,4,24,"suit_light")
    if left:
        # Solid watch and band are attached to the cuff, never floating cubes.
        a.box(x,3,13,x+4,4,14,"gold")
        a.box(x,2,13,x+3,3,15,"steel_dark")
        a.box(x+1,1,13,x+3,2,15,"gold")
        a.set(x+1,1,14,"ink")
    else:
        # A small executive case is part of the hand's rigid mesh. Its post
        # touches the palm and lid, so no seventh part or detached accessory.
        a.box(16,3,3,24,8,9,"ink")
        a.box(16,3,3,17,8,9,"steel_dark")
        a.box(23,3,3,24,8,9,"steel_dark")
        a.box(16,3,8,24,8,9,"suit_light")
        a.box(17,4,9,19,6,12,"ink")
        a.box(19,4,10,22,6,12,"ink")
        a.box(21,4,9,22,6,11,"ink")
        a.box(18,2,6,20,3,7,"gold")
        a.box(21,2,6,23,3,7,"gold")
    return a


def boss_leg(left):
    a=Asset("leg_left" if left else "leg_right")
    x=3 if left else 9
    a.box(x,4,3,x+4,9,13,"suit")
    a.box(x+1,3,4,x+2,4,13,"suit_light")
    shoe=2 if left else 9
    a.box(shoe,0,0,shoe+5,10,1,"lapel")
    a.box(shoe,0,1,shoe+5,10,3,"ink")
    a.box(shoe+1,3,3,shoe+4,8,4,"ink")
    a.box(shoe+1,1,2,shoe+4,2,3,"suit_light")
    a.set(shoe+1,1,2,"chrome")
    return a


def build_boss():
    joints=dict(DEFAULT_JOINTS)
    joints.update(torso=(8,5.5,13),head=(8,5.5,25),arm_left=(1.5,5.5,24),arm_right=(14.5,5.5,24),
                  leg_left=(5,5.5,13),leg_right=(11,5.5,13))
    return save_character("corporate_boss",
        [boss_torso(),boss_head(),boss_arm(True),boss_arm(False),boss_leg(True),boss_leg(False)],
        "Original fictional adult executive with a broad shoulder silhouette, navy suit and angular lapels, white shirt, red tie, side-parted hair with silver temples, brows, gold watch, polished black shoes and a connected hand-held briefcase.",
        joints=joints,root_pivot=(8,5.5,0))


def robot_torso():
    a=Asset("torso")
    a.box(3,3,14,13,9,17,"steel_dark")
    a.box(3,3,17,13,9,25,"steel")
    a.box(3,3,24,13,9,25,"chrome")
    a.box(3,3,18,4,9,24,"chrome")
    a.box(12,7,18,13,9,24,"chrome")
    a.box(5,2,19,11,3,23,"steel_dark")
    a.box(6,1,20,10,3,22,"cyan")
    a.box(6,1,20,7,2,21,"chrome")
    # Raised vents and three small controls on the chassis.
    for x in (4,6,8,10):
        a.box(x,2,16,x+1,3,19,"ink")
    for x,color in ((5,"tie_red"),(8,"gold"),(11,"cyan")):
        a.set(x,2,18,color)
    a.box(7,2,14,9,3,16,"gold")
    a.box(7,9,19,9,10,23,"steel_dark")
    a.box(6,9,17,10,10,18,"chrome")
    return a


def robot_head():
    a=Asset("head")
    a.box(6,4,25,10,8,27,"steel_dark")
    a.box(3,1,26,13,10,34,"steel")
    a.box(3,0,29,13,1,33,"steel_dark")
    a.box(5,0,30,7,1,32,"cyan")
    a.box(9,0,30,11,1,32,"cyan")
    a.box(3,0,32,13,2,34,"chrome")
    a.box(5,0,27,11,1,28,"steel_dark")
    for x in (6,8,10): a.set(x,0,27,"chrome")
    a.box(3,1,26,4,9,29,"chrome")
    a.box(12,1,26,13,9,29,"chrome")
    a.box(4,2,34,12,9,35,"steel_dark")
    # Chunky antenna is connected directly to the cap.
    a.box(10,5,35,11,7,38,"chrome")
    a.box(9,4,38,12,8,39,"cyan")
    # Side fasteners and back panel make the rear readable in the same style.
    a.box(3,9,29,13,10,32,"steel_dark")
    a.box(5,9,30,11,10,31,"chrome")
    a.set(3,2,30,"gold")
    a.set(12,2,30,"gold")
    return a


def robot_arm(left):
    a=Asset("arm_left" if left else "arm_right")
    x=-1 if left else 13
    a.box(x,3,21,x+4,9,25,"steel_dark")
    a.box(x+1,4,17,x+3,8,22,"steel")
    a.box(x,3,16,x+4,9,18,"steel_dark")
    a.box(x,3,12,x+4,8,17,"steel")
    a.box(x,2,10,x+4,8,12,"chrome")
    a.box(x,2,8,x+1,7,11,"steel_dark")
    a.box(x+3,2,8,x+4,7,11,"steel_dark")
    a.box(x+1,1,9,x+3,2,11,"chrome")
    a.box(x,3,22,x+4,4,24,"chrome")
    a.box(x+1,2,13,x+3,3,16,"cyan")
    a.box(x+1,2,16,x+3,3,17,"gold")
    return a


def robot_leg(left):
    a=Asset("leg_left" if left else "leg_right")
    x=4 if left else 9
    a.box(x,3,3,x+3,9,14,"steel")
    a.box(x,3,11,x+3,9,13,"steel_dark")
    a.box(x,3,5,x+3,9,6,"steel_dark")
    plate=3 if left else 9
    a.box(plate,2,7,plate+4,3,10,"chrome")
    a.box(plate+1,1,8,plate+3,2,9,"gold")
    a.box(plate,0,0,plate+4,10,1,"ink")
    a.box(plate,0,1,plate+4,10,3,"steel_dark")
    a.box(plate,0,1,plate+4,2,2,"chrome")
    a.box(plate+1,3,3,plate+3,8,4,"steel_dark")
    return a


def build_robot():
    joints=dict(DEFAULT_JOINTS)
    joints.update(torso=(8,5.5,14),head=(8,5.5,25),arm_left=(2.5,5.5,24),arm_right=(13.5,5.5,24),
                  leg_left=(5.5,5.5,14),leg_right=(10.5,5.5,14))
    return save_character("robot",
        [robot_torso(),robot_head(),robot_arm(True),robot_arm(False),robot_leg(True),robot_leg(False)],
        "Original chunky steel robot with cyan visor eyes and antenna, chrome brow and cheek armor, cyan chest display, vents and colored controls, dark joint bands, articulated claw hands and heavy boots.",
        joints=joints,root_pivot=(8,5.5,0))


if __name__=="__main__":
    build_boss()
    build_robot()
