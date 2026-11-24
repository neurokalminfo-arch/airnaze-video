# Temperatura para dormir: cuarto fresco, pies calentitos (noche neón).
# Primitivas nuevas: thermo (termómetro), body_heat (silueta que suelta calor por manos y pies), sock (calcetín), breeze (aire fresco).
import math

KEY = {"calefacción", "revés:", "temperatura.", "manos", "pies.", "cargado,", "vueltas", "fresco.", "calcetines.", "airnaze", "fácil.", "sí", "no."}


def timeline(L):
    A = L.A
    t_calef = A("calefacción"); t_tardas = A("tardas")
    t_pasa = A("pasa"); t_bajar = A("bajar"); t_temp = A("temperatura.")
    t_por = A("por", t_temp); t_suelta = A("suelta"); t_manos = A("manos"); t_pies = A("pies.")
    t_pero = A("pero"); t_cargado = A("cargado,"); t_adonde = A("adónde")
    t_y = A("y", t_adonde + 0.3); t_vueltas = A("vueltas"); t_destap = A("destapándote.")
    t_truco = A("el", t_destap); t_fresco = A("fresco.", t_truco); t_ventila = A("ventila"); t_acost = A("acostarte,")
    t_ysi = A("y", t_acost); t_frios = A("fríos,"); t_calcet = A("calcetines.")
    t_calent = A("calentitos,"); t_fresco2 = A("fresco.", t_calent)
    t_si = A("y", t_fresco2); t_cerrada = A("cerrada,"); t_airnaze = A("airnaze")
    t_q = A("tú,", t_airnaze) - 0.35; t_comenta = A("comenta"); t_sii = A("sí", t_comenta); t_no = A("no.", t_comenta)
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp = L.clamp, L.ramp, L.back, L.eio, L.lerp

    def hook(F, t, t0):                       # 1 · dormitorio recalentado + termómetro en rojo
        F.cam(1.0 + 0.07 * eio(t / 3.5), cx=640, cy=1000)
        L.bedroom(F, t, clock_glow=1.0, head_glow=(L.RED, 0.5 + 0.2 * math.sin(t * 4)), shake=0.3 * ramp(t, t_tardas, t_tardas + 0.4))
        F.g.set_source_rgba(*L.RED, 0.10 + 0.05 * math.sin(t * 3)); F.g.rectangle(0, 0, L.W, L.H); F.g.fill()
        L.badge(F.o, t, t_calef, 540, 440, "A TOPE", "", col=L.RED)
        L.label(F.o, t, t_tardas, 540, 1640, "Y AUN ASÍ NO TE DUERMES", L.PINK, size=44)

    def reves(F, t, t0):                      # 2 · al revés: el termómetro del cuerpo baja
        L.bg_holo(F.b, t); F.cam(1.0 + 0.05 * eio((t - t0) / 3), cx=540, cy=950)
        L.thermo(F, t, lerp(0.9, 0.45, ramp(t, t_bajar, t_temp + 0.6)), cx=400)
        L.arrow(F.g, 700, 700, 700, 1100, L.CYAN, 18, 60, ramp(t, t_bajar, t_bajar + 0.3))
        L.label(F.o, t, t0 + 0.1, 540, 470, "AL REVÉS", L.GOLD, size=50)
        L.label(F.o, t, t_bajar, 540, 1600, "TU CUERPO BAJA UN POCO", L.CYAN, size=44)
        L.label(F.o, t, t_temp - 0.2, 540, 1710, "SU TEMPERATURA", L.CYAN, size=44)

    def manos(F, t, t0):                      # 3 · suelta calor por manos y pies
        F.cam(1.0 + 0.04 * eio((t - t0) / 4), cx=540, cy=1000)
        L.body_heat(F, t, release=ramp(t, t_suelta - 0.3, t_suelta + 0.4), cy=1020, s=0.95)
        L.label(F.o, t, t_manos, 200, 860, "MANOS", L.GOLD, size=42)
        L.label(F.o, t, t_pies, 540, 1580, "Y PIES", L.GOLD, size=42)
        L.label(F.o, t, t0 + 0.2, 540, 470, "SUELTA CALOR", L.GRN, size=46)

    def atrapado(F, t, t0):                   # 4 · cuarto caliente y cargado: el calor no tiene adónde ir
        F.cam(1.0 + 0.05 * eio((t - t0) / 3), cx=540, cy=1000)
        L.body_heat(F, t, release=1.0, trapped=ramp(t, t0, t_cargado), cy=1010, s=0.8)
        L.label(F.o, t, t_cargado - 0.3, 540, 420, "CALIENTE Y CARGADO", L.RED, size=46)
        L.label(F.o, t, t_adonde - 0.1, 540, 1650, "EL CALOR NO TIENE ADÓNDE IR", L.PINK, size=40)

    def vueltas(F, t, t0):                    # 5 · noche dando vueltas y destapándote
        F.cam(1.04 + 0.02 * math.sin(t * 5), cx=640, cy=1050)
        L.bedroom(F, t, clock_glow=1.0, shake=0.8, head_glow=(L.PINK, 0.45))
        L.badge(F.o, t, t_vueltas, 540, 440, "3:47", "", col=L.GOLD)
        L.label(F.o, t, t_vueltas, 540, 1600, "DANDO VUELTAS", L.PINK, size=46)
        L.label(F.o, t, t_destap - 0.2, 540, 1710, "Y DESTAPÁNDOTE", L.VIO, size=42)

    def truco(F, t, t0):                      # 6 · cuarto fresco: ventila un rato (aire fresco entrando)
        F.cam(1.0 + 0.06 * eio((t - t0) / 4), cx=300, cy=900)
        L.bedroom(F, t, clock_glow=0.5, nose_air=0.6)
        L.breeze(F.g, t, ramp(t, t_ventila - 0.4, t_ventila + 0.4), x0=120, y0=560, y1=1100)
        F.g.set_source_rgba(*L.CYAN, 0.08); F.g.rectangle(0, 0, L.W, L.H); F.g.fill()
        L.label(F.o, t, t0 + 0.1, 540, 440, "EL TRUCO", L.GOLD, size=46)
        L.label(F.o, t, t_fresco - 0.2, 540, 1560, "CUARTO FRESCO", L.CYAN, size=48)
        L.label(F.o, t, t_ventila, 540, 1680, "VENTILA UN RATO ANTES", L.GRN, size=42)

    def calcet(F, t, t0):                     # 7 · ¿pies fríos? calcetines
        L.bg_holo(F.b, t); F.cam(1.0 + 0.05 * eio((t - t0) / 3), cx=540, cy=1000)
        k = back((t - t_calcet + 0.3) / 0.45) if t > t_calcet - 0.3 else 0
        col = L.mix(L.CYAN, L.GOLD, ramp(t, t_calcet - 0.3, t_calcet + 0.4))
        bob = 12 * math.sin(t * 3)
        L.sock(F.g, 360, 930 + bob, s=1.25 * (0.8 + 0.2 * k), col=col, glow=k, ang=-0.12)
        L.sock(F.g, 730, 980 - bob, s=1.25 * (0.8 + 0.2 * k), col=col, glow=k, ang=0.1)
        L.label(F.o, t, t_frios - 0.3, 540, 470, "¿PIES FRÍOS?", L.CYAN, size=50)
        L.label(F.o, t, t_calcet - 0.1, 540, 1620, "CALCETINES", L.GOLD, size=56)

    def formula(F, t, t0):                    # 8 · pies calentitos + cuarto fresco
        L.bg_holo(F.b, t); F.cam(1.0)
        L.sock(F.g, 300, 900, s=0.85, col=L.GOLD, glow=1.0, a=ramp(t, t0, t0 + 0.3))
        L.thermo(F, t, 0.3, cx=780, top=640, bot=1260, wid=100, scale_lbl=False)
        F.o.select_font_face("Inter Display", 0, 1); F.o.set_font_size(110); F.o.set_source_rgba(1, 1, 1, ramp(t, t0 + 0.2, t0 + 0.5))
        F.o.move_to(505, 1000); F.o.show_text("+")
        L.label(F.o, t, t0 + 0.1, 300, 1440, "PIES CALENTITOS", L.GOLD, size=36)
        L.label(F.o, t, t_fresco2 - 0.3, 780, 1440, "CUARTO FRESCO", L.CYAN, size=36)

    def producto(F, t, t0):                   # 9 · nariz algo cerrada → AirNaze (única aparición)
        if t < t_airnaze - 0.1:
            L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
            L.holo_nose(F, t, s=0.9, pl=0.6, pr=0.6)
            L.label(F.o, t, t_cerrada - 0.3, 540, 1600, "NARIZ ALGO CERRADA", L.PINK, size=44)
        else:
            L.product_card(F, t, t_airnaze, img=None, items=["PADS POR FUERA DE LA NARIZ", "UN ARCO QUE SE CONECTA", "PARA QUE EL AIRE PASE MÁS FÁCIL"])

    def cierre(F, t, t0):                     # 10 · CTA comenta SÍ o NO
        def fondo(F, t, t0):
            L.bg_holo(F.b, t)
            L.sock(F.g, 300, 930, s=0.75, col=L.GOLD, glow=0.6, ang=0.08 * math.sin(t * 2), a=0.6)
        L.close_cta(F, t, t0, None, t_comenta, scene_draw=fondo)
        L.pill(F.o, t, t_sii, "SÍ", 1520, col=L.GRN)
        L.pill(F.o, t, t_no, "NO", 1680, col=L.PINK)

    return [(0, "gancho", hook), (t_pasa - 0.1, "reves", reves), (t_por - 0.1, "manos", manos), (t_pero - 0.1, "atrapado", atrapado),
            (t_y - 0.1, "vueltas", vueltas), (t_truco - 0.1, "truco", truco), (t_ysi - 0.1, "calcetines", calcet),
            (t_calent - 0.5, "formula", formula), (t_si - 0.1, "producto", producto), (t_q - 0.1, "cierre", cierre)], end


def ACCENTS(L): return [L.A("calefacción"), L.A("temperatura."), L.A("cargado,"), L.A("calcetines."), L.A("sí", L.A("comenta"))]
def CHIMES(L): return [L.A("airnaze")]
