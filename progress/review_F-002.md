<!-- progress/review_F-002.md -->
# F-002 · Tanda 1 — Identificación de obra y proveedor · Review

- **Veredicto: APPROVED**
- Rama revisada: `feature/F-002-obra-proveedor` (árbol principal), HEAD
  `886f901`. 14 commits sobre `dev`.
- Fecha: 2026-08-14.
- **Nivel de rigor: `estandar`** (declarado en `harness/features.json`).
  Exige: C1–C3, C3 bis, C5, tests trazables (C4), **fase RED** en los
  requisitos centrales, **cobertura** de las líneas cambiadas ≥ 80 % y
  **campaña de mutación** con todos los supervivientes analizados. NO exige
  cero supervivientes (eso es `critico`), pero sí que ninguno quede en
  `PENDIENTE`.

Primera feature que toca servicios de producción (sv2 y sv3). La he revisado
con esa vara: además de los checkpoints, he verificado a mano las tres
trampas de dominio de C3, el contrato real productor→consumidor del gap R12
(sv1 escribe / sv3 lee), que Sigrid se toca SOLO en lectura vía `sigrid-api`,
y que la regla dura **SIN DESPLIEGUE** se ha respetado. Todo pasa.

---

## 1. Evidencia de primera mano (ejecutada por el reviewer, no leída del informe)

| Comando | Resultado real |
|---|---|
| `bash harness/init.sh` | `ENTORNO LISTO`, **exit 0** (comprobado aparte: `EXIT=0`). 242 tests raíz en verde en 34,3 s. |
| `PUERTA COBERTURA` (dentro de init.sh) | `[OK] 82.1% de 469 líneas cambiadas cubiertas (385/469, umbral 80%, nivel estandar)` |
| `PUERTA RUTAS SENSIBLES [evals]` | `AVISO`: falta evidencia de 1 ruta tocada (`services/albaranes-api/config/prompts.yaml`). Esperado; ver §5. |
| `python -m pytest tests -q` en `services/albaranes-api` | **56 passed** en 0,64 s |
| `python -m pytest tests -q` en `services/albaranes-persistencia` | **88 passed** en 1,14 s |
| `python -m evals.runner` | `NO_EVALUABLE`, **exit 2** (el esperado con los libros vacíos) |
| `python -m harness.rutas_sensibles --validar` | `1 verificación(es), 14 ruta(s) sensible(s) declaradas: evals (aviso)`, exit 0 |
| `git status --porcelain` | limpio (el único `??` era `progress/evals_manual.md`, generado por MI corrida del runner sin `--feature`; lo he borrado). |

Los avisos de servicios «sin directorio de tests» (sv1, sv4, sv5, sv6, infra)
son deuda previa del repositorio, ajena a esta feature.

## 2. Verificación INDEPENDIENTE de la campaña de mutación

No me he creído los totales del informe: los he recalculado con cálculo puro
(`harness.alcance` + `harness.mutacion.generar_mutantes`, sin ejecutar la
suite ni escribir en disco).

| Métrica | `progress/mutacion_F-002.md` | Recálculo del reviewer | ¿Coincide? |
|---|---|---|---|
| Ficheros en alcance | 22 | 22 | ✔ |
| Líneas en alcance | 1484 | 1484 | ✔ |
| Base del diff | `89bc79d…` .. `feature/F-002-obra-proveedor` | idéntica | ✔ |
| Mutantes generados | 108 | **108** | ✔ |

El reparto por fichero también cuadra (29 en `sigrid_api_obras_client.py`, 21
en `header_resolver_service.py`, 18 en `sqlalchemy_albaran_repository.py`,
9+9+4+4+4+4+3+2+1 en el resto).

**Muestreo de supervivientes** (protocolo: 2–3; he hecho 5). Cada uno existe
como mutante REAL, con el mismo fichero:línea, el mismo operador y el mismo
texto original→mutado que declara el informe:

| # | Declarado | Comprobado en el generador |
|---|---|---|
| 3 | `header_resolver_service.py:102` `[logico]` `if not a or not b:` → `if not a and not b:` | ✔ existe, operador y textos idénticos |
| 8 | `sqlalchemy_albaran_repository.py:1672` `[entero]` `fila[0]` → `fila[1]` | ✔ |
| 10 | `sqlalchemy_albaran_repository.py:1722` `[booleano]` `review_required = True` → `False` | ✔ |
| 12 | `sqlalchemy_albaran_repository.py:1771` `[logico]` `codigo_leido or '—'` → `codigo_leido and '—'` | ✔ |
| 1 | `sigrid_api_obras_client.py:180` `[logico]` `response.text or ''` → `response.text and ''` | ✔ |

La campaña NO declara cero mutantes, así que la prueba de control por
exclusión de alcance no aplica.

**Juicio de los 13 análisis** (los he leído uno a uno, ninguno en
`PENDIENTE`):

- Los **7 equivalentes** (1, 2, 3, 4, 5, 6, 7) están bien clasificados. Los
  he verificado por lectura: el recorte `[:300]` y su `or`/`and` solo componen
  el texto de un `RuntimeError` que `obtener()` captura y convierte en `None`
  (probado); la guarda `if not a or not b` es redundante porque `_match_score`
  ya devuelve `0.0` con cadena vacía; y `ensure_ascii`/`indent` no cambian lo
  que `json.loads` devuelve a sv4. Fijarlos en tests sería congelar formato,
  no reglas.
- Los **6 huecos reales** (8–13) están en las transacciones PostgreSQL de
  `sqlalchemy_albaran_repository.py` y el análisis es honesto: los declara
  huecos, no los disfraza de equivalentes. La imposibilidad de alcanzarlos
  con un unit test es real y verificable en el código (`SessionFactory`
  construye/crea la BBDD en su `__init__` y `review_notes` se añade por
  `ALTER TABLE` fuera del ORM: `sqlalchemy_albaran_repository.py:262`), y ya
  estaba declarada como riesgo en `design.md` con control compensatorio.
  Señalar `review_required = True` (supervivientes 10 y 11) como «lo primero
  que hay que mirar en la prueba local» es la lectura correcta: es la línea
  de la que depende que algo llegue al revisor.

Con nivel `estandar`, 13 supervivientes analizados NO bloquean. Sí dejan una
consecuencia que el líder debe respetar: **T12 (MANUAL) no es opcional antes
de marcar `done`** — es el único control que cubre esos 6 huecos.

## 3. Trampas de dominio de C3 (verificadas en el código, no en el informe)

1. **La lógica se construye sobre las tablas MERGE, nunca sobre las raw.**
   ✔ Las cinco escrituras nuevas (`marcar_revision_cabecera`,
   `descartar_obra_no_valida`, `retirar_revision_obra`,
   `set_merge_proveedor_nombre_canonico`, más `_escribir_notas`) van todas
   contra `AlbaranDocumentMergeOrm` / `UPDATE albaran_documents_merge`. El
   barrido del diff (`INSERT INTO|UPDATE |DELETE FROM`) devuelve **una sola**
   sentencia y es sobre el merge. Ninguna tabla raw se escribe.
2. **Sin renames de columnas** (sv5 lee el merge con SQL crudo). ✔ El diff no
   trae ni un `ALTER TABLE`, ni un `RENAME`, ni un `CREATE TABLE`: la feature
   usa columnas que ya existían. Comprobado además que sv5
   (`services/albaran-valoracion-api`) **no lee** `review_required`,
   `review_reasons_json` ni `review_notes` (grep: cero ocurrencias), así que
   ni siquiera hay acoplamiento nuevo por esas columnas.
3. **La canonicalización de proveedor conserva el literal leído en las raw.**
   ✔ `set_merge_proveedor_nombre_canonico` delega en
   `update_merge_proveedor_nombre` (línea 1612), que hace `session.get(
   AlbaranDocumentMergeOrm, document_id)` y toca **solo** `proveedor_nombre`
   del merge. El literal leído sigue en las tablas raw y en
   `raw_extraction_json`. La red de proveedor con CIF que no casa (R9/R10)
   **no sobrescribe nada**: propone y marca (comprobado en
   `_red_proveedor_por_cif`, y hay test
   `test_f002_r9_no_sobrescribe_el_cif_ni_el_nombre_leidos`).
4. Importes/cantidades y unidades (tercera trampa del checkpoint): la feature
   no toca líneas, ni agregados, ni el conversor de sv6. N/A por alcance.

**Extra, porque toca producción:** he verificado el contrato real del gap R12
de punta a punta, no solo contra los fakes de los tests —que podrían codificar
la misma suposición equivocada—:

- Productor: sv1 escribe `payload_json = json.dumps(meta)`
  (`intake_cola_adapter.py:75`) con las claves `email_message_id`,
  `email_received_at_utc`, `from_address`, `subject`, `attachment_filename`,
  `attachment_content_type`, `attachment_sha256`, `page_number`,
  `total_pages` (`polling_pipeline.py:300-311`).
- Traductor: `_MAPEO_EMAIL` / `_MAPEO_DOCUMENTO` del adaptador nuevo mapean
  exactamente esas nueve claves.
- Consumidor: `_build_document` de sv3 lee `email_ctx["id"|"subject"|
  "sender"|"receivedDateTime"]` y `document_ctx["source_attachment_*"|
  "page_count"]` (líneas 1918–1968). **Cuadra.**
- Wiring: `RepositorioWorkflows` duck-tipa sobre `create_session()`
  (`repositorio.py:53-63`) y el `SessionFactory` de sv3 lo expone con la
  firma que `main_worker.py` le pasa por nombre. El worker arrancará.

## 4. Prohibiciones

- **Sigrid, solo lectura vía `sigrid-api`.** ✔ El cliente nuevo de sv2 hace
  `POST {base_url}/api/sql/read` con un `SELECT` y `x-functions-key`
  (`sigrid_api_obras_client.py:157-185`). No hay conexión SQL directa, ni
  endpoint de escritura, ni `INSERT/UPDATE/DELETE` contra Sigrid en todo el
  diff. sv3 sigue usando sus clientes de lectura ya existentes.
- **`ruesma_comun` intacto.** ✔ `git diff --stat` no toca
  `services/albaranes-comun/**`: el adaptador usa su API pública
  (`obtener_por_correlation_key`) tal cual, como mandaba el design.
- **SIN DESPLIEGUE (regla dura del humano).** ✔ Verificado:
  - Ni un fichero de `infra/` en el diff; ningún `.github/`, ningún script de
    despliegue tocado.
  - Ningún rastro de `az`, `deploy.ps1` o `build_images.ps1` ejecutado: la
    única mención en todo el material es la frase del informe que declara que
    NO se han ejecutado.
  - **T9 marcada `[~] PENDIENTE-DE-DESPLIEGUE` con justificación escrita** en
    `tasks.md:79-89`: la lista exacta de env vars y del secret queda escrita
    en el informe (hecho), y `azure-apps/albaranes.md` NO se actualiza porque
    ese documento describe **lo que hay desplegado**. El razonamiento es
    correcto y lo suscribo: escribir allí que sv2 consume `sigrid-api` antes
    de que exista el secret dejaría el documento mintiendo, que es peor que
    no tenerlo. No es una tarea a medias: es una tarea con su condición de
    ejecución escrita y su dueño (el humano, en el mismo trabajo del
    despliegue).
  - T10 sí está hecha (variables nuevas en los `.env.example`), sin un solo
    valor real. Ver el hallazgo lateral del §7.

**Barrido de datos sensibles sobre el diff** (patrones: correos, IPv4, GUID
de suscripción/tenant, `BEGIN ... PRIVATE KEY`, `AccountKey=`, `sv=20…`,
`Bearer …`, y pares `clave = "literal"` para `function_key|api_key|password|
secret|token`): **limpio**. Los únicos aciertos son
`proveedor@ejemplo.es` (fixture inventada), `127.0.0.1:11433` (túnel local
documentado) y `sigrid_api_function_key="clave-de-prueba"` (valor de test).
El CIF `A81873903` que aparece en `prompts.yaml` es el de Construcciones
Ruesma y ya estaba en el fichero antes de esta feature.

## 5. Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con **exit 0** (ejecutado por mí).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` (init.sh los verifica uno a uno, todos `[OK]`).

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-002']`.
- [x] Rama actual `feature/F-002-obra-proveedor`, la de la feature en curso.
- [x] `progress/current.md` describe solo la sesión de F-002 (más una
      sección explícita de «Pendientes del humano (heredados)», que es
      seguimiento vivo, no resto de sesión anterior).
- [x] Ninguna feature pasa a `done` en esta rama, así que no hay nada que
      añadir a `history.md`.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** Comprobado import a import sobre los ficheros
      del diff: ningún fichero de `domain/` o `application/` de sv3 importa
      `infrastructure`, `sqlalchemy`, `httpx` ni `psycopg`. Los adaptadores
      nuevos viven donde deben: `infrastructure/sigrid/` (cliente HTTP y
      caché de sv2) e `interface_adapters/worker/` (adaptador de contexto de
      sv3). El puerto `ObrasActivasProvider` está en `domain/ports/`.
      El único import de `infrastructure` en un fichero de `application/`
      (`albaran_extraction_service.py:35`, `RevisionRulesRepository`) es
      **previo** a esta feature: el diff solo añade el import del puerto de
      dominio.
- [x] Primera línea con la ruta relativa en los **14** ficheros nuevos
      (verificado con `head -1` sobre cada uno).
- [x] Sin `print()` de debug (cero coincidencias en el diff), sin TODO/FIXME,
      sin secretos hardcodeados (§4), sin dependencias nuevas: `httpx` ya
      estaba en sv2 y no se ha tocado ningún `requirements.txt`.
- [x] Reglas de dominio y las tres trampas del monorepo: verificadas una a
      una en §3.

### C3 bis — Documentos que entran de fuera

**N/A justificado:** el diff no añade ni modifica ningún fichero de
`docs/referencia/` (verificado en `git diff --stat`: no aparece la carpeta).
No hay PDF ni ofimática en el árbol ni en el historial de la rama. Aun así he
ejecutado el barrido de datos sensibles sobre el diff completo y su resultado
consta en §4, con los patrones usados.

### C4 — La verificación es real

- [x] Cada requisito EARS tiene ≥ 1 test trazable y todos pasan. Tabla
      completa en §6. **R1–R17 y R1-bis: 17 + 1 requisitos, 0 huérfanos.**
- [x] Los unit tests no tocan red ni BBDD: sv2 sustituye `httpx.Client` por
      un doble y sv3 usa fakes de repositorio y de cliente Sigrid. Las suites
      corren en 0,64 s y 1,14 s, lo que por sí solo descarta E/S real.
- [x] Verificaciones `MANUAL (humano)` listadas con su comando exacto: las
      cinco de T12 están en `tasks.md:102-116` y, con el SQL literal y los
      valores esperados, en `progress/impl_F-002.md` §«Verificaciones MANUAL
      del humano (T12)». `progress/current.md` las declara pendientes y
      apunta al informe. **Matiz escrito** (no bloqueante): C4 pide que estén
      «listadas en `progress/current.md`» y allí están *referenciadas*, no
      copiadas. La intención del checkpoint —que el humano no las pierda— se
      cumple en un salto, y la regla ANTI TELÉFONO-DESCOMPUESTO del repo
      empuja el detalle a `progress/`. Recomendación del §7.4.

### C4 bis — El rigor declarado se cumple (nivel `estandar`)

- [x] La feature declara `rigor: "estandar"` en `harness/features.json`, valor
      válido según `harness/rigor.json`.
- [x] **Fase RED**: `progress/impl_F-002.md` §«Fase RED» trae **salidas
      reales** de los fallos previos al código, para los requisitos
      centrales y no para los de relleno: T3 (`9 failed, 18 passed`, con el
      `AssertionError: assert [] == [('0937', 'obra_inexistente:0937')]` y el
      `TypeError: ObraEnrichmentService.__init__() got an unexpected keyword
      argument 'enabled_red'`), T4 (`5 failed, 9 passed`, con
      `assert None == 'HORPRESOL, S.L.'`), T5 y T6
      (`ModuleNotFoundError` de los módulos aún inexistentes) y T7/T8
      (`ModuleNotFoundError` + los cuatro fallos del prompt sin tocar). Son
      trazas con forma de traza, no «se hizo TDD».
- [x] **Cobertura**: `PUERTA COBERTURA` en `[OK]` con su porcentaje, **82,1 %
      (385/469)** sobre umbral 80 %. Ejecutada por mí.
- [x] **Mutación**: existe `progress/mutacion_F-002.md` generado por la
      herramienta, con totales **verificados de forma independiente** por el
      reviewer (§2): alcance y nº de mutantes recalculados y coincidentes,
      cinco supervivientes muestreados y confirmados como mutantes reales.
- [x] Los 13 supervivientes tienen su análisis **completado**; ninguno en
      `PENDIENTE`. El nivel `estandar` no exige cero supervivientes.
- [x] El informe trae la sección **«Evidencias»** con los cuatro números:
      tests (242 raíz + 56 sv2 + 88 sv3, todos verdes), cobertura del diff
      (82,1 %), mutantes y supervivientes (108 / 13) y tiempo de las suites
      (46,6 s / 0,6 s / 1,8 s). Los he contrastado con mis propias corridas:
      cuadran (mi raíz tardó 34,3 s, mejor que la suya; el resto, idéntico).
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Verificaciones extra por rutas sensibles

**APLICA**: el diff toca `services/albaranes-api/config/prompts.yaml`
(commit `929b9fd`, T8), declarada en `harness/rutas_sensibles.json`, y la
puerta de `init.sh` la señaló.

- [x] Existe el informe declarado para esta feature:
      `progress/evals_F-002.md`.
- [ ] El informe **no** cumple las `exige_lineas` de la declaración
      (`MODO: completa`, `FASES: IA1,IA2,IA3,IA4,E2E`, `VEREDICTO: VERDE`).
      Lo he leído yo, no me he fiado del resumen: trae `MODO: determinista`,
      `FASES: IA3,IA4,E2E` y `VEREDICTO: NO_EVALUABLE`.
- [x] El informe es **FRESCO**: su commit es `b0a4b9c`, de esta rama y
      POSTERIOR al único commit que toca una ruta sensible (`929b9fd`). Su
      cabecera declara `Commit HEAD: 2033164`, también posterior a `929b9fd`.
      Verificado con `git log -- progress/evals_F-002.md` y recorriendo qué
      commit tocó qué ruta sensible.
- [x] **Motivo escrito de la evidencia que falta** (la exigencia es `aviso`,
      así que este bloque no bloquea, pero el motivo tiene que constar y
      aquí consta):
      1. La pasada completa exige LLM real y el arnés corre con
         `REQUIERE_ENV=0`, sin `.env` global: el runner responde «faltan en
         el entorno GEMINI_API_KEY, OPENAI_API_KEY. No se ha consumido ningún
         caso». Lo he reproducido: `python -m evals.runner` sale
         `NO_EVALUABLE` con **exit 2**.
      2. Aunque hubiera claves, el veredicto seguiría siendo `NO_EVALUABLE`:
         los libros de `evals/ground_truth/` están vacíos y un informe sin
         casos nunca es VERDE, por construcción del propio runner.
      3. Eso es exactamente lo previsto por la **decisión D5 de F-011**, que
         es la razón de que la exigencia arranque en `aviso` y suba a
         `bloqueo` cuando el ground truth esté relleno (`CHECKPOINTS.md`
         §C4 ter, último párrafo).
      **Consecuencia que el humano debe tener presente:** el cambio del
      prompt de IA1 —el más delicado de esta feature, porque cambia lo que la
      IA puede responder en `obra_codigo` y redefine `proveedor_nombre`— NO
      está evaluado por evals. Los tests de sv2 comprueban que el bloque se
      renderiza y que las reglas están en el YAML real
      (`test_f002_r1_el_prompt_real_tiene_el_placeholder`,
      `test_f002_r4_*`), que es todo lo que un test determinista puede
      comprobar; que la IA se comporte mejor con ese prompt lo dirá el
      ground truth, o la prueba local del humano.

### C5 — La sesión se cerró bien

- [x] `tasks.md` con las tareas ejecutables en `[x]` y un commit
      `F-002 Tn: …` por tarea: T1 `42251b6`, T2 `9703447`, T3 `f772f8a`,
      T4 `8d394db`, T5 `3d573d2`, T6 `2d7a2ee`, T7 `92df1eb`, T8 `929b9fd`,
      T10 `2033164`, T11 `b0a4b9c`. Los tres commits restantes (`a0857fe`,
      `e87558e`, `886f901`) son el cierre de la campaña de mutación y usan
      el formato mínimo `F-002: …`, correctamente etiquetados.
      **Dos excepciones, ambas justificadas por escrito** (no son checkboxes
      olvidados):
      - **T9 `[~]`**: pendiente-de-despliegue por la regla dura SIN
        DESPLIEGUE del humano, con la justificación en `tasks.md:79-89` y el
        detalle accionable en el informe. Ver §4.
      - **T12 `[ ]`**: es MANUAL del humano por definición; `CHECKPOINTS.md`
        C4 la contempla explícitamente como «pendiente de que el humano la
        ejecute». No puede estar `[x]` en el momento del review.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status`
      limpio (el único `??` lo generé yo y lo he borrado).
- [x] `features.json` refleja el estado real: `in_progress`. El diff sobre
      `dev` cambia **solo** `spec_ready` → `in_progress`, nada más. Correcto:
      no se ha marcado `done`, y no debe marcarse hasta que el humano cierre
      T12.

## 6. Trazabilidad requisito → test

| Req | Test(s) que lo cubren | ¿Pasa? |
|---|---|---|
| R1 | `test_f002_r1_el_bloque_de_obras_se_inyecta_en_el_placeholder`, `_las_obras_van_ordenadas_por_codigo_ascendente`, `_la_lista_se_capa_a_obras_activas_max`, `_el_cap_por_defecto_son_300_obras`, `_un_cap_absurdo_deja_al_menos_una_obra`, `_el_bloque_prohibe_codigos_fuera_de_la_lista`, `_el_prompt_real_tiene_el_placeholder`, `_compatibilidad_yaml_sin_placeholder_appendea_el_bloque`, `_la_obra_sin_nombre_no_rompe_el_bloque` | ✔ |
| R1-bis | `test_f002_r1bis_descarta_codigos_no_numericos`, `_descarta_codigos_que_no_son_de_4_digitos`, `_descarta_los_codigos_por_debajo_del_corte`, `_el_corte_es_estricto_mayor_que`, `_con_corte_cero_no_se_descarta_ninguna_por_valor`, `_con_corte_cero_sigue_exigiendo_4_digitos`, `_defaults_de_configuracion`, + 8 del cliente (dedupe, columnas por nombre, truncado, max_rows) | ✔ |
| R2 | `test_f002_r2_sin_lista_se_pone_la_nota_de_no_disponible`, `_sin_proveedor_cableado_la_extraccion_sigue`, `_un_proveedor_que_revienta_no_rompe_la_extraccion`, `_un_error_http_no_propaga_y_devuelve_none`, `_un_400_se_trata_como_error_aunque_traiga_cuerpo`, `_un_ok_false_no_propaga_y_devuelve_none`, `_una_respuesta_sin_ok_no_se_da_por_buena`, `_una_lista_vacia_tras_el_filtro_es_no_disponible`, `_si_el_proveedor_falla_se_sirve_la_lista_vieja`, `_sin_lista_previa_devuelve_none`, `_el_cliente_exige_sus_tres_credenciales`, `_sin_las_tres_credenciales_sigrid_no_esta_disponible`, `_el_transporte_reintenta_una_vez`, `_sin_lista_y_sin_placeholder_no_se_appendea_nada` | ✔ |
| R3 | `test_f002_r3_dentro_del_ttl_solo_se_consulta_una_vez`, `_al_expirar_el_ttl_se_refresca`, `_justo_en_el_borde_del_ttl_no_se_refresca`, `_la_cache_no_deja_mutar_lo_cacheado` | ✔ |
| R4 | `test_f002_r4_el_prompt_exige_la_razon_social_del_bloque_fiscal`, `_el_prompt_veta_la_marca_del_logotipo`, `_las_reglas_llegan_a_las_instructions` (leen el `prompts.yaml` REAL, no una copia) | ✔ |
| R5 | `test_f002_r5_obra_inexistente_se_descarta_y_marca_revision`, `_obra_existente_no_se_descarta` | ✔ |
| R6 | `test_f002_r6_codigo_no_normalizable_se_descarta` (`1234`, `12345`, `abc`, `09.37`), `_sin_codigo_leido_no_marca_revision` | ✔ |
| R7 | `test_f002_r7_obra_validada_retira_el_aviso`, `_reproceso_de_obra_invalida_repite_el_mismo_motivo`, `_motivo_no_se_duplica_al_reprocesar`, `_motivo_nuevo_se_suma_a_los_existentes`, `_motivos_con_json_roto_no_revientan`, `_retirada_quita_solo_los_motivos_de_obra`, `_retirada_del_ultimo_motivo_deja_la_columna_nula`, `_la_nota_de_obra_no_se_acumula`, `_la_nota_de_obra_no_pisa_las_de_otras_redes` | ✔ |
| R8 | `test_f002_r8_cif_existente_canoniza_el_nombre`, `_cif_existente_retira_el_aviso_previo`, `_sin_razon_social_no_pisa_el_nombre_leido` | ✔ |
| R9 | `test_f002_r9_horpresol_deja_propuesta_a_revision`, `_la_propuesta_nombra_el_cif_leido_y_el_candidato`, `_no_sobrescribe_el_cif_ni_el_nombre_leidos`, `_el_umbral_es_inclusivo`, `_ante_un_empate_gana_el_primer_candidato` | ✔ |
| R10 | `test_f002_r10_sin_candidato_marca_revision_sin_propuesta`, `_sin_obra_efectiva_marca_revision_sin_propuesta`, `_un_parecido_por_debajo_del_umbral_no_se_propone`, `_sin_nombre_leido_la_nota_no_escupe_none` | ✔ |
| R11 | `test_f002_r11_sin_cif_deduce_por_nombre_como_siempre`, `_sin_cif_no_consulta_el_maestro_prv` (regresión) | ✔ |
| R12 | `test_f002_r12_payload_de_sv1_se_traduce_a_contexto_de_email`, `_..._de_documento`, `_el_handler_pasa_la_fecha_de_recepcion_al_pipeline`, `_sin_fila_de_workflow_el_contexto_va_vacio`, `_payload_roto_no_revienta`, `_sin_correlation_key_no_se_consulta_la_bbdd`, `_sin_contexto_el_handler_manda_lo_de_siempre`, `_sin_fuente_cableada_*` (2), `_error_del_repositorio_no_revienta` | ✔ |
| R13 | `test_f002_r13_albaran_de_2023_en_correo_de_2026_va_a_revision`, `_fecha_muy_posterior_tambien_va_a_revision`, `_dentro_del_margen_no_marca_nada`, `_el_borde_exacto_no_marca`, `_un_dia_mas_alla_del_borde_marca`, `_max_dias_configurable`, `_acepta_los_formatos_de_recepcion_reales`, `_el_pipeline_ejecuta_el_guard_al_reenriquecer` | ✔ |
| R14 | `test_f002_r14_sin_fecha_de_email_usa_hoy_como_referencia`, `_sin_fecha_de_email_un_albaran_reciente_no_marca`, `_fecha_de_email_ilegible_cae_a_hoy` | ✔ |
| R15 | `test_f002_r15_fecha_nula_o_no_parseable_es_no_op` | ✔ |
| R16 | `test_f002_r16_excepcion_del_cliente_no_rompe_ni_descarta`, `_fallo_del_repositorio_al_descartar_no_rompe`, `_fallo_del_repositorio_al_retirar_no_rompe`, `_error_consultando_el_cif_no_rompe_ni_marca`, `_error_marcando_revision_no_rompe(_la_persistencia)`, `_error_leyendo_las_fechas_no_rompe`, `_un_guard_que_revienta_no_rompe_el_pipeline`, `_una_fuente_que_revienta_no_rompe_el_handler` | ✔ |
| R17 | `test_f002_r17_las_tres_redes_vienen_activadas_por_defecto`, `_red_apagada_no_descarta_obra_inexistente`, `_red_apagada_no_retira_avisos`, `_red_apagada_no_consulta_ni_marca`, `_guard_apagado_no_lee_ni_marca`, `_servicio_deshabilitado_no_toca_nada`, `_sin_guard_cableado_el_pipeline_sigue` | ✔ |

Cobertura de requisitos: **18/18**. Ninguno queda sin test, y ningún test
`test_f002_*` está huérfano de requisito.

## 7. Juicio de las desviaciones y observaciones (no bloquean)

### 7.1 Desviación 1 — el scorer propio `_score_razon_social`: **correcta, no requería volver a la PARADA 1**

La he verificado ejecutando el código real:

```
_score_razon_social('GRUPO OTTO HORPRESOL', 'HORPRESOL, S.L.') = 1.0
_match_score      ('grupo otto horpresol', 'horpresol, s.l.') = 0.333…
```

El implementer dice la verdad: con `_match_score` tal cual, el caso de
referencia **de la propia R9** puntúa 0,33 y, con el umbral 0,5 que fijó la
decisión P3, **no habría generado propuesta**. El `design.md` se contradecía
con el requisito que decía implementar.

Por qué la desviación es la salida correcta y no un cambio de plan
encubierto:

1. **No cambia el contrato con el humano.** R9 pide «score de nombre >=
   umbral del resolver»; el umbral sigue siendo `HEADER_RESOLVER_MIN_SCORE`
   (0,5, decisión P3), el comportamiento sigue siendo *proponer sin
   sobrescribir* (D3) y no se toca ningún otro servicio. Lo que cambia es
   *cómo* se calcula un número interno: eso es implementación, y el design
   lo mencionaba como nota de implementación, no como decisión de negocio.
2. **Cero regresión, y es comprobable.** `_score_razon_social` se usa
   ÚNICAMENTE en `_mejor_candidato_por_nombre`, de la red nueva. Los caminos
   previos del resolver (deducción por nombre, familia+obra, notas de
   candidatos) siguen llamando a `_match_score` sin tocar — verificado
   leyendo el fichero, no solo el diff.
3. **La alternativa era peor.** Implementar el design al pie de la letra
   habría entregado una feature que falla su propio caso de referencia y que
   habría pasado los tests solo si los tests se hubieran escrito para el
   comportamiento equivocado. Volver a la PARADA 1 estaría justificado si el
   arreglo hubiera cambiado *qué* hace la feature (bajar el umbral,
   sobrescribir automáticamente, tocar sv4 o `ruesma_comun`); no es el caso.
4. **Está documentada donde toca**: `progress/impl_F-002.md` §«Decisiones de
   diseño» y `progress/current.md` §«Desviaciones», ambas antes del review.

**Observación para el humano (no bloqueante).** El scorer hereda de
`_match_score` la regla «si uno contiene al otro, 1.0», y ahora la aplica en
los dos sentidos. Consecuencia: un candidato cuya razón social sea una
subcadena del nombre leído puntúa 1,0 aunque el parecido sea accidental
(comprobado: `_score_razon_social('TRANSPORTES DEL NORTE SL', 'SL') = 1.0`).
El daño posible está acotado por diseño —la red **solo propone**, nunca
sobrescribe, y el documento va a revisión igual por R9 o por R10, así que lo
único que puede fallar es *qué candidato se sugiere*—, pero conviene mirar en
la prueba local (T12, escenario 2) si alguna propuesta sale absurda. Si
ocurre, el arreglo natural es exigir al token que casa una longitud mínima,
no bajar el umbral.

### 7.2 Las otras tres desviaciones

- **`conftest.py` con `sys.path` explícito** en vez de vacío: necesaria y
  correcta. Un `conftest.py` vacío no hace importables `application/`,
  `domain/` ni `infrastructure/` cuando la suite se lanza desde otro
  directorio, y el portero las lanza desde la raíz del servicio. Lo he
  comprobado: las dos suites corren tanto desde la raíz del servicio como a
  través de `init.sh`.
- **Lógica de marcas extraída a funciones puras** (`anadir_motivo_revision`,
  `quitar_motivos_con_prefijo`, `sustituir_nota_por_prefijo`): es una mejora
  real de testabilidad, no un atajo. Gracias a ella la idempotencia, el
  dedupe por prefijo y el JSON histórico roto están probados sin BBDD (9
  tests de R7), y lo que queda sin cubrir es solo la transacción — que es
  justo lo que declaran los supervivientes 8–13, sin disfrazarlo.
- **El guard de fecha no retira su nota** cuando la fecha vuelve a estar en
  rango: límite consciente y correctamente anotado. R7 solo lo exige para
  obra, así que no es un incumplimiento. Merece entrar en la lista de mejoras
  futuras: la asimetría entre las tres redes sorprenderá a alguien.

### 7.3 Hallazgo lateral confirmado: el `.gitignore` de sv2 se traga los `.example`

**Confirmado, y lo dejo como observación para el humano — no lo he tocado**,
igual que el implementer.

```
git check-ignore -v services/albaranes-api/.env.example
services/albaranes-api/.gitignore:189:*.example    services/albaranes-api/.env.example
```

La línea 189 de ese `.gitignore` es `*.example`, dentro de un bloque que
también ignora `*.json`, `*.txt` y `*.csv`. Efecto real: el `.env.example` de
sv2 **existe actualizado en disco** —lo he leído: trae `SIGRID_API_BASE_URL`,
`SIGRID_API_FUNCTION_KEY`, `SIGRID_API_DATABASE`, `SIGRID_API_TIMEOUT_S`,
`OBRAS_ACTIVAS_ENABLED/TTL_S/MAX/COD_MIN`, todos **sin valores**— pero no
entra en git, así que nadie que clone el repositorio verá las variables
nuevas que sv2 necesita. El de sv3 sí entra y está bien.

Es un descuido del `.gitignore` (un `.env.example` está precisamente para
versionarse), es **anterior** a esta feature y arreglarlo toca un fichero
fuera del alcance de la spec. Decisión del humano; si me pregunta, la
recomendación es cambiar `*.example` por una excepción `!.env.example`, o
retirar el patrón, en un cambio propio.

### 7.4 Recomendaciones menores (ninguna bloquea)

1. **`progress/current.md`**: copiar las cinco verificaciones MANUAL de T12
   con su SQL literal, en vez de referenciar el informe. Es lo que pide C4 al
   pie de la letra y ahorra un salto justo en el momento en que el humano se
   sienta a probar.
2. **`design.md` sigue diciendo `_match_score`** en la sección de la red de
   proveedor. La desviación está registrada en dos sitios, así que no hay
   engaño, pero conviene que el líder actualice esa línea del design (o le
   añada una nota) para que la spec no quede mintiendo sobre el código que
   describe.
3. **Ruff**: los 14 ficheros nuevos añaden 23 avisos (7 `I001` orden de
   imports, 6 `RUF100` `noqa` innecesarios —los `# noqa: BLE001` sobran
   porque esa regla no está activada—, 4 `UP006` `Dict` en vez de `dict`,
   3 `DTZ011`, 2 `UP035`, 1 `B017`). Es deuda del mismo tipo que la que ya
   arrastra el repositorio (1065 avisos, declarados no bloqueantes por
   `init.sh`) y **18 de los 23 son autocorregibles**. No bloquea; sería una
   limpieza barata antes del merge a `dev`.

## 8. Automejora del protocolo (propuesta, NO aplicada)

Dos huecos que este review ha rozado y que el humano puede decidir cerrar:

1. **`CHECKPOINTS.md` C5 no contempla las tareas MANUAL ni las
   pendientes-de-despliegue.** Dice «todas las tareas `[x]`», pero una tarea
   MANUAL del humano NO puede estar `[x]` cuando el reviewer pasa, y una
   tarea congelada por una regla dura del humano tampoco. Hoy eso obliga al
   reviewer a razonar la excepción por su cuenta (lo he hecho en C5), y otro
   reviewer podría rechazar la feature por ello. Propuesta: admitir
   explícitamente los estados `[ ]` para tareas MANUAL y `[~]` para
   pendientes-de-despliegue, **exigiendo en ambos casos justificación
   escrita en `tasks.md` y su reflejo en el informe de review**.
2. **`.claude/agents/reviewer.md` no dice qué hacer cuando la corrida del
   reviewer genera artefactos.** `python -m evals.runner` sin `--feature`
   escribe `progress/evals_manual.md`, que aparece como fichero sin trackear
   y contamina el C5 que el propio reviewer está evaluando. Propuesta: añadir
   al protocolo que el reviewer ejecute el runner con `--feature F-XXX`
   cuando solo quiera reproducir la salida, y que borre cualquier artefacto
   que genere antes de evaluar C5 (es lo que he hecho, y consta en §1).

---

## Veredicto final

**APPROVED.** El entorno está en verde por mi propia ejecución, los 18
requisitos tienen test trazable y pasan, la fase RED trae trazas reales, la
cobertura del diff cumple (82,1 % ≥ 80 %), la campaña de mutación es
auténtica —recalculada y muestreada por mí, no creída—, las tres trampas de
dominio están respetadas en el código, Sigrid solo se toca en lectura vía
`sigrid-api`, `ruesma_comun` está intacto y la regla dura **SIN DESPLIEGUE**
se ha cumplido sin dejar tareas a medias: T9 está congelada con su motivo
escrito y su lista de acciones lista para el día del despliegue.

Dos condiciones que el líder debe respetar antes de marcar `done`, y que no
son mías sino de los propios checkpoints:

1. **T12 (MANUAL) tiene que ejecutarla el humano.** Es el único control que
   cubre los 6 supervivientes reales de las transacciones PostgreSQL, y el
   primero a mirar es `review_required` en `albaran_documents_merge`: si esa
   columna no se pone a `true`, nada de esta feature llega al revisor por
   mucho que los tests estén verdes.
2. **El prompt de IA1 no está evaluado por evals** (C4 ter en `aviso` con los
   libros vacíos). Rellenar `evals/ground_truth/` y subir la exigencia a
   `bloqueo` sigue siendo el pendiente que hereda F-011.
