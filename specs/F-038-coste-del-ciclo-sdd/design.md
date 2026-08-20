<!-- specs/F-038-coste-del-ciclo-sdd/design.md -->
# F-038 · Diseño técnico

Feature de **arnés**, no de dominio: no toca ningún servicio del pipeline ni
el schema de PostgreSQL, así que la arquitectura hexagonal de
`docs/ARCHITECTURE.md` no entra en juego. `harness/` es utillaje del
repositorio y su suite vive en `tests/` (raíz).

**Límite de microservicio:** ninguna responsabilidad nueva. Todo lo que se
toca ya es del arnés y, por la regla de propagación de `CLAUDE.md`, viaja
después a `arnes-base` como 1.7.0.

## Ficheros a crear

| Ruta | Qué es |
|---|---|
| `harness/tamano.py` | Medidor de los topes de papeleo (R13–R16). API pura + CLI `python -m harness.tamano --feature F-XXX`. |
| `tests/test_f038_r1_r4_ejecutor_raiz.py` | T0: ruta acotada, línea base e identidad. |
| `tests/test_f038_r5_r9_muestreo_por_nivel.py` | Lectura de `rigor.json`, precedencia y muestreo. |
| `tests/test_f038_r10_r12_informe.py` | SHA, línea base, media por mutante, `n/d`. |
| `tests/test_f038_r13_r16_tamano.py` | Topes, CLI y ficheros ausentes. |
| `tests/test_f038_r17_r21_documentos.py` | Los cuatro documentos declaran topes, 60 s e incremental. |

## Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `harness/mutacion.py` | `EjecutorPytest` gana `ruta`; `ejecutor_para` la resuelve; `identidad()` la incluye; `comprobar_linea_base` devuelve tiempos; `InformeMutacion` gana `sha_head` y `segundos_linea_base`; `escribir_informe` imprime R10–R12 y R9; CLI resuelve muestreo por nivel. |
| `harness/mutacion_paralela.py` | Propagar `sha_head` y `segundos_linea_base` al agregar los informes de los workers (nada más). |
| `harness/rigor.py` | Lectores y validación de `max_mutantes`/`semilla` por nivel y del bloque `tamano`. |
| `harness/rigor.json` | `nivel_por_defecto` → `estandar`; `max_mutantes`/`semilla` por nivel; bloque `tamano`. |
| `harness/init.sh` | Sección **7 quater**: puerta de topes de tamaño de la feature en curso. |
| `specs/SPECS.md` | Topes de `requirements.md`/`design.md` y «una tarea por línea». |
| `.claude/agents/spec-author.md` | Topes de su producto. |
| `.claude/agents/implementer.md` | Tope del informe (150). |
| `.claude/agents/reviewer.md` | Tope (100), umbral 60 s, revisión incremental, RM1–RM6. |
| `CHECKPOINTS.md` | C4 bis: 60 s, y checkboxes de RM1, RM2, RM5, RM6. |
| `progress/mutacion_F-012.md` (y los demás afectados) | Cabecera de invalidez. |

## Ficheros que NO se tocan

- `services/**` — ninguno. Esta feature no toca el pipeline.
- `harness/alcance.py`, `harness/cobertura.py`, `harness/backlog.py`,
  `harness/rutas_sensibles.json` — no intervienen.
- `harness/features.json` salvo el `status` de F-038 (lo lleva el líder).
- Las 12 specs existentes y sus informes: **no se recortan** (D3).
- `C:\Users\pgris\PycharmProjects\arnes-base` — **nada dentro de esta rama**
  (D6).

## Funciones y firmas

**`harness/mutacion.py`**

- `EjecutorPytest.__init__(..., ruta: str | None = None)`. `correr()` añade
  `ruta` al final de los argumentos —normales y de línea base— cuando no es
  `None`. `identidad() -> (raiz_resuelta, ejecutable, ruta or "")`.
- `ejecutor_para(...)`: cuando `servicio is None or servicio.lenguaje !=
  "python"`, devuelve `EjecutorPytest(raiz=raiz, ruta=_ruta_raiz(raiz))`, donde
  `_ruta_raiz(raiz)` devuelve `"tests"` si `Path(raiz)/"tests"` es directorio y
  `None` si no.
- `comprobar_linea_base(...) -> dict[str, float]`: mismo comportamiento, más el
  tiempo medido por etiqueta. Los ejecutores sin `linea_base` (dobles de test)
  no aportan entrada.
- `InformeMutacion`: `sha_head: str | None`, `segundos_linea_base: dict[str,
  float]`. `escribir_informe` añade a **Totales**: `SHA de HEAD medido`,
  `Línea base (s)` por etiqueta (o `n/d`), `Media por mutante evaluado (s)`; y,
  si `muestreado`, una línea `Muestreo: n de N, semilla S, nivel L`.
- `resolver_muestreo(pedido_max, pedido_semilla, nivel_max, nivel_semilla) ->
  (int | None, int | None)`: función pura, testable sin disco. `pedido_max == 0`
  → `None` (sin tope). Es la única sede de la precedencia de R7.
- `_muestreo_configurado(feature: str) -> (int | None, int | None)`: resuelve el
  nivel con `harness.rigor` y devuelve los valores del nivel; ante cualquier
  `ValueError` de configuración, `(None, None)` —igual que hacen hoy
  `_timeout_configurado` y `_workers_configurados`—.

**`harness/rigor.py`**

- `max_mutantes_nivel(nivel, rigor) -> int | None` y
  `semilla_nivel(nivel, rigor) -> int | None`. Claves **opcionales**: ausencia,
  `null`, `bool` o entero inválido → `None` (misma doctrina que
  `workers_mutacion`, para no romper proyectos con `rigor.json` viejo).
- `topes_tamano(rigor) -> dict[str, int]` con las cuatro claves. Ausencia del
  bloque → `{}` (la puerta se declara `N/A`, no rompe).

**`harness/tamano.py`** (nuevo, sin dependencias fuera de la stdlib)

- `RUTAS = {"requirements": "specs/{slug}/requirements.md", "design": ...,
  "impl": "progress/impl_{feature}.md", "review": "progress/review_{feature}.md"}`.
- `medir(feature, slug, topes, raiz=".") -> list[Exceso]` con
  `Exceso(clave, ruta, lineas, tope)`. Solo mide ficheros existentes.
- `slug_de_feature(feature, raiz=".") -> str | None`: del `branch` de
  `features.json` (`feature/F-038-slug` → `F-038-slug`), o del único directorio
  `specs/F-038-*`. Sin slug, los dos ficheros de spec se saltan.
- `main(argv)`: `--feature` (obligatorio), `--raiz`. Códigos: 0 todo dentro,
  1 algún exceso (imprime `ruta: N líneas > tope T`), 2 error de uso o
  configuración ausente.

## `init.sh` — sección 7 quater

Se coloca **después** de 7 ter (rutas sensibles) y antes de 8. Resuelve la
feature en curso igual que ya hace la puerta de cobertura (rama actual →
`branch` de `features.json`, y si no, la `in_progress`). Entonces:

- Sin feature en curso, sin `harness/tamano.py`, o sin bloque `tamano` en
  `rigor.json` → `warn` + `PUERTA TAMAÑO: N/A` **con el motivo impreso**.
- Con feature en curso → `python -m harness.tamano --feature F-XXX`; código 0
  → `ok`; código 1 → `ko` (init.sh en rojo) reproduciendo la salida.

## Riesgos y decisiones

**D1 · `ruta="tests"` en `ejecutor_para`, no `testpaths` en la raíz.**
Descartado dar `testpaths` a un `pyproject.toml`/`pytest.ini` de la raíz: (a) es
configuración que cada uno de los cinco proyectos tendría que crear y mantener,
mientras que el arreglo en `ejecutor_para` viaja solo con el arnés; (b) cambia
el significado de cualquier `pytest` a pelo que lance un humano en la raíz, no
solo el de la campaña; (c) `init.sh` **ya** resuelve exactamente este problema
con la ruta explícita `tests` y su comentario lo dice — así el arnés pasa a
tener UNA sola regla en vez de dos. Consecuencia asumida: en un repositorio sin
`tests/` en la raíz el comportamiento no mejora (R2), y si alguien pone la suite
de la raíz en otro sitio, hay que declararlo; hoy ningún proyecto lo hace.

**D2 · La precedencia vive en una función pura.** `resolver_muestreo` se prueba
sin disco ni git; el CLI solo la llama. Evita repetir la regla en la rama serie
y en la paralela.

**D3 · Los topes no son retroactivos.** Las 12 specs existentes exceden hoy
(`requirements.md` de 114 a 333 líneas; `design.md` de 225 a 573). Medirlas
pondría `init.sh` en rojo permanente y reescribirlas costaría justo los tokens
que esta feature ahorra. Por eso la puerta mide **solo la feature en curso**:
lo viejo queda amnistiado por construcción, sin lista de excepciones que
mantener. Riesgo aceptado: una spec vieja que se retome y se edite pasará a
medirse, y habrá que resumirla entonces — que es el resultado deseado.

**D4 · Ninguna de RM1..RM6 es puerta automática de `init.sh`.** RM1 no lo puede
ser porque HEAD se mueve con cada commit posterior a la campaña (incluido el
del propio informe): la comprobación de frescura exige juicio. RM2 depende de
cuánto tarda la suite del módulo mutado, que `init.sh` no conoce. RM3 lo declara
la propia ficha. RM4 es una técnica de verificación, no un criterio de
aceptación. RM5 y RM6 exigen leer código y decidir. Lo que sí se automatiza es
el **dato** sobre el que juzgan (R10–R12): la herramienta lo escribe siempre, y
sus tests lo garantizan. RM1, RM2, RM5 y RM6 pasan a checkbox de C4 bis, que
bloquea el cierre aunque no sea automático; RM3 y RM4 quedan como criterio en
`reviewer.md`.

**D5 · Repetir F-012 NO entra en esta feature.** Sus 61 mutantes se midieron
con la invocación rota, pero F-012 está `done` y remedirla es una auditoría
—con su análisis de supervivientes— que cuesta exactamente lo que esta feature
viene a ahorrar. Aquí se hace lo barato y lo que evita el daño: estampar el
aviso de invalidez en cabecera de los informes afectados, para que nadie los
cite como evidencia. La remedición queda como **deuda declarada** y como
pregunta 2 al humano.

**D6 · El porte a `arnes-base` (1.7.0) va después del merge en `dev`.** Nunca
dentro de esta rama: en F-034 hacerlo dentro provocó el rechazo entero del
reviewer. La entrada de `GUIA_INSTALACION.md` debe decir, además de los cambios,
que **`nivel_por_defecto` pasa a `estandar` y las campañas de ese nivel quedan
muestreadas (20 mutantes): sus números NO son comparables con los de versiones
anteriores**, igual que avisó la 1.6.0. Sube de MENOR por eso.

**D7 · Riesgo de la propia feature.** F-038 es rigor `estandar` y toca
`harness/`: su campaña de mutación **solo puede medirse con T0 ya hecho**. De
ahí que T0 sea la primera tarea y no una más.
