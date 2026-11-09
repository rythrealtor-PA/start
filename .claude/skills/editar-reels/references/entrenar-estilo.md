# Enseñarle a Claude un estilo de edición nuevo

Úsalo cuando el usuario diga "quiero que mis videos se vean como los de X". La IA copia bien un estilo cuando entiende **por qué** funciona cada escena, no solo cómo se ve.

## 1. Juntar referencias
- Pide al usuario de 10 a 20 videos del creador o estilo que le guste, ojalá los mejor editados. Van en `referencias/<nombre-estilo>/`. Pueden ser archivos o links. Si es un link y la skill `watch` está instalada, úsala para sacar los frames y la transcripción.
- Las capturas de pantalla de escenas sueltas también sirven. Ponlas en `referencias/<nombre-estilo>/capturas/`.

## 2. Analizar cada video
Por cada video, saca una transcripción palabra por palabra y frames de cada cambio de escena:
```bash
python3 "${SKILL_DIR}/scripts/transcribe.py" ref.mp4 ref.json
ffmpeg -i ref.mp4 -vf "select='gt(scene,0.25)',scale=360:-1" -vsync vfr frames/ref_%03d.png
```
Mira los frames y estudia tres cosas:
1. **Dónde va cada animación respecto al guion.** ¿Qué tipo de frase dispara un gráfico? ¿Cuándo vuelve a la cara?
2. **Cómo está compuesto el diseño.** Fuentes, tamaños, colores, texturas, posición del texto y cuántos elementos hay a la vez.
3. **La lógica de la animación.** Cuánto dura cada entrada y salida, qué curva usa y si hay movimiento de cámara.

## 3. Agrupar en principios
Agrupa todas las escenas en categorías (texto, B-roll, gráfico, ilustración, etc.) y escribe de 5 a 10 **principios** del estilo, cada uno con su regla de uso ("cuando anuncia algo nuevo, cara; cuando describe, se muestra").

## 4. Guardar el estilo
Guarda el resultado en `marca/estilos/<nombre-estilo>.md` con:
- Los principios con su regla de uso y una o dos capturas de ejemplo.
- Fuentes, colores (hex), texturas y tamaños.
- Las duraciones típicas de las animaciones.
- Un "mapa guion → escena" con frases típicas y la escena que les corresponde.

Cuando el usuario pida un video "en el estilo X", lee ese archivo junto con `estilo.md`. Si chocan, manda el de la marca (logo, colores, nombre); el estilo X aporta el ritmo y la composición.

## Advertencia
Copia la **lógica** del estilo, no el contenido. No reutilices el material, los gráficos ni la música de otro creador en los videos publicados.
