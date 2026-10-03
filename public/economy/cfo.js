// Launch finance model: turns the BUD flows in forecast.json into USD using a constant-product
// BUD/USD pool, starter pack sales and the studio's revenue allocation. Pure functions; the CFO tab drives them.

export const DEFAULT_ASSUMPTIONS = {
  launchPrice: 0.025, // USD per BUD when the pool opens
  lpUsd: 25000, // USD the studio seeds into the BUD/USD pool at launch
  founderPrice: 20, // USD, Garage + 2 Skunk #1
  growerPrice: 75, // USD, Garden Shed + 4 Skunk #1 + OG Kush
  buybackPct: 30, // % of pack revenue used to buy BUD from the pool and burn it
  lpPct: 30, // % of pack revenue added to the pool, paired with treasury BUD
  treasurySellPct: 20, // % of treasury BUD inflow sold for operating cash
  paybackDays: 14, // target payback for a pack buyer
};

export const PACKS = [
  { id: 'founder', name: 'Founder Pack', contents: 'Garage + 2 Skunk #1', priceKey: 'founderPrice' },
  { id: 'grower', name: 'Grower Pack', contents: 'Garden Shed + 4 Skunk #1 + OG Kush', priceKey: 'growerPrice' },
];

export function runModel(hourly, a) {
  const P0 = a.launchPrice;
  let U = a.lpUsd;
  let B = a.lpUsd / P0; // BUD liquidity reserve paired at launch (pre-minted, outside mining emission)
  const reserve = B;
  let treasuryBud = 0;
  let opsUsd = 0;
  let lpAddedUsd = 0;
  let buybackBurned = 0;
  let buyerUsd = 0;
  let sellerUsd = 0;
  let packUsd = 0;
  const path = [{ hour: 0, price: P0, U, B }];
  for (let i = 1; i < hourly.length; i++) {
    const h = hourly[i];
    const prev = hourly[i - 1];
    // Growers sell part of what they harvest.
    const sold = h.sold - prev.sold;
    if (sold > 0) {
      const k = U * B;
      const nb = B + sold;
      sellerUsd += U - k / nb;
      U = k / nb;
      B = nb;
    }
    // Newcomers buy BUD to skip ahead.
    const bought = Math.min(h.bought - prev.bought, B * 0.5);
    if (bought > 0) {
      const k = U * B;
      const nb = B - bought;
      buyerUsd += k / nb - U;
      U = k / nb;
      B = nb;
    }
    // Starter packs are sold for USD; the studio splits the revenue.
    let revenue = 0;
    for (const pack of PACKS) revenue += ((h.packs[pack.id] || 0) - (prev.packs[pack.id] || 0)) * a[pack.priceKey];
    packUsd += revenue;
    const buyback = (revenue * a.buybackPct) / 100;
    if (buyback > 0) {
      const k = U * B;
      const nu = U + buyback;
      buybackBurned += B - k / nu;
      B = k / nu;
      U = nu;
    }
    treasuryBud += h.treasury - prev.treasury;
    const lpUsd = (revenue * a.lpPct) / 100;
    if (lpUsd > 0) {
      const pairBud = Math.min(treasuryBud, (lpUsd * B) / U);
      const pairUsd = (pairBud * U) / B;
      treasuryBud -= pairBud;
      B += pairBud;
      U += pairUsd;
      lpAddedUsd += pairUsd;
      opsUsd += lpUsd - pairUsd; // unpaired remainder stays as cash
    }
    opsUsd += revenue - buyback - lpUsd;
    // Treasury sells part of its BUD inflow for operating cash.
    const tSell = (Math.max(0, h.treasury - prev.treasury) * a.treasurySellPct) / 100;
    if (tSell > 0 && treasuryBud >= tSell) {
      const k = U * B;
      const nb = B + tSell;
      opsUsd += U - k / nb;
      U = k / nb;
      B = nb;
      treasuryBud -= tSell;
    }
    path.push({ hour: h.hour, price: U / B, U, B });
  }
  const last = path[path.length - 1];
  return {
    path, reserve, treasuryBud, opsUsd, lpAddedUsd, buybackBurned, buyerUsd, sellerUsd, packUsd,
    price: last.price, poolUsd: last.U, treasuryUsd: treasuryBud * last.price,
  };
}

export function priceAt(model, hour) {
  let best = model.path[0];
  for (const p of model.path) if (p.hour <= hour) best = p;
  return best.price;
}
