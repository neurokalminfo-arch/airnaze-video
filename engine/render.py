#!/usr/bin/env python3
"""AirNaze short-video renderer (1080x1920, 30 fps).

Usage: python3 render.py spec.json out.mp4 [--frames]   (--frames: only write preview PNGs)

spec.json:
{
  "music_seed": 3,
  "scenes": [
    {"type": "hook",  "voice": "...", "big": "Texto grande", "small": "subtítulo"},
    {"type": "tip",   "voice": "...", "n": 1, "title": "...", "sub": "...", "icon": "drop"},
    {"type": "stat",  "voice": "...", "value": "20.000", "label": "respiraciones al día"},
    {"type": "versus","voice": "...", "left": "Boca", "right": "Nariz", "lsub": "...", "rsub": "..."},
    {"type": "breath","voice": "...", "big": "Inhala 4 · Exhala 6"},
    {"type": "brand", "voice": "...", "big": "...", "small": "..."}
  ]
}
icons: drop, moon, bed, wind, window, clock, run, leaf, phone, sun, nose, check
"""
import json, math, os, random, subprocess, sys, wave, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(HERE, "voices", "es_ES-davefx-medium.onnx")
FD = "/usr/share/fonts/opentype/inter/"
def F(name, size): return ImageFont.truetype(FD + name, size)

NAVY = (6, 22, 56); DEEP = (3, 12, 34); BLUE = (30, 110, 255); SKY = (90, 180, 255)
ICE = (205, 232, 255); WHITE = (255, 255, 255); MINT = (110, 240, 210)

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(t): t = clamp(t); return 1 - (1 - t) ** 3
def eback(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def prog(t, start, dur): return clamp((t - start) / dur)

# ---------- background layers ----------
def make_gradient(top, bottom):
    g = np.linspace(0, 1, H)[:, None]
    arr = (np.array(top)[None, None, :] * (1 - g[..., None]) + np.array(bottom)[None, None, :] * g[..., None])
    arr = np.repeat(arr, W, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB")

def make_blob(r, color, alpha):
    s = r * 3
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([r, r, 2 * r, 2 * r], fill=color + (alpha,))
    return im.filter(ImageFilter.GaussianBlur(r * 0.45))

class Background:
    def __init__(self, seed):
        rnd = random.Random(seed)
        self.grads = [make_gradient(NAVY, DEEP), make_gradient((8, 40, 100), (4, 14, 40)), make_gradient((10, 30, 80), (2, 30, 60))]
        self.blobs = []
        for i in range(4):
            r = rnd.randint(260, 420)
            col = rnd.choice([BLUE, SKY, (60, 90, 255), (20, 160, 220)])
            self.blobs.append((make_blob(r, col, rnd.randint(70, 120)), rnd.random() * 6.28, rnd.uniform(0.15, 0.35), rnd.uniform(0.1, 0.9), rnd.uniform(0.1, 0.9)))
        self.parts = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1.5, 4.5), rnd.uniform(20, 70)) for _ in range(46)]

    def draw(self, T, variant):
        img = self.grads[variant % len(self.grads)].copy()
        for (b, ph, sp, cx, cy) in self.blobs:
            x = cx * W + math.sin(T * sp + ph) * 220 - b.width / 2
            y = cy * H + math.cos(T * sp * 0.8 + ph) * 300 - b.height / 2
            img.paste(b, (int(x), int(y)), b)
        d = ImageDraw.Draw(img, "RGBA")
        # flowing "air" lines
        for k in range(3):
            pts = []
            base = H * (0.18 + 0.32 * k)
            for x in range(-20, W + 40, 30):
                y = base + math.sin(x / 170 + T * (0.9 + k * 0.3) + k) * (40 + 15 * k)
                pts.append((x, y))
            d.line(pts, fill=ICE + (26,), width=3, joint="curve")
        for (x, y, r, sp) in self.parts:
            yy = (y - T * sp) % H
            xx = x + math.sin(T + y) * 12
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=WHITE + (60,))
        return img

# ---------- text helpers ----------
def wrap(text, font, maxw, draw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def fit_font(text, name, start, maxw, maxlines, draw):
    s = start
    while s > 40:
        f = F(name, s)
        if len(wrap(text, f, maxw, draw)) <= maxlines: return f
        s -= 6
    return F(name, 40)

def text_layer(lines, font, color, align="center", spacing=1.12, shadow=True):
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lh = int(font.size * spacing)
    wmax = max(int(tmp.textlength(l, font=font)) for l in lines) + 40
    im = Image.new("RGBA", (wmax, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        lw = d.textlength(l, font=font)
        x = (wmax - lw) / 2 if align == "center" else 20
        if shadow: d.text((x + 3, 20 + i * lh + 5), l, font=font, fill=(0, 0, 20, 110))
        d.text((x, 20 + i * lh), l, font=font, fill=color)
    return im

def paste_t(img, layer, cx, cy, alpha=1.0, scale=1.0, rot=0):
    if alpha <= 0.01: return
    L = layer
    if scale != 1.0:
        L = L.resize((max(1, int(L.width * scale)), max(1, int(L.height * scale))), Image.BICUBIC)
    if rot: L = L.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = L.getchannel("A").point(lambda v: int(v * alpha)); L = L.copy(); L.putalpha(a)
    img.paste(L, (int(cx - L.width / 2), int(cy - L.height / 2)), L)

# ---------- icons ----------
def icon(name, size, color=WHITE, t=1.0):
    s = size; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w = max(6, s // 14)
    c = color + (255,)
    if name == "drop":
        d.polygon([(s*.5, s*.08), (s*.22, s*.55), (s*.78, s*.55)], fill=c); d.ellipse([s*.2, s*.36, s*.8, s*.92], fill=c)
    elif name == "moon":
        d.ellipse([s*.12, s*.12, s*.88, s*.88], fill=c); d.ellipse([s*.36, s*.02, s*1.02, s*.7], fill=(0, 0, 0, 0))
    elif name == "bed":
        d.rounded_rectangle([s*.08, s*.5, s*.92, s*.72], 12, fill=c); d.rounded_rectangle([s*.12, s*.36, s*.38, s*.52], 14, fill=c)
        d.rectangle([s*.08, s*.72, s*.14, s*.86], fill=c); d.rectangle([s*.86, s*.72, s*.92, s*.86], fill=c)
    elif name == "wind":
        for i, y in enumerate([.3, .5, .7]):
            L = [.85, .65, .75][i] * t
            d.line([(s*.1, s*y), (s*(.1 + L*.8), s*y)], fill=c, width=w)
            d.arc([s*(.1 + L*.8) - s*.1, s*y - s*.2, s*(.1 + L*.8) + s*.1, s*y], 270, 90, fill=c, width=w)
    elif name == "window":
        d.rounded_rectangle([s*.12, s*.1, s*.88, s*.9], 16, outline=c, width=w)
        d.line([(s*.5, s*.1), (s*.5, s*.9)], fill=c, width=w); d.line([(s*.12, s*.5), (s*.88, s*.5)], fill=c, width=w)
    elif name == "clock":
        d.ellipse([s*.1, s*.1, s*.9, s*.9], outline=c, width=w)
        a = -math.pi/2 + t * 2 * math.pi
        d.line([(s*.5, s*.5), (s*.5 + math.cos(a)*s*.3, s*.5 + math.sin(a)*s*.3)], fill=c, width=w)
        d.line([(s*.5, s*.5), (s*.5, s*.3)], fill=c, width=w)
    elif name == "run":
        d.ellipse([s*.55, s*.06, s*.75, s*.26], fill=c)
        for a, b in [((.6, .3), (.45, .6)), ((.45, .6), (.25, .85)), ((.45, .6), (.7, .75)), ((.7, .75), (.65, .95)), ((.55, .38), (.3, .4)), ((.55, .38), (.8, .5))]:
            d.line([(s*a[0], s*a[1]), (s*b[0], s*b[1])], fill=c, width=w + 4)
    elif name == "leaf":
        d.ellipse([s*.15, s*.15, s*.85, s*.85], fill=c); d.line([(s*.2, s*.8), (s*.75, s*.25)], fill=NAVY + (255,), width=w)
    elif name == "phone":
        d.rounded_rectangle([s*.28, s*.06, s*.72, s*.94], 26, outline=c, width=w); d.line([(s*.43, s*.84), (s*.57, s*.84)], fill=c, width=w)
    elif name == "sun":
        d.ellipse([s*.3, s*.3, s*.7, s*.7], fill=c)
        for k in range(8):
            a = k * math.pi / 4 + t
            d.line([(s*.5 + math.cos(a)*s*.3, s*.5 + math.sin(a)*s*.3), (s*.5 + math.cos(a)*s*.45, s*.5 + math.sin(a)*s*.45)], fill=c, width=w)
    elif name == "nose":
        d.arc([s*.2, s*.08, s*.8, s*.92], 300, 120, fill=c, width=w)
        d.ellipse([s*.3, s*.62, s*.48, s*.78], outline=c, width=w); d.ellipse([s*.52, s*.62, s*.7, s*.78], outline=c, width=w)
    else:  # check
        d.line([(s*.15, s*.55), (s*.42, s*.8), (s*.88, s*.22)], fill=c, width=w + 4, joint="curve")
    return im

# ---------- captions ----------
def chunks(text, n=5):
    w = text.split(); return [" ".join(w[i:i + n]) for i in range(0, len(w), n)]

def draw_caption(img, text, t, dur):
    cs = chunks(text)
    if not cs: return
    weights = [len(c) for c in cs]; tot = sum(weights); acc = 0; idx = len(cs) - 1
    for i, wgt in enumerate(weights):
        if t < (acc + wgt) / tot * dur: idx = i; break
        acc += wgt
    f = F("Inter-Bold.otf", 50)
    d = ImageDraw.Draw(img, "RGBA")
    lines = wrap(cs[idx], f, 880, d)
    y0 = 1560
    for i, l in enumerate(lines):
        lw = d.textlength(l, font=f); x = (W - lw) / 2; y = y0 + i * 66
        d.rounded_rectangle([x - 22, y - 8, x + lw + 22, y + 62], 18, fill=(0, 8, 30, 170))
        d.text((x, y), l, font=f, fill=WHITE)

def draw_brand_tag(img):
    d = ImageDraw.Draw(img, "RGBA"); f = F("Inter-ExtraBold.otf", 38)
    d.rounded_rectangle([60, 90, 60 + d.textlength("AirNaze", font=f) + 44, 150], 30, fill=(255, 255, 255, 30))
    d.text((82, 96), "AirNaze", font=f, fill=WHITE)

def progress_bar(img, T, total):
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([60, 1850, W - 60, 1858], 4, fill=(255, 255, 255, 40))
    d.rounded_rectangle([60, 1850, 60 + (W - 120) * clamp(T / total), 1858], 4, fill=SKY + (230,))

# ---------- scene drawers ----------
def scene_hook(img, s, t, dur, cache):
    d = ImageDraw.Draw(img)
    if "big" not in cache:
        f = fit_font(s["big"], "InterDisplay-Black.otf", 132, 920, 5, d)
        cache["bigf"] = f; cache["words"] = s["big"].split()
        cache["lines"] = wrap(s["big"], f, 920, d)
        cache["big"] = True
    f = cache["bigf"]; lines = cache["lines"]; lh = int(f.size * 1.08)
    y0 = 760 - len(lines) * lh / 2; widx = 0
    for li, l in enumerate(lines):
        ws = l.split(); total = sum(d.textlength(w + " ", font=f) for w in ws) - d.textlength(" ", font=f)
        x = (W - total) / 2
        for w in ws:
            p = eback(prog(t, 0.1 + widx * 0.12, 0.35)); widx += 1
            ww = d.textlength(w, font=f)
            if p > 0:
                acc = [a.lower() for a in s.get("accent", [])]
                layer = text_layer([w], f, MINT if w.strip("¿?¡!.,").lower() in acc else WHITE, shadow=True)
                paste_t(img, layer, x + ww / 2, y0 + li * lh + lh / 2 - (1 - p) * 60, alpha=clamp(p), scale=0.6 + 0.4 * p)
            x += ww + d.textlength(" ", font=f)
    if s.get("small"):
        p = eo(prog(t, 0.9, 0.5))
        L = text_layer(wrap(s["small"], F("Inter-Medium.otf", 54), 900, d), F("Inter-Medium.otf", 54), ICE)
        paste_t(img, L, W / 2, 760 + len(lines) * lh / 2 + 120 + (1 - p) * 40, alpha=p)

def scene_tip(img, s, t, dur, cache):
    d = ImageDraw.Draw(img, "RGBA")
    # big number slides from left
    mir = (s.get("n", 1) % 2 == 0); NX, IX, TY = (730, 300, 600) if mir else (300, 780, 600)
    p = eo(prog(t, 0, 0.5))
    num = text_layer([f"0{s['n']}" if s.get("n") else "•"], F("InterDisplay-Black.otf", 300), SKY, shadow=False)
    paste_t(img, num, NX + (1 - p) * (500 if mir else -500), TY, alpha=0.9 * p)
    # icon bubble pops right, pulsing
    p2 = eback(prog(t, 0.2, 0.5)); pulse = 1 + 0.05 * math.sin(t * 4)
    if p2 > 0:
        r = 170 * p2 * pulse
        d.ellipse([IX - r, TY - r, IX + r, TY + r], fill=(255, 255, 255, 34))
        d.ellipse([IX - r * .78, TY - r * .78, IX + r * .78, TY + r * .78], fill=BLUE + (255,))
        ic = icon(s.get("icon", "check"), int(180 * p2) + 1, WHITE, t)
        img.paste(ic, (int(IX - ic.width / 2), int(TY - ic.height / 2)), ic)
    # card slides up
    p3 = eo(prog(t, 0.35, 0.55))
    cy = 1180 + (1 - p3) * 500
    tf = fit_font(s["title"], "InterDisplay-ExtraBold.otf", 92, 860, 3, d)
    tl = wrap(s["title"], tf, 860, d)
    sf = F("Inter-Medium.otf", 50); sl = wrap(s.get("sub", ""), sf, 860, d) if s.get("sub") else []
    h = len(tl) * tf.size * 1.12 + len(sl) * 64 + 120
    if p3 > 0:
        card = Image.new("RGBA", (W - 100, int(h)), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, card.width - 1, card.height - 1], 48, fill=(255, 255, 255, 236))
        cd.rounded_rectangle([0, 0, 16, card.height - 1], 8, fill=BLUE + (255,))
        y = 50
        for l in tl: cd.text((60, y), l, font=tf, fill=NAVY); y += tf.size * 1.12
        y += 16
        for i, l in enumerate(sl):
            a = int(255 * eo(prog(t, 0.7 + i * 0.15, 0.4)))
            cd.text((60, y), l, font=sf, fill=(40, 70, 120, a)); y += 64
        paste_t(img, card, W / 2, cy + h / 2 - 120, alpha=p3)

def scene_stat(img, s, t, dur, cache):
    d = ImageDraw.Draw(img, "RGBA")
    val = s["value"]; digits = "".join(ch for ch in val if ch.isdigit())
    p = eo(prog(t, 0.1, min(1.6, dur * 0.5)))
    if digits:
        lead = val[:len(val) - len(val.lstrip("+~<>"))]
        tail = val[len(val.rstrip("%+x hminsegd")):]
        cur = int(int(digits) * p); shown = lead + f"{cur:,}".replace(",", ".") + tail
    else: shown = val
    # ring
    r = 330; ang = 360 * p
    d.ellipse([W/2 - r, 720 - r, W/2 + r, 720 + r], outline=(255, 255, 255, 40), width=26)
    d.arc([W/2 - r, 720 - r, W/2 + r, 720 + r], -90, -90 + ang, fill=MINT + (255,), width=26)
    f = fit_font(shown, "InterDisplay-Black.otf", 180, 470, 1, d)
    paste_t(img, text_layer([shown], f, WHITE), W / 2, 720)
    p2 = eo(prog(t, 0.6, 0.5))
    lf = F("InterDisplay-Bold.otf", 70)
    paste_t(img, text_layer(wrap(s["label"], lf, 900, d), lf, ICE), W / 2, 1230 + (1 - p2) * 60, alpha=p2)

def scene_versus(img, s, t, dur, cache):
    d = ImageDraw.Draw(img, "RGBA")
    for side, key, sub, col, x0 in [(-1, "left", "lsub", (255, 110, 120), 0), (1, "right", "rsub", MINT, W / 2)]:
        st = 0.1 if side < 0 else 0.45
        p = eo(prog(t, st, 0.5))
        x = x0 + side * (1 - p) * 0  # panels drop in
        y_off = (1 - p) * -700
        d.rounded_rectangle([x + 40, 360 + y_off, x + W / 2 - 20, 1320 + y_off], 44, fill=(255, 255, 255, 30 if side < 0 else 46))
        tf = F("InterDisplay-Black.otf", 96)
        paste_t(img, text_layer([s[key]], tf, col), x + W / 4 + 10, 560 + y_off, alpha=p)
        sf = F("Inter-SemiBold.otf", 52)
        paste_t(img, text_layer(wrap(s[sub], sf, 400, d), sf, WHITE), x + W / 4 + 10, 920 + y_off, alpha=eo(prog(t, st + 0.3, 0.5)))
    p3 = eback(prog(t, 0.9, 0.4))
    if p3 > 0:
        r = 70 * p3
        d.ellipse([W/2 - r, 840 - r, W/2 + r, 840 + r], fill=BLUE + (255,))
        paste_t(img, text_layer(["vs"], F("InterDisplay-Black.otf", 64), WHITE, shadow=False), W / 2, 836, alpha=clamp(p3))

def scene_breath(img, s, t, dur, cache):
    d = ImageDraw.Draw(img, "RGBA")
    ph = (math.sin(t * 2 * math.pi / 5 - math.pi / 2) + 1) / 2  # 5 s breath cycle
    for k, a in [(1.25, 25), (1.1, 50), (1.0, 255)]:
        r = (190 + 170 * ph) * k
        d.ellipse([W/2 - r, 780 - r, W/2 + r, 780 + r], fill=(SKY if k > 1 else BLUE) + (a,))
    lab = "inhala" if math.cos(t * 2 * math.pi / 5 - math.pi / 2) < 0 else "exhala"
    lab = "inhala" if (t % 5) < 2.5 else "exhala"
    paste_t(img, text_layer([lab], F("InterDisplay-Black.otf", 96), WHITE, shadow=False), W / 2, 780)
    p = eo(prog(t, 0.3, 0.5)); bf = fit_font(s["big"], "InterDisplay-ExtraBold.otf", 84, 900, 3, d)
    paste_t(img, text_layer(wrap(s["big"], bf, 900, d), bf, ICE), W / 2, 1290 + (1 - p) * 50, alpha=p)

def scene_brand(img, s, t, dur, cache):
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(4):  # expanding rings
        q = ((t * 0.6 + i * 0.25) % 1.0)
        r = 120 + q * 520
        d.ellipse([W/2 - r, 640 - r, W/2 + r, 640 + r], outline=ICE + (int(120 * (1 - q)),), width=6)
    p = eback(prog(t, 0.1, 0.6))
    paste_t(img, text_layer(["AirNaze"], F("InterDisplay-Black.otf", 150), WHITE), W / 2, 640, alpha=clamp(p), scale=0.7 + 0.3 * clamp(p))
    p2 = eo(prog(t, 0.6, 0.5)); bf = fit_font(s["big"], "InterDisplay-ExtraBold.otf", 80, 900, 3, d)
    paste_t(img, text_layer(wrap(s["big"], bf, 900, d), bf, WHITE), W / 2, 1060 + (1 - p2) * 50, alpha=p2)
    if s.get("small"):
        p3 = eo(prog(t, 1.0, 0.5)); sf = F("Inter-SemiBold.otf", 50)
        L = text_layer(wrap(s["small"], sf, 820, d), sf, NAVY, shadow=False)
        pill = Image.new("RGBA", (L.width + 60, L.height + 20), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill.width - 1, pill.height - 1], 40, fill=MINT + (255,))
        pill.paste(L, (30, 10), L)
        paste_t(img, pill, W / 2, 1320, alpha=p3, scale=0.9 + 0.1 * p3)

PRODUCT_DIR = os.path.join(os.path.dirname(HERE), "assets", "product")

def load_product(name):
    path = os.path.join(PRODUCT_DIR, name) if name else ""
    if not name or not os.path.exists(path):
        sys.exit(f"Falta la foto del producto: {path or '(sin img)'} — usa una de assets/product/ o cambia la escena")
    im = Image.open(path).convert("RGB")
    side = 860; r = max(side / im.width, side / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    l, tp = (im.width - side) // 2, (im.height - side) // 2
    return im.crop((l, tp, l + side, tp + side))

def scene_product(img, s, t, dur, cache):
    """Foto real de assets/product/ (s['img']), con zoom lento y rasgos en chips (s['items'])."""
    d = ImageDraw.Draw(img, "RGBA")
    if "photo" not in cache: cache["photo"] = load_product(s.get("img"))
    ph = cache["photo"]; side = ph.width
    p = eo(prog(t, 0, 0.6))
    z = 1.0 + 0.06 * clamp(t / max(dur, 0.1))
    inner = ph.resize((int(side * z), int(side * z)), Image.BILINEAR)
    off = (inner.width - side) // 2
    inner = inner.crop((off, off, off + side, off + side))
    mask = Image.new("L", (side, side), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, side - 1, side - 1], 56, fill=255)
    card = Image.new("RGBA", (side, side), (0, 0, 0, 0)); card.paste(inner, (0, 0), mask)
    cy = 640 + (1 - p) * 700
    d.rounded_rectangle([W/2 - side/2 - 14, cy - side/2 - 14, W/2 + side/2 + 14, cy + side/2 + 14], 66, fill=(255, 255, 255, int(40 * p)))
    paste_t(img, card, W / 2, cy, alpha=p)
    if s.get("tag"):
        tf = F("InterDisplay-ExtraBold.otf", 46)
        L = text_layer([s["tag"]], tf, NAVY, shadow=False)
        pill = Image.new("RGBA", (L.width + 40, L.height + 10), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill.width - 1, pill.height - 1], 36, fill=MINT + (255,))
        pill.paste(L, (20, 5), L)
        paste_t(img, pill, W / 2, cy - side / 2, alpha=eo(prog(t, 0.4, 0.4)))
    cf = F("Inter-SemiBold.otf", 48)
    for i, it in enumerate(s.get("items", [])[:3]):
        q = eback(prog(t, 0.7 + i * 0.35, 0.45))
        if q <= 0: continue
        L = text_layer([it], cf, WHITE, shadow=False)
        chip = Image.new("RGBA", (L.width + 70, L.height + 6), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip); cd.rounded_rectangle([0, 0, chip.width - 1, chip.height - 1], 34, fill=BLUE + (240,))
        cd.ellipse([22, chip.height / 2 - 9, 40, chip.height / 2 + 9], fill=MINT + (255,))
        chip.paste(L, (45, 3), L)
        paste_t(img, chip, W / 2, 1180 + i * 105, alpha=clamp(q), scale=0.85 + 0.15 * clamp(q))

DRAW = {"hook": scene_hook, "tip": scene_tip, "stat": scene_stat, "versus": scene_versus, "breath": scene_breath, "brand": scene_brand, "product": scene_product}
TRANS = ["slide", "zoom", "wipe", "fade"]

# ---------- audio ----------
def tts(text, path):
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE, "-f", path, "--length-scale", "0.93", "--sentence-silence", "0.15"],
                   input=text.encode(), check=True, capture_output=True)
    with wave.open(path) as w: return w.getnframes() / w.getframerate()

def music(total, seed, path, sr=44100):
    rnd = np.random.default_rng(seed); n = int(total * sr); t = np.arange(n) / sr
    roots = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    k = seed % 4; roots = roots[k:] + roots[:k]
    bpm = 96; beat = 60 / bpm; bar = beat * 4
    out = np.zeros(n)
    for i in range(int(total / bar) + 1):
        ch = roots[i % 4]; s0 = int(i * bar * sr); s1 = min(n, int((i + 1) * bar * sr))
        if s0 >= n: break
        tt = t[s0:s1] - i * bar; env = np.minimum(1, tt / 0.4) * np.minimum(1, (bar - tt) / 0.3)
        for m in ch:
            f = 440 * 2 ** ((m - 69) / 12)
            out[s0:s1] += env * 0.05 * (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.003 * tt) + 0.2 * np.sin(4 * np.pi * f * tt))
        fb = 440 * 2 ** ((ch[0] - 12 - 69) / 12)
        out[s0:s1] += 0.07 * env * np.sin(2 * np.pi * fb * tt)
        # arpeggio
        for k in range(8):
            a0 = s0 + int(k * beat / 2 * sr); a1 = min(s1, a0 + int(0.25 * sr))
            if a0 >= s1: break
            m = ch[k % 3] + 12; f = 440 * 2 ** ((m - 69) / 12); ta = t[a0:a1] - t[a0]
            out[a0:a1] += 0.035 * np.exp(-ta * 9) * np.sin(2 * np.pi * f * ta)
    # soft kick + hat
    for b in range(int(total / beat) + 1):
        s0 = int(b * beat * sr)
        if s0 >= n: break
        k1 = min(n, s0 + int(0.25 * sr)); tk = t[s0:k1] - t[s0]
        out[s0:k1] += 0.16 * np.exp(-tk * 18) * np.sin(2 * np.pi * (50 + 60 * np.exp(-tk * 30)) * tk)
        h0 = s0 + int(beat / 2 * sr); h1 = min(n, h0 + int(0.04 * sr))
        if h0 < n: out[h0:h1] += 0.03 * rnd.standard_normal(h1 - h0) * np.exp(-np.arange(h1 - h0) / sr * 80)
    fade = np.minimum(1, np.minimum(t / 1.0, (total - t) / 1.2)); out *= fade
    out = (out / (np.abs(out).max() + 1e-9) * 0.8 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(out.tobytes())

# ---------- main ----------
def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; only_frames = "--frames" in sys.argv
    work = os.path.splitext(out)[0] + "_work"; os.makedirs(work, exist_ok=True)
    scenes = spec["scenes"]; bg = Background(spec.get("music_seed", 1))
    durs = []
    for i, s in enumerate(scenes):
        vd = tts(s["voice"], f"{work}/v{i}.wav"); s["_vd"] = vd
        durs.append(max(2.2, vd + 0.45))
    durs[-1] += 0.8
    total = sum(durs); starts = np.cumsum([0] + durs[:-1])
    TD = 0.35  # transition-in length
    files = []
    for i, s in enumerate(scenes):
        dur = durs[i]; nfr = int(round(dur * FPS)); cache = {}; trans = TRANS[i % len(TRANS)]
        prev = scenes[i - 1] if i else None; pcache = {}
        if only_frames:
            frames_to = [int(nfr * 0.25), int(nfr * 0.8)]
        else:
            tmp = f"{work}/s{i}.tmp.mp4"
            proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
            frames_to = range(nfr)
        for fi in frames_to:
            t = fi / FPS; T = starts[i] + t
            img = bg.draw(T, i)
            DRAW[s["type"]](img, s, t, dur, cache)
            # transition in: blend from previous scene's last look
            if i and t < TD:
                p = eo(t / TD)
                pimg = bg.draw(T, i - 1); DRAW[prev["type"]](pimg, prev, durs[i - 1] + t, durs[i - 1], pcache)
                if trans == "slide":
                    comp = Image.new("RGB", (W, H)); comp.paste(pimg, (int(-W * p), 0)); comp.paste(img, (int(W * (1 - p)), 0)); img = comp
                elif trans == "zoom":
                    z = img.resize((int(W * (1.25 - .25 * p)), int(H * (1.25 - .25 * p))), Image.BILINEAR)
                    z = z.crop(((z.width - W) // 2, (z.height - H) // 2, (z.width - W) // 2 + W, (z.height - H) // 2 + H))
                    img = Image.blend(pimg, z, p)
                elif trans == "wipe":
                    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle([0, H * (1 - p), W, H], fill=255); pimg.paste(img, (0, 0), m); img = pimg
                else:
                    img = Image.blend(pimg, img, p)
            draw_brand_tag(img); draw_caption(img, s["voice"], t, s["_vd"]); progress_bar(img, T, total)
            if only_frames: img.save(f"{work}/preview_{i}_{fi}.jpg", quality=88)
            else: proc.stdin.write(img.tobytes())
        if not only_frames:
            proc.stdin.close(); proc.wait()
            if proc.returncode: sys.exit(f"scene {i} failed")
            os.replace(tmp, f"{work}/s{i}.mp4"); files.append(f"{work}/s{i}.mp4")
    if only_frames: print("frames in", work); return
    with open(f"{work}/list.txt", "w") as fl:
        for f in files: fl.write(f"file '{os.path.abspath(f)}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy", f"{work}/video.mp4"], check=True)
    # voice track
    sr = 22050; vtrack = np.zeros(int(total * sr) + sr, dtype=np.float32)
    for i in range(len(scenes)):
        with wave.open(f"{work}/v{i}.wav") as w:
            sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
        s0 = int((starts[i] + 0.2) * sr); vtrack[s0:s0 + len(a)] += a
    with wave.open(f"{work}/voice.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(np.clip(vtrack, -32767, 32767).astype(np.int16).tobytes())
    music(total + 0.5, spec.get("music_seed", 1), f"{work}/music.wav")
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/video.mp4", "-i", f"{work}/voice.wav", "-i", f"{work}/music.wav",
                    "-filter_complex",
                    "[1:a]aresample=44100,highpass=f=80,acompressor=threshold=0.1:ratio=3,asplit=2[v1][vsc];"
                    "[2:a]volume=0.55[m];[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[md];"
                    "[v1][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out); print(out, round(total, 1), "s")

if __name__ == "__main__":
    main()
