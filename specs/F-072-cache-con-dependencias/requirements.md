<!-- specs/F-072-cache-con-dependencias/requirements.md -->
# F-072 · La caché de suites tiene en cuenta las dependencias de cada servicio

Rigor **critico** (justificación en `design.md` §1). Origen: review de F-070, O1
(`progress/review_F-070.md` de la rama de F-070, §Automejora). Cubre también la
F-028 del taller `arnes-base` y su encargo 1.7.12 (§4, §9 y §10).

**El defecto.** La clave de `.arnes_cache/suite_<nombre>.ok` es solo
`git rev-parse HEAD:<ruta>`. (a) Un commit en `services/albaranes-comun` no
invalida la caché de los servicios que la importan. (b) En un worktree, los
servicios importan la comun editable del árbol principal: `init.sh` dio verde por
caché con sv3, sv4 y sv9 rotos (`ImportError: canonizar_codigo_obra`).

Glosario: **dependencia** = ruta del repositorio declarada en `depende_de`;
**módulo vigilado** = nombre declarado en `importa`; **entrada local** = fichero
no versionado cuya huella entra en la clave; **sonda** = subproceso que pregunta
al intérprete del servicio dónde resuelve cada módulo vigilado.

## A. Esquema de `harness/servicios.json` (`harness/servicios.py`)

- **R1.** El sistema debe aceptar una declaración sin `depende_de`, `importa` ni
  `entradas_no_versionadas` y producir para cada servicio esos tres campos vacíos,
  con la salida de `--shell` y de `--validar` idéntica byte a byte a la de hoy.
- **R2.** CUANDO un servicio declara `depende_de`, el sistema debe cargarlo como
  tupla de rutas relativas a la raíz, normalizadas igual que `ruta` (barras, sin
  barra final), en el orden declarado.
- **R3.** SI `depende_de` no es una lista, o alguno de sus elementos no es un texto
  no vacío, contiene `|`, es una ruta absoluta, tiene un segmento `..`, no existe
  en el repositorio (ni como fichero ni como carpeta) o está repetido, ENTONCES el
  sistema debe fallar con `ValueError` que nombre el servicio, el campo y el valor.
- **R4.** CUANDO un servicio declara `importa`, el sistema debe cargarlo como tupla
  de nombres de módulo; SI algún nombre no tiene forma de identificador de Python
  con puntos (`ruesma_comun`, `pkg.sub`), está repetido, o el servicio no es de
  lenguaje `python`, ENTONCES debe fallar con `ValueError` que lo nombre.
- **R5.** CUANDO un servicio declara `entradas_no_versionadas`, el sistema debe
  cargarlas como tupla de rutas relativas normalizadas, existan o no; SI no son
  lista, o un elemento incumple las reglas de forma de R3 (todas salvo la de
  existencia), ENTONCES debe fallar con `ValueError`.
- **R6.** El sistema debe fallar en `--validar` (código 1, mensaje en stderr) ante
  cualquier error de R3–R5, de modo que `init.sh` lo marque KO como hoy.

## B. Clave de la caché (`harness/cache_suites.py`)

- **R7.** El sistema debe componer la clave de un servicio Python con: una marca de
  formato, el hash en `HEAD` de su ruta, el hash en `HEAD` de cada dependencia, la
  ruta resuelta de su intérprete, el origen resuelto de cada módulo vigilado y la
  huella de cada entrada local. Cambiar cualquiera de esos datos debe cambiar la
  clave; no cambiar ninguno debe reproducirla igual.
- **R8.** La clave debe ser independiente del orden en que se declaren las
  dependencias, los módulos y las entradas locales.
- **R9.** El sistema debe tomar como entradas locales `.env` de la raíz y
  `<ruta>/.env` además de las declaradas, y su huella debe ser nombre, tamaño y
  fecha de modificación, o «ausente» si no existe.
- **R10.** El sistema NO debe leer el contenido de una entrada local: ni el contenido
  ni un digest suyo pueden aparecer en la clave ni en el texto del que se deriva.
- **R11.** SI la ruta del servicio o alguna dependencia tiene cambios sin commitear
  (incluidos ficheros no rastreados), ENTONCES el sistema no debe dar clave (ni se
  sirve ni se guarda) y no debe avisar: es el comportamiento de hoy.
- **R12.** SI la ruta del servicio o una dependencia no existe en `HEAD`, ENTONCES el
  sistema no debe dar clave; si es una dependencia, debe emitir un aviso que la
  nombre y diga que no está versionada.
- **R13.** CUANDO el origen de un módulo vigilado cae fuera del repositorio en curso
  (`git rev-parse --show-toplevel`), el sistema debe emitir un aviso con el
  servicio, el módulo y la ruta real, que diga que la suite prueba esa copia y no
  la de este árbol, y no debe dar clave.
- **R14.** CUANDO el origen de un módulo vigilado cae dentro del repositorio pero fuera
  de la ruta del servicio y de sus dependencias, el sistema debe emitir un aviso
  que pida declarar esa ruta en `depende_de`, y no debe dar clave.
- **R15.** SI un módulo vigilado no se encuentra, o la sonda falla o tarda más de su
  límite, ENTONCES el sistema debe emitir un aviso con el motivo y no dar clave.
- **R16.** El sistema debe ejecutar la sonda con el intérprete del servicio, desde la
  carpeta del servicio, y sin ejecutar el código del módulo vigilado de primer
  nivel (localizarlo sin importarlo).
- **R17.** La comparación de rutas de R13 y R14 debe ignorar mayúsculas y separadores
  donde el sistema operativo los ignora (Windows).

## C. Decisión y salida (`python -m harness.cache_suites`)

- **R18.** CUANDO hay clave, coincide con el contenido de
  `.arnes_cache/suite_<nombre>.ok` y, si el intérprete del servicio tiene
  `coverage`, existe `<ruta>/coverage.json`, el sistema debe decidir **servir** e
  informar la fecha de modificación de ese fichero (`AAAA-MM-DD HH:MM`, hora local).
- **R19.** En cualquier otro caso el sistema debe decidir **ejecutar** y devolver la
  clave si la hay (para guardarla tras el verde), o vacía si no.
- **R20.** Un fichero de caché escrito con el formato anterior (hash de árbol) no
  debe coincidir nunca con una clave nueva.
- **R21.** DONDE se pide sin caché (`--sin-cache`), el sistema nunca debe decidir
  servir, pero debe devolver la clave para refrescar la caché tras el verde.
- **R22.** El sistema debe escribir por stdout cero o más líneas `AVISO|<texto>` y una
  última línea `SERVIR|<fecha>` o `EJECUTAR|<clave o vacío>`, con código 0. SI el
  servicio no está declarado o la declaración es inválida, ENTONCES debe salir con
  código 1 y el motivo en stderr.

## D. `harness/init.sh` §7 bis

- **R23.** El portero debe decidir la caché de cada servicio Python solo a través de
  `python -m harness.cache_suites`: ya no compone la clave en bash.
- **R24.** El portero debe imprimir cada `AVISO|` como `[AVISO] servicio <nombre>
  (<ruta>): <texto>`; ante `SERVIR|<fecha>`, `[OK]` con «caché: ni el servicio ni
  sus dependencias han cambiado desde el verde del <fecha>»; y, tras un verde con
  clave no vacía, guardar esa clave en el fichero de caché. Sin clave no guarda.
- **R25.** CUANDO `ARNES_SIN_CACHE=1`, el portero debe avisarlo una vez al entrar en
  la sección y pasar `--sin-cache` en cada servicio.
- **R26.** SI la llamada al módulo de caché falla, ENTONCES el portero debe emitir un
  `[AVISO]` nominal y ejecutar la suite sin guardar caché (nunca servirla).
- **R27.** La llamada al módulo de caché no debe consumir la entrada estándar del
  bucle de servicios.

## E. Declaración de albaranes y documentación

- **R28.** `harness/servicios.json` de albaranes debe declarar
  `"depende_de": ["services/albaranes-comun"]` e `"importa": ["ruesma_comun"]` en
  sv1, sv2, sv3, sv4, sv5, sv6 y sv9; `comun` e `infra` no declaran nada.
- **R29.** `harness/servicios.ejemplo.json` debe documentar los tres campos nuevos en
  su `$doc` y mostrarlos en un servicio de ejemplo.
- **R30.** `harness/ARNES_VERSION.md` debe anotar que este repositorio lleva la caché
  con dependencias de la 1.7.16 sobre su 1.7.2, y `harness/VERSION` no cambia.

## F. Escenarios de aceptación (tests de punta a punta del módulo, sin red)

- **R31.** Escenario (a): en un repositorio git temporal con un servicio que depende
  de otro, un commit en la dependencia debe cambiar la clave del dependiente y
  dejar igual la de un tercer servicio sin dependencias.
- **R32.** Escenario (b): con la sonda real (intérprete del test) y un módulo vigilado
  que resuelve fuera del repositorio temporal, la decisión debe ser
  `EJECUTAR|` vacía con el aviso de R13.
- **R33.** Escenario del encargo 1.7.12: tocar `<ruta>/.env` debe cambiar la clave, y
  tocar un fichero bajo `__pycache__` del servicio no debe cambiarla.

## G. Porte a `arnes-base` (regla de propagación)

- **R34.** En `arnes-base` (payload `arnes-base/arnes-base/`), `harness/servicios.py`,
  `harness/cache_suites.py`, `harness/servicios.ejemplo.json` y la sección 7 bis de
  `harness/init.sh` deben quedar idénticos a los de albaranes (ignorando fin de
  línea), con los tests portados con nombre genérico, `harness/VERSION` en 1.7.16
  y la sección «1.7.16» en `GUIA_INSTALACION.md`.
