# Así se usa (convertir): primeras noches con AirNaze, empezar por el nivel más suave (noche neón).
# Primitivas nuevas: level_stairs (escalera de niveles), checklist (pasos con ✓), sneaker (zapatilla).
import math

KEY = {"error", "fuerte.", "zapatillas", "maratón.", "niveles,", "suave.", "seca,", "pads", "arco.", "rutina.", "nivel.", "quince", "perfil.", "comentarios."}


def timeline(L):
    A = L.A
    t_fuerte = A("fuerte."); t_es = A("es", t_fuerte); t_zap = A("zapatillas"); t_mar = A("maratón.")
    t_air2 = A("airnaze", t_es); t_poco = A("poco", t_air2)
    t_emp = A("empieza"); t_suave = A("suave.")
    t_antes = A("antes"); t_nariz = A("nariz", t_antes); t_pegas = A("pegas"); t_conectas = A("conectas"); t_nada = A("nada")
    t_las = A("las", t_nada); t_notaras = A("notarás."); t_rutina = A("rutina.")
    t_y = A("y", t_rutina); t_comodo = A("cómodo,"); t_subes = A("subes")
    t_pack = A("el", A("nivel.", t_subes)); t_envio = A("envío"); t_dev = A("devolución."); t_tienes = A("tienes")
    t_q = A("por", A("perfil.")); t_com = A("comentarios.", t_q)
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp = L.clamp, L.ramp, L.back, L.eio, L.lerp

    def hook(F, t, t0):                       # 1 · salto del nivel 1 al 3: el error
        L.bg_holo(F.b, t); F.cam(1.0 + 0.06 * eio(t / 4), cx=540, cy=1000)
        jump = ramp(t, 1.2, t_fuerte + 0.2)
        L.level_stairs(F, t, active=1 + 2 * jump, jump=jump if jump < 1 else 0)
        L.label(F.o, t, 0.15, 540, 470, "ERROR TÍPICO", L.RED, size=54)
        L.label(F.o, t, 1.0, 540, 1430, "LA PRIMERA NOCHE", L.GOLD, size=44)
        L.label(F.o, t, t_fuerte - 0.3, 540, 1560, "NIVEL MÁS FUERTE", L.RED, size=48)

    def zapas(F, t, t0):                      # 2 · zapatillas nuevas en una maratón
        L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
        bob = 30 * abs(math.sin((t - t0) * 5))
        L.sneaker(F.g, 540, 1000 - bob, 1.7, L.mix(L.CYAN, L.RED, ramp(t, t_mar, t_mar + 0.4)), ang=-0.08)
        for i in range(5):
            x = (900 - ((t - t0) * 600 + i * 220)) % 1100 - 40
            F.g.set_source_rgba(*L.VIO, 0.5); F.g.set_line_width(6); F.g.move_to(x, 1180); F.g.line_to(x + 90, 1180); F.g.stroke()
        L.label(F.o, t, t_zap, 540, 1430, "ZAPATILLAS NUEVAS", L.CYAN, size=46)
        L.label(F.o, t, t_mar, 540, 1560, "¿EN UNA MARATÓN?", L.RED, size=50)

    def niveles(F, t, t0):                    # 3 · hay niveles: poco a poco
        L.bg_holo(F.b, t); F.cam(1.0 + 0.04 * eio((t - t0) / 3), cx=540, cy=1000)
        a = 1 + 2 * (0.5 - 0.5 * math.cos((t - t0) * 2.2))
        L.level_stairs(F, t, active=a)
        L.label(F.o, t, t0 + 0.2, 540, 470, "AIRNAZE TIENE NIVELES", L.VIO, size=46)
        L.label(F.o, t, t_poco, 540, 1430, "POCO A POCO", L.CYAN, size=50)

    def suave(F, t, t0):                      # 4 · empieza por el más suave
        L.bg_holo(F.b, t); F.cam(1.0 + 0.10 * eio((t - t0) / 2.5), cx=290, cy=1100)
        L.level_stairs(F, t, active=1, cols=(L.GRN, L.mix(L.GOLD, L.VIO, 0.6), L.mix(L.RED, L.VIO, 0.6)))
        L.label(F.o, t, t_suave - 0.2, 540, 1500, "EMPIEZA POR EL MÁS SUAVE", L.GRN, size=46)

    def rutina(F, t, t0):                     # 5 · antes de dormir: 3 pasos con ✓
        L.bg_night(F.b); F.cam(1.0)
        F.b.set_source(L.rad(540, 1000, 20, 800, [(0, (*L.GOLD, 0.18)), (1, (*L.GOLD, 0))])); F.b.paint()
        L.checklist(F, t, ["Nariz limpia y seca", "Pads por fuera", "Conecta el arco"], [t_nariz, t_pegas, t_conectas], y0=820, gap=210)
        L.label(F.o, t, t0 + 0.1, 540, 520, "ANTES DE DORMIR", L.GOLD, size=48)
        L.label(F.o, t, t_nada, 540, 1560, "NADA MÁS", L.GRN, size=50)

    def noches(F, t, t0):                     # 6 · las primeras noches → parte de tu rutina
        F.cam(1.0 + 0.06 * eio((t - t0) / 4), cx=540, cy=1000)
        L.bedroom(F, t, head_glow=(L.mix(L.GOLD, L.CYAN, ramp(t, t_rutina - 0.6, t_rutina)), 0.45), nose_air=ramp(t, t0, t0 + 1), clock_glow=1.0)
        L.label(F.o, t, t_notaras - 0.3, 540, 470, "LAS PRIMERAS NOCHES LO NOTAS", L.GOLD, size=40)
        L.label(F.o, t, t_rutina - 0.4, 540, 1560, "LUEGO, PARTE DE TU RUTINA", L.CYAN, size=44)

    def subes(F, t, t0):                      # 7 · cómodo → subes un nivel
        L.bg_holo(F.b, t); F.cam(1.0 + 0.04 * eio((t - t0) / 3), cx=540, cy=1000)
        L.level_stairs(F, t, active=1 + ramp(t, t_subes, t_subes + 0.6))
        L.label(F.o, t, t_comodo, 540, 470, "CUANDO ESTÉS CÓMODO", L.GRN, size=46)
        L.label(F.o, t, t_subes, 540, 1430, "SUBES UN NIVEL", L.CYAN, size=52)

    def producto(F, t, t0):                   # 8 · AirNaze: pack de bienvenida
        L.product_card(F, t, t0, img=None, items=["PACK DE BIENVENIDA · 15 DÍAS", "ENVÍO GRATIS", "30 DÍAS DE DEVOLUCIÓN"], y=880)
        L.label(F.o, t, t_tienes, 540, 1690, "ENLACE EN EL PERFIL", L.GRN, size=46)

    def cierre(F, t, t0):                     # 9 · CTA
        def fondo(F, t, t0):
            L.bg_holo(F.b, t)
            L.level_stairs(F, t, active=1 + 2 * (0.5 - 0.5 * math.cos((t - t0) * 1.6)), cx=360, base=1780, s=0.55)
        L.close_cta(F, t, t0, None, t_com, scene_draw=fondo)

    return [(0, "gancho", hook), (t_es, "zapatillas", zapas), (t_air2, "niveles", niveles), (t_emp, "suave", suave),
            (t_antes, "rutina", rutina), (t_las, "noches", noches), (t_y, "subes", subes), (t_pack, "producto", producto),
            (t_q, "cierre", cierre)], end


def ACCENTS(L): return [L.A("fuerte."), L.A("maratón."), L.A("pegas"), L.A("conectas"), L.A("subes")]
def CHIMES(L): return [L.A("el", L.A("nivel.", L.A("subes")))]
