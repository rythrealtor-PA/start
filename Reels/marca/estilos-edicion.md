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
