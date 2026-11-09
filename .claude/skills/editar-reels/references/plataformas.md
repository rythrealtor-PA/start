# Plataformas: formato, zona segura y duración

Todos los videos van en **1080×1920 (9:16)** a 30 fps. 4K vertical (2160×3840) solo si el usuario lo pide; pesa más y tarda más, sin ventaja real en el teléfono.

## Zona segura (en un cuadro de 1080×1920)
La interfaz de cada app tapa partes del video. Nada importante (subtítulos, cifras o logos) debe caer ahí.

| Plataforma | Arriba | Abajo | Derecha (botones) | Izquierda |
|---|---|---|---|---|
| Instagram Reels | ~220 px | ~420 px (caption y nombre) | ~140 px | ~60 px |
| TikTok | ~160 px | ~480 px | ~160 px | ~60 px |
| YouTube Shorts | ~200 px | ~400 px | ~150 px | ~60 px |

- La zona segura común queda entre y≈220 y y≈1440, y x≈60 a x≈920. Ahí van los subtítulos (por defecto en y=1180, centrados) y los gráficos.
- Si un gráfico ocupa el centro, sube los subtítulos con `--y 1000` o escóndelos en esa escena.

## Duración
- Reels: lo mejor suele ser 15–45 s; un video de historia o explicación puede llegar a 60–90 s si retiene.
- TikTok: menos de 90 s.
- Shorts: menos de 60 s.
- Si el corte final pasa de 60 s, propón al usuario partirlo en dos videos o quitar una idea.

## Audio
- Normaliza a -14 LUFS (`finalize.py` ya lo hace).
- La música queda debajo de la voz; con `--duck` se agacha sola.

## Portada
- Usa un frame con la cara expresiva y el texto del hook (`--cover`). Si el usuario quiere una portada diseñada, puede hacerla en Canva o en un generador de imágenes a partir de ese frame.
