<!-- progress/impl_F-011.md -->
# F-011 · Evals de IA con ground truth y puerta en el arnés — Informe del implementer

Rama `feature/F-011-evals-ia`. Rigor **estandar**. Spec:
`specs/F-011-evals-ia/` (requirements R1–R28, decisiones D1–D7 de 2026-08-13).
Las 14 tareas de `tasks.md` están en `[x]`, con un commit `F-011 Tn: …` cada
una.

## Qué cambió

### Nuevo: `evals/` — el banco de casos y su runner

| Fichero | Qué hace |
|---|---|
| `evals/modelos.py` | Dataclasses puras y los dos **sentinelas** del contrato de datos: `NO_COMPARAR` (celda `?`) y `ESPERA_REVISION` (literal `REVISIÓN`). Veredictos y códigos de salida |
| `evals/barrido.py` | Barrido de datos sensibles de C3 bis (correo, IP, GUID, credencial, token). Precios, razones sociales y CIF quedan fuera a propósito (D1) |
| `evals/criticidad.py` + `criticidad.json` | Clasifica cada campo comparado: crítico → FALLO, laxo → AVISO, sin clasificar → crítico **con aviso** (R8) |
| `evals/conversor.py` | CLI `python -m evals.conversor`: los 6 libros → `evals/fixtures/`. Todo en memoria, barrido, y solo entonces disco. Salida determinista |
| `evals/comparador.py` | Compara esperado vs obtenido resolviendo los sentinelas, empareja tablas por clave (no por posición) y reparte severidades |
| `evals/informe.py` | Informe Markdown + las cuatro líneas parseables (`MODO:`, `FASES:`, `PROVEEDORES:`, `VEREDICTO:`) que lee la puerta |
| `evals/runner.py` | CLI de las dos corridas, orquestación de subprocesos, informe en `progress/` y códigos de salida |
| `evals/procesos/sv6_build.py` | Envelope estimulado desde el ground truth, build real de sv6 en subproceso y evaluación del caso |
| `evals/procesos/sv5_valoracion.py` | Contexto desde INPUTS, IA3+IA4 reales, envelope de hand-off y aplicación de la conciliación |
| `evals/procesos/sv2_extraccion.py` | Composición mínima de sv2 (sin `composition.py` ni `Settings`), proveedor primario por defecto (D3) y preprocesado idéntico al de producción |
| `evals/requirements.txt` | Dependencias del venv raíz (D6). Instaladas |
| `evals/fixtures/*/_indice.json` | Salida real del conversor sobre los 6 libros de hoy: 0 casos, con el `sha256` de cada libro |
| `evals/README.md` | Reescrito: los 6 libros, las dos corridas, criticidad, comandos y dónde queda todo |

### Nuevo: la puerta del arnés

- `harness/rutas_sensibles.py` — **genérico**: carga y validación de la
  declaración, cotejo del diff (reutiliza `harness/alcance.py` sin su filtro
  de solo-Python) y evaluación de la puerta. CLI `--validar` / `--puerta`.
- `harness/rutas_sensibles.json` — declaración de este repositorio: 13 rutas
  (prompts YAML, schemas Pydantic, clientes LLM, redes de sv6, unit registry),
  exigencia `aviso` (D5).

### Modificado

- `harness/init.sh` — sección **7 ter**, tras la puerta de cobertura. Sin
  declaración no imprime ni una línea; exit 3 → `[AVISO]`, 1 → `[KO]`.
- `CHECKPOINTS.md` — bloque **C4 ter** (parte genérica marcada como tal, más
  el párrafo específico de evals).
- `progress/current.md`, `specs/F-011-evals-ia/tasks.md`.

### Fuera de este repositorio (T11, regla de propagación)

Commit local `4c294c9` en `C:\Users\pgris\PycharmProjects\arnes-base`
(**sin push**): `harness/rutas_sensibles.py` tal cual,
`harness/rutas_sensibles.ejemplo.json`, sección 7 ter de su `init.sh`, bloque
C4 ter genérico de su `CHECKPOINTS.md`, versión **1.4.0** y su capítulo en
`GUIA_INSTALACION.md`. Lo específico de albaranes (declaración real, runner,
criticidad) NO se ha portado.

### Lo que NO se ha tocado

Nada bajo `services/`. Tampoco `harness/alcance.py`, `cobertura.py`,
`mutacion.py`, `rigor.*`, `servicios.*` ni `features.json`. Los `.xlsx` y
`evals/inputs/albaranes/` siguen sin versionar.

## Decisiones de diseño

1. **Un subproceso por servicio.** sv2, sv5 y sv6 usan paquetes de primer
   nivel homónimos (`application`, `domain`): no caben en un intérprete. Cada
   adaptador se lanza con `python -m evals.procesos.<x>`, inserta la raíz de
   SU servicio en `sys.path` y devuelve JSON por stdout. El hand-off sv5→sv6
   es el envelope serializado, igual que en producción.
2. **Parte pura fuera del subproceso.** Construir el envelope, proyectar los
   records y comparar no necesita ningún servicio: vive en funciones puras que
   los tests ejercitan en su propio proceso. Solo la composición de servicios
   está detrás de la frontera.
3. **El emparejamiento de filas es por clave, no por posición.** sv6 inyecta
   sintéticas deterministas (M1 por año, red de código de hormigón) y el orden
   del ground truth no tiene por qué coincidir.
4. **El conversor escribe todo o nada.** El barrido corre sobre el contenido
   completo antes de tocar el disco: unos fixtures a medias con un correo
   dentro ya estarían escritos.
5. **La puerta es neutra.** No sabe qué son los «evals»: lee de la declaración
   el comando, el informe y las `exige_lineas` que ese informe debe contener.
   Por eso el módulo se porta a `arnes-base` sin tocar una línea.

## Desviaciones respecto a la spec (requieren decisión del humano)

### 1. Las sintéticas PROHIBIDAS no desaparecen del build de sv6

`design.md` afirmaba: «Asserts: las prohibidas NO aparecen en los records
finales». Medido contra el código real de sv6, eso **no ocurre hoy**:
`ValuationBuilder.build` clasifica las líneas en tres pasadas y construye un
record por cada una; **no descarta ninguna**. Lo que sí hace con una sintética
que el contrato no tarifa es no inventarle precio y mandarla a revisión.

Salida real del build con la prohibida inyectada (caso sintético del test):

```json
{"merge_line_id": null, "line_kind": "synthetic_modifier",
 "descripcion_linea": "ADITIVO SUPERPLASTIFICANTE",
 "precio_unitario_final": null, "precio_unitario_source": "none",
 "importe_calculado": null, "importe_source": "none",
 "codigo_partida_final": "01.02.03", "partida_action": "inherited_from_base_line",
 "review_required": true,
 "review_reasons": ["inherited_from_base_line", "modifier_identified_no_tariff"]}
```

**Qué se ha hecho**: implementar el eval como dice la spec —si la prohibida
aparece en los records, el caso es ROJO, con el motivo «sintética prohibida
emitida»—. El eval no se ha afinado para pasar: cuando haya casos reales dirá
la verdad. No se ha tocado sv6 (la spec lo prohíbe expresamente).

**Qué decide el humano**: si lo correcto es que sv6 descarte esas líneas, es
un cambio en sv6 y por tanto otra feature; si lo correcto es que queden a
revisión con precio nulo, hay que relajar la lectura de la TABLA 3 en el
comparador. Los dos tests que documentan el comportamiento de hoy son
`test_f011_r13_la_prohibida_emitida_no_lleva_precio_y_queda_a_revision` y
`test_f011_r13_una_prohibida_emitida_es_un_fallo_critico`.

### 2. Campos del ground truth que el extremo-a-extremo no puede observar

`RESULTADO_FINAL` TABLA 1 pide obra, proveedor, CIF, fecha y nº de albarán.
Esos datos **no salen del build de sv6**: salen de la extracción (IA1), y el
envelope DTO de sv6 ni siquiera los transporta. Compararlos daría ROJO por un
motivo que no es un fallo del sistema.

Solución: cada tabla declara sus campos **observables**
(`OBSERVABLES` en `evals/procesos/sv6_build.py`) y los demás se listan en el
informe como «campos no observables en esta corrida». No se saltan en
silencio: se ven. Su eval es el libro IA1.

### 3. La campaña de mutación se lanzó acotando la suite

`PYTEST_ADDOPTS="--ignore=services"`. El arnés 1.3.0 de este repositorio lanza
la suite de la raíz sin acotar ruta, con lo que cada mutante arrastraba los
~120 s de la suite del servicio `comun` —que no puede cazar ningún mutante de
F-011—. Sin tocar código del arnés. (En `arnes-base` 1.3.1 esto ya está
corregido en `init.sh`; ese arreglo llegará a este repositorio al actualizar.)

## Fase RED

Rigor `estandar`: traza real del fallo ANTES de que existiera el código, para
los requisitos centrales que declara `tasks.md` (R2, R4, R7, R13, R20–R25).

### R4 — barrido de datos sensibles

```
$ .venv/Scripts/python.exe -m pytest tests/test_f011_r4_barrido.py -q --tb=short
tests\test_f011_r4_barrido.py:9: in <module>
    from evals.barrido import PATRONES, barrer
E   ModuleNotFoundError: No module named 'evals.barrido'
ERROR tests/test_f011_r4_barrido.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.22s
```

Después de escribir `evals/barrido.py`: `9 passed in 0.02s`.

### R7 y R8 — criticidad

```
$ .venv/Scripts/python.exe -m pytest tests/test_f011_r7_r8_criticidad.py -q --tb=short
tests\test_f011_r7_r8_criticidad.py:14: in <module>
    from evals.criticidad import (
E   ModuleNotFoundError: No module named 'evals.criticidad'
ERROR tests/test_f011_r7_r8_criticidad.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.22s
```

Después: `23 passed in 0.25s`.

### R1, R2, R3, R5 y R6 — conversor

```
$ .venv/Scripts/python.exe -m pytest tests/test_f011_r1_r2_r3_conversor.py \
    tests/test_f011_r5_determinismo.py tests/test_f011_r6_ausencias.py -q --tb=line
tests\test_f011_r5_determinismo.py:13: in <module>
    from evals.conversor import convertir
E   ModuleNotFoundError: No module named 'evals.conversor'
ERROR tests/test_f011_r1_r2_r3_conversor.py
ERROR tests/test_f011_r5_determinismo.py
ERROR tests/test_f011_r6_ausencias.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
3 errors in 0.33s
```

Después: `23 passed in 10.33s`.

### R2 (comparación) y R15 — comparador e informe

```
$ .venv/Scripts/python.exe -m pytest tests/test_f011_r2_comparador.py \
    tests/test_f011_r15_informe.py -q --tb=line
tests\test_f011_r15_informe.py:8: in <module>
    from evals.informe import (
E   ModuleNotFoundError: No module named 'evals.informe'
ERROR tests/test_f011_r2_comparador.py
ERROR tests/test_f011_r15_informe.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 0.32s
```

Después: `24 passed in 0.07s`.

### R13 — modo determinista (la RED más útil de toda la feature)

Primero, sin el módulo:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f011_r13_determinista.py \
    tests/test_f011_r17_secuencial.py -q --tb=line
tests\test_f011_r13_determinista.py:18: in <module>
    from evals.procesos.sv6_build import (
E   ModuleNotFoundError: No module named 'evals.procesos'
ERROR tests/test_f011_r13_determinista.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.35s
```

Y después, ya con el adaptador escrito, **dos tests siguieron en rojo contra
el sv6 real**, que es lo que destapó la desviación nº 1 de arriba:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f011_r13_determinista.py \
    tests/test_f011_r17_secuencial.py -q --tb=short
..F.F.....                                                               [100%]
__________ test_f011_r13_el_build_real_de_sv6_resuelve_la_linea_base __________
tests\test_f011_r13_determinista.py:180: in test_...
    assert base["review_required"] is False
E   assert True is False
_____ test_f011_r13_lo_que_el_ground_truth_declara_bien_no_genera_fallos ______
tests\test_f011_r13_determinista.py:213: in test_...
    assert fallos_de_linea == []
E   AssertionError: assert [Discrepancia... no declara')] == []
E     Left contains 5 more items, first extra item: Discrepancia(
E       campo='IA3.lineas_valoradas[1].precio_source',
E       esperado='contrato_db', obtenido='albaran', severidad='fallo', motivo='')
2 failed, 8 passed in 1.99s
```

No se «arregló» el eval para que pasara: se midió qué hace sv6 de verdad
(`precio_unitario_source = albaran_declared` cuando el importe declarado del
albarán coincide; `review_required = True` por la prohibida inyectada) y se
reescribieron los tests contra la realidad medida, usando el convenio `?` del
propio contrato de datos para los campos cuyo valor depende de reglas internas
de sv6. Verde final: `10 passed in 1.92s`.

### R20–R25 — la puerta

```
$ .venv/Scripts/python.exe -m pytest tests/test_f011_r19_r20_declaracion.py \
    tests/test_f011_r21_r22_ausente_o_rota.py tests/test_f011_r23_r24_r25_puerta.py -q --tb=line
tests\test_f011_r23_r24_r25_puerta.py:18: in <module>
    from harness.rutas_sensibles import (
E   ModuleNotFoundError: No module named 'harness.rutas_sensibles'
ERROR tests/test_f011_r19_r20_declaracion.py
ERROR tests/test_f011_r21_r22_ausente_o_rota.py
ERROR tests/test_f011_r23_r24_r25_puerta.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
3 errors in 0.33s
```

Después: `36 passed in 5.08s`.

## Trazabilidad requisito → test

| Requisito | Fichero de test |
|---|---|
| R1, R2, R3, R4 | `tests/test_f011_r1_r2_r3_conversor.py`, `tests/test_f011_r4_barrido.py` |
| R5 | `tests/test_f011_r5_determinismo.py` |
| R6 | `tests/test_f011_r6_ausencias.py` |
| R7, R8 | `tests/test_f011_r7_r8_criticidad.py`, `tests/test_f011_r2_comparador.py` |
| R9, R10 | `tests/test_f011_r9_r10_cli.py` |
| R11 | `tests/test_f011_r11_ia12.py` |
| R12 | `tests/test_f011_r12_omitidos.py`, `tests/test_f011_r9_r10_cli.py` |
| R13 | `tests/test_f011_r13_determinista.py` |
| R14 | `tests/test_f011_r14_e2e_real.py` |
| R15 | `tests/test_f011_r15_informe.py` |
| R16 | `tests/test_f011_r16_exit_codes.py` |
| R17 | `tests/test_f011_r17_secuencial.py` |
| R18 | `tests/test_f011_r18_sin_casos.py` |
| R19, R20 | `tests/test_f011_r19_r20_declaracion.py` |
| R21, R22 | `tests/test_f011_r21_r22_ausente_o_rota.py` |
| R23, R24, R25, R26 | `tests/test_f011_r23_r24_r25_puerta.py` |
| R27 | MANUAL (humano): diff del commit `4c294c9` en `arnes-base` |
| R28 | Transversal: ningún test toca red, BBDD ni LLM (los subprocesos solo importan sv6 con un envelope ya construido) |

## Verificaciones MANUAL (humano) pendientes

1. **Pasada completa de evals** — `python -m evals.runner --con-llm --feature
   F-011`. Cuesta llamadas LLM reales. Hoy daría NO_EVALUABLE: los seis libros
   están sin casos. Se lanza cuando el humano los rellene.
2. **Diff de `arnes-base`** — `git -C C:/Users/pgris/PycharmProjects/arnes-base
   diff HEAD~1`, y decidir el push (los agentes no empujan).
3. **Las dos decisiones abiertas** de la sección «Desviaciones».

## Corrida de humo (T12)

```
$ .venv/Scripts/python.exe -m evals.runner --feature F-011
NO_EVALUABLE · informe en C:\Users\pgris\PycharmProjects\albaranes\progress\evals_F-011.md
EXIT=2
```

El informe (`progress/evals_F-011.md`, versionado) trae las tres fases del
modo determinista en NO_EVALUABLE con el motivo «no hay ningún caso en
evals/fixtures/inputs/» y la línea `VEREDICTO: NO_EVALUABLE`.

Puerta, con la declaración real:

```
$ .venv/Scripts/python.exe -m harness.rutas_sensibles --validar
    1 verificación(es), 13 ruta(s) sensible(s) declaradas: evals (aviso)
EXIT=0

$ bash harness/init.sh    (línea de la sección 7 ter)
[OK] PUERTA RUTAS SENSIBLES [evals]: N/A (F-011 no toca ninguna ruta sensible declarada)
```

Y la comprobación de R21, moviendo temporalmente la declaración fuera del
árbol de trabajo y relanzando `bash harness/init.sh`:

```
$ grep -c "RUTAS SENSIBLES" /tmp/init_sin_declaracion.log
0
```

(Esa misma corrida salió en rojo, como debía: al no estar el fichero, el test
`test_f011_r20_la_declaracion_de_este_repositorio_es_sana` falla. La
declaración se restauró inmediatamente después.)

## Cierre: `bash harness/init.sh` en verde (T14)

```
185 passed, 3 skipped in 155.65s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio comun (services/albaranes-comun): pytest en verde
[OK] PUERTA COBERTURA: 88.8% de 1254 líneas cambiadas cubiertas (1113/1254, umbral 80%, nivel estandar)
[OK] PUERTA RUTAS SENSIBLES [evals]: N/A (F-011 no toca ninguna ruta sensible declarada)
[OK] Rama actual: feature/F-011-evals-ia
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
EXIT=0
```

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados y resultado** | `169 passed` (suite de `tests/`, la que estrena esta feature: 0 antes, 169 ahora). Con la suite completa que lanza `init.sh` (raíz + servicio `comun`): `185 passed, 3 skipped` |
| **Cobertura de las líneas cambiadas** | `PUERTA COBERTURA: 88.8% de 1254 líneas cambiadas cubiertas (1113/1254, umbral 80%, nivel estandar)` → `[OK]` |
| **Mutantes generados y supervivientes** | 305 generados, 305 evaluados, **172 muertos, 133 supervivientes**, 0 timeouts, 3694,1 s. Índice de mutación 56,4 %. Campaña completa (sin muestreo). Los 133 supervivientes están analizados uno a uno en `progress/mutacion_F-011.md`: ninguna sección se quedó sin completar |
| **Tiempo de ejecución de la suite** | `169 passed in 16.68s` (`tests/`); `185 passed, 3 skipped in 158.01s` la suite completa de `init.sh` |

Lo que queda sin medir por cobertura y por qué: la composición de clientes LLM
reales y los `ejecutar_trabajo` de sv2 y sv5 llevan `# pragma: no cover` porque
solo se ejecutan **dentro del subproceso**, con la raíz del servicio en
`sys.path`; medirlos desde el proceso padre es imposible por construcción. El
equivalente de sv6 sí se ejerce de verdad en `test_f011_r13_*` a través de la
frontera del subproceso, aunque su cobertura tampoco la vea el padre.

### Campaña de mutación

```
$ PYTEST_ADDOPTS="--ignore=services" .venv/Scripts/python.exe       -m harness.mutacion --feature F-011 --timeout 120
F-011: 13 fichero(s), 3812 línea(s) de producción (origen rama,
       42139da4067a65d8c6dd1cc8c4cbfe3d740c0c3e..feature/F-011-evals-ia)
...
305 mutantes evaluados, 172 muertos, 133 supervivientes, 0 timeouts en 3694.1 s
Informe: progress/mutacion_F-011.md
```

El desglose de los 133 supervivientes por naturaleza, el análisis individual de
cada uno y la deuda accionable que deja la campaña están en
`progress/mutacion_F-011.md`. En una línea: **39** solo se ejecutan dentro del
subproceso que compone un servicio real (imposibles de cazar sin claves LLM y
casos reales), **26** son valores de reserva que el ground truth de los tests
nunca fuerza, **11** son `frozen=True` (equivalentes), **8** son redacción del
informe, y los **49** restantes son ramas concretas del conversor, del runner,
de la puerta y del estímulo del envelope, cada una con su motivo escrito.

Lo que NO sobrevivió, que es lo que sostiene la feature: los mutantes de
`comparar` (sentinelas y severidades), de `criticidad.clasificar`, de la
localización de tablas y los convenios de celda del conversor, del cálculo del
veredicto y los códigos de salida, y de las decisiones de la puerta.

**Nota de método**: la campaña se lanzó con `PYTEST_ADDOPTS=--ignore=services`.
El arnés 1.3.0 de este repositorio ejecuta la suite de la raíz sin acotar ruta,
de modo que cada mutante arrastraba los ~120 s de la suite del servicio `comun`
—que no puede cazar ningún mutante de F-011—: 10 horas de campaña en vez de
una. No se ha tocado código del arnés. El reviewer puede recalcular alcance y
número de mutantes con `harness.alcance` y `harness.mutacion` sin ejecutar la
suite, que es lo que pide C4 bis.

Un primer intento de campaña quedó interrumpido a mitad y dejó
`harness/rutas_sensibles.py` mutado en el árbol de trabajo; se restauró con
`git checkout --` y se relanzó la campaña entera desde cero. La que consta
arriba es la completa, y al terminar el árbol quedó limpio.
