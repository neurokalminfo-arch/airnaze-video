# Fábrica diaria de vídeos AirNaze

Cada ejecución crea **1 vídeo corto** (1080x1920, 25–35 s, voz + música) y lo deja programado en Metricool para Instagram (@myairnaze, Reel) y TikTok (@myairnaze).
Hay dos ejecuciones al día: slot `am` = **10:00** y slot `pm` = **19:00** (hora de Madrid). Se publica sin revisión previa.

## Pasos de cada ejecución
1. `bash engine/setup.sh` (voz Piper en español + dependencias; tarda ~1 min la primera vez).
2. Lee **`ESTRATEGIA.md`** (embudo, series, calendario semanal) y **`aprendizajes.md`** (lo que dicen los datos; manda sobre el calendario base). Haz lo que toque hoy según el día de la semana y el slot; si hay una promesa de CTA pendiente, prioriza cumplirla.
3. Lee los temas ya usados: `grep -h '"topic"\|"stage"\|"hook_type"' episodes/*/spec.json`. No repitas tema ni gancho de los últimos 30 días. Escribe `episodes/AAAA-MM-DD-<tema-corto>-<slot>/spec.json` con todas las etiquetas (`stage`, `series`, `hook_type`, `cta`, `pillar`). Si el CTA promete un vídeo, apúntalo en "Promesas pendientes" de `aprendizajes.md` (y bórralo de ahí cuando lo cumplas).
4. `python3 engine/render.py episodes/<id>/spec.json episodes/<id>/final.mp4 --frames` y **mira los fotogramas** (`episodes/<id>/final_work/preview_*.jpg`; haz una hoja de contacto): texto completo, nada cortado ni solapado. Corrige y repite. Después, sin `--frames`, el render completo (~1 min).
5. Comprueba la duración con ffprobe (25–35 s ideal, máx. 40 s; si se pasa, recorta voz y vuelve a renderizar). Borra `final_work/`, luego `git add -A && git commit && git push origin main`. URL pública:
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

## Qué se puede decir de AirNaze (sale de airnaze.com/products/pack-de-bienvenida)
- Sistema con **pads adhesivos** que se pegan **por fuera** de la nariz y un **arco** que se conecta a ellos. Tiene niveles: se empieza por el más suave.
- Uso: nariz limpia y seca → pads por fuera → conectar el arco. Ayuda a que el aire pase más fácil por la nariz. Sin pastillas ni sprays.
- Cómodo, discreto, fácil de poner. Aguanta el sudor en el entreno.
- Momentos: dormir, entrenar, trabajo con concentración, ambientes cargados, cuando notas la nariz algo cerrada.
- El Pack de Bienvenida da para 15 días. Envío gratis y 30 días de devolución (solo en vídeos `convertir`, sin precio).
- La web usa claims como "33 % más oxígeno", "menos ronquidos" o "mejores ciclos REM": **no se repiten** en orgánico (ver ESTRATEGIA.md §8).

## Lo que NO se dice
- Nada de "cura", "trata", "elimina los ronquidos", apnea, "previene", ni ningún claim médico o de salud.
- Ni porcentajes, ni precio, ni descuentos, ni promesas de rendimiento ("rendirás un 20 % más").
- Datos solo si son ciertos y generales (p. ej. "unas 20.000 respiraciones al día"; "la nariz filtra, calienta y humedece el aire"). Ante la duda, sin cifra.
- AirNaze aparece en **una sola escena** (la penúltima), salvo en vídeos `convertir`, donde puede ser el tema. Nunca lo dibujes ni lo inventes: usa la escena `product` con una foto real de `assets/product/` (rótalas; mira cuáles hay con `ls assets/product/`). Si la carpeta está vacía, usa icono (`wind`, `nose`) y texto, y avísalo en el resumen.
- CTA: guardar o comentar algo concreto ("cuéntame: ¿duermes con la boca abierta?"). Nunca "compra ya".

## Formato de spec.json
```json
{"slot":"am|pm","pillar":"descanso|respiracion|entrenamiento|habitos","topic":"...","publish_at":"AAAA-MM-DDTHH:MM:SS",
 "stage":"atraer|conectar|convertir","series":"mito-o-verdad|reto-60s|tu-noche-mejor|entrena-con-la-nariz|me-preguntasteis|asi-se-usa|ninguna",
 "hook_type":"pregunta|mito|dato|error|reto|historia","cta":"guardar|comentar|compartir|perfil",
 "caption":"texto del post con emojis y pregunta final","hashtags":["#dormirmejor","..."],"tiktok_title":"título corto",
 "music_seed": 1,
 "scenes":[ ... ]}
```
- 5–7 escenas, **350–480 caracteres de voz** en total. Cambia `music_seed` (0–20) en cada vídeo.
- Tipos de escena (`type`), alterna: no más de 2 `tip` seguidos.
  - `hook`: `big` (pregunta o frase corta), `small`, `accent` [palabras en color menta]. Siempre la primera.
  - `tip`: `n`, `title`, `sub`, `icon`.
  - `stat`: `value` (p. ej. "20.000"), `label`. Solo datos ciertos.
  - `versus`: `left`, `lsub`, `right`, `rsub` (comparación corta).
  - `breath`: `big` (círculo que respira 5 s: ideal para mini retos de respiración).
  - `brand`: `big`, `small` (cierre con CTA). Siempre la última.
  - `product`: `img` (nombre de archivo en `assets/product/`), `tag` (p. ej. "AirNaze"), `items` (2–3 rasgos reales, cortos). Foto con zoom lento y rasgos en chips.
- `voice` en cada escena: lo que dice la voz (también salen como subtítulos).
- Iconos: drop, moon, bed, wind, window, clock, run, leaf, phone, sun, nose, check.

## Motor
- `engine/render.py`: voz Piper (es_ES davefx), animación dibujada con Pillow por escena, transiciones variadas, subtítulos, música original sintetizada con la voz por encima (-14 LUFS).
- Nunca subas claves a este repositorio (es público).
