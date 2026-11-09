# Cómo construir las escenas (FFmpeg y Remotion)

Hay dos caminos. Elige según la escena:
- **FFmpeg:** rápido y sin instalar nada más. Sirve para zooms, B-roll con viñeta, tarjetas de texto simples, superponer PNG y meter clips.
- **Remotion** (React → video, necesita Node.js): para animaciones de verdad, como líneas que se dibujan, gráficos, la transición hoja → llave, mapas y textos que entran palabra por palabra.

Trabaja a 1080×1920, 30 fps. Cada escena se renderiza como **clip aparte** (`escenas/03_grafico.mp4` o `.mov` con transparencia) y luego se coloca encima del video base en su rango de tiempo. **El audio siempre viene del video base**: los gráficos no cambian la voz.

## Colocar una escena encima del video (en su rango de tiempo)
Escena a pantalla completa de 4.0 s, del segundo 12.5 al 16.5:
```bash
ffmpeg -i base.mp4 -i escenas/03_grafico.mp4 -filter_complex \
 "[1:v]setpts=PTS-STARTPTS+12.5/TB[g];[0:v][g]overlay=0:0:enable='between(t,12.5,16.5)':eof_action=pass[v]" \
 -map "[v]" -map 0:a -c:v libx264 -crf 18 -preset veryfast -pix_fmt yuv420p -c:a copy out.mp4
```
Si son varias escenas, encadena los overlays en un solo comando (`[v1][g2]overlay=...`) para no recomprimir el video muchas veces. Para un clip con transparencia (texto sobre la cara), usa ProRes 4444 `.mov` o WebM VP9 con alpha.

## Recetas FFmpeg
**Zoom suave (punch-in) en un tramo**, del 100% al 110% entre 5.0 y 5.6 s, que se mantiene hasta 8 s:
```bash
ffmpeg -i in.mp4 -vf "scale=iw*2:-1,zoompan=z='if(between(it,5,5.6),1+0.1*(it-5)/0.6,if(between(it,5.6,8),1.1,1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30" -c:a copy out.mp4
```
(`it` es el tiempo en segundos. Escalar ×2 antes evita el temblor del zoompan.)

**B-roll con Ken Burns, viñeta y oscurecido** (clip de 3 s a partir de una foto: `d=90` = 90 cuadros a 30 fps; no uses `-loop`, multiplicaría la duración):
```bash
ffmpeg -i casa.jpg -vf "scale=2160:-2,zoompan=z='1+0.0015*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=90:s=1080x1920:fps=30,vignette=PI/4,eq=brightness=-0.05" -pix_fmt yuv420p escenas/broll_casa.mp4
```

**Tarjeta de texto simple** (fondo de color con texto centrado; necesita la ruta de la fuente):
```bash
ffmpeg -f lavfi -i color=c=0x14161A:s=1080x1920:d=3:r=30 -vf "drawtext=fontfile=marca/fuentes/Inter-Bold.ttf:text='We count keys,':fontcolor=white:fontsize=84:x=(w-tw)/2:y=820,drawtext=fontfile=marca/fuentes/PlayfairDisplay-Italic.ttf:text='not sales.':fontcolor=0xE8B04B:fontsize=110:x=(w-tw)/2:y=930,fade=t=in:d=0.3" -pix_fmt yuv420p escenas/texto.mp4
```

## Remotion (animaciones)
1. La primera vez, en `Reels/motion/`: `npx create-video@latest --yes --blank motion`. Pide permiso antes, porque descarga paquetes. Instala con `npm i`.
2. Crea un componente por tipo de escena (`TextoCinematico`, `Grafico`, `LineaIdeas`, `HojaLlave`, `Mapa`) que reciba props como textos, números, colores y fuentes. **Reutilízalos de video en video.** Con el tiempo se vuelve la librería de la marca.
3. Lee los colores y fuentes de `marca/estilo.md` y carga las fuentes desde `marca/fuentes/` con `@font-face`.
4. Usa curvas de animación suaves (`spring` o `interpolate` con `Easing.bezier(0.16,1,0.3,1)`), nada lineal. Las entradas duran 0.3–0.6 s y las salidas son más rápidas.
5. Para renderizar una escena: `npx remotion render <Id> escenas/03_grafico.mp4 --props='{"...": "..."}'`. Para transparencia: `--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le` → `.mov`.
6. Si Remotion falla por el navegador, necesita Chrome; Remotion lo descarga solo la primera vez.

**Hoja → llave:** dos PNG (`hoja.png`, `llave.png`). La hoja cae con una rotación sinusoidal de y=-200 a y=900 en 0.7 s. En el último 0.2 s hace un crossfade y un scale-pop a la llave, que brilla un instante y sale.

## Texto o elementos detrás de la cabeza (opcional, pesado)
Requiere separar a la persona del fondo cuadro por cuadro:
1. `pip install "rembg[cpu]"` (pide permiso; descarga un modelo de unos 170 MB).
2. Extrae los frames del tramo: `ffmpeg -ss A -to B -i base.mp4 frames/%05d.png`.
3. Saca la máscara de cada frame: `rembg p -om frames mascaras`.
4. Compón en este orden: fondo (video), texto o gráfico, la persona recortada encima (video con la máscara como alpha: `alphamerge`).
Úsalo solo en 1–2 momentos clave, como el hook. Tarda varios minutos por segundo de video en una computadora sin tarjeta gráfica.

## Checklist antes de mostrar la pasada
- [ ] Ningún texto en la zona tapada (ver `plataformas.md`).
- [ ] Cada gráfico entra justo cuando se dice la palabra (±3 frames).
- [ ] Nada tapa la cara en los momentos emotivos.
- [ ] Las fuentes y colores son los de `estilo.md`.
