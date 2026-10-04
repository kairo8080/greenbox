import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import esbuild from '../viewer/node_modules/esbuild/lib/main.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const catalog = JSON.parse(await fs.readFile(path.join(root, 'viewer/palettes.json'), 'utf8'));
const cast = [
  ['rasta_grower', 'Rasta grower'], ['corporate_boss', 'Corporate boss'], ['robot', 'Robot'],
  ['chef', 'Chef'], ['blonde_lady', 'Blonde lady'], ['party_woman', 'Party woman'], ['skeleton', 'Skeleton'],
];

function glbDocument(bytes) {
  if (bytes.readUInt32LE(0) !== 0x46546c67 || bytes.readUInt32LE(4) !== 2 || bytes.readUInt32LE(8) !== bytes.length) throw new Error('Invalid source GLB');
  const length = bytes.readUInt32LE(12);
  const document = JSON.parse(bytes.subarray(20, 20 + length).toString('utf8').trim());
  if (document.buffers.some(buffer => buffer.uri) || document.images?.some(image => image.uri)) throw new Error('Viewer assets must be self-contained GLBs');
  return document;
}

async function asset(id, label, kind, glbPath, voxPath, source, variant = {}) {
  const bytes = await fs.readFile(path.join(root, glbPath));
  const document = glbDocument(bytes);
  const triangles = document.meshes.reduce((sum, mesh) => sum + mesh.primitives.reduce((total, primitive) => {
    if ((primitive.mode ?? 4) !== 4) throw new Error('Viewer expects triangulated meshes');
    return total + document.accessors[primitive.indices ?? primitive.attributes.POSITION].count / 3;
  }, 0), 0);
  return { id, label, kind, ...variant, glb: bytes.toString('base64'), vox: voxPath ? (await fs.readFile(path.join(root, voxPath))).toString('base64') : null,
    glbSha256: crypto.createHash('sha256').update(bytes).digest('hex'), triangles,
    voxels: source?.voxels?.length ?? null, height: source ? source.dimensions[2] * 0.05 : null };
}

const models = [];
for (const [id, label] of cast) {
  const base = `voxel_sources/character_cast/${id}/${id}`;
  const source = JSON.parse(await fs.readFile(path.join(root, `${base}.json`), 'utf8'));
  models.push(await asset(id, label, 'character', `${base}.glb`, `${base}.vox`, source, { style: 'original', characterId: id }));
}
for (const [id, label] of cast) {
  const base = `voxel_sources/chibi_cast/${id}/${id}`;
  const source = JSON.parse(await fs.readFile(path.join(root, `${base}.json`), 'utf8'));
  models.push(await asset(`${id}_chibi`, label, 'character', `${base}.glb`, `${base}.vox`, source, { style: 'chibi', characterId: id }));
}
for (const [id, label] of cast) {
  const base = `voxel_sources/garden_cast/${id}/${id}`;
  const source = JSON.parse(await fs.readFile(path.join(root, `${base}.json`), 'utf8'));
  models.push(await asset(`${id}_garden`, label, 'character', `${base}.glb`, `${base}.vox`, source, { style: 'garden', characterId: id }));
}
models.push(await asset('bedroom', 'Rasta bedroom', 'room', 'game/assets/rasta_bedroom.glb', 'voxel_sources/rasta_room/rasta_bedroom.vox'));
models.push(await asset('props', 'Grow props', 'props', 'game/assets/starter_props.glb', null));
for (const [id, label] of [['starter_loft','Level-one bedroom'],['roots_street','ROOTS district']]) {
  const base = `voxel_sources/lore_scenes/${id}/${id}`;
  const source = JSON.parse(await fs.readFile(path.join(root, `${base}.json`), 'utf8'));
  const scene = JSON.parse(await fs.readFile(path.join(root, `voxel_sources/lore_scenes/${id}/scene.json`), 'utf8'));
  models.push(await asset(id, label, 'lore', `${base}.glb`, `${base}.vox`, source, { loreLights: scene.lights }));
}
const gardenBase = 'voxel_sources/garden_scenes/seedling_garden/seedling_garden';
const gardenSource = JSON.parse(await fs.readFile(path.join(root, `${gardenBase}.json`), 'utf8'));
const gardenScene = JSON.parse(await fs.readFile(path.join(root, 'voxel_sources/garden_scenes/seedling_garden/scene.json'), 'utf8'));
models.push(await asset('seedling_garden', 'Seedling garden', 'lore', `${gardenBase}.glb`, `${gardenBase}.vox`, gardenSource, { loreLights: gardenScene.lights ?? [] }));
const result = await esbuild.build({ entryPoints: [path.join(root, 'viewer/viewer.js')], bundle: true, write: false, format: 'iife', target: ['es2022'], minify: true, legalComments: 'inline', sourcemap: false });
const [shell, css] = await Promise.all(['viewer-shell.html', 'viewer.css'].map(file => fs.readFile(path.join(root, 'viewer', file), 'utf8')));
const embedded = JSON.stringify({ schema: 'greenbox-viewer-v4', catalog, models }).replaceAll('<', '\\u003c');
const script = result.outputFiles[0].text.replace(/<\/script/gi, '<\\/script');
const license = await fs.readFile(path.join(root, 'viewer/node_modules/three/LICENSE'), 'utf8');
const html = shell.replace('<!-- VIEWER_STYLE -->', () => css).replace('<!-- VIEWER_DATA -->', () => embedded).replace('<!-- VIEWER_SCRIPT -->', () => script)
  .replace('</body>', () => `<!-- Bundled Three.js 0.186.1 license\n${license}\n-->\n</body>`);
const destination = path.join(root, 'public/viewer/index.html');
const portable = path.join(root, 'outputs/greenbox-character-viewer.html');
await fs.mkdir(path.dirname(destination), { recursive: true });
await fs.mkdir(path.dirname(portable), { recursive: true });
await fs.writeFile(destination, html);
await fs.writeFile(portable, html);
await fs.copyFile(path.join(root, 'viewer/node_modules/three/LICENSE'), path.join(root, 'viewer/THREE-LICENSE.txt'));
console.log(`Built ${models.length} real voxel assets into one offline HTML (${(Buffer.byteLength(html) / 1024 / 1024).toFixed(2)} MiB).`);
console.log(`Portable file: ${portable}`);
