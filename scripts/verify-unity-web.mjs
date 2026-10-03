import { createHash } from 'node:crypto';
import { readFile, readdir, realpath, stat } from 'node:fs/promises';
import { basename, dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { brotliDecompressSync, gunzipSync } from 'node:zlib';

// Usage: node scripts/verify-unity-web.mjs [export-directory]
// The default is ../unity-build relative to this script. Explicit paths use cwd.
// Static integrity checks do not establish gameplay, performance, or build freshness.
const repository = dirname(dirname(fileURLToPath(import.meta.url)));
const currentBuild = join(repository, 'unity-build');
const publishedBuild = join(repository, 'public', 'unity');
const output = process.argv[2] ? resolve(process.argv[2]) : currentBuild;
const failures = [];
const warnings = [];
const references = [];
const files = new Map();
let dataEntries = 0;
let assetChecks = 0;

function check(condition, message) { if (!condition) failures.push(message); }
function inside(parent, child) {
  const path = relative(parent, child);
  return path !== '..' && !path.startsWith(`..${process.platform === 'win32' ? '\\' : '/'}`) && !isAbsolute(path);
}

// Resolve the literal URLs and simple buildUrl + "file" expressions Unity emits.
// Never evaluate JavaScript from an export being inspected.
function stringExpression(expression, values) {
  const token = /\s*("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[$A-Za-z_][\w$]*)\s*/y;
  let position = 0;
  let result = '';
  while (position < expression.length) {
    token.lastIndex = position;
    const match = token.exec(expression);
    if (!match) return null;
    const value = match[1];
    if (/^["']/.test(value)) {
      let invalid = false;
      const literal = value.slice(1, -1).replace(/\\(u[\da-fA-F]{4}|x[\da-fA-F]{2}|.)/g, (_, escape) => {
        if (/^[ux]/.test(escape)) return String.fromCharCode(parseInt(escape.slice(1), 16));
        if (/^[\\/'"]$/.test(escape)) return escape;
        invalid = true;
        return '';
      });
      if (invalid) return null;
      result += literal;
    } else {
      if (!values.has(value)) return null;
      result += values.get(value);
    }
    position = token.lastIndex;
    if (position === expression.length) return result;
    if (expression[position++] !== '+') return null;
  }
  return null;
}

async function localFile(url) {
  if (/^[a-z][a-z\d+.-]*:/i.test(url) || url.startsWith('//')) throw new Error(`External file reference: ${url}`);
  const path = decodeURIComponent(url.replace(/[?#].*$/, '')).replace(/^\/+/, '');
  if (!path || /[\\\x00-\x1f]/.test(path)) throw new Error(`Invalid file URL: ${url}`);
  const target = resolve(output, path);
  if (!inside(output, target)) throw new Error(`File escapes export directory: ${url}`);
  // Windows permits mismatched case; static Linux hosting does not.
  let cursor = output;
  for (const part of relative(output, target).split(/[\\/]/)) {
    if (!(await readdir(cursor)).includes(part)) throw new Error(`Missing or differently cased file: ${url}`);
    cursor = join(cursor, part);
  }
  if (!inside(await realpath(output), await realpath(target))) throw new Error(`File symlink escapes export directory: ${url}`);
  const info = await stat(target);
  if (!info.isFile() || info.size === 0) throw new Error(`File is empty or not a regular file: ${url}`);
  const buffer = await readFile(target);
  files.set(target, buffer.length);
  return buffer;
}

function decoded(buffer, url) {
  if (buffer[0] === 0x1f && buffer[1] === 0x8b) return gunzipSync(buffer);
  const filename = url.replace(/[?#].*$/, '');
  if (filename.endsWith('.br') || filename.endsWith('.unityweb')) return brotliDecompressSync(buffer);
  return buffer;
}

function validateData(buffer, url) {
  // Confirmed against this export and its generated loader's data parser.
  const signature = Buffer.from('UnityWebData1.0\0', 'ascii');
  if (buffer.length < 20 || !buffer.subarray(0, 16).equals(signature)) {
    failures.push(`${url} has no readable UnityWebData1.0 header.`);
    return;
  }
  const headerEnd = buffer.readUInt32LE(16);
  if (headerEnd < 20 || headerEnd > buffer.length) {
    failures.push(`${url} has an invalid data directory length.`);
    return;
  }
  let position = 20;
  const paths = new Set();
  while (position < headerEnd) {
    if (position + 12 > headerEnd) { failures.push(`${url} has a truncated data directory.`); return; }
    const offset = buffer.readUInt32LE(position);
    const length = buffer.readUInt32LE(position + 4);
    const pathLength = buffer.readUInt32LE(position + 8);
    position += 12;
    if (!pathLength || position + pathLength > headerEnd || offset < headerEnd || offset + length > buffer.length) {
      failures.push(`${url} has an invalid data entry.`);
      return;
    }
    const path = buffer.subarray(position, position + pathLength).toString('utf8');
    check(!paths.has(path), `${url} repeats an archive entry: ${path}`);
    paths.add(path);
    position += pathLength;
  }
  check(paths.size > 0, `${url} contains no data entries.`);
  dataEntries += paths.size;
}

async function validateSourceAssets() {
  const manifest = JSON.parse(await readFile(join(repository, 'unity', 'voxel-imports.json'), 'utf8'));
  check(manifest.schema === 'greenbox-unity-voxel-import-v1' && Array.isArray(manifest.assets) && manifest.assets.length > 0,
    'unity/voxel-imports.json must contain a recognized nonempty asset manifest.');
  if (!Array.isArray(manifest.assets)) return;
  for (const entry of manifest.assets) {
    if (!entry || typeof entry.asset !== 'string' || basename(entry.asset) !== entry.asset || typeof entry.source !== 'string'
      || !/^[\da-f]{64}$/i.test(entry.sha256) || !Number.isInteger(entry.bytes) || entry.bytes <= 0) {
      failures.push('Invalid voxel import manifest entry.');
      continue;
    }
    const source = resolve(repository, entry.source);
    if (!inside(repository, source)) { failures.push(`Asset source escapes repository: ${entry.source}`); continue; }
    const imported = join(repository, 'unity', 'Greenbox', 'Assets', 'Resources', 'Voxels', entry.asset);
    for (const [label, path] of [['source', source], ['Unity import', imported]]) {
      try {
        const buffer = await readFile(path);
        check(buffer.length === entry.bytes, `${label} size differs from manifest: ${entry.asset}`);
        check(createHash('sha256').update(buffer).digest('hex') === entry.sha256.toLowerCase(),
          `${label} SHA-256 differs from manifest: ${entry.asset}`);
        assetChecks++;
      } catch (error) { failures.push(`${label} unavailable: ${entry.asset} (${error.code ?? error.message})`); }
    }
  }
}

try {
  const html = (await localFile('index.html')).toString('utf8');
  check(/<html\b/i.test(html), 'index.html must contain an HTML launcher.');
  check(!html.includes('{{{') && !html.includes('}}}'), 'index.html contains unresolved Unity template placeholders.');
  if (relative(publishedBuild, output) === '')
    check(/<base\b[^>]*\bhref=["']\/unity\/["']/i.test(html), 'Published Unity HTML must retain its /unity/ base for nested asset URLs.');
  const values = new Map();
  for (const match of html.matchAll(/\b(?:const|let|var)\s+([$A-Za-z_][\w$]*)\s*=\s*([^;\r\n]+)/g)) {
    const value = stringExpression(match[2], values);
    if (value !== null) values.set(match[1], value);
  }
  for (const match of html.matchAll(/\b(dataUrl|frameworkUrl|codeUrl)\s*:\s*([^,}\r\n]+)/g)) {
    const value = stringExpression(match[2], values);
    if (value === null) failures.push(`Cannot resolve ${match[1]} statically: ${match[2]}`);
    else references.push({ role: { dataUrl: 'data', frameworkUrl: 'framework', codeUrl: 'wasm' }[match[1]], url: value });
  }
  for (const match of html.matchAll(/\b[$A-Za-z_][\w$]*\.src\s*=\s*([^;\r\n]+)/g)) {
    const value = stringExpression(match[1], values);
    if (value !== null && /\.loader\.js(?:\.(?:gz|br|unityweb))?(?:[?#]|$)/.test(value)) references.push({ role: 'loader', url: value });
  }
  for (const match of html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["']/gi)) {
    if (/\.loader\.js(?:\.(?:gz|br|unityweb))?(?:[?#]|$)/.test(match[1])) references.push({ role: 'loader', url: match[1] });
  }
  for (const role of ['loader', 'data', 'framework', 'wasm'])
    check(references.some(reference => reference.role === role), `index.html must reference a Unity ${role} file.`);
  for (const { role, url } of references) {
    try {
      const buffer = await localFile(url);
      if (role === 'wasm') check(decoded(buffer, url).subarray(0, 8).equals(Buffer.from([0, 97, 115, 109, 1, 0, 0, 0])),
        `${url} must contain a WebAssembly version 1 module.`);
      if (role === 'data') validateData(decoded(buffer, url), url);
    } catch (error) { failures.push(`${role}: ${error.message}`); }
  }
  if (relative(currentBuild, output) === '' || relative(publishedBuild, output) === '') await validateSourceAssets();
  else warnings.push('External export: repository source/import hashes were not checked.');
} catch (error) { failures.push(error.code ?? error.message); }

for (const warning of warnings) console.warn(`Warning: ${warning}`);
console.log('Static validation does not test browser gameplay, performance, hosting headers, or prove export freshness.');
if (failures.length) {
  for (const failure of failures) console.error(`Error: ${failure}`);
  process.exitCode = 1;
} else {
  const bytes = [...files.values()].reduce((sum, size) => sum + size, 0);
  console.log(`Unity Web export verified: ${files.size} files, ${(bytes / 1024 / 1024).toFixed(2)} MiB, ${dataEntries} data entries, ${assetChecks} source/import hash checks.`);
}
