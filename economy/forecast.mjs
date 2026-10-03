// Precomputes the live-launch forecast the Assets, Tasks & ROI and CFO tabs read.
// Usage: node economy/forecast.mjs  (writes public/economy/forecast.json; deterministic for a given seed)
import { writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { ROOMS, STRAINS, COSMETICS } from '../public/economy/content.js';
import { createGame, advance, summary, LIVE_CONFIG } from '../public/economy/engine.js';
import { checkIn, grantPack } from './strategy.mjs';

const SEED = 20261003;
const HOUR = 3600;
const DAYS = 14;
const SNAP_HOURS = [1, 6, 12, 24, 48, 72, 120, 168, 240, 336];
const ARCHETYPES = [
  { id: 'f2p_casual', name: 'Free, checks in every 12h', every: 12, automate: false },
  { id: 'f2p_active', name: 'Free, checks in hourly', every: 1, automate: false },
  { id: 'founder_daily', name: 'Founder Pack, once a day, manual', every: 24, automate: false, pack: 'founder' },
  { id: 'founder_auto', name: 'Founder Pack, once a day + automation', every: 24, automate: true, pack: 'founder' },
  { id: 'grower_auto', name: 'Grower Pack, once a day + automation', every: 24, automate: true, pack: 'grower' },
];
const round = (n, d = 2) => Math.round(n * 10 ** d) / 10 ** d;

function snapshotPlayer(state) {
  const s = summary(state);
  const p = state.player;
  return {
    hour: state.height / HOUR,
    earned: round(p.earnedTotal), spoiled: round(p.spoiledTotal), spent: round(p.spent),
    wallet: round(p.wallet + p.pending), room: p.room, potency: Math.round(s.potency), share: s.share,
    perDay: round(s.perHour * 24), utilities: [...p.utilities],
  };
}

function runPlayer(arch, cfg = LIVE_CONFIG) {
  const state = createGame(SEED, cfg);
  if (arch.pack) grantPack(state, cfg.packs.find((x) => x.id === arch.pack));
  const snaps = [];
  const events = [];
  const onEvent = (e) => { if (events.length < 40 && !events.some((x) => x.e === e)) events.push({ hour: round(state.height / HOUR, 1), e }); };
  for (let h = 1; h <= DAYS * 24; h++) {
    advance(state, HOUR);
    if (h % arch.every === 0) checkIn(state, { automate: arch.automate, onEvent });
    if (SNAP_HOURS.includes(h)) snaps.push(snapshotPlayer(state));
  }
  return { ...arch, snaps, events };
}

function gameRun(cfg = LIVE_CONFIG) {
  const state = createGame(SEED, cfg);
  const hourly = [];
  const sample = () => {
    const t = state.token;
    const active = state.bots.filter((b) => b.active);
    const rooms = new Array(ROOMS.length).fill(0);
    for (const b of active) rooms[b.room] += b.count;
    hourly.push({
      hour: state.height / HOUR, players: state.stats.players, active: active.reduce((n, b) => n + b.count, 0) + 1,
      network: Math.round(summary(state).networkPotency), minted: round(t.minted), burned: round(t.burned),
      treasury: round(t.treasury), spoiled: round(t.spoiled), dormant: round(t.dormant),
      bought: round(state.market.bought), sold: round(state.market.sold), float: round(state.market.float),
      spendBy: Object.fromEntries(Object.entries(state.spendBy).map(([k, v]) => [k, round(v)])),
      packs: { ...state.stats.packs }, items: { ...state.sold }, rooms,
    });
  };
  sample();
  for (let h = 1; h <= DAYS * 24; h++) {
    advance(state, HOUR);
    sample();
  }
  const daily = [];
  for (let d = DAYS + 1; d <= 49; d++) {
    advance(state, 24 * HOUR);
    const t = state.token;
    daily.push({ day: d, players: state.stats.players, minted: round(t.minted), burned: round(t.burned), treasury: round(t.treasury), items: { ...state.sold } });
  }
  return { hourly, daily };
}

// Exported so balance experiments can run the same forecast on another config without writing the file.
export function buildForecast(cfg = LIVE_CONFIG) {
  return {
    generated: 'node economy/forecast.mjs',
    seed: SEED,
    config: cfg,
    catalog: { rooms: ROOMS, strains: STRAINS, cosmetics: COSMETICS },
    game: gameRun(cfg),
    players: ARCHETYPES.map((arch) => runPlayer(arch, cfg)),
  };
}

function main() {
  const started = Date.now();
  const out = buildForecast();
  writeFileSync(new URL('../public/economy/forecast.json', import.meta.url), JSON.stringify(out));
  console.log(`forecast.json written in ${((Date.now() - started) / 1000).toFixed(1)}s`);
  for (const p of out.players) {
    const last = p.snaps[p.snaps.length - 1];
    const d1 = p.snaps.find((s) => s.hour === 24);
    console.log(`${p.name.padEnd(28)} day1 earned ${d1.earned} room ${d1.room} | day14 earned ${last.earned} spoiled ${last.spoiled} room ${last.room} ${last.perDay}/day`);
  }
  const g = out.game.hourly[out.game.hourly.length - 1];
  console.log('game day14', JSON.stringify({ players: g.players, minted: g.minted, burned: g.burned, treasury: g.treasury, spoiled: g.spoiled, spendBy: g.spendBy, packs: g.packs, items: g.items }));
}

// Write the file only when run as a script, not when imported.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();
