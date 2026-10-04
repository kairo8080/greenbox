"""Independent source and actual GLB face verification; no authoring imports."""
from collections import defaultdict
from pathlib import Path
import hashlib, importlib.util, json, math
ROOT=Path(__file__).resolve().parents[1]
NAMES=('grower_toybox','mystery_standard','mystery_420_founder','booster_common','booster_rare','booster_epic','card_common','card_rare','card_epic')
PALETTE_HASH='09cb38d6cb39613d53228591ed2d7cdefc47a98cbdb81f78ab19b65dd3c36293'
spec=importlib.util.spec_from_file_location('independent_binary_qa',Path(__file__).resolve().parent/'verify_cast.py')
qa=importlib.util.module_from_spec(spec); spec.loader.exec_module(qa)
require=qa.require; sha=qa.sha; load_json=qa.load_json; source_cells=qa.source_cells
read_vox=qa.read_vox; read_png=qa.read_png; read_glb=qa.read_glb; accessor=qa.accessor
expected_faces=qa.expected_faces; area_in_cell=qa.area_in_cell; components=qa.components; near=qa.near

def verify(name):
 folder=ROOT/name; data=load_json(folder/(name+'.json')); manifest=load_json(folder/'source_manifest.json')
 require(data['schema']=='greenbox-voxel-collectible-v1' and data['name']==name,'Wrong collectible source schema/id')
 palette=data['palette']; require(len(palette)==256 and all(len(c)==4 and all(type(v)is int and 0<=v<=255 for v in c) for c in palette),'Invalid palette')
 require(hashlib.sha256(bytes(v for c in palette for v in c)).hexdigest()==PALETTE_HASH,'Canonical full indexed palette differs')
 require(data['metadata']['voxel_pitch_meters']==manifest['voxel_pitch_meters']==.05,'Source pitch changed')
 cells=source_cells(data); dims=data['dimensions']; vox=read_vox(folder/(name+'.vox'))
 require(vox['cells']==cells and vox['palette']==palette and vox['dimensions']==dims,'Actual editable VOX differs from JSON')
 require([max(p[i] for p in cells)+1 for i in range(3)]==dims and [min(p[i] for p in cells) for i in range(3)]==[0,0,0],'Source occupied bounds are not tight')
 require(manifest['occupied_voxels']==len(cells) and manifest['dimensions_voxels']==dims,'Source counts/bounds differ')
 require(manifest['canonical_palette_sha256']==PALETTE_HASH,'Manifest palette changed')
 for filename,expected_hash in manifest['sha256'].items(): require(sha(folder/filename)==expected_hash,'Stale manifest hash: '+filename)
 sizes=components(cells); require(sizes==[len(cells)] and data['metadata']['connected_components']==1,'Collectible disconnected')
 if name=='grower_toybox':
  provenance=data['metadata']['reused_character']; source=ROOT/provenance['path']; original=load_json(source)
  require(sha(source)==provenance['sha256'] and original['palette']==palette,'Reused grower input changed')
  offset=provenance['offset_voxels']; origin=data['normalization_offset']
  reused={tuple(p[i]+offset[i]-origin[i] for i in range(3)):c for p,c in source_cells(original).items()}
  require(all(cells.get(p)==c for p,c in reused.items()) and len(reused)==7318,'Original grower geometry/colors were altered')
  require(all((x,1,z) not in cells for x in range(3,29) for z in range(6,39)),'Toybox front window is filled')
 doc,binary=read_glb(folder/(name+'.glb'))
 require(not doc.get('cameras') and not doc.get('skins') and not doc.get('animations') and not doc.get('extensions',{}).get('KHR_lights_punctual'),'Preview objects/rig leaked into static GLB')
 require(len(doc['meshes'])==len(doc['nodes'])==len(doc['materials'])==len(doc['images'])==1,'Unexpected static prop GLB structure')
 node=doc['nodes'][0]; require(node.get('name')==name and node.get('mesh')==0 and 'children' not in node,'Wrong prop node')
 require(near(node.get('translation',[0,0,0]),[0,0,0]) and near(node.get('rotation',[0,0,0,1]),[0,0,0,1]) and near(node.get('scale',[1,1,1]),[1,1,1]),'Prop pivot transform changed')
 require(doc['scenes'][doc.get('scene',0)]['nodes']==[0],'Wrong default scene')
 png=read_png(folder/'palette.png',pixels=True)
 require((png['width'],png['height'],png['channels'])==(16,16,4),'Wrong palette atlas dimensions')
 require(png['pixels']==bytes(v for c in palette[1:]+palette[:1] for v in c),'Full palette atlas differs')
 image=doc['images'][0]; require(image.get('mimeType')=='image/png' and 'uri' not in image,'GLB texture external or wrong format')
 view=doc['bufferViews'][image['bufferView']]; start=view.get('byteOffset',0)
 require(binary[start:start+view['byteLength']]==(folder/'palette.png').read_bytes(),'Embedded atlas changed')
 material=doc['materials'][0]; pbr=material['pbrMetallicRoughness']; texture=doc['textures'][pbr['baseColorTexture']['index']]
 require(near(pbr.get('baseColorFactor',[1,1,1,1]),[1,1,1,1]) and not material.get('emissiveTexture') and material.get('alphaMode','OPAQUE')=='OPAQUE','Palette multiplied or surface changed')
 sampler=doc['samplers'][texture['sampler']]; require(texture['source']==0 and sampler.get('magFilter')==9728 and sampler.get('minFilter') in (9728,9984),'Palette not nearest sampled')
 pivot=[dims[0]/2,dims[1]/2,0]; require(near(data['metadata']['source_ground_pivot_voxels'],pivot),'Ground pivot changed')
 expected=expected_faces(cells); coverage=defaultdict(float); triangles=0; vertices=0; positions=[]
 for primitive in doc['meshes'][0]['primitives']:
  require(primitive.get('mode',4)==4 and primitive['material']==0,'Invalid triangle primitive')
  attr=primitive['attributes']; require('NORMAL' in attr and 'TEXCOORD_0' in attr and 'COLOR_0' not in attr,'Missing flat normals/UV or redundant colors')
  points=accessor(doc,binary,attr['POSITION']); normals=accessor(doc,binary,attr['NORMAL']); uv=accessor(doc,binary,attr['TEXCOORD_0'])
  require(len(points)==len(normals)==len(uv),'Different attribute lengths')
  indices=[v[0] for v in accessor(doc,binary,primitive['indices'])]
  require(len(indices)%3==0 and all(0<=i<len(points) for i in indices),'Invalid triangle index')
  native=[]
  for p in points:
   positions.append(p); raw=(p[0]/.05+pivot[0],-p[2]/.05+pivot[1],p[1]/.05)
   require(all(math.isfinite(v) and abs(v-round(v))<5e-5 for v in raw),'Vertex leaves actual occupied cube grid')
   native.append(tuple(round(v) for v in raw))
  for n in normals: require(sum(abs(v)>1e-6 for v in n)==1 and abs(sum(v*v for v in n)-1)<1e-6,'Smoothed or nonaxis-aligned normal')
  for start in range(0,len(indices),3):
   ids=indices[start:start+3]; points3=[native[i] for i in ids]; n=normals[ids[0]]
   require(all(near(normals[i],n,1e-6) for i in ids),'Interpolated normals')
   native_n=(n[0],-n[2],n[1]); axis=max(range(3),key=lambda i:abs(native_n[i])); sign=1 if native_n[axis]>0 else -1; plane=points3[0][axis]
   require(all(p[axis]==plane for p in points3),'Triangle leaves cubic face plane')
   a,b=([points3[k][i]-points3[0][i] for i in range(3)] for k in (1,2))
   cross=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
   require(cross[axis]*sign>0 and all(cross[i]==0 for i in range(3) if i!=axis),'Inward or degenerate triangle')
   tex=uv[ids[0]]; require(all(near(uv[i],tex,1e-7) for i in ids),'Palette UV gradient')
   tx,ty=math.floor(tex[0]*16),math.floor(tex[1]*16)
   require(0<=tx<16 and 0<=ty<16 and near(tex,((tx+.5)/16,(ty+.5)/16),1e-7),'UV not exact texel center')
   color=tx+ty*16+1; require(color<=255,'Triangle samples air')
   triangles+=1; other=[i for i in range(3) if i!=axis]; points2=[(p[other[0]],p[other[1]]) for p in points3]
   for u in range(min(p[0] for p in points2),max(p[0] for p in points2)):
    for v in range(min(p[1] for p in points2),max(p[1] for p in points2)):
     area=area_in_cell(points2,u,v)
     if area<1e-10: continue
     key=(axis,sign,plane,u,v,color); require(key in expected,'Triangle covers air, hidden face or wrong palette color'); coverage[key]+=area
  vertices+=len(points)
 require(coverage.keys()==expected.keys() and all(abs(a-1)<1e-6 for a in coverage.values()),'Mesh fails exact exposed cube face coverage')
 actual_bounds=[[min(p[i] for p in positions) for i in range(3)],[max(p[i] for p in positions) for i in range(3)]]
 expected_bounds=[[-dims[0]*.025,0,-dims[1]*.025],[dims[0]*.025,dims[2]*.05,dims[1]*.025]]
 require(all(near(a,b,2e-6) for a,b in zip(actual_bounds,expected_bounds)),'GLB centered-ground bounds differ')
 report=load_json(folder/'mesh_validation.json')
 require(report['source_sha256']==sha(folder/(name+'.json')) and report['source_vox_sha256']==sha(folder/(name+'.vox')),'Stale export source hash')
 require(report['mesh']['triangles']==report['glb']['triangles_unique_mesh_data']==triangles and report['mesh']['filled_voxels']==len(cells) and report['mesh']['exposed_unit_faces']==len(expected),'Export report count differs from actual parsed geometry')
 require(report['glb']['sha256']==sha(folder/(name+'.glb')) and report['palette_png_sha256']==sha(folder/'palette.png'),'Stale export hashes')
 preview=read_png(folder/'rendered.png'); require([preview['width'],preview['height']]==[640,800] and preview['at_least_distinct_pixel_values']>=64,'Blank or wrong actual preview')
 theme=load_json(ROOT/'preview_theme.json'); themed=read_png(folder/'preview_palette.png',pixels=True)
 require(themed['pixels']==bytes(v for c in theme['colors'][1:]+theme['colors'][:1] for v in c),'Preview atlas does not match Garden theme')
 blend=(folder/(name+'.blend')).read_bytes(); require(len(blend)>1000 and blend.startswith((b'BLENDER',b'\x28\xb5\x2f\xfd',b'\x1f\x8b')),'Invalid Blender file container')
 return {'asset':name,'id':name,'status':'pass','filled_voxels':len(cells),'dimensions_voxels':dims,'voxel_pitch_meters':.05,
  'connected_components':1,'canonical_palette_sha256':PALETTE_HASH,'vox_sha256':sha(folder/(name+'.vox')),'source_json_sha256':sha(folder/(name+'.json')),
  'glb':{'sha256':sha(folder/(name+'.glb')),'triangles':triangles,'vertices':vertices,'bytes':(folder/(name+'.glb')).stat().st_size,
   'world_bounds_y_up_meters':actual_bounds,'exact_source_surface_and_palette_coverage':True,'exposed_unit_faces_verified':len(expected),
   'all_vertices_on_source_cube_grid':True,'flat_outward_normals':True,'pivot':'centered ground','materials':1},
  'preview':{k:preview[k] for k in ('width','height','bytes','sha256')},'blend':{'sha256':sha(folder/(name+'.blend')),'bytes':len(blend)}}

def main():
 summaries=[]
 for name in NAMES:
  result=verify(name); summaries.append(result)
  print(json.dumps({'asset':name,'status':'pass','filled_voxels':result['filled_voxels'],'triangles':result['glb']['triangles']}),flush=True)
 catalog=load_json(ROOT/'assets.json'); require([a['id'] for a in catalog['assets']]==list(NAMES),'Catalog ID order/count changed')
 for item,result in zip(catalog['assets'],summaries):
  require(item['filled_voxels']==result['filled_voxels'] and item['triangles']==result['glb']['triangles'] and item['vox_sha256']==result['vox_sha256'] and item['glb_sha256']==result['glb']['sha256'],'Catalog stale source/GLB counts/hashes')
 report={'schema':'independent-greenbox-collectibles-validation-v1','status':'pass','assets_verified':len(summaries),
  'verification':'Independent binary VOX and GLB parsing; actual triangle clipping against every exposed source cube face; all 256 canonical palette texels; exact reused grower; real open window; centered ground bounds; actual rendered previews.',
  'canonical_palette_sha256':PALETTE_HASH,'voxel_pitch_meters':.05,'total_filled_voxels':sum(r['filled_voxels'] for r in summaries),
  'total_triangles':sum(r['glb']['triangles'] for r in summaries),'assets':summaries}
 (ROOT/'pack_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print('PACK_VALIDATION '+json.dumps({k:report[k] for k in ('status','assets_verified','total_filled_voxels','total_triangles')}),flush=True)

if __name__=='__main__': main()
