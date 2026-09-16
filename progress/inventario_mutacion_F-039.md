<!-- progress/inventario_mutacion_F-039.md -->
# Inventario de campañas de mutación (F-039 · R1)

Una fila por cada `progress/mutacion_*.md` del repositorio, con las dos cosas
que hacen falta para saber si sus números valen: si su alcance incluye
**ficheros fuera de `services/`** —los que hasta F-038 se juzgaban con una
invocación rota— y su **veredicto**.

`tests/test_f039_r1_r2_r23_r25_documentos.py` obliga a que este inventario no
se quede atrás: un informe nuevo sin fila aquí pone la suite en rojo (R2).

## Por qué «fuera de `services/`» es la columna que importa

Hasta F-038, `ejecutor_para` juzgaba un fichero que no cae en ningún servicio
de `harness/servicios.json` con `python -m pytest` **sin ruta** desde la raíz.
Esa invocación moría en la recolección en menos de un segundo, y el ejecutor
leía el `exit 1` como **MUERTO**. Todo mutante de un fichero fuera de
`services/` medido antes de F-038 salió «muerto» sin que ningún test lo
juzgara. Los de dentro de `services/` sí se juzgaron con la suite de su
servicio: esos números no están tocados por este defecto.

## Vocabulario de veredictos

| Veredicto | Qué significa |
|---|---|
| `VÁLIDA` | Sus números valen como evidencia tal cual están. |
| `INVÁLIDA (no se repone)` | Juzgada con la invocación rota; se decidió no rehacerla y el aviso de cabecera se queda para siempre. |
| `REMEDIDA` | Se rehízo; el informe bueno es otro fichero, enlazado en su fila. |
| `INVALIDADA PARA SIEMPRE` | Como la anterior, y además se descarta rehacerla nunca (decisión escrita del humano). |
| `MANUAL` | Medida a mano, fuera del CLI, porque el CLI no podía medirla. |
| `SIN SUJETO` | No hay nada que mutar: alcance vacío o sin código Python. |

## Inventario

| Informe | ¿Alcance fuera de `services/`? | Veredicto | Nota |
|---|---|---|---|
| `progress/mutacion_F-001.md` | No | `SIN SUJETO` | Alcance de 0 líneas, 0 mutantes generados. No hay nada que reponer. |
| `progress/mutacion_F-002.md` | No | `VÁLIDA` | Todo el alcance es `services/**`: se juzgó con la suite de cada servicio. Medida con el arnés 1.5.2, que no mutaba `is`/`is not`: no comparable con las posteriores a la 1.6.0, pero sus muertos son muertos de verdad. |
| `progress/mutacion_F-011.md` | **Sí** (`evals/**`, `harness/rutas_sensibles.py`) | `INVALIDADA PARA SIEMPRE` | Decisión del humano del 2026-08-20: 305 mutantes y 133 supervivientes, la campaña más cara del repositorio; no se rehace y no se abre ficha. Consecuencia escrita en su cabecera: la puerta de evals de F-011 **no tiene detrás ninguna medición de mutación válida**. |
| `progress/mutacion_F-012.md` | **Sí** (`harness/mutacion.py`, `harness/mutacion_paralela.py`, `harness/rigor.py`) | `INVÁLIDA (no se repone)` | Sus 55 «muertos» no los mató ningún test. Decisión del humano del 2026-08-20: **no se reponen sus números**. `progress/mutacion_maquinaria_paralela_F-039.md` cubre el mismo *sujeto* —la maquinaria de mutación— pero mide **otro código**, el de hoy: ni lo repone ni es comparable con él. |
| `progress/mutacion_F-019.md` | No | `REMEDIDA` | Rehecha con el arnés 1.6.0 en `progress/mutacion_F-019_remedida.md` (49 mutantes en vez de 31). El motivo fue el operador `is`/`is not` que faltaba, no la invocación. |
| `progress/mutacion_F-019_remedida.md` | No | `VÁLIDA` | La medición buena de F-019. |
| `progress/mutacion_F-027.md` | No | `REMEDIDA` | Rehecha en `progress/mutacion_F-027_remedida.md` (1 mutante en vez de 0, y muerto). Mismo motivo que F-019. |
| `progress/mutacion_F-027_remedida.md` | No | `VÁLIDA` | La medición buena de F-027. |
| `progress/mutacion_F-034.md` | **Sí** (`harness/mutacion.py`) | `MANUAL` | Ya remedido a mano: sus números salen de inyectar `EjecutorPytest` con la ruta de la suite de la raíz, y su cabecera lo explica con el código exacto. **No se toca** (R25 de F-039). |
| `progress/mutacion_F-035.md` | No (no hay Python que mutar) | `MANUAL` | F-035 no cambia una línea de Python en este repositorio: todo su código vive en `arnes-base`. La evidencia equivalente es una campaña manual de 7 mutantes sobre `instalar_arnes.ps1` y `politica_ficheros.json`, 7 muertos. |
| `progress/mutacion_F-038.md` | **Sí** (`harness/mutacion.py`, `harness/mutacion_paralela.py`, `harness/rigor.py`, `harness/tamano.py`) | `VÁLIDA` | Primera campaña medida **ya con `ejecutor_para` arreglado**, en la propia rama que lo arregló. Es la prueba de que la invocación quedó bien. |
| `progress/mutacion_maquinaria_paralela_F-039.md` | **Sí** (`harness/mutacion.py`, `harness/mutacion_paralela.py`, `harness/rigor.py`) | `VÁLIDA` | Campaña **nueva** sobre la maquinaria de mutación tal como es hoy, alcance declarado con `--ficheros` y muestreada a 20 mutantes por el nivel `estandar`. No es la campaña de F-012 rehecha. |
| `progress/mutacion_F-039.md` | **Sí** (`harness/alcance.py`, `harness/mutacion.py`) | `VÁLIDA` | Campaña de la propia F-039 sobre su diff, la que exige el nivel `estandar` para cerrar la feature. |
| `progress/mutacion_F-040.md` | **Sí** (`harness/mutacion.py`, `harness/mutacion_paralela.py`, `harness/rigor.py`) | `VÁLIDA` | Campaña de la propia F-040 sobre su diff, muestreada a 20 mutantes por el nivel `estandar`. **Primera campaña con el timeout DERIVADO** de la línea base (137 s efectivos sobre un suelo de 120) y con el tope de workers nuevo (4): sus tiempos no son comparables con los de campañas anteriores. Sus muertos son muertos de verdad; uno de sus tres «supervivientes» resultó ser FALSO al reproducirlo a mano (ver `progress/impl_F-040.md`, «El quinto defecto»), lo que sobra-cuenta trabajo pero no infla el número de muertos. |

| `progress/mutacion_F-043_bloque_A.md` | No | `VÁLIDA` | Campaña del **bloque A** de F-043 (T1-T4), no de la feature entera. Alcance declarado con `--ficheros` sobre los dos módulos nuevos de `ruesma_comun/contratos/` porque esta rama sale de la de F-036, no de `dev`: con `--feature` el diff arrastra los 32 ficheros de F-036 y la campaña deja de medir este bloque. 12 mutantes, 12 muertos, 0 supervivientes, campaña completa (sin muestreo). La campaña de la feature entera es su T28 y sigue pendiente. |
| `progress/mutacion_F-043.md` | No | `VÁLIDA` | La campaña **completa** de F-043, que es su T28. 38 ficheros y 3123 líneas de alcance: `--feature F-043` arrastra también F-036 entera, porque esta rama sale de la de F-036 y no de `dev`, y eso es lo que se quería aquí —F-036 se cierra apoyada en esta misma medición—. 347 mutantes, **184 muertos y 163 supervivientes**, sin muestreo. Los **3 «timeouts»** que imprimió el CLI NO eran mutantes lentos sino contención del arranque (los mutantes 6, 7 y 9 de 347, con 4 workers midiendo líneas base a la vez): reinyectados uno a uno mueren en menos de 3,5 s, y por eso se cuentan como muertos. Los 163 supervivientes quedan **todos** analizados, ninguno `PENDIENTE`: 96 eran huecos reales y se cerraron con tests nuevos, 7 son equivalentes justificados con su guarda, y 60 se justifican **en bloque** —los dos `scripts/diagnose_sigrid_contrato_docs*.py`, diagnósticos manuales fuera del pipeline, con autorización expresa del humano del 2026-09-10—. El desglose, en `progress/impl_F-043_T28_supervivientes.md`. |

| `progress/mutacion_F-043_T31_defecto.md` | No | `VÁLIDA` | Campaña acotada al **arreglo del defecto de T31** (la clasificación no llegaba a las seis columnas `tipologia*` cuando el documento ya estaba persistido), no a la feature entera: `--base HEAD~3 --rama HEAD` para que el diff sean solo sus tres commits, `--workers 1` porque el árbol tenía un fichero sin versionar ajeno al trabajo. 2 ficheros y 114 líneas de alcance, **7 mutantes, 7 muertos, 0 supervivientes**, campaña completa (sin muestreo). No repone ni sustituye a `progress/mutacion_F-043.md`, que es la de T28: mide líneas que aquella no tenía. El análisis, en `progress/impl_F-043_T31_defecto.md` §7.1. |
| `progress/mutacion_F-045.md` | No | `VÁLIDA` | Campaña **completa** (sin muestreo, nivel `critico`) de la CAPA 1 de F-045: el paquete nuevo `evals/revision/`, 11 ficheros y 2371 líneas de alcance —son ficheros nuevos, así que el diff es el fichero entero—. **266 mutantes, 176 muertos, 90 supervivientes**, 0 timeouts, 0 sin veredicto, 6381 s con `--workers 4` (con el `README.md` del humano apartado a un stash mientras corría: la campaña paralela crea sus worktrees desde HEAD y se niega con el árbol sucio). Antes hubo que **desbloquear la línea base**, que estaba ROJA para CUALQUIER campaña de este repositorio: `harness/mutacion.py` lanza la suite con `PYTHONDONTWRITEBYTECODE=1` y `test_C_un_mutante_nunca_se_juzga_con_el_bytecode_del_anterior` heredaba esa variable en sus subprocesos; el arreglo es mejora del arnés y hay que portarla a `arnes-base`. Los 90 supervivientes quedan **todos analizados, ninguno `PENDIENTE`**: 71 cerrados con tests nuevos (62 tests en dos ficheros más refuerzos en los de la CLI) y 19 justificados como equivalentes en seis grupos. El cierre NO se midió con una segunda campaña —el intento se degradó: cinco horas en el primer fichero con un worker bloqueado— sino **reinyectando cada superviviente uno a uno** contra la suite acotada a F-045 (~11 s cada uno), la misma técnica que esta tabla documenta para F-043. |

| `progress/mutacion_F-045_lote2.md` | No | `VÁLIDA` | Campaña **completa** del SEGUNDO lote de F-045: las dos decisiones del humano del 2026-09-16 y la huella de importación que hizo falta para aplicarlas. `--base 5132bdc --rama HEAD` para que el diff sean solo esos commits; 7 ficheros y **325 líneas** de alcance, **44 mutantes, 35 muertos, 9 supervivientes**, 0 timeouts, 871 s con 4 workers. Los 9 caían en el codigo que acababa de perder datos —`huella.py` entero y las dos guardas de `escritura.py`— y se cierran **8 con test y 1 como equivalente** (`sort_keys`, comprobado ejecutando `json.dumps` con y sin él sobre la huella real: idéntico, porque dentro hay listas y no dicts, a diferencia de `mapa.py`). La primera versión de este informe decía «los 9 con test» y era falsa por los dos lados: el reviewer encontró que el 7 es equivalente y que el 3 **seguía vivo**, porque su test colapsaba las filas en un `dict` y no veía que el mutante duplica la sintética del humano. No repone a `progress/mutacion_F-045.md`, que es la de la capa 1: mide líneas que aquella no tenía. |

## Recuento

- Informes inventariados: **17**.
- Con alcance fuera de `services/`: **7** (F-011, F-012, F-034, F-038,
  maquinaria-paralela-F-039, F-039, F-040).
- Medidos con la invocación rota y **no repuestos**: **2** (F-011 y F-012).
  Ninguno de los dos se va a rehacer, y las dos cabeceras lo dicen.
