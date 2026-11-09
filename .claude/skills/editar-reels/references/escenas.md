# Catálogo de escenas

Usa este catálogo para armar el plan de edición. Cada escena dice **cuándo usarla**, **cómo se ve** y **cómo hacerla**. Las fuentes, colores y textura salen de `marca/estilo.md`; así todas las escenas se ven de la misma marca.

## Regla del ritmo
- **Si dice algo nuevo, va la cara. Si lo describe, se muestra.** Cuando el broker anuncia una idea ("hay tres errores…"), va en A-roll, que es su cara. Cuando la explica ("el primero es…"), se muestra algo.
- Cambia algo cada 3–5 s: corte, zoom suave, texto o B-roll.
- Una sola cosa protagonista a la vez. Si hay gráfico, el subtítulo puede ocultarse o subir.
- Pon pocas escenas en los momentos emotivos y más en los de datos.

## 1. A-roll con subtítulos (la base)
- **Cuándo:** el hook, las ideas nuevas, las opiniones, la emoción y el cierre con la pregunta.
- **Cómo se ve:** la cara del broker con subtítulos animados (`captions.py`). Usa un **zoom suave** (punch-in del 100% al 108–112% en 0.5–0.8 s) en la palabra más fuerte de cada frase. Si hay un cambio de tema, alterna el encuadre: plano normal y luego un plano más cerrado.
- **Cómo:** `vertical.py --zoom 1.1` para el plano cerrado. Para un zoom animado, usa `zoompan` o Remotion (ver `motion-graphics.md`).

## 2. Texto protagonista ("cinematic text")
- **Cuándo:** una frase memorable, una cifra o una promesa ("Contamos llaves, no ventas").
- **Cómo se ve:** fondo liso con textura de papel suave, en el color de marca u oscuro. La palabra clave va en negrita grande al centro, con la fuente de acento si es emotiva. Las otras palabras van más pequeñas arriba o abajo del centro. Pon máximo 5 palabras en pantalla. Entra con un deslizamiento corto o un fade de 0.3 s.
- **Variante cita:** comillas grandes alrededor del texto. Sirve para cerrar con la idea principal.

## 3. B-roll con texto
- **Cuándo:** el broker describe algo que se puede ver, como una casa, una cocina, las montañas, una firma o unas llaves.
- **Cómo se ve:** la toma de apoyo de fondo, con viñeta (bordes oscuros), un leve desenfoque en los bordes y quizá una textura de papel. El texto cinematográfico encima describe la escena.
- **Fuente:** primero busca en `broll/` (material propio), luego en fotos de listings con permiso y, al final, en stock libre con licencia clara.

## 4. Mapa / ubicación
- **Cuándo:** el broker habla de pueblos, zonas, trayectos o "dónde comprar".
- **Cómo se ve:** un mapa simple de los Poconos con un punto que se ilumina. Una línea dibuja el trayecto y aparece una etiqueta con el nombre del pueblo.
- **Ojo (Fair Housing):** las etiquetas hablan de precios, inventario, días en el mercado y trayectos. Nunca de quién vive ahí.

## 5. Gráfico / número
- **Cuándo:** precios, porcentajes, comisiones, días en el mercado o tasas.
- **Cómo se ve:** fondo oscuro con una cuadrícula fina que brilla, y una bola o línea del color de acento que sube o baja mientras el broker habla. Cada cifra aparece justo cuando la dice. Para el desglose de una comisión, usa barras que se restan una por una.
- **Datos:** solo números que dijo el broker o que te dio el usuario. Si es un ejemplo, escribe "Ejemplo" en pantalla.

## 6. Línea que conecta ideas
- **Cuándo:** una lista de pasos, una progresión ("primero… luego… al final") o tres conceptos ligados.
- **Cómo se ve:** fondo claro con textura y una línea fina del color de acento que se dibuja. La cámara sigue la línea, y la línea se interrumpe en cada palabra clave para continuar hacia la siguiente.

## 7. Llamado de objeto ("callout")
- **Cuándo:** el broker muestra o menciona algo concreto, como un contrato, unas llaves, un letrero o una foto suya.
- **Cómo se ve:** el objeto al centro (recortado o en tarjeta con sombra), con dos o tres etiquetas alrededor que aparecen una por una.

## 8. Lado a lado
- **Cuándo:** comparaciones como "antes y después", "lo que hacen otros y lo que hacemos nosotros" o "amanecer contra atardecer".
- **Cómo se ve:** pantalla dividida, con imagen o ícono a un lado y texto al otro, o dos columnas con un ✓ y una ✗.

## 9. Firma de marca: hoja → llave
- **Cuándo:** una transición importante, cuando se menciona una familia o una casa vendida, o el inicio del cierre.
- **Cómo se ve:** una hoja de fresno cae girando y, al tocar el centro, se convierte en una llave. Dura 0.8–1.2 s y lleva un "whoosh" suave.
- Ver `marca-lobo.md`.

## 10. Cierre de marca
- **Cuándo:** siempre, al final.
- **Cómo:** `finalize.py --logo`. Agrega 2–3 s después de la última palabra con el último frame congelado, desenfocado y oscurecido, y el logo entrando con un fade.

## Ejemplo de plan (tabla que se entrega al usuario)

| Tiempo | Lo que dice | Escena | Nota |
|---|---|---|---|
| 0.0–3.1 | "Every agent puts their face on their sign…" | A-roll + texto grande del hook | zoom en "disappear" |
| 3.1–8.0 | "In real estate it's always about the agent…" | B-roll de letreros genéricos + texto | sin caras reales |
| 8.0–12.5 | "So our wolf fades, on purpose." | Llamado de objeto: el logo, con zoom al lobo desvaneciéndose | — |
| … | … | … | … |
| 50–57 | "What did your last agent get wrong?" | A-roll + subtítulos | cierre con pregunta |
| final | — | Cierre de marca | 2.5 s |
