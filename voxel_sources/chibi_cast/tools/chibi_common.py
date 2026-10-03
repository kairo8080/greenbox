"""Original Greenbox chibi artwork on the same exact cubic grid and palette."""
from pathlib import Path
import sys, json, hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from character_common import Asset, COL, RGB, PALETTE, PITCH, components
PACK = ROOT
JOINTS = {'torso':(10,7,7), 'head':(10,7,14),
          'arm_left':(5.5,7,12.5), 'arm_right':(14.5,7,12.5),
          'leg_left':(7.5,7,7), 'leg_right':(12.5,7,7)}
ROOT_PIVOT = (10,7,0)

def soft_box(asset, x0,y0,z0,x1,y1,z1,color):
    """Step the edges by one occupied cube; never bevel or smooth a mesh."""
    for x in range(x0,x1):
        for y in range(y0,y1):
            for z in range(z0,z1):
                edges = sum((x in (x0,x1-1), y in (y0,y1-1), z in (z0,z1-1)))
                if edges < 2: asset.set(x,y,z,color)
    return asset

def head_base(skin='skin_pale'):
    a=Asset('head')
    a.box(8,5,14,12,9,16,skin)
    soft_box(a,2,1,15,18,13,28,skin)
    return a

def face(a, skin='skin_pale', eyes='ink', smile='lip', blush=True):
    # Oversized eyes with highlights, compact nose and a small gentle smile.
    a.box(5,0,21,8,2,24,eyes); a.box(12,0,21,15,2,24,eyes)
    a.set(5,0,23,'white'); a.set(12,0,23,'white')
    a.box(9,0,19,11,2,21,skin)
    a.box(8,0,18,12,2,19,smile)
    if blush:
        a.box(3,0,19,5,2,20,'blush'); a.box(15,0,19,17,2,20,'blush')
    return a

def torso_base(color='teal'):
    a=Asset('torso'); a.box(6,4,7,14,10,14,color)
    return a

def arm_base(left, sleeve='teal', skin='skin_pale'):
    a=Asset('arm_left' if left else 'arm_right'); x=3 if left else 14
    a.box(x,4,9,x+3,10,14,sleeve)
    a.box(x,4,6,x+3,9,9,skin)
    return a

def leg_base(left, trouser='navy', shoe='ink'):
    a=Asset('leg_left' if left else 'leg_right'); x=6 if left else 11
    a.box(x,4,3,x+3,10,7,trouser)
    a.box(5 if left else 10,2,0,10 if left else 15,11,3,shoe)
    return a

def save_character(name, parts, description, joints=None):
    joints = joints or JOINTS
    if {part.name for part in parts} != set(JOINTS): raise ValueError('Exactly six named rigid parts required')
    whole=Asset(name)
    serialized=[]
    for part in parts:
        if any(cell in whole.v for cell in part.v): raise ValueError(f'{name}: part overlap in {part.name}')
        if len(components(part.v)) != 1: raise ValueError(f'{name}: disconnected {part.name}')
        whole.v.update(part.v)
        item=part.serialized(); joint=joints[part.name]
        item['metadata']={'part':part.name,'connected_components':1,'joint_source_voxels':list(joint),
          'mesh_pivot_source_voxels':[joint[i]-item['normalization_offset'][i] for i in range(3)],
          'joint_glb_translation_meters':[(joint[0]-10)*PITCH,joint[2]*PITCH,-(joint[1]-7)*PITCH]}
        serialized.append(item)
    if len(components(whole.v)) != 1: raise ValueError(f'{name}: disconnected assembled model')
    data=whole.serialized(); data.update(schema='rigid-voxel-avatar-v1',palette=PALETTE,parts=serialized)
    data['metadata']={'authoring':'Original Greenbox chibi occupied-cube artwork; no external character asset or likeness',
      'design':description,'style':'chibi','voxel_pitch_meters':PITCH,
      'source_axes':'X/Y horizontal, Z up; faces native -Y','glb_axes':'Y up, forward +Z',
      'source_root_pivot':list(ROOT_PIVOT),'connected_components':1,'part_overlap_cells':0,
      'mesh_pivot_source_voxels':[ROOT_PIVOT[i]-data['normalization_offset'][i] for i in range(3)]}
    folder=PACK/name; folder.mkdir(parents=True,exist_ok=True)
    path=folder/(name+'.json')
    path.write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
    # common.write_vox uses the same mutable PALETTE shared with character_common.
    from common import write_vox
    write_vox(folder/(name+'.vox'),data)
    for item in serialized: write_vox(folder/(item['name']+'.vox'),item)
    manifest={'asset':name,'description':description,'dimensions_voxels':data['dimensions'],
      'voxel_count':len(data['voxels']),'metadata':data['metadata'],
      'parts':[{k:item[k] for k in ('name','dimensions','normalization_offset','metadata')} for item in serialized],
      'vox_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.vox')},
      'source_json_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (folder/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'asset':name,'voxels':len(data['voxels']),'dimensions':data['dimensions']}),flush=True)
    return data
