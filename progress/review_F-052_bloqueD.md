Revisión incremental desde ce6bbd4 (Bloque D, pasada 1): `git diff ce6bbd4..7a157f9` (Bloques A–C aprobados, no se releen)

# F-052 · Review PARCIAL del Bloque D (T14, T14 bis, T16, T18, `ruesma_comun` 0.7.0)

- **Veredicto del bloque:** APROBADO. No es veredicto de cierre de F-052 (faltan T19–T23).
- **Nivel de rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación con 0
  supervivientes sin justificar y MANUAL. T19 y T20–T23 fuera del bloque por plan.

## Verificación propia

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` (entero) | exit 0, ENTORNO LISTO; raíz `1067 passed in 356.76s`; servicios en verde |
| Puertas | cobertura `97.5% de 601 líneas (586/601)`; tamaño `requirements 150/150, design 250/250, impl 192/220`; rutas sensibles N/A |
| Suites a mano, una a una | sv3 `400 passed in 7.61s`; comun `327 passed in 35.68s`; sv4 (su `.venv`) `372 passed in 17.19s` |
| RED de T14 bis (test de comun de `f25be76` sobre `36713de`, copia) | `3 failed, 31 passed`: coincide con el informe |
| Mutantes manuales reproducidos (copia de sv3 en scratchpad) | `maximo >= LIMITE` → `>`: muere (`test_f052_r29_justo_15_s_ya_falla`); `pagina_lineas` por defecto → 1000: muere (`test_f052_pagina_por_defecto_1200_lineas_en_una_sola_peticion`) |
| ruff de los `.py` del diff | 6 avisos, todos en `sigrid_api_contrato_client.py` e idénticos en `ce6bbd4`: deuda previa |
| Árbol tras las pruebas | limpio (`git status` vacío) |

## T14 · el script es de solo lectura (comprobado, no supuesto)

- Ejecuté los tres modos contra `DobleSigridApi` con un transporte espía: **todas** las
  peticiones van a `/api/sql/read` (ninguna a `/api/documents` ni a otra ruta), todas las SQL
  empiezan por `SELECT`/`WITH` y ninguna contiene `INSERT|UPDATE|DELETE|MERGE|EXEC|DROP|ALTER|
  CREATE|TRUNCATE|INTO`. R29: 5 peticiones; R30 (0691+0696): 6; obras grandes: 1.
- No toca PostgreSQL (solo `config.settings` para el `.env`). `fetch_contratos` solo hace
  SELECT (`header_and_lines`, `rcg/gra`); `download_contrato_pdf` no se llama.
- Secretos: la clave va en cabecera (`x-functions-key`), nunca en URL. Errores redactados
  (`redactar` con clave y URL de settings, ambas `str`); `ValidationError` del `.env` solo
  enseña nombres de campo; `configurar_logs()` deja el logger del cliente (que escribe la URL
  y `logger.exception`) en CRITICAL y la raíz en WARNING (httpx INFO no sale). Tests:
  `test_f052_r29_error_xml_falla_sin_filtrar_la_clave`, `..._env_invalido_no_muestra_valores`,
  `test_f052_redactar_oculta_clave_y_url`.
- Mide lo que piden R29/R30/§8 y lo que T20/T21 esperan leer:
  - R29: agregada N veces por el método público, filas/`truncated`/bytes/segundos por petición
    (`TransporteQueMide`, sin alterar petición ni respuesta), CIF dentro, score con
    `_score_razon_social` y el mismo criterio estricto `>` de `_mejor_candidato_por_nombre`
    (comprobado en `header_resolver_service.py:528-533`), umbral `HEADER_RESOLVER_MIN_SCORE`,
    `fetch_contratos` con contratos y nº de líneas; «< 15 s» de design §10 con `>=` en la frontera.
  - R30: `_SQL_LINEAS_OBRA` es **idéntica** a la consulta por líneas previa a F-052 (comparada con
    `c8a295e`, merge-base con `dev`); `texto_por_lineas` reproduce su agregación (mismos 3
    campos, `strip`, no vacíos). La lista `DISTINCT` de `fetch_proveedores_por_obra` (sv3) es
    la misma SQL que `_SQL_PROVEEDORES_POR_OBRA` del selector de sv4 salvo el `ORDER BY`: el
    conjunto de CIF coincide, como pide R30. Lectura «sin tope» = `max_rows` 500.000 y `NO_TOLERA`.
  - §8: `HAVING COUNT(*) > 1000` sobre el mismo FROM (los `LEFT JOIN pro/con_pro` omitidos son
    1:1 y no cambian el recuento); imprime la lista para el SELECT de T23.
- Tests: 35 contra el doble (OK, truncado, error XML, CIF ausente, umbral, mejor ≠ CIF,
  familias y CIF de más/de menos, argumentos inválidos con código 2 sin consultar).

## T14 bis · tamaño de página

- `MAX_FILAS_POR_PETICION = 500_000`, `PAGINA_MAXIMA = 499_999` en `ruesma_comun.sigrid`;
  `leer_paginado` rechaza `pagina > PAGINA_MAXIMA` antes de pedir nada.
- sv3: `max_rows` por defecto 500.000; `pagina_lineas` y `search_proveedores(max_rows=…)` por
  defecto 499.999; `__init__` rechaza `max_rows` ∉ [1, 500.000] y `pagina_lineas` ∉
  [1, 499.999]; `_enviar_sql_read` rechaza cualquier `max_rows` > 500.000 sin enviar
  (`test_f052_ninguna_peticion_pasa_del_tope`: `doble.peticiones == []`).
- `truncated` y `max_paginas=20` intactos. `composition.py` y `app.py` no pasan `max_rows` ni
  página: heredan los defectos. Las 2 lecturas `TOLERA` de sv3 (`rcg/gra`) son de pocas filas.
- Tests no debilitados: `test_f052_r11_*_1200_lineas_*` pasa a `pagina_lineas=1000` explícito
  y sigue probando dos páginas; R13 (tope de páginas) sigue con páginas pequeñas; comun
  conserva todos los de `leer_paginado` y gana 3. Nuevos: una sola petición por defecto,
  límites justos admitidos, fuera de rango rechazados.
- 230 s: anotado en el cliente, `ARCHITECTURE.md`, `azure-apps` §8 y el informe (matiz: O-D1).
  Fuera (D6, O-C4): la copia de sv4 del cliente y `SigridApiObraClient` de sv3.

## T18 · `docs/ARCHITECTURE.md`, `sv3.md`, `sv4.md`

- «Acceso a datos»: 500.000 de `MAX_ALLOWED_ROWS` con referencia a `sigrid_api.md` §4.1
  (comprobado: §4.1 dice 500.000 en la instancia), el 1.000 como `max_rows` del cliente, las
  tres reglas (`truncated` nunca en silencio → `PoliticaTruncado`/`comprobar_truncado`;
  agregar en SQL; paginar con `ruesma_comun.sigrid`), coherentes con §6.3 de `sigrid_api.md`.
- Excepción de reconstrucción: `ruesma_comun.sigrid` y `.obras` solo los importan sv3 y sv4
  (verificado con `git grep`: solo `albaranes-persistencia`, `albaranes-front` y la propia
  comun), orden sv3 → sv4 con su motivo (DDL de `contratos_busqueda_*`).
- `sv3.md` y `sv4.md` no citan 1.000, 10.000, `max_rows` ni `truncated`: sin cambios, correcto.

## T16 · `azure-apps/albaranes.md` (commit `141f9aa`, solo `albaranes.md`)

- §3: las 4 columnas con tipos idénticos al DDL (`phase2_ddl.py`, `orm_models.py:203-206`:
  64/32/16/64), dueño sv3, lector sv4, escritor del re-fetch solo-front, sin backfill, y el
  aviso de orden sv3 → sv4.
- §8 nuevo: `truncated` y políticas por consulta, 1.000 = `max_rows` del cliente, agregada en
  SQL con **dependencia de `WITH` + `FOR XML PATH`** y su degradación, paginadas con página de
  499.999 y tope de 20, grounding con 200 por CIF (`max_proveedores_candidatos: int = 200`),
  `ruesma_comun` 0.7.0 con reconstrucción conjunta sv3 → sv4 y rollback al revés.
- Ningún otro documento de `azure-apps` tocado (`git show --stat`: 1 fichero); árbol de
  `azure-apps` limpio. Sin secretos, IDs de suscripción/tenant ni IPs: solo nombres de
  servicio, tablas y comandos `deploy.ps1`.

**`ruesma_comun` 0.7.0**: `pyproject.toml`, `__version__` y README dicen 0.7.0; `git grep` no
halla ningún `0.6.0` ni pin en requirements o Dockerfiles; un test ata paquete y `pyproject`.

## Checkpoints (alcance del bloque)

- C1 [x] init.sh exit 0; ficheros base presentes.
- C2 [x] una sola feature `in_progress` (F-052), rama correcta, `current.md` al día.
- C3 [x] hexagonal: el script vive en `scripts/` (adaptador de diagnóstico), constantes de
  tope en comun sin HTTP ni SQL; primera línea con ruta en los ficheros nuevos; el `print` del
  script es su salida, no depuración; sin secretos (la «clave» de tests es ficticia).
- C3 bis N/A: el bloque no incorpora documentos de fuera a `docs/referencia/`.
- C4 [x] tests sin red ni BBDD (doble HTTP en memoria); MANUAL T20–T23 listadas en `tasks.md`.
- C4 bis: rigor declarado [x]; RED [x] (salida real en el informe y reproducida una);
  cobertura [x] 97,5 %; «Evidencias» [x] con los cuatro números. Mutación, RM1–RM6 y campaña:
  **N/A en este bloque**, justificado: la campaña es T19 y se revisará en su pasada; los 17
  mutantes manuales son evidencia complementaria, no la sustituyen.
- C4 ter [x] N/A impreso por init.sh (no toca rutas sensibles).
- C5: tareas del bloque `[x]` con commits `F-052 Tn: …`; T19–T23 abiertas por plan
  (no es cierre). Sin ficheros sin trackear.

## Cobertura del bloque (requisito → test)

| Requisito / tarea | Test |
|---|---|
| R29 (instrumento) | `test_f052_r29_*` (13) en `test_f052_script_verificacion.py` |
| R30 (instrumento) | `test_f052_r30_*` (5), incl. `texto_por_lineas_como_el_codigo_antiguo` |
| design §8 | `test_f052_listar_obras_grandes`, `..._truncada_falla` |
| T14 bis (comun) | `test_f052_tope_de_sigrid_api_y_pagina_maxima`, `test_f052_leer_paginado_*_tope`/`*_pagina_maxima_*` |
| T14 bis (sv3) | `test_f052_pagina_por_defecto_*`, `test_f052_max_rows_por_defecto_*`, `test_f052_cliente_rechaza_*` (4), `..._admite_los_limites_justos`, `test_f052_ninguna_peticion_pasa_del_tope` |
| 0.7.0 | `test_f052_version_0_7_0_en_paquete_y_pyproject` |

## Observaciones (no bloquean; para el líder y el cierre)

- **O-D1 · «acotada por `timeout_s`» es aproximado.** En httpx `timeout=30` es por operación
  (conectar, leer cada trozo…), no un plazo total, y `timeout_seconds` de sigrid-api acota la
  ejecución SQL, no la serialización. Con los volúmenes medidos (≤ 3.543 filas) es irrelevante;
  `sigrid_api.md` §4.1 avisa además de que 500.000 «no es una recomendación». La decisión del
  humano manda; si se quiere precisión, una frase en `ARCHITECTURE.md` y `azure-apps` §8 al cierre.
- **O-D2 · fecha.** `ARCHITECTURE.md` y la constante: «leído el 2026-09-30»; `sigrid_api.md`
  §4.1: comprobado el 2026-08-18. El valor coincide; la fecha no la puedo verificar.
- **O-D3 · `azure-apps` §8 «(sv7 → sv3)»** alude al camino del difunto sv7, que un lector de
  `azure-apps` puede no conocer. Cosmético.
- **O-D4 · R29 no compara 81 filas ni `CTSU24/0402`**: los imprime y el humano los contrasta
  con T20/T21. Aceptable en un instrumento manual.
- Abiertas fuera del bloque: O-C4, O-C5, O-B2, T19 (incluirá `scripts/`), T20–T23 y el «1.000»
  del `CLAUDE.md` transversal y de otros documentos de `azure-apps` (otros dueños).

**Cambios requeridos:** ninguno.
