# Greenbox grow economy

A playable browser prototype of Greenbox's game mechanics and token economy, using the original BigCoin
idle-mining game as the blueprint and reskinning server mining as a cannabis grow operation. The UI is
deliberately a plain placeholder; the point is to play-test the rules and the numbers.

- Page: `public/economy/index.html` (served at `/economy/` on the Vercel site; any static server works). Four tabs:
  - **Play demo**: the game on the compressed demo schedule, with a minimal canvas view of the room.
  - **Assets**: every room, strain, utility, decoration and starter pack, with category, what it adds, BUD and USD price, output, payback, supply cap, release day and forecast sales.
  - **Tasks & ROI**: manual tasks and the utilities that automate them, an automation payback calculator, hour/day/week progress for five player types, and a whole-game developer view.
  - **CFO**: launch assumptions (editable), price path, what to sell first, where revenue goes, and how much payout keeps the flywheel turning.
- Engine: `public/economy/engine.js` (pure, deterministic, no DOM) and `public/economy/content.js` (items). `public/economy/cfo.js` is the USD model.
- Forecast: `npm run forecast` regenerates `public/economy/forecast.json` (live schedule, 14 days hourly plus days 15-49). Rerun it after changing `LIVE_CONFIG` or content; a test fails when it is stale.
- Tests: `npm run test:economy` (also the first step of `npm run build`).
- Balance run: `npm run balance -- [hours] [seed]` plays a diligent player on the demo schedule.

Everything is simulated. There is no wallet, chain, or real token, and other growers are bots.

## Blueprint mapping

| BigCoin | Greenbox |
| --- | --- |
| $BIG token | BUD |
| Facility (slots, power limit, upgrade cost, 24h cooldown) | Grow room: Closet → Biodome II, same nine tiers and numbers |
| Miner NFT (hashrate, power draw) | Strain: Bagseed (free starter) → Greenbox Genesis, 13 strains |
| Hashpower share of the network | Potency share of the network |
| Staking lock | Rooting lock after planting |
| Sell miner back (burned) | Compost: burns it, refunds 20% of its price from the treasury |
| Cosmetics (take a slot, no power, limited drops) | Decorations |
| Badges | Badges |
| Claim rewards | Harvest |

Room numbers and six strain rows (Bagseed, Ditch Weed, Skunk #1, OG Kush, Runtz, Greenbox Genesis) copy BigCoin's
published Facilities and Miners tables. The other seven strains are interpolated so value per BUD rises with tier.
The 20% compost refund, decoration prices and badges are Greenbox inventions; BigCoin's docs do not give them.

## Token rules

- Each block (one game second) mints the block reward, split across every active grower by `your potency / network potency`.
- Reward starts at 2.5 BUD (BigCoin's figure) and halves every 43,200 blocks (12 hours at 1×). That caps the season at 216,000 BUD.
  BigCoin halves every 4.2M blocks (about 51 days) with a 21M cap; the schedule is compressed so halvings happen while you play. All of this is in `DEFAULT_CONFIG`.
- Every purchase burns 75% and sends 25% to the treasury. Compost refunds come out of the treasury and stop when it is empty.
- Strains you mint plant straight away when they fit, otherwise they go to inventory. Planted strains are locked for 30 minutes.
- Room upgrades go one tier at a time with a 1 hour cooldown.

## Tasks, utilities and the live schedule

- **Harvest**: earnings sit in a drying rack. After 12 hours without a harvest the rack is full and new earnings spoil (removed from supply). The **Auto-Trimmer** (40 BUD) harvests hourly.
- **Water**: one watering lasts 4 hours; a dry room runs at 50% potency. **Drip Irrigation** (60 BUD) waters automatically.
- **CO2 Generator** (400 BUD) adds 10% potency. **LED Retrofit** (250 BUD) cuts strain power draw by 25%, so more plants fit.
- **Seedling pool**: 15% of every block is shared per head among growers who are still in the Closet and joined less than 7 days ago, so free players can afford their first upgrades.
- **Live schedule** (`LIVE_CONFIG`, used by the forecast): BigCoin's real halving (4.2M blocks, 21M cap), 24h room cooldown and rooting lock, staged strain releases (White Widow day 1 to Greenbox Genesis day 14) and season supply caps on the six top strains.
- **Starter packs** (live only): Founder Pack (Garage + 2 Skunk #1) and Grower Pack (Garden Shed + 4 Skunk #1 + OG Kush), sold for USD. They are the only outside cash in the model.
- **Market**: simulated growers sell 25% of each harvest; some newcomers buy BUD on joining (40% buy about 100 BUD, 8% about 1,500). The CFO tab turns those flows into a USD price with a constant-product pool.
- Live growers are cohorts of 25 players, which keeps a 20,000-player forecast fast.

## The simulated network

On the demo schedule the season launches with 40 bot growers plus you, each holding a free Bagseed. Bots:

- earn by the same pro-rata rule and spend with the same burn split, so supply, burn and treasury numbers are coherent;
- check in at their own pace (every minute to about once an hour), keep up to 30% of their balance unspent, buy the most potency per BUD that fits, upgrade when full, and replace their weakest strain once their room is maxed or on cooldown;
- join with launch hype (decaying with a 6 hour half-life) and occasionally quit, about 12 times as often in the hour after a halving;
- buy limited decorations now and then, so drops can sell out.

Bots also buy Drip Irrigation and the Auto-Trimmer when their check-in habit would cost them output, and CO2 and LED later. Bots ignore the rooting lock. Quitting bots' balances count as dormant supply.

## What the forecast shows (live schedule, default CFO assumptions)

- 1,500 players at launch, about 20,000 by day 14 and 38,000 by day 49.
- About 64% of minted BUD is burned by day 14.
- A free player who checks in every 12 hours has about 59 BUD and a Garage by day 14. A Founder Pack player on a daily check-in earns 545 BUD manually and 757 BUD with Drip Irrigation and an Auto-Trimmer (100 BUD).
- With a $0.025 launch price, a $25k pool and 30% of pack revenue to buybacks, the modeled price reaches about $0.07 by day 14, funded by newcomer buying and buybacks.

On the demo schedule (`npm run balance`) a player who reinvests every minute holds about 9-12% of the network,
competing with a handful of diligent bots, while late joiners stay small. This is BigCoin's early-miner advantage and the reason critics called it Ponzi-like: income per hour falls with
each halving and as network potency grows, so the only way to keep your share is to keep reinvesting. About 75% of
everything minted ends up burned in a typical demo run.

## Not built yet

Referrals (BigCoin paid 2.5% of referees' mining), a secondary market for strains, BigCoin 2.0 merge mining, any
on-chain token, and real art. The 20% compost refund, utilities, seedling pool, starter packs, buy-in and sell rates,
and the USD launch figures are Greenbox assumptions, not BigCoin data. The Unity and Godot grow-room games elsewhere in this repository use separate, simpler rules.
