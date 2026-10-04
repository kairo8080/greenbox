"""Export canonical six-part Garden voxels, then render a themed 45 degree view.

Run in Blender's Python. The pose is applied to the preview root only; editable
voxel cells and the neutral game export retain their original cubic grid.
"""
from pathlib import Path
import argparse, hashlib, json, math, struct, sys
from types import SimpleNamespace
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_bedroom as exporter

def verify_glb(path, asset, palette_path, triangle_count):
 raw=path.read_bytes()
 if struct.unpack_from('<4sII',raw)!=(b'glTF',2,len(raw)): raise ValueError('Invalid GLB header')
 length,kind=struct.unpack_from('<II',raw,12)
 if kind!=0x4E4F534A: raise ValueError('Missing GLB JSON')
 doc=json.loads(raw[20:20+length]); nodes=doc['nodes']
 if len(nodes)!=7 or len(doc['meshes'])!=6: raise ValueError('Expected one root and six rigid meshes')
 root=next(n for n in nodes if n.get('name')=='CharacterRoot')
 if {nodes[i]['name'] for i in root['children']} != {p['name'] for p in asset['parts']}:
  raise ValueError('Rigid part hierarchy differs from source')
 if any(n.get('rotation') not in (None,[0,0,0,1]) for n in nodes):
  raise ValueError('Preview pose leaked into neutral GLB')
 for part in asset['parts']:
  node=next(n for n in nodes if n['name']==part['name'])
  if any(abs(a-b)>1e-6 for a,b in zip(node.get('translation',[0,0,0]),part['metadata']['joint_glb_translation_meters'])):
   raise ValueError('Joint translation mismatch')
 triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])
 if triangles!=triangle_count or len(doc['materials'])!=1: raise ValueError('Surface export differs')
 if doc.get('cameras') or doc.get('extensions',{}).get('KHR_lights_punctual'):
  raise ValueError('Preview objects leaked into export')
 view=doc['bufferViews'][doc['images'][0]['bufferView']]
 start=28+length+view.get('byteOffset',0)
 if raw[start:start+view['byteLength']]!=palette_path.read_bytes(): raise ValueError('Palette changed')
 if any(s.get('magFilter')!=9728 for s in doc['samplers']): raise ValueError('Palette filtering changed')
 return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'triangles':triangles,
  'meshes':6,'materials':1,'palette_embedded_exactly':True,'nearest_sampling':True,
  'preview_objects_excluded':True,'neutral_pose':True,'joint_translations_verified':True}

def process(folder, samples=32):
 name=folder.name; source=folder/(name+'.json')
 asset=json.loads(source.read_text(encoding='utf-8'))
 pitch=asset['metadata']['voxel_pitch_meters']; root_pivot=asset['metadata']['source_root_pivot']
 bpy.ops.wm.read_factory_settings(use_empty=True)
 scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
 geometry=bpy.data.collections.new('Game character'); scene.collection.children.link(geometry)
 studio=bpy.data.collections.new('Preview camera and lighting'); scene.collection.children.link(studio)
 root=bpy.data.objects.new('CharacterRoot',None); geometry.objects.link(root)
 root['voxel_pitch_meters']=pitch; root['source_vox']=name+'.vox'
 palette=folder/'palette.png'
 atlas,palette_hash=exporter.write_palette_atlas(palette,asset['palette'])
 mats=(exporter.make_material(name+' exact palette',atlas),exporter.make_material('Unused emission',atlas,True))
 objects=[]; records=[]
 for part in asset['parts']:
  voxels={(x,y,z):c for x,y,z,c in part['voxels']}
  mesh,center,record=exporter.mesh_for_asset(part,voxels,asset['palette'],pitch,set(),mats)
  joint=part['metadata']['mesh_pivot_source_voxels']
  for v in mesh.vertices: v.co+=Vector([(center[i]-joint[i])*pitch for i in range(3)])
  mesh.update(); obj=bpy.data.objects.new(part['name'],mesh); geometry.objects.link(obj)
  obj.parent=root; raw_joint=part['metadata']['joint_source_voxels']
  obj.location=[(raw_joint[i]-root_pivot[i])*pitch for i in range(3)]
  obj['rigid_joint']=part['metadata']['joint_glb_translation_meters']
  objects.append(obj); records.append(record)
 glb=folder/(name+'.glb'); exporter.export_objects(glb,[root]+objects)
 checked=verify_glb(glb,asset,palette,sum(r['triangles'] for r in records))
 root.rotation_euler.z=math.radians(45)
 bpy.context.view_layer.update()
 args=SimpleNamespace(engine='eevee',samples=samples,resolution=[800,1000])
 camera,_=exporter.setup_preview({'instances':[]},{},objects,studio,pitch,asset['palette'],set(),args)
 mins,maxs,corners=exporter.bounds_for_objects(objects)
 height=maxs[2]-mins[2]
 target=Vector(((mins[0]+maxs[0])*.5,(mins[1]+maxs[1])*.5,mins[2]+height*.5))
 # Palette changes occur only after the neutral canonical GLB has been exported.
 theme=json.loads((ROOT/'preview_theme.json').read_text(encoding='utf-8'))
 theme_atlas,theme_sha=exporter.write_palette_atlas(folder/'garden_preview_palette.png',theme['colors'])
 for mat in mats:
  for node in mat.node_tree.nodes:
   if node.type=='TEX_IMAGE': node.image=theme_atlas
 # A moderate orthographic elevation shows the broad head panels and short limbs.
 camera.data.type='ORTHO'
 distance=height*3.05
 camera.location=target+Vector((0,-distance,distance*math.tan(math.radians(24))))
 exporter.aim(camera,target)
 camera.data.clip_start=.01; camera.data.clip_end=100
 bpy.context.view_layer.update()
 projection=[camera.matrix_world.inverted()@point for point in corners]
 camera.data.ortho_scale=1
 frame=camera.data.view_frame(scene=scene)
 camera.data.ortho_scale=max(
  (max(p.x for p in projection)-min(p.x for p in projection))/(max(p.x for p in frame)-min(p.x for p in frame)),
  (max(p.y for p in projection)-min(p.y for p in projection))/(max(p.y for p in frame)-min(p.y for p in frame)))*1.16
 # A curved studio floor keeps a low camera from revealing a hard horizon.
 ground=bpy.data.objects.get('Preview ground (excluded from export)')
 ground_material=ground.data.materials[0]
 bpy.data.objects.remove(ground,do_unlink=True)
 profile=[(-20,-.01),(3,-.01)]
 radius=4
 for step in range(1,33):
  angle=(math.pi*.5)*step/32
  profile.append((3+radius*math.sin(angle),radius*(1-math.cos(angle))-.01))
 profile.append((7,20))
 vertices=[(x,y,z) for y,z in profile for x in (-50,50)]
 faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(profile)-1)]
 backdrop_mesh=bpy.data.meshes.new('Studio curved backdrop')
 backdrop_mesh.from_pydata(vertices,[],faces); backdrop_mesh.materials.append(ground_material)
 for face in backdrop_mesh.polygons: face.use_smooth=True
 backdrop=bpy.data.objects.new('Preview backdrop; excluded from GLB',backdrop_mesh); studio.objects.link(backdrop)
 bpy.context.view_layer.update()
 scene.render.filepath=str(folder/(name+'_preview.png'))
 blend=folder/(name+'.blend'); bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 bpy.ops.render.render(write_still=True)
 report={'asset':name,'source_json_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
  'source_voxel_count':len(asset['voxels']),'dimensions_voxels':asset['dimensions'],
  'height_meters':height,'palette_sha256':palette_hash,'parts':records,'glb':checked,
  'preview':{'method':'Rendered from actual occupied-cube geometry','character_yaw_degrees':45,
   'face_direction_in_image':'right','camera_type':'orthographic','camera_elevation_degrees':24,
   'resolution':[800,1000],'theme':theme['label'],'theme_palette_png_sha256':theme_sha,
   'game_glb_uses_canonical_palette':True},'blender':bpy.app.version_string}
 (folder/'mesh_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('CAST_EXPORT '+json.dumps({'name':name,**checked}),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.add_argument('folders',nargs='+',type=Path); parser.add_argument('--samples',type=int,default=32)
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
 for folder in args.folders: process(folder.resolve(),args.samples)
