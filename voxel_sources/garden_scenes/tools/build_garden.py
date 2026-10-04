"""Original Greenbox seedling garden made from exact occupied cubic cells."""
from lore_common import ROOT, Asset, COL, SceneBuilder, text
import json


def terrain():
    a=Asset('garden_layered_terrain')
    a.box(0,0,0,120,104,3,'floor_light')
    # Pond bed and the terraced banks have broad horizontal strata.
    a.box(0,0,3,120,104,7,'water')
    a.box(0,42,3,120,104,10,'floor_dark')
    a.box(0,42,10,120,104,16,'floor')
    a.box(0,42,16,120,104,20,'floor_light')
    a.box(0,42,20,120,104,22,'leaf_light')
    a.box(91,20,3,120,42,8,'floor_dark')
    a.box(91,20,8,120,42,12,'floor')
    a.box(91,20,12,120,42,15,'floor_light')
    a.box(91,20,15,120,42,17,'leaf_light')
    # Warm path ends above a simple soil stair at the water's edge.
    a.box(55,42,20,74,95,22,'linen')
    a.box(55,73,20,94,87,22,'linen')
    a.box(51,36,7,78,42,12,'floor_light')
    a.box(54,39,12,75,42,17,'floor_light')
    a.box(55,42,17,74,46,22,'linen')
    # Sparse corner patches only: chunky, legible cells without all-over noise.
    for x,y,w,d,c in [(1,44,5,6,'leaf_tip'),(7,49,3,3,'leaf'),(108,92,8,4,'leaf_tip'),(105,96,4,3,'leaf'),(28,97,8,5,'leaf_tip'),(35,95,4,4,'leaf'),(86,43,5,4,'leaf_tip'),(91,38,4,3,'leaf'),(112,24,6,4,'leaf_tip')]:
        z=21 if y>=42 else 16
        a.box(x,y,z,x+w,y+d,z+1,c)
    for x,y,w,d in [(59,49,4,3),(65,64,4,3),(59,89,3,2),(78,78,3,3)]:
        a.box(x,y,21,x+w,y+d,22,'trim')
    # Terrain side blocks are deliberate large patches, not individual dithering.
    a.box(0,62,17,1,70,20,'wood_light')
    a.box(0,69,15,1,73,18,'wood_light')
    a.box(112,41,14,117,42,18,'wood_light')
    a.box(116,41,11,120,42,16,'wood_light')
    a.box(119,69,16,120,77,20,'wood_light')
    a.box(119,76,14,120,80,18,'wood_light')
    a.meta={'description':'6 by 5.2 meter layered garden tile with inset opaque teal pond, two soil terraces, a warm path and sparse broad corner patches.'}
    return a


def tree(name,width,height):
    a=Asset(name); c=width//2
    a.box(c-3,c-3,0,c+3,c+3,24,'wood')
    a.box(c-3,c-3,4,c+3,c,9,'wood_light')
    a.box(0,0,24,width,width,height,'leaf')
    a.box(0,0,height-6,width,width,height,'leaf_light')
    a.box(0,0,height-1,width,width,height,'leaf_tip')
    a.box(0,0,24,width,2,height-10,'leaf_dark')
    # One stepped accent on the canopy corner rather than grain/noise.
    a.box(width-5,0,height-6,width,2,height-2,'leaf_tip')
    a.box(width-2,0,height-12,width,2,height-5,'leaf_light')
    a.box(0,4,26,2,11,29,'leaf_light')
    a.box(0,10,25,2,14,28,'leaf_light')
    a.meta={'description':'Original cuboid canopy tree; broad lime top, olive lower canopy, one sparse corner highlight and a square wooden trunk.'}
    return a


def fence():
    a=Asset('garden_short_plank_fence')
    for x in (0,21,42): a.box(x,0,0,x+3,4,19,'wood_light')
    a.box(0,0,6,45,3,10,'wood'); a.box(0,0,13,45,3,17,'wood')
    a.box(0,0,16,45,1,17,'wood_light')
    a.meta={'description':'Connected three-post plank fence with two broad horizontal rails.'}
    return a


def bench():
    a=Asset('garden_oak_bench')
    for x in (2,28):
        a.box(x,1,0,x+3,3,9,'wood'); a.box(x,8,0,x+3,10,19,'wood')
    a.box(0,0,9,33,12,12,'wood_light')
    a.box(0,8,14,33,11,18,'wood')
    a.box(0,8,18,33,11,19,'wood_light')
    a.meta={'description':'Original oak garden bench, broad seat and one simple backrest.'}
    return a


def flower(name,color='white'):
    a=Asset(name)
    a.box(2,2,0,3,3,3,'stem')
    a.box(0,1,2,5,4,3,color); a.box(1,0,2,4,5,3,color)
    a.box(2,2,3,3,3,4,'yellow')
    a.meta={'description':'Connected five-cell-wide flower with square petals and warm center.'}
    return a


def grass():
    a=Asset('garden_grass_tuft')
    a.box(0,0,0,8,5,2,'leaf'); a.box(1,1,2,3,3,7,'leaf_light')
    a.box(4,2,2,6,4,5,'leaf_tip')
    a.meta={'description':'Original small cluster of two cuboid grass blades on a connected root base.'}
    return a


def fish():
    a=Asset('garden_teal_fish')
    a.box(2,1,0,12,5,3,'teal'); a.box(3,1,3,11,5,4,'water')
    a.box(0,0,1,3,6,3,'blue')
    a.box(10,0,1,12,1,2,'ink'); a.box(10,5,1,12,6,2,'ink')
    a.meta={'description':'Original connected miniature fish, teal cuboid body and blue square tail. Artistic pond surface silhouette.'}
    return a


def lily():
    a=Asset('garden_lily_pad')
    a.box(0,2,0,11,9,1,'leaf_tip'); a.box(2,0,0,9,11,1,'leaf_light')
    a.box(8,0,0,11,4,1,'leaf_tip')
    a.erase(0,0,0,4,4,1)
    a.box(4,4,1,7,7,2,'white'); a.box(5,5,2,6,6,3,'pink_light')
    a.meta={'description':'Connected blocky lily pad with an original stepped notch and one pale flower; surface prop touches water without overlap.'}
    return a


def reeds():
    a=Asset('garden_pond_reeds')
    a.box(0,0,0,13,4,2,'teal')
    for x,h in ((1,23),(8,17)):
        a.box(x,1,2,x+2,3,h,'wood_light'); a.box(x,1,h-7,x+2,3,h,'yellow')
        a.box(x+2,1,8,x+4,3,11,'leaf')
    a.meta={'description':'Two square pond reeds with ochre tips; a connected dark teal root base sits on the pond surface.'}
    return a


def sign():
    a=Asset('garden_greenbox_seedling_sign')
    a.box(14,2,0,17,5,17,'wood')
    a.box(0,0,14,31,6,28,'teal')
    a.box(1,0,15,30,1,27,'teal_light')
    text(a,'SEED',4,-1,19,'linen')
    a.meta={'description':'Original raised SEED marker: simple turquoise board on a square wooden post.'}
    return a


def main():
    scene=SceneBuilder('seedling_garden')
    scene.add(terrain())
    scene.add(tree('garden_tall_lime_tree',28,60),(7,71,22))
    scene.add(tree('garden_small_lime_tree',18,43),(42,83,22))
    scene.add(fence(),(72,98,22))
    scene.add(bench(),(4,51,22))
    scene.add(sign(),(88,54,22))
    scene.add(reeds(),(11,20,7))
    scene.add(lily(),(37,8,7),name='pond_lily_left')
    scene.add(lily(),(77,23,7),name='pond_lily_right')
    scene.add(fish(),(49,19,7),name='pond_fish_left')
    scene.add(fish(),(71,5,7),name='pond_fish_right')
    for i,(x,y,z) in enumerate(((40,56,22),(49,69,22),(80,47,22),(104,26,17),(8,91,22),(109,69,22))):
        scene.add(flower('garden_cream_flower'),(x,y,z),name='garden_cream_flower_'+str(i))
    for i,(x,y,z) in enumerate(((38,92,22),(45,49,22),(73,92,22),(94,23,17),(13,44,22))):
        scene.add(grass(),(x,y,z),name='grass_cluster_'+str(i))
    source=ROOT/'work/bedroom/scene.json'
    scene.add(scene.import_asset(source,'cannabis_plant_small',alias='garden_plant_small_cc0_leaf'),(77,83,22))
    scene.add(scene.import_asset(source,'cannabis_plant_medium',alias='garden_plant_medium_cc0_leaf'),(100,79,22))
    scene.add(scene.import_asset(source,'watering_can',alias='garden_teal_watering_can'),(83,69,22))
    character_path=ROOT/'voxel_sources/garden_cast/rasta_grower/rasta_grower.json'
    grower=scene.import_asset(character_path,alias='garden_rasta_grower')
    grower['metadata']['lore_role']='Original Greenbox seedling garden caretaker'
    scene.add(grower,(65,52,22))
    flattened=scene.save('Original Greenbox seedling garden: a warm layered 6 by 5.2 meter outdoor voxel tile with broad lime and olive cube tree canopies, a stepped sand path, a turquoise pond, fish, lily pads, square reeds, an oak bench, flowers, plank fence, SEED marker, a new compact Rasta grower, preserved CC0-leaf-derived potted plant assets and a watering can. Source shapes are occupied cubes and colors remain the canonical indexed Greenbox palette. Garden theme is a global presentation remap. Static game art diorama only.',lights=[])
    assert flattened['metadata']['intentional_union_overlap_cells']==0, 'Modular placements overlap'
    assert flattened['metadata']['connected_components']==1, 'Diorama should be connected through terrain'


if __name__=='__main__': main()
