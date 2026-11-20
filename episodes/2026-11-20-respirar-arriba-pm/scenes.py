# Me preguntasteis: respirar por arriba al final del día (noche neón). Primitivas nuevas: holo_torso, rev_gauge.
import math

KEY = {"cansancio", "diafragma", "pulmones", "barriga", "hombros", "pecho", "desconectar", "mano", "nariz", "airnaze", "fácil", "comentarios"}


def timeline(L):
    A = L.A
    t_final = A("final"); t_sent = A("sentado?")
    t_no = A("no"); t_es2 = A("es", A("cansancio")); t_donde = A("dónde")
    t_el = A("el", t_donde); t_dia = A("diafragma"); t_pulm = A("pulmones")
    t_cuando = A("cuando"); t_baja = A("baja"); t_barriga = A("barriga")
    t_pero = A("pero"); t_prisas = A("prisas"); t_arriba = A("arriba:"); t_hombros = A("hombros"); t_pecho = A("pecho,"); t_corto = A("corto")
    t_yasi = A("así"); t_desc = A("desconectar.")
    t_prueba = A("prueba"); t_mano = A("mano"); t_boca = A("boca", t_prueba); t_lento = A("lento")
    t_que = A("que", t_lento); t_suba = A("suba"); t_noh = A("hombros.", t_suba)
    t_ysi = A("si", t_noh); t_airnaze = A("airnaze")
    t_q = A("tú"); t_com = A("comentarios", t_q)
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp = L.clamp, L.ramp, L.back, L.eio, L.lerp

    def fast(t): return 0.5 + 0.5 * math.sin(t * 7.5)
    def slow(t, t0): return 0.5 - 0.5 * math.cos((t - t0) * 1.1)

    def hook(F, t, t0):                       # 1 · oficina 19:40, respiración rápida arriba
        L.bg_night(F.b); F.cam(1.0 + 0.08 * eio(t / 5), cx=540, cy=900)
        st = ramp(t, t_final, t_final + 0.6)
        L.holo_torso(F, t, cy=900, s=0.9, chest=st * fast(t), shoulders=0.6 * st * fast(t),
                     tint=L.mix(L.CYAN, L.RED, st), desk=1.0)
        L.badge(F.o, t, 0.3, 820, 520, "19:40")
        L.label(F.o, t, t_sent, 540, 1700, "Y ESTÁS SENTADO", L.GOLD, size=44)

    def no_es(F, t, t0):                      # 2 · no es cansancio: flechas arriba / abajo
        L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
        L.holo_torso(F, t, cy=1000, s=0.85, chest=fast(t) * 0.6, shoulders=0.3 * fast(t), tint=L.VIO)
        L.label(F.o, t, t0 + 0.2, 540, 1700, "NO ES CANSANCIO", (0.62, 0.58, 1), size=44)
        a = ramp(t, t_donde, t_donde + 0.3)
        if a > 0:
            L.arrow(F.g, 150, 900, 150, 560, L.RED, 12, 40, a)
            L.arrow(F.g, 930, 760, 930, 1180, L.GRN, 12, 40, a)

    def diafragma(F, t, t0):                  # 3 · zoom al diafragma
        L.bg_holo(F.b, t); F.cam(lerp(1.0, 1.35, eio((t - t0) / 1.8)), cx=540, cy=980)
        L.holo_torso(F, t, cy=1000, s=0.85, chest=0.3, dia=ramp(t, t_dia, t_dia + 0.4) * (0.7 + 0.3 * math.sin(t * 5)))
        L.label(F.o, t, t_dia, 540, 1640, "DIAFRAGMA", L.GRN, size=48)
        L.label(F.o, t, t_pulm, 820, 760, "PULMONES", L.CYAN, size=44)

    def tranquilo(F, t, t0):                  # 4 · respiración tranquila: baja y la barriga se mueve
        L.bg_holo(F.b, t); F.cam(1.0 + 0.04 * clamp((t - t0) / 3))
        b = slow(t, t_baja) if t > t_baja else 0
        L.holo_torso(F, t, cy=1000, s=0.85, chest=0.3 + 0.2 * b, belly=b, dia=0.8)
        L.label(F.o, t, t0 + 0.2, 540, 1560, "TRANQUILO", L.GRN, size=44)
        L.label(F.o, t, t_barriga, 540, 1660, "SE MUEVE LA BARRIGA", L.GRN, size=44)

    def estres(F, t, t0):                     # 5 · estrés: hombros y pecho, corto y rápido
        L.bg_holo(F.b, t); F.cam(1.0, dx=6 * math.sin(t * 31) * ramp(t, t_corto, t_corto + 0.2))
        f = fast(t * 1.2)
        L.holo_torso(F, t, cy=1020, s=0.85, chest=f, shoulders=f * ramp(t, t_hombros, t_hombros + 0.3), tint=L.RED)
        L.label(F.o, t, t_prisas, 540, 1560, "PRISAS + ESTRÉS", L.PINK, size=44)
        a = ramp(t, t_hombros, t_hombros + 0.3)
        if a > 0:
            for x in (250, 830): L.arrow(F.g, x, 700, x, 520, L.RED, 12, 40, a)
        L.label(F.o, t, t_pecho, 540, 1660, "CORTO Y RÁPIDO", L.RED, size=44)

    def revs(F, t, t0):                       # 6 · pasado de vueltas: cuesta desconectar
        F.cam(0.96 + 0.04 * back((t - t0) / 0.35))
        v = lerp(0.35, 0.92, ramp(t, t0, t0 + 0.8))
        L.rev_gauge(F, t, t0, v, cy=960, label_txt="PASADO DE VUELTAS")
        L.label(F.o, t, t_desc, 540, 1600, "CUESTA DESCONECTAR", L.PINK, size=44)

    def casa(F, t, t0):                       # 7 · en casa: mano en la barriga, boca cerrada, nariz
        L.bg_night(F.b); F.cam(1.0 + 0.06 * eio((t - t0) / 5), cx=540, cy=1000)
        b = slow(t, t_lento) if t > t_lento else 0.15
        L.holo_torso(F, t, cy=1000, s=0.85, chest=0.25, belly=b, dia=0.6, lamp=ramp(t, t0, t0 + 0.6),
                     hand=ramp(t, t_mano, t_mano + 0.4))
        L.label(F.o, t, t0 + 0.2, 280, 660, "AL LLEGAR A CASA", L.GOLD, size=44)
        L.label(F.o, t, t_mano, 540, 1600, "MANO EN LA BARRIGA", L.GRN, size=42)
        L.label(F.o, t, t_boca, 540, 1690, "BOCA CERRADA · NARIZ", L.CYAN, size=42)

    def sube(F, t, t0):                       # 8 · que suba la mano, no los hombros
        L.bg_night(F.b); F.cam(1.04)
        b = slow(t, t_lento)
        L.holo_torso(F, t, cy=1000, s=0.85, chest=0.25, belly=b, dia=0.8, lamp=1.0, hand=1.0,
                     ok_hand=clamp((t - t_suba) / 0.35) if t > t_suba else 0,
                     x_sh=clamp((t - t_noh) / 0.35) if t > t_noh else 0)
        L.label(F.o, t, t_suba, 540, 1640, "SUBE LA MANO", L.GRN, size=46)

    def producto(F, t, t0):                   # 9 · nariz cerrada → AirNaze (única aparición)
        if t < t_airnaze - 0.1:
            L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
            op = ramp(t, t0 + 0.8, t_airnaze)
            L.holo_nose(F, t, s=0.9, pl=lerp(0.6, -0.5, op), pr=lerp(0.6, -0.5, op))
            L.label(F.o, t, t0 + 0.3, 540, 1600, "NARIZ ALGO CERRADA", L.PINK, size=44)
        else:
            L.product_card(F, t, t_airnaze, img=None, items=["PADS POR FUERA DE LA NARIZ", "UN ARCO QUE SE CONECTA", "PARA QUE EL AIRE PASE MÁS FÁCIL"])

    def cierre(F, t, t0):                     # 10 · CTA: ¿barriga u hombros?
        def fondo(F, t, t0):
            L.bg_holo(F.b, t)
            L.holo_torso(F, t, cy=1150, s=0.7, chest=0.3, belly=slow(t, t0), dia=0.7)
        L.close_cta(F, t, t0, None, t_com, scene_draw=fondo)

    return [(0, "gancho", hook), (t_no, "no_es", no_es), (t_el, "diafragma", diafragma), (t_cuando, "tranquilo", tranquilo),
            (t_pero, "estres", estres), (t_yasi - 0.2, "revs", revs), (t_prueba, "casa", casa), (t_que, "sube", sube),
            (t_ysi - 0.2, "producto", producto), (t_q, "cierre", cierre)], end


def ACCENTS(L): return [L.A("diafragma"), L.A("pero"), L.A("hombros"), L.A("prueba")]
def CHIMES(L): return [L.A("airnaze")]
def TICKS_UNTIL(L): return L.A("no")
