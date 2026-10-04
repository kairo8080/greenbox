import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import esbuild from '../viewer/node_modules/esbuild/lib/main.js';
import { Matrix4, Quaternion, Vector3, Box3 } from '../viewer/node_modules/three/build/three.module.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const layoutPath = 'voxel_sources/neighborhood/game_layout.json';
const layoutBytes = await fs.readFile(path.join(root, layoutPath));
const layout = JSON.parse(layoutBytes);
if (layout.schema !== 'greenbox-neighborhood-layout-v1' || layout.environmentIncludesStaticCharacters !== false)
  throw new Error('Neighborhood requires a checked layout and a bare environment.');
const catalog = JSON.parse(await fs.readFile(path.join(root, 'viewer/palettes.json'), 'utf8'));
const modelSpecs = [
  ['neighbor_commons','voxel_sources/neighborhood/neighbor_commons/neighbor_commons.glb'],
  ['rasta_grower','voxel_sources/garden_cast/rasta_grower/rasta_grower.glb'],
  ...layout.neighbors.map(neighbor => [neighbor.characterId, `voxel_sources/garden_cast/${neighbor.characterId}/${neighbor.characterId}.glb`]),
];
for (const rarity of ['common','rare','epic']) {
  const source = `voxel_sources/collectibles/card_${rarity}/card_${rarity}.glb`;
  await fs.access(path.join(root,source));
  modelSpecs.push([`${rarity}_card`, source]);
}
const models = [];
const physics = {schema:'greenbox-actual-avatar-footprints-v1',models:{}};
function modelBounds(document) {
  const box = new Box3();
  function visit(index,parent) {
    const node = document.nodes[index], transform = new Matrix4();
    if (node.matrix) transform.fromArray(node.matrix);
    else transform.compose(new Vector3().fromArray(node.translation??[0,0,0]),new Quaternion().fromArray(node.rotation??[0,0,0,1]),new Vector3().fromArray(node.scale??[1,1,1]));
    transform.premultiply(parent);
    if (node.mesh !== undefined) for (const primitive of document.meshes[node.mesh].primitives) {
      const accessor = document.accessors[primitive.attributes.POSITION];
      if (!accessor.min || !accessor.max) throw new Error('Model footprint requires actual position accessor bounds.');
      for (const x of [accessor.min[0],accessor.max[0]]) for (const y of [accessor.min[1],accessor.max[1]]) for (const z of [accessor.min[2],accessor.max[2]])
        box.expandByPoint(new Vector3(x,y,z).applyMatrix4(transform));
    }
    for (const child of node.children??[]) visit(child,transform);
  }
  for (const index of document.scenes[document.scene??0].nodes) visit(index,new Matrix4());
  const x = Math.max(Math.abs(box.min.x),Math.abs(box.max.x)),z = Math.max(Math.abs(box.min.z),Math.abs(box.max.z));
  return {min:box.min.toArray(),max:box.max.toArray(),halfExtents:[x,z],radius:Math.hypot(x,z)};
}
for (const [id, source] of modelSpecs) {
  if (models.some(model => model.id === id)) continue;
  const bytes = await fs.readFile(path.join(root,source));
  if (bytes.readUInt32LE(0) !== 0x46546c67 || bytes.readUInt32LE(4) !== 2 || bytes.readUInt32LE(8) !== bytes.length)
    throw new Error(`Invalid GLB source: ${source}`);
  const document = JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString('utf8').trim());
  if (document.buffers?.some(buffer => buffer.uri) || document.images?.some(image => image.uri))
    throw new Error(`Neighborhood model has external resources: ${id}`);
  const triangles = document.meshes.reduce((total, mesh) => total + mesh.primitives.reduce((sum, primitive) => {
    if ((primitive.mode ?? 4) !== 4 || !Number.isInteger(primitive.indices)) throw new Error('Expected indexed triangles.');
    return sum + document.accessors[primitive.indices].count / 3;
  },0),0);
  models.push({ id, source, glb:bytes.toString('base64'), glbSha256:hash(bytes), bytes:bytes.length, triangles });
  if (['rasta_grower',...layout.neighbors.map(neighbor => neighbor.characterId)].includes(id)) physics.models[id] = modelBounds(document);
}
const bundle = await esbuild.build({ entryPoints:[path.join(root,'neighborhood/neighborhood.js')], bundle:true, write:false,
  format:'iife', target:['es2022'], minify:true, legalComments:'inline', sourcemap:false });
const [shell, css, license] = await Promise.all([
  fs.readFile(path.join(root,'neighborhood/neighborhood-shell.html'),'utf8'),
  fs.readFile(path.join(root,'neighborhood/neighborhood.css'),'utf8'),
  fs.readFile(path.join(root,'viewer/node_modules/three/LICENSE'),'utf8'),
]);
const embedded = JSON.stringify({ schema:'greenbox-neighborhood-v1', layout, layoutSource:layoutPath, layoutSha256:hash(layoutBytes), catalog, physics, models }).replaceAll('<','\\u003c');
const html = shell.replace('/* NEIGHBORHOOD_STYLE */',() => css).replace('/* NEIGHBORHOOD_DATA */',() => embedded)
  .replace('/* NEIGHBORHOOD_SCRIPT */',() => bundle.outputFiles[0].text.replace(/<\/script/gi,'<\\/script'))
  .replace('</body>',() => `<!-- Bundled Three.js 0.186.1 license\n${license}\n-->\n</body>`);
await fs.mkdir(path.join(root,'public/neighborhood'),{recursive:true});
await fs.writeFile(path.join(root,'public/neighborhood/index.html'),html);
await fs.writeFile(path.join(root,'neighborhood/THREE-LICENSE.txt'),license);
console.log(`Built self-contained Greenbox neighborhood: ${models.length} voxel GLBs, ${models.reduce((sum,model) => sum+model.triangles,0)} triangles, ${(Buffer.byteLength(html)/1024/1024).toFixed(2)} MiB.`);
