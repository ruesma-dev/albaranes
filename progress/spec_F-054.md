<!-- progress/spec_F-054.md -->
# Spec F-054 · sv1 ingiere los PDF de correos adjuntos encadenados (2026-09-30)

Autor: spec-author. Rama `feature/F-054-correo-adjunto-encadenado` (worktree
`../albaranes-F-054`, desde `dev` c8a295e). Estado: **`spec_ready`**.

## Qué se ha escrito

- `specs/F-054-correo-adjunto-encadenado/requirements.md` (149/150): R1–R27
  en EARS, en cinco bloques: clasificación, extracción, ingesta, destino y
  logs/cableado.
- `specs/F-054-correo-adjunto-encadenado/design.md` (239/250): solo sv1,
  ficheros a crear/modificar/no tocar, contrato exacto del `meta` (§6),
  pipeline (§7), tests (§8), decisiones DA1–DA7 (§9), verificación manual (§10).
- `specs/F-054-correo-adjunto-encadenado/tasks.md`: T1–T13, entre ellas T12
  (MANUAL, posterior al cierre: devolver a mano los correos de `Errores`) y
  T13 (`bash harness/init.sh`).
- Alta de F-054 en `harness/features.json` (`spec_ready`, `sdd`, `rigor`
  `estandar`, `priority` 1, `servicios` `["sv1-email"]`) y `BACKLOG.md`
  regenerado.
- Puerta de tamaño: `python -m harness.tamano --feature F-054` →
  dentro de los topes.
- Punto de partida: `progress/explore_F-054_encadenados.md`, commiteado junto
  con la spec. Modelo: F-020 de `partes` (rama `dev`), leído en solo lectura.

## Decisiones del humano recogidas (cerradas, requirements DH1–DH4)

- DH1: el extractor MIME vive en sv1 (`infrastructure/document/` + puerto en
  `domain/ports/`), no en `ruesma_comun`.
- DH2: alcance mínimo; los adjuntos directos no cambian; 5 niveles, todo o
  nada; solo PDF.
- **DH3** (contestada el 2026-09-30): el contexto de IA1 (F-048) es el del
  correo **EXTERIOR**, el de quien reenvía, con `ContextoCorreo` sin cambios.
  Las cabeceras del interior quedan fuera de alcance: no se leen, no se
  loguean y no viajan a ninguna parte.
- DH4: fuera `conversationId`/hilo, enlaces, `.msg`, imágenes interiores y el
  reproceso automático de `Errores`.

**No queda ninguna pregunta abierta.**

## Decisiones de diseño que conviene que el humano valide (design §9)

1. **DA1 · `$value` y no `$expand`**: un solo GET con el cliente de hoy, como
   en partes.
2. **DA2 · Tope de 5 niveles como constante**, no variable de entorno. Si se
   excede, **todo o nada**.
3. **DA3 · Un `.eml` adjuntado como fichero también se abre.** Hoy viaja
   opaco a sv2, que no puede leerlo. Es un cambio de comportamiento
   deliberado.
4. **DA4 · Un correo adjunto sin PDF, junto a otras páginas aceptadas, va a
   `Procesados` con WARNING.** Es el mismo criterio que D2 de partes. La
   alternativa es mandarlo siempre a `Errores`.
5. **DA5 · Dos claves nuevas en `meta`** (`correo_adjunto_id` y
   `correo_adjunto_nivel`), que solo llegan a `workflow_runs.payload_json`.
   sv3 las ignora porque traduce con un mapeo cerrado
   (`workflow_context_adapter.py`). No cambian ni `MensajeExtraccion` ni sv2.
6. **DA6 · No se loguea el `name` de Graph de un correo adjunto**: Graph pone
   ahí el asunto del mensaje adjunto, y loguearlo contradiría DH3 y R36.
   Aquí nos apartamos de partes, que sí lo loguea.
7. **DA7 · Una página duplicada cuenta como aceptada**, como hoy: un correo
   reprocesado va a `Procesados`.

Otras dos elecciones del spec-author:

- **Rigor `estandar`**: toca solo sv1; no hay schema, ni contratos de cola o
  blob, ni recurso compartido, ni dinero (igual que F-020 de partes). Si el
  humano quiere tratar la ingesta del buzón de producción como `critico`, se
  cambia el campo.
- **Prioridad 1**: en el caso mixto se pierden albaranes sin aviso.

## Hallazgo aparte (NO se arregla en F-054)

`services/albaranes-email/infrastructure/graph/token_provider.py` es **copia
literal** de `services/albaranes-comun/ruesma_comun/graph/token_provider.py`:
solo difiere la línea 1, y `main.py:16` importa la copia local. Incumple la
regla del monorepo de no copiar lógica compartida. Propuesta: ficha propia en
el backlog que haga que sv1 importe la de `ruesma_comun` y borre la copia.
Design §4 la declara intocable dentro de F-054.

## Riesgos que el implementer debe tener presentes

- El constructor de `PollingPipeline` gana un argumento obligatorio. Eso
  obliga a tocar `tests/dobles_sv1.py` y los dos constructores de
  `tests/test_f048_r36_logs.py`, sin cambiar ninguna aserción.
- Los textos de log que casan los tests de F-048 (`ERROR sv7`,
  `sin contexto de correo (…)`) se conservan literales.
- La verificación real contra el buzón la hace el humano tras desplegar
  (T12). Ningún agente llama a Graph.
