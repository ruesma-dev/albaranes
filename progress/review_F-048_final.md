<!-- progress/review_F-048_final.md -->
Revisión completa (review final, pasada 1) de `1807e83..63571a6`. Lo aprobado en las seis reviews por bloques se da por bueno; aquí se mira la feature de extremo a extremo, T34 y el cierre

# F-048 · Review final (todo salvo los bloques E y G)

**Veredicto: CHANGES_REQUESTED**. Solo es papeleo: el código, los tests y la campaña de mutación están
listos. Quedan tres arreglos baratos: un checkbox de C4 vacío, un riesgo de despliegue sin su comando y
un criterio de T37 que daría un falso rojo. Hechos esos tres, solo faltan E y G (última sección).
**Rigor** `critico` (declarado): RED, cobertura ≥ 80 %, 0 supervivientes sin justificar, RM1–RM6, MANUAL.

## Qué se ejecutó (resultados reales)

- `bash harness/init.sh`: **exit 0, ENTORNO LISTO**; raíz `865 passed in 125.20s`; `PUERTA COBERTURA 99.5 %
  (661/664)`; `TAMAÑO` OK (impl 218/220); `[AVISO] RUTAS SENSIBLES` 11 rutas, sin `evals_F-048.md` (T40).
- Suites a mano, una detrás de otra, `-p no:cacheprovider`: comun `274 passed, 3 skipped in 102.86s` ·
  sv1 `98 passed` · sv2 `374 passed` · sv3 `233 passed` · sv4 (su `.venv`) `247 passed`.
- `git diff e7fe2c0..HEAD --stat -- services/ ':!**/tests/**'` sale **vacío**: después solo hay 4 tests
  `test_f048_t34_supervivientes.py`, papeleo y `tasks.md`. `git status` limpio; worktree temporal retirado.

## Mutación (T34) · RM1–RM6

- **Recálculo propio** (`harness.alcance` + `generar_mutantes`, puro): **34 ficheros, 1.883 líneas, 175
  mutantes**, igual que el informe. Muestreo los supervivientes 2, 9, 22 y 26: existen, con el mismo
  operador y el mismo texto original→mutado. Ni «⚠ CAMPAÑA NO VÁLIDA» ni base rota; campaña completa.
- **Tiempo total 617,2 s > 60 s ⇒ campaña no reejecutada**: basta el recálculo, RM1–RM6 y la reinyección.
  Coste por mutante 617,2 × 4 / 175 = **14,1 s**.
- **RM1** [x] medido `e7fe2c0750cf…`; producción sin cambios desde entonces. **RM2** [x] media 3,5 × 4 = 14 s
  frente a líneas base de 3,6 s (sv1) a 117 s (comun). 146 de los 175 mutantes son de fuera de comun, y
  con `-x` los muertos abortan pronto: no hay salto de orden de magnitud.
- **RM3** [x] Revisé la lista de los 175 y no veo ningún muerto equivalente. Ejemplo: el `+= 2` de
  `mail_client.py:39` deja el contador en 1 al cerrar, así que no es equivalente.
- **RM4** [x] 3 huecos reinyectados en copias; coinciden antes, después y nº de fallos, con la traza en
  la copia: n.º 2 (`origen_datos_resolver.py:174`) `6 passed` → `2 failed` (incluye `TypeError: 'NoneType'
  object is not a mapping`) · n.º 24 (`mail_client.py:305`) `26 passed` → `1 failed` (`DID NOT RAISE`) ·
  n.º 26 (`review_models.py:928`, sv4) `1 passed` → `1 failed`.
- **RM5** [x] **22 y 23**: en un `git worktree` de HEAD con la línea 39 y luego la 45 mutadas, sv1 da
  `98 passed`; guarda y demostración, `10 passed`. Diferencial propio sobre 20.010 HTML (10 a mano:
  anidados, cruzados, sin cerrar, autocerrados, mayúsculas; más 20.000 aleatorios): **0 discrepancias** y
  el control detectado (script/style son CDATA: contador en 0 o ±1). **9**, por lectura:
  `CalledProcessError` es `SubprocessError` y cae en el `except` que devuelve `False` (`capturar_correo.py:73`).
- **RM6** [x] No se quitó ninguna guarda: T34 no tocó producción.

## Coherencia de extremo a extremo (leída en el código): sin desajustes

1. **sv1** escribe `input/{id}.correo.json` con `guardar_contexto_correo`/`nombre_blob_correo` de comun
   ANTES de `publicar`, y `correo_blob` lleva ese nombre (`intake_cola_adapter.py:128-140, 164-169`).
2. **sv2**: `ejecutar_worker(tipo_mensaje="extraccion")` → `desde_texto` → `MensajeExtraccion` con el campo;
   lo lee `getattr` y lo abre `leer_contexto_correo`, la misma función de comun. `sellar_origen_datos`
   corre sobre el envelope FINAL con la lectura de fase 1 (recortada por CR-C3), hace
   `pop("lectura_correo")` y escribe `data.origen_datos`.
3. **sv3**: el mismo `OrigenDatos` de comun (`extra="ignore"`, compatible con F-049). El merge lo pasa a
   mano y solo marca las filas 3 (`discrepancia`) y 5 (`correo_ambiguo`).
4. **La red de obra** quita solo lo que empieza por `obra_`, y los motivos son `correo_obra_*` (CR-D1).
5. **sv4** lee `raw_extraction_json → data.origen_datos` con el mismo modelo, solo en la vista MERGE, en
   la misma ruta que el SELECT de T37. `raw_extraction_json` solo lo leen sv3 y sv4; sv5 es código muerto.

## Orden de despliegue

**sv3 → sv2 → sv1 es correcto.** **sv2 antes que sv3** rompe: sv2 sella `origen_datos` siempre y el
sv3 viejo (`extra='forbid'`) manda **todo documento a poison** mientras dure el hueco; por lo mismo, el
rollback va al revés (sv1 → sv2 → sv3). **sv1 antes que sv2** no rompe: el sv2 viejo ignora
`correo_blob` y extrae sin correo; el blob lo purga la lifecycle. **sv4**, cuando sea. **Hallazgo**:
`.\deploy.ps1` sin `-Only` sigue `$APPS` (sv1, sv2, sv3…; `infra/00_vars.ps1:61-68`, `deploy.ps1:61,77`)
y **actualiza sv2 antes que sv3**. La regla 15 y `azure-apps` dan el orden, pero no el comando (cambio 2).

## C4 ter: PENDIENTE DEL HUMANO (T40), no es un defecto

`python -m harness.rutas_sensibles` sale con exit 3 (`aviso`): 11 rutas y ningún `progress/evals_F-048.md`.
Tendrá que traer `MODO: completa`, `FASES: IA1,IA2,IA3,IA4,E2E` y `VEREDICTO: VERDE`. Se factura, así que lo
decide el humano. **Nota**: `.gitignore:46` excluye `progress/evals_*.md`, así que «su commit pertenece a
la rama» es imposible. La frescura se juzgará por la fecha del fichero, que ha de ser posterior a `63571a6`.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés. **C3 bis** N/A: no se toca `docs/referencia/`.
- **C2** [x] una feature `in_progress` · [x] rama · **[ ] `current.md`**: `:930-935` dice aún «siguiente paso:
  aprobación de la v3» (cambio 1) · N/A `history.md` (nada pasa a `done`).
- **C3** [x] Hexagonal: ningún `domain/` tocado importa infraestructura. [x] Los 34 `.py` llevan la
  ruta en la primera línea. [x] No hay prints de depuración (los dos `print` son la salida de dos CLI).
  [x] Sin secretos ni dependencias nuevas; el barrido de los tests solo da `@ejemplo.test` y un
  `600123123` inventado. [x] Trampas: se lee el merge, sin DDL, lectores de `raw_extraction_json`
  listados, sin importes.
- **C4** [x] Cada R tiene test en verde o MANUAL (tabla). [x] Sin red ni BBDD. **[ ] MANUAL en
  `current.md` con comando**: T36–T41 solo están en `tasks.md` (cambio 1).
- **C4 bis** [x] Rigor declarado. [x] RED pegado en `impl_F-048.md` y en los ficheros de bloque.
  [x] Cobertura 99,5 %. [x] Mutación verificada. [x] Ni campaña no válida ni base rota. [x] RM1, RM2, RM5
  y RM6. [x] 0 `PENDIENTE` y 0 sin justificar; al ser `critico`, **el humano acepta los 3 equivalentes**.
  [x] Evidencias: `impl_F-048.md:207-218` y el cuadro de `impl_F-048_T34_supervivientes.md`, con los
  workers.
- **C4 ter**: aviso con motivo (T40). **C5** [x] Un commit `F-048 Tn:` por tarea hecha (T1–T35
  comprobados). [x] Árbol limpio. [x] `in_progress`. Quedan E y G, a propósito.

## Trazabilidad (`test_f048_rN_*`)

| R | Cobertura |
|---|---|
| R1 · R8–R9 · R13 · R24 · R37 | comun `r1_contexto`, `r8_r9_mensaje`, `r13_prompt`, `r24_origen_datos`, `r37_llm_logger`, `t34_*` |
| R2–R7 · R10 · R36 · R39 | sv1 `r2_r4_graph`, `r3_r5_pipeline`, `r6_*`, `r7_r10_intake`, `r36_logs`, `r39_captura`, `t34_*`; R36 también sv2 `r36_logs` y comun `r36_retry_policy` |
| R11–R25 · R42 | sv2 `r11_worker`, `r12_render_fase1`, `r14_*`, `r15_schema`, `r16_prompt_yaml`, `r18_lista_obras`, `r18_normalizacion`, `r19_r22_tabla_d5`, `r23_r25_sellado`, `r24_lectura_tolerante`, `r42_encolar` |
| R26–R31 | sv3 `r26_modelo`, `r27_merge`, `r28_red_obra`, `r29_r31_motivos_revision` (R30 en `r29_r30_*`) |
| R32–R35 | sv4 `r32_r34_vista_avisos`, `r35_vista_modelo`, `t34_*` |
| R38 | sv1 `r39_captura` (`git check-ignore`); **falta la parte de evals: T29 (E)** |
| R40 · R41 / R43 / R44 | **T31 (E)** / **MANUAL T36–T39** / RED + `PUERTA COBERTURA` + T34 |

## Menores y avisos de las reviews por bloques

- **Cerrados con su CR**: A 1–8 y el aviso A · B 1, 3, 5 y 6 (el 2, en la regla 15) · C1 completo · C2
  1–3 y los avisos A y B · D 1–3 y el aviso C · F completo.
- **Sin anotar** (no bloquean; entran en el cambio 1): B-4 (un 429/503 de Graph deja el correo sin
  contexto) y C1-2 (colisiones de la lista), los dos para contarlos en T40. A-B (la caché de `init.sh`
  no ve comun) sigue siendo automejora; por eso corrí las suites a mano.

## Cambios requeridos

1. **`progress/current.md`**: añadir arriba «F-048 · pendiente del humano» con (a) el bloque E, bloqueado
   por F-047 (`git merge-base --is-ancestor 9f8a008 HEAD`); (b) T36–T41 con el comando EXACTO de
   `tasks.md:70-75`; (c) aceptar los 3 equivalentes de T34; (d) en T40, contar también los avisos «sin
   contexto de correo» de sv1 y los WARNING de colisión (B-4, C1-2). Y corregir o retirar `:930-935`.
2. **`docs/ARCHITECTURE.md:224-226`** y **`azure-apps/albaranes.md:210-212`**: el comando
   (`.\deploy.ps1 -Only sv3`, `check_deploy.ps1`, luego `-Only sv2` y `-Only sv1`), que `.\deploy.ps1` sin
   `-Only` actualiza sv2 antes que sv3 (hueco de poison) y que el rollback va al revés. En `azure-apps`,
   commit aparte y sin push.
3. **`specs/F-048-correo-contexto-ia1/tasks.md:71` (T37)**: el `Select-String` en `LLM_CALL_LOG_DIR` de «una
   frase del cuerpo» saldrá ROJO aunque todo esté bien. La respuesta cruda de IA1 trae
   `lectura_correo.evidencia`, que es por diseño una frase del correo (R15; menor 1(b) de C2), y
   `origen_datos` la guarda recortada a 160 (R24). Hay que precisar que se busca una frase del cuerpo que
   NO sea la de la evidencia.

## Qué falta para cerrar, hechos los cambios

**E**: integrar F-047 y T29–T31 (`pytest tests/test_f048_evals_correos.py`, `pytest tests -k "f048 and
inyeccion"`). **G**: T36 `capturar_correo.py --message-id <ID> --caso <CASO>` ×3; T37–T39 en local con el
SELECT de `tasks.md:71`; T40 `python -m evals.runner --con-llm --feature F-048` (se factura); T41
`bash harness/init.sh`. Después, review de E y G, incremental desde `63571a6`.

## Automejora (propuesta, no aplicada)

- **C4 ter** (`arnes-base`): con el informe de evals ignorado por git, «su commit pertenece a la rama» →
  «modificado después del último commit a una ruta sensible». **`reviewer.md`**: si la feature fija un
  orden de despliegue, mirar también el orden por defecto del script, no solo la documentación.
