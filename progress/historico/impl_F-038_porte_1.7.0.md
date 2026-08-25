<!-- progress/impl_F-038_porte_1.7.0.md -->
# F-038 · Tarea P1: porte del arnés a `arnes-base` como 1.7.0

Regla de propagación del `CLAUDE.md`. F-038 quedó cerrada y mergeada en `dev`
(merge `816fb94`); esto lleva sus mejoras genéricas al arnés versionado.

- **Destino:** `C:\Users\pgris\PycharmProjects\arnes-base`, rama `main`.
- **Versión:** `arnes-base/harness/VERSION` pasa de **1.6.3** a **1.7.0**.
- **Commits:** `ed4b5a8`, `0e062b3`, `357d324`, `d0eb8ea`, `3a2a71f`,
  `c6d4979`. Sin `git push` ni PR, como se pidió.
- **`albaranes` no se ha tocado** salvo este fichero.

## 1. No fue copiar: fue integrar

El aviso del encargo se confirmó, y la medida exacta de la divergencia es esta
(diff de `albaranes@34dada0`, o sea PRE-F-038, contra `arnes-base@f1b250e`):

| Fichero | Divergencia real | Cómo se portó |
|---|---|---|
| `harness/mutacion.py` | **solo** el arreglo de bytecode de la 1.6.3 (13 líneas) | `patch` del diff de F-038 |
| `harness/init.sh` | solo adaptaciones de proyecto (`[ADAPTAR]`, `REQUIERE_ENV`) | `patch` |
| `CHECKPOINTS.md` | adaptaciones + dos puntos nuevos de la 1.6.3 | `patch` + **1 hunk a mano** |
| `.claude/agents/reviewer.md` | 6 líneas de la 1.6.3 | `patch` |
| `mutacion_paralela.py`, `rigor.py`, `rigor.json`, `specs/SPECS.md`, `implementer.md`, `spec-author.md` | **ninguna: byte a byte idénticos** | copia directa |

De 19 hunks en `mutacion.py`, **19 aplicaron**; el `env={**os.environ,
"PYTHONDONTWRITEBYTECODE": "1"}` de la 1.6.3 sigue en su sitio (verificado:
`harness/mutacion.py:560`), dentro del mismo `subprocess.run` que ahora recibe
la ruta acotada. El único hunk rechazado en todo el porte fue el de
`CHECKPOINTS.md`, exactamente donde la 1.6.3 había escrito.

### El conflicto de C4 bis, y por qué no bastaba con quedarse con uno

La 1.6.3 añadió a C4 bis dos puntos que no existen en el origen: el **coste por
mutante con el factor de workers** y la **cabecera de campaña no válida**.
F-038 añade ahí RM1, RM2, RM5 y RM6. Se conservan los dos lados, pero **no
puestos uno detrás de otro**: se contradecían.

- La 1.6.3 decía que un coste «muy por debajo del tiempo de la suite» es
  sospechoso.
- RM2 dice lo contrario para ese caso: la campaña evalúa con `-x`, el mutante
  que muere aborta la suite en el primer fallo, y **a más muertos más baja la
  media**, así que una media por debajo de la línea base es normal.

Integración elegida: la regla de la 1.6.3 se queda con su señal dura —**por
debajo de un segundo** es sospechoso por construcción, que es el síntoma del
bytecode envenenado— y **delega explícitamente en RM2** el juicio de «bajo pero
mayor que un segundo», que ya trabaja sobre datos impresos. A cambio, RM2 gana
el matiz que le faltaba y que la 1.6.3 sí tenía: en campaña **paralela**,
«Tiempo total» es tiempo de reloj y hay que multiplicarlo por los workers para
compararlo con `mutantes × media`; la línea base y la media, no.

Ninguna de las dos partes perdió trabajo, y no hizo falta bloquear.

## 2. Qué se portó

Los siete puntos del encargo, todos:

1. **T0** — `ejecutor_para` acota la suite de la raíz a `tests` cuando el
   fichero no cae en ningún servicio Python y `<raiz>/tests` existe.
   `EjecutorPytest` gana `ruta`, aplicada también a la línea base y presente en
   `identidad()`.
2. **Muestreo por nivel** — `max_mutantes` y `semilla` en `rigor.json`
   (`estandar` 20 / semilla `20260820`; `critico` sin tope), lectores en
   `rigor.py`, `resolver_muestreo` como sede única de la precedencia
   (`--max-mutantes` > nivel > sin tope) y `--max-mutantes 0` = sin tope.
3. **`nivel_por_defecto`** de `critico` a `estandar`.
4. **El informe imprime** SHA completo de HEAD, línea base en segundos por
   ejecutor (`n/d`, nunca cero), media por mutante y la línea de muestreo con
   su nivel. Propagado en la campaña paralela (`fusionar`).
5. **Puerta de tamaño** — `harness/tamano.py` (nuevo), sección **7 quater** de
   `init.sh` y el bloque `tamano` de `rigor.json` con los topes
   **150 / 250 / 220 / 140**. Son los **recalibrados**, no los 120/200/150/100
   originales; la guía lo dice explícitamente para quien los vea citados.
6. **Documentos** — topes en `specs/SPECS.md` y en los tres agentes; en
   `reviewer.md` el umbral de 5 min → **60 s**, la revisión **incremental por
   defecto** declarando el SHA base y las reglas **RM1–RM6**; en
   `CHECKPOINTS.md`, C4 bis con el umbral y los checkbox de RM1, RM2, RM5 y
   RM6, con **RM5 solo en `critico` y muestra de uno** y **RM2 por salto de
   orden de magnitud**.
7. **Los cinco tests**, renombrados a la convención del destino (allí ningún
   test lleva `F-XXX` ni números de requisito en el nombre):

   | En `albaranes` | En `arnes-base` |
   |---|---|
   | `test_f038_r1_r4_ejecutor_raiz.py` | `test_mutacion_ejecutor_raiz.py` |
   | `test_f038_r5_r9_muestreo_por_nivel.py` | `test_mutacion_muestreo_por_nivel.py` |
   | `test_f038_r10_r12_informe.py` | `test_mutacion_informe_trazabilidad.py` |
   | `test_f038_r13_r16_tamano.py` | `test_tamano.py` |
   | `test_f038_r17_r21_documentos.py` | `test_documentos_del_arnes.py` |

Además, del `features.json` viajó **solo** el `$rigor_doc` (la parte genérica),
no el backlog.

## 3. La deuda del encargo: saldada

En un proyecto no-Python, ni la puerta de **cobertura** ni la nueva de
**tamaño** imprimían nada, mientras `CHECKPOINTS.md` promete un N/A «con su
motivo impreso». Un tramo mudo no es un N/A: es un checkbox que ningún reviewer
puede marcar ni justificar. Era barato, así que se arregló: cada una imprime
ahora su motivo, distinguiendo «proyecto sin Python» de «no hay intérprete en
el PATH». Se corrigió de paso la frase de `CHECKPOINTS.md` que decía «ambas
herramientas» cuando ya son tres comandos.

## 4. Qué NO se portó, y por qué

- **`BACKLOG.md`, `features.json` (backlog), `specs/F-038-*/`, `progress/*`**:
  estado del proyecto, no arnés. `politica_ficheros.json` los clasifica así.
- **El arreglo T17 de `tests/test_f012_r1_r5_r11_coordinador.py`** (extender el
  filtro de filas de reloj con `| Media por mutante`): **no tiene destino**.
  `arnes-base` no lleva ese test de paridad serie/paralelo, así que no hay nada
  que arreglar allí. La fusión que ese test cubría en `albaranes`
  (`sha_head` y `segundos_linea_base`) sí queda cubierta en el destino, por
  `test_mutacion_informe_trazabilidad.py`, que importa `fusionar`.
- **Las entradas históricas de la guía (1.5.2, 1.6.3) que citan «5 minutos»**:
  son un registro de cambios y se dejan como están; la entrada de la 1.7.0 dice
  que las sustituye. Sí se corrigieron las dos secciones de **referencia** que
  quedaban desfasadas (el nivel por defecto y la ficha de la campaña).

## 5. Dos cosas que aparecieron y hubo que arreglar

1. **`arnes-base/BACKLOG.md` no existía** y `tests/test_backlog_md.py` —que
   viaja en el payload— fallaba dentro del propio repositorio desde antes de
   este trabajo. Se generó la semilla con `python harness/backlog.py`. Es
   `estado_del_proyecto`, así que el instalador nunca la escribe sobre la de un
   proyecto real.
2. **`.coverage` y `coverage.json` tumbaban al instalador.** Los genera el
   propio `init.sh`, git no los versiona, pero el instalador barre el **disco**:
   en cuanto ejecuté el portero dentro del payload para verificar la puerta de
   tamaño, la prueba del instalador abortó con «ficheros del payload sin
   clasificar». Añadidos a `excluidos` en `politica_ficheros.json`, que es
   literalmente la categoría descrita para esto.

## 6. Entrada de `GUIA_INSTALACION.md`

Escrita con los **cuatro avisos** exigidos, al principio y en ese orden:
`nivel_por_defecto` a `estandar` (y «`critico` se declara, no se hereda»);
campañas `estandar` muestreadas a 20 con semilla fija y **números no
comparables** con versiones anteriores; **puerta nueva** que pone el portero en
rojo, con sus cuatro topes; y la orden de **repetir las campañas antiguas**
sobre ficheros que no pertenecen a ningún servicio. Cierra con «Qué hacer al
actualizar» en cuatro pasos y la lista de ficheros de la versión.

## 7. Evidencias

Números reales, medidos en el destino. Todo en serie: nada en paralelo.

| Evidencia | Resultado |
|---|---|
| Suite de `arnes-base` **antes** del porte | `1 failed, 47 passed, 1 skipped in 17.24s` (el fallo, `test_backlog_md.py`, ya venía de antes) |
| Suite de `arnes-base` **después** | `134 passed, 1 skipped in 17.74s` — **verde**, `python -m pytest tests -q` desde `arnes-base/arnes-base` |
| Tests añadidos | **+86** (de 49 recogidos a 135) |
| Prueba del instalador | `TODO VERDE: 65 comprobaciones.` (`tests_instalador\prueba_instalador.ps1`, exit 0) |
| `ruff check .` en el payload | **40 avisos antes, 40 después** — el porte no añade deuda de lint (el «antes» se midió sobre un `git archive HEAD` en el scratchpad, no a ojo) |
| Sección 7 quater viva | `bash harness/init.sh` imprime `[AVISO] PUERTA TAMAÑO: N/A (…no hay papeleo que medir)` |
| Árbol de `arnes-base` | limpio tras los seis commits |

**Cobertura de líneas cambiadas y campaña de mutación: no se midieron**, y el
motivo no es el lenguaje. `arnes-base` es un repositorio de payload sin rama de
feature ni `features.json` real: `harness/cobertura` se declara N/A por rama y
`harness.mutacion` necesita una feature declarada con su alcance. El destino no
tiene ciclo SDD propio; la evidencia de estos cambios es la campaña de F-038 en
`albaranes` (`progress/mutacion_F-038.md`: 20 mutantes, 19 muertos, base 52,1 s,
media 36,4 s) más las 134 pruebas que aquí quedan en verde.

**Fase RED: no aplica a esta tarea.** Es un porte, no código nuevo: los 86 tests
viajan ya escritos, con su fase RED documentada en `progress/impl_F-038.md`. Lo
que sí se comprobó es lo contrario y es lo que importa aquí — que los tests
portados **fallarían** sin el código portado, cosa que garantiza que aplicaron
sobre el destino y no sobre una copia del origen.

## 8. Qué queda pendiente

- **`git push` y PR**: no se han hecho, por norma. Lo decide el humano.
- **Propagar la 1.7.0 a los demás proyectos** con
  `.\instalar_arnes.ps1 -Destino <ruta> -Modo actualizar`. Incluido
  **`albaranes`**, cuyo `harness/ARNES_VERSION.md` sigue sellado en **1.6.1**:
  al actualizarlo recibirá también la 1.6.2 y la 1.6.3, que aquí nunca
  llegaron —en particular el arreglo del **bytecode envenenado**, que hoy
  `albaranes` no tiene—.
- **Deuda heredada, no tocada**: el filtro de filas de reloj de
  `test_f012_r1_r5_r11_coordinador.py` en `albaranes` sigue siendo una lista de
  prefijos a mano, así que la próxima fila de reloj volverá a romperlo. Está ya
  recogida en la ficha de **F-039**.
- **Al actualizar cualquier proyecto**, aplicarle los cuatro avisos: declarar
  `critico` donde hiciera falta y repetir las campañas medidas con la
  invocación rota.
