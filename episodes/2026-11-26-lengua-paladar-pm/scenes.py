# ¿Dónde tienes la lengua? Postura de reposo para respirar por la nariz (noche neón).
# Primitivas nuevas: mouth_profile (corte de perfil con paladar, lengua y vías de aire) y breath_counter (5 respiraciones).
import math

KEY = {"lengua", "abajo", "abrirse", "labios", "apretar", "paladar", "solo", "reposo", "cansancio", "cinco", "airnaze", "arriba"}


def timeline(L):
    A = L.A
    t_lengua = A("lengua"); t_fijate = A("fíjate")
    t_si = A("si"); t_abajo = A("abajo"); t_abrirse = A("abrirse")
    t_prueba = A("prueba"); t_labios = A("labios"); t_dientes = A("dientes", t_labios); t_lengua2 = A("lengua", t_labios); t_paladar = A("paladar")
    t_ahora = A("ahora", t_paladar); t_notas = A("notas"); t_solo = A("solo")
    t_esa = A("esa"); t_reposo = A("reposo")
    t_al = A("al", t_reposo); t_cansancio = A("cansancio"); t_cae = A("cae"); t_abre = A("abre"); t_ahi = A("ahí")
    t_esta = A("esta", t_ahi); t_coloca = A("colócala"); t_cinco = A("cinco"); t_nariz3 = A("nariz", t_cinco)
    t_y = A("y", t_nariz3); t_cerrada = A("cerrada"); t_airnaze = A("airnaze")
    t_comenta = A("comenta"); t_arriba = A("arriba", t_comenta); t_abajo2 = A("abajo", t_comenta); t_donde = A("dónde", t_comenta)
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp, mix = L.clamp, L.ramp, L.back, L.eio, L.lerp, L.mix

    def hook(F, t, t0):                       # 1 · ¿dónde tienes la lengua? (perfil con interrogación)
        L.bg_holo(F.b, t); F.cam(1.0 + 0.08 * eio(t / 3.0), cx=480, cy=980)
        L.mouth_profile(F, t, cx=600, cy=1000, s=1.05, tongue=0.5 + 0.08 * math.sin(t * 3), lips=1.0, q=ramp(t, t_lengua - 0.2, t_lengua + 0.2), tongue_col=L.GOLD)
        L.label(F.o, t, t_lengua, 540, 1600, "¿DÓNDE ESTÁ TU LENGUA?", L.GOLD, size=50)
        L.label(F.o, t, t_fijate, 540, 1720, "SIN MOVERLA", L.VIO, size=44)

    def abajo(F, t, t0):                      # 2 · lengua abajo → la boca se abre sola
        L.bg_holo(F.b, t); F.cam(1.0 + 0.05 * eio((t - t0) / 3), cx=420, cy=1000)
        op = ramp(t, t_abrirse - 0.3, t_abrirse + 0.5)
        L.mouth_profile(F, t, cx=620, cy=980, s=1.0, tongue=0.0, lips=1 - op, mouth_air=op)
        L.label(F.o, t, t_abajo, 540, 470, "LENGUA ABAJO", L.PINK, size=52)
        L.label(F.o, t, t_abrirse - 0.2, 540, 1620, "LA BOCA SE ABRE SOLA", L.RED, size=46)

    def pasos(F, t, t0):                      # 3 · prueba: 3 pasos que se marcan
        L.bg_night(F.b); F.cam(1.0 + 0.03 * eio((t - t0) / 4))
        L.badge(F.o, t, t_prueba, 540, 500, "PRUEBA", "", col=L.GOLD)
        L.checklist(F, t, ["LABIOS CERRADOS", "DIENTES SIN APRETAR", "LENGUA AL PALADAR"], [t_labios, t_dientes, t_lengua2], y0=820, gap=220, col=L.CYAN)

    def sube(F, t, t0):                       # 4 · la lengua sube al paladar y el aire entra por la nariz
        L.bg_holo(F.b, t); F.cam(1.0 + 0.06 * eio((t - t0) / 3.5), cx=420, cy=950)
        k = ramp(t, t0, t0 + 0.8)
        L.mouth_profile(F, t, cx=620, cy=980, s=1.0, tongue=k, lips=1.0, nose_air=ramp(t, t_ahora, t_ahora + 0.6))
        L.label(F.o, t, t0 + 0.3, 540, 470, "LENGUA ARRIBA", L.CYAN, size=52)
        L.label(F.o, t, t_solo - 0.4, 540, 1620, "EL AIRE ENTRA CASI SOLO", L.GRN, size=44)

    def reposo(F, t, t0):                     # 5 · postura de reposo: la nariz trabaja (holograma de la nariz)
        L.bg_holo(F.b, t); F.cam(0.95 + 0.07 * eio((t - t0) / 3))
        L.holo_nose(F, t, s=0.95, pl=-0.3, pr=-0.3)
        L.label(F.o, t, t_reposo - 0.3, 540, 1600, "POSTURA DE REPOSO", L.GRN, size=54)

    def cansancio(F, t, t0):                  # 6 · al final del día la lengua se cae y respiras por la boca (dormitorio)
        F.cam(1.0 + 0.06 * eio((t - t0) / 4), cx=700, cy=1100)
        op = ramp(t, t_abre - 0.3, t_abre + 0.4)
        L.bedroom(F, t, head_glow=(L.PINK, 0.5 * op), mouth=op, mouth_air=op)
        L.label(F.o, t, t_cansancio, 540, 470, "CANSANCIO", L.GOLD, size=52)
        L.label(F.o, t, t_cae - 0.1, 540, 1600, "LA LENGUA SE CAE", L.PINK, size=48)
        L.label(F.o, t, t_abre, 540, 1720, "Y RESPIRAS POR LA BOCA", L.RED, size=42)

    def noche(F, t, t0):                      # 7 · esta noche en la cama: lengua arriba + 5 respiraciones lentas
        F.cam(1.0 + 0.04 * eio((t - t0) / 5), cx=700, cy=1000)
        L.bedroom(F, t, head_glow=(L.CYAN, 0.5), mouth=0.0, nose_air=1.0)
        n = lerp(0, 5, ramp(t, t_cinco, t_nariz3 + 0.6))
        L.breath_counter(F, t, n, cy=1500)
        L.label(F.o, t, t_coloca, 540, 470, "LENGUA ARRIBA", L.CYAN, size=52)
        L.label(F.o, t, t_cinco, 540, 1680, "5 RESPIRACIONES LENTAS", L.GRN, size=44)

    def producto(F, t, t0):                   # 8 · nariz algo cerrada → AirNaze (única aparición)
        if t < t_airnaze - 0.1:
            L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
            L.holo_nose(F, t, s=0.9, pl=0.6, pr=0.6)
            L.label(F.o, t, t_cerrada - 0.3, 540, 1600, "NARIZ ALGO CERRADA", L.PINK, size=44)
        else:
            L.product_card(F, t, t_airnaze, img=None, items=["PADS POR FUERA DE LA NARIZ", "UN ARCO QUE SE CONECTA", "PARA QUE EL AIRE PASE"])

    def cierre(F, t, t0):                     # 9 · comenta ARRIBA o ABAJO
        def fondo(F, t, t0):
            L.bg_holo(F.b, t)
            L.mouth_profile(F, t, cx=560, cy=1100, s=0.66, tongue=0.5 + 0.5 * math.sin(t * 2.0), lips=1.0, col=L.VIO)
            L.label(F.o, t, t_arriba, 300, 1500, "ARRIBA", L.CYAN, size=64)
            L.label(F.o, t, t_abajo2, 780, 1500, "ABAJO", L.PINK, size=64)
        L.close_cta(F, t, t0, None, t_donde, scene_draw=fondo)

    return [(0, "gancho", hook), (t_si - 0.1, "abajo", abajo), (t_prueba - 0.1, "pasos", pasos), (t_ahora - 0.1, "sube", sube),
            (t_esa - 0.1, "reposo", reposo), (t_al - 0.1, "cansancio", cansancio), (t_esta - 0.1, "noche", noche),
            (t_y - 0.1, "producto", producto), (t_comenta - 0.2, "cierre", cierre)], end


def ACCENTS(L): return [L.A("lengua"), L.A("abrirse"), L.A("paladar"), L.A("reposo"), L.A("cinco")]
def CHIMES(L): return [L.A("airnaze")]
