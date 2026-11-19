"""Música de fondo + efectos sintetizados para el estilo noche neón."""
import numpy as np, wave
SR = 44100
PROGS = [[[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]],   # Am F C G
         [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]],   # Dm Bb F C
         [[52, 55, 59], [48, 52, 55], [55, 59, 62], [50, 54, 57]],   # Em C G D
         [[45, 48, 52], [41, 45, 48], [43, 47, 50], [40, 44, 47]]]   # Am F G E
def note(m): return 440 * 2 ** ((m - 69) / 12)
def bed(path, dur, boundaries=(), accents=(), chimes=(), ticks_until=0.0, seed=0):
    n = int(dur * SR); mus = np.zeros(n); chords = PROGS[seed % len(PROGS)]; cl = 4.0
    for i in range(int(dur / cl) + 1):
        s0 = int(i * cl * SR); s1 = min(n, int((i + 1) * cl * SR) + SR)
        if s0 >= n: break
        seg = np.arange(s1 - s0) / SR
        env = np.minimum(1, seg / 1.2) * np.exp(-np.maximum(0, seg - cl) / 0.8)
        for m in chords[i % 4]:
            f = note(m - 12)
            mus[s0:s1] += env * (0.5 * np.sin(2 * np.pi * f * seg) + 0.18 * np.sin(2 * np.pi * 2 * f * seg + 0.3) + 0.08 * np.sin(2 * np.pi * 3.01 * f * seg))
        mus[s0:s1] += env * 0.6 * np.sin(2 * np.pi * note(chords[i % 4][0] - 24) * seg)
    for k in range(int(dur / 0.5)):
        st = int(k * 0.5 * SR); ch = chords[int(k * 0.5 / cl) % 4]; m = ch[k % 3] + 12
        seg = np.arange(min(int(0.45 * SR), n - st)) / SR
        mus[st:st + len(seg)] += 0.12 * np.exp(-seg * 6) * np.sin(2 * np.pi * note(m) * seg)
    mus *= 0.18 / (np.max(np.abs(mus)) + 1e-9)
    rng = np.random.default_rng(seed + 1); sfx = np.zeros(n)
    for b in boundaries:
        st = int(max(0, b - 0.25) * SR); L = int(0.55 * SR); seg = np.arange(max(0, min(L, n - st))) / SR
        if not len(seg): continue
        nz = np.convolve(rng.standard_normal(len(seg)), np.ones(8) / 8, "same")
        sfx[st:st + len(seg)] += 0.10 * np.sin(np.pi * seg / 0.55) ** 2 * nz
    for k in range(int(ticks_until / 0.5)):
        st = int(k * 0.5 * SR); L = int(0.03 * SR); seg = np.arange(L) / SR
        sfx[st:st + L] += 0.05 * np.exp(-seg * 200) * np.sin(2 * np.pi * (2200 if k % 2 else 1800) * seg)
    for a in accents:
        st = int(a * SR); L = min(int(0.6 * SR), n - st); seg = np.arange(max(0, L)) / SR
        sfx[st:st + len(seg)] += 0.05 * np.exp(-seg * 18) * np.sin(2 * np.pi * (note(84) - 200 * seg) * seg)
    for a in chimes:
        st = int(a * SR); L = min(int(0.6 * SR), n - st); seg = np.arange(max(0, L)) / SR
        for f in (note(76), note(79), note(83)): sfx[st:st + len(seg)] += 0.06 * np.exp(-seg * 3) * np.sin(2 * np.pi * f * seg)
    mix = np.clip(mus + sfx, -1, 1); st = np.stack([mix, mix], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
