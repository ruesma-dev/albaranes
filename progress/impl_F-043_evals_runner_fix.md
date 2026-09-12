<!-- progress/impl_F-043_evals_runner_fix.md -->
# F-043 · arreglo del canal de salida de los subprocesos de evals

Defecto que impedía lanzar la pasada de evals con LLM (T30). Medido y
arreglado el 2026-09-12 en `feature/F-043-clasificacion-por-ia1`.

## La causa

`python -m evals.runner --con-llm --feature F-043` moría en
`evals/procesos/sv2_extraccion.py:239`, `json.loads(proceso.stdout)`, con
`JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

El subproceso NO fallaba: volvía con código 0 y el JSON entero. Lo que pasaba
es que PyMuPDF escribe en **STDOUT** —el mismo canal por el que vuelve el
resultado— su aviso de que `fitz` está deprecado, en cuanto `_adjuntos()`
importa la librería para preparar el PDF del albarán. El stdout del hijo era:

```
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
{"resultados": []}
```

Reproducido a mano en este mismo intérprete (`import fitz` + un `print` de
JSON, sin evals de por medio): esas dos líneas exactas por stdout, con el
aviso primero.

Con `casos: []` nadie abre un PDF, nadie importa `fitz` y el stdout sale
limpio: por eso ni los tests ni la corrida determinista lo veían nunca.

## La solución, y por qué esta

Nuevo módulo `evals/procesos/canal.py`. Arregla el canal **por los dos
extremos**, que son dos barreras independientes:

1. **El que escribe blinda su stdout** (`blindar_stdout`): duplica el
   descriptor 1 y le enchufa encima el 2 (`os.dup2(2, 1)`). A partir de ahí
   nadie —ni un `print` de Python ni una librería en C— puede escribir en el
   canal limpio; el ruido sale por stderr, que es donde el lector ya mira
   cuando algo falla. El JSON se emite al final por el descriptor guardado.
2. **El que lee delimita la carga** (`leer`): la carga viaja entre
   `<<<EVALS-JSON-INICIO>>>` y `<<<EVALS-JSON-FIN>>>`, y el lector se queda
   con la **última** marcada.

Ninguna de las dos sobra. El blindaje solo puede actuar a partir de la
primera línea que ejecuta el hijo: lo que se imprima ANTES —un
`sitecustomize`, el banner de un intérprete, un `.pth` hablador— ya está en el
canal, y de eso solo salvan las marcas. Y al revés: sin blindaje, el ruido se
tragaría en silencio en vez de quedar en stderr, donde se diagnostica; si
mañana lo que se cuela es un error de verdad («MuPDF error: cannot open
document»), llega al humano en vez de perderse.

Descartado por insuficiente, como pedía el encargo: **filtrar el aviso de
`fitz` por su texto**. Tapa el síntoma de hoy y deja el canal igual de
frágil para la próxima librería habladora.

Descartado por más caro sin ser más robusto: **devolver el JSON por un fichero
temporal** cuya ruta se pasa por argv. Resuelve lo mismo, pero añade un fichero
que limpiar, un modo nuevo de fallar (disco, permisos) y rompe la costumbre de
lanzar el subproceso a mano y ver la salida.

## Fase RED → GREEN

El test reproduce el defecto sin gastar un céntimo: inyecta el ruido con un
`sitecustomize` de mentira en `PYTHONPATH`, que el arranque del intérprete
importa **antes** de que el hijo ejecute nada (el peor caso posible), y usa
sv6, que no llama a ningún LLM.

**RED** (mismo cuerpo del test, contra el código de entonces):

```
$ python -m pytest scratchpad/test_red_f043.py -q --tb=short
scratchpad/test_red_f043.py:15: in test_f043_el_lector_tolera_ruido_en_stdout_del_subproceso
    assert ejecutar_en_subproceso({"casos": []}) == {"resultados": []}
evals\procesos\sv6_build.py:590: in ejecutar_en_subproceso
    return json.loads(proceso.stdout)
...
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
s = 'warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.\n{"resultados": []}\n'
1 failed in 6.11s
```

(el `s = ...` del traceback es el stdout que recibió `json.loads`: el mismo
ruido y el mismo JSON intacto detrás que en la corrida real)

**GREEN**, ya con el canal y con el fichero de test definitivo,
`tests/test_f043_canal_subproceso.py` (9 tests):

```
$ python -m pytest tests/test_f043_canal_subproceso.py -q
.........                                                                [100%]
9 passed in 3.67s
```

Uno de esos nueve es el caso original con la librería de verdad
(`canal.blindar_stdout()`, `import fitz`, `canal.emitir(...)`): el aviso
aparece en stderr, no en stdout, y `leer` recupera la carga. Se salta solo si
PyMuPDF no está instalado.

## Los otros dos procesos tenían el mismo defecto

`sv5_valoracion.py` y `sv6_build.py` traían el mismo `json.loads(proceso.stdout)`
palabra por palabra (sv2:239, sv5:395, sv6:590). Los tres pasan ahora por
`canal.emitir` / `canal.leer`, y un test estructural
(`test_f043_ningun_proceso_de_evals_vuelve_a_leer_stdout_a_pelo`) impide que
vuelva a aparecer en `evals/procesos/`.

## Verificación de que no cambia nada más

- Pasada determinista completa (sin LLM, atraviesa los subprocesos de sv5 y
  sv6): `python -m evals.runner --feature F-043` termina y escribe informe,
  **idéntico salvo fecha y commit** al de la misma corrida sobre el código
  anterior (con mis cambios en `git stash`). Su ROJO es anterior a este
  trabajo y ajeno a él.
- El subproceso real de sv2, el que rompía, atravesado con cero casos y una
  clave de mentira (ni una llamada al proveedor): devuelve
  `{'resultados': [], 'proveedores': ['gemini']}` por el canal nuevo.

## ¿Queda desbloqueada la pasada de T30?

**Sí, en lo que toca a este defecto.** Los dos tramos del camino que fallaba
están verificados sin gastar: el blindaje contra el aviso real de PyMuPDF y el
subproceso de sv2 de punta a punta. Lo único que no se ha ejercitado es la
llamada al LLM en sí, que es exactamente lo que el encargo prohibía y lo que
no tenía nada que ver con el fallo: el subproceso ya volvía con código 0 y el
resultado completo.

Aviso para no crear falsas expectativas: **desbloqueada no es lo mismo que en
verde**. `progress/current.md` §3 deja abierto que las CONDICIONES no se
propagan al `contexto_linea` y los importes salen ×6 —se ve en la corrida
determinista de hoy, 720,0 donde se espera 120—, así que la pasada correrá,
pero su veredicto seguirá siendo ROJO hasta que eso se arregle.

## Segundo asunto, para que no se pierda: RES-001 y la carretera M-401

En la corrida del 2026-09-12, IA1 extrajo `obra_codigo = "0401"` para RES-001.
La dirección del albarán es `M-401 - S/N, FUENLABRADA`: **la IA convirtió el
nombre de la carretera en el código de obra**.

Un matiz que agrava el caso, leído del ground truth
(`evals/fixtures/IA1/RES-001.json`): el valor esperado de `obra_codigo` es
**vacío**, y el comentario del libro lo explica —«No imprime codigo de obra
(687/691 son de Sigrid)»—. O sea que no es que la IA acertara el campo
equivocado: **se inventó un código donde el papel no trae ninguno**, con el
trozo de texto que más se le parecía. Justo lo que el banco existe para cazar.
NO se ha tocado: es materia de prompt y lo dirá la eval cuando corra.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (suite raíz) | **565 passed, 0 failed** (incluye los 9 nuevos del canal) |
| Tiempo de la suite raíz | **131,03 s** suelta · **167,38 s** dentro de `init.sh` (con cobertura) |
| Suites de servicio | las 6 en verde en `init.sh` (sv3: 192 passed en 6,27 s; el resto por caché) |
| Cobertura de las líneas cambiadas | **90,2 % de 772 líneas (696/772)**, umbral 80 %, nivel `critico` → PUERTA COBERTURA en verde |
| `bash harness/init.sh` | **ENTORNO LISTO** (los avisos son anteriores: sin tests en sv1, `[ADAPTAR]` en specs de F-034/F-035, y la ruta sensible que reclama justo la pasada de T30) |
| Mutantes generados y supervivientes | campaña automática **imposible** (ver abajo); campaña a mano sobre `canal.py`: **7 mutantes, 5 muertos, 2 supervivientes** |

**Por qué no hay campaña automática.**
`python -m harness.mutacion --feature F-043 --ficheros evals/procesos/canal.py --workers 1`
aborta antes de mutar nada:

```
LÍNEA BASE EN ROJO en .: la suite falla SIN mutar nada.
  Tests que fallan sin mutar:
    - tests/test_mutacion_prueba_de_verdad.py::test_C_un_mutante_nunca_se_juzga_con_el_bytecode_del_anterior
```

Es una de las causas que la propia herramienta documenta: `evals/` no cae en
ningún servicio de `harness/servicios.json`, así que la suite se invoca **sin
ruta** desde la raíz y esa recolección tumba un test del arnés que con ruta
pasa (`python -m pytest tests/test_mutacion_prueba_de_verdad.py -q` →
`6 passed`). Es anterior a este trabajo y vive en `harness/`, que el encargo
me prohíbe tocar: **queda para el humano** (es mejora de arnés, y de las que
se propagan a `arnes-base`).

**Campaña a mano** (aplicar mutante → correr `tests/test_f043_canal_subproceso.py`
→ restaurar; script en el scratchpad, el fichero quedó restaurado y el árbol
limpio):

| Mutante | Resultado |
|---|---|
| `rfind` → `find` en la marca de inicio | MUERTO |
| `inicio < 0` → `inicio <= 0` | MUERTO (**era un hueco real**: ningún test leía un stdout cuya marca empezara en el carácter 0; se añadió el test y el mutante pasó de superviviente a muerto) |
| `fin < 0` → `fin <= 0` | SOBREVIVE |
| descriptor de destino invertido en `emitir` | MUERTO |
| `os.dup2(2, 1)` → `pass` (blindaje desactivado) | MUERTO |
| `emitir` sin marca de fin | MUERTO |
| `_recorte`: tope 2 000 → 20 000 caracteres | SOBREVIVE |

Análisis de los dos supervivientes, los dos en el formateo del diagnóstico y
ninguno en el camino del dato:

- `fin < 0` → `fin <= 0`: **equivalente en la práctica**. Solo se distinguen
  si la marca de fin va pegada a la de inicio, o sea con carga de longitud
  cero. `emitir` siempre escribe `\n` entre ambas y el mensaje sale de una
  sola escritura (una escritura parcial corta la cola, nunca el centro), así
  que ese stdout no lo puede producir ningún emisor. Cambia qué mensaje de
  error se da ante una entrada inalcanzable; pinarlo con un test sería fijar
  el texto de un error imposible.
- `_recorte` con otro tope: **equivalente**. El tope decide cuánto ruido se
  copia dentro del `RuntimeError`; no hay comportamiento que dependa de él.
  Un test del número exacto clavaría una cifra arbitraria.

## Ficheros tocados

- `evals/procesos/canal.py` — **nuevo**: el canal (blindaje, `emitir`, `leer`).
- `evals/procesos/sv2_extraccion.py`, `sv5_valoracion.py`, `sv6_build.py` —
  `main()` blinda y emite por el canal; `ejecutar_en_subproceso()` lee por él.
- `tests/test_f043_canal_subproceso.py` — **nuevo**: 9 tests.
- `evals/README.md` — qué es el canal y por qué, para el próximo adaptador.

Commits: `F-043 evals: el JSON del subproceso deja de viajar mezclado con el
ruido` y `F-043 evals: documenta el canal y cierra el hueco que enseno la
mutacion`.

## Verificaciones MANUAL pendientes

- La pasada de T30 con LLM (`python -m evals.runner --con-llm --feature F-043`)
  la lanza el humano: se factura y el encargo la prohibía expresamente.
- La línea base roja de `harness.mutacion` para ficheros fuera de
  `harness/servicios.json` (arnés, propagable a `arnes-base`).
