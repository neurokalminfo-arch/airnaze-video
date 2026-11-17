#!/usr/bin/env python3
"""AirNaze v2 — "Kinetic + collage" renderer (1080x1920, 30 fps).

Usage: python3 render_v2.py spec.json out.mp4 [--frames]
  --frames  -> solo fotogramas de prueba + hoja de contacto (work/contact.jpg)

Lenguaje visual: papel recortado y rasgado, cinta adhesiva, tramas de semitono,
impresión risográfica desalineada, garabatos a mano que "hierven" (12 fps),
tipografía gigante que entra a golpes al ritmo, cortes en el beat, subtítulos
karaoke. Cada escena cambia de papel/color.

Tipos de escena (type):
  slam     big, accent[], kicker            gancho: palabras a golpes que llenan la pantalla
  stat     value, label                     cifra gigante que cuenta + garabato
  cutout   word, sub                        palabra en letras recortadas (nota de rescate)
  triple   items[{word, icon}] (2-3)        lista a golpes en tiras de papel
  step     n, title, sub, icon              paso numerado (número contorno + tira + sticker)
  split    left, lsub, right, rsub          pantalla partida rasgada: mal (X) vs bien (✓)
  breath   big                              discos de papel que respiran (ciclo 5 s)
  product  img (assets/product/), tag, items   polaroid con cinta (o sticker si no hay foto)
  close    big, small                       bocadillo de papel + sello AirNaze + flecha a comentarios
Compatibilidad v1: hook->slam, tip->step, versus->split, brand->close.
Opcional por escena: "theme": blue|cream|navy|mint.
icons: drop, moon, bed, wind, window, clock, run, leaf, phone, sun, nose, check
"""
import json, math, os, random, subprocess, sys, wave
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VOICE = os.path.join(HERE, "voices", "es_ES-davefx-medium.onnx")
FONTDIR = os.path.join(ROOT, "assets", "fonts")
PRODUCT_DIR = os.path.join(ROOT, "assets", "product")
BPM = 112; BEAT = 60 / BPM; HALF = BEAT / 2

# ---------- palette ----------
CREAM = (243, 236, 222); COBALT = (30, 76, 235); NAVY = (11, 22, 58); MINT = (112, 240, 208)
CORAL = (255, 104, 84); WHITE = (255, 255, 255); SKY = (130, 196, 255); INK = (14, 18, 36)
THEMES = {
    "blue":  dict(bg=COBALT, ink=CREAM, acc=MINT, acc2=CORAL, scrap=CREAM, scrap_ink=COBALT, half=NAVY),
    "cream": dict(bg=CREAM, ink=COBALT, acc=CORAL, acc2=COBALT, scrap=COBALT, scrap_ink=CREAM, half=SKY),
    "navy":  dict(bg=NAVY, ink=CREAM, acc=MINT, acc2=CORAL, scrap=MINT, scrap_ink=NAVY, half=COBALT),
    "mint":  dict(bg=MINT, ink=NAVY, acc=COBALT, acc2=CORAL, scrap=NAVY, scrap_ink=MINT, half=WHITE),
}
DEFAULT_THEME = {"slam": "blue", "stat": "cream", "cutout": "navy", "triple": "cream", "step": "cream",
                 "split": "cream", "breath": "blue", "product": "cream", "close": "mint"}
ALIAS = {"hook": "slam", "tip": "step", "versus": "split", "brand": "close"}

FONTS = {"anton": "Anton-Regular.ttf", "archivo": "ArchivoBlack-Regular.ttf", "serif": "DMSerifDisplay-Regular.ttf",
         "serif_i": "DMSerifDisplay-Italic.ttf", "marker": "PermanentMarker-Regular.ttf", "brush": "CaveatBrush-Regular.ttf",
         "mono": "SpaceMono-Bold.ttf", "rubik": "RubikMonoOne-Regular.ttf", "bebas": "BebasNeue-Regular.ttf"}

@lru_cache(maxsize=512)
def font(key, size): return ImageFont.truetype(os.path.join(FONTDIR, FONTS[key]), int(size))

# ---------- easing / time ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(t): t = clamp(t); return 1 - (1 - t) ** 3
def eback(t, s=2.2):
    t = clamp(t); c3 = s + 1
    return 1 + c3 * (t - 1) ** 3 + s * (t - 1) ** 2
def prog(t, start, dur): return clamp((t - start) / max(dur, 1e-6))
def stop(t, fps=12): return math.floor(t * fps) / fps          # stop-motion time
def boil(seed, t, amp=3.0):
    r = random.Random(seed * 7919 + int(t * 12)); return r.uniform(-amp, amp), r.uniform(-amp, amp)

# ---------- paper & textures ----------
_rng = np.random.default_rng(7)
def paper_array(w, h, color, seed=0, strength=1.0):
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3), np.float32) * np.array(color, np.float32)
    small = rng.standard_normal((h // 40 + 2, w // 40 + 2)).astype(np.float32)
    blot = np.array(Image.fromarray(((small * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 - 0.5
    fine = rng.standard_normal((h, w)).astype(np.float32)
    lum = (blot * 14 + fine * 5) * strength
    return np.clip(base + lum[..., None], 0, 255).astype(np.uint8)

@lru_cache(maxsize=16)
def paper_bg(color, seed):
    arr = paper_array(W + 80, H + 80, color, seed)
    im = Image.fromarray(arr, "RGB"); d = ImageDraw.Draw(im, "RGBA"); r = random.Random(seed)
    for _ in range(140):  # fibres
        x, y = r.uniform(0, W + 80), r.uniform(0, H + 80); a = r.uniform(0, 6.28); L = r.uniform(10, 40)
        sh = 255 if sum(color) < 380 else 0
        d.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], fill=(sh, sh, sh, 18), width=1)
    return im

@lru_cache(maxsize=8)
def halftone(color, size=620, step=26):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = size / 2
    for y in range(0, size, step):
        for x in range(0, size, step):
            xx = x + (step / 2 if (y // step) % 2 else 0)
            dist = math.hypot(xx - c, y - c) / c
            r = (1 - dist) * step * 0.48
            if r > 1: d.ellipse([xx - r, y - r, xx + r, y + r], fill=color + (255,))
    return im

GRAIN = [(_rng.standard_normal((H, W)) * 4).astype(np.int16) for _ in range(3)]

def torn_points(w, h, seed, jag=9, step=14):
    r = random.Random(seed); pts = []
    def edge(p0, p1):
        n = max(2, int(math.dist(p0, p1) / step))
        for i in range(n):
            f = i / n; x = p0[0] + (p1[0] - p0[0]) * f; y = p0[1] + (p1[1] - p0[1]) * f
            pts.append((x + r.uniform(-jag, jag) * 0.5, y + r.uniform(-jag, jag) * 0.5))
    m = jag
    edge((m, m), (w - m, m)); edge((w - m, m), (w - m, h - m)); edge((w - m, h - m), (m, h - m)); edge((m, h - m), (m, m))
    return pts

@lru_cache(maxsize=256)
def torn(w, h, color, seed, jag=10, shadow=True, ellipse=False):
    """Recorte de papel rasgado con borde blanco (alma del papel) y sombra."""
    w, h = int(w), int(h); pad = 30
    mask = Image.new("L", (w + 2 * pad, h + 2 * pad), 0); md = ImageDraw.Draw(mask)
    if ellipse:
        r = random.Random(seed); pts = []
        for k in range(90):
            a = k / 90 * 2 * math.pi; j = 1 + r.uniform(-0.012, 0.012)
            pts.append((pad + w / 2 + math.cos(a) * w / 2 * j, pad + h / 2 + math.sin(a) * h / 2 * j))
    else:
        pts = [(x + pad, y + pad) for x, y in torn_points(w, h, seed, jag)]
    md.polygon(pts, fill=255)
    core = mask
    inner = mask.filter(ImageFilter.MinFilter(7))
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    if shadow:
        sh = mask.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.42))
        sl = Image.new("RGBA", mask.size, (0, 0, 0, 255)); sl.putalpha(sh)
        out.alpha_composite(sl, (6, 12))
    white = Image.new("RGBA", mask.size, (250, 247, 240, 255)); white.putalpha(core)
    out.alpha_composite(white)
    tex = Image.fromarray(paper_array(mask.size[0], mask.size[1], color, seed % 97, 0.8), "RGB").convert("RGBA"); tex.putalpha(inner)
    out.alpha_composite(tex)
    return out

@lru_cache(maxsize=64)
def tape(w, h, seed, color=(250, 244, 220, 175)):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = random.Random(seed)
    zz = 10; left = [(r.uniform(0, zz), y) for y in range(0, h + 1, 8)]; right = [(w - r.uniform(0, zz), y) for y in range(h, -1, -8)]
    d.polygon(left + right, fill=color)
    d.line([(14, 6), (w - 14, 6)], fill=(255, 255, 255, 70), width=3)
    return im

# ---------- text ----------
@lru_cache(maxsize=1024)
def text_img(text, key, size, fill, stroke=0, sfill=None, pad=6):
    f = font(key, size); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    b = d.textbbox((0, 0), text, font=f, stroke_width=stroke)
    im = Image.new("RGBA", (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-b[0] + pad, -b[1] + pad), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im

@lru_cache(maxsize=512)
def riso(text, key, size, fill, off_col, off=(9, 7)):
    """Impresión riso desalineada: capa de color desplazada debajo."""
    a = text_img(text, key, size, off_col); b = text_img(text, key, size, fill)
    im = Image.new("RGBA", (b.width + abs(off[0]), b.height + abs(off[1])), (0, 0, 0, 0))
    im.alpha_composite(a, (off[0], off[1])); im.alpha_composite(b, (0, 0))
    return im

def tw(text, key, size): return font(key, size).getlength(text)

def fit(text, key, maxw, start, minimum=40):
    s = start
    while s > minimum and tw(text, key, s) > maxw: s -= 4
    return s

def wrap(text, key, size, maxw):
    lines, cur = [], ""
    for w_ in text.split():
        t = (cur + " " + w_).strip()
        if tw(t, key, size) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def put(img, layer, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if alpha <= 0.01 or layer is None: return
    L = layer
    if rot: L = rot_cached(L, round(rot, 1))
    if scale != 1.0:
        L = L.resize((max(1, int(L.width * scale)), max(1, int(L.height * scale))), Image.BILINEAR)
    if alpha < 0.99:
        L = L.copy(); L.putalpha(L.getchannel("A").point(lambda v: int(v * alpha)))
    comp(img, L, int(cx - L.width / 2), int(cy - L.height / 2))

def comp(img, L, x, y):
    """alpha_composite que admite coordenadas negativas / fuera de cuadro."""
    if x >= img.width or y >= img.height or x + L.width <= 0 or y + L.height <= 0: return
    cx0, cy0 = max(0, -x), max(0, -y)
    if cx0 or cy0: L = L.crop((cx0, cy0, L.width, L.height))
    img.alpha_composite(L, (max(0, x), max(0, y)))

_rotc = {}
def rot_cached(L, angle):
    k = (id(L), angle)
    if k not in _rotc:
        if len(_rotc) > 600: _rotc.clear()
        _rotc[k] = (L.rotate(angle, resample=Image.BICUBIC, expand=True), L)  # keep ref so id stays valid
    return _rotc[k][0]

def label(text, key, size, fg, bg, seed, padx=34, pady=20, jag=8):
    """Texto sobre tira de papel rasgado."""
    t = text_img(text, key, size, fg)
    p = torn(t.width + 2 * padx, t.height + 2 * pady, bg, seed, jag)
    out = p.copy(); out.alpha_composite(t, ((p.width - t.width) // 2, (p.height - t.height) // 2)); return out

_labc = {}
def label_c(*a, **k):
    key = (a, tuple(sorted(k.items())))
    if key not in _labc: _labc[key] = label(*a, **k)
    return _labc[key]

# ---------- doodles (hand-drawn, boiling) ----------
def jit_path(pts, seed, t, amp=2.5):
    r = random.Random(seed * 31 + int(t * 12))
    return [(x + r.uniform(-amp, amp), y + r.uniform(-amp, amp)) for x, y in pts]

def draw_path(img, pts, frac, color, width=10):
    if frac <= 0 or len(pts) < 2: return
    n = max(2, int(len(pts) * clamp(frac))); P = pts[:n]
    d = ImageDraw.Draw(img); d.line(P, fill=color, width=width, joint="curve")
    for x, y in (P[0], P[-1]): d.ellipse([x - width / 2, y - width / 2, x + width / 2, y + width / 2], fill=color)

def scribble_circle(cx, cy, rx, ry, seed):
    r = random.Random(seed); pts = []; a0 = r.uniform(0, 6.28)
    for k in range(70):
        a = a0 + k / 70 * 2.25 * math.pi; rr = 1 + 0.06 * math.sin(k * 0.3) + r.uniform(-0.015, 0.015)
        pts.append((cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr * (1 + 0.04 * k / 70)))
    return pts

def underline(x0, x1, y, seed):
    r = random.Random(seed)
    return [(x0 + (x1 - x0) * k / 30, y + math.sin(k * 0.5) * 6 + r.uniform(-2, 2) + k * 0.3) for k in range(31)]

def arrow(p0, p1, seed, bend=0.25):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2; dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    c = (mx - dy * bend, my + dx * bend); pts = []
    for k in range(31):
        f = k / 30; x = (1 - f) ** 2 * p0[0] + 2 * (1 - f) * f * c[0] + f * f * p1[0]
        y = (1 - f) ** 2 * p0[1] + 2 * (1 - f) * f * c[1] + f * f * p1[1]; pts.append((x, y))
    a = math.atan2(p1[1] - pts[-4][1], p1[0] - pts[-4][0]); L = 46
    head = [(p1[0] - math.cos(a - 0.5) * L, p1[1] - math.sin(a - 0.5) * L), p1, (p1[0] - math.cos(a + 0.5) * L, p1[1] - math.sin(a + 0.5) * L)]
    return pts, head

def xmark(cx, cy, s): return [(cx - s, cy - s), (cx + s, cy + s * 0.9)], [(cx + s * 0.9, cy - s), (cx - s * 0.9, cy + s)]
def checkmark(cx, cy, s): return [(cx - s, cy), (cx - s * 0.6, cy + s * 0.25), (cx - s * 0.2, cy + s * 0.6), (cx + s * 0.4, cy - s * 0.2), (cx + s, cy - s)]

def sparkle(img, cx, cy, s, color, t, seed):
    jx, jy = boil(seed, t, 3); d = ImageDraw.Draw(img)
    for a in range(4):
        ang = a * math.pi / 2 + 0.2
        d.line([(cx + jx + math.cos(ang) * s * 0.35, cy + jy + math.sin(ang) * s * 0.35), (cx + jx + math.cos(ang) * s, cy + jy + math.sin(ang) * s)], fill=color, width=8)

# ---------- icons / stickers ----------
def icon(name, s, color):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w = max(6, s // 12); c = color + (255,)
    if name == "drop":
        d.polygon([(s*.5, s*.08), (s*.22, s*.55), (s*.78, s*.55)], fill=c); d.ellipse([s*.2, s*.36, s*.8, s*.92], fill=c)
    elif name == "moon":
        d.ellipse([s*.12, s*.12, s*.88, s*.88], fill=c); d.ellipse([s*.36, s*.02, s*1.02, s*.7], fill=(0, 0, 0, 0))
    elif name == "bed":
        d.rounded_rectangle([s*.08, s*.5, s*.92, s*.72], 12, fill=c); d.rounded_rectangle([s*.12, s*.36, s*.38, s*.52], 14, fill=c)
        d.rectangle([s*.08, s*.72, s*.14, s*.86], fill=c); d.rectangle([s*.86, s*.72, s*.92, s*.86], fill=c)
    elif name == "wind":
        for i, y in enumerate([.3, .5, .7]):
            L = [.85, .65, .75][i]
            d.line([(s*.1, s*y), (s*(.1 + L*.8), s*y)], fill=c, width=w)
            d.arc([s*(.1 + L*.8) - s*.1, s*y - s*.2, s*(.1 + L*.8) + s*.1, s*y], 270, 90, fill=c, width=w)
    elif name == "window":
        d.rounded_rectangle([s*.12, s*.1, s*.88, s*.9], 16, outline=c, width=w)
        d.line([(s*.5, s*.1), (s*.5, s*.9)], fill=c, width=w); d.line([(s*.12, s*.5), (s*.88, s*.5)], fill=c, width=w)
    elif name == "clock":
        d.ellipse([s*.1, s*.1, s*.9, s*.9], outline=c, width=w)
        d.line([(s*.5, s*.5), (s*.72, s*.5)], fill=c, width=w); d.line([(s*.5, s*.5), (s*.5, s*.28)], fill=c, width=w)
    elif name == "run":
        d.ellipse([s*.55, s*.06, s*.75, s*.26], fill=c)
        for a, b in [((.6, .3), (.45, .6)), ((.45, .6), (.25, .85)), ((.45, .6), (.7, .75)), ((.7, .75), (.65, .95)), ((.55, .38), (.3, .4)), ((.55, .38), (.8, .5))]:
            d.line([(s*a[0], s*a[1]), (s*b[0], s*b[1])], fill=c, width=w + 4)
    elif name == "leaf":
        pts = [(s * (.18 + .64 * k / 20), s * (.82 - .64 * k / 20)) for k in range(21)]
        up = [(x - math.sin(k / 20 * math.pi) * s * .2, y - math.sin(k / 20 * math.pi) * s * .2) for k, (x, y) in enumerate(pts)]
        dn = [(x + math.sin(k / 20 * math.pi) * s * .2, y + math.sin(k / 20 * math.pi) * s * .2) for k, (x, y) in enumerate(pts)]
        d.polygon(up + dn[::-1], fill=c); d.line([(s * .12, s * .88), (s * .7, s * .3)], fill=(0, 0, 0, 0), width=max(3, w // 2))
    elif name == "phone":
        d.rounded_rectangle([s*.28, s*.06, s*.72, s*.94], 26, outline=c, width=w); d.line([(s*.43, s*.84), (s*.57, s*.84)], fill=c, width=w)
    elif name == "sun":
        d.ellipse([s*.3, s*.3, s*.7, s*.7], fill=c)
        for k in range(8):
            a = k * math.pi / 4
            d.line([(s*.5 + math.cos(a)*s*.3, s*.5 + math.sin(a)*s*.3), (s*.5 + math.cos(a)*s*.45, s*.5 + math.sin(a)*s*.45)], fill=c, width=w)
    elif name == "nose":
        d.arc([s*.2, s*.08, s*.8, s*.92], 300, 120, fill=c, width=w)
        d.ellipse([s*.3, s*.62, s*.48, s*.78], outline=c, width=w); d.ellipse([s*.52, s*.62, s*.7, s*.78], outline=c, width=w)
    else:
        d.line([(s*.15, s*.55), (s*.42, s*.8), (s*.88, s*.22)], fill=c, width=w + 4, joint="curve")
    return im

@lru_cache(maxsize=64)
def sticker(name, size, bg, fg, seed):
    pad = 40; s = size; im = Image.new("RGBA", (s + 2 * pad, s + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse([pad - 16, pad - 16, pad + s + 16, pad + s + 16], fill=255)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 255)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * .4)))
    im.alpha_composite(sh, (5, 10))
    wb = Image.new("RGBA", im.size, (255, 255, 255, 255)); wb.putalpha(m); im.alpha_composite(wb)
    ImageDraw.Draw(im).ellipse([pad, pad, pad + s, pad + s], fill=bg + (255,))
    ic = icon(name, int(s * 0.62), fg); im.alpha_composite(ic, (pad + (s - ic.width) // 2, pad + (s - ic.height) // 2))
    return im.rotate(random.Random(seed).uniform(-14, 14), resample=Image.BICUBIC, expand=True)

def ransom(word, seed, size=170, maxw=960):
    """Palabra con letras recortadas de 'revistas' distintas. Devuelve lista de (layer, x_offset, rot)."""
    r = random.Random(seed); keys = ["anton", "archivo", "serif_i", "rubik", "bebas", "serif"]
    cols = [(CREAM, COBALT), (COBALT, CREAM), (MINT, NAVY), (CORAL, WHITE), (WHITE, INK), (NAVY, MINT)]
    while True:
        items = []; x = 0
        for i, ch in enumerate(word):
            if ch == " ": x += size * 0.35; continue
            k = keys[(i + seed) % len(keys)]; bg, fg = cols[r.randrange(len(cols))]
            if bg == CREAM and i == 0: bg, fg = CORAL, WHITE
            sz = size * r.uniform(0.85, 1.12) * (1.15 if k in ("anton", "bebas") else 1)
            t = text_img(ch, k, sz, fg)
            p = torn(t.width + 34, t.height + 30, bg, seed * 50 + i, 7)
            L = p.copy(); L.alpha_composite(t, ((p.width - t.width) // 2, (p.height - t.height) // 2))
            items.append([L, x + (L.width - 60) / 2, r.uniform(-9, 9), r.uniform(-18, 18)]); x += L.width - 60 - 6
        if x <= maxw or size < 70: return items, x
        size *= 0.9

# ---------- background ----------
def draw_bg(theme, seed, t, dur):
    th = THEMES[theme]; bg = paper_bg(th["bg"], seed % 5)
    ox = int(40 + 30 * math.sin(t * 0.35 + seed)); oy = int(40 + 36 * t / max(dur, 1))
    img = bg.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
    ht = halftone(th["half"]); r = random.Random(seed)
    corner = r.choice([(-140, -120), (W - 480, -160), (-180, H - 560), (W - 460, H - 600)])
    comp(img, ht, int(corner[0] + 10 * math.sin(t)), int(corner[1] + 10 * math.cos(t * 0.8)))
    return img

# ---------- scenes ----------
def sc_slam(img, s, t, dur, ctx):
    th = ctx["th"]; raw = s["big"].upper().split(); acc = {a.upper().strip("¿?¡!.,") for a in s.get("accent", [])}
    lines = []
    for w_ in raw:
        if lines and len(lines[-1]) <= 3: lines[-1] += " " + w_
        else: lines.append(w_)
    if "slam_layout" not in ctx:
        styles = []; r = random.Random(ctx["seed"])
        for i, ln in enumerate(lines):
            isacc = any(x.strip("¿?¡!.,") in acc for x in ln.split())
            st = ["solid", "strip", "serif", "outline"][i % 4]
            if isacc: st = "accent"
            key = {"solid": "anton", "strip": "anton", "serif": "serif_i", "outline": "anton", "accent": "anton"}[st]
            txt = ln if st != "serif" else ln.capitalize()
            size = fit(txt, key, 900 if st != "strip" else 820, 330 if key == "anton" else 220, 60)
            if st == "solid": L = riso(txt, key, size, th["ink"], th["acc2"])
            elif st == "serif": L = text_img(txt, key, size, th["acc"])
            elif st == "outline": L = text_img(txt, key, size, th["bg"], 7, th["ink"])
            elif st == "strip": L = label(txt, key, size, th["scrap_ink"], th["scrap"], ctx["seed"] + i, 30, 10)
            else:
                t_ = riso(txt, key, size, th["bg"], INK, (8, 8)); p = torn(t_.width + 50, t_.height + 20, th["acc"], ctx["seed"] + 40 + i, 9)
                L = p.copy(); L.alpha_composite(t_, ((p.width - t_.width) // 2, (p.height - t_.height) // 2))
            styles.append((L, r.uniform(-3.5, 3.5)))
        hs = [L.height for L, _ in styles]; tot = sum(hs) - 30 * (len(hs) - 1)
        sc = min(1.0, 1020 / tot); ctx["slam_layout"] = (styles, hs, sc)
    styles, hs, sc = ctx["slam_layout"]; n = len(styles)
    step_ = min(0.42, 0.72 * ctx["vd"] / n); ctx["slam_times"] = [0.05 + i * step_ for i in range(n)]
    tot = (sum(hs) - 30 * (n - 1)) * sc; y = 820 - tot / 2; top0 = y; shake = 0
    for i, (L, rot) in enumerate(styles):
        ti = ctx["slam_times"][i]; h = hs[i] * sc
        if t >= ti:
            p = prog(t, ti, 0.2); scale = sc * (1 + 0.85 * (1 - eo(p))) * (1 + 0.05 * t / dur)
            put(img, L, W / 2, y + h / 2, scale, rot, clamp(p * 4))
            shake = max(shake, 22 * math.exp(-(t - ti) * 16))
        y += h - 30 * sc
    if s.get("kicker"):
        k = label_c(s["kicker"].upper(), "mono", 40, INK, (250, 244, 220), 3, 26, 12, 5)
        jx, jy = boil(5, t, 2); put(img, k, W / 2 + jx, max(215, top0 - 35) + jy - (1 - eo(prog(t, 0, 0.3))) * 200, 1, -3)
    if t > ctx["slam_times"][-1] + 0.35:
        f = eo(prog(t, ctx["slam_times"][-1] + 0.35, 0.35))
        draw_path(img, jit_path(underline(200, 880, y + 50 * sc, 12), 12, t), f, th["acc2"] + (255,), 12)
        sparkle(img, 120, top0 + 60, 58, th["acc"], t, 2); sparkle(img, 960, y - 40, 46, th["acc2"], t, 6)
    ctx["shake"] = shake

def sc_stat(img, s, t, dur, ctx):
    th = ctx["th"]; val = s["value"]; digits = "".join(c for c in val if c.isdigit())
    p = eo(prog(t, 0.05, min(1.4, dur * 0.45)))
    if digits:
        cur = int(int(digits) * p); shown = f"{cur:,}".replace(",", ".")
        lead = val[:len(val) - len(val.lstrip("+~<>"))]; shown = lead + shown
    else: shown = val
    size = fit(val, "anton", 940, 400, 120)
    put(img, halftone(th["acc"]), W / 2 + 120, 700, 1.05)
    L = riso(shown, "anton", size, th["ink"], th["acc"], (12, 10)); jx, jy = boil(11, t, 2)
    put(img, L, W / 2 + jx, 720 + jy, 1 + 0.15 * (1 - eo(prog(t, 0, 0.25))))
    rx = min(500, tw(val, "anton", size) / 2 + 70)
    draw_path(img, jit_path(scribble_circle(W / 2, 720, rx, size * 0.62, 4), 4, t), eo(prog(t, 0.6, 0.6)), th["acc2"] + (255,), 11)
    lab = label_c(s["label"].upper(), "archivo", fit(s["label"].upper(), "archivo", 760, 70, 36), th["scrap_ink"], th["scrap"], 21)
    q = eback(prog(t, 0.35, 0.4)); put(img, lab, W / 2 + (1 - q) * 900, 1150, 1, -3)
    sparkle(img, 170, 430, 60, th["acc2"], t, 3); sparkle(img, 930, 1010, 44, th["acc"], t, 9)

def sc_cutout(img, s, t, dur, ctx):
    th = ctx["th"]
    if "ransom" not in ctx: ctx["ransom"] = ransom(s["word"].upper(), ctx["seed"] % 50 + 3, 300, 940)
    items, total = ctx["ransom"]; x0 = W / 2 - total / 2 - 30; per = min(0.12, 0.55 * ctx["vd"] / max(1, len(items)))
    for i, (L, xo, rot, yo) in enumerate(items):
        ti = 0.05 + i * per; tt = stop(t)
        if tt < ti: continue
        sc = 1.35 if tt - ti < 1 / 12 else 1.0
        jx, jy = boil(i + 40, t, 2.5); put(img, L, x0 + xo + jx, 700 + yo + jy, sc, rot)
    if s.get("sub"):
        lines = wrap(s["sub"], "marker", 76, 880); y = 1010
        rv = eo(prog(t, 0.45, 0.8))
        for j, ln in enumerate(lines):
            L = text_img(ln, "marker", 76, th["ink"]); cw = int(L.width * clamp(rv * len(lines) - j))
            if cw > 2: put(img, L.crop((0, 0, cw, L.height)), W / 2 - L.width / 2 + cw / 2, y)
            y += 100
        f = eo(prog(t, 0.9, 0.4)); col = th["acc"] + (255,)
        draw_path(img, jit_path(underline(220, 860, y + 10, 6), 6, t), f, col, 10)
        sparkle(img, 140, 470, 56, th["acc"], t, 4); sparkle(img, 950, 930, 44, th["acc2"], t, 8)

def sc_triple(img, s, t, dur, ctx):
    th = ctx["th"]; items = s["items"][:3]; n = len(items)
    per = 0.78 * ctx["vd"] / n; ys = [470, 800, 1130] if n == 3 else [600, 1000]
    bgs = [th["scrap"], th["acc"], INK]; fgs = [th["scrap_ink"], INK if th["acc"] in (MINT, CORAL) else WHITE, th["bg"] if th["bg"] != INK else CREAM]
    for i, it in enumerate(items):
        ti = 0.05 + i * per; p = eback(prog(t, ti, 0.35))
        if t < ti: continue
        side = -1 if i % 2 == 0 else 1; word = it["word"].upper()
        L = label_c(word, "anton", fit(word, "anton", 700, 230, 80), fgs[i % 3], bgs[i % 3], 60 + i, 50, 6, 10)
        x = W / 2 - 40 * side + side * (1 - p) * -1100
        put(img, L, x, ys[i], 1, 2.5 * side)
        num = text_img(f"0{i + 1}", "mono", 44, th["ink"]); put(img, num, x - L.width / 2 + 10, ys[i] - L.height / 2 - 10, 1, 0, clamp(p))
        if it.get("icon"):
            q = prog(stop(t), ti + 0.25, 0.01)
            if q >= 1:
                st = sticker(it["icon"], 150, th["acc2"] if bgs[i % 3] != th["acc2"] else th["acc"], WHITE, i + 3)
                jx, jy = boil(i * 9, t, 3); sx = clamp(x + (L.width / 2 + 10) * (1 if side < 0 else -1), 120, W - 120)
                put(img, st, sx + jx, ys[i] - 95 + jy, 1.3 if stop(t) < ti + 0.34 else 1)
    if t > 0.05 + (n - 1) * per + 0.4:
        y = ys[n - 1] + 150; f = eo(prog(t, 0.05 + (n - 1) * per + 0.4, 0.4))
        draw_path(img, jit_path(underline(260, 840, y, 2), 2, t), f, th["acc2"] + (255,), 10)

def sc_step(img, s, t, dur, ctx):
    th = ctx["th"]; n = s.get("n", 1)
    num = text_img(f"{n:02d}" if isinstance(n, int) else str(n), "anton", 560, th["bg"], 9, th["acc2"])
    p = eo(prog(t, 0, 0.3)); jx, jy = boil(n, t, 2)
    put(img, num, 330 + jx - (1 - p) * 600, 620 + jy, 1, -4)
    if s.get("icon"):
        st = sticker(s["icon"], 230, th["acc"], th["bg"] if th["bg"] != CREAM else COBALT, n + 2)
        if stop(t) >= 0.25: put(img, st, 800 + boil(n + 5, t, 3)[0], 540, 1.25 if stop(t) < 0.34 else 1)
    title = s["title"].upper(); size = fit(title, "anton", 860, 150, 70); lines = wrap(title, "anton", size, 860)
    y = 1010
    for j, ln in enumerate(lines):
        L = label_c(ln, "anton", size, th["scrap_ink"], th["scrap"], 80 + j + n, 34, 4, 9)
        q = eback(prog(t, 0.25 + j * 0.12, 0.35)); put(img, L, W / 2 + (1 - q) * (1000 if j % 2 else -1000), y + L.height / 2, 1, -2 + 3 * j)
        y += L.height - 10
    if s.get("sub"):
        sub = wrap(s["sub"], "marker", 58, 860); rv = eo(prog(t, 0.7, 0.6))
        for j, ln in enumerate(sub):
            L = text_img(ln, "marker", 58, th["ink"]); cw = int(L.width * clamp(rv * len(sub) - j))
            if cw > 2: put(img, L.crop((0, 0, cw, L.height)), W / 2 - L.width / 2 + cw / 2, y + 60 + j * 78)

def sc_split(img, s, t, dur, ctx):
    top, bot = THEMES["cream"], THEMES["blue"]; seed = ctx["seed"]
    if "halves" not in ctx:
        A = draw_bg("cream", seed, 0, dur); B = draw_bg("blue", seed + 1, 0, dur)
        m = Image.new("L", (W, H), 0); r = random.Random(seed); pts = [(0, 0), (W, 0)]
        y = 880
        for x in range(W, -1, -18): pts.append((x, y - 120 * (x / W - 0.5) + r.uniform(-9, 9)))
        ImageDraw.Draw(m).polygon(pts, fill=255)
        edge = m.filter(ImageFilter.MaxFilter(13)); topL = A.copy(); topL.putalpha(m)
        core = Image.new("RGBA", (W, H), (250, 247, 240, 255)); core.putalpha(edge)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 255)); sh.putalpha(edge.filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * .45)))
        ctx["halves"] = (B, topL, core, sh)
    B, topL, core, sh = ctx["halves"]
    p = eo(prog(t, 0, 0.32)); dy = int(-(1 - p) * H * 0.6)
    img.paste(B, (0, int((1 - p) * H * 0.6)))
    comp(img, sh, 0, dy + 14); comp(img, core, 0, dy); comp(img, topL, 0, dy)
    if 0.32 <= t < 0.6: ctx["shake"] = 18 * math.exp(-(t - 0.32) * 12)
    L1 = riso(s["left"].upper(), "anton", fit(s["left"].upper(), "anton", 760, 330, 100), top["ink"], top["acc"])
    put(img, L1, W / 2, 440 + dy, 1, -3)
    put(img, text_img(s["lsub"], "marker", 64, INK), W / 2, 680 + dy, 1, -2)
    L2 = riso(s["right"].upper(), "anton", fit(s["right"].upper(), "anton", 760, 330, 100), bot["ink"], bot["acc"])
    by = int((1 - p) * H * 0.6)
    put(img, L2, W / 2, 1130 + by, 1, 2)
    put(img, text_img(s["rsub"], "marker", 64, MINT), W / 2, 1340 + by, 1, 1)
    a, b = xmark(W / 2, 440, 230); f = eo(prog(t, 0.55, 0.35))
    draw_path(img, jit_path(a, 1, t), f * 2, CORAL + (255,), 22); draw_path(img, jit_path(b, 2, t), f * 2 - 1, CORAL + (255,), 22)
    f2 = eo(prog(t, max(0.9, ctx["vd"] * 0.55), 0.35))
    draw_path(img, jit_path(checkmark(910, 1010, 90), 3, t), f2, MINT + (255,), 20)

def sc_breath(img, s, t, dur, ctx):
    th = ctx["th"]; tt = stop(t); ph = (1 - math.cos(tt * 2 * math.pi / 5)) / 2
    for k, (col, base) in enumerate([(th["scrap"], 470), (th["acc"], 360), (INK, 250)]):
        disc = torn(base * 2, base * 2, col, 300 + k, 6, True, True)
        put(img, disc, W / 2 + boil(k, t, 3)[0], 820, 0.62 + 0.38 * ph)
    lab = "INHALA" if (tt % 5) < 2.5 else "EXHALA"
    put(img, text_img(lab, "rubik", 74, MINT if th["acc"] != MINT else CREAM), W / 2, 820, 1, -4)
    big = s["big"].upper(); L = label_c(big, "anton", fit(big, "anton", 820, 120, 60), INK, (250, 244, 220), 33, 36, 12, 6)
    put(img, L, W / 2, 250 + (1 - eo(prog(t, 0, 0.3))) * -300, 1, -2)
    cnt = text_img(f"{max(0, 60 - int(t * 12) % 61)}s" if s.get("countdown") else "60s", "marker", 90, th["acc2"])
    put(img, cnt, 900, 1290, 1, 10); draw_path(img, jit_path(scribble_circle(900, 1290, 120, 80, 8), 8, t), 1, th["acc2"] + (255,), 8)

def sc_product(img, s, t, dur, ctx):
    th = ctx["th"]; name = s.get("img"); path = os.path.join(PRODUCT_DIR, name) if name else ""
    p = eo(prog(t, 0, 0.35))
    if name and os.path.exists(path):
        if "polaroid" not in ctx:
            ph = Image.open(path).convert("RGB"); side = 760; r = max(side / ph.width, side / ph.height)
            ph = ph.resize((int(ph.width * r) + 1, int(ph.height * r) + 1), Image.LANCZOS)
            l, tp = (ph.width - side) // 2, (ph.height - side) // 2; ctx["photo"] = ph.crop((l, tp, l + side, tp + side))
            ctx["polaroid"] = True
        side = 760; z = 1 + 0.07 * clamp(t / dur); inner = ctx["photo"].resize((int(side * z), int(side * z)), Image.BILINEAR)
        o = (inner.width - side) // 2; inner = inner.crop((o, o, o + side, o + side))
        pol = Image.new("RGBA", (side + 60, side + 170), (252, 250, 244, 255)); pol.paste(inner, (30, 30))
        if s.get("tag"):
            tg = text_img(s["tag"], "marker", 70, COBALT); pol.alpha_composite(tg, ((pol.width - tg.width) // 2, side + 50))
        put(img, pol, W / 2, 680 - (1 - p) * 1400, 1, -4)
        put(img, tape(220, 64, 1), W / 2 - 300, 680 - (side + 170) / 2 + 10 - (1 - p) * 1400, 1, -35)
        put(img, tape(220, 64, 2), W / 2 + 300, 680 - (side + 170) / 2 + 30 - (1 - p) * 1400, 1, 30)
    else:
        st = sticker("wind", 360, COBALT, WHITE, 5); put(img, st, W / 2, 520 - (1 - p) * 1200)
        if "ransom" not in ctx: ctx["ransom"] = ransom((s.get("tag") or "AirNaze").upper(), 17, 210, 900)
        items, total = ctx["ransom"]
        for i, (L, xo, rot, yo) in enumerate(items):
            if stop(t) >= 0.3 + i * 0.06: put(img, L, W / 2 - total / 2 - 30 + xo + boil(i, t, 2)[0], 880 + yo * 0.5, 1.3 if stop(t) < 0.3 + i * 0.06 + 0.09 else 1, rot)
    for i, it in enumerate(s.get("items", [])[:3]):
        ti = 0.8 + i * 0.45
        if t < ti: continue
        L = label_c(it, "archivo", 50, INK if i != 1 else WHITE, [MINT, CORAL, (250, 244, 220)][i % 3], 90 + i, 28, 14, 6)
        q = eback(prog(t, ti, 0.3)); y = 1130 + i * 120
        put(img, L, W / 2 + (-1) ** i * 60, y, 0.6 + 0.4 * q, (-1) ** i * 3)

def sc_close(img, s, t, dur, ctx):
    th = ctx["th"]; tt = stop(t); p = eback(prog(tt, 0, 0.25))
    big = s["big"].upper(); size = fit(big, "anton", 2000, 150, 70); lines = wrap(big, "anton", size, 720)
    while len(lines) > 3: size -= 8; lines = wrap(big, "anton", size, 720)
    bw = 900; bh = int(len(lines) * size * 1.05 + 220)
    bub = torn(bw, bh, th["scrap"], 77, 8, True, True).copy(); d = ImageDraw.Draw(bub)
    tail = [(bw * 0.25, bh * 0.85), (bw * 0.12 + 30, bh + 70), (bw * 0.42, bh * 0.9)]
    d.polygon(tail, fill=th["scrap"] + (255,))
    y = (bub.height - len(lines) * size * 1.05) / 2
    for ln in lines:
        L = text_img(ln, "anton", size, th["scrap_ink"]); bub.alpha_composite(L, ((bub.width - L.width) // 2, int(y))); y += size * 1.05
    put(img, bub, W / 2 + boil(1, t, 2)[0], 700, 0.3 + 0.7 * p, -2)
    if s.get("small"):
        sm = text_img(s["small"], "marker", 64, th["ink"]); rv = eo(prog(t, 0.7, 0.5)); cw = int(sm.width * rv)
        if cw > 2: put(img, sm.crop((0, 0, cw, sm.height)), W / 2 - sm.width / 2 + cw / 2 - 60, 1130, 1, -3)
        pts, head = arrow((W / 2 + sm.width / 2 - 20, 1180), (900, 1330), 5, 0.3); f = eo(prog(t, 1.1, 0.4))
        draw_path(img, jit_path(pts, 5, t), f, th["acc2"] + (255,), 9)
        if f >= 1: draw_path(img, jit_path(head, 6, t), 1, th["acc2"] + (255,), 9)
    if t >= 0.55:
        stamp = text_img("AIRNAZE", "rubik", 64, th["acc2"], 0); fr = Image.new("RGBA", (stamp.width + 50, stamp.height + 36), (0, 0, 0, 0))
        ImageDraw.Draw(fr).rectangle([4, 4, fr.width - 5, fr.height - 5], outline=th["acc2"] + (255,), width=8); fr.alpha_composite(stamp, (25, 18))
        q = prog(t, 0.55, 0.12); put(img, fr, 300, 260, 1.6 - 0.6 * eo(q), -9, 0.9)

DRAW = {"slam": sc_slam, "stat": sc_stat, "cutout": sc_cutout, "triple": sc_triple, "step": sc_step, "split": sc_split,
        "breath": sc_breath, "product": sc_product, "close": sc_close}

# ---------- overlays ----------
def caption(img, words, times, t, ctx):
    if not words: return
    idx = 0
    for i, (a, b) in enumerate(times):
        if t >= a: idx = i
    # chunk around idx (max 3 words / 20 chars)
    chunks, cur = [], []
    for i, w_ in enumerate(words):
        if cur and (len(cur) >= 3 or sum(len(words[j]) for j in cur) + len(w_) > 18): chunks.append(cur); cur = []
        cur.append(i)
    if cur: chunks.append(cur)
    ch = next(c for c in chunks if idx in c)
    if t < times[0][0] - 0.05 or t > times[-1][1] + 0.6: return
    size = 60; key = "archivo"; gap = 18
    toks = [words[j].upper() for j in ch]; widths = [tw(x, key, size) for x in toks]
    total = sum(widths) + gap * (len(toks) - 1); x = W / 2 - total / 2; y = 1470
    for j, tok, wdt in zip(ch, toks, widths):
        if j == idx:
            box = torn(int(wdt + 36), 92, MINT, 500 + j % 7, 6, False)
            put(img, box, x + wdt / 2, y + 4)
            L = text_img(tok, key, size, NAVY)
        else:
            L = text_img(tok, key, size, CREAM, 6, NAVY)
        put(img, L, x + wdt / 2, y); x += wdt + gap

def overlays(img, i, n, t):
    tg = label_c("AIRNAZE", "mono", 34, INK, (250, 244, 220), 2, 22, 10, 4); jx, jy = boil(99, t, 1.5)
    put(img, tg, 140 + jx, 120 + jy, 1, -4)
    put(img, text_img(f"{i + 1:02d}/{n:02d}", "mono", 34, CREAM, 4, NAVY), W - 120, 118)

def apply_grain(img, k):
    a = np.asarray(img.convert("RGB"), dtype=np.int16) + GRAIN[k % 3][..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")

# ---------- audio ----------
def tts(text, path):
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE, "-f", path, "--length-scale", "0.9", "--sentence-silence", "0.12"],
                   input=text.encode(), check=True, capture_output=True)
    with wave.open(path) as w: return w.getnframes() / w.getframerate()

def write_wav(path, x, sr=44100):
    x = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())

def music2(total, seed, sr=44100):
    rng = np.random.default_rng(seed); n = int(total * sr); out = np.zeros(n); t = np.arange(n) / sr
    progs = [[57, 53, 48, 55], [50, 53, 48, 55], [57, 55, 53, 52], [52, 48, 50, 55]]; pr = progs[seed % 4]
    def add(s0, sig):
        s0 = int(s0 * sr); e = min(n, s0 + len(sig))
        if s0 < n: out[s0:e] += sig[:e - s0]
    def tt(d): return np.arange(int(d * sr)) / sr
    k = tt(0.32); kick = 0.55 * np.exp(-k * 11) * np.sin(2 * np.pi * (45 * k + 90 / 25 * (1 - np.exp(-k * 25))))
    c = tt(0.18); clap = 0.22 * np.exp(-c * 22) * np.diff(rng.standard_normal(len(c) + 1))
    h = tt(0.04); hat = np.diff(rng.standard_normal(len(h) + 1)) * np.exp(-h * 120)
    nb = int(total / BEAT) + 1
    for b in range(nb):
        bar = b // 4; root = pr[bar % 4]; tb = b * BEAT
        add(tb, kick)
        if b % 4 in (1, 3): add(tb, clap)
        add(tb + HALF, 0.07 * hat); add(tb, 0.035 * hat)
        f = 440 * 2 ** ((root - 24 - 69) / 12); bt = tt(HALF * 0.9)
        add(tb + HALF, 0.2 * np.tanh(3 * np.sin(2 * np.pi * f * bt)) * np.exp(-bt * 7))
        if b % 4 in (0, 2) and bar % 2 == 0 or b % 8 == 7:
            st = tt(0.28); chord = [root, root + 3 + (seed % 2), root + 7]
            sig = sum(sum(np.sin(2 * np.pi * 440 * 2 ** ((m - 69) / 12) * hk * st) / hk for hk in (1, 2, 3)) for m in chord)
            add(tb + HALF, 0.05 * sig * np.exp(-st * 9))
    fade = np.minimum(1, np.minimum(t / 0.3, (total - t) / 1.2)); out *= np.clip(fade, 0, 1)
    return out / (np.abs(out).max() + 1e-9) * 0.85

def sfx_track(total, events, sr=44100):
    rng = np.random.default_rng(3); n = int(total * sr) + sr; out = np.zeros(n)
    def tt(d): return np.arange(int(d * sr)) / sr
    for (time, kind) in events:
        if kind == "thump":
            k = tt(0.25); s = 0.8 * np.exp(-k * 16) * np.sin(2 * np.pi * (40 * k + 110 / 30 * (1 - np.exp(-k * 30))))
        elif kind == "rip":
            k = tt(0.34); crack = (rng.random(len(k)) > 0.6).astype(float)
            s = 0.5 * np.diff(rng.standard_normal(len(k) + 1)) * crack * np.exp(-k * 7) * np.minimum(1, k / 0.02)
        elif kind == "whoosh":
            k = tt(0.42); nz = rng.standard_normal(len(k)); nz = np.convolve(nz, np.ones(18) / 18, "same")
            s = 1.4 * nz * np.sin(np.pi * k / k[-1]) ** 2
        else:  # pop
            k = tt(0.09); s = 0.45 * np.exp(-k * 40) * np.sin(2 * np.pi * (700 * k - 2500 * k * k))
        s0 = int(time * sr); e = min(n, s0 + len(s)); out[s0:e] += s[:e - s0]
    return out[:int(total * sr)]

# ---------- main ----------
def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; only_frames = "--frames" in sys.argv
    work = os.path.splitext(out)[0] + "_work"; os.makedirs(work, exist_ok=True)
    scenes = spec["scenes"]; seed0 = spec.get("music_seed", 1)
    for s in scenes: s["type"] = ALIAS.get(s["type"], s["type"])
    durs = []; prev_theme = None
    for i, s in enumerate(scenes):
        vd = tts(s["voice"], f"{work}/v{i}.wav"); s["_vd"] = vd
        d = max(2.1, vd + 0.4); d = math.ceil(d / HALF) * HALF; durs.append(d)   # cuts land on the beat grid
        th = s.get("theme") or DEFAULT_THEME[s["type"]]
        if th == prev_theme: th = [x for x in ("cream", "blue", "navy", "mint") if x != prev_theme][i % 3]
        s["_theme"] = th; prev_theme = th if s["type"] != "split" else "blue"
    durs[-1] += 0.8
    total = sum(durs); starts = list(np.cumsum([0] + durs[:-1]))
    TRANS = ["tear", "punch", "drop", "punch"]; TD = 0.3; VOFF = 0.12
    ctxs = [dict(th=THEMES[s["_theme"]], seed=seed0 * 13 + i * 7, vd=s["_vd"]) for i, s in enumerate(scenes)]
    # caption timings
    for s in scenes:
        ws = s["voice"].split(); wts = [len(w_) + 2 for w_ in ws]; tot = sum(wts); acc = 0; tm = []
        for w_ in wts: tm.append((VOFF + acc / tot * s["_vd"], VOFF + (acc + w_) / tot * s["_vd"])); acc += w_
        s["_words"], s["_times"] = ws, tm
    # sfx events
    events = []
    for i, s in enumerate(scenes):
        if i: events.append((starts[i], {"tear": "rip", "punch": "thump", "drop": "whoosh"}[TRANS[i % 4]]))
        if s["type"] == "slam":
            n = len([x for x in s["big"].split() if len(x) > 3]) or 1; step_ = min(0.42, 0.72 * s["_vd"] / n)
            events += [(starts[i] + 0.05 + k * step_, "thump") for k in range(n)]
        if s["type"] == "close": events.append((starts[i] + 0.55, "thump"))
        if s["type"] in ("triple", "cutout", "product", "step"): events.append((starts[i] + 0.3, "pop"))

    def render_scene(i, t):
        s = scenes[i]; ctx = ctxs[i]; ctx["shake"] = 0
        img = draw_bg(s["_theme"], ctx["seed"], t, durs[i])
        DRAW[s["type"]](img, s, t, durs[i], ctx)
        return img, ctx.get("shake", 0)

    def frame(fi):
        T = fi / FPS; i = max(k for k in range(len(scenes)) if starts[k] <= T + 1e-9); t = T - starts[i]
        img, shake = render_scene(i, t)
        if i and t < TD:
            kind = TRANS[i % 4]; p = eo(t / TD); prev, _ = render_scene(i - 1, durs[i - 1] + t)
            if kind == "tear":
                r = np.random.default_rng(i); offs = np.cumsum(r.normal(0, 4, W)); offs -= offs.mean()
                ey = (H + 120) * (1 - p) - 60; Y = np.arange(H)[:, None]; edge = ey + offs[None, :] + np.linspace(-80, 80, W)[None, :]
                m = (Y > edge); core = (Y > edge - 14) & ~m
                a = np.asarray(prev.convert("RGB")).copy(); b = np.asarray(img.convert("RGB"))
                a[m] = b[m]; a[core] = (250, 247, 240); img = Image.fromarray(a).convert("RGBA")
            elif kind == "punch":
                z = 1.18 - 0.18 * p; zz = img.resize((int(W * z), int(H * z)), Image.BILINEAR)
                img = zz.crop(((zz.width - W) // 2, (zz.height - H) // 2, (zz.width - W) // 2 + W, (zz.height - H) // 2 + H))
                if t < 2 / FPS: img = Image.blend(img, Image.new("RGBA", (W, H), ctxs[i]["th"]["acc"] + (255,)), 0.55)
            else:
                y = int(-H * (1 - eback(p, 1.2))); comp(prev, Image.new("RGBA", (W, 40), (0, 0, 0, 90)), 0, y + H - 10)
                prev.paste(img, (0, y)); img = prev
        s = scenes[i]; caption(img, s["_words"], s["_times"], t, ctxs[i]); overlays(img, i, len(scenes), T)
        if shake > 0.5:
            r = random.Random(fi); dx, dy = int(r.uniform(-shake, shake)), int(r.uniform(-shake, shake))
            c = Image.new("RGBA", (W, H), ctxs[i]["th"]["bg"] + (255,)); c.paste(img, (dx, dy)); img = c
        return apply_grain(img, fi // 4)

    nfr = int(round(total * FPS))
    if only_frames:
        thumbs = []
        for i in range(len(scenes)):
            for f in (0.12, 0.45, 0.85):
                fi = int((starts[i] + durs[i] * f) * FPS); im = frame(fi); im.save(f"{work}/preview_{i}_{fi}.jpg", quality=85)
                thumbs.append(im.resize((270, 480)))
        cols = 6; rows = math.ceil(len(thumbs) / cols); sheet = Image.new("RGB", (270 * cols, 480 * rows), (0, 0, 0))
        for k, im in enumerate(thumbs): sheet.paste(im, ((k % cols) * 270, (k // cols) * 480))
        sheet.save(f"{work}/contact.jpg", quality=85); print("frames in", work, "| total", round(total, 1), "s"); return
    vid = f"{work}/video.mp4"
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    for fi in range(nfr): proc.stdin.write(frame(fi).tobytes())
    proc.stdin.close(); proc.wait()
    if proc.returncode: sys.exit("video encode failed")
    sr = 22050; vtrack = np.zeros(int(total * sr) + sr, dtype=np.float32)
    for i in range(len(scenes)):
        with wave.open(f"{work}/v{i}.wav") as w:
            sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
        s0 = int((starts[i] + VOFF) * sr); vtrack[s0:s0 + len(a)] += a
    with wave.open(f"{work}/voice.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(np.clip(vtrack, -32767, 32767).astype(np.int16).tobytes())
    write_wav(f"{work}/music.wav", music2(total + 0.3, seed0)); write_wav(f"{work}/sfx.wav", sfx_track(total + 0.3, events))
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", f"{work}/voice.wav", "-i", f"{work}/music.wav", "-i", f"{work}/sfx.wav",
                    "-filter_complex",
                    "[1:a]aresample=44100,highpass=f=80,acompressor=threshold=0.1:ratio=3,asplit=2[v1][vsc];"
                    "[2:a]volume=0.5[m];[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=250[md];"
                    "[3:a]volume=0.35[fx];"
                    "[v1][md][fx]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    # 2.ª pasada de sonoridad: llevar a ~-14 LUFS con limitador
    r = subprocess.run(["ffmpeg", "-i", tmp, "-af", "ebur128=framelog=quiet", "-f", "null", "-"], capture_output=True, text=True).stderr
    try: I = float([l for l in r.splitlines() if " I:" in l][-1].split()[1])
    except Exception: I = -14.0
    if I < -14.6:
        tmp2 = out + ".tmp2.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", f"volume={-14 - I:.1f}dB,alimiter=limit=0.89:level=disabled",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", tmp2], check=True)
        os.replace(tmp2, tmp)
    os.replace(tmp, out); print(out, round(total, 1), "s")

if __name__ == "__main__":
    main()
