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
que es lo que corre en producción), `--fases` para acotar la corrida.

Pedir IA1/IA2 sin `--con-llm` se rechaza: el gasto en LLM nunca es implícito.

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
