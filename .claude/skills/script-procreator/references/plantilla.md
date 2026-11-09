# Plantilla de entrega (cópiala tal cual en cada guion)

````markdown
# [Título interno del video]

| Plataforma | Duración estimada | Objetivo | Audiencia | Formato | Modo |
|---|---|---|---|---|---|
| Reels/TikTok | [N] s | Marca / Leads / … | [una persona concreta] | [formato de formatos.md] | Palabra por palabra / Viñetas |

## 🎣 Hook (0–[N] s)
- **Visual:** [qué se ve en el primer frame y qué se mueve]
- **Dice:** "[frase exacta]"
- **Texto en pantalla:** `[máx. 7 palabras]`

## Guion con tiempos
| Tiempo | Visual / escena (editar-reels) | Script | Texto en pantalla |
|---|---|---|---|
| 0–3 s | A-roll + texto grande | "[hook]" *(traducción si aplica)* | `[…]` |
| … | … | "[…]" — **re-hook:** "[…]" | `[…]` |
| [fin] | A-roll → cierre de marca | "[pregunta final]" | `[…]` |

## Texto para grabar (teleprompter)
[HOOK]
[frase del hook]

[PUNTO 1]
[…]

[CIERRE]
[…]

## Caption
[2–3 líneas: refuerza el hook + la pregunta para comentar] 
[5–8 hashtags: 2–3 locales (#poconos #poconosrealestate), 2 de nicho, 1–2 amplios]

**Comentario fijado:** [pista, pregunta o "comenta X para…"]

## Hooks alternativos (A/B)
1. "[…]"
2. "[…]"
3. "[…]"

## Notas de edición
- Palabras clave a resaltar en los subtítulos: [ … ]
- B-roll o material que hay que conseguir: [ … ]
- Firma de marca: [hoja → llave en …s / cierre de logo]

## Checklist
- [x] Hook < 3 s, confirma la promesa y abre una pregunta
- [x] Punto más fuerte primero · re-hooks en cada transición
- [x] Dos o más emociones · cierre con visualización y CTA o pregunta
- [x] Duración dentro del objetivo · sin datos inventados · Fair Housing ok
````

**Reglas del "Texto para grabar":**
- Solo lo que se dice en voz alta, en el idioma de grabación, con las marcas de sección en mayúsculas entre corchetes (`[HOOK]`, `[PUNTO 1]`, `[RE-HOOK]`, `[CIERRE]`) en su propia línea. `estimar_duracion.py` usa esas marcas para calcular los tiempos de cada sección.
- Las pausas intencionales se marcan con `(pausa)`; no cuentan como palabras y suman 0.5 s.
- Nada de acotaciones de cámara en esta sección; esas van en la tabla.
