// Greenbox economy engine: pure, deterministic, no DOM. The UI and tests drive it.
// One block = one game second. Each block's BUD reward is split across every active grower
// by their share of total network potency (BigCoin's pro-rata hashpower rule).
import { ROOMS, STRAINS, COSMETICS, BADGES } from './content.js';

export const SAVE_VERSION = 1;

export const DEFAULT_CONFIG = {
  blockReward: 2.5, // BUD per block at launch, as in BigCoin
  halvingInterval: 43200, // blocks; 12 hours at 1 block/s (BigCoin: 4.2M blocks, about 51 days)
  burnShare: 0.75, // of every purchase; the rest goes to the treasury
  sellBackShare: 0.2, // of the mint price, refunded from the treasury when a strain is sold back
  roomCooldown: 3600, // blocks between room upgrades (BigCoin: 24h)
  strainLock: 1800, // blocks a planted strain stays locked (BigCoin: 24h)
  startingBots: 40,
  joinChance: 0.004, // per block at launch hype; decays with hypeHalfLife
  joinFloor: 0.08, // fraction of joinChance that never decays
  hypeHalfLife: 21600,
  quitChance: 0.0004, // per bot decision
  halvingShock: 12, // quit multiplier for the period right after a halving
  halvingShockBlocks: 3600,
  collectorChance: 0.003, // per block, a network grower tries to buy a limited cosmetic
  maxCatchUp: 43200, // offline blocks simulated on load
};

const strainIndex = Object.fromEntries(STRAINS.map((s, i) => [s.id, i]));
const BOT_NAMES = ['Mary', 'Jay', 'Herb', 'Sativa Sam', 'Indie', 'Kush Kid', 'Dank', 'Ganja Gran', 'Bud', 'Skunky',
  'Rasta Ray', 'Leafy', 'Trichome Tom', 'Dro', 'Chronic Chris', 'Hash Hal', 'Pheno Phil', 'Terp Tess', 'Kief Kim', 'Roach'];

// Mulberry32: small seeded RNG whose state lives in the save so runs replay exactly.
function rand(state) {
  let t = (state.rng = (state.rng + 0x6d2b79f5) >>> 0);
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

const ok = (message) => ({ ok: true, message });
const fail = (message) => ({ ok: false, message });

export function supplyCap(cfg) {
  return cfg.blockReward * cfg.halvingInterval * 2;
}

export function rewardAt(cfg, height) {
  const era = Math.floor(height / cfg.halvingInterval);
  return era > 52 ? 0 : cfg.blockReward / 2 ** era;
}

export function createGame(seed = 1, overrides = {}) {
  const cfg = { ...DEFAULT_CONFIG, ...overrides };
  const state = {
    version: SAVE_VERSION,
    cfg,
    rng: seed >>> 0,
    height: 0,
    token: { minted: 0, burned: 0, treasury: 0, dormant: 0 },
    player: {
      wallet: 0, pending: 0, room: 0, roomReadyAt: 0,
      slots: [], inventory: [], nextUid: 1,
      claimedTotal: 0, earnedTotal: 0, spent: 0, minted: 0, mintedIds: [], cosmeticsBought: 0, badges: [],
    },
    bots: [],
    cosmeticsSold: {},
    stats: { joins: 0, quits: 0 },
    log: [],
  };
  plant(state.player, 'strain', 'bagseed', 0);
  state.player.mintedIds.push('bagseed');
  for (let i = 0; i < cfg.startingBots; i++) addBot(state);
  log(state, `Season launched with ${cfg.startingBots + 1} growers. You got a free Bagseed.`);
  return state;
}

function log(state, message) {
  state.log.unshift({ h: state.height, message });
  if (state.log.length > 60) state.log.length = 60;
}

function addBot(state) {
  const n = state.stats.joins++;
  state.bots.push({
    name: `${BOT_NAMES[n % BOT_NAMES.length]} #${n + 1}`,
    balance: 0, room: 0, roomReadyAt: 0, items: [strainIndex.bagseed],
    potency: STRAINS[strainIndex.bagseed].potency, watts: STRAINS[strainIndex.bagseed].watts,
    active: true,
    // Diligence: how often the bot checks in to reinvest, from every minute to about once an hour.
    every: Math.floor(60 + rand(state) ** 2 * 3600),
    nextAct: state.height + 1 + Math.floor(rand(state) * 600),
    reserve: rand(state) * 0.3, // fraction of balance kept unspent
  });
}

function plant(owner, kind, id, height) {
  owner.slots.push({ uid: owner.nextUid++, kind, id, plantedAt: height });
}

// ---- Derived values ----

export function playerPotency(state) {
  let total = 0;
  for (const s of state.player.slots) if (s.kind === 'strain') total += STRAINS[strainIndex[s.id]].potency;
  return total;
}

export function playerWatts(state) {
  let total = 0;
  for (const s of state.player.slots) if (s.kind === 'strain') total += STRAINS[strainIndex[s.id]].watts;
  return total;
}

export function networkPotency(state) {
  let total = playerPotency(state);
  for (const b of state.bots) if (b.active) total += b.potency;
  return total;
}

export function circulating(state) {
  const t = state.token;
  return t.minted - t.burned - t.treasury;
}

export function summary(state) {
  const cfg = state.cfg;
  const mine = playerPotency(state);
  const net = networkPotency(state);
  const reward = rewardAt(cfg, state.height);
  const share = net > 0 ? mine / net : 0;
  const room = ROOMS[state.player.room];
  return {
    height: state.height,
    reward,
    era: Math.floor(state.height / cfg.halvingInterval),
    nextHalvingIn: cfg.halvingInterval - (state.height % cfg.halvingInterval),
    cap: supplyCap(cfg),
    potency: mine,
    watts: playerWatts(state),
    networkPotency: net,
    share,
    perHour: share * reward * 3600,
    room,
    slotsUsed: state.player.slots.length,
    activeGrowers: 1 + state.bots.filter((b) => b.active).length,
    roomCooldown: Math.max(0, state.player.roomReadyAt - state.height),
    circulating: circulating(state),
  };
}

// ---- Simulation ----

export function advance(state, blocks) {
  const n = Math.max(0, Math.floor(blocks));
  for (let i = 0; i < n; i++) stepBlock(state);
}

function stepBlock(state) {
  const cfg = state.cfg;
  const t = state.token;
  const cap = supplyCap(cfg);
  const reward = Math.min(rewardAt(cfg, state.height), cap - t.minted);
  const net = networkPotency(state);
  if (reward > 0 && net > 0) {
    const mine = playerPotency(state);
    const playerCut = (reward * mine) / net;
    state.player.pending += playerCut;
    state.player.earnedTotal += playerCut;
    for (const b of state.bots) if (b.active) b.balance += (reward * b.potency) / net;
    t.minted += reward;
  }
  state.height++;
  if (state.height % cfg.halvingInterval === 0) {
    log(state, `Halving! Block reward is now ${rewardAt(cfg, state.height)} BUD.`);
  }

  // Network churn: hype brings new growers early on, halvings shake out the weak.
  const hype = cfg.joinFloor + (1 - cfg.joinFloor) * 0.5 ** (state.height / cfg.hypeHalfLife);
  if (rand(state) < cfg.joinChance * hype * (reward > 0 ? 1 : 0)) addBot(state);
  const shocked = state.height % cfg.halvingInterval < cfg.halvingShockBlocks && state.height >= cfg.halvingInterval;
  for (const b of state.bots) {
    if (!b.active || state.height < b.nextAct) continue;
    b.nextAct = state.height + b.every;
    if (rand(state) < cfg.quitChance * (shocked ? cfg.halvingShock : 1)) {
      b.active = false;
      t.dormant += b.balance;
      state.stats.quits++;
      continue;
    }
    botInvest(state, b);
  }
  // Collectors in the network chip away at limited cosmetic drops.
  if (rand(state) < cfg.collectorChance && state.bots.length) {
    const b = state.bots[Math.floor(rand(state) * state.bots.length)];
    const open = COSMETICS.filter((c) => c.supply !== null && (state.cosmeticsSold[c.id] || 0) < c.supply);
    const c = open[Math.floor(rand(state) * open.length)];
    if (b.active && c && b.balance >= c.cost) {
      b.balance -= c.cost;
      spend(state, c.cost);
      state.cosmeticsSold[c.id] = (state.cosmeticsSold[c.id] || 0) + 1;
    }
  }
  checkBadges(state);
}

function spend(state, amount) {
  const burn = amount * state.cfg.burnShare;
  state.token.burned += burn;
  state.token.treasury += amount - burn;
}

// Greedy bot: buy the most potency per BUD that fits, upgrade the room when full, replace the weakest strain at the cap.
function botInvest(state, b) {
  const cfg = state.cfg;
  for (let guard = 0; guard < 50; guard++) {
    const budget = b.balance * (1 - b.reserve);
    const room = ROOMS[b.room];
    const freeSlots = room.slots - b.items.length;
    const freeWatts = room.watts - b.watts;
    let best = -1;
    let bestScore = 0;
    for (let i = 1; i < STRAINS.length; i++) {
      const s = STRAINS[i];
      if (s.cost > budget) continue;
      if (freeSlots > 0 && s.watts <= freeWatts) {
        const score = s.potency / s.cost;
        if (score > bestScore) { best = i; bestScore = score; }
      }
    }
    if (best >= 0) {
      const s = STRAINS[best];
      b.balance -= s.cost;
      spend(state, s.cost);
      b.items.push(best);
      b.potency += s.potency;
      b.watts += s.watts;
      continue;
    }
    const next = ROOMS[b.room + 1];
    if (next && state.height >= b.roomReadyAt && next.cost <= budget && (freeSlots <= 1 || freeWatts < 30)) {
      b.balance -= next.cost;
      spend(state, next.cost);
      b.room++;
      b.roomReadyAt = state.height + cfg.roomCooldown;
      continue;
    }
    // Room maxed out (or waiting on cooldown): swap the weakest strain for the best one that fits.
    let weakest = 0;
    for (let k = 1; k < b.items.length; k++) if (STRAINS[b.items[k]].potency < STRAINS[b.items[weakest]].potency) weakest = k;
    const w = STRAINS[b.items[weakest]];
    let swap = -1;
    for (let i = STRAINS.length - 1; i > b.items[weakest]; i--) {
      const s = STRAINS[i];
      if (s.cost <= budget && b.watts - w.watts + s.watts <= room.watts && s.potency > w.potency * 2) { swap = i; break; }
    }
    if (freeSlots > 0 || swap < 0) return;
    const refund = Math.min(state.token.treasury, w.cost * cfg.sellBackShare);
    state.token.treasury -= refund;
    b.balance += refund;
    b.items.splice(weakest, 1);
    b.potency -= w.potency;
    b.watts -= w.watts;
  }
}

function checkBadges(state) {
  const p = state.player;
  for (const badge of BADGES) {
    if (!p.badges.includes(badge.id) && badge.test(p)) {
      p.badges.push(badge.id);
      log(state, `Badge earned: ${badge.name}.`);
    }
  }
}

// ---- Player actions. Each returns { ok, message } and never throws on bad input. ----

export function claim(state) {
  const p = state.player;
  if (p.pending <= 0) return fail('Nothing to harvest yet.');
  const amount = p.pending;
  p.wallet += amount;
  p.claimedTotal += amount;
  p.pending = 0;
  checkBadges(state);
  return ok(`Harvested ${amount.toFixed(3)} BUD.`);
}

function pay(state, amount) {
  const p = state.player;
  if (amount > p.wallet + 1e-9) return false;
  p.wallet = Math.max(0, p.wallet - amount);
  p.spent += amount;
  spend(state, amount);
  return true;
}

export function canFit(state, strainId) {
  const s = STRAINS[strainIndex[strainId]];
  const room = ROOMS[state.player.room];
  if (state.player.slots.length >= room.slots) return 'No free slot. Upgrade your room or sell something.';
  if (playerWatts(state) + s.watts > room.watts) return `Not enough power (needs ${s.watts} W).`;
  return null;
}

// Minting auto-plants when it fits, like BigCoin auto-staking; otherwise the seed waits in inventory.
export function buyStrain(state, strainId) {
  const s = STRAINS[strainIndex[strainId]];
  if (!s) return fail('Unknown strain.');
  if (s.starter) return fail('Bagseed is the free starter and cannot be bought.');
  const p = state.player;
  if (!pay(state, s.cost)) return fail(`You need ${s.cost} BUD.`);
  p.minted++;
  if (!p.mintedIds.includes(s.id)) p.mintedIds.push(s.id);
  const problem = canFit(state, s.id);
  if (problem) {
    p.inventory.push({ uid: p.nextUid++, kind: 'strain', id: s.id });
    checkBadges(state);
    return ok(`Bought ${s.name}. Stored in inventory: ${problem}`);
  }
  plant(p, 'strain', s.id, state.height);
  checkBadges(state);
  return ok(`Planted ${s.name}. Locked for ${state.cfg.strainLock} blocks.`);
}

export function buyCosmetic(state, cosmeticId) {
  const c = COSMETICS.find((x) => x.id === cosmeticId);
  if (!c) return fail('Unknown cosmetic.');
  const sold = state.cosmeticsSold[c.id] || 0;
  if (c.supply !== null && sold >= c.supply) return fail(`${c.name} is sold out.`);
  const p = state.player;
  if (p.slots.length >= ROOMS[p.room].slots) return fail('No free slot for decorations.');
  if (!pay(state, c.cost)) return fail(`You need ${c.cost} BUD.`);
  state.cosmeticsSold[c.id] = sold + 1;
  p.cosmeticsBought++;
  plant(p, 'cosmetic', c.id, state.height);
  checkBadges(state);
  return ok(`Placed ${c.name}.`);
}

export function cosmeticsLeft(state, cosmeticId) {
  const c = COSMETICS.find((x) => x.id === cosmeticId);
  return c.supply === null ? null : c.supply - (state.cosmeticsSold[c.id] || 0);
}

export function upgradeRoom(state) {
  const p = state.player;
  const next = ROOMS[p.room + 1];
  if (!next) return fail('You already own the biggest room.');
  if (state.height < p.roomReadyAt) return fail(`Contractors are busy for ${p.roomReadyAt - state.height} more blocks.`);
  if (!pay(state, next.cost)) return fail(`You need ${next.cost} BUD.`);
  p.room++;
  p.roomReadyAt = state.height + state.cfg.roomCooldown;
  log(state, `Moved into the ${next.name}.`);
  checkBadges(state);
  return ok(`Upgraded to ${next.name}: ${next.slots} slots, ${next.watts} W.`);
}

export function lockLeft(state, slot) {
  if (slot.kind !== 'strain') return 0;
  return Math.max(0, slot.plantedAt + state.cfg.strainLock - state.height);
}

// Uproot moves a strain or cosmetic back to inventory once its lock has expired.
export function uproot(state, uid) {
  const p = state.player;
  const i = p.slots.findIndex((s) => s.uid === uid);
  if (i < 0) return fail('Nothing planted there.');
  const left = lockLeft(state, p.slots[i]);
  if (left > 0) return fail(`Still rooting: locked for ${left} more blocks.`);
  const [slot] = p.slots.splice(i, 1);
  p.inventory.push({ uid: slot.uid, kind: slot.kind, id: slot.id });
  return ok('Moved to inventory.');
}

export function replant(state, uid) {
  const p = state.player;
  const i = p.inventory.findIndex((s) => s.uid === uid);
  if (i < 0) return fail('Not in inventory.');
  const item = p.inventory[i];
  if (item.kind === 'strain') {
    const problem = canFit(state, item.id);
    if (problem) return fail(problem);
  } else if (p.slots.length >= ROOMS[p.room].slots) {
    return fail('No free slot.');
  }
  p.inventory.splice(i, 1);
  p.slots.push({ uid: item.uid, kind: item.kind, id: item.id, plantedAt: state.height });
  return ok('Planted.');
}

// Selling back burns the item; the treasury refunds part of its mint price while it has funds.
export function sellBack(state, uid) {
  const p = state.player;
  const i = p.inventory.findIndex((s) => s.uid === uid);
  if (i < 0) return fail('Uproot it into inventory first.');
  const item = p.inventory[i];
  const base = item.kind === 'strain' ? STRAINS[strainIndex[item.id]].cost : COSMETICS.find((c) => c.id === item.id).cost;
  const refund = Math.min(state.token.treasury, base * state.cfg.sellBackShare);
  state.token.treasury -= refund;
  p.wallet += refund;
  p.inventory.splice(i, 1);
  return ok(`Composted it for ${refund.toFixed(2)} BUD.`);
}

// ---- Saves ----

export function serialize(state) {
  return JSON.stringify(state);
}

export function deserialize(text) {
  const state = JSON.parse(text);
  if (!state || state.version !== SAVE_VERSION) throw new Error('Unsupported save version.');
  state.cfg = { ...DEFAULT_CONFIG, ...state.cfg };
  return state;
}
