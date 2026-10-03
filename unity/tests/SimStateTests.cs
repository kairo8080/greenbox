using System;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using Greenbox;

// Standalone domain checks: compile against the real System runtime, without Unity stubs.
internal static class SimStateTests
{
    private static int checks;
    private static readonly List<string> failures = new List<string>();

    public static int Main()
    {
        try
        {
            StarterAndCare();
            ProgressionAndPurchases();
            TimeAndStress();
            SaveValidation();
            JsonRoundTrip();
        }
        catch (Exception exception)
        {
            failures.Add("Unexpected exception: " + exception);
        }
        foreach (string failure in failures) Console.Error.WriteLine("FAIL: " + failure);
        Console.WriteLine("SIM_STATE_TESTS: " + checks + " checks; " + failures.Count + " failures");
        return failures.Count == 0 ? 0 : 1;
    }

    private static void Check(bool condition, string label)
    {
        checks++;
        if (!condition) failures.Add(label);
    }

    private static bool Near(double first, double second)
    {
        return Math.Abs(first - second) < 0.000000001;
    }

    private static SimActionResult Crop(SimState state, int index)
    {
        Check(state.Plant(index).ok, "A crop can be planted in an owned empty pot");
        if (!state.lamp_on) state.ToggleLight();
        for (int i = 0; i < 80 && state.pots[index].state != "ready"; i++)
        {
            if (state.pots[index].moisture < 45.0) state.Water(index);
            state.Tick(1.0);
        }
        return state.Harvest(index);
    }

    private static void StarterAndCare()
    {
        SimState state = new SimState();
        Check(state.level == 1 && state.xp == 0 && state.cash == 25 && state.selected == 0, "Starter economy and selection");
        Check(state.pots.Length == 3 && state.pots[0].owned && !state.pots[1].owned && !state.pots[2].owned, "Exactly one of three pots starts owned");
        Check(!state.lamp_on && !state.upgraded_light && !state.fan && state.XpTarget() == 20, "Starter equipment and XP target");
        Check(!state.Water(0).ok && !state.Harvest(0).ok, "Empty pots deny watering and harvesting");
        Check(!state.Plant(-1).ok && !state.Plant(3).ok && !state.Plant(1).ok, "Invalid and locked pot indices deny safely");
        Check(state.Plant(0).ok && state.cash == 20 && state.pots[0].state == "seedling", "Seed costs five credits");
        Check(!state.Plant(0).ok && state.cash == 20, "Duplicate planting does not charge");
        state.Tick(5.0);
        Check(state.pots[0].growth == 0.0 && state.pots[0].moisture < 35.0, "Lamp off stops growth but not evaporation");
        Check(!state.Harvest(0).ok, "Immature harvest denies");
        Check(state.Water(0).ok && state.pots[0].moisture == 80.0, "Water restores moisture");
        for (int i = 0; i < 20; i++) state.Water(0);
        Check(state.xp == 0 && state.cash == 20, "Repeated water awards no XP or money");
        Check(state.ToggleLight().ok && state.lamp_on, "Lamp toggle succeeds");
        state.Tick(25.0);
        Check(state.pots[0].state == "growing" && state.pots[0].growth > 0.25, "Growing stage appears");
        state.Tick(30.0);
        Check(state.pots[0].state == "flowering", "Flowering stage appears");
        state.Tick(25.0);
        Check(state.pots[0].state == "ready" && state.pots[0].growth == 1.0, "Cared-for crop becomes ready");
        SimActionResult reward = state.Harvest(0);
        Check(reward.ok && reward.eventName == "harvested" && reward.xp_added == 20 && reward.revenue == 30 && reward.levelup, "Harvest reports exact rewards");
        Check(state.cash == 50 && state.xp == 20 && state.level == 2 && state.total_harvests == 1 && state.XpTarget() == 60, "First harvest progresses to level two");
        Check(state.pots[0].state == "empty" && !state.Harvest(0).ok && state.cash == 50 && state.xp == 20, "Cleared pot blocks double rewards");
        SimState poor = new SimState { cash = 4 };
        Check(!poor.Plant(0).ok && poor.cash == 4 && poor.pots[0].state == "empty", "Insufficient funds leaves pot unchanged");
    }

    private static void ProgressionAndPurchases()
    {
        SimState state = new SimState();
        foreach (string id in new[] { "pot2", "lamp", "fan", "pot3" })
            Check(!state.BuyUpgrade(id).ok && state.cash == 25, "Level one gate denies " + id);
        Check(!state.BuyUpgrade(null).ok && !state.BuyUpgrade("missing").ok, "Unknown upgrades deny safely");
        Crop(state, 0);
        Check(state.BuyUpgrade("second_pot").ok && state.pots[1].owned && state.cash == 15, "Second-pot alias spends exact price");
        Check(!state.BuyUpgrade("pot2").ok && state.cash == 15, "Duplicate upgrade cannot charge");
        Check(!state.BuyUpgrade("lamp").ok && !state.upgraded_light && state.cash == 15, "Unaffordable upgrade cannot charge");
        Check(!state.BuyUpgrade("fan").ok, "Level two denies fan");
        Crop(state, 1);
        Check(state.level == 2 && state.xp == 40, "Second harvest remains level two");
        Check(Crop(state, 0).levelup && state.level == 3 && state.xp == 60, "Third harvest unlocks level three");
        Check(state.BuyUpgrade("better_light").ok && state.upgraded_light && state.cash == 20, "Better-light alias spends exact price");
        Crop(state, 0);
        Check(state.BuyUpgrade("fan").ok && state.fan && state.cash == 15, "Fan purchases at level three");
        Crop(state, 0);
        Crop(state, 1);
        Check(state.BuyUpgrade("third_pot").ok && state.pots[2].owned && state.cash == 10, "Third-pot alias completes the room");
        Check(state.level == 3 && !state.BuyUpgrade("lamp").ok, "Progression caps at three and equipment is purchased once");
        SimState prerequisite = new SimState { xp = 60, level = 3, cash = 100 };
        Check(!prerequisite.BuyUpgrade("pot3").ok && prerequisite.cash == 100, "Third pot requires second pot");
        SimState lampFirst = new SimState();
        Crop(lampFirst, 0);
        Check(lampFirst.BuyUpgrade("lamp").ok && lampFirst.cash == 5 && lampFirst.Plant(0).ok, "First-harvest lamp purchase leaves enough for another seed");
    }

    private static void TimeAndStress()
    {
        SimState dry = new SimState();
        dry.Plant(0);
        dry.ToggleLight();
        dry.Tick(100.0);
        Check(dry.pots[0].moisture == 0.0 && dry.pots[0].health < 100.0 && dry.pots[0].state != "ready", "Drought lowers health and slows growth");
        dry.Water(0);
        double healthAfterWater = dry.pots[0].health;
        dry.Tick(10.0);
        Check(dry.pots[0].health > healthAfterWater, "Neglected plants recover");
        dry.Tick(100000.0);
        Check(dry.pots[0].health >= 10.0 && dry.pots[0].growth <= 1.0, "Large tick retains safe bounds without permanent death");

        SimState normal = new SimState();
        normal.Plant(0); normal.Water(0); normal.ToggleLight();
        SimState faster = new SimState();
        faster.Plant(0); faster.Water(0); faster.ToggleLight(); faster.upgraded_light = true;
        normal.Tick(54.0); faster.Tick(54.0);
        Check(faster.pots[0].state == "ready" && normal.pots[0].state != "ready", "Improved lamp shortens crop cycle");
        SimState withFan = new SimState { fan = true };
        withFan.Plant(0); withFan.Water(0); withFan.Tick(20.0);
        Check(Near(withFan.pots[0].moisture, 70.4), "Fan conserves moisture at exact rate");
        double before = normal.pots[0].growth;
        normal.Tick(-1.0); normal.Tick(Double.NaN); normal.Tick(Double.PositiveInfinity);
        Check(normal.pots[0].growth == before, "Invalid deltas do not advance simulation");

        SimState coarse = new SimState();
        coarse.Plant(0); coarse.Water(0); coarse.ToggleLight(); coarse.Tick(20.0);
        SimState fine = new SimState();
        fine.Plant(0); fine.Water(0); fine.ToggleLight();
        for (int i = 0; i < 200; i++) fine.Tick(0.1);
        Check(Near(coarse.pots[0].growth, fine.pots[0].growth) && Near(coarse.pots[0].moisture, fine.pots[0].moisture), "Healthy simulation agrees across frame sizes");
    }

    private static void SaveValidation()
    {
        SimState source = new SimState();
        Crop(source, 0); source.BuyUpgrade("pot2"); source.Plant(1); source.ToggleLight(); source.Water(1);
        SimSaveData saved = source.ToSaveData();
        SimState loaded = new SimState();
        Check(loaded.TryLoad(saved) && Same(source.ToSaveData(), loaded.ToSaveData()), "Valid model snapshot restores all fields");
        saved.pots[1].growth = 0.99;
        Check(source.pots[1].growth != 0.99 && loaded.pots[1].growth != 0.99, "Save and loaded model have independent pot objects");

        SimSaveData baseline = loaded.ToSaveData();
        List<Action<SimSaveData>> corruptions = new List<Action<SimSaveData>>
        {
            d => d.version = 2, d => d.xp = -1, d => d.cash = -1, d => d.total_harvests = -1,
            d => d.level = 3, d => d.fan = true, d => d.pots = null,
            d => d.pots = new PotState[2], d => d.pots[1] = null, d => d.pots[1].state = "unknown",
            d => d.pots[1].state = null, d => d.pots[1].growth = Double.NaN,
            d => d.pots[1].moisture = Double.PositiveInfinity, d => d.pots[1].health = Double.NegativeInfinity,
            d => d.pots[0].owned = false, d => d.pots[2].state = "ready", d => d.pots[2].owned = true
        };
        Check(!loaded.TryLoad(null) && Same(baseline, loaded.ToSaveData()), "Null save rejection is atomic");
        for (int i = 0; i < corruptions.Count; i++)
        {
            SimSaveData malformed = source.ToSaveData();
            corruptions[i](malformed);
            Check(!loaded.TryLoad(malformed) && Same(baseline, loaded.ToSaveData()), "Malformed save " + i + " rejection is atomic");
        }
        SimSaveData normalized = source.ToSaveData();
        normalized.pots[1].growth = 5.0; normalized.pots[1].moisture = -2.0; normalized.pots[1].health = 150.0; normalized.selected = 2;
        Check(loaded.TryLoad(normalized), "Finite out-of-range plant gauges normalize");
        Check(loaded.selected == 0 && loaded.pots[1].state == "ready" && loaded.pots[1].growth == 1.0 && loaded.pots[1].moisture == 0.0 && loaded.pots[1].health == 100.0, "Normalized gauges and locked selection have safe values");
        SimSaveData extreme = new SimState { level = 3, xp = Int32.MaxValue, cash = Int32.MaxValue, total_harvests = Int32.MaxValue }.ToSaveData();
        extreme.pots[0] = new PotState { owned = true, state = "ready", growth = 1.0, moisture = 80.0, health = 100.0 };
        Check(loaded.TryLoad(extreme) && loaded.Harvest(0).ok && loaded.cash == 1000000000 && loaded.xp == 1000000000 && loaded.total_harvests == 1000000000, "Extreme edited counters cannot overflow on harvest");
        SimSaveData prerequisite = new SimState { level = 3, xp = 60 }.ToSaveData();
        prerequisite.pots[2].owned = true;
        Check(!loaded.TryLoad(prerequisite), "Saved third pot requires saved second pot");
    }

    private static void JsonRoundTrip()
    {
        SimState source = new SimState();
        Crop(source, 0); source.BuyUpgrade("pot2"); source.Plant(1); source.Water(1); source.Tick(12.345);
        JavaScriptSerializer serializer = new JavaScriptSerializer();
        string json = serializer.Serialize(source.ToSaveData());
        Check(json.Contains("\"version\":1") && json.Contains("\"lamp_on\"") && json.Contains("\"pots\""), "JSON retains version and existing snake-case fields");
        SimSaveData data = serializer.Deserialize<SimSaveData>(json);
        SimState restored = new SimState();
        Check(restored.TryLoad(data) && Same(source.ToSaveData(), restored.ToSaveData()) && restored.selected == 1, "Real JSON round trip preserves owned-pot selection and domain values");
    }

    private static bool Same(SimSaveData a, SimSaveData b)
    {
        if (a.version != b.version || a.level != b.level || a.xp != b.xp || a.cash != b.cash || a.selected != b.selected
            || a.lamp_on != b.lamp_on || a.upgraded_light != b.upgraded_light || a.fan != b.fan || a.total_harvests != b.total_harvests) return false;
        for (int i = 0; i < 3; i++)
        {
            PotState first = a.pots[i], second = b.pots[i];
            if (first.owned != second.owned || first.state != second.state || !Near(first.growth, second.growth)
                || !Near(first.moisture, second.moisture) || !Near(first.health, second.health)) return false;
        }
        return true;
    }
}
