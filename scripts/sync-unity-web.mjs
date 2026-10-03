import { spawnSync } from 'node:child_process';
import { copyFile, lstat, mkdir, mkdtemp, readFile, readdir, realpath, rename, rm, writeFile } from 'node:fs/promises';
import { basename, dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Usage: node scripts/sync-unity-web.mjs [export-directory]
// Validates before replacing the fixed public/unity directory; never replaces public/.
const repository = dirname(dirname(fileURLToPath(import.meta.url)));
const source = process.argv[2] ? resolve(process.argv[2]) : join(repository, 'unity-build');
const publicDirectory = join(repository, 'public');
const target = join(publicDirectory, 'unity');
const validator = join(repository, 'scripts', 'verify-unity-web.mjs');
let stage;
let retainStage = false;

function inside(parent, child) {
  const path = relative(parent, child);
  return path !== '..' && !path.startsWith(`..${process.platform === 'win32' ? '\\' : '/'}`) && !isAbsolute(path);
}

async function exists(path) {
  try { return await lstat(path); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

function verify(path) {
  const result = spawnSync(process.execPath, [validator, path], { stdio: 'inherit' });
  if (result.error || result.status !== 0) throw new Error(`Unity export verification failed: ${path}`);
}

async function assertTarget() {
  // Check both lexical and filesystem paths before any recursive removal or move.
  if (resolve(target) !== join(repository, 'public', 'unity') || basename(target) !== 'unity')
    throw new Error('Refusing an unexpected publication target.');
  const realRepository = await realpath(repository);
  const realPublic = await realpath(publicDirectory);
  if (relative(join(realRepository, 'public'), realPublic) !== '') throw new Error('public/ must not be a redirected filesystem path.');
  const info = await exists(target);
  if (info && (!info.isDirectory() || info.isSymbolicLink()
    || relative(join(realPublic, 'unity'), await realpath(target)) !== ''))
    throw new Error('public/unity must be a regular directory within public/.');
  return Boolean(info);
}

async function copyExport(from, to) {
  await mkdir(to, { recursive: true });
  for (const entry of await readdir(from, { withFileTypes: true })) {
    if (from === source && entry.name === 'vercel.json') continue; // Root vercel.json owns hosting headers.
    if (entry.isSymbolicLink()) throw new Error(`Export contains a filesystem link: ${join(from, entry.name)}`);
    if (entry.isDirectory()) await copyExport(join(from, entry.name), join(to, entry.name));
    else if (entry.isFile()) await copyFile(join(from, entry.name), join(to, entry.name));
    else throw new Error(`Export contains an unsupported filesystem entry: ${entry.name}`);
  }
}

async function removeStage() {
  if (!stage || retainStage) return;
  const actual = await realpath(stage);
  const realRepository = await realpath(repository);
  if (!inside(realRepository, actual) || dirname(actual) !== realRepository || !basename(actual).startsWith('.unity-publish-'))
    throw new Error(`Refusing to remove an unexpected staging directory: ${actual}`);
  await rm(actual, { recursive: true, force: true });
}

try {
  verify(source);
  await mkdir(publicDirectory, { recursive: true });
  await assertTarget();
  const realSource = await realpath(source);
  const realTarget = join(await realpath(publicDirectory), 'unity');
  if (inside(realSource, realTarget) || inside(realTarget, realSource))
    throw new Error('Export and publication directories must not contain each other.');

  stage = await mkdtemp(join(repository, '.unity-publish-'));
  const next = join(stage, 'next');
  const previous = join(stage, 'previous');
  await copyExport(source, next);
  const index = join(next, 'index.html');
  let html = await readFile(index, 'utf8');
  if (/<base\b/i.test(html)) throw new Error('Export already has an HTML base; confirm its mount path before publishing.');
  if (!/<head\b[^>]*>/i.test(html)) throw new Error('Export has no HTML head for its publication base.');
  html = html.replace(/<head\b[^>]*>/i, '$&\n  <base href="/unity/">');
  // Unity resolves StreamingAssets against document.URL rather than the HTML base.
  html = html.replace(/(\bstreamingAssetsUrl\s*:\s*)(["'])StreamingAssets\2/g, '$1"/unity/StreamingAssets"');
  await writeFile(index, html);
  verify(next);

  const hadPrevious = await assertTarget();
  if (hadPrevious) await rename(target, previous);
  try { await rename(next, target); }
  catch (error) {
    if (hadPrevious) {
      try { await rename(previous, target); }
      catch (rollbackError) {
        retainStage = true;
        throw new Error(`Publish failed; previous preview retained at ${previous}. Restore error: ${rollbackError.message}`);
      }
    }
    throw error;
  }
  console.log(`Unity preview copied to ${target}. Existing Godot root files were preserved.`);
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exitCode = 1;
} finally {
  try { await removeStage(); }
  catch (error) { console.error(`Staging cleanup: ${error.message}`); process.exitCode = 1; }
}
