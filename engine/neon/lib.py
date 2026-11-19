"""Motor del estilo \"noche neon\" de AirNaze: primitivas de escena (ver skills/airnaze-noche-neon/SKILL.md)."""
import cairo, math, random, json, os, sys, subprocess
import numpy as np
from PIL import Image, ImageFilter

W, H, FPS = 1080, 1920, 30
WORDS = []
CHUNKS = []
def load_words(path):
    """Carga words.json (palabra, inicio, fin) del episodio y prepara los subtítulos."""
    global WORDS, CHUNKS
    WORDS[:] = json.load(open(path))
    CHUNKS[:] = chunks()

# ---------------- utils ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def eio(x): x = clamp(x); return 0.5 - 0.5 * math.cos(math.pi * x)
def back(x):
    x = clamp(x); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def ramp(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def lerp(a, b, k): return a + (b - a) * k
def mix(c1, c2, k): return tuple(lerp(a, b, k) for a, b in zip(c1, c2))
def norm(w): return w.lower().strip(".,:;¿?¡!…")
def A(word, after=0.0):
    for w, s, e in WORDS:
        if s >= after - 1e-6 and norm(w) == norm(word): return s
    raise KeyError(f"palabra '{word}' no encontrada despues de {after:.2f}s")
def last_end(): return WORDS[-1][2]
def lin(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, col in stops:
        (g.add_color_stop_rgba if len(col) == 4 else g.add_color_stop_rgb)(o, *col)
    return g
def rad(cx, cy, r0, r1, stops):
    g = cairo.RadialGradient(cx, cy, r0, cx, cy, r1)
    for o, col in stops: g.add_color_stop_rgba(o, *col)
    return g
def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()
def ell(c, x, y, rx, ry):
    c.save(); c.translate(x, y); c.scale(max(rx, 0.01), max(ry, 0.01)); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()

CYAN = (0.38, 0.88, 1.0); PINK = (1.0, 0.42, 0.75); GOLD = (1.0, 0.8, 0.38); VIO = (0.66, 0.55, 1.0)
RED = (1.0, 0.35, 0.42); GRN = (0.45, 0.95, 0.6); WHITE = (1, 1, 1)

class Frame:
    def __init__(self):
        self.bs = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); self.b = cairo.Context(self.bs)
        self.gs = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); self.g = cairo.Context(self.gs)
        self.os_ = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); self.o = cairo.Context(self.os_)
        self.photos = []
    def cam(self, z=1.0, cx=W / 2, cy=H / 2, dx=0, dy=0):
        for c in (self.b, self.g):
            c.translate(cx + dx, cy + dy); c.scale(z, z); c.translate(-cx, -cy)
    def compose(self):
        def img(s):
            a = np.ndarray((H, W, 4), np.uint8, s.get_data()).copy()
            return Image.fromarray(a[:, :, [2, 1, 0, 3]], "RGBA")
        base = img(self.bs); gl = img(self.gs)
        small = gl.resize((W // 4, H // 4), Image.BILINEAR)
        b1 = small.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
        b2 = small.filter(ImageFilter.GaussianBlur(18)).resize((W, H), Image.BILINEAR)
        out = Image.alpha_composite(base, b2); out = Image.alpha_composite(out, b1); out = Image.alpha_composite(out, b1)
        out = Image.alpha_composite(out, gl)
        for ph, px, py, k in self.photos:
            if k > 0.05:
                p2 = ph.resize((max(1, int(ph.width * k)), max(1, int(ph.height * k))))
                out.alpha_composite(p2, (int(px + ph.width * (1 - k) / 2), int(py + ph.height * (1 - k) / 2)))
        out = Image.alpha_composite(out, img(self.os_))
        return out

# ---------------- captions (karaoke, top) ----------------
KEY = set()   # palabras clave del episodio (en minúsculas, sin puntuación): salen en recuadro
def chunks():
    out = []; cur = []
    tmp = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10); c = cairo.Context(tmp)
    c.select_font_face("Inter Display", 0, 1); c.set_font_size(60)
    for i, (w, s, e) in enumerate(WORDS):
        cand = cur + [i]
        width = sum(c.text_extents(WORDS[j][0]).x_advance for j in cand) + 16 * (len(cand) - 1)
        if cur and (width > W - 140 or len(cand) > 6):
            out.append(cur); cur = [i]
        else:
            cur = cand
        if w.endswith((".", "?", "…", ":")) and cur:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out
def caption(c, t, y=262):
    ch = None
    for k, idx in enumerate(CHUNKS):
        st = WORDS[idx[0]][1]; en = WORDS[CHUNKS[k + 1][0]][1] if k + 1 < len(CHUNKS) else WORDS[idx[-1]][2] + 0.6
        if st - 0.05 <= t < en: ch = idx
    if not ch: return
    c.select_font_face("Inter Display", 0, 1); size = 60; c.set_font_size(size)
    sp = 16
    ws = [c.text_extents(WORDS[j][0]).x_advance for j in ch]
    iskeys = [norm(WORDS[j][0]) in KEY or WORDS[j][0].lower().strip(".,:;¡!…") in KEY for j in ch]
    tot = sum(ws) + sp * (len(ch) - 1) + 30 * sum(iskeys); x = W / 2 - tot / 2
    active = max([j for j in ch if WORDS[j][1] <= t + 0.02] or [ch[0]])
    for j, wd, ik in zip(ch, ws, iskeys):
        w, s, e = WORDS[j]
        if ik: x += 15
        if s > t + 0.02: x += wd + sp + (15 if ik else 0); continue
        k = clamp((t - s) / 0.12)
        iskey = norm(w) in KEY or w.lower().strip(".,:;¡!…") in KEY
        if iskey:
            pad = 14
            c.save(); c.translate(x + wd / 2, y - size * 0.3); sc = 0.85 + 0.15 * back(k); c.scale(sc, sc)
            rrect(c, -wd / 2 - pad, -size * 0.62, wd + 2 * pad, size * 1.3, 14); c.set_source_rgba(0.09, 0.08, 0.25, 0.9); c.fill_preserve()
            c.set_source_rgba(0.62, 0.6, 1, 0.95); c.set_line_width(3); c.stroke(); c.restore()
        if j == active or iskey: c.set_source_rgba(1, 1, 1, k)
        else: c.set_source_rgba(0.78, 0.78, 0.88, 0.62)
        c.move_to(x, y + (1 - k) * 10); c.show_text(w); x += wd + sp + (15 if ik else 0)

def badge(c, t, t0, x, y, num, unit="", col=VIO, sub=None):
    if t < t0: return
    k = back((t - t0) / 0.35)
    c.save(); c.translate(x, y); c.scale(k, k)
    c.select_font_face("Inter Display", 0, 1); c.set_font_size(112); e1 = c.text_extents(num)
    c.set_font_size(46); e2 = c.text_extents(unit) if unit else None
    w = e1.x_advance + (e2.x_advance + 14 if unit else 0) + 56; h = 140
    rrect(c, -w / 2, -h / 2, w, h, 26); c.set_source_rgba(0.06, 0.05, 0.14, 0.85); c.fill()
    c.set_font_size(112); c.set_source_rgb(*col); c.move_to(-w / 2 + 28, 40); c.show_text(num)
    if unit: c.set_font_size(46); c.move_to(-w / 2 + 28 + e1.x_advance + 12, 40); c.show_text(unit)
    if sub:
        c.set_font_size(34); es = c.text_extents(sub); c.set_source_rgba(0.85, 0.85, 0.95, 0.85); c.move_to(-es.x_advance / 2, h / 2 + 46); c.show_text(sub)
    c.restore()

def label(c, t, t0, x, y, txt, col, size=36, anchor="c"):
    if t < t0: return
    k = back((t - t0) / 0.3)
    c.select_font_face("Inter Display", 0, 1); c.set_font_size(size); e = c.text_extents(txt)
    c.save(); c.translate(x, y); c.scale(k, k)
    ox = -e.x_advance / 2 if anchor == "c" else 0
    rrect(c, ox - 14, -size * 0.95, e.x_advance + 28, size * 1.4, 10); c.set_source_rgba(*col, 0.95); c.fill()
    c.set_source_rgb(0.07, 0.05, 0.14); c.move_to(ox, 0); c.show_text(txt); c.restore()

# ---------------- backgrounds ----------------
def bg_night(c):
    c.set_source(lin(0, 0, 0, H, [(0, (0.07, 0.05, 0.17)), (0.55, (0.15, 0.09, 0.29)), (1, (0.05, 0.03, 0.11))])); c.paint()
def bg_holo(c, t):
    c.set_source(lin(0, 0, 0, H, [(0, (0.05, 0.04, 0.16)), (0.5, (0.11, 0.07, 0.3)), (1, (0.04, 0.03, 0.12))])); c.paint()
    c.set_source(rad(W / 2, 900, 50, 900, [(0, (0.45, 0.3, 0.9, 0.28)), (1, (0.45, 0.3, 0.9, 0))])); c.paint()
    r = random.Random(7)
    for i in range(16):
        x = r.uniform(0, W); a = 0.04 + 0.03 * math.sin(t * 0.8 + i)
        c.set_source(lin(0, 300, 0, H, [(0, (0.7, 0.75, 1, 0)), (0.5, (0.7, 0.75, 1, a)), (1, (0.7, 0.75, 1, 0))])); c.rectangle(x, 300, 2, H - 300); c.fill()
    for i in range(60):
        x = r.uniform(0, W); y = (r.uniform(0, H) - t * r.uniform(6, 20)) % H
        c.set_source_rgba(0.85, 0.85, 1, r.uniform(0.15, 0.55)); c.arc(x, y, r.uniform(1, 2.6), 0, 6.3); c.fill()
def bg_sunset(c, t):
    c.set_source(lin(0, 0, 0, H, [(0, (0.1, 0.07, 0.22)), (0.22, (0.55, 0.35, 0.45)), (0.33, (0.98, 0.68, 0.45)), (0.36, (0.97, 0.92, 0.86)),
                                  (0.40, (0.35, 0.6, 0.9)), (0.7, (0.18, 0.22, 0.6)), (1, (0.1, 0.08, 0.3))])); c.paint()
    r = random.Random(5)
    for i in range(18):
        x = r.uniform(0, W)
        c.set_source(lin(0, 700, 0, H, [(0, (0.7, 0.8, 1, 0)), (0.5, (0.7, 0.8, 1, 0.06)), (1, (0.7, 0.8, 1, 0))])); c.rectangle(x, 700, 2, H - 700); c.fill()
    for i in range(50):
        c.set_source_rgba(1, 1, 1, r.uniform(0.2, 0.7) * (0.7 + 0.3 * math.sin(t * 2 + i))); c.arc(r.uniform(0, W), r.uniform(380, 1700), r.uniform(1, 2.5), 0, 6.3); c.fill()

# ---------------- bedroom ----------------
def bedroom(F, t, clock_glow=1.0, shake=0.0, head_glow=None, mouth=0.0, snore=0.0, airnaze=0.0, nose_air=0.0, mouth_air=0.0):
    c = F.b; g = F.g
    bg_night(c)
    r = random.Random(3)
    wx, wy, ww, wh = 70, 520, 330, 520
    rrect(c, wx - 14, wy - 14, ww + 28, wh + 28, 10); c.set_source_rgb(0.22, 0.13, 0.3); c.fill()
    c.rectangle(wx, wy, ww, wh); c.set_source(lin(0, wy, 0, wy + wh, [(0, (0.12, 0.12, 0.32)), (1, (0.22, 0.16, 0.42))])); c.fill()
    for i in range(30):
        c.set_source_rgba(1, 1, 1, r.uniform(0.3, 0.9) * (0.7 + 0.3 * math.sin(t * 3 + i))); c.arc(wx + r.uniform(5, ww - 5), wy + r.uniform(5, wh * 0.6), r.uniform(1, 2.5), 0, 6.3); c.fill()
    c.save(); c.rectangle(wx, wy, ww, wh); c.clip()
    g2 = rad(wx + 230, wy + 120, 0, 90, [(0, (1, 0.95, 0.8, 0.5)), (1, (1, 0.95, 0.8, 0))]); c.set_source(g2); c.arc(wx + 230, wy + 120, 90, 0, 6.3); c.fill()
    c.set_source_rgb(0.98, 0.95, 0.85); c.arc(wx + 230, wy + 120, 34, 0, 6.3); c.fill()
    c.set_source_rgb(0.12, 0.12, 0.32); c.arc(wx + 246, wy + 110, 30, 0, 6.3); c.fill()
    for i in range(9):
        bw = r.uniform(26, 46); bh = r.uniform(60, 190); bx = wx + i * 38
        c.rectangle(bx, wy + wh - bh, bw, bh); c.set_source_rgb(0.08, 0.06, 0.18); c.fill()
        for k in range(5):
            if r.random() < 0.5: c.set_source_rgba(1, 0.8, 0.4, 0.8); c.rectangle(bx + 6, wy + wh - bh + 10 + k * 28, 5, 7); c.fill()
    c.restore()
    c.set_source_rgb(0.22, 0.13, 0.3); c.rectangle(wx + ww / 2 - 6, wy, 12, wh); c.fill(); c.rectangle(wx, wy + wh / 2 - 6, ww, 12); c.fill()
    c.move_to(wx, wy + wh); c.line_to(wx + ww, wy + wh); c.line_to(wx + ww + 380, 1500); c.line_to(wx + 120, 1500); c.close_path()
    c.set_source(lin(0, wy + wh, 0, 1500, [(0, (0.6, 0.6, 1, 0.12)), (1, (0.6, 0.6, 1, 0))])); c.fill()
    c.rectangle(0, 1380, W, H - 1380); c.set_source(lin(0, 1380, 0, H, [(0, (0.12, 0.07, 0.2)), (1, (0.04, 0.02, 0.08))])); c.fill()
    # bed
    c.set_source(lin(0, 1060, 0, 1300, [(0, (0.38, 0.24, 0.14)), (1, (0.22, 0.13, 0.08))])); rrect(c, 40, 1170, 700, 150, 20); c.fill()
    c.set_source(lin(0, 860, 0, 1180, [(0, (0.45, 0.29, 0.17)), (1, (0.25, 0.15, 0.09))])); rrect(c, 690, 880, 60, 460, 18); c.fill()
    for x in (60, 700): c.set_source_rgb(0.2, 0.12, 0.07); c.rectangle(x, 1300, 30, 90); c.fill()
    br = 1 + 0.012 * math.sin(t * 1.6)
    c.save(); c.translate(350, 1200); c.scale(1, br); c.translate(-350, -1200)
    c.set_source(lin(0, 1060, 0, 1200, [(0, (0.36, 0.27, 0.62)), (1, (0.22, 0.16, 0.42))])); rrect(c, 30, 1060, 640, 140, 40); c.fill()
    c.set_source_rgba(1, 1, 1, 0.07); c.set_line_width(4)
    for k in range(5): c.move_to(80 + k * 110, 1080); c.curve_to(110 + k * 110, 1120, 90 + k * 110, 1160, 120 + k * 110, 1190); c.stroke()
    c.restore()
    c.set_source(lin(0, 1040, 0, 1110, [(0, (0.95, 0.95, 1)), (1, (0.75, 0.75, 0.88))])); rrect(c, 520, 1030, 170, 70, 35); c.fill()
    # head (profile, facing up/left)
    hx, hy = 585, 1022
    c.set_source_rgb(0.07, 0.05, 0.1); ell(c, hx, hy, 54, 46); c.fill()
    c.set_source_rgb(0.07, 0.05, 0.1); ell(c, hx - 50, hy - 16, 16, 12); c.fill()  # nose bump
    if airnaze > 0:
        pass  # (no dibujar AirNaze: regla de marca)
    if mouth > 0.05:
        c.set_source_rgb(0.02, 0.01, 0.03); ell(c, hx - 46, hy + 14, 10, 6 + 7 * mouth); c.fill()
    if head_glow:
        col, a = head_glow
        c.set_source(rad(hx - 50, hy - 14, 0, 90, [(0, (*col, 0.75 * a)), (1, (*col, 0))])); c.arc(hx - 50, hy - 14, 90, 0, 6.3); c.fill()
    for amt, tx, ty in ((nose_air, hx - 66, hy - 16), (mouth_air, hx - 60, hy + 14)):
        if amt <= 0: continue
        for k in range(7):
            p = (t * 0.9 + k / 7) % 1
            x = tx - 220 * (1 - p); y = ty - 140 * (1 - p) + math.sin(p * 7 + k) * 6
            g.set_source_rgba(*CYAN, math.sin(p * math.pi) * amt); g.arc(x, y, 7, 0, 6.3); g.fill()
    if snore > 0:
        for k in range(3):
            p = (t * 1.4 + k / 3) % 1
            g.set_source_rgba(*GOLD, (1 - p) * snore); g.set_line_width(6)
            g.arc(hx - 50, hy + 10, 40 + 160 * p, math.pi * 1.1, math.pi * 1.55); g.stroke()
    # nightstand + lamp glow + clock
    c.set_source(lin(800, 0, 1040, 0, [(0, (0.55, 0.36, 0.2)), (1, (0.36, 0.22, 0.12))])); rrect(c, 790, 1130, 250, 260, 14); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25); c.rectangle(810, 1250, 210, 4); c.fill()
    c.set_source_rgb(0.9, 0.75, 0.4); c.arc(915, 1200, 8, 0, 6.3); c.fill(); c.arc(915, 1320, 8, 0, 6.3); c.fill()
    c.set_source(lin(0, 1110, 0, 1135, [(0, (0.62, 0.42, 0.24)), (1, (0.48, 0.3, 0.17))])); rrect(c, 775, 1110, 280, 28, 8); c.fill()
    c.set_source(rad(915, 990, 0, 420, [(0, (1, 0.7, 0.35, 0.33 * clock_glow)), (1, (1, 0.6, 0.3, 0))])); c.arc(915, 990, 420, 0, 6.3); c.fill()
    sx = shake * 5 * math.sin(t * 70)
    clock(g, 915 + sx, 1010, 95, 3 + 12 / 60 + (t / 3600), shake)

def clock(gc, cx, cy, R, hours, ring=0.0):
    gc.set_source(lin(cx - R, 0, cx + R, 0, [(0, (0.95, 0.72, 0.3)), (0.5, (1, 0.88, 0.5)), (1, (0.8, 0.55, 0.2))]))
    for d in (-1, 1): gc.arc(cx + d * 62, cy - R + 5, 30, 0, 6.3); gc.fill()
    gc.arc(cx, cy, R, 0, 6.3); gc.fill()
    gc.set_source_rgb(0.99, 0.96, 0.88); gc.arc(cx, cy, R - 16, 0, 6.3); gc.fill()
    gc.set_source_rgb(0.2, 0.15, 0.1)
    for k in range(12):
        a = k / 12 * 6.283; gc.set_line_width(5); gc.move_to(cx + (R - 30) * math.sin(a), cy - (R - 30) * math.cos(a)); gc.line_to(cx + (R - 22) * math.sin(a), cy - (R - 22) * math.cos(a)); gc.stroke()
    gc.set_line_width(9); gc.set_line_cap(cairo.LINE_CAP_ROUND)
    hh = (hours % 12) / 12 * 6.283; mm = (hours * 60 % 60) / 60 * 6.283
    for ang, ln in ((hh, 0.45), (mm, 0.7)):
        gc.move_to(cx, cy); gc.line_to(cx + R * ln * math.sin(ang), cy - R * ln * math.cos(ang)); gc.stroke()
    gc.set_source_rgb(0.8, 0.55, 0.2)
    for d in (-1, 1): gc.set_line_width(10); gc.move_to(cx + d * 50, cy + R - 10); gc.line_to(cx + d * 65, cy + R + 12); gc.stroke()
    if ring > 0:
        gc.set_line_width(6)
        for k, rr in enumerate((130, 165)):
            gc.set_source_rgba(1, 0.6, 0.4, ring * (0.6 + 0.4 * math.sin(time_g[0] * 12 + k)))
            for a0 in (-2.4, -1.0): gc.arc(cx, cy, rr, a0, a0 + 0.5); gc.stroke()
time_g = [0.0]

# ---------------- holographic nose section ----------------
def wall(y, pinch):
    # half-width of a nasal channel at height y (0=top..1=bottom), pinch>0 closes the valve, <0 opens
    ys = [0.0, 0.08, 0.25, 0.5, 0.68, 0.78, 0.88, 0.95, 1.0]
    ws = [0.02, 0.33, 0.52, 0.58, 0.46, 0.30, 0.16 * (1 - pinch) + 0.01, 0.30 - 0.06 * pinch, 0.36]
    ws = [max(0.012, v) for v in ws]
    return float(np.interp(y, ys, ws))

def holo_nose(F, t, cx=540, cy=900, s=1.0, pl=0.0, pr=0.0, swell_l=0.0, swell_r=0.0, rot=0.0, air=1.0,
              turb=0.0, x_l=0.0, x_r=0.0, speed=1.0):
    c, g = F.b, F.g
    for cc in (c, g):
        cc.save(); cc.translate(cx, cy); cc.rotate(rot); cc.scale(s, s)
    Hn, Wn = 820, 600   # local size, local coords centered
    top = -Hn / 2
    # outer nose silhouette (face-front hologram)
    c.set_source(rad(0, 0, 50, 520, [(0, (0.35, 0.3, 0.9, 0.25)), (1, (0.35, 0.3, 0.9, 0))])); c.arc(0, 0, 520, 0, 6.3); c.fill()
    def outline(cc, col, lw, a):
        cc.set_source_rgba(*col, a); cc.set_line_width(lw)
        cc.move_to(-70, top); cc.curve_to(-90, top + 300, -300, top + 520, -300, top + 700)
        cc.curve_to(-300, top + 800, -200, top + 840, -120, top + 820)
        cc.curve_to(-60, top + 860, 60, top + 860, 120, top + 820)
        cc.curve_to(200, top + 840, 300, top + 800, 300, top + 700)
        cc.curve_to(300, top + 520, 90, top + 300, 70, top); cc.stroke()
    outline(g, CYAN, 4, 0.9)
    # tissue fill
    c.set_source_rgba(0.55, 0.35, 0.8, 0.18)
    c.move_to(-70, top); c.curve_to(-90, top + 300, -300, top + 520, -300, top + 700); c.curve_to(-300, top + 800, -200, top + 840, -120, top + 820)
    c.curve_to(-60, top + 860, 60, top + 860, 120, top + 820); c.curve_to(200, top + 840, 300, top + 800, 300, top + 700)
    c.curve_to(300, top + 520, 90, top + 300, 70, top); c.close_path(); c.fill()
    # channels
    y0, y1 = top + 60, top + 830
    ys = np.linspace(0, 1, 70)
    def edges(side, yy):
        p = pl if side < 0 else pr
        sw = swell_l if side < 0 else swell_r
        w = wall(yy, p) * 280
        w *= (1 - 0.85 * sw * clamp(1 - abs(yy - 0.6) / 0.55))
        inner = 22
        return inner, inner + max(4, w)
    for side in (-1, 1):
        sw = swell_l if side < 0 else swell_r
        pts_o = [(side * edges(side, yy)[1], lerp(y0, y1, yy)) for yy in ys]
        pts_i = [(side * edges(side, yy)[0], lerp(y0, y1, yy)) for yy in ys]
        c.move_to(*pts_o[0]); [c.line_to(*p) for p in pts_o[1:]]; [c.line_to(*p) for p in pts_i[::-1]]; c.close_path()
        c.set_source_rgba(0.03, 0.02, 0.1, 0.85); c.fill()
        col = mix(CYAN, PINK, clamp(sw * 1.3 + (pl if side < 0 else pr) * 0.8))
        g.set_source_rgba(*col, 0.95); g.set_line_width(5); g.set_line_join(1)
        g.move_to(*pts_o[0]); [g.line_to(*p) for p in pts_o[1:]]; g.stroke()
        # turbinates
        for yy, ry in ((0.32, 70), (0.5, 60)):
            ex = side * edges(side, yy)[1]; ey = lerp(y0, y1, yy)
            k = turb * (0.5 + 0.5 * math.sin(t * 3)) + sw
            g.set_source_rgba(*mix(PINK, (1, 0.6, 0.85), 0.3), 0.35 + 0.5 * clamp(k)); ell(g, ex + side * 18, ey, 26 + 14 * clamp(k), ry); g.fill()
        # air
        if air > 0:
            rg = random.Random(11 + side)
            for i in range(26):
                u = rg.uniform(0.15, 0.85); ph = rg.random(); v = rg.uniform(0.8, 1.2)
                yy = 1 - ((t * 0.35 * speed * v + ph) % 1)
                a_, b_ = edges(side, yy)
                if b_ - a_ < 14 and 0.2 < yy < 0.95: continue
                x = side * lerp(a_, b_, u); y = lerp(y0, y1, yy) + 60 * (1 - yy) * 0
                al = air * clamp((1 - yy) * 6) * clamp(yy * 5)
                g.set_source_rgba(*CYAN, al); g.arc(x, y + 60 * clamp((yy - 0.95) * 20), 6, 0, 6.3); g.fill()
        xk = x_l if side < 0 else x_r
        if xk > 0:
            k = back(xk); X = side * 150; Y = lerp(y0, y1, 0.62)
            g.save(); g.translate(X, Y); g.rotate(-rot); g.scale(k, k)
            g.set_source_rgba(*RED, 1); g.arc(0, 0, 46, 0, 6.3); g.fill()
            g.set_source_rgb(1, 1, 1); g.set_line_width(10); g.set_line_cap(1)
            for d in (1, -1): g.move_to(-16, -16 * d); g.line_to(16, 16 * d); g.stroke()
            g.restore()
    # septum
    g.set_source_rgba(*CYAN, 0.8); g.set_line_width(3)
    for d in (-1, 1): g.move_to(d * 22, y0 + 20); g.line_to(d * 22, y1); g.stroke()
    for cc in (c, g): cc.restore()

# ---------------- neon waves ----------------
def waves(F, t, phase_shift=0.0, bed=True, amp=300, base=1200, period=560, speed=0.0):
    c, g = F.b, F.g
    bg_sunset(c, t)
    off = t * speed
    fl = lambda x: base + amp * math.sin(((x + off) / period) * 2 * math.pi + phase_shift)
    fr = lambda x: base + amp * math.sin(((x + off) / period) * 2 * math.pi + phase_shift + math.pi)
    for f, col in ((fl, PINK), (fr, CYAN)):
        pts = [(x, f(x)) for x in range(-40, W + 41, 6)]
        for lw, a, cl in ((10, 0.9, col), (4, 1, (1, 1, 1))):
            g.set_source_rgba(*cl, a); g.set_line_width(lw); g.set_line_join(1)
            g.move_to(*pts[0]); [g.line_to(*p) for p in pts[1:]]; g.stroke()
    return fl, fr

def bed_icon(c, x, y, ang=0.0, s=1.0):
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    c.set_source(lin(0, -40, 0, 20, [(0, (0.36, 0.27, 0.62)), (1, (0.22, 0.16, 0.42))])); rrect(c, -110, -45, 220, 55, 18); c.fill()
    c.set_source_rgb(0.95, 0.95, 1); rrect(c, 50, -60, 60, 30, 14); c.fill()
    c.set_source_rgb(0.05, 0.04, 0.08); c.arc(78, -58, 22, math.pi, 2 * math.pi); c.fill()
    c.set_source(lin(0, 0, 0, 40, [(0, (0.5, 0.32, 0.18)), (1, (0.3, 0.18, 0.1))])); rrect(c, -120, 5, 240, 24, 8); c.fill(); c.rectangle(105, -70, 16, 100); c.fill()
    c.restore()

def bubble(c, t, t0, x, y):
    if t < t0: return
    k = back((t - t0) / 0.35)
    c.save(); c.translate(x, y); c.scale(k, k)
    rrect(c, -150, -95, 300, 190, 70); c.set_source_rgb(1, 1, 1); c.fill()
    c.move_to(-70, 80); c.line_to(-130, 150); c.line_to(-10, 90); c.close_path(); c.fill()
    for i in range(3):
        a = 0.35 + 0.65 * max(0, math.sin(t * 6 - i * 0.9))
        c.set_source_rgba(0.3, 0.25, 0.6, a); c.arc(-60 + 60 * i, 0, 20, 0, 6.3); c.fill()
    c.restore()

def arrow(c, x1, y1, x2, y2, col, w=14, head=44, a=1.0):
    ang = math.atan2(y2 - y1, x2 - x1)
    c.set_source_rgba(*col, a); c.set_line_width(w); c.set_line_cap(1)
    c.move_to(x1, y1); c.line_to(x2 - head * 0.6 * math.cos(ang), y2 - head * 0.6 * math.sin(ang)); c.stroke()
    c.move_to(x2, y2); c.line_to(x2 - head * math.cos(ang - 0.45), y2 - head * math.sin(ang - 0.45))
    c.line_to(x2 - head * math.cos(ang + 0.45), y2 - head * math.sin(ang + 0.45)); c.close_path(); c.fill()

def logo(c, t, t0, y=440, size=120):
    if t < t0: return
    k = back((t - t0) / 0.4)
    c.select_font_face("Inter Display", 0, 1); c.set_font_size(size); e = c.text_extents("AirNaze")
    c.save(); c.translate(W / 2, y); c.scale(k, k); c.set_source_rgb(1, 1, 1); c.move_to(-e.x_advance / 2, e.height / 2 - 6); c.show_text("AirNaze"); c.restore()

def pill(c, t, t0, txt, y, col=GRN):
    if t < t0: return
    k = back((t - t0) / 0.3) * (1 + 0.04 * math.sin(t * 8))
    c.select_font_face("Inter Display", 0, 1); c.set_font_size(64); e = c.text_extents(txt)
    c.save(); c.translate(W / 2, y); c.scale(k, k)
    rrect(c, -e.x_advance / 2 - 60, -68, e.x_advance + 120, 132, 66); c.set_source_rgb(*col); c.fill()
    c.set_source_rgb(0.04, 0.1, 0.07); c.move_to(-e.x_advance / 2, 23); c.show_text(txt); c.restore()


# ---------------- escenas añadidas para la fábrica diaria ----------------
def comment_arrow(c, t, t0, y=1250):
    """Flecha verde que rebota hacia el icono de comentarios (lado derecho) + 'comenta aquí'."""
    if t < t0: return
    a = clamp((t - t0) / 0.3); b = 18 * math.sin(t * 9)
    arrow(c, 640 + b, y, 990 + b, y, GRN, 22, 70, a)
    c.select_font_face("Inter Display", 0, 1); c.set_font_size(62); c.set_source_rgba(1, 1, 1, a)
    e = c.text_extents("comenta aquí"); c.move_to(815 - e.x_advance / 2, y + 110); c.show_text("comenta aquí")

def stat(F, t, t0, value, label_txt, col=VIO, y=900):
    """Dato grande (solo datos ciertos y generales) sobre fondo holográfico, con anillo de neón que gira."""
    bg_holo(F.b, t)
    k = back((t - t0) / 0.4)
    g = F.g; g.save(); g.translate(W / 2, y); g.scale(k, k)
    for i, (r, lw, a) in enumerate(((330, 6, 0.9), (360, 3, 0.5))):
        g.set_source_rgba(*(CYAN if i == 0 else PINK), a); g.set_line_width(lw)
        st = (t - t0) * (0.8 if i == 0 else -0.5)
        g.arc(0, 0, r, st, st + 4.6); g.stroke()
    g.restore()
    c = F.o; c.save(); c.translate(W / 2, y); c.scale(k, k)
    c.select_font_face("Inter Display", 0, 1); c.set_font_size(190); e = c.text_extents(value)
    c.set_source_rgb(*col); c.move_to(-e.x_advance / 2, 65); c.show_text(value)
    c.set_font_size(50); e = c.text_extents(label_txt); c.set_source_rgba(1, 1, 1, 0.92); c.move_to(-e.x_advance / 2, 170); c.show_text(label_txt)
    c.restore()

def _photo(path):
    try:
        im = Image.open(path).convert("RGBA"); return im
    except Exception:
        return None

def product_card(F, t, t0, img=None, tag="AirNaze", items=(), y=930):
    """Única aparición de AirNaze. Con foto real (assets/product/...) dentro de un marco de neón;
    sin foto: nombre + icono de nariz con aire. NUNCA dibuja el producto."""
    bg_holo(F.b, t)
    k = back((t - t0) / 0.45)
    c, g = F.o, F.g
    cw, ch = 700, 700
    x0, y0 = W / 2 - cw / 2, y - ch / 2
    g.save(); g.translate(W / 2, y); g.scale(k, k); g.translate(-W / 2, -y)
    rrect(g, x0, y0, cw, ch, 48); g.set_source_rgba(*CYAN, 0.9); g.set_line_width(6); g.stroke()
    g.restore()
    ph = _photo(img) if img else None
    if ph is not None:
        ph.thumbnail((cw - 40, ch - 40))
        F.photos.append((ph, int(W / 2 - ph.width / 2), int(y - ph.height / 2), k))
    else:
        c.save(); c.translate(W / 2, y); c.scale(k, k)
        rrect(c, -cw / 2, -ch / 2, cw, ch, 48); c.set_source_rgba(0.08, 0.07, 0.2, 0.85); c.fill()
        # icono nariz + aire (no es el producto)
        c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(14); c.set_line_cap(1); c.set_line_join(1)
        c.move_to(-20, -210); c.curve_to(-30, -120, -110, -60, -110, 0); c.curve_to(-110, 50, -60, 60, -30, 40)
        c.move_to(20, -210); c.curve_to(30, -120, 110, -60, 110, 0); c.curve_to(110, 50, 60, 60, 30, 40); c.stroke()
        for i in range(3):
            p = ((t - t0) * 0.8 + i / 3) % 1
            c.set_source_rgba(*CYAN, math.sin(p * math.pi)); c.arc(-60 + 60 * i, 200 - 150 * p, 12, 0, 6.3); c.fill()
        c.select_font_face("Inter Display", 0, 1); c.set_font_size(120); e = c.text_extents("AirNaze")
        c.set_source_rgb(1, 1, 1); c.move_to(-e.x_advance / 2, 250); c.show_text("AirNaze")
        c.restore()
    if tag and ph is not None:
        logo(c, t, t0, y=y - ch / 2 - 90, size=96)
    for i, it in enumerate(items):
        label(c, t, t0 + 0.5 + 0.35 * i, W / 2, y + ch / 2 + 90 + i * 78, it, (0.62, 0.58, 1), size=40)

def close_cta(F, t, t0, question, t_arrow, scene_draw=None):
    """Cierre: lo que se ve detrás (scene_draw opcional) + bocadillo + pregunta grande + flecha a comentarios."""
    if scene_draw: scene_draw(F, t, t0)
    else: bg_holo(F.b, t)
    bubble(F.o, t, t0 + 0.2, 790, 600)
    if question:
        k = back((t - t0 - 0.3) / 0.35)
        c = F.o; c.save(); c.translate(W / 2, 980); c.scale(k, k)
        c.select_font_face("Inter Display", 0, 1); size = 84; c.set_font_size(size)
        words = question.split(); lines = []; cur = ""
        for w in words:
            tst = (cur + " " + w).strip()
            if c.text_extents(tst).x_advance > W - 160 and cur: lines.append(cur); cur = w
            else: cur = tst
        lines.append(cur)
        for i, ln in enumerate(lines):
            e = c.text_extents(ln); c.set_source_rgb(1, 1, 1); c.move_to(-e.x_advance / 2, i * (size + 14)); c.show_text(ln)
        c.restore()
    comment_arrow(F.o, t, t_arrow)
