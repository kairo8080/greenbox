# Greenbox grow economy

A playable browser prototype of Greenbox's game mechanics and token economy, using the original BigCoin
idle-mining game as the blueprint and reskinning server mining as a cannabis grow operation. The UI is
deliberately a plain placeholder; the point is to play-test the rules and the numbers.

- Play: `public/economy/index.html` (served at `/economy/` on the Vercel site; any static server works).
- Engine: `public/economy/engine.js` (pure, deterministic, no DOM) and `public/economy/content.js` (rooms, strains, decorations, badges).
- Tests: `npm run test:economy` (also runs as the first step of `npm run build`).
- Balance run: `npm run balance -- [hours] [seed]` plays a diligent player against the simulated network and prints milestones.

Everything is simulated in the browser. There is no wallet, chain, or real token, and the other growers are bots.

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

## The simulated network

The season launches with 40 bot growers plus you, each holding a free Bagseed (a fair launch). Bots:

- earn by the same pro-rata rule and spend with the same burn split, so supply, burn and treasury numbers are coherent;
- check in at their own pace (every minute to about once an hour), keep up to 30% of their balance unspent, buy the most potency per BUD that fits, upgrade when full, and replace their weakest strain once their room is maxed or on cooldown;
- join with launch hype (decaying with a 6 hour half-life) and occasionally quit, about 12 times as often in the hour after a halving;
- buy limited decorations now and then, so drops can sell out.

Bots ignore the rooting lock. Quitting bots' balances count as dormant supply.

## What the balance run shows

`npm run balance -- 24 7`, with a player who reinvests every minute:

```text
0.03h first Ditch Weed
0.13h room -> Garage
0.50h first Skunk #1
1.13h room -> Garden Shed
2.13h room -> Basement
3.13h room -> Greenhouse
5.03h room -> High Voltage Warehouse
7.60h room -> Vertical Farm
20.80h room -> Biodome I
```

That player holds 14-22% of the network, competing with a handful of diligent bots, while late joiners stay stuck on
a Bagseed. This is BigCoin's early-miner advantage and the reason critics called it Ponzi-like: income per hour falls with
each halving and as network potency grows, so the only way to keep your share is to keep reinvesting. About 75-80% of
everything minted ends up burned in a typical run.

## Not built yet

Referrals (BigCoin paid 2.5% of referees' mining), a secondary market for strains, BigCoin 2.0 merge mining, any
on-chain token, and real art. The Unity and Godot grow-room games elsewhere in this repository use separate, simpler rules.
