"""Shared palette, units and serialization for Greenbox's true voxel cast."""
from pathlib import Path
import sys, json, hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Asset, RGB, COL, PALETTE, write_vox
from voxel_components import components
PITCH = .05
EXTRA = {
 'rasta_red': (201,47,43), 'rasta_gold': (242,194,54), 'rasta_green': (39,130,73),
 'skin': (142,88,52), 'locs': (39,28,23), 'skin_light': (175,115,73),
 'skin_pale': (235,181,145), 'skin_tan': (187,130,84),
 'hair_blonde': (243,203,91), 'hair_blonde_shadow': (186,132,48),
 'hair_brown': (74,47,34), 'suit': (45,51,72), 'suit_light': (63,77,98),
 'tie_red': (175,39,50), 'steel': (151,170,184), 'steel_dark': (78,99,111),
 'chrome': (207,221,224), 'cyan': (77,223,224), 'chef_white': (246,242,234),
 'bone': (231,221,191), 'bone_shadow': (176,163,130),
 'dress_pink': (204,55,135), 'dress_violet': (119,58,157),
 'heel_dark': (40,31,48), 'hair_auburn': (139,54,36),
 'lapel': (26,32,52), 'eye_blue': (55,100,134), 'lip': (171,58,68),
 'gold': (228,176,55), 'blush': (212,118,99),
}
for index, (name,rgb) in enumerate(EXTRA.items(),34):
 RGB[name]=rgb; COL[name]=index; PALETTE[index]=(*rgb,255)

DEFAULT_JOINTS={
 'torso':(8,5.5,13), 'head':(8,5.5,23),
 'arm_left':(3.5,5.5,22), 'arm_right':(12.5,5.5,22),
 'leg_left':(6,5.5,13), 'leg_right':(10,5.5,13),
}

def save_character(name, parts, description, joints=None, root_pivot=(8,5.5,0)):
 joints=joints or DEFAULT_JOINTS
 if {p.name for p in parts} != set(DEFAULT_JOINTS):
  raise ValueError('Exactly six named rigid parts are required')
 whole=Asset(name); overlaps=[]
 for part in parts:
  overlaps.extend(p for p in part.v if p in whole.v)
  whole.v.update(part.v)
 if overlaps: raise ValueError(f'{name}: {len(overlaps)} overlapping part cells')
 if len(components(whole.v)) != 1: raise ValueError(f'{name}: disconnected assembled character')
 serialized=[]
 for part in parts:
  if len(components(part.v)) != 1: raise ValueError(f'{name}/{part.name}: disconnected rigid part')
  data=part.serialized(); joint=joints[part.name]
  data['metadata']={
   'part':part.name, 'connected_components':1,
   'joint_source_voxels':list(joint),
   'mesh_pivot_source_voxels':[joint[i]-data['normalization_offset'][i] for i in range(3)],
   'joint_glb_translation_meters':[(joint[0]-root_pivot[0])*PITCH,joint[2]*PITCH,-(joint[1]-root_pivot[1])*PITCH],
  }
  serialized.append(data)
 data=whole.serialized()
 data.update(schema='rigid-voxel-avatar-v1',palette=PALETTE,parts=serialized)
 data['metadata']={
  'authoring':'Original occupied-cube artwork for Greenbox; no external character asset or likeness',
  'design':description,'voxel_pitch_meters':PITCH,
  'source_axes':'X/Y horizontal, Z up; faces native -Y',
  'glb_axes':'Y up, forward +Z','source_root_pivot':list(root_pivot),
  'connected_components':1,'part_overlap_cells':0,
  'mesh_pivot_source_voxels':[root_pivot[i]-data['normalization_offset'][i] for i in range(3)],
 }
 folder=ROOT/name
 folder.mkdir(parents=True,exist_ok=True)
 path=folder/(name+'.json'); path.write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8')
 write_vox(folder/(name+'.vox'),data)
 for part in serialized: write_vox(folder/(part['name']+'.vox'),part)
 manifest={'asset':name,'description':description,'dimensions_voxels':data['dimensions'],
  'voxel_count':len(data['voxels']),'metadata':data['metadata'],
  'parts':[{k:p[k] for k in ('name','dimensions','normalization_offset','metadata')} for p in serialized],
  'vox_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.vox')},
  'source_json_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 (folder/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'asset':name,'voxels':len(data['voxels']),'dimensions':data['dimensions'],'path':str(folder)}),flush=True)
 return data
