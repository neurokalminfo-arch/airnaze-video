# Estrategia de contenido orgánico AirNaze

Objetivo: vender sin sonar a venta. Aportamos valor real sobre respirar, descansar y entrenar; la gente nos guarda, nos comenta y vuelve; y cuando necesita respirar mejor por la nariz, AirNaze ya es su marca.

## 1. Embudo: cada vídeo tiene un trabajo
Cada `spec.json` lleva `"stage"`. Reparto semanal (14 vídeos):

| Etapa | Peso | Vídeos/semana | Trabajo del vídeo | AirNaze | Métrica que manda |
|---|---|---|---|---|---|
| `atraer` | ~60 % | 8 | Valor puro que se comparte: mitos, datos, errores, trucos | Solo un guiño en la penúltima escena, o nada | Alcance, compartidos, % que no lo salta en 3 s |
| `conectar` | ~25 % | 3–4 | Series fijas y respuestas a comentarios: que nos esperen | Natural, como parte del hábito | Guardados, comentarios, seguidores |
| `convertir` | ~15 % | 2 | Cómo se usa, dudas, cuándo ponerlo, qué incluye el pack | Protagonista, con foto real | Visitas al perfil y a la web, ventas |

- Nunca dos `convertir` seguidos. Máximo 2 por semana. Mejor el jueves pm y el domingo pm (momento de pensar en dormir mejor).
- Un `convertir` también aporta valor: responde una duda real ("¿se cae al sudar?", "¿se nota por la noche?").

## 2. Series fijas (`series`)
Formatos reconocibles que crean costumbre. Usar con nombre visible en el gancho (`small`).

- **Mito o verdad** (atraer): "Respirar por la boca al correr da más aire". Desmontar con datos generales y ciertos.
- **Reto 60 segundos** (conectar): una técnica de respiración guiada con la escena `breath`. CTA: "Hazlo ahora y cuéntame cómo te has quedado".
- **Tu noche, mejor** (atraer/conectar, pm): un hábito de sueño concreto por vídeo.
- **Entrena con la nariz** (atraer, am): respiración nasal en calentamiento, cardio suave, recuperación.
- **Me preguntasteis** (conectar): responde un comentario real de vídeos anteriores (en `aprendizajes.md` se apuntan los comentarios que piden algo).
- **Así se usa** (convertir): colocación, nivel suave al empezar, cuándo ponerlo. Con foto real.

## 3. Calendario semanal base
| Día | 10:00 (am) | 19:00 (pm) |
|---|---|---|
| Lun | Entrena con la nariz · atraer | Tu noche, mejor · atraer |
| Mar | Mito o verdad · atraer | Reto 60 s · conectar |
| Mié | Hábitos (trabajo, estrés) · atraer | Tu noche, mejor · atraer |
| Jue | Entrena con la nariz · atraer | Así se usa · **convertir** |
| Vie | Mito o verdad · atraer | Me preguntasteis · conectar |
| Sáb | Hábitos (finde, viaje, alergia) · atraer | Reto 60 s · conectar |
| Dom | Dato curioso · atraer | Descanso + AirNaze · **convertir** |

Es una base: si `aprendizajes.md` dice que algo funciona mejor, manda `aprendizajes.md`.

## 4. Ganchos (`hook_type`)
`pregunta` · `mito` · `dato` · `error` · `reto` · `historia` (situación cotidiana: "Son las 3 de la mañana y…"). Rotar; no repetir el mismo tipo 3 veces seguidas.
- Los 2 primeros segundos deciden el vídeo: texto grande y voz desde el fotograma 1, sin introducciones.

## 5. CTA (`cta`)
`guardar` · `comentar` (pregunta concreta o palabra clave: "Comenta NOCHE y te hago la rutina completa") · `compartir` ("Mándaselo a quien ronca a tu lado") · `perfil` (solo en `convertir`: "Lo tienes en el enlace del perfil").
- Si un vídeo promete algo en su CTA ("Comenta NOCHE y…"), ese vídeo se hace en los 7 días siguientes (serie *Me preguntasteis*) y se apunta en `aprendizajes.md`.

## 6. Etiquetas obligatorias en cada spec.json
`"stage"`, `"series"`, `"hook_type"`, `"cta"`, además de `pillar`, `slot`, `topic`. Sirven para que el análisis semanal cruce qué funciona.

## 7. Cómo medimos (análisis semanal, lunes)
Por reel (Instagram, connector `reels`; TikTok, connector `posts`): vistas, alcance, `reelsSkipRate` (saltan en 3 s), `retention` (% visto), `averageWatchTime`, guardados, compartidos, comentarios.
- **Gancho**: skip rate. **Contenido**: retención. **Valor**: guardados + compartidos por cada 1.000 de alcance. **Vínculo**: comentarios y seguidores.
- Venta: visitas a la web desde Instagram/TikTok (Shopify) y pedidos de la semana; atribución aproximada, no por vídeo.
- Hasta tener ~30 vídeos, las conclusiones son "pistas", no reglas.

## 8. Sobre lo que dice la tienda
La web usa claims fuertes ("33 % más oxígeno", "menos ronquidos", "mejores ciclos REM"). En orgánico **no** se repiten: son claims de salud que Instagram/TikTok pueden penalizar y que restan credibilidad al tono cercano. Se habla de lo que se ve y se siente (pads por fuera, arco, nivel suave para empezar, aguanta el sudor, discreto) y de hábitos.
