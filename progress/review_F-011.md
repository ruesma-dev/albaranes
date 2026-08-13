<!-- progress/review_F-011.md -->
# F-011 · Evals de IA con ground truth y puerta en el arnés — Review

- **Veredicto: CHANGES_REQUESTED**
- Rama revisada: `feature/F-011-evals-ia` (HEAD `7e88275`), árbol principal.
- Fecha: 2026-08-13.
- **Nivel de rigor: `estandar`** (declarado en `harness/features.json`).
  Exige: C1–C3, C3 bis, C5, tests trazables (C4), **fase RED** en los
  requisitos centrales, **cobertura** de las líneas cambiadas ≥ 80 % y
  **campaña de mutación** con todos los supervivientes analizados (no exige
  cero supervivientes; eso es `critico`).

Un solo motivo bloquea, y es barato de cerrar: la declaración de rutas
sensibles se ha quedado **una ruta corta** respecto a la spec aprobada, sin
que conste en ninguna parte que se decidió quitarla. Todo lo demás —y es
mucho— está verificado y en verde.

---

## 1. Cambio requerido (bloqueante)

### 1.1 Falta la ruta de las reglas de revisión de sv5 en `harness/rutas_sensibles.json`

`harness/rutas_sensibles.json` declara **13** rutas. La spec aprobada pide
**14**:

- `requirements.md` R19 (línea 149): «La declaración inicial cubre: prompts
  YAML **y reglas de revisión de sv2 y sv5**…».
- `design.md` línea 102, en el esquema literal de la declaración:
  `{ "patron": "services/albaran-valoracion-api/config/revision_rules.yaml",
  "motivo": "reglas de revisión sv5" }`.

La declaración implementada incluye la de sv2
(`services/albaranes-api/config/revision_rules.yaml`, línea 18 del JSON) y
**no** la de sv5. El fichero existe en el árbol
(`services/albaran-valoracion-api/config/revision_rules.yaml`) y sv5 trae su
`infrastructure/prompts/revision_rules_repository.py` que lo carga, así que el
patrón no está muerto: casaría con un fichero real y `--validar` lo aceptaría
sin problema.

Por qué bloquea aun siendo una línea:

1. **La omisión es silenciosa por construcción.** `validar()` detecta patrones
   *muertos* (`rutas_sensibles.py:206-226`), pero nada detecta un patrón
   *ausente*. Si mañana alguien edita las reglas de revisión de sv5, la puerta
   imprimirá tranquilamente «N/A (F-XXX no toca ninguna ruta sensible
   declarada)». Es exactamente el fallo que esta feature existe para evitar, y
   el argumento que el propio módulo escribe en su docstring: degradar a «sin
   puerta» en silencio es la peor salida posible.
2. **No consta como desviación.** El informe del implementer documenta tres
   desviaciones con su razonamiento y las deja a decisión del humano; esta
   cuarta no aparece: `progress/impl_F-011.md` dice «13 rutas» sin más. Un
   reviewer no puede distinguir «se decidió quitarla porque sv5 no compone hoy
   ese repositorio» de «se cayó al copiar la lista».

**Cómo cerrarlo** (cualquiera de las dos, la elige el humano):

- **(a)** Añadir la entrada que falta a `harness/rutas_sensibles.json`, entre
  las de sv5:
  `{ "patron": "services/albaran-valoracion-api/config/revision_rules.yaml", "motivo": "reglas de revisión sv5" }`.
- **(b)** Dejarla fuera **a propósito**, escribiendo el motivo en
  `progress/impl_F-011.md` (por ejemplo: en sv5 la clase
  `RevisionRulesRepository` no se instancia en ninguna composición —
  comprobado: no hay ni una llamada `RevisionRulesRepository(` en sv5 —, luego
  ese YAML no llega hoy a ningún prompt) y corrigiendo `design.md` para que la
  spec y el código digan lo mismo.

En ambos casos, y para que esto no vuelva a poder pasar sin que salte nadie:
**un test que fije el conjunto declarado**, no solo el esquema. Los tests
actuales de R19/R20 (`tests/test_f011_r19_r20_declaracion.py`) validan forma,
duplicados, campos obligatorios y que ningún patrón esté muerto; ninguno
comprueba *qué* rutas hay. Bastaría un
`test_f011_r19_la_declaracion_cubre_las_rutas_de_la_spec` con la lista de
patrones esperada.

---

## 2. Comprobaciones de primera mano

Todo lo de esta sección lo he ejecutado yo, no lo he leído del informe.

| Comprobación | Comando | Resultado |
|---|---|---|
| Arnés completo | `bash harness/init.sh` | **exit 0**, `ENTORNO LISTO` (ver nota 2.1) |
| Suite de la raíz | `.venv/Scripts/python.exe -m pytest tests -q` | `169 passed in 11.56s` |
| Suite completa (init) | dentro de `init.sh` | raíz `188 passed, 3 skipped in 166.98s`; servicio `comun` `19 passed, 3 skipped` |
| Cobertura | puerta de `init.sh` | `[OK] PUERTA COBERTURA: 88.8% de 1254 líneas cambiadas cubiertas (1113/1254, umbral 80%, nivel estandar)` |
| Puerta de rutas sensibles | dentro de `init.sh` | `[OK] PUERTA RUTAS SENSIBLES [evals]: N/A (F-011 no toca ninguna ruta sensible declarada)` |
| Declaración sana | `python -m harness.rutas_sensibles --validar` | `1 verificación(es), 13 ruta(s) sensible(s) declaradas: evals (aviso)`, **exit 0** |
| Runner determinista | `python -m evals.runner` | `NO_EVALUABLE · informe en …`, **exit 2** (lo esperado hoy: libros vacíos) |
| Árbol limpio | `git status --short` | vacío (borré el `progress/evals_manual.md` que dejó mi propia corrida) |

### 2.1 Nota sobre la primera corrida de `init.sh` (fue un artefacto MÍO, no del código)

Mi **primera** corrida de `init.sh` terminó en **rojo**:
`[KO] PUERTA COBERTURA: 0.0% de 1497 líneas cambiadas cubiertas (0/1497…)`.
Lo dejo escrito porque un 0,0 % asusta y conviene que no se malinterprete
luego: lancé comandos en paralelo mientras esa corrida estaba en marcha y el
`coverage.json` de la raíz no estaba en su sitio cuando la puerta fue a
leerlo. Con el `coverage.json` presente, la misma puerta sobre el mismo commit
da `88.8% de 1254` — reproducido a mano — y la **segunda corrida de `init.sh`,
lanzada sola y sin nada más tocando el repositorio, termina en exit 0** con esa
misma cifra. No hay ningún fallo del código de la feature aquí. Ver la
propuesta de automejora 6.1, que sí sale de este episodio.

---

## 3. Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0 (segunda corrida, limpia).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` (los verifica el propio `init.sh`).

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: F-011.
- [x] Rama actual `feature/F-011-evals-ia`, no `main` ni `dev`.
- [x] `progress/current.md` describe solo la sesión de F-011.
- [x] Ninguna feature `done` nueva; `progress/history.md` sin deuda.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal a la escala de `evals/`**: lógica pura (`modelos`,
      `barrido`, `criticidad`, `conversor`, `comparador`, `informe`) sin
      imports de servicios; los adaptadores que componen sv2/sv5/sv6 viven
      aislados en `evals/procesos/` y solo se ejecutan en subproceso. **Cero
      ficheros tocados bajo `services/`** (verificado en el diffstat), que era
      la restricción dura del diseño.
- [x] Primera línea con la ruta relativa en **todos** los ficheros `.py` del
      diff (comprobado uno a uno con un barrido sobre
      `git diff dev...HEAD --name-only`).
- [x] Sin `print()` de debug. Los `print` de `evals/procesos/*.py` son el
      protocolo de los subprocesos (JSON por stdout, errores por stderr) y
      `docs/CONVENTIONS.md` los permite en scripts.
- [x] Sin secretos. Barrido propio sobre las líneas añadidas del diff
      (correos, IPs, GUID de suscripción/tenant, `password|secret|api_key|
      token|AccountKey|sas=`): los únicos aciertos son **entradas sintéticas de
      los tests del barrido** (`pedidos@proveedor-hormigones.es`,
      `10.140.22.7`, el UUID de ejemplo `3f2504e0-…`,
      `"una-clave-de-prueba-no-real"`). Ninguna credencial real.
- [x] Sin dependencias nuevas fuera de la spec: `evals/requirements.txt`
      corresponde a D6.
- [x] Reglas de dominio: la feature no toca merge/raw, ni schema, ni
      conversión de unidades — compone sv6 desde fuera con su
      `unit_registry.yaml` real.

### C3 bis — Documentos que entran de fuera

**N/A justificado**: la feature no añade ni modifica nada en
`docs/referencia/`. Aun así he comprobado lo colindante, porque aquí sí entran
datos del humano: `git log --diff-filter=A` sobre la rama no añade **ningún**
`.xlsx/.xls/.pdf/.docx/.pptx`, los seis libros siguen sin versionar y los seis
`evals/fixtures/*/_indice.json` versionados contienen `"casos": []` y el
`sha256` del libro: cero datos de proveedor.

### C4 — La verificación es real

- [x] R1–R26 tienen test trazable `test_f011_rN_*` y todos pasan (169 tests en
      19 ficheros; recorrido el conjunto de nombres, no falta ningún número).
      R27 es MANUAL y lo he verificado yo (§4); R28 es transversal.
- [x] Los unit tests no tocan red, BBDD ni LLM: `tests/conftest.py` construye
      los libros Excel con `openpyxl` en directorio temporal y nunca lee
      `evals/ground_truth/`; la puerta se prueba con `EjecutorGit` falso; sv6
      se ejercita en subproceso con un envelope ya construido.
- [x] Las verificaciones MANUAL están listadas en `progress/current.md` con su
      comando exacto (pasada completa con LLM, diff de `arnes-base`, y las dos
      decisiones abiertas).

### C4 bis — El rigor declarado se cumple

- [x] `rigor: "estandar"` declarado en `harness/features.json`.
- [x] **Fase RED con traza real**, no con una frase: el informe pega las
      salidas de colecta en rojo de R4, R7/R8, R1–R6, R2/R15, R13 y R20–R25.
      La de R13 es la buena: tras escribir el adaptador, **dos tests siguieron
      rojos contra el sv6 real** (`assert True is False`, y una lista de cinco
      discrepancias con `precio_source` `contrato_db` vs `albaran`), y de ahí
      salió la desviación nº 1 en vez de un test afinado para pasar.
- [x] **Cobertura**: `[OK] 88.8 %` de 1254 líneas cambiadas, umbral 80 %.
- [x] **Mutación verificada de forma independiente**. Recalculado con
      `harness.alcance.alcance_de_feature` + `harness.mutacion.generar_mutantes`
      (cálculo puro, sin ejecutar la suite):

      13 ficheros · 3812 líneas · **305 mutantes**

      coincide **exactamente**, fichero a fichero, con el alcance y el total de
      `progress/mutacion_F-011.md` (305 generados, 305 evaluados, 172 muertos,
      133 supervivientes, 0 timeouts). Muestreados tres supervivientes y
      confirmados como mutantes reales, con el mismo operador y el mismo texto
      original→mutado:
      - nº 1 `evals/barrido.py:46` [booleano] `@dataclass(frozen=True)` → `(frozen=False)` ✔
      - nº 2 `evals/comparador.py:48` [booleano] `return False` → `return True` ✔
      - nº 126 `harness/rutas_sensibles.py:252` [entero] `…patron[:-2])` → `…patron[:-3])` ✔
      No es un informe escrito a mano.
- [x] **Ningún superviviente en `PENDIENTE`**: 133 secciones `#### Análisis`
      para 133 supervivientes, cero coincidencias de «PENDIENTE» en el fichero.
      El nivel `estandar` no exige cero supervivientes; exige análisis, y lo
      hay, con una tabla de clasificación por naturaleza y una sección de deuda
      accionable (el hueco de `lineas_no_casadas` de sv5 es el que tiene
      consecuencia de negocio y está bien señalado).
- [x] Sección **«Evidencias»** con los cuatro números: tests (169 / 185+3),
      cobertura (88,8 %), mutantes y supervivientes (305 / 133) y tiempo de
      suite (16,68 s la de `tests/`, 158 s la completa).
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A justificado, y verificado por mí, no leído del informe**: hay
declaración (`harness/rutas_sensibles.json`), pero el diff de la feature
**no toca ni una** de las rutas declaradas — el diffstat de `git diff dev...HEAD`
no contiene un solo fichero bajo `services/`. La puerta lo dice con su motivo
impreso (`N/A (F-011 no toca ninguna ruta sensible declarada)`), que es lo que
pide R25. Por tanto no hay informe de evals que exigir ni frescura que
comprobar.

Dos apuntes para cuando SÍ aplique: `progress/evals_F-011.md` está versionado
pero es de una corrida **determinista** (`MODO: determinista`,
`FASES: IA3,IA4,E2E`, `VEREDICTO: NO_EVALUABLE`), así que **no** valdría como
evidencia: no cumple ninguna de las tres `exige_lineas`. Es correcto que no
valga. Y el bloqueante §1.1 es justo un agujero en esta puerta.

### C5 — La sesión se cerró bien

- [x] `tasks.md` con T1–T14 en `[x]` y un commit `F-011 Tn: …` por tarea
      (15 commits en la rama; T5 llevó un commit extra de lint, correctamente
      etiquetado).
- [x] Sin ficheros temporales ni artefactos sospechosos: `git status` limpio.
- [x] `features.json` refleja el estado real (`in_progress`; no se ha marcado
      `done`, que es lo correcto hasta que cierre el review).

---

## 4. Propagación a `arnes-base` (R27) — verificada

- `git -C C:/Users/pgris/PycharmProjects/arnes-base log --oneline -3` muestra
  el commit **`4c294c9` «1.4.0: puerta de rutas sensibles»**, local y sin push,
  como manda la regla.
- Contenido: `arnes-base/harness/rutas_sensibles.py` (440 líneas),
  `rutas_sensibles.ejemplo.json`, sección 7 ter de su `init.sh`, bloque C4 ter
  de su `CHECKPOINTS.md`, `harness/VERSION` a 1.4.0 y su capítulo en
  `GUIA_INSTALACION.md`.
- **El módulo portado es idéntico** al de este repositorio
  (`diff --strip-trailing-cr` sin diferencias): se portó el mecanismo, no una
  variante.
- **No se portó nada específico de albaranes**: ni la declaración real, ni el
  runner, ni la criticidad. El bloque genérico de C4 ter de este repo está
  marcado con sus comentarios `==== GENÉRICO ====` y el párrafo de evals queda
  fuera de ellos. Correcto.

---

## 5. Las tres desviaciones del informe

| # | Desviación | Juicio |
|---|---|---|
| 1 | Las sintéticas PROHIBIDAS no desaparecen del build de sv6 | **Justificada y bien resuelta.** El diseño afirmaba algo que el código de sv6 no hace; se midió (traza del record con `precio_unitario_final: null`, `review_required: true`, `modifier_identified_no_tariff`) y **el eval se dejó como pide la spec**, no afinado para pasar. No se tocó sv6, que la spec prohíbe. Decisión pendiente del humano, correctamente escalada. No esconde ningún requisito incumplido |
| 2 | Campos del ground truth no observables por el extremo-a-extremo | **Justificada.** Obra, proveedor, CIF, fecha y nº de albarán no salen del build de sv6 (ni los transporta su envelope): compararlos daría ROJO por algo que no es un fallo del sistema, y su eval es el libro IA1. Lo importante: **no se saltan en silencio** — `podar()` (comparador) y `campos_no_observables()` los listan en el informe como «no observables en esta corrida». Es una relajación de R14 acotada, visible y con el mecanismo para verla |
| 3 | Campaña de mutación con `PYTEST_ADDOPTS=--ignore=services` | **Justificada.** La suite acotada no puede debilitar la campaña: los 305 mutantes viven en `evals/` y `harness/rutas_sensibles.py`, y ningún test del servicio `comun` puede cazarlos; lo único que se quitó fueron ~120 s por mutante. No se tocó código del arnés. He recalculado alcance y mutantes por mi cuenta y cuadran al mutante |

La que no está en la lista y debería, es el §1.1.

---

## 6. Observaciones no bloqueantes y automejora (propuestas, no aplicadas)

### 6.1 `harness/cobertura.py` no distingue «0 % cubierto» de «no hay medición»

Cuando falta el `coverage.json` de la raíz, `cobertura_lineas_cambiadas()`
mete cada fichero por la rama de «no medido» y suma sus líneas ejecutables al
denominador con cero al numerador: el resultado es un
`[KO] PUERTA COBERTURA: 0.0% de 1497 líneas` que parece un desastre de tests y
en realidad es un fichero que no está. Que además cambie el denominador
(1497 frente a 1254) hace el diagnóstico aún más confuso. Propongo que la
puerta, si no encuentra ninguna medición para **ningún** fichero del alcance,
lo diga con esas palabras («no hay `coverage.json`: la medición no se ha
ejecutado o se ha borrado») en vez de publicar un porcentaje inventado. Es
genérico: va a `arnes-base`, no aquí.

### 6.2 `--validar` no puede detectar una ruta que falta

Consecuencia directa del §1.1 y también genérica. Una idea barata para
`arnes-base`: permitir que cada verificación declare `rutas_minimas` (o que el
repositorio fije su lista en un test, como propongo en §1.1). Hoy la
declaración solo se defiende de patrones muertos, que es el error menos grave
de los dos: el patrón muerto se ve; el ausente, no.

### 6.3 Código muerto declarado en el propio informe de mutación

`ValorEsperado.desde_json` (`evals/modelos.py`) no lo llama nadie y deja
cuatro supervivientes; el informe lo reconoce y propone «o test o borrarlo».
Suscribo lo segundo. No bloquea.

### 6.4 Sobre este protocolo de review

La copia de `.claude/agents/reviewer.md` de esta rama no incluye la prueba de
control del cero en mutación que sí trae `arnes-base` 1.3.1 (commit `84698fc`).
Aquí no hacía falta —la campaña declara 133 supervivientes, no cero— pero
conviene que llegue a este repositorio en la próxima actualización del arnés,
junto con el arreglo de la sección 7 (acotar pytest a `tests/`) que la
desviación nº 3 tuvo que sortear a mano.

---

## 7. Trazabilidad requisito → test (verificada contra el árbol)

| Requisito | Test que lo cubre | ¿Pasa? |
|---|---|---|
| R1, R2, R3 | `tests/test_f011_r1_r2_r3_conversor.py` (12) | ✔ |
| R2 (comparación) | `tests/test_f011_r2_comparador.py` (13) | ✔ |
| R4 | `tests/test_f011_r4_barrido.py` (9) | ✔ |
| R5 | `tests/test_f011_r5_determinismo.py` (5) | ✔ |
| R6 | `tests/test_f011_r6_ausencias.py` (6) | ✔ |
| R7, R8 | `tests/test_f011_r7_r8_criticidad.py` (8) | ✔ |
| R9, R10 | `tests/test_f011_r9_r10_cli.py` (11) | ✔ |
| R11 | `tests/test_f011_r11_ia12.py` (8) | ✔ |
| R12 | `tests/test_f011_r12_omitidos.py` (6) | ✔ |
| R13 | `tests/test_f011_r13_determinista.py` (10) | ✔ |
| R14 | `tests/test_f011_r14_e2e_real.py` (8) | ✔ |
| R15 | `tests/test_f011_r15_informe.py` (11) | ✔ |
| R16 | `tests/test_f011_r16_exit_codes.py` (4) | ✔ |
| R17 | `tests/test_f011_r17_secuencial.py` (2) | ✔ |
| R18 | `tests/test_f011_r18_sin_casos.py` (5) | ✔ |
| R19, R20 | `tests/test_f011_r19_r20_declaracion.py` (11) | ✔ **pero** ninguno fija el conjunto de rutas declarado → §1.1 |
| R21, R22 | `tests/test_f011_r21_r22_ausente_o_rota.py` (6) | ✔ |
| R23, R24, R25, R26 | `tests/test_f011_r23_r24_r25_puerta.py` (14) | ✔ |
| R27 | MANUAL — verificado por el reviewer en `arnes-base` (§4) | ✔ |
| R28 | Transversal — comprobado en C3 y C4 | ✔ |

---

## 8. Qué hace falta para el APPROVED

Solo esto:

1. Resolver §1.1 — añadir
   `services/albaran-valoracion-api/config/revision_rules.yaml` a
   `harness/rutas_sensibles.json`, **o** dejar por escrito por qué se queda
   fuera y alinear `design.md`.
2. Añadir el test que fija el conjunto de rutas declarado, para que la
   siguiente omisión salte sola.
3. Relanzar `bash harness/init.sh` (sin nada más corriendo en paralelo) y
   pegar el resultado.

No hace falta repetir la campaña de mutación: el cambio es de configuración
JSON y de tests, fuera del alcance de mutación (`harness/rutas_sensibles.json`
no es código de producción Python). Sí conviene volver a lanzar
`python -m harness.rutas_sensibles --validar` para confirmar que el patrón
nuevo casa con su fichero.

Las dos decisiones abiertas de las desviaciones 1 y 2 son del humano y **no**
bloquean este review: el código está implementado como manda la spec y ambas
están documentadas donde deben.
