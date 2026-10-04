"""Original Greenbox Neighbor Commons, a native integer-grid voxel environment."""
from pathlib import Path
import hashlib, json
from lore_common import ROOT, Asset, SceneBuilder, text, leaf_motif


def terrain():
    a=Asset('commons_layered_ground')
    a.box(0,0,0,240,200,1,'floor_dark')
    a.box(0,0,1,240,200,3,'floor')
    a.box(0,0,3,240,200,4,'leaf_light')
    a.box(10,10,3,230,143,4,'floor_light')
    # A broad cross-shaped plaza is always level with the surrounding grass.
    a.box(86,10,3,157,144,4,'linen')
    a.box(9,98,3,231,144,4,'linen')
    for x,w in ((23,24),(77,24),(137,24),(192,24)):
        a.box(x,137,3,x+w,147,4,'linen')
    for x,y,w,d in ((14,82,7,5),(77,25,5,8),(170,23,8,5),(216,85,7,4),(88,127,5,3),(140,61,4,3),(121,13,6,4),(210,123,5,3)):
        a.box(x,y,3,x+w,y+d,4,'trim')
    for x,y,w,d in ((0,21,8,7),(232,77,8,6),(176,192,6,8),(4,185,6,8),(230,15,10,7)):
        a.box(x,y,3,x+w,y+d,4,'leaf_tip')
    a.meta={'description':'Level 12 by 10 meter terrain. Four cubic strata, bright grass border, warm soil court and cream walking paths. Ground top is exactly native Z 4 = world Y .2 m.'}
    return a


def home(name,width,color,light,sign,door_side=1):
    a=Asset(name); depth=50
    # Hollow voxel house shell; closed decorative front prevents unseen interiors.
    a.box(0,0,0,width,2,49,'wall')
    a.box(0,2,0,2,depth,49,'wall_shadow')
    a.box(width-2,2,0,width,depth,49,'wall_shadow')
    a.box(2,depth-2,0,width-2,depth,49,'wall')
    a.box(0,0,0,width,2,5,'floor_dark')
    a.box(0,0,39,width,3,49,color)
    a.box(0,0,44,width,1,49,light)
    a.box(0,0,49,width,depth,53,color)
    a.box(3,3,53,width-3,depth-3,55,light)
    a.box(0,0,52,5,5,53,light)
    a.box(3,0,47,5,1,52,light)
    # Door and broad opaque teal windows: no alpha planes or raster artwork.
    dx=width-17 if door_side else 5
    a.box(dx,0,0,dx+12,2,28,'wood')
    a.box(dx+2,0,2,dx+10,1,25,'teal')
    a.box(dx+8,-1,13,dx+10,0,15,'gold')
    wx=6 if door_side else 22
    a.box(wx,-1,10,wx+16,0,31,'trim')
    a.box(wx+2,-2,12,wx+14,-1,29,'blue')
    a.box(wx+7,-3,12,wx+9,-2,29,'linen')
    a.box(wx+2,-3,19,wx+14,-2,21,'linen')
    a.box(wx+1,-3,9,wx+15,0,12,color)
    a.box(width-2,8,14,width,29,32,'blue')
    a.box(width-1,16,14,width,18,32,'trim')
    # The sign belongs to the same reusable house asset and touches its backing.
    label_width=len(sign)*6-1; sx=max(2,(width-label_width)//2)
    text(a,sign,sx,-1,40,'white')
    a.meta={'description':f'Original {sign} neighbor home/shop with chunky {color} roof, inset solid teal door, crossed opaque window and raised pixel letters. Decorative closed exterior; interiors are not navigable.'}
    return a


def tree(name,width,height):
    a=Asset(name); c=width//2
    a.box(c-2,c-2,0,c+2,c+2,34,'wood')
    a.box(c-2,c-2,6,c+2,c-1,11,'wood_light')
    a.box(0,0,34,width,width,height,'leaf')
    a.box(0,0,height-5,width,width,height,'leaf_light')
    a.box(0,0,height-1,width,width,height,'leaf_tip')
    a.box(0,0,34,width,2,height-10,'leaf_dark')
    a.box(width-4,0,height-5,width,1,height-1,'leaf_tip')
    a.meta={'description':'Original simple cuboid lime/olive tree canopy with square trunk and one broad corner highlight.'}
    return a


def bench():
    a=Asset('commons_oak_bench')
    for x in (2,30):
        a.box(x,1,0,x+3,4,10,'wood')
        a.box(x,10,0,x+3,13,22,'wood')
    a.box(0,0,10,35,14,13,'wood_light')
    a.box(0,10,16,35,13,21,'wood')
    a.box(0,10,21,35,13,22,'wood_light')
    return a


def market():
    a=Asset('commons_night_market_stall')
    # One connected frame, stepped awning and simple collectible displays.
    for x in (0,49): a.box(x,0,0,x+3,40,39,'wood')
    a.box(3,2,0,49,5,23,'purple')
    a.box(3,3,20,49,36,24,'wood_light')
    a.box(0,0,39,52,40,43,'ink')
    a.box(0,0,43,52,40,44,'purple')
    a.box(0,0,34,52,3,39,'purple')
    # Short MARKET label remains readable at game scale.
    text(a,'MARKET',8,-1,35,'rasta_gold')
    a.box(3,0,3,49,2,18,'teal')
    leaf_motif(a,25,-1,5,'leaf_tip',scale=1)
    for x,color in ((8,'leaf_light'),(20,'blue'),(32,'violet')):
        a.box(x,8,24,x+8,14,36,color)
        a.box(x+1,7,26,x+7,8,34,'ink')
        a.box(x+3,6,28,x+5,7,32,'white')
    a.box(40,23,24,47,30,31,'yellow')
    a.meta={'description':'Fictional Night Market game trade stall, with wood counter, deep violet awning, MARKET lettering, three decorative rarity card blocks and one closed yellow box. Gameplay exchanges fictional collectibles only.'}
    return a


def lamp():
    a=Asset('commons_courtyard_lamp')
    a.box(0,0,0,8,8,2,'slate')
    a.box(3,3,2,5,5,37,'ink')
    a.box(0,0,32,8,8,34,'ink')
    a.box(1,1,34,7,7,41,'warm_light')
    a.box(0,0,41,8,8,43,'ink')
    return a


def flower():
    a=Asset('commons_square_flower')
    a.box(2,2,0,3,3,3,'stem')
    a.box(0,1,2,5,4,3,'white'); a.box(1,0,2,4,5,3,'white')
    a.box(2,2,3,3,3,4,'yellow')
    return a


def world_point(x,y,z=4): return [round((x-120)*.05,6),round(z*.05,6),round(-(y-100)*.05,6)]
def blocker(name,x0,y0,x1,y1):
    return {'id':name,'minX':round((x0-120)*.05,6),'maxX':round((x1-120)*.05,6),'minZ':round(-(y1-100)*.05,6),'maxZ':round(-(y0-100)*.05,6),'nativeBounds':[x0,y0,x1,y1]}


def write_layout(folder,scene):
    homes=[('chef_home',12,142,58,195),('artist_home',66,142,112,195),('robot_lab',126,142,172,195),('party_home',180,142,228,195)]
    blockers=[blocker(*p) for p in homes]
    blockers += [blocker('night_market',18,24,70,65),blocker('courtyard_bench',105,62,140,76)]
    # At character height the high canopies are walk-under; block the true trunks.
    blockers += [blocker('tree_left_trunk',7,90,11,94),blocker('tree_right_trunk',229,94,233,98)]
    blockers += [blocker('lamp_left',76,99,84,107),blocker('lamp_right',160,99,168,107)]
    blockers += [blocker('pot_market',75,40,96,51),blocker('pot_court',170,62,191,73)]
    names=[('chef','Miso','chef',35,['Welcome to the Commons! I trade recipes and grow-room snacks.','Try the Night Market for a lucky seed card.']),('artist','Sunny','blonde_lady',89,['Every little garden deserves a bright corner.','Send me a happy emoji if you like our new colors!']),('robot','BUD-01','robot',149,['Greeting received. Neighbor connection: online.','Rare gear makes my collection circuits very happy.']),('party','Zee','party_woman',204,['The courtyard is our tiny after-party.','Got a spare card? The Night Market swaps collectibles.'])]
    layout={'schema':'greenbox-neighborhood-layout-v1','assetId':'neighbor_commons','voxelPitchMeters':.05,'sourceRootPivotNative':[120,100,0],
      'coordinateConvention':'GLB Y up, front +Z. World [X,Y,Z] = [(nativeX-120)*.05,nativeZ*.05,-(nativeY-100)*.05]. All characters use a feet-at-origin root.',
      'bounds':{'minX':-6,'maxX':6,'minZ':-5,'maxZ':5},'floorY':.2,
      'walkArea':{'minX':-5.7,'maxX':5.7,'minZ':-4.7,'maxZ':4.7},'player':{'spawn':[0,.2,3.3],'radius':.24,'speed':2.6},'blockers':blockers,
      'neighbors':[{'id':pid,'name':name,'characterId':cid,'position':world_point(x,130),'yaw':0,'dialogue':lines,'interactionRadius':1.8} for pid,name,cid,x,lines in names],
      'market':{'id':'night_market','name':'Night Market','position':world_point(44,16),'radius':1.8,'description':'Fictional neighborhood exchange for in-game cards, boxes and gear.'},
      'displaySpots':[{'id':'common_card','position':world_point(30,37,28)},{'id':'rare_card','position':world_point(42,37,28)},{'id':'epic_card','position':world_point(54,37,28)}],
      'miniMap':{'north':'negative Z','background':'leaf_light','path':'linen','showNeighbors':True,'showMarket':True},
      'sourceVoxSha256':hashlib.sha256((folder/'neighbor_commons.vox').read_bytes()).hexdigest(),
      'sourceSceneSha256':hashlib.sha256((folder/'scene.json').read_bytes()).hexdigest(),
      'environmentIncludesStaticCharacters':False,'authoredDate':'2026-10-04'}
    (folder/'game_layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'game_layout.json').write_bytes((folder/'game_layout.json').read_bytes())


def main():
    s=SceneBuilder('neighbor_commons'); s.add(terrain())
    for name,width,x,color,light,label,side in [('commons_chef_home',46,12,'teal','teal_light','CHEF',1),('commons_artist_home',46,66,'pink','pink_light','ART',0),('commons_robot_lab',46,126,'blue','cyan','LAB',1),('commons_party_home',48,180,'purple','violet','CLUB',0)]:
        # Front window/letters extend three cells forward. Placement corrects their normalization.
        s.add(home(name,width,color,light,label,side),(x,145,4))
    s.add(tree('commons_lime_tree_left',18,66),(0,83,4))
    s.add(tree('commons_lime_tree_right',18,60),(222,87,4))
    s.add(bench(),(105,62,4)); s.add(market(),(18,25,4))
    s.add(lamp(),(76,99,4),name='courtyard_lamp_left'); s.add(lamp(),(160,99,4),name='courtyard_lamp_right')
    imported=s.import_asset(ROOT/'work/bedroom/scene.json','cannabis_plant_small',alias='commons_plant_small_cc0_leaf')
    s.add(imported,(75,40,4),name='market_leaf_pot'); s.add(imported,(170,62,4),name='courtyard_leaf_pot')
    for i,(x,y) in enumerate(((2,27),(231,26),(6,174),(231,178),(6,124),(227,70),(60,192),(175,192))):
        s.add(flower(),(x,y,4),name='commons_flower_'+str(i))
    flat=s.save('Original Greenbox Neighbor Commons. A 12 by 10 meter level voxel neighborhood with four compact colorful closed house fronts, wide sandy and cream courtyard paths, bright cuboid lime trees, oak bench, two street lamps, preserved CC0-leaf-derived potted plants and a tucked-away fictional Night Market collectible trade stall. Bare environment only: game supplies separate movable characters. Palette remains canonical; Garden theme is a presentation remap.',lights=[])
    assert flat['metadata']['intentional_union_overlap_cells']==0
    assert flat['metadata']['connected_components']==1
    assert flat['dimensions']==[240,200,70]
    write_layout(s.directory,s)


if __name__=='__main__': main()
