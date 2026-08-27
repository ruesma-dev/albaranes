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
- [x] T4: Declarar `clasificacion` en `DocumentoAlbaran` de sv2 y de sv3, con default `None` (R8)  |  Verificación: **dos comandos, uno por servicio** — `pytest services/albaranes-api/tests -k f043_schema` y `pytest services/albaranes-persistencia/tests -k f043_schema`. Van separados porque sv2 y sv3 tienen ambos un paquete `infrastructure/sigrid` de primer nivel: en un solo proceso de pytest uno tapa al otro y la pasada muere al RECOGER, antes de ejecutar nada (defecto previo del monorepo, ajeno a F-043).
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
- [x] T26: Actualizar `docs/ARCHITECTURE.md` (regla nueva) y el §9 de `docs/referencia/dominio_negocio_albaranes.md` (puntero al catálogo)  |  Verificación: revisión del reviewer contra el diseño
- [x] T27: Cobertura de líneas cambiadas ≥ 80 % (R32)  |  Verificación: `python -m harness.cobertura --base dev --config harness/rigor.json` (lo mismo que lanza `init.sh`). **Ojo**: `harness.cobertura` NO tiene opción `--feature` —la feature la deduce de la rama—, y `--feature F-043` no da error: argparse lo abrevia a `--features F-043`, busca el catálogo de features en un fichero llamado `F-043`, no lo encuentra y la puerta se declara **N/A con exit code 0**. Un falso verde.
- [ ] T28: Campaña de mutación COMPLETA (sin tope de mutantes) con 0 supervivientes; cada superviviente exige test nuevo o justificación escrita (R32)  |  Verificación: `python -m harness.mutacion --feature F-043`
- [x] T29: Topes de tamaño del papeleo de la feature (R32)  |  Verificación: `python -m harness.tamano --feature F-043`
- [ ] T30: Pasada de evals con LLM real (ruta sensible tocada: prompts de sv2 y sv5, schemas y catálogo). SE FACTURA: requiere el visto bueno del humano (duda 6)  |  Verificación: MANUAL (humano) — `python -m evals.runner --con-llm --feature F-043`, informe `progress/evals_F-043.md` con `MODO: completa`, `FASES: IA1,IA2,IA3,IA4,E2E` y `VEREDICTO: VERDE`
- [ ] T31: Comprobar de extremo a extremo el caso real: **RE-EXTRAER** SS-0003967 en local (revalorar NO basta) y ver que IA1 lo clasifica `residuos` y que las puertas de residuos de sv6 se abren  |  Verificación: MANUAL (humano) — los cinco pasos de abajo

  > **Por qué no vale la T31 anterior.** Decía «revalorar con `curl … :8003/…/value` y ver 210,00 € en 2 líneas», y eso no puede dar verde por dos motivos: (a) esa vía publica `q-valoracion` y **no re-extrae**, así que el merge sigue con las seis columnas `tipologia*` a NULL y `tipologia` nunca será `residuos` (decisión 5 del humano: sin backfill); (b) aun re-extraído, con el match REAL de IA3 el albarán sale en **90,00 €**, no en 210,00 € — la guarda de F-036 R15 anula el casado de la base porque la línea 26481 tarifa el recargo, no la retirada. Los cuatro escenarios están medidos en `progress/impl_F-043_bloque_D.md` §3.
  >
  > **Paso 0 · pipeline local arriba** (`infra/docs/levantar-pipeline-local.md`): Azurite + Postgres, y sv5, sv6 (worker), sv3 (worker), sv2 (worker) y sv4 en el orden de esa tabla. `VALUATION_TRIGGER_ENABLED=false` en sv3, como dice el doc.
  >
  > **Paso 1 · el `document_id` del caso.** `psql "$env:ALBARANES_DB_URL" -c "SELECT id, numero_albaran, tipologia FROM albaran_documents_merge WHERE numero_albaran='SS-0003967';"` — anótalo. Si en la BBDD local no está, vale cualquier `document_id` nuevo: siembra el PDF con `cd services\albaranes-api; .\.venv\Scripts\python.exe seed_input.py <DOCUMENT_ID> "<ruta_del_pdf>"`.
  >
  > **Paso 2 · re-extraer (esto es lo que la T31 vieja no hacía).** `cd services\albaranes-api; .\.venv\Scripts\python.exe encolar_extraccion.py <DOCUMENT_ID>` — publica en `q-extraccion`, el worker de sv2 vuelve a leer el PDF de `input/{document_id}.pdf`, IA1 clasifica y el envelope baja por `q-persistencia` a sv3.
  >
  > **Paso 3 · valorar.** Si sv3 auto-seleccionó contrato, ya publicó `q-valoracion` y sv6 valoró solo. Si no: `curl.exe -X POST http://localhost:8003/v1/valuation/run -H "Content-Type: application/json" -d "{\"document_id\": \"<DOCUMENT_ID>\", \"force\": true}"`.
  >
  > **Paso 4 · leer el resultado.** `psql "$env:ALBARANES_DB_URL" -c "SELECT tipologia, tipologia_confianza_pct, tipologia_origen, tipologia_mixta, tipologia_motivo FROM albaran_documents_merge WHERE id='<DOCUMENT_ID>';"` y `psql "$env:ALBARANES_DB_URL" -c "SELECT total_valorado, total_lines, review_required, review_reasons_json FROM albaran_valuations WHERE document_id='<DOCUMENT_ID>';"` (`albaran_valuations.document_id` es UNIQUE: una fila por documento).
  >
  > **ES VERDE si**: `tipologia='residuos'`, `tipologia_origen` es `ia1` o `ia2`, `tipologia_confianza_pct > 0` y `tipologia_motivo` cita algo del papel (esto es lo que F-043 entrega); **y** la valoración trae `total_lines = 2` —la base del contenedor más la sintética `INCREMENTO LER 170604`— con `review_required = true` y `total_valorado = 90.00`. Ese 90,00 € es el número correcto con el match real de IA3, y es un avance real: el albarán pasa de valorarse **de más en silencio** (540,00 € en 1 línea) a valorarse de menos **y pedir revisión**. Si IA3 casa la base con la línea de CONTENEDOR en vez de con la del incremento, salen **210,00 €** en esas mismas 2 líneas (120 + 90) y también es verde.
  >
  > **NO es verde si**: `tipologia` sigue a NULL (no se re-extrajo: repite el paso 2), o la valoración trae `total_lines = 1` con 540,00 € o 720,00 € (las puertas de residuos no se abrieron: la clasificación no llegó a sv6). Que el total sea 90,00 € en vez de 210,00 € **no** es un fallo de F-043: es el prompt de IA3 y se juega en **T30**.
  >
  > **Con esta tarea en verde se cierra la T24 pendiente de F-036**, con el matiz de arriba: F-043 entrega la maquinaria de residuos alcanzable sin `tipo_familia`; el importe exacto depende de T30.
- [ ] T32: Verificar en sv4 que el revisor ve familia, confianza y motivo, y que un albarán con confianza por debajo del umbral aparece marcado a revisión  |  Verificación: MANUAL (humano) — abrir la ficha del documento en `http://localhost:8004`
- [x] T33: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
