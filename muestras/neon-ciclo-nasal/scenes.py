# Episodio de referencia del estilo "noche neón" (ver skills/airnaze-noche-neon/SKILL.md).
# Cada escena es una función (F, t, t0) que dibuja con las primitivas de engine/neon/lib.py (L).
# Los tiempos se anclan a palabras de la voz con L.A("palabra", despues_de_segundos).
import math

KEY = {"resfriado", "turnos", "cornetes", "nasal", "tumbarte", "abajo", "estrecho", "boca", "seca", "airnaze", "fácil", "comentarios"}


def timeline(L):
    A = L.A
    t_no = A("no"); t_tapa = A("tapa"); t_otro = A("otro"); t_perf = A("perfecto?")
    t_turnos = A("turnos"); t_por = A("por", t_turnos); t_cornetes = A("cornetes"); t_hinchan = A("hinchan")
    t_y = A("y", A("deshinchan") + 0.1); t_cierra = A("cierra", t_y); t_abre = A("abre", t_y); t_ciclo = A("ciclo")
    t_al = A("al", t_ciclo); t_tumb = A("tumbarte"); t_carga = A("carga")
    t_ysi = A("y", t_carga); t_abajo = A("abajo")
    t_si = A("si", t_abajo); t_estrecho = A("estrecho"); t_cierra2 = A("cierra", t_estrecho); t_boca = A("boca", t_si)
    t_poreso = A("por", t_boca); t_seca = A("seca")
    t_truco = A("un", t_seca); t_airnaze = A("airnaze"); t_pads = A("pads"); t_arco = A("arco")
    t_q = A("¿a", t_arco); t_com = A("comentarios", t_q)
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp = L.clamp, L.ramp, L.back, L.eio, L.lerp

    def hook(F, t, t0):                       # 1 · gancho: dormitorio a las 3:12
        F.cam(1.0 + 0.10 * eio(t / 6), cx=700, cy=1050)
        hg = None
        if t > t_tapa: hg = (L.RED, ramp(t, t_tapa, t_tapa + 0.4) * (0.7 + 0.3 * math.sin(t * 6)))
        if t > t_otro: hg = (L.CYAN, ramp(t, t_otro, t_otro + 0.4))
        L.bedroom(F, t, head_glow=hg, nose_air=ramp(t, t_perf, t_perf + 0.4))
        L.badge(F.o, t, 0.4, 860, 640, "3:12")

    def turnos(F, t, t0):                     # 2 · no es un resfriado: la nariz se turna
        L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
        sw = 0.5 + 0.5 * math.sin((t - t_turnos) * 2.2) if t > t_turnos else 0
        L.holo_nose(F, t, swell_l=0.75 if t < t_turnos else sw * 0.8, swell_r=0.0 if t < t_turnos else (1 - sw) * 0.8)
        L.label(F.o, t, t0 + 0.3, 540, 1560, "NO ES UN RESFRIADO", (0.62, 0.58, 1), size=44)

    def cornetes(F, t, t0):                   # 3 · zoom a los cornetes
        L.bg_holo(F.b, t); F.cam(lerp(1.0, 1.55, eio((t - t0) / 1.6)), cx=540, cy=760)
        k = 0.35 if t > t_hinchan else 0
        L.holo_nose(F, t, turb=ramp(t, t_cornetes, t_cornetes + 0.4), swell_l=k * (0.5 + 0.5 * math.sin(t * 2.4)), swell_r=k * (0.5 - 0.5 * math.sin(t * 2.4)))
        L.label(F.o, t, t_cornetes, 540, 1560, "CORNETES", (1, 0.55, 0.8), size=44)

    def ciclo(F, t, t0):                      # 4 · ondas de neón con la cama
        fl, fr = L.waves(F, t, phase_shift=(t - t0) * 0.9)
        x = 400; y = fl(x); slope = (fl(x + 2) - fl(x - 2)) / 4
        L.bed_icon(F.o, x, y - 10, math.atan(slope) * 0.7)
        L.label(F.o, t, t_cierra, 260, 1640, "IZQUIERDA", L.PINK)
        L.label(F.o, t, t_abre, 820, 1640, "DERECHA", L.CYAN)
        L.label(F.o, t, t_ciclo, 540, 620, "CICLO NASAL", (0.95, 0.9, 1), size=46)

    def tumbado(F, t, t0):                    # 5 · al tumbarte gira y se carga
        L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
        rot = -math.pi / 2 * ramp(t, t_tumb, t_tumb + 0.8)
        c = ramp(t, t_carga, t_carga + 0.6)
        L.holo_nose(F, t, s=0.85, rot=rot, swell_l=0.3 * c, swell_r=0.3 * c)
        L.label(F.o, t, t_tumb, 540, 1600, "TUMBADO", (0.62, 0.58, 1))
        L.badge(F.o, t, t_carga, 800, 560, "+", "cargada", col=L.PINK)

    def de_lado(F, t, t0):                    # 6 · de lado: el de abajo se carga
        L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
        sw = ramp(t, t_abajo, t_abajo + 1.0)
        L.holo_nose(F, t, s=0.85, rot=-math.pi / 2, swell_l=0.3 + 0.45 * sw, swell_r=0.3 * (1 - sw))
        a = ramp(t, t_abajo, t_abajo + 0.3)
        if a > 0: L.arrow(F.g, 960, 640, 960, 1180, L.PINK, 12, 40, a)
        L.label(F.o, t, t_abajo, 540, 1620, "LADO DE ABAJO", L.PINK)

    def cerrado(F, t, t0):                    # 7 · el lado estrecho se cierra
        L.bg_holo(F.b, t); F.cam(1.0 + 0.04 * clamp((t - t0) / 3))
        cl = ramp(t, t_cierra2, t_cierra2 + 0.6)
        L.holo_nose(F, t, s=0.85, rot=-math.pi / 2, swell_l=0.75 + 0.25 * cl, swell_r=0.1, x_l=clamp((t - t_cierra2) / 0.35) if t > t_cierra2 else 0)
        L.label(F.o, t, t_estrecho, 540, 1620, "EL LADO ESTRECHO", L.PINK)

    def boca(F, t, t0):                       # 8 · respiras por la boca: boca seca
        F.cam(1.0 + 0.2 * eio((t - t0) / 1.5), cx=560, cy=1040)
        L.bedroom(F, t, mouth=ramp(t, t0, t0 + 0.4), mouth_air=ramp(t, t0 + 0.2, t0 + 0.6), head_glow=(L.RED, 0.4))
        L.label(F.o, t, t0 + 0.2, 540, 1560, "BOCA ABIERTA", L.RED, size=44)
        L.label(F.o, t, t_seca, 540, 700, "BOCA SECA", (1, 0.75, 0.45), size=44)

    def producto(F, t, t0):                   # 9 · truco + AirNaze (única aparición; sin dibujar el producto)
        if t < t_airnaze - 0.1:
            L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
            op = ramp(t, t0 + 0.6, t_airnaze)
            L.holo_nose(F, t, s=0.9, pl=lerp(0.5, -0.6, op), pr=lerp(0.5, -0.6, op))
            a = ramp(t, t0 + 0.6, t0 + 0.9)
            for d in (-1, 1): L.arrow(F.g, 540 + d * 140, 1600, 540 + d * 330, 1600, L.GRN, 12, 40, a)
        else:
            L.product_card(F, t, t_airnaze, img=None, items=["PADS POR FUERA DE LA NARIZ", "UN ARCO QUE SE CONECTA", "SIN PASTILLAS NI SPRAYS"])

    def cierre(F, t, t0):                     # 10 · CTA comentar
        def fondo(F, t, t0):
            fl, fr = L.waves(F, t, phase_shift=(t - t0) * 0.9)
            x = 400; y = fl(x); slope = (fl(x + 2) - fl(x - 2)) / 4
            L.bed_icon(F.o, x, y - 10, math.atan(slope) * 0.7)
        L.close_cta(F, t, t0, None, t_com, scene_draw=fondo)

    return [(0, "gancho", hook), (t_no, "turnos", turnos), (t_por, "cornetes", cornetes), (t_y, "ciclo", ciclo),
            (t_al, "tumbado", tumbado), (t_ysi, "de_lado", de_lado), (t_si, "cerrado", cerrado), (t_boca - 0.15, "boca", boca),
            (t_truco, "producto", producto), (t_q, "cierre", cierre)], end


def ACCENTS(L): return [L.A("cornetes"), L.A("ciclo"), L.A("tumbarte"), L.A("abajo")]
def CHIMES(L): return [L.A("airnaze")]
def TICKS_UNTIL(L): return L.A("no")
