<!-- specs/F-047-evals-ciclo-completo/design.md -->
# F-047 · Diseño técnico — el ciclo completo del banco de evals

## 1. La cadena, y por qué NO va por colas

El hand-off entre servicios en producción es un JSON, no la cola: la cola solo
lo transporta. El ciclo se encadena **por esos mismos JSON, en secuencia y en
memoria**, reutilizando el código de aplicación de cada servicio:

| Paso | Qué corre (código de producción reutilizado) | Qué sale |
|---|---|---|
| IA1 | `AlbaranExtractionService.extract_phase_1` (sv2) | `DocumentoAlbaran` |
| IA2 | `.review_phase_2` (sv2) | documento revisado |
| sv2→sv3 | `clasificacion_resolver.resolver_clasificacion` + `phase_merge.construir_envelope_final` (sv2) | envelope de `q-persistencia` |
| contrato | `obra_code_normalizer`, `albaran_normalizer`, `contexto_linea_merger` (sv3) + `SigridApiContratoClient.fetch_contratos` + `contrato_selector.elegir_contrato_probable` | `ContextoValoracion` |
| IA3+IA4 | `ValuationExtractionService` + `ConciliacionService` (sv5) | envelope de sv5 |
| build | `valuation_builder` (sv6) | records finales |

Dos escalones de HOY quedan a la vista y se cierran aquí: el eval **no pasaba
por `phase_merge`** (fusionaba fase 1 y 2 a mano) ni por el resolver de
clasificación, que es justo la costura de F-043.

**No hacen falta ni Azurite ni Postgres.** La ficha los daba por necesarios
porque el ciclo real va por colas; encadenando por hand-off no lo son, y evita
lo que hace inservible la vía por colas para un banco: es asíncrona, no deja ver
la salida de cada IA sin espiar la BBDD, y escribir en Postgres desde local es
justo lo que las reglas duras prohíben. **Decisión para el humano** (va a
`progress/current.md`).

**Costuras que este diseño NO cubre**, y se declaran en el informe en vez de
fingirse: el transporte por cola, la persistencia SQL de sv3/sv6, el
`header_grounding_service` contra Sigrid y la descarga de PDF de contrato. Cada
una es candidata a ficha propia; ninguna produce un verde silencioso porque lo
que no se ejecuta no se compara.

## 2. Ficheros

### A crear

- `evals/cadena.py` — orquesta el ciclo de UN caso: llama a los adaptadores en
  orden, recoge `SalidaFase` por fase y corta en cuanto una fase no produce
  (R4). Puro respecto de la red: recibe los adaptadores inyectados.
- `evals/procesos/sv3_contrato.py` — adaptador de sv3. Parte PURA: del envelope
  de sv2 al `ContextoValoracion` (líneas de albarán + `contexto_linea` +
  clasificación). Parte de SUBPROCESO: `fetch_contratos` contra sigrid-api con
  `sys.path` de sv3, agrupando por (CIF, obra) (R26, R27).
- `evals/atribucion.py` — puro. Etiqueta cada `Discrepancia` con
  `PROPIO`/`ARRASTRADO`/`INDETERMINADO` (§3). Sin red, sin BBDD, sin LLM.
- `evals/atribucion.json` — el mapa de dependencias versionado (R13).
- `evals/salidas.py` — caché de salidas crudas por caso y fase (§6).
- `evals/preflight.py` — comprobación de dependencias antes de gastar (§5).
- `tests/test_f047_*.py` — un fichero por bloque de requisitos.

### A modificar

- `evals/modelos.py` — `Discrepancia` gana `atribucion`, `fase_origen` y
  `causa`; `ResultadoCaso` cuenta propios/arrastrados/indeterminados;
  `ResultadoFase.veredicto()` mira SOLO los propios (R11);
  `ResultadoPasada.veredicto()` degrada a NO_EVALUABLE con indeterminados (R12).
- `evals/runner.py` — `corrida_ciclo()` nueva; `corrida_completa()` se renombra
  a `corrida_por_fases()` sin cambiar su comportamiento; `--por-fases`,
  `--reutilizar`, `--desde`; `--casos` filtra TODAS las fases (hoy solo
  `inputs`, `IA1` e `IA2`).
- `evals/informe.py` — `MODO_CICLO`, el eje de atribución, el cuadro por fase,
  el apartado por fase de origen y el de entrada que ahora produce el sistema.
- `evals/procesos/sv2_extraccion.py` — el subproceso devuelve además el
  envelope de `phase_merge` y la clasificación resuelta; `OBSERVABLES` gana
  `tipologia` cuando el ciclo la produce.
- `evals/mapa_casos.json` y `evals/revision/{reparto,escritura,informe}.py` —
  el mapa gana `clasificacion` (`no_regresion`/`defecto_conocido`),
  `familia_en_catalogo` y `criterios_residuos` para que el informe del CICLO
  agrupe por los mismos ejes que hoy agrupa el de importación (R33).
- `.gitignore` — `evals/salidas/`.
- `evals/README.md` — las dos formas de correr y el eje de atribución.

### Que NO se tocan

`evals/conversor.py` (única puerta a los fixtures y único sitio del barrido de
sensibles), `evals/comparador.py`, `evals/criticidad.py` y sus datos, los seis
libros de `evals/ground_truth/`, los 264 fixtures, y **ningún fichero bajo
`services/`**: el banco se adapta al sistema, nunca al revés.

## 3. La atribución del fallo

### El mapa (`evals/atribucion.json`)

Declara, por campo comparado de aguas abajo, de qué campos de aguas arriba
depende **en la misma línea del mismo caso**. Forma:

```json
{"IA3.lineas_valoradas.importe_calculado":
   ["IA1.lineas.cantidad", "IA3.lineas_valoradas.precio_unitario_final"],
 "E2E.lineas.precio_source": ["IA3.lineas_valoradas.precio_source"],
 "IA3.lineas_valoradas.codigo_producto_contrato":
   ["IA1.lineas.descripcion_esperada", "IA2.contexto.valor_esperado",
    "CONTRATO.contrato_elegido"]}
```

Se carga validando contra las tablas de `OBSERVABLES` de cada proyección: un
campo que ninguna proyección produce ABORTA la carga (R14). No hay herencia
implícita entre fases: lo que no está declarado es `PROPIO`.

### La regla (`evals/atribucion.py`)

Entrada: las discrepancias de las cinco fases de UN caso. Salida: las mismas
discrepancias etiquetadas. En este orden:

1. **Línea ausente en IA1** — si `IA1.lineas[n]` salió como «fila del ground
   truth que el sistema no ha producido», toda discrepancia de la línea `n`
   aguas abajo es `ARRASTRADO` a IA1, causa `linea ausente en IA1` (R9).
2. **Identidad dudosa** — si la línea `n` existe pero su campo de identidad
   (`descripcion_esperada`) discrepa, con fallo o con aviso, el emparejado por
   `num_linea` ya no es fiable: toda discrepancia posterior de `n` es
   `INDETERMINADO` (R10). Es el caso en que atribuir mal sería peor que no
   atribuir, y por eso existe la tercera etiqueta.
3. **Dependencia declarada que falló** — la discrepancia es `ARRASTRADO` a la
   fase del campo del que depende, con ese campo como causa. Si varias
   dependencias fallaron, gana la de la fase MÁS TEMPRANA (R5: primera fase
   donde nace).
4. **Todo lo demás** es `PROPIO`.

Para los campos de cabecera (sin línea) la ligadura es por caso, y la regla 2 no
aplica: no hay emparejado que romper.

### Qué hace cada etiqueta con el veredicto

- `PROPIO` con severidad `fallo` → la fase es ROJA (R11).
- `ARRASTRADO` → no tumba a nadie; suma en el recuento de la fase de ORIGEN y
  aparece en su apartado (R35). Un error de IA1 deja de contarse cuatro veces.
- `INDETERMINADO` → no tumba a nadie, pero impide el VERDE de la pasada
  (NO_EVALUABLE, R12): el banco no pudo juzgar y eso tiene que verse.

## 4. Qué ground truth se reutiliza, fase por fase

| Libro / tabla | En ciclo completo |
|---|---|
| `IA1` cabeceras y líneas | **Sigue igual.** Su entrada ya era el PDF |
| `IA2` contexto | **Sigue igual.** Cambia de dónde viene su entrada, no la expectativa |
| `IA3` líneas valoradas y sintéticas | **Sigue igual**, y por fin mide: hay contrato |
| `IA4` conciliación | **Sigue igual** |
| `RESULTADO_FINAL` | **Sigue igual**: es el destino |
| `INPUTS.CASOS.tipologia` | De entrada a **expectativa** de la clasificación (R5) |
| `INPUTS.CASOS.contrato_codigo` | De entrada a **expectativa** de la fase contrato (R17) |
| `INPUTS.LINEAS_ALBARAN` | **Deja de ser entrada**: las produce IA1. Es el mismo dato que `IA1.LINEAS`, que sí sigue siendo expectativa. Se conserva para `--por-fases` |
| `INPUTS.CONTRATO_LINEAS` | **Deja de tener sentido** en ciclo: las trae sigrid-api. Se conserva para `--por-fases`, donde sus señuelos (RES C1/C2) siguen midiendo el matching |
| `INPUTS.CONDICIONES` · `fecha_albaran`, `numero_albaran` | **Las produce IA1** |
| `INPUTS.CONDICIONES` · `codigo_ler`, `volumen_m3` | **Las produce IA2** (`contexto_linea`) |
| `INPUTS.CONDICIONES` · `tamano_contenedor_contrato` | No la produce ninguna IA: sale del contrato. Si el contrato leído no la trae, el criterio de contenedores queda **NO_EVALUABLE**, no se inyecta (R18) |

Nada de esto se borra de los libros: se deja de leer en modo ciclo y se declara
en el informe. Con esto desaparece el motivo de los ~865 fallos «obtenido None»
de la pasada del 2026-09-16, y las tres vías de
`progress/impl_F-045_contrato_lineas.md` quedan sin objeto.

## 5. Las dos formas de correr, y el preflight

```
python -m evals.runner --con-llm [--casos ...] [--reutilizar] [--desde IA3]
python -m evals.runner --con-llm --por-fases        # aislar un defecto
python -m evals.runner                              # determinista, sin red
```

`--con-llm` a secas es el **ciclo** (R20); `--por-fases` es lo de hoy, intacto
(R19). El determinista no cambia (R21). `MODO: ciclo` en la línea parseable, y
`informe.es_pasada_completa` exige `ciclo` + las cinco partes; acepta también
`completa` durante la transición, con un aviso de que no cubre las costuras.

`evals/preflight.py` corre ANTES de la primera llamada y devuelve la lista de lo
que falta, nombrado: claves LLM por proveedor, `SIGRID_API_BASE_URL` /
`_FUNCTION_KEY` / `_DATABASE`, un `fetch_contratos` de prueba, el fichero de
cada caso pedido y sus fixtures. Si falta algo → salida 2 y ni una llamada
gastada (R23, R24). Un caso cuyo contrato no llega queda NO_EVALUABLE con
motivo, nunca valorado contra contrato vacío (R25).

## 6. El coste

- `--casos` acota el ciclo entero (R28): hoy solo filtra `inputs`, `IA1` e
  `IA2`, y el resto se colaba entero.
- `evals/salidas/<caso_id>.json` (fuera de git, R32) guarda por fase la salida
  cruda más su **huella**: sha256 del albarán, proveedor, modelo y sha256 del
  `prompts.yaml` del servicio. `--reutilizar` reaprovecha las fases con huella
  idéntica; si difiere, se reejecuta y el informe dice qué cambió (R29, R30).
- `--desde IA3` reejecuta de ahí en adelante con las anteriores reutilizadas
  (R31): iterar sobre el valorador deja de costar una pasada de extracción.
- Las salidas crudas llevan precios de proveedor. No se versionan, no pasan por
  el barrido y **no entran nunca en `evals/fixtures/`**: el conversor sigue
  siendo la única puerta.

## 7. El informe

Sobre el de hoy, sin quitar nada: se conservan las secciones de no observables y
de sin clasificar (R36) y se añaden

- por fase, el cuadro con **propios / arrastrados / indeterminados / omitidos**
  contados por separado (R34);
- **«Dónde nace cada fallo»**: los fallos agrupados por fase de ORIGEN (R35);
- **«Entrada que ahora produce el sistema»**: la tabla de §4 (R16);
- los casos separados por expectativa —no regresión frente a defecto conocido—
  y los **rojos que nacen esperados** (familias fuera de catálogo por F-046,
  criterios de residuos sin implementar), leídos de `mapa_casos.json` (R33).

## 8. Límite de servicio

F-047 vive entero en `evals/` y no toca `services/`. El adaptador de sv3 importa
código de sv3 en su subproceso, igual que los de sv2, sv5 y sv6 ya hacen con los
suyos: es el patrón vigente del banco, no una dependencia nueva. La consulta a
Sigrid va por sigrid-api y solo en lectura.

## 9. Riesgos y alternativas descartadas

- **El ciclo por colas** (Azurite + Postgres + los 6 servicios): descartado en
  §1. Si el humano lo quiere, es ficha propia y otro diseño.
- **Atribuir por «la fase anterior falló»**: descartado. Marca como arrastrado
  todo lo que venga después de un fallo cualquiera y esconde defectos reales de
  sv5 detrás de un error de sv2. De ahí el mapa de dependencias.
- **No tener `INDETERMINADO`**: descartado por petición explícita del humano.
  Cuando el emparejado de líneas se rompe, atribuir es adivinar.
- **Sintetizar las líneas de contrato del Excel** (vía A de F-045): sin objeto,
  y además regalaba la respuesta a IA3.
- **Riesgo de fidelidad del paso de contrato**: se reutiliza el núcleo de
  decisión de sv3 (normalizador de obra, selector de contrato), no su
  persistencia. Si sv3 cambia ese núcleo y el banco no se entera, el eval mide
  otro sistema: lo ata un test que importa los símbolos reales de sv3.
- **Riesgo de coste**: la primera pasada de ciclo se lanza acotada (T16) antes
  de la de 59 casos (T17). Las dos son verificación MANUAL del humano.
