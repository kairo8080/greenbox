import test from 'node:test';
import assert from 'node:assert/strict';
import { ROOMS, STRAINS } from '../../public/economy/content.js';
import {
  createGame, advance, claim, buyStrain, buyCosmetic, buyUtility, upgradeRoom, uproot, replant, sellBack, water,
  summary, supplyCap, rewardAt, playerWatts, serialize, deserialize, cosmeticsLeft, effectivePotency, LIVE_CONFIG,
} from '../../public/economy/engine.js';

// A network of one: no bots at launch and nobody joins.
const SOLO = { startingBots: 0, joinChance: 0 };
const near = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) <= eps * Math.max(1, Math.abs(b)), `${a} != ${b}`);

// Every minted BUD is in a wallet, pending, a bot balance, dormant, the treasury, or burned.
function assertConserved(state) {
  const t = state.token;
  const bots = state.bots.reduce((sum, b) => sum + b.balance * b.count, 0);
  near(t.minted, state.player.wallet + state.player.pending + bots + t.dormant + t.treasury + t.burned + t.spoiled + state.market.float);
}

function rich(state, amount = 100000) {
  // Test helper: pretend the player harvested this much (keeps conservation by minting it).
  state.player.wallet += amount;
  state.token.minted += amount;
}

test('halving schedule and supply cap follow the configured season', () => {
  const cfg = { blockReward: 2.5, halvingInterval: 100 };
  assert.equal(supplyCap(cfg), 500);
  assert.equal(rewardAt(cfg, 0), 2.5);
  assert.equal(rewardAt(cfg, 99), 2.5);
  assert.equal(rewardAt(cfg, 100), 1.25);
  assert.equal(rewardAt(cfg, 250), 0.625);
});

test('emission never exceeds the cap and stays conserved through bot spending', () => {
  const state = createGame(3, { halvingInterval: 500, startingBots: 30 });
  advance(state, 500 * 40);
  assert.ok(state.token.minted <= supplyCap(state.cfg) + 1e-9);
  near(state.token.minted, supplyCap(state.cfg), 1e-6);
  assertConserved(state);
  assert.ok(state.token.burned > 0, 'bots should have spent and burned BUD');
});

test('each block is split by share of network potency', () => {
  const state = createGame(1, { startingBots: 3, joinChance: 0 });
  const before = summary(state);
  advance(state, 1);
  near(state.player.pending, 2.5 * before.share);
  near(before.share, 100 / 400);
});

test('purchases burn 75% and send 25% to the treasury', () => {
  const state = createGame(1, SOLO);
  rich(state, 100);
  const r = buyStrain(state, 'ditchweed');
  assert.ok(r.ok, r.message);
  near(state.token.burned, 3);
  near(state.token.treasury, 1);
  assertConserved(state);
});

test('claim moves pending rewards into the wallet', () => {
  const state = createGame(1, SOLO);
  advance(state, 10);
  near(state.player.pending, 25);
  assert.ok(claim(state).ok);
  near(state.player.wallet, 25);
  assert.equal(claim(state).ok, false);
  assert.ok(state.player.badges.includes('first_claim'));
});

test('slots and power limits gate planting; overflow goes to inventory', () => {
  const state = createGame(1, SOLO);
  rich(state);
  const r = buyStrain(state, 'skunk'); // 30 W > Closet's 28 W
  assert.ok(r.ok);
  assert.equal(state.player.slots.length, 1);
  assert.equal(state.player.inventory.length, 1);
  for (let i = 0; i < 3; i++) buyStrain(state, 'ditchweed');
  assert.equal(state.player.slots.length, 4);
  assert.ok(playerWatts(state) <= ROOMS[0].watts);
  buyStrain(state, 'ditchweed');
  assert.equal(state.player.slots.length, 4);
  assert.equal(state.player.inventory.length, 2);
  assert.equal(buyCosmetic(state, 'gnome').ok, false, 'cosmetics need a free slot too');
});

test('free starter cannot be bought and unaffordable buys change nothing', () => {
  const state = createGame(1, SOLO);
  assert.equal(buyStrain(state, 'bagseed').ok, false);
  assert.equal(buyStrain(state, 'ditchweed').ok, false);
  assert.equal(state.player.inventory.length, 0);
  assert.equal(state.token.burned, 0);
});

test('room upgrades go one tier at a time with a cooldown', () => {
  const state = createGame(1, { ...SOLO, roomCooldown: 50 });
  rich(state);
  assert.ok(upgradeRoom(state).ok);
  assert.equal(state.player.room, 1);
  assert.equal(upgradeRoom(state).ok, false);
  advance(state, 50);
  assert.ok(upgradeRoom(state).ok);
  assert.equal(state.player.room, 2);
  near(state.token.burned, (42 + 106) * 0.75);
});

test('planted strains are locked, then can be uprooted, replanted, or sold back', () => {
  const state = createGame(1, { ...SOLO, strainLock: 20 });
  rich(state, 10);
  buyStrain(state, 'ditchweed');
  const slot = state.player.slots.find((s) => s.id === 'ditchweed');
  assert.equal(uproot(state, slot.uid).ok, false);
  advance(state, 20);
  assert.ok(uproot(state, slot.uid).ok);
  assert.equal(state.player.inventory.length, 1);
  assert.ok(replant(state, slot.uid).ok);
  advance(state, 20);
  uproot(state, slot.uid);
  const wallet = state.player.wallet;
  assert.ok(sellBack(state, slot.uid).ok);
  near(state.player.wallet - wallet, 4 * 0.2);
  assert.equal(state.player.inventory.length, 0);
  assertConserved(state);
});

test('limited cosmetics sell out', () => {
  const state = createGame(1, SOLO);
  rich(state);
  upgradeRoom(state);
  state.sold.neon = 99;
  assert.ok(buyCosmetic(state, 'neon').ok);
  assert.equal(cosmeticsLeft(state, 'neon'), 0);
  assert.equal(buyCosmetic(state, 'neon').ok, false);
});

test('runs are deterministic per seed and survive a save round trip', () => {
  const a = createGame(42);
  const b = createGame(42);
  advance(a, 5000);
  const restored = deserialize(serialize(b));
  advance(restored, 5000);
  assert.equal(serialize(a), serialize(restored));
  assert.throws(() => deserialize(JSON.stringify({ version: 999 })));
});

test('the network grows and halvings shake out growers', () => {
  const state = createGame(7);
  advance(state, state.cfg.halvingInterval * 2);
  const s = summary(state);
  assert.ok(state.stats.joins > state.cfg.startingBots);
  assert.ok(state.stats.quits > 0);
  assert.ok(s.networkPotency > 41 * STRAINS[0].potency * 100);
  assertConserved(state);
});

test('a dry room halves potency until watered; Drip Irrigation removes the chore', () => {
  const state = createGame(1, SOLO);
  advance(state, state.cfg.waterBlocks);
  assert.equal(summary(state).wet, false);
  near(effectivePotency(state), 50);
  assert.ok(water(state).ok);
  near(effectivePotency(state), 100);
  rich(state, 1000);
  assert.ok(buyUtility(state, 'drip').ok);
  advance(state, state.cfg.waterBlocks * 3);
  assert.equal(summary(state).wet, true);
  assert.equal(buyUtility(state, 'drip').ok, false, 'utilities are bought once');
});

test('a full drying rack spoils new harvests; the Auto-Trimmer keeps harvesting', () => {
  const state = createGame(1, { ...SOLO, storageBlocks: 100, trimmerEvery: 50, waterBlocks: 1e9 });
  advance(state, 150);
  near(state.player.pending, 250);
  near(state.player.spoiledTotal, 125);
  assertConserved(state);
  claim(state);
  rich(state, 40);
  buyUtility(state, 'trimmer');
  advance(state, 10000);
  near(state.player.spoiledTotal, 125);
  assert.ok(state.player.pending < 2.5 * state.cfg.trimmerEvery + 1e-6);
  assertConserved(state);
});

test('CO2 boosts potency and LED Retrofit cuts strain power draw', () => {
  const state = createGame(1, SOLO);
  rich(state);
  upgradeRoom(state);
  buyStrain(state, 'skunk');
  const watts = playerWatts(state);
  buyUtility(state, 'led');
  assert.ok(playerWatts(state) < watts);
  const before = effectivePotency(state);
  buyUtility(state, 'co2');
  near(effectivePotency(state), before * 1.1);
});

test('the live schedule gates strain releases and caps their season supply', () => {
  const state = createGame(1, { ...LIVE_CONFIG, startingBots: 0, joinChance: 0 });
  rich(state, 1e6);
  for (let i = 0; i < 8; i++) upgradeRoom(state) || null;
  assert.equal(buyStrain(state, 'genesis').ok, false);
  advance(state, 336 * 3600);
  state.sold.genesis = 100;
  assert.match(buyStrain(state, 'genesis').message, /sold out/);
  state.sold.genesis = 99;
  assert.ok(buyStrain(state, 'genesis').ok);
});

test('live cohorts represent many players and keep supply conserved', () => {
  const state = createGame(5, LIVE_CONFIG);
  advance(state, 3 * 24 * 3600);
  assert.ok(state.stats.players >= 1500);
  assert.ok(state.token.spoiled > 0, 'casual growers lose some harvest before automating');
  assert.ok(state.spendBy.utilities > 0);
  assertConserved(state);
});

test('the committed forecast matches the current live config and catalog', async () => {
  const { readFile } = await import('node:fs/promises');
  const f = JSON.parse(await readFile(new URL('../../public/economy/forecast.json', import.meta.url), 'utf8'));
  assert.deepEqual(f.config, JSON.parse(JSON.stringify(LIVE_CONFIG)), 'rerun npm run forecast');
  assert.deepEqual(f.catalog.strains.map((s) => [s.id, s.cost, s.supply]), STRAINS.map((s) => [s.id, s.cost, s.supply]), 'rerun npm run forecast');
});
