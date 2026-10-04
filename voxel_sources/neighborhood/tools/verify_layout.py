"""Independent coordinate/collision/reachability QA; no builder or renderer imports."""
from pathlib import Path
from collections import deque
import hashlib, json, math
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'neighbor_commons'

def require(test,message):
    if not test: raise AssertionError(message)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def world_bounds(rect):
    x0,y0,x1,y1=rect
    return [(x0-120)*.05,(x1-120)*.05,-(y1-100)*.05,-(y0-100)*.05]
def main():
    layout=json.loads((FOLDER/'game_layout.json').read_text())
    require((ROOT/'game_layout.json').read_bytes()==(FOLDER/'game_layout.json').read_bytes(),'Root integration layout differs from native map layout')
    scene=json.loads((FOLDER/'scene.json').read_text())
    require(layout['schema']=='greenbox-neighborhood-layout-v1','Wrong game layout schema')
    require(layout['floorY']==.2 and layout['sourceRootPivotNative']==[120,100,0] and layout['voxelPitchMeters']==.05,'Changed floor/root/scale')
    require(layout['bounds']=={'minX':-6,'maxX':6,'minZ':-5,'maxZ':5},'Changed map bounds')
    require(layout['sourceVoxSha256']==sha(FOLDER/'neighbor_commons.vox') and layout['sourceSceneSha256']==sha(FOLDER/'scene.json'),'Stale layout source hashes')
    require(layout['environmentIncludesStaticCharacters'] is False,'Environment embeds runtime characters')
    sources={a['name']:a for a in scene['assets']}
    ground=sources['commons_layered_ground']
    tops={}
    for x,y,z,c in ground['voxels']: tops[x,y]=max(tops.get((x,y),0),z+1)
    require(len(tops)==240*200 and set(tops.values())=={4},'Ground is missing cells or differs from level floor')
    association={'chef_home':'commons_chef_home','artist_home':'commons_artist_home','robot_lab':'commons_robot_lab','party_home':'commons_party_home','night_market':'commons_night_market_stall','courtyard_bench':'commons_oak_bench','tree_left_trunk':'commons_lime_tree_left','tree_right_trunk':'commons_lime_tree_right','lamp_left':'courtyard_lamp_left','lamp_right':'courtyard_lamp_right','pot_market':'market_leaf_pot','pot_court':'courtyard_leaf_pot'}
    instances={i['name']:i for i in scene['instances']}
    blockers=[]
    for b in layout['blockers']:
        instance=instances[association[b['id']]]; asset=sources[instance['asset']]; off=instance['offset']
        # All source solids intersecting even the tallest current Garden character.
        cells=[(x+off[0],y+off[1],z+off[2]) for x,y,z,c in asset['voxels'] if 4<=z+off[2]<37]
        require(bool(cells),'Empty character-height blocker source')
        rect=[min(p[0] for p in cells),min(p[1] for p in cells),max(p[0] for p in cells)+1,max(p[1] for p in cells)+1]
        require(rect==b['nativeBounds'],'Collider differs from actual source slab: '+b['id'])
        actual=[b[k] for k in ('minX','maxX','minZ','maxZ')]
        require(all(abs(a-c)<1e-7 for a,c in zip(actual,world_bounds(rect))),'Collider has wrong centered/exported axes: '+b['id'])
        blockers.append({'id':b['id'],'nativeBounds':rect,'worldBounds':actual,'sourceInstance':instance['name']})
    radius=layout['player']['radius']; area=layout['walkArea']
    def open_point(x,z):
        if not (area['minX']+radius<=x<=area['maxX']-radius and area['minZ']+radius<=z<=area['maxZ']-radius): return False
        return not any(b['minX']-radius<x<b['maxX']+radius and b['minZ']-radius<z<b['maxZ']+radius for b in layout['blockers'])
    def grid(p): return (round(p[0]/.05),round(p[2]/.05))
    origin=grid(layout['player']['spawn']); require(open_point(origin[0]*.05,origin[1]*.05),'Blocked player spawn')
    visited={origin}; q=deque([origin])
    while q:
        x,z=q.popleft()
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
            p=x+dx,z+dz
            if p not in visited and open_point(p[0]*.05,p[1]*.05): visited.add(p); q.append(p)
    targets=[]
    for t in [*layout['neighbors'],layout['market']]:
        p=t['position']; require(p[1]==.2,'Interaction feet are not on level floor')
        require(grid(p) in visited,'Player cannot reach interaction target: '+t['id'])
        targets.append({'id':t['id'],'position':p,'reachableFromSpawnWithPlayerRadius':True})
    require(len({t['characterId'] for t in layout['neighbors']})==4,'Neighbors require four unique Garden characters')
    require(all(len(t['dialogue'])>=2 and 0<t['interactionRadius']<=1.8 for t in layout['neighbors']),'Missing talk contract')
    report={'schema':'independent-greenbox-neighborhood-layout-validation-v1','status':'pass','layoutSha256':sha(FOLDER/'game_layout.json'),'sourceVoxSha256':layout['sourceVoxSha256'],'sourceSceneSha256':layout['sourceSceneSha256'],'floorY':.2,'worldBounds':layout['bounds'],'collisionSourceSlabNativeZ':[4,37],'collisionCharacterHeightMeters':1.65,'sourceRootPivotNative':[120,100,0],'blockers':blockers,'reachableTargets':targets,'reachableGridPoints':len(visited),'playerRadiusMeters':radius,'reachabilityScope':'50 mm grid flood fill with player radius around source-derived axis-aligned blockers. Runtime movement and interactions tested by game integration separately.'}
    (ROOT/'layout_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':'pass','blockers':len(blockers),'reachableTargets':len(targets),'reachableGridPoints':len(visited)}))
if __name__=='__main__': main()
