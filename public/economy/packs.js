// Collectible layer (Kairo, 4 Oct 2026): items with rarity, pulled from mystery boxes, TCG style.
// Internal design only: nothing here is announced, and nothing is minted until a grower unlocks it by playing.

// Rarity changes the look plus a small yield bonus that only counts while the plant is watered.
// Pot slots come from the grower's level, never from rarity, so care beats cards.
export const RARITY = [
  { id: 'common', name: 'Common', odds: 0.748, bonus: 0 },
  { id: 'rare', name: 'Rare', odds: 0.21, bonus: 0.05 },
  { id: 'epic', name: 'Epic', odds: 0.042, bonus: 0.1 }, // 4.20%
];

// kind 'nft': a collectible, account-bound until unlock, then airdropped and tradable.
// kind 'game': stays in the game for good.
export const ITEMS = [
  { id: 'room', name: 'Room', kind: 'nft', kit: 1, from: 'Kit · Standard Box',
    names: { common: 'Broken Studio', rare: 'Basement Grow', epic: 'Humboldt Cabin' },
    lore: 'Every grow starts in a broken studio. Humboldt County is the heart of the Emerald Triangle.' },
  { id: 'character', name: 'Character', kind: 'nft', kit: 1, from: 'Kit · ranks up by playing',
    names: { common: 'Budtender', rare: 'Hash Maker', epic: 'Landrace Hunter' },
    lore: 'Landrace hunters travel to collect old local strains, like Afghani and Acapulco Gold.' },
  { id: 'pot', name: 'Pot', kind: 'nft', kit: 2, from: 'Kit · both boxes',
    names: { common: 'Plastic Pot', rare: 'Fabric Pot', epic: 'Hempcrete Pot' },
    lore: 'Hempcrete: hemp hurd and lime, a real building material.' },
  { id: 'seed', name: 'Seed', kind: 'nft', kit: 3, from: 'Kit · both boxes · harvests',
    names: { common: 'Bagseed', rare: 'Skunk #1', epic: 'Afghani Mother' },
    lore: 'Planting uses the seed up; harvests can drop new ones.' },
  { id: 'led', name: 'LED light', kind: 'nft', kit: 1, from: 'Kit · Founder Booster',
    names: { common: 'Blurple Panel', rare: 'Full-Spectrum Bar', epic: 'Sunlight Bar' },
    lore: '"Blurple": growers\' name for the first red and blue LED panels.' },
  { id: 'water', name: 'Water', kind: 'game', kit: 1, from: 'Free, refill by hand', lore: 'Dry plants stop growing.' },
  { id: 'buds', name: 'Buds', kind: 'game', kit: 0, from: 'Harvests', lore: 'Sold to the Corp at the 4:20 pm price.' },
  { id: 'points', name: 'BUD points', kind: 'game', kit: 0, from: 'Selling buds', lore: 'Spent on automation and the Rosin Press.' },
  { id: 'tools', name: 'Automation', kind: 'game', kit: 0, from: 'Bought with BUD points', lore: 'Drip Irrigation, Auto-Trimmer, CO2.' },
];

export const BOXES = [
  { id: 'kit', name: 'Starter Kit', price: 'Free', note: 'Every grower, account-bound',
    fixed: [['room', 'common'], ['character', 'common'], ['pot', 'common'], ['pot', 'common'], ['led', 'common'],
      ['seed', 'common'], ['seed', 'common'], ['seed', 'common']] },
  { id: 'standard', name: 'Mystery Box · Standard', price: 'Price open', note: '3 random pulls', slots: ['room', 'pot', 'seed'] },
  { id: 'founder', name: 'Founder Booster', price: 'Price open', note: 'Launch only · 1 Rare or better · Founder foil (look only)',
    slots: ['pot', 'led', 'seed', 'seed'], guaranteeRare: true },
];

export const PITY = 20; // an Epic is guaranteed by the 20th box in a row without one
export const PRESS = 5; // Rosin Press: 5 duplicates of one rarity press into 1 of the next
export const UNLOCK = { harvests: 20, days: 7 }; // proof of play before anything can leave the game

const byId = (id) => ITEMS.find((i) => i.id === id);
const odds = (id) => RARITY.find((r) => r.id === id).odds;
export const itemName = (type, rarity) => byId(type).names[rarity];

export function rollRarity(r) {
  let acc = 0;
  for (const x of RARITY) { acc += x.odds; if (r < acc) return x.id; }
  return 'common';
}

// Opens one box. pity = boxes in a row without an Epic before this one. Returns the pulls and the new pity count.
export function openBox(boxId, rng = Math.random, pity = 0) {
  const box = BOXES.find((b) => b.id === boxId);
  if (box.fixed) return { items: box.fixed.map(([type, rarity]) => ({ type, rarity, name: itemName(type, rarity) })), pity };
  const rar = box.slots.map(() => rollRarity(rng()));
  if (box.guaranteeRare && rar.every((r) => r === 'common')) {
    rar[rar.length - 1] = rng() < odds('epic') / (odds('rare') + odds('epic')) ? 'epic' : 'rare';
  }
  if (!rar.includes('epic') && pity + 1 >= PITY) rar[Math.floor(rng() * rar.length)] = 'epic';
  return {
    items: box.slots.map((type, i) => ({ type, rarity: rar[i], name: itemName(type, rar[i]) })),
    pity: rar.includes('epic') ? 0 : pity + 1,
  };
}

// Exact odds for one box: chance of at least one Rare-or-better, of at least one Epic, and boxes to an Epic on average (with pity).
export function boxStats(boxId) {
  const box = BOXES.find((b) => b.id === boxId);
  if (box.fixed) return null;
  const n = box.slots.length, pc = odds('common'), pe = odds('epic'), pr = odds('rare');
  const rareUp = box.guaranteeRare ? 1 : 1 - pc ** n;
  let noEpic = (1 - pe) ** n;
  if (box.guaranteeRare) noEpic -= pc ** n * (pe / (pr + pe));
  let avg = 0;
  for (let k = 0; k < PITY; k++) avg += noEpic ** k;
  return { rareUp, epic: 1 - noEpic, avgToEpic: avg };
}
