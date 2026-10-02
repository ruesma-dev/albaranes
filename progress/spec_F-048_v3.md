<!-- progress/spec_F-048_v3.md -->
# F-048 · Spec v3 (2026-09-23): solo obra; discrepancia y correo ambiguo a revisión

Autor: spec-author. Rama `feature/F-048-correo-contexto-ia1`. Aplica las
decisiones del humano del 2026-09-23 sobre la spec v2 (2026-09-22) sin
rehacerla. Tamaños: requirements 149/150, design 249/250, tasks 41 tareas, una
por línea (`python -m harness.tamano --feature F-048` en verde).

## Decisiones aplicadas

1. **Precedencia y cruce (D3 confirmada)**: la cita literal del humano está en
   design D3. IA1 lee el código del correo y el del papel por separado; el
   resolver de sv2 cruza y sella. Manda el correo.
2. **D6 revisada: la discrepancia MANDA A REVISIÓN.** Revoca la v2 (que la
   guardaba y pintaba sin revisión). sv3 añade `obra_correo_distinta_papel` a
   `review_reasons` en el merge, en `_build_review_reasons`, con un
   `_motivos_de_origen_datos` hermano de `_motivos_de_clasificacion` de F-043
   (verificado: `albaran_confidence_service.py:280-288` y `:547-646`). Se usa
   el código del correo. Si el papel no trae código, no hay discrepancia.
   D6 bis (bajar el %) sigue fuera.
3. **D4 bis decidida**: con varios códigos, si el del papel es uno de ellos
   → `correo_confirma_papel`, sin revisión; si no, o el papel no trae código
   → `correo_ambiguo`, sv3 añade `obra_correo_ambigua`. En los dos casos el
   resolver no toca `cabecera.obra_codigo` (se queda la lectura del papel, o
   ninguna) y los códigos van a `candidatos_correo`, visibles en sv4.
4. **D8 nueva, solo obra**: fuera `lectura_correo.partida_codigos`, R21 (la
   precedencia de la partida), la discrepancia por línea, `DiscrepanciaPartida`
   y `origen_datos.partida`. R16 obliga al prompt a decir que del correo nunca
   se toma la partida. En «Fuera de alcance» consta «partida en el correo, de
   momento».

## Nombres de los motivos (ajustados a la convención)

Los motivos de F-043 llevan prefijo de campo (`clasificacion_*`). Por eso uso
`obra_correo_distinta_papel` y `obra_correo_ambigua` (el humano sugirió
`correo_ambiguo`, que sigue siendo el MOTIVO de `origen_datos.obra.motivo`,
no el de revisión). Se definen UNA vez en `ruesma_comun.contratos.origen_datos`
(`MOTIVOS_REVISION_ORIGEN`) y los importan sv3 y sv4: así no se repite la copia
de `MOTIVOS_CLASIFICACION_EN_DUDA` que F-043 dejó en `review_models.py`.

## Cambios por fichero

- **requirements.md**: renumerado de corrido, R1–R44 (antes R1–R41 y
  desordenado, con R39–R41 delante de R30). Correspondencia con la v2: R1–R17
  igual (R15 y R16 reescritas, solo obra); R18 igual y con motivo
  `correo_unico`; **R19 nueva** (el cruce y la discrepancia, antes R22);
  **R20 reescrita** (D4 bis, antes R19); R21 = antigua R20; **antigua R21 (la
  partida), retirada**; R22–R28 = antiguas R23–R29; **R29–R31 nuevas** (motivos
  de sv3); R32–R33 = antiguas R39–R40 (R33 incluye `correo_confirma_papel`);
  **R34 nueva** (los motivos en el bloque existente y el aviso en estilo
  advertencia); R35 = antigua R41; R36–R44 = antiguas R30–R38.
- **design.md**: §1 añade cómo calcula sv3 los motivos y cómo los pinta sv4
  (verificado con grep); D3 con la cita del 23; D4 bis decidida; D5 señala la
  duda de `correo_fuera_de_lista`; D6 reescrita; D8 nueva; §3 sin
  `DiscrepanciaPartida` ni `partida`, con los motivos nuevos, las constantes de
  revisión y `normalizar_codigo`; §5 sv3 (`_motivos_de_origen_datos`,
  `origen_datos: OrigenDatos | None`) y sv4 (`origen_en_duda`); §6 no se tocan
  `marcar_revision_cabecera`, las redes ni el DDL (`review_reasons_json` ya
  existe); §7 reducido; §9: riesgo nuevo «MÁS albaranes a revisión», falsas
  discrepancias por formato y la duda abierta. Condensado para caber en 250.
- **tasks.md**: T1–T41 (antes T1–T40). T5 con los motivos y sin partida; T13
  y T16 solo obra; T17 = obra único/lista/fuera/sin dato/sin correo; **T18
  reescrita** (el cruce y D4 bis; ya no es la partida); **T26 nueva** (sv3,
  motivos de revisión, RED primero); T27–T28 = antiguas T26–T27, ampliadas con
  los motivos y `origen_en_duda`; T29–T41 = antiguas T28–T40, con las
  referencias a R y a T renumeradas. T37 (manual E2E) comprueba ahora
  `review_required`, `review_reasons_json` y el aviso; T38, que el motivo no
  se duplica al reprocesar; T39, que no hay motivos `obra_correo_*` sin correo;
  T40 cuenta las revisiones nuevas.
- **Trazabilidad** comprobada con un script: 44 R, todas con al menos una T;
  41 T de corrido.
- **harness/features.json**: título «...SOLO el codigo de OBRA, cruzado con el
  papel» y un párrafo final con las decisiones del 23. `status` sin tocar.
  `BACKLOG.md` regenerado con `python harness/backlog.py`.
- **progress/current.md**: cabecera y punto de reanudación al día, con las
  dudas abiertas.

## Orden de despliegue

Sigue sv3 → sv2 → sv1. Los motivos nuevos no lo cambian: solo se disparan con
`origen_datos`, que emite únicamente el sv2 nuevo. sv4 puede ir cuando sea,
porque su bloque de motivos ya pinta cualquier código.

## Dudas para el humano (no bloquean; están en current.md)

1. `correo_fuera_de_lista` no manda a revisión (D5 validada el 22). Con «si no
   cuadra, revisión» quizá debería.
2. El cruce solo ignora mayúsculas y espacios. Con ceros a la izquierda o
   guiones saldrían falsas discrepancias, y esos albaranes irían a revisión.
3. La muestra validada («diez de los 33 con partida mal») apuntaba a la
   partida; quizá haya que reajustarla. Siguen pendientes quién captura la
   muestra y cómo llegan los correos.
4. La ficha de F-049 menciona `origen_datos.partida.validada` «que F-048 deja a
   null»: ya no existe; lo creará F-049 (es compatible, `extra="ignore"`).
   La ficha de F-049 no se ha tocado.
5. Criterio que he fijado yo (revisable): con varios códigos, «distintos»
   significa tras normalizar, y se cuentan antes de filtrar por la lista de
   obras activas. En ese caso el resolver no toca la cabecera, así que la lista
   no interviene y la red de obra de sv3 actúa como hoy.
