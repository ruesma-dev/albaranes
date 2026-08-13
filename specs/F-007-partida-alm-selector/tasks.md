<!-- specs/F-007-partida-alm-selector/tasks.md -->
# F-007 · Tanda 5 — Partida ALM por defecto y selector de candidatas · Tareas

Rama: `feature/F-007-partida-alm-selector`. Un commit por tarea
(`F-007 Tn: ...`). Los tests van junto a su implementación y NO tocan red
ni BBDD (mocks/fakes). Antes de T1: resolver con el humano las preguntas
abiertas P1–P3 del design. Al crear `tests/` en sv6/sv4, comprobar que
`pytest` está disponible en el entorno del arnés (aviso heredado de F-002).

- [ ] T1: sv6 — settings nuevos (`ALM_DEFAULT_ENABLED`,
      `FAMILIAS_DESTINADAS` con helper a `set[str]`) + esqueleto
      `services/albaran-valoracion-persist/tests/` (conftest vacío con
      comentario de ruta)
      | Verificación: `pytest services/albaran-valoracion-persist/tests -q`
      en verde (test de parseo del CSV de familias y defaults).

- [ ] T2: sv6 — `PartidaAction` += `"alm_default"` y rama nueva en
      `PartidaMatcher.match()` (kwarg `aplicar_alm_por_defecto`, literal
      ALM como `codigo_partida_final`, match IA conservado, razón
      `alm_default_suministro_no_destinado`)
      | Verificación: pytest sv6 en verde (tests `test_f007_r1_*`,
      `_r2_*`, `_r3_*` sobre el matcher puro; R1 cubre la no-regresión del
      ALM impreso y de la partida impresa).

- [ ] T3: sv6 — `ValuationBuilder`: helper de familia
      (`_es_suministro_no_destinado`), paso del flag a `match()`, fallback
      «LINEA NUEVA» prefiriendo `partida_result.codigo_partida_final`, y
      cableado de los settings en `composition.py`
      | Verificación: pytest sv6 en verde (tests `test_f007_r4_*`,
      `_r5_*`, `_r6_*`, `_r7_*`; R6 con
      `resolve_partida_for_complementaria(codigo_partida_base="ALM")`).

- [ ] T4: sv4 — `domain/services/producto_clave.py` (normalizador puro) +
      esqueleto `services/albaranes-front/tests/`
      | Verificación: `pytest services/albaranes-front/tests -q` en verde
      (tests `test_f007_r13_*`: tildes, espacios, None, truncado, misma
      entrada ⇒ misma clave).

- [ ] T5: sv4 — DDL `partida_memoria` en `initialize()` + métodos
      `obtener_partida_memoria` / `upsert_partida_memoria` en
      `review_repository.py` + setting `ALM_CODIGO_PARTIDA` en sv4
      | Verificación: pytest sv4 en verde (test `test_f007_r14_*`: el DDL
      declarado contiene `IF NOT EXISTS` y el PK compuesto). Idempotencia
      real: MANUAL (humano) — arrancar sv4 dos veces contra el PG local y
      comprobar que la segunda no falla
      (`docker compose` local o `solo-front`).

- [ ] T6: sv4 — hooks de ESCRITURA de memoria (best-effort, try/except con
      log) en `update_line_conciliacion` y en `set_line_conciliacion`
      (modo `contract_line`): clave desde la descripción de la línea del
      albarán (fallback descripción salmón), exclusión de vacío y del
      literal ALM, no-op sin `obra_codigo`
      | Verificación: pytest sv4 en verde (tests `test_f007_r10_*`,
      `_r11_*`, `_r12_*` sobre la lógica de decisión con repositorio
      fake).

- [ ] T7: sv4 — LECTURA de memoria en el detalle del documento: campo
      `partida_sugerida` en el modelo de conciliación
      (`review_models.py`), relleno solo cuando la partida efectiva está
      vacía o es ALM, best-effort
      | Verificación: pytest sv4 en verde (tests `test_f007_r9_*`: con
      memoria ⇒ sugerencia expuesta; sin obra ⇒ nada; fallo del repo ⇒ el
      detalle carga igual).

- [ ] T8: sv4 — front: `data-partida-sugerida` y `data-descripcion` en el
      input de partida (`document_detail.html`) + `app.js`: grupo
      «Candidatas (mismo recurso)» calculado de `#contrato-lines-json`
      (R8) y sugerencia de memoria preseleccionada con marca visual, sin
      autoaplicar (R9)
      | Verificación: MANUAL (humano) — en el pipeline local, abrir un
      documento de hormigón con contrato de clones: el combo muestra
      candidatas primero; elegir una partida, guardar, abrir otro albarán
      del mismo producto y obra: aparece prerrellenada como sugerencia y
      NO se persiste sin guardar.

- [ ] T9: docs — `docs/ARCHITECTURE.md` (sv4 dueño de `undo_log` y
      `partida_memoria`; regla ALM por defecto en semántica de dominio) y
      `docs/referencia/dominio_negocio_albaranes.md` §10.8 (🔶 → ✅ de las
      dos reglas implementadas)
      | Verificación: revisión del reviewer contra CHECKPOINTS.md (los
      docs cuentan lo que el código hace).

- [ ] T10: Ejecutar `bash harness/init.sh` en verde
      | Verificación: salida completa sin [KO], pegada en
      `progress/impl_F-007.md`.

Verificación E2E adicional (MANUAL, humano, requiere BBDD/pipeline local):
valorar un albarán genérico SIN partida impresa → la línea sale con
partida «ALM», `partida_action='alm_default'` en
`albaran_line_valuations`, y el precio del contrato intacto; con
`ALM_DEFAULT_ENABLED=false` el mismo albarán sale como hoy.
