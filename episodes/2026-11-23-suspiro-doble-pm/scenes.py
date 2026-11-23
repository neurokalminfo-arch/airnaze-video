# Suspiro doble para soltar el día (noche neón).
# Primitivas nuevas: air_tube (tubo de aire en dos tomas), save_cta (cierre "guárdalo").
import math

KEY = {"nariz.", "encima.", "despacio,", "largo.", "doble.", "solo", "propósito.", "llenar,", "revoluciones.", "sofá", "cama:", "airnaze", "fácil.", "guárdalo"}


def timeline(L):
    A = L.A
    t_coge = A("coge"); t_nariz = A("nariz.")
    t_y = A("y"); t_otra = A("otra"); t_encima = A("encima.")
    t_ahora = A("ahora", 5.0); t_desp = A("despacio,"); t_largo = A("largo.")
    t_eso = A("eso"); t_doble = A("doble.")
    t_tu = A("tu"); t_solo = A("solo"); t_cuenta = A("cuenta.")
    t_no = A("no"); t_raro = A("raro:"); t_prop = A("propósito.")
    t_la = A("la", t_prop); t_seg = A("segunda"); t_llenar = A("llenar,")
    t_y2 = A("y", t_llenar); t_salida = A("salida", t_y2); t_bajar = A("bajar"); t_rev = A("revoluciones.")
    t_al = A("al"); t_sofa = A("sofá"); t_cama = A("cama:"); t_dos = A("dos", t_cama); t_nariz2 = A("nariz.", t_dos)
    t_si = A("si", t_nariz2); t_airnaze = A("airnaze")
    t_guarda = A("guárdalo"); t_dormir = A("dormir.")
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp = L.clamp, L.ramp, L.back, L.eio, L.lerp

    def hook(F, t, t0):                       # 1 · prueba ahora: nariz en holograma cogiendo aire
        L.bg_holo(F.b, t); F.cam(1.0 + 0.08 * eio(t / 3), cx=540, cy=980)
        L.holo_nose(F, t, s=1.0, pl=-0.3, pr=-0.3)
        L.badge(F.o, t, 0.2, 540, 430, "AHORA", "", col=L.GRN)
        L.label(F.o, t, 0.4, 540, 1490, "PRUEBA ESTO", L.GOLD, size=44)
        L.label(F.o, t, t_coge, 540, 1600, "COGE AIRE POR LA NARIZ", L.CYAN, size=44)

    def tomas(F, t, t0):                      # 2 · tubo: 1ª toma + otra encima
        F.cam(1.0 + 0.05 * eio((t - t0) / 3), cx=540, cy=990)
        lv = lerp(0.65, 1.0, ramp(t, t_otra, t_encima + 0.3))
        L.air_tube(F, t, lv * ramp(t, t0 - 0.2, t0 + 0.6) if t < t0 + 0.6 else lv, marks=ramp(t, t0, t0 + 0.5), cx=430)
        L.label(F.o, t, t_otra, 540, 1600, "+ OTRA PEQUEÑA TOMA ENCIMA", L.GRN, size=42)

    def soltar(F, t, t0):                     # 3 · suéltalo todo, despacio, largo
        F.cam(1.04 - 0.04 * eio((t - t0) / 2.5), cx=540, cy=990)
        lv = lerp(1.0, 0.08, ramp(t, t0 + 0.2, t_eso + 0.2))
        L.air_tube(F, t, lv, out=ramp(t, t0, t0 + 0.4), cx=540, top=700)
        L.label(F.o, t, t_desp, 540, 1560, "DESPACIO", L.VIO, size=46)
        L.label(F.o, t, t_largo, 540, 1670, "LARGO", L.CYAN, size=46)

    def nombre(F, t, t0):                     # 4 · eso es un suspiro doble
        L.stat(F, t, t0 + 0.1, "2 + 1", "dos tomas · una salida larga", col=L.CYAN, y=920)
        L.label(F.o, t, t_doble - 0.2, 540, 1460, "SUSPIRO DOBLE", L.GRN, size=56)

    def cuerpo(F, t, t0):                     # 5 · tu cuerpo ya lo hace solo
        L.bg_holo(F.b, t); F.cam(1.0 + 0.05 * eio((t - t0) / 4), cx=540, cy=1050)
        ph = ((t - t0) % 2.6) / 2.6
        ch = 0.25 + 0.75 * (ramp(ph, 0.0, 0.25) * 0.7 + ramp(ph, 0.3, 0.4) * 0.3) * (1 - ramp(ph, 0.45, 1.0))
        L.holo_torso(F, t, cy=1080, s=0.85, chest=ch, belly=0.3 * ch)
        L.label(F.o, t, t_solo, 540, 1650, "TU CUERPO YA LO HACE SOLO", L.GOLD, size=42)
        L.label(F.o, t, t_cuenta - 0.3, 540, 1750, "SIN QUE TE DES CUENTA", L.VIO, size=38)

    def vida(F, t, t0):                       # 6 · de toda la vida, pero a propósito: ondas que se calman
        F.cam(1.0)
        L.waves(F, t, phase_shift=(t - t0) * 0.6, bed=False, amp=lerp(260, 120, ramp(t, t_raro, t_prop + 0.5)), base=1150, speed=60)
        L.label(F.o, t, t_raro - 0.2, 540, 560, "NO ES UN TRUCO RARO", L.PINK, size=44)
        L.label(F.o, t, t_prop - 0.4, 540, 1640, "DE TODA LA VIDA · A PROPÓSITO", L.GRN, size=42)

    def llenar(F, t, t0):                     # 7 · la 2ª toma termina de llenar
        F.cam(1.0 + 0.06 * eio((t - t0) / 2), cx=540, cy=700)
        L.air_tube(F, t, lerp(0.65, 1.0, ramp(t, t_seg, t_llenar + 0.4)), marks=1.0, cx=430)
        L.label(F.o, t, t_llenar - 0.2, 540, 1600, "TERMINA DE LLENAR", L.GRN, size=46)

    def revol(F, t, t0):                      # 8 · la salida larga: bajar revoluciones
        v = lerp(0.9, 0.25, ramp(t, t_bajar, t_rev + 0.8))
        L.rev_gauge(F, t, t0, v)
        L.label(F.o, t, t_salida, 540, 1520, "SALIDA LARGA", L.CYAN, size=44)
        L.label(F.o, t, t_bajar, 540, 1630, "BAJAR REVOLUCIONES", L.GRN, size=44)

    def casa(F, t, t0):                       # 9 · al llegar a casa, en el sofá
        L.bg_night(F.b); F.cam(1.0 + 0.05 * eio((t - t0) / 2), cx=540, cy=1000)
        ph = ((t - t0) % 2.2) / 2.2
        ch = 0.3 + 0.7 * ramp(ph, 0, 0.35) * (1 - ramp(ph, 0.4, 1))
        L.holo_torso(F, t, cy=1060, s=0.82, chest=ch, belly=0.4 * ch, lamp=1.0, tint=L.CYAN)
        L.label(F.o, t, t_al, 540, 520, "AL LLEGAR A CASA", L.GOLD, size=44)
        L.label(F.o, t, t_sofa, 540, 1660, "EN EL SOFÁ", L.VIO, size=44)

    def cama(F, t, t0):                       # 10 · o ya en la cama: 2 o 3 por la nariz
        F.cam(1.0 + 0.05 * eio((t - t0) / 3), cx=540, cy=1000)
        L.bedroom(F, t, clock_glow=0.6, nose_air=ramp(t, t_dos, t_dos + 0.5))
        L.badge(F.o, t, t_dos, 540, 420, "2–3", "suspiros", col=L.CYAN)
        L.label(F.o, t, t_nariz2 - 0.3, 540, 1600, "POR LA NARIZ", L.GRN, size=46)

    def producto(F, t, t0):                   # 11 · nariz algo cerrada → AirNaze (única aparición)
        if t < t_airnaze - 0.1:
            L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
            L.holo_nose(F, t, s=0.9, pl=0.6, pr=0.6)
            L.label(F.o, t, t0 + 0.3, 540, 1600, "NARIZ ALGO CERRADA", L.PINK, size=44)
        else:
            L.product_card(F, t, t_airnaze, img=None, items=["PADS POR FUERA DE LA NARIZ", "UN ARCO QUE SE CONECTA", "PARA QUE EL AIRE PASE MÁS FÁCIL"])

    def cierre(F, t, t0):                     # 12 · CTA guardar
        def fondo(F, t, t0):
            L.bg_holo(F.b, t)
            L.waves(F, t, phase_shift=t * 0.5, bed=False, amp=90, base=1650, speed=40)
        L.save_cta(F, t, t0, t_guarda + 0.3, scene_draw=fondo, txt="guárdalo para esta noche")

    return [(0, "gancho", hook), (t_y - 0.1, "tomas", tomas), (t_ahora - 0.1, "soltar", soltar), (t_eso, "nombre", nombre),
            (t_tu, "cuerpo", cuerpo), (t_no, "vida", vida), (t_la, "llenar", llenar), (t_y2, "revol", revol),
            (t_al, "casa", casa), (t_o_cama(L, t_sofa), "cama", cama), (t_si - 0.2, "producto", producto),
            (t_guarda - 0.1, "cierre", cierre)], end


def t_o_cama(L, after):
    return L.A("o", after)


def ACCENTS(L): return [L.A("encima."), L.A("doble."), L.A("revoluciones."), L.A("cama:")]
def CHIMES(L): return [L.A("airnaze")]
