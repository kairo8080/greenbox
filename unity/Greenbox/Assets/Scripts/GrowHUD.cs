using UnityEngine;

namespace Greenbox
{
    public sealed class GrowHUD : MonoBehaviour
    {
        public const float SidebarWidth = 284;
        public GrowGameController Game;
        private GUIStyle title, heading, normal, small, button, muted, gold;
        private readonly Color cream = new Color(.94f, .92f, .83f);
        private readonly Color green = new Color(.56f, .77f, .61f);
        private readonly Color amber = new Color(.94f, .78f, .47f);
        private readonly Color red = new Color(.80f, .42f, .38f);
        private Vector2 scroll;
        private string message = "", reward = "";
        private bool goodMessage = true;
        private float messageUntil, rewardUntil;

        public void ShowMessage(string text, bool good = true)
        {
            message = text;
            goodMessage = good;
            messageUntil = Time.unscaledTime + 4;
        }
        public void ShowReward(string text)
        {
            reward = text;
            rewardUntil = Time.unscaledTime + 2.8f;
        }
        public bool IsPointerOverPanel(Vector3 point)
        {
            Vector2 guiPoint = new Vector2(point.x, Screen.height - point.y);
            return SidebarRect().Contains(guiPoint) || new Rect(20, 20, WorldWidth() - 40, 130).Contains(guiPoint);
        }
        private float WorldWidth() { return Mathf.Max(500, Screen.width - SidebarWidth - 40); }
        private Rect SidebarRect() { return new Rect(Screen.width - SidebarWidth - 20, 20, SidebarWidth, Screen.height - 40); }

        private void InitializeStyles()
        {
            if (normal != null) return;
            normal = new GUIStyle(GUI.skin.label) { fontSize = 14, wordWrap = true };
            normal.normal.textColor = cream;
            title = new GUIStyle(normal) { fontSize = 22, fontStyle = FontStyle.Bold };
            heading = new GUIStyle(normal) { fontSize = 19, fontStyle = FontStyle.Bold };
            small = new GUIStyle(normal) { fontSize = 12 };
            muted = new GUIStyle(small);
            muted.normal.textColor = new Color(.7f, .73f, .68f);
            gold = new GUIStyle(normal);
            gold.normal.textColor = amber;
            button = new GUIStyle(GUI.skin.button) { fontSize = 12, wordWrap = false, alignment = TextAnchor.MiddleCenter };
            button.normal.textColor = cream;
            button.hover.textColor = Color.white;
            button.active.textColor = green;
        }

        private void OnGUI()
        {
            if (Game == null || Game.State == null) return;
            InitializeStyles();
            if (!string.IsNullOrEmpty(Game.StartupError))
            {
                Fill(new Rect(30, 30, Screen.width - 60, 140), new Color(.10f, .12f, .10f, .97f));
                GUI.Label(new Rect(45, 45, Screen.width - 90, 100), Game.StartupError, normal);
                return;
            }
            SimState state = Game.State;
            float world = WorldWidth();
            Rect top = new Rect(20, 20, world - 40, 126);
            Panel(top);
            Stripes(new Rect(top.x + 14, top.y + 11, top.width - 28, 3));
            GUI.Label(new Rect(36, 42, top.width - 220, 32), "GREENBOX", title);
            GUI.Label(new Rect(top.xMax - 196, 45, 100, 25), "LEVEL " + state.level, heading);
            GUI.Label(new Rect(top.xMax - 88, 45, 76, 25), state.cash + " cr", gold);
            string xp = state.level >= 3 ? state.xp + " XP · MAX" : state.xp + " / " + state.XpTarget() + " XP";
            GUI.Label(new Rect(36, 78, 112, 21), xp, small);
            Bar(new Rect(155, 83, Mathf.Max(20, top.width - 153), 8), (float)state.xp / Mathf.Max(1, state.XpTarget()), green);
            GUI.Label(new Rect(36, 104, top.width - 32, 35), (Game.Paused ? "PAUSED · " : "NEXT: ") + state.Objective(), normal);
            DrawSidebar(state);
            DrawPotLabels(state);
            GUI.Label(new Rect(22, Screen.height - 38, world - 35, 34), "WASD move / cancel walk · Click pot to walk · E interact · Space pause · Wheel zoom · M sound", muted);
            if (Time.unscaledTime < messageUntil)
            {
                Rect toast = new Rect(20, Screen.height - 104, world - 40, 52);
                Panel(toast);
                GUIStyle feedback = new GUIStyle(normal) { alignment = TextAnchor.MiddleCenter };
                feedback.normal.textColor = goodMessage ? cream : red;
                GUI.Label(new Rect(toast.x + 12, toast.y + 6, toast.width - 24, toast.height - 12), message, feedback);
            }
            if (Time.unscaledTime < rewardUntil)
            {
                GUIStyle rewardStyle = new GUIStyle(title) { alignment = TextAnchor.MiddleCenter };
                rewardStyle.normal.textColor = amber;
                GUI.Label(new Rect(20, Screen.height * .42f, world - 40, 60), reward, rewardStyle);
            }
        }

        private void DrawSidebar(SimState state)
        {
            Rect side = SidebarRect();
            Panel(side);
            Rect viewport = new Rect(side.x + 13, side.y + 13, side.width - 26, side.height - 26);
            float width = viewport.width - (viewport.height < 720 ? 18 : 0);
            scroll = GUI.BeginScrollView(viewport, scroll, new Rect(0, 0, width, 714), false, false);
            Stripes(new Rect(1, 0, width - 2, 3));
            GUI.Label(new Rect(0, 14, width, 20), "YOUR FIRST ROOM", muted);
            GUI.Label(new Rect(0, 36, width, 29), "POT " + (Game.Selected + 1), heading);
            for (int i = 0; i < 3; i++)
            {
                GUI.backgroundColor = Game.Selected == i ? green : Color.white;
                if (GUI.Button(new Rect(i * (width / 3), 73, width / 3 - 5, 34), state.pots[i].owned ? "POT " + (i + 1) : "LOCKED", button)) Game.Action("select", i);
            }
            GUI.backgroundColor = Color.white;
            PotState pot = state.pots[Game.Selected];
            bool active = pot.owned && pot.state != "empty";
            GUI.Label(new Rect(0, 119, width, 22), pot.owned ? (pot.state == "ready" ? "READY · TIME TO HARVEST" : pot.state.ToUpperInvariant()) : "LOCKED · UPGRADE YOUR ROOM", gold);
            Meter("GROWTH", active ? (float)pot.growth * 100 : 0, 149, width, green);
            Meter("WATER", active ? (float)pot.moisture : 0, 197, width, new Color(.45f, .75f, .84f));
            Meter("HEALTH", active ? (float)pot.health : 0, 245, width, amber);
            GUI.Label(new Rect(0, 294, width, 44), Game.Paused ? "Paused. Resume to walk or care for plants." : Game.InteractionPrompt(), normal);
            bool near = Game.IsNearPot(Game.Selected);
            float half = (width - 6) * .5f;
            ActionButton(new Rect(0, 346, half, 36), near ? "PLANT SEED  5 cr" : "WALK & PLANT", "plant", pot.owned && pot.state == "empty" && state.cash >= 5);
            ActionButton(new Rect(half + 6, 346, half, 36), near ? "WATER" : "WALK & WATER", "water", active && pot.state != "ready");
            ActionButton(new Rect(0, 388, half, 36), near ? "HARVEST & SELL" : "WALK & HARVEST", "harvest", pot.owned && pot.state == "ready");
            ActionButton(new Rect(half + 6, 388, half, 36), state.lamp_on ? "LAMP: ON" : "LAMP: OFF", "light", true);
            ActionButton(new Rect(0, 431, width, 34), Game.Paused ? "RESUME" : "PAUSE", "pause", true);
            GUI.Label(new Rect(0, 477, width, 23), "BUILD UP YOUR SETUP", gold);
            Upgrade("pot2", "SECOND POT", 35, 2, state.pots[1].owned, new Rect(0, 507, width, 35));
            Upgrade("lamp", "BETTER LAMP", 45, 2, state.upgraded_light, new Rect(0, 548, width, 35));
            Upgrade("fan", "ROOM FAN", 30, 3, state.fan, new Rect(0, 589, width, 35));
            Upgrade("pot3", "THIRD POT", 55, 3, state.pots[2].owned, new Rect(0, 630, width, 35));
            GUI.Label(new Rect(0, 678, width, 38), "Small room. Big plans.\nCare → harvest → sell → upgrade.", muted);
            GUI.EndScrollView();
        }

        private void ActionButton(Rect rect, string label, string action, bool valid)
        {
            bool previous = GUI.enabled;
            GUI.enabled = previous && valid;
            if (GUI.Button(rect, label, button)) Game.Action(action, Game.Selected);
            GUI.enabled = previous;
        }
        private void Upgrade(string id, string title, int price, int level, bool owned, Rect rect)
        {
            string caption = title + (owned ? " · OWNED" : "  " + price + " cr" + (Game.State.level < level ? " / LV " + level : ""));
            bool valid = !owned && Game.State.level >= level && Game.State.cash >= price && (id != "pot3" || Game.State.pots[1].owned);
            ActionButton(rect, caption, id, valid);
        }
        private void Meter(string label, float amount, float y, float width, Color fill)
        {
            GUI.Label(new Rect(0, y, width, 23), label + "     " + Mathf.RoundToInt(amount) + "%", small);
            Bar(new Rect(0, y + 27, width, 9), amount / 100, fill);
        }
        private void DrawPotLabels(SimState state)
        {
            if (Game.sceneCamera == null) return;
            for (int i = 0; i < 3; i++)
            {
                PotState pot = state.pots[i];
                Vector3 p = Game.sceneCamera.WorldToScreenPoint(Game.PotPosition(i) + Vector3.up * (pot.state == "ready" || pot.state == "flowering" ? 1.85f : 1.3f));
                if (p.z <= 0) continue;
                string label = !pot.owned ? "LV " + (i + 1) : pot.state == "empty" ? "POT " + (i + 1) : pot.state == "ready" ? "HARVEST!" : (i + 1) + " · " + Mathf.RoundToInt((float)pot.growth * 100) + "%";
                GUIStyle floating = new GUIStyle(small) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
                floating.normal.textColor = pot.state == "ready" ? amber : cream;
                Rect labelRect = new Rect(p.x - 55, Screen.height - p.y, 110, 24);
                Fill(labelRect, new Color(.06f, .09f, .08f, .76f));
                GUI.Label(labelRect, label, floating);
            }
        }
        private void Panel(Rect rect) { Fill(rect, new Color(.085f, .09f, .08f, .96f)); }
        private void Stripes(Rect rect)
        {
            float width = (rect.width - 4) / 3;
            Fill(new Rect(rect.x, rect.y, width, rect.height), red);
            Fill(new Rect(rect.x + width + 2, rect.y, width, rect.height), amber);
            Fill(new Rect(rect.x + width * 2 + 4, rect.y, width, rect.height), green);
        }
        private static void Bar(Rect rect, float fraction, Color fill)
        {
            Fill(rect, new Color(.18f, .23f, .20f));
            Fill(new Rect(rect.x, rect.y, rect.width * Mathf.Clamp01(fraction), rect.height), fill);
        }
        private static void Fill(Rect rect, Color color)
        {
            Color previous = GUI.color;
            GUI.color = color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = previous;
        }
    }
}
