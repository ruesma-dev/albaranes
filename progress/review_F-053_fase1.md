Revisión completa (pasada 1) de la fase 1, `dev` (`e7d7507`)...`86ae0ac`
<!-- progress/review_F-053_fase1.md -->
# Review F-053 · fase 1 (T0a, T1, T2, T2b, T3–T16) · reviewer, 2026-10-06

**Veredicto: CHANGES_REQUESTED.** La parte que escribe en el ERP aguanta. Probé 18 controles negativos míos, contrastados
con el contrato y con el código de sigrid-api, y los tests cazaron todos. Pero hay una fuga de secretos al log de
arranque (H1, contra R35 y C3) y un campo del adjunto que no existe en la respuesta real de sigrid-api (H2). Son dos
arreglos pequeños; la pasada 2 será incremental desde `86ae0ac`.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 %, mutación con
cero supervivientes y MANUAL con su comando. Es una review intermedia, así que no se exigen T17+ (sv4, infra, docs y
mutación T25) ni `init.sh` (decisión del humano en F-049: suites sustitutas en las fases intermedias).

## Verificación ejecutada (no copiada del informe)

- Suites, una tras otra, con el `.venv` raíz y `PYTHONPATH` apuntando al comun del worktree (comprobé que
  `ruesma_comun` se importa desde `albaranes-F-053`). Resultados: sv9 **430 passed** (17,6 s) · comun **374** (62,6 s) ·
  sv3 **444** (25,0 s) · sv6 **289** (19,2 s) · raíz **1083** (253,3 s). Todo bajo `coverage`.
- `python -m harness.cobertura --base dev --config harness/rigor.json` →
  `PUERTA COBERTURA: 96.1% de 1401 líneas cambiadas cubiertas (1346/1401, umbral 80%, nivel critico)`.
- `harness.tamano` en topes; `ruff check .` desde sv9 limpio (los 19 I001 desde la raíz son de configuración); ruta en
  la primera línea de los 40 ficheros nuevos; sin `print`.
- Contrato F-009 v8.2 (`13fd99d`, solo lectura con `git show`): `contrato_albaranes.md` §2–§4 y el código de esa rama
  (`albaran_compra_models.py`, `sql_models.py`, `concepto_grafico_models.py`).
- Árbol limpio al terminar; cada control restaurado byte a byte y comprobado con `git diff --quiet`.

## Controles negativos propios (sv9 entera tras cada uno; todos cazados)

NC1 simulación sigue a la grabación 3 · NC2 grabación con reintentos 5 · NC3/NC13 5xx o estado desconocido en la
grabación → `error` 7/2 · NC4 `idempotente` sin comparar totales 3 · NC5 sin R14 3 · NC6 importe 0 se manda 4 · NC7 sin
`signo_incoherente` 4 · NC8 `incierto` sin la petición guardada 1 · NC9 `COMMIT` sin mayúsculas 4 · NC10
`naturaleza_no_valida` → `no_admitido` 5 · NC11 gana `no_admitido` en líneas 6 · NC12 `en_vuelo` tras grabar 1 · NC14
vinculada con `descripcion` 2 · NC15 partida vacía como `'ALM'` 2 · NC16 precio con signo 1 · NC17 adjunto en
simulación 2 · NC18 la previa no compara partidas 6 (failed sobre 430).

## Lo que se miró con especial cuidado (conforme salvo lo que se dice)

- **Nada graba sin `ALTA_SIGRID_COMMIT=true`**: solo dos escrituras, `alta_albaran(commit=True)` (`alta_sigrid_service.py:267`,
  tras el corte de simulación de :258) y `concepto-grafico` (solo `ModoAlta.REAL`, :314 y :375); real solo con el
  literal `true`. Una previa que no responde `previsto` nunca graba (protege también ante un sigrid-api sin F-009).
- **Grabación única**: `_post` sin tenacity, cliente nuevo, 240 s; 5xx/tiempo/conexión/200 ilegible/estado desconocido
  ⇒ `incierto`; `previsto` ⇒ `error`. El `incierto` se retoma con la petición guardada (idempotencia por `synckey` bajo
  applock) y se comparan totales por `referencia_linea` (`registrado_distinto`, también con `creado`).
- **Duplicados**: SQL de R14 idéntica a la del contrato §7, `NO_TOLERA truncado`; `FOR UPDATE OF m` más el estado
  hacen que una segunda entrega con `en_curso` dentro de la Espera se ignore.
- **Validación local**: solo líneas con importe ≠ 0; vinculada sin importe fuera; signos opuestos ⇒ `revisar` sin
  llamadas; sin partida = sin clave. La petición casa con el Pydantic real (`extra="forbid"`, `strict`, nulos omitidos);
  nunca `naturaleza`, `almacen`, `paride` ni `lineas_recibidas`.
- **Clasificador**: igual a design §2 y a los `CODIGOS_CABECERA`/`CODIGOS_LINEA` del código de F-009 (18 + 10). Línea
  repetida en `details.lineas`: un motivo por entrada y gana `error`. `lineas[].producto` nulo no se lee;
  `precio_distinto_del_contrato` informativo.
- **DDL (desviación 1): favorable.** sv3 aplica `apply_phase2_ddl` al arrancar la API (`app.py:109`) y el worker
  (`composition.py:74`); `schema_contribution` solo exporta (incluye `_PHASE2_DDL` y la tabla en `owned_tables`); un
  fallo se registra sin tumbar sv3. sv6 aplica su `schema_contribution`. Con DESDE vacía sv9 no reclama: el orden de
  design §8 (sv6 y sv3 → sv9 → sv4 → DESDE) es seguro.
- **Desviaciones 2–14 del implementer: aceptadas** (la 8, condicionada a D2).

## Hallazgos

**H1 · MEDIA · secretos en el log de arranque (R35, C3).** `main_worker.py:48-51` registra
`logger.error("... %s", exc)` con el `ValidationError` de `Settings`. Pydantic vuelca el diccionario de entrada en
`input_value=`. Lo reproduje con valores ficticios, quitando `GRAPH_KEY`:
`Field required [type=missing, input_value={'SIGRID_API_BASE_URL': '..._PASSWORD': 'PGSECRETO'}`. Por ese camino
`PG_PASSWORD`, `GRAPH_KEY` o `SIGRID_API_FUNCTION_KEY` (según qué variables falten y cuáles haya) acaban en Log
Analytics. Ningún otro servicio hace esto: es nuevo de sv9.

**H2 · BAJA-MEDIA · el adjunto lee un campo que sigrid-api no devuelve.** `sigrid_api_alta_client.py:255-256` lee
`grafico.ide`, pero `AttachConceptoGraficoResponse.grafico` (`GraficoPreview`, `13fd99d`) solo trae
`ide_documental` e `ide_negocio`. Consecuencia: `sigrid_gra_ide` quedará siempre `NULL`. Los tests
(`test_f053_cliente_sigrid.py:276`, `:292`) usan una forma inventada, así que no lo detectan.

**H3 · BAJA · la entrada de F-053 en `features.json` no tiene `branch`.** Por eso
`python -m harness.rutas_sensibles --puerta` sale `N/A (sin feature en curso con rama...)`; F-051 sí lo lleva.
El diff no toca rutas sensibles (C4 ter N/A), pero la puerta de cierre (T30) debe funcionar sola.

**O1 · observación.** La cola tiene una visibilidad de 600 s y el peor caso de un mensaje ronda los 13 min: tres
reintentos de lectura y de previa de 60 s, 240 s de grabación y el adjunto. Si un mensaje acaba en `error` o
`revisar` después de los 600 s, la segunda entrega vuelve a procesarlo (`_REPETIBLES`). No duplica nada (el `error`
deja el ERP intacto e intervienen la idempotencia y el applock), pero relaja «una sola vez». Se arregla pasando
`visibilidad_s` a `ejecutar_worker` por encima del peor caso. Puede ir en esta pasada o en T22.

## Cambios requeridos

1. `services/albaranes-alta-sigrid/main_worker.py:48-51`: registrar `[(e["loc"], e["msg"]) for e in
   exc.errors(include_input=False)]` en vez de `exc` (conserva el motivo de R44). Test con `caplog` y secretos
   ficticios en el entorno: ninguno en el log, el motivo del mapeo sí. Control negativo: volver a `exc` ⇒ falla.
2. `sigrid_api_alta_client.py:255-256`: leer `grafico.ide_negocio` (el `gra` de negocio que enlaza `rcg`; si se
   prefiere el documental, que se justifique) y ajustar los tests de `concepto-grafico` a la forma real de
   `AttachConceptoGraficoResponse` en `13fd99d`, citando el fichero.
3. `harness/features.json`: añadir `"branch": "feature/F-053-alta-sigrid"` a F-053, regenerar `BACKLOG.md` con
   `python harness/backlog.py` y comprobar que `python -m harness.rutas_sensibles --puerta --base dev` deja de salir
   N/A por falta de rama.

## Checkpoints (contra el alcance de la fase 1)

- C1 · N/A justificado: `init.sh` en el worktree no es exigible en esta review intermedia (decisión del humano, como
  en F-049). Lo sustituyen las 5 suites y la cobertura de arriba. Se exige en T30. Los ficheros del arnés existen.
- C2 · [x] Solo F-053 `in_progress`; rama `feature/F-053-alta-sigrid`; `current.md` al día; F-051 `blocked`.
- C3 · [ ] Hexagonal [x] (el dominio solo importa los puros de comun), primera línea [x], sin prints [x],
  dependencias previstas [x] (httpx, tenacity, sqlalchemy y psycopg, que ya estaban en el venv). **Sin secretos:
  [ ] por H1.** Trampas del monorepo: (1) [x] solo lee tablas merge; (2) [x] `producto_sigrid` declara sus lectores
  (sv4 y sv9; sv5 no la lee) y el test de drift del ORM está en verde; (3) [x] la cantidad de una vinculada es la
  convertida por sv6; las sintéticas entran si tienen importe y van al final por `id` (H26).
- C3 bis · N/A: no toca `docs/referencia/`.
- C4 · [x] Cada requisito de la fase tiene tests `test_f053_rN_*` y todos pasan (tabla abajo). Sin red ni BBDD
  (fakes, `MockTransport` y sesión simulada). MANUAL T0b, T0c y T0 con su comando en el informe §8 y en
  `current.md`. T14 contra PostgreSQL real queda para T26.
- C4 bis · [x] `rigor` declarado. [x] Fase RED con la salida real por tarea (informe §6). [x] Cobertura 96,1 %
  medida por mí. Mutación, RM1–RM6 y supervivientes: **N/A justificado** porque la campaña es T25, fuera de esta fase
  por encargo del líder; al cierre se exige completa, con cero supervivientes. [x] «Evidencias» presente, con el
  número de workers N/A por no haber campaña.
- C4 ter · N/A: el diff no toca rutas de `harness/rutas_sensibles.json` (comprobado a mano; la puerta no resuelve, H3).
- C5 · [x] Un commit `F-053 Tn:` por tarea (T0a, T1, T2, T2b, T3–T16) y `[x]` en `tasks.md`. T0d sigue `[ ]` con
  motivo: su verificación es `init.sh`. [x] Sin temporales trackeados (los `coverage.json` están ignorados).
  [x] `features.json` coherente.

## Cobertura requisito → tests (fase 1; R1–R4, R25–R27, R29–R31, R37, R40, R41 son de sv4, T17+)

R5 5 · R6 3 · R7 4 · R8 2 · R9 5 (`servicio_entrada`, `servicio_real`) · R10 19 · R11 3 · R12 21 · R13 2 · R39 7 · R43 1
(`validador`) · R14 4 · R15 12 (duplicados, comparador, clasificador) · R16 1 · R17 15 · R18 21 · R19 5 · R20 10 · R21 2
· R22 8 · R23 4 · R24 8 · R28 9 · R33 12 · R35 3 · R32 5 y R38 13 (comun) · R34 1 y R36 9 (sv3/sv6) · R42 2 (sv6) · R44 7.

## Decisiones para el humano (no bloquean esta fase)

- **D1 · el reingreso en sv3 borra el alta.** `sqlalchemy_albaran_repository._delete_existing_records`, llamado al
  persistir de nuevo un PDF con el mismo `source_sha256`, borra el merge aunque esté aprobado. El FK
  `ON DELETE CASCADE` de design §6 se lleva por delante la fila del alta, también si está `registrado`, y el documento
  vuelve como nuevo, con otro id. La red de seguridad funciona: R14 lo detectaría como `ya_en_sigrid` en la
  reaprobación. Pero se pierde el rastro de lo grabado. Hay tres opciones: aceptarlo; `ON DELETE RESTRICT` o sin FK
  (choca con la purga de sv4, R27); o que sv3 no borre un merge con un alta bloqueante (sería un cambio de sv3 fuera
  de la fase 1).
- **D2 · desviación 8 del implementer.** Una línea casada con una línea de otro contrato distinto del de la
  valoración se manda como «sin vincular», con producto genérico, sin dar ningún motivo. La previa no lo detecta,
  porque el total y la partida coinciden. ¿Se acepta en silencio, como ya hace la medición, o se prefiere `revisar`
  con un motivo?

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C3 podría pedir explícitamente que los `ValidationError` de configuración se registren sin
`input_value`. Es el mismo patrón que ya trata `function_app.py` de sigrid-api y vale para cualquier proyecto (arnes-base).
