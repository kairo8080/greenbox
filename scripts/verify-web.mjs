import { readFile, readdir, stat } from 'node:fs/promises';
import { dirname, join, posix } from 'node:path';
import { fileURLToPath } from 'node:url';

const repository = dirname(dirname(fileURLToPath(import.meta.url)));
const game = join(repository, 'game');
const web = join(repository, 'public');
const failures = [];
const warnings = [];
const required = ['index.html', 'index.js', 'index.wasm', 'index.pck'];

function check(condition, message) {
  if (!condition) failures.push(message);
}

async function readRequired(path, label) {
  try {
    const info = await stat(path);
    check(info.isFile() && info.size > 0, `${label} must be a nonempty file.`);
    return info.isFile() ? await readFile(path) : null;
  } catch (error) {
    failures.push(`${label} is unavailable: ${error.code ?? error.message}`);
    return null;
  }
}

function sections(text) {
  const result = new Map();
  let current;
  for (const line of text.split(/\r?\n/)) {
    const heading = line.match(/^\s*\[([^\]]+)\]\s*$/);
    if (heading) {
      current = new Map();
      result.set(heading[1], current);
    } else if (current) {
      const entry = line.match(/^\s*([^;#=]+?)\s*=\s*(.*?)\s*$/);
      if (entry) current.set(entry[1], entry[2]);
    }
  }
  return result;
}

async function exactAssetPath(resource) {
  const segments = resource.slice('res://'.length).split('/');
  let path = game;
  for (const segment of segments) {
    if (!segment || segment === '.' || segment === '..') return false;
    try {
      const names = await readdir(path);
      if (!names.includes(segment)) return false;
      path = join(path, segment);
    } catch {
      return false;
    }
  }
  try {
    return (await stat(path)).isFile();
  } catch {
    return false;
  }
}

async function sourceFiles(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name === 'runtime') continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await sourceFiles(path));
    else if (/\.(gd|godot|tscn|tres)$/.test(entry.name)) files.push(path);
  }
  return files;
}

const exported = new Map();
for (const filename of required) {
  exported.set(filename, await readRequired(join(web, filename), `public/${filename}`));
}

const wasm = exported.get('index.wasm');
if (wasm) {
  check(wasm.subarray(0, 8).equals(Buffer.from([0, 97, 115, 109, 1, 0, 0, 0])),
    'index.wasm must contain an uncompressed WebAssembly version 1 module.');
}
const pack = exported.get('index.pck');
if (pack) check(pack.subarray(0, 4).toString('ascii') === 'GDPC', 'index.pck has an invalid Godot pack header.');

const html = exported.get('index.html')?.toString('utf8');
if (html) {
  check(/<html\b/i.test(html), 'index.html must contain the exported HTML launcher.');
  check(!/\$GODOT_[A-Z_]+/.test(html), 'index.html still contains unexpanded Godot shell placeholders.');
  for (const filename of ['index.js', 'index.wasm', 'index.pck']) {
    check(html.includes(filename), `index.html must reference ${filename}; keep export filenames together.`);
  }
}

const projectBuffer = await readRequired(join(game, 'project.godot'), 'game/project.godot');
if (projectBuffer) {
  const project = sections(projectBuffer.toString('utf8'));
  check(project.get('rendering')?.get('renderer/rendering_method') === '"gl_compatibility"',
    'The Web build requires the Compatibility rendering method.');
  check(project.get('application')?.get('run/main_scene') === '"res://main.tscn"',
    'The expected game entry point is res://main.tscn.');
  await readRequired(join(game, 'main.tscn'), 'game/main.tscn');
}

const presetBuffer = await readRequired(join(game, 'export_presets.cfg'), 'game/export_presets.cfg');
if (presetBuffer) {
  const presets = sections(presetBuffer.toString('utf8'));
  const webPreset = [...presets].find(([name, values]) => /^preset\.\d+$/.test(name) && values.get('platform') === '"Web"');
  check(Boolean(webPreset), 'A Web export preset is required.');
  if (webPreset) {
    const [name, values] = webPreset;
    const options = presets.get(`${name}.options`);
    check(values.get('name') === '"Web"', 'Name the Web export preset Web so the export script can select it.');
    check(options?.get('variant/thread_support') === 'false', 'The static Web build must disable thread support.');
    check(options?.get('variant/extensions_support') === 'false', 'The static Web build must disable GDExtensions.');
    check(options?.get('progressive_web_app/enabled') === 'false', 'PWA caching is disabled for this prototype.');
    if (['custom_template/debug', 'custom_template/release'].some(key => options?.get(key) && options.get(key) !== '""')) {
      warnings.push('Web export uses custom templates; those paths must be available when re-exporting locally.');
    }
  }
}

const references = new Set();
try {
  for (const file of await sourceFiles(game)) {
    const source = await readFile(file, 'utf8');
    for (const match of source.matchAll(/res:\/\/assets\/[^"'\s)]+/g)) references.add(match[0]);
  }
  // The mesh can exist while an external palette image is missing or mis-cased.
  for (const resource of [...references].filter(path => path.endsWith('.glb'))) {
    if (!await exactAssetPath(resource)) continue;
    const relative = resource.slice('res://'.length);
    const glb = await readFile(join(game, ...relative.split('/')));
    const headerValid = glb.length >= 20 && glb.subarray(0, 4).toString('ascii') === 'glTF'
      && glb.readUInt32LE(4) === 2 && glb.readUInt32LE(8) === glb.length;
    check(headerValid, `Invalid GLB header: ${resource}`);
    if (!headerValid) continue;
    const jsonLength = glb.readUInt32LE(12);
    const jsonValid = glb.readUInt32LE(16) === 0x4e4f534a && 20 + jsonLength <= glb.length;
    check(jsonValid, `Invalid GLB JSON chunk: ${resource}`);
    if (!jsonValid) continue;
    const gltf = JSON.parse(glb.subarray(20, 20 + jsonLength).toString('utf8').replace(/\0+$/, '').trim());
    for (const entry of [...(gltf.images ?? []), ...(gltf.buffers ?? [])]) {
      if (!entry.uri || entry.uri.startsWith('data:')) continue;
      check(!/^[a-z]+:/i.test(entry.uri), `Asset must use a local dependency: ${resource} -> ${entry.uri}`);
      if (/^[a-z]+:/i.test(entry.uri)) continue;
      const dependency = posix.normalize(posix.join(posix.dirname(relative), decodeURIComponent(entry.uri)));
      check(dependency.startsWith('assets/'), `Asset dependency must stay in game/assets: ${resource} -> ${entry.uri}`);
      if (dependency.startsWith('assets/')) references.add(`res://${dependency}`);
    }
  }
  for (const resource of [...references].sort()) {
    check(await exactAssetPath(resource), `Missing or differently cased asset filename: ${resource}`);
  }
  check(references.size > 0, 'No asset references were found in the Godot source.');
} catch (error) {
  failures.push(`Could not inspect game assets: ${error.code ?? error.message}`);
}

for (const warning of warnings) console.warn(`Warning: ${warning}`);
if (failures.length) {
  for (const failure of failures) console.error(`Error: ${failure}`);
  console.error('Web verification failed. Re-export with matching Godot templates, then run npm run build.');
  process.exitCode = 1;
} else {
  const bytes = [...exported.values()].reduce((sum, content) => sum + content.length, 0);
  console.log(`Web export verified: ${required.length} files, ${(bytes / 1024 / 1024).toFixed(2)} MiB, ${references.size} valid asset references.`);
  console.log('This checks committed files and configuration; browser gameplay and export freshness need separate verification.');
}
