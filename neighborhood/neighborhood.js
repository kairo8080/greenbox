import * as THREE from '../viewer/node_modules/three/build/three.module.js';
import { OrbitControls } from '../viewer/node_modules/three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from '../viewer/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
import { buildPalette } from '../viewer/palette-core.mjs';
import { OFFERS, ITEM_LABELS, createState, movePlayer, nearestStation, previewTrade, completeTrade, withAvatarColliders } from './game-core.mjs';

const data = JSON.parse(document.getElementById('neighborhood-data').textContent);
const layout = withAvatarColliders(data.layout,data.physics);
const ui = Object.fromEntries(['world-canvas','world-wrap','world-labels','reaction-labels','loading','error-banner','coin-count','minimap','map-position','interact','inventory','trade-count','palette-select','activity-status','interaction-dialog','dialog-title','dialog-eyebrow','dialog-body','dialog-actions','dialog-close','reset-demo','zoom-in','zoom-out','camera-reset'].map(id => [id, document.getElementById(id)]));
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const keys = new Set(), touchKeys = new Map(), touchStarts = new Map(), actors = [], reactions = [];
let state = createState(layout), renderer, camera, controls, player, ready = false, nearest = null;
let theme = 'garden', lastTime = 0, walkTime = 0, dialogSession = null, restoreFocus = null, mapTime = 0;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#d7e4ce');
const loader = new GLTFLoader();
const paletteCanvas = document.createElement('canvas');
paletteCanvas.width = paletteCanvas.height = 16;
const paletteContext = paletteCanvas.getContext('2d');
const paletteTexture = new THREE.CanvasTexture(paletteCanvas);
paletteTexture.flipY = false;
paletteTexture.colorSpace = THREE.SRGBColorSpace;
paletteTexture.minFilter = paletteTexture.magFilter = THREE.NearestFilter;
paletteTexture.generateMipmaps = false;
const decode = value => Uint8Array.from(atob(value), character => character.charCodeAt(0));
const announce = text => { ui['activity-status'].textContent = text; };
const element = (tag, text, className) => { const node = document.createElement(tag); if (text) node.textContent = text; if (className) node.className = className; return node; };

function updatePalette() {
  const palette = buildPalette(data.catalog, theme, true);
  const pixels = new ImageData(16, 16);
  for (let texel = 0; texel < 256; texel++) pixels.data.set(palette[(texel + 1) % 256], texel * 4);
  paletteContext.putImageData(pixels, 0, 0);
  paletteTexture.needsUpdate = true;
  if (ready) drawMinimap();
}

function materialize(root, character = false) {
  root.traverse(object => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = !character;
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      if (material.map) material.map = paletteTexture;
      if (material.emissiveMap) material.emissiveMap = paletteTexture;
      material.needsUpdate = true;
    }
  });
  return root;
}

async function parseModel(modelId) {
  const model = data.models.find(entry => entry.id === modelId);
  if (!model) throw new Error(`Missing voxel asset: ${modelId}`);
  const bytes = decode(model.glb);
  return (await loader.parseAsync(bytes.buffer, '')).scene;
}

async function makeActor(id, modelId, name, position, yaw, isPlayer = false) {
  const root = materialize(await parseModel(modelId), true);
  root.position.fromArray(position);
  root.rotation.y = yaw;
  const joints = Object.fromEntries(['head','torso','arm_left','arm_right','leg_left','leg_right'].map(part => {
    const joint = root.getObjectByName(part);
    if (!joint || !joint.userData.rigid_joint) throw new Error(`Character ${modelId} is missing its ${part} rigid pivot.`);
    return [part, joint];
  }));
  scene.add(root);
  const label = element('div', name, `name-label${isPlayer ? ' player-label' : ''}`);
  ui['world-labels'].append(label);
  const actor = { id, root, joints, label, height: new THREE.Box3().setFromObject(root).getSize(new THREE.Vector3()).y, isPlayer, name };
  actors.push(actor);
  return actor;
}

function resize() {
  if (!renderer) return;
  const width = ui['world-wrap'].clientWidth, height = ui['world-wrap'].clientHeight;
  renderer.setSize(width, height, false);
  const aspect = width / height;
  const halfHeight = Math.max(7.6,9/aspect);
  camera.left = -halfHeight * aspect;
  camera.right = halfHeight * aspect;
  camera.top = halfHeight;
  camera.bottom = -halfHeight;
  camera.updateProjectionMatrix();
}

function resetCamera() {
  camera.position.set(8.4, 11.5, 13.5);
  camera.zoom = 1;
  controls.target.set(0, 0.2, 0.2);
  camera.lookAt(controls.target);
  camera.updateProjectionMatrix();
  controls.update();
}

function setButtonText() {
  const station = nearest;
  ui.interact.disabled = !ready || !station;
  ui.interact.replaceChildren(document.createTextNode(station ? station.type === 'market' ? 'Visit the Night Market ' : `Talk to ${station.name} ` : 'Walk up to a neighbor '), element('kbd', 'E'));
  for (const actor of actors) actor.label.classList.toggle('nearby', station?.id === actor.id);
  const marketLabel = document.getElementById('market-label');
  if (marketLabel) marketLabel.classList.toggle('nearby', station?.type === 'market');
}

function renderPocket() {
  ui['coin-count'].textContent = String(state.coins);
  ui.inventory.replaceChildren();
  const symbols = { seed_token: '✿', common_card: '▧', rare_card: '◆', epic_card: '✦' };
  for (const [id, label] of Object.entries(ITEM_LABELS)) {
    const item = element('li');
    item.append(element('span', symbols[id]), element('span', label), element('strong', String(state.inventory[id])));
    ui.inventory.append(item);
  }
  ui['trade-count'].textContent = state.trades ? `${state.trades} ${state.trades === 1 ? 'trade' : 'trades'} made. Your collection is growing.` : 'No trades yet. A new collection awaits.';
}

function clearDialogContent() {
  ui['dialog-body'].replaceChildren();
  ui['dialog-actions'].replaceChildren();
  ui['dialog-actions'].className = 'dialog-actions';
}

function dialogButton(text, callback, primary = false) {
  const button = element('button', text, primary ? 'primary-action' : '');
  button.type = 'button';
  button.addEventListener('click', callback);
  ui['dialog-actions'].append(button);
  return button;
}

function openDialog(session, title, eyebrow) {
  keys.clear(); touchKeys.clear(); touchStarts.clear();
  for (const button of document.querySelectorAll('[data-move]')) button.classList.remove('active');
  restoreFocus = document.activeElement;
  dialogSession = session;
  ui['dialog-title'].textContent = title;
  ui['dialog-eyebrow'].textContent = eyebrow;
  clearDialogContent();
  ui['interaction-dialog'].showModal();
}

function renderConversation() {
  clearDialogContent();
  const session = dialogSession;
  const lines = session.station.dialogue;
  ui['dialog-body'].append(element('p', lines[session.line], 'dialog-copy'));
  const meta = element('div', '', 'neighbor-meta');
  meta.append(element('span', 'Local neighbor'), element('span', `${session.line + 1} / ${lines.length}`));
  ui['dialog-body'].append(meta);
  dialogButton('Send a little 💚', () => { showReaction('heart', session.station.id); announce(`You shared a heart with ${session.station.name}.`); });
  if (session.line < lines.length - 1) dialogButton('Keep talking', () => { session.line++; renderConversation(); ui['dialog-actions'].lastElementChild.focus(); }, true);
  else dialogButton('See you around', closeDialog, true);
}

function renderMarket() {
  clearDialogContent();
  ui['dialog-eyebrow'].textContent = 'BLACK MARKET · GAME COLLECTIBLES';
  ui['dialog-body'].append(element('p', 'A small after-hours exchange. Trade collectible cards with the game coins in your pocket.', 'trade-note'));
  const list = element('div', '', 'offer-list');
  for (const offer of OFFERS) {
    const preview = previewTrade(state, offer.id);
    const card = element('button', '', 'offer-card');
    card.type = 'button'; card.dataset.rarity = offer.rarity;
    const text = element('span');
    text.append(element('strong', offer.label), element('small', !preview.ok ? preview.reason : offer.stock !== null ? `${offer.rarity.toUpperCase()} · ${state.stock[offer.id]} left` : 'ONE SEED TOKEN'));
    card.append(element('span', offer.id === 'sell_seed' ? '✿' : offer.rarity === 'epic' ? '✦' : offer.rarity === 'rare' ? '◆' : '▧', 'offer-symbol'), text,
      element('span', offer.coins < 0 ? `${-offer.coins} coins` : `+${offer.coins} coins`, 'offer-cost'));
    card.disabled = !preview.ok;
    card.addEventListener('click', () => { dialogSession.offerId = offer.id; renderTradeOffer(); ui['dialog-actions'].lastElementChild.focus(); });
    list.append(card);
  }
  ui['dialog-body'].append(list, element('p', `Your pocket: ${state.coins} game coins. This is a fictional local exchange; no payments or online trading.`, 'trade-note'));
  dialogButton('Back to the street', closeDialog, true);
}

function renderTradeOffer() {
  clearDialogContent();
  const offer = OFFERS.find(entry => entry.id === dialogSession.offerId);
  const preview = previewTrade(state, offer.id);
  ui['dialog-body'].append(element('p', offer.description, 'dialog-copy'));
  const summary = element('div', '', 'trade-summary');
  summary.append(element('p', offer.coins < 0 ? `You give: ${-offer.coins} game coins` : `You give: 1 ${ITEM_LABELS[offer.item].toLowerCase()}`),
    element('p', offer.coins < 0 ? `You receive: 1 ${ITEM_LABELS[offer.item].toLowerCase()}` : `You receive: ${offer.coins} game coins`),
    element('p', preview.ok ? `Coins after the trade: ${preview.coinsAfter}` : preview.reason));
  ui['dialog-body'].append(summary);
  dialogButton('Cancel', () => { dialogSession.offerId = null; renderMarket(); ui['dialog-actions'].lastElementChild.focus(); });
  const confirm = dialogButton('Confirm trade', () => {
    if (!dialogSession || nearestStation(state.player, layout)?.type !== 'market') { announce('Visit the market to trade.'); closeDialog(); return; }
    const result = completeTrade(state, offer.id, layout);
    if (!result.ok) { announce(result.reason); renderTradeOffer(); return; }
    state = result.state;
    renderPocket();
    const successMessage = `Trade complete. ${offer.coins < 0 ? `Added one ${ITEM_LABELS[offer.item].toLowerCase()}` : 'Traded one seed token'}; ${state.coins} game coins remain.`;
    dialogSession.offerId = null;
    renderMarket();
    ui['dialog-actions'].lastElementChild.focus();
    showReaction('sparkles');
    announce(successMessage);
  }, true);
  confirm.disabled = !preview.ok;
}

function closeDialog() { ui['interaction-dialog'].close(); }
function interact() {
  if (!ready || ui['interaction-dialog'].open) return;
  nearest = nearestStation(state.player, layout);
  if (!nearest) { announce('Walk a little closer to a neighbor or the Night Market.'); return; }
  if (nearest.type === 'market') {
    openDialog({ type: 'market', station: nearest, offerId: null }, nearest.name, 'BLACK MARKET · GAME COLLECTIBLES');
    renderMarket();
  } else {
    openDialog({ type: 'neighbor', station: nearest, line: 0 }, nearest.name, 'HELLO, NEIGHBOR');
    renderConversation();
    announce(`Talking with ${nearest.name}.`);
  }
  ui['dialog-close'].focus();
}

const emoji = { wave: '👋', heart: '💚', sparkles: '✨', smile: '😄' };
function reactionForActor(actor, symbol) {
  const label = element('div', symbol, 'reaction-label');
  ui['reaction-labels'].append(label);
  reactions.push({ actor, label, expires: performance.now() + 2800 });
}
function showReaction(id, neighborId = null) {
  if (!ready) return;
  reactionForActor(player, emoji[id]);
  const station = neighborId ? layout.neighbors.find(entry => entry.id === neighborId) : nearestStation(state.player, layout);
  if (station && station.type !== 'market') {
    const neighbor = actors.find(actor => actor.id === station.id);
    if (neighbor) reactionForActor(neighbor, id === 'wave' ? '👋' : id === 'heart' ? '💚' : '😄');
    announce(`${station.name} returned your ${id === 'heart' ? 'heart' : id === 'wave' ? 'wave' : 'good energy'}.`);
  } else announce('You sent a little good energy into the neighborhood.');
}

function drawMinimap() {
  const canvas = ui.minimap, context = canvas.getContext('2d'), width = canvas.width, height = canvas.height;
  const padding = 12, sx = (width - padding * 2) / (layout.bounds.maxX - layout.bounds.minX), sz = (height - padding * 2) / (layout.bounds.maxZ - layout.bounds.minZ);
  const point = (x, z) => [padding + (x - layout.bounds.minX) * sx, padding + (z - layout.bounds.minZ) * sz];
  context.clearRect(0, 0, width, height);
  context.fillStyle = '#e5edcf'; context.fillRect(0, 0, width, height);
  context.fillStyle = '#f5e7c4'; context.fillRect(padding, point(0, -1.7)[1], width - padding * 2, 2.3 * sz);
  context.fillRect(point(-0.8, 0)[0], point(0, -1.7)[1], 1.6 * sx, point(0, 4.3)[1] - point(0, -1.7)[1]);
  for (const blocker of layout.blockers) {
    const [x, z] = point(blocker.minX, blocker.minZ);
    const colors = { chef_home:'#dbb581', artist_home:'#79bfc0', robot_lab:'#7298bc', party_home:'#d288a4', night_market:'#9b7356' };
    context.fillStyle = colors[blocker.id] ?? '#a5b98b';
    context.fillRect(x, z, (blocker.maxX - blocker.minX) * sx, (blocker.maxZ - blocker.minZ) * sz);
  }
  context.font = 'bold 8px system-ui'; context.textAlign = 'center';
  for (const neighbor of layout.neighbors) {
    const [x, z] = point(neighbor.position[0], neighbor.position[2]);
    context.fillStyle = '#fafaf0'; context.beginPath(); context.arc(x,z,5,0,Math.PI*2); context.fill();
    context.strokeStyle = '#819d6a'; context.lineWidth = 1.5; context.stroke();
    context.fillStyle = '#52664e'; context.fillText(neighbor.name, x, z + 14);
  }
  const [mx, mz] = point(layout.market.position[0], layout.market.position[2]);
  context.fillStyle = '#c44b80'; context.fillRect(mx - 4, mz - 4, 8, 8);
  context.fillStyle = '#85536a'; context.fillText('MARKET', mx, mz + 14);
  const [px, pz] = point(state.player.x, state.player.z);
  context.fillStyle = '#218f89'; context.beginPath(); context.arc(px,pz,5.5,0,Math.PI*2); context.fill();
  context.strokeStyle = '#fbfff7'; context.lineWidth = 2; context.stroke();
  context.save(); context.translate(px,pz); context.rotate(-state.player.yaw); context.fillStyle = '#218f89'; context.beginPath(); context.moveTo(0,8); context.lineTo(-3,4); context.lineTo(3,4); context.fill(); context.restore();
  ui['map-position'].textContent = `Your position: ${state.player.x.toFixed(1)} east, ${(-state.player.z).toFixed(1)} north. ${nearest ? `Nearby: ${nearest.name}.` : ''}`;
}

function projectLabel(label, position) {
  const vector = position.clone().project(camera);
  const width = ui['world-wrap'].clientWidth, height = ui['world-wrap'].clientHeight;
  label.hidden = vector.z < -1 || vector.z > 1 || Math.abs(vector.x) > 1.15 || Math.abs(vector.y) > 1.2;
  label.style.left = `${(vector.x * .5 + .5) * width}px`;
  label.style.top = `${(-vector.y * .5 + .5) * height}px`;
}

function animate(time) {
  requestAnimationFrame(animate);
  if (!ready || document.hidden) { lastTime = time; return; }
  const seconds = Math.min((time - lastTime) / 1000 || 0, .05); lastTime = time;
  const active = direction => [...keys].some(code => keyDirections[code] === direction) || [...touchKeys.values()].includes(direction);
  const input = ui['interaction-dialog'].open ? { x: 0, z: 0 } : { x: Number(active('right')) - Number(active('left')), z: Number(active('down')) - Number(active('up')) };
  const previous = state.player;
  state.player = movePlayer(state.player, input, seconds, layout);
  const moved = Math.hypot(state.player.x - previous.x, state.player.z - previous.z) > .0001;
  walkTime += moved ? seconds * 11 : 0;
  const stride = moved && !reducedMotion.matches ? Math.sin(walkTime) * .55 : 0;
  player.joints.leg_left.rotation.x = stride;
  player.joints.leg_right.rotation.x = -stride;
  player.joints.arm_left.rotation.x = -stride * .6;
  player.joints.arm_right.rotation.x = stride * .6;
  player.root.position.set(state.player.x, state.player.y + (moved && !reducedMotion.matches ? Math.abs(Math.sin(walkTime)) * .018 : 0), state.player.z);
  // Instant heading keeps the rendered cube footprint identical to collision.
  // Interpolating through a wider 45-degree pose could clip a nearby wall.
  player.root.rotation.y = state.player.yaw;
  player.joints.head.rotation.y = 0;
  for (const actor of actors.filter(actor => !actor.isPlayer)) {
    const nearby = Math.hypot(state.player.x - actor.root.position.x, state.player.z - actor.root.position.z) < 2.1;
    const desired = nearby ? Math.atan2(state.player.x - actor.root.position.x, state.player.z - actor.root.position.z) : 0;
    actor.root.rotation.y += Math.atan2(Math.sin(desired - actor.root.rotation.y), Math.cos(desired - actor.root.rotation.y)) * Math.min(1, seconds * 3);
    actor.joints.head.rotation.y = !reducedMotion.matches ? Math.sin(time * .0008 + actors.indexOf(actor)) * .045 : 0;
  }
  const nextNearest = nearestStation(state.player, layout);
  if (nextNearest?.id !== nearest?.id) { nearest = nextNearest; setButtonText(); }
  else nearest = nextNearest;
  // Keep the entire small neighborhood in view, with a gentle player bias.
  if (!controls.dragging) {
    const follow = new THREE.Vector3(state.player.x * .16, .2, state.player.z * .08);
    const delta = follow.sub(controls.target).multiplyScalar(reducedMotion.matches ? 1 : Math.min(1, seconds * 2));
    controls.target.add(delta); camera.position.add(delta);
  }
  controls.update();
  scene.updateMatrixWorld(true);
  for (const actor of actors) projectLabel(actor.label, actor.root.position.clone().add(new THREE.Vector3(0, actor.height + .15, 0)));
  projectLabel(document.getElementById('market-label'), new THREE.Vector3(layout.market.position[0], 2.0, 2.85));
  for (let index = reactions.length - 1; index >= 0; index--) {
    const reaction = reactions[index];
    if (time > reaction.expires) { reaction.label.remove(); reactions.splice(index, 1); }
    else projectLabel(reaction.label, reaction.actor.root.position.clone().add(new THREE.Vector3(0, reaction.actor.height + .55, 0)));
  }
  if (time - mapTime > 100) { drawMinimap(); mapTime = time; }
  renderer.render(scene, camera);
}

const keyDirections = { KeyW:'up', ArrowUp:'up', KeyS:'down', ArrowDown:'down', KeyA:'left', ArrowLeft:'left', KeyD:'right', ArrowRight:'right' };
window.addEventListener('keydown', event => {
  if (ui['interaction-dialog'].open || event.ctrlKey || event.metaKey || event.altKey || ['INPUT','SELECT','TEXTAREA'].includes(event.target.tagName)) return;
  if (keyDirections[event.code]) { event.preventDefault(); keys.add(event.code); }
  if (event.code === 'KeyE' && !event.repeat) { event.preventDefault(); interact(); }
});
window.addEventListener('keyup', event => { if (keyDirections[event.code]) keys.delete(event.code); });
window.addEventListener('blur', () => { keys.clear(); touchKeys.clear(); touchStarts.clear(); for (const button of document.querySelectorAll('[data-move]')) button.classList.remove('active'); });
document.addEventListener('visibilitychange', () => { if (document.hidden) { keys.clear(); touchKeys.clear(); touchStarts.clear(); } });
for (const button of document.querySelectorAll('[data-move]')) {
  button.addEventListener('pointerdown', event => {
    if (!ready || ui['interaction-dialog'].open) return;
    event.preventDefault(); button.setPointerCapture(event.pointerId); touchKeys.set(event.pointerId, button.dataset.move); touchStarts.set(event.pointerId,{x:state.player.x,z:state.player.z}); button.classList.add('active');
  });
  const release = event => {
    const direction = touchKeys.get(event.pointerId), start = touchStarts.get(event.pointerId);
    touchKeys.delete(event.pointerId); touchStarts.delete(event.pointerId); button.classList.remove('active');
    // A quick tap makes a visible step. Holding keeps continuous movement and
    // release adds no extra step; cancellation never moves the character.
    if(event.type==='pointerup' && direction && start && ready && !ui['interaction-dialog'].open
      && Math.hypot(state.player.x-start.x,state.player.z-start.z)<.025) {
      state.player = movePlayer(state.player,{x:Number(direction==='right')-Number(direction==='left'),z:Number(direction==='down')-Number(direction==='up')},.2,layout);
    }
  };
  button.addEventListener('pointerup', release); button.addEventListener('pointercancel', release); button.addEventListener('lostpointercapture', release);
  // Enter and Space move one small step when using the accessible controls.
  button.addEventListener('click', event => {
    if (event.detail !== 0 || !ready || ui['interaction-dialog'].open) return;
    const direction = button.dataset.move;
    state.player = movePlayer(state.player, { x: Number(direction === 'right') - Number(direction === 'left'), z: Number(direction === 'down') - Number(direction === 'up') }, .18, layout);
  });
}
for (const button of document.querySelectorAll('[data-emoji]')) button.addEventListener('click', () => showReaction(button.dataset.emoji));
ui.interact.addEventListener('click', interact);
ui['dialog-close'].addEventListener('click', closeDialog);
ui['interaction-dialog'].addEventListener('close', () => { dialogSession = null; keys.clear(); touchKeys.clear(); touchStarts.clear(); (restoreFocus?.isConnected ? restoreFocus : ui['world-canvas']).focus({ preventScroll:true }); });
ui['reset-demo'].addEventListener('click', () => {
  if (!ready) return;
  openDialog({ type:'reset' }, 'Start a fresh visit?', 'A NEW DAY ON SEEDLING LANE');
  ui['dialog-body'].append(element('p', 'Return home with 60 game coins and three seed tokens. This visit’s collected cards and trades will reset.', 'dialog-copy'));
  dialogButton('Keep this visit', closeDialog);
  dialogButton('Start fresh', () => { state = createState(layout); renderPocket(); resetCamera(); reactions.splice(0).forEach(reaction => reaction.label.remove()); announce('Welcome back. Your fresh visit is ready.'); closeDialog(); }, true);
});
for (const [id, preset] of Object.entries(data.catalog.presets)) { const option = element('option', preset.label); option.value = id; ui['palette-select'].append(option); }
ui['palette-select'].value = theme;
ui['palette-select'].addEventListener('change', () => { theme = ui['palette-select'].value; updatePalette(); announce(`Neighborhood colors: ${data.catalog.presets[theme].label}.`); });
ui['zoom-in'].addEventListener('click', () => { if (!ready) return; camera.zoom = Math.min(controls.maxZoom, camera.zoom * 1.2); camera.updateProjectionMatrix(); });
ui['zoom-out'].addEventListener('click', () => { if (!ready) return; camera.zoom = Math.max(controls.minZoom, camera.zoom / 1.2); camera.updateProjectionMatrix(); });
ui['camera-reset'].addEventListener('click', () => { if (ready) resetCamera(); });

async function start() {
  updatePalette(); renderPocket();
  try {
    renderer = new THREE.WebGLRenderer({ canvas:ui['world-canvas'], antialias:true, alpha:false, powerPreference:'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.12;
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
    camera = new THREE.OrthographicCamera(-10,10,7.6,-7.6,.1,65);
    controls = new OrbitControls(camera, ui['world-canvas']);
    controls.enablePan = false; controls.enableDamping = !reducedMotion.matches;
    controls.dampingFactor = .08; controls.minZoom = .8; controls.maxZoom = 2.5;
    controls.minPolarAngle = .35; controls.maxPolarAngle = 1.15;
    controls.addEventListener('start', () => { controls.dragging = true; });
    controls.addEventListener('end', () => { controls.dragging = false; });
    const ambient = new THREE.HemisphereLight('#fff8de','#749666',2.05); scene.add(ambient);
    const sun = new THREE.DirectionalLight('#fff4d6',3.1); sun.position.set(-8,12,9); sun.castShadow = true;
    sun.shadow.mapSize.set(1024,1024); Object.assign(sun.shadow.camera,{left:-9,right:9,top:9,bottom:-9,near:1,far:40});
    sun.shadow.bias = -.0006; sun.shadow.normalBias = .035; scene.add(sun);
    scene.add(materialize(await parseModel('neighbor_commons')));
    player = await makeActor('player','rasta_grower','You',layout.player.spawn,0,true);
    await Promise.all(layout.neighbors.map(neighbor => makeActor(neighbor.id, neighbor.characterId, neighbor.name, neighbor.position, neighbor.yaw ?? 0)));
    // Display the exact voxel TCG cards if the optional collectible GLBs are supplied.
    for (const spot of layout.displaySpots ?? []) {
      if (!data.models.some(model => model.id === spot.id)) continue;
      const card = materialize(await parseModel(spot.id));
      const box = new THREE.Box3().setFromObject(card);
      const size = box.getSize(new THREE.Vector3());
      const scale = .56 / Math.max(size.x,size.y,size.z);
      card.scale.setScalar(scale); card.position.fromArray(spot.position); card.rotation.y = .05;
      scene.add(card);
    }
    const marketLabel = element('div','Night Market','name-label market-label'); marketLabel.id = 'market-label'; ui['world-labels'].append(marketLabel);
    resetCamera(); resize(); new ResizeObserver(resize).observe(ui['world-wrap']);
    ready = true; ui.loading.hidden = true; setButtonText(); drawMinimap();
    ui['world-canvas'].focus({ preventScroll:true });
    requestAnimationFrame(animate);
  } catch (error) {
    ui.loading.hidden = true; ui['error-banner'].hidden = false;
    ui['error-banner'].textContent = `The neighborhood could not start. ${error.message} Try reloading in a browser with WebGL enabled.`;
    console.error(error);
  }
}
start();
