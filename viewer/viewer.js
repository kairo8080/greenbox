import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { buildPalette, writeVoxPalette, writeGlbPalette } from './palette-core.mjs';

const data = JSON.parse(document.getElementById('viewer-data').textContent);
const ui = Object.fromEntries(['viewer-canvas', 'canvas-wrap', 'loading-status', 'error-banner', 'selected-label', 'stats', 'scene-labels', 'asset-select', 'character-style', 'view-mode', 'character-select', 'framing', 'sync-cameras', 'motion-toggle', 'reset-view', 'palette-select', 'protect-identity', 'palette-swatches', 'palette-status', 'export-palette', 'export-vox', 'export-glb'].map(id => [id, document.getElementById(id)]));
const state = { selected: 'rasta_grower', style: 'chibi', collection: 'characters', mode: 'compare', framing: 'body', synced: true, spinning: false, theme: 'original', protected: true, overrides: {} };
const records = new Map();
const panels = document.createElement('div');
panels.id = 'view-panels';
ui['canvas-wrap'].append(panels);
const paletteCanvas = document.createElement('canvas');
paletteCanvas.width = paletteCanvas.height = 16;
const paletteContext = paletteCanvas.getContext('2d');
const paletteTexture = new THREE.CanvasTexture(paletteCanvas);
paletteTexture.flipY = false;
paletteTexture.colorSpace = THREE.SRGBColorSpace;
paletteTexture.minFilter = paletteTexture.magFilter = THREE.NearestFilter;
paletteTexture.generateMipmaps = false;
let palette, renderer, views = [], driver, dirty = true, syncing = false;
let previousTime = 0, statsTime = 0;
const number = value => value.toLocaleString('en-US');
const hex = color => '#' + color.slice(0, 3).map(value => value.toString(16).padStart(2, '0')).join('');
const decode = value => Uint8Array.from(atob(value), character => character.charCodeAt(0));
const selectedModelId = () => state.style === 'chibi' ? `${state.selected}_chibi` : state.selected;
const characterModels = () => data.models.filter(model => model.kind === 'character' && model.style === state.style);

function updatePalette() {
  palette = buildPalette(data.catalog, state.theme, state.protected, state.overrides);
  const pixels = new ImageData(16, 16);
  for (let texel = 0; texel < 256; texel++) pixels.data.set(palette[(texel + 1) % 256], texel * 4);
  paletteContext.putImageData(pixels, 0, 0);
  paletteTexture.needsUpdate = true;
  for (const input of ui['palette-swatches'].children) input.value = hex(palette[Number(input.dataset.index)]);
  const edits = Object.keys(state.overrides).length;
  ui['palette-status'].textContent = `${data.catalog.presets[state.theme].label} · ${state.protected ? 'identity protected' : 'all colors themed'}${edits ? ` · ${edits} custom color${edits === 1 ? '' : 's'}` : ''}`;
  dirty = true;
}

function makeSwatches() {
  for (const [role, index] of Object.entries(data.catalog.roles).filter(([, index]) => index > 0).sort((a, b) => a[1] - b[1])) {
    const input = document.createElement('input');
    input.type = 'color';
    input.dataset.index = index;
    const label = `${role.replaceAll('_', ' ')} · color ${index}`;
    input.setAttribute('aria-label', label);
    input.title = `${label} — edit this color for every asset`;
    input.addEventListener('input', () => { state.overrides[index] = input.value; updatePalette(); });
    ui['palette-swatches'].append(input);
  }
}

function applyMaterials(root, style) {
  root.traverse(object => {
    if (!object.isMesh) return;
    object.castShadow = true;
    // Broad chibi faces stay clean while the models cast ground shadows.
    object.receiveShadow = style !== 'chibi';
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    for (const material of materials) {
      if (material.map) material.map = paletteTexture;
      if (material.emissiveMap) material.emissiveMap = paletteTexture;
      material.needsUpdate = true;
    }
  });
}

function modelClone(record) {
  const clone = record.scene.clone(true);
  if (record.kind === 'props') {
    // A prop can contain ordinary and emissive primitives. Move the whole
    // named source node so its LED/light remains attached to its body.
    const meshes = clone.children;
    let cursor = 0;
    for (const mesh of meshes) {
      clone.updateMatrixWorld(true);
      const box = new THREE.Box3().setFromObject(mesh);
      const center = box.getCenter(new THREE.Vector3());
      mesh.position.x += cursor - box.min.x;
      mesh.position.y -= box.min.y;
      mesh.position.z -= center.z;
      cursor += box.max.x - box.min.x + 0.3;
    }
  }
  clone.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(clone);
  const center = box.getCenter(new THREE.Vector3());
  clone.position.add(new THREE.Vector3(-center.x, -box.min.y, -center.z));
  clone.updateMatrixWorld(true);
  return clone;
}

function highlightSelection() {
  for (const view of views) {
    const selected = view.ids.includes(selectedModelId());
    view.panel.classList.toggle('is-selected', selected && state.collection === 'characters');
    view.label.classList.toggle('is-selected', selected && state.collection === 'characters');
  }
  const selected = currentRecord();
  ui['selected-label'].textContent = selected.label + (state.collection === 'characters' ? ` · ${state.style === 'chibi' ? 'chibi' : 'original'}${state.mode === 'compare' ? ' · comparing seven' : ''}` : '');
  ui['character-select'].value = state.selected;
  ui['export-vox'].disabled = !selected.voxBytes;
  ui['export-vox'].title = selected.voxBytes ? 'Download the current palette in the editable voxel source' : 'Props have separate VOX sources; download the original prop library as GLB';
  document.querySelector('.export-note').textContent = `Download ${selected.label.toLowerCase()} with the current palette.`;
  dirty = true;
}

function currentRecord() {
  return records.get(state.collection === 'characters' ? selectedModelId() : state.collection === 'room' ? 'bedroom' : 'props');
}

function chooseDriver(view) {
  if (driver !== view) {
    const previousSyncing = syncing;
    syncing = true;
    for (const other of views) {
      other.controls.enableDamping = false;
      other.controls.update();
      other.controls.enableDamping = true;
    }
    syncing = previousSyncing;
    driver = view;
  }
  if (state.collection === 'characters' && view.ids.length === 1) {
    state.selected = records.get(view.ids[0]).characterId;
    highlightSelection();
  }
}

function syncViews() {
  if (!state.synced || views.length < 2 || !driver || syncing) return;
  syncing = true;
  const offset = driver.camera.position.clone().sub(driver.controls.target).divideScalar(driver.frameDistance);
  const pan = driver.controls.target.clone().sub(driver.defaultTarget).divideScalar(driver.height);
  for (const view of views) {
    if (view === driver) continue;
    view.controls.target.copy(view.defaultTarget).addScaledVector(pan, view.height);
    view.camera.position.copy(view.controls.target).addScaledVector(offset, view.frameDistance);
    view.controls.enableDamping = false;
    view.controls.update();
    view.controls.enableDamping = true;
  }
  syncing = false;
}

function makeView(ids, label) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#bed7d2');
  scene.add(new THREE.HemisphereLight(0xfff6df, 0x52644f, 2.25));
  const key = new THREE.DirectionalLight(0xfff1d7, 3.0);
  key.position.set(-3, 6, 5);
  key.castShadow = true;
  key.shadow.mapSize.set(512, 512);
  key.shadow.bias = -0.0002;
  key.shadow.normalBias = 0.008;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xc9e8ef, 1.15);
  fill.position.set(4, 3, -3);
  scene.add(fill);
  const models = new Map();
  let cursor = 0;
  for (const id of ids) {
    const model = modelClone(records.get(id));
    const box = new THREE.Box3().setFromObject(model);
    if (ids.length > 1) {
      const width = box.max.x - box.min.x;
      model.position.x += cursor + width / 2;
      cursor += width + 0.48;
    }
    scene.add(model);
    models.set(id, model);
  }
  if (ids.length > 1) for (const model of models.values()) model.position.x -= (cursor - 0.48) / 2;
  scene.updateMatrixWorld(true);
  const box = new THREE.Box3();
  for (const model of models.values()) box.union(new THREE.Box3().setFromObject(model));
  const size = box.getSize(new THREE.Vector3());
  const groundSize = Math.max(size.x, size.z, size.y) * 2.2;
  const span = Math.max(size.x, size.z, size.y);
  const center = box.getCenter(new THREE.Vector3());
  key.target.position.copy(center);
  scene.add(key.target);
  key.position.copy(center).add(new THREE.Vector3(-0.8, 1.7, 1.0).multiplyScalar(span * 2));
  Object.assign(key.shadow.camera, { left: -span, right: span, top: span, bottom: -span, near: 0.1, far: span * 10 });
  key.shadow.camera.updateProjectionMatrix();
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(groundSize, groundSize), new THREE.MeshStandardMaterial({ color: '#e6d4ab', roughness: 1 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(box.getCenter(new THREE.Vector3()).x, box.min.y - 0.008, box.getCenter(new THREE.Vector3()).z);
  ground.receiveShadow = true;
  ground.userData.viewerGround = true;
  scene.add(ground);
  const panel = document.createElement('div');
  panel.className = 'view-panel';
  panel.tabIndex = 0;
  panel.setAttribute('role', 'group');
  panel.setAttribute('aria-label', `${label} 3D view. Drag to orbit, wheel to zoom.`);
  panels.append(panel);
  const tag = document.createElement('div');
  tag.className = 'scene-label';
  tag.textContent = label;
  ui['scene-labels'].append(tag);
  const camera = new THREE.PerspectiveCamera(36, 1, 0.01, Math.max(100, groundSize * 10));
  const controls = new OrbitControls(camera, panel);
  controls.enableDamping = true;
  controls.dampingFactor = 0.1;
  controls.rotateSpeed = 0.7;
  controls.autoRotateSpeed = 1.2;
  controls.maxPolarAngle = Math.PI * 0.88;
  controls.listenToKeyEvents(panel);
  const view = { ids, scene, models, panel, label: tag, camera, controls, box, height: size.y, defaultTarget: new THREE.Vector3(), frameDistance: 1, needsShadow: true };
  panel.addEventListener('pointerdown', () => chooseDriver(view), { capture: true });
  panel.addEventListener('wheel', () => chooseDriver(view), { passive: true, capture: true });
  panel.addEventListener('focus', () => chooseDriver(view));
  panel.addEventListener('contextmenu', event => event.preventDefault());
  controls.addEventListener('change', () => { dirty = true; if (view === driver && !syncing) syncViews(); });
  return view;
}

function frameView(view, resetAngle = true) {
  const aspect = Math.max(0.1, view.panel.clientWidth / Math.max(1, view.panel.clientHeight));
  view.camera.aspect = aspect;
  view.camera.updateProjectionMatrix();
  let box = view.box.clone();
  const portrait = state.framing === 'portrait' && state.collection === 'characters';
  if (portrait) {
    const model = view.models.get(view.ids.length === 1 ? view.ids[0] : selectedModelId());
    let head;
    model?.traverse(object => { if (object.isMesh && /head/i.test(object.name)) head = object; });
    if (head) {
      box = new THREE.Box3().setFromObject(head);
      const headSize = box.getSize(new THREE.Vector3());
      box.min.y -= headSize.y * 0.22;
      box.expandByVector(new THREE.Vector3(0.1, 0.06, 0.05));
    }
  }
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const tangent = Math.tan(THREE.MathUtils.degToRad(view.camera.fov / 2));
  const elevation = defaultElevation();
  const depth = (size.x + size.z) / Math.sqrt(2);
  const projectedHeight = size.y * Math.cos(elevation) + depth * Math.sin(elevation);
  const projectedWidth = portrait ? depth : Math.max(size.x, size.z);
  view.frameDistance = Math.max(projectedHeight / (2 * tangent), projectedWidth / (2 * tangent * aspect)) * (portrait ? 1.1 : 1.28) + size.z * (portrait ? 0.1 : 0.3);
  view.defaultTarget.copy(center);
  view.controls.minDistance = Math.max(0.12, view.height * 0.15);
  view.controls.maxDistance = Math.max(view.frameDistance * 10, view.height * 12);
  if (resetAngle) setAngle(view, state.collection === 'room' ? Math.PI / 4 : -Math.PI / 4, defaultElevation());
}

function defaultElevation() {
  return THREE.MathUtils.degToRad(state.collection === 'room' ? 28 : state.collection === 'props' ? 15 : 4);
}

function setAngle(view, azimuth, elevation) {
  const cos = Math.cos(elevation);
  syncing = true;
  view.controls.enableDamping = false;
  view.controls.update();
  view.controls.target.copy(view.defaultTarget);
  view.camera.position.copy(view.defaultTarget).add(new THREE.Vector3(Math.sin(azimuth) * cos, Math.sin(elevation), Math.cos(azimuth) * cos).multiplyScalar(view.frameDistance));
  view.controls.update();
  view.controls.enableDamping = true;
  syncing = false;
  dirty = true;
}

function rebuildViews() {
  for (const view of views) {
    view.controls.dispose();
    view.scene.traverse(object => {
      if (object.userData.viewerGround) { object.geometry.dispose(); object.material.dispose(); }
      if (object.isLight && object.shadow) object.shadow.dispose();
    });
  }
  views = []; driver = null;
  panels.replaceChildren(); ui['scene-labels'].replaceChildren();
  const compare = state.collection === 'characters' && state.mode === 'compare';
  panels.classList.toggle('compare', compare);
  if (compare) views = characterModels().map(model => makeView([model.id], model.label));
  else if (state.collection === 'characters' && state.mode === 'lineup') views = [makeView(characterModels().map(model => model.id), `All seven ${state.style} characters`)];
  else { const record = currentRecord(); views = [makeView([record.id], record.label)]; }
  driver = views.find(view => view.ids.includes(selectedModelId())) ?? views[0];
  for (const view of views) frameView(view);
  ui['view-mode'].disabled = state.collection !== 'characters';
  ui['character-style'].disabled = state.collection !== 'characters';
  ui['character-select'].disabled = state.collection !== 'characters';
  ui['framing'].disabled = state.collection !== 'characters';
  ui['sync-cameras'].disabled = !compare;
  highlightSelection();
  dirty = true;
}

function resize() {
  const width = Math.max(1, Math.round(ui['canvas-wrap'].clientWidth));
  const height = Math.max(1, Math.round(ui['canvas-wrap'].clientHeight));
  renderer.setSize(width, height, false);
  for (const view of views) {
    const oldDistance = view.frameDistance;
    const offset = view.camera.position.clone().sub(view.controls.target);
    frameView(view, false);
    view.camera.position.copy(view.controls.target).addScaledVector(offset, view.frameDistance / oldDistance);
    view.controls.update();
  }
  syncViews(); dirty = true;
}

function render(time) {
  const delta = Math.min(0.05, (time - previousTime) / 1000 || 0);
  previousTime = time;
  if (!document.hidden) {
    for (const view of views) view.controls.autoRotate = state.spinning && (state.synced ? view === driver : true);
    if (state.synced) { driver?.controls.update(delta); syncViews(); }
    else for (const view of views) view.controls.update(delta);
    if (dirty || state.spinning) {
      const canvasRect = ui['viewer-canvas'].getBoundingClientRect();
      renderer.setScissorTest(false);
      renderer.setClearColor('#1b2820'); renderer.clear();
      renderer.setScissorTest(true);
      for (const view of views) {
        const rect = view.panel.getBoundingClientRect();
        const x = rect.left - canvasRect.left, y = canvasRect.bottom - rect.bottom;
        const left = Math.max(0, x), bottom = Math.max(0, y);
        const right = Math.min(canvasRect.width, x + rect.width), top = Math.min(canvasRect.height, y + rect.height);
        if (right <= left || top <= bottom) continue;
        renderer.setViewport(x, y, rect.width, rect.height);
        renderer.setScissor(left, bottom, right - left, top - bottom);
        renderer.shadowMap.needsUpdate = view.needsShadow;
        renderer.render(view.scene, view.camera);
        view.needsShadow = false;
        view.label.style.left = `${x + rect.width / 2}px`;
        view.label.style.top = `${rect.bottom - canvasRect.top - 36}px`;
      }
      dirty = false;
    }
    if (time - statsTime > 250 && driver) {
      statsTime = time;
      const ids = new Set(views.flatMap(view => view.ids));
      const triangles = [...ids].reduce((sum, id) => sum + records.get(id).triangles, 0);
      const azimuth = Math.round(THREE.MathUtils.radToDeg(driver.controls.getAzimuthalAngle()));
      const zoom = Math.round(driver.frameDistance / driver.camera.position.distanceTo(driver.controls.target) * 100);
      ui.stats.textContent = `${ids.size} asset${ids.size === 1 ? '' : 's'} · ${number(triangles)} triangles · angle ${azimuth}° · zoom ${zoom}%`;
    }
  }
  requestAnimationFrame(render);
}

const downloadUrls = new Map();
function save(bytes, name, type) {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const extension = name.split('.').at(-1);
  const previous = downloadUrls.get(extension);
  if (previous) URL.revokeObjectURL(previous);
  downloadUrls.set(extension, url);
  let results = document.getElementById('export-results');
  if (!results) {
    results = document.createElement('div'); results.id = 'export-results';
    results.setAttribute('aria-live', 'polite');
    document.querySelector('.export-section').append(results);
  }
  results.querySelector(`[data-extension="${extension}"]`)?.remove();
  const link = document.createElement('a');
  link.href = url; link.download = name; link.dataset.extension = extension;
  link.textContent = `Save ${name}`;
  results.append(link); link.click();
}

function reportError(error) {
  ui['error-banner'].hidden = false;
  ui['error-banner'].textContent = error.message;
}

function wireControls() {
  ui['asset-select'].addEventListener('change', event => { state.collection = event.target.value; rebuildViews(); });
  ui['view-mode'].addEventListener('change', event => { state.mode = event.target.value; rebuildViews(); });
  ui['character-style'].addEventListener('change', event => { state.style = event.target.value; rebuildViews(); });
  ui.framing.addEventListener('change', event => { state.framing = event.target.value; for (const view of views) frameView(view); syncViews(); });
  ui['character-select'].addEventListener('change', event => {
    state.selected = event.target.value;
    if (state.mode === 'solo') rebuildViews();
    else if (state.mode === 'lineup' && state.framing === 'portrait') { for (const view of views) frameView(view); highlightSelection(); }
    else { chooseDriver(views.find(view => view.ids.includes(selectedModelId())) ?? driver); highlightSelection(); }
  });
  ui['sync-cameras'].addEventListener('change', event => { state.synced = event.target.checked; syncViews(); });
  ui['reset-view'].addEventListener('click', () => { for (const view of views) frameView(view); syncViews(); });
  for (const [id, azimuth] of [['front', 0], ['right', -Math.PI / 2], ['left', Math.PI / 2], ['back', Math.PI]])
    document.getElementById(`camera-${id}`).addEventListener('click', () => { for (const view of state.synced ? views : [driver]) setAngle(view, azimuth, defaultElevation()); });
  ui['motion-toggle'].textContent = 'Turntable';
  ui['motion-toggle'].addEventListener('click', event => { state.spinning = !state.spinning; event.currentTarget.setAttribute('aria-pressed', String(state.spinning)); });
  ui['palette-select'].addEventListener('change', event => { state.theme = event.target.value; state.overrides = {}; updatePalette(); });
  ui['protect-identity'].addEventListener('change', event => { state.protected = event.target.checked; updatePalette(); });
  document.querySelector('label[for="protect-identity"] span').textContent = 'Protect identity colors';
  ui['export-palette'].addEventListener('click', () => save(JSON.stringify({ schema: 'greenbox-active-palette-v1', theme: state.theme, protectIdentity: state.protected, overrides: state.overrides, roles: data.catalog.roles, colors: palette }, null, 2), `greenbox_palette_${state.theme}.json`, 'application/json'));
  ui['export-vox'].addEventListener('click', () => { try { const record = currentRecord(); save(writeVoxPalette(record.voxBytes, palette), `${record.id}_${state.theme}.vox`, 'application/octet-stream'); } catch (error) { reportError(error); } });
  ui['export-glb'].addEventListener('click', async () => {
    try {
      const record = currentRecord();
      const blob = await new Promise((resolve, reject) => paletteCanvas.toBlob(value => value ? resolve(value) : reject(new Error('Cannot encode the palette.')), 'image/png'));
      save(writeGlbPalette(record.glbBytes, new Uint8Array(await blob.arrayBuffer())), `${record.id}_${state.theme}.glb`, 'model/gltf-binary');
    } catch (error) { reportError(error); }
  });
}

async function start() {
  renderer = new THREE.WebGLRenderer({ canvas: ui['viewer-canvas'], antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.autoClear = false;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.shadowMap.autoUpdate = false;
  makeSwatches(); updatePalette();
  const loader = new GLTFLoader();
  let loaded = 0;
  await Promise.all(data.models.map(async model => {
    const glbBytes = decode(model.glb);
    const gltf = await loader.parseAsync(glbBytes.buffer, '');
    applyMaterials(gltf.scene, model.style);
    records.set(model.id, { ...model, scene: gltf.scene, glbBytes, voxBytes: model.vox ? decode(model.vox) : null });
    ui['loading-status'].textContent = `Loaded ${++loaded} of ${data.models.length} assets`;
  }));
  wireControls();
  document.querySelectorAll('[data-ready-control]').forEach(control => { control.disabled = false; });
  rebuildViews(); resize();
  ui['loading-status'].textContent = '';
  new ResizeObserver(resize).observe(ui['canvas-wrap']);
  window.addEventListener('resize', resize);
  ui['viewer-canvas'].addEventListener('webglcontextlost', event => { event.preventDefault(); reportError(new Error('The 3D graphics context was lost. Reload this file to reopen the models.')); });
  requestAnimationFrame(render);
}
start().catch(error => { ui['loading-status'].textContent = ''; reportError(new Error(`The viewer could not start: ${error.message}. Open it in a browser with WebGL 2 enabled.`)); });
