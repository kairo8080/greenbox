import test from 'node:test';
import assert from 'node:assert/strict';
import { RARITY, ITEMS, BOXES, PITY, openBox, boxStats, rollRarity } from '../../public/economy/packs.js';

// Small seeded generator so pulls are repeatable.
function lcg(seed) {
  let s = seed >>> 0;
  return () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 2 ** 32);
}

test('rarity odds add up to 100% and Epic is 4.20%', () => {
  assert.ok(Math.abs(RARITY.reduce((a, r) => a + r.odds, 0) - 1) < 1e-12);
  assert.equal(RARITY.find((r) => r.id === 'epic').odds, 0.042);
  assert.equal(rollRarity(0), 'common');
  assert.equal(rollRarity(0.999), 'epic');
});

test('every collectible has a name per rarity; box slots are known items', () => {
  for (const i of ITEMS.filter((x) => x.kind === 'nft')) for (const r of RARITY) assert.ok(i.names[r.id], `${i.id} ${r.id}`);
  for (const b of BOXES) for (const t of b.slots || b.fixed.map(([x]) => x)) assert.ok(ITEMS.some((i) => i.id === t && i.kind === 'nft'), t);
});

test('starter kit matches the item list and is all Common', () => {
  const { items } = openBox('kit');
  for (const i of ITEMS.filter((x) => x.kind === 'nft')) assert.equal(items.filter((x) => x.type === i.id).length, i.kit, i.id);
  assert.ok(items.every((x) => x.rarity === 'common'));
});

test('standard box pulls one room, one pot, one seed', () => {
  const { items } = openBox('standard', lcg(1));
  assert.deepEqual(items.map((x) => x.type), ['room', 'pot', 'seed']);
});

test('founder booster always holds a Rare or better', () => {
  const rng = lcg(7);
  for (let i = 0; i < 5000; i++) assert.ok(openBox('founder', rng).items.some((x) => x.rarity !== 'common'));
});

test('pity guarantees an Epic by the 20th box', () => {
  const never = () => 0; // always rolls Common
  let pity = 0;
  for (let i = 1; i < PITY; i++) {
    const r = openBox('standard', never, pity);
    assert.ok(!r.items.some((x) => x.rarity === 'epic'));
    pity = r.pity;
  }
  const r = openBox('standard', never, pity);
  assert.ok(r.items.some((x) => x.rarity === 'epic'));
  assert.equal(r.pity, 0);
});

test('exact box odds match a large sample', () => {
  for (const id of ['standard', 'founder']) {
    const s = boxStats(id), rng = lcg(42), n = 200000;
    let epic = 0, rare = 0;
    for (let i = 0; i < n; i++) {
      const { items } = openBox(id, rng, 0);
      if (items.some((x) => x.rarity === 'epic')) epic++;
      if (items.some((x) => x.rarity !== 'common')) rare++;
    }
    assert.ok(Math.abs(epic / n - s.epic) < 0.005, `${id} epic ${epic / n} vs ${s.epic}`);
    assert.ok(Math.abs(rare / n - s.rareUp) < 0.005, `${id} rare ${rare / n} vs ${s.rareUp}`);
    assert.ok(s.avgToEpic < PITY);
  }
});
