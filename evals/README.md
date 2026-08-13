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
