using System;

namespace Greenbox
{
    [Serializable]
    public sealed class PotState
    {
        public bool owned;
        public string state;
        public double growth;
        public double moisture;
        public double health;

        public static PotState Empty(bool isOwned)
        {
            return new PotState { owned = isOwned, state = "empty", health = 100.0 };
        }

        public PotState Copy()
        {
            return new PotState { owned = owned, state = state, growth = growth, moisture = moisture, health = health };
        }
    }

    [Serializable]
    public sealed class SimSaveData
    {
        public int version = SimState.SaveVersion;
        public int level;
        public int xp;
        public int cash;
        public int selected;
        public PotState[] pots;
        public bool lamp_on;
        public bool upgraded_light;
        public bool fan;
        public int total_harvests;
    }

    [Serializable]
    public sealed class SimActionResult
    {
        public bool ok;
        public string message;
        public string eventName;
        public int xp_added;
        public int revenue;
        public bool levelup;
        public string upgrade;

        internal SimActionResult(bool success, string text, string actionEvent = "")
        {
            ok = success;
            message = text;
            eventName = actionEvent;
            upgrade = "";
        }
    }

    // Pure gameplay rules; the controller owns elapsed play time, pause, UI, and storage.
    [Serializable]
    public sealed class SimState
    {
        public const int SaveVersion = 1;
        public const int PotCount = 3;
        public const double GrowSeconds = 75.0;
        public const int SeedCost = 5;
        public const int HarvestRevenue = 30;
        public const int HarvestXp = 20;
        private const int CounterLimit = 1000000000;

        public int level = 1;
        public int xp;
        public int cash = 25;
        public int selected;
        public bool lamp_on;
        public bool upgraded_light;
        public bool fan;
        public int total_harvests;
        public PotState[] pots = { PotState.Empty(true), PotState.Empty(false), PotState.Empty(false) };

        public void Tick(double delta)
        {
            if (!Finite(delta) || delta <= 0.0 || pots == null) return;
            // Substeps keep drought behavior stable when a frame takes longer than usual.
            double remaining = Math.Min(delta, 3600.0);
            while (remaining > 0.0)
            {
                double step = Math.Min(remaining, 1.0);
                TickStep(step);
                remaining -= step;
            }
        }

        private void TickStep(double delta)
        {
            foreach (PotState pot in pots)
            {
                if (pot == null || !pot.owned || pot.state == "empty") continue;
                pot.moisture = Math.Max(0.0, pot.moisture - (fan ? 0.48 : 0.6) * delta);
                if (pot.moisture < 12.0)
                    pot.health = Math.Max(10.0, pot.health - 0.9 * delta);
                else if (pot.moisture >= 25.0)
                    pot.health = Math.Min(100.0, pot.health + (fan ? 0.6 : 0.35) * delta);
                if (lamp_on && pot.growth < 1.0)
                {
                    double waterFactor = pot.moisture >= 12.0 ? 1.0 : 0.25;
                    double healthFactor = 0.5 + pot.health / 200.0;
                    double lightFactor = upgraded_light ? 1.4 : 1.0;
                    pot.growth = Math.Min(1.0, pot.growth + delta / GrowSeconds * waterFactor * healthFactor * lightFactor);
                }
                pot.state = Stage(pot.growth);
            }
        }

        public SimActionResult Plant(int index)
        {
            string problem = PotProblem(index);
            if (problem != "") return Denied(problem);
            if (pots[index].state != "empty") return Denied("This pot already has a plant.");
            if (cash < SeedCost) return Denied("A seed costs 5 credits. Harvest a crop to earn more.");
            cash -= SeedCost;
            pots[index] = new PotState { owned = true, state = "seedling", moisture = 35.0, health = 100.0 };
            selected = index;
            return new SimActionResult(true, "Seed planted! Water it and switch on the lamp.", "planted");
        }

        public SimActionResult Water(int index)
        {
            string problem = PotProblem(index);
            if (problem != "") return Denied(problem);
            if (pots[index].state == "empty") return Denied("Plant a seed before watering.");
            pots[index].moisture = 80.0;
            pots[index].health = Math.Min(100.0, pots[index].health + 8.0);
            selected = index;
            return new SimActionResult(true, "Watered. Keep the moisture gauge out of the red.", "watered");
        }

        public SimActionResult Harvest(int index)
        {
            string problem = PotProblem(index);
            if (problem != "") return Denied(problem);
            if (pots[index].state != "ready") return Denied("This plant is still growing.");
            int previousLevel = level;
            // Saturation also makes manually edited extreme saves safe from integer overflow.
            cash = AddCounter(cash, HarvestRevenue);
            xp = AddCounter(xp, HarvestXp);
            total_harvests = AddCounter(total_harvests, 1);
            level = LevelForXp(xp);
            pots[index] = PotState.Empty(true);
            selected = index;
            string message = "Harvest sold: +30 credits and +20 XP.";
            if (level > previousLevel) message += " Level " + level + "! New upgrades unlocked.";
            return new SimActionResult(true, message, "harvested")
            {
                xp_added = HarvestXp,
                revenue = HarvestRevenue,
                levelup = level > previousLevel
            };
        }

        public SimActionResult ToggleLight()
        {
            lamp_on = !lamp_on;
            return lamp_on
                ? new SimActionResult(true, "Lamp on. Plants grow while they have water.", "light_on")
                : new SimActionResult(true, "Lamp off. Growth is paused.", "light_off");
        }

        public SimActionResult BuyUpgrade(string id)
        {
            if (id == "second_pot") id = "pot2";
            else if (id == "better_light" || id == "upgraded_light") id = "lamp";
            else if (id == "third_pot") id = "pot3";
            if (!HasThreePots()) return Denied("The pot setup is unavailable.");

            int price;
            int requiredLevel;
            bool owned;
            string label;
            switch (id)
            {
                case "pot2": price = 35; requiredLevel = 2; owned = pots[1].owned; label = "Second pot"; break;
                case "lamp": price = 45; requiredLevel = 2; owned = upgraded_light; label = "Better grow light"; break;
                case "fan": price = 30; requiredLevel = 3; owned = fan; label = "Desk fan"; break;
                case "pot3": price = 55; requiredLevel = 3; owned = pots[2].owned; label = "Third pot"; break;
                default: return Denied("Unknown upgrade.");
            }
            if (owned) return Denied("You already own this upgrade.");
            if (level < requiredLevel) return Denied(label + " unlocks at level " + requiredLevel + ".");
            if (id == "pot3" && !pots[1].owned) return Denied("Buy the second pot first.");
            if (cash < price) return Denied(label + " costs " + price + " credits.");

            cash -= price;
            switch (id)
            {
                case "pot2": pots[1] = PotState.Empty(true); break;
                case "pot3": pots[2] = PotState.Empty(true); break;
                case "lamp": upgraded_light = true; break;
                case "fan": fan = true; break;
            }
            return new SimActionResult(true, label + " installed!", "upgraded") { upgrade = id };
        }

        public string Objective()
        {
            bool planted = false;
            foreach (PotState pot in pots)
            {
                if (pot.owned && pot.state == "ready") return "Harvest your ready crop for credits and XP.";
                if (pot.owned && pot.state != "empty") planted = true;
            }
            if (!planted) return total_harvests == 0
                ? "Plant your first seed (5 credits)."
                : "Plant another crop and keep building your bedroom setup.";
            if (!lamp_on) return "Switch on your lamp to start growing.";
            foreach (PotState pot in pots)
                if (pot.owned && pot.state != "empty" && pot.moisture < 35.0) return "Water the thirsty plant.";
            if (level == 1) return "Grow and harvest your first crop to reach level 2.";
            if (level == 2 && !pots[1].owned) return "Save 35 credits for your second pot.";
            if (!upgraded_light) return "Save 45 credits for a faster grow light.";
            if (level < 3) return "Earn 60 total XP to unlock level 3 equipment.";
            if (!fan) return "Add a fan to help plants recover and conserve water.";
            if (!pots[2].owned) return "Unlock the third pot and complete your bedroom setup.";
            return "Your starter room is complete. Keep growing and earning!";
        }

        public int XpTarget() { return level == 1 ? 20 : 60; }

        public SimSaveData ToSaveData()
        {
            PotState[] copy = new PotState[pots.Length];
            for (int i = 0; i < pots.Length; i++) copy[i] = pots[i].Copy();
            return new SimSaveData
            {
                version = SaveVersion, level = level, xp = xp, cash = cash, selected = selected,
                pots = copy, lamp_on = lamp_on, upgraded_light = upgraded_light,
                fan = fan, total_harvests = total_harvests
            };
        }

        public bool TryLoad(SimSaveData data)
        {
            // Never replace live data until the entire incoming save is valid.
            if (data == null || data.version != SaveVersion || data.xp < 0 || data.cash < 0 || data.total_harvests < 0
                || data.pots == null || data.pots.Length != PotCount) return false;
            int loadedXp = Math.Min(data.xp, CounterLimit);
            int loadedLevel = LevelForXp(loadedXp);
            if (data.level != loadedLevel || (data.upgraded_light && loadedLevel < 2) || (data.fan && loadedLevel < 3)) return false;

            PotState[] loadedPots = new PotState[PotCount];
            for (int i = 0; i < PotCount; i++)
            {
                PotState raw = data.pots[i];
                if (raw == null || !KnownStage(raw.state) || !Finite(raw.growth) || !Finite(raw.moisture) || !Finite(raw.health)) return false;
                if ((i == 0 && !raw.owned) || (i > 0 && raw.owned && loadedLevel < i + 1) || (!raw.owned && raw.state != "empty")) return false;
                if (raw.state == "empty") loadedPots[i] = PotState.Empty(raw.owned);
                else
                {
                    double growth = Clamp(raw.growth, 0.0, 1.0);
                    loadedPots[i] = new PotState
                    {
                        owned = raw.owned, state = Stage(growth), growth = growth,
                        moisture = Clamp(raw.moisture, 0.0, 100.0), health = Clamp(raw.health, 10.0, 100.0)
                    };
                }
            }
            if (loadedPots[2].owned && !loadedPots[1].owned) return false;
            int loadedSelected = Math.Max(0, Math.Min(data.selected, PotCount - 1));
            if (!loadedPots[loadedSelected].owned) loadedSelected = 0;

            xp = loadedXp;
            level = loadedLevel;
            cash = Math.Min(data.cash, CounterLimit);
            selected = loadedSelected;
            lamp_on = data.lamp_on;
            upgraded_light = data.upgraded_light;
            fan = data.fan;
            total_harvests = Math.Min(data.total_harvests, CounterLimit);
            pots = loadedPots;
            return true;
        }

        private string PotProblem(int index)
        {
            if (!HasThreePots() || index < 0 || index >= PotCount) return "That pot does not exist.";
            return pots[index].owned ? "" : "Unlock this pot in the upgrade shop.";
        }

        private bool HasThreePots()
        {
            return pots != null && pots.Length == PotCount && pots[0] != null && pots[1] != null && pots[2] != null;
        }

        private static SimActionResult Denied(string message) { return new SimActionResult(false, message); }
        private static bool Finite(double value) { return !Double.IsNaN(value) && !Double.IsInfinity(value); }
        private static double Clamp(double value, double minimum, double maximum) { return Math.Max(minimum, Math.Min(value, maximum)); }
        private static int AddCounter(int value, int amount) { return (int)Math.Min(CounterLimit, (long)value + amount); }
        private static int LevelForXp(int value) { return value >= 60 ? 3 : (value >= 20 ? 2 : 1); }
        private static bool KnownStage(string value)
        {
            return value == "empty" || value == "seedling" || value == "growing" || value == "flowering" || value == "ready";
        }
        private static string Stage(double growth)
        {
            return growth >= 1.0 ? "ready" : (growth >= 0.72 ? "flowering" : (growth >= 0.25 ? "growing" : "seedling"));
        }
    }
}
