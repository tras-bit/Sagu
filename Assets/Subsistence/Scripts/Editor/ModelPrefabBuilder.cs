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
//  Хай-поли пасс (ModelsHP), v1.1.5 «TEX-FIX»:
//   - ФАЗА 1 (до StartAssetEditing): альбедо color×AO → <имя>_albedo.png,
//     типы текстур (нормаль → NormalMap/linear) через настоящий
//     SaveAndReimport, и материал сохраняется НА ДИСК как ассет
//     ModelsHP/<имя>/<имя>_HP.mat. В 1.1.4 материал жил только в памяти —
//     ссылка из префаба терялась, и в игре оставались плоские FBX-материалы.
//   - ФАЗА 2: LOD-дети добавляются ДО назначения материала, поэтому
//     <имя>_HP.mat получает и LOD0, и LOD1/LOD2 (раньше LOD-уровни
//     оставались с FBX-материалами — отсюда «перемешанные» текстуры).
//   - Пороги LOD 0.50/0.22/0.08 (раньше 0.60/0.30/0.10 — LOD1 включался
//     почти всегда).
//
//  Пункт безопасно запускать повторно: префабы и материалы перезаписываются.
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
            if (Directory.Exists(ModelsHPRoot))
                foreach (var dir in Directory.GetDirectories(ModelsHPRoot))
                {
                    string baseName = Path.GetFileName(dir);
                    if (File.Exists($"{dir}/{baseName}_hp.fbx"))
                        hpDirs[baseName] = dir.Replace('\\', '/');
                }

            // ФАЗА 1 — всё, что требует немедленного импорта/записи ассетов:
            // альбедо, типы текстур, материал-ассет <имя>_HP.mat.
            var hpMats = new Dictionary<string, Material>();
            int hpTexFixed = PrepareHpAssets(hpDirs, hpMats);

            int made = 0, skipped = 0, reimported = 0, hpUsed = 0;
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
                        // Сначала LOD-дети, ПОТОМ материал — иначе LOD1/LOD2
                        // останутся с плоскими FBX-материалами (баг 1.1.4).
                        SetupLodGroup(instance, name, hpDirs[name]);
                        Material mat;
                        if (hpMats.TryGetValue(name, out mat) && mat != null)
                            ApplyHpMaterial(instance, mat);
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
                      $"(переимпортировано {reimported}, пропущено {skipped}, из них хай-поли <b>{hpUsed}</b>, " +
                      $"материалов HP <b>{hpMats.Count}</b>, текстур поправлено {hpTexFixed}) → {ResourcesModels}\n" +
                      "Дальше ничего настраивать не нужно: World/ModelLibrary подхватит их сам.");
        }

        // ------------------------------------------------------------------
        //  Хай-поли пасс (ModelsHP)
        // ------------------------------------------------------------------

        /// <summary>
        /// Фаза 1: для каждой ModelsHP-модели готовит ассеты НА ДИСКЕ —
        /// альбедо (color×AO), правильные типы текстур и материал
        /// &lt;имя&gt;_HP.mat. Выполняется ВНЕ StartAssetEditing, чтобы
        /// SaveAndReimport срабатывал сразу, а не откладывался.
        /// </summary>
        static int PrepareHpAssets(Dictionary<string, string> hpDirs, Dictionary<string, Material> mats)
        {
            if (hpDirs.Count == 0) return 0;
            var shader = Shader.Find("HDRP/Lit") ?? Shader.Find("Standard");
            if (shader == null) return 0;

            int fixedTex = 0;
            foreach (var kv in hpDirs)
            {
                string name = kv.Key, dir = kv.Value;

                // 1) альбедо: color × AO (AO вшит в альбедо, floor 0.55)
                string albedoPath = MakeAlbedoAo(dir, name);
                if (string.IsNullOrEmpty(albedoPath) || !File.Exists(albedoPath))
                    albedoPath = $"{dir}/{name}_color.png";
                if (!File.Exists(albedoPath)) continue;

                // 2) типы текстур: альбедо Default/sRGB, нормаль NormalMap/linear
                var albedo = EnsureTexture(albedoPath, false, ref fixedTex);
                var normal = EnsureTexture($"{dir}/{name}_normal.png", true, ref fixedTex);
                if (albedo == null) continue;

                // 3) материал-ассет: ссылка из префаба живёт только на ассет с GUID.
                var mat = GetOrCreateMaterial($"{dir}/{name}_HP.mat", shader);
                if (!mat.HasProperty("_BaseColorMap")) continue;   // HDRP/Lit не нашёлся — не ломаем
                mat.SetTexture("_BaseColorMap", albedo);
                if (normal != null && mat.HasProperty("_NormalMap"))
                    mat.SetTexture("_NormalMap", normal);
                if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", 0.75f);
                EditorUtility.SetDirty(mat);
                mats[name] = mat;
            }
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            return fixedTex;
        }

        /// <summary>Импортирует/правит PNG из ModelsHP (normalMap=true → NormalMap, linear). Возвращает текстуру.</summary>
        static Texture2D EnsureTexture(string path, bool normalMap, ref int fixedCount)
        {
            if (!File.Exists(path)) return null;
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null)
            {
                AssetDatabase.ImportAsset(path);
                importer = AssetImporter.GetAtPath(path) as TextureImporter;
            }
            if (importer != null)
            {
                bool dirty = false;
                var wantType = normalMap ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (importer.textureType != wantType) { importer.textureType = wantType; dirty = true; }
                if (importer.sRGBTexture == normalMap) { importer.sRGBTexture = !normalMap; dirty = true; }
                if (importer.anisoLevel != 4) { importer.anisoLevel = 4; dirty = true; }          // чётче под углом
                if (!importer.mipmapEnabled) { importer.mipmapEnabled = true; dirty = true; }     // без «муара» вдали
                if (dirty) { importer.SaveAndReimport(); fixedCount++; }
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        /// <summary>Загружает материал-ассет или создаёт новый на диске (перечитывается поверх при повторах).</summary>
        static Material GetOrCreateMaterial(string matPath, Shader shader)
        {
            var mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
            if (mat != null)
            {
                if (mat.shader != shader) mat.shader = shader;
                return mat;
            }
            mat = new Material(shader);
            AssetDatabase.CreateAsset(mat, matPath);
            return mat;
        }

        /// <summary>Вешает HP-материал на ВСЕ рендереры инстанса: LOD0 + LOD1 + LOD2.</summary>
        static void ApplyHpMaterial(GameObject instance, Material mat)
        {
            var renderers = instance.GetComponentsInChildren<Renderer>(true);
            for (int i = 0; i < renderers.Length; i++)
                renderers[i].sharedMaterial = mat;
        }

        /// <summary>Смешивает <имя>_color.png с <имя>_ao.png → <имя>_albedo.png (AO floor 0.55 + панч контраста/насыщенности).</summary>
        static string MakeAlbedoAo(string dir, string name)
        {
            string outPath = $"{dir}/{name}_albedo.png";
            string colorPath = $"{dir}/{name}_color.png";
            string aoPath = $"{dir}/{name}_ao.png";
            if (!File.Exists(colorPath)) return "";
            if (!File.Exists(aoPath)) return outPath;

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
                    // ПАНЧ: контраст вокруг средней яркости + насыщенность — без этого
                    // запечённые карты выглядят белёсыми/выцветшими (жалоба «текстуры говно»)
                    float r = Mathf.Clamp01((c.r * k - 0.5f) * 1.13f + 0.5f);
                    float g = Mathf.Clamp01((c.g * k - 0.5f) * 1.13f + 0.5f);
                    float b = Mathf.Clamp01((c.b * k - 0.5f) * 1.13f + 0.5f);
                    float lum = 0.299f * r + 0.587f * g + 0.114f * b;
                    rp[i] = new Color(lum + (r - lum) * 1.22f, lum + (g - lum) * 1.22f, lum + (b - lum) * 1.22f, c.a);
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

        /// <summary>LODGroup: LOD0 = сама модель, LOD1/LOD2 из <имя>_lod1/_lod2.fbx (50/22/8 % экрана).</summary>
        static void SetupLodGroup(GameObject instance, string name, string dir)
        {
            GameObject lod1 = LoadHpModel($"{dir}/{name}_lod1.fbx");
            GameObject lod2 = LoadHpModel($"{dir}/{name}_lod2.fbx");
            if (lod1 == null) return;

            var own = instance.GetComponentsInChildren<Renderer>(true);
            var go1 = Object.Instantiate(lod1, instance.transform); go1.name = "LOD1";
            var rs1 = go1.GetComponentsInChildren<Renderer>(true);

            LOD[] lods;
            if (lod2 != null)
            {
                var go2 = Object.Instantiate(lod2, instance.transform); go2.name = "LOD2";
                var rs2 = go2.GetComponentsInChildren<Renderer>(true);
                lods = new[] { new LOD(0.50f, own), new LOD(0.22f, rs1), new LOD(0.08f, rs2) };
            }
            else
            {
                lods = new[] { new LOD(0.50f, own), new LOD(0.15f, rs1) };
            }
            var group = instance.GetComponent<LODGroup>();
            if (group == null) group = instance.AddComponent<LODGroup>();
            group.SetLODs(lods);
            // lod1/lod2 — ассеты FBX (_lod1/_lod2.fbx), источник мешей для префаба: уничтожать
            // их нельзя и не нужно — DestroyImmediate по ассету даёт
            // «Destroying assets is not permitted» ×159 в консоли. Источники остаются в ModelsHP.
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
            // 2022.3: importMaterials выпилен (CS0619/CS0200) — теперь materialImportMode (1 = ImportStandard, как было true)
            if (importer.materialImportMode != ModelImporterMaterialImportMode.ImportStandard)
            { importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard; dirty = true; }
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
