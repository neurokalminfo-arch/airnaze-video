---
name: airnaze-noche-neon
description: Estilo "noche neón" de los Reels/TikToks de AirNaze (desde el 19-11-2026): explicador ilustrado y cinematográfico hecho 100 % con código (escenas con luz cálida y neón, metáforas visuales, subtítulos karaoke arriba, voz de Carlos en ElevenLabs). Úsala para escribir el guion, las escenas (scenes.py) y renderizar cada vídeo corto de AirNaze.
---

# AirNaze · estilo "noche neón"

Referencia visual: explicadores tipo "¿Por qué a veces duermes 8 h y te despiertas destruido?": cada idea es **una metáfora visual** (dormitorio de noche con despertador dorado, nariz en holograma, ondas de neón con una cama que sube y baja…), paleta índigo/morado con luces cálidas ámbar y neón cian/rosa, polvo flotando, cámara que se acerca despacio.
Todo se dibuja con código (`engine/neon/lib.py`): **nada de Higgsfield ni IA de imagen/vídeo**. Las reglas de marca, claims y publicación siguen en `CLAUDE.md` y mandan sobre esta skill.

Ejemplo completo y funcionando: `muestras/neon-ciclo-nasal/` (spec.json + scenes.py + final.mp4). **Léelo antes de escribir un episodio.**

## Guion (spec.json → `voice`)
- Un único texto (`voice`) de **560–760 caracteres** → 35–46 s. Máximo 48 s.
- Estructura: **gancho-paradoja** (pregunta sobre algo que le pasa a todo el mundo, sin marca) → **"No es X, es Y"** → **mecanismo** en 3–5 ideas visuales → **consecuencia** que reconoces ("por eso te levantas con la boca seca") → **truco práctico** → **AirNaze en una frase** con lo que se puede decir (pads por fuera + arco que se conecta, para que el aire pase más fácil) → **CTA** de comentar/guardar con pregunta concreta.
- Frases cortas, segunda persona, español de España. Datos solo ciertos y generales (comprueba con búsqueda web si dudas; si no, sin cifra).

## Escenas (scenes.py)
`timeline(L)` devuelve `[(inicio_s, nombre, funcion(F, t, t0)), ...], fin_s`. Ancla cada escena y cada animación a una palabra de la voz con `L.A("palabra", despues_de)` (las palabras van tal cual en `words.json`, sin mayúsculas ni signos al comparar).
- 8–11 escenas; **un cambio visual cada 3–5 s**. Dentro de cada escena, algo se mueve siempre (cámara, partículas, brillo, etiquetas que entran en la palabra justa).
- Primitivas de `lib.py` (puedes combinarlas, cambiar parámetros y **crear 1–2 primitivas nuevas por vídeo** dentro de `lib.py` si el tema lo pide: un corredor, una oficina, un sofá, un avión… con el mismo lenguaje visual):
  - `bedroom(F, t, head_glow=(color, a), mouth=0..1, mouth_air, nose_air, snore)`: dormitorio de noche con ventana, luna, ciudad, cama y despertador dorado. `F.cam(zoom, cx, cy)` para acercar.
  - `holo_nose(F, t, s, rot, pl, pr, swell_l, swell_r, turb, x_l, x_r)`: corte de la nariz en holograma (canales, cornetes, aire cian). `pl/pr` cierran (+) o abren (−) la entrada; `swell_*` hinchan; `rot=-pi/2` = tumbado; `x_l/x_r` muestran una ✖.
  - `waves(F, t, phase_shift)` + `bed_icon(...)`: ondas de neón rosa/cian sobre atardecer con una cama encima (ciclos, turnos, subidas y bajadas).
  - `stat(F, t, t0, "20.000", "respiraciones al día")`: dato grande con anillo de neón.
  - `badge(F.o, t, t0, x, y, "3:12")`, `label(F.o, t, t0, x, y, "TEXTO", color)`: placas y etiquetas que entran con rebote.
  - `product_card(F, t, t0, img="assets/product/<foto>", items=[...])`: **única** aparición de AirNaze (penúltima escena). Con foto real si hay en `assets/product/`; si no, tarjeta con nombre + icono de nariz y avísalo en el resumen. **Nunca dibujes el producto** (ni arco ni pads dibujados).
  - `close_cta(F, t, t0, None, t_comentarios, scene_draw=fondo)`: bocadillo + flecha "comenta aquí". La pregunta la dice la voz y sale en el subtítulo.
- `KEY = {...}`: 8–12 palabras clave del guion que salen en recuadro en los subtítulos karaoke (arriba).
- Opcional: `ACCENTS(L)` (pops en momentos clave), `CHIMES(L)` (campanita al decir AirNaze), `TICKS_UNTIL(L)` (tic-tac del reloj en el gancho).

## Reglas visuales
- Paleta: índigo/morado de fondo, ámbar cálido (lámparas, reloj), neón cian (aire, lo que funciona), rosa/rojo (lo que se cierra, el problema), verde (solución, CTA). Nada de blanco plano ni tarjetas genéricas.
- Subtítulos arriba (y=262), etiquetas en la parte baja (y≈1550–1700) o junto al objeto; nunca tapes la escena principal ni el subtítulo.
- Cada vídeo nuevo: **cambia al menos 3 metáforas** respecto al anterior (no repitas la misma secuencia de escenas), y cambia `music_seed`.
- Revisa SIEMPRE la hoja de contacto (`--frames`): textos completos, nada cortado ni solapado, ninguna escena vacía al principio.

## Comandos
```
bash engine/neon/setup.sh
ELEVENLABS_API_KEY=... python3 engine/neon/tts.py episodes/<id>      # voz de Carlos → voice.mp3 + words.json
python3 engine/neon/render.py episodes/<id> --frames                 # hoja de contacto en final_work/contact.jpg
python3 engine/neon/render.py episodes/<id>                          # final.mp4 (voz + música + efectos, ~1,5 min)
```
Si cambias el guion, vuelve a generar la voz (las anclas dependen de words.json).
