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


# ---------------- añadidas 20-11-2026: torso en holograma y cuentarrevoluciones ----------------
def holo_torso(F, t, cx=540, cy=1000, s=1.0, chest=0.0, belly=0.0, shoulders=0.0, dia=0.0,
               hand=0.0, tint=None, desk=0.0, lamp=0.0, x_sh=0.0, ok_hand=0.0):
    """Busto en holograma de perfil frontal: pulmones (se llenan con `chest`), diafragma (baja con `belly`,
    brilla con `dia`), barriga que se abomba (`belly`), hombros que suben (`shoulders`), mano en la barriga (`hand`).
    `tint` colorea el contorno (CYAN tranquilo, RED estrés). `desk`: mesa con portátil delante; `lamp`: luz cálida de casa."""
    c, g = F.b, F.g
    col = tint or CYAN
    if lamp > 0:
        c.set_source(rad(860, 520, 20, 700, [(0, (1, 0.72, 0.38, 0.45 * lamp)), (1, (1, 0.6, 0.3, 0))])); c.paint()
        g.set_source_rgba(*GOLD, 0.9 * lamp); ell(g, 860, 520, 46, 46); g.fill()
        g.set_source_rgba(*GOLD, 0.6 * lamp); g.set_line_width(4); g.move_to(860, 300); g.line_to(860, 474); g.stroke()
    for cc in (c, g):
        cc.save(); cc.translate(cx, cy); cc.scale(s, s)
    c.set_source(rad(0, -60, 40, 620, [(0, (*col, 0.20)), (1, (*col, 0))])); c.arc(0, -60, 620, 0, 6.3); c.fill()
    sh = -40 * shoulders
    bl = 70 * belly
    # head + neck
    g.set_source_rgba(*col, 0.95); g.set_line_width(5)
    ell(g, 0, -560 + sh * 0.5, 105, 125); g.stroke()
    def body(cc):
        cc.move_to(-55, -435 + sh * 0.5); cc.line_to(-60, -380 + sh)
        cc.curve_to(-170, -365 + sh, -290, -350 + sh, -300, -260 + sh)
        cc.curve_to(-305, -120, -250, 60, -240, 200)
        cc.curve_to(-235 - bl * 0.4, 330, -220 - bl, 420, -210, 520)
        cc.line_to(210, 520)
        cc.curve_to(220 + bl, 420, 235 + bl * 0.4, 330, 240, 200)
        cc.curve_to(250, 60, 305, -120, 300, -260 + sh)
        cc.curve_to(290, -350 + sh, 170, -365 + sh, 60, -380 + sh); cc.line_to(55, -435 + sh * 0.5)
    c.set_source_rgba(0.5, 0.35, 0.85, 0.16); body(c); c.close_path(); c.fill()
    g.set_source_rgba(*col, 0.95); g.set_line_width(5); g.set_line_join(1); body(g); g.stroke()
    # lungs
    k = 0.82 + 0.22 * chest
    for side in (-1, 1):
        g.save(); g.translate(side * 115, -120 + sh * 0.6); g.scale(k, k)
        g.move_to(side * -40, -170); g.curve_to(side * 90, -190, side * 120, -20, side * 110, 120)
        g.curve_to(side * 100, 170, side * -10, 175, side * -50, 140); g.curve_to(side * -70, 40, side * -60, -100, side * -40, -170)
        g.set_source_rgba(*mix(col, PINK, 0.35), 0.18 + 0.25 * chest); g.fill_preserve()
        g.set_source_rgba(*mix(col, (1, 1, 1), 0.2), 0.85); g.set_line_width(4); g.stroke()
        g.restore()
    # diaphragm dome
    dy = 40 + 55 * belly
    dc = mix(col, GRN, clamp(dia))
    for lw, a in ((14, 0.35 + 0.4 * dia), (5, 1)):
        g.set_source_rgba(*dc, a); g.set_line_width(lw); g.set_line_cap(1)
        g.move_to(-235, 95 + dy); g.curve_to(-160, -10 + dy * 0.6, 160, -10 + dy * 0.6, 235, 95 + dy); g.stroke()
    # belly air dots
    if belly > 0.05:
        r = random.Random(3)
        for i in range(14):
            x = r.uniform(-150, 150); y = r.uniform(240, 460)
            g.set_source_rgba(*GRN, 0.5 * belly * (0.5 + 0.5 * math.sin(t * 3 + i))); g.arc(x, y, 5, 0, 6.3); g.fill()
    # hand on belly
    if hand > 0:
        hy = 360 - 30 * belly; hx = 40 + bl * 0.3
        a = clamp(hand)
        c.set_source_rgba(0.98, 0.78, 0.6, 0.85 * a); rrect(c, hx - 150, hy - 70, 230, 140, 60); c.fill()
        c.set_source_rgba(0.98, 0.78, 0.6, 0.85 * a); rrect(c, hx + 40, hy - 30, 200, 70, 34); c.fill()
        g.set_source_rgba(*GOLD, a); g.set_line_width(4)
        rrect(g, hx - 150, hy - 70, 230, 140, 60); g.stroke()
        for i in range(4):
            g.move_to(hx - 120 + 50 * i, hy - 60); g.line_to(hx - 120 + 50 * i, hy - 20); g.stroke()
        if ok_hand > 0:
            kk = back(ok_hand); g.save(); g.translate(hx - 190, hy); g.scale(kk, kk)
            g.set_source_rgba(*GRN, 1); g.arc(0, 0, 46, 0, 6.3); g.fill()
            g.set_source_rgb(0.04, 0.1, 0.07); g.set_line_width(10); g.set_line_cap(1)
            g.move_to(-20, 2); g.line_to(-5, 18); g.line_to(22, -16); g.stroke(); g.restore()
    if x_sh > 0:
        kk = back(x_sh)
        for side in (-1, 1):
            g.save(); g.translate(side * 250, -420 + sh); g.scale(kk, kk)
            g.set_source_rgba(*RED, 1); g.arc(0, 0, 42, 0, 6.3); g.fill()
            g.set_source_rgb(1, 1, 1); g.set_line_width(10); g.set_line_cap(1)
            for d in (1, -1): g.move_to(-15, -15 * d); g.line_to(15, 15 * d); g.stroke()
            g.restore()
    for cc in (c, g): cc.restore()
    if desk > 0:
        a = clamp(desk)
        c.set_source_rgba(0.18, 0.12, 0.3, 0.97 * a); c.rectangle(0, 1480, W, H - 1480); c.fill()
        g.set_source_rgba(*GOLD, 0.7 * a); g.set_line_width(4); g.move_to(0, 1480); g.line_to(W, 1480); g.stroke()
        c.set_source_rgba(0.12, 0.1, 0.22, a); c.move_to(300, 1480); c.line_to(780, 1480); c.line_to(740, 1270); c.line_to(340, 1270); c.close_path(); c.fill()
        c.set_source(rad(540, 1360, 10, 380, [(0, (0.6, 0.85, 1, 0.45 * a)), (1, (0.6, 0.85, 1, 0))])); c.arc(540, 1360, 380, 0, 6.3); c.fill()
        g.set_source_rgba(0.7, 0.9, 1, 0.9 * a); g.set_line_width(3); g.move_to(340, 1270); g.line_to(740, 1270); g.stroke()

def rev_gauge(F, t, t0, val, cx=540, cy=980, R=330, label_txt=None):
    """Cuentarrevoluciones de neón: `val` 0..1 (zona roja arriba). Metáfora de ir 'pasado de vueltas'."""
    bg_holo(F.b, t)
    g, o = F.g, F.o
    k = back((t - t0) / 0.4)
    g.save(); g.translate(cx, cy); g.scale(k, k)
    a0, a1 = math.pi * 0.8, math.pi * 2.2
    for i in range(40):
        u = i / 39; a = lerp(a0, a1, u)
        colr = mix(CYAN, RED, clamp((u - 0.45) / 0.4))
        g.set_source_rgba(*colr, 0.9); g.set_line_width(8 if i % 5 == 0 else 4)
        r1 = R - (48 if i % 5 == 0 else 26)
        g.move_to(r1 * math.cos(a), r1 * math.sin(a)); g.line_to(R * math.cos(a), R * math.sin(a)); g.stroke()
    jit = 0.02 * math.sin(t * 23) * clamp(val)
    a = lerp(a0, a1, clamp(val + jit))
    g.set_source_rgba(*mix(CYAN, RED, clamp(val)), 1); g.set_line_width(12); g.set_line_cap(1)
    g.move_to(0, 0); g.line_to((R - 70) * math.cos(a), (R - 70) * math.sin(a)); g.stroke()
    g.set_source_rgba(1, 1, 1, 0.95); g.arc(0, 0, 24, 0, 6.3); g.fill()
    g.restore()
    if label_txt:
        o.select_font_face("Inter Display", 0, 1); o.set_font_size(54); e = o.text_extents(label_txt)
        o.set_source_rgba(1, 1, 1, clamp((t - t0) / 0.3)); o.move_to(cx - e.x_advance / 2, cy + R * 0.55); o.show_text(label_txt)


# ---------------- añadidas 21-11-2026: mancuerna, pulso, ruta gimnasio→cama, ducha y piernas en la pared ----------------
def dumbbell(g, x, y, s=1.0, ang=0.0, col=None, a=1.0):
    """Mancuerna de neón (contorno)."""
    col = col or PINK
    g.save(); g.translate(x, y); g.rotate(ang); g.scale(s, s)
    g.set_source_rgba(*col, a); g.set_line_width(7); g.set_line_join(1)
    rrect(g, -70, -9, 140, 18, 9); g.stroke()
    for sd in (-1, 1):
        rrect(g, sd * 70 - (26 if sd > 0 else 0) + (0 if sd > 0 else 0), -60, 26, 120, 10); g.stroke()
        rrect(g, sd * 104 - 13, -42, 26, 84, 10); g.stroke()
    g.restore()

def pulse_line(F, t, y=1250, rate=1.6, amp=1.0, col=None, x0=60, x1=1020, a=1.0):
    """Línea de pulso de neón que avanza: `rate` = latidos por segundo (visual), `amp` = altura del pico."""
    g = F.g; col = col or RED
    pts = []
    n = 220
    for i in range(n + 1):
        x = lerp(x0, x1, i / n)
        ph = ((x - x0) / 260.0 * rate * 0.6 - t * rate) % 1.0
        if ph < 0.06: v = -ph / 0.06 * 0.25
        elif ph < 0.10: v = lerp(-0.25, 1.0, (ph - 0.06) / 0.04)
        elif ph < 0.15: v = lerp(1.0, -0.55, (ph - 0.10) / 0.05)
        elif ph < 0.20: v = lerp(-0.55, 0, (ph - 0.15) / 0.05)
        elif 0.32 < ph < 0.42: v = 0.18 * math.sin((ph - 0.32) / 0.1 * math.pi)
        else: v = 0
        pts.append((x, y - v * 150 * amp))
    for lw, aa in ((16, 0.25), (6, 1.0)):
        g.set_source_rgba(*col, aa * a); g.set_line_width(lw); g.set_line_join(1); g.set_line_cap(1)
        g.move_to(*pts[0])
        for p in pts[1:]: g.line_to(*p)
        g.stroke()

def route(F, t, p, brake=0.0, y=1000):
    """Carretera de neón del gimnasio (mancuerna) a la cama. `p` 0..1 = dónde va el punto;
    `brake` 0..1 = tramo de frenada (de rosa a cian) antes de la cama."""
    bg_holo(F.b, t)
    g, c = F.g, F.b
    xa, xb = 150, 930
    c.set_source_rgba(0.12, 0.09, 0.3, 0.9); rrect(c, xa - 40, y - 55, xb - xa + 80, 110, 55); c.fill()
    for i in range(14):
        x = lerp(xa + 60, xb - 60, i / 13)
        u = (x - xa) / (xb - xa)
        col = mix(PINK, CYAN, clamp((u - (1 - brake * 0.55)) / 0.12)) if brake > 0 else PINK
        g.set_source_rgba(*col, 0.8); g.set_line_width(6); g.move_to(x - 18, y); g.line_to(x + 18, y); g.stroke()
    if brake > 0:
        xs = lerp(xb, xa, brake * 0.55)
        g.set_source_rgba(*CYAN, 0.9 * brake); g.set_line_width(5)
        rrect(g, xs, y - 70, xb - xs + 30, 140, 40); g.stroke()
    dumbbell(g, xa - 10, y - 190, 0.85, 0.0, PINK)
    bed_icon(c, xb - 10, y - 160, 0.0, 0.95)
    g.set_source_rgba(*GOLD, 0.8); g.set_line_width(4); g.arc(xb - 80, y - 290, 26, 0.6, 5.2); g.stroke()
    px = lerp(xa, xb, clamp(p))
    hot = 1 - clamp(brake * 1.2) if p > 0.75 else 1
    col = mix(CYAN, RED, hot)
    for k in range(6):
        g.set_source_rgba(*col, 0.25 * (1 - k / 6)); g.arc(px - k * 34 * (1 - brake * 0.7), y, 26 - k * 2, 0, 6.3); g.fill()
    g.set_source_rgba(*col, 1); g.arc(px, y, 30, 0, 6.3); g.fill()

def shower_lamp(F, t, steam=1.0, dim=0.0):
    """Baño de noche: ducha con vapor templado a la izquierda y lámpara que baja la luz a la derecha."""
    c, g = F.b, F.g
    bg_night(c)
    warm = 1 - 0.6 * dim
    c.set_source(rad(800, 640, 20, 760, [(0, (1, 0.72, 0.38, 0.55 * warm)), (1, (1, 0.6, 0.3, 0))])); c.paint()
    # ducha
    g.set_source_rgba(*CYAN, 0.95); g.set_line_width(7); g.set_line_cap(1)
    g.move_to(180, 1500); g.line_to(180, 620); g.curve_to(180, 560, 230, 540, 300, 560); g.line_to(330, 600); g.stroke()
    rrect(g, 280, 596, 120, 34, 14); g.stroke()
    r = random.Random(11)
    for i in range(36):
        x = r.uniform(290, 395); sp = r.uniform(500, 760)
        yy = 650 + ((t * sp + r.uniform(0, 900)) % 850)
        g.set_source_rgba(*CYAN, 0.55); g.set_line_width(3); g.move_to(x + (yy - 650) * 0.05, yy); g.line_to(x + (yy - 650) * 0.05 + 2, yy + 22); g.stroke()
    for i in range(9):
        ph = (t * 0.22 + i / 9) % 1
        x = 340 + 120 * math.sin(i * 2.1 + t * 0.7) * ph; yy = 1400 - 820 * ph
        c.set_source_rgba(1, 0.92, 0.85, 0.22 * steam * math.sin(ph * math.pi)); c.arc(x, yy, 60 + 90 * ph, 0, 6.3); c.fill()
    # lámpara
    g.set_source_rgba(*GOLD, 0.7); g.set_line_width(5); g.move_to(800, 1500); g.line_to(800, 760); g.stroke()
    g.move_to(700, 760); g.line_to(900, 760); g.line_to(850, 620); g.line_to(750, 620); g.close_path()
    g.set_source_rgba(*GOLD, 0.25 + 0.6 * warm); g.fill_preserve(); g.set_source_rgba(*GOLD, 0.95); g.stroke()
    c.set_source_rgba(0.14, 0.1, 0.26, 1); c.rectangle(0, 1500, W, H - 1500); c.fill()
    g.set_source_rgba(*VIO, 0.6); g.set_line_width(3); g.move_to(0, 1500); g.line_to(W, 1500); g.stroke()

def legs_wall(F, t, breath=0.0, timer=None, cx=540, floor=1330, s=1.0, nose_air=0.0, calm=0.0):
    """Figura de neón tumbada boca arriba con las piernas apoyadas en la pared (derecha), cojín, y
    temporizador de 60 s opcional (`timer` 0..1 transcurrido). `breath` 0..1 hincha la barriga; `nose_air` aire cian por la nariz."""
    c, g = F.b, F.g
    bg_night(c)
    c.set_source(rad(260, 600, 20, 800, [(0, (1, 0.7, 0.38, 0.25)), (1, (1, 0.6, 0.3, 0))])); c.paint()
    wx = 860
    c.set_source(lin(wx, 0, W, 0, [(0, (0.2, 0.14, 0.38)), (1, (0.14, 0.1, 0.28))])); c.rectangle(wx, 380, W - wx, floor - 380); c.fill()
    c.set_source_rgba(0.13, 0.09, 0.26, 1); c.rectangle(0, floor, W, H - floor); c.fill()
    g.set_source_rgba(*VIO, 0.8); g.set_line_width(4); g.move_to(0, floor); g.line_to(wx, floor); g.line_to(wx, 380); g.stroke()
    col = mix(PINK, CYAN, clamp(calm))
    g.save(); g.translate(cx, floor); g.scale(s, s); g.translate(-cx, -floor)
    # esterilla
    c.set_source_rgba(0.3, 0.22, 0.55, 0.9); rrect(c, 70, floor - 26, 790, 26, 12); c.fill()
    # cabeza y cuerpo tumbado
    hy = floor - 85
    g.set_source_rgba(*col, 0.95); g.set_line_width(7); g.set_line_cap(1); g.set_line_join(1)
    ell(g, 170, hy, 58, 52); g.stroke()
    bb = 16 * breath
    g.move_to(228, hy + 10); g.curve_to(330, hy - 30, 470, hy - 44 - bb, 560, hy - 30 - bb)
    g.curve_to(640, hy - 20, 700, hy - 10, wx - 70, hy - 4)
    g.move_to(228, hy + 40); g.line_to(wx - 70, floor - 34); g.stroke()
    # brazos relajados
    g.move_to(320, hy - 10); g.curve_to(380, floor - 20, 450, floor - 22, 500, floor - 30); g.stroke()
    # piernas en la pared
    g.move_to(wx - 70, hy - 4); g.curve_to(wx - 30, hy - 10, wx - 30, hy - 60, wx - 36, hy - 110)
    g.line_to(wx - 30, 520); g.move_to(wx - 70, floor - 34); g.curve_to(wx - 10, floor - 40, wx - 6, hy - 80, wx - 8, hy - 130); g.line_to(wx - 4, 520); g.stroke()
    g.move_to(wx - 30, 520); g.line_to(wx - 70, 470); g.move_to(wx - 4, 520); g.line_to(wx - 34, 462); g.stroke()
    # aire por la nariz
    if nose_air > 0:
        for i in range(4):
            p = (t * 0.45 + i / 4) % 1
            g.set_source_rgba(*CYAN, nose_air * math.sin(p * math.pi)); g.arc(150 - 10 * i, hy - 70 - 220 * p, 10 - 1.5 * i, 0, 6.3); g.fill()
    g.restore()
    if timer is not None:
        tx, ty, R = 360, 760, 150
        g.set_source_rgba(*VIO, 0.35); g.set_line_width(14); g.arc(tx, ty, R, 0, 6.3); g.stroke()
        g.set_source_rgba(*GRN, 1); g.set_line_width(14); g.set_line_cap(1)
        g.arc(tx, ty, R, -math.pi / 2, -math.pi / 2 + 2 * math.pi * clamp(timer)); g.stroke()
        o = F.o; o.select_font_face("Inter Display", 0, 1); o.set_font_size(110)
        txt = str(max(0, int(round(60 * (1 - clamp(timer)))))); e = o.text_extents(txt)
        o.set_source_rgb(1, 1, 1); o.move_to(tx - e.x_advance / 2, ty + 38); o.show_text(txt)
        o.set_font_size(34); e = o.text_extents("SEG"); o.set_source_rgba(1, 1, 1, 0.8); o.move_to(tx - e.x_advance / 2, ty + 90); o.show_text("SEG")


def level_stairs(F, t, active=1, jump=0.0, cx=540, base=1250, s=1.0, cols=None):
    """Escalera de neón de 3 peldaños (niveles 1·2·3). `active` = peldaño iluminado (1–3, admite decimales:
    se mueve una bola de luz entre peldaños). `jump` > 0 dibuja un salto en arco del 1 al 3 (el error)."""
    g, c = F.g, F.o
    cols = cols or (GRN, GOLD, RED)
    sw, sh = 250 * s, 170 * s
    x0 = cx - 1.5 * sw
    for i in range(3):
        x = x0 + i * sw; y = base - (i + 1) * sh
        lit = clamp(1 - abs(active - (i + 1)))
        col = cols[i]
        rrect(g, x + 8, y, sw - 16, (i + 1) * sh, 18)
        g.set_source_rgba(*col, 0.10 + 0.25 * lit); g.fill_preserve()
        g.set_source_rgba(*col, 0.45 + 0.55 * lit); g.set_line_width(5 + 4 * lit); g.stroke()
        c.select_font_face("Inter Display", 0, 1); c.set_font_size(96 * s); e = c.text_extents(str(i + 1))
        c.set_source_rgba(1, 1, 1, 0.55 + 0.45 * lit); c.move_to(x + sw / 2 - e.x_advance / 2, y + 120 * s); c.show_text(str(i + 1))
    # bola de luz sobre el peldaño activo
    k = clamp(active, 1, 3) - 1
    bx = x0 + sw / 2 + k * sw; by = base - (k + 1) * sh - 50 * s - 10 * abs(math.sin(t * 4))
    if jump > 0:
        p = clamp(jump)
        bx = lerp(x0 + sw / 2, x0 + 2.5 * sw, p); by = lerp(base - sh, base - 3 * sh, p) - 50 * s - 260 * s * math.sin(p * math.pi)
        g.set_source_rgba(*RED, 0.6); g.set_line_width(5); g.set_dash([18, 14])
        for i in range(41):
            q = i / 40 * p
            xx = lerp(x0 + sw / 2, x0 + 2.5 * sw, q); yy = lerp(base - sh, base - 3 * sh, q) - 50 * s - 260 * s * math.sin(q * math.pi)
            (g.move_to if i == 0 else g.line_to)(xx, yy)
        g.stroke(); g.set_dash([])
    g.set_source(rad(bx, by, 4, 70 * s, [(0, (1, 1, 1, 1)), (0.3, (*CYAN, 0.8)), (1, (*CYAN, 0))])); g.arc(bx, by, 70 * s, 0, 6.3); g.fill()


def checklist(F, t, items, ts, cx=540, y0=760, gap=200, col=None):
    """Lista de pasos de neón: cada fila entra en su tiempo `ts[i]` y se marca con ✓ que se dibuja."""
    g, c = F.g, F.o; col = col or GRN
    for i, (txt, t0) in enumerate(zip(items, ts)):
        if t < t0 - 0.05: 
            rrect(g, cx - 430, y0 + i * gap - 70, 860, 140, 30); g.set_source_rgba(*VIO, 0.25); g.set_line_width(3); g.stroke(); continue
        k = back((t - t0) / 0.35); y = y0 + i * gap
        g.save(); g.translate(cx, y); g.scale(k, k)
        rrect(g, -430, -70, 860, 140, 30); g.set_source_rgba(*col, 0.12); g.fill_preserve(); g.set_source_rgba(*col, 0.9); g.set_line_width(5); g.stroke()
        g.arc(-350, 0, 44, 0, 6.3); g.set_source_rgba(*col, 0.9); g.set_line_width(5); g.stroke()
        p = ramp(t, t0 + 0.15, t0 + 0.55)
        if p > 0:
            pts = [(-372, 2), (-356, 20), (-326, -18)]
            g.set_line_width(9); g.set_line_cap(1); g.set_line_join(1); g.move_to(*pts[0])
            if p < 0.4: g.line_to(lerp(pts[0][0], pts[1][0], p / 0.4), lerp(pts[0][1], pts[1][1], p / 0.4))
            else: g.line_to(*pts[1]); q = (p - 0.4) / 0.6; g.line_to(lerp(pts[1][0], pts[2][0], q), lerp(pts[1][1], pts[2][1], q))
            g.stroke()
        g.restore()
        c.save(); c.translate(cx, y); c.scale(k, k)
        c.select_font_face("Inter Display", 0, 1); c.set_font_size(52); c.set_source_rgb(1, 1, 1)
        c.move_to(-270, 18); c.show_text(txt); c.restore()


def sneaker(g, x, y, s=1.0, col=None, a=1.0, ang=0.0):
    """Zapatilla de neón (contorno sencillo con cordones)."""
    col = col or CYAN
    g.save(); g.translate(x, y); g.rotate(ang); g.scale(s, s)
    g.set_source_rgba(*col, a); g.set_line_width(8); g.set_line_join(1); g.set_line_cap(1)
    g.move_to(-200, 40); g.line_to(-200, -60); g.curve_to(-190, -110, -120, -110, -100, -70)
    g.curve_to(-60, -40, 0, -30, 60, -10); g.curve_to(150, 10, 210, 20, 210, 50); g.line_to(210, 70)
    g.line_to(-200, 70); g.close_path(); g.stroke()
    g.move_to(-200, 40); g.line_to(210, 40); g.stroke()
    for i in range(4):
        xx = -80 + i * 38; g.move_to(xx, -60 + i * 9); g.line_to(xx + 26, -36 + i * 9); g.stroke()
    g.restore()

# ---------------- añadidas 23-11-2026: tubo de aire en dos tomas y cierre de "guárdalo" ----------------
def air_tube(F, t, level, marks=0.0, out=0.0, cx=540, top=560, bot=1420, wid=260):
    """Tubo de cristal de neón que se llena de aire cian. `level` 0..1 (relleno); `marks` 0..1 muestra las
    marcas de la 1ª toma (65 %) y la 2ª (100 %); `out` 0..1 = soplo largo saliendo por arriba (exhalación)."""
    c, g = F.b, F.g
    bg_holo(c, t)
    x0 = cx - wid / 2; h = bot - top
    c.set_source_rgba(0.08, 0.07, 0.2, 0.85); rrect(c, x0, top, wid, h, wid / 2); c.fill()
    lv = clamp(level)
    if lv > 0.005:
        yl = bot - h * lv + 6 * math.sin(t * 4)
        c.save(); rrect(c, x0 + 10, top + 10, wid - 20, h - 20, wid / 2 - 10); c.clip()
        c.set_source(lin(0, yl, 0, bot, [(0, (0.55, 0.95, 1.0, 0.95)), (1, (0.2, 0.45, 0.95, 0.85))])); c.rectangle(x0, yl, wid, bot - yl); c.fill()
        r = random.Random(5)
        for i in range(14):
            bx = x0 + 30 + r.uniform(0, wid - 60); sp = r.uniform(60, 140)
            by = bot - ((t * sp + r.uniform(0, h)) % max(1, bot - yl))
            c.set_source_rgba(1, 1, 1, 0.35); c.arc(bx, by, r.uniform(5, 11), 0, 6.3); c.fill()
        c.restore()
        g.set_source_rgba(1, 1, 1, 0.9); g.set_line_width(5); g.move_to(x0 + 18, yl); g.line_to(x0 + wid - 18, yl); g.stroke()
    for lw, a in ((18, 0.25), (6, 0.95)):
        g.set_source_rgba(*CYAN, a); g.set_line_width(lw); rrect(g, x0, top, wid, h, wid / 2); g.stroke()
    if marks > 0:
        for frac, txt, col in ((0.65, "1ª TOMA", CYAN), (0.97, "2ª TOMA", GRN)):
            y = bot - h * frac
            g.set_source_rgba(*col, marks); g.set_line_width(5); g.move_to(x0 + wid + 10, y); g.line_to(x0 + wid + 60, y); g.stroke()
            c2 = F.o; c2.select_font_face("Inter Display", 0, 1); c2.set_font_size(40); c2.set_source_rgba(*col, marks)
            c2.move_to(x0 + wid + 74, y + 14); c2.show_text(txt)
    if out > 0:
        for i in range(7):
            p = (t * 0.35 + i / 7) % 1
            x = cx + 30 * math.sin(p * 5 + i); y = top - 40 - 320 * p
            g.set_source_rgba(*CYAN, out * 0.7 * math.sin(p * math.pi)); g.set_line_width(8); g.set_line_cap(1)
            g.move_to(x - 70 * (1 - p * 0.4), y); g.curve_to(x - 20, y - 30, x + 20, y + 30, x + 70 * (1 - p * 0.4), y); g.stroke()

def save_cta(F, t, t0, t_arrow, scene_draw=None, txt="guárdalo"):
    """Cierre de CTA 'guardar': marcapáginas de neón que late + flecha hacia el botón de guardar (abajo derecha)."""
    if scene_draw: scene_draw(F, t, t0)
    else: bg_holo(F.b, t)
    if t < t0 + 0.15: return
    k = back((t - t0 - 0.15) / 0.4) * (1 + 0.05 * math.sin(t * 6))
    c = F.o; c.save(); c.translate(W / 2, 860); c.scale(k, k)
    c.set_source(rad(0, 0, 10, 330, [(0, (0.45, 0.95, 0.6, 0.35)), (1, (0.45, 0.95, 0.6, 0))])); c.arc(0, 0, 330, 0, 6.3); c.fill()
    c.move_to(-120, -170); c.line_to(120, -170); c.line_to(120, 180); c.line_to(0, 90); c.line_to(-120, 180); c.close_path()
    c.set_source_rgba(0.06, 0.12, 0.1, 0.9); c.fill_preserve(); c.set_source_rgb(*GRN); c.set_line_width(14); c.set_line_join(1); c.stroke()
    c.restore()
    if t >= t_arrow:
        a = clamp((t - t_arrow) / 0.3); b = 18 * math.sin(t * 9)
        arrow(c, 780 + b * 0.5, 1320 + b, 980 + b * 0.5, 1510 + b, GRN, 22, 70, a)
        c.select_font_face("Inter Display", 0, 1); c.set_font_size(66); c.set_source_rgba(1, 1, 1, a)
        e = c.text_extents(txt); c.move_to(560 - e.x_advance / 2, 1240); c.show_text(txt)

# ---------------- añadidas 24-11-2026: termómetro, cuerpo que suelta calor y calcetín ----------------
def thermo(F, t, level, cx=540, top=520, bot=1380, wid=120, scale_lbl=True):
    """Termómetro de neón. `level` 0..1: altura y color del líquido (alto = rojo/caliente, bajo = cian/fresco)."""
    g, c = F.g, F.b
    lv = clamp(level); col = mix(CYAN, RED, lv)
    R = wid * 0.85; by = bot - R
    c.set_source_rgba(0.08, 0.07, 0.2, 0.85); rrect(c, cx - wid / 2, top, wid, by - top, wid / 2); c.fill(); c.arc(cx, by, R, 0, 6.3); c.fill()
    yl = by - (by - top - 40) * lv + 5 * math.sin(t * 3)
    g.set_source_rgba(*col, 0.95); rrect(g, cx - wid / 2 + 22, yl, wid - 44, by - yl, (wid - 44) / 2); g.fill()
    g.arc(cx, by, R - 22, 0, 6.3); g.fill()
    for lw, a in ((16, 0.25), (6, 0.95)):
        g.set_source_rgba(*col, a); g.set_line_width(lw)
        g.new_sub_path(); g.arc(cx, by, R, -math.pi / 2 + 0.75, 1.5 * math.pi - 0.75)
        g.line_to(cx - wid / 2, top + wid / 2); g.arc(cx, top + wid / 2, wid / 2, math.pi, 2 * math.pi); g.close_path(); g.stroke()
    if scale_lbl:
        for i in range(9):
            y = top + 60 + i * (by - top - 120) / 8
            g.set_source_rgba(1, 1, 1, 0.6); g.set_line_width(4); g.move_to(cx + wid / 2 + 14, y); g.line_to(cx + wid / 2 + (52 if i % 2 == 0 else 34), y); g.stroke()

def heat_wave(g, x, y, ang, p, col, a, ln=170):
    """Una onda de calor (línea ondulada) que sale de (x, y) en dirección `ang`; p 0..1 = recorrido."""
    dx, dy = math.cos(ang), math.sin(ang); nx, ny = -dy, dx
    d0 = 30 + p * 140
    g.set_source_rgba(*col, a * math.sin(p * math.pi)); g.set_line_width(7); g.set_line_cap(1)
    for k in range(13):
        u = k / 12; d = d0 + u * ln * 0.6; off = 14 * math.sin(u * 8 + p * 6)
        px, py = x + dx * d + nx * off, y + dy * d + ny * off
        if k == 0: g.move_to(px, py)
        else: g.line_to(px, py)
    g.stroke()

def body_heat(F, t, release=1.0, trapped=0.0, cx=540, cy=1000, s=1.0, cool=0.0):
    """Silueta de neón de pie que suelta calor (ondas ámbar) por manos y pies. `trapped` 0..1 = caja-cuarto
    que lo encierra: las ondas rebotan y el cuarto se llena de neblina roja. `cool` tiñe el cuerpo de cian."""
    c, g = F.b, F.g
    bg_holo(c, t)
    col = mix(GOLD, CYAN, cool)
    if trapped > 0:
        bx, by, bw, bh = 140, 470, 800, 1060
        c.set_source(rad(cx, cy, 50, 650, [(0, (1.0, 0.3, 0.35, 0.35 * trapped)), (1, (1.0, 0.3, 0.35, 0.12 * trapped))]))
        rrect(c, bx, by, bw, bh, 30); c.fill()
        for lw, a in ((18, 0.25), (6, 0.9)):
            g.set_source_rgba(*RED, a * trapped); g.set_line_width(lw); rrect(g, bx, by, bw, bh, 30); g.stroke()
    g.save(); g.translate(cx, cy); g.scale(s, s)
    b = 6 * math.sin(t * 2)
    for lw, a in ((22, 0.25), (9, 0.95)):
        g.set_source_rgba(*col, a); g.set_line_width(lw); g.set_line_cap(1); g.set_line_join(1)
        g.arc(0, -330 + b, 70, 0, 6.3); g.stroke()
        g.move_to(0, -250 + b); g.line_to(0, 60); g.stroke()
        g.move_to(0, -190 + b); g.line_to(-170, -20); g.move_to(0, -190 + b); g.line_to(170, -20); g.stroke()
        g.move_to(0, 60); g.line_to(-110, 330); g.move_to(0, 60); g.line_to(110, 330); g.stroke()
    g.restore()
    pts = [(-170, -20, math.pi * 1.0), (170, -20, 0.0), (-110, 330, math.pi * 0.75), (110, 330, math.pi * 0.25)]
    for i, (px, py, ang) in enumerate(pts):
        X, Y = cx + px * s, cy + py * s
        g.set_source_rgba(*GOLD, 0.9 * release); g.arc(X, Y, 18, 0, 6.3); g.fill()
        for j in range(3):
            p = (t * 0.6 + j / 3 + i * 0.13) % 1
            if trapped > 0.5: p = p * 0.55          # se queda cerca: no tiene adónde ir
            heat_wave(g, X, Y, ang + 0.25 * math.sin(j * 2 + t), p, mix(GOLD, RED, trapped), release)

def sock(g, x, y, s=1.0, col=None, a=1.0, ang=0.0, glow=0.0):
    """Calcetín de neón (contorno, puño con rayas). `glow` 0..1 añade halo cálido."""
    col = col or GOLD
    g.save(); g.translate(x, y); g.rotate(ang); g.scale(s, s)
    if glow > 0:
        g.set_source(rad(0, 80, 10, 260, [(0, (1.0, 0.75, 0.35, 0.35 * glow)), (1, (1.0, 0.75, 0.35, 0))])); g.arc(0, 80, 260, 0, 6.3); g.fill()
    g.set_source_rgba(*col, a); g.set_line_width(10); g.set_line_join(1); g.set_line_cap(1)
    g.move_to(-70, -200); g.line_to(70, -200); g.line_to(70, 90); g.curve_to(70, 130, 110, 140, 160, 150)
    g.curve_to(220, 165, 220, 260, 150, 260); g.line_to(-30, 260); g.curve_to(-90, 260, -70, 170, -70, 120); g.close_path(); g.stroke()
    for k in range(3):
        yy = -170 + k * 30; g.move_to(-70, yy); g.line_to(70, yy); g.stroke()
    g.restore()

def breeze(g, t, k=1.0, x0=80, x1=1000, y0=650, y1=1250, col=None):
    """Corrientes de aire fresco de neón cruzando la escena (ventilar)."""
    col = col or CYAN; r = random.Random(11)
    for i in range(9):
        y = r.uniform(y0, y1); sp = r.uniform(0.35, 0.6); p = (t * sp + r.random()) % 1
        x = lerp(x0 - 200, x1, p); a = k * 0.8 * math.sin(p * math.pi)
        g.set_source_rgba(*col, a); g.set_line_width(7); g.set_line_cap(1)
        g.move_to(x, y); g.curve_to(x + 80, y - 30, x + 150, y + 30, x + 230, y); g.stroke()

# ---------------- añadidas 25-11-2026: deportista que jadea / camina y cronómetro-nariz ----------------
def athlete(F, t, pose=0.0, walk=0.0, cx=540, floor=1420, s=1.0, col=None, mouth_air=0.0, nose_air=0.0, pant=0.0):
    """Figura de neón de perfil (mira a la izquierda). `pose` 0 = doblado con las manos en las rodillas, 1 = erguido.
    `walk` 0..1 = balanceo de piernas al caminar. `mouth_air` bocanadas rosas por la boca; `nose_air` aire cian que entra por la nariz;
    `pant` 0..1 = el cuerpo sube y baja rápido (jadeo)."""
    g = F.g; col = col or PINK
    k = clamp(pose)
    bob = pant * 10 * math.sin(t * 14)
    def P(a, b): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
    hip = P((cx + 110, floor - 330), (cx, floor - 360))
    sh = P((cx - 150, floor - 420 + bob), (cx - 10, floor - 690 + bob * 0.4))
    head = P((cx - 240, floor - 400 + bob), (cx - 20, floor - 790 + bob * 0.4))
    knee_f = P((cx + 40, floor - 170), (cx - 10, floor - 180))
    sw = walk * 0.45 * math.sin(t * 5.5)
    g.save(); g.translate(cx, floor); g.scale(s, s); g.translate(-cx, -floor)
    for lw, aa in ((22, 0.18), (9, 0.95)):
        g.set_source_rgba(*col, aa); g.set_line_width(lw); g.set_line_cap(1); g.set_line_join(1)
        # piernas
        for sgn in (1, -1):
            a = sgn * sw
            kx = hip[0] + (knee_f[0] - hip[0]) * math.cos(a) - (knee_f[1] - hip[1]) * math.sin(a) * 0.3 - sgn * sw * 120
            ky = knee_f[1]
            fx = kx + (cx + 70 * (1 - k) - kx) * 0.3 - sgn * sw * 160
            g.move_to(*hip); g.line_to(kx, ky); g.line_to(fx, floor - 10); g.line_to(fx - 50, floor - 10); g.stroke()
        # torso
        g.move_to(*hip); g.line_to(*sh); g.stroke()
        # brazos: doblado → manos en las rodillas; erguido → braceo suave
        hand = P((knee_f[0] - 10, knee_f[1] - 30), (sh[0] + 30 - 60 * sw, sh[1] + 290))
        elbow = P(((sh[0] + hand[0]) / 2 - 20, (sh[1] + hand[1]) / 2 + 40), (sh[0] - 30 - 40 * sw, sh[1] + 150))
        g.move_to(*sh); g.line_to(*elbow); g.line_to(*hand); g.stroke()
        # cabeza
        g.arc(head[0], head[1], 52, 0, 6.3); g.stroke()
    # boca / nariz
    mx, my = head[0] - 50, head[1] + 22
    nx, ny = head[0] - 56, head[1] - 4
    if mouth_air > 0:
        for i in range(5):
            p = ((t * 2.4 + i / 5) % 1.0)
            r = 14 + 46 * p
            g.set_source_rgba(*PINK, mouth_air * 0.55 * (1 - p)); g.set_line_width(5)
            g.arc(mx - 30 - p * 230, my + 10 + 40 * p * math.sin(i), r, 0, 6.3); g.stroke()
        g.set_source_rgba(*PINK, mouth_air); g.arc(mx + 6, my, 12, 0, 6.3); g.fill()
    if nose_air > 0:
        for i in range(4):
            p = ((t * 0.9 + i / 4) % 1.0)
            x0 = nx - 260 * (1 - p); y0 = ny - 30 + 18 * math.sin(i * 2.1 + t)
            g.set_source_rgba(*CYAN, nose_air * 0.85 * math.sin(p * math.pi)); g.set_line_width(6); g.set_line_cap(1)
            g.move_to(x0, y0); g.line_to(x0 + 70, y0 + 4); g.stroke()
    g.restore()

def nose_stopwatch(F, t, prog, cx=540, cy=960, R=300, col=None, a=1.0):
    """Cronómetro de neón con una nariz en el centro: el anillo se llena con `prog` 0..1 (de rosa a verde)."""
    g, o = F.g, F.o
    col = col or mix(PINK, GRN, clamp(prog))
    g.save(); g.translate(cx, cy)
    g.set_source_rgba(0.06, 0.05, 0.16, 0.85 * a); g.arc(0, 0, R, 0, 6.3); g.fill()
    g.set_source_rgba(*VIO, 0.6 * a); g.set_line_width(6); g.arc(0, 0, R, 0, 6.3); g.stroke()
    rrect(g, -40, -R - 70, 80, 50, 12); g.stroke()
    g.move_to(0, -R - 20); g.line_to(0, -R); g.stroke()
    for i in range(60):
        an = i / 60 * 2 * math.pi - math.pi / 2; l = 34 if i % 5 == 0 else 16
        g.set_source_rgba(1, 1, 1, (0.7 if i % 5 == 0 else 0.3) * a); g.set_line_width(5 if i % 5 == 0 else 3)
        g.move_to((R - 30) * math.cos(an), (R - 30) * math.sin(an)); g.line_to((R - 30 - l) * math.cos(an), (R - 30 - l) * math.sin(an)); g.stroke()
    if prog > 0:
        for lw, aa in ((40, 0.25), (16, 1.0)):
            g.set_source_rgba(*col, aa * a); g.set_line_width(lw); g.set_line_cap(1)
            g.arc(0, 0, R + 2, -math.pi / 2, -math.pi / 2 + 2 * math.pi * clamp(prog)); g.stroke()
    # nariz de perfil en el centro
    s = R / 300.0
    g.scale(s, s)
    for lw, aa in ((20, 0.2), (8, 1.0)):
        g.set_source_rgba(*col, aa * a); g.set_line_width(lw); g.set_line_cap(1); g.set_line_join(1)
        g.move_to(-20, -150); g.curve_to(-30, -60, -90, 10, -100, 50); g.curve_to(-105, 80, -70, 95, -40, 85)
        g.curve_to(-20, 100, 10, 95, 20, 70); g.stroke()
    an = -math.pi / 2 + 2 * math.pi * clamp(prog)
    g.set_source_rgba(1, 1, 1, 0.9 * a); g.set_line_width(7); g.set_line_cap(1)
    g.move_to(0, 0); g.line_to(190 * math.cos(an), 190 * math.sin(an)); g.stroke()
    g.arc(0, 0, 14, 0, 6.3); g.fill()
    g.restore()


# ---------------- añadidas 26-11-2026: perfil de boca y lengua, contador de respiraciones ----------------
def mouth_profile(F, t, cx=540, cy=980, s=1.0, tongue=0.0, lips=1.0, nose_air=0.0, mouth_air=0.0, col=None, tongue_col=None, q=0.0):
    """Corte de perfil de la cabeza (mirando a la izquierda) en holograma: paladar, lengua y vías de aire.
    tongue 0 = lengua abajo (pegada a los dientes de abajo) .. 1 = apoyada en el paladar; lips 0 abiertos .. 1 cerrados;
    nose_air / mouth_air = flujo de aire cian/rosa; q = signo de interrogación parpadeando sobre la lengua."""
    g = F.g; col = col or VIO
    tcol = tongue_col or mix(PINK, CYAN, tongue)
    g.save(); g.translate(cx, cy); g.scale(s, s)
    open_ = 1 - clamp(lips)
    jaw = 60 * open_                        # la mandíbula baja al abrir
    g.set_line_cap(1); g.set_line_join(1)
    # contorno: frente → nariz → labio superior
    for lw, aa in ((22, 0.18), (7, 0.95)):
        g.set_source_rgba(*col, aa); g.set_line_width(lw)
        g.move_to(-80, -430); g.curve_to(-150, -380, -170, -300, -165, -230)
        g.curve_to(-200, -170, -260, -110, -270, -70); g.curve_to(-275, -40, -240, -30, -210, -35)
        g.curve_to(-215, -10, -225, 10, -220, 30); g.line_to(-205, 40)
        g.stroke()
        # labio inferior + barbilla + cuello (se mueve con la mandíbula)
        g.move_to(-205, 50 + jaw); g.curve_to(-225, 70 + jaw, -220, 100 + jaw, -200, 120 + jaw)
        g.curve_to(-210, 170 + jaw, -190, 230 + jaw, -130, 250 + jaw); g.curve_to(-40, 270 + jaw, 60, 230, 120, 330)
        g.stroke()
        # nuca y cráneo
        g.move_to(-80, -430); g.curve_to(150, -470, 330, -320, 320, -80); g.curve_to(315, 60, 260, 160, 230, 330); g.stroke()
    # paladar (arco) y fosa nasal
    g.set_source_rgba(*GOLD, 0.85); g.set_line_width(6)
    g.move_to(-190, -10); g.curve_to(-120, -70, 0, -80, 90, -40); g.curve_to(130, -20, 150, 20, 150, 60); g.stroke()
    g.set_source_rgba(*VIO, 0.45); g.set_line_width(4)
    g.move_to(-235, -70); g.curve_to(-150, -140, 20, -150, 150, -90); g.curve_to(200, -60, 210, 0, 200, 80); g.stroke()
    # dientes (arriba y abajo)
    g.set_source_rgba(1, 1, 1, 0.85)
    rrect(g, -200, -12, 26, 34, 6); g.fill()
    rrect(g, -196, 36 + jaw, 24, 30, 6); g.fill()
    # lengua: interpolación entre abajo y arriba
    k = ease(tongue)
    tip = (lerp(-170, -165, k), lerp(55 + jaw, -20, k))
    mid = (lerp(-60, -40, k), lerp(70 + jaw, -55, k))
    back_ = (lerp(70, 90, k), lerp(60 + jaw * 0.6, -25, k))
    base = (lerp(120, 130, k), lerp(170, 150, k))
    floor_ = (-120, lerp(110 + jaw, 60, k))
    g.move_to(*tip); g.curve_to(tip[0] + 30, tip[1] - 30 * (1 - k) - 10 * k, mid[0] - 50, mid[1], *mid)
    g.curve_to(mid[0] + 60, mid[1], back_[0] - 20, back_[1] - 10, *back_)
    g.curve_to(back_[0] + 40, back_[1] + 20, base[0], base[1] - 40, *base)
    g.curve_to(40, 170, -60, 130, *floor_); g.curve_to(-150, floor_[1] - 10, tip[0] - 10, tip[1] + 25, *tip); g.close_path()
    g.set_source_rgba(*tcol, 0.35); g.fill_preserve()
    g.set_source_rgba(*tcol, 0.95); g.set_line_width(7); g.stroke()
    # aire por la nariz (cian) y por la boca (rosa)
    for i in range(6):
        p = (t * 0.9 + i / 6) % 1
        if nose_air > 0.02:
            x = lerp(-330, 180, p); y = -70 - 40 * math.sin(math.pi * (x + 260) / 460) if x > -260 else -55
            g.set_source_rgba(*CYAN, nose_air * math.sin(math.pi * p)); g.arc(x, y, 13, 0, 6.3); g.fill()
        if mouth_air > 0.02:
            x = lerp(-340, 120, p); y = 25 + jaw * 0.5 + 12 * math.sin(p * 18)
            g.set_source_rgba(*PINK, mouth_air * math.sin(math.pi * p)); g.arc(x, y, 14, 0, 6.3); g.fill()
    if q > 0:
        o = F.o; o.save(); o.translate(cx - 40 * s, cy - 170 * s)
        o.select_font_face("Inter Display", 0, 1); o.set_font_size(150 * s)
        o.set_source_rgba(*GOLD, q * (0.6 + 0.4 * math.sin(t * 5))); o.move_to(-40 * s, 0); o.show_text("?"); o.restore()
    g.restore()


def breath_counter(F, t, n_done, n=5, cx=540, cy=1450, gap=150, R=46, col=None):
    """Fila de `n` lunas/círculos de neón que se llenan una a una (n_done puede ser fraccionario); el actual respira."""
    g = F.g; col = col or CYAN
    x0 = cx - gap * (n - 1) / 2
    for i in range(n):
        x = x0 + i * gap
        f = clamp(n_done - i)
        r = R * (1 + (0.15 * math.sin(t * 2.2) if 0 < f < 1 else 0))
        g.set_source_rgba(*VIO, 0.5); g.set_line_width(5); g.arc(x, cy, r, 0, 6.3); g.stroke()
        if f > 0:
            g.set_source_rgba(*mix(VIO, col, f), 0.35 + 0.6 * f); g.arc(x, cy, r * (0.35 + 0.65 * f), 0, 6.3); g.fill()
            g.set_source_rgba(*col, 0.9 * f); g.set_line_width(6); g.arc(x, cy, r, 0, 6.3); g.stroke()


# ---------------- añadidas 27-11-2026: plato de pizza de neón y engranaje-motor ----------------
def pizza_plate(g, t, cx=540, cy=1000, s=1.0, slices=8, steam=1.0, col=None, a=1.0):
    """Plato con pizza de neón (porciones `slices` de 8 que quedan) y vapor que sube (`steam` 0..1)."""
    col = col or GOLD
    g.save(); g.translate(cx, cy); g.scale(s, s)
    g.set_source_rgba(*VIO, 0.6 * a); g.set_line_width(6); ell(g, 0, 40, 330, 120); g.stroke()
    g.set_source_rgba(*VIO, 0.25 * a); ell(g, 0, 40, 290, 100); g.stroke()
    n = int(round(clamp(slices / 8.0) * 8))
    for k in range(n):
        a0 = -math.pi / 2 + k * math.pi / 4; a1 = a0 + math.pi / 4
        g.save(); g.scale(1, 0.38)
        g.move_to(0, 0); g.arc(0, 0, 250, a0 + 0.03, a1 - 0.03); g.close_path()
        g.set_source_rgba(*col, 0.18 * a); g.fill_preserve(); g.set_source_rgba(*col, 0.95 * a); g.set_line_width(7); g.stroke()
        am = (a0 + a1) / 2
        for rr, dd in ((150, 0.0), (205, 0.12)):
            g.set_source_rgba(*RED, 0.9 * a); g.arc(rr * math.cos(am + dd), rr * math.sin(am + dd), 18, 0, 6.3); g.fill()
        g.restore()
    if steam > 0:
        for i in range(4):
            p = (t * 0.45 + i / 4) % 1; x = -120 + i * 80 + 20 * math.sin(t * 2 + i); y = -40 - 300 * p
            g.set_source_rgba(1, 1, 1, steam * 0.55 * a * math.sin(p * math.pi)); g.set_line_width(7); g.set_line_cap(1)
            g.move_to(x, y); g.curve_to(x + 30, y - 40, x - 30, y - 80, x, y - 120); g.stroke()
    g.restore()


def engine_gear(g, t, cx, cy, r=120, speed=1.0, col=None, a=1.0, glow=0.0):
    """Engranaje de neón que gira (`speed` vueltas/s aprox.) con halo de calor `glow`: el 'motor encendido'."""
    col = col or RED
    if glow > 0:
        g.set_source(rad(cx, cy, 10, r * 2.4, [(0, (*col, 0.45 * glow)), (1, (*col, 0))])); g.arc(cx, cy, r * 2.4, 0, 6.3); g.fill()
    g.save(); g.translate(cx, cy); g.rotate(t * speed * 2.0)
    teeth = 10
    for k in range(teeth * 2):
        ang = k * math.pi / teeth; rr = r if k % 2 == 0 else r * 0.8
        x, y = rr * math.cos(ang), rr * math.sin(ang)
        (g.move_to if k == 0 else g.line_to)(x, y)
        ang2 = ang + math.pi / teeth * 0.6
        g.line_to(rr * math.cos(ang2), rr * math.sin(ang2))
    g.close_path(); g.set_source_rgba(*col, 0.15 * a); g.fill_preserve(); g.set_source_rgba(*col, 0.95 * a); g.set_line_width(7); g.set_line_join(1); g.stroke()
    g.arc(0, 0, r * 0.3, 0, 6.3); g.stroke()
    g.restore()
