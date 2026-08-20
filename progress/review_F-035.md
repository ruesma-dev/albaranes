<!-- progress/review_F-035.md -->
# F-035 · Review — el instalador en modo `actualizar` no puede pisar estado del proyecto

**Veredicto: CHANGES_REQUESTED**

> Que quede dicho antes que nada, porque el veredicto no debe leerse como una
> enmienda a la totalidad: **el arreglo es real y lo he comprobado por mi
> cuenta, no leyendo el informe**. Reproduje la fase RED con el instalador
> anterior y vi el incidente (`esperado <7>, obtenido <1>`); reproduje dos
> mutantes de la campaña manual y murieron donde el informe dice; y comprobé
> que proteger no ha paralizado nada. Lo que falla está en la **red que vigila
> el arreglo**, no en el arreglo: hay un mutante que **sobrevive** a las 47
> comprobaciones y que devuelve al instalador justo el comportamiento que la
> propia spec señala como causa contribuyente del incidente. Más los cierres de
> C5, que están sin hacer.

- **Feature**: F-035, `sdd=true`, `rigor: estandar` (declarado en
  `harness/features.json`).
- **Código revisado**: `C:\Users\pgris\PycharmProjects\arnes-base`,
  `89a9ba9..b6ac623` (12 commits, rama `main`, sin push). Entregado como
  **1.6.1**.
- **Spec**: `specs/F-035-instalador-no-pisa-estado/` (R1–R41).

---

## Nivel de rigor y qué exige

`estandar` (`harness/rigor.json`): fase RED **sí**, cobertura **sí**, mutación
**sí** con los supervivientes documentados y analizados,
`supervivientes_maximos: null` («los supervivientes se documentan y el reviewer
juzga»). No es `critico`, así que un superviviente no es descalificación
automática: es material de juicio. Lo he juzgado abajo, en CR-1.

| Puerta | Estado | Motivo |
|---|---|---|
| Fase RED | **[x] CUMPLE**, y verificada por mí | §1 |
| Cobertura | **N/A justificado** | En `albaranes` no cambia ni una línea de Python: el código es PowerShell y vive en `arnes-base`. `bash harness/init.sh` imprime `PUERTA COBERTURA: N/A (rama dev: solo aplica en ramas de feature)`; el motivo de fondo, más fuerte, es que la puerta **no tiene sujeto**. No es una herramienta que no se lanzó: es una medición sin nada que medir |
| Mutación | **[x] CUMPLE en forma**, campaña MANUAL con texto exacto por fila; dos filas reproducidas por mí | §2 |
| Evidencias | **[x] CUMPLE**: el informe trae la sección con los cuatro números | `progress/impl_F-035.md` §Evidencias |

---

## 1. La fase RED, contrastada (el punto crítico del encargo)

No me he fiado de la traza pegada en el informe. Copié el árbol de `arnes-base`
a mi scratchpad, sustituí `instalar_arnes.ps1` por
`git show 89a9ba9:instalar_arnes.ps1` (269 líneas, el instalador **anterior**) y
ejecuté contra él la suite **tal cual la entrega el implementer**:

```
=== Prueba del instalador del arnes (...\scratchpad\red\instalar_arnes.ps1)

### P1 - features.json sobrevive a -Modo actualizar -Forzar (R9, R10, R39)
  [FALLO] harness/features.json sigue teniendo 7 features
          esperado <7>, obtenido <1>
...
FALLOS: 20 de 40 comprobaciones.
```

**La prueba de fuego prueba de verdad.** Con el instalador viejo, P1 falla con
exactamente el mensaje que el informe declara, y con él P2, P5, P6, P7, P10,
P11, P12 y P13. Contra el instalador nuevo, ejecutado por mí desde el
repositorio real: **TODO VERDE: 47 comprobaciones**, exit 0, **42 s** (el
informe declara 44 s; misma magnitud), y `git status --porcelain` de
`arnes-base` vacío después.

Dato interesante y que confirma la honradez del informe: **P3 pasa también
contra el instalador viejo**. Es lo que el propio `tasks.md` T6 anticipaba
(«P3 pasa contra el comportamiento actual; queda como red de no-regresión»), no
un caso inflado para engordar el verde.

## 2. La campaña de mutación manual, contrastada

`progress/mutacion_F-035.md` trae la tabla con **una fila por mutante** y el
**texto exacto original → mutado**, que es lo que la hace reproducible.
Reproduje dos filas al pie de la letra, sobre una copia en scratchpad (jamás
sobre el árbol versionado):

| Mutante | Sustitución exacta aplicada | Resultado que obtengo | Lo que declara el informe |
|---|---|---|---|
| **M1** | se elimina la línea `    "harness/features.json",` de `estado_del_proyecto` | **MUERTO**: 4 fallos — P1, P6 (×2), P13 | MUERTO por P1, P6, P13 ✔ |
| **M3** | `if (-not $patron.Contains('*')) { return 10000 + $patron.Length }` → `if (-not $patron.Contains('*')) { return 0 }` | **MUERTO**: 4 fallos — P1, P6 (×2), P13; exit 1 | MUERTO por P1, P6, P13 ✔ |

Coinciden fila a fila, incluida la corrección honesta que el informe hace sobre
el diseño (M3 **no** muere en P9, y el informe lo dice en vez de disimularlo).
La campaña es manual y no declara «Tiempo total»: la regla de reejecutar por
debajo de 5 minutos es para la campaña automática de `harness.mutacion`, que
aquí **no tiene sujeto** (0 líneas de Python en el diff de `albaranes`). En su
lugar he hecho lo que sí procede: reproducir filas y **generar un mutante mío**.

## 3. El mutante que sobrevive (CR-1)

Este es el hallazgo. Mutante **MR1**, en `instalar_arnes.ps1` (línea 473):

```
    if ($cat -eq 'puro' -and -not $PreguntarTodo -and -not $SoloDiff) {
->  if ($false) {
```

Es decir: **el arnés puro deja de aplicarse sin preguntar y vuelve a pasar por
el diálogo, fichero a fichero.** Resultado de la suite completa con el mutante
puesto:

```
--------------------------------------------------
TODO VERDE: 47 comprobaciones.
```

**Sobrevive entero.** Y no es un superviviente cosmético:

- Deja **R11 sin verificar** («se sobrescribe sin preguntar») y **R12 sin
  verificar en absoluto** (`-PreguntarTodo` no lo ejercita ningún caso).
- El comportamiento que MR1 destruye es, por escrito en la propia spec y en los
  comentarios del código, **causa contribuyente del incidente**: «preguntar por
  los 20 ficheros genéricos es lo que convertía la actualización en un
  interrogatorio del que se salía pulsando T, y la T era la que hacía el
  destrozo» (R23 y el comentario de la línea 470). Con MR1, el instalador
  vuelve a los ~13 diffs seguidos y la suite no se entera.
- La suite no lo caza porque **todos los casos que tocan el arnés puro usan
  `-Forzar`** (P3, P5, P7, P11, P12 vienen de `Get-EscenarioForzado` o pasan
  `-Forzar`), y con `-Forzar` el diálogo responde `s` igualmente. El único caso
  sin `-Forzar` (P4) solo mira `CLAUDE.md`, que es `adaptado`.

Que conste: **el código está bien; lo que falta es la red**. Lo comprobé a mano
sobre el instalador real, con entrada estándar vacía y sin `-Forzar`:

```
  [ACTUALIZADO] .claude/agents/leader.md
  CLAUDE.md : [N] conservar el tuyo (POR DEFECTO: Intro)  [S] sobrescribir ...
  (Intro) se CONSERVA CLAUDE.md
  Actualizados: 1 | Conservados: 1 | Saltados: 0 | Protegidos: 0
```

y con `-PreguntarTodo`, `leader.md` queda **CONSERVADO**: R11 y R12 se cumplen
de hecho. Por eso el arreglo es de test, no de producto.

## 4. Proteger no se ha convertido en paralizar (punto 3 del encargo)

Confirmado, y por tres vías independientes:

1. **P3** deja `.claude/agents/leader.md` idéntico al del payload tras
   `-Forzar` (borra el `MODIFICADO POR EL PROYECTO` sembrado).
2. **P7**, última aserción: con `-IgnorarPrecondiciones` el arnés puro **sí** se
   actualiza.
3. **Mi ejecución manual** de §3: sin `-Forzar` y sin consola, `leader.md` sale
   `[ACTUALIZADO]` y el resumen dice `Actualizados: 1`.

Un instalador que no rompe nada porque no hace nada habría fallado las tres.

## 5. La política, contra el payload real (punto 2 del encargo)

Crucé `politica_ficheros.json` con **todos** los ficheros del payload en disco
(no solo los versionados): 35 versionados + 19 artefactos de herramienta.
**Todos casan.** Sin agujeros:

| Ruta del payload | Cae en | Cómo |
|---|---|---|
| `.claude/agents/*.md` (4) | `arnes_puro` | `.claude/agents/**` |
| `.claude/settings.json` | `adaptado` | entrada exacta (**decisión D1**) |
| `CLAUDE.md`, `CHECKPOINTS.md` | `adaptado` | exactas |
| `docs/ARCHITECTURE.md` | `estado_del_proyecto` | exacta |
| `docs/CONVENTIONS.md` | `adaptado` | exacta (**decisión D2**) |
| `docs/referencia/README.md` | `adaptado` | exacta, gana a `docs/referencia/**` por R3 |
| `harness/features.json`, `servicios.json`, `rutas_sensibles.json` | `estado_del_proyecto` | exactas, ganan a `harness/**` por R3 |
| `harness/init.sh` | `adaptado` | exacta |
| `harness/VERSION`, `*.py`, `rigor.json`, `*.ejemplo.json` | `arnes_puro` | `harness/**` |
| `harness/gitignore.arnes` | `excluidos` | exacta |
| `progress/*.md` (2) | `estado_del_proyecto` | `progress/**` |
| `scripts/*` (2), `tests/*.py` (5) | `arnes_puro` | prefijos |
| `specs/SPECS.md` | `arnes_puro` | exacta, gana a `specs/**` por R3 |
| `__pycache__`, `.pyc`, `.pytest_cache`, `.ruff_cache` (19) | `excluidos` | `**/…`, resueltos **antes** que las categorías |

Entradas preventivas que hoy no existen en el payload (`BACKLOG.md`, `.env`,
`.claude/settings.local.json`, `specs/**`, `docs/referencia/**`): R5 las admite
y ninguna ejecución las trata como error. Verificado: la suite entera pasa.

**R4 verificado, no creído**: P10 mete `docs/inventado.md` en un payload
desechable y comprueba `exit != 0`, que se nombra la ruta y que **no se ha
escrito nada** en el destino. Contra el instalador viejo P10 falla en las dos
aserciones que importan; contra el nuevo pasa. Además, con M1 se ve el
mecanismo de otra forma: el informe de mutación explica que borrar
`"progress/**"` de la política no desprotege, **aborta**, y por eso M2 se
repitió como M2 bis. Ese razonamiento es correcto y es de las cosas mejor
hechas de esta feature.

## 6. Las cinco decisiones del humano (punto 4 del encargo)

| Decisión | Aplicada | Dónde se ve |
|---|---|---|
| **D1** `.claude/settings.json` como `adaptado`, no intocable | **Sí** | `politica_ficheros.json`, lista `adaptado` |
| **D2** `docs/CONVENTIONS.md` como `adaptado` | **Sí** | ídem |
| **D3** `-IgnorarPrecondiciones` separado de `-Forzar` | **Sí** | `param()` con dos switches distintos y el comentario que explica por qué; P7 usa cada uno por separado y el bloqueo solo cede con el segundo |
| **D4** normalización de fin de línea dentro | **Sí** | `Get-EstadoContenido` con tercer estado `solo-eol`; P11 lo comprueba **en los dos sentidos**: el `.json` CRLF no se reescribe y un `.png` que solo difiere en un `0x0D` **sí** se actualiza |
| **D5** rigor `estandar` | **Sí** | `harness/features.json` |

Ninguna se ha aplicado «de otra manera». D4 en particular está mejor resuelta
de lo que pedía: la lista de extensiones de texto evita normalizar binarios, y
hay caso que lo vigila.

## 7. Recorrido de CHECKPOINTS.md

| Punto | Estado | Nota |
|---|---|---|
| **C1** init.sh exit 0 | **[x]** | Ejecutado por mí: `ENTORNO LISTO`, 305 passed en 110 s, arnés v1.6.1. Los dos `[AVISO]` (ruff, servicios sin tests) son deuda previa, no de F-035 |
| **C1** ficheros del arnés presentes | **[x]** | |
| **C2** ≤1 feature `in_progress` | **[x]** | Ninguna |
| **C2** rama `feature/F-XXX` | **N/A justificado** | En `albaranes` no hay código de esta feature; el trabajo vive en `arnes-base` (rama `main` de ese repo, que no usa el arnés). **Pero** `features.json` declara `branch: feature/F-035-instalador-no-pisa-estado`, que nunca se creó: o se crea, o se corrige el campo (ver CR-4) |
| **C2** `current.md` solo sesión activa | **[ ]** | `progress/current.md` no tiene sección de la **implementación** de F-035; la única entrada es la de cuando se escribió la spec. T15 lo pedía |
| **C3** arquitectura hexagonal | **N/A justificado** | PowerShell en otro repositorio; no hay capas de dominio/infra que separar. La separación equivalente sí se respeta: la **política es un fichero de datos fuera del payload**, no lógica cableada en el script |
| **C3** primera línea con la ruta | **[x]** | `# instalar_arnes.ps1`, `# tests_instalador/prueba_instalador.ps1`, `<!-- tests_instalador/README.md -->`. `politica_ficheros.json` no puede llevar comentario: usa `$doc`, que es el convenio del repo |
| **C3** sin prints de depuración, sin TODOs, sin secretos | **[x]** | Barrido sobre `git diff 89a9ba9..HEAD` con patrones `password/secret/api_key/token/connectionstring/subscription/tenant`, IPv4 y GUID: **cero coincidencias**. Los `Write-Host` son interfaz de usuario, no depuración |
| **C3 bis** documentos de fuera | **N/A justificado** | La feature no añade ni toca nada en `docs/referencia/` |
| **C4** cada requisito con ≥1 test trazable | **[ ]** | **R12 no tiene ningún caso** y **R11 no tiene ninguno que lo distinga** (demostrado con MR1). Sin test también: R15, R18, R20, R26 (la constancia en el manifiesto) y R27. Detalle en la tabla de cobertura |
| **C4** unit tests sin red ni BBDD | **[x]** | Repos de mentira en `%TEMP%` y `git init` local; ninguna llamada de red |
| **C4** verificaciones MANUAL listadas en `current.md` | **[ ]** | La parte de T16 que queda (repetir el `-SoloDiff` desde una rama limpia de `dev`) está en `impl_F-035.md` §7 con su comando exacto, pero **no** en `progress/current.md`, que es donde el checkpoint la pide |
| **C4 bis** rigor declarado | **[x]** | `estandar`, válido |
| **C4 bis** fase RED | **[x]** | Verificada por mí contra `89a9ba9` (§1) |
| **C4 bis** cobertura | **N/A justificado** | Puerta sin sujeto: 0 líneas de Python en el diff de `albaranes`. `init.sh` imprime el N/A con motivo |
| **C4 bis** mutación con totales verificados | **[x]** | Campaña MANUAL, tabla con texto exacto por fila; **dos filas reproducidas** por mí (M1, M3) y coincidentes (§2) |
| **C4 bis** los muertos comprobados, no contados | **[x]** | Reproducidos M1 y M3 ejecutando la suite entera, no recalculando |
| **C4 bis** campaña manual con una fila por mutante y texto exacto | **[x]** | Cumple. Es el formato que exige el checkpoint |
| **C4 bis** supervivientes analizados, ninguno en PENDIENTE | **[ ]** | El informe declara **0 supervivientes**. He encontrado uno (**MR1**, §3) que la campaña no probó. En `estandar` un superviviente no descalifica solo, pero este toca dos requisitos sin test y revierte una causa del incidente: exige caso nuevo, no párrafo |
| **C4 bis** sección «Evidencias» con los cuatro números | **[x]** | Presente y correcta |
| **C4 ter** rutas sensibles | **N/A justificado** | La puerta de `init.sh` no señaló rutas tocadas: el diff de `albaranes` no toca prompts, schemas, clientes LLM ni redes de sv6 |
| **C5** `tasks.md` con todo `[x]` y un commit `F-035 Tn:` por tarea | **[ ]** | **17 de 17 tareas siguen en `[ ]`**. En `arnes-base` los 12 commits T2–T14 están y son correctos; en `albaranes` los artefactos de T15 entraron dentro de `104de9b F-034 review 2a pasada (CHANGES_REQUESTED) e informes de F-035`, sin mensaje `F-035 T15:` |
| **C5** sin temporales ni artefactos sospechosos | **[x]** | `git status --porcelain` vacío en los **dos** repositorios, comprobado después de ejecutar la suite y todos mis mutantes (que corrieron siempre sobre copias en scratchpad) |
| **C5** `features.json` refleja el estado real | **[ ]** | F-035 sigue en **`spec_ready`** con la implementación entregada |

## 8. Cobertura requisito → verificación

| Req. | Cubierto por | |
|---|---|---|
| R1 política en la raíz, fuera del payload | inspección: existe en raíz y no aparece en `git ls-files arnes-base` | [x] |
| R2 cuatro listas | `Get-Politica` aborta (exit 2) si falta una; inspección | [x] |
| R3 especificidad | P1, P6, P13; **mutante M3 reproducido** | [x] |
| R4 aborta sin clasificar | **P10** (verificado también en rojo contra el viejo) | [x] |
| R5 rutas preventivas ausentes | implícito en toda ejecución (la política lista `.env`, `BACKLOG.md`, `specs/**`…) | [x] |
| R6 mínimo de `estado_del_proyecto` | política + P1, P2, P6 | [x] |
| R7 lista de `adaptado` | política + P4 | [x] |
| R8 lista de `arnes_puro` | política + P3 | [x] |
| R9 protegido: ni diff, ni pregunta, ni escritura | **P1, P2, P6** | [x] |
| R10 ninguna combinación lo sobrescribe | P1 (`-Forzar`), P7 (`-IgnorarPrecondiciones`), P13 (`-SoloDiff`); por construcción, la guarda va antes de bifurcar | [x] |
| R11 puro sin preguntar, previo backup | backup: P5. **«Sin preguntar»: NINGUNO** — MR1 sobrevive | **[ ]** |
| R12 `-PreguntarTodo` | **ninguno** (comprobado a mano por mí: funciona) | **[ ]** |
| R13 diff + pregunta con default CONSERVAR | P4; el literal del prompt, por inspección | [x] |
| R14 Intro conserva | P4 — y he confirmado que la rama que ejercita es la de Intro | [x] |
| R15 sin consola, conserva sin bucle | **ninguno**: el comentario de P4 dice que cubre «la consola no interactiva», pero con la entrada redirigida a fichero vacío `Read-Host` **devuelve cadena vacía** y entra por la rama de Intro (`(Intro) se CONSERVA`), no por el `catch` | **[ ]** |
| R16 ausente ⇒ se copia | instalación inicial de cada escenario (copia `progress/`, `features.json`…) | [x] |
| R17 backup con sello, fuera del repo | P5 | [x] |
| R18 backup no creable ⇒ aborta antes de escribir | **ninguno**; verificado a mano y **con un defecto**: ver CR-3 | **[ ]** |
| R19 copia previa al backup | P5 («la copia es la versión PREVIA») | [x] |
| R20 fallo de backup suelto ⇒ conserva y sale ≠ 0 | **ninguno** | **[ ]** |
| R21 MANIFIESTO con destino, versiones, parámetros, rama y commit | P5 (destino, commit, fichero); versiones y parámetros solo por inspección | [x] parcial |
| R22 imprime la ruta del backup | P5 | [x] |
| R23 `solo-eol` | **P11**, en los dos sentidos (texto y binario) | [x] |
| R24 excluidos | **P12** | [x] |
| R25 sucio en el alcance bloquea | **P7** y **P8** (el contraejemplo) | [x] |
| R26 `-IgnorarPrecondiciones` + constancia en el manifiesto | P7 cubre el flag; **la constancia en el manifiesto, ninguno** | [x] parcial |
| R27 aviso de rama y commits por detrás de `dev` | **ninguno** | **[ ]** |
| R28 aviso si el destino no es repo git | **ninguno**; verificado a mano por mí: el aviso sale | **[ ]** |
| R29 resumen con las siete cuentas | P6 (`Protegidos: 4`), P11 (`Iguales salvo finales de linea: 1`) | [x] |
| R30 lista las rutas protegidas | P6 (marca completa `[PROTEGIDO] <ruta>`, no la ruta suelta: buen detalle) | [x] |
| R31 `-SoloDiff` no escribe nada | **P13** | [x] |
| R32 modo `instalar` intacto | **P9** (pasaba ya en rojo: no-regresión legítima) | [x] |
| R33 `ARNES_VERSION.md` y `.gitignore` aditivo | P13 (no se reescribe con `-SoloDiff`) + implícito; la **idempotencia** del `.gitignore`, solo por inspección | [x] parcial |
| R34 PS 5.1 sin dependencias | la suite corre sin módulos; sin framework a propósito | [x] |
| R35 guía: categorías, política, backup, precondiciones | `GUIA_INSTALACION.md` §«Qué no puede pisar el instalador (1.6.1)» | [x] |
| R36 corregido «qué conservar casi siempre» | el literal ya no aparece en la guía | [x] |
| R37 versión MINOR siguiente | **desviación declarada**: 1.6.1 en vez de 1.7.0, por orden expresa del humano; el informe la escribe y la razona (el payload no cambia). Aceptada | [x] |
| R38 texto de `ARNES_VERSION.md` | reescrito: dice qué protege el instalador por sí mismo | [x] |
| R39 prueba de fuego con N features y `-Forzar` | **P1**, con N=7 | [x] |
| R40 (i)–(viii) | P2, P3, P4, P5, P7, P8, P9, P10 — **las ocho** | [x] |
| R41 salida ≠ 0 nombrando la comprobación | verificado en todas mis ejecuciones en rojo | [x] |

---

## Cambios requeridos

**CR-1 · Cerrar el superviviente MR1: R11 y R12 sin caso que los distinga.**
`tests_instalador/prueba_instalador.ps1`. Todos los casos que tocan el arnés
puro usan `-Forzar`, así que la suite sigue en verde con el atajo del arnés puro
anulado. Reproducción exacta, para que no haya que buscarla:
`instalar_arnes.ps1` línea 473,
`    if ($cat -eq 'puro' -and -not $PreguntarTodo -and -not $SoloDiff) {` →
`    if ($false) {` ⇒ `TODO VERDE: 47 comprobaciones`.
Añadir un caso **P14** con escenario sembrado y **sin `-Forzar`**:

1. `-Modo actualizar` ⇒ `.claude/agents/leader.md` ya no contiene
   `MODIFICADO POR EL PROYECTO`, la salida contiene
   `[ACTUALIZADO] .claude/agents/leader.md` y **no** contiene una línea de
   prompt para ese fichero (R11);
2. `-Modo actualizar -PreguntarTodo` sobre un escenario nuevo ⇒ el mismo
   fichero **sí** conserva su marcador (R12).

Después, volver a aplicar MR1 y comprobar que **muere**. El comportamiento ya
es correcto —lo verifiqué a mano—, así que esto es escribir la red, no arreglar
el producto.

**CR-2 · Corregir el comentario falso de P4 y cubrir R15.**
`tests_instalador/prueba_instalador.ps1`, cabecera de `Test-P4`: dice «Invoke
Instalador redirige la entrada estándar a un fichero vacío: es exactamente el
caso de la consola no interactiva». **No lo es.** Con esa redirección
`Read-Host` devuelve cadena vacía y se ejecuta la rama de **Intro** (lo he
comprobado: la salida trae `(Intro) se CONSERVA CLAUDE.md`, nunca `Sin consola
de la que leer`). El `catch` de R15 no lo ejecuta ningún caso. Corregir el
comentario (P4 cubre R13/R14, que ya es valioso) y, o bien añadir un caso que
llegue de verdad al `catch`, o declarar R15 como verificado solo por
inspección y decirlo en el informe. Lo que no puede quedarse es el comentario
afirmando lo que no hace.

**CR-3 · R18: la guarda del backup tiene un agujero por el que su propio
mensaje no llega a imprimirse.** `instalar_arnes.ps1`, `New-DirectorioBackup`,
línea 305: el `Join-Path` que construye la ruta está **fuera** del `try`. Con
`-DirBackup` apuntando a una raíz irresoluble, PowerShell lanza
`DriveNotFoundException` antes de entrar en el `try`, y el instalador termina
con un volcado de excepción en crudo y **exit 1** en vez del mensaje que el
autor escribió («Se aborta ANTES de escribir nada en el destino. Prueba con
-DirBackup <ruta>») y **exit 4**. Verificado por mí:

```
Join-Path : No se encuentra la unidad. No existe ninguna unidad con el nombre 'Z'.
En ...\instalar_arnes.ps1: 305 Carácter: 24
   codigo=1
   no ha escrito nada en el destino (R18 OK)
```

El resultado seguro se salva (no escribe nada), por eso no es un defecto grave,
pero el `exit 1` colisiona con el que ya significa «no aplicados por fallo de
backup», y el humano recibe una traza de PowerShell en lugar de la instrucción
de qué hacer. Meter la construcción de la ruta dentro del `try` (o usar
`[IO.Path]::Combine`) y añadir la aserción a un caso.

**CR-4 · Cerrar C5, que está entero sin hacer.** Cuatro cosas, todas en
`albaranes`:

1. `specs/F-035-instalador-no-pisa-estado/tasks.md`: **17 de 17 tareas en
   `[ ]`**. Marcar las hechas y dejar explícito lo que queda (la parte MANUAL
   de T16 es del humano).
2. `harness/features.json`: F-035 sigue en **`spec_ready`**. Y declara
   `branch: feature/F-035-instalador-no-pisa-estado`, que nunca existió: o se
   crea la rama, o se corrige el campo con la nota de que el código vive en
   `arnes-base`.
3. `progress/current.md`: no hay sección de la implementación de F-035 (T15 la
   pedía) y **la verificación MANUAL pendiente no está listada allí con su
   comando exacto**, como exige C4. Hoy solo vive en `impl_F-035.md` §7.
4. Los artefactos de T15 entraron en el commit `104de9b F-034 review 2a pasada
   (CHANGES_REQUESTED) e informes de F-035`, sin el `F-035 T15:` que pide la
   convención. No se reescribe historia por esto: basta con que los commits que
   cierren F-035 lleven su prefijo.

> Sobre CR-4: el informe del implementer **avisa** de que `current.md` y
> `features.json` los tenía ocupados el agente de F-034 y los deja al líder.
> La restricción operativa es real y está bien documentada, pero el checkpoint
> sigue vacío y esto se cierra antes de dar por buena la feature, no después.

---

## Lo que está bien y merece constar

- La guarda de categoría (c) va **antes** de bifurcar por modo, por `-Forzar` y
  por el diálogo. Eso hace R10 cierto **por construcción**, no por revisión: no
  existe camino desde la tecla `T` hasta un fichero de estado. Es la decisión
  de diseño correcta.
- Los `excluidos` resueltos **antes** que las categorías, con el comentario que
  explica por qué (`harness/**` le ganaría a `**/*.pyc` por longitud de
  prefijo). Descubierto por P12, no por suerte.
- `Assert-Contiene` usa `.Contains` y no `-like`, con el comentario que explica
  que `-like` trataba `[PROTEGIDO]` como clase de caracteres y hacía pasar la
  comprobación sin que el fichero estuviera protegido. Es exactamente el tipo
  de falso verde que un reviewer busca, y lo cazaron ellos.
- P6 busca la marca completa `[PROTEGIDO] <ruta>` y no la ruta suelta, «porque
  la ruta a secas también aparece dentro de un diff». Mismo nivel de cuidado.
- El análisis de M2 → M2 bis en `mutacion_F-035.md`: detectar que el mutante
  moría por la comprobación de integridad y no por el caso previsto, y
  repetirlo bien en vez de apuntarse el muerto, es justo lo que F-034 vino a
  corregir en el mutador. Aquí se ha aplicado a mano y por iniciativa propia.
- La desviación de R37 (1.6.1 en vez de 1.7.0) está **declarada como
  desviación**, con el argumento a favor y señalando que contradice la spec.
  Así es como se entrega una orden del humano que choca con el papel.

## Propuesta de mejora del protocolo (no aplicada; la decide el humano)

`CHECKPOINTS.md`, bloque **C4 bis**, punto de la campaña manual. Hoy exige
reproducir «al menos dos filas» de la tabla, y eso comprueba que los **muertos
declarados** lo están. No exige lo que ha encontrado el fallo de esta feature:
**generar al menos un mutante propio**, distinto de los de la tabla, sobre la
guarda que el implementer *no* eligió mutar. Reproducir muertos ajenos verifica
honradez; inventar uno propio verifica **cobertura**. Sugiero añadir al punto:
«el reviewer genera además **un mutante propio** sobre una decisión del código
que la tabla no cubra, y lo ejecuta: si sobrevive, es un hueco de la suite y
exige caso nuevo». Vale para cualquier proyecto, así que iría a `arnes-base`.

Segunda, menor, para `.claude/agents/reviewer.md`: la regla de reejecutar la
campaña por debajo de 5 minutos está escrita solo para la campaña automática.
Cuando la campaña es **manual** (proyecto no Python, o código en otro
repositorio) no hay «Tiempo total» que mirar, y conviene decir qué la sustituye
—reproducir filas **y** generar un mutante propio—, que es lo que he hecho aquí
a falta de instrucción explícita.

---

**Veredicto: CHANGES_REQUESTED** — CR-1 a CR-4.

El arreglo funciona y está bien pensado; lo he verificado con el instalador
anterior en la mano. Lo que falta es que la red que lo vigila cubra las dos
mitades del arreglo, no solo la que da miedo: **el estado ya no se pisa (bien
probado), pero que el arnés genérico siga aplicándose sin interrogatorio no lo
prueba nadie**, y ese interrogatorio es la mitad de la historia del 2026-08-19.

---

# Segunda pasada (2026-08-20)

**Veredicto: APPROVED**, con tres condiciones de cierre nombradas al final que
son de bookkeeping del líder, no cambios de producto.

**Desde dónde reviso.** Revisión **incremental**: solo
`git -C ...\arnes-base diff b6ac623..HEAD` (cuatro commits: `efdfbe7`,
`d64be41`, `d937012`, `9e2ced7`) más los cambios documentales de `albaranes`
desde `0762f2b` (`c86b488`, `b1f7924`). Todo lo que la primera pasada dio por
bueno —la política contra el payload real, las cinco decisiones del humano, la
fase RED contra `89a9ba9`, las filas M1 y M3 de la campaña manual— queda dado
por bueno y no se vuelve a mirar.

Entregado ahora como **1.6.2**. `arnes-base` limpio
(`git status --porcelain` vacío) y sin `push`, comprobado por mí en los dos
repositorios.

---

## CR-1 · CERRADO. El mutante MR1 muere, y lo he matado yo

Era el punto crítico del encargo, así que no me he fiado del informe. Copié el
árbol de `arnes-base` al scratchpad, apliqué **la misma mutación** que encontró
la primera pasada —`instalar_arnes.ps1`, hoy línea 481,
`    if ($cat -eq 'puro' -and -not $PreguntarTodo -and -not $SoloDiff) {` →
`    if ($false) {`, con `assert` de que el literal aparecía **exactamente una
vez** antes de sustituir— y ejecuté la suite entera:

```
### P14 - el arnes puro se aplica sin preguntar; -PreguntarTodo si pregunta (R11, R12)
  [FALLO] sin -Forzar, el arnes puro se pone al dia igualmente (R11)
          aparece <MODIFICADO POR EL PROYECTO> y no deberia
  [FALLO] y el resumen lo da por actualizado
          no aparece <[ACTUALIZADO] .claude/agents/leader.md> en la salida
  [FALLO] no se ha preguntado por el
          aparece <.claude/agents/leader.md : [N] conservar el tuyo> y no deberia
...
FALLOS: 4 de 65 comprobaciones.
```

**MUERTO.** Donde antes salía `TODO VERDE: 47 comprobaciones`, ahora caen tres
aserciones de P14 y una cuarta de propina: P15 detecta que el prompt de
`leader.md` también pasa por el diálogo (`esperado <1>, obtenido <2>` en la
cuenta de «Sin consola de la que leer»). El agujero no solo está tapado: está
tapado por dos sitios.

Sobre el diseño de P14, dos aciertos que merecen constar. Usa **el literal
exacto del prompt** (`.claude/agents/leader.md : [N] conservar el tuyo`) en vez
de buscar la ruta suelta, que aparecería igualmente dentro de un diff —el mismo
cuidado que ya tenía P6—. Y para R12 monta un **escenario nuevo**, porque en el
anterior `leader.md` ya había quedado al día y no habría nada que preguntar: es
la clase de detalle que convierte un caso en verde permanente sin que nadie se
entere.

Suite limpia, restaurando la copia: **TODO VERDE: 65 comprobaciones**, exit 0,
**67 s** (eran 47 y 42 s en la 1.6.1).

## CR-2 · CERRADO, y P15 llega de verdad al `catch`

Dos mitades, las dos comprobadas.

**El comentario de P4 ya no miente.** Dice ahora lo contrario de lo que decía
—que redirigir la entrada estándar a un fichero vacío **no** es la consola no
interactiva— y remite a P15. Mejor todavía: P4 **añade la aserción que lo
fija**, `Assert-Contiene $r.Texto '(Intro) se CONSERVA CLAUDE.md'`. Eso convierte
el comentario en algo comprobable: si alguien cambiase el arnés para que esa
redirección cayera por el `catch`, P4 fallaría en vez de seguir en verde
diciendo una cosa y probando otra. Un comentario corregido se vuelve a pudrir;
una aserción, no.

**R15 ya tiene caso, y no es de adorno.** P15 lanza `powershell.exe` con
`-NonInteractive` (switch `-SinConsola` nuevo en `Invoke-Instalador`), que es lo
único que hace que `Read-Host` **lance excepción** en lugar de devolver cadena
vacía. Que llega al `catch` lo prueba la propia aserción
`'Sin consola de la que leer'`, pero eso solo demuestra que la rama se ejecuta,
no que se compruebe lo que hace. Así que generé **un mutante propio**, distinto
de los del informe, dentro del `catch` (línea 523):

| Mutante | Sustitución | Resultado |
|---|---|---|
| **MR2** (mío) | `            $respuesta = 'n'` → `            $respuesta = 's'` | **MUERTO**: 2 de 65, **las dos en P15** («CLAUDE.md se conserva, que es lo seguro» y «el resumen lo da por conservado») |

Muere solo ahí, que es exactamente lo que debe pasar: ningún otro caso alcanza
esa rama. Sin P15 el mutante sobrevivía entero, tal como declara `d64be41`.

Y P15 comprueba además que **se intenta una sola vez** contando las apariciones
del mensaje. No es cosmético: hasta la 1.6.0 se preguntaba cinco veces, y en una
consola sin entrada eso es un bucle que cuelga a quien lance el instalador. Es
justamente el modo de fallo que un agente automatizado sufriría en silencio.

## CR-3 · CERRADO. Verificado por dos vías independientes

**(a) Que P16 es guarda de verdad, no acompañamiento.** Revertí el arreglo en la
copia del scratchpad —volviendo a `Join-Path (Join-Path ...) ...` **fuera** del
`try`, la forma de la 1.6.1— y ejecuté la suite:

```
### P16 - raiz de backup irresoluble: exit 4, mensaje propio y nada escrito (R18)
  [FALLO] sale con el codigo 4 ...  esperado <4>, obtenido <1>
  [FALLO] imprime el diagnostico
  [FALLO] y dice que hacer
  [FALLO] no hay volcado de excepcion en crudo -- aparece <Join-Path> y no deberia
  [OK]    no ha escrito nada en el destino
```

Cuatro de cinco, y **la quinta pasa**: el resultado seguro se salvaba también
antes. Esa quinta aserción en verde es la que hace honesto el caso —dice la
verdad sobre qué estaba mal y qué no—, y coincide fila a fila con lo que declara
`d937012`.

**(b) Ejecución manual del instalador REAL**, fuera de la suite, contra un
repositorio de mentira montado por mí en el scratchpad y con una letra de unidad
que en esta máquina no existe:

```
=== Arnes v1.6.2 (2026-08-20) -> ...\scratchpad\p2\destino
Rama del destino: master (8b945b9)
No puedo crear el directorio de backup en Z:\no_existe_backup\destino\20260820-112810
  No se encuentra la unidad. No existe ninguna unidad con el nombre 'Z'.
Se aborta ANTES de escribir nada en el destino. Prueba con -DirBackup <ruta>.
EXITCODE=4
--- el destino sigue intacto? ---
MODIFICADO POR EL PROYECTO
```

Está todo lo que faltaba: el **exit 4** en vez del 1 que ya significaba otra
cosa, el diagnóstico, **la causa** («no existe ninguna unidad con el nombre
'Z'») y **qué hacer**, sin una línea de traza de PowerShell. Y el destino
intacto.

Dos detalles del arreglo que están bien pensados. `[IO.Path]::Combine` es
composición de cadenas pura y no resuelve la unidad, así que el fallo lo levanta
`New-Item` **dentro** del `try`, que es donde tiene que salir. Y P16 **busca una
letra libre en la máquina** en vez de cablear `Z:`, con el comentario que
explica por qué: en otra máquina `Z:` puede ser una unidad de red montada y el
caso dejaría de probar lo que dice probar. Eso es un test que sigue siendo
verdad fuera de aquí.

También es correcto que la aserción sea `Assert-NoContiene $r.Texto 'Join-Path'`
y no el texto del error: el texto cambia con el idioma de Windows y el nombre
del cmdlet no. Sigue siendo la guarda exacta de la regresión.

## Commit extra `9e2ced7` · OK, y no ha pisado nada

Comprobado lo que pedía el encargo, que era el riesgo real de este porte:

- **Solo añade lo que dice.** En el diff completo del fichero de tests hay
  **una única línea borrada** en todo el commit: el `from harness.mutacion
  import ...` que se reescribe en bloque para meter `_delimitado` y
  `_es_palabra`. Todo lo demás son inserciones: los tres tests y el fixture
  `FUENTE_COMENTARIO_ISLA`.
- **La variante genérica del último test sigue en pie.** `arnes-base` termina
  con `test_la_declaracion_de_rutas_sensibles_dice_cuando_sube_a_bloqueo`
  (genérica, se salta si el repositorio no declara `rutas_sensibles.json`) y
  `albaranes` con
  `test_f034_r14_la_puerta_de_evals_no_se_declara_sobre_lo_no_versionado`
  (atada a los fixtures de evals). La divergencia deliberada está
  intacta, y los tres tests portados caen en las **mismas líneas** (244, 266,
  276, 281) en los dos ficheros.
- **Suite del payload verificada por mí**: `11 passed, 1 skipped` en
  `test_mutacion_operadores.py` (el skip es el de rutas sensibles, por diseño),
  y **46 passed, 1 skipped, 1 failed** en la suite completa. Los 46 confirman
  los 43 + 3. El fallo es `test_backlog_md`, **preexistente y ajeno**:
  comprobé que `arnes-base/BACKLOG.md` tampoco existía en `b6ac623`, porque el
  payload es una plantilla y no un proyecto instalado.

Sobre el fondo: el diagnóstico es correcto y molesto de admitir. La 1.6.0 portó
el mutador **antes** de que existieran los tests que lo protegen, así que quien
instaló 1.6.0 o 1.6.1 se llevó `_es_palabra` y `_delimitado` sin la red. Que se
haya detectado y cerrado por iniciativa propia, y que el commit deje escritos
los dos mutantes de comprobación, es la regla de propagación funcionando de
verdad y no solo citada.

## CR-4 · CERRADO en lo sustantivo

| Lo que pedía CR-4 | Estado |
|---|---|
| `tasks.md` con las tareas marcadas | **[x]** T1–T15 en `[x]`. Quedan T16 y T17, ver condiciones de cierre |
| `features.json` con F-035 fuera de `spec_ready` | **[x]** `in_progress`, con `NOTA DE RAMA` explicando que el código vive en `arnes-base` y que esta rama sostiene spec, informe y rastro |
| La rama, que no existía | **[x]** creada: `init.sh` imprime `Rama actual: feature/F-035-instalador-no-pisa-estado` |
| `current.md` con la verificación MANUAL y su comando exacto | **[x]** sección de F-035 con el bloque `powershell` completo, qué comprobar y por qué es seguro (`-SoloDiff` no escribe, lo prueba P13) |
| Commits con prefijo `F-035` | **[x]** `c86b488` y `b1f7924`. `b1f7924` va aparte y **dice por qué** —el commit anterior se comió `current.md` por el escape de una ruta de Windows— en vez de disimularlo dentro del otro |

**T16 dada por buena** según lo indicado en el encargo: la ejecutó el humano el
20-ago y salió `Protegidos: 4`, que son **exactamente los cuatro ficheros que el
incidente del 19-ago destruyó** (`docs/ARCHITECTURE.md`,
`harness/features.json`, `progress/current.md`, `progress/history.md`), con 11
«iguales salvo finales de línea». Ese dato no es papeleo: es la feature entera
demostrada contra el repositorio real y contra el incidente que la originó.

**T17 verificada por mí ahora**: `bash harness/init.sh` → **ENTORNO LISTO**,
`305 passed in 109.25s`, `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python
de producción frente a dev)` y `PUERTA RUTAS SENSIBLES [evals]: N/A (F-035 no
toca ninguna ruta sensible declarada)`. Los dos N/A vienen ahora **con el motivo
de esta feature impreso**, no con el genérico de rama, que es mejor de lo que
había en la primera pasada.

## La versión 1.6.2: bien numerada y bien documentada

**Bien numerada.** El criterio de este repositorio está escrito y es de
comportamiento, no de recuento de ficheros: la 1.6.0 fue MINOR «porque cambia la
vara de medir… los informes de mutación anteriores no son comparables con los de
después». Por ese mismo criterio la 1.6.2 es PATCH: no cambia nada de lo que el
arnés instalado exige a un proyecto. Los tres tests portados verifican
`harness/mutacion.py`, que es arnés puro y va a la misma versión, así que no
pueden poner en rojo a nadie al actualizar —lo confirman mis 46 passed—. Sigue
además el precedente ya aceptado por el humano en la 1.6.1 frente a R37.

**Bien documentada, y con un detalle que casi nadie hace**: al subir la suite de
47 a 65 comprobaciones, la sección **de la 1.6.1** se corrigió para no seguir
afirmando «13 casos (47 comprobaciones)», y remite a la sección nueva. He
barrido la guía: no queda ninguna cifra obsoleta. La sección de la 1.6.2 explica
el defecto, por qué el exit 1 era ambiguo, los tres casos nuevos y el porte de
los tests, y la lista de «Ficheros de la 1.6.2» se actualizó al añadirse
`9e2ced7`. El párrafo de cabecera también se reescribió cuando dejó de ser
cierto que «no cambia nada del arnés instalado». Eso es mantener un documento,
no adjuntarlo.

## Recorrido de CHECKPOINTS.md — solo lo que cambia

| Punto | Antes | Ahora | Nota |
|---|---|---|---|
| **C1** init.sh exit 0 | [x] | **[x]** | ENTORNO LISTO, 305 passed, arnés 1.6.2 |
| **C2** rama `feature/F-XXX` | N/A | **[x]** | La rama existe y es la activa. Deja de hacer falta el N/A |
| **C2** `current.md` solo sesión activa | [ ] | **[x]** | Sección de F-035 presente |
| **C4** cada requisito con ≥1 test | [ ] | **[x]** | R11, R12 (P14), R15 (P15) y R18 (P16) tienen caso propio, los cuatro verificados por mutación |
| **C4** verificaciones MANUAL en `current.md` | [ ] | **[x]** | T16 con su comando exacto |
| **C4 bis** supervivientes analizados | [ ] | **[x]** | MR1 cerrado y **matado por mí**; MR2, mutante propio de esta pasada, también muere |
| **C5** `tasks.md` con todo `[x]` | [ ] | **[x] con condición** | T1–T15 marcadas; T16 (humano, hecha) y T17 (verificada por mí) solo falta tildarlas al cerrar |
| **C5** `features.json` estado real | [ ] | **[x] con condición** | `in_progress` correcto; la `NOTA DE RAMA` cita 1.6.1, ver condición 3 |
| **C5** sin artefactos sueltos | [x] | **[x] con condición** | `arnes-base` limpio; en `albaranes` quedan 208 líneas sin commitear, ver condición 1 |

Los requisitos que la primera pasada dejó con `[ ]` o `[x] parcial` y que esta
pasada **no** tocaba (R20, R26 constancia en el manifiesto, R27, R28, R21/R33
parciales) siguen igual. No eran cambios requeridos —los dejé fuera de los CR a
propósito— y no lo son ahora: quedan anotados como deuda conocida de la suite
del instalador, para cuando vuelva a tocarse.

---

## Condiciones de cierre (del líder, en el commit que cierre F-035)

No son cambios de producto ni reabren nada. Son las tres cosas que, por
construcción, solo pueden hacerse en el momento de cerrar. La aprobación va
condicionada a que entren en ese commit:

1. **Commitear `progress/impl_F-035.md`.** Tiene **208 líneas sin commitear**
   (el addendum de la segunda pasada). El implementer lo dejó así **a propósito
   y lo dice por escrito**, porque tenía prohibido tocar `albaranes`; la razón
   es buena, pero el rastro del arnés no puede quedarse en el árbol de trabajo,
   que es exactamente cómo se estuvo a punto de perder todo el 19-ago. Con
   prefijo `F-035`.
2. **Tildar T16 y T17** en `tasks.md`, con la nota de que T16 la ejecutó el
   humano el 20-ago (`Protegidos: 4`, los cuatro del incidente) y que T17 quedó
   verificada en esta review.
3. **Refrescar las dos referencias a 1.6.1.** La `NOTA DE RAMA` de
   `harness/features.json` dice «commits de `arnes-base` `1e67231..b6ac623`
   (versión **1.6.1**)» y la sección de `current.md` dice **1.6.1** y «CR-1,
   CR-2 y CR-3 **en curso**». Lo entregado es **1.6.2**, hasta `9e2ced7`, y los
   tres CR están cerrados. Se escribieron antes de que existiera esta ronda, así
   que no es un descuido; pero es el fichero de estado del proyecto en la feature
   que trata precisamente de no perder el estado del proyecto, y ahí conviene
   predicar con el ejemplo.

## Propuesta de mejora del protocolo (se mantiene, y esta pasada la confirma)

La propuesta de la primera pasada —que el reviewer **genere un mutante propio**
sobre una decisión que la tabla del implementer no cubra— ha vuelto a ganarse el
sitio. En esta pasada, MR2 (`$respuesta = 'n'` → `'s'` dentro del `catch`) es lo
único que separa «P15 ejecuta la rama» de «P15 comprueba la rama»: la aserción
del mensaje sola habría pasado igual con el mutante puesto en la mitad de sus
comprobaciones. Reproducir muertos ajenos verifica honradez; inventar uno propio
verifica cobertura, y es lo que ha encontrado algo en las dos pasadas.

Segunda, menor y nueva: `harness/init.sh` avisa de **marcas `[ADAPTAR]` sin
resolver** en `specs/F-035-.../design.md` y `requirements.md`. Es un **falso
positivo**: ahí `[ADAPTAR]` no es un hueco de plantilla, es el nombre del
marcador citado como criterio de clasificación («el criterio discriminante no es
"tiene marcas `[ADAPTAR]`"»). Una spec que hable del arnés siempre disparará ese
aviso. Sugiero excluir las líneas donde la marca aparece entre comillas o dentro
de una tabla, o al menos que el aviso diga que puede ser una cita. Es AVISO y no
bloquea, pero un aviso que siempre está encendido deja de leerse.

---

**Veredicto: APPROVED** — CR-1, CR-2, CR-3 y CR-4 cerrados, con las tres
condiciones de cierre de arriba.

Lo que hacía falta ya está: la red cubre las **dos** mitades del arreglo. Que el
estado del proyecto no se pise lo probaban trece casos; que el arnés genérico
siga aplicándose **sin interrogatorio** —la otra mitad de la historia del
2026-08-19, la que hace que alguien pulse `T`— ahora lo prueba P14, y lo he
comprobado matando el mutante yo mismo. De regalo, dos defectos que nadie había
pedido buscar: un `catch` que no ejercitaba nadie y un mensaje de aborto que
estaba escrito pero no llegaba a imprimirse nunca.
