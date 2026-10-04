"""Build original Greenbox collectible objects on the exact canonical cubic grid."""
from pathlib import Path
import hashlib, json
from character_common import Asset, COL, PALETTE, PITCH, components
from common import write_vox
from lore_common import text, leaf_motif, FONT
ROOT=Path(__file__).resolve().parents[1]
PALETTE_HASH='09cb38d6cb39613d53228591ed2d7cdefc47a98cbdb81f78ab19b65dd3c36293'
FONT['?']=['01110','10001','00001','00010','00100','00000','00100']
LABELS={'grower_toybox':'Grower toybox','mystery_standard':'Standard mystery box','mystery_420_founder':'420 Founder mystery box',
 'booster_common':'Common booster pack','booster_rare':'Rare booster pack','booster_epic':'Epic booster pack',
 'card_common':'Common / Watering can','card_rare':'Rare / Grow light','card_epic':'Epic / Greenhouse key'}
RARITIES={'grower_toybox':'collectible','mystery_standard':'standard','mystery_420_founder':'founder',
 **{f'{kind}_{rarity}':rarity for kind in ('booster','card') for rarity in ('common','rare','epic')}}
DESCRIPTIONS={}

def toybox():
 a=Asset('grower_toybox')
 a.box(0,0,0,32,28,5,'linen')
 a.box(0,0,5,3,28,48,'teal'); a.box(29,0,5,32,28,48,'teal')
 a.box(3,25,5,29,28,48,'teal')
 a.box(3,25,7,29,26,39,'leaf_dark')
 a.box(0,0,39,32,28,48,'teal')
 a.box(0,0,47,32,28,48,'teal_light')
 a.box(0,0,39,32,1,40,'teal_light')
 a.box(3,1,5,29,25,6,'leaf_light')
 text(a,'GB',4,-1,41,'linen')
 leaf_motif(a,24,-1,42,'leaf_tip',scale=0.5)
 a.box(0,0,1,32,1,2,'teal_light')
 # The display window is real empty volume. No transparent mesh covers it.
 source=ROOT/'inputs/rasta_grower.json'; grower=json.loads(source.read_text(encoding='utf-8'))
 assert grower['palette']==[list(c) for c in PALETTE]
 offset=(5,4,6)
 reused={tuple(cell[i]+offset[i] for i in range(3)):cell[3] for cell in grower['voxels']}
 assert not set(a.v)&set(reused),'Toybox frame must not intersect original character'
 a.v.update(reused)
 a.meta['reused_character']={'path':'inputs/rasta_grower.json','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
  'asset':'rasta_grower','offset_voxels':list(offset),'cells_preserved_exactly':True,'reused_cells':len(reused)}
 a.meta['display_window']={'axis':'front -Y','transparent_surface':False,'opening_native_voxels':[[3,0,6],[29,25,39]],
  'description':'Frame edges surround an actual air opening; original character occupies only its preserved source cells inside.'}
 DESCRIPTIONS[a.name]='Open-front teal and cream toy display with the original Garden grower, raised original GB badge and lime interior. Static connected collectible prop; the separately supplied character keeps its six movable parts.'
 return a

def mystery(founder=False):
 a=Asset('mystery_420_founder' if founder else 'mystery_standard')
 shell='ink' if founder else 'teal'; accent='gold' if founder else 'linen'
 a.box(0,0,0,28,28,28,shell)
 a.box(0,0,0,28,28,3,accent); a.box(0,0,25,28,28,28,shell)
 a.box(0,0,27,28,28,28,accent)
 for x in (0,26): a.box(x,0,3,x+2,28,27,accent)
 a.box(0,0,24,28,1,25,accent); a.box(0,0,3,28,1,4,accent)
 if founder:
  text(a,'420',5,-1,11,'gold')
  text(a,'GB',9,-1,4,'linen')
  a.box(2,2,27,26,26,28,'suit')
  leaf_motif(a,14,14,28,'gold',plane='xy')
  DESCRIPTIONS[a.name]='Dark Founder mystery crate, golden corner rails, raised 420 number and original lime/gold leaf crest. Founder is an art rarity label, with no token or financial promise.'
 else:
  text(a,'?',9,-1,7,'linen',scale=2)
  a.box(11,0,0,17,28,3,'teal_light')
  a.box(2,2,27,26,26,28,'teal_light')
  leaf_motif(a,14,14,28,'leaf_tip',plane='xy')
  DESCRIPTIONS[a.name]='Standard turquoise mystery crate with cream corner rails, raised question mark and original leaf crest.'
 return a

def icon(a,rarity,y=-1,z=14,x=0):
 # Every mark is a finite occupied cube relief bonded to the wrapper/card.
 def b(x0,z0,x1,z1,c): a.box(x+x0,y,z+z0,x+x1,y+1,z+z1,c)
 if rarity=='common':
  b(7,0,17,7,'teal_light'); b(7,7,17,8,'teal')
  b(4,2,7,7,'teal'); b(3,3,4,6,'teal'); b(4,6,7,8,'teal')
  b(17,3,20,6,'teal_light'); b(20,5,22,8,'teal_light'); b(21,8,24,10,'teal_light')
  b(22,10,24,12,'water'); b(24,8,25,10,'water')
  b(8,8,16,9,'metal'); b(9,0,12,1,'water')
 elif rarity=='rare':
  b(5,9,21,13,'steel_dark'); b(6,9,20,10,'white')
  b(12,13,14,16,'steel'); b(9,15,17,16,'steel')
  for px in (7,11,15,18):
   b(px,5,px+1,8,'warm_light'); b(px,1,px+1,3,'yellow')
  b(7,10,9,12,'warm_light'); b(12,10,14,12,'warm_light'); b(17,10,19,12,'warm_light')
 else:
  b(9,9,17,11,'gold'); b(9,15,17,17,'gold')
  b(8,11,10,15,'gold'); b(16,11,18,15,'gold')
  b(12,1,15,10,'gold'); b(14,1,20,3,'gold'); b(17,4,20,6,'gold')
  b(10,14,12,16,'rasta_gold'); b(18,1,20,2,'rasta_gold')

def rarity_marks(a,rarity,y,z):
 n=('common','rare','epic').index(rarity)+1
 for i in range(n): a.box(4+i*4,y,z,6+i*4,y+1,z+2,'gold' if rarity=='epic' else 'linen')

def booster(rarity):
 a=Asset('booster_'+rarity); primary={'common':'leaf','rare':'blue','epic':'dress_pink'}[rarity]
 shade={'common':'leaf_dark','rare':'navy','epic':'dress_violet'}[rarity]
 a.box(1,0,2,25,7,36,primary)
 a.box(0,0,0,26,7,3,shade); a.box(0,0,35,26,7,38,shade)
 a.box(1,0,36,25,1,37,'linen'); a.box(1,0,1,25,1,2,'linen')
 # Wide seal folds and sparse corner chips preserve the wrapper silhouette.
 for x in range(2,25,4):
  a.box(x,0,0,x+1,7,1,primary); a.box(x,0,37,x+1,7,38,primary)
 a.box(2,0,12,24,1,30,shade)
 text(a,'GB',7,-1,30,'linen')
 icon(a,rarity,z=12)
 text(a,rarity[0],18,-1,4,'linen')
 rarity_marks(a,rarity,-1,6)
 a.box(4,7,13,22,8,27,'linen'); text(a,'GB',8,8,18,shade)
 DESCRIPTIONS[a.name]=f'Sealed {rarity} booster wrapper, raised Greenbox badge, {1+list(("common","rare","epic")).index(rarity)} rarity blocks and matching original item relief. No randomized opening mechanic is included.'
 return a

def card(rarity):
 a=Asset('card_'+rarity); edge={'common':'leaf','rare':'blue','epic':'dress_pink'}[rarity]
 a.box(0,0,0,26,2,38,edge)
 a.box(2,0,2,24,1,36,'linen')
 a.box(3,0,12,23,1,29,'ink' if rarity=='epic' else 'navy' if rarity=='rare' else 'leaf_dark')
 text(a,'GB',4,-1,30,edge)
 text(a,rarity[0],18,-1,30,edge)
 icon(a,rarity,z=12)
 rarity_marks(a,rarity,-1,8)
 # Broad lower stat strips read as game information without tiny fake text.
 a.box(4,-1,4,17,0,5,edge); a.box(4,-1,6,13,0,7,edge)
 a.box(20,-1,4,22,0,7,'gold' if rarity=='epic' else edge)
 a.box(2,1,2,24,2,36,edge)
 a.box(4,2,10,22,3,28,'linen'); text(a,'GB',8,3,17,edge)
 DESCRIPTIONS[a.name]=f'{rarity.capitalize()} voxel TCG item card with a raised '+{'common':'watering can','rare':'grow light','epic':'greenhouse key'}[rarity]+' icon, rarity marks, cream face and original GB back. All art is actual 1-cell relief, not an image plane.'
 return a

def save(a):
 assert len(components(a.v))==1,(a.name,'disconnected')
 data=a.serialized(); dims=data['dimensions']; pivot=[dims[0]/2,dims[1]/2,0]
 data.update(schema='greenbox-voxel-collectible-v1',palette=PALETTE)
 data['metadata'].update(description=DESCRIPTIONS[a.name],voxel_pitch_meters=PITCH,source_axes='Z up, front -Y',glb_axes='Y up, front +Z',
  source_ground_pivot_voxels=pivot,connected_components=1,rarity=RARITIES[a.name],
  grid_scale_note='0.05 m per occupied cell. Cards and packs are enlarged collectible art at source scale; uniformly resize their game instances for hand-held use.')
 folder=ROOT/a.name; folder.mkdir(parents=True,exist_ok=True)
 (folder/(a.name+'.json')).write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
 write_vox(folder/(a.name+'.vox'),data)
 manifest={'id':a.name,'label':LABELS[a.name],'rarity':RARITIES[a.name], 'description':DESCRIPTIONS[a.name],
  'dimensions_voxels':dims,'occupied_voxels':len(a.v),'connected_components':1,'voxel_pitch_meters':PITCH,
  'canonical_palette_sha256':PALETTE_HASH,'source_normalization_offset':data['normalization_offset'],'source_ground_pivot_voxels':pivot,
  'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [folder/(a.name+'.json'),folder/(a.name+'.vox')]}}
 (folder/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'id':a.name,'voxels':len(a.v),'dimensions':dims}),flush=True)

def main():
 assert hashlib.sha256(bytes(v for c in PALETTE for v in c)).hexdigest()==PALETTE_HASH
 for a in (toybox(),mystery(),mystery(True),*[booster(r) for r in ('common','rare','epic')],*[card(r) for r in ('common','rare','epic')]): save(a)

if __name__=='__main__': main()
