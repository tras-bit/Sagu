#!/usr/bin/env node
/**
 * SUBSISTENCE — сервер опросника v3.
 * Отдаёт site/questions3.html и собирает ответы в answers/ (latest.json + архив по времени).
 * Запуск: node tools/answers_server.mjs [порт]   (по умолчанию 3000)
 * Зависимостей нет — только стандартные модули Node.
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PORT = Number(process.argv[2] || process.env.PORT || 3000);
const ANSWERS_DIR = path.join(ROOT, "answers");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".fbx": "application/octet-stream",
};

function sendFile(res, filePath) {
  const safe = path.resolve(filePath);
  if (!safe.startsWith(ROOT)) { res.writeHead(403); res.end("forbidden"); return; }
  fs.readFile(safe, (err, data) => {
    if (err) { res.writeHead(404); res.end("not found"); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(safe).toLowerCase()] || "application/octet-stream" });
    res.end(data);
  });
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on("data", (c) => {
      size += c.length;
      if (size > 5 * 1024 * 1024) { reject(new Error("too large")); req.destroy(); return; }
      chunks.push(c);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const p = url.pathname;

  if (req.method === "GET" && (p === "/" || p === "/index.html" || p.startsWith("/questions"))) {
    return sendFile(res, path.join(ROOT, "site", "questions3.html"));
  }
  if (req.method === "GET" && (p === "/api/answers" || p === "/api/answers/latest")) {
    const latest = path.join(ANSWERS_DIR, "latest.json");
    if (fs.existsSync(latest)) return sendFile(res, latest);
    res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
    return res.end(JSON.stringify({ answers: null, note: "ответов пока нет" }));
  }
  if (req.method === "POST" && p === "/api/answers") {
    try {
      const body = JSON.parse(await readBody(req));
      fs.mkdirSync(ANSWERS_DIR, { recursive: true });
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      const file = `answers_${ts}.json`;
      fs.writeFileSync(path.join(ANSWERS_DIR, file), JSON.stringify(body, null, 2));
      fs.writeFileSync(path.join(ANSWERS_DIR, "latest.json"), JSON.stringify(body, null, 2));
      console.log(`[answers] сохранено ${body.answered}/${body.total} ответов -> answers/${file}`);
      res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
      return res.end(JSON.stringify({ ok: true, file }));
    } catch (e) {
      res.writeHead(400, { "Content-Type": "application/json; charset=utf-8" });
      return res.end(JSON.stringify({ ok: false, error: String(e) }));
    }
  }
  // статика: /site/*, /docs/*, /tools/*, /extras/*
  if (req.method === "GET") {
    const rel = decodeURIComponent(p.replace(/^\/+/, ""));
    if (rel && !rel.includes("..")) return sendFile(res, path.join(ROOT, rel));
  }
  res.writeHead(404); res.end("not found");
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`[subsistence] опросник v3: http://0.0.0.0:${PORT}/`);
  console.log(`[subsistence] ответы будут падать в ${ANSWERS_DIR}/`);
});
