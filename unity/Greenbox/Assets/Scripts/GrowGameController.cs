using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;

namespace Greenbox
{
    public sealed class GrowGameController : MonoBehaviour
    {
        [Tooltip("glTFast converts glTF coordinates by mirroring X.")]
        public bool mirrorX = true;
        public bool freshPreview;
        public Camera sceneCamera;
        public SimState State { get; private set; }
        public PlayerController Player { get; private set; }
        public GrowHUD Hud { get; private set; }
        public bool Paused { get { return manualPaused || browserHidden || focusLost || applicationPaused; } }
        public bool Muted { get; private set; }
        public float CareTimer { get; private set; }
        public string CareAction { get; private set; }
        public string StartupError { get; private set; }
        public string SavePath { get; private set; }
        public int Selected { get { return State == null ? 0 : State.selected; } }
        public const float InteractionRange = 1.30f;

        private static readonly Vector3[] PotPositions =
        {
            new Vector3(4.60f,.20f,-4.60f), new Vector3(5.60f,.20f,-4.60f), new Vector3(5.10f,.20f,-3.60f)
        };
        private static readonly Vector3[] ApproachPositions =
        {
            new Vector3(4.60f,.20f,-3.50f), new Vector3(5.70f,.20f,-3.50f), new Vector3(5.10f,.20f,-2.60f)
        };
        private readonly string[] lastStages = { "", "", "" };
        private readonly GameObject[] potRoots = new GameObject[3];
        private readonly Transform[] foliageRoots = new Transform[3];
        private readonly GameObject[] selectionRings = new GameObject[3];
        private readonly BoxCollider[] potColliders = new BoxCollider[3];
        private readonly List<BoxCollider> rackColliders = new List<BoxCollider>();
        private readonly List<Bounds> furniture = new List<Bounds>();
        private readonly List<BurstPiece> bursts = new List<BurstPiece>();
        private GameObject room, propLibrary, budgetLamp, growRack, fanArt;
        private BoxCollider budgetCollider;
        private Light growLight;
        private Material ringMaterial, particleMaterial, groundMaterial;
        private AudioSource audioSource;
        private float saveTimer;
        private string pendingCare = "";
        private int pendingPot = -1;
        private bool ready;
        private bool manualPaused, browserHidden, focusLost, applicationPaused;

        private struct BurstPiece
        {
            public GameObject gameObject;
            public Vector3 start, end;
            public float age;
        }

        private void Awake()
        {
            Application.targetFrameRate = 60;
            State = new SimState();
            foreach (string arg in Environment.GetCommandLineArgs())
                if (arg == "--fresh-preview") freshPreview = true;
            SavePath = Path.Combine(Application.persistentDataPath, "save.json");
            if (!freshPreview) LoadGame();
            Hud = gameObject.AddComponent<GrowHUD>();
            Hud.Game = this;
            try
            {
                BuildWorld();
                SyncVisuals();
                ready = true;
                Hud.ShowMessage("WASD to move. Click a pot to walk over, then press E to plant.");
            }
            catch (Exception error)
            {
                StartupError = "The voxel scene could not load. " + error.Message;
                Debug.LogException(error, this);
            }
        }

        public Vector3 Map(Vector3 canonical) { return new Vector3(mirrorX ? -canonical.x : canonical.x, canonical.y, canonical.z); }
        public Vector3 Canonical(Vector3 world) { return Map(world); }
        public Vector3 PotPosition(int index) { return Map(PotPositions[Mathf.Clamp(index, 0, 2)]); }
        public bool IsNearPot(int index)
        {
            return Player != null && index >= 0 && index < 3 && HorizontalDistance(Player.transform.position, PotPosition(index)) <= InteractionRange;
        }

        public static float HorizontalDistance(Vector3 a, Vector3 b)
        {
            a.y = b.y = 0;
            return Vector3.Distance(a, b);
        }

        private void BuildWorld()
        {
            room = InstantiateResource("rasta_bedroom");
            room.name = "Voxel Bedroom";
            propLibrary = InstantiateResource("starter_props");
            propLibrary.name = "Hidden Prop Library";
            propLibrary.SetActive(false);
            foreach (string name in new[] { "cannabis_plant_small", "cannabis_plant_medium", "cannabis_plant_bushy", "water_reservoir", "home_grower_character" })
            {
                Transform old = FindDeep(room.transform, name);
                if (old != null) old.gameObject.SetActive(false);
            }
            growRack = FindObject(room, "grow_light_rack");
            fanArt = FindObject(room, "small_fan");
            budgetLamp = CopyProp("lamp_budget", transform);
            budgetLamp.transform.position = PotPosition(0);
            budgetLamp.transform.rotation = Quaternion.Euler(0, 180, 0);
            GameObject packet = CopyProp("seed_packet", transform);
            packet.transform.position = Map(new Vector3(3.35f, .2f, -2.7f));

            ringMaterial = MakeMaterial(new Color(.56f, .86f, .69f), true);
            particleMaterial = MakeMaterial(new Color(.57f, .88f, .88f), true);
            for (int i = 0; i < 3; i++)
            {
                potRoots[i] = new GameObject("Pot " + (i + 1));
                potRoots[i].transform.SetParent(transform, false);
                potRoots[i].transform.position = PotPosition(i);
                CopyProp("pot_empty", potRoots[i].transform);
                foliageRoots[i] = new GameObject("Foliage").transform;
                foliageRoots[i].SetParent(potRoots[i].transform, false);
                foliageRoots[i].localPosition = new Vector3(0, .4f, 0);
                potColliders[i] = Collision("Pot Collider " + (i + 1), PotPositions[i] + new Vector3(0, .225f, 0), new Vector3(.55f, .45f, .55f));
                selectionRings[i] = MakeRing(i);
            }
            Collision("Floor", new Vector3(3.6f, .1f, -3), new Vector3(7.2f, .2f, 6));
            AddObstacle("Left Wall", new Vector3(.125f, 1.7f, -2.925f), new Vector3(.25f, 3, 5.85f));
            AddObstacle("Back Wall", new Vector3(3.6f, 1.7f, -5.825f), new Vector3(7.2f, 3, .35f));
            AddObstacle("Bed", new Vector3(1.175f, .7f, -4.5f), new Vector3(1.45f, 1, 2.2f));
            AddObstacle("Desk", new Vector3(6.05f, .7f, -1.25f), new Vector3(1.3f, 1, .7f));
            AddObstacle("Chair", new Vector3(6.05f, .5f, -.55f), new Vector3(.5f, .6f, .5f));
            AddObstacle("Bedside Table", new Vector3(2.25f, .65f, -5.3f), new Vector3(.5f, .9f, .5f));
            AddObstacle("Stereo", new Vector3(.9f, .65f, -2.475f), new Vector3(1.2f, .9f, .65f));
            budgetCollider = Collision("Budget Lamp Base", PotPositions[0] + new Vector3(-.55f, .09f, 0), new Vector3(.5f, .18f, .65f));
            foreach (float x in new[] { 4.15f, 5.95f })
                foreach (float z in new[] { -5.15f, -4.15f })
                    rackColliders.Add(Collision("Light Rack Post", new Vector3(x, 1.35f, z), new Vector3(.1f, 2.3f, .1f)));

            if (sceneCamera == null)
            {
                sceneCamera = new GameObject("Isometric Camera").AddComponent<Camera>();
                sceneCamera.tag = "MainCamera";
                sceneCamera.gameObject.AddComponent<AudioListener>();
            }
            sceneCamera.orthographic = true;
            sceneCamera.orthographicSize = 5.6f;
            sceneCamera.transform.position = Map(new Vector3(13.6f, 10.4f, 9.3f));
            sceneCamera.transform.LookAt(Map(new Vector3(3.6f, .9f, -3)));
            sceneCamera.clearFlags = CameraClearFlags.SolidColor;
            sceneCamera.backgroundColor = new Color(.07f, .11f, .12f);
            sceneCamera.nearClipPlane = .1f;
            sceneCamera.farClipPlane = 150;
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(.58f, .67f, .61f);
            Light sunlight = new GameObject("Warm Sun").AddComponent<Light>();
            sunlight.type = LightType.Directional;
            sunlight.color = new Color(1, .94f, .81f);
            sunlight.intensity = .9f;
            sunlight.transform.rotation = Quaternion.Euler(55, mirrorX ? 25 : -25, 0);
            sunlight.shadows = LightShadows.Soft;
            growLight = NewPointLight("Grow Lamp Glow", new Vector3(5.1f, 2.1f, -4.35f), new Color(1, .56f, .79f), 2.5f, 0);
            NewPointLight("Bedside Glow", new Vector3(2.25f, 1.45f, -5.3f), new Color(1, .76f, .44f), 2.3f, .55f);
            groundMaterial = MakeMaterial(new Color(.07f, .11f, .12f), false);
            Cube("Diorama Plinth", Map(new Vector3(3.6f, -.09f, -3)), new Vector3(7.45f, .17f, 6.25f), groundMaterial);
            Cube("Backdrop Ground", Map(new Vector3(3.6f, -.25f, -3)), new Vector3(100, .1f, 100), groundMaterial);
            BuildPlayer();
            audioSource = gameObject.AddComponent<AudioSource>();
            audioSource.playOnAwake = false;
            audioSource.volume = .10f;
            ForceNearestTextures(room);
            ForceNearestTextures(propLibrary);
        }

        private void BuildPlayer()
        {
            GameObject playerRoot = new GameObject("Player");
            playerRoot.transform.position = Map(new Vector3(3.35f, .2f, -1.95f));
            CharacterController capsule = playerRoot.AddComponent<CharacterController>();
            capsule.height = 1.6f;
            capsule.radius = .21f;
            capsule.center = new Vector3(0, .8f, 0);
            capsule.skinWidth = .025f;
            capsule.stepOffset = .18f;
            Player = playerRoot.AddComponent<PlayerController>();
            Player.Game = this;
            Player.ViewCamera = sceneCamera;
            GameObject avatar = InstantiateResource("rasta_character");
            avatar.transform.SetParent(playerRoot.transform, false);
            Player.Visual = avatar.transform;
            Transform canSource = FindDeep(room.transform, "watering_can");
            Player.InitializeJoints(canSource);
            ForceNearestTextures(avatar);
        }

        private GameObject InstantiateResource(string name)
        {
            GameObject source = Resources.Load<GameObject>("Voxels/" + name);
            if (source == null) throw new InvalidOperationException("Missing imported voxel prefab: Resources/Voxels/" + name);
            return Instantiate(source);
        }

        private GameObject CopyProp(string name, Transform parent)
        {
            Transform source = FindDeep(propLibrary.transform, name);
            if (source == null) throw new InvalidOperationException("Missing voxel prop: " + name);
            GameObject copy = Instantiate(source.gameObject, parent, false);
            copy.name = name;
            copy.transform.localPosition = Vector3.zero;
            copy.SetActive(true);
            return copy;
        }

        public static Transform FindDeep(Transform root, string name)
        {
            if (root.name == name) return root;
            for (int i = 0; i < root.childCount; i++)
            {
                Transform result = FindDeep(root.GetChild(i), name);
                if (result != null) return result;
            }
            return null;
        }
        private static GameObject FindObject(GameObject root, string name)
        {
            Transform result = FindDeep(root.transform, name);
            return result == null ? null : result.gameObject;
        }

        private BoxCollider Collision(string name, Vector3 canonicalPosition, Vector3 size)
        {
            GameObject collider = new GameObject(name);
            collider.transform.SetParent(transform, false);
            collider.transform.position = Map(canonicalPosition);
            BoxCollider box = collider.AddComponent<BoxCollider>();
            box.size = size;
            return box;
        }
        private void AddObstacle(string name, Vector3 position, Vector3 size)
        {
            Collision(name, position, size);
            furniture.Add(new Bounds(position, size));
        }
        private Light NewPointLight(string name, Vector3 position, Color color, float range, float intensity)
        {
            Light light = new GameObject(name).AddComponent<Light>();
            light.type = LightType.Point;
            light.transform.position = Map(position);
            light.color = color;
            light.range = range;
            light.intensity = intensity;
            light.shadows = LightShadows.None;
            return light;
        }
        private static Material MakeMaterial(Color color, bool unlit)
        {
            Material source = Resources.Load<Material>(unlit ? "GreenboxUnlit" : "GreenboxLit");
            Shader shader = Shader.Find(unlit ? "Unlit/Color" : "Standard");
            if (shader == null) shader = Shader.Find("Universal Render Pipeline/Unlit");
            if (source == null && shader == null) throw new InvalidOperationException("A basic scene shader is unavailable.");
            Material material = source != null ? new Material(source) : new Material(shader);
            material.color = color;
            if (material.HasProperty("_Glossiness")) material.SetFloat("_Glossiness", .05f);
            return material;
        }
        private static GameObject Cube(string name, Vector3 position, Vector3 size, Material material)
        {
            GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.name = name;
            cube.transform.position = position;
            cube.transform.localScale = size;
            Collider collider = cube.GetComponent<Collider>();
            collider.enabled = false;
            Destroy(collider);
            cube.GetComponent<Renderer>().sharedMaterial = material;
            return cube;
        }
        private GameObject MakeRing(int index)
        {
            GameObject root = new GameObject("Selection Ring " + (index + 1));
            root.transform.position = PotPosition(index) + Vector3.up * .016f;
            for (int side = 0; side < 4; side++)
            {
                Vector3 size = side < 2 ? new Vector3(.65f, .016f, .035f) : new Vector3(.035f, .016f, .65f);
                Vector3 offset = side == 0 ? new Vector3(0, 0, -.31f) : side == 1 ? new Vector3(0, 0, .31f) : side == 2 ? new Vector3(-.31f, 0, 0) : new Vector3(.31f, 0, 0);
                GameObject part = Cube("Ring Edge", root.transform.position + offset, size, ringMaterial);
                part.transform.SetParent(root.transform, true);
            }
            return root;
        }
        private static void ForceNearestTextures(GameObject root)
        {
            foreach (Renderer renderer in root.GetComponentsInChildren<Renderer>(true))
                foreach (Material material in renderer.sharedMaterials)
                    if (material != null)
                        foreach (string property in new[] { "_MainTex", "_BaseMap", "_BaseColorTexture" })
                            if (material.HasProperty(property) && material.GetTexture(property) != null)
                                material.GetTexture(property).filterMode = FilterMode.Point;
        }

        private void Update()
        {
            if (!ready) return;
            sceneCamera.rect = new Rect(0, 0, Mathf.Max(.45f, (Screen.width - GrowHUD.SidebarWidth - 40f) / Screen.width), 1);
            if (Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.Escape)) Action("pause", Selected);
            if (!Paused)
            {
                State.Tick(Time.deltaTime);
                CareTimer = Mathf.Max(0, CareTimer - Time.deltaTime);
                if (Input.GetKeyDown(KeyCode.E)) InteractNearest();
                if (Input.GetKeyDown(KeyCode.L)) Action("light", Selected);
                if (Input.GetKeyDown(KeyCode.Alpha1)) Action("select", 0);
                if (Input.GetKeyDown(KeyCode.Alpha2)) Action("select", 1);
                if (Input.GetKeyDown(KeyCode.Alpha3)) Action("select", 2);
                if (Input.GetMouseButtonDown(0) && !Hud.IsPointerOverPanel(Input.mousePosition)) WorldClick();
                if (Mathf.Abs(Input.mouseScrollDelta.y) > .01f && !Hud.IsPointerOverPanel(Input.mousePosition))
                    sceneCamera.orthographicSize = Mathf.Clamp(sceneCamera.orthographicSize - Input.mouseScrollDelta.y * .22f, 4.3f, 7);
                if (fanArt != null && State.fan) fanArt.transform.localRotation = Quaternion.Euler(0, Mathf.Sin(Time.time * 1.1f) * 9, 0);
            }
            if (Input.GetKeyDown(KeyCode.M))
            {
                Muted = !Muted;
                Hud.ShowMessage(Muted ? "Sound muted" : "Sound on");
            }
            SyncVisuals();
            UpdateBursts(Time.deltaTime);
            saveTimer += Time.unscaledDeltaTime;
            if (saveTimer >= 5) { saveTimer = 0; SaveGame(); }
        }

        private void WorldClick()
        {
            int nearest = -1;
            float distance = 65;
            for (int i = 0; i < 3; i++)
            {
                Vector3 projected = sceneCamera.WorldToScreenPoint(PotPosition(i) + Vector3.up * .45f);
                float candidate = Vector2.Distance(new Vector2(projected.x, projected.y), Input.mousePosition);
                if (projected.z > 0 && candidate < distance) { nearest = i; distance = candidate; }
            }
            if (nearest >= 0) { Action("select", nearest); return; }
            Plane floor = new Plane(Vector3.up, new Vector3(0, .2f, 0));
            Ray ray = sceneCamera.ScreenPointToRay(Input.mousePosition);
            float enter;
            if (floor.Raycast(ray, out enter))
            {
                Vector3 destination = Canonical(ray.GetPoint(enter));
                if (destination.x > .3f && destination.x < 6.9f && destination.z > -5.7f && destination.z < -.3f)
                    WalkTo(Map(destination), "", -1);
            }
        }

        public void Action(string action, int index)
        {
            if (!ready) return;
            index = Mathf.Clamp(index, 0, 2);
            if (action == "pause")
            {
                manualPaused = !manualPaused;
                Hud.ShowMessage(Paused ? "Paused — your plants can wait." : "Back in the bedroom.");
                return;
            }
            if (action == "select")
            {
                State.selected = index;
                if (!Paused && State.pots[index].owned) ApproachPot(index);
                return;
            }
            if (Paused) { Hud.ShowMessage("Resume before caring for plants or buying equipment.", false); return; }
            if (action == "plant" || action == "water" || action == "harvest")
            {
                if (IsNearPot(index)) PerformCare(action, index); else ApproachPot(index, action);
                return;
            }
            SimActionResult result = action == "light" ? State.ToggleLight() : State.BuyUpgrade(action);
            ShowResult(result, action, index);
        }

        public void InteractNearest()
        {
            if (Paused || CareTimer > 0) return;
            int index = State.pots[Selected].owned && IsNearPot(Selected) ? Selected : -1;
            if (index < 0)
            {
                float nearest = InteractionRange;
                for (int i = 0; i < 3; i++)
                    if (State.pots[i].owned)
                    {
                        float distance = HorizontalDistance(Player.transform.position, PotPosition(i));
                        if (distance <= nearest) { nearest = distance; index = i; }
                    }
            }
            if (index < 0) { Hud.ShowMessage("Walk closer to a pot, or click it to walk over.", false); return; }
            State.selected = index;
            string stage = State.pots[index].state;
            PerformCare(stage == "empty" ? "plant" : stage == "ready" ? "harvest" : "water", index);
        }

        public void PerformCare(string action, int index)
        {
            if (Paused || CareTimer > 0 || index < 0 || index >= 3) return;
            if (!IsNearPot(index)) { Hud.ShowMessage("Walk closer to that plant first.", false); return; }
            Player.CancelWalk();
            SimActionResult result = action == "plant" ? State.Plant(index) : action == "harvest" ? State.Harvest(index) : State.Water(index);
            if (result.ok)
            {
                State.selected = index;
                CareTimer = 1.05f;
                CareAction = action;
                Player.Face(PotPosition(index));
            }
            ShowResult(result, action, index);
        }

        public void ApproachPot(int index, string care = "")
        {
            if (Paused || CareTimer > 0 || index < 0 || index >= 3) return;
            if (!State.pots[index].owned) { Hud.ShowMessage("Unlock this pot in the upgrade shop.", false); return; }
            State.selected = index;
            WalkTo(Map(ApproachPositions[index]), care, index);
        }
        private void WalkTo(Vector3 destination, string care, int index)
        {
            if (Paused || CareTimer > 0) return;
            List<Vector3> path = FindPath(Player.transform.position, destination);
            Player.CancelWalk();
            if (path.Count == 0) { Hud.ShowMessage("No clear route. Use WASD to step around the furniture.", false); return; }
            pendingCare = care;
            pendingPot = index;
            Player.FollowPath(path, delegate
            {
                string requested = pendingCare;
                int pot = pendingPot;
                CancelPendingCare();
                if (!string.IsNullOrEmpty(requested)) PerformCare(requested, pot);
            });
            Hud.ShowMessage(index >= 0 ? "Walking to pot " + (index + 1) + " — WASD cancels." : "Walking — WASD cancels.");
        }
        public void CancelPendingCare() { pendingCare = ""; pendingPot = -1; }

        public string InteractionPrompt()
        {
            if (CareTimer > 0) return CareAction == "water" ? "Watering…" : CareAction == "harvest" ? "Harvesting…" : "Planting a seed…";
            if (Player != null && Player.Walking) return "Walking" + (pendingPot >= 0 ? " to pot " + (pendingPot + 1) : "") + " · WASD cancels";
            if (!State.pots[Selected].owned) return "This space unlocks at level " + (Selected + 1);
            if (!IsNearPot(Selected)) return "Walk to pot " + (Selected + 1) + " · E to interact";
            string stage = State.pots[Selected].state;
            return "E: " + (stage == "empty" ? "PLANT" : stage == "ready" ? "HARVEST" : "WATER") + " · POT " + (Selected + 1);
        }

        private void ShowResult(SimActionResult result, string action, int index)
        {
            Hud.ShowMessage(result.message, result.ok);
            if (!result.ok) return;
            PlayTone(action == "harvest" ? 720 : 480);
            if (action == "plant" || action == "water" || action == "harvest") Burst(PotPosition(index) + Vector3.up * .55f);
            if (action == "harvest") Hud.ShowReward("+" + result.xp_added + " XP  ·  +" + result.revenue + " credits" + (result.levelup ? "  ·  LEVEL UP!" : ""));
            SyncVisuals();
            SaveGame();
        }

        private void SyncVisuals()
        {
            for (int i = 0; i < 3; i++)
            {
                PotState pot = State.pots[i];
                potRoots[i].SetActive(pot.owned);
                potColliders[i].enabled = pot.owned;
                selectionRings[i].SetActive(pot.owned && i == Selected);
                if (lastStages[i] != pot.state)
                {
                    foreach (Transform child in foliageRoots[i]) { child.gameObject.SetActive(false); Destroy(child.gameObject); }
                    string prop = pot.state == "seedling" ? "foliage_seedling" : pot.state == "growing" ? "foliage_small" : pot.state == "flowering" ? "foliage_medium" : "foliage_bushy";
                    if (pot.state != "empty") CopyProp(prop, foliageRoots[i]);
                    lastStages[i] = pot.state;
                }
            }
            budgetLamp.SetActive(!State.upgraded_light);
            budgetCollider.enabled = !State.upgraded_light;
            if (growRack != null) growRack.SetActive(State.upgraded_light);
            if (fanArt != null) fanArt.SetActive(State.fan);
            foreach (BoxCollider collider in rackColliders) collider.enabled = State.upgraded_light;
            growLight.intensity = State.lamp_on ? (State.upgraded_light ? 1.3f : .55f) : 0;
        }

        private List<Vector3> FindPath(Vector3 worldStart, Vector3 worldEnd)
        {
            const int width = 36, height = 30;
            bool[,] solid = new bool[width, height];
            List<Bounds> active = new List<Bounds>(furniture);
            for (int i = 0; i < 3; i++) if (State.pots[i].owned) active.Add(new Bounds(PotPositions[i], new Vector3(.55f, .45f, .55f)));
            if (!State.upgraded_light) active.Add(new Bounds(PotPositions[0] + new Vector3(-.55f, 0, 0), new Vector3(.5f, .18f, .65f)));
            else foreach (BoxCollider collider in rackColliders) active.Add(new Bounds(Canonical(collider.transform.position), collider.size));
            for (int x = 0; x < width; x++) for (int z = 0; z < height; z++)
            {
                Vector3 p = GridPoint(x, z);
                bool blocked = p.x < .35f || p.x > 6.9f || p.z > -.3f || p.z < -5.7f;
                foreach (Bounds obstacle in active)
                    if (Mathf.Abs(p.x - obstacle.center.x) < obstacle.extents.x + .24f && Mathf.Abs(p.z - obstacle.center.z) < obstacle.extents.z + .24f) blocked = true;
                solid[x, z] = blocked;
            }
            Vector2Int start = NearestCell(Canonical(worldStart), solid), end = NearestCell(Canonical(worldEnd), solid);
            List<Vector3> output = new List<Vector3>();
            if (start.x < 0 || end.x < 0) return output;
            int[,] cost = new int[width, height];
            bool[,] closed = new bool[width, height];
            Vector2Int[,] parent = new Vector2Int[width, height];
            for (int x = 0; x < width; x++) for (int z = 0; z < height; z++) { cost[x, z] = int.MaxValue; parent[x, z] = new Vector2Int(-1, -1); }
            List<Vector2Int> open = new List<Vector2Int> { start };
            cost[start.x, start.y] = 0;
            while (open.Count > 0)
            {
                int best = 0, score = int.MaxValue;
                for (int i = 0; i < open.Count; i++)
                {
                    Vector2Int c = open[i];
                    int h = 10 * Mathf.Max(Mathf.Abs(c.x - end.x), Mathf.Abs(c.y - end.y));
                    int f = cost[c.x, c.y] + h;
                    if (f < score) { score = f; best = i; }
                }
                Vector2Int current = open[best];
                open.RemoveAt(best);
                if (current == end)
                {
                    for (Vector2Int c = end; c.x >= 0; c = parent[c.x, c.y])
                    {
                        output.Add(Map(GridPoint(c.x, c.y)));
                        if (c == start) break;
                    }
                    output.Reverse();
                    return output;
                }
                closed[current.x, current.y] = true;
                for (int dx = -1; dx <= 1; dx++) for (int dz = -1; dz <= 1; dz++)
                {
                    if (dx == 0 && dz == 0) continue;
                    int nx = current.x + dx, nz = current.y + dz;
                    if (nx < 0 || nx >= width || nz < 0 || nz >= height || solid[nx, nz] || closed[nx, nz]) continue;
                    if (dx != 0 && dz != 0 && (solid[current.x + dx, current.y] || solid[current.x, current.y + dz])) continue;
                    int candidate = cost[current.x, current.y] + (dx == 0 || dz == 0 ? 10 : 14);
                    if (candidate >= cost[nx, nz]) continue;
                    cost[nx, nz] = candidate;
                    parent[nx, nz] = current;
                    Vector2Int next = new Vector2Int(nx, nz);
                    if (!open.Contains(next)) open.Add(next);
                }
            }
            return output;
        }
        private static Vector3 GridPoint(int x, int z) { return new Vector3(x * .2f + .1f, .2f, -(z * .2f + .1f)); }
        private static Vector2Int NearestCell(Vector3 point, bool[,] solid)
        {
            Vector2Int result = new Vector2Int(-1, -1);
            float nearest = float.MaxValue;
            for (int x = 0; x < 36; x++) for (int z = 0; z < 30; z++) if (!solid[x, z])
            {
                Vector3 delta = GridPoint(x, z) - point;
                float distance = delta.x * delta.x + delta.z * delta.z;
                if (distance < nearest) { nearest = distance; result = new Vector2Int(x, z); }
            }
            return result;
        }

        private void Burst(Vector3 position)
        {
            for (int i = 0; i < 14; i++)
            {
                GameObject piece = Cube("Care Spark", position, Vector3.one * .045f, particleMaterial);
                bursts.Add(new BurstPiece { gameObject = piece, start = position, end = position + new Vector3(UnityEngine.Random.Range(-.32f, .32f), UnityEngine.Random.Range(.3f, .85f), UnityEngine.Random.Range(-.32f, .32f)), age = 0 });
            }
        }
        private void UpdateBursts(float delta)
        {
            for (int i = bursts.Count - 1; i >= 0; i--)
            {
                BurstPiece piece = bursts[i];
                piece.age += delta;
                float t = piece.age / .7f;
                if (t >= 1) { Destroy(piece.gameObject); bursts.RemoveAt(i); continue; }
                piece.gameObject.transform.position = Vector3.Lerp(piece.start, piece.end, 1 - (1 - t) * (1 - t));
                piece.gameObject.transform.localScale = Vector3.one * (.045f * (1 - t));
                bursts[i] = piece;
            }
        }
        private void PlayTone(float frequency)
        {
            if (Muted || audioSource == null) return;
            const int rate = 22050;
            float[] samples = new float[2205];
            for (int i = 0; i < samples.Length; i++) samples[i] = Mathf.Sin(2 * Mathf.PI * frequency * i / rate) * (1f - (float)i / samples.Length) * .3f;
            AudioClip clip = AudioClip.Create("Care Tone", samples.Length, 1, rate, false);
            clip.SetData(samples, 0);
            audioSource.PlayOneShot(clip);
            Destroy(clip, .25f);
        }

        public void SaveGame()
        {
            if (freshPreview || State == null || string.IsNullOrEmpty(SavePath)) return;
            string temporary = SavePath + ".tmp";
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(SavePath));
                File.WriteAllText(temporary, JsonUtility.ToJson(State.ToSaveData(), true));
                if (File.Exists(SavePath)) File.Replace(temporary, SavePath, null); else File.Move(temporary, SavePath);
            }
            catch (Exception error)
            {
                Debug.LogWarning("Progress save failed; temporary progress retained. " + error.Message);
                if (Hud != null) Hud.ShowMessage("Progress could not be saved. Check the game data folder.", false);
            }
        }
        public void Save() { SaveGame(); }
        public void SetBrowserHidden(string value)
        {
            browserHidden = value == "1";
            if (browserHidden) SaveGame();
            else
            {
                // The page lifecycle bridge restores only focus pauses, never the player's pause.
                focusLost = false;
                applicationPaused = false;
            }
        }
        private void LoadGame()
        {
            if (!File.Exists(SavePath)) return;
            string json;
            try
            {
                json = File.ReadAllText(SavePath);
            }
            catch (Exception error)
            {
                freshPreview = true;
                Debug.LogWarning("Existing progress is unreadable; saving disabled for this session. " + error.Message);
                return;
            }
            SimSaveData data = null;
            try
            {
                bool complete = true;
                foreach (string field in new[] { "version", "level", "xp", "cash", "selected", "pots", "lamp_on", "upgraded_light", "fan", "total_harvests" })
                    if (json.IndexOf("\"" + field + "\"", StringComparison.Ordinal) < 0) complete = false;
                if (complete) data = JsonUtility.FromJson<SimSaveData>(json);
            }
            catch (ArgumentException) { }
            if (data != null && State.TryLoad(data)) return;
            try
            {
                string backup = SavePath + ".invalid-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fffffff");
                File.Copy(SavePath, backup, false);
                Debug.LogWarning("Invalid progress preserved at " + backup);
            }
            catch (Exception error)
            {
                // Never overwrite unreadable progress when a safe backup cannot be made.
                freshPreview = true;
                Debug.LogWarning("Existing progress retained; saving disabled for this session. " + error.Message);
            }
        }
        private void OnApplicationFocus(bool focused)
        {
            focusLost = !focused;
            if (!focused && ready) SaveGame();
        }
        private void OnApplicationPause(bool paused)
        {
            applicationPaused = paused;
            if (paused && ready) SaveGame();
        }
        private void OnApplicationQuit() { SaveGame(); }
    }
}
