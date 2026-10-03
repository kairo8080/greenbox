// Headless balance run: a diligent player reinvests every minute against the simulated network.
// Usage: node economy/balance.mjs [hours=48] [seed=7]
import { ROOMS, STRAINS } from '../public/economy/content.js';
import { createGame, advance, claim, buyStrain, upgradeRoom, canFit, summary, playerWatts, uproot, sellBack, lockLeft } from '../public/economy/engine.js';

const hours = Number(process.argv[2] || 48);
const state = createGame(Number(process.argv[3] || 7));
const seen = new Set();
const fmt = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : n.toFixed(2));
const stamp = () => `${(state.height / 3600).toFixed(2)}h`;

function play() {
  claim(state);
  for (let guard = 0; guard < 50; guard++) {
    const p = state.player;
    const room = ROOMS[p.room];
    const choices = STRAINS.filter((s) => !s.starter && s.cost <= p.wallet && !canFit(state, s.id));
    choices.sort((a, b) => b.potency / b.cost - a.potency / a.cost);
    if (choices.length) {
      buyStrain(state, choices[0].id);
      if (!seen.has(choices[0].id)) { seen.add(choices[0].id); console.log(`${stamp()} first ${choices[0].name}`); }
      continue;
    }
    const full = p.slots.length >= room.slots - 1 || room.watts - playerWatts(state) < 30;
    if (full && upgradeRoom(state).ok) { console.log(`${stamp()} room -> ${ROOMS[p.room].name}`); continue; }
    if (full && replaceWeakest()) continue;
    break;
  }
}

// Compost the weakest unlocked strain when a strain at least twice as strong is affordable and would fit in its place.
function replaceWeakest() {
  const p = state.player;
  const room = ROOMS[p.room];
  const planted = p.slots.filter((s) => s.kind === 'strain' && lockLeft(state, s) === 0);
  if (!planted.length) return false;
  const byId = Object.fromEntries(STRAINS.map((s) => [s.id, s]));
  planted.sort((a, b) => byId[a.id].potency - byId[b.id].potency);
  const weak = byId[planted[0].id];
  const better = STRAINS.filter((s) => s.cost <= p.wallet && s.potency > weak.potency * 2 &&
    playerWatts(state) - weak.watts + s.watts <= room.watts);
  if (!better.length) return false;
  uproot(state, planted[0].uid);
  sellBack(state, p.inventory[p.inventory.length - 1].uid);
  return true;
}

for (let h = 0; h < hours * 60; h++) {
  advance(state, 60);
  play();
  if ((h + 1) % 240 === 0) {
    const s = summary(state);
    console.log(`-- ${stamp()} reward ${s.reward} growers ${s.activeGrowers} net ${fmt(s.networkPotency)} mine ${fmt(s.potency)} ` +
      `share ${(s.share * 100).toFixed(2)}% ${fmt(s.perHour)}/h wallet ${fmt(state.player.wallet)} ` +
      `minted ${fmt(state.token.minted)} burned ${fmt(state.token.burned)} treasury ${fmt(state.token.treasury)}`);
  }
}
