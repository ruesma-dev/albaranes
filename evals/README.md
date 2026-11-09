<!-- evals/README.md -->
# Evals de IA — ground truth del pipeline

Banco de casos con resultado esperado para las cuatro fases de IA y para el
resultado final del albarán. Implementado en la feature **F-011**
(`specs/F-011-evals-ia/`).

## Los seis libros de `ground_truth/`

| Libro | Qué contiene | Papel |
|---|---|---|
| `RESULTADO_FINAL.xlsx` | Cómo debe quedar cada albarán al final: datos generales, cada línea impresa con su match, partida, precio e importe, y las líneas añadidas que NO están impresas | **Maestro**. Si solo se rellena un libro, este |
| `IA1_extraccion.xlsx` | Cabecera y líneas esperadas de la extracción (sv2) | Eval de fase |
| `IA2_contexto.xlsx` | `contexto_linea` esperado por línea y tipología (sv2) | Eval de fase |
| `IA3_valoracion.xlsx` | Matches esperados, sintéticas que DEBEN emitirse y sintéticas PROHIBIDAS (sv5) | Eval de fase |
| `IA4_conciliacion.xlsx` | Conciliación esperada de las líneas sin match (sv5) | Eval de fase |
| `INPUTS.xlsx` | La ENTRADA de los casos de IA3/IA4: líneas de albarán, líneas de contrato y condiciones | Entrada |

Los libros IA1–IA4 no sustituyen al maestro: sirven para **localizar en qué
fase se rompe** lo que el extremo-a-extremo detecta.

Los albaranes de entrada de IA1/IA2 van en `inputs/albaranes/` con el nombre
`<caso_id>.pdf` (o `.jpg`). Cada pestaña LEEME explica cómo rellenar su libro.

### Convenios de celda

- Celda **vacía** → el eval espera `null`.
- **`?`** → ese campo NO se compara en ese caso (por encima de la criticidad).
- **`REVISIÓN`** en precio o partida de `RESULTADO_FINAL` → se espera que el
  sistema NO invente y lo deje a revisión humana. Es un resultado esperado
  legítimo, no un hueco.
- Fechas en `AAAA-MM-DD`; `descuentos` como lista separada por `;`; decimales
  con coma o con punto.
- `caso_id` con prefijo de tipología: `GEN/HOR/MOR/RES/BOM/COM/ALQ-NNN`.

## Qué se versiona y qué no

Los `.xlsx` y los albaranes **no** se versionan (ofimática y documentos de
proveedor fuera de git). Sí se versionan los **fixtures** JSON que genera el
conversor, tras el barrido de datos sensibles de C3 bis. Precios, razones
sociales y CIF sí entran en los fixtures: son el ground truth y el repositorio
es privado (decisión D1 de F-011).

## Comandos

```bash
# 1. Libros Excel -> fixtures JSON versionables (todo o nada)
python -m evals.conversor

# 2a. Modo determinista: redes de sv6 estimuladas + extremo a extremo.
#     Cero llamadas de red, cero coste. Para el desarrollo diario.
python -m evals.runner --feature F-XXX

# 2b. Pasada completa: IA1, IA2, IA3, IA4 y extremo a extremo con LLM reales.
#     CUESTA DINERO. Se lanza a demanda o cuando la puerta la exige.
python -m evals.runner --con-llm --feature F-XXX

# 3. La puerta del arnés (la ejecuta init.sh; nunca lanza los evals)
python -m harness.rutas_sensibles --validar
```

Opciones útiles: `--casos GEN-001,HOR-002` para acotar, `--proveedores` para
ampliar IA1/IA2 más allá del proveedor primario (por defecto solo el primario,
que es lo que corre en producción) y fijar el de IA3/IA4 (el primero de la
lista; sin ella, el de producción, F-084), `--fases` para acotar la corrida.

Pedir IA1/IA2 sin `--con-llm` se rechaza: el gasto en LLM nunca es implícito.

## El contrato de cada caso: líneas y documento (F-084)

IA3, IA4 y el extremo a extremo solo miden el modelo si el caso trae su
contrato: sin líneas, todo sale `no_match` con cualquier modelo. Dos
subcomandos lo traen de producción. **Los dos son solo lectura, los lanza el
humano con sus credenciales en la consola** y `harness/init.sh` no los invoca
nunca.

```bash
# 1. Líneas del contrato: sigrid-api -> ground_truth/INPUTS.xlsx › CONTRATO_LINEAS
python -m evals.contratos lineas --dry-run     # solo el informe, el libro no se toca
python -m evals.contratos lineas [--casos A,B]

# 2. Cabecera y documento del contrato: BBDD albaranes + SharePoint
python -m evals.contratos documentos [--casos A,B]

# 3. Libros -> fixtures, y la corrida determinista
python -m evals.conversor
python -m evals.runner --feature F-XXX
```

El orden importa: **importar → convertir → determinista**. Las líneas entran
por el libro, no por los fixtures, porque el conversor regenera los JSON desde
los libros y pisaría cualquier cosa escrita a mano.

- **`lineas`** lee de sigrid-api (`POST /api/sql/read`, un `SELECT` por código
  de contrato distinto, `emp = 1`, `NO_TOLERA` con `truncated`) con
  `SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY` y `SIGRID_API_DATABASE`.
  Escribe una fila por línea y caso en `CONTRATO_LINEAS` (con `linea_sigrid`,
  la línea de Sigrid) y la `fecha_albaran` que falte en `CONDICIONES`, sacada
  de IA1. Copia el libro a `ground_truth/copias/` antes de escribir y no lo
  guarda si nada cambia. **No toca los casos que ya tienen líneas** (los RES
  escritos a mano, con sus señuelos). Un contrato que falla (truncado, 0 o más
  de un `ctr.ide`) no se escribe y el resto sigue.
- **`documentos`** lee, con la SQL y el descargador de sv5, la fila de
  `albaran_contratos_merge` (sesión de solo lectura) y el MD del contrato que
  sv3 dejó en SharePoint, o el PDF si no hay MD (tope `MAX_PDF_MB` = 40, el de
  sv5). Necesita las `PG_*` **de Azure** en la consola (el `.env` de los
  servicios apunta a local), `GRAPH_KEY` y las `SHAREPOINT_*` de sv5. El
  documento queda en `evals/inputs/contratos/` (no versionado: precios de
  proveedor y firmantes) y su huella en `evals/fixtures/contratos/_indice.json`
  (versionado, sin contenido: tipo, sha256, tamaño, motivo y la cabecera).
- **El informe** de los dos es `progress/import_F-084.md`: recuentos,
  `caso_id` y `num_linea`, nunca precios ni descripciones. Lleva el control del
  contrato vigente: de las líneas IA3 con precio `contrato_db`, cuántas tienen
  su precio entre los importados (Sigrid da el precio de hoy).

Lo que hace el runner con eso:

- El contexto de IA3 es el de producción: descuento, precio neto e importe
  derivado como el `SELECT` de sv5, la clasificación del documento desde la
  tipología del caso (sv5 elige `valuation_residuos` para los RES), las
  categorías de unidad de `UnitCategoryPrefilter`, la fecha y el número de
  `CONDICIONES`, la cabecera del índice y el documento local en la misma
  llamada (MD en el texto, PDF como adjunto).
- Un caso con contrato y **sin líneas de contrato** sale `OMITIDO` en IA3, IA4
  y E2E, en las dos corridas, sin mandarlo a sv5. Igual si el índice declara un
  documento que **no está en local** o no casa con su sha256 (un clon limpio):
  mejor no medir que medir otra cosa. Un descuento compuesto (`a;b`) sale
  `ERROR`.
- Sin `--proveedores`, IA3/IA4 usan `IA3_PROVIDER` del entorno o, si no, el
  proveedor de producción, y el modelo de la variable del proveedor
  (`OPENAI_MODEL`…) o el de producción: la referencia de IA3 de
  `evals/precios_modelos.json`, que vigila `infra/create_capps.ps1`. El informe
  dice el modelo y el documento con que se valoró cada fase.
- Con `--fases IA3,IA4,E2E`, sv2 no se invoca ni se le piden claves.
- **El determinista no mide el emparejamiento** y lo dice en su informe: una
  línea sin emparejar en el ground truth sigue sin emparejar, porque emparejar
  es trabajo de IA3/IA4 y solo lo mide la corrida con LLM.

## Cómo se decide el veredicto

No hay umbral porcentual. Manda **qué campo** discrepa, según
`evals/criticidad.json`:

- Campo **crítico** (partida, cantidades, precios, importes, códigos) →
  **FALLO**: el caso es ROJO.
- Campo **laxo** (descripciones, comentarios, motivos) → **AVISO**: consta en
  el informe y no impide el verde.
- Campo **sin clasificar** → se trata como crítico y además se avisa: olvidar
  una entrada no puede relajar nada.

Subir un campo de laxo a crítico es una línea de `evals/criticidad.json`.

Códigos de salida del runner: `0` VERDE, `1` ROJO, `2` NO_EVALUABLE. Mientras
los libros estén vacíos el veredicto es NO_EVALUABLE: un informe sin casos no
es evidencia.

## Dónde queda todo

- `evals/fixtures/<fase>/<caso_id>.json` — casos convertidos (versionados),
  con el `sha256` del libro del que salieron.
- `progress/evals_F-XXX.md` — informe de cada corrida (o `evals_manual.md`).

## La puerta del arnés

`harness/rutas_sensibles.json` declara las rutas cuyo cambio exige una pasada
completa: prompts YAML, schemas Pydantic, clientes LLM y redes deterministas
de sv6. Si el diff de la feature las toca, `bash harness/init.sh` reclama el
informe. La exigencia arranca en `aviso` y se sube a `bloqueo` cuando los
libros tengan casos. El mecanismo es genérico y vive también en `arnes-base`;
lo específico de este repositorio es la declaración y el runner.

## Dependencias

`pip install -r evals/requirements.txt` en el venv **raíz** del monorepo. El
runner compone sv2, sv5 y sv6 desde fuera, cada uno en su propio subproceso
(comparten los nombres de sus paquetes de primer nivel y no caben en el mismo
intérprete).

### El canal de vuelta del subproceso

Cada subproceso devuelve su resultado por stdout, pero **no como JSON a pelo**:
lo emite entre las marcas de `evals/procesos/canal.py`, y antes de empezar el
trabajo redirige su descriptor 1 al 2. El motivo tiene fecha: el 2026-09-12 la
pasada con LLM murió entera en `json.loads` porque PyMuPDF había escrito en
STDOUT su aviso de que `fitz` está deprecado. Cualquier librería puede imprimir
ahí; el canal de datos no puede ser el mismo sitio donde todo el mundo habla. Si
escribes un adaptador nuevo en `evals/procesos/`, usa `canal.emitir` y
`canal.leer`: hay un test que lo vigila.

Si un hijo muere, su stderr completo sale por la consola de la pasada y **no se
redirige a `progress/`** (puede llevar valores del albarán): guárdalo tú si lo
necesitas, porque el informe solo trae el motivo corto.

## Comparar modelos (F-083)

`python -m evals.comparar_modelos` mide varios modelos en **una** fase (IA1, IA2,
IA3 o IA4) con el acierto del banco y el **coste por albarán**, para decidir si
merece la pena cambiar el modelo de producción. **Cuesta dinero y solo lo lanza
el humano**; `harness/init.sh` no lo invoca nunca.

```bash
# Siempre primero: estimación sin claves ni llamadas (sale con 0)
python -m evals.comparar_modelos --fase IA1 --modelos gpt-6-luna,gemini-4-argon --estimar

# La corrida de verdad (pide las claves de los proveedores que use)
python -m evals.comparar_modelos --fase IA1 --modelos gpt-6-luna,gemini-4-argon \
    [--casos GEN-001,HOR-001] [--repeticiones 3] [--tope-usd 25] [--tope-total-usd 200]
```

- **Modelos y precios**: `evals/precios_modelos.json`, versionado, con fuente
  oficial y fecha de consulta por modelo. Los `excluido` no se pueden pedir.
- **Referencia**: el modelo de producción de la fase (`infra/create_capps.ps1`)
  se añade siempre y va primero en cada repetición; la recomendación se decide
  contra ella, medida en la misma invocación.
- **Cómo se aísla la fase**: IA2 parte de una IA1 de la referencia hecha una
  sola vez; IA4 concilia sobre una IA3 de la referencia hecha una sola vez; en
  IA3 la conciliación sale del libro IA4 (sin LLM). Cada bloque (modelo,
  repetición) corre en su propio subproceso.
- **Coste**: tokens reales leídos por `evals/procesos/medidor.py`, que entra
  como `call_logger` de los clientes de comun sin tocarlos, por la tabla.

Paradas **antes de gastar** (código 2), por este orden: modelo que no está en
la tabla o está excluido, tabla de precios caducada, falta la clave de algún
proveedor (también el de la preparación), la estimación supera `--tope-usd`,
o el gasto acumulado de la feature más la estimación supera `--tope-total-usd`.

Códigos de salida: `0` hecho, `1` ningún candidato dio resultado, `2` parada
antes de gastar, `3` cortado por `--tope-usd` a mitad (lo pendiente queda
`NO_EJECUTADO` y el informe se escribe con lo hecho).

Dónde queda cada cosa:

- `progress/comparar_modelos_F-083.md` — resumen **sin valores**, acumulativo:
  una sección por invocación con la tabla por modelo (casos, `ERROR`,
  `NO_EJECUTADO`, fallos críticos, tiempos, tokens, USD por albarán, modelo
  servido y motivo de parada), la recomendación y dos líneas que se leen de
  vuelta: `GASTO:` (el gasto real, que suma el tope de la feature) y `TOKENS:`
  (que usa la estimación siguiente).
- `evals/salidas/comparar_modelos/<fecha-hora>/` — el detalle **con valores**
  (`detalle.md`, `resultados.json` y un `registros_*.jsonl` por bloque). Git lo
  ignora.

Si el modelo que dice la respuesta no es el pedido (Google sirve
`gemini-3.8-flash` a quien pide `gemini-3.7-flash`), el informe lo avisa junto
al modelo. Las cifras de IA3 y E2E no son comparables con las del runner: aquí
IA4 sale del libro.

## Comparar la fecha (F-112)

`python -m evals.comparar_fecha` mide si la fecha de recepción del correo como
referencia del año (`{fecha_recepcion}` en IA1, `{revision_fecha}` en IA2) arregla
el año mal leído sin romper lo que funciona. Compara la variante **base** (los
YAML de `--base`, por defecto `dev`) con la **rama**, IA1 y luego IA2, sin correo,
sin lista de obras y sin Sigrid. **Cuesta dinero y solo lo lanza el humano.**

```bash
# Antes: las imágenes del juego D (no llama a ninguna IA; deterministas)
python -m evals.sinteticos_fecha

# Comprobaciones sin gastar (claves, albaranes, JSON de casos, git show de la base)
python -m evals.comparar_fecha --solo-validar

# La corrida de verdad: A, B a 20, C y D, dos repeticiones
python -m evals.comparar_fecha --variante ambas --repeticiones 2 [--juegos A,B,C,D]
```

- **Juegos**: **A**, los documentos de producción de `evals/casos_fecha.json`
  (versionado; `caso_id`, `tipologia`, `clase` `anio`/`dudoso`/`antigua`,
  `fecha_esperada` y `recibido`, sin datos del proveedor) con su recepción real;
  **B**, 20 casos del banco con fecha esperada (semilla fija) y referencia =
  esperada + 7 días; **C**, los del banco anteriores a 2025, referencia +730
  días; **D**, los sintéticos de cambio de año de `evals/casos_fecha_sinteticos.json`
  (lo escribe `evals.sinteticos_fecha`; imágenes `SIN-00N.jpg` en
  `evals/inputs/albaranes/`). En A y D la referencia sale de `fecha_recepcion_de`
  de sv2 (día en Europe/Madrid).
- **Categorías** por fecha: `exacta`, `referencia` (copió la recepción),
  `solo_anio` (el fallo), `otra`, `nula`, `error`; mayoría de las repeticiones
  (empate ⇒ `inestable`). Aparte, el **efecto de IA2** por ejecución: `corrige`,
  `estropea`, `cambia`, `igual`.
- **Veredicto** (C1–C7 de la spec): VERDE solo con las dos variantes, los cuatro
  juegos y todos los criterios; si no, NO APLICA o ROJO.
- Paradas **antes de gastar** (código 2): falta una clave, ningún caso con
  albarán, un JSON de casos que no valida (el mensaje no cita su contenido) o el
  `git show` de la base falla.
- Dónde queda: `progress/comparar_fecha_F-112.md`, **sin valores** (recuentos,
  caso_id, tabla del efecto de IA2 y veredicto); `evals/salidas/comparar_fecha/<fecha-hora>/`,
  con las fechas leídas (git lo ignora).
