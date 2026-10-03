// Greenbox economy content: the BigCoin blueprint reskinned as a grow operation.
// Facilities -> grow rooms, miners -> strains, hashrate -> potency (pp/s), power -> watts.
// Room numbers and six strain rows copy BigCoin's published tables; the other strains are interpolated.

export const TOKEN = 'BUD';

// Rooms are in-game upgrades tied to the account, not NFTs (as in BigCoin).
export const ROOMS = [
  { id: 'closet', name: 'Closet', cost: 0, slots: 4, watts: 28 },
  { id: 'garage', name: 'Garage', cost: 42, slots: 8, watts: 168 },
  { id: 'shed', name: 'Garden Shed', cost: 106, slots: 12, watts: 420 },
  { id: 'basement', name: 'Basement', cost: 190, slots: 16, watts: 1120 },
  { id: 'greenhouse', name: 'Greenhouse', cost: 230, slots: 20, watts: 7000 },
  { id: 'warehouse', name: 'High Voltage Warehouse', cost: 275, slots: 20, watts: 13125 },
  { id: 'vertical', name: 'Vertical Farm', cost: 295, slots: 24, watts: 20000 },
  { id: 'biodome1', name: 'Biodome I', cost: 850, slots: 42, watts: 40000 },
  { id: 'biodome2', name: 'Biodome II', cost: 1020, slots: 42, watts: 65000 },
];

// potency: share weight, like hashrate. watts: power draw against the room limit. Every strain is an NFT (ERC-721), like BigCoin miners.
// supply: season cap shared by every grower (null = unlimited), sized from the live forecast: the lower capped tiers sell out late in the first halving era, top tiers stay scarce into era 2. unlockHours: release time after launch on the live schedule.
export const STRAINS = [
  { id: 'bagseed', name: 'Bagseed', cost: 0, potency: 100, watts: 1, nft: true, starter: true, supply: null, unlockHours: 0 },
  { id: 'ditchweed', name: 'Ditch Weed', cost: 4, potency: 180, watts: 6, nft: true, supply: null, unlockHours: 0 },
  { id: 'northern', name: 'Northern Lights Auto', cost: 12, potency: 600, watts: 12, nft: true, supply: null, unlockHours: 0 },
  { id: 'skunk', name: 'Skunk #1', cost: 34, potency: 5000, watts: 30, nft: true, supply: null, unlockHours: 0 },
  { id: 'bluedream', name: 'Blue Dream', cost: 70, potency: 10000, watts: 55, nft: true, supply: null, unlockHours: 0 },
  { id: 'ogkush', name: 'OG Kush', cost: 127, potency: 20000, watts: 90, nft: true, supply: null, unlockHours: 0 },
  { id: 'widow', name: 'White Widow', cost: 260, potency: 48000, watts: 180, nft: true, supply: null, unlockHours: 24 },
  { id: 'gluestick', name: 'Gorilla Glue', cost: 520, potency: 110000, watts: 380, nft: true, supply: 2000, unlockHours: 48 },
  { id: 'gelato', name: 'Gelato', cost: 1050, potency: 250000, watts: 750, nft: true, supply: 400, unlockHours: 72 },
  { id: 'cake', name: 'Wedding Cake', cost: 1700, potency: 400000, watts: 1200, nft: true, supply: 600, unlockHours: 120 },
  { id: 'runtz', name: 'Runtz', cost: 2550, potency: 800000, watts: 2000, nft: true, supply: 400, unlockHours: 168 },
  { id: 'zkittlez', name: 'Zkittlez Mother', cost: 3600, potency: 1500000, watts: 3400, nft: true, supply: 200, unlockHours: 240 },
  { id: 'genesis', name: 'Greenbox Genesis', cost: 5100, potency: 2508000, watts: 5000, nft: true, supply: 100, unlockHours: 336 },
];

// Utilities: in-game items tied to the account (not NFTs), bought once per grower, no slot. They automate a manual task or boost the whole room.
export const UTILITIES = [
  { id: 'drip', name: 'Drip Irrigation', cost: 60, kind: 'automation', effect: 'Waters the room automatically, so plants never dry out.' },
  { id: 'trimmer', name: 'Auto-Trimmer', cost: 40, kind: 'automation', effect: 'Harvests every hour, so the drying rack never overflows.' },
  { id: 'led', name: 'LED Retrofit', cost: 250, kind: 'space', effect: 'Strains draw 25% less power, so more plants fit.' },
  { id: 'co2', name: 'CO2 Generator', cost: 400, kind: 'harvest', effect: '+10% potency for every strain.' },
];

// Limited decorations are collectible NFTs; open ones are plain in-game items. Cosmetics take a slot, draw no power and add no potency. `supply` is a capped drop shared with the network.
export const COSMETICS = [
  { id: 'gnome', name: 'Garden Gnome', cost: 3, supply: null, nft: false },
  { id: 'lavalamp', name: 'Lava Lamp', cost: 8, supply: null, nft: false },
  { id: 'poster', name: 'Reggae Poster', cost: 15, supply: 2000, nft: true },
  { id: 'goldpot', name: 'Golden Pot', cost: 60, supply: 500, nft: true },
  { id: 'neon', name: 'Neon Leaf Sign', cost: 150, supply: 100, nft: true },
];

export const BADGES = [
  { id: 'first_claim', name: 'First Harvest', test: (p) => p.claimedTotal > 0 },
  { id: 'first_strain', name: 'Green Thumb', test: (p) => p.minted >= 1 },
  { id: 'garage', name: 'Moved Out', test: (p) => p.room >= 1 },
  { id: 'greenhouse', name: 'Glass House', test: (p) => p.room >= 4 },
  { id: 'biodome', name: 'Biodome Baron', test: (p) => p.room >= 8 },
  { id: 'burn_100', name: 'Smoke Signal', test: (p) => p.spent * 0.75 >= 100 },
  { id: 'burn_10k', name: 'Bonfire', test: (p) => p.spent * 0.75 >= 10000 },
  { id: 'collector', name: 'Decorator', test: (p) => p.cosmeticsBought >= 3 },
  { id: 'genesis', name: 'Genesis Grower', test: (p) => p.mintedIds.includes('genesis') },
  { id: 'automated', name: 'Hands Free', test: (p) => p.utilities.includes('drip') && p.utilities.includes('trimmer') },
];
