// Scripted player for balance runs and forecasts: at each check-in it does the manual tasks, then reinvests greedily.
import { ROOMS, STRAINS, UTILITIES } from '../public/economy/content.js';
import {
  claim, water, buyStrain, buyUtility, upgradeRoom, canFit, playerWatts, uproot, sellBack, lockLeft,
  isUnlocked, supplyLeft, strainWatts,
} from '../public/economy/engine.js';

const byId = Object.fromEntries(STRAINS.map((s) => [s.id, s]));
const utilCost = (id) => UTILITIES.find((u) => u.id === id).cost;

// Gives the player a USD starter pack at launch, the same way simulated founders get theirs.
export function grantPack(state, pack) {
  const p = state.player;
  p.room = pack.room;
  for (const id of pack.strains) p.slots.push({ uid: p.nextUid++, kind: 'strain', id, plantedAt: 0 });
}

export function checkIn(state, { automate = false, onEvent = () => {} } = {}) {
  claim(state);
  water(state);
  const p = state.player;
  const has = (id) => p.utilities.includes(id);
  if (automate) {
    if (!has('drip') && p.wallet >= utilCost('drip')) buyUtility(state, 'drip');
    if (!has('trimmer') && p.wallet >= utilCost('trimmer')) buyUtility(state, 'trimmer');
  }
  for (let guard = 0; guard < 60; guard++) {
    const room = ROOMS[p.room];
    const choices = STRAINS.filter((s) => !s.starter && s.cost <= p.wallet && isUnlocked(state, s) &&
      supplyLeft(state, s) !== 0 && !canFit(state, s.id));
    choices.sort((a, b) => b.potency / b.cost - a.potency / a.cost);
    if (choices.length) {
      buyStrain(state, choices[0].id);
      onEvent(`bought ${choices[0].name}`);
      continue;
    }
    const freeWatts = room.watts - playerWatts(state);
    const full = p.slots.length >= room.slots - 1 || freeWatts < 30;
    if (full && upgradeRoom(state).ok) { onEvent(`moved into ${ROOMS[p.room].name}`); continue; }
    if (!has('led') && p.slots.length < room.slots - 1 && freeWatts < 30 && buyUtility(state, 'led').ok) { onEvent('installed LED Retrofit'); continue; }
    if (!has('co2') && p.room >= 4 && buyUtility(state, 'co2').ok) { onEvent('installed CO2 Generator'); continue; }
    if (full && replaceWeakest(state)) continue;
    break;
  }
}

// Compost the weakest unlocked strain when one at least twice as strong is affordable and fits in its place.
function replaceWeakest(state) {
  const p = state.player;
  const room = ROOMS[p.room];
  const planted = p.slots.filter((s) => s.kind === 'strain' && lockLeft(state, s) === 0);
  if (!planted.length) return false;
  planted.sort((a, b) => byId[a.id].potency - byId[b.id].potency);
  const weak = byId[planted[0].id];
  const better = STRAINS.filter((s) => s.cost <= p.wallet && s.potency > weak.potency * 2 && isUnlocked(state, s) &&
    supplyLeft(state, s) !== 0 &&
    playerWatts(state) - strainWatts(p.utilities, weak) + strainWatts(p.utilities, s) <= room.watts);
  if (!better.length) return false;
  uproot(state, planted[0].uid);
  sellBack(state, p.inventory[p.inventory.length - 1].uid);
  return true;
}
