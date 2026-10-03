// Greenbox economy engine: pure, deterministic, no DOM. The UI, forecasts and tests drive it.
// One block = one game second. Each block's BUD reward is split across every active grower
// by their share of total network potency (BigCoin's pro-rata hashpower rule).
import { ROOMS, STRAINS, COSMETICS, UTILITIES, BADGES } from './content.js';

export const SAVE_VERSION = 2;
const HOUR = 3600;

// DEMO compresses the season so halvings happen while you play. LIVE is the launch plan used by the forecasts.
export const DEMO_CONFIG = {
  blockReward: 2.5, // BUD per block at launch, as in BigCoin
  halvingInterval: 43200, // blocks; 12 hours at 1 block/s
  tick: 1, // blocks simulated per step; forecasts use bigger steps for speed
  burnShare: 0.75, // of every purchase; the rest goes to the treasury
  sellBackShare: 0.2, // of the mint price, refunded from the treasury when a strain is sold back
  roomCooldown: HOUR, // blocks between room upgrades
  strainLock: HOUR / 2, // blocks a planted strain stays locked
  waterBlocks: 4 * HOUR, // one watering keeps the room wet this long
  dryPenalty: 0.5, // potency multiplier while the room is dry
  seedlingPool: 0.15, // share of each block paid equally to new growers still in the Closet (onboarding faucet)
  seedlingDays: 7, // how long after joining a grower can draw from the seedling pool
  storageBlocks: 12 * HOUR, // the drying rack fills after this long without a harvest; later earnings spoil
  trimmerEvery: HOUR, // Auto-Trimmer harvest interval
  ledWatts: 0.75, // strain power draw with the LED Retrofit
  co2Boost: 1.1, // potency multiplier with the CO2 Generator
  unlockScale: 0, // 0 = every strain on sale from block 0; 1 = follow each strain's unlockHours
  startingBots: 40,
  cohort: 1, // players represented by each simulated grower
  checkInMin: 60, // simulated growers check in somewhere between these (blocks), skewed toward the minimum
  checkInMax: HOUR,
  joinChance: 0.004, // per block at launch hype; decays with hypeHalfLife
  joinFloor: 0.08, // fraction of joinChance that never decays
  hypeHalfLife: 6 * HOUR,
  quitChance: 0.0004, // per check-in
  halvingShock: 12, // quit multiplier for the period right after a halving
  halvingShockBlocks: HOUR,
  collectorChance: 0.003, // per block, a network grower tries to buy a limited cosmetic
  sellShare: 0, // fraction of new earnings a simulated grower sells to the market at each check-in
  buyIns: [], // [{ chance, bud }]: new growers who buy BUD from the market on joining
  packs: [], // [{ id, chance, room, strains }]: starter packs sold for USD outside the BUD economy (nothing burned)
  maxCatchUp: 12 * HOUR, // offline blocks simulated on load
};
export const DEFAULT_CONFIG = DEMO_CONFIG;

export const LIVE_CONFIG = {
  ...DEMO_CONFIG,
  halvingInterval: 4200000, // BigCoin's schedule: about 49 days at 1 block/s, 21M BUD cap
  tick: 60,
  roomCooldown: 24 * HOUR,
  strainLock: 24 * HOUR,
  unlockScale: 1,
  startingBots: 60,
  cohort: 25, // 60 x 25 = 1,500 launch players
  checkInMin: 600,
  checkInMax: 24 * HOUR,
  joinChance: 0.0016,
  joinFloor: 0.15,
  hypeHalfLife: 72 * HOUR,
  quitChance: 0.003,
  collectorChance: 0.02,
  sellShare: 0.25,
  buyIns: [{ chance: 0.4, bud: 100 }, { chance: 0.08, bud: 1500 }],
  packs: [
    { id: 'founder', chance: 0.15, room: 1, strains: ['skunk', 'skunk'] },
    { id: 'grower', chance: 0.03, room: 2, strains: ['skunk', 'skunk', 'skunk', 'skunk', 'ogkush'] },
  ],
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
  const cfg = { ...DEMO_CONFIG, ...overrides };
  const state = {
    version: SAVE_VERSION,
    cfg,
    rng: seed >>> 0,
    height: 0,
    token: { minted: 0, burned: 0, treasury: 0, dormant: 0, spoiled: 0 },
    player: {
      wallet: 0, pending: 0, room: 0, roomReadyAt: 0, waterUntil: cfg.waterBlocks, lastClaim: 0, joinedAt: 0,
      slots: [], inventory: [], utilities: [], nextUid: 1,
      claimedTotal: 0, earnedTotal: 0, spoiledTotal: 0, spent: 0, minted: 0, mintedIds: [], cosmeticsBought: 0, badges: [],
    },
    bots: [],
    sold: {}, // season mint counts for supply-capped strains and cosmetics, across all growers
    spendBy: { strains: 0, rooms: 0, utilities: 0, cosmetics: 0 },
    stats: { joins: 0, quits: 0, players: 1, packs: {} },
    // BUD sold by growers waits in the market float until newcomers buy it. bought/sold are running totals.
    market: { float: 0, bought: 0, sold: 0 },
    log: [],
  };
  plant(state.player, 'strain', 'bagseed', 0);
  state.player.mintedIds.push('bagseed');
  for (let i = 0; i < cfg.startingBots; i++) addBot(state);
  log(state, `Season launched with ${state.stats.players} growers. You got a free Bagseed.`);
  return state;
}

function log(state, message) {
  state.log.unshift({ h: state.height, message });
  if (state.log.length > 60) state.log.length = 60;
}

function addBot(state) {
  const cfg = state.cfg;
  const n = state.stats.joins++;
  state.stats.players += cfg.cohort;
  const bag = STRAINS[strainIndex.bagseed];
  const every = Math.floor(cfg.checkInMin + rand(state) ** 2 * (cfg.checkInMax - cfg.checkInMin));
  state.bots.push({
    name: `${BOT_NAMES[n % BOT_NAMES.length]} #${n + 1}`,
    count: cfg.cohort,
    balance: 0, fresh: 0, room: 0, roomReadyAt: 0, items: [strainIndex.bagseed], utilities: [],
    potency: bag.potency, watts: bag.watts,
    active: true,
    every,
    lastAct: state.height,
    joinedAt: state.height,
    nextAct: state.height + 1 + Math.floor(rand(state) * Math.min(every, 600)),
    reserve: rand(state) * 0.3, // fraction of balance kept unspent
  });
  const b = state.bots[state.bots.length - 1];
  let roll = rand(state);
  for (const pack of cfg.packs) {
    if (roll < pack.chance) {
      state.stats.packs[pack.id] = (state.stats.packs[pack.id] || 0) + b.count;
      b.room = pack.room;
      for (const id of pack.strains) {
        const st = STRAINS[strainIndex[id]];
        b.items.push(strainIndex[id]);
        b.potency += st.potency;
        b.watts += st.watts;
      }
      break;
    }
    roll -= pack.chance;
  }
  roll = rand(state);
  for (const tier of cfg.buyIns) {
    if (roll < tier.chance) {
      const got = Math.min(state.market.float, tier.bud * b.count);
      state.market.float -= got;
      state.market.bought += got;
      b.balance = got / b.count;
      break;
    }
    roll -= tier.chance;
  }
}

function plant(owner, kind, id, height) {
  owner.slots.push({ uid: owner.nextUid++, kind, id, plantedAt: height });
}

// ---- Derived values ----

export function strainWatts(utilities, strain) {
  return utilities.includes('led') ? Math.ceil(strain.watts * 0.75) : strain.watts;
}

export function playerPotency(state) {
  let total = 0;
  for (const s of state.player.slots) if (s.kind === 'strain') total += STRAINS[strainIndex[s.id]].potency;
  return total;
}

export function playerWatts(state) {
  let total = 0;
  const u = state.player.utilities;
  for (const s of state.player.slots) if (s.kind === 'strain') total += strainWatts(u, STRAINS[strainIndex[s.id]]);
  return total;
}

export function isWet(state) {
  return state.player.utilities.includes('drip') || state.height < state.player.waterUntil;
}

export function rackFull(state) {
  return state.height - state.player.lastClaim >= state.cfg.storageBlocks;
}

function multiplier(cfg, utilities, wet) {
  return (utilities.includes('co2') ? cfg.co2Boost : 1) * (wet ? 1 : cfg.dryPenalty);
}

// Potency that actually counts this block, after CO2 and watering.
export function effectivePotency(state) {
  return playerPotency(state) * multiplier(state.cfg, state.player.utilities, isWet(state));
}

function botEffective(state, b) {
  const wet = b.utilities.includes('drip') || state.height - b.lastAct < state.cfg.waterBlocks;
  return b.potency * multiplier(state.cfg, b.utilities, wet) * b.count;
}

export function networkPotency(state) {
  let total = effectivePotency(state);
  for (const b of state.bots) if (b.active) total += botEffective(state, b);
  return total;
}

export function circulating(state) {
  const t = state.token;
  return t.minted - t.burned - t.treasury - t.spoiled;
}

export function isUnlocked(state, strain) {
  return state.height >= strain.unlockHours * HOUR * state.cfg.unlockScale;
}

export function supplyLeft(state, item) {
  return item.supply == null ? null : item.supply - (state.sold[item.id] || 0);
}

export function summary(state) {
  const cfg = state.cfg;
  const mine = effectivePotency(state);
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
    basePotency: playerPotency(state),
    potency: mine,
    watts: playerWatts(state),
    networkPotency: net,
    share,
    perHour: share * reward * HOUR,
    room,
    slotsUsed: state.player.slots.length,
    activeGrowers: state.stats.players - state.stats.quits * cfg.cohort,
    roomCooldown: Math.max(0, state.player.roomReadyAt - state.height),
    wet: isWet(state),
    dryIn: Math.max(0, state.player.waterUntil - state.height),
    rackFull: rackFull(state),
    rackIn: Math.max(0, state.player.lastClaim + cfg.storageBlocks - state.height),
    circulating: circulating(state),
  };
}

// ---- Simulation ----

export function advance(state, blocks) {
  const tick = state.cfg.tick;
  let n = Math.max(0, Math.floor(blocks));
  while (n > 0) {
    const k = Math.min(tick, n);
    step(state, k);
    n -= k;
  }
}

function step(state, k) {
  const cfg = state.cfg;
  const t = state.token;
  const p = state.player;
  const cap = supplyCap(cfg);
  let reward = 0;
  for (let i = 0; i < k; i++) reward += rewardAt(cfg, state.height + i);
  reward = Math.min(reward, cap - t.minted);
  const net = networkPotency(state);
  if (reward > 0 && net > 0) {
    // Seedling pool: a slice of every block is split per head among new growers still in the Closet.
    const window = cfg.seedlingDays * 24 * HOUR;
    const seedling = (o) => o.room === 0 && state.height - (o.joinedAt || 0) < window;
    let heads = seedling(p) ? 1 : 0;
    for (const b of state.bots) if (b.active && seedling(b)) heads += b.count;
    const pool = heads > 0 ? reward * cfg.seedlingPool : 0;
    const perHead = heads > 0 ? pool / heads : 0;
    const main = reward - pool;
    const credit = (amount, toBot) => {
      if (toBot) {
        if (state.height - toBot.lastAct >= cfg.storageBlocks && !toBot.utilities.includes('trimmer')) { t.spoiled += amount; return; }
        toBot.balance += amount / toBot.count;
        toBot.fresh += amount / toBot.count;
      } else {
        p.earnedTotal += amount;
        if (rackFull(state)) {
          p.spoiledTotal += amount;
          t.spoiled += amount;
        } else {
          p.pending += amount;
        }
      }
    };
    credit((main * effectivePotency(state)) / net + (seedling(p) ? perHead : 0), null);
    for (const b of state.bots) {
      if (b.active) credit((main * botEffective(state, b)) / net + (seedling(b) ? perHead * b.count : 0), b);
    }
    t.minted += reward;
  }
  const before = Math.floor(state.height / cfg.halvingInterval);
  state.height += k;
  if (Math.floor(state.height / cfg.halvingInterval) > before) {
    log(state, `Halving! Block reward is now ${rewardAt(cfg, state.height)} BUD.`);
  }
  if (p.utilities.includes('trimmer') && state.height - p.lastClaim >= cfg.trimmerEvery) claim(state);

  // Network churn: hype brings new growers early on, halvings shake out the weak.
  const hype = cfg.joinFloor + (1 - cfg.joinFloor) * 0.5 ** (state.height / cfg.hypeHalfLife);
  const joinP = 1 - (1 - cfg.joinChance * hype) ** k;
  if (reward > 0 && rand(state) < joinP) addBot(state);
  const shocked = state.height % cfg.halvingInterval < cfg.halvingShockBlocks && state.height >= cfg.halvingInterval;
  for (const b of state.bots) {
    if (!b.active || state.height < b.nextAct) continue;
    b.nextAct = state.height + b.every;
    b.lastAct = state.height; // checking in waters and harvests
    if (rand(state) < cfg.quitChance * (shocked ? cfg.halvingShock : 1)) {
      b.active = false;
      t.dormant += b.balance * b.count;
      b.balance = 0;
      state.stats.quits++;
      continue;
    }
    if (cfg.sellShare > 0) {
      const sell = Math.min(b.balance, b.fresh * cfg.sellShare);
      b.fresh = 0;
      b.balance -= sell;
      state.market.float += sell * b.count;
      state.market.sold += sell * b.count;
    }
    botInvest(state, b);
  }
  // Collectors in the network chip away at limited cosmetic drops.
  if (rand(state) < 1 - (1 - cfg.collectorChance) ** k && state.bots.length) {
    const b = state.bots[Math.floor(rand(state) * state.bots.length)];
    const open = COSMETICS.filter((c) => c.supply !== null && supplyLeft(state, c) > 0);
    const c = open[Math.floor(rand(state) * open.length)];
    if (b.active && c && b.balance * b.count >= c.cost) {
      b.balance -= c.cost / b.count; // one collector in the cohort buys one item
      spend(state, c.cost, 'cosmetics');
      state.sold[c.id] = (state.sold[c.id] || 0) + 1;
    }
  }
  checkBadges(state);
}

function spend(state, amount, category) {
  const burn = amount * state.cfg.burnShare;
  state.token.burned += burn;
  state.token.treasury += amount - burn;
  state.spendBy[category] += amount;
}

function botBuyUtility(state, b, id) {
  const u = UTILITIES.find((x) => x.id === id);
  b.balance -= u.cost;
  spend(state, u.cost * b.count, 'utilities');
  b.utilities.push(id);
  if (id === 'led') b.watts = b.items.reduce((sum, i) => sum + strainWatts(b.utilities, STRAINS[i]), 0);
}

// Greedy bot: automate what its check-in habit neglects, buy the most potency per BUD that fits,
// upgrade the room when full, add boosts, and replace the weakest strain once the room is maxed.
function botInvest(state, b) {
  const cfg = state.cfg;
  for (let guard = 0; guard < 60; guard++) {
    const budget = b.balance * (1 - b.reserve);
    const room = ROOMS[b.room];
    const freeSlots = room.slots - b.items.length;
    const freeWatts = room.watts - b.watts;
    const has = (id) => b.utilities.includes(id);
    if (!has('drip') && b.every > cfg.waterBlocks && budget >= 60 && b.room >= 1) { botBuyUtility(state, b, 'drip'); continue; }
    if (!has('trimmer') && b.every > cfg.storageBlocks * 0.8 && budget >= 40 && b.room >= 1) { botBuyUtility(state, b, 'trimmer'); continue; }
    let best = -1;
    let bestScore = 0;
    for (let i = 1; i < STRAINS.length; i++) {
      const s = STRAINS[i];
      if (s.cost > budget || !isUnlocked(state, s)) continue;
      const left = supplyLeft(state, s);
      if (left !== null && left < b.count) continue;
      if (freeSlots > 0 && strainWatts(b.utilities, s) <= freeWatts) {
        const score = s.potency / s.cost;
        if (score > bestScore) { best = i; bestScore = score; }
      }
    }
    if (best >= 0) {
      const s = STRAINS[best];
      b.balance -= s.cost;
      spend(state, s.cost * b.count, 'strains');
      if (s.supply != null) state.sold[s.id] = (state.sold[s.id] || 0) + b.count;
      b.items.push(best);
      b.potency += s.potency;
      b.watts += strainWatts(b.utilities, s);
      continue;
    }
    const next = ROOMS[b.room + 1];
    if (next && state.height >= b.roomReadyAt && next.cost <= budget && (freeSlots <= 1 || freeWatts < 30)) {
      b.balance -= next.cost;
      spend(state, next.cost * b.count, 'rooms');
      b.room++;
      b.roomReadyAt = state.height + cfg.roomCooldown;
      continue;
    }
    if (!has('led') && freeSlots > 1 && freeWatts < 30 && budget >= 250) { botBuyUtility(state, b, 'led'); continue; }
    if (!has('co2') && b.room >= 4 && budget >= 400) { botBuyUtility(state, b, 'co2'); continue; }
    // Room maxed out (or waiting on cooldown): swap the weakest strain for a much stronger one that fits.
    if (freeSlots > 0) return;
    let weakest = 0;
    for (let k = 1; k < b.items.length; k++) if (STRAINS[b.items[k]].potency < STRAINS[b.items[weakest]].potency) weakest = k;
    const w = STRAINS[b.items[weakest]];
    let swap = -1;
    for (let i = STRAINS.length - 1; i > b.items[weakest]; i--) {
      const s = STRAINS[i];
      const left = supplyLeft(state, s);
      if (s.cost <= budget && isUnlocked(state, s) && (left === null || left >= b.count) &&
        b.watts - strainWatts(b.utilities, w) + strainWatts(b.utilities, s) <= room.watts && s.potency > w.potency * 2) { swap = i; break; }
    }
    if (swap < 0) return;
    const refund = Math.min(state.token.treasury, w.cost * cfg.sellBackShare * b.count);
    state.token.treasury -= refund;
    b.balance += refund / b.count;
    b.items.splice(weakest, 1);
    b.potency -= w.potency;
    b.watts -= strainWatts(b.utilities, w);
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

// Manual task: harvest. Moves the drying rack into the wallet and empties the rack.
export function claim(state) {
  const p = state.player;
  p.lastClaim = state.height;
  if (p.pending <= 0) return fail('Nothing to harvest yet.');
  const amount = p.pending;
  p.wallet += amount;
  p.claimedTotal += amount;
  p.pending = 0;
  checkBadges(state);
  return ok(`Harvested ${amount.toFixed(3)} BUD.`);
}

// Manual task: water. Free, keeps the room at full potency for waterBlocks.
export function water(state) {
  const p = state.player;
  if (p.utilities.includes('drip')) return ok('Drip Irrigation already keeps the room wet.');
  p.waterUntil = state.height + state.cfg.waterBlocks;
  return ok('Watered. Plants stay at full potency for 4 hours.');
}

function pay(state, amount, category) {
  const p = state.player;
  if (amount > p.wallet + 1e-9) return false;
  p.wallet = Math.max(0, p.wallet - amount);
  p.spent += amount;
  spend(state, amount, category);
  return true;
}

export function canFit(state, strainId) {
  const s = STRAINS[strainIndex[strainId]];
  const room = ROOMS[state.player.room];
  if (state.player.slots.length >= room.slots) return 'No free slot. Upgrade your room or sell something.';
  const w = strainWatts(state.player.utilities, s);
  if (playerWatts(state) + w > room.watts) return `Not enough power (needs ${w} W).`;
  return null;
}

// Minting auto-plants when it fits, like BigCoin auto-staking; otherwise the seed waits in inventory.
export function buyStrain(state, strainId) {
  const s = STRAINS[strainIndex[strainId]];
  if (!s) return fail('Unknown strain.');
  if (s.starter) return fail('Bagseed is the free starter and cannot be bought.');
  if (!isUnlocked(state, s)) return fail(`${s.name} is not released yet.`);
  if (supplyLeft(state, s) === 0) return fail(`${s.name} is sold out this season.`);
  const p = state.player;
  if (!pay(state, s.cost, 'strains')) return fail(`You need ${s.cost} BUD.`);
  if (s.supply != null) state.sold[s.id] = (state.sold[s.id] || 0) + 1;
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
  return ok(`Planted ${s.name}. Rooting for ${Math.round(state.cfg.strainLock / 60)} minutes.`);
}

export function buyUtility(state, utilityId) {
  const u = UTILITIES.find((x) => x.id === utilityId);
  if (!u) return fail('Unknown utility.');
  const p = state.player;
  if (p.utilities.includes(u.id)) return fail(`You already own ${u.name}.`);
  if (!pay(state, u.cost, 'utilities')) return fail(`You need ${u.cost} BUD.`);
  p.utilities.push(u.id);
  checkBadges(state);
  return ok(`Installed ${u.name}.`);
}

export function buyCosmetic(state, cosmeticId) {
  const c = COSMETICS.find((x) => x.id === cosmeticId);
  if (!c) return fail('Unknown cosmetic.');
  if (supplyLeft(state, c) === 0) return fail(`${c.name} is sold out.`);
  const p = state.player;
  if (p.slots.length >= ROOMS[p.room].slots) return fail('No free slot for decorations.');
  if (!pay(state, c.cost, 'cosmetics')) return fail(`You need ${c.cost} BUD.`);
  state.sold[c.id] = (state.sold[c.id] || 0) + 1;
  p.cosmeticsBought++;
  plant(p, 'cosmetic', c.id, state.height);
  checkBadges(state);
  return ok(`Placed ${c.name}.`);
}

export function cosmeticsLeft(state, cosmeticId) {
  return supplyLeft(state, COSMETICS.find((x) => x.id === cosmeticId));
}

export function upgradeRoom(state) {
  const p = state.player;
  const next = ROOMS[p.room + 1];
  if (!next) return fail('You already own the biggest room.');
  if (state.height < p.roomReadyAt) return fail(`Contractors are busy for ${p.roomReadyAt - state.height} more blocks.`);
  if (!pay(state, next.cost, 'rooms')) return fail(`You need ${next.cost} BUD.`);
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
  state.cfg = { ...DEMO_CONFIG, ...state.cfg };
  return state;
}
