---
name: script-procreator
description: Escribe guiones de video que retienen y se vuelven virales para la brokerage inmobiliaria (Reels, TikTok, Shorts y videos largos de YouTube) con el broker hablando a cámara. Combina tres insumos (el estilo propio del broker, los principios de guion que funcionan y la información del tema) para producir el guion completo con hook, cuerpo con curiosity gaps y re-hooks, cierre con CTA, tiempos, texto en pantalla, caption, hooks alternativos y notas de edición. Úsala SIEMPRE que el usuario pida un guion, script, libreto, idea de video, hook, "qué digo en el video", "hazme un reel sobre…", "write a script", contenido para redes o una serie de videos, aunque no mencione la palabra skill, y también para mejorar o reescribir un guion que ya tiene.
---

# Script Procreator

Escribe guiones que la gente vea hasta el final. La IA sola escribe guiones genéricos: sin hook, sin tensión y con aspecto de clase. Escribe guiones buenos cuando junta **tres insumos**:

1. **Su estilo:** cómo habla el broker, su ritmo y sus frases. Sale de sus videos anteriores.
2. **Los principios:** qué hace que un guion retenga. Están en `references/principios.md`.
3. **La información:** el tema, los datos, la historia o el link de donde sale el contenido.

Si falta alguno, el guion sale flojo. Tu trabajo es reunir los tres y combinarlos.

Habla con el usuario en su idioma (normalmente español). El guion va en el idioma en que se va a grabar (ver "Idioma" abajo).

## Carpeta de trabajo
Crea esta estructura la primera vez que no exista. Es el equivalente a los "tres grupos" del método:
```
Guiones/
  mi-estilo/      transcripciones o textos de videos propios que funcionaron (insumo 1)
  info/           notas, links, datos y documentos del tema de cada video (insumo 3)
  guiones/        los guiones terminados, uno por archivo: AAAA-MM-DD-tema.md
  aprendizajes.md lo que el usuario corrigió o le gustó. Léelo SIEMPRE antes de escribir.
```
Los principios (insumo 2) ya vienen en esta skill. Si el usuario tiene grabaciones propias, puede transcribirlas con la skill `editar-reels` (`transcribe.py`) y guardar el texto en `mi-estilo/`.

## Antes de escribir: leer el contexto
1. `references/principios.md`: la fórmula completa. Léela siempre: es el corazón de la skill.
2. `references/marca.md`: la brokerage, el logo (lobo, fresno, llaves, Poconos), la audiencia y las reglas legales.
3. `Guiones/aprendizajes.md` y 2–3 archivos de `Guiones/mi-estilo/` si existen. Imita el vocabulario, el largo de las frases y las muletillas buenas del broker, para que el guion suene a él y no a un robot.
4. `references/formatos.md` cuando haya que elegir un formato o un hook, o cuando el usuario pida ideas.

## El brief (pregunta solo lo que falte)
Si el usuario ya dio un tema, no lo frenes con un cuestionario. Deduce lo que puedas, usa los valores recomendados y dile qué supusiste. Pregunta, idealmente en una sola tanda con opciones:
- **Tema e información:** de qué trata y qué datos, historia o link lo respaldan. Si faltan datos, usa `[X]` en vez de inventarlos.
- **Objetivo:** reconocimiento de marca (recomendado mientras la brokerage es nueva), leads, reclutar agentes o comunidad.
- **Audiencia:** compradores primerizos, vendedores, gente que se muda a los Poconos, compradores de segunda casa, inversionistas u otros agentes. Una sola por guion. Un guion para todos no le llega a nadie.
- **Plataforma y duración:** Reel/TikTok de 30–60 s (recomendado), Short o YouTube largo de 6–12 min.
- **Modo:** palabra por palabra (recomendado para videos cortos y temas técnicos o legales) o con viñetas (historias y videos largos conversacionales).

## Cómo escribir el guion
1. **Ángulo:** busca la tensión del tema. ¿Qué problema, error, mito o pregunta hay detrás? Un tema sin tensión es una clase, y las clases no retienen.
2. **Hooks:** escribe 8–10 hooks distintos con las fórmulas de `formatos.md`. Evalúa cada uno con tres preguntas: ¿confirma el clic o la promesa?, ¿abre una pregunta que solo se responde al final?, ¿se entiende en 2 segundos sin sonido? Usa el mejor y guarda otros 3 como alternativas para probar.
3. **Cuerpo:** sigue `principios.md`. Empieza por el punto más fuerte y revela los puntos de uno en uno, dejando algo sin resolver. Pon un re-hook en cada transición y cambia algo cada 8–12 s en video corto (cada 30–40 s en video largo).
4. **Cierre:** da un resumen corto, haz que imaginen el resultado, plantea el siguiente problema y termina con un CTA natural. En reels, el cierre ideal es una **pregunta para comentarios** y la firma de marca.
5. **Tiempos:** escribe el texto hablado con marcas de sección y calcula los tiempos reales:
   ```bash
   python3 "${SKILL_DIR}/scripts/estimar_duracion.py" Guiones/guiones/archivo.md --lang en
   ```
   Si se pasa de la duración objetivo, recorta. Casi siempre sobra contexto en el cuerpo, no en el hook.
6. **Revisión:** pasa el guion por la checklist de `principios.md` (sección "Checklist") y corrige antes de mostrarlo. No le entregues al usuario un borrador que tú mismo reprobarías.

`SKILL_DIR` es la carpeta de este SKILL.md.

## Formato de entrega
Guarda el guion en `Guiones/guiones/AAAA-MM-DD-tema.md` usando **exactamente** la plantilla de `references/plantilla.md`: ficha, hook, guion con tiempos, texto para grabar, caption, hooks alternativos, notas de edición y checklist. En el chat muestra el hook, el guion con tiempos y la ruta del archivo. No pegues todo dos veces.

Las **notas de edición** usan los nombres de escena de la skill `editar-reels` (A-roll, texto protagonista, B-roll con texto, mapa, gráfico, hoja → llave, cierre de marca). Así el guion pasa directo a edición.

## Idioma
- Por defecto, el guion se graba en el idioma de la audiencia. En los Poconos suele ser inglés. Si el usuario no lo ha dicho, pregunta una vez y anota la respuesta en `aprendizajes.md`.
- Si el guion va en inglés y el usuario habla español, agrega la traducción al español debajo de cada línea del guion con tiempos (en cursiva). El "texto para grabar" va solo en el idioma de grabación.
- Para la comunidad hispana, escribe el guion directamente en español natural, no traducido.

## Series y lotes
Si el usuario pide varios guiones o "contenido para el mes", propón primero una lista de ideas con su formato, hook y objetivo, y espera a que elija. Después escribe los guiones uno por uno. Varía los formatos: no hagas cinco "3 tips" seguidos.

## Aprender del usuario
Cuando el usuario corrija algo que aplique a todos sus guiones ("no uses la palabra 'journey'", "mis hooks funcionan mejor con números", "este video tuvo 20K vistas"), anótalo con fecha en `Guiones/aprendizajes.md`. Si comparte resultados de un video publicado, anota qué formato y qué hook funcionaron. Con el tiempo, esa lista vale más que cualquier fórmula.

## Reglas que protegen al broker
- **No inventes datos, historias ni testimonios.** Usa `[X]` y avisa qué falta. Las historias de clientes van con permiso o anonimizadas.
- **Fair Housing:** no describas zonas por quién vive ahí ni uses "seguro", "para familias" o "buenas escuelas". Habla de precios, inventario, trayectos y desarrollo.
- **Comisiones:** nunca digas "la comisión estándar es X%". Siempre aclara que es negociable y que los números son de ejemplo.
- **Publicidad:** recuerda incluir el nombre de la brokerage y la licencia donde el estado lo exija.
- No copies guiones de otros creadores. Toma la estructura y escribe contenido propio.
