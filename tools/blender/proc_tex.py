#!/usr/bin/env python3
"""SUBSISTENCE — процедурные текстуры для перезапекания (волна RETEX 1.2.0).

Проблема: генераторы моделей красят всё ПЛОСКИМИ цветами + мелкий шум —
запечённые альбедо получаются «жёлтым месивом» без деталей.

Решение: детерминированные тайлящиеся текстуры по имени материала:
дерево (волокна/плашки/сучки), шлифованный металл, бетон, обои (полосы+ракош),
плитка со швами, ковёр, натяжной потолок, ткань (плетение), ржавчина, медь,
глянец, резина, бумага, песчаник + органическая «крапчатость» для кожи монстров.
Все текстуры тайлящиеся (решётчатый шум с периодом), 1024×1024, кэш в /tmp/proc_tex.

Использование: import proc_tex; path = proc_tex.texture_for("M_BPWood", (0.45,0.30,0.16))
"""
import hashlib
import os

import numpy as np
from PIL import Image

CACHE = "/tmp/proc_tex"
SIZE = 1024


def _seed(name):
    return int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16)


def _lattice(period, seed):
    return np.random.default_rng(seed % (2**32)).random((period, period))


def _vnoise(size, period, seed):
    """Тайлящийся value-noise: билинейная интерполяция решётки period×period."""
    tbl = _lattice(period, seed)
    xs = np.linspace(0, period, size, endpoint=False)
    x0 = np.floor(xs).astype(int) % period
    x1 = (x0 + 1) % period
    fx = xs - np.floor(xs)
    ys = np.linspace(0, period, size, endpoint=False)
    y0 = np.floor(ys).astype(int) % period
    y1 = (y0 + 1) % period
    fy = ys - np.floor(ys)
    sx = fx * fx * (3 - 2 * fx)
    sy = fy * fy * (3 - 2 * fy)
    top = tbl[np.ix_(y0, x0)] * (1 - sx)[None, :] + tbl[np.ix_(y0, x1)] * sx[None, :]
    bot = tbl[np.ix_(y1, x0)] * (1 - sx)[None, :] + tbl[np.ix_(y1, x1)] * sx[None, :]
    return top * (1 - sy)[:, None] + bot * sy[:, None]


def _fbm(size, seed, octaves=5, base_period=4, gain=0.55):
    out = np.zeros((size, size))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out += amp * _vnoise(size, max(2, base_period * (2 ** o)), seed + o * 7919)
        tot += amp
        amp *= gain
    return out / tot


def _streaks(size, seed, along_x=0.7):
    """Шлифовка: усреднить шум по оси → вытянутые полосы."""
    h = _vnoise(size, 96, seed).mean(axis=0)[None, :]
    v = _vnoise(size, 96, seed + 1).mean(axis=1)[:, None]
    return h * along_x + v * (1 - along_x)


def _grunge(size, seed, power=2.0, amount=0.25):
    """Крупные грязевые пятна."""
    return (_fbm(size, seed, 4, 3) ** power) * amount


def _clip01(a):
    return np.clip(a, 0.0, 1.0)


# ------------------------------------------------------------------ текстуры

def tex_wood(size, seed, base, planks=7):
    f = _fbm(size, seed, 5, 4)
    xs = np.linspace(0, 1, size)[None, :]
    grain = 0.5 + 0.5 * np.sin((xs * planks * 5.5 + f * 2.4) * np.pi * 2)
    grain = grain ** 1.7
    fine = _vnoise(size, 110, seed + 3)
    grain = _clip01(grain * 0.72 + fine * 0.34)

    ph = size // planks
    py = np.minimum(np.arange(size) // ph, planks - 1)
    rng = np.random.default_rng(seed + 5)
    tint = (0.9 + rng.random(planks) * 0.2)[py][:, None]
    seam = (((np.arange(size) % ph) < 2) | ((np.arange(size) % ph) > ph - 3)).astype(float)[:, None]

    yy, xx = np.mgrid[0:size, 0:size]
    knots = np.zeros((size, size))
    for cx, cy in zip(rng.integers(40, size - 40, 3), rng.integers(40, size - 40, 3)):
        r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        knots += (np.sin(r * 0.5 + f * 3) ** 2) * _clip01(1 - r / 30.0)
    knots = _clip01(knots)

    shade = (1 - grain * 0.30 - seam * 0.42 - knots * 0.22) * tint
    shade *= 1 - _grunge(size, seed + 7, 2, 0.10)
    return _clip01(base[None, None, :] * shade[..., None])


def tex_steel(size, seed, base):
    brushed = _streaks(size, seed)
    shade = 0.66 + brushed * 0.52
    shade *= 1 - _grunge(size, seed + 2, 2.0, 0.30)
    # панельные швы (кессоны)
    yy, xx = np.mgrid[0:size, 0:size]
    seams = ((xx % 256) < 2).astype(float) * 0.12 + ((yy % 256) < 2).astype(float) * 0.12
    shade = np.clip(shade - seams, 0.2, 1.4)
    rng = np.random.default_rng(seed + 9)
    scratch = np.zeros((size, size))
    for _ in range(26):
        y0 = rng.integers(0, size)
        x0, x1 = np.sort(rng.integers(0, size, 2))
        w = rng.integers(1, 2)
        scratch[y0:y0 + w, x0:x1] += rng.random() * 0.35
    shade = shade * (1 + _clip01(scratch) * 0.5)
    return _clip01(base[None, None, :] * shade[..., None])


def tex_concrete(size, seed, base):
    m = _fbm(size, seed, 6, 4)
    speck = _vnoise(size, 220, seed + 1)
    dots = (speck > 0.82) * 0.14 + (speck < 0.1) * 0.10
    stains = _fbm(size, seed + 2, 4, 2) ** 1.8
    shade = 0.62 + m * 0.52
    shade *= 1 - stains * 0.24
    shade -= dots
    return _clip01(base[None, None, :] * shade[..., None])


def tex_wallpaper(size, seed, base):
    xs = np.linspace(0, 1, size)[None, :]
    ys = np.linspace(0, 1, size)[:, None]
    stripes = 0.5 + 0.5 * np.sin(xs * np.pi * 2 * 14)
    stripes = stripes ** 0.6
    motif = ((np.add.outer(np.arange(size) % 72 < 5, np.arange(size) % 72 < 5)) > 0)
    motif = motif.astype(float) * 0.16
    paper = _vnoise(size, 160, seed + 4) * 0.10
    damp = (ys ** 1.6) * 0.22
    shade = (0.94 + stripes * 0.10 - motif - damp) * (1 - paper * 0.5)
    shade *= 1 - _grunge(size, seed + 6, 2.4, 0.14)
    return _clip01(base[None, None, :] * shade[..., None])


def tex_tile(size, seed, base, n=8):
    xs = np.linspace(0, 1, size)
    gx = (xs * n) % 1.0
    grout_x = ((gx < 0.045) | (gx > 0.955)).astype(float)
    gxx = np.floor(xs * n).astype(int)
    grout = np.maximum(grout_x[None, :], grout_x[:, None])
    tile_id = gxx[:, None] + gxx[None, :] * 31 + (np.floor(xs * n)[None, :].astype(int) * 17)
    rng = np.random.default_rng(seed + 21)
    tint = 0.92 + (rng.random((n, n)) * 0.14)
    idx = np.minimum(np.floor(xs * n).astype(int), n - 1)
    tint_full = tint[idx[:, None], idx[None, :]]
    dirt = _fbm(size, seed + 8, 4, 3) * 0.14
    shade = (tint_full - grout * 0.30 - dirt + _vnoise(size, 140, seed + 2) * 0.05)
    return _clip01(base[None, None, :] * shade[..., None])


def tex_carpet(size, seed, base):
    fine = _vnoise(size, 256, seed)
    fiber = _streaks(size, seed + 1, 0.6)
    patches = _fbm(size, seed + 2, 4, 3) * 0.16
    shade = 0.80 + fine * 0.30 + fiber * 0.10 - patches
    return _clip01(base[None, None, :] * shade[..., None])


def tex_ceiling(size, seed, base):
    xs = np.linspace(0, 1, size)
    g = ((xs * 4) % 1.0 < 0.04).astype(float)
    grid = np.maximum(g[None, :], g[:, None]) * 0.34
    speck = (_vnoise(size, 200, seed + 1) > 0.78) * 0.10
    shade = (0.97 - grid - speck) * (1 - _fbm(size, seed + 3, 3, 3) * 0.08)
    return _clip01(base[None, None, :] * shade[..., None])


def tex_fabric(size, seed, base):
    yy, xx = np.mgrid[0:size, 0:size]
    weave = ((xx // 4 + yy // 4) % 2) * 0.10
    fuzz = _vnoise(size, 180, seed + 2) * 0.16
    worn = _fbm(size, seed + 5, 4, 3) ** 1.6 * 0.18
    shade = 0.92 + weave + fuzz * 0.5 - worn
    return _clip01(base[None, None, :] * shade[..., None])


def tex_rust(size, seed, base):
    blotch = _fbm(size, seed, 5, 4)
    orange = np.array([0.55, 0.28, 0.12])
    dark = np.array([0.22, 0.12, 0.08])
    col = dark[None, None, :] * (1 - blotch[..., None]) + orange[None, None, :] * blotch[..., None]
    pits = (_vnoise(size, 190, seed + 3) < 0.08) * 0.25
    col *= 1 - pits[..., None]
    return _clip01(col * (base[None, None, :] * 1.6 + 0.4))


def tex_copper(size, seed, base):
    patina = _fbm(size, seed, 5, 3) ** 1.7
    green = np.array([0.35, 0.55, 0.42])
    col = base[None, None, :] * (1 - patina[..., None] * 0.7) + green[None, None, :] * patina[..., None] * 0.7
    col *= 1 - _grunge(size, seed + 4, 2, 0.15)[..., None]
    return _clip01(col)


def tex_hazard(size, seed, base):
    yy, xx = np.mgrid[0:size, 0:size]
    d = ((xx + yy) / 72.0) % 1.0 < 0.5
    black = np.array([0.10, 0.10, 0.10])
    col = np.where(d[..., None], black[None, None, :], base[None, None, :])
    wear = _fbm(size, seed + 2, 4, 4) ** 1.5
    col *= 1 - wear[..., None] * 0.35
    return _clip01(col)


def tex_stone(size, seed, base):
    xs = np.linspace(0, 1, size)
    rows = 5
    row_h = size // rows
    yy = np.minimum(np.arange(size) // row_h, rows - 1)
    offset = (yy % 2) * 0.5
    gx = (xs[None, :] + offset[:, None]) % 0.5
    seam = ((gx < 0.03) | (gx > 0.97)).astype(float)
    hseam = ((np.arange(size) % row_h) < 2).astype(float)[:, None]
    seams = np.maximum(seam, hseam)
    rng = np.random.default_rng(seed + 31)
    tint = 0.88 + rng.random((rows, 4)) * 0.2
    col_id = np.floor((xs[None, :] + offset[:, None]) * 8).astype(int) % 4
    tint_full = tint[yy, col_id]
    m = _fbm(size, seed, 5, 4)
    shade = tint_full * (0.78 + m * 0.34) - seams * 0.35
    return _clip01(base[None, None, :] * shade[..., None])


def tex_mottle(size, seed, base):
    """Органика/универсальный фолбэк: крапчатая кожа вместо плоского цвета."""
    m = _fbm(size, seed, 5, 4)
    blotch = _fbm(size, seed + 1, 4, 2) ** 1.5
    fine = _vnoise(size, 170, seed + 2) * 0.10
    shade = (0.76 + m * 0.38 - blotch * 0.24 - fine)
    return _clip01(base[None, None, :] * shade[..., None])


def tex_rubber(size, seed, base):
    fine = _vnoise(size, 200, seed)
    scuff = _streaks(size, seed + 1, 0.8)
    shade = 0.86 + fine * 0.18 + scuff * 0.10
    return _clip01(base[None, None, :] * shade[..., None])


def tex_paper(size, seed, base):
    fiber = _streaks(size, seed, 0.5)
    speck = (_vnoise(size, 240, seed + 2) > 0.9) * 0.08
    shade = 0.94 + fiber * 0.08 - speck
    return _clip01(base[None, None, :] * shade[..., None])


# ------------------------------------------------------------------ маршрутизация

def _kind(name):
    n = name.lower()
    if "wallpaper" in n: return "wallpaper"
    if "carpet" in n: return "carpet"
    if "ceiling" in n: return "ceiling"
    if "tile" in n: return "tile"
    if "wood" in n or "plank" in n or "lumber" in n: return "wood"
    if "hazard" in n: return "hazard"
    if "copper" in n: return "copper"
    if "rust" in n: return "rust"
    if "chrome" in n or "polish" in n: return "steel"
    if "steel" in n or "metal" in n or "hqm" in n or "iron" in n or "alumin" in n: return "steel"
    if "stone" in n: return "stone"
    if "concrete" in n or "cement" in n or "asphalt" in n: return "concrete"
    if "rubber" in n or "tire" in n: return "rubber"
    if "canvas" in n or "cloth" in n or "fabric" in n or "strap" in n or "webbing" in n or "denim" in n or "wool" in n: return "fabric"
    if "paper" in n or "tag" in n: return "paper"
    if "skin" in n or "flesh" in n or "weed" in n or "mass" in n or "cloak" in n or "bone" in n or "teeth" in n or "maw" in n or "core" in n: return "mottle"
    return "mottle"


_TEX = {
    "wood": tex_wood, "steel": tex_steel, "concrete": tex_concrete, "wallpaper": tex_wallpaper,
    "tile": tex_tile, "carpet": tex_carpet, "ceiling": tex_ceiling, "fabric": tex_fabric,
    "rust": tex_rust, "copper": tex_copper, "hazard": tex_hazard, "stone": tex_stone,
    "mottle": tex_mottle, "rubber": tex_rubber, "paper": tex_paper,
}

_METAL_NAMES = ("steel", "metal", "hqm", "chrome", "copper", "iron", "alumin", "brass")


def is_metallic(name):
    n = name.lower()
    return any(k in n for k in _METAL_NAMES)


def is_emissive(name, strength_hint=0.0):
    n = name.lower()
    return strength_hint > 0.01 or any(k in n for k in ("lamp", "glow", "emissive", "reactor", "visor", "eye", "arc", "screen"))


def texture_for(name, base_rgb, size=SIZE):
    """Детерминированная текстура по имени материала и его базовому цвету → путь к PNG."""
    key = f"{name}_{int(base_rgb[0]*255):02x}{int(base_rgb[1]*255):02x}{int(base_rgb[2]*255):02x}_{size}"
    path = os.path.join(CACHE, key + ".png")
    if os.path.exists(path):
        return path
    os.makedirs(CACHE, exist_ok=True)
    seed = _seed(key)
    base = np.array([max(0.02, min(1.0, c)) for c in base_rgb[:3]])
    tex = _TEX[_kind(name)](size, seed, base)
    img = Image.fromarray((tex * 255).astype(np.uint8), "RGB")
    img.save(path, "PNG")
    return path
