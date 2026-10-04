"""Generate seven original Garden chibi characters from occupied cubic cells."""
from garden_common import Asset, head_base, face, torso_base, arm_base, leg_base, chip, save_character

def rasta_grower():
    h=head_base('skin'); face(h,'skin_light',mouth='locs')
    # Three broad loc panels and a layered knitted cap, with few color chips.
    h.box(2,13,11,20,19,27,'locs')
    h.box(1,4,13,3,17,25,'locs'); h.box(19,4,13,21,17,25,'locs')
    h.box(2,2,24,5,5,27,'locs'); h.box(17,2,24,20,5,27,'locs')
    h.box(1,1,25,21,19,27,'rasta_green')
    h.box(1,1,27,21,19,28,'rasta_gold'); h.box(2,2,28,20,18,29,'rasta_red')
    h.box(3,3,29,19,17,31,'rasta_green')
    chip(h,3,3,30,'leaf_tip',3); chip(h,18,14,30,'leaf_light',2,axis='y')
    t=torso_base('rasta_green'); t.box(9,6,5,13,8,9,'rasta_gold')
    t.box(10,5,5,12,7,9,'rasta_red'); t.box(7,6,4,15,8,5,'ink')
    a=[arm_base(True,'rasta_green','skin'),arm_base(False,'rasta_green','skin')]
    for p,x in zip(a,(4,15)): p.box(x,7,6,x+3,12,7,'rasta_gold')
    l=[leg_base(True,'navy','ink'),leg_base(False,'navy','ink')]
    save_character('rasta_grower',[t,h,*a,*l],
      'Garden chibi grower: large cubic head, chunky loc panels, red/gold/green layered cap, two bold 3x3 eyes, tiny striped shirt and very short blue trousers.')

def corporate_boss():
    h=head_base('skin_pale'); face(h,'skin_pale')
    h.box(2,2,23,20,18,27,'hair_brown'); h.box(3,3,27,19,17,29,'hair_brown')
    h.box(2,2,21,7,5,25,'hair_brown'); h.box(2,5,19,4,17,25,'hair_brown')
    h.box(18,5,20,20,17,25,'hair_brown')
    chip(h,3,3,28,'wood_light',3); chip(h,18,14,28,'locs',2,axis='y')
    h.box(5,1,21,8,3,22,'hair_brown'); h.box(14,1,21,17,3,22,'hair_brown')
    t=torso_base('suit'); t.box(10,6,5,12,8,9,'chef_white')
    t.box(9,5,6,10,7,9,'suit_light'); t.box(12,5,6,13,7,9,'suit_light')
    t.box(10,5,5,12,7,8,'tie_red'); t.box(13,6,6,15,8,7,'chef_white')
    a=[arm_base(True,'suit','skin_pale'),arm_base(False,'suit','skin_pale')]
    a[0].box(4,6,5,7,8,6,'gold')
    # A attached briefcase remains the right rigid arm, clear of the tiny feet.
    a[1].box(17,8,3,20,10,5,'wood'); a[1].box(18,6,0,23,13,4,'wood')
    a[1].box(19,5,2,22,7,3,'gold')
    l=[leg_base(True,'suit','ink'),leg_base(False,'suit','ink')]
    save_character('corporate_boss',[t,h,*a,*l],
      'Garden chibi corporate boss: broad cubic face, dark combed hair panels, small red tie, navy suit, gold wristwatch and attached brown briefcase; bold minimal eyes.')

def robot():
    h=head_base('steel'); h.box(9,8,9,13,12,10,'steel_dark')
    h.box(4,1,15,18,3,23,'steel_dark')
    h.box(6,0,18,9,2,21,'cyan'); h.box(13,0,18,16,2,21,'cyan')
    h.box(9,0,16,13,2,17,'chrome')
    h.box(1,7,16,3,13,23,'steel_dark'); h.box(19,7,16,21,13,23,'steel_dark')
    h.box(1,8,18,2,12,20,'cyan'); h.box(20,8,18,21,12,20,'cyan')
    h.box(3,3,27,19,17,29,'steel'); h.box(10,9,29,12,11,31,'steel_dark')
    h.box(9,8,31,13,12,33,'rasta_gold')
    chip(h,3,3,28,'chrome',3); chip(h,18,14,28,'steel_dark',2,axis='y')
    t=torso_base('steel'); t.box(8,6,5,14,8,8,'steel_dark')
    t.box(9,5,6,13,7,8,'cyan'); t.box(10,5,5,12,7,6,'rasta_gold')
    a=[arm_base(True,'steel','steel_dark'),arm_base(False,'steel','steel_dark')]
    for p,x in zip(a,(4,15)): p.box(x,7,6,x+3,12,7,'cyan')
    l=[leg_base(True,'steel_dark','steel'),leg_base(False,'steel_dark','steel')]
    save_character('robot',[t,h,*a,*l],
      'Garden chibi helper robot: enormous clean steel cube head, dark visor and cyan block eyes, tiny metal body and feet, chunky side housings and compact gold antenna.')

def chef():
    h=head_base('skin_tan'); face(h,'skin_tan',mouth='hair_brown')
    h.box(2,12,18,20,18,26,'hair_brown'); h.box(2,4,19,4,17,25,'hair_brown')
    h.box(18,4,19,20,17,25,'hair_brown')
    h.box(1,1,25,21,19,28,'chef_white')
    h.box(2,2,28,20,18,31,'chef_white'); h.box(4,4,31,18,16,33,'chef_white')
    chip(h,2,2,30,'linen',3); chip(h,19,14,30,'trim',2,axis='y')
    t=torso_base('chef_white'); t.box(7,6,4,15,8,6,'rasta_red')
    t.box(9,5,7,13,7,9,'rasta_red'); t.box(10,5,6,12,7,7,'rasta_gold')
    t.set(9,6,6,'ink'); t.set(13,6,6,'ink')
    a=[arm_base(True,'chef_white','skin_tan'),arm_base(False,'chef_white','skin_tan')]
    l=[leg_base(True,'ink','ink'),leg_base(False,'ink','ink')]
    save_character('chef',[t,h,*a,*l],
      'Garden chibi chef: enormous warm cubic face, stacked block toque, compact cream jacket, red neckerchief and waist apron, tiny dark feet; sparse cream corner accents.')

def blonde_lady():
    h=head_base('skin_pale'); face(h,'skin_pale',mouth='lip')
    h.box(2,2,24,20,18,28,'hair_blonde'); h.box(3,3,28,19,17,30,'hair_blonde')
    h.box(1,4,12,4,19,26,'hair_blonde'); h.box(18,4,12,21,19,26,'hair_blonde')
    h.box(4,15,12,18,19,26,'hair_blonde_shadow')
    h.box(3,1,22,9,4,25,'hair_blonde'); h.box(9,1,23,17,4,26,'hair_blonde')
    chip(h,3,3,29,'rasta_gold',3); chip(h,18,14,29,'warm_light',2,axis='y')
    t=torso_base('teal'); t.box(9,6,7,13,8,9,'teal_light')
    t.box(7,6,4,15,8,5,'rasta_gold')
    a=[arm_base(True,'teal','skin_pale'),arm_base(False,'teal','skin_pale')]
    l=[leg_base(True,'navy','heel_dark'),leg_base(False,'navy','heel_dark')]
    save_character('blonde_lady',[t,h,*a,*l],
      'Garden chibi blonde neighbor: clean cube face and two black eye blocks, layered broad golden hair panels, little teal top with gold hem, tiny navy trousers and dark shoes.')

def party_woman():
    h=head_base('skin_light'); face(h,'skin_pale',mouth='lip')
    h.box(2,2,23,20,18,28,'hair_auburn'); h.box(3,3,28,19,17,30,'hair_auburn')
    h.box(1,4,13,4,19,27,'hair_auburn'); h.box(18,4,12,21,19,27,'hair_auburn')
    h.box(4,15,12,18,19,27,'hair_brown'); h.box(3,1,22,11,4,26,'hair_auburn')
    h.box(1,3,21,3,5,24,'gold'); h.box(19,3,21,21,5,24,'gold')
    chip(h,3,3,29,'clay_light',3); chip(h,18,14,29,'hair_brown',2,axis='y')
    t=torso_base('dress_pink'); t.box(7,6,4,15,8,5,'dress_violet')
    t.box(9,6,7,13,8,9,'gold'); t.box(10,5,6,12,7,8,'dress_pink')
    a=[arm_base(True,'dress_pink','skin_light'),arm_base(False,'dress_pink','skin_light')]
    a[1].box(15,6,5,18,8,6,'gold')
    l=[leg_base(True,'skin_light','heel_dark'),leg_base(False,'skin_light','heel_dark')]
    save_character('party_woman',[t,h,*a,*l],
      'Garden chibi party neighbor: enormous cube head, chunky auburn hair and square gold earrings, bright pink/violet tiny outfit, necklace and very short dark-shoed legs.')

def skeleton():
    h=head_base('bone'); h.box(5,1,17,9,3,21,'ink'); h.box(13,1,17,17,3,21,'ink')
    h.box(10,1,14,12,3,17,'bone_shadow'); h.box(7,1,12,15,3,14,'ink')
    for x in (8,11,14): h.box(x,1,12,x+1,3,14,'bone')
    chip(h,2,2,26,'chef_white',3); chip(h,19,15,24,'bone_shadow',3,axis='z')
    # Keep skull solid: recesses are dark occupied cells rather than hollow tricks.
    t=torso_base('bone_shadow'); t.box(8,6,5,14,8,9,'bone')
    t.box(10,5,4,12,7,9,'bone')
    for z in (5,7): t.box(8,5,z,14,7,z+1,'ink')
    a=[arm_base(True,'bone','bone'),arm_base(False,'bone','bone')]
    for p,x in zip(a,(4,15)): p.box(x,7,5,x+3,11,6,'bone_shadow')
    l=[leg_base(True,'bone_shadow','bone'),leg_base(False,'bone_shadow','bone')]
    save_character('skeleton',[t,h,*a,*l],
      'Garden chibi skeleton: oversized solid bone cube skull, bold 4x4 dark eye sockets, compact tooth row, tiny graphic ribcage and block bone arms and feet; no hollow or smoothed substitute geometry.')

if __name__=='__main__':
    for builder in (rasta_grower,corporate_boss,robot,chef,blonde_lady,party_woman,skeleton): builder()
