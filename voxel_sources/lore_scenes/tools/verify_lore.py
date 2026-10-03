"""Independently verify editable lore scenes and their actual cubic GLB surfaces.

--sources-only checks modular/flattened JSON, VOX and provenance without writing.
--scene NAME checks one scene without writing the final pack report.
With no flags, writes only outputs/greenbox-lore-pack/pack_validation.json.
No scene authoring helper or Blender renderer is imported.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT
NAMES = ('roots_street', 'starter_loft')
PALETTE_HASH = '09cb38d6cb39613d53228591ed2d7cdefc47a98cbdb81f78ab19b65dd3c36293'
EPSILON = 5e-5

# Reuse the independent byte parsers/triangle clipping from the earlier QA.
# This module is a stdlib-only verifier, separate from all authoring/export code.
spec = importlib.util.spec_from_file_location('independent_voxel_binary_qa', Path(__file__).resolve().parent/'verify_cast.py')
binary_qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binary_qa)
require = binary_qa.require
sha = binary_qa.sha
load_json = binary_qa.load_json
source_cells = binary_qa.source_cells
read_vox = binary_qa.read_vox
read_png = binary_qa.read_png
read_glb = binary_qa.read_glb
accessor = binary_qa.accessor
expected_faces = binary_qa.expected_faces
area_in_cell = binary_qa.area_in_cell
components = binary_qa.components
near = binary_qa.near


def palette_check(palette):
    require(isinstance(palette,list) and len(palette)==256 and all(isinstance(c,list) and len(c)==4
            and all(type(v) is int and 0<=v<=255 for v in c) for c in palette), 'Invalid 256 RGBA byte palette')
    require(hashlib.sha256(bytes(v for c in palette for v in c)).hexdigest()==PALETTE_HASH,
            'Canonical full palette differs')


def check_import(asset, palette):
    provenance = asset.get('metadata',{}).get('import_source')
    if not provenance:
        return None
    path = (ROOT/provenance['path']).resolve()
    require(path.is_relative_to(ROOT), 'Import provenance escapes the pack')
    if not path.is_file():
        catalog = load_json(ROOT/'inputs'/'index.json')
        record = catalog['sources'][provenance['path']]
        require(record['sha256']==provenance['sha256'], 'Bundled provenance catalog hash differs')
        path = (ROOT/record['bundled_path']).resolve()
        require(path.is_relative_to(ROOT), 'Bundled input escapes the pack')
    require(sha(path)==provenance['sha256'], 'Imported source hash changed')
    original = load_json(path)
    original_asset = next(a for a in original['assets'] if a['name']==provenance['source_asset']) if 'assets' in original else original
    pitch = original.get('voxel_pitch', original.get('metadata',{}).get('voxel_pitch_meters'))
    require(pitch==.05, 'Imported character/plant source has incompatible voxel scale')
    mapping = {int(k):v for k,v in provenance['color_remap'].items()}
    original_cells = source_cells(original_asset)
    require(set(mapping)==set(original_cells.values()), 'Imported color remap does not cover exact source colors')
    require(all(type(v) is int and 1<=v<=255 and original['palette'][k]==palette[v] for k,v in mapping.items()),
            'Imported source RGBA colors changed')
    expected={p:mapping[c] for p,c in original_cells.items()}; actual=source_cells(asset)
    modification=asset.get('metadata',{}).get('modifications'); rotated=False; recolored=0
    if provenance['source_asset']=='chair' and modification=='Rotated 180 degrees on the same integer grid to face the desk.':
        dx,dy,_=asset['dimensions']
        expected={(dx-1-p[0],dy-1-p[1],p[2]):c for p,c in expected.items()}; rotated=True
    if provenance['source_asset']=='teal_single_bed' and modification=='Existing cubic bed geometry retained; blanket recolored into broad original red/gold/green bands.':
        require(actual.keys()==expected.keys(),'Recolored bed changed its source occupied geometry')
        changed={p:c for p,c in actual.items() if c!=expected[p]}
        require(bool(changed) and set(changed.values())=={34,35,36}, 'Rasta blanket recolor must use original red/gold/green palette roles')
        require(all(1<=p[0]<28 and 1<=p[1]<29 and 12<=p[2]<17 for p in changed),
                'Documented blanket recolor changed cells outside the blanket region')
        recolored=len(changed)
    else:
        require(actual==expected,'Imported source occupied cells or color mapping changed')
    require(asset['dimensions']==original_asset['dimensions'] and
            asset['normalization_offset']==original_asset['normalization_offset'], 'Imported source bounds/origin changed')
    return {'path':provenance['path'],'source_asset':provenance['source_asset'],'sha256':sha(path),
            'exact_occupied_geometry_preserved_up_to_documented_grid_rotation':True,
            'documented_rotation_degrees':180 if rotated else 0,'documented_palette_edits_cells':recolored,
            'source_rgba_preserved_outside_documented_palette_edits':True,'voxel_pitch_meters':pitch}


def check_sources(name):
    folder=PACK/name
    scene=load_json(folder/'scene.json'); flat_scene=load_json(folder/'flat_scene.json')
    flat=load_json(folder/(name+'.json')); manifest=load_json(folder/'source_manifest.json')
    require(scene.get('schema')=='greenbox-lore-scene-v1', 'Unexpected modular scene schema')
    require(scene['voxel_pitch']==flat_scene['voxel_pitch']==.05, 'Lore scene voxel pitch changed')
    for palette in (scene['palette'], flat_scene['palette'], flat['palette']): palette_check(palette)
    require(flat['name']==manifest['name']==name, 'Scene name differs')
    require(flat['metadata']['voxel_pitch_meters']==.05, 'Flattened source pitch changed')
    require(set(scene['emissive_indices'])=={15,16,32,33,51} and
            scene['emissive_indices']==flat_scene['emissive_indices'], 'Emissive palette mapping changed')
    models={}; model_reports=[]; imports=[]
    for asset in scene['assets']:
        require(asset['name'] not in models, 'Duplicate modular source name')
        cells=source_cells(asset); models[asset['name']]=cells
        vox=read_vox(folder/'assets'/(asset['name']+'.vox'))
        require(vox['cells']==cells and vox['dimensions']==asset['dimensions'] and vox['palette']==scene['palette'],
                'Modular editable VOX differs from source JSON')
        reused=check_import(asset,scene['palette'])
        if reused: imports.append(reused)
        sizes=components(cells)
        model_reports.append({'name':asset['name'],'filled_voxels':len(cells),'dimensions':asset['dimensions'],
                              'connected_components':len(sizes),'component_sizes':sizes,
                              'vox_sha256':sha(folder/'assets'/(asset['name']+'.vox'))})
    require(bool(models), 'Empty modular scene')
    union={}; overlaps=0; changed_color_overlaps=0; instance_names=set()
    for instance in scene['instances']:
        require(instance['name'] not in instance_names and instance['asset'] in models, 'Invalid/duplicate scene instance')
        instance_names.add(instance['name'])
        offset=instance['offset']
        require(len(offset)==3 and all(type(v) is int for v in offset), 'Instance placement is not on the voxel grid')
        require(instance.get('hidden',False) is False, 'Hidden modular models cannot be silently flattened')
        for p,c in models[instance['asset']].items():
            point=tuple(p[i]+offset[i] for i in range(3))
            if point in union:
                overlaps+=1; changed_color_overlaps+=int(union[point]!=c)
            union[point]=c
    require(bool(union), 'Empty instantiated scene')
    mins=[min(p[i] for p in union) for i in range(3)]
    dims=[max(p[i] for p in union)-mins[i]+1 for i in range(3)]
    require(flat['normalization_offset']==mins and flat['dimensions']==dims, 'Flattened bounds/origin differ from modular placements')
    normalized={tuple(p[i]-mins[i] for i in range(3)):c for p,c in union.items()}
    require(source_cells(flat)==normalized, 'Flattened last-write-wins union differs from modular scene cells')
    vox=read_vox(folder/(name+'.vox'))
    require(vox['cells']==normalized and vox['dimensions']==dims and vox['palette']==scene['palette'],
            'Flattened editable VOX differs from true source occupancy/colors')
    sizes=components(union)
    require(flat['metadata']['connected_components']==manifest['connected_components']==len(sizes),
            'Deliberate disconnected component count is stale')
    require(flat['metadata']['intentional_union_overlap_cells']==manifest['intentional_union_overlap_cells']==overlaps,
            'Deliberate union overlap count is stale')
    require(manifest['occupied_voxels']==len(union) and manifest['dimensions']==dims and
            manifest['palette_sha256']==PALETTE_HASH and manifest['voxel_pitch_meters']==.05, 'Source manifest totals/palette/scale differ')
    require(manifest['instances']==scene['instances'], 'Manifest instance placements differ')
    require(manifest['assets']==[{'name':a['name'],'voxels':len(a['voxels']),'dimensions':a['dimensions']} for a in scene['assets']],
            'Manifest modular asset dimensions/counts differ')
    require(manifest['provenance']==flat['metadata']['provenance'] and
            manifest['provenance']==[a['metadata']['import_source'] for a in scene['assets'] if a.get('metadata',{}).get('import_source')],
            'Scene imported source provenance differs')
    for filename in (name+'.json',name+'.vox','scene.json','flat_scene.json'):
        require(manifest['sha256'].get(filename)==sha(folder/filename), 'Source manifest hash is stale: '+filename)
    require(flat_scene['assets']==[flat] and flat_scene['instances']==[
        {'name':name,'asset':name,'offset':mins,'layer':0,'hidden':False}], 'Renderer flattened source/placement differs')
    require({k:v for k,v in flat_scene.items() if k not in ('assets','instances')}==
            {k:v for k,v in scene.items() if k not in ('assets','instances')}, 'Flat scene changed modular scene palette/environment settings')
    summary={'asset':name,'status':'sources-pass','filled_voxels':len(union),'dimensions_voxels':dims,
             'normalization_offset':mins,'voxel_pitch_meters':.05,'height_meters':dims[2]*.05,
             'canonical_palette_sha256':PALETTE_HASH,'colors_used':sorted(set(union.values())),
             'connected_components':len(sizes),'component_sizes':sizes,'intentional_union_overlap_cells':overlaps,
             'union_overlaps_changing_color':changed_color_overlaps,'last_write_wins_union_verified_exactly':True,
             'modular_assets':model_reports,'modular_instance_count':len(scene['instances']),'reused_sources':imports,
             'source_json_sha256':sha(folder/(name+'.json')),'flat_scene_sha256':sha(folder/'flat_scene.json'),
             'vox_sha256':sha(folder/(name+'.vox')),'source_manifest_sha256':sha(folder/'source_manifest.json')}
    return flat,flat_scene,union,summary


IDENTITY=[[float(i==j) for j in range(4)] for i in range(4)]
def multiply(a,b): return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def transform(m,p): return tuple(sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3))
def node_matrix(node):
    if 'matrix' in node:
        require(len(node['matrix'])==16, 'Invalid node matrix')
        return [[node['matrix'][j*4+i] for j in range(4)] for i in range(4)]
    x,y,z,w=node.get('rotation',[0,0,0,1]); sx,sy,sz=node.get('scale',[1,1,1]); tx,ty,tz=node.get('translation',[0,0,0])
    require(abs(x*x+y*y+z*z+w*w-1)<1e-5,'Invalid node rotation quaternion')
    return [[(1-2*(y*y+z*z))*sx,2*(x*y-z*w)*sy,2*(x*z+y*w)*sz,tx],
            [2*(x*y+z*w)*sx,(1-2*(x*x+z*z))*sy,2*(y*z-x*w)*sz,ty],
            [2*(x*z-y*w)*sx,2*(y*z+x*w)*sy,(1-2*(x*x+y*y))*sz,tz],[0,0,0,1]]


def find_output(folder,*names):
    return next((folder/n for n in names if (folder/n).is_file()), folder/names[0])


def check_export(name,flat,scene,cells,summary):
    folder=PACK/name
    glb_path=find_output(folder,name+'.glb','bedroom.glb')
    palette_path=find_output(folder,'palette.png','bedroom_palette.png')
    blend_path=find_output(folder,name+'.blend','bedroom.blend')
    render_report_path=find_output(folder,'mesh_validation.json','bedroom_mesh_report.json')
    document,binary=read_glb(glb_path)
    require(not document.get('cameras') and not document.get('skins') and not document.get('animations') and
            not document.get('extensions',{}).get('KHR_lights_punctual'),'Preview camera/lights or character rig leaked into flat scene GLB')
    require(len(document['meshes'])==1 and len(document['materials'])==2 and len(document['images'])==1,
            'Lore export must have one flattened mesh, two surface materials and one shared atlas')
    png=read_png(palette_path,pixels=True)
    require((png['width'],png['height'],png['channels'])==(16,16,4),'Unexpected palette atlas layout')
    require(png['pixels']==bytes(v for c in flat['palette'][1:]+flat['palette'][:1] for v in c), 'Palette atlas RGBA differs from canonical source')
    image=document['images'][0]; require('uri' not in image and image['mimeType']=='image/png','Palette is external or not PNG')
    view=document['bufferViews'][image['bufferView']]; start=view.get('byteOffset',0)
    require(binary[start:start+view['byteLength']]==palette_path.read_bytes(),'Embedded palette PNG differs from actual source atlas')
    material_emission=[]
    for material in document['materials']:
        pbr=material['pbrMetallicRoughness']; texture_info=pbr['baseColorTexture']
        require(near(pbr.get('baseColorFactor',[1,1,1,1]),[1,1,1,1]) and texture_info.get('texCoord',0)==0,'Palette multiplied or wrong UV set')
        texture=document['textures'][texture_info['index']]
        require(texture['source']==0,'Different source texture')
        sampler=document['samplers'][texture['sampler']]
        require(sampler.get('magFilter')==9728 and sampler.get('minFilter') in (9728,9984),'Palette not nearest sampled')
        emissive='emissiveTexture' in material; material_emission.append(emissive)
        if emissive:
            emission=document['textures'][material['emissiveTexture']['index']]
            require(emission['source']==texture['source'] and emission['sampler']==texture['sampler'],'Emission atlas differs from base color')
    require(sorted(material_emission)==[False,True],'Missing ordinary/emissive material split')
    mesh_world=[]; visited=set()
    def visit(index,parent):
        require(index not in visited and 0<=index<len(document['nodes']),'Invalid/repeated scene node')
        visited.add(index); node=document['nodes'][index]; world=multiply(parent,node_matrix(node))
        if 'mesh' in node: mesh_world.append((node,world))
        for child in node.get('children',[]): visit(child,world)
    for index in document['scenes'][document.get('scene',0)]['nodes']: visit(index,IDENTITY)
    require(len(visited)==len(document['nodes']) and len(mesh_world)==1 and mesh_world[0][0]['mesh']==0,
            'Unexpected disconnected/duplicated scene nodes or mesh instances')
    node,world=mesh_world[0]
    require(node.get('name')==name,'Flat lore mesh scene name changed')
    require(all(near(world[i][:3],IDENTITY[i][:3],1e-6) for i in range(3)), 'Unexpected flat scene rotation/scale')
    expected=expected_faces(cells); coverage=defaultdict(float); triangles=0; vertices=0; positions=[]
    emissive_indices=set(scene['emissive_indices']); emissive_triangles=0
    for primitive in document['meshes'][0]['primitives']:
        require(primitive.get('mode',4)==4 and primitive['material'] in (0,1), 'Invalid triangle material/mode')
        attributes=primitive['attributes']
        require('NORMAL' in attributes and 'TEXCOORD_0' in attributes and 'COLOR_0' not in attributes,'Missing flat normals/UVs or redundant color multiplier')
        points=accessor(document,binary,attributes['POSITION']); normals=accessor(document,binary,attributes['NORMAL']); uv=accessor(document,binary,attributes['TEXCOORD_0'])
        require(len(points)==len(normals)==len(uv),'Vertex attribute counts differ')
        indices=[v[0] for v in accessor(document,binary,primitive['indices'])]
        require(len(indices)%3==0 and all(0<=i<len(points) for i in indices),'Invalid triangle indices')
        native=[]
        for point in points:
            p=transform(world,point); positions.append(p); raw=(p[0]/.05,-p[2]/.05,p[1]/.05)
            require(all(math.isfinite(v) and abs(v-round(v))<EPSILON for v in raw),'Mesh vertex leaves actual source cube grid')
            native.append(tuple(round(v) for v in raw))
        for normal in normals:
            require(sum(abs(v)>1e-6 for v in normal)==1 and abs(sum(v*v for v in normal)-1)<1e-6,'Smoothed/nonaxis-aligned mesh normal')
        for start in range(0,len(indices),3):
            ids=indices[start:start+3]; points3=[native[i] for i in ids]; n=normals[ids[0]]
            require(all(near(normals[i],n,1e-6) for i in ids),'Interpolated triangle normals')
            native_n=(n[0],-n[2],n[1]); axis=max(range(3),key=lambda i:abs(native_n[i])); sign=1 if native_n[axis]>0 else -1; plane=points3[0][axis]
            require(all(p[axis]==plane for p in points3),'Triangle leaves a cubic face plane')
            a,b=([points3[k][i]-points3[0][i] for i in range(3)] for k in (1,2))
            cross=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
            require(cross[axis]*sign>0 and all(cross[i]==0 for i in range(3) if i!=axis),'Inward/degenerate triangle winding')
            tex=uv[ids[0]]; require(all(near(uv[i],tex,1e-7) for i in ids),'Palette UV has face gradient')
            tx,ty=math.floor(tex[0]*16),math.floor(tex[1]*16)
            require(0<=tx<16 and 0<=ty<16 and near(tex,((tx+.5)/16,(ty+.5)/16),1e-7),'UV not on palette texel center')
            color=tx+ty*16+1; require(color<=255,'Triangle samples air')
            emission=material_emission[primitive['material']]
            require(emission==(color in emissive_indices),'Emissive/ordinary material differs from source color role')
            triangles+=1; emissive_triangles+=int(emission)
            other=[i for i in range(3) if i!=axis]; points2=[(p[other[0]],p[other[1]]) for p in points3]
            for u in range(min(p[0] for p in points2),max(p[0] for p in points2)):
                for v in range(min(p[1] for p in points2),max(p[1] for p in points2)):
                    area=area_in_cell(points2,u,v)
                    if area<1e-10: continue
                    key=(axis,sign,plane,u,v,color)
                    require(key in expected,'Triangle covers air, hidden cube surface, or wrong source palette index')
                    coverage[key]+=area
        vertices+=len(points)
    require(coverage.keys()==expected.keys() and all(abs(a-1)<1e-6 for a in coverage.values()),'Mesh does not cover every exposed source cube face exactly once')
    actual_bounds=[[min(p[i] for p in positions) for i in range(3)],[max(p[i] for p in positions) for i in range(3)]]
    mins=[min(p[i] for p in cells)*.05 for i in range(3)]; maxs=[(max(p[i] for p in cells)+1)*.05 for i in range(3)]
    expected_bounds=[[mins[0],mins[2],-maxs[1]],[maxs[0],maxs[2],-mins[1]]]
    require(all(near(a,b,2e-6) for a,b in zip(actual_bounds,expected_bounds)),'GLB world bounds differ from flattened source cells')
    render_report=load_json(render_report_path)
    if render_report.get('schema')=='greenbox-lore-mesh-v1':
        require(render_report['source_sha256']==summary['flat_scene_sha256'] and render_report['source_vox_sha256']==summary['vox_sha256']
                and render_report['voxel_pitch_meters']==.05,'Lore renderer report refers to stale/different source')
        require(sum(a['triangles'] for a in render_report['assets'])==render_report['glb']['triangles_unique_mesh_data']==triangles
                and sum(a['filled_voxels'] for a in render_report['assets'])==len(cells)
                and sum(a['exposed_unit_faces'] for a in render_report['assets'])==len(expected),'Lore renderer report counts disagree with independently parsed files')
        require(render_report['palette_png_sha256']==sha(palette_path),'Lore renderer atlas hash changed')
        preview_paths={mode:folder/(name+'_'+mode+'.png') for mode in ('day','night')}
        resolution=[1440,1000]
    else:
        require(render_report['scene_sha256']==summary['flat_scene_sha256'] and render_report['voxel_pitch_meters']==.05,'Renderer report refers to stale/different source')
        require(render_report['total_asset_triangles']==triangles and render_report['total_instanced_voxels']==len(cells)
                and render_report['total_asset_exposed_unit_faces']==len(expected),'Renderer report counts disagree with independently parsed files')
        preview_paths={'studio':find_output(folder,name+'_preview.png','bedroom_preview.png')}
        resolution=render_report['preview_camera']['resolution']
    previews={}
    for mode,path in preview_paths.items():
        preview=read_png(path)
        require(preview['at_least_distinct_pixel_values']>=64 and [preview['width'],preview['height']]==resolution,
                'Blank preview or changed render dimensions: '+mode)
        previews[mode]={k:preview[k] for k in ('width','height','bytes','sha256')}
    blend=blend_path.read_bytes()
    require(len(blend)>1000 and blend.startswith((b'BLENDER',b'\x28\xb5\x2f\xfd',b'\x1f\x8b')),'Invalid saved Blender file header')
    summary.update({'status':'pass','glb':{'path':str(glb_path.relative_to(ROOT)),'sha256':sha(glb_path),'bytes':glb_path.stat().st_size,
        'triangles':triangles,'vertices':vertices,'exposed_unit_faces_verified':len(expected),'emissive_triangles':emissive_triangles,
        'materials':2,'world_bounds_y_up_meters':actual_bounds,'exact_flat_source_surface_and_palette_coverage':True,
        'all_vertices_on_source_cube_grid':True,'flat_outward_axis_normals':True,'source_emissive_role_mapping_preserved':True},
        'previews':previews,'blend':{'sha256':sha(blend_path),'bytes':len(blend),
        'verification_scope':'Nonempty saved Blender file with recognized container magic; internal scene blocks not decoded.'}})
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-only',action='store_true'); parser.add_argument('--scene',choices=NAMES)
    args=parser.parse_args(); summaries=[]
    for name in (args.scene,) if args.scene else NAMES:
        try:
            flat,scene,cells,summary=check_sources(name)
            if not args.sources_only: summary=check_export(name,flat,scene,cells,summary)
            summaries.append(summary)
            print(json.dumps({'asset':name,'status':summary['status'],'voxels':summary['filled_voxels'],
                              'components':summary['connected_components'],'triangles':summary.get('glb',{}).get('triangles')}),flush=True)
        except Exception as error:
            print(json.dumps({'asset':name,'status':'fail','error':str(error)}),flush=True); raise
    if not args.sources_only and not args.scene:
        report={'schema':'independent-greenbox-lore-pack-validation-v1','status':'pass',
                'verification':'Independent modular placement union, editable VOX bytes, provenance and exact actual GLB triangle clipping against every exposed flattened source cube face.',
                'canonical_palette_sha256':PALETTE_HASH,'voxel_pitch_meters':.05,'assets_verified':len(summaries),
                'total_filled_voxels':sum(s['filled_voxels'] for s in summaries),'total_triangles':sum(s['glb']['triangles'] for s in summaries),'assets':summaries}
        (PACK/'pack_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('PACK_VALIDATION '+json.dumps({k:report[k] for k in ('status','assets_verified','total_filled_voxels','total_triangles')}),flush=True)


if __name__=='__main__': main()
