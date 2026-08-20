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

## Recuento

- Informes inventariados: **13**.
- Con alcance fuera de `services/`: **6** (F-011, F-012, F-034, F-038,
  maquinaria-paralela-F-039, F-039).
- Medidos con la invocación rota y **no repuestos**: **2** (F-011 y F-012).
  Ninguno de los dos se va a rehacer, y las dos cabeceras lo dicen.
