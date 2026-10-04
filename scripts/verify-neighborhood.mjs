import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { createState, collisionBlockers, positionAllowed, movePlayer, nearestStation, previewTrade, completeTrade, OFFERS, withAvatarColliders, playerEnvelope } from '../neighborhood/game-core.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const html = await fs.readFile(path.join(root,'public/neighborhood/index.html'),'utf8');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const embedded = html.match(/<script id="neighborhood-data" type="application\/json">([\s\S]*?)<\/script>/);
assert(embedded,'Missing embedded model data');
const data = JSON.parse(embedded[1]);
assert.equal(data.schema,'greenbox-neighborhood-v1');
assert.equal(data.layout.schema,'greenbox-neighborhood-layout-v1');
assert.equal(data.layout.environmentIncludesStaticCharacters,false);
assert.equal(data.models.length,9);
assert.equal(data.layout.neighbors.length,4);
assert.deepEqual(data.catalog,JSON.parse(await fs.readFile(path.join(root,'viewer/palettes.json'),'utf8')));
assert.equal(data.layoutSha256,hash(await fs.readFile(path.join(root,data.layoutSource))));
assert.deepEqual(data.layout,JSON.parse(await fs.readFile(path.join(root,data.layoutSource),'utf8')));
assert(!/<(?:script|link|img)\b[^>]*(?:src|href)\s*=\s*["'](?:https?:|\/\/)/i.test(html),'Remote runtime resource');
assert(!html.includes('NEIGHBORHOOD_SCRIPT') && !html.includes('NEIGHBORHOOD_DATA') && !html.includes('NEIGHBORHOOD_STYLE'),'Unreplaced template');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert(script,'Missing runtime bundle');
new vm.Script(script,{filename:'neighborhood-bundle.js'});
assert(!/\bfetch\s*\(/.test(await fs.readFile(path.join(root,'neighborhood/neighborhood.js'),'utf8')),'Neighborhood source fetches external assets');
const summaries = [];
for (const model of data.models) {
  const bytes = Buffer.from(model.glb,'base64');
  assert.equal(bytes.length,model.bytes);
  assert.equal(bytes.readUInt32LE(0),0x46546c67); assert.equal(bytes.readUInt32LE(4),2); assert.equal(bytes.readUInt32LE(8),bytes.length);
  assert.equal(model.glbSha256,hash(bytes));
  assert.equal(model.glbSha256,hash(await fs.readFile(path.join(root,model.source))));
  assert.equal(bytes.readUInt32LE(16),0x4e4f534a);
  const document = JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString('utf8').trim());
  assert(!document.buffers.some(buffer => buffer.uri) && !document.images?.some(image => image.uri));
  const count = document.meshes.reduce((total, mesh) => total + mesh.primitives.reduce((sum, primitive) => sum+document.accessors[primitive.indices].count/3,0),0);
  assert.equal(count,model.triangles);
  if (['rasta_grower',...data.layout.neighbors.map(neighbor => neighbor.characterId)].includes(model.id)) {
    for (const part of ['head','torso','arm_left','arm_right','leg_left','leg_right']) {
      const node = document.nodes.find(entry => entry.name === part);
      assert(node?.extras?.rigid_joint && node.translation && Number.isInteger(node.mesh),`${model.id} lacks ${part} joint`);
    }
  }
  summaries.push({id:model.id,bytes:bytes.length,triangles:count,sha256:model.glbSha256});
}
assert.equal(data.physics.schema,'greenbox-actual-avatar-footprints-v1');
assert.equal(Object.keys(data.physics.models).length,5);
for (const footprint of Object.values(data.physics.models)) {
  assert(Math.abs(footprint.radius-Math.hypot(...footprint.halfExtents))<1e-12);
  assert(footprint.halfExtents[0]>.4 && footprint.halfExtents[1]>.4,'Footprint smaller than actual Garden cube heads');
}
const layout = withAvatarColliders(data.layout,data.physics), state = createState(layout);
assert(positionAllowed(state.player,playerEnvelope(layout.player,state.player.yaw),layout.bounds,collisionBlockers(layout)),'Spawn is blocked');
const emptyLayout = {...layout,player:{...layout.player,halfExtents:undefined},blockers:[],neighbors:[]};
const start = {x:0,y:layout.floorY,z:0,yaw:0};
const cardinal = movePlayer(start,{x:1,z:0},.2,emptyLayout), diagonal = movePlayer(start,{x:1,z:1},.2,emptyLayout);
assert(Math.abs(Math.hypot(cardinal.x,cardinal.z)-Math.hypot(diagonal.x,diagonal.z))<1e-12,'Diagonal speed differs');
const wallLayout = {...emptyLayout,blockers:[{id:'wall',minX:.45,maxX:.6,minZ:-2,maxZ:2}]};
const wall = movePlayer(start,{x:1,z:1},.25,wallLayout);
assert(wall.x <= .45-layout.player.radius && wall.z > .3,'Wall sliding or thin-wall collision failed');
const edge = movePlayer({...start,x:layout.bounds.maxX-layout.player.radius-.01},{x:1,z:0},.25,emptyLayout);
assert(edge.x <= layout.bounds.maxX-layout.player.radius,'Player left terrain');
assert.deepEqual(movePlayer(start,{x:0,z:0},.1,emptyLayout),start,'No input moves player');
assert.throws(() => movePlayer(start,{x:NaN,z:0},.1,emptyLayout),TypeError);
for (const neighbor of layout.neighbors) assert.equal(nearestStation({x:neighbor.position[0],z:neighbor.position[2]+1.5},layout)?.id,neighbor.id);
assert.equal(nearestStation({x:layout.market.position[0],z:layout.market.position[2]},layout)?.type,'market');
const outOfRange = completeTrade(state,'common',layout); assert.equal(outOfRange.ok,false); assert.equal(outOfRange.state,state);
const atMarket = {...state,player:{...state.player,x:layout.market.position[0],z:layout.market.position[2]}};
const original = JSON.stringify(atMarket), preview = previewTrade(atMarket,'rare');
assert(preview.ok); assert.equal(JSON.stringify(atMarket),original,'Preview/cancel mutates inventory');
const buy = completeTrade(atMarket,'rare',layout);
assert(buy.ok); assert.equal(buy.state.coins,42); assert.equal(buy.state.inventory.rare_card,1); assert.equal(buy.state.stock.rare,3);
assert.equal(JSON.stringify(atMarket),original,'Trade mutates old state');
const sell = completeTrade(buy.state,'sell_seed',layout);
assert(sell.ok); assert.equal(sell.state.coins,48); assert.equal(sell.state.inventory.seed_token,2); assert.equal(sell.state.trades,2);
assert.equal(completeTrade({...atMarket,coins:0},'common',layout).ok,false,'Insufficient coins accepted');
assert.equal(completeTrade({...atMarket,inventory:{...atMarket.inventory,seed_token:0}},'sell_seed',layout).ok,false,'Missing item accepted');
assert.equal(completeTrade({...atMarket,stock:{...atMarket.stock,epic:0}},'epic',layout).ok,false,'Sold-out item accepted');
assert.equal(completeTrade(atMarket,'unknown',layout).ok,false,'Unknown offer accepted');
assert.deepEqual(createState(layout),state,'Reset does not restore initial state');
for (const offer of OFFERS) {
  const result = completeTrade(atMarket,offer.id,layout); assert(result.ok);
  assert.equal(result.state.coins-atMarket.coins,offer.coins);
  assert.equal(result.state.inventory[offer.item]-atMarket.inventory[offer.item],offer.amount);
}
// Cardinal paths use the conservative larger unrotated half-extent, so any
// accepted path also fits every 90-degree player heading. Diagonal turning is
// separately checked with the actual rotated footprint.
const envelope = Math.max(...layout.player.halfExtents), blockers = collisionBlockers(layout), step = .1;
const origin = state.player, visited = new Set(['0,0']), queue = [{x:0,z:0}], reached = new Set();
for (let cursor=0;cursor<queue.length;cursor++) {
  const cell = queue[cursor], point = {x:origin.x+cell.x*step,z:origin.z+cell.z*step};
  const station = nearestStation(point,layout); if(station) reached.add(station.id);
  for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]) {
    const next = {x:cell.x+dx,z:cell.z+dz}, key = `${next.x},${next.z}`;
    if(visited.has(key)) continue;
    const position = {x:origin.x+next.x*step,z:origin.z+next.z*step};
    if(positionAllowed(position,envelope,layout.bounds,blockers)) {visited.add(key);queue.push(next);}
  }
}
for(const station of [...layout.neighbors,layout.market]) assert(reached.has(station.id),`${station.id} unreachable with actual avatar envelope`);
const diagonalLayout = {...layout,blockers:[],neighbors:[]};
const rotated = movePlayer(start,{x:1,z:1},.1,diagonalLayout);
const rotatedEnvelope = playerEnvelope(layout.player,rotated.yaw);
assert(rotatedEnvelope.x>=Math.max(...layout.player.halfExtents)-1e-8 && rotatedEnvelope.z>=Math.max(...layout.player.halfExtents)-1e-8);
assert(positionAllowed(rotated,rotatedEnvelope,layout.bounds,collisionBlockers(diagonalLayout)),'Rotated footprint invalid');
const nearWallLayout = {...layout,blockers:[{id:'wall',minX:.8,maxX:1,minZ:-2,maxZ:2}],neighbors:[]};
const constrained = movePlayer({...start,x:.2},{x:1,z:1},.1,nearWallLayout);
assert(positionAllowed(constrained,playerEnvelope(layout.player,constrained.yaw),nearWallLayout.bounds,collisionBlockers(nearWallLayout)),'Turning clips a wall');
const report = {schema:'greenbox-neighborhood-validation-v1',status:'pass',html:{path:'public/neighborhood/index.html',bytes:Buffer.byteLength(html),sha256:hash(Buffer.from(html))},
  layoutSha256:data.layoutSha256,modelCount:summaries.length,triangles:summaries.reduce((total,model)=>total+model.triangles,0),models:summaries,
  physics:data.physics,reachableStations:[...reached],reachableCells:visited.size,
  checks:['embedded original GLB bytes and source hashes','embedded layout and full palette catalog match sources','six actual rigid pivots for all five characters','no external GLB resources','bundled script syntax','normalized diagonal speed','wall collision and sliding','terrain boundary containment','no input stops movement','four NPC and market ranges','out-of-range trade rejection','preview/cancel preserves state','atomic trade coin/item/stock conservation','insufficient coins and inventory rejection','sold-out and unknown offer rejection','reset restores initial visit','actual model footprints and yaw rotation','head envelope wall-safe turning','all five stations reachable with larger avatar envelope'],
  limits:['Browser movement, rendered models, dialogue, reactions and touch interaction require live browser validation.','This is a single-player local session; inventory is reset on reload and no network exchange exists.']};
await fs.writeFile(path.join(root,'neighborhood/validation.json'),JSON.stringify(report,null,2)+'\n');
console.log(`Neighborhood validation passed: ${summaries.length} embedded GLBs, ${report.triangles} triangles; movement, range, trade and reset rules pass.`);
