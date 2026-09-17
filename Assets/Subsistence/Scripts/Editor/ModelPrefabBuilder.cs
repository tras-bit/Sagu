// ============================================================================
//  SUBSISTENCE — Editor/ModelPrefabBuilder.cs
//  Меню: «Subsistence → 7. Модели: префабы и Resources»
//
//  Что делает:
//   1) проходит по всем FBX в Assets/Subsistence/Models (**),
//   2) настраивает импортер: без анимаций/камер/света, без коллайдеров,
//      mesh compression off, global scale 1, материалы импортируются,
//   3) собирает из каждой модели префаб и кладёт его в
//      Assets/Subsistence/Resources/Models/<Имя>.prefab — именно оттуда
//      World/ModelLibrary.cs достаёт визуалы в рантайме (Resources.Load).
//
//  После этого пункта код сам начинает использовать настоящие модели:
//  монстры, транспорт, торговец, вендинг, кабина лифта, лут-контейнеры и
//  блоки постройки (с тинтом по тиру). Пока пункт не нажат — работают
//  примитивные заглушки, игра не падает.
//
//  Пункт безопасно запускать повторно: префабы перезаписываются.
// ============================================================================
#if UNITY_EDITOR
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Subsistence.EditorTools
{
    public static class ModelPrefabBuilder
    {
        const string ModelsRoot = "Assets/Subsistence/Models";
        const string ModelsHPRoot = "Assets/Subsistence/ModelsHP";   // хай-поли пасс (ANSWERS_V3 8а)
        const string ResourcesModels = "Assets/Subsistence/Resources/Models";

        [MenuItem("Subsistence/7. Модели: префабы и Resources", priority = 7)]
        public static void BuildModelPrefabs()
        {
            if (!Directory.Exists(ModelsRoot))
            {
                Debug.LogError($"[Subsistence] Нет папки {ModelsRoot} — нечего собирать.");
                return;
            }
            if (!Directory.Exists(ResourcesModels))
            {
                Directory.CreateDirectory(ResourcesModels);
                AssetDatabase.Refresh();
            }

            var fbx = new List<string>();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { ModelsRoot }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (path.EndsWith(".fbx", System.StringComparison.OrdinalIgnoreCase)) fbx.Add(path);
            }
            fbx.Sort(System.StringComparer.OrdinalIgnoreCase);

            // Хай-поли пасс: ModelsHP/<имя>/<имя>_hp.fbx (+ _color/_normal/_ao + _lod1/_lod2).
            // Если для модели есть HP-версия — префаб собирается из неё (имя то же, рантайм не меняется).
            var hpDirs = new Dictionary<string, string>();
            int hpUsed = 0;
            if (Directory.Exists(ModelsHPRoot))
                foreach (var dir in Directory.GetDirectories(ModelsHPRoot))
                {
                    string baseName = Path.GetFileName(dir);
                    if (File.Exists($"{dir}/{baseName}_hp.fbx"))
                        hpDirs[baseName] = dir.Replace('\\', '/');
                }

            int made = 0, skipped = 0, reimported = 0;
            try
            {
                AssetDatabase.StartAssetEditing();
                for (int i = 0; i < fbx.Count; i++)
                {
                    string path = fbx[i];
                    string name = Path.GetFileNameWithoutExtension(path);
                    bool isHp = hpDirs.ContainsKey(name);
                    if (isHp) path = $"{hpDirs[name]}/{name}_hp.fbx";
                    if (ConfigureImporter(path)) reimported++;

                    var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                    if (model == null) { skipped++; continue; }

                    // Инстанс модели → префаб. Так в префаб попадает вся иерархия FBX.
                    var instance = PrefabUtility.InstantiatePrefab(model) as GameObject;
                    if (instance == null) { skipped++; continue; }
                    instance.name = name;

                    if (isHp)
                    {
                        SetupHpMaterial(instance, name, hpDirs[name]);
                        SetupLodGroup(instance, name, hpDirs[name]);
                        hpUsed++;
                    }

                    string dest = $"{ResourcesModels}/{name}.prefab";
                    var saved = PrefabUtility.SaveAsPrefabAsset(instance, dest, out bool ok);
                    Object.DestroyImmediate(instance);

                    if (ok && saved != null) made++; else skipped++;
                }
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();
            }

            Debug.Log($"<color=#39ff6a>[Subsistence]</color> Модели: префабов собрано <b>{made}</b> " +
                      $"(переимпортировано {reimported}, пропущено {skipped}, из них хай-поли <b>{hpUsed}</b>) → {ResourcesModels}\n" +
                      "Дальше ничего настраивать не нужно: World/ModelLibrary подхватит их сам.");
        }

        // ------------------------------------------------------------------
        //  Хай-поли пасс (ModelsHP): материал с запечёнными картами + LODGroup
        // ------------------------------------------------------------------

        /// <summary>Материал HDRP/Lit с albedo×AO и нормалями из ModelsHP/<имя>/.</summary>
        static void SetupHpMaterial(GameObject instance, string name, string dir)
        {
            var renderers = instance.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length == 0) return;

            string albedoPath = MakeAlbedoAo(dir, name);                 // color × AO (AO вшит в альбедо)
            string normalPath = $"{dir}/{name}_normal.png";
            string colorPath = $"{dir}/{name}_color.png";
            if (!File.Exists(albedoPath) && !File.Exists(colorPath)) return;

            var shader = Shader.Find("HDRP/Lit") ?? Shader.Find("Standard");
            if (shader == null) return;
            var mat = new Material(shader);

            var albedo = LoadHpTexture(File.Exists(albedoPath) ? albedoPath : colorPath, false);
            if (albedo != null) mat.SetTexture("_BaseColorMap", albedo);
            if (File.Exists(normalPath))
            {
                var normal = LoadHpTexture(normalPath, true);            // true → TextureImporter NormalMap
                if (normal != null) mat.SetTexture("_NormalMap", normal);
            }
            if (mat.HasProperty("_BaseColorMap") && mat.GetTexture("_BaseColorMap") == null) return; // HDRP не нашёлся — не ломаем
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", 0.75f);

            for (int i = 0; i < renderers.Length; i++)
                renderers[i].sharedMaterial = mat;
        }

        /// <summary>Импорт PNG из ModelsHP как текстуры (normalMap=true → тип NormalMap, linear).</summary>
        static Texture2D LoadHpTexture(string path, bool normalMap)
        {
            if (!File.Exists(path)) return null;
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer != null)
            {
                bool dirty = false;
                if (normalMap && importer.textureType != TextureImporterType.NormalMap)
                { importer.textureType = TextureImporterType.NormalMap; dirty = true; }
                if (!normalMap && importer.textureType != TextureImporterType.Default)
                { importer.textureType = TextureImporterType.Default; dirty = true; }
                if (importer.sRGBTexture == normalMap) { importer.sRGBTexture = !normalMap; dirty = true; }
                if (dirty) importer.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        /// <summary>Смешивает <имя>_color.png с <имя>_ao.png (AO вшивается в альбедо: floor 0.55) → <имя>_albedo.png.</summary>
        static string MakeAlbedoAo(string dir, string name)
        {
            string outPath = $"{dir}/{name}_albedo.png";
            string colorPath = $"{dir}/{name}_color.png";
            string aoPath = $"{dir}/{name}_ao.png";
            if (!File.Exists(colorPath)) return "";
            if (!File.Exists(aoPath) || File.Exists(outPath)) return outPath;

            var color = LoadReadablePng(colorPath);
            var ao = LoadReadablePng(aoPath);
            if (color == null || ao == null)
            {
                if (color != null) Object.DestroyImmediate(color);
                if (ao != null) Object.DestroyImmediate(ao);
                return "";
            }

            int w = color.width, h = color.height;
            var result = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var cp = color.GetPixels();
            var rp = new Color[cp.Length];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    int i = y * w + x;
                    float occ = ao.GetPixel(x * ao.width / w, y * ao.height / h).r;
                    float k = 0.55f + 0.45f * occ;                     // AO: 0.55 (тень) … 1.0 (открыто)
                    var c = cp[i];
                    rp[i] = new Color(c.r * k, c.g * k, c.b * k, c.a);
                }
            result.SetPixels(rp);
            result.Apply(false, false);
            File.WriteAllBytes(outPath, result.EncodeToPNG());
            Object.DestroyImmediate(color); Object.DestroyImmediate(ao); Object.DestroyImmediate(result);
            AssetDatabase.ImportAsset(outPath);
            return outPath;
        }

        static Texture2D LoadReadablePng(string path)
        {
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
            return tex.LoadImage(File.ReadAllBytes(path)) ? tex : null;
        }

        /// <summary>LODGroup: LOD0 = сама модель, LOD1/LOD2 из <имя>_lod1/_lod2.fbx (60/30/10 % экрана).</summary>
        static void SetupLodGroup(GameObject instance, string name, string dir)
        {
            GameObject lod1 = LoadHpModel($"{dir}/{name}_lod1.fbx");
            GameObject lod2 = LoadHpModel($"{dir}/{name}_lod2.fbx");
            if (lod1 == null)
            {
                if (lod2 != null) Object.DestroyImmediate(lod2);
                return;
            }

            var own = instance.GetComponentsInChildren<Renderer>(true);
            var go1 = Object.Instantiate(lod1, instance.transform); go1.name = "LOD1";
            var rs1 = go1.GetComponentsInChildren<Renderer>(true);

            LOD[] lods;
            if (lod2 != null)
            {
                var go2 = Object.Instantiate(lod2, instance.transform); go2.name = "LOD2";
                var rs2 = go2.GetComponentsInChildren<Renderer>(true);
                lods = new[] { new LOD(0.60f, own), new LOD(0.30f, rs1), new LOD(0.10f, rs2) };
            }
            else
            {
                lods = new[] { new LOD(0.60f, own), new LOD(0.15f, rs1) };
            }
            var group = instance.GetComponent<LODGroup>();
            if (group == null) group = instance.AddComponent<LODGroup>();
            group.SetLODs(lods);
            Object.DestroyImmediate(lod1);
            if (lod2 != null) Object.DestroyImmediate(lod2);
        }

        static GameObject LoadHpModel(string path)
        {
            if (!File.Exists(path)) return null;
            return AssetDatabase.LoadAssetAtPath<GameObject>(path);
        }

        /// <summary>Настройки импорта: статичный меш, без анимаций/камер/света, без коллайдеров.</summary>
        static bool ConfigureImporter(string path)
        {
            var importer = AssetImporter.GetAtPath(path) as ModelImporter;
            if (importer == null) return false;

            bool dirty = false;
            if (importer.importAnimation) { importer.importAnimation = false; dirty = true; }
            if (importer.animationType != ModelImporterAnimationType.None) { importer.animationType = ModelImporterAnimationType.None; dirty = true; }
            if (importer.importCameras) { importer.importCameras = false; dirty = true; }
            if (importer.importLights) { importer.importLights = false; dirty = true; }
            if (importer.importBlendShapes) { importer.importBlendShapes = false; dirty = true; }
            if (!importer.importMaterials) { importer.importMaterials = true; dirty = true; }
            if (importer.addCollider) { importer.addCollider = false; dirty = true; }   // коллайдеры даёт геймплей
            if (importer.meshCompression != ModelImporterMeshCompression.Off) { importer.meshCompression = ModelImporterMeshCompression.Off; dirty = true; }
            if (Mathf.Abs(importer.globalScale - 1f) > 0.0001f) { importer.globalScale = 1f; dirty = true; }

            if (dirty) importer.SaveAndReimport();
            return dirty;
        }

        [MenuItem("Subsistence/8. Проверить модели (отчёт)", priority = 8)]
        public static void ReportModels()
        {
            var names = new List<string>();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { ModelsRoot }))
                names.Add(Path.GetFileNameWithoutExtension(AssetDatabase.GUIDToAssetPath(guid)));

            var ready = new List<string>();
            for (int i = 0; i < names.Count; i++)
                if (File.Exists($"{ResourcesModels}/{names[i]}.prefab")) ready.Add(names[i]);

            Debug.Log($"<color=#39ff6a>[Subsistence]</color> Моделей в проекте: <b>{names.Count}</b>, " +
                      $"готовых префабов в Resources: <b>{ready.Count}</b>.\n" +
                      (ready.Count < names.Count ? "Нажми «Subsistence → 7. Модели: префабы и Resources»." : "Всё готово."));
        }
    }
}
#endif
