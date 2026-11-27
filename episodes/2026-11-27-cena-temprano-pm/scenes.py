# Cena fuerte del viernes y a la cama del tirón: el error típico (noche neón).
# Primitivas nuevas: pizza_plate (plato con pizza y vapor) y engine_gear (motor encendido en la tripa).
import math

KEY = {"error", "motor", "encendido", "digestión", "desconectar", "vueltas", "horas", "ligero", "paseo", "cocina", "nariz", "airnaze", "guárdalo"}


def timeline(L):
    A = L.A
    t_cena = A("cena"); t_cama = A("cama"); t_error = A("error")
    t_tumbarte = A("tumbarte"); t_llena = A("llena"); t_motor = A("motor"); t_encendido = A("encendido")
    t_tu = A("tu"); t_digestion = A("digestión"); t_desconectar = A("desconectar")
    t_por = A("por", t_desconectar); t_vueltas = A("vueltas"); t_pesado = A("pesado")
    t_el = A("el", t_pesado); t_cena2 = A("cena", t_el); t_horas = A("horas"); t_ligero = A("ligero")
    t_despues = A("después"); t_nada = A("nada", t_despues); t_sofa = A("sofá"); t_paseo = A("paseo"); t_cocina = A("cocina")
    t_ya = A("ya", t_cocina); t_lento = A("lento", t_ya)
    t_y = A("y", t_lento); t_cerrada = A("cerrada"); t_airnaze = A("airnaze")
    t_guardalo = A("guárdalo"); t_pizza = A("pizza", t_guardalo)
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp, mix = L.clamp, L.ramp, L.back, L.eio, L.lerp, L.mix

    def hook(F, t, t0):                       # 1 · pizza humeante → a la cama del tirón
        L.bg_holo(F.b, t); F.cam(1.0 + 0.08 * eio(t / 3.0), cy=950)
        k = L.back(t / 0.35)
        L.pizza_plate(F.g, t, cx=540, cy=900, s=1.05 * k, slices=8, steam=1.0)
        if t > t_cama - 0.1:
            L.bed_icon(F.g, 540, 1300, 0.0, 1.0)
        L.label(F.o, t, 0.05, 540, 470, "CENA FUERTE", L.GOLD, size=60)
        L.label(F.o, t, t_cama - 0.1, 540, 1580, "+ A LA CAMA DEL TIRÓN", L.PINK, size=46)
        L.label(F.o, t, t_error - 0.1, 540, 1700, "EL ERROR TÍPICO", L.RED, size=50)

    def motor(F, t, t0):                      # 2 · tripa llena = motor encendido (busto con engranaje)
        F.cam(1.0 + 0.06 * eio((t - t0) / 3), cy=1000)
        L.holo_torso(F, t, cx=540, cy=1000, s=1.0, belly=0.35, tint=L.VIO, lamp=0.5)
        on = ramp(t, t_motor - 0.2, t_encendido + 0.2)
        L.engine_gear(F.g, t, 540, 1160, r=110, speed=0.3 + 2.5 * on, col=L.mix(L.GOLD, L.RED, on), glow=on)
        L.label(F.o, t, t_llena - 0.2, 540, 470, "TRIPA LLENA", L.GOLD, size=56)
        L.label(F.o, t, t_motor, 540, 1650, "MOTOR ENCENDIDO", L.RED, size=54)

    def trabaja(F, t, t0):                    # 3 · digestión a tope cuando quieres desconectar (cuentarrevoluciones)
        F.cam(1.0 + 0.04 * eio((t - t0) / 3))
        v = 0.55 + 0.3 * ramp(t, t_digestion - 0.2, t_digestion + 0.5)
        L.rev_gauge(F, t, t0, v, cy=950, label_txt=None)
        L.label(F.o, t, t_digestion - 0.1, 540, 470, "DIGESTIÓN A TOPE", L.RED, size=54)
        L.label(F.o, t, t_desconectar - 0.2, 540, 1500, "Y TÚ QUIERES DESCONECTAR", L.CYAN, size=44)

    def vueltas(F, t, t0):                    # 4 · das vueltas en la cama
        F.cam(1.0 + 0.05 * eio((t - t0) / 3), cx=700, cy=1100)
        L.bedroom(F, t, head_glow=(L.PINK, 0.45), shake=0.6 * ramp(t, t_vueltas - 0.2, t_vueltas + 0.3))
        L.label(F.o, t, t_vueltas - 0.1, 540, 470, "DAS VUELTAS", L.PINK, size=56)
        L.label(F.o, t, t_pesado - 0.3, 540, 1650, "TE NOTAS PESADO", L.RED, size=50)

    def horas(F, t, t0):                      # 5 · truco: cena un par de horas antes (dos relojes) y más ligero
        L.bg_night(F.b); F.cam(1.0 + 0.03 * eio((t - t0) / 4))
        L.label(F.o, t, t_el, 540, 470, "EL TRUCO", L.GRN, size=58)
        k1 = back((t - t_cena2) / 0.35)
        if t > t_cena2 - 0.05:
            F.g.save(); F.g.translate(290, 860); F.g.scale(k1 * 0.8, k1 * 0.8); L.clock(F.g, 0, 0, 160, 21.0); F.g.restore()
            L.label(F.o, t, t_cena2, 290, 1110, "CENA", L.GOLD, size=46)
        if t > t_horas - 0.25:
            p = ramp(t, t_horas - 0.25, t_horas + 0.4)
            F.g.set_source_rgba(*L.CYAN, 0.9); F.g.set_line_width(8); F.g.set_line_cap(1)
            F.g.move_to(430, 860); F.g.line_to(L.lerp(430, 650, p), 860); F.g.stroke()
            L.label(F.o, t, t_horas - 0.2, 540, 790, "2 H", L.CYAN, size=50)
            k2 = back((t - t_horas) / 0.35)
            F.g.save(); F.g.translate(790, 860); F.g.scale(k2 * 0.8, k2 * 0.8); L.clock(F.g, 0, 0, 160, 23.0); F.g.restore()
            L.label(F.o, t, t_horas, 790, 1110, "CAMA", L.CYAN, size=46)
        sl = 8 - 5 * ramp(t, t_ligero - 0.3, t_ligero + 0.3)
        L.pizza_plate(F.g, t, cx=540, cy=1420, s=0.6, slices=sl, steam=0.6)
        L.label(F.o, t, t_ligero - 0.1, 540, 1660, "MÁS LIGERO", L.GRN, size=50)

    def despues(F, t, t0):                    # 6 · después: sofá tumbado ✗ → paseo corto / recoger la cocina ✓
        L.bg_holo(F.b, t); F.cam(1.0 + 0.03 * eio((t - t0) / 4))
        L.label(F.o, t, t_despues - 0.1, 540, 470, "DESPUÉS", L.GOLD, size=58)
        L.label(F.o, t, t_despues + 0.25, 540, 700, "✗  SOFÁ TUMBADO", L.RED, size=50)
        L.checklist(F, t, ["PASEO CORTO", "RECOGER LA COCINA"], [t_paseo, t_cocina], y0=960, gap=220, col=L.GRN)
        if t > t_paseo:
            L.sneaker(F.g, 540, 1500, s=0.9, col=L.CYAN, a=clamp((t - t_paseo) / 0.3), ang=0.05 * math.sin(t * 6))

    def cama(F, t, t0):                       # 7 · ya en la cama: respira lento por la nariz
        F.cam(1.0 + 0.05 * eio((t - t0) / 4), cx=700, cy=1050)
        L.bedroom(F, t, head_glow=(L.CYAN, 0.5), nose_air=1.0)
        L.label(F.o, t, t_ya, 540, 470, "YA EN LA CAMA", L.CYAN, size=56)
        L.label(F.o, t, t_lento - 0.1, 540, 1650, "RESPIRA LENTO POR LA NARIZ", L.GRN, size=42)

    def producto(F, t, t0):                   # 8 · nariz algo cerrada → AirNaze (única aparición)
        if t < t_airnaze - 0.1:
            L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
            L.holo_nose(F, t, s=0.9, pl=0.6, pr=0.6)
            L.label(F.o, t, t_cerrada - 0.3, 540, 1600, "NARIZ ALGO CERRADA", L.PINK, size=44)
        else:
            L.product_card(F, t, t_airnaze, img=None, items=["PADS POR FUERA DE LA NARIZ", "UN ARCO QUE SE CONECTA", "PARA QUE EL AIRE PASE"])

    def cierre(F, t, t0):                     # 9 · guárdalo para el próximo viernes de pizza
        def fondo(F, t, t0):
            L.bg_holo(F.b, t)
            L.pizza_plate(F.g, t, cx=540, cy=1500, s=0.55, slices=8, steam=0.8, a=0.7)
            L.label(F.o, t, t_pizza - 0.3, 540, 1750, "PRÓXIMO VIERNES DE PIZZA", L.GOLD, size=42)
        L.save_cta(F, t, t0, t_guardalo + 0.3, scene_draw=fondo)

    return [(0, "gancho", hook), (t_tumbarte - 0.1, "motor", motor), (t_tu - 0.1, "trabaja", trabaja), (t_por - 0.1, "vueltas", vueltas),
            (t_el - 0.1, "horas", horas), (t_despues - 0.15, "despues", despues), (t_ya - 0.1, "cama", cama),
            (t_y - 0.1, "producto", producto), (t_guardalo - 0.2, "cierre", cierre)], end


def ACCENTS(L): return [L.A("error"), L.A("motor"), L.A("vueltas"), L.A("horas"), L.A("paseo")]
def CHIMES(L): return [L.A("airnaze")]
