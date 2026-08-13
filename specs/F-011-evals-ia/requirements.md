<!-- specs/F-011-evals-ia/requirements.md -->
# F-011 · Evals de IA con ground truth y puerta en el arnés — Requisitos

Notación EARS. Cada R se traduce a >= 1 test (`test_f011_rN_*`). Los términos
«fixture», «pasada completa», «informe de evals», «rutas sensibles»,
«criticidad» y «puerta» se definen en `design.md`. Contrato de datos de
partida: `evals/README.md` — **6 libros** Excel en `evals/ground_truth/`
(`IA1_extraccion`, `IA2_contexto`, `IA3_valoracion`, `IA4_conciliacion`,
`INPUTS` y el maestro `RESULTADO_FINAL`), sin versionar; albaranes de entrada
en `evals/inputs/albaranes/`, sin versionar.

## A. Conversor xlsx → fixtures JSON (alcance punto 1)

- **R1.** CUANDO se ejecuta `python -m evals.conversor`, el sistema debe leer
  los 6 libros de `evals/ground_truth/` y generar en `evals/fixtures/` un
  fichero JSON por caso para cada libro que lo mencione (fases IA1–IA4,
  inputs de IA3/IA4 y resultado final extremo-a-extremo), versionables en
  git.

- **R2.** El conversor debe aplicar los convenios de celda del contrato de
  datos: celda vacía → el eval espera `null`; celda `?` → ese campo NO se
  compara (sentinela explícito en el fixture, no ausencia silenciosa); el
  literal `REVISIÓN` en precio o partida de `RESULTADO_FINAL` → sentinela
  «se espera que el sistema deje ese valor a revisión humana» (resultado
  esperado legítimo, no un hueco); fechas en `AAAA-MM-DD`; `descuentos` como
  lista separada por `;`; decimales con coma o punto.

- **R3.** El conversor debe localizar las tablas de cada pestaña por su fila
  de título (`TABLA 1 —`, `TABLA 2 —`, `TABLA 3 —`; en `INPUTS`, el título
  único de cada pestaña), tolerando filas en blanco de separación y pestañas
  de tipología sin casos (solo cabeceras → cero casos, sin error).

- **R4.** SI el barrido de datos sensibles integrado detecta en el contenido
  a convertir algún patrón prohibido (correos, IPs, GUIDs de suscripción o
  tenant, credenciales, tokens, cadenas tipo clave — los patrones de C3 bis
  de `CHECKPOINTS.md`), ENTONCES el conversor debe abortar SIN escribir
  ningún fixture y listar libro, pestaña, celda y patrón de cada hallazgo.
  El barrido es parte del conversor, no un paso manual posterior. Precios,
  razones sociales y CIF NO son patrones del barrido: son el ground truth
  (decisión D1).

- **R5.** El conversor debe producir salida determinista: el mismo Excel
  produce byte a byte el mismo JSON (claves ordenadas, UTF-8, sin
  timestamps; los metadatos de trazabilidad usan el sha256 del libro origen,
  que es estable).

- **R6.** SI falta alguno de los 6 libros, o una pestaña declarada en el
  contrato de datos, ENTONCES el conversor debe fallar con mensaje que
  identifique el fichero o pestaña ausente, sin escribir fixtures parciales.

## B. Comparación y criticidad

- **R7.** El comparador debe clasificar cada campo comparado por criticidad
  según la configuración versionada `evals/criticidad.json`, ajustable campo
  a campo: discrepancia en campo **crítico** (por defecto: partida final /
  `codigo_partida`, cantidades, precios, importes y códigos — producto,
  obra, contrato, CIF, LER…) → **FALLO** del caso; discrepancia en campo
  **laxo** (por defecto: `descripcion` y comentarios) → **AVISO**, que no
  falla el caso pero consta en el informe. El convenio `?` sigue excluyendo
  un campo caso a caso, por encima de la criticidad.

- **R8.** SI un campo aparece en los fixtures y no está clasificado en
  `evals/criticidad.json` ni cubierto por sus valores por defecto, ENTONCES
  el comparador debe tratarlo como crítico e incluir un aviso de campo sin
  clasificar en el informe: la omisión no relaja nada.

## C. Runner de evals (alcance punto 2)

- **R9.** CUANDO se ejecuta `python -m evals.runner --con-llm`, el sistema
  debe ejecutar la **pasada completa**: las CUATRO fases (IA1, IA2 contra la
  extracción real de sv2; IA3, IA4 contra los servicios LLM reales de sv5)
  MÁS el eval extremo-a-extremo contra `RESULTADO_FINAL` (salida final del
  pipeline de valoración: IA3 + IA4 + build determinista de sv6). La pasada
  no se trocea por fase: la contención de coste está en CUÁNDO se lanza
  (puerta o petición del humano), no en cuánto ejecuta (decisión D2).
  NUNCA se invoca desde `harness/init.sh`.

- **R10.** CUANDO se ejecuta `python -m evals.runner` sin `--con-llm`, el
  sistema debe ejecutar el modo **determinista** (sin ninguna llamada LLM ni
  de red): las redes de sv6 para IA3/IA4 y el extremo-a-extremo con
  propuesta estimulada (ver R13). SI se piden IA1/IA2 o la pasada completa
  sin `--con-llm`, ENTONCES debe rechazarlo con mensaje claro: el gasto en
  LLM siempre es explícito.

- **R11.** En IA1/IA2 el runner debe invocar por defecto solo el proveedor
  primario de cada fase (los `IA_PRIMERA_FASE` / `IA_SEGUNDA_FASE` de sv2),
  ampliable con `--proveedores`; el veredicto se calcula sobre los
  proveedores invocados en esa corrida (decisión D3, del líder, revisable).
  El material se preprocesa igual que en producción y la comparación aplica
  R2 y la criticidad de R7.

- **R12.** SI el fichero de albarán de un caso no existe en
  `evals/inputs/albaranes/` (no se versiona), ENTONCES el runner debe marcar
  el caso como OMITIDO con su motivo, continuar con el resto y listar los
  omitidos en el informe.

- **R13.** El modo determinista debe ejercitar las redes deterministas de
  sv6 (builder, matcher de partidas, conversor de unidades, calculadora de
  importes, reconciliador de precios, vetos) estimulando el papel de la IA
  con una propuesta construida desde el propio ground truth (matches de
  TABLA 1 de IA3 + sintéticas esperadas de TABLA 2 + sintéticas PROHIBIDAS
  de TABLA 3 inyectadas como si la IA las hubiera propuesto) y assertar que
  las redes vetan las prohibidas, conservan las esperadas y producen
  partidas, importes y flags de revisión esperados; y debe comparar además
  el resultado del build contra el fixture de `RESULTADO_FINAL`
  (extremo-a-extremo determinista).

- **R14.** En la pasada completa, el eval extremo-a-extremo debe construir
  el contexto de valoración desde los fixtures de `INPUTS`, invocar IA3 e
  IA4 reales de sv5, pasar el envelope resultante al build determinista de
  sv6 y comparar los records finales (datos generales, líneas impresas con
  su match/partida/precio/origen, y líneas añadidas no impresas) contra el
  fixture de `RESULTADO_FINAL`, aplicando criticidad (R7) y el sentinela
  `REVISIÓN` (R2). SI las claves LLM necesarias no están en el entorno,
  ENTONCES debe fallar con mensaje claro ANTES de consumir ningún caso.

- **R15.** CUANDO una corrida termina, el runner debe escribir el informe
  `progress/evals_F-XXX.md` (con `--feature F-XXX`; sin feature,
  `progress/evals_manual.md`) con: fecha, commit HEAD, modo, fases y
  extremo-a-extremo ejecutados, proveedores invocados, tabla por caso
  (VERDE/ROJO/OMITIDO, fallos críticos y avisos laxos campo a campo),
  totales por fase y una línea de veredicto final parseable
  (`VEREDICTO: VERDE|ROJO|NO_EVALUABLE`). Los libros IA1–IA4 son evals de
  fase: su papel en el informe es localizar en qué fase se rompe lo que el
  extremo-a-extremo detecte.

- **R16.** El runner debe salir con código 0 si el veredicto es VERDE
  (los avisos laxos no lo impiden), 1 si es ROJO y 2 si es NO_EVALUABLE
  (sin casos para alguna parte pedida, claves ausentes en modo real,
  fixtures inexistentes).

- **R17.** El runner debe ejecutar los casos en secuencia estricta (el
  pipeline es secuencial por documento): sin hilos, sin asyncio concurrente,
  sin pools.

- **R18.** SI una parte de la corrida no tiene ningún caso en los fixtures
  (libros aún sin rellenar), ENTONCES el veredicto debe ser NO_EVALUABLE
  (nunca VERDE): un informe sin casos no es evidencia.

## D. Puerta del arnés (alcance punto 3)

- **R19.** El sistema debe declarar las rutas sensibles en
  `harness/rutas_sensibles.json` (declaración a mano, patrón de
  `harness/servicios.json`): una o más verificaciones, cada una con nombre,
  comando sugerido, plantilla de informe, exigencia (`bloqueo` | `aviso`) y
  lista de rutas (glob relativo a la raíz + motivo). La declaración inicial
  cubre: prompts YAML y reglas de revisión de sv2 y sv5, schemas Pydantic
  (`domain/models/`) de sv2 y sv5, clientes LLM y `json_coercion` (en
  `ruesma_comun/llm/` y en `infrastructure/llm/` de sv2 y sv5), y redes
  deterministas de sv6 (`application/services/`, `domain/models/` y
  `config/unit_registry.yaml`), con exigencia inicial `aviso` (decisión D4).

- **R20.** CUANDO se ejecuta `python -m harness.rutas_sensibles --validar`,
  el sistema debe validar la declaración (JSON bien formado, campos
  obligatorios, sin nombres duplicados, y cada patrón casa con >= 1 fichero
  existente del repositorio) y salir 0 solo si es sana.

- **R21.** MIENTRAS no exista `harness/rutas_sensibles.json`, el arnés no
  debe cambiar de comportamiento: la sección nueva de `init.sh` se salta por
  completo (regla de oro de `harness/servicios.py`).

- **R22.** SI `harness/rutas_sensibles.json` existe pero es inválido,
  ENTONCES `bash harness/init.sh` debe terminar en KO: la declaración rota
  no degrada en silencio a «sin puerta».

- **R23.** CUANDO `init.sh` corre con declaración presente y hay una feature
  `in_progress` con rama, la puerta debe calcular el diff de la feature
  contra la rama base reutilizando `harness/alcance.py` (resolución de
  referencias y parseo del diff, SIN el filtro de solo-Python: los prompts
  YAML también cuentan) y cotejar los ficheros tocados contra los patrones
  declarados.

- **R24.** SI el diff toca rutas sensibles y el informe de evals de la
  feature no existe, no corresponde a una pasada completa, o su veredicto no
  es VERDE, ENTONCES la puerta debe fallar ([KO] con exigencia `bloqueo`;
  [AVISO] con exigencia `aviso`) imprimiendo las rutas tocadas y el comando
  exacto para lanzar los evals.

- **R25.** SI el diff no toca ninguna ruta sensible, o no hay feature en
  curso con rama, ENTONCES la puerta debe declararse N/A en [OK] con el
  motivo impreso (patrón de la puerta de cobertura).

- **R26.** La puerta NUNCA ejecuta los evals (ni siquiera el modo
  determinista): solo comprueba el informe. La frescura del informe (que su
  commit pertenezca a la rama y sea posterior al último cambio de rutas
  sensibles) la verifica el reviewer según el bloque nuevo de
  `CHECKPOINTS.md`.

## E. Propagación a arnes-base (alcance punto 4)

- **R27.** El mecanismo genérico —`harness/rutas_sensibles.py`, un
  `harness/rutas_sensibles.ejemplo.json`, la sección de `init.sh` y el
  párrafo genérico de `CHECKPOINTS.md`— debe portarse a
  `C:\Users\pgris\PycharmProjects\arnes-base` en esta misma feature (commit
  local allí; push lo hace el humano). Lo específico de albaranes (la
  declaración real de rutas, el runner de evals, la criticidad) NO se porta.

## F. Transversales

- **R28.** Los tests unitarios de F-011 no deben tocar red, BBDD ni APIs
  LLM: clientes falsos, ejecutor de git inyectado (patrón `EjecutorGit` de
  `harness/alcance.py`) y libros Excel sintéticos construidos en el test.
  Todo fichero de código nuevo lleva su ruta relativa en la primera línea y
  todo el contenido en español.

## Decisiones tomadas (2026-08-13)

Respuestas del humano a las preguntas abiertas de la primera versión de esta
spec; ya incorporadas a los requisitos de arriba.

- **D1 — Precios en fixtures (era P1).** Precios, razones sociales y CIF SE
  VERSIONAN en los fixtures: repo privado y son el ground truth. El barrido
  C3 bis sigue bloqueando sus patrones (GUIDs, IPs, credenciales, correos).
  → R4.
- **D2 — Alcance de una pasada (era P2).** Cada fase tiene su eval y una
  pasada ejecuta LAS CUATRO más el extremo-a-extremo; no se trocea por fase.
  La contención de coste va en el CUÁNDO (puerta por rutas sensibles o
  petición explícita del humano), no en el cuánto. → R9.
- **D3 — Proveedores IA1/IA2 (dentro de P2).** Proveedor primario por
  defecto con opción `--proveedores`; decisión del líder, revisable por el
  humano. → R11.
- **D4 — Criterio de verde (era P3).** Sin umbral porcentual: clasificación
  por criticidad. Campos críticos (partida y valores leídos: cantidades,
  precios, importes, códigos) → discrepancia = FALLO; campos laxos
  (descripcion…) → AVISO. Configuración versionada y ajustable por campo;
  `?` sigue excluyendo caso a caso. → R7, R8.
- **D5 — Exigencia inicial de la puerta (era P4).** Arranca en `aviso`; se
  sube a `bloqueo` cuando haya ground truth rellenado. → R19.
- **D6 — Dependencias del runner (era P5).** `evals/requirements.txt`
  instalado en el venv raíz, documentado en `evals/README.md`.
- **D7 — Libro maestro `RESULTADO_FINAL.xlsx` (nuevo).** Eval
  extremo-a-extremo contra el resultado final que rellena el administrativo
  (datos generales, líneas impresas como deben quedar, líneas añadidas no
  impresas; `REVISIÓN` como resultado esperado legítimo). El conversor lo
  transforma en fixtures y el runner compara contra él la salida final del
  pipeline de valoración; los libros IA1–IA4 quedan como evals de fase para
  localizar dónde falla algo. Misma criticidad de D4. → R1, R2, R13, R14.
