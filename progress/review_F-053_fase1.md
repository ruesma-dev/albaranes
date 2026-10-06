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
- `harness.tamano`: dentro de los topes. `ruff check .` desde sv9: limpio. Desde la raíz salen 19 I001, que son un
  artefacto de configuración. Primera línea con la ruta en los 40 ficheros nuevos; sin `print`.
- Contrato F-009 v8.2 (`13fd99d`, solo lectura con `git show`, nada editado). Coteja con `contrato_albaranes.md`
  §2–§4 y además con el código vivo de esa rama: `albaran_compra_models.py`, `sql_models.py` y
  `concepto_grafico_models.py`.
- Árbol limpio al terminar (`git status --porcelain` vacío). Los controles se restauraron byte a byte, comprobado con
  `git diff --quiet` después de cada uno.

## Controles negativos propios (sv9 entera tras cada uno; todos cazados)

| # | Qué rompí | Resultado |
|---|---|---|
| NC1 | La simulación sigue hasta la grabación (sin el `return` de R19) | 3 failed |
| NC2 | La grabación con `_post_con_reintentos` | 5 failed |
| NC3 / NC13 | 5xx o estado desconocido en la grabación → `error` en vez de `incierto` | 7 / 2 failed |
| NC4 | `idempotente` sin comparar totales (R15) | 3 failed |
| NC5 | Sin buscar altas a mano (R14) | 3 failed |
| NC6 / NC7 | Se manda una línea de importe 0 (R13) / sin `signo_incoherente` (R39) | 4 / 4 failed |
| NC8 | Un `incierto` no reenvía la petición guardada | 1 failed |
| NC9 | `ALTA_SIGRID_COMMIT` sin distinguir mayúsculas (`True` sería real) | 4 failed |
| NC10 / NC11 | `naturaleza_no_valida` → `no_admitido` / en `lineas_no_validas` gana `no_admitido` | 5 / 6 failed |
| NC12 | `en_vuelo` marcado después de la grabación (R9) | 1 failed |
| NC14 / NC15 / NC16 | Vinculada con `descripcion` (H7) / partida vacía mandada como `'ALM'` / precio con signo | 2 / 2 / 1 failed |
| NC17 / NC18 | Adjunto también en simulación / la previa no compara partidas | 2 / 6 failed |

## Lo que se miró con especial cuidado (conforme salvo lo que se dice)

- **Nada graba sin `ALTA_SIGRID_COMMIT=true`.** Solo hay dos escrituras en el ERP: `alta_albaran(commit=True)`
  (`alta_sigrid_service.py:267`, después del corte de simulación de la :258) y `concepto-grafico`, que solo se llama
  con `ModoAlta.REAL` (:314, :375). Solo el literal `true` activa el modo real; una variable vacía vale su defecto.
  Además, una previa que no responde `previsto` no llega a grabar: también protege si sv9 se apunta por error a un
  sigrid-api sin F-009.
- **Grabación única.** La grabación usa `_post` con un cliente nuevo, sin tenacity y con un timeout de 240 s. Los
  5xx, el tiempo agotado, los fallos de conexión, un 200 ilegible o un estado desconocido llevan a `incierto`.
  `previsto` en la grabación lleva a `error`, porque sigrid-api declara que no escribió. El `incierto` se retoma tras
  la Espera con la petición guardada, y la idempotencia (`synckey` bajo applock) devuelve `idempotente`. Se comparan
  los totales por `referencia_linea` y lo distinto queda en `registrado_distinto`, también si vuelve `creado`.
- **Duplicados.** La SQL de R14 es idéntica a la del contrato §7 y lleva `NO_TOLERA truncado`. La reclamación hace
  `FOR UPDATE OF m` sobre el merge y además guarda el estado, así que una segunda entrega con `en_curso` dentro de la
  Espera se ignora.
- **Validación local.** Solo se mandan las líneas con importe ≠ 0. Una vinculada sin importe no se manda. Signos
  opuestos llevan a `revisar` sin llamar a nadie. Sin partida = ninguna clave `partida`. La petición casa con el
  modelo Pydantic real: `extra="forbid"`; `strict` en cantidad, precio, ints y fecha; las claves nulas no se mandan;
  `referencia_linea` = `str(id)`. No se mandan `naturaleza`, `almacen`, `paride` ni `lineas_recibidas`.
- **Clasificador.** Coincide con la tabla de design §2 y con los `CODIGOS_CABECERA`/`CODIGOS_LINEA` del código de
  F-009: 17 + 1 códigos de cabecera y 10 de línea. Una misma línea repetida en `details.lineas` da un motivo por
  entrada, y gana `error`. Un `lineas[].producto` nulo no se lee. `precio_distinto_del_contrato` es informativo,
  porque el defecto solo bloquea `producto_sin_historico`.
- **DDL (desviación 1): dictamen favorable.** sv3 aplica `apply_phase2_ddl` al arrancar la API (`app.py:109`) y el
  worker (`composition.py:74`). `schema_contribution` solo exporta (lo usaba sv7) e incluye `_PHASE2_DDL` y la tabla
  en `owned_tables`. El fallo se registra y no tumba sv3. sv6 sí aplica su `schema_contribution` (el ALTER va ahí).
  Orden de despliegue: con DESDE vacía sv9 no llega a reclamar, así que el orden de design §8 (sv6 y sv3 → sv9 →
  sv4 → DESDE) es seguro.
- **Las demás desviaciones (2–14) de §4 del informe del implementer: aceptadas.** La 8 queda condicionada a D2.

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
Mirado a mano, el diff no toca ninguna ruta sensible, así que C4 ter es N/A esta vez, pero la puerta de cierre
(T30) tiene que funcionar sola.

**O1 · observación.** La cola tiene una visibilidad de 600 s y el peor caso de un mensaje ronda los 13 min: tres
reintentos de lectura y de previa de 60 s, 240 s de grabación y el adjunto. Si un mensaje acaba en `error` o
`revisar` después de los 600 s, la segunda entrega vuelve a procesarlo (`_REPETIBLES`). No duplica nada (el `error`
deja el ERP intacto e intervienen la idempotencia y el applock), pero relaja «una sola vez». Se arregla pasando
`visibilidad_s` a `ejecutar_worker` por encima del peor caso. Puede ir en esta pasada o en T22.

## Cambios requeridos

1. `services/albaranes-alta-sigrid/main_worker.py:48-51`: no registrar `str(exc)`. Registrar
   `[(e["loc"], e["msg"]) for e in exc.errors(include_input=False)]`, que conserva el motivo de R44 sin los valores.
   Añadir un test con `caplog` que fije secretos ficticios en el entorno, provoque el fallo de configuración y
   compruebe que ninguno aparece en el log y que el motivo del mapeo sí. Control negativo: volver a `%s, exc` → el
   test falla.
2. `sigrid_api_alta_client.py:255-256`: leer `grafico.ide_negocio` (el `gra` de negocio que enlaza `rcg`; si se
   prefiere el documental, que se justifique) y ajustar los tests de `concepto-grafico` a la forma real de
   `AttachConceptoGraficoResponse` en `13fd99d`, citando el fichero.
3. `harness/features.json`: añadir `"branch": "feature/F-053-alta-sigrid"` a F-053, regenerar `BACKLOG.md` con
   `python harness/backlog.py` y comprobar que `python -m harness.rutas_sensibles --puerta --base dev` deja de salir
   N/A por falta de rama.

## Checkpoints (contra el alcance de la fase 1)

- C1 · N/A justificado: `init.sh` en el worktree no es exigible en esta review intermedia (decisión del humano, como
  en F-049). Lo sustituyen las 5 suites y la cobertura de arriba. Se exige en T30. Los ficheros del arnés existen.
- C2 · [x] Solo F-053 está `in_progress`; la rama es `feature/F-053-alta-sigrid`; `current.md` está al día; F-051
  sigue `blocked` y no `done`.
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
- C4 ter · N/A: el diff no toca ninguna ruta de `harness/rutas_sensibles.json`. Comprobado a mano, porque la puerta
  no resuelve la feature (H3).
- C5 · [x] Un commit `F-053 Tn:` por tarea (T0a, T1, T2, T2b, T3–T16) y `[x]` en `tasks.md`. T0d sigue `[ ]` con
  motivo: su verificación es `init.sh`. [x] Sin temporales trackeados (los `coverage.json` están ignorados).
  [x] `features.json` coherente.

## Cobertura requisito → tests (fase 1; R1–R4, R25–R27, R29–R31, R37, R40, R41 son de sv4, T17+)

| Req | Tests (nº) | Req | Tests (nº) | Req | Tests (nº) |
|---|---|---|---|---|---|
| R5 | `servicio_entrada` (5) | R14 | `servicio_duplicados` (4) | R23 | `servicio_real` (4) |
| R6 | ídem (3) | R15 | duplicados, comparador, clasificador (12) | R24 | `cliente_sigrid` (8) |
| R7 | ídem (4) | R16 | `servicio_previa` (1 + R35) | R28 | `servicio_anulacion` (9) |
| R8 | ídem (2) | R17 | comparador, previa (15) | R32 | comun (5) |
| R9 | entrada, real (5) | R18 | clasificador, previa (21) | R33 | cliente (12) |
| R10 | `validador` (19) | R19 | previa, esqueleto (5) | R34 | sv3 `no_escribe` (1) |
| R11 | ídem (3) | R20 | real, clasificador (10) | R35 | cliente, previa (3) |
| R12 | ídem (21) | R21 | ídem (2) | R36 | sv3 y sv6 DDL (9) |
| R13 | ídem (2) | R22 | real, cliente (8) | R38 | comun (13) |
| R39 | validador, duplicados (7) | R42 | sv6 (2) | R43 / R44 | validador (1) / settings y comun (7) |

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
