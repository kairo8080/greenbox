"""Garden chibi grid: large cube heads above tiny original Greenbox bodies."""
from pathlib import Path
import json, hashlib
from character_common import Asset, COL, RGB, PALETTE, PITCH, components
from common import write_vox

PACK = Path(__file__).resolve().parents[1]
ROOT_PIVOT = (11,10,0)
JOINTS = {'torso':(11,10,4),'head':(11,10,9),
 'arm_left':(7,10,8),'arm_right':(15,10,8),
 'leg_left':(8.5,10,4),'leg_right':(13.5,10,4)}

def head_base(color):
    a=Asset('head')
    a.box(9,8,9,13,12,10,color)
    a.box(2,2,10,20,18,27,color)
    return a

def face(a,skin,eyes='ink',mouth='lip'):
    # Dark solid eye blocks read clearly from small game cameras.
    a.box(5,1,17,8,3,20,eyes); a.box(14,1,17,17,3,20,eyes)
    a.box(10,1,15,12,3,17,skin)
    a.box(10,1,13,12,3,14,mouth)
    return a

def torso_base(color):
    a=Asset('torso'); a.box(7,7,4,15,13,9,color)
    return a

def arm_base(left,sleeve,skin):
    a=Asset('arm_left' if left else 'arm_right'); x=4 if left else 15
    a.box(x,7,6,x+3,12,9,sleeve)
    a.box(x,7,3,x+3,11,6,skin)
    return a

def leg_base(left,trouser,shoe):
    a=Asset('leg_left' if left else 'leg_right'); x=7 if left else 12
    a.box(x,7,2,x+3,12,4,trouser)
    a.box(x,6,0,x+3,13,2,shoe)
    return a

def chip(a,x,y,z,color,length=2,axis='x'):
    """A small colored corner mark; it never changes cubic occupancy."""
    for i in range(length):
        p=[x,y,z]; p['xyz'.index(axis)]+=i
        if tuple(p) not in a.v: raise ValueError('Corner chip outside solid surface')
        a.set(*p,color)

def save_character(name,parts,description):
    if {p.name for p in parts} != set(JOINTS): raise ValueError('Exactly six rigid parts required')
    whole=Asset(name); serialized=[]
    for part in parts:
        if set(part.v)&set(whole.v): raise ValueError(name+': part overlap '+part.name)
        if len(components(part.v))!=1: raise ValueError(name+': disconnected part '+part.name)
        whole.v.update(part.v); item=part.serialized(); joint=JOINTS[part.name]
        item['metadata']={'part':part.name,'connected_components':1,
          'joint_source_voxels':list(joint),
          'mesh_pivot_source_voxels':[joint[i]-item['normalization_offset'][i] for i in range(3)],
          'joint_glb_translation_meters':[(joint[0]-ROOT_PIVOT[0])*PITCH,joint[2]*PITCH,-(joint[1]-ROOT_PIVOT[1])*PITCH]}
        serialized.append(item)
    if len(components(whole.v))!=1: raise ValueError(name+': disconnected assembly')
    data=whole.serialized(); data.update(schema='rigid-voxel-avatar-v1',palette=PALETTE,parts=serialized)
    data['metadata']={'authoring':'Original Greenbox Garden chibi occupied-cube artwork; no external model, game logo or character likeness',
      'design':description,'style':'garden','voxel_pitch_meters':PITCH,
      'source_axes':'X/Y horizontal, Z up; faces native -Y','glb_axes':'Y up, forward +Z',
      'source_root_pivot':list(ROOT_PIVOT),'connected_components':1,'part_overlap_cells':0,
      'mesh_pivot_source_voxels':[ROOT_PIVOT[i]-data['normalization_offset'][i] for i in range(3)],
      'reference_note':'Broad cubic proportions and sparse corner-color accents from user-supplied voxel art references; original Greenbox designs, no imported screenshot content'}
    folder=PACK/name; folder.mkdir(parents=True,exist_ok=True)
    source=folder/(name+'.json')
    source.write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
    for item in [data]+serialized: write_vox(folder/(item['name']+'.vox'),item)
    manifest={'asset':name,'description':description,'dimensions_voxels':data['dimensions'],
      'voxel_count':len(data['voxels']),'metadata':data['metadata'],
      'parts':[{k:item[k] for k in ('name','dimensions','normalization_offset','metadata')} for item in serialized],
      'vox_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob('*.vox'))},
      'source_json_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    (folder/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'asset':name,'voxels':len(data['voxels']),'dimensions':data['dimensions']}),flush=True)
    return data
