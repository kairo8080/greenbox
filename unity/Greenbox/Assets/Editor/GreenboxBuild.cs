using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace Greenbox.Editor
{
    /// <summary>Repeatable scene setup and browser export using imported voxel meshes.</summary>
    public static class GreenboxBuild
    {
        public const string ScenePath = "Assets/Scenes/Bedroom.unity";
        private static readonly string[] Models = { "rasta_bedroom", "rasta_character", "starter_props" };

        [InitializeOnLoadMethod]
        private static void FirstOpen()
        {
            if (!Application.isBatchMode && !File.Exists(ScenePath))
                EditorApplication.delayCall += PrepareWhenImported;
        }

        private static void PrepareWhenImported()
        {
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                EditorApplication.delayCall += PrepareWhenImported;
                return;
            }
            // Report a broken import explicitly; don't replace an existing user's scene.
            try { Prepare(); }
            catch (Exception error) { Debug.LogException(error); }
        }

        [MenuItem("Greenbox/Prepare Bedroom Scene")]
        public static void Prepare()
        {
            ValidateModels();
            ConfigurePlayer();
            if (!File.Exists(ScenePath))
            {
                Directory.CreateDirectory("Assets/Scenes");
                var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                var game = new GameObject("Greenbox").AddComponent<GrowGameController>();
                game.mirrorX = true; // glTFast converts right-handed glTF by mirroring X.
                EditorSceneManager.SaveScene(scene, ScenePath);
            }
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            Debug.Log("Greenbox ready: open Assets/Scenes/Bedroom.unity and press Play.");
        }

        [MenuItem("Greenbox/Validate Voxel Imports")]
        public static void ValidateModels()
        {
            foreach (var model in Models)
            {
                var asset = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/Voxels/" + model + ".glb");
                if (asset == null)
                    throw new InvalidOperationException("Missing imported prefab: " + model + ". Check glTFast package/import errors.");
                var meshes = asset.GetComponentsInChildren<MeshFilter>(true);
                if (meshes.Length == 0 || meshes.Any(m => m.sharedMesh == null))
                    throw new InvalidOperationException("Missing voxel mesh in " + model);
                long triangles = 0;
                foreach (var filter in meshes)
                    for (int submesh = 0; submesh < filter.sharedMesh.subMeshCount; submesh++)
                        triangles += filter.sharedMesh.GetIndexCount(submesh) / 3;
                Debug.Log(model + ": " + meshes.Length + " combined meshes, " + triangles + " triangles.");
            }
            var avatar = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/Voxels/rasta_character.glb");
            foreach (var joint in new[] { "torso", "head", "arm_left", "arm_right", "leg_left", "leg_right" })
                if (!avatar.GetComponentsInChildren<Transform>(true).Any(t => t.name == joint))
                    throw new InvalidOperationException("Missing character joint: " + joint);
        }

        private static void ConfigurePlayer()
        {
            PlayerSettings.companyName = "Greenbox";
            PlayerSettings.productName = "Greenbox";
            PlayerSettings.bundleVersion = "0.1.0";
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.runInBackground = false;
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.SetGraphicsAPIs(BuildTarget.WebGL, new[] { GraphicsDeviceType.OpenGLES3 });
            PlayerSettings.WebGL.threadsSupport = false;
            // Let the static host compress responses; this avoids mandatory .br/.gz headers.
            PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Disabled;
            PlayerSettings.WebGL.decompressionFallback = false;
            PlayerSettings.WebGL.initialMemorySize = 128;
            PlayerSettings.WebGL.maximumMemorySize = 512;
            PlayerSettings.WebGL.dataCaching = true;
            PlayerSettings.WebGL.template = "PROJECT:Greenbox";
            QualitySettings.vSyncCount = 0;
            QualitySettings.antiAliasing = 2;
            QualitySettings.shadowDistance = 18;
            QualitySettings.shadowResolution = ShadowResolution.Low;

            var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]);
            var input = settings.FindProperty("activeInputHandler");
            if (input != null) { input.intValue = 0; settings.ApplyModifiedPropertiesWithoutUndo(); }

            // Referenced resource materials retain the variants we use without including
            // every variant of Unity's Standard shader in a small browser game.
            foreach (var entry in new[] { new[] { "GreenboxLit", "Standard" }, new[] { "GreenboxUnlit", "Unlit/Color" } })
            {
                var path = "Assets/Resources/" + entry[0] + ".mat";
                if (AssetDatabase.LoadAssetAtPath<Material>(path) == null)
                {
                    var shader = Shader.Find(entry[1]);
                    if (shader == null) throw new InvalidOperationException("Missing shader: " + entry[1]);
                    var material = new Material(shader) { color = Color.white };
                    if (material.HasProperty("_Glossiness")) material.SetFloat("_Glossiness", .05f);
                    AssetDatabase.CreateAsset(material, path);
                }
            }

            // Retain the tiny unlit shader as well for editor-authored replacement effects.
            var graphics = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset")[0]);
            var included = graphics.FindProperty("m_AlwaysIncludedShaders");
            foreach (var shaderName in new[] { "Unlit/Color" })
            {
                var shader = Shader.Find(shaderName);
                if (shader == null) throw new InvalidOperationException("Missing shader: " + shaderName);
                bool present = false;
                for (int i = 0; i < included.arraySize; i++)
                    present |= included.GetArrayElementAtIndex(i).objectReferenceValue == shader;
                if (!present)
                {
                    int slot = included.arraySize;
                    included.InsertArrayElementAtIndex(slot);
                    included.GetArrayElementAtIndex(slot).objectReferenceValue = shader;
                }
            }
            graphics.ApplyModifiedPropertiesWithoutUndo();
        }

        [MenuItem("Greenbox/Build Browser Game")]
        public static void BuildWeb()
        {
            Prepare();
            if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.WebGL, BuildTarget.WebGL))
                throw new InvalidOperationException("Install Web Build Support for this Unity version in Unity Hub.");
            string output = ReadArgument("-greenboxOutput") ?? Path.GetFullPath("../../unity-build");
            Directory.CreateDirectory(output);
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = output,
                target = BuildTarget.WebGL,
                options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException("Greenbox Web build failed: " + report.summary.result);
            File.WriteAllText(Path.Combine(output, "vercel.json"),
                "{\"headers\":[{\"source\":\"/Build/(.*).wasm\",\"headers\":[{\"key\":\"Content-Type\",\"value\":\"application/wasm\"}]}]}");
            Debug.Log("Greenbox browser build: " + output + " (" + report.summary.totalSize + " bytes)");
        }

        private static string ReadArgument(string key)
        {
            var args = Environment.GetCommandLineArgs();
            for (int i = 0; i + 1 < args.Length; i++) if (args[i] == key) return args[i + 1];
            return null;
        }
    }
}
