// Deterministic local game rules. The renderer never owns coins or inventory.
export const ITEM_LABELS = Object.freeze({ seed_token: 'Seed token', common_card: 'Common card', rare_card: 'Rare card', epic_card: 'Epic card' });
export const OFFERS = Object.freeze([
  Object.freeze({ id: 'common', label: 'Common card', rarity: 'common', coins: -8, item: 'common_card', amount: 1, stock: 8, description: 'A little find for your Greenbox collection.' }),
  Object.freeze({ id: 'rare', label: 'Rare card', rarity: 'rare', coins: -18, item: 'rare_card', amount: 1, stock: 4, description: 'A turquoise treasure from the neighborhood.' }),
  Object.freeze({ id: 'epic', label: 'Epic card', rarity: 'epic', coins: -32, item: 'epic_card', amount: 1, stock: 2, description: 'A raspberry gem for your collection.' }),
  Object.freeze({ id: 'sell_seed', label: 'Trade a seed token', rarity: 'common', coins: 6, item: 'seed_token', amount: -1, stock: null, description: 'Swap one game seed token for six game coins.' }),
]);

function number(value, name) { if (!Number.isFinite(value)) throw new TypeError(`${name} must be finite.`); return value; }
const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
const distance = (a, b) => Math.hypot(a.x - b[0], a.z - b[2]);

export function createState(layout) {
  const [x, y, z] = layout.player.spawn;
  return { player: { x, y, z, yaw: 0 }, coins: 60,
    inventory: { seed_token: 3, common_card: 0, rare_card: 0, epic_card: 0 },
    stock: Object.fromEntries(OFFERS.filter(offer => offer.stock !== null).map(offer => [offer.id, offer.stock])), trades: 0 };
}

export function withAvatarColliders(layout, physics) {
  const player = physics.models.rasta_grower;
  if (!player || !player.halfExtents.every(value => Number.isFinite(value) && value > 0)) throw new TypeError('Missing actual player footprint.');
  return { ...layout, player: { ...layout.player, halfExtents:player.halfExtents.map(value => value + .01) },
    neighbors:layout.neighbors.map(neighbor => ({ ...neighbor, colliderRadius:physics.models[neighbor.characterId].radius + .01 })) };
}

export function playerEnvelope(player, yaw = 0) {
  if (!player.halfExtents) return { x:player.radius, z:player.radius };
  const [x, z] = player.halfExtents;
  return { x:Math.abs(Math.cos(yaw))*x+Math.abs(Math.sin(yaw))*z, z:Math.abs(Math.sin(yaw))*x+Math.abs(Math.cos(yaw))*z };
}

export function collisionBlockers(layout) {
  return [...layout.blockers, ...layout.neighbors.map(neighbor => ({ id: `npc_${neighbor.id}`,
    minX: neighbor.position[0] - (neighbor.colliderRadius ?? .23), maxX: neighbor.position[0] + (neighbor.colliderRadius ?? .23),
    minZ: neighbor.position[2] - (neighbor.colliderRadius ?? .23), maxZ: neighbor.position[2] + (neighbor.colliderRadius ?? .23) }))];
}

export function positionAllowed(position, radius, bounds, blockers) {
  const envelope = typeof radius === 'number' ? {x:radius,z:radius} : radius;
  return position.x >= bounds.minX + envelope.x && position.x <= bounds.maxX - envelope.x
    && position.z >= bounds.minZ + envelope.z && position.z <= bounds.maxZ - envelope.z
    && !blockers.some(box => position.x > box.minX - envelope.x && position.x < box.maxX + envelope.x
      && position.z > box.minZ - envelope.z && position.z < box.maxZ + envelope.z);
}

export function movePlayer(position, input, seconds, layout) {
  const dx = number(input.x, 'Input X'), dz = number(input.z, 'Input Z');
  const magnitude = Math.hypot(dx, dz);
  if (!magnitude) return { ...position };
  // Normalize diagonals and take small steps, so a long frame cannot tunnel through a wall.
  const scale = layout.player.speed * clamp(number(seconds, 'Frame duration'), 0, 0.25) / Math.max(1, magnitude);
  const steps = Math.max(1, Math.ceil(magnitude * scale / 0.06));
  const blockers = collisionBlockers(layout), desiredYaw = Math.atan2(dx, dz);
  const next = { ...position };
  for (let step = 0; step < steps; step++) {
    // Rotate the true horizontal model envelope. Keep the current heading when a
    // turn would intersect a wall; the player can move sideways until it fits.
    if (positionAllowed(next, playerEnvelope(layout.player,desiredYaw),layout.bounds,blockers)) next.yaw = desiredYaw;
    const envelope = playerEnvelope(layout.player,next.yaw);
    const x = clamp(next.x + dx * scale / steps, layout.bounds.minX + envelope.x, layout.bounds.maxX - envelope.x);
    if (positionAllowed({ ...next, x }, envelope, layout.bounds, blockers)) next.x = x;
    const z = clamp(next.z + dz * scale / steps, layout.bounds.minZ + envelope.z, layout.bounds.maxZ - envelope.z);
    if (positionAllowed({ ...next, z }, envelope, layout.bounds, blockers)) next.z = z;
  }
  return next;
}

export function nearestStation(position, layout) {
  const stations = layout.neighbors.map(neighbor => ({ ...neighbor, type: 'neighbor', range: neighbor.interactionRadius ?? neighbor.radius ?? 1.8 }));
  stations.push({ ...layout.market, type: 'market', range: layout.market.radius });
  return stations.map(station => ({ ...station, distance: distance(position, station.position) }))
    .filter(station => station.distance <= station.range).sort((a, b) => a.distance - b.distance)[0] ?? null;
}

export function previewTrade(state, offerId) {
  const offer = OFFERS.find(entry => entry.id === offerId);
  if (!offer) return { ok: false, reason: 'That offer is unavailable.' };
  if (!Number.isSafeInteger(state.coins) || state.coins < 0
    || !Number.isSafeInteger(state.inventory[offer.item]) || state.inventory[offer.item] < 0)
    return { ok: false, reason: 'Your inventory needs a reset.' };
  if (offer.stock !== null && (!Number.isSafeInteger(state.stock[offer.id]) || state.stock[offer.id] <= 0))
    return { ok: false, reason: 'This item is sold out.' };
  if (state.coins + offer.coins < 0) return { ok: false, reason: 'You need more game coins.' };
  if (state.inventory[offer.item] + offer.amount < 0) return { ok: false, reason: 'You need a seed token to trade.' };
  if (!Number.isSafeInteger(state.coins + offer.coins) || !Number.isSafeInteger(state.inventory[offer.item] + offer.amount))
    return { ok: false, reason: 'This trade is too large.' };
  return { ok: true, offer, coinsAfter: state.coins + offer.coins, itemsAfter: state.inventory[offer.item] + offer.amount };
}

export function completeTrade(state, offerId, layout) {
  if (!layout || nearestStation(state.player, layout)?.type !== 'market')
    return { ok: false, reason: 'Visit the market to trade.', state };
  const preview = previewTrade(state, offerId);
  if (!preview.ok) return { ok: false, reason: preview.reason, state };
  const { offer } = preview;
  const next = { ...state, player: { ...state.player }, inventory: { ...state.inventory }, stock: { ...state.stock },
    coins: preview.coinsAfter, trades: state.trades + 1 };
  next.inventory[offer.item] = preview.itemsAfter;
  if (offer.stock !== null) next.stock[offer.id]--;
  return { ok: true, offer, state: next };
}
