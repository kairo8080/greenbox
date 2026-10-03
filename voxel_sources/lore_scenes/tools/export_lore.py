"""Export exact lore scene cube surfaces and render day/night art-direction previews."""
from pathlib import Path
import argparse, hashlib, json, math, sys
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_bedroom as export

def render_scene(folder, samples):
    source=folder/'flat_scene.json'; scene_data=json.loads(source.read_text(encoding='utf-8'))
    models,palette,pitch,emission=export.validate_scene(scene_data)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
    assets=bpy.data.collections.new('True voxel lore geometry'); studio=bpy.data.collections.new('Preview lighting and camera')
    scene.collection.children.link(assets); scene.collection.children.link(studio)
    atlas,atlas_hash=export.write_palette_atlas(folder/'palette.png',palette)
    materials=(export.make_material('Greenbox exact palette',atlas),export.make_material('Greenbox luminous palette',atlas,True))
    objects=[]; mesh_records=[]
    for instance in scene_data['instances']:
        asset,voxels=models[instance['asset']]
        mesh,pivot,record=export.mesh_for_asset(asset,voxels,palette,pitch,emission,materials)
        obj=bpy.data.objects.new(instance['name'],mesh); assets.objects.link(obj)
        obj.location=tuple((instance['offset'][i]+pivot[i])*pitch for i in range(3))
        obj['voxel_pitch_meters']=pitch; objects.append(obj); mesh_records.append(record)
    export.export_objects(folder/(folder.name+'.glb'),objects)
    checked=export.verify_glb(folder/(folder.name+'.glb'),objects,folder/'palette.png')
    mins,maxs,_=export.bounds_for_objects(objects); size=Vector(maxs)-Vector(mins); span=max(size)
    target=(Vector(mins)+Vector(maxs))/2; target.z-=size.z*.12
    camera_data=bpy.data.cameras.new('Diorama camera'); camera=bpy.data.objects.new('Diorama camera',camera_data)
    studio.objects.link(camera); scene.camera=camera
    camera_data.type='ORTHO'; camera_data.ortho_scale=span*1.36
    camera.location=target+Vector((1.0,-1.8,1.35))*span
    export.aim(camera,target)
    scene.render.engine='CYCLES'; scene.cycles.samples=samples; scene.cycles.use_denoising=True
    scene.render.resolution_x=1440; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
    world=bpy.data.worlds.new('Greenbox mood world'); world.use_nodes=True; scene.world=world
    ground_mesh=bpy.data.meshes.new('Backdrop mesh'); ground_mesh.from_pydata([(-span,-span,-.02),(span*2,-span,-.02),(span*2,span*2,-.02),(-span,span*2,-.02)],[],[(0,1,2,3)])
    ground=bpy.data.objects.new('Preview backdrop',ground_mesh); studio.objects.link(ground)
    ground_mat=bpy.data.materials.new('Backdrop'); ground_mat.diffuse_color=(.025,.045,.07,1); ground.data.materials.append(ground_mat)
    light_objects=[]
    for mode in ('day','night'):
        for obj in light_objects: bpy.data.objects.remove(obj,do_unlink=True)
        light_objects=[]; night=mode=='night'
        world.node_tree.nodes['Background'].inputs['Color'].default_value=(.025,.045,.09,1) if night else (.58,.82,.88,1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28 if night else .5
        light_objects.append(export.area_light(studio,'Moon' if night else 'Sun',target+Vector((-span,-span,span*1.7)),target,(18 if night else 140)*span*span,span*.35,(.28,.44,1) if night else (1,.89,.7)))
        light_objects.append(export.area_light(studio,'Sky fill',target+Vector((span,-span*.8,span)),target,(8 if night else 55)*span*span,span,(.28,.44,.9) if night else (.68,.84,1)))
        for i,light in enumerate(scene_data.get('lights',[])):
            pos=Vector(tuple(value*pitch for value in light['source_voxels']))
            color=light['color'].lstrip('#'); rgb=tuple(int(color[j:j+2],16)/255 for j in (0,2,4))
            light_objects.append(export.area_light(studio,'Accent '+str(i),pos,pos+Vector((0,0,-1)),(light.get('night',5)*22 if night else light.get('day',1)*8),.6,rgb))
        ground_mat.diffuse_color=(.025,.045,.07,1) if night else (.42,.56,.55,1)
        scene.render.filepath=str(folder/(folder.name+'_'+mode+'.png'))
        bpy.ops.render.render(write_still=True)
        if (folder.name=='starter_loft' and night) or (folder.name=='roots_street' and not night):
            bpy.ops.wm.save_as_mainfile(filepath=str(folder/(folder.name+'.blend')))
    report={'schema':'greenbox-lore-mesh-v1','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_vox_sha256':hashlib.sha256((folder/(folder.name+'.vox')).read_bytes()).hexdigest(),'voxel_pitch_meters':pitch,'assets':mesh_records,'glb':checked,'bounds_native_meters':{'min':mins,'max':maxs},'palette_png_sha256':atlas_hash,'source_axes':'Z up, front -Y','glb_axes':'Y up, front +Z','preview_geometry':'Actual exact occupied-cube surfaced union; no smoothed geometry or copied reference assets','lights_and_camera_excluded_from_glb':True,'blender':bpy.app.version_string}
    (folder/'mesh_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('LORE_EXPORT '+json.dumps({'name':folder.name,**checked}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('folders',nargs='+',type=Path); parser.add_argument('--samples',type=int,default=16)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    for folder in args.folders: render_scene(folder.resolve(),args.samples)
