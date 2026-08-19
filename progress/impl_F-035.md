<!-- progress/impl_F-035.md -->
# F-035 · Informe de implementación — el instalador ya no puede pisar estado del proyecto

> **Todo el código de esta feature vive en otro repositorio.** En `albaranes`
> no se ha cambiado ni una línea de código: solo este informe y
> `progress/mutacion_F-035.md`, ambos **sin commitear** a propósito (la rama
> `feature/F-034-...` la tiene ocupada otro agente; los commitea el líder).
> El trabajo está en `C:\Users\pgris\PycharmProjects\arnes-base`, en 12
> commits locales **sin `push`**.

## Resumen en una frase

`instalar_arnes.ps1 -Modo actualizar` ya no ofrece siquiera los ficheros que
son estado del proyecto (`harness/features.json`, `docs/ARCHITECTURE.md`,
`progress/**`, `specs/**`...), aplica lo genérico sin preguntar previo backup, y
solo pregunta —con CONSERVAR por defecto— por lo que mezcla ambas cosas. Se ha
reproducido primero el incidente en un banco de pruebas (7 features → 1) y
después se ha visto desaparecer.

---

## 1. La prueba de fuego, antes y después

El encargo pedía verlo **fallar** antes de arreglarlo. Es lo que se hizo:
primero la prueba (commits `1e67231` y `4819afa`), después el arreglo.

### ANTES — fase RED contra `instalar_arnes.ps1` 1.6.0 (commit `1e67231`)

Comando exacto, desde `C:\Users\pgris\PycharmProjects\arnes-base`:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tests_instalador\prueba_instalador.ps1
```

Salida real:

```
=== Prueba del instalador del arnes (C:\Users\pgris\PycharmProjects\arnes-base\instalar_arnes.ps1)

### P1 - features.json sobrevive a -Modo actualizar -Forzar (R9, R10, R39)
  [OK]    el escenario parte de 7 features
  [FALLO] harness/features.json sigue teniendo 7 features
          esperado <7>, obtenido <1>
  [OK]    el instalador termina con codigo 0

--------------------------------------------------
FALLOS: 1 de 3 comprobaciones.
  - P1 - features.json sobrevive a -Modo actualizar -Forzar (R9, R10, R39): harness/features.json sigue teniendo 7 features -- esperado <7>, obtenido <1>
EXITCODE=1
```

**`esperado <7>, obtenido <1>` es el incidente del 2026-08-19 reproducido en un
banco de pruebas**: mismo 34→1 de entonces, a escala.

Con el resto de casos (commit `4819afa`), el rojo fue el que la spec predecía
—P1, P2, P6, P11 y P12 fallando, **P9 pasando**—:

```
### P1 - features.json sobrevive a -Modo actualizar -Forzar (R9, R10, R39)
  [FALLO] harness/features.json sigue teniendo 7 features       esperado <7>, obtenido <1>
### P2 - ARCHITECTURE.md y progress/*.md intactos (R9, R40-i)
  [FALLO] docs/ARCHITECTURE.md sigue con sus 200 lineas         esperado <200>, obtenido <26>
  [FALLO] progress/current.md conserva su marcador
  [FALLO] progress/history.md conserva su marcador
### P6 - el resumen lista los protegidos (R29, R30)
  [FALLO] el resumen cuenta 4 protegidos
  [FALLO] el resumen nombra harness/features.json como protegido
  [FALLO] el resumen nombra docs/ARCHITECTURE.md como protegido
  [FALLO] el resumen nombra progress/current.md como protegido
  [FALLO] el resumen nombra progress/history.md como protegido
### P9 - el modo instalar no pisa nada (R32, R40-vii)
  [OK]    features.json sigue con 7 features
  [OK]    CLAUDE.md conserva su marcador
  [OK]    el instalador termina con codigo 0
### P11 - CRLF frente a LF no cuenta como diferencia (R23)
  [FALLO] harness/rigor.json no se ha reescrito
  [FALLO] harness/rigor.json conserva sus CRLF
  [FALLO] el resumen los cuenta aparte
### P12 - ni __pycache__ ni .pyc ni .pytest_cache en el destino (R24)
  [FALLO] el destino no tiene artefactos de herramienta         esperado <0>, obtenido <19>
FALLOS: 13 de 17 comprobaciones.
EXITCODE=1
```

Que **P9 pasara ya entonces** confirma el diagnóstico de la spec: el modo
`instalar` nunca fue el problema; el agujero estaba solo en `actualizar`.

### DESPUÉS — misma prueba, mismo comando (commit `b6ac623`)

```
### P1 - features.json sobrevive a -Modo actualizar -Forzar (R9, R10, R39)
  [OK]    harness/features.json sigue teniendo 7 features
  [OK]    el instalador termina con codigo 0
### P2 - ARCHITECTURE.md y progress/*.md intactos (R9, R40-i)
  [OK]    docs/ARCHITECTURE.md sigue con sus 200 lineas
  [OK]    progress/current.md conserva su marcador
  [OK]    progress/history.md conserva su marcador
### P3 - un fichero de arnes puro si se actualiza (R11, R40-ii)
  [OK]    .claude/agents/leader.md ya no tiene la version del proyecto
  [OK]    .claude/agents/leader.md es identico al del payload
### P4 - Intro / sin consola conserva el fichero adaptado (R13, R14, R15, R40-iii)
  [OK]    CLAUDE.md conserva su marcador
  [OK]    el resumen lo da por conservado
  [OK]    el instalador termina con codigo 0
### P5 - backup previo con manifiesto (R17, R19, R21, R40-iv)
  [OK]    hay un directorio de backup con sello de fecha
  [OK]    el backup contiene .claude/agents/leader.md
  [OK]    la copia es la version PREVIA del destino, no la nueva
  [OK]    existe el MANIFIESTO.md
  [OK]    el manifiesto lista el fichero respaldado
  [OK]    el manifiesto trae la ruta del destino
  [OK]    el manifiesto trae el commit del destino
  [OK]    el instalador imprime donde ha dejado el backup
### P6 - el resumen lista los protegidos (R29, R30)
  [OK]    el resumen cuenta 4 protegidos
  [OK]    el resumen nombra harness/features.json como protegido
  [OK]    el resumen nombra docs/ARCHITECTURE.md como protegido
  [OK]    el resumen nombra progress/current.md como protegido
  [OK]    el resumen nombra progress/history.md como protegido
### P7 - arbol sucio en ruta del arnes: bloquea (R25, R26, R40-v)
  [OK]    el instalador sale con codigo distinto de 0
  [OK]    nombra la ruta sucia
  [OK]    no ha escrito nada en el destino
  [OK]    con -IgnorarPrecondiciones si corre
  [OK]    y entonces si actualiza el arnes puro
### P8 - sucio fuera del alcance del arnes: no bloquea (R25, R40-vi)
  [OK]    el instalador corre igualmente
  [OK]    no aborta
  [OK]    el trabajo en curso sigue intacto
### P9 - el modo instalar no pisa nada (R32, R40-vii)
  [OK]    features.json sigue con 7 features
  [OK]    CLAUDE.md conserva su marcador
  [OK]    el instalador termina con codigo 0
### P10 - payload sin clasificar: aborta y no escribe (R4, R40-viii)
  [OK]    el instalador sale con codigo distinto de 0
  [OK]    nombra la ruta sin clasificar
  [OK]    no ha escrito nada en el destino
### P11 - CRLF frente a LF no cuenta como diferencia (R23)
  [OK]    harness/rigor.json no se ha reescrito
  [OK]    harness/rigor.json conserva sus CRLF
  [OK]    el resumen los cuenta aparte
  [OK]    un .png se sigue comparando byte a byte, y se actualiza
### P12 - ni __pycache__ ni .pyc ni .pytest_cache en el destino (R24)
  [OK]    el destino no tiene artefactos de herramienta
### P13 - -SoloDiff no escribe nada y aun asi dice que protegeria (R31)
  [OK]    dice igualmente cuales protegeria
  [OK]    no crea el directorio de backup
  [OK]    no reescribe harness/ARNES_VERSION.md
  [OK]    no toca el arnes puro
  [OK]    no toca el estado del proyecto

--------------------------------------------------
TODO VERDE: 47 comprobaciones.
EXITCODE=0
```

---

## 2. Los commits de `arnes-base` (para el reviewer)

`git -C C:\Users\pgris\PycharmProjects\arnes-base log --oneline`, sobre
`89a9ba9` (1.6.0). Rama `main`, **sin `push`**; el remoto sigue en `89a9ba9`.

| Hash | Tarea | Qué |
|---|---|---|
| `1e67231` | T2 | La prueba de fuego, **en rojo**. Andamio + P1. |
| `4819afa` | T3 | P2, P6, P9, P11, P12, también en rojo. |
| `1e7bb4e` | T4 | `politica_ficheros.json`. |
| `3133969` | T5 | El instalador lee la política y comprueba que la cubre entera. |
| `1c77ac6` | T6 | P3, red de no-regresión. |
| `723618c` | T7 | **El recorrido decide por categoría. Aquí P1 se pone verde.** |
| `a605fd7` | T8 | Diálogo con CONSERVAR por defecto + P4. |
| `a67bcc1` | T9 | Normalización CRLF/BOM, estado `solo-eol`. |
| `bf4ce69` | T10 | Backup previo, manifiesto, `-DirBackup` + P5. |
| `d4e2d05` | T11 | Precondiciones, `-IgnorarPrecondiciones` + P7, P8. |
| `65154f8` | T12 | Resumen con protegidos, texto de `ARNES_VERSION.md` + P13. |
| `b6ac623` | T14 | VERSION 1.6.1 y sección nueva de `GUIA_INSTALACION.md`. |

Árbol de `arnes-base` limpio al terminar (`git status --porcelain` vacío).

## 3. Ficheros tocados

**En `arnes-base`** (nada más):

| Fichero | Estado |
|---|---|
| `instalar_arnes.ps1` | modificado (269 → 668 líneas) |
| `politica_ficheros.json` | **nuevo** (51 líneas, raíz, fuera del payload) |
| `tests_instalador/prueba_instalador.ps1` | **nuevo** (490 líneas; 13 casos, 47 comprobaciones) |
| `tests_instalador/README.md` | **nuevo** |
| `GUIA_INSTALACION.md` | modificado (sección C corregida + sección de la 1.6.1) |
| `arnes-base/harness/VERSION` | `1.6.0` → `1.6.1` |

**El payload no cambia** (salvo `VERSION`): esta versión no mejora el arnés
instalado, mejora quien lo instala.

**En `albaranes`**: solo `progress/impl_F-035.md` y `progress/mutacion_F-035.md`,
sin commitear. No se ha tocado `harness/features.json` ni `progress/current.md`
(los tiene en uso el agente de F-034); **queda para el líder** marcar F-035 y
anotar `current.md`.

## 4. Decisiones de diseño

Las cinco decisiones abiertas se implementaron como las aprobó el humano: D1
(`.claude/settings.json` como `adaptado`), D2 (`docs/CONVENTIONS.md` como
`adaptado`), D3 (`-IgnorarPrecondiciones` separado de `-Forzar`), D4 (la
normalización de finales de línea entra) y D5 (rigor `estandar`, ver §6).
Además:

- **La comprobación de categoría (c) va antes de bifurcar por modo, por
  `-Forzar` y por el diálogo.** Es lo que hace que R10 sea cierto por
  construcción y no por revisión: no hay ningún camino desde `-Forzar` o la
  tecla `T` hasta un fichero de estado.
- **Los `excluidos` se resuelven antes que las categorías, no por
  especificidad.** Si compitieran, `harness/**` (8 caracteres de prefijo) le
  ganaría a `**/*.pyc` (0) y los `.pyc` volverían a viajar al destino. Se
  descubrió con P12.
- **El alcance de la precondición incluye las rutas protegidas.** Aunque el
  instalador ya no las escriba: un fichero de estado modificado y sin commitear
  es justo el único caso en que se puede destruir algo que git no puede
  devolver, así que ahí es donde más interesa parar. Es también lo que exige P7.
- **Sin política legible, el instalador no arranca** (`exit 2`). El fallo
  abierto sería volver al comportamiento que causó el incidente.
- **Si falla el backup de un fichero suelto, ese fichero no se sobrescribe**, el
  recorrido sigue y la salida es ≠ 0. Abortar a mitad dejaría el destino
  mezclado, que es peor.

## 5. Desviaciones respecto a la spec (justificadas)

1. **Versión `1.6.1`, no `1.7.0`.** R37 y `design.md` §8 piden el **MINOR**
   siguiente. El humano ordenó explícitamente `1.6.1` en el encargo («la 1.6.0
   ya está publicada y pusheada; no la toques»). Se ha hecho como ordenó y se
   deja escrito aquí porque **contradice R37**: si el reviewer aplica la spec al
   pie de la letra, este es el punto. A favor del PATCH: el payload no cambia
   en absoluto, así que ningún proyecto recibe capacidad nueva al actualizar; lo
   que cambia es el instalador, que no se instala en ningún sitio.
2. **Dos patrones más en `excluidos` que los de R24**: `**/.ruff_cache/**` y
   `**/.mypy_cache/**`. El `.ruff_cache` entró en el payload con la 1.6.0 y P12
   lo cazó copiándose al destino; además, sin clasificarlo, R4 haría abortar el
   instalador en **todas** las ejecuciones. Es la misma clase de artefacto que
   los cuatro que R24 sí lista.
3. **Un caso de prueba más, P13**, para R31 (`-SoloDiff` no escribe nada). La
   spec pedía el requisito pero no le asignaba caso; sin él, R31 no estaba
   verificado.
4. **M2 de la campaña de mutación se repitió como «M2 bis»** porque el mutante
   propuesto moría por la comprobación de integridad y no por P2. Detalle y
   motivo en `progress/mutacion_F-035.md`.
5. **`progress/current.md` y `harness/features.json` no se han tocado** por la
   restricción operativa (otro agente en la rama). Queda para el líder.

## 6. Nota sobre el rigor `estandar` (D5) — leer antes de juzgar las puertas

F-035 está declarada `rigor: estandar`, y **aquí no hay puerta que saltar: hay
puerta sin sujeto**. En `albaranes` no cambia ninguna línea de Python ni de SQL,
así que:

- La **puerta de cobertura de líneas cambiadas** de `harness/init.sh` no tiene
  líneas que medir.
- `python -m harness.mutacion --feature F-035` daría **0 mutantes por falta de
  sujeto**, no por calidad —exactamente el «cero muertos falso» que F-034 acaba
  de corregir—.

La evidencia equivalente, prevista en `design.md` §7.2 y §7.3 y aceptada por el
humano, es la de este informe: **fase RED real y pegada** (§1) y **campaña de
mutación manual sobre PowerShell** (`progress/mutacion_F-035.md`).

## 7. Verificación MANUAL (T16) — hecha en parte, y lo que falta

`-SoloDiff` no escribe nada (lo prueba P13), así que se pudo ejecutar contra
este repositorio sin tocarlo. **Comprobado antes y después: `albaranes` sigue en
`feature/F-034-mutacion-is-y-coherencia-evals` con el mismo único
`M harness/mutacion.py`.** Salida: `EXITCODE=0`.

```
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\albaranes" -Modo actualizar -SoloDiff

[PROTEGIDO] docs/ARCHITECTURE.md (estado del proyecto: el instalador no lo toca)
[PROTEGIDO] harness/features.json (estado del proyecto: el instalador no lo toca)
[PROTEGIDO] progress/current.md (estado del proyecto: el instalador no lo toca)
[PROTEGIDO] progress/history.md (estado del proyecto: el instalador no lo toca)
[NUEVO]    tests/test_mutacion_linea_base.py
[NUEVO]    tests/test_mutacion_prueba_de_verdad.py
[GITIGNORE] el bloque del arnes ya estaba
Nuevos: 2 | Ya iguales: 11 | Iguales salvo finales de linea: 6
Actualizados: 0 | Conservados: 12 | Saltados: 0 | Protegidos: 4
```

Los **cuatro protegidos son exactamente los cuatro que el incidente destruyó**.
Traducido a preguntas al humano, sobre este mismo repositorio:

| | 1.6.0 | 1.6.1 |
|---|---|---|
| Ficheros ofrecidos como «distintos» | **22** (12 reales + 6 puro ruido CRLF + los 4 de estado) | 12 mostrados, y de ellos **solo 6 se preguntan** |
| Ficheros de estado ofrecidos | 4 | **0** |
| Preguntas de las que se salía pulsando `T` | 22 | 6, con Intro = conservar |

**Lo que falta y es del humano** (`design.md` §7.4): repetir este `-SoloDiff`
sobre una rama limpia creada desde `dev`. En la rama de F-034 seis de los doce
diffs son trabajo en vuelo de esa feature, no diferencias reales con el arnés,
así que el número final de «distintos» que verá desde `dev` será menor. Y
**aplicar de verdad la 1.6.1 a `albaranes` no es parte de F-035**: lo decide el
humano después.

## 8. Qué queda fuera / abierto

- **Sin `push` en ninguno de los dos repositorios**, como se pidió. `arnes-base`
  tiene 12 commits locales por delante de `origin/main`.
- **`albaranes` no se ha actualizado a la 1.6.1.** Es un paso posterior del
  humano.
- **La prueba solo corre en Windows** (PowerShell 5.1 + git) y **no hay CI en
  `arnes-base`**: hay que lanzarla a mano. Asumido en `design.md` §9 (R-4).
- **`harness/rigor.json` sigue clasificado como arnés puro** (R-3 del diseño):
  un proyecto que hubiera bajado su umbral lo pierde al actualizar. Riesgo
  aceptado y ahora escrito también en la guía, cubierto por el backup.
- **`bash harness/init.sh` de `albaranes` NO se ha ejecutado** (T17), por
  indicación expresa: lo tiene ocupado el agente de F-034 y en Windows dos
  suites a la vez tumban el proceso (`0xC0000142`). Queda pendiente para el
  líder. No hay cambios de código en este repositorio que puedan romperlo.

## Evidencias

| Evidencia | Valor | Cómo se ha obtenido |
|---|---|---|
| **Tests ejecutados y resultado** | **47 comprobaciones, 13 casos (P1-P13), 0 fallos, salida 0** | `powershell -NoProfile -File tests_instalador\prueba_instalador.ps1` en `arnes-base` |
| **Tiempo de ejecución de la suite** | **44 s** | medido con `Get-Date` alrededor de la misma invocación |
| **Mutantes generados y supervivientes** | **7 mutantes, 7 muertos, 0 supervivientes** (campaña MANUAL sobre PowerShell) | `progress/mutacion_F-035.md`, mutante a mutante con el texto exacto original → mutado |
| **Cobertura de las líneas cambiadas** | **No aplicable: 0 líneas de Python cambiadas en `albaranes`** | `harness/cobertura.py` mide el diff de este repositorio; el código de F-035 está en `arnes-base` y es PowerShell. No es puerta pasada, es puerta sin sujeto (§6) |
| **Fase RED** | **P1 fallando con `esperado <7>, obtenido <1>`** contra la 1.6.0, antes de tocar el instalador | §1, commit `1e67231` |
| **Verificación contra el repositorio real** | 4 protegidos, 0 ficheros de estado ofrecidos, `albaranes` sin modificar | §7 |
