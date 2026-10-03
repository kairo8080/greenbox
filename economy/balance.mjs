// Headless balance run on the demo schedule: a diligent player reinvests every minute against the simulated network.
// Usage: node economy/balance.mjs [hours=48] [seed=7]
import { ROOMS } from '../public/economy/content.js';
import { createGame, advance, summary } from '../public/economy/engine.js';
import { checkIn } from './strategy.mjs';

const hours = Number(process.argv[2] || 48);
const state = createGame(Number(process.argv[3] || 7));
const seen = new Set();
const fmt = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : n.toFixed(2));
const stamp = () => `${(state.height / 3600).toFixed(2)}h`;
const onEvent = (e) => {
  const key = e.startsWith('bought') ? e : `${e} ${ROOMS[state.player.room].id}`;
  if (!seen.has(key)) { seen.add(key); console.log(`${stamp()} ${e}`); }
};

for (let m = 0; m < hours * 60; m++) {
  advance(state, 60);
  checkIn(state, { onEvent });
  if ((m + 1) % 240 === 0) {
    const s = summary(state);
    console.log(`-- ${stamp()} reward ${s.reward} growers ${s.activeGrowers} net ${fmt(s.networkPotency)} mine ${fmt(s.potency)} ` +
      `share ${(s.share * 100).toFixed(2)}% ${fmt(s.perHour)}/h wallet ${fmt(state.player.wallet)} ` +
      `minted ${fmt(state.token.minted)} burned ${fmt(state.token.burned)} treasury ${fmt(state.token.treasury)}`);
  }
}
