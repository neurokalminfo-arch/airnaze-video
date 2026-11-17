---
name: airnaze-reels-collage
description: Crea los Reels/TikToks de AirNaze con el estilo propio "kinetic + collage" (papel rasgado, cinta, riso, garabatos que hierven, tipografía a golpes al ritmo). Úsala cada vez que haya que escribir el guion (spec.json) y renderizar un vídeo corto de AirNaze, o revisar uno, para que no parezca contenido genérico de IA.
---

# AirNaze · Reels "kinetic + collage"

Motor: `engine/render_v2.py` (repo `neurokalminfo-arch/airnaze-video`). Las reglas de marca, claims y publicación siguen en `CLAUDE.md`; esta skill manda en **guion visual y ritmo**.

## Por qué este estilo
Lo genérico de IA es: fondo degradado oscuro, manchas difusas, tarjetas redondeadas blancas, iconos planos, texto que aparece con fundido. Aquí hacemos lo contrario:
- **Materia**: papel con fibra y grano, recortes rasgados con alma blanca, cinta adhesiva, tramas de semitono, impresión riso desalineada.
- **Mano humana**: garabatos, flechas, X y ✓ dibujados que "hierven" a 12 fps (stop-motion).
- **Golpe**: tipografía gigante (Anton, DM Serif itálica, contorno, letras de nota de rescate) que entra a golpes con sacudida de cámara; cortes en el beat (112 bpm); SFX de papel, golpe y pop.
- **Contraste**: cada escena cambia de papel (azul cobalto / crema / navy / menta). Nunca dos iguales seguidas.

## Estructura dinámica (8 escenas, 30–42 s, máx. 45 s)
Regla de oro: **algo nuevo cada 2–3 s** y un cambio de lenguaje en cada escena.

| # | Momento | Escena recomendada | Trabajo |
|---|---|---|---|
| 1 | Gancho (0–4 s) | `slam` | Frase corta a golpes que llena la pantalla. Voz desde el fotograma 1. |
| 2 | Prueba | `stat` o `split` | Un dato cierto o un contraste que sorprende. |
| 3 | Giro | `cutout` | Una palabra clave en letras recortadas ("FILTRO", "SILENCIO", "CALMA"). |
| 4 | Valor | `triple` o `step` | Lo práctico: 2–3 verbos o un paso concreto. |
| 5 | Contraste | `split` | Mal (X roja) vs bien (✓ menta). |
| 6 | Acción | `breath` / `step` | Reto o hábito para hacer ya. |
| 7 | AirNaze | `product` | Única aparición de marca (foto real si hay en `assets/product/`). |
| 8 | CTA | `close` | Pregunta concreta en bocadillo + flecha a comentarios. |

Se puede quitar una escena (mínimo 6). No repitas el mismo tipo seguido. `step` máximo 2 seguidos.

## Escenas (`type`) y campos
- `slam`: `big` (3–6 palabras), `accent` [palabras clave], `kicker` (etiqueta en cinta: "DATO DEL DÍA", "MITO O VERDAD", "RETO 60 S", "TU NOCHE, MEJOR").
- `stat`: `value` ("20.000"), `label`. Solo datos ciertos y generales.
- `cutout`: `word` (≤ 8 letras), `sub` (frase corta escrita a rotulador).
- `triple`: `items` [{`word`, `icon`}] ×2–3. Palabras ≤ 9 letras.
- `step`: `n`, `title`, `sub`, `icon`.
- `split`: `left`, `lsub`, `right`, `rsub` (palabras cortas: BOCA/NARIZ, PANTALLA/LIBRO).
- `breath`: `big` ("60 s solo nariz"). Discos que respiran en ciclos de 5 s.
- `product`: `img` (archivo de `assets/product/`), `tag`, `items` (2–3 rasgos reales). Sin foto → sticker + "AIRNAZE" recortado.
- `close`: `big` (pregunta, ≤ 4 palabras), `small` ("te leo aquí").
- Opcional en cualquiera: `theme`: blue | cream | navy | mint.
- Iconos: drop, moon, bed, wind, window, clock, run, leaf, phone, sun, nose, check.
- Compatibles con v1: hook→slam, tip→step, versus→split, brand→close.

## Guion
- Voz total 420–560 caracteres (≈ 30–40 s). Frases cortas, segunda persona, España.
- El texto en pantalla **no repite** la voz: la resume en 1–4 palabras (los subtítulos karaoke ya llevan la voz).
- Gancho: pregunta que identifica, mito, dato, error o reto (ver ESTRATEGIA.md). Rótalos.
- Cambia `music_seed` (0–20) en cada vídeo.

## Render y control de calidad
1. `python3 engine/render_v2.py episodes/<id>/spec.json episodes/<id>/final.mp4 --frames` → mira `final_work/contact.jpg` (3 fotogramas por escena).
2. Comprueba: nada cortado por los bordes, el texto grande no pisa los subtítulos (franja y≈1430–1510), los stickers no tapan letras, cada escena se ve distinta a la anterior.
3. Render completo sin `--frames` (~1 min). Duración con ffprobe: 30–42 s, máx. 45 s. Sonoridad ≈ -14 LUFS (el motor la ajusta).
4. Si algo se solapa: acorta el texto de pantalla (no el tamaño), o cambia de tipo de escena.
