# Descanso entre series: la nariz como cronómetro (noche neón).
# Primitivas nuevas: athlete (deportista que jadea doblado / camina erguido) y nose_stopwatch (cronómetro con nariz).
import math

KEY = {"doblado,", "boca.", "toca.", "cronómetro", "dispara.", "revoluciones.", "camina", "despacio.", "siguiente", "airnaze", "sudor.", "guárdalo"}


def timeline(L):
    A = L.A
    t_doblado = A("doblado,"); t_jade = A("jadeando")
    t_prueba = A("prueba"); t_cierra = A("cierra")
    t_si = A("si", t_cierra); t_toca = A("toca.")
    t_tu = A("tu", t_toca); t_crono = A("cronómetro")
    t_al = A("al", t_crono); t_dispara = A("dispara.")
    t_si2 = A("si", t_dispara); t_cuesta = A("cuesta"); t_revol = A("revoluciones.")
    t_asi = A("así"); t_camina = A("camina")
    t_inspira = A("inspira"); t_suelta = A("suelta"); t_despacio = A("despacio.")
    t_cuando = A("cuando"); t_comodo = A("cómodo,"); t_sig = A("siguiente")
    t_y = A("y", t_sig + 0.3); t_cerrada = A("cerrada,"); t_airnaze = A("airnaze"); t_sudor = A("sudor.")
    t_guarda = A("guárdalo")
    end = L.last_end() + 1.2
    clamp, ramp, back, eio, lerp = L.clamp, L.ramp, L.back, L.eio, L.lerp

    def gym_bg(F, t, warm=1.0):
        L.bg_night(F.b)
        F.b.set_source(L.rad(540, 1500, 20, 900, [(0, (1, 0.42, 0.75, 0.22 * warm)), (1, (1, 0.42, 0.75, 0))])); F.b.paint()
        F.b.set_source_rgba(0.12, 0.08, 0.24, 1); F.b.rectangle(0, 1420, L.W, L.H - 1420); F.b.fill()
        F.g.set_source_rgba(*L.VIO, 0.7); F.g.set_line_width(4); F.g.move_to(0, 1420); F.g.line_to(L.W, 1420); F.g.stroke()
        for i, x in enumerate((140, 940)):           # rack de mancuernas al fondo
            L.dumbbell(F.g, x, 1360, 0.6, 0.0, L.GOLD, 0.35)

    def hook(F, t, t0):                       # 1 · doblado jadeando por la boca
        F.cam(1.0 + 0.08 * eio(t / 3.5), cx=420, cy=1100)
        gym_bg(F, t)
        L.athlete(F, t, pose=0.0, cx=600, mouth_air=1.0, pant=1.0)
        L.label(F.o, t, t_doblado - 0.1, 540, 1600, "DOBLADO", L.PINK, size=50)
        L.label(F.o, t, t_jade, 540, 1720, "Y JADEANDO POR LA BOCA", L.RED, size=42)

    def cierra(F, t, t0):                     # 2 · prueba: cierra la boca (el aire entra por la nariz)
        F.cam(1.0 + 0.05 * eio((t - t0) / 3), cx=420, cy=900)
        gym_bg(F, t, 0.6)
        k = ramp(t, t_cierra, t_cierra + 0.5)
        L.athlete(F, t, pose=0.35 * k, cx=600, mouth_air=1 - k, nose_air=k, pant=1 - 0.6 * k, col=L.mix(L.PINK, L.CYAN, k))
        L.badge(F.o, t, t_prueba, 540, 440, "PRUEBA", "", col=L.GOLD)
        L.label(F.o, t, t_cierra, 540, 1620, "CIERRA LA BOCA", L.CYAN, size=52)

    def notoca(F, t, t0):                     # 3 · si aún no puedes por la nariz: todavía no te toca
        L.bg_holo(F.b, t); F.cam(1.0 + 0.04 * eio((t - t0) / 3))
        L.nose_stopwatch(F, t, 0.18 + 0.04 * math.sin(t * 3), cy=960, R=300)
        L.label(F.o, t, t0 + 0.2, 540, 470, "¿AÚN NO PUEDES?", L.PINK, size=50)
        L.label(F.o, t, t_toca - 0.3, 540, 1600, "TODAVÍA NO TE TOCA", L.PINK, size=48)

    def crono(F, t, t0):                      # 4 · tu nariz es el cronómetro del descanso
        L.bg_holo(F.b, t); F.cam(1.0 + 0.07 * eio((t - t0) / 3), cy=960)
        L.nose_stopwatch(F, t, lerp(0.2, 1.0, ramp(t, t_crono - 0.2, t_al - 0.2)), cy=960, R=320)
        L.label(F.o, t, t_crono, 540, 1580, "EL CRONÓMETRO", L.GRN, size=54)
        L.label(F.o, t, t_crono + 0.4, 540, 1700, "DEL DESCANSO", L.GRN, size=46)

    def dispara(F, t, t0):                    # 5 · al acabar la serie la respiración se dispara (pulso de neón)
        L.bg_holo(F.b, t); F.cam(1.0 + 0.03 * math.sin(t * 6))
        drop = ramp(t, t0, t0 + 0.5)
        L.dumbbell(F.g, 540, lerp(650, 820, drop), 1.4, 0.15 * drop, L.GOLD, 1.0)
        k = ramp(t, t_dispara - 0.6, t_dispara + 0.2)
        L.pulse_line(F, t, y=1220, rate=lerp(1.2, 3.2, k), amp=lerp(0.6, 1.2, k), col=L.mix(L.GOLD, L.RED, k))
        L.label(F.o, t, t0 + 0.2, 540, 470, "FIN DE LA SERIE", L.GOLD, size=46)
        L.label(F.o, t, t_dispara - 0.3, 540, 1620, "LA RESPIRACIÓN SE DISPARA", L.RED, size=42)

    def revol(F, t, t0):                      # 6 · jadeando por la boca cuesta más bajar de revoluciones
        F.cam(1.0 + 0.05 * eio((t - t0) / 3))
        L.rev_gauge(F, t, t0, 0.9 - 0.12 * ramp(t, t_cuesta, t_revol + 0.5))
        L.label(F.o, t, t0 + 0.15, 540, 470, "SIGUES POR LA BOCA", L.PINK, size=46)
        L.label(F.o, t, t_cuesta, 540, 1600, "CUESTA MÁS BAJAR", L.RED, size=48)

    def camina(F, t, t0):                     # 7 · termina la serie y camina un poco
        F.cam(1.0 + 0.05 * eio((t - t0) / 4), cx=540, cy=1000)
        gym_bg(F, t, 0.4)
        k = ramp(t, t0, t_camina)
        L.athlete(F, t, pose=0.35 + 0.65 * k, walk=ramp(t, t_camina - 0.2, t_camina + 0.3), cx=560, col=L.mix(L.PINK, L.CYAN, k), pant=0.4 * (1 - k))
        L.label(F.o, t, t_asi, 540, 440, "TERMINA LA SERIE", L.GOLD, size=46)
        L.label(F.o, t, t_camina, 540, 1620, "CAMINA UN POCO", L.CYAN, size=52)

    def respira(F, t, t0):                    # 8 · inspira por la nariz, suelta despacio (pulso que se calma)
        F.cam(1.0 + 0.04 * eio((t - t0) / 4), cx=420, cy=900)
        gym_bg(F, t, 0.3)
        L.athlete(F, t, pose=1.0, walk=0.6, cx=600, floor=1300, s=0.85, col=L.CYAN, nose_air=1.0)
        k = ramp(t, t_suelta, t_despacio + 0.6)
        L.pulse_line(F, t, y=1560, rate=lerp(2.2, 1.0, k), amp=lerp(0.7, 0.35, k), col=L.mix(L.PINK, L.CYAN, k), a=0.9)
        L.label(F.o, t, t_inspira, 540, 420, "INSPIRA POR LA NARIZ", L.CYAN, size=46)
        L.label(F.o, t, t_suelta, 540, 520, "SUELTA DESPACIO", L.GRN, size=46)

    def siguiente(F, t, t0):                  # 9 · respiras cómodo por la nariz → siguiente serie
        L.bg_holo(F.b, t); F.cam(1.0 + 0.05 * eio((t - t0) / 3))
        full = ramp(t, t0, t_comodo + 0.2)
        L.nose_stopwatch(F, t, lerp(0.6, 1.0, full), cy=880, R=270)
        lift = back((t - t_sig) / 0.4) if t > t_sig else 0
        L.dumbbell(F.g, 540, 1340 - 60 * lift, 1.0 + 0.2 * lift, 0, L.GRN, 0.4 + 0.6 * lift)
        L.label(F.o, t, t_comodo - 0.4, 540, 400, "¿CÓMODO POR LA NARIZ?", L.CYAN, size=46)
        L.label(F.o, t, t_sig, 540, 1620, "SIGUIENTE SERIE", L.GRN, size=54)

    def producto(F, t, t0):                   # 10 · nariz algo cerrada → AirNaze (única aparición)
        if t < t_airnaze - 0.1:
            L.bg_holo(F.b, t); F.cam(0.94 + 0.06 * back((t - t0) / 0.35))
            L.holo_nose(F, t, s=0.9, pl=0.6, pr=0.6)
            L.label(F.o, t, t_cerrada - 0.3, 540, 1600, "NARIZ ALGO CERRADA", L.PINK, size=44)
        else:
            L.product_card(F, t, t_airnaze, img=None, items=["PADS POR FUERA DE LA NARIZ", "UN ARCO QUE SE CONECTA", "AGUANTA EL SUDOR"])

    def cierre(F, t, t0):                     # 11 · guárdalo para tu próximo entreno
        def fondo(F, t, t0):
            L.bg_holo(F.b, t)
            L.dumbbell(F.g, 540, 560, 0.9, 0.1 * math.sin(t * 2), L.GOLD, 0.5)
        L.save_cta(F, t, t0, t_guarda + 0.3, scene_draw=fondo, txt="guárdalo")

    return [(0, "gancho", hook), (t_prueba - 0.1, "cierra", cierra), (t_si - 0.1, "notoca", notoca), (t_tu - 0.1, "crono", crono),
            (t_al - 0.1, "dispara", dispara), (t_si2 - 0.1, "revol", revol), (t_asi - 0.1, "camina", camina),
            (t_inspira - 0.2, "respira", respira), (t_cuando - 0.1, "siguiente", siguiente), (t_y - 0.1, "producto", producto),
            (t_guarda - 0.2, "cierre", cierre)], end


def ACCENTS(L): return [L.A("doblado,"), L.A("cierra"), L.A("cronómetro"), L.A("dispara."), L.A("siguiente")]
def CHIMES(L): return [L.A("airnaze")]
