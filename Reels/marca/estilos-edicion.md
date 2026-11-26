# Estilos de edición de la marca (definidos por el usuario el 2026-11-09)

> Claude: lee este archivo en cada video, junto con `estilo.md` y `aprendizajes.md`.
> El usuario pide los estilos por número o por nombre ("usa la 2 y el hook text").
> Si no dice cuáles, propón en el plan cuáles usar y en qué momento.
> Las imágenes de referencia están en `referencias/estilos/`.

La clave de todos: **el texto o la imagen va DETRÁS de la persona**. Es lo más importante.
Se logra recortando a la persona en cada cuadro (MODNet, `herramientas/matte.py`) y poniéndola encima.

---

## 1 · "3 behind" (tres imágenes detrás)
- **Ref:** `referencias/estilos/1-three-behind.png`
- El usuario manda **3 imágenes** (por ejemplo, fotos de casas).
- Aparecen con una animación **smooth** (fade + escala o deslizamiento suave, una tras otra) **detrás de la persona**, en la parte de arriba: arriba a la izquierda, centro y derecha, como tarjetas con sombra, ligeramente inclinadas y superpuestas.
- Salen igual de suave.

## 2 · Texto grande con dos fuentes (detrás de la persona)
- **Ref:** `referencias/estilos/2-texto-grande-detras-a.png` ("AGENT mastermind") y `2-texto-grande-detras-b.png` ("The first showing of your house happens online").
- Texto **grande** que mezcla **dos tipos de fuente** y **dos colores** (una palabra en sans muy gruesa y otra en serif itálica).
- Va **detrás de la persona** todo el tiempo que está en pantalla. La cabeza tapa solo una parte para que se lea.
- **Aparece y desaparece de forma smooth y rápida** (unos 0.3 s de entrada y 0.2 s de salida).
- Mientras está, se **ocultan los subtítulos** normales, porque el texto grande ya es lo que dice.
- Receta Ashwood: línea serif itálica (Playfair Display ExtraBold Italic, dorado oscuro `#B8862E`) + línea sans gruesa (Inter Black, `#161616`) que ocupa todo el ancho.

## 3 · "1 behind" (una foto detrás de la cabeza)
- **Ref:** `referencias/estilos/3-one-behind.png`
- El usuario manda **una foto** (por ejemplo, una captura o la foto de una casa).
- Se pone **detrás de la cabeza** del que habla, entra smooth y sale igual.
- Dura **solo 2 segundos**.

## 4 · "Hook text" (título detrás + subtítulos encima)
- **Ref:** el hook de los primeros segundos.
- Un **título detrás de la cabeza** y, al mismo tiempo, los **subtítulos por encima de la persona**, cambiando mientras habla.
- El título dura **3 segundos**. Se usa en el hook (0–3 s).

## 5 · Título detrás de la cabeza (solo título)
- **Ref:** `referencias/estilos/5-titulo-detras.png` ("Right person")
- Igual que el 4, pero **solo el título** detrás de la cabeza, sin subtítulos encima.

---

## Cómo se construyen (herramienta)
Estilos 2, 4 y 5 (texto): `herramientas/text_behind.py` con un `capas.json` (ejemplo completo en `proyectos/2026-11-09-drive-reel/capas.json`).
```bash
python3 herramientas/text_behind.py --input proyectos/X/v1_corte.mp4 --spec proyectos/X/capas.json \
  --output proyectos/X/v3_texto.mp4 --ass-in proyectos/X/subs.ass --ass-out proyectos/X/subs_final.ass
ffmpeg -i proyectos/X/v3_texto.mp4 -vf "ass=proyectos/X/subs_final.ass:fontsdir=marca/fuentes" -c:a copy proyectos/X/v4.mp4
```
- `"y": "auto"` (valor por defecto) mide dónde está la cabeza y coloca el texto para que la tape solo un poco (`"overlap"`, 60 px; baja el número si la cabeza tapa demasiado, como cuando la persona se inclina hacia la cámara).
- `"hide_captions": true` en las capas del estilo 2; `false` en el hook (estilo 4).
- Estilos 1 y 3 (imágenes): en "lines" usa `{"image": "ruta.jpg", "width": 860, "border": 10, "radius": 28, "rotate": 0}` (ruta relativa a capas.json). Para el 3 ("1 behind") la capa dura 2 s y `"overlap"` ~200 para que la cabeza tape la parte de abajo de la foto.
- Estilo 1 ("3 behind"): capa con `"layout": "row"` y 3 imágenes; cada una con `"x"`, `"dy"`, `"rotate"`, `"width"`/`"height"` (recorte). Ejemplo en `proyectos/2026-11-11-poconos-emily/capas.json`. Opciones de capa: `"stagger"`, `"in"`, `"out"` (segundos).

## Extras (agregados el 2026-11-21, video "Google questions")
- **Fondo de video detrás de la persona:** en capas.json, `"backgrounds": [{"video": "../../broll/clip.mp4", "start": 0, "end": 2.85, "fade_in": 0, "fade_out": 0.3}]`. El clip reemplaza la pared y la persona queda al frente; los títulos van entre el fondo y la persona. Úsalo en el hook en vez de una toma de Google Earth.
- **Barra de búsqueda que se escribe sola:** en "lines", `{"search": "is it expensive to live in the Poconos?", "width": 1000, "height": 150, "size": 50, "type_time": 1.3}`. Es genérica, sin logo de Google. Usa `overlap` ~40 para que la cabeza toque solo el borde de abajo y la pregunta se lea.
- **Clips de stock con cortes bruscos:** usa una sola toma en cámara lenta suavizada (`setpts=2*PTS,minterpolate=fps=30:mi_mode=mci`), sin cortes dentro del hook.
- **Número que cuenta hacia arriba** (precios, acres): en "lines", `{"count": 300, "fmt": "${}K", "font": "heavy", "max_size": 330, "count_time": 1.0}`. Va de 0 al número con suavidad; se ve "smooth y cool" para precios.
- **Capa al frente** (`"front": true` + `"y"` fijo): cuando el video original ya trae un zoom a la cara y la cabeza taparía todo el título, ese título va encima de la persona.

## Personaje animado que se asoma (2026-11-26, Thanksgiving)
- `herramientas/turkey.py`: un turkey dibujado (original, estilo cartoon) se asoma por un costado con medio cuerpo, saluda con el ala y parpadea. Ciclo: 6 s sin turkey, 8 s saludando, se va, y vuelve por el lado contrario. Sin sonido.
- Opciones: `--first 6 --gap 6 --show 8 --size 640 --y 900 --peek 0.67`. `--y 900` lo deja entre el título de arriba y los subtítulos, y del lado derecho no queda debajo de los botones de Instagram.
