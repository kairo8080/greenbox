// Greenbox economy content: the BigCoin blueprint reskinned as a grow operation.
// Facilities -> grow rooms, miners -> strains, hashrate -> potency (pp/s), power -> watts.
// Room numbers and six strain rows copy BigCoin's published tables; the other strains are interpolated.

export const TOKEN = 'BUD';

// Rooms are in-game upgrades tied to the account, not NFTs (as in BigCoin).
export const ROOMS = [
  { id: 'closet', name: 'Closet', cost: 0, slots: 4, watts: 28, lore: 'Four pots and a free bagseed. Every grow starts here.' },
  { id: 'garage', name: 'Garage', cost: 840, slots: 8, watts: 168, lore: 'Eight pots, one cracked window. Costs 840 BUD: 2 x 420.' },
  { id: 'shed', name: 'Garden Shed', cost: 2120, slots: 12, watts: 420, lore: 'Out back, out of sight, twelve pots deep.' },
  { id: 'basement', name: 'Basement', cost: 3800, slots: 16, watts: 1120, lore: 'Lights on 18/6 down here. Nobody upstairs asks.' },
  { id: 'greenhouse', name: 'Greenhouse', cost: 4600, slots: 20, watts: 7000, lore: 'Glass walls, real sun, twenty pots in flower.' },
  { id: 'warehouse', name: 'High Voltage Warehouse', cost: 5500, slots: 20, watts: 13125, lore: 'Power-hungry and proud. Keep the meter spinning.' },
  { id: 'vertical', name: 'Vertical Farm', cost: 5900, slots: 24, watts: 20000, lore: 'Racks to the ceiling. Sea of Green: many small plants, fast flower.' },
  { id: 'biodome1', name: 'Biodome I', cost: 17000, slots: 42, watts: 40000, lore: 'Forty-two pots under one dome. Croptober all year.' },
  { id: 'biodome2', name: 'Biodome II', cost: 20400, slots: 42, watts: 65000, lore: 'Forty-two pots, Emerald Triangle scale, sealed under glass. The top grow.' },
];

// potency: share weight, like hashrate. watts: power draw against the room limit. Every strain is an NFT (ERC-721), like BigCoin miners.
// supply: season cap shared by every grower (null = unlimited), sized from the live forecast: the lower capped tiers sell out late in the first halving era, top tiers stay scarce into era 2. unlockHours: release time after launch on the live schedule.
export const STRAINS = [
  { id: 'bagseed', name: 'Bagseed', cost: 0, potency: 100, watts: 1, nft: true, starter: true, supply: null, unlockHours: 0, lore: 'Seeds found in a bag of bought weed. Genetics unknown, cost zero.' },
  { id: 'ditchweed', name: 'Ditch Weed', cost: 80, potency: 180, watts: 6, nft: true, supply: null, unlockHours: 0, lore: 'Feral cannabis. In 2006 NORML reported 98% of US-eradicated pot was ditchweed.' },
  { id: 'northern', name: 'Northern Lights Auto', cost: 240, potency: 600, watts: 12, nft: true, supply: null, unlockHours: 0, lore: 'An autoflower: ruderalis genes, it flowers by age, not light.' },
  { id: 'skunk', name: 'Skunk #1', cost: 680, potency: 5000, watts: 30, nft: true, supply: null, unlockHours: 0, lore: 'Afghani x Acapulco Gold x Colombian. The neighbors smell it first.' },
  { id: 'bluedream', name: 'Blue Dream', cost: 1400, potency: 10000, watts: 55, nft: true, supply: null, unlockHours: 0, lore: 'Blue, dreamy, and built for the long sesh.' },
  { id: 'ogkush', name: 'OG Kush', cost: 2540, potency: 20000, watts: 90, nft: true, supply: null, unlockHours: 0, lore: 'Topped a 2014 all-time list; nearly one in three new hybrids carried OG.' },
  { id: 'widow', name: 'White Widow', cost: 5200, potency: 48000, watts: 180, nft: true, supply: null, unlockHours: 24, lore: 'Reportedly Brazilian sativa x South Indian indica. First drop: day 1, 4:20 pm.' },
  { id: 'gluestick', name: 'Resin Stick', cost: 10400, potency: 110000, watts: 380, nft: true, supply: 2000, unlockHours: 48, lore: 'So much resin it glues your scissors shut.' },
  { id: 'gelato', name: 'Gelato', cost: 21000, potency: 250000, watts: 750, nft: true, supply: 400, unlockHours: 72, lore: 'Dessert-grade frost, iced in trichomes. Drops day 3 at 4:20 pm.' },
  { id: 'cake', name: 'Wedding Cake', cost: 34000, potency: 400000, watts: 1200, nft: true, supply: 600, unlockHours: 120, lore: 'Tiered, frosted, dense. Save a slice for the sesh.' },
  { id: 'runtz', name: 'Sugar Kief', cost: 51000, potency: 800000, watts: 2000, nft: true, supply: 400, unlockHours: 168, lore: 'Candy-sweet and dusted in kief, the trichome powder.' },
  { id: 'zkittlez', name: 'Afghani Mother', cost: 72000, potency: 1500000, watts: 3400, nft: true, supply: 200, unlockHours: 240, lore: 'Only 200. Called a cornerstone of modern breeding. Clones come from mothers.' },
  { id: 'genesis', name: 'Greenbox Genesis', cost: 102000, potency: 2508000, watts: 5000, nft: true, supply: 100, unlockHours: 336, lore: 'Only 100. In Greenbox, the lost 1971 crop finally sprouts.' },
];

// Utilities: in-game items tied to the account (not NFTs), bought once per grower, no slot. They automate a manual task or boost the whole room.
export const UTILITIES = [
  { id: 'drip', name: 'Drip Irrigation', cost: 1200, kind: 'automation', effect: 'Waters the room automatically, so plants never dry out.', lore: 'Waters itself while you sleep. The room never dries out.' },
  { id: 'trimmer', name: 'Auto-Trimmer', cost: 800, kind: 'automation', effect: 'Harvests every hour, so the drying rack never overflows.', lore: 'Harvests every hour, so nothing spoils on the drying rack.' },
  { id: 'led', name: 'LED Retrofit', cost: 5000, kind: 'space', effect: 'Strains draw 25% less power, so more plants fit.', lore: 'Same light, 25% less power, so more strains fit your power limit.' },
  { id: 'co2', name: 'CO2 Generator', cost: 8000, kind: 'harvest', effect: '+10% potency for every strain.', lore: 'Pumps CO2 into the room: +10% potency for every strain.' },
];

// Limited decorations are collectible NFTs; open ones are plain in-game items. Cosmetics take a slot, draw no power and add no potency. `supply` is a capped drop shared with the network.
export const COSMETICS = [
  { id: 'gnome', name: 'Garden Gnome', cost: 60, supply: null, nft: false, lore: 'Guards the grow. Has seen nothing. Says nothing.' },
  { id: 'lavalamp', name: 'Lava Lamp', cost: 160, supply: null, nft: false, lore: 'Slow blobs for a slow 4:20 afternoon.' },
  { id: 'poster', name: 'Hemp for Victory Poster', cost: 300, supply: 2000, nft: true, lore: 'A 1942 USDA film urged US farmers to grow hemp for the war.' },
  { id: 'goldpot', name: 'Golden Pot', cost: 1200, supply: 500, nft: true, lore: 'Only 500 cast. For the grower who has everything.' },
  { id: 'neon', name: '4:20 Neon Clock', cost: 3000, supply: 100, nft: true, lore: 'A neon clock stuck at 4:20 pm. Only 100 lit.' },
];

export const BADGES = [
  { id: 'first_claim', name: 'First Harvest', test: (p) => p.claimedTotal > 0 },
  { id: 'first_strain', name: 'Green Thumb', test: (p) => p.minted >= 1 },
  { id: 'garage', name: 'Garage', test: (p) => p.room >= 1, lore: 'Eight pots, one cracked window. Costs 840 BUD: 2 x 420.' },
  { id: 'greenhouse', name: 'Greenhouse', test: (p) => p.room >= 4, lore: 'Glass walls, real sun, twenty pots in flower.' },
  { id: 'biodome', name: 'Biodome Baron', test: (p) => p.room >= 8 },
  { id: 'burn_100', name: 'Smoke Signal', test: (p) => p.spent * 0.75 >= 2000 },
  { id: 'burn_10k', name: 'Bonfire', test: (p) => p.spent * 0.75 >= 200000 },
  { id: 'collector', name: 'Decorator', test: (p) => p.cosmeticsBought >= 3 },
  { id: 'genesis', name: 'Greenbox Genesis', test: (p) => p.mintedIds.includes('genesis'), lore: 'Only 100. In Greenbox, the lost 1971 crop finally sprouts.' },
  { id: 'automated', name: 'Hands Free', test: (p) => p.utilities.includes('drip') && p.utilities.includes('trimmer') },
];

// Lore: built on real cannabis history (the 1971 4:20 pm meeting, grow stages, slang), fact-checked 3 Oct 2026.
// Sources and the full fact list: /mnt/project-files/research/greenbox-lore.md.
export const LORE = {
  "tagline": "Grow the lost crop. 420M BUD, halving every 42 days at 4:20.",
  "story": "1971, California: five high-school friends met at 4:20 pm to hunt for a cannabis crop its grower had abandoned, using the grower's treasure map. They never found it, and after several failed searches they shortened their plan's name to just '4:20'.\nYou pick up the hunt. Start in a Closet with a free bagseed, plant better strains and climb to Biodome II. Every second is one toke, and its BUD goes around the circle by potency: puff, puff, pass.\nOnly 420M BUD will ever exist. Every 42 days, at 4:20 pm UTC, the yield halves.",
  "terms": [
    {
      "mechanic": "block",
      "name": "Toke",
      "line": "One second = one toke."
    },
    {
      "mechanic": "emission",
      "name": "Puff, Puff, Pass",
      "line": "Each toke, the BUD goes around the circle, split by potency."
    },
    {
      "mechanic": "hashrate",
      "name": "Potency",
      "line": "More trichomes, bigger share."
    },
    {
      "mechanic": "burn",
      "name": "Blaze",
      "line": "75% of every spend goes up in smoke, forever."
    },
    {
      "mechanic": "treasury",
      "name": "The Stash",
      "line": "25% of every spend. Pays Compost refunds."
    },
    {
      "mechanic": "halving",
      "name": "4:20 Halving",
      "line": "Every 42 days at 4:20 pm UTC, the yield halves."
    },
    {
      "mechanic": "new-player pool",
      "name": "Seedling Pool",
      "line": "15% of each toke is shared equally by Closet growers in their first 7 days."
    },
    {
      "mechanic": "referral",
      "name": "Sesh Invite",
      "line": "Bring a friend, earn 4.20% (planned)."
    },
    {
      "mechanic": "sell-back",
      "name": "Compost",
      "line": "Sell a strain or decoration back for 20% of its price, paid from the Stash while it has funds."
    },
    {
      "mechanic": "harvest/claim",
      "name": "Harvest",
      "line": "Move your BUD from the drying rack to your wallet."
    },
    {
      "mechanic": "rooting lock",
      "name": "Rooting",
      "line": "A newly planted item stays locked 24 h while it roots (30 min in demo)."
    },
    {
      "mechanic": "drying rack",
      "name": "Drying Rack",
      "line": "Holds 12 h of BUD. Harvest before it spoils."
    },
    {
      "mechanic": "watering",
      "name": "Water",
      "line": "Keeps the room at full potency for 4 h. A dry room runs at half potency."
    }
  ],
  "eras": [
    {
      "era": 1,
      "name": "Germination",
      "line": "The biggest yield there will ever be."
    },
    {
      "era": 2,
      "name": "Sprout",
      "line": "First leaves."
    },
    {
      "era": 3,
      "name": "Veg",
      "line": "Lights on 18/6 while plants grow."
    },
    {
      "era": 4,
      "name": "Flip",
      "line": "Lights flip to 12/12 to start flowering."
    },
    {
      "era": 5,
      "name": "Flower",
      "line": "Buds form and fill out."
    },
    {
      "era": 6,
      "name": "Ripen",
      "line": "Trichomes turn clear, cloudy, then amber."
    },
    {
      "era": 7,
      "name": "Cure",
      "line": "Halving every 42 days until all 399,168,000 mined BUD are out."
    }
  ],
  "events": [
    {
      "when": "Launch · 4:20 pm UTC",
      "name": "First Meet",
      "what": "Block 0. Growing starts and the BUD pool opens."
    },
    {
      "when": "Days 1–14 · 4:20 pm UTC",
      "name": "Strain Drops",
      "what": "White Widow, Resin Stick, Gelato, Wedding Cake, Sugar Kief, Afghani Mother, Greenbox Genesis."
    },
    {
      "when": "Every 42 days · 4:20 pm UTC",
      "name": "4:20 Halving",
      "what": "The yield per toke halves and a new era starts."
    },
    {
      "when": "Optional · 20 Apr",
      "name": "4/20 Halving",
      "what": "Launch on 9 Mar at 4:20 pm UTC and halving 1 lands on 4/20 at 4:20."
    },
    {
      "when": "Optional · 10 Jul",
      "name": "710 Day",
      "what": "Limited oil-lamp decoration drop: 710 upside down reads OIL. Not modelled."
    }
  ],
  "map": [
    {
      "bitcoin": "21M BTC cap",
      "bigcoin": "21M token cap, taken from Bitcoin",
      "greenbox": "420M BUD total. 420 comes from the 1971 4:20 pm meeting time"
    },
    {
      "bitcoin": "Origin story",
      "bigcoin": "Borrows Bitcoin's lore: the 21M cap and mining",
      "greenbox": "The 1971 hunt for an abandoned crop, using the grower's treasure map. The game's founding story"
    },
    {
      "bitcoin": "Mining",
      "bigcoin": "Miners in facilities",
      "greenbox": "Growing: strains in grow rooms, from seed to harvest"
    },
    {
      "bitcoin": "Hashpower",
      "bigcoin": "Miner hashrate",
      "greenbox": "Potency: the trichomes ('crystals') on the flower"
    },
    {
      "bitcoin": "Halvings",
      "bigcoin": "Halving every 4.2M blocks (~48.6 days)",
      "greenbox": "4:20 Halving: every 42 days, always at 4:20 pm UTC"
    },
    {
      "bitcoin": "Blocks",
      "bigcoin": "Block reward split by hashrate",
      "greenbox": "Toke: one second, one hit. The BUD goes around by potency: puff, puff, pass"
    },
    {
      "bitcoin": "Genesis block",
      "bigcoin": "Launch block",
      "greenbox": "First Meet: block 0 at 4:20 pm UTC, the 1971 meeting time"
    },
    {
      "bitcoin": "n/a",
      "bigcoin": "In-game spends are burned",
      "greenbox": "Blaze: 75% of every spend goes up in smoke"
    },
    {
      "bitcoin": "n/a",
      "bigcoin": "Share of spends kept back",
      "greenbox": "The Stash: 25% of every spend, which pays Compost refunds"
    },
    {
      "bitcoin": "n/a",
      "bigcoin": "2.5% referral reward",
      "greenbox": "Sesh Invite: 4.20% referral reward (planned, not built)"
    }
  ]
};
