// ============================================================================
//  SUBSISTENCE — Net/MirrorAdapter/NetFlow.cs
//  Рантайм-оркестратор сети (31в: 2–4 игрока). Тот кусок, которого не хватало:
//  именно здесь создаются MirrorSubsistenceManager + транспорт и запускаются
//  Host / Client / ServerOnly.
//
//  Потоки запуска (все приходят сюда):
//    • меню консоли: [2] HOST → NetFlow.StartHost, [3] JOIN ip → StartClient
//    • командная строка: --server → StartServerOnly, --client --host X → StartClient
//    • RuntimeBootstrap зовёт это ПОСЛЕ генерации мира (сид фиксированный —
//      мир у всех участников одинаковый, сервер досылает лишь состояние).
//
//  Префаб игрока: Resources/Net/MirrorPlayer.prefab — собирается один раз
//  меню «Subsistence → 11. Сеть: собрать Mirror (менеджер+префаб)».
// ============================================================================
#if MIRROR
using System;
using System.Reflection;
using Mirror;
using Subsistence.Core;
using UnityEngine;

namespace Subsistence.Net
{
    public static class NetFlow
    {
        static MirrorSubsistenceManager _manager;
        public static bool Active => _manager != null && (NetworkServer.active || NetworkClient.active);
        public static bool IsHost => _manager != null && NetworkServer.active && NetworkClient.active;
        public static int Online => NetworkServer.connections.Count;

        /// <summary>Менеджер + транспорт + префаб игрока (идемпотентно).</summary>
        public static MirrorSubsistenceManager EnsureManager()
        {
            if (_manager != null) return _manager;

            var go = new GameObject("SubsistenceNet");
            UnityEngine.Object.DontDestroyOnLoad(go);
            var mgr = go.AddComponent<MirrorSubsistenceManager>();

            // Транспорт: в v96 в пакете лежат KcpTransport и TelepathyTransport.
            // Берём KCP (надёжнее для FPS), фолбэк — Telepathy. Через рефлексию,
            // чтобы не зависеть от точного состава минорной версии пакета.
            if (go.GetComponent<Transport>() == null)
            {
                foreach (var name in new[] { "KcpTransport", "TelepathyTransport", "SimpleWebTransport" })
                {
                    var t = Type.GetType("Mirror." + name + ", Mirror", false)
                            ?? Type.GetType(name + ", Mirror", false);
                    if (t != null) { go.AddComponent(t); break; }
                }
                if (go.GetComponent<Transport>() == null)
                    Debug.LogError("[NetFlow] В пакете Mirror не найден транспорт (KcpTransport/Telepathy). Установи Mirror целиком.");
            }

            // Префаб игрока (меню «11»): тело-аватар + PlayerController(remote) + MirrorPlayer
            var prefab = Resources.Load<GameObject>("Net/MirrorPlayer");
            if (prefab == null)
            {
                Debug.LogError("[NetFlow] Нет Resources/Net/MirrorPlayer.prefab — запусти в редакторе меню " +
                               "«Subsistence → 11. Сеть: собрать Mirror (менеджер+префаб)» и пересобери билд.");
            }
            else mgr.playerPrefab = prefab;

            _manager = mgr;
            Debug.Log("[NetFlow] Менеджер готов: транспорт " + go.GetComponent<Transport>().GetType().Name +
                      ", тик " + Balance.TickRate + " Гц, порт по умолчанию " + CmdLine.Port + ".");
            return mgr;
        }

        static void SetPort(GameObject host, ushort port)
        {
            var tr = host.GetComponent<Transport>();
            if (tr == null) return;
            var p = tr.GetType().GetProperty("Port");
            if (p != null && p.CanWrite) { try { p.SetValue(tr, (int)port, null); } catch { } }
        }

        /// <summary>Хост: играем + принимаем подключения (2–4 игрока).</summary>
        public static bool StartHost(ushort port = 7777)
        {
            var mgr = EnsureManager();
            if (mgr == null || mgr.playerPrefab == null) return false;
            if (Active) { Debug.LogWarning("[NetFlow] Сеть уже запущена."); return true; }
            SetPort(mgr.gameObject, port);
            mgr.StartHost();
            Debug.Log($"[NetFlow] ХОСТ: порт {port}. Друзьям: JOIN <твой-ip>:{port}");
            return true;
        }

        /// <summary>Клиент: подключаемся к хосту.</summary>
        public static bool StartClient(string address, ushort port = 7777)
        {
            var mgr = EnsureManager();
            if (mgr == null) return false;
            if (Active) { Debug.LogWarning("[NetFlow] Сеть уже запущена."); return true; }
            if (string.IsNullOrEmpty(address)) address = "127.0.0.1";
            SetPort(mgr.gameObject, port);
            mgr.networkAddress = address;
            mgr.StartClient();
            Debug.Log($"[NetFlow] КЛИЕНТ: подключение к {address}:{port} ...");
            return true;
        }

        /// <summary>Выделенный сервер (в т.ч. -batchmode -nographics).</summary>
        public static bool StartServerOnly(ushort port = 7777)
        {
            var mgr = EnsureManager();
            if (mgr == null || mgr.playerPrefab == null) return false;
            if (Active) return true;
            SetPort(mgr.gameObject, port);
            mgr.StartServer();
            Debug.Log($"[NetFlow] СЕРВЕР (без игрока): порт {port}");
            return true;
        }

        public static void StopAll()
        {
            if (_manager == null) return;
            if (NetworkClient.active) _manager.StopClient();
            if (NetworkServer.active) _manager.StopServer();
            Debug.Log("[NetFlow] Сеть остановлена.");
        }

        /// <summary>Строка статуса для консоли (NETSTAT).</summary>
        public static string Status()
        {
            if (!Active) return "сеть не запущена";
            string s = NetworkServer.active ? "сервер" : "";
            if (NetworkClient.active) s += (s.Length > 0 ? "+клиент (хост)" : "клиент");
            s += $", онлайн {Online}, адрес {(NetworkClient.active ? _manager.networkAddress : "локально")}";
            return s;
        }
    }
}
#endif
