"""Three original Greenbox chibi characters, authored as occupied cubic cells."""
from chibi_common import (
    Asset, COL, RGB, PALETTE, soft_box, head_base, torso_base,
    arm_base, leg_base, save_character, JOINTS,
)

REFERENCE = 'https://thetouryst.shinen.com/deluxe/'


def simple_face(a, skin, mouth='lip', brows='ink'):
    # Small square eyes and clean graphic features suit the chunky voxel head.
    a.box(6,0,21,8,2,23,'ink')
    a.box(12,0,21,14,2,23,'ink')
    a.box(5,0,24,8,2,25,brows)
    a.box(12,0,24,15,2,25,brows)
    a.box(9,0,19,11,2,21,skin)
    a.box(8,0,18,12,2,19,mouth)
    return a


def rasta_grower():
    head = head_base('skin')
    simple_face(head, 'skin_light', mouth='locs', brows='locs')
    # Locs attach to the back and both temples, with a deliberate stepped edge.
    head.box(4,11,17,16,14,27,'locs')
    for x in (2,17):
        head.box(x,3,18,x+1,12,27,'locs')
    for x in (3,6,10,14,16):
        head.box(x,12,16,x+1,15,25,'locs')
    head.box(3,1,25,5,4,27,'locs')
    head.box(15,1,25,17,4,27,'locs')
    # The compact knitted cap retains the grower's red/gold/green identity.
    soft_box(head,1,0,26,19,14,29,'rasta_green')
    head.box(2,1,27,18,13,28,'rasta_gold')
    head.box(2,1,28,18,13,29,'rasta_red')
    soft_box(head,3,2,29,17,12,31,'rasta_green')
    head.box(7,4,30,13,10,32,'rasta_green')
    torso = torso_base('rasta_green')
    torso.box(8,3,8,12,5,14,'rasta_gold')
    torso.box(9,2,8,11,4,14,'rasta_red')
    torso.box(6,3,7,14,5,8,'ink')
    torso.box(9,2,7,11,4,8,'gold')
    left = arm_base(True, 'rasta_green', 'skin')
    right = arm_base(False, 'rasta_green', 'skin')
    for arm,x in ((left,3),(right,14)):
        arm.box(x,4,9,x+3,10,10,'rasta_gold')
    legs = [leg_base(True,'navy','ink'),leg_base(False,'navy','ink')]
    for leg,x in zip(legs,(6,11)):
        leg.box(x,2,1,x+3,4,2,'linen')
    save_character('rasta_grower',[torso,head,left,right,*legs],
        'Original tropical grower: oversized cubic head, compact body, short sturdy '
        'legs, knitted red/gold/green cap and readable locs. Restrained 2x2 dark eyes '
        'and clean graphic features. Visual inspiration from The Touryst: '+REFERENCE+
        '; no copied game assets, characters or textures.')


def corporate_boss():
    head = head_base('skin_pale')
    simple_face(head,'skin_pale',mouth='lip',brows='hair_brown')
    # A severe block of combed hair and a side part, rather than fine noisy strands.
    head.box(2,1,26,18,13,28,'hair_brown')
    soft_box(head,3,2,28,17,12,30,'hair_brown')
    head.box(2,3,23,4,12,27,'hair_brown')
    head.box(16,3,23,18,12,27,'hair_brown')
    head.box(3,1,24,7,3,27,'hair_brown')
    head.box(6,1,27,7,10,29,'locs')
    # Compact three-dimensional jaw/jowls reinforce the broad boss silhouette.
    head.box(4,0,17,7,2,19,'skin_pale')
    head.box(13,0,17,16,2,19,'skin_pale')
    torso = torso_base('suit')
    torso.box(9,3,9,11,5,14,'chef_white')
    torso.box(6,3,10,9,5,14,'lapel')
    torso.box(11,3,10,14,5,14,'lapel')
    torso.box(7,2,12,9,4,14,'suit_light')
    torso.box(11,2,12,13,4,14,'suit_light')
    torso.box(9,2,9,11,4,13,'tie_red')
    torso.box(9,2,13,11,4,14,'tie_red')
    torso.box(12,2,10,14,4,11,'chef_white')
    torso.set(10,3,8,'gold')
    left = arm_base(True,'suit','skin_pale')
    right = arm_base(False,'suit','skin_pale')
    left.box(3,4,9,6,10,10,'chef_white')
    right.box(14,4,9,17,10,10,'chef_white')
    # Gold wristwatch and briefcase attach to their owning rigid arm.
    left.box(3,3,8,6,5,9,'gold')
    left.set(4,3,8,'chef_white')
    right.box(16,5,6,19,7,8,'wood')
    soft_box(right,17,3,2,22,10,7,'wood')
    right.box(18,3,5,21,4,6,'gold')
    legs = [leg_base(True,'suit','ink'),leg_base(False,'suit','ink')]
    save_character('corporate_boss',[torso,head,left,right,*legs],
        'Original chibi corporate boss: oversized square head, broad suit silhouette, '
        'short sturdy legs, red tie, combed hair, gold wristwatch and attached briefcase. '
        'Restrained dark square eyes. Visual inspiration from The Touryst: '+REFERENCE+
        '; no copied game assets, characters or textures.')


def robot():
    head = head_base('steel')
    head.box(8,5,14,12,9,16,'steel_dark')
    # One simple recessed-looking visor with two lit square eyes.
    head.box(4,0,20,16,2,25,'steel_dark')
    head.box(6,-1,21,8,1,23,'cyan')
    head.box(12,-1,21,14,1,23,'cyan')
    head.box(7,0,18,13,2,19,'chrome')
    head.box(8,-1,18,12,1,19,'ink')
    head.box(0,5,21,3,9,25,'steel_dark')
    head.box(17,5,21,20,9,25,'steel_dark')
    head.box(0,6,22,1,8,24,'cyan')
    head.box(19,6,22,20,8,24,'cyan')
    head.box(4,3,27,16,11,29,'chrome')
    head.box(9,6,28,11,8,33,'steel_dark')
    soft_box(head,8,5,32,12,9,35,'rasta_gold')
    head.box(9,5,33,11,6,34,'cyan')
    torso = torso_base('steel')
    torso.box(7,3,8,13,5,13,'steel_dark')
    torso.box(8,2,10,12,4,12,'cyan')
    torso.box(7,2,8,9,4,10,'rasta_gold')
    torso.box(11,2,8,13,4,10,'chrome')
    torso.box(6,4,7,14,10,8,'steel_dark')
    arms = [arm_base(True,'steel','steel_dark'),
            arm_base(False,'steel','steel_dark')]
    for arm,x in zip(arms,(3,14)):
        arm.box(x,4,9,x+3,10,10,'cyan')
        arm.box(x,3,11,x+3,5,13,'chrome')
    legs = [leg_base(True,'steel_dark','steel'),leg_base(False,'steel_dark','steel')]
    for leg,x in zip(legs,(6,11)):
        leg.box(x,1,1,x+3,3,2,'cyan')
    save_character('robot',[torso,head,*arms,*legs],
        'Original chibi helper robot: oversized chunky cube head, compact metal body, '
        'short sturdy limbs, two cyan square visor eyes, ear housings, antenna and '
        'clear chest panels. Visual inspiration from The Touryst: '+REFERENCE+
        '; no copied game assets, characters or textures.')


if __name__ == '__main__':
    rasta_grower()
    corporate_boss()
    robot()
