<!-- specs/F-011-evals-ia/requirements.md -->
# F-011 · Evals de IA con ground truth y puerta en el arnés — Requisitos

Notación EARS. Cada R se traduce a >= 1 test (`test_f011_rN_*`). Los términos
«fixture», «informe de evals», «rutas sensibles» y «puerta» se definen en
`design.md`. Contrato de datos de partida: `evals/README.md` (5 libros Excel
en `evals/ground_truth/`, sin versionar; albaranes de entrada en
`evals/inputs/albaranes/`, sin versionar).

## A. Conversor xlsx → fixtures JSON (alcance punto 1)

- **R1.** CUANDO se ejecuta `python -m evals.conversor`, el sistema debe leer
  los 5 libros de `evals/ground_truth/` (`IA1_extraccion`, `IA2_contexto`,
  `IA3_valoracion`, `IA4_conciliacion`, `INPUTS`) y generar en
  `evals/fixtures/` un fichero JSON por caso y fase (más los inputs de
  IA3/IA4), versionables en git.

- **R2.** El conversor debe aplicar los convenios de celda del contrato de
  datos: celda vacía → el eval espera `null`; celda `?` → ese campo NO se
  compara (sentinela explícito en el fixture, no ausencia silenciosa); fechas
  en `AAAA-MM-DD`; `descuentos` como lista separada por `;`.

- **R3.** El conversor debe localizar las tablas de cada pestaña por su fila
  de título (`TABLA 1 —`, `TABLA 2 —`, `TABLA 3 —`; en `INPUTS`, el título
  único de cada pestaña), tolerando filas en blanco de separación y pestañas
  de tipología sin casos (solo cabeceras → cero casos, sin error).

- **R4.** SI el barrido de datos sensibles integrado detecta en el contenido
  a convertir algún patrón prohibido (correos, IPs, GUIDs de suscripción o
  tenant, credenciales, tokens, cadenas tipo clave — los patrones de C3 bis
  de `CHECKPOINTS.md`), ENTONCES el conversor debe abortar SIN escribir
  ningún fixture y listar libro, pestaña, celda y patrón de cada hallazgo.
  El barrido es parte del conversor, no un paso manual posterior.

- **R5.** El conversor debe producir salida determinista: el mismo Excel
  produce byte a byte el mismo JSON (claves ordenadas, UTF-8, sin
  timestamps; los metadatos de trazabilidad usan el sha256 del libro origen,
  que es estable).

- **R6.** SI falta alguno de los 5 libros, o una pestaña declarada en el
  contrato de datos, ENTONCES el conversor debe fallar con mensaje que
  identifique el fichero o pestaña ausente, sin escribir fixtures parciales.

## B. Runner de evals (alcance punto 2)

- **R7.** CUANDO se ejecuta `python -m evals.runner --fases <lista>`, el
  sistema debe evaluar las fases pedidas contra los fixtures de
  `evals/fixtures/` y escribir el informe de evals (ver R12). Para IA3/IA4 el
  modo por defecto es `determinista`; el modo `real` (llamadas LLM) exige el
  flag explícito `--con-llm`. IA1/IA2 solo existen en modo real y por tanto
  exigen siempre `--con-llm`.

- **R8.** El runner debe evaluar IA1/IA2 invocando la extracción real de sv2
  (fase 1 y fase 2, con el preprocesado de material que usa sv2 en
  producción) sobre los ficheros de `evals/inputs/albaranes/`, por cada
  proveedor solicitado, y comparar el resultado contra el fixture aplicando
  los convenios de R2. NUNCA se invoca desde `harness/init.sh`.

- **R9.** SI el fichero de albarán de un caso de IA1/IA2 no existe en
  `evals/inputs/albaranes/` (no se versiona), ENTONCES el runner debe marcar
  el caso como OMITIDO con su motivo, continuar con el resto y listar los
  omitidos en el informe.

- **R10.** El runner en modo determinista de IA3/IA4 debe ejercitar las redes
  deterministas de sv6 (builder, matcher de partidas, conversor de unidades,
  calculadora de importes, reconciliador de precios, vetos) SIN NINGUNA
  llamada de red ni BBDD: el papel de la IA se estimula con una propuesta
  construida desde el propio ground truth (matches de TABLA 1 + sintéticas
  esperadas de TABLA 2 + sintéticas PROHIBIDAS de TABLA 3 inyectadas como si
  la IA las hubiera propuesto), y se asserta que las redes vetan las
  prohibidas, conservan las esperadas y producen partidas, importes y flags
  de revisión esperados.

- **R11.** El runner en modo real de IA3/IA4 debe construir el contexto de
  valoración desde los fixtures de `INPUTS` (líneas de albarán, líneas de
  contrato, condiciones) e invocar los servicios LLM de sv5 directamente con
  ese contexto, sin BBDD ni SharePoint. SI las claves LLM necesarias no están
  en el entorno, ENTONCES debe fallar con mensaje claro ANTES de consumir
  ningún caso.

- **R12.** CUANDO una corrida termina, el runner debe escribir el informe
  `progress/evals_F-XXX.md` (con `--feature F-XXX`; sin feature,
  `progress/evals_manual.md`) con: fecha, commit HEAD, modo, fases
  ejecutadas, proveedores invocados, tabla por caso (VERDE/ROJO/OMITIDO y
  discrepancias campo a campo), totales por fase y una línea de veredicto
  final parseable (`VEREDICTO: VERDE|ROJO|NO_EVALUABLE`).

- **R13.** El runner debe salir con código 0 si el veredicto es VERDE, 1 si
  es ROJO y 2 si es NO_EVALUABLE (sin casos para alguna fase pedida, claves
  ausentes en modo real, fixtures inexistentes).

- **R14.** El runner debe ejecutar los casos en secuencia estricta (el
  pipeline es secuencial por documento): sin hilos, sin asyncio concurrente,
  sin pools.

- **R15.** SI una fase pedida no tiene ningún caso en los fixtures (libros
  aún sin rellenar), ENTONCES el veredicto de la corrida debe ser
  NO_EVALUABLE (nunca VERDE): un informe sin casos no es evidencia.

## C. Puerta del arnés (alcance punto 3)

- **R16.** El sistema debe declarar las rutas sensibles en
  `harness/rutas_sensibles.json` (declaración a mano, patrón de
  `harness/servicios.json`): una o más verificaciones, cada una con nombre,
  comando sugerido, plantilla de informe, exigencia (`bloqueo` | `aviso`) y
  lista de rutas (glob relativo a la raíz + fases exigidas + motivo). La
  declaración inicial cubre: prompts YAML y reglas de revisión de sv2 y sv5,
  schemas Pydantic (`domain/models/`) de sv2 y sv5, clientes LLM y
  `json_coercion` (en `ruesma_comun/llm/` y en `infrastructure/llm/` de sv2
  y sv5), redes deterministas de sv6 (`application/services/`,
  `domain/models/` y `config/unit_registry.yaml`).

- **R17.** CUANDO se ejecuta `python -m harness.rutas_sensibles --validar`,
  el sistema debe validar la declaración (JSON bien formado, campos
  obligatorios, sin nombres duplicados, y cada patrón casa con >= 1 fichero
  existente del repositorio) y salir 0 solo si es sana.

- **R18.** MIENTRAS no exista `harness/rutas_sensibles.json`, el arnés no
  debe cambiar de comportamiento: la sección nueva de `init.sh` se salta por
  completo (regla de oro de `harness/servicios.py`).

- **R19.** SI `harness/rutas_sensibles.json` existe pero es inválido,
  ENTONCES `bash harness/init.sh` debe terminar en KO: la declaración rota
  no degrada en silencio a «sin puerta».

- **R20.** CUANDO `init.sh` corre con declaración presente y hay una feature
  `in_progress` con rama, la puerta debe calcular el diff de la feature
  contra la rama base reutilizando `harness/alcance.py` (resolución de
  referencias y parseo del diff, SIN el filtro de solo-Python: los prompts
  YAML también cuentan) y cotejar los ficheros tocados contra los patrones
  declarados.

- **R21.** SI el diff toca rutas sensibles y el informe de evals de la
  feature no existe, no cubre todas las fases exigidas por las rutas
  tocadas, o su veredicto no es VERDE, ENTONCES la puerta debe fallar
  ([KO] con exigencia `bloqueo`; [AVISO] con exigencia `aviso`) imprimiendo
  las rutas tocadas, las fases exigidas y el comando exacto para lanzar los
  evals.

- **R22.** SI el diff no toca ninguna ruta sensible, o no hay feature en
  curso con rama, ENTONCES la puerta debe declararse N/A en [OK] con el
  motivo impreso (patrón de la puerta de cobertura).

- **R23.** La puerta NUNCA ejecuta los evals (ni siquiera el modo
  determinista): solo comprueba el informe. La frescura del informe (que su
  commit pertenezca a la rama y sea posterior al último cambio de rutas
  sensibles) la verifica el reviewer según el bloque nuevo de
  `CHECKPOINTS.md`.

## D. Propagación a arnes-base (alcance punto 4)

- **R24.** El mecanismo genérico —`harness/rutas_sensibles.py`, un
  `harness/rutas_sensibles.ejemplo.json`, la sección de `init.sh` y el
  párrafo genérico de `CHECKPOINTS.md`— debe portarse a
  `C:\Users\pgris\PycharmProjects\arnes-base` en esta misma feature (commit
  local allí; push lo hace el humano). Lo específico de albaranes (la
  declaración real de rutas, el runner de evals) NO se porta.

## E. Transversales

- **R25.** Los tests unitarios de F-011 no deben tocar red, BBDD ni APIs
  LLM: clientes falsos, ejecutor de git inyectado (patrón `EjecutorGit` de
  `harness/alcance.py`) y libros Excel sintéticos construidos en el test.
  Todo fichero de código nuevo lleva su ruta relativa en la primera línea y
  todo el contenido en español.

## Preguntas abiertas (validar el humano antes de implementar)

- **P1 — Precios de proveedor en los fixtures.** `CLAUDE.md` cita «precios de
  proveedor» como dato sensible, pero el ground truth de IA3 ES
  esencialmente precios; `evals/README.md` ya decidió versionar los fixtures
  tras el barrido C3 bis (que no cubre precios). Propuesta: los precios y
  razones sociales/CIF se quedan en los fixtures (repo privado, son el
  ground truth); el barrido bloquea solo los patrones C3 bis. ¿Confirmado?
- **P2 — Proveedores que cuentan para el verde de IA1/IA2.** sv2 llama a 3
  proveedores. Propuesta: por defecto el runner invoca solo el proveedor
  primario de cada fase (los `IA_PRIMERA_FASE`/`IA_SEGUNDA_FASE` de sv2) y
  `--proveedores` permite ampliarlo; el veredicto se calcula sobre los
  proveedores invocados en esa corrida. ¿De acuerdo, o el verde exige los 3?
- **P3 — Umbral de verde.** Propuesta: 100 % de los campos comparados de
  todos los casos ejecutados (los `?` ya dan margen caso a caso). ¿Se acepta,
  o se quiere tolerancia porcentual por fase?
- **P4 — Exigencia inicial de la puerta.** Los 5 libros están hoy SIN casos:
  con exigencia `bloqueo`, cualquier feature que toque prompts (F-002…F-006)
  quedaría bloqueada hasta que se rellenen. Propuesta: arrancar la
  declaración con `"exigencia": "aviso"` y subirla a `bloqueo` cuando haya
  ground truth; el cambio es una línea del JSON. ¿Valor inicial?
- **P5 — Dependencias del runner en el venv raíz.** Los servicios no
  declaran venv propio en `harness/servicios.json` (todo corre con el venv
  raíz), al que faltan dependencias que el runner necesita para importar
  sv2/sv6 (PyYAML, pydantic-settings, PyMuPDF, opencv-headless, numpy).
  Propuesta: `evals/requirements.txt` con esas dependencias, instalado en el
  venv raíz y documentado en `evals/README.md`. ¿Confirmado?
