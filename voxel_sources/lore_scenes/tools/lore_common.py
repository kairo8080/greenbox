"""Exact Greenbox voxel palette, simple raised lettering and editable scene assembly."""
from pathlib import Path
import copy, hashlib, json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import Asset, COL, RGB, PALETTE, PITCH, components
from common import write_vox
OUT = ROOT

FONT = {
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01111'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
' ':['00000']*7,
}

def text(asset, value, x, y, z, color='white', scale=1, depth=1):
    """Raised letters in X/Z, facing native -Y; z is glyph bottom."""
    for position, char in enumerate(value.upper()):
        glyph=FONT[char]
        for row,line in enumerate(glyph):
            for column,bit in enumerate(line):
                if bit=='1':
                    px=x+(position*6+column)*scale; pz=z+(6-row)*scale
                    asset.box(px,y,pz,px+scale,y+depth,pz+scale,color)
    return asset

def leaf_motif(asset, x, y, z, color='leaf_light', scale=1, plane='xz'):
    """Original seven-lobe decorative icon; separate from reused plant sources."""
    tips=((-5,5),(-7,2),(-4,7),(0,10),(4,7),(7,2),(5,5))
    def point(a,b):
        return (x+a*scale,y,z+b*scale) if plane=='xz' else (x+a*scale,y+b*scale,z)
    for a,b in tips: asset.line(point(0,1),point(a,b),color,radius=0)
    asset.line(point(0,-2),point(0,3),color)
    return asset

class SceneBuilder:
    def __init__(self,name):
        self.name=name; self.assets=[]; self.instances=[]; self.provenance=[]
        self.directory=OUT/name
    def add(self,asset,offset=(0,0,0),name=None):
        """Asset offsets refer to raw origin; normalized dict offsets to its minimum."""
        raw=isinstance(asset,Asset)
        data=asset.serialized() if raw else copy.deepcopy(asset)
        modelname=data['name']
        if not any(item['name']==modelname for item in self.assets): self.assets.append(data)
        elif data != next(item for item in self.assets if item['name']==modelname):
            raise ValueError('Same name has different source cells: '+modelname)
        shift=data['normalization_offset'] if raw else (0,0,0)
        place=[int(offset[i]+shift[i]) for i in range(3)]
        label=name or modelname
        if any(item['name']==label for item in self.instances): raise ValueError('Instance names must be unique')
        self.instances.append({'name':label,'asset':modelname,'offset':place,'layer':0,'hidden':False})
        return data
    def import_asset(self,path,asset_name=None,alias=None):
        path=Path(path)
        logical_path=str(path.relative_to(ROOT)).replace('\\','/')
        input_path=path
        if not input_path.is_file():
            catalog=json.loads((ROOT/'inputs'/'index.json').read_text(encoding='utf-8'))
            record=catalog['sources'][logical_path]
            input_path=(ROOT/record['bundled_path']).resolve()
            input_path.relative_to(ROOT.resolve())
            if hashlib.sha256(input_path.read_bytes()).hexdigest()!=record['sha256']:
                raise ValueError('Bundled source input SHA-256 differs: '+logical_path)
        source=json.loads(input_path.read_text(encoding='utf-8'))
        data=copy.deepcopy(next(item for item in source['assets'] if item['name']==asset_name) if 'assets' in source else source)
        palette=source['palette']; used={cell[3] for cell in data['voxels']}
        mapping={index:next(i for i,color in enumerate(PALETTE) if i and list(color)==list(palette[index])) for index in used}
        data['voxels']=[[x,y,z,mapping[c]] for x,y,z,c in data['voxels']]
        if alias: data['name']=alias
        data.pop('parts',None); data.pop('palette',None)
        data.setdefault('metadata',{})['import_source']={'path':logical_path,'sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),'source_asset':asset_name or source.get('name'),'color_remap':mapping}
        self.provenance.append(data['metadata']['import_source'])
        return data
    def save(self,description,lights=None):
        self.directory.mkdir(parents=True,exist_ok=True)
        modelmap={item['name']:item for item in self.assets}; union=Asset(self.name); overlap=0
        for instance in self.instances:
            for x,y,z,color in modelmap[instance['asset']]['voxels']:
                point=tuple(instance['offset'][i]+(x,y,z)[i] for i in range(3))
                if point in union.v: overlap+=1
                union.v[point]=color
        flattened=union.serialized(); flattened['palette']=PALETTE
        flattened['metadata']={'description':description,'voxel_pitch_meters':PITCH,'source_axes':'X/Y horizontal, Z up; front -Y','intentional_union_overlap_cells':overlap,'connected_components':len(components(union.v)),'original_art':True,'provenance':self.provenance}
        flatpath=self.directory/(self.name+'.json')
        flatpath.write_text(json.dumps(flattened,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
        write_vox(self.directory/(self.name+'.vox'),flattened)
        assetdir=self.directory/'assets'; assetdir.mkdir(exist_ok=True)
        for asset in self.assets: write_vox(assetdir/(asset['name']+'.vox'),asset)
        scene={'schema':'greenbox-lore-scene-v1','voxel_pitch':PITCH,'palette':PALETTE,'assets':self.assets,'instances':self.instances,'emissive_indices':[15,16,32,33,51],'description':description,'lights':lights or []}
        (self.directory/'scene.json').write_text(json.dumps(scene,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
        flat_scene={**scene,'assets':[flattened],'instances':[{'name':self.name,'asset':self.name,'offset':flattened['normalization_offset'],'layer':0,'hidden':False}]}
        (self.directory/'flat_scene.json').write_text(json.dumps(flat_scene,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
        source_files=[self.directory/(self.name+suffix) for suffix in ('.vox','.json')]+[self.directory/name for name in ('scene.json','flat_scene.json')]
        manifest={'name':self.name,'description':description,'occupied_voxels':len(union.v),'dimensions':flattened['dimensions'],'voxel_pitch_meters':PITCH,'palette_sha256':hashlib.sha256(bytes(channel for color in PALETTE for channel in color)).hexdigest(),'intentional_union_overlap_cells':overlap,'connected_components':flattened['metadata']['connected_components'],'assets':[{'name':item['name'],'voxels':len(item['voxels']),'dimensions':item['dimensions']} for item in self.assets],'instances':self.instances,'provenance':self.provenance,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source_files)}}
        (self.directory/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'name':self.name,'dimensions':flattened['dimensions'],'voxels':len(union.v),'assets':len(self.assets),'overlap':overlap,'folder':str(self.directory)}),flush=True)
        return flattened
