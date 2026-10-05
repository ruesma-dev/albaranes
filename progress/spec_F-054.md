<!-- progress/spec_F-054.md -->
# Spec F-054 · sv1 ingiere los documentos de correos adjuntos encadenados

Autor: spec-author. Rama `feature/F-054-correo-adjunto-encadenado` (worktree
`../albaranes-F-054`, desde `dev` c8a295e). Estado: **`spec_ready` v2**, lista
para implementar (no hay ninguna feature `in_progress`).

## Historial

- **v1 (2026-09-30)**: spec solo para PDF. Commit `1c9757b`.
- **v2 (2026-10-02)**: decisiones del humano sobre DA1–DA7. Las imágenes
  válidas del interior también entran (DH5); DA4 reformulada; nueva DA8.

## Qué hay

- `specs/F-054-correo-adjunto-encadenado/requirements.md` (150/150): R1–R27 en
  EARS y decisiones del humano DH1–DH5.
- `specs/F-054-correo-adjunto-encadenado/design.md` (246/250): solo sv1. Incluye:
  - el extractor `MimeDocumentoExtractor`, en
    `infrastructure/document/mime_documento_extractor.py` (renombrado en v2:
    ya no saca solo PDF);
  - el modelo `DocumentoInterior`;
  - el contrato del `meta` (§6), el pipeline (§7), los tests (§8) y DA1–DA8 (§9).
- `specs/F-054-correo-adjunto-encadenado/tasks.md`: T1–T13. La fase RED, con
  traza, cubre R1, R7, R9, R15, R21 y R25. T12 es la tarea MANUAL posterior
  al cierre. T13 es `bash harness/init.sh`.
- `harness/features.json`: título y descripción de F-054 al día con v2.
  `BACKLOG.md` regenerado.
- Puerta de tamaño (`python -m harness.tamano --feature F-054`): dentro de los
  topes.

## Decisiones del humano (todas cerradas; no queda ninguna pregunta abierta)

- **DH1–DH4 (2026-09-30)**:
  - el extractor va en sv1;
  - los adjuntos directos no cambian;
  - tope de 5 niveles, todo o nada;
  - el contexto de IA1 es el del correo **exterior**, y las cabeceras del
    interior quedan fuera;
  - fuera de alcance: hilo, enlaces, `.msg` y el reproceso automático.
- **DH5 (2026-10-02)**: «si no tiene pdf pero tiene imagenes validas, tambien
  vale». «Imágenes interiores» sale de la lista de fuera de alcance.
- **DA1, DA2, DA3, DA5, DA6 y DA7**: aceptadas tal cual.

## Cómo se ha concretado DH5 (lo que el humano debe conocer)

- **Qué hace hoy el camino directo con una imagen.** `_is_eligible` no filtra
  tipos: solo descarta inline (`isInline` de Graph), `itemAttachment` y
  `referenceAttachment`, y lo que pasa de `MAX_ATTACHMENT_MB`. El
  `PdfPageSplitter` deja cualquier no-PDF como un único documento con su
  `mime_type`. sv2 trata como imagen todo `image/*` y lo pasa por el
  preproceso best-effort.
- **DA8 · Imagen interior válida = parte `image/*` con `Content-Disposition:
  attachment`**, y bajo `MAX_ATTACHMENT_MB`. Son los mismos dos filtros del
  camino directo, traducidos a MIME: `inline` es lo que Graph marca
  `isInline`. No se filtra ningún tipo de imagen, porque el camino directo
  tampoco lo hace.
- **DA4 v2.** Un correo adjunto sin PDF ni imagen válida, junto a otras páginas
  aceptadas, va a `Procesados` con WARNING. Con DH5, lo que queda sin
  documento es texto o logos inline, que no traen albarán; mandarlo a
  `Errores` obligaría a reprocesar a mano un correo cuyos albaranes ya
  entraron. Si el correo no tiene ninguna página aceptada, va a `Errores`.
- **Riesgos anotados, sin filtro nuevo** (design §9):
  - Logos y firmas pequeñas: el camino directo no tiene tamaño mínimo, así
    que una firma adjuntada como `attachment` entra y gasta una extracción
    de IA. Las firmas incrustadas (`inline`, con `cid:`) sí se filtran.
  - Una imagen sin `Content-Disposition` se ignora con WARNING. Si algún
    cliente adjunta fotos así, se perderían. Si se observa, se abre una ficha
    propia.

## Hallazgo aparte (NO se arregla en F-054)

`services/albaranes-email/infrastructure/graph/token_provider.py` es **copia
literal** de `services/albaranes-comun/ruesma_comun/graph/token_provider.py`:
solo cambia la línea 1, y `main.py:16` importa la copia local. Incumple la
regla del monorepo de no copiar lógica compartida. Propuesta: una ficha propia
en el backlog para que sv1 importe la de `ruesma_comun` y se borre la copia.
Design §4 la declara intocable dentro de F-054.

## Para el implementer

- El constructor de `PollingPipeline` gana un argumento obligatorio. Hay que
  tocar `tests/dobles_sv1.py` y los dos constructores de
  `tests/test_f048_r36_logs.py`, sin cambiar ninguna aserción.
- Se conservan literales los textos de log que casan los tests de F-048
  (`ERROR sv7`, `sin contexto de correo (…)`).
- Ningún agente llama a Graph. La verificación real es la T12, que hace el
  humano tras desplegar.
- Rigor `estandar`, prioridad 1. Toca solo sv1: no hay schema, contratos de
  cola o blob, recurso compartido ni dinero.
