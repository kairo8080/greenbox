"""Shared cubic grid and collection palette for the bedroom kit."""
import json, math, struct
from pathlib import Path

RGB = {
 'ink':(29,37,42), 'slate':(52,66,70), 'wall':(180,197,181),
 'wall_shadow':(150,174,158), 'trim':(229,224,200),
 'floor':(159,114,75), 'floor_dark':(133,91,63), 'floor_light':(184,136,91),
 'wood':(109,70,51), 'wood_light':(167,104,65), 'linen':(237,226,200),
 'teal':(49,117,122), 'teal_light':(76,158,157), 'pink':(221,80,157),
 'pink_light':(255,157,224), 'warm_light':(255,217,135),
 'leaf_dark':(33,78,42), 'leaf':(48,117,52), 'leaf_light':(80,153,60),
 'leaf_tip':(119,184,79), 'soil':(62,48,34), 'clay':(181,87,61),
 'clay_light':(219,126,83), 'blue':(77,162,188), 'water':(104,199,215),
 'white':(246,242,221), 'yellow':(235,180,73), 'navy':(47,75,107),
 'purple':(110,83,130), 'stem':(115,149,69), 'metal':(109,125,132),
 'screen':(114,203,189), 'violet':(132,99,223),
}
COL = {name:i+1 for i,name in enumerate(RGB)}
PALETTE = [(0,0,0,0)] + [(*rgb,255) for rgb in RGB.values()]
PALETTE += [(0,0,0,255)]*(256-len(PALETTE))

class Asset:
 def __init__(self,name): self.name=name; self.v={}; self.meta={}
 def set(self,x,y,z,color): self.v[(int(x),int(y),int(z))]=COL[color] if isinstance(color,str) else color
 def box(self,x0,y0,z0,x1,y1,z1,color):
  for x in range(x0,x1):
   for y in range(y0,y1):
    for z in range(z0,z1): self.set(x,y,z,color)
  return self
 def erase(self,x0,y0,z0,x1,y1,z1):
  for p in list(self.v):
   if x0<=p[0]<x1 and y0<=p[1]<y1 and z0<=p[2]<z1: del self.v[p]
 def line(self,a,b,color,radius=0):
  n=max(abs(b[i]-a[i]) for i in range(3))*3+1
  for k in range(int(n)+1):
   p=[round(a[i]+(b[i]-a[i])*k/n) for i in range(3)]
   for dx in range(-radius,radius+1):
    for dy in range(-radius,radius+1):
     for dz in range(-radius,radius+1): self.set(p[0]+dx,p[1]+dy,p[2]+dz,color)
  return self
 def cylinder(self,cx,cy,z0,z1,radius,color,inner=0):
  for x in range(math.floor(cx-radius),math.ceil(cx+radius)+1):
   for y in range(math.floor(cy-radius),math.ceil(cy+radius)+1):
    d=(x+.5-cx)**2+(y+.5-cy)**2
    if inner**2<=d<=radius**2:
     for z in range(z0,z1): self.set(x,y,z,color)
  return self
 def serialized(self):
  mins=[min(p[i] for p in self.v) for i in range(3)]
  dims=[max(p[i] for p in self.v)-mins[i]+1 for i in range(3)]
  cells=[[p[0]-mins[0],p[1]-mins[1],p[2]-mins[2],c] for p,c in sorted(self.v.items())]
  return {'name':self.name,'dimensions':dims,'normalization_offset':mins,'voxels':cells,'metadata':self.meta}

def save_assets(path,assets):
 Path(path).write_text(json.dumps([a.serialized() for a in assets],separators=(',',':')),encoding='utf-8')

def chunk(tag,content=b'',children=b''):
 return tag.encode()+struct.pack('<II',len(content),len(children))+content+children
def write_vox(path,asset):
 dims=asset['dimensions']; cells=asset['voxels']
 assert all(0<d<=256 for d in dims)
 data=chunk('SIZE',struct.pack('<3i',*dims))+chunk('XYZI',struct.pack('<i',len(cells))+b''.join(bytes(c) for c in cells))
 data+=chunk('RGBA',b''.join(bytes(c) for c in PALETTE[1:]+[PALETTE[0]]))
 Path(path).write_bytes(b'VOX '+struct.pack('<i',150)+chunk('MAIN',children=data))
