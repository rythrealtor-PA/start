---
name: editar-reels
description: Edita videos crudos de "talking head" (el broker hablando a cámara) y los convierte en Reels/TikToks/Shorts verticales listos para publicar, con cortes de silencios y tomas falsas, subtítulos con palabras clave resaltadas, plan de escenas, B-roll, música, efectos de sonido y cierre con el logo de la marca, todo dentro de Claude Code y con aprobación del usuario en cada paso. Úsala SIEMPRE que el usuario quiera editar, cortar, subtitular, montar o "dejar listo" un video, reel, short o TikTok que grabó, cuando suba una toma en bruto, cuando diga "edítame este video", "quita los silencios", "ponle subtítulos", "hazlo vertical", "edit my reel", "cut this video", o cuando quiera enseñarle a Claude un estilo de edición nuevo a partir de videos de referencia, aunque no diga la palabra "skill".
---

# Editar Reels

Convierte una toma cruda del broker hablando a cámara en un video vertical que retenga a la gente. El método mezcla dos ideas que funcionan:

1. **Editar por pasadas con aprobación.** Primero el corte, luego los subtítulos, luego los gráficos y al final el sonido. El usuario aprueba cada versión antes de seguir. Un error en el corte arrastrado hasta el render final cuesta horas, y detectado en la pasada 1 cuesta segundos.
2. **Planear antes de construir.** La IA sola no es lo bastante creativa para decidir cada escena. Por eso se arma un **plan de edición** escena por escena, el usuario lo ajusta y solo entonces se construye. El primer borrador suele quedar al 60–70%; las revisiones lo terminan.

Habla con el usuario en su idioma (normalmente español), con frases cortas y sin jerga técnica. Si usas un término como "B-roll" o "render", explícalo en pocas palabras la primera vez.

## Carpeta de trabajo

Todo vive en una carpeta `Reels/` dentro del proyecto del usuario. Si no existe, créala:

```bash
python3 "${SKILL_DIR}/scripts/init_project.py" ./Reels
```

```
Reels/
  tomas/          videos crudos. Nunca se modifican: se trabaja con una copia.
  referencias/    videos o capturas de un estilo que le guste al usuario
  marca/
    estilo.md     colores, fuentes, logo, tono. Léelo SIEMPRE antes de editar.
    aprendizajes.md  lo que el usuario corrigió en otros videos. Léelo SIEMPRE.
    logos/        PNG/SVG con transparencia
    fuentes/      archivos .ttf/.otf
  musica/  sfx/  broll/   música, efectos y tomas de apoyo (propiedades, pueblo, drone)
  proyectos/AAAA-MM-DD-nombre/   un folder por reel, con todas sus versiones
```

`SKILL_DIR` es la carpeta donde está este SKILL.md, y los scripts están en `scripts/`.

## Primera vez (configuración)

1. Corre `python3 "${SKILL_DIR}/scripts/check_env.py"`. Si falta algo, muestra al usuario los comandos de instalación que imprime y pide permiso antes de instalar. El mínimo es FFmpeg más un transcriptor (faster-whisper). Node.js y Chrome solo hacen falta para los gráficos animados.
2. Si `marca/estilo.md` todavía tiene campos `[POR DEFINIR]`, hazle al usuario pocas preguntas y guarda sus respuestas en ese archivo: colores de marca (código hex), fuentes, logo en PNG y nombre de la brokerage. La plantilla ya trae la historia del logo (el lobo, el fresno, las llaves y los Poconos). Lee `references/marca-lobo.md` para entender cómo se usa en los videos.
3. Si el usuario quiere copiar el estilo de un creador, sigue `references/entrenar-estilo.md`.

## Flujo para cada video

Antes de empezar, lee `marca/estilo.md` y `marca/aprendizajes.md`. Así cada video sale mejor que el anterior sin que el usuario repita sus correcciones.

### 0 · Preparar
- Toma el video que indique el usuario, o el más reciente de `tomas/`. Crea `proyectos/AAAA-MM-DD-tema/` y trabaja ahí.
- Haz las preguntas rápidas que no estén respondidas en `estilo.md`. Usa la herramienta de preguntas si existe y propón siempre una opción recomendada:
  - **Plataforma:** Instagram, TikTok o Shorts. Define la zona segura (ver `references/plataformas.md`).
  - **Calidad:** 1080p (recomendado; rápido) o 4K.
  - **Cantidad de gráficos:** pocos, equilibrado (recomendado) o muchos.
  - **Música:** tranquila, épica, ninguna o "elige tú".
- Si el video está horizontal, se pasa a vertical en el paso 1.

### 1 · Corte (pasada 1)
```bash
python3 "${SKILL_DIR}/scripts/transcribe.py" tomas/toma.mp4 proyectos/X/palabras.json --language es
```
- Lee la transcripción completa (`palabras.txt`). Busca **tomas falsas**: frases que se repiten porque el broker se equivocó y volvió a empezar. Normalmente se queda el último intento. Anota los rangos a eliminar.
- Corta los silencios y las tomas falsas:
```bash
python3 "${SKILL_DIR}/scripts/cut_silences.py" --input tomas/toma.mp4 --words proyectos/X/palabras.json \
  --drop "12.4-17.9,41.0-44.2" --output proyectos/X/v1_corte.mp4 --words-out proyectos/X/palabras_corte.json
```
  Por defecto se eliminan las pausas de más de 0.35 s y se dejan 30 ms de margen alrededor de cada palabra. Sube `--max-gap` si el corte queda demasiado acelerado. Si no hay transcripción, usa `--from-silence`.
- Si el video es horizontal: `python3 "${SKILL_DIR}/scripts/vertical.py" v1_corte.mp4 v1_vertical.mp4`. Usa `--x 0.4` para mover el encuadre hacia la cara, o `--mode blur` para ver el cuadro completo con un fondo difuminado.
- **Muestra la versión al usuario** y espera su aprobación. Pregúntale si se comió alguna palabra o si quiere sacar alguna frase.

### 2 · Plan de edición (antes de construir nada)
Crea `proyectos/X/plan.md` con una tabla así: tiempo | lo que dice | escena propuesta | nota. Elige cada escena de `references/escenas.md` con estas reglas:
- **Los primeros 3 segundos deciden todo.** El hook necesita cara más texto grande y, si se puede, algo en movimiento.
- **Cuando el broker anuncia una idea nueva, va su cara. Cuando la describe, se muestra.** Esa alternancia es la que da ritmo.
- Cambia algo en pantalla cada 3–5 s: un corte, un zoom suave, texto o B-roll. Una sola cosa protagonista a la vez.
- La firma visual de la marca va al menos una vez: una hoja que cae y se convierte en llave, o el cierre con el logo.
- Pon pocos gráficos en las partes emotivas y más en las de datos (precios, porcentajes, pasos).

Muéstrale el plan al usuario para que cambie, quite o agregue escenas. Este es el paso más importante: no lo saltes aunque el usuario tenga prisa. Ofrécele un plan "automático" que pueda aprobar con un "sí".

### 3 · Subtítulos (pasada 2)
- Propón al usuario las **palabras clave** que irán resaltadas (más grandes y en el color de acento): números, precios, lugares, la promesa y la palabra del hook. Máximo una o dos por frase.
- Genera y quema los subtítulos:
```bash
python3 "${SKILL_DIR}/scripts/captions.py" --words proyectos/X/palabras_corte.json --keywords "Poconos,llaves,$400,000" \
  --style marca/estilo.md --fontsdir marca/fuentes --output proyectos/X/subs.ass \
  --burn proyectos/X/v1_vertical.mp4 --burn-out proyectos/X/v2_subs.mp4
```
  Los subtítulos van en frases de máximo 4 palabras. La palabra que se está diciendo se ilumina, y la posición respeta la zona segura de la plataforma. El script toma colores y fuentes del `estilo.md`, y los flags los sobrescriben.
- Muestra la versión y espera aprobación.

### 4 · Gráficos y B-roll (pasada 3)
Construye las escenas del plan aprobado. Lee `references/escenas.md` (cómo se ve cada escena) y `references/motion-graphics.md` (cómo hacerlas con FFmpeg o con Remotion).
- Antes de construir, haz la lista de assets (lo que necesitas) y búscalos primero en `broll/`, `marca/logos/` y `referencias/`. Si falta algo, pídeselo al usuario. Usa solo material con derechos de uso: fotos propias de listings, o stock gratuito con licencia clara.
- Si el usuario pide texto o elementos **detrás de su cabeza**, eso necesita separar a la persona del fondo. Es opcional y pesado; sigue la sección correspondiente de `motion-graphics.md`.
- Muestra la versión y espera aprobación.

### 5 · Sonido y cierre (pasada 4)
```bash
python3 "${SKILL_DIR}/scripts/finalize.py" --input proyectos/X/v3_graficos.mp4 --output proyectos/X/final.mp4 \
  --music musica/tema.mp3 --duck --sfx "0.2:sfx/whoosh.wav,14.8:sfx/click.wav" \
  --logo marca/logos/logo.png --logo-seconds 2.5 --cover proyectos/X/portada.jpg --cover-time 1.0
```
- La música va baja (-20 dB por defecto) y se agacha sola cuando el broker habla (`--duck`). Pon efectos solo donde algo aparece: whoosh en transiciones y click en textos clave. Si se abusa de ellos, cansan.
- Al final se normaliza el volumen a -14 LUFS, el estándar de redes, y se genera una portada desde un frame.
- Entrega la ruta de `final.mp4` y de la portada, más un caption sugerido con hashtags locales (#poconos #poconosrealestate).

### 6 · Revisiones y aprendizaje
- Las revisiones se piden en lenguaje normal ("el gráfico entra tarde", "los subtítulos van muy rápido"). Aplica el cambio en la pasada que corresponda y re-renderiza solo desde ahí. No hace falta rehacer el corte para cambiar un color.
- Cuando el usuario corrija algo que aplica a todos sus videos ("nunca uses rojo", "me gusta el zoom más lento"), **agrégalo a `marca/aprendizajes.md`** con fecha. Así la skill mejora con cada uso.

## Reglas que protegen al usuario
- No modifiques nunca los archivos de `tomas/`. Guarda cada versión con un nombre nuevo (`v1_`, `v2_`…), así siempre se puede volver atrás.
- **Fair Housing:** en textos y subtítulos no describas zonas por quién vive ahí. Evita palabras como "seguro", "para familias" o "buenas escuelas" y habla de precios, inventario y trayectos. Si el script del broker dice algo así, avísale.
- No inventes datos de mercado en los gráficos. Usa solo los números que dijo el broker o que te dio el usuario.
- Para usar música, efectos, fotos y videos de terceros hace falta licencia. Si no hay, pregunta.

## Archivos de referencia
- `references/escenas.md`: catálogo de escenas (texto, B-roll, mapa, gráfico, llamado de objeto, cierre de logo) y cuándo usar cada una.
- `references/marca-lobo.md`: la historia del logo y cómo convertirla en animaciones y textos.
- `references/plataformas.md`: zonas seguras, duraciones y formatos por red social.
- `references/motion-graphics.md`: cómo construir las escenas con FFmpeg o Remotion, y cómo separar del fondo.
- `references/entrenar-estilo.md`: cómo enseñarle a Claude el estilo de otro creador a partir de 10–20 videos.
- `references/revisiones.md`: frases útiles para pedir cambios y la checklist de control de calidad.
