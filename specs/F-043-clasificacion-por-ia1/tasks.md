<!-- specs/F-043-clasificacion-por-ia1/tasks.md -->
# F-043 · Tareas

Rama `feature/F-043-clasificacion-por-ia1`. Rigor `critico`: **fase RED
obligatoria** en toda tarea con test (falla antes, pasa después; la traza va
al informe). Un commit por tarea, `F-043 Tn: ...`. Sin `git push`.

**Las seis dudas están RESUELTAS** (decisiones del humano del 2026-08-26, al
final de `requirements.md`). La única que sigue abierta a propósito es el
alcance de las evals, que se decide al llegar a **T30** y no antes.

- [x] T1: Crear `ruesma_comun/contratos/familias.py` con el catálogo (R1–R5), `familias_documento/linea`, `obtener`, `render_catalogo_markdown` y los dos `prompt_*_de`  |  Verificación: `pytest services/albaranes-comun/tests/test_f043_familias.py -k "catalogo or render or prompt"`
- [x] T2: Añadir `familia_efectiva` al catálogo con las cuatro ramas de §1.1 del diseño (R18–R21, R27)  |  Verificación: `pytest services/albaranes-comun/tests/test_f043_familias.py -k efectiva`
- [x] T3: Crear `ruesma_comun/contratos/clasificacion.py` con `ClasificacionAlbaran` (R7) y exportarlo en `ruesma_comun/contratos/__init__.py`  |  Verificación: `pytest services/albaranes-comun/tests/test_f043_familias.py -k contrato`
- [x] T4: Declarar `clasificacion` en `DocumentoAlbaran` de sv2 y de sv3, con default `None` (R8)  |  Verificación: `pytest services/albaranes-api/tests services/albaranes-persistencia/tests -k f043_schema`
- [x] T5: Inyectar `{catalogo_familias}` en el render del `task` de fase 1 (`albaran_extraction_service`) junto a `{obras_activas}` (R6)  |  Verificación: `pytest services/albaranes-api/tests/test_f043_prompt_fase1.py`
- [x] T6: Escribir en `config/prompts.yaml` de sv2 el bloque «Clasificación del albarán» de `albaran_factura_es`: marcador, campos obligatorios y `generico` como respuesta legítima (R6, R7, R4)  |  Verificación: `pytest services/albaranes-api/tests/test_f043_prompt_fase1.py -k bloque`
- [x] T7: Añadir a los cuatro `albaran_revision_fase2_*` la confirmación o corrección de `clasificacion` en `documento_revisado` (R16)  |  Verificación: `pytest services/albaranes-api/tests/test_f043_prompt_fase1.py -k fase2`
- [x] T8: Crear `clasificacion_resolver.py` con `resolver_clasificacion` (R10, R11, R12, R16), sin importar `ler` ni funciones de texto  |  Verificación: `pytest services/albaranes-api/tests/test_f043_clasificacion_resolver.py`
- [x] T9: Test de no-regresión de la prohibición: documento con LER en todas las líneas y `familia='generico'` ⇒ `generico` (R13)  |  Verificación: `pytest services/albaranes-api/tests/test_f043_clasificacion_resolver.py -k prohibicion`
- [x] T10: Borrar `tipologia_resolver.py`, el enum `Tipologia`, `texto_contiene_hormigon`, `texto_contiene_mortero` y el override por CIF; sus tests viejos se retiran citando el requisito que los sustituye (R12, R14)  |  Verificación: `pytest services/albaranes-api/tests` + `grep -rn "tipologia_resolver\|override_por_cif" services/albaranes-api --include=*.py` sin resultados
- [x] T11: `phase_merge.construir_envelope_final` recibe la clasificación y la escribe **en `data`**, dejando `meta.tipologia` como espejo (R9)  |  Verificación: `pytest services/albaranes-api/tests -k phase_merge`
- [x] T12: `extraction_worker` resuelve con fase 1, enruta con `prompt_fase2_de` (caída al genérico si la clave no existe) y re-resuelve con fase 2 (R15, R16)  |  Verificación: `pytest services/albaranes-api/tests -k worker`
- [x] T13: Test de que la clasificación SOBREVIVE el saneado de `meta` de sv3 (R9), reproduciendo `_sanear_envelope`  |  Verificación: `pytest services/albaranes-persistencia/tests/test_f043_persistencia_clasificacion.py -k sanear`
- [x] T14: DDL idempotente de las seis columnas + índice en `phase2_ddl.py`, espejado en `schema_contribution.py` y en el ORM (R22)  |  Verificación: `pytest services/albaranes-persistencia/tests -k ddl`
- [x] T15: Persistir los seis campos en `albaran_documents_merge` al escribir el merge (R22)  |  Verificación: `pytest services/albaranes-persistencia/tests/test_f043_persistencia_clasificacion.py -k persiste`
- [x] T16: Umbral `clasificacion_confianza_minima_pct` en `config/settings.py` de sv3 y motivos `clasificacion_confianza_baja`, `clasificacion_mixta` y `clasificacion_ausente` (R11, R28, R29)  |  Verificación: `pytest services/albaranes-persistencia/tests/test_f043_persistencia_clasificacion.py -k motivos`
- [x] T17: Motivo `linea_sin_familia_en_albaran_mixto` en las líneas que no heredan (R19)  |  Verificación: `pytest services/albaranes-persistencia/tests/test_f043_persistencia_clasificacion.py -k mixto`
- [x] T18: sv5 — ampliar el SELECT del contexto con las seis columnas y montar `ContextoValoracion.clasificacion` (R23)  |  Verificación: `pytest services/albaran-valoracion-api/tests/test_f043_contexto_clasificacion.py -k select`
- [x] T19: sv5 — retirar `_derivar_tipologia_valoracion` y elegir el prompt con `prompt_valoracion_de(familia)`, con caída al genérico (R24, R27)  |  Verificación: `pytest services/albaran-valoracion-api/tests/test_f043_contexto_clasificacion.py -k prompt`
- [x] T20: sv5 — serializar `clasificacion` dentro del `context` del envelope hacia sv6 (R23)  |  Verificación: `pytest services/albaran-valoracion-api/tests -k envelope`
- [x] T21: sv6 — `ValuationContextDto.clasificacion` con default, y test de que un envelope sin ella sigue validando (R27)  |  Verificación: `pytest services/albaran-valoracion-persist/tests -k f043_envelope`
- [x] T22: sv6 — sustituir las seis puertas de familia y el padre de la sintética por `familia_efectiva` (R20, R25)  |  Verificación: `pytest services/albaran-valoracion-persist/tests/test_f043_familia_efectiva.py`
- [x] T23: sv6 — test de aceptación R26: SS-0003967 con clasificación de documento `residuos` y líneas sin `tipo_familia` ⇒ 210,00 € en 2 líneas (contenedor 120 + incremento LER 90), reutilizando `tests/f036_escenarios_residuos.py`  |  Verificación: `pytest services/albaran-valoracion-persist/tests/test_f043_r26_ss0003967.py`
- [x] T24: sv4 — exponer `clasificacion` en el modelo de vista y pintarla en `document_detail.html` junto a los motivos de revisión (R30)  |  Verificación: `pytest services/albaranes-front/tests/test_f043_vista_clasificacion.py`
- [x] T25: Añadir `ruesma_comun/contratos/familias.py` y `clasificacion.py` a `harness/rutas_sensibles.json` (sus textos entran en el prompt)  |  Verificación: `python -m harness.rutas_sensibles --puerta --base dev` lista la ruta
- [ ] T26: Actualizar `docs/ARCHITECTURE.md` (regla nueva) y el §9 de `docs/referencia/dominio_negocio_albaranes.md` (puntero al catálogo)  |  Verificación: revisión del reviewer contra el diseño
- [ ] T27: Cobertura de líneas cambiadas ≥ 80 % (R32)  |  Verificación: `python -m harness.cobertura --feature F-043`
- [ ] T28: Campaña de mutación COMPLETA (sin tope de mutantes) con 0 supervivientes; cada superviviente exige test nuevo o justificación escrita (R32)  |  Verificación: `python -m harness.mutacion --feature F-043`
- [ ] T29: Topes de tamaño del papeleo de la feature (R32)  |  Verificación: `python -m harness.tamano --feature F-043`
- [ ] T30: Pasada de evals con LLM real (ruta sensible tocada: prompts de sv2 y sv5, schemas y catálogo). SE FACTURA: requiere el visto bueno del humano (duda 6)  |  Verificación: MANUAL (humano) — `python -m evals.runner --con-llm --feature F-043`, informe `progress/evals_F-043.md` con `MODO: completa`, `FASES: IA1,IA2,IA3,IA4,E2E` y `VEREDICTO: VERDE`
- [ ] T31: Comprobar de extremo a extremo el caso real: revalorar SS-0003967 en local y ver `albaran_documents_merge.tipologia='residuos'` y total 210,00 € en 2 líneas; con ello se cierra la T24 pendiente de F-036  |  Verificación: MANUAL (humano) — `curl -X POST http://localhost:8003/v1/albaranes/{document_id}/value` y `SELECT tipologia, tipologia_confianza_pct, tipologia_motivo, tipologia_origen FROM albaran_documents_merge WHERE numero_albaran='SS-0003967';`
- [ ] T32: Verificar en sv4 que el revisor ve familia, confianza y motivo, y que un albarán con confianza por debajo del umbral aparece marcado a revisión  |  Verificación: MANUAL (humano) — abrir la ficha del documento en `http://localhost:8004`
- [ ] T33: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
