# Reto 60 s tras entrenar por la tarde: piernas en la pared (noche neón).
# Primitivas nuevas: dumbbell, pulse_line, route, shower_lamp, legs_wall.
import math

KEY = {"entrenado", "encendido:", "pulso", "calor,", "frenar.", "bajar.", "ducha", "luz", "piernas", "pared,", "nariz.", "airnaze", "fácil.", "comentarios"}


def timeline(L):
    A = L.A
    t_tarde = A("tarde."); t_te = A("te"); t_pulso = A("pulso"); t_calor = A("calor,"); t_cabeza = A("cabeza")
    t_no = A("no"); t_ent = A("entrenar", t_no); t_es = A("es", A("sueño."))
    t_pasas = A("pasas"); t_gim = A("gimnasio"); t_alm = A("almohada"); t_sin = A("sin")
    t_y = A("y", t_sin); t_nec = A("necesita"); t_bajar = A("bajar.")
    t_asi = A("así"); t_ducha = A("ducha"); t_luz = A("luz"); t_reto = A("reto:", t_luz)
    t_60 = A("sesenta"); t_piernas = A("piernas"); t_boca = A("boca", t_piernas); t_lento = A("lento", t_boca)
    t_nota = A("nota"); t_ritmo = A("ritmo.")
    t_si = A("si", t_ritmo); t_airnaze = A("airnaze")
    t_q = A("lo", t_airnaze); t_com = A("comentarios", t_q)
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp = L.clamp, L.ramp, L.back, L.eio, L.lerp

    def hook(F, t, t0):                       # 1 · gimnasio de tarde: mancuerna de neón
        L.bg_holo(F.b, t); F.cam(1.0 + 0.08 * eio(t / 4), cx=540, cy=950)
        F.b.set_source(L.rad(540, 950, 20, 700, [(0, (1.0, 0.42, 0.75, 0.25)), (1, (1.0, 0.42, 0.75, 0))])); F.b.paint()
        L.dumbbell(F.g, 540, 950 + 30 * math.sin(t * 3.2), 2.1, -0.25 + 0.08 * math.sin(t * 3.2), L.PINK)
        L.badge(F.o, t, 0.25, 540, 560, "60", "s", col=L.GRN, sub="RETO PARA ESTA NOCHE")
        L.label(F.o, t, t_tarde - 0.6, 540, 1560, "SI HAS ENTRENADO POR LA TARDE", L.GOLD, size=42)

    def encendido(F, t, t0):                  # 2 · en la cama, el cuerpo sigue encendido
        F.cam(1.0 + 0.06 * eio((t - t0) / 4), cx=540, cy=1000)
        L.bedroom(F, t, head_glow=(L.RED, 0.5 + 0.3 * math.sin(t * 6)), clock_glow=1.0)
        L.pulse_line(F, t, y=1700, rate=2.4, amp=0.8, col=L.RED, a=ramp(t, t_pulso, t_pulso + 0.3))
        L.label(F.o, t, t_pulso, 260, 470, "PULSO ALTO", L.RED, size=42)
        L.label(F.o, t, t_calor, 820, 470, "CALOR", L.GOLD, size=42)
        L.label(F.o, t, t_cabeza, 540, 1530, "LA CABEZA A MIL", L.PINK, size=44)

    def no_es(F, t, t0):                      # 3 · entrenar no es el problema
        L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
        L.dumbbell(F.g, 540, 950, 1.6, 0.0, L.mix(L.PINK, L.GRN, ramp(t, t_ent, t_ent + 0.5)))
        L.label(F.o, t, t_ent, 540, 1560, "ENTRENAR NO ES EL PROBLEMA", L.GRN, size=42)

    def ruta(F, t, t0):                       # 4 · del gimnasio a la almohada sin frenar
        F.cam(1.0)
        p = ramp(t, t_gim, t_sin + 0.3)
        L.route(F, t, p, 0.0)
        L.label(F.o, t, t_gim, 230, 680, "GIMNASIO", L.PINK, size=38)
        L.label(F.o, t, t_alm, 860, 680, "ALMOHADA", L.VIO, size=38)
        L.label(F.o, t, t_sin, 540, 1500, "SIN FRENAR", L.RED, size=50)

    def bajar(F, t, t0):                      # 5 · un rato para bajar: tramo de frenada
        F.cam(1.0 + 0.04 * eio((t - t0) / 3))
        br = ramp(t, t_nec, t_bajar + 0.4)
        L.route(F, t, lerp(0.45, 0.92, eio((t - t0) / max(0.5, t_asi - t0))), br)
        L.label(F.o, t, t_nec, 540, 1500, "UN RATO PARA BAJAR", L.CYAN, size=48)

    def ducha(F, t, t0):                      # 6 · ducha templada + luz baja
        F.cam(1.0 + 0.05 * eio((t - t0) / 4), cx=540, cy=1000)
        L.shower_lamp(F, t, steam=ramp(t, t_ducha, t_ducha + 0.5), dim=ramp(t, t_luz, t_luz + 0.6))
        L.label(F.o, t, t_asi, 540, 470, "ANTES DE DORMIR", L.GOLD, size=40)
        L.label(F.o, t, t_ducha, 330, 1600, "DUCHA TEMPLADA", L.CYAN, size=40)
        L.label(F.o, t, t_luz, 800, 1690, "LUZ BAJA", L.GOLD, size=40)

    def reto(F, t, t0):                       # 7 · reto: piernas en la pared, 60 s, nariz
        F.cam(1.0 + 0.04 * eio((t - t0) / 5), cx=540, cy=1000)
        tm = clamp((t - t_60) / 18.0) if t > t_60 else 0
        L.legs_wall(F, t, breath=0.5 + 0.5 * math.sin((t - t0) * 1.3), timer=tm if t > t_60 - 0.2 else None,
                    nose_air=ramp(t, t_boca, t_boca + 0.5))
        L.label(F.o, t, t_piernas, 540, 1480, "PIERNAS EN LA PARED", L.GRN, size=44)
        L.label(F.o, t, t_boca, 540, 1590, "BOCA CERRADA · NARIZ", L.CYAN, size=42)
        L.label(F.o, t, t_lento, 540, 1690, "LENTO", L.VIO, size=42)

    def calma(F, t, t0):                      # 8 · baja el ritmo: pulso que se calma
        F.cam(1.0)
        tm = clamp((t - t_60) / 18.0)
        L.legs_wall(F, t, breath=0.5 + 0.5 * math.sin((t - t0) * 1.0), timer=tm, nose_air=0.8, calm=ramp(t, t0, t_ritmo + 0.3))
        r = lerp(2.0, 0.9, ramp(t, t0, t_ritmo + 0.4))
        L.pulse_line(F, t, y=1640, rate=r, amp=lerp(0.8, 0.45, ramp(t, t0, t_ritmo)), col=L.mix(L.RED, L.CYAN, ramp(t, t0, t_ritmo)))
        L.label(F.o, t, t_nota + 0.1, 540, 1470, "BAJA EL RITMO", L.GRN, size=46)

    def producto(F, t, t0):                   # 9 · nariz algo cerrada → AirNaze (única aparición)
        if t < t_airnaze - 0.1:
            L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
            op = ramp(t, t0 + 0.8, t_airnaze)
            L.holo_nose(F, t, s=0.9, pl=lerp(0.6, -0.5, op), pr=lerp(0.6, -0.5, op))
            L.label(F.o, t, t0 + 0.3, 540, 1600, "NARIZ ALGO CERRADA", L.PINK, size=44)
        else:
            L.product_card(F, t, t_airnaze, img=None, items=["PADS POR FUERA DE LA NARIZ", "UN ARCO QUE SE CONECTA", "PARA QUE EL AIRE PASE MÁS FÁCIL"])

    def cierre(F, t, t0):                     # 10 · CTA
        def fondo(F, t, t0):
            L.bg_holo(F.b, t)
            L.dumbbell(F.g, 300, 1000, 1.0, -0.2, L.CYAN, 0.8)
            L.pulse_line(F, t, y=1500, rate=0.9, amp=0.45, col=L.CYAN)
        L.close_cta(F, t, t0, None, t_com, scene_draw=fondo)

    return [(0, "gancho", hook), (t_te, "encendido", encendido), (t_no, "no_es", no_es), (t_es, "ruta", ruta),
            (t_y, "bajar", bajar), (t_asi, "ducha", ducha), (t_reto - 0.1, "reto", reto), (t_nota, "calma", calma),
            (t_si - 0.2, "producto", producto), (t_q, "cierre", cierre)], end


def ACCENTS(L): return [L.A("encendido:"), L.A("sin"), L.A("reto:", L.A("luz")), L.A("nota")]
def CHIMES(L): return [L.A("airnaze")]
def TICKS_UNTIL(L): return L.A("te")
