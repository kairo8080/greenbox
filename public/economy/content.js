// Greenbox economy content: the BigCoin blueprint reskinned as a grow operation.
// Facilities -> grow rooms, miners -> strains, hashrate -> potency (pp/s), power -> watts.
// Room numbers and six strain rows copy BigCoin's published tables; the other strains are interpolated.

export const TOKEN = 'BUD';

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

// potency: share weight, like hashrate. watts: power draw against the room limit.
export const STRAINS = [
  { id: 'bagseed', name: 'Bagseed', cost: 0, potency: 100, watts: 1, starter: true },
  { id: 'ditchweed', name: 'Ditch Weed', cost: 4, potency: 180, watts: 6 },
  { id: 'northern', name: 'Northern Lights Auto', cost: 12, potency: 600, watts: 12 },
  { id: 'skunk', name: 'Skunk #1', cost: 34, potency: 5000, watts: 30 },
  { id: 'bluedream', name: 'Blue Dream', cost: 70, potency: 10000, watts: 55 },
  { id: 'ogkush', name: 'OG Kush', cost: 127, potency: 20000, watts: 90 },
  { id: 'widow', name: 'White Widow', cost: 260, potency: 48000, watts: 180 },
  { id: 'gluestick', name: 'Gorilla Glue', cost: 520, potency: 110000, watts: 380 },
  { id: 'gelato', name: 'Gelato', cost: 1050, potency: 250000, watts: 750 },
  { id: 'cake', name: 'Wedding Cake', cost: 1700, potency: 400000, watts: 1200 },
  { id: 'runtz', name: 'Runtz', cost: 2550, potency: 800000, watts: 2000 },
  { id: 'zkittlez', name: 'Zkittlez Mother', cost: 3600, potency: 1500000, watts: 3400 },
  { id: 'genesis', name: 'Greenbox Genesis', cost: 5100, potency: 2508000, watts: 5000 },
];

// Cosmetics take a slot, draw no power and add no potency. `supply` is a capped drop shared with the network.
export const COSMETICS = [
  { id: 'gnome', name: 'Garden Gnome', cost: 3, supply: null },
  { id: 'lavalamp', name: 'Lava Lamp', cost: 8, supply: null },
  { id: 'poster', name: 'Reggae Poster', cost: 15, supply: 500 },
  { id: 'goldpot', name: 'Golden Pot', cost: 60, supply: 100 },
  { id: 'neon', name: 'Neon Leaf Sign', cost: 150, supply: 25 },
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
];
