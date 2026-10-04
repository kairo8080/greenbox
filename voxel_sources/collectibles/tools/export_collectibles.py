"""Export canonical, centered-ground GLBs before rendering Garden presentation."""
from pathlib import Path
import argparse, hashlib, json, sys
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_bedroom as export
from build_collectibles import LABELS, RARITIES

def render(folder,samples):
 name=folder.name; source=folder/(name+'.json'); data=json.loads(source.read_text(encoding='utf-8'))
 palette=data['palette']; pitch=data['metadata']['voxel_pitch_meters']
 voxels={(x,y,z):c for x,y,z,c in data['voxels']}
 bpy.ops.wm.read_factory_settings(use_empty=True)
 scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
 game=bpy.data.collections.new('Game voxel collectible'); studio=bpy.data.collections.new('Preview studio only')
 scene.collection.children.link(game); scene.collection.children.link(studio)
 atlas,atlas_sha=export.write_palette_atlas(folder/'palette.png',palette)
 mats=(export.make_material('Greenbox exact source palette',atlas),export.make_material('Unused source emission',atlas,True))
 mesh,pivot,record=export.mesh_for_asset(data,voxels,palette,pitch,set(),mats)
 obj=bpy.data.objects.new(name,mesh); game.objects.link(obj)
 obj['voxel_pitch_meters']=pitch; obj['source_ground_pivot_voxels']=list(pivot)
 export.export_objects(folder/(name+'.glb'),[obj])
 check=export.verify_glb(folder/(name+'.glb'),[obj],folder/'palette.png')
 check['sha256']=hashlib.sha256((folder/(name+'.glb')).read_bytes()).hexdigest()
 theme=json.loads((ROOT/'preview_theme.json').read_text(encoding='utf-8'))
 image,theme_sha=export.write_palette_atlas(folder/'preview_palette.png',theme['colors'])
 for mat in mats:
  for node in mat.node_tree.nodes:
   if node.type=='TEX_IMAGE': node.image=image
 mins,maxs,corners=export.bounds_for_objects([obj]); size=Vector(maxs)-Vector(mins); span=max(size)
 target=(Vector(mins)+Vector(maxs))/2
 camera_data=bpy.data.cameras.new('Collectible studio camera'); camera=bpy.data.objects.new('Collectible studio camera',camera_data)
 studio.objects.link(camera); scene.camera=camera
 camera_data.type='ORTHO'; camera_data.clip_start=.01; camera_data.clip_end=100
 # Cards stay near frontal so the raised item symbols remain readable.
 direction=(.7,-2.5,1.1) if name.startswith(('card_','booster_')) else (1.55,-2.5,1.65)
 camera.location=target+Vector(direction)*span; export.aim(camera,target)
 scene.render.resolution_x=640; scene.render.resolution_y=800; scene.render.resolution_percentage=100
 bpy.context.view_layer.update()
 projected=[camera.matrix_world.inverted()@p for p in corners]
 camera_data.ortho_scale=1; frame=camera_data.view_frame(scene=scene)
 camera_data.ortho_scale=max((max(p.x for p in projected)-min(p.x for p in projected))/(max(p.x for p in frame)-min(p.x for p in frame)),
  (max(p.y for p in projected)-min(p.y for p in projected))/(max(p.y for p in frame)-min(p.y for p in frame)))*1.16
 scene.render.engine='CYCLES'; scene.cycles.samples=samples; scene.cycles.use_denoising=True; scene.cycles.max_bounces=4
 scene.render.threads_mode='FIXED'; scene.render.threads=4
 scene.view_settings.view_transform='Standard'; scene.render.image_settings.file_format='PNG'
 world=bpy.data.worlds.new('Cream studio world'); world.use_nodes=True; scene.world=world
 world.node_tree.nodes['Background'].inputs['Color'].default_value=(.79,.84,.75,1)
 world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
 gmesh=bpy.data.meshes.new('Studio ground'); gmesh.from_pydata([(-span*4,-span*4,-.015),(span*4,-span*4,-.015),(span*4,span*4,-.015),(-span*4,span*4,-.015)],[],[(0,1,2,3)])
 ground=bpy.data.objects.new('Ground excluded from export',gmesh); studio.objects.link(ground)
 gmat=bpy.data.materials.new('Warm sage studio'); gmat.diffuse_color=(.65,.7,.61,1); gmesh.materials.append(gmat)
 export.area_light(studio,'Warm studio key',target+Vector((-span,-span*1.1,span*1.8)),target,55*span*span,span*.65,(1,.94,.84))
 export.area_light(studio,'Cool soft fill',target+Vector((span,-span*.8,span)),target,20*span*span,span,(.76,.92,1))
 scene.render.filepath=str(folder/'rendered.png'); bpy.ops.render.render(write_still=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')))
 report={'schema':'greenbox-collectible-mesh-v1','id':name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
  'source_vox_sha256':hashlib.sha256((folder/(name+'.vox')).read_bytes()).hexdigest(),'voxel_pitch_meters':pitch,
  'mesh':record,'glb':check,'palette_png_sha256':atlas_sha,'preview_palette_png_sha256':theme_sha,
  'canonical_export_before_preview_theme':True,'source_ground_pivot_voxels':list(pivot),
  'source_axes':'Z up, front -Y','glb_axes':'Y up, front +Z','preview_geometry':'Actual exact occupied-cube surface',
  'preview_theme':'Greenbox Garden','preview_resolution':[640,800],'blender':bpy.app.version_string,
  'preview_camera_lights_and_ground_excluded_from_glb':True}
 (folder/'mesh_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print('COLLECTIBLE_EXPORT '+json.dumps({'id':name,'triangles':check['triangles_unique_mesh_data'],'bytes':check['bytes']}),flush=True)

def catalog():
 assets=[]
 for name,label in LABELS.items():
  folder=ROOT/name
  if not (folder/'mesh_validation.json').is_file(): return
  source=json.loads((folder/(name+'.json')).read_text(encoding='utf-8')); report=json.loads((folder/'mesh_validation.json').read_text(encoding='utf-8'))
  assets.append({'id':name,'label':label,'kind':'collectible','rarity':RARITIES[name],
   'vox':f'{name}/{name}.vox','json':f'{name}/{name}.json','glb':f'{name}/{name}.glb','blend':f'{name}/{name}.blend','preview':f'{name}/rendered.png',
   'dimensions_voxels':source['dimensions'],'filled_voxels':len(source['voxels']),'triangles':report['glb']['triangles_unique_mesh_data'],
   'voxel_pitch_meters':.05,'pivot':'centered ground','source_ground_pivot_voxels':report['source_ground_pivot_voxels'],
   'axes':'GLB Y up, front +Z','scale_note':source['metadata']['grid_scale_note'],
   'vox_sha256':report['source_vox_sha256'],'glb_sha256':report['glb']['sha256']})
 (ROOT/'assets.json').write_text(json.dumps({'schema':'greenbox-collectibles-catalog-v1','voxel_pitch_meters':.05,'assets':assets},indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.add_argument('folders',nargs='*',type=Path); parser.add_argument('--samples',type=int,default=12)
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
 for folder in args.folders or [ROOT/name for name in LABELS]: render(folder.resolve(),args.samples)
 catalog()
