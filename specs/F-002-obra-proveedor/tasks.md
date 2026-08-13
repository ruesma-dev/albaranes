<!-- specs/F-002-obra-proveedor/tasks.md -->
# F-002 · Tanda 1 — Identificación de obra y proveedor · Tareas

Rama: `feature/F-002-obra-proveedor`. Un commit por tarea
(`F-002 Tn: ...`). Los tests van junto a su implementación y NO tocan red
ni BBDD (fakes/mocks). Antes de T3 y T8: comprobar que el venv del servicio
tiene `pytest` (al crear `tests/` la sección 7 bis de init.sh empieza a
ejecutarlo).

- [ ] T1: sv3 — ampliar puertos (`obra_merge_repository_port.py`,
      `header_resolver_ports.py`) y `config/settings.py` (flags
      `RED_OBRA_ENABLED`, `RED_PROVEEDOR_CIF_ENABLED`,
      `FECHA_GUARD_ENABLED`, `FECHA_GUARD_MAX_DIAS`).
      | Verificación: `python -m compileall` del servicio sin errores
      (lo cubre init.sh, sección 6).

- [ ] T2: sv3 — métodos nuevos en `sqlalchemy_albaran_repository.py`
      (`marcar_revision_cabecera`, `descartar_obra_no_valida`,
      `retirar_revision_obra`, `get_merge_fechas_para_guard`), idempotentes
      (motivo no duplicado; nota con dedupe por prefijo).
      | Verificación: compileall + revisión contra design.md. La escritura
      real contra PG es MANUAL (humano) en T12.

- [ ] T3: sv3 — red de obra en `obra_enrichment_service.py` + `tests/`
      (`conftest.py`, `test_f002_red_obra.py`): R5 (0937 inexistente →
      descartar+revisión), R6 (código no normalizable), R7 (retirada al
      validar; idempotencia en reproceso), R16 (excepción del cliente no
      rompe), R17 (flag a false = comportamiento previo).
      | Verificación: `pytest services/albaranes-persistencia/tests -q`
      en verde (tests `test_f002_r5_*`, `_r6_*`, `_r7_*`, `_r16_*`, `_r17_*`).

- [ ] T4: sv3 — red de proveedor en `header_resolver_service.py`
      (+ `fetch_proveedor_by_cif` en el puerto) +
      `test_f002_red_proveedor.py`: R8 (CIF válido → nombre canónico prv.raz),
      R9 (HORPRESOL: CIF no casa + nombre casa con candidato de la obra →
      nota-propuesta + revisión, sin sobrescribir), R10 (sin candidato →
      revisión sin propuesta), R11 (sin CIF → regresión del flujo actual).
      | Verificación: pytest sv3 en verde (tests `test_f002_r8_*`.. `_r11_*`).

- [ ] T5: sv3 — `fecha_guard_service.py` + paso en
      `persist_albaran_pipeline.py` (3 rutas) + wiring en `composition.py`
      + `test_f002_fecha_guard.py`: R13 (2023 vs 2026 → revisión), R14
      (sin fecha de email → referencia now UTC), R15 (fecha nula/rota →
      no-op), R16/R17.
      | Verificación: pytest sv3 en verde (tests `test_f002_r13_*`.. `_r15_*`).

- [ ] T6: sv3 — contexto de email desde `workflow_runs`: puerto
      `FuenteContextoEmail` en `worker/ports.py`, adaptador
      `workflow_context_adapter.py`, handler de `persistence_worker.py` y
      wiring en `main_worker.py` + `test_f002_contexto_email_worker.py`:
      R12 (payload → context con email.receivedDateTime), fila ausente /
      payload roto → contexto como hoy (best-effort).
      | Verificación: pytest sv3 en verde (tests `test_f002_r12_*`).

- [ ] T7: sv2 — `config/settings.py` (bloque SIGRID_* + OBRAS_ACTIVAS_*),
      puerto `obras_activas_provider.py`, cliente
      `sigrid_api_obras_client.py` y caché `obras_activas_cache.py` +
      `tests/` (`conftest.py`, `test_f002_obras_cache.py`): R3 (dentro del
      TTL, 1 sola llamada), expiración → refresco, error → None y stale si
      lo hay.
      | Verificación: `pytest services/albaranes-api/tests -q` en verde
      (tests `test_f002_r3_*`).

- [ ] T8: sv2 — prompt `albaran_factura_es` en `config/prompts.yaml`
      (placeholder `{obras_activas}` + regla de elección SOLO de la lista +
      reescritura de `proveedor_nombre` según R4) y render en
      `albaran_extraction_service.extract_phase_1` + wiring
      (`composition.py`, `api/app.py`) + `test_f002_prompt_obras.py`: R1
      (bloque determinista: orden por código, cap, presente en las
      instructions), R2 (provider None/error → nota de no disponible y la
      extracción no lanza), R4 (las instructions renderizadas exigen razón
      social del bloque fiscal y vetan el logotipo), compatibilidad
      (YAML sin placeholder → append al final del task).
      | Verificación: pytest sv2 en verde (tests `test_f002_r1_*`, `_r2_*`,
      `_r4_*`).

- [ ] T9: docs — actualizar `azure-apps/albaranes.md` (sv2 pasa a consumir
      sigrid-api: endpoint, variables y secret nuevos de
      `ca-sv2-extraccion`) y dejar en `progress/` la lista exacta de env
      vars/secret a aplicar en Azure (lo aplica el humano).
      | Verificación: revisión del diff de `azure-apps/` (repo hermano) y
      nota en `progress/impl_F-002.md`.

- [ ] T10: `.env.example` de sv2 con las variables nuevas (sin valores
      reales) y comentario en `.env.example` de sv3 si aplica flags nuevos.
      | Verificación: revisión; ningún secreto en el diff.

- [ ] T11: Ejecutar `bash harness/init.sh` en verde (incluye pytest de
      todos los servicios declarados y cobertura del diff).
      | Verificación: `bash harness/init.sh` → ENTORNO LISTO.

- [ ] T12: MANUAL (humano) — verificación integrada en local
      (Azurite + PG local + sigrid-api real, solo lectura):
      1) reprocesar un albarán con obra inventada (caso 0937) →
         merge sin obra + `review_required` + nota `[AVISO] Obra`;
      2) albarán HORPRESOL → nota-propuesta de proveedor;
      3) albarán con fecha antigua (caso 2023) → motivo
         `fecha_albaran_fuera_de_rango`;
      4) confirmar que `email_received_datetime` se rellena en el merge;
      5) anotar el nº real de obras devueltas por la query (pregunta P2).
      | Verificación: MANUAL (humano), resultados pegados en
      `progress/impl_F-002.md`.
