# Fábrica diaria de vídeos AirNaze

Cada ejecución crea **1 vídeo corto** (1080x1920, 30–40 s, voz + música) y lo deja programado en Metricool para Instagram (@myairnaze, Reel) y TikTok (@myairnaze).
Hay dos ejecuciones al día: slot `am` = **10:00** y slot `pm` = **19:00** (hora de Madrid). Se publica sin revisión previa.

## Pasos de cada ejecución
1. `bash engine/setup.sh` (voz Piper en español + dependencias; tarda ~1 min la primera vez).
2. Lee los temas ya usados: `grep -h '"topic"' episodes/*/spec.json`. No repitas tema ni gancho de los últimos 30 días.
3. Elige pilar con la rotación (abajo) y escribe `episodes/AAAA-MM-DD-<tema-corto>-<slot>/spec.json`.
4. `python3 engine/render.py episodes/<id>/spec.json episodes/<id>/final.mp4 --frames` y **mira los fotogramas** (`episodes/<id>/final_work/preview_*.jpg`; haz una hoja de contacto): texto completo, nada cortado ni solapado. Corrige y repite. Después, sin `--frames`, el render completo (~1 min).
5. Comprueba la duración con ffprobe (30–40 s ideal, máx. 50 s). Borra `final_work/`, luego `git add -A && git commit && git push origin main`. URL pública:
   `https://raw.githubusercontent.com/neurokalminfo-arch/airnaze-video/main/episodes/<id>/final.mp4` (comprueba con curl que da 200; puede tardar unos segundos tras el push).
6. Programa en Metricool (`createScheduledPost`, `draft: false`, `autoPublish: true`, zona `Europe/Madrid`):
   - blogId **7796113** (marca Airnaze) · providers `[instagram, tiktok]` · `instagramData: {type: REEL, showReelOnFeed: true}` · `tiktokData: {title: tiktok_title, privacyOption: PUBLIC_TO_EVERYONE}` · texto = caption + hashtags.
   - Si Metricool da "internal error while storing the media", reintenta tras unos segundos.
   - Si la hora del slot ya pasó, no lo publiques: dilo en el resumen.
   - NO toques las marcas Fetbull, Valkyra, neurokalm ni La Gran Pregunta.
7. Resumen final: tema, gancho, hora, enlace del planner de Metricool.

## Marca
Idea: respirar mejor, descansar mejor, entrenar mejor, vivir mejor. AirNaze es un **dilatador nasal externo**. Queremos una marca humana que acompaña hábitos cotidianos, no un producto que se enseña.
- Tono cercano, natural, informal. Español de España, segunda persona. **Nunca** médico, terapéutico ni de teletienda.
- Primero algo práctico y útil que la gente reconozca; después AirNaze, de forma natural.
- Visual: identidad azul, capas y animaciones distintas en cada escena. Cada escena aporta algo nuevo.

## Rotación de pilares
- Pilares: **descanso** (~35 %), **respiración** (~25 %), **entrenamiento** (~25 %), **hábitos del día a día** (~15 %: trabajo, estrés, viajes, alergia estacional). Nunca el mismo pilar dos vídeos seguidos.
- Mañana (am): energía, entrenar, concentración, empezar el día, respiración consciente.
- Tarde (pm): desconectar, preparar la noche, dormir mejor, recuperar tras entrenar.
- Formatos de gancho que rotar: pregunta que identifica ("¿Boca seca al despertar?"), mito ("Respirar por la boca al correr no es más eficiente"), dato curioso, error típico, mini reto ("prueba esto 60 segundos").

## Qué se puede decir de AirNaze
- Se pega **por fuera** de la nariz. Ayuda a que el aire pase más fácil por la nariz. Sin pastillas ni sprays.
- Momentos: dormir, entrenar, día a día, cuando notas la nariz algo cerrada.

## Lo que NO se dice
- Nada de "cura", "trata", "elimina los ronquidos", apnea, "previene", ni ningún claim médico o de salud.
- Ni porcentajes, ni precio, ni descuentos, ni promesas de rendimiento ("rendirás un 20 % más").
- Datos solo si son ciertos y generales (p. ej. "unas 20.000 respiraciones al día"; "la nariz filtra, calienta y humedece el aire"). Ante la duda, sin cifra.
- AirNaze aparece en **una sola escena** (la penúltima). No hay fotos del producto en el repo: no lo dibujes ni lo inventes; usa icono (`wind`, `nose`) y texto.
- CTA: guardar o comentar algo concreto ("cuéntame: ¿duermes con la boca abierta?"). Nunca "compra ya".

## Formato de spec.json
```json
{"slot":"am|pm","pillar":"descanso|respiracion|entrenamiento|habitos","topic":"...","publish_at":"AAAA-MM-DDTHH:MM:SS",
 "caption":"texto del post con emojis y pregunta final","hashtags":["#dormirmejor","..."],"tiktok_title":"título corto",
 "music_seed": 1,
 "scenes":[ ... ]}
```
- 6–8 escenas, **450–600 caracteres de voz** en total. Cambia `music_seed` (0–20) en cada vídeo.
- Tipos de escena (`type`), alterna: no más de 2 `tip` seguidos.
  - `hook`: `big` (pregunta o frase corta), `small`, `accent` [palabras en color menta]. Siempre la primera.
  - `tip`: `n`, `title`, `sub`, `icon`.
  - `stat`: `value` (p. ej. "20.000"), `label`. Solo datos ciertos.
  - `versus`: `left`, `lsub`, `right`, `rsub` (comparación corta).
  - `breath`: `big` (círculo que respira 5 s: ideal para mini retos de respiración).
  - `brand`: `big`, `small` (cierre con CTA). Siempre la última.
- `voice` en cada escena: lo que dice la voz (también salen como subtítulos).
- Iconos: drop, moon, bed, wind, window, clock, run, leaf, phone, sun, nose, check.

## Motor
- `engine/render.py`: voz Piper (es_ES davefx), animación dibujada con Pillow por escena, transiciones variadas, subtítulos, música original sintetizada con la voz por encima (-14 LUFS).
- Nunca subas claves a este repositorio (es público).
