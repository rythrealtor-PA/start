# El logo en los videos: lobo, fresno y llaves

El logo cuenta una historia. Úsala en los gráficos, transiciones y textos para que cada video refuerce la marca sin que parezca anuncio.

| Elemento | Significado | Cómo se usa en video |
|---|---|---|
| Fresno (ash tree) | El árbol de donde crece la brokerage | Silueta de fondo en las escenas de texto; textura sutil |
| Hojas que caen = llaves | Cada hoja es una familia que llegó a casa | Transición hoja → llave. Contador "Keys fallen: #" en la serie de cierres |
| Lobo mirando al amanecer | Nunca le damos la espalda al progreso | Escenas de mercado y tendencias. Luz cálida dorada en las escenas "de futuro" |
| Lobo que se desvanece | El cliente es el protagonista; nosotros somos un capítulo | Al hablar del cliente, el logo baja de opacidad y el cliente o la casa quedan al frente |
| Poconos en la melena | Donde nacimos | Escena de mapa o montañas; el trazo de las montañas se convierte en la melena |

## Animaciones de firma (prioridad)
1. **Hoja → llave** (0.8–1.2 s). Úsala en las transiciones importantes o cuando se nombra una casa o familia.
2. **Cierre de logo** (2–3 s). Va siempre (`finalize.py --logo`).
3. **El trazo de las montañas** (1.5 s). Las montañas reales se funden con la melena del lobo. Úsalo en videos de "somos de aquí".
4. **El lobo se desvanece** (1–2 s). La opacidad baja del 100% al 25% mientras el texto dice "you're the main character".

## Para construirlas hace falta
- El logo en **capas separadas** (PNG/SVG): fresno, hojas, llaves, lobo, melena con montañas y sol. Si el usuario solo tiene el logo completo, pídele las capas a su diseñador. Mientras tanto, usa el logo completo con zoom y fades.
- Una **hoja de fresno** y una **llave** en PNG transparente, para la transición.

## Textos de marca listos para pantalla
- "We count keys, not sales."
- "Our backs are never turned on progress."
- "You're the main character. We're just a chapter."
- "Born in the Poconos."
- "Keys fallen: [#]"
