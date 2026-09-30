# F-052 · Review PARCIAL del Bloque A (T1–T6)

Revisión completa del Bloque A (pasada 1): `git diff dev...a0bd84e`, commits 5588131..a0bd84e.

- **Veredicto del bloque:** CAMBIOS (dos cambios pequeños, CR-A1 y CR-A2; el código de
  producción es correcto y no hay regresiones). No es veredicto de cierre de F-052.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`). Exige fase RED,
  cobertura de líneas cambiadas ≥ 80 %, mutación con 0 supervivientes sin justificar y
  MANUAL con comando. La mutación es T19 y los MANUAL son T20–T23: fuera del bloque.

## Verificación ejecutada por el reviewer

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` | exit 0, ENTORNO LISTO; raíz `1067 passed in 314.56s` |
| Puerta cobertura | `[OK] 100.0% de 95 líneas cambiadas (95/95, umbral 80%, nivel critico)` |
| Puerta tamaño | `impl 219/220` (ver O2) |
| sv3 a mano (sin caché) | `284 passed in 4.62s` |
| comun a mano, después | `306 passed in 30.32s` |
| ruff sobre los ficheros nuevos | `All checks passed!` |
| SQL agregada: design §4 vs `_SQL_RESUMEN_OBRA_AGREGADO` | `diff` literal: idénticas |
| RED de T4 reproducida (copia en scratchpad, cliente de dcf9292) | `7 failed, 1 passed`: `[500, 500] == [500, 700]`, `1000 == 3543`, `assert 1000 > 5000` — coincide con el informe |
| RED de T5/T6 reproducida (copia, cliente de 6d9c795) | `9 failed, 10 passed`, los mismos 9 FAILED del informe |
| Mutante propio M1: quitar `filas.sort(...)` en el resumen | muerto (5 fallos: r5 barajado ×3, r5 ganador ×2) |
| Mutante propio M3: `max_rows=tamano` en la página | muerto (7 fallos en r11/r12/r13) |

Árbol de trabajo limpio tras las pruebas (todo en el scratchpad, `git status` vacío).

## Checkpoints (en lo aplicable al bloque)

- C1 [x] init.sh en verde; ficheros del arnés presentes.
- C2 [x] una sola `in_progress` (F-052) y rama correcta. «current.md solo la sesión
  activa»: N/A en review de bloque — `current.md` tiene 881 líneas de sesiones previas;
  lo resuelve el líder antes del cierre, no el Bloque A.
- C3 [x] hexagonal: `ruesma_comun.sigrid.lectura` puro (sin HTTP ni BBDD, recibe logger);
  el cliente de infraestructura lo usa; el doble vive en `tests/`. Primera línea con ruta
  en los 9 ficheros. Sin `print`, TODO, secretos, IPs ni GUID (barrido del diff con
  patrones de IP, GUID, `password|secret|key=|token`). Sin dependencias nuevas (`httpx`
  ya estaba). Trampas del monorepo: no toca merge/raw, schema ni importes.
- C3 bis N/A: no toca `docs/referencia/`.
- C4 [x] R2–R5 y R7–R14 con tests `test_f052_rN_*` en verde (tabla abajo); sin red ni
  BBDD (MockTransport). MANUAL listados en `current.md` (T20–T23), fuera del bloque.
- C4 bis:
  - [x] rigor declarado `critico`.
  - [x] fase RED: trazas reales en `impl_F-052.md` para T1–T6, y reproducidas por mí
    las de T4 y T5/T6. La de T2 es honesta (el test de humo del transporte).
  - [x] cobertura 95/95.
  - N/A mutación (T19, fuera del Bloque A por plan de `tasks.md`); el mutante manual
    de T6 («`nombre` por `texto`») consta muerto con su traza.
  - N/A RM1–RM6: no hay campaña que revisar todavía.

## Trazabilidad requisito → test (Bloque A)

| Req. | Tests |
|---|---|
| R2 | `test_f052_r2_el_resumen_trae_los_81_con_salmedina_y_su_texto`, `_r2_paso_obra_familia_puntua_los_81` |
| R3 | `test_f052_r3_una_sola_peticion_con_la_consulta_agregada`, `_r3_truncado_lanza_y_no_pagina`, `_r3_sin_obra_no_consulta`, `_r3_un_resumen_por_cif_codigos_y_texto` |
| R4 | `test_f052_r4_mismas_familias_por_cif_en_todo_el_fixture[0691,0668]`, `_r4_el_fixture_no_es_trivial`, `_r4_casos_dirigidos` ×4 |
| R5 | `test_f052_r5_barajado_mismo_resumen_y_mismo_orden` ×3; `_r5_mismo_ganador_y_misma_nota_con_tres_barajados` ×3 (débil: CR-A1). La parte «red por nombre» es de T7 |
| R7 | `test_f052_r7_politica_es_obligatoria_y_sin_valor_por_defecto`, `_r7_max_rows_opcional_por_llamada`, `_r7_politica_invalida_*` (comun) |
| R8/R9 | `test_f052_r8_*`, `test_f052_r9_*` (comun y cliente) |
| R10 | `test_f052_r10_consultas_no_tolera_lanzan_si_truncado` ×5, `_r10_documentos_del_contrato_toleran_con_warning`, `_r10_sin_truncado_*`, `_r10_docstring_*` |
| R11 | `test_f052_r11_fetch_contratos_1200_lineas_agrupadas_en_orden`, `_r11_caso_normal_una_sola_llamada`, `_r11_pagina_lineas_configurable` |
| R12 | `test_f052_r12_search_proveedores_devuelve_los_3543`, `_r12_hallazgo_el_max_rows_pedido_llega_a_sigrid_api`, `_r12_*_pagina_si_la_pagina_es_menor` |
| R13 | `test_f052_r13_*` (cliente y comun). El rastro `error` es de T10 |
| R14 | `test_f052_r14_*` (comun) |

## Lo revisado en los puntos pedidos

- **`truncated` nunca en silencio**: `_post_sql_read` separa HTTP (`_enviar_sql_read`) de
  la política (`comprobar_truncado`); `politica` keyword-only sin defecto y tipada
  (`TypeError` aunque no trunque). Las 7 consultas llevan la política de design §3
  (5 NO_TOLERA, 2 TOLERA); no queda ninguna llamada sin ella (grep del cliente).
- **Paginación**: `max_rows = pagina + 1` hace que una página llena nunca se marque
  truncada; tope `max_paginas` → `SigridRespuestaTruncada`. `ORDER BY` de
  `header_and_lines` es único (todas las uniones son por clave `ide`; `ctr.ide` desempata
  contratos sin líneas) y el de `search_proveedores` lo es sobre `DISTINCT cif, raz`.
- **Bug de `max_rows` ignorado**: confirmado en el diff (`"max_rows": self._max_rows`) y
  con RED reproducida (`assert 1000 > 5000`).
- **Agregada**: una llamada, NO_TOLERA, `max_rows` del cliente (1.000 ≥ 163), dedupe por
  CIF, `split('|')`, `None → ""`. Que sigrid-api real la acepte queda para T20/T21.
- **Doble**: modela `truncated` como `filas >= max_rows` («se alcanzó», `sigrid_api.md`
  §6.1): conservador frente al real. Rechaza `OFFSET` sin `ORDER BY` (400), sirve
  `search_proveedores` desordenada si falta `ORDER BY`, trunca la consulta antigua a
  1.000 sin SALMEDINA (test de humo) y baraja lo no fijado por `OFFSET`. No pasa por
  construcción: lo prueban las dos RED reproducidas y los dos mutantes muertos.
- **T6**: compara de verdad el `texto` que devuelve el cliente real (vía agregada del
  doble) con el texto por líneas reconstruido como el código anterior, en los 81 + 3 CIF
  y cuatro casos dirigidos; el fixture tiene ≥ 60 CIF con familia.
- **Consumidores**: el puerto no cambia; `HeaderResolverService` y
  `HeaderGroundingService` siguen funcionando (suite sv3 verde). `test_f002_red_proveedor`
  usa su propio fake y no se ve afectado. sv4 tiene su copia del cliente (D6): intacta.

## Cambios requeridos

1. **CR-A1 · R5 «mismo ganador» pasa también en el caso degenerado.**
   `services/albaranes-persistencia/tests/test_f052_resumen_obra.py:154-171`
   (`test_f052_r5_mismo_ganador_y_misma_nota_con_tres_barajados`) solo compara los cuatro
   resultados entre sí. Si el paso obra + familia falla siempre (consulta rota, lista
   vacía), los cuatro degradan igual y el test pasa: de hecho pasó en la RED contra T4
   (entre los «10 passed»). Añadir, por caso, el resultado esperado de la referencia
   —`(B82899550, "deterministic")` en `red-por-nombre`; nota con «Candidatos con contrato
   en la obra 0691» en `familia-sin-nombre`; `B10000000` en `nombre-debil-y-familia`— y
   que el doble no recibió `search_proveedores` (el paso no degradó al fallback global).
2. **CR-A2 · `leer_paginado` acepta en silencio una página de más de `pagina` filas.**
   `services/albaranes-comun/ruesma_comun/sigrid/lectura.py:165-178`. Si `leer_pagina`
   devuelve más filas que `tamano` (FETCH no aplicado, o una página truncada con
   `pagina + 1` filas bajo `TOLERA`), se añaden todas y la siguiente página, con
   `offset = n * pagina`, repite filas sin aviso. Hoy no es alcanzable en sv3 (las dos
   paginadas son NO_TOLERA y usan `con_paginacion`), pero es la función compartida que
   sv4 y otros van a usar. Tratar `len(trozo) > pagina` como anomalía (excepción, o
   recorte a `pagina` con WARNING según política) y cubrirlo con un test en
   `test_f052_sigrid_lectura.py` cuya fuente devuelva `tamano + 1` filas.

## Observaciones (no bloquean el bloque)

- **O1 · grounding**: `HeaderGroundingService` (`header_grounding_service.py:328-348`)
  toma los 200 primeros de `search_proveedores()`. Antes eran los 200 primeros de un
  orden no garantizado de una lista cortada a 1.000; ahora, los 200 primeros por CIF de
  3.543, y una respuesta truncada lanza (antes pasaba). Efecto menor e intencionado por
  R12, pero conviene anotarlo en el informe de Bloque B o en `azure-apps/albaranes.md` (T16).
- **O2 · tamaño**: `impl_F-052.md` está en 219/220 con solo 6 de 24 tareas. El Bloque B
  tendrá que resumir el A (las trazas RED ya reproducidas pueden condensarse a su línea
  clave y enlazar a los commits) o la puerta de tamaño se pondrá roja.
- **O3 · `con_paginacion`** acepta cualquier `ORDER BY` de la SQL, también uno interno
  (como los de `FOR XML PATH`). SQL Server rechazaría el `OFFSET` sin orden exterior, así
  que no es silencioso; basta con saberlo si alguien lo aplica a una SQL con subconsultas.
- **O4 · dedupe por CIF** ordena en Python por punto de código, no con la collation de
  Sigrid: con un CIF con dos `raz` que solo difieran en mayúsculas o acentos podría
  quedarse otra que la «primera de la SQL». Determinista igualmente (R5); sin efecto en
  la puntuación salvo el nombre mostrado.
- **O5**: R5 en su parte «red por nombre» y R13 en su parte «rastro `error`» se cierran
  en T7 y T10; R1 ya sale verde con el cliente de T5, así que su RED de T7 tendrá que ir
  contra el código anterior a T5 o contra la firma nueva (el implementer ya lo avisa).

## Propuesta de automejora (no aplicada)

`reviewer.md`, sección de fase RED: pedir que el reviewer mire también los tests que
**pasaron** en la traza RED de un requisito central y justifique por qué pasaban. Aquí
fue lo que destapó CR-A1; hoy el protocolo solo mira los que fallan.
