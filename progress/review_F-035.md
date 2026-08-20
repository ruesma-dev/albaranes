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
