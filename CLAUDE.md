# Fábrica diaria de vídeos AirNaze

Cada ejecución crea **1 vídeo corto** (1080x1920, 35–46 s, voz + música) con el estilo **noche neón** y lo deja programado en Metricool para Instagram (@myairnaze, Reel) y TikTok (@myairnaze).
Hay dos ejecuciones al día: slot `am` = **10:00** y slot `pm` = **19:00** (hora de Madrid). Se publica sin revisión previa.

## Pasos de cada ejecución
1. `bash engine/neon/setup.sh` (dependencias + fuente Inter). La voz es la de **Carlos en ElevenLabs**: la clave llega en el prompt de la tarea y se usa SOLO como variable de entorno `ELEVENLABS_API_KEY` (nunca en archivos: el repo es público).
2. Lee **`ESTRATEGIA.md`** (embudo, series, calendario semanal) y **`aprendizajes.md`** (lo que dicen los datos; manda sobre el calendario base). Haz lo que toque hoy según el día de la semana y el slot; si hay una promesa de CTA pendiente, prioriza cumplirla.
3. Lee los temas ya usados: `grep -h '"topic"\|"stage"\|"hook_type"' episodes/*/spec.json`. No repitas tema ni gancho de los últimos 30 días. Escribe `episodes/AAAA-MM-DD-<tema-corto>-<slot>/spec.json` con todas las etiquetas (`stage`, `series`, `hook_type`, `cta`, `pillar`). Si el CTA promete un vídeo, apúntalo en "Promesas pendientes" de `aprendizajes.md` (y bórralo de ahí cuando lo cumplas).
4. Sigue **`skills/airnaze-noche-neon/SKILL.md`** y el ejemplo `muestras/neon-ciclo-nasal/`. Escribe el guion en `spec.json` (`voice`, `style: "noche-neon"`), genera la voz (`python3 engine/neon/tts.py episodes/<id>`), escribe `episodes/<id>/scenes.py`, y `python3 engine/neon/render.py episodes/<id> --frames`: **mira la hoja de contacto** `episodes/<id>/final_work/contact.jpg` (texto completo, nada cortado ni solapado, ninguna escena vacía). Corrige y repite. Después, sin `--frames`, el render completo (~1,5 min).
   Si ElevenLabs falla tras reintentar unos minutos, usa como respaldo el motor anterior (`bash engine/setup.sh` + `engine/render_v2.py`, estilo collage con voz Piper) y dilo en el resumen.
5. Comprueba la duración con ffprobe (35–46 s ideal, máx. 48 s; si se pasa, recorta el guion, regenera la voz y vuelve a renderizar). Borra `final_work/`, luego `git add -A && git commit && git push origin main`. URL pública:
   `https://raw.githubusercontent.com/neurokalminfo-arch/airnaze-video/main/episodes/<id>/final.mp4` (comprueba con curl que da 200; puede tardar unos segundos tras el push).
6. Programa en Metricool (`createScheduledPost`, `draft: false`, `autoPublish: true`, zona `Europe/Madrid`):
   - blogId **7796113** (marca Airnaze) · providers `[instagram, tiktok]` · `instagramData: {type: REEL, showReelOnFeed: true}` · `tiktokData: {title: tiktok_title, privacyOption: PUBLIC_TO_EVERYONE}` · texto = caption + hashtags.
   - Si Metricool da "internal error while storing the media", reintenta tras unos segundos.
   - Si la hora del slot ya pasó, no lo publiques: dilo en el resumen.
   - NO toques las marcas Fetbull, Valkyra, neurokalm ni La Gran Pregunta.
   - **Verifica siempre** con `getScheduledPosts` (blogId 7796113, hoy, Europe/Madrid) que el post queda con `draft: false`, `autoPublish: true` y la hora correcta. Si sale `draft: true`, corrígelo con `updateScheduledPost` (mismo contenido completo, `draft: false`) y vuelve a comprobarlo. Un post en borrador NO se publica.
   - Si el episodio del slot ya existía en el repo, no crees otro, pero haz igualmente esta verificación en Metricool y corrige el borrador si hace falta (si el post no existe y la hora no ha pasado, prográmalo con el `final.mp4` ya subido).
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
Estilo **noche neón** (el actual): las etiquetas de abajo + `"style": "noche-neon"`, `"voice"` (guion completo, 560–760 caracteres) y `music_seed`. Las escenas NO van en spec.json sino en `episodes/<id>/scenes.py` (ver la skill). El formato de `scenes` de abajo es el del motor collage (respaldo).

```json
{"slot":"am|pm","pillar":"descanso|respiracion|entrenamiento|habitos","topic":"...","publish_at":"AAAA-MM-DDTHH:MM:SS",
 "stage":"atraer|conectar|convertir","series":"mito-o-verdad|reto-60s|tu-noche-mejor|entrena-con-la-nariz|me-preguntasteis|asi-se-usa|ninguna",
 "hook_type":"pregunta|mito|dato|error|reto|historia","cta":"guardar|comentar|compartir|perfil",
 "caption":"texto del post con emojis y pregunta final","hashtags":["#dormirmejor","..."],"tiktok_title":"título corto",
 "music_seed": 1,
 "scenes":[ ... ]}
```
- 6–8 escenas, **420–560 caracteres de voz** en total. Cambia `music_seed` (0–20) en cada vídeo. Estructura y reglas visuales: `skills/airnaze-reels-collage/SKILL.md`.
- Tipos de escena (`type`); nunca el mismo tipo dos veces seguidas:
  - `slam`: `big` (3–6 palabras), `accent` [palabras clave], `kicker` (etiqueta en cinta). Siempre la primera.
  - `stat`: `value` (p. ej. "20.000"), `label`. Solo datos ciertos.
  - `cutout`: `word` (≤ 8 letras, en letras recortadas), `sub` (frase corta a rotulador).
  - `triple`: `items` [{`word`, `icon`}] ×2–3, palabras ≤ 9 letras.
  - `step`: `n`, `title`, `sub`, `icon`.
  - `split`: `left`, `lsub`, `right`, `rsub` (mal con X vs bien con ✓; palabras cortas).
  - `breath`: `big` (discos que respiran 5 s: mini retos de respiración).
  - `product`: `img` (archivo en `assets/product/`), `tag`, `items` (2–3 rasgos reales). Sin foto: sticker + "AIRNAZE" recortado. Siempre la penúltima.
  - `close`: `big` (pregunta CTA, ≤ 4 palabras), `small`. Siempre la última.
  - Opcional: `theme` (blue|cream|navy|mint). Los tipos v1 (`hook`, `tip`, `versus`, `brand`) siguen funcionando.
- `voice` en cada escena: lo que dice la voz (también salen como subtítulos).
- Iconos: drop, moon, bed, wind, window, clock, run, leaf, phone, sun, nose, check.

## Motor
- `engine/neon/` (el que se usa desde el 19-11-2026): estilo "noche neón" dibujado con código (pycairo + glow), subtítulos karaoke arriba, voz Carlos (ElevenLabs), música y efectos sintetizados, -14 LUFS. Skill: `skills/airnaze-noche-neon/SKILL.md`.
- `engine/render_v2.py` (respaldo si falla ElevenLabs): estilo "kinetic + collage": papel rasgado, cinta, riso, garabatos a 12 fps, tipografía a golpes, cortes en el beat (112 bpm), subtítulos karaoke, música + SFX sintetizados, voz Piper (es_ES davefx), -14 LUFS. Fuentes OFL en `assets/fonts/`.
- `engine/render.py`: motor antiguo (v1), solo de respaldo si v2 falla.
- Nunca subas claves a este repositorio (es público).
