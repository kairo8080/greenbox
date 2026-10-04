"""Export canonical cube surfaces; render a Garden-themed geometry preview."""
from pathlib import Path
import argparse, hashlib, json, sys
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_bedroom as export


def render_scene(folder,samples):
    source=folder/'flat_scene.json'; scene_data=json.loads(source.read_text(encoding='utf-8'))
    models,palette,pitch,emission=export.validate_scene(scene_data)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
    assets=bpy.data.collections.new('True voxel garden geometry'); studio=bpy.data.collections.new('Preview lighting and camera')
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
    # This exact canonical GLB is exported before changing any preview materials.
    export.export_objects(folder/(folder.name+'.glb'),objects)
    checked=export.verify_glb(folder/(folder.name+'.glb'),objects,folder/'palette.png')
    themes=json.loads((ROOT/'preview_palette.json').read_text(encoding='utf-8'))
    preview_palette=themes['colors']
    preview_atlas,preview_hash=export.write_palette_atlas(folder/'preview_palette.png',preview_palette)
    for material in materials:
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE': node.image=preview_atlas
    mins,maxs,_=export.bounds_for_objects(objects); size=Vector(maxs)-Vector(mins); span=max(size)
    target=(Vector(mins)+Vector(maxs))/2; target.z-=size.z*.1
    camera_data=bpy.data.cameras.new('Garden diorama camera'); camera=bpy.data.objects.new('Garden diorama camera',camera_data)
    studio.objects.link(camera); scene.camera=camera
    camera_data.type='ORTHO'; camera_data.ortho_scale=span*1.86
    camera.location=target+Vector((1.5,-2.0,1.8))*span; export.aim(camera,target)
    scene.render.engine='CYCLES'; scene.cycles.samples=samples; scene.cycles.use_denoising=True
    scene.render.resolution_x=1200; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='Standard'
    world=bpy.data.worlds.new('Garden studio world'); world.use_nodes=True; scene.world=world
    ground_mesh=bpy.data.meshes.new('Backdrop mesh'); ground_mesh.from_pydata([(-span*3,-span*3,-.02),(span*4,-span*3,-.02),(span*4,span*4,-.02),(-span*3,span*4,-.02)],[],[(0,1,2,3)])
    ground=bpy.data.objects.new('Preview backdrop',ground_mesh); studio.objects.link(ground)
    ground_mat=bpy.data.materials.new('Pale sage backdrop'); ground_mat.diffuse_color=(.6,.66,.6,1); ground.data.materials.append(ground_mat)
    light_objects=[]
    for mode in ('day','night'):
        for obj in light_objects: bpy.data.objects.remove(obj,do_unlink=True)
        light_objects=[]; night=mode=='night'
        world.node_tree.nodes['Background'].inputs['Color'].default_value=(.04,.07,.15,1) if night else (.75,.85,.79,1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value=.2 if night else .3
        light_objects.append(export.area_light(studio,'Moon' if night else 'Sun',target+Vector((-span,-span,span*1.7)),target,(12 if night else 55)*span*span,span*.28,(.4,.61,1) if night else (1,.91,.75)))
        light_objects.append(export.area_light(studio,'Sky fill',target+Vector((span,-span*.8,span)),target,(5 if night else 20)*span*span,span,(.34,.48,.9) if night else (.73,.9,1)))
        ground_mat.diffuse_color=(.035,.055,.095,1) if night else (.6,.66,.6,1)
        scene.render.filepath=str(folder/(folder.name+'_'+mode+'.png'))
        bpy.ops.render.render(write_still=True)
        if not night: bpy.ops.wm.save_as_mainfile(filepath=str(folder/(folder.name+'.blend')))
    report={'schema':'greenbox-lore-mesh-v1','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_vox_sha256':hashlib.sha256((folder/(folder.name+'.vox')).read_bytes()).hexdigest(),'voxel_pitch_meters':pitch,'assets':mesh_records,'glb':checked,'bounds_native_meters':{'min':mins,'max':maxs},'palette_png_sha256':atlas_hash,'preview_palette_png_sha256':preview_hash,'preview_theme':'Garden','preview_palette_sha256':hashlib.sha256(bytes(v for color in preview_palette for v in color)).hexdigest(),'source_axes':'Z up, front -Y','glb_axes':'Y up, front +Z','preview_geometry':'Actual exact occupied-cube surfaced union; Garden palette preview remap only; no smoothed geometry or copied reference assets','lights_and_camera_excluded_from_glb':True,'blender':bpy.app.version_string}
    (folder/'mesh_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('GARDEN_EXPORT '+json.dumps({'name':folder.name,**checked}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('folders',nargs='+',type=Path); parser.add_argument('--samples',type=int,default=16)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    for folder in args.folders: render_scene(folder.resolve(),args.samples)
