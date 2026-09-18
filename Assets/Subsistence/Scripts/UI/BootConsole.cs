// ============================================================================
//  SUBSISTENCE — UI/BootConsole.cs
//  Системная консоль в стиле BACKROOMS OPERATING SYSTEM (как на референсе):
//   • шапка:  C:\SUBSISTENCESYSTEM> BACKROOMS OPERATING SYSTEM v2.0 CONSOLE [MIRROR: 7777]
//   • главное меню — обычное игровое: логотип SUBSISTENCE, крупные кнопки (1–5),
//     персонаж-хазмат справа, панель «СЕТЕВАЯ ИГРА» с полем IP
//   • на время загрузки лог разворачивается на весь экран (BIOS-стиль с ASCII-лого)
//   • снизу:  строка ввода  C:\SUBSISTENCE> _  + подсказки TAB/↑/CTRL+C/ENTER
//  Команды: PLAY HOST JOIN <ip> MAP SYSINFO SETTINGS HELP CLS EXIT (+ SEED <n>)
//  Опросник проекта (40 вопросов) в игре не нужен — он живёт отдельно:
//  site/questions.html (открывается на ПК двойным кликом).
//  Всё создаётся кодом (uGUI), работает и в пустой сцене.
// ============================================================================
using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.UI;
using Subsistence.Core;

namespace Subsistence.UI
{
    public static class UIState
    {
        public static bool AnyMenuOpen;
        public static bool BootRunning;
        public static float AimSensitivityMult = 1f;
        public static bool HudHidden;
    }

    /// <summary>Палитра и фабрика UI-элементов (единый «терминальный» стиль).</summary>
    public static class UIStyle
    {
        public static readonly Color TermGreen = new Color(0.36f, 1f, 0.57f, 1f);
        public static readonly Color TermGreenBright = new Color(0.70f, 1f, 0.82f, 1f);
        public static readonly Color TermGreenDim = new Color(0.18f, 0.55f, 0.33f, 1f);
        public static readonly Color TermGreenDark = new Color(0.09f, 0.36f, 0.21f, 1f);
        public static readonly Color BackroomsYellow = new Color(0.83f, 0.76f, 0.42f, 1f);
        public static readonly Color PanelBg = new Color(0.016f, 0.07f, 0.04f, 1f);
        public static readonly Color PanelBgDeep = new Color(0.008f, 0.04f, 0.024f, 1f);
        public static readonly Color PanelBgLight = new Color(0.04f, 0.13f, 0.08f, 1f);
        public static readonly Color DangerRed = new Color(1f, 0.42f, 0.37f, 1f);
        public static readonly Color Warning = new Color(1f, 0.90f, 0.50f, 1f);

        static Font _font;
        public static Font Font
        {
            get
            {
                if (_font != null) return _font;
                // для ASCII-арта нужен моноширинный шрифт: сначала пробуем системные
                string[] mono = { "Consolas", "Courier New", "DejaVu Sans Mono", "Liberation Mono",
                                  "Menlo", "Monaco", "Cascadia Mono", "Ubuntu Mono", "FreeMono" };
                var installed = Font.GetOSInstalledFontNames();
                if (installed != null)
                    foreach (var want in mono)
                        foreach (var have in installed)
                            if (string.Equals(have, want, StringComparison.OrdinalIgnoreCase))
                            { _font = Font.CreateDynamicFontFromOSFont(have, 16); break; }
                if (_font == null) _font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                if (_font == null) _font = Resources.GetBuiltinResource<Font>("Arial.ttf");
                if (_font == null)
                {
                    var names = Font.GetOSInstalledFontNames();
                    if (names != null && names.Length > 0) _font = Font.CreateDynamicFontFromOSFont(names[0], 16);
                }
                return _font;
            }
        }

        public static Canvas CreateCanvas(string name, int sortOrder, out CanvasScaler scaler)
        {
            var go = new GameObject(name, typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = go.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = sortOrder;
            scaler = go.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            return canvas;
        }

        public static RectTransform Panel(Transform parent, string name, Vector2 anchorMin, Vector2 anchorMax,
                                          Vector2 offsetMin, Vector2 offsetMax, Color bg)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            var rt = go.GetComponent<RectTransform>();
            rt.anchorMin = anchorMin; rt.anchorMax = anchorMax; rt.offsetMin = offsetMin; rt.offsetMax = offsetMax;
            go.GetComponent<Image>().color = bg;
            return rt;
        }

        /// <summary>
        /// Кнопка в терминальном стиле (тёмная плашка + зелёная рамка + моноширинный подпись).
        /// Позиция считается от левого верхнего угла родителя: (x, y) — верхний левый угол кнопки.
        /// </summary>
        public static Button Btn(Transform parent, string label, Vector2 pos, Vector2 size,
                                 UnityEngine.Events.UnityAction onClick)
        {
            var rt = Panel(parent, "Btn_" + label, new Vector2(0, 1), new Vector2(0, 1),
                           new Vector2(pos.x, pos.y - size.y), new Vector2(pos.x + size.x, pos.y),
                           TermGreenDark);                                   // внешний контур = рамка

            var core = Panel(rt, "Core", Vector2.zero, Vector2.one, new Vector2(2, 2), new Vector2(-2, -2),
                             new Color(0.03f, 0.11f, 0.06f, 0.96f));         // внутренняя плашка
            var coreImage = core.GetComponent<Image>();

            var text = Label(rt, label, 22, TermGreenBright, TextAnchor.MiddleCenter);
            text.rectTransform.offsetMin = new Vector2(6, 4);
            text.rectTransform.offsetMax = new Vector2(-6, -4);

            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = coreImage;                                   // подсвечиваем плашку, не рамку
            var colors = btn.colors;
            colors.normalColor = Color.white;
            colors.highlightedColor = new Color(1.7f, 1.7f, 1.7f, 1f);
            colors.pressedColor = new Color(0.6f, 0.85f, 0.7f, 1f);
            colors.selectedColor = Color.white;
            colors.fadeDuration = 0.06f;
            btn.colors = colors;
            if (onClick != null) btn.onClick.AddListener(onClick);
            return btn;
        }

        public static Text Label(Transform parent, string text, int size, Color color, TextAnchor anchor = TextAnchor.UpperLeft)
        {
            var go = new GameObject("Text", typeof(RectTransform), typeof(Text));
            go.transform.SetParent(parent, false);
            var t = go.GetComponent<Text>();
            t.font = Font; t.text = text; t.fontSize = size; t.color = color; t.alignment = anchor;
            t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Overflow;
            t.supportRichText = true;
            var rt = t.rectTransform;
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = new Vector2(8, 6); rt.offsetMax = new Vector2(-8, -6);
            return t;
        }
    }

    /// <summary>
    /// Терминальная консоль-меню: и загрузочный экран (печатает
    /// «loading level0_corridors ... starts ... ok»), и системное меню из 9 пунктов.
    /// </summary>
    public class BootConsole : MonoBehaviour
    {
        public static BootConsole Instance { get; private set; }

        [Header("Печать")]
        public float charDelay = 0.006f;
        public float lineDelay = 0.12f;
        public bool skippable = true;

        [Header("Поведение")]
        public bool autoPlayOnBoot = false;     // в редакторе удобно: сразу загрузка (минуя ввод)
        public string version = "1.1.8-alpha";

        public event Action OnPlayRequested;     // PLAY/HOST → RuntimeBootstrap грузит мир
        public event Action Finished;

        // ------------------------------------------------------------------ UI
        Canvas _canvas;
        RectTransform _root;
        Text _log, _headerLeft, _headerRight, _input, _hintLeft;
        RectTransform _caret;

        // ---- главное меню (обычное кнопочное, вместо терминального бокового)
        RectTransform _menuRoot;          // логотип + кнопки + фон-персонаж; скрывается на время загрузки
        RectTransform _netPanel;          // модалка «СЕТЕВАЯ ИГРА» (хост/подключение)
        UnityEngine.UI.InputField _ipField;
        RectTransform _promptBar, _hintBar;
        bool _bootMode;                   // true = идёт загрузка: лог развёрнут на весь экран

        // ------------------------------------------------------------- печать
        readonly List<string> _lines = new List<string>(256);
        readonly List<string> _pending = new List<string>(64);
        readonly StringBuilder _sb = new StringBuilder(4096);
        bool _typing, _skipRequested;

        // -------------------------------------------------------------- ввод
        string _buffer = "";
        readonly List<string> _history = new List<string>(32);
        int _histIdx;
        float _caretTimer, _clock;

        /// <summary>Главное меню: 5 крупных кнопок, клавиши 1–5. Терминальные команды работают в строке внизу.</summary>
        static readonly string[,] Menu =
        {
            { "1", "НОВАЯ ИГРА",       "PLAY"     },
            { "2", "СЕТЕВАЯ ИГРА",     "NETWORK"  },
            { "3", "НАСТРОЙКИ",        "SETTINGS" },
            { "4", "СПРАВКА",          "HELP"     },
            { "5", "ВЫХОД",            "EXIT"     },
        };

        static readonly string[] Logo = new string[]
        {
            " ███  █   █ ████   ███  █████  ███  █████ █████ █   █  ███  █████",
            "█   █ █   █ █   █ █   █   █   █   █   █   █     ██  █ █   █ █    ",
            "█     █   █ █   █ █       █   █       █   █     █ █ █ █     █    ",
            " ███  █   █ ████   ███    █    ███    █   ████  █ █ █ █     ████ ",
            "    █ █   █ █   █     █   █       █   █   █     █ █ █ █     █    ",
            "█   █ █   █ █   █ █   █   █   █   █   █   █     █  ██ █   █ █    ",
            " ███   ███  ████   ███  █████  ███    █   █████ █   █  ███  █████"
        };

        const string QuestionsHint = "опросник проекта (40 вопросов): site/questions.html — открывается на ПК двойным кликом";

        // ==================================================================== //
        void Awake()
        {
            Instance = this;
            try
            {
                BuildUI();
                PrintHeader();
            }
            catch (System.Exception e)
            {
                // меню не должно умирать молча: показываем ошибку на экран вместо пустоты
                Debug.LogException(e);
                FatalFallback(e);
                return;
            }
            // самопроверка: зелёная строка в логе = меню живое и всё кликается
            var problems = MenuSelfCheck();
            if (problems.Length == 0)
                Print("<color=#5cff92>[МЕНЮ] проверка пройдена: EventSystem, канвас + raycaster, 8 кнопок, поле IP — всё кликается</color>");
            else
                foreach (var p in problems)
                    Print("<color=#ff6b5e>[МЕНЮ] ПРОБЛЕМА: " + p + "</color>");
        }

        /// <summary>Канвас меню (для редакторского теста «Subsistence → 12»).</summary>
        public Canvas MenuCanvas => _canvas;

        /// <summary>
        /// Самопроверка меню: EventSystem (иначе кнопки не жмутся), канвас с raycaster'ом,
        /// 8 кнопок, поле IP с текстом, лог/строка ввода, и нет объектов с двумя Graphic
        /// (именно это ломало меню в 1.1.1). Пустой массив = всё в порядке.
        /// </summary>
        public string[] MenuSelfCheck()
        {
            var problems = new List<string>();
            // current не заполнен в edit-режиме (OnEnable не звался) — ищем и объект тоже
            var es = UnityEngine.EventSystems.EventSystem.current
                     ?? FindAnyObjectByType<UnityEngine.EventSystems.EventSystem>();
            if (es == null)
                problems.Add("нет EventSystem — кнопки не будут нажиматься");
            if (_canvas == null) problems.Add("канвас не создан");
            else if (_canvas.gameObject.GetComponent<GraphicRaycaster>() == null)
                problems.Add("на канвасе нет GraphicRaycaster — клики не дойдут до кнопок");
            if (_menuRoot == null) problems.Add("главное меню не собрано");
            else
            {
                int btns = _menuRoot.GetComponentsInChildren<Button>(true).Length;
                if (btns < 8) problems.Add($"кнопок {btns} из 8 (5 меню + СОЗДАТЬ СЕРВЕР + ПОДКЛЮЧИТЬСЯ + НАЗАД)");
            }
            if (_netPanel == null) problems.Add("панель «СЕТЕВАЯ ИГРА» не создана");
            if (_ipField == null) problems.Add("поле IP не создано");
            else if (_ipField.textComponent == null || _ipField.placeholder == null)
                problems.Add("поле IP без текста/подсказки — ввод не будет виден");
            if (_log == null || _input == null || _caret == null)
                problems.Add("лог/строка ввода/курсор не созданы");
            if (_promptBar == null || _hintBar == null) problems.Add("нижняя панель не создана");
            if (_canvas != null)
            {
                var seen = new HashSet<GameObject>();
                int dup = 0;
                foreach (var g in _canvas.GetComponentsInChildren<Graphic>(true))
                    if (!seen.Add(g.gameObject)) dup++;
                if (dup > 0) problems.Add($"объектов с двумя Graphic: {dup} — UI соберётся криво (Can't add 'Image')");
            }
            return problems.ToArray();
        }

        /// <summary>Аварийный экран: если сборка меню упала — красная ошибка вместо пустого зависшего экрана.</summary>
        void FatalFallback(System.Exception e)
        {
            try
            {
                if (_canvas == null)
                {
                    var go = new GameObject("BootFatalCanvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
                    _canvas = go.GetComponent<Canvas>();
                    _canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                    _canvas.sortingOrder = 300;
                    if (UnityEngine.EventSystems.EventSystem.current == null)
                        new GameObject("EventSystem", typeof(UnityEngine.EventSystems.EventSystem),
                                       typeof(UnityEngine.EventSystems.StandaloneInputModule));
                }
                var t = UIStyle.Label(_canvas.transform,
                    "<color=#ff6b5e>ОШИБКА СБОРКИ МЕНЮ</color>\n\n" +
                    e.GetType().Name + ": " + e.Message + "\n\n" +
                    "пришли этот текст — починю. Запуск игры пока невозможен.",
                    26, Color.white, TextAnchor.UpperLeft);
                t.rectTransform.anchorMin = new Vector2(0.08f, 0.55f);
                t.rectTransform.anchorMax = new Vector2(0.92f, 0.95f);
            }
            catch { /* совсем плохо — остаётся только лог Unity */ }
        }

        void Start()
        {
            if (autoPlayOnBoot) RequestPlay(false);
        }

        void Update()
        {
            HandleKeys();
            BlinkCaret();
            UpdateClock();
        }

        // ------------------------------------------------------------- сборка UI
        void BuildUI()
        {
            // Кнопки/поля работают мышью только при живом EventSystem — создаём, если нет
            if (UnityEngine.EventSystems.EventSystem.current == null)
            {
                var es = new GameObject("EventSystem",
                                        typeof(UnityEngine.EventSystems.EventSystem),
                                        typeof(UnityEngine.EventSystems.StandaloneInputModule));
                if (Application.isPlaying) DontDestroyOnLoad(es);   // в edit-режиме (тест «12») DontDestroyOnLoad не нужен
            }

            _canvas = UIStyle.CreateCanvas("SystemConsoleCanvas", 200, out _);
            _root = UIStyle.Panel(_canvas.transform, "Root", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, UIStyle.PanelBg);

            // ШАПКА -----------------------------------------------------------
            var hdr = UIStyle.Panel(_root, "Header", new Vector2(0, 1), new Vector2(1, 1),
                                    new Vector2(0, -38), new Vector2(0, 0), UIStyle.PanelBgDeep);
            _headerLeft = UIStyle.Label(hdr, "C:\\SUBSISTENCESYSTEM> BACKROOMS OPERATING SYSTEM v2.0 CONSOLE  [MIRROR: 7777]",
                                        18, UIStyle.TermGreenBright, TextAnchor.MiddleLeft);
            _headerLeft.rectTransform.offsetMax = new Vector2(-420, -6);
            _headerRight = UIStyle.Label(hdr, "", 16, UIStyle.TermGreenDim, TextAnchor.MiddleRight);
            _headerRight.rectTransform.offsetMin = new Vector2(900, 0);

            // ГЛАВНОЕ МЕНЮ -----------------------------------------------------
            // Обычное игровое меню: слева логотип и крупные кнопки, справа персонаж,
            // внизу — строка команд (SEED/HOST/JOIN/ip… работают как раньше).
            _menuRoot = UIStyle.Panel(_root, "MainMenu", Vector2.zero, Vector2.one,
                                      Vector2.zero, Vector2.zero, new Color(0, 0, 0, 0));

            // фон: рендер персонажа (скин из Resources/skins, прозрачный фон) у правого края
            var charTex = Resources.Load<Texture2D>("skins/hazmat.clean");
            if (charTex != null)
            {
                var bgGo = new GameObject("MenuCharacter", typeof(RawImage));
                bgGo.transform.SetParent(_menuRoot, false);
                var brt = bgGo.GetComponent<RectTransform>();
                brt.anchorMin = new Vector2(1, 0); brt.anchorMax = new Vector2(1, 1);
                brt.offsetMin = new Vector2(-880, -40); brt.offsetMax = new Vector2(20, 40);
                var bg = bgGo.GetComponent<RawImage>();
                bg.texture = charTex;
                bg.color = new Color(1f, 1f, 1f, 0.88f);
                // квадратная текстура в неквадратной зоне: кроп по uvRect, чтобы персонаж не растягивался
                float areaAspect = 880f / 1120f;                       // 880×(1080+40)
                bg.uvRect = new Rect((1f - areaAspect) * 0.5f, 0f, areaAspect, 1f);
            }
            // затемнение под кнопками, чтобы текст читался на любом фоне
            UIStyle.Panel(_menuRoot, "ShadeSolid", new Vector2(0, 0), new Vector2(0.58f, 1),
                          Vector2.zero, Vector2.zero, new Color(0.012f, 0.024f, 0.018f, 0.985f));
            UIStyle.Panel(_menuRoot, "ShadeFade", new Vector2(0.58f, 0), new Vector2(0.78f, 1),
                          Vector2.zero, Vector2.zero, new Color(0.012f, 0.024f, 0.018f, 0.62f));
            UIStyle.Panel(_menuRoot, "TopLine", new Vector2(0, 1), new Vector2(1, 1),
                          new Vector2(0, -40), new Vector2(0, -38), UIStyle.TermGreenDark);
            UIStyle.Panel(_menuRoot, "BottomLine", new Vector2(0, 0), new Vector2(1, 0),
                          new Vector2(0, 54), new Vector2(0, 56), UIStyle.TermGreenDark);

            // логотип
            var title = UIStyle.Label(_menuRoot, "SUBSISTENCE", 88, UIStyle.TermGreenBright, TextAnchor.MiddleLeft);
            title.fontStyle = FontStyle.Bold;
            title.rectTransform.anchorMin = new Vector2(0, 1); title.rectTransform.anchorMax = new Vector2(0.6f, 1);
            title.rectTransform.offsetMin = new Vector2(64, -196); title.rectTransform.offsetMax = new Vector2(0, -92);
            var tagline = UIStyle.Label(_menuRoot,
                                        "ВЫЖИВАНИЕ В BACKROOMS · L0 КОРИДОРЫ / L37 БАССЕЙНЫ / L3 ЭЛЕКТРОСТАНЦИЯ",
                                        19, UIStyle.TermGreenDim, TextAnchor.MiddleLeft);
            tagline.rectTransform.anchorMin = new Vector2(0, 1); tagline.rectTransform.anchorMax = new Vector2(0.62f, 1);
            tagline.rectTransform.offsetMin = new Vector2(68, -230); tagline.rectTransform.offsetMax = new Vector2(0, -200);

            // колонка кнопок
            for (int i = 0; i < Menu.GetLength(0); i++)
            {
                int idx = i;
                var btn = MenuBtn(_menuRoot, Menu[i, 1], new Vector2(64, -300 - i * 82), new Vector2(460, 66));
                btn.onClick.AddListener(() => Execute(Menu[idx, 2], null));
            }
            var menuHint = UIStyle.Label(_menuRoot,
                                         "клавиши 1–5 · мышь · команды: HOST · JOIN ip:порт · MAP · SYSINFO · SEED 1337 · HELP",
                                         14, UIStyle.TermGreenDark, TextAnchor.MiddleLeft);
            menuHint.rectTransform.anchorMin = new Vector2(0, 1); menuHint.rectTransform.anchorMax = new Vector2(0.62f, 1);
            menuHint.rectTransform.offsetMin = new Vector2(68, -760); menuHint.rectTransform.offsetMax = new Vector2(0, -736);

            // модалка «СЕТЕВАЯ ИГРА» ------------------------------------------
            _netPanel = UIStyle.Panel(_menuRoot, "NetPanel", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f),
                                      new Vector2(-340, -286), new Vector2(340, 286), new Color(0.028f, 0.085f, 0.055f, 0.985f));
            UIStyle.Panel(_netPanel, "Frame", Vector2.zero, Vector2.one, new Vector2(-2, -2), new Vector2(2, 2), UIStyle.TermGreenDark);
            var netTitle = UIStyle.Label(_netPanel, "СЕТЕВАЯ ИГРА", 36, UIStyle.TermGreenBright, TextAnchor.MiddleLeft);
            netTitle.fontStyle = FontStyle.Bold;
            netTitle.rectTransform.anchorMin = new Vector2(0, 1); netTitle.rectTransform.anchorMax = new Vector2(1, 1);
            netTitle.rectTransform.offsetMin = new Vector2(30, -66); netTitle.rectTransform.offsetMax = new Vector2(-20, -18);
            var hostBtn = MenuBtn(_netPanel, "СОЗДАТЬ СЕРВЕР   (ПОРТ 7777)", new Vector2(30, -100), new Vector2(620, 62));
            hostBtn.onClick.AddListener(() => Execute("HOST", null));
            var ipLabel = UIStyle.Label(_netPanel, "АДРЕС ХОСТА  (IP:ПОРТ)", 15, UIStyle.TermGreenDim, TextAnchor.MiddleLeft);
            ipLabel.rectTransform.anchorMin = new Vector2(0, 1); ipLabel.rectTransform.anchorMax = new Vector2(1, 1);
            ipLabel.rectTransform.offsetMin = new Vector2(32, -196); ipLabel.rectTransform.offsetMax = new Vector2(-20, -172);

            var ifGo = new GameObject("IPField", typeof(RectTransform), typeof(Image), typeof(InputField));
            ifGo.transform.SetParent(_netPanel, false);
            var ifRt = ifGo.GetComponent<RectTransform>();
            ifRt.anchorMin = new Vector2(0, 1); ifRt.anchorMax = new Vector2(1, 1);
            ifRt.offsetMin = new Vector2(30, -252); ifRt.offsetMax = new Vector2(-30, -198);
            ifGo.GetComponent<Image>().color = new Color(0.008f, 0.035f, 0.022f, 1f);
            var ipText = UIStyle.Label(ifGo.transform, "", 24, new Color(0.92f, 1f, 0.95f, 1f), TextAnchor.MiddleLeft);
            ipText.rectTransform.offsetMin = new Vector2(14, 2); ipText.rectTransform.offsetMax = new Vector2(-10, -2);
            var ipPh = UIStyle.Label(ifGo.transform, "192.168.1.5:7777", 24, UIStyle.TermGreenDark, TextAnchor.MiddleLeft);
            ipPh.rectTransform.offsetMin = new Vector2(14, 2); ipPh.rectTransform.offsetMax = new Vector2(-10, -2);
            _ipField = ifGo.GetComponent<InputField>();
            _ipField.textComponent = ipText;
            _ipField.placeholder = ipPh;
            _ipField.text = "";
            var joinBtn = MenuBtn(_netPanel, "ПОДКЛЮЧИТЬСЯ", new Vector2(30, -286), new Vector2(620, 62));
            joinBtn.onClick.AddListener(() =>
                Execute("JOIN", string.IsNullOrEmpty(_ipField.text) ? null : _ipField.text.Trim()));
            var netHint = UIStyle.Label(_netPanel,
                "как играть: у одного «СОЗДАТЬ СЕРВЕР», у остальных — его IP (у хоста: ipconfig). ENTER в поле = подключиться, ESC = закрыть.\n" +
                "Mirror включается в редакторе: меню Subsistence → 3, затем → 11. Выделенный сервер: Subsistence.exe -batchmode -nographics -server",
                14, UIStyle.TermGreenDark, TextAnchor.UpperLeft);
            netHint.rectTransform.anchorMin = new Vector2(0, 1); netHint.rectTransform.anchorMax = new Vector2(1, 1);
            netHint.rectTransform.offsetMin = new Vector2(32, -420); netHint.rectTransform.offsetMax = new Vector2(-28, -362);
            var backBtn = MenuBtn(_netPanel, "НАЗАД", new Vector2(30, -442), new Vector2(620, 54));
            backBtn.onClick.AddListener(() => _netPanel.gameObject.SetActive(false));
            _netPanel.gameObject.SetActive(false);

            // ЛОГ -------------------------------------------------------------
            // В меню — компактная область справа-снизу (команды SYSINFO/HELP печатают туда),
            // на время загрузки разворачивается на весь экран (EnterBootMode).
            UIStyle.Panel(_menuRoot, "LogPlate", new Vector2(0.585f, 0), new Vector2(1, 0.38f),
                          new Vector2(0, 58), new Vector2(0, 0), new Color(0.008f, 0.02f, 0.014f, 0.72f));
            _log = UIStyle.Label(_root, "", 15, UIStyle.TermGreen, TextAnchor.UpperLeft);
            _log.rectTransform.anchorMin = new Vector2(0.60f, 0); _log.rectTransform.anchorMax = new Vector2(1f, 0.38f);
            _log.rectTransform.offsetMin = new Vector2(14, 64); _log.rectTransform.offsetMax = new Vector2(-18, -6);
            _log.lineSpacing = 1.05f;
            _log.verticalOverflow = VerticalWrapMode.Truncate;

            // СТРОКА ВВОДА ----------------------------------------------------
            _promptBar = UIStyle.Panel(_root, "Prompt", new Vector2(0, 0), new Vector2(1, 0),
                                       new Vector2(0, 22), new Vector2(0, 52), UIStyle.PanelBgDeep);
            var ps1 = UIStyle.Label(_promptBar, "C:\\SUBSISTENCE>", 17, UIStyle.TermGreenBright, TextAnchor.MiddleLeft);
            ps1.rectTransform.offsetMax = new Vector2(-1000, -2);
            _input = UIStyle.Label(_promptBar, "", 17, UIStyle.TermGreen, TextAnchor.MiddleLeft);
            _input.rectTransform.offsetMin = new Vector2(246, 0);
            _input.rectTransform.offsetMax = new Vector2(-16, 0);
            _caret = UIStyle.Panel(_promptBar, "Caret", new Vector2(0, 0.5f), new Vector2(0, 0.5f),
                                   new Vector2(246, -9), new Vector2(255, 9), UIStyle.TermGreen);

            // ПОДСКАЗКИ -------------------------------------------------------
            _hintBar = UIStyle.Panel(_root, "Hint", new Vector2(0, 0), new Vector2(1, 0),
                                     new Vector2(0, 0), new Vector2(0, 22), new Color(0.008f, 0.04f, 0.024f, 1f));
            _hintLeft = UIStyle.Label(_hintBar, "> ВЫБЕРИ ПУНКТ МЕНЮ (КЛАВИШИ 1–5 ИЛИ МЫШЬ) · ПОЛНЫЙ СПИСОК КОМАНД — HELP",
                                      14, UIStyle.TermGreenDim, TextAnchor.MiddleLeft);
            _hintLeft.rectTransform.offsetMax = new Vector2(-640, 0);
            var hintRight = UIStyle.Label(_hintBar, "TAB — автодополнение   ↑ ↓ — история   CTRL+C — выход   ENTER — выполнить",
                                          14, UIStyle.TermGreenDim, TextAnchor.MiddleRight);
            hintRight.rectTransform.offsetMin = new Vector2(700, 0);
        }

        /// <summary>Кнопка главного меню: тонкая рамка, тёмная плашка, крупная подпись, подсветка при наведении.</summary>
        Button MenuBtn(RectTransform parent, string label, Vector2 topLeft, Vector2 size)
        {
            var rt = UIStyle.Panel(parent, "MB_" + label, new Vector2(0, 1), new Vector2(0, 1),
                                   new Vector2(topLeft.x, topLeft.y - size.y), new Vector2(topLeft.x + size.x, topLeft.y),
                                   new Color(0.10f, 0.24f, 0.16f, 0.55f));            // рамка
            var core = UIStyle.Panel(rt, "Core", Vector2.zero, Vector2.one, new Vector2(2, 2), new Vector2(-2, -2),
                                     new Color(0.026f, 0.075f, 0.05f, 0.95f));        // плашка
            var coreImage = core.GetComponent<Image>();
            var txt = UIStyle.Label(rt, label, 25, new Color(0.88f, 0.99f, 0.92f, 1f), TextAnchor.MiddleLeft);
            txt.fontStyle = FontStyle.Bold;
            txt.rectTransform.offsetMin = new Vector2(26, 4);
            txt.rectTransform.offsetMax = new Vector2(-12, -4);
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = coreImage;                                          // подсвечивается плашка
            var c = btn.colors;
            c.normalColor = Color.white;
            c.highlightedColor = new Color(1.8f, 1.9f, 1.85f, 1f);                  // заметная подсветка
            c.pressedColor = new Color(0.6f, 0.9f, 0.72f, 1f);
            c.selectedColor = Color.white;
            c.fadeDuration = 0.07f;
            btn.colors = c;
            return btn;
        }

        /// <summary>Модалка «СЕТЕВАЯ ИГРА»: хост одним кликом, подключение по IP.</summary>
        void OpenNetPanel()
        {
            if (_netPanel == null) return;
            _netPanel.gameObject.SetActive(!_netPanel.gameObject.activeSelf);
            if (_netFieldActive()) _ipField.ActivateInputField();
        }

        bool _netFieldActive() => _ipField != null && _netPanel != null && _netPanel.gameObject.activeSelf;

        /// <summary>Убирает главное меню и разворачивает лог на весь экран — режим загрузки мира.</summary>
        void EnterBootMode()
        {
            if (_bootMode) return;
            _bootMode = true;
            if (_menuRoot != null) _menuRoot.gameObject.SetActive(false);
            if (_promptBar != null) _promptBar.gameObject.SetActive(false);
            if (_hintBar != null) _hintBar.gameObject.SetActive(false);
            if (_log != null)
            {
                _log.rectTransform.anchorMin = Vector2.zero;
                _log.rectTransform.anchorMax = Vector2.one;
                _log.rectTransform.offsetMin = new Vector2(36, 64);
                _log.rectTransform.offsetMax = new Vector2(-36, -52);
                _log.fontSize = 17;
                _log.verticalOverflow = VerticalWrapMode.Truncate;
            }
            _lines.Clear();
            foreach (var l in Logo) Add("<color=#7dffa8>" + l + "</color>");
            Add("");
            Flush();
        }

        void UpdateClock()
        {
            if (_headerRight == null) return;
            _clock += Time.unscaledDeltaTime;
            if (_clock < 1f) return;
            _clock = 0f;
            _headerRight.text = $"{DateTime.Now:dd.MM.yyyy HH:mm}   ·   версия {version}   ·   ОТЛАДКА";
        }

        void BlinkCaret()
        {
            if (_caret == null) return;
            _caretTimer += Time.unscaledDeltaTime;
            bool on = (_caretTimer % 1f) < 0.55f;
            var img = _caret.GetComponent<Image>();
            if (img != null) img.enabled = on;
            float w = _buffer.Length * 9.6f;
            _caret.anchoredPosition = new Vector2(246 + Mathf.Min(w, 1200), _caret.anchoredPosition.y);
            if (_input != null) _input.text = _buffer;
        }

        // ------------------------------------------------------------- ВВОД
        void HandleKeys()
        {
            if (!_root.gameObject.activeSelf) return;

            // Печать в поле IP (модалка сети) — консоль не должна перехватывать клавиши
            var es = UnityEngine.EventSystems.EventSystem.current;
            var focused = es != null && es.currentSelectedGameObject != null
                          ? es.currentSelectedGameObject.GetComponent<InputField>() : null;
            if (focused != null)
            {
                if (focused == _ipField && (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter)))
                {
                    focused.DeactivateInputField();
                    Execute("JOIN", string.IsNullOrEmpty(focused.text) ? null : focused.text.Trim());
                }
                if (Input.GetKeyDown(KeyCode.Escape)) focused.DeactivateInputField();
                return;
            }
            if (Input.GetKeyDown(KeyCode.Escape) && _netPanel != null && _netPanel.gameObject.activeSelf)
            { _netPanel.gameObject.SetActive(false); return; }

            // цифры-хоткеи главного меню — ДО набора в строку: пустой буфер + меню на экране
            // (раньше проверка шла после Input.inputString, цифра уже попадала в буфер — хоткеи не работали)
            if (_buffer.Length == 0 && _menuRoot != null && _menuRoot.gameObject.activeSelf)
            {
                for (int i = 0; i < Menu.GetLength(0); i++)
                {
                    int d = Menu[i, 0][0] - '0';
                    if (d >= 0 && d <= 9 && Input.GetKeyDown(KeyCode.Alpha0 + d)) { Execute(Menu[i, 2], null); return; }
                }
            }

            string typed = Input.inputString;
            for (int i = 0; i < typed.Length; i++)
            {
                char c = typed[i];
                if (c == '\b') { if (_buffer.Length > 0) _buffer = _buffer.Substring(0, _buffer.Length - 1); }
                else if (c == '\n' || c == '\r') { Submit(); }
                else if (!char.IsControl(c) && _buffer.Length < 64) _buffer += c;
            }

            if (Input.GetKeyDown(KeyCode.UpArrow) && _history.Count > 0)
            {
                _histIdx = Mathf.Max(0, _histIdx - 1);
                _buffer = _history[_histIdx];
            }
            if (Input.GetKeyDown(KeyCode.DownArrow) && _history.Count > 0)
            {
                _histIdx = Mathf.Min(_history.Count, _histIdx + 1);
                _buffer = _histIdx >= _history.Count ? "" : _history[_histIdx];
            }
            if (Input.GetKeyDown(KeyCode.Tab))
            {
                string up = _buffer.ToUpperInvariant();
                foreach (var c in new[] { "PLAY", "HOST", "JOIN", "MAP", "SYSINFO", "SETTINGS", "HELP", "CLS", "EXIT", "SEED" })
                    if (c.StartsWith(up)) { _buffer = c; break; }
            }
            if (Input.GetKey(KeyCode.LeftControl) && Input.GetKeyDown(KeyCode.C)) _buffer = "";

        }

        void Submit()
        {
            string raw = _buffer.Trim();
            _buffer = "";
            if (raw.Length == 0) return;
            _history.Add(raw);
            _histIdx = _history.Count;
            var parts = raw.Split(' ');
            Execute(parts[0].ToUpperInvariant(), parts.Length > 1 ? parts[1] : null);
        }

        // ------------------------------------------------------------- КОМАНДЫ
        public void Execute(string cmd, string arg)
        {
            if (_hintLeft != null) _hintLeft.text = "> " + cmd + (string.IsNullOrEmpty(arg) ? "" : " " + arg);
            switch (cmd)
            {
                case "1": case "PLAY": RequestPlay(false); break;
                case "2": case "NETWORK": OpenNetPanel(); break;
                case "HOST":
#if MIRROR
                    // Мир уже собран? Поднимаем сеть сразу, без пересоздания мира.
                    if (UIState.BootRunning)
                    {
                        if (Subsistence.Net.NetFlow.StartHost(Subsistence.Net.CmdLine.Port))
                            Print($"<color=#39ff6a>[NET] ХОСТ: порт {Subsistence.Net.CmdLine.Port} — ждём игроков. Друзьям: JOIN <твой-ip>:{Subsistence.Net.CmdLine.Port}</color>");
                    }
                    else RequestPlay(true);
#else
                    RequestPlay(true);
#endif
                    break;
                case "JOIN":
#if MIRROR
                    // 31в: настоящий JOIN. Адрес: JOIN / JOIN ip / JOIN ip:port.
                    if (!TryParseEndpoint(arg, out var joinAddr, out var joinPort))
                    { Print("<color=#ffd23f>формат: JOIN ip[:port], например JOIN 192.168.1.5:7777</color>"); break; }
                    joinAddress = joinAddr;
                    joinPort = (ushort)(joinPort > 0 ? joinPort : Subsistence.Net.CmdLine.Port);
                    if (UIState.BootRunning)
                    {
                        // мир уже собран — подключаемся сразу
                        if (Subsistence.Net.NetFlow.StartClient(joinAddress, joinPort))
                            Print($"<color=#39ff6a>[NET] подключение к {joinAddress}:{joinPort} ...</color>");
                    }
                    else
                    {
                        Print($"<color=#b6ffd0>подключение к {joinAddress}:{joinPort} — загружаю мир и вхожу...</color>");
                        RequestPlay(false, true);
                    }
#else
                    Print("<color=#ffd23f>Mirror не включён в этом билде — меню «Subsistence → 3. Включить Mirror», потом «11. Сеть: собрать Mirror»</color>");
#endif
                    break;
                case "MAP": ShowMap(); break;
                case "SYSINFO": case "ABOUT": ShowSysinfo(); break;
                case "3": case "SETTINGS": ShowSettings(); break;
                case "4": case "HELP": ShowHelp(); break;
                case "C": case "CLS": case "CLEAR": PrintHeader(); break;
                case "5": case "EXIT": case "QUIT":
                    Print("завершение сеанса... спасибо, что играешь в SUBSISTENCE.");
                    Application.Quit();
                    break;
                case "SKINS": case "SHOP":
                    // 38_skins: витрина скинов (закрытая игра — только наши скины, без модов)
                    Subsistence.Progression.SkinShopUI.Open();
                    Print("витрина скинов открыта: 1..9 — купить/надеть, 0 — снять, ESC — закрыть");
                    break;
                case "LOADBOTS": case "BOTS":
                {
                    // Стенд «сеть 100+»: серверные боты + холостой прогон рассылки (docs/MULTIPLAYER.md)
                    int n = 112;
                    if (!string.IsNullOrEmpty(arg) && int.TryParse(arg, out int parsed)) n = Mathf.Clamp(parsed, 1, Balance.MaxPlayerSlots);
                    var load = gameObject.GetComponent<Subsistence.Net.NetLoadTest>();
                    if (load == null) load = gameObject.AddComponent<Subsistence.Net.NetLoadTest>();
                    load.bots = n;
                    Print($"стенд нагрузки: <color=#b6ffd0>{n}</color> ботов — старт вместе с миром, отчёт каждые 10 с (тег [netload])");
                    if (!UIState.BootRunning) RequestPlay(false);
                    break;
                }
                case "NETSTAT": case "NET":
                    // Что реально идёт по сети: приём снапшотов, трафик, реестр сущностей (100+)
                    if (!UIState.BootRunning) RequestPlay(false);
                    Print($"<color=#2f8c53>{Subsistence.Net.SnapshotClient.Report()}</color>");
#if MIRROR
                    Print($"запуск сети: {Subsistence.Net.NetFlow.Status()}");
#endif
                    Print($"сущностей в реестре: {Subsistence.Net.NetEntity.RegisteredCount}, " +
                          $"транспорт: {Subsistence.Net.NetworkBridge.Host?.GetType().Name ?? "offline"}, " +
                          $"онлайн-профиль: AOI {Subsistence.Core.Balance.AoiRadius:F0} м → " +
                          $"{Subsistence.Core.Balance.AoiRadiusMin:F0} м, снапшоты {Subsistence.Core.Balance.SnapshotRate:F0} Гц, " +
                          $"лимит пакета {Subsistence.Core.Balance.MaxEntitiesPerSnapshot}");
                    break;
                case "NETRESET":
                    Subsistence.Net.SnapshotClient.ResetStats();
#if MIRROR
                    Subsistence.Net.NetFlow.StopAll();
                    Print("счётчики сети сброшены, сеть остановлена (снова — после рестарта игры: HOST / JOIN ip)");
#else
                    Print("счётчики сети сброшены");
#endif
                    break;
                case "SEED":
                    if (int.TryParse(arg, out int s))
                    {
                        PlayerPrefs.SetInt("subsistence_seed", s);
                        Print($"seed = <color=#b6ffd0>{s}</color> (применится при следующей генерации)");
                    }
                    else Print("<color=#ffd23f>SEED: укажи число, например SEED 1337</color>");
                    break;
                default:
                    // 36_anticheat: админ-команды живут в Net/AdminSystem (god, noclip, tp, give, spawn, ban...)
                    if (Subsistence.Net.AdminSystem.TryExecute(cmd, arg)) break;
                    Print($"<color=#ffd23f>неизвестная команда: {cmd} — набери HELP</color>");
                    break;
            }
        }

        void RequestPlay(bool host, bool join = false)
        {
            UIState.AnyMenuOpen = false;
            UIState.BootRunning = true;
            hostRequested = host;
            joinRequested = join;
            EnterBootMode();                  // меню прочь, лог на весь экран — пошла загрузка
            OnPlayRequested?.Invoke();
        }

        // ---- сеть (31в): что попросили из меню — RuntimeBootstrap стартует ПОСЛЕ генерации мира ----
        [NonSerialized] public bool hostRequested;
        [NonSerialized] public bool joinRequested;
        [NonSerialized] public string joinAddress = "127.0.0.1";
        [NonSerialized] public ushort joinPort = 7777;

        /// <summary>"ip", "ip:port", "" → адрес+порт (0 = порт по умолчанию).</summary>
        static bool TryParseEndpoint(string s, out string addr, out int port)
        {
            addr = "127.0.0.1"; port = 0;
            if (string.IsNullOrWhiteSpace(s)) return true;
            int i = s.LastIndexOf(':');
            if (i >= 0)
            {
                if (!int.TryParse(s.Substring(i + 1), out port) || port < 1 || port > 65535) return false;
                s = s.Substring(0, i);
            }
            if (string.IsNullOrWhiteSpace(s)) return false;
            addr = s.Trim();
            return true;
        }



        // ------------------------------------------------------------- ЭКРАНЫ
        public void PrintHeader()
        {
            _lines.Clear();
            _pending.Clear();
            _lines.Add("<color=#b6ffd0>SUBSISTENCE 2.0</color> — режим выживания в Backrooms");
            _lines.Add($"сид мира: <color=#b6ffd0>{PlayerPrefs.GetInt("subsistence_seed", 1337)}</color> (сменить: SEED 1337) · версия {version}");
            _lines.Add("");
            _lines.Add("Быстрый старт: <color=#b6ffd0>НОВАЯ ИГРА</color> — одиночная · <color=#b6ffd0>СЕТЕВАЯ ИГРА</color> — с друзьями (2–4)");
            _lines.Add("Команды строки: <color=#b6ffd0>HOST</color> · <color=#b6ffd0>JOIN ip:порт</color> · <color=#b6ffd0>MAP</color> · <color=#b6ffd0>SYSINFO</color> · <color=#b6ffd0>SETTINGS</color> · <color=#b6ffd0>HELP</color> · <color=#b6ffd0>SKINS</color> · <color=#b6ffd0>CLS</color>");
            _lines.Add($"<color=#2f8c53>{QuestionsHint}</color>");
            Flush();
        }

        void ShowHelp()
        {
            AddRange(new[]
            {
                "<color=#b6ffd0>СПИСОК КОМАНД</color>",
                "PLAY              запустить одиночную сессию (загрузка уровней 0 → 37 → 3)",
                "NETWORK           панель сетевой игры (хост / подключение по IP:порт)",
                "HOST              создать сервер (Mirror, порт 7777; цель 100+ онлайн, лимит 128)",
                "JOIN <ip>         подключиться к серверу (например: JOIN 127.0.0.1)",
                "MAP               карта трёх уровней с легендой и тирами лута",
                "SYSINFO           состояние систем проекта и краткое описание",
                "SETTINGS          графические и сетевые настройки",
                "HELP              этот список",
                "CLS               очистить экран",
                "EXIT              выход",
                "SKINS             витрина скинов (купленное хранится локально)",
                "NETSTAT           сеть: приём снапшотов, трафик, реестр сущностей (для теста 100+)",
                "LOADBOTS [n]       стенд нагрузки: n серверных ботов (по умолчанию 112)",
                "SEED <число>      служебная: сменить seed генерации мира",
                "",
                $"<color=#2f8c53>{QuestionsHint}</color>",
            });
        }

        void ShowMap()
        {
            AddRange(new[]
            {
                "<color=#b6ffd0>КАРТА СИСТЕМЫ SUBSISTENCE</color> — 3 уровня, 3 тира лута [OK]",
                "",
                "<color=#d9cf7a>LEVEL 0 — ЖЁЛТЫЕ КОРИДОРЫ · TIER 1 · старт</color>",
                "  обои · ковролин · гудящие лампы · Smiler идёт на свет и на любой шум (12_sanity: рассудка нет)",
                "  лут: самопал, waterpipe, лук, хазмат (редко), зелёная ключ-карта",
                "  переходы: ЛИФТЫ по ключ-картам (зелёная → Level 37, синяя → Level 3), вниз — свободно",
                "  стройка разрешена везде, кроме чужой территории под шкафом (25_build_zones)",
                "",
                "<color=#7fd7e0>LEVEL 37 — БАССЕЙНЫ · TIER 2</color>",
                "  вода 0.4–2.6 м: замедление, шум, переохлаждение, воздух 5 с · эхо усиливает шум",
                "  лут: MP5, pump, semi-auto, roadsign-броня, сачель, синяя ключ-карта (насосные)",
                "  опасность: Hound (6.8 м/с), Partygoer (360°), Clump",
                "",
                "<color=#9ad67a>LEVEL 3 — ЭЛЕКТРОСТАНЦИЯ · TIER 3 · эндшпиль</color>",
                "  реактор 12 рад/с · разливы ОЖ 4 рад/с · без хазмата смерть за ~2 минуты",
                "  лут: AK/M249/РПГ, металл-броня, ПНВ, C4, красная ключ-карта, ТВЭЛ",
                "  опасность: Skin-Stealer (босс Bacteria убран из игры — решение 29_boss)",
                "  транспорт: вагонетки по кольцевым рельсам, тележки для лута, самокат",
            });
        }

        void ShowSysinfo()
        {
            AddRange(new[]
            {
                "<color=#b6ffd0>СОСТОЯНИЕ СИСТЕМ</color>",
                "СИСТЕМА       : SUBSISTENCE OS v" + version + "  <color=#5cff92>[ОК]</color>",
                "ЯДРО          : инвентарь/прочность/оружие/броня/стройка/рейды  <color=#5cff92>[ОК]</color>",
                "УРОВНИ        : 3/3  <color=#5cff92>[ОК]</color>",
                "ЛУТ           : 9 таблиц, 3 тира  <color=#5cff92>[ОК]</color>",
                "МОНСТРЫ       : Smiler · Hound · Partygoer · Clump · Skin-Stealer  <color=#5cff92>[ОК]</color>",
                "РАССУДОК      : механика убрана (12_sanity)  <color=#5cff92>[ОК]</color>",
                "ТРАНСПОРТ     : самокаты · тележки лута · вагонетки · лифты по картам  <color=#5cff92>[ОК]</color>",
                "ТОРГОВЛЯ      : вендинг + NPC в безопасных комнатах (PvP и спавн выключены)  <color=#5cff92>[ОК]</color>",
                "АДМИНЫ        : своя валидация + god/noclip/kick/ban/give (аудит-лог)  <color=#5cff92>[ОК]</color>",
                "ПРОИЗВОДИТЕЛЬН: цель 120 FPS / RTX 3060 · только Windows  <color=#5cff92>[ОК]</color>",
                "МОДЕЛИ        : 35 FBX / 35 GLB / 36 превью  <color=#5cff92>[ОК]</color>",
                "СЕТЬ          : Mirror-адаптер, AOI 32 м, античит-валидатор  <color=#5cff92>[ОК]</color>",
                "ОШИБОК        : <color=#5cff92>0</color>",
                "",
                "<color=#b6ffd0>О ПРОЕКТЕ</color>",
                "SUBSISTENCE — сетевой survival-хоррор: механики Rust (строительство, рейды, прочность,",
                "лут, крафт) в мире Backrooms. Три уровня = три тира лута.",
                "Unity 2022.3.62f2 · HDRP 14.0.12 · Mirror-адаптер · 22 скрипта C# · 35 моделей FBX/GLB.",
            });
        }

        void ShowSettings()
        {
            AddRange(new[]
            {
                "<color=#b6ffd0>НАСТРОЙКИ ПРОЕКТА</color>",
                "Графика: HDRP 14.0.12 · объёмный туман 0.35 · SSAO 0.6 · тени 60 м · bloom 0.15",
                $"Производительность: цель {Balance.TargetFps} FPS (RTX 3060) · апскейл/DLSS — в HDRP-ассете",
                $"Вайп: раз в {Balance.WipeDays} дней · размер уровня: {Balance.LevelSizeMeters:F0}×{Balance.LevelSizeMeters:F0} м",
                $"Seed мира: <color=#b6ffd0>{PlayerPrefs.GetInt("subsistence_seed", 1337)}</color> (сменить: SEED 1337)",
                "Сервер: порт 7777 · тик 30 Гц · снапшоты 20 Гц · AOI 32 м · макс. 128 игроков",
                "",
                "<color=#b6ffd0>УПРАВЛЕНИЕ</color>",
                "WASD — движение · SHIFT — бег · CTRL/C — присед · Z — лёж · SPACE — прыжок",
                "ЛКМ — огонь · ПКМ — прицел/апгрейд · R — перезарядка/поворот · E — взаимодействие",
                "TAB — инвентарь · Q — крафт / радиальное меню постройки · G — выбросить · F — съесть",
                "M — карта · V — голосовой чат · ENTER — чат",
            });
        }

        // ------------------------------------------------------------- ПЕЧАТЬ
        void AddRange(IEnumerable<string> lines) { foreach (var l in lines) Add(l); Flush(); }
        void Add(string line) => _lines.Add(line);

        /// <summary>Добавить строку с «печатной машинкой» (используется загрузкой уровней).
        /// Печать запускается сама — раньше Play() никто не вызывал и лог молчал.</summary>
        public void Print(string line)
        {
            _pending.Add(FormatBoot(line));
            if (!_typing && isActiveAndEnabled) StartCoroutine(TypeRoutine());
        }

        public void PrintBoot(string tag, string message) => Print($"<color=#5cff92>[{tag}]</color> {message}");
        public void PrintOk(string what) => Print($"<color=#5cff92>{what} ... ok</color>");
        public void PrintWarn(string what) => Print($"<color=#ffd23f>{what} ... warn</color>");
        public void PrintFail(string what) => Print($"<color=#ff6b5e>{what} ... fail</color>");

        static string FormatBoot(string line)
        {
            if (line.Contains("... starts")) return "<color=#b6ffd0>" + line + "</color>";
            if (line.Contains("... ok")) return "<color=#5cff92>" + line + "</color>";
            return line;
        }

        /// <summary>Начать печать очереди (после нажатия PLAY).</summary>
        public void Play()
        {
            if (_typing) return;
            StartCoroutine(TypeRoutine());
        }

        IEnumerator TypeRoutine()
        {
            UIState.BootRunning = true;
            _typing = true;
            _skipRequested = false;
            while (_pending.Count > 0 || _lines.Count == 0)
            {
                if (_pending.Count == 0) { yield return null; continue; }
                string line = _pending[0];
                _pending.RemoveAt(0);

                if (_skipRequested) { _lines.Add(line); Flush(); continue; }

                string plain = StripTags(line);
                string shown = "";
                for (int i = 0; i < plain.Length; i++)
                {
                    shown += plain[i];
                    Flush(shown);
                    if (skippable && (Input.anyKeyDown || Input.GetMouseButtonDown(0))) _skipRequested = true;
                    if (!_skipRequested) yield return new WaitForSeconds(charDelay);
                }
                _lines.Add(line);
                Flush();
                if (!_skipRequested) yield return new WaitForSeconds(lineDelay);
            }
            _typing = false;
            UIState.BootRunning = false;
            Finished?.Invoke();
        }

        static string StripTags(string s)
        {
            int lt;
            while ((lt = s.IndexOf('<')) >= 0)
            {
                int gt = s.IndexOf('>', lt);
                if (gt < 0) break;
                s = s.Remove(lt, gt - lt + 1);
            }
            return s;
        }

        void Flush(string current = null)
        {
            if (_log == null) return;
            _sb.Length = 0;
            int max = 46;
            int start = Mathf.Max(0, _lines.Count - max);
            for (int i = start; i < _lines.Count; i++) _sb.Append(_lines[i]).Append('\n');
            if (current != null) _sb.Append(current);
            _log.text = _sb.ToString();
        }

        public void Hide() { if (_canvas != null) _canvas.gameObject.SetActive(false); }
        public void Show() { if (_canvas != null) _canvas.gameObject.SetActive(true); EnterBootMode(); }
        public bool IsTyping => _typing;
        public bool IsVisible => _canvas != null && _canvas.gameObject.activeSelf;
    }
}
