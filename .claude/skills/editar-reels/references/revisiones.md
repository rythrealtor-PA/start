# Revisiones y control de calidad

El primer borrador suele quedar al 60–70%. Las revisiones concretas lo terminan. Ayuda al usuario a pedir cambios así, con **qué**, **dónde** (segundo) y **cómo**:

| Lo que nota el usuario | Qué hacer |
|---|---|
| "Se comió una palabra en el segundo 12" | Pasada 1: sube `--pad` a 0.06 o quita esa zona de `--drop`, y re-corta |
| "El corte se siente acelerado" | Pasada 1: `--max-gap 0.5` |
| "Los subtítulos van muy rápido" | Pasada 2: `--max-words 3`, o menos palabras clave |
| "El subtítulo tapa el gráfico" | Pasada 2: `--y 1000` en esa parte, o esconder los subtítulos durante la escena |
| "El gráfico entra tarde" | Pasada 3: adelanta el overlay 3–5 frames (0.1–0.17 s) |
| "Hay demasiadas cosas en pantalla" | Pasada 3: una sola cosa a la vez; quita la menos importante |
| "La música tapa la voz" | Pasada 4: `--music-db -24`, o activa `--duck` |
| "El logo dura poco / mucho" | Pasada 4: `--logo-seconds` |
| "No parece mi estilo" | Agregar referencias en `referencias/` y actualizar `marca/estilo.md` |

Re-renderiza desde la pasada afectada, no desde cero. Si el cambio aplica a todos los videos, anótalo en `marca/aprendizajes.md`.

## Control de calidad antes de entregar
- [ ] Los primeros 3 s tienen el hook con texto grande y algo que se mueve.
- [ ] No quedan silencios largos, respiraciones fuertes ni tomas repetidas.
- [ ] Los subtítulos están bien escritos, con nombres propios correctos (Poconos, nombre de la brokerage).
- [ ] Nada importante cae en la zona tapada de la app.
- [ ] La voz se entiende sobre la música.
- [ ] El cierre de marca está al final.
- [ ] Ningún texto viola Fair Housing ni inventa datos.
- [ ] La duración es adecuada para la plataforma.
- [ ] Hay portada y caption sugerido.
