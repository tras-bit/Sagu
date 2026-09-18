#!/usr/bin/env python3
"""
make_wav_sfx.py — синтез .wav-сэмплов (ANSWERS_V3 37в + 39а).

37в (фон сэмплами):  hum_lamp (L0), hum_transformer (L3), water_pool (L37) — зацикленные.
39а (выстрелы):      по стволу из нашей девятки: ak / m4 / mp5 / pump / m249 / bolt / rocket.
Плюс explosion.wav — граната Ф-1, С4, попадание РПГ.

Все звуки собираются слоями (транзиент + тело + низ + хвост-реверб + механика),
финал — мягкая сатурация и нормализация. 44100 Гц, 16 бит, моно.
Кладётся в Assets/Subsistence/Resources/audio/ — ProcAudio.Get подхватит .wav
раньше процедурной версии (см. патч ProcAudio.cs).

Запуск:  python3 tools/make_wav_sfx.py [--check]
"""
import os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "Assets", "Subsistence", "Resources", "audio")
SR = 44100
RNG = np.random.default_rng(20260918)

def t(dur):  return np.arange(int(SR * dur)) / SR

def env_exp(n, tau):
    """Экспоненциальное затухание (tau в секундах)."""
    return np.exp(-np.arange(n) / (tau * SR))

def noise(n):  return RNG.standard_normal(n)

def sine(f, n, phase=0.0):  return np.sin(2 * np.pi * f * np.arange(n) / SR + phase)

def fftfilt(x, lo=None, hi=None, roll=0.15):
    """Полосовой фильтр через rfft-маску с плавными краями (roll — октавы)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo: m *= 1 / (1 + (lo / np.maximum(f, 1e-9)) ** (2 / max(roll, .01)))
    if hi: m *= 1 / (1 + (np.maximum(f, 1e-9) / hi) ** (2 / max(roll, .01)))
    return np.fft.irfft(X * m, len(x))

def fftconv(x, ir):
    n = len(x) + len(ir) - 1
    n2 = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, n2) * np.fft.rfft(ir, n2), n2)[:len(x)]

def reverb(x, dur=0.8, tone=2500.0, decay=3.0):
    """Ранние отражения + хвост: свёртка с затухающим шумовым IR."""
    n = int(SR * dur)
    ir = noise(n) * env_exp(n, dur / decay)
    ir = fftfilt(ir, hi=tone)
    ir[0] = 0
    wet = fftconv(x, ir) * 0.5
    out = np.zeros(max(len(x), len(wet)))
    out[:len(x)] += x
    out[:len(wet)] += wet
    return out

def soft_clip(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)

def norm(x, peak=0.94):
    m = np.max(np.abs(x)) or 1.0
    return x * (peak / m)

def place(buf, sig, at):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf): buf[i:j] += sig[:j - i]

def click(dur=0.012, hi=6000, lo=800, gain=1.0):
    n = int(SR * dur)
    return fftfilt(noise(n), lo=lo, hi=hi) * env_exp(n, dur / 3) * gain

def thump(f0=90, f1=55, dur=0.25, gain=1.0):
    n = int(SR * dur)
    fr = np.linspace(f0, f1, n)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    return np.sin(ph) * env_exp(n, dur / 4) * gain

def body(dur, hi=3000, lo=150, tau=None, gain=1.0):
    n = int(SR * dur)
    return fftfilt(noise(n), lo=lo, hi=hi) * env_exp(n, tau or dur / 3.2) * gain

def mech(freqs=(1900, 2600), dur=0.045, gain=0.5):
    """Металлический клёк: сумма расстроенных синусов с быстрым затуханием."""
    n = int(SR * dur)
    s = np.zeros(n)
    for f in freqs:
        s += sine(f * (1 + RNG.uniform(-0.02, 0.02)), n)
    return s / len(freqs) * env_exp(n, dur / 3.5) * gain

# ------------------------------------------------------------------ выстрелы
def shot(kind):
    if kind == "ak":            # 7.62 — злой, с низом и эхом подсобки
        d = 0.55; base = (body(0.30, hi=2800, lo=120) * 1.0, thump(95, 50, 0.30) * 1.1)
        extras = [(0.16, mech((1700, 2300), 0.05, 0.4))]   # затвор
        rv = (0.5, 2200, 3.2); click0 = (0.003, 9000, 1.2)
    elif kind == "m4":          # 5.56 — сухой, звонкий, короткий
        d = 0.40; base = (body(0.20, hi=5200, lo=220) * 0.9, thump(120, 70, 0.16) * 0.7)
        extras = []; rv = (0.35, 3200, 3.5); click0 = (0.002, 11000, 1.3)
    elif kind == "mp5":         # 9 мм — компактный щелчок
        d = 0.30; base = (body(0.12, hi=3800, lo=300) * 0.8, thump(150, 95, 0.10) * 0.55)
        extras = []; rv = (0.22, 3000, 3.0); click0 = (0.002, 8000, 0.9)
    elif kind == "pump":        # 12 калибр — бум + перезарядка помпой
        d = 0.95; base = (body(0.45, hi=1900, lo=90) * 1.15, thump(75, 40, 0.45) * 1.3)
        extras = [(0.30, mech((900, 1400), 0.05, 0.5)),      # цевьё назад
                  (0.42, mech((1100, 1700), 0.06, 0.6))]     # цевьё вперёд
        rv = (0.7, 1800, 3.0); click0 = (0.003, 7000, 1.1)
    elif kind == "m249":        # 5.56 с ленты — как m4, но жирнее + лента
        d = 0.50; base = (body(0.24, hi=4200, lo=150) * 1.05, thump(105, 60, 0.20) * 0.95)
        extras = [(at, mech((2400, 3100), 0.03, 0.22)) for at in (0.05, 0.09, 0.13)]  # лента
        rv = (0.45, 2600, 3.2); click0 = (0.002, 10000, 1.2)
    elif kind == "bolt":        # болтовка — резкий крэк + длинный хвост
        d = 1.35; base = (body(0.16, hi=6500, lo=180) * 1.2, thump(85, 45, 0.30) * 1.15)
        extras = [(0.45, mech((1300, 2000), 0.07, 0.55)),    # рукоять вверх
                  (0.58, mech((1500, 2300), 0.07, 0.65))]    # рукоять вниз
        rv = (1.3, 2400, 2.6); click0 = (0.002, 12000, 1.5)
    elif kind == "rocket":      # пуск — шум-свелл + кольцо трубы
        d = 1.3
        n = int(SR * d)
        x = np.zeros(n)
        x += fftfilt(noise(n), lo=250, hi=900) * np.minimum(1, t(d) * 9) * env_exp(n, 0.5) * 0.9
        place(x, thump(60, 35, 0.5, 1.4), 0)                # отдача в лицо
        place(x, mech((380, 520), 0.5, 0.5), 0)             # кольцо трубы
        x += fftfilt(noise(n), hi=1800) * env_exp(n, 0.9) * 0.25   # шипение
        return norm(soft_clip(x, 2.2))
    n = int(SR * d)
    x = np.zeros(n)
    for b in base: place(x, b, 0)
    c = click(click0[0], hi=click0[1], gain=click0[2])
    x[:len(c)] += c
    x = reverb(x, rv[0], rv[1], rv[2])
    for at, sig in extras: place(x, sig, at)
    return norm(soft_clip(x, 2.2))

def explosion():               # Ф-1 / С4 / попадание РПГ
    n = int(SR * 2.6)
    x = np.zeros(n)
    place(x, thump(70, 30, 1.6, 1.6), 0)                    # саб-бум
    place(x, body(0.9, hi=1400, lo=60) * 1.3, 0)            # тело
    for _ in range(9):                                      # осколки/щебень
        at = RNG.uniform(0.05, 0.8)
        place(x, mech((RNG.uniform(1500, 4000),), 0.04, RNG.uniform(0.1, 0.3)), at)
    x = reverb(x, 1.5, 1300, 2.8)
    x = soft_clip(x, 2.6)
    return norm(x)

# ------------------------------------------------------------------ фоны (лупы)
def hum_lamp(dur=4.0):
    """L0: гудение ламп 100 Гц + гармоники + лёгкое мерцание. Луп периодический."""
    n = int(SR * dur)
    x = np.zeros(n)
    for f, g in ((100, .55), (200, .28), (300, .16), (400, .07)):
        x += sine(f, n) * g
    flick = 0.9 + 0.1 * np.sin(2 * np.pi * 0.75 * np.arange(n) / SR + 1.1)   # мерцание — периодичное
    x *= flick
    x += fftfilt(noise(n), hi=350) * 0.02                   # шум сеть/дроссель
    return norm(x, 0.72)

def hum_transformer(dur=6.0):
    """L3: трансформатор 50 Гц + жужжание 150 Гц + редкие потрескивания."""
    n = int(SR * dur)
    x = np.zeros(n)
    for f, g in ((50, .6), (100, .18), (150, .34), (250, .12)):
        x += sine(f, n) * g
    buzz = 0.85 + 0.15 * np.sign(np.sin(2 * np.pi * 100 * np.arange(n) / SR))  # прямоугольная жужжалка
    x = x * 0.75 + x * buzz * 0.25
    for _ in range(7):                                      # треск изоляции
        at = RNG.uniform(0.2, dur - 0.3)
        place(x, click(0.01, hi=5500, lo=1200, gain=RNG.uniform(.12, .3)), at)
    x += fftfilt(noise(n), hi=300) * 0.025
    return norm(x, 0.78)

def water_pool(dur=8.0):
    """L37: плеск воды (бэнд-шумовые свеллы) + редкие капли. Луп с кроссфейдом."""
    n = int(SR * dur)
    x = fftfilt(noise(n), lo=350, hi=1300)
    sw = np.zeros(n)
    for f in (0.22, 0.6, 1.1, 0.38, 0.85):                  # наложенные волны-свеллы
        sw += 0.5 * (1 + np.sin(2 * np.pi * f * np.arange(n) / SR + RNG.uniform(0, 6))) ** 2
    x *= sw / sw.max() * 0.55
    x += fftfilt(noise(n), hi=240) * 0.10                   # гул зала сквозь воду
    for at in (1.3, 4.05, 6.7):                             # капли: свист вниз + бульк
        d = np.zeros(int(SR * .18))
        fr = np.linspace(1400, 350, len(d))
        d = np.sin(2 * np.pi * np.cumsum(fr) / SR) * env_exp(len(d), .05)
        place(x, d * 0.35, at)
        place(x, fftfilt(noise(len(d)), lo=500, hi=1500) * env_exp(len(d), .04) * .3, at + .06)
    cf = int(SR * 0.8)                                      # бесшовный луп: кроссфейд
    fade = np.linspace(0, 1, cf)
    x[:cf] = x[:cf] * fade + x[-cf:] * (1 - fade)
    x = x[:-cf]
    return norm(x, 0.66)

# ------------------------------------------------------------------ запись
def write(name, data):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + ".wav")
    d16 = np.clip(data, -1, 1)
    pcm = (d16 * 32767).astype("<i2")
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return p

CLIPS = {
    "hum_lamp":        lambda: hum_lamp(),
    "hum_transformer": lambda: hum_transformer(),
    "water_pool":      lambda: water_pool(),
    "shot_rifle_ak":   lambda: shot("ak"),
    "shot_rifle_m4":   lambda: shot("m4"),
    "shot_smg_mp5":    lambda: shot("mp5"),
    "shot_shotgun_pump": lambda: shot("pump"),
    "shot_lmg_m249":   lambda: shot("m249"),
    "shot_rifle_bolt": lambda: shot("bolt"),
    "shot_rocket_launcher": lambda: shot("rocket"),
    "explosion":       lambda: explosion(),
}

if __name__ == "__main__":
    check = "--check" in sys.argv
    for name, fn in CLIPS.items():
        data = fn()
        if not check:
            p = write(name, data)
            dur = len(data) / SR
            print(f"[wav] {name:24s} {dur:5.2f} c  {os.path.getsize(p)//1024:4d} КБ")
        else:
            print(f"[wav] {name:24s} {len(data)/SR:5.2f} с (check)")
    print(f"[wav] всего {len(CLIPS)} клипов → {OUT}")
