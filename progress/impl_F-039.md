<!-- progress/impl_F-039.md -->
# F-039 · Informe de implementación

Rama `feature/F-039-remedir-campanas-invocacion-rota`. Nivel `estandar`.
**16 de 20 tareas hechas**, más los dos CR del review: T5–T7 son verificación
MANUAL del humano y T17 (porte a `arnes-base`) va **tras el merge en `dev`**.

Lo que cambió, en una línea: el arnés ya sabe declarar qué filas de un informe
salen del reloj y ya sabe mutar **ficheros enteros** sin un diff detrás, y con
eso se ha medido —con números válidos— la maquinaria de mutación de hoy. Los 7
supervivientes están analizados y **la lista de huecos se presenta al humano
sin abrir ficha** (R20).

## Qué cambió, por tarea

| Tarea | Ficheros | Qué |
|---|---|---|
| T1 | `tests/test_f039_r3_r7_filas_de_reloj.py` (nuevo) | Fase RED de R3–R7 |
| T2, T3 | `harness/mutacion.py` | `FILAS_DE_RELOJ` y `lineas_comparables()` pegadas a `escribir_informe` |
| T4 | `tests/test_f012_r1_r5_r11_coordinador.py` | Fuera el `_comparable` a mano de las líneas 258-272 |
| T5–T7 | `progress/verificacion_paralela_F-039.md` (nuevo) | Preparada la verificación MANUAL del paralelo |
| T8 | `tests/test_f039_r15_r16_alcance_por_ficheros.py` (nuevo) | Fase RED de R15–R16 |
| T9 | `harness/alcance.py`, `harness/mutacion.py` | `alcance_de_ficheros()`, constantes `SIN_DIFF` / `ORIGEN_FICHEROS` y el flag `--ficheros` |
| T10 | — | Línea base de R22 comprobada antes de gastar nada |
| T11–T13 | `progress/mutacion_maquinaria_paralela_F-039.md` (nuevo) | La campaña, su cabecera manual y los 7 análisis |
| T14 | `progress/current.md` | Huecos agrupados por causa, **sin** tocar `features.json` |
| T15 | `progress/inventario_mutacion_F-039.md`, `tests/test_f039_r1_r2_r23_r25_documentos.py` (nuevos) | Inventario de las 13 campañas y su portero |
| T16 | `progress/mutacion_F-011.md`, `progress/mutacion_F-012.md` | Solo cabeceras (R23, R24) |
| T19 | `progress/mutacion_F-039.md` (nuevo) | Campaña de la feature sobre su propio diff |

`progress/mutacion_F-034.md` **no se ha tocado** (R25): lo comprueba un test.

## Fase RED · las trazas reales

### T1 — R3/R4/R5, antes de escribir `FILAS_DE_RELOJ`

`python -m pytest tests/test_f039_r3_r7_filas_de_reloj.py`

```text
collected 0 items / 1 error
__________ ERROR collecting tests/test_f039_r3_r7_filas_de_reloj.py ___________
tests\test_f039_r3_r7_filas_de_reloj.py:17: in <module>
    from harness.mutacion import (
E   ImportError: cannot import name 'FILAS_DE_RELOJ' from 'harness.mutacion'
    (C:\Users\pgris\PycharmProjects\albaranes\harness\mutacion.py)
=========================== short test summary info ===========================
ERROR tests/test_f039_r3_r7_filas_de_reloj.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.22s ===============================
```

Tras T2 quedaron 6 verdes y **1 en rojo a propósito** —el de R7— hasta que T4
sustituyó el filtro a mano del test de F-012: `1 failed, 6 passed in 0.22s`, con
`AssertionError: el test de paridad de F-012 debe comparar con lineas_comparables`.

### T8 — R15/R16, antes de escribir `alcance_de_ficheros`

`python -m pytest tests/test_f039_r15_r16_alcance_por_ficheros.py`

```text
collected 0 items / 1 error
______ ERROR collecting tests/test_f039_r15_r16_alcance_por_ficheros.py _______
tests\test_f039_r15_r16_alcance_por_ficheros.py:17: in <module>
    from harness.alcance import Alcance, alcance_de_ficheros
E   ImportError: cannot import name 'alcance_de_ficheros' from 'harness.alcance'
    (C:\Users\pgris\PycharmProjects\albaranes\harness\alcance.py)
=========================== short test summary info ===========================
ERROR tests/test_f039_r15_r16_alcance_por_ficheros.py
============================== 1 error in 0.19s ===============================
```

## Decisiones de diseño y desviaciones respecto a la spec

1. **`escribir_informe` sí cambia una línea.** El design decía «el contenido
   del informe no cambia», pero R15 exige la frase literal `Origen del diff:
   **ficheros** (alcance declarado en la orden).`. Un alcance declarado a mano
   no tiene diff: imprimir `` `(sin diff)` .. `<sha>` `` haría creer que se
   comparó algo con algo. Es una rama de tres líneas, con test propio a los dos
   lados (el caso `ficheros` y el caso `rama`, que no puede comerse).
2. **`SIN_DIFF` y `ORIGEN_FICHEROS` viven en `alcance.py`**: `escribir_informe`
   reconoce el origen, y dos literales sueltos divergen.
3. **T11 se lanzó con `--workers 1`** (el design lo dice: sin N verde del
   bloque C, en serie; y R8 lo exige) **y con `--timeout 400`**, que no estaba
   en el comando del design. Motivo abajo; no cambia ni un mutante.
4. **T17 no se hace en esta rama** (F-038 D6): portar a `arnes-base` dentro de
   la rama de una feature es lo que provocó el rechazo entero del reviewer en
   F-034. Detalle al final.

## T11 · La campaña sobre la maquinaria de HOY

```bash
python -m harness.mutacion --feature F-039 \
  --ficheros harness/mutacion.py,harness/mutacion_paralela.py,harness/rigor.py \
  --workers 1 --timeout 400 \
  --salida progress/mutacion_maquinaria_paralela_F-039.md
```

**20 mutantes de 417** (semilla `20260820`, nivel `estandar`), alcance de los
tres ficheros enteros (**2.742 líneas**): **13 muertos, 7 supervivientes, 0
timeouts, 0 sin veredicto**, en **838,7 s** sobre una línea base de **57,1 s**
(media 41,9 s por mutante). SHA medido: `b0761e8`. El muestreo tocó los tres
ficheros, así que el riesgo que anotaba el design —que el paralelo se quedara
sin muestra— no se materializó.

### Hicieron falta tres pasadas, y el motivo importa

Las dos primeras se invalidaron **solas, y con razón**. Diagnóstico, porque no
es lo que parece:

- La suite de la raíz **nunca estuvo roja**: con la invocación exacta de la
  línea base, `409 passed` y código 0, pero en **149 s** en vez de 51 s.
- Causa: otra sesión estaba corriendo **campañas de mutación en paralelo de
  `datamart-seg-anual`** en esta misma máquina (arrancadas a las 21:49 y a las
  22:06, con ~15 pytest simultáneos). Evidencia: los `CommandLine` de los
  procesos vivos.
- Con la máquina tres veces más lenta, la suite limpia dejó de caber en el
  timeout de 120 s de `harness/rigor.json`. La primera pasada murió en la
  **línea base de cierre** (`código -1` = expirada); la segunda dejó **1
  mutante sin veredicto**.
- Remedio: esperar a que la máquina quedara libre y darle aire al reloj con
  `--timeout 400`. La tercera pasada salió limpia. **No se tocó
  `harness/rigor.json`** (D5 sigue en pie).

Hallazgo que se deja escrito y **no se arregla aquí** (excede F-039 y
`mutacion.py` es el código que se está midiendo): `_base_rota_al_final` **no
distingue una línea base que expira de una que falla** y estampa «ROJA al
terminar (código -1)», que manda a buscar un test caído inexistente.
`comprobar_linea_base` sí lo distingue. En `current.md` §3, para el humano.

### Los 7 supervivientes, agrupados por causa (R19, R20)

Ninguno en `PENDIENTE`; el análisis completo de cada uno vive en el informe.

| Grupo | Qué no se prueba | Supervivientes |
|---|---|---|
| **A · El CLI de `harness.mutacion` no se ejercita de punta a punta** | `main` con un centinela sucio —arrancaría la campaña **encima del mutante viejo** y llamaría a eso «el código»— y el código de salida de `--restaurar` | `mutacion.py:1807`, `mutacion.py:1688` |
| **B · El informe solo se escribe por su camino feliz** | La sección `## Timeouts` (`lineas -= [...]` es un `TypeError` en cuanto hay uno) y el mensaje de `_base_rota_al_final`, que no tiene **ni un test** | `mutacion.py:1539`, `mutacion.py:1282` |
| **C · Mutante equivalente** | — (justificado recorriendo el bucle de `analisis_escritos`) | `mutacion.py:1348` |
| **D · `rigor.py` valida el tipo, no el rango** | Un `timeout_por_mutante_s` entero pero `<= 0` pasa; con `timeout=0` **toda** la campaña sale «timeout» | `rigor.py:118` |
| **E · La limpieza de worktrees solo se prueba cuando funciona** | El respaldo `rmtree` + `prune` para cuando `git worktree remove` falla, que es el único caso para el que existe | `mutacion_paralela.py:257` |

**R21 no se ha disparado**: ninguno de los siete revela un defecto de
comportamiento vivo, son huecos de test (y uno equivalente). **R20 cumplido**:
la lista está presentada en `progress/current.md` §2, **sin ficha y sin tocar
`harness/features.json`**.

## Verificaciones MANUAL pendientes

- **T5 y T6 (humano).** `--workers 5` lanza cinco suites simultáneas y en esta
  máquina dos ya tumban el proceso (`0xC0000142`). El comando exacto, el
  criterio de verde y el descenso 5 → 3 → 2 están listos para copiar y pegar en
  `progress/verificacion_paralela_F-039.md`, con la tabla esperando la salida.
- **T7 (humano, condicional).** Solo aplica si esa línea base sale roja; su
  sección de diagnóstico está preparada en el mismo fichero.
- **No bloquean nada de lo medido**: R8 pide no remedir con maquinaria sin
  verificar, y por eso T11 se midió **en serie**, que es como se ha medido
  siempre en este repositorio. Lo que queda pendiente del humano es el uso de
  `--workers` en campañas futuras, no los números de T11.

## T17 · Porte a `arnes-base`, DESPUÉS del merge en `dev`

No se ha tocado `arnes-base`. Lo que hay que portar, con sus tests:

1. `FILAS_DE_RELOJ` + `lineas_comparables()` en `harness/mutacion.py` (junto a
   `escribir_informe`), el cambio en el test de paridad de F-012 y
   `tests/test_f039_r3_r7_filas_de_reloj.py`.
2. `alcance_de_ficheros()` + `SIN_DIFF` + `ORIGEN_FICHEROS` en
   `harness/alcance.py`, el flag `--ficheros` y su rama en `main`, la rama de
   `escribir_informe` para el origen `ficheros`, y
   `tests/test_f039_r15_r16_alcance_por_ficheros.py`.

Lo que **no** se porta: el inventario, las campañas y las cabeceras, que son de
este repositorio. `tests/test_f039_r1_r2_r23_r25_documentos.py` tampoco.

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** (suite de la raíz, dentro de `init.sh`) | **420 passed**, 0 fallos. Eran 409 antes de la feature: +9 de R15/R16, +9 de R1/R2/R18/R23–R25 y +7 de R3–R7, menos los que ya existían |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 32 de 32 líneas, umbral 80 %, nivel `estandar` (línea `PUERTA COBERTURA` de `init.sh`). Era 96,9 % antes de CR-2 |
| **Mutación de la feature** (T19, reejecutada tras CR-2) | 13 mutantes generados, 13 evaluados, **13 muertos, 0 supervivientes**, 0 timeouts, en 482,2 s sobre línea base de 51,5 s, SHA `adea6ab` → `progress/mutacion_F-039.md` |
| **Mutación de la maquinaria** (T11, campaña del bloque D) | 417 generados, 20 evaluados (muestreo `estandar`), 13 muertos, **7 supervivientes** (6 huecos + 1 equivalente), 0 timeouts, 838,7 s → `progress/mutacion_maquinaria_paralela_F-039.md` |
| **Tiempo de ejecución de la suite** | **80,46 s** medida con cobertura dentro de `init.sh`; **51,5 s** sin cobertura (línea base de las campañas) |
| **Suites de los 6 servicios** | En verde (caché de `init.sh`: árbol sin cambios; esta feature no toca `services/**`) |

### Salida real de `bash harness/init.sh`

```text
[OK] pytest en verde (con medición de cobertura)     420 passed in 80.46s
[OK] PUERTA COBERTURA: 100.0% de 32 líneas cambiadas cubiertas (32/32, umbral 80%, nivel estandar)
[OK] PUERTA RUTAS SENSIBLES [evals]: N/A (F-039 no toca ninguna ruta sensible declarada)
[OK] PUERTA TAMAÑO: F-039 dentro de los topes (requirements 150/150, design 224/250, impl 220/220, review 140/140)
[OK] Rama actual: feature/F-039-remedir-campanas-invocacion-rota
ENTORNO LISTO. Puedes trabajar.
```

Avisos previos que no bloquean: `ruff` 1108, sv1 e `infra` sin tests, marcas
`[ADAPTAR]` en las specs de F-034 y F-035.

## Segunda pasada · los dos CR del review (`progress/review_F-039.md`)

- **CR-1 · R18 no tenía guarda.** Dos `test_f039_r18_*`: la cabecera manual del
  informe debe llevar el `--ficheros` **completo** del comando de reproducción y
  el aviso de que mide **otro código** que `mutacion_F-012.md`. Hacía falta
  porque `escribir_informe` conserva los análisis pero **no la cabecera**. RED
  demostrada retirándola y restaurándola con `git checkout --`:
  `AssertionError: la cabecera no lleva el --ficheros COMPLETO` y
  `AssertionError: ... tiene que decir que mide OTRO código`. Corregida además
  la verificación de T12 en `tasks.md`, que citaba un test inexistente.
- **CR-2 · la guarda de alcance vacío no se alcanzaba desde el CLI.** Pasa
  **detrás** del filtrado: lo que importa es que quede algo que mutar, no cómo
  venga la lista. RED por el camino del CLI, con el defecto capturado en la
  propia traza —`assert 0 == 2` y, en stdout, `0 mutantes evaluados …
  Informe: …`—. Hoy `--ficheros ","` sale con **2** y sin escribir informe.
- **T19 reejecutado**, porque CR-2 toca `harness/alcance.py`, que está en el
  diff: 13 mutantes, **13 muertos, 0 supervivientes**, SHA `adea6ab` —desde ahí
  ningún fichero de su alcance se ha movido—, y entre los muertos el de la
  guarda nueva (`alcance.py:262`). **T11 no se toca**: nada de su alcance
  (`mutacion.py`, `mutacion_paralela.py`, `rigor.py`) se ha movido desde
  `b0761e8`.
