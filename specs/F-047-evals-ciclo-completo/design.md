<!-- specs/F-047-evals-ciclo-completo/design.md -->
# F-047 · Diseño técnico — el ciclo completo por el pipeline real

## 1. El recorrido, y por qué las persistencias no se saltan

El banco inyecta el albarán por la misma puerta que sv1 y deja que el pipeline
LOCAL lo recorra entero, con sus colas y sus dos persistencias:

```
evals (hace de sv1) ──q-extraccion──▶ sv2 ──q-persistencia──▶ sv3
   blob input/ + workflow_runs          IA1+IA2                persiste raw+merge
                                                               + contratos (sigrid-api)
        ┌──────────────────q-valoracion──────────────────────────┘
        ▼
       sv6 ──HTTP :8002──▶ sv5 (IA3+IA4) ──▶ sv6 aplica reglas y PERSISTE
```

Los dos defectos que justifican la ficha son **de persistencia**: el
`contexto_linea` que se perdía en el reproceso —dejando la red de sintéticas sin
`codigo_ler`— y la rama de duplicado que no llamaba a `save()`, con las seis
columnas `tipologia*` en NULL. Un ciclo que encadenara los hand-off en memoria
no ejecutaría ni sv3 ni el replace de sv6, así que no vería ninguno de los dos.
Por eso el ciclo pasa por Postgres, y por eso las salidas de cada fase se leen de
la base: **medir lo persistido es parte de lo que se mide**.

## 2. El hallazgo que condiciona el diseño: `workflow_runs` no avanza

`ruesma_comun.workflows` ofrece `transicionar`, pero **ningún worker la llama**:
el único código que mueve `current_state` son los tests de humo del paquete. En
el pipeline real la fila la crea sv1 en `email_received` y ahí se queda. El
criterio de terminación NO puede ser el estado del workflow (R4).

El criterio es el **dato persistido**, que sí avanza y es lo que de verdad
importa. Cinco hitos observables, cada uno con su evidencia:

| Hito | Evidencia observable (solo `SELECT`) |
|---|---|
| H1 · extracción persistida | filas en `albaran_documents` / `albaran_lines` del `document_id` |
| H2 · merge escrito | fila en `albaran_documents_merge` con sus seis columnas `tipologia*` y `albaran_lines_merge.contexto_linea_json` |
| H3 · contrato resuelto | filas en `albaran_contratos_merge` + `albaran_contrato_lines_merge`; `selected_contrato_codigo` no nulo |
| H4 · valoración persistida | fila en `albaran_valuations` (trae `raw_ia_envelope_json`) |
| H5 · líneas valoradas | filas en `albaran_line_valuations` + `contrato_lines_derived` |

H4/H5 juntos son el fin del caso. Las lecturas van por una sesión propia en
`autocommit` y solo `SELECT`: el banco no escribe en las tablas que mide (R3).

## 3. La espera: por avance, nunca por reloj

`evals/espera.py` sondea los hitos con retroceso exponencial y **cuenta el plazo
desde el último avance**, no desde el arranque del caso (R5). Un caso que acaba
de pasar H2 arranca el plazo de H3 de cero, así que un albarán lento no consume
el presupuesto del siguiente y un `sleep` fijo deja de hacer falta.

Tres salidas, y ninguna es un verde silencioso:

- **Avanza a H5** → el caso se evalúa.
- **Aparece en una cola `-poison`** → el caso se da por fallado en el acto, con
  el mensaje y la cola, sin agotar el plazo (R6). Se vigilan las tres colas
  `-poison` del recorrido.
- **Se agota el plazo de un hito** → NO_EVALUABLE con el hito donde se quedó y
  lo último visto en la base. Nunca ROJO —no sabemos si el sistema falló— ni
  VERDE.

**El caso especial de H3.** Si sv3 encuentra más de un contrato no auto-
selecciona: deja `selected_contrato_codigo` nulo esperando a sv4, y sin
`q-valoracion` el caso no llegaría nunca a H4. El banco lo detecta (hay filas en
`albaran_contratos_merge` y no hay selección), **hace el gesto del revisor** —
fija el contrato de `INPUTS.CASOS.contrato_codigo` y publica
`MensajeValoracion`— y marca ese caso como «selección no medida» (R7). Cuando
sv3 sí auto-selecciona, el código elegido se compara con el declarado y ese
fallo es `PROPIO` de la fase de contrato.

## 4. Entrada, aislamiento y reproceso

`evals/inyeccion.py` reproduce `IntakeColaClient.submit_email_received`
reutilizando `RepositorioWorkflows`, `AlmacenBlobs` y `PublicadorColas` de
`ruesma_comun` (R2): crea la fila de `workflow_runs`, sube el fichero a
`input/{document_id}.pdf` y publica `MensajeExtraccion`. No se copia lógica: se
llaman las mismas piezas.

- **Identidad de pasada**: `pasada_id` con fecha y contador. Por caso,
  `document_id` UUID nuevo y `correlation_key = eval/{pasada_id}/{caso_id}`, que
  es UNIQUE: dos pasadas nunca chocan y dos casos de la misma pasada tampoco
  (R20).
- **El dedup por `source_sha256` sí choca**, y es el interruptor del reproceso.
  La unicidad es un índice parcial `WHERE is_active`, justo para que la baja
  lógica permita re-ingerir. Por eso una pasada normal empieza dando de **baja
  lógica** los documentos de pasadas anteriores del banco —la misma vía que usa
  sv4, nunca un `DELETE` a mano (R21)—, reconocibles por el prefijo
  `eval/{pasada_id}/` de su `source_document_id`.
- **`--reproceso`** hace lo contrario a propósito: reinyecta sin dar de baja el
  anterior, para ejercitar la rama de duplicado y el re-fetch, y comprueba lo
  que esos defectos rompían: que `contexto_linea_json` sigue ahí y que las seis
  `tipologia*` no quedan en nulo (R22). Es una comprobación propia, con su
  expectativa propia, no la pasada normal.
- **Al terminar no se borra nada**: la base queda consultable en el portal
  (:8004) y la limpieza es `--limpiar <pasada_id>`, acción aparte (R23).

## 5. Ficheros

### A crear

- `evals/ciclo.py` — orquesta la pasada: preparación, inyección, espera, lectura
  y comparación, caso a caso y con concurrencia acotada.
- `evals/inyeccion.py` — la puerta de entrada (§4) y el gesto de revisor de §3.
- `evals/espera.py` — hitos, sondeo, plazos y vigilancia de `-poison` (§3).
- `evals/lectura_bbdd.py` — los `SELECT` de cada hito y la proyección de lo leído
  al vocabulario de los libros (reutiliza `proyectar_ia1`, `proyectar_ia2`,
  `proyectar_ia3`, `proyectar_final`, `proyectar_ia4`, que ya existen).
- `evals/atribucion.py` + `evals/atribucion.json` — la atribución (§6).
- `evals/preflight.py` — comprobación de entorno (§7).
- `evals/salidas.py` — volcado de lo leído, fuera de git (§8).
- `tests/test_f047_*.py` — uno por bloque de requisitos.

### A modificar

- `evals/modelos.py` — `Discrepancia` gana `atribucion`, `fase_origen` y
  `causa`; `ResultadoFase.veredicto()` mira SOLO los propios;
  `ResultadoPasada.veredicto()` degrada a NO_EVALUABLE con indeterminados (R14).
- `evals/runner.py` — `corrida_ciclo()`; `corrida_completa()` se renombra a
  `corrida_por_fases()` sin cambiar conducta; `--por-fases`, `--reutilizar`,
  `--desde`, `--reproceso`, `--limpiar`; `--casos` filtra TODAS las fases.
- `evals/informe.py` — `MODO_CICLO`, eje de atribución, cuadro por fase, «dónde
  nace cada fallo» y «costuras que esta corrida NO vigila».
- `evals/mapa_casos.json` y `evals/revision/{reparto,escritura,informe}.py` — el
  mapa gana `clasificacion`, `familia_en_catalogo` y `criterios_residuos` para
  que el informe del ciclo agrupe por los mismos ejes que el de importación.
- `.gitignore` — `evals/salidas/`.
- `evals/README.md`, `infra/docs/levantar-pipeline-local.md` — cómo se lanza.

### Que NO se tocan

`evals/conversor.py` (única puerta a los fixtures y único sitio del barrido de
sensibles), `evals/comparador.py`, `evals/criticidad.py`, los seis libros, los
264 fixtures, `infra/local/arrancar_local.ps1` (se usa tal cual) y **ningún
fichero bajo `services/`**: el banco se adapta al sistema, nunca al revés.

## 6. La atribución del fallo

### El mapa (`evals/atribucion.json`)

Declara, por campo de aguas abajo, de qué campos de aguas arriba depende **en la
misma línea del mismo caso**:

```json
{"IA3.lineas_valoradas.importe_calculado":
   ["IA1.lineas.cantidad", "IA3.lineas_valoradas.precio_unitario_final"],
 "E2E.lineas.precio_source": ["IA3.lineas_valoradas.precio_source"],
 "IA3.lineas_valoradas.codigo_producto_contrato":
   ["IA1.lineas.descripcion_esperada", "IA2.contexto.valor_esperado",
    "CONTRATO.contrato_elegido"]}
```

Se valida contra las tablas `OBSERVABLES` de cada proyección: un campo que
ninguna produce ABORTA la carga (R15). Lo no declarado es `PROPIO`.

### La regla (`evals/atribucion.py`), en este orden

1. **Línea ausente en IA1** → toda discrepancia de esa línea aguas abajo es
   `ARRASTRADO` a IA1, causa `linea ausente en IA1` (R12).
2. **Identidad dudosa** → si la línea existe pero su `descripcion_esperada`
   discrepa, con fallo o con aviso, el emparejado por `num_linea` ya no es
   fiable y todo lo posterior de esa línea es `INDETERMINADO` (R13). Es el caso
   en que atribuir mal sería peor que no atribuir.
3. **Dependencia declarada que falló** → `ARRASTRADO` a esa fase, con el campo
   como causa; si fallaron varias, gana la fase MÁS TEMPRANA.
4. **Todo lo demás** → `PROPIO`.

Para campos de cabecera la ligadura es por caso y la regla 2 no aplica.

Efecto en el veredicto: `PROPIO` con severidad `fallo` pone ROJA su fase;
`ARRASTRADO` no tumba a nadie y suma en el recuento de la fase de ORIGEN —un
error de IA1 deja de contarse cuatro veces—; `INDETERMINADO` no tumba a nadie
pero impide el VERDE de la pasada (R14).

**IA4 es best-effort en sv6**: si ninguna línea la necesitaba, o falló y se
ignoró, IA4 queda OMITIDO en ese caso (R19). Sus líneas se reconocen en
`raw_ia_envelope_json` por `match_method='semantic'` y el sufijo `| IA4:` de
`razon_corta`, y hay un test que ata ese reconocimiento al código de sv6.

## 7. Entorno y preflight

El ciclo corre **solo en local**, con `infra/local/arrancar_local.ps1 -SinSv1`
(sv1 sobra: el banco hace su papel) sobre Azurite y Postgres, tal como describe
`infra/docs/levantar-pipeline-local.md`. `evals/preflight.py` corre ANTES de
inyectar el primer caso (R27, R28) y nombra lo que falte:

- Azurite (10001) y Postgres (5432) escuchando, y las colas creadas.
- sv2, sv3 y sv6 consumiendo, y sv5 respondiendo en :8002.
- Claves LLM de los proveedores y credenciales `SIGRID_API_*`.
- El fichero de albarán y los fixtures de cada caso pedido.
- **Guardarraíl**: si la cadena de colas, la de blobs o la de BBDD no son las
  locales, se NIEGA a arrancar (R9), con el mismo criterio que
  `arrancar_local.ps1` aplica al `.env` de sv4.

sigrid-api la consulta sv3, no el banco: sigue siendo solo lectura y con sus
topes (R29). El preflight solo comprueba que las credenciales están.

## 8. Coste, reaprovechamiento y reentrada

- `--casos` acota el ciclo entero (R30): hoy solo filtraba `inputs`, `IA1` e
  `IA2` y el resto se colaba entero.
- `--reutilizar <pasada_id>` no reinyecta los casos que ya llegaron a H5 en esa
  pasada: los lee de la base (R31). Iterar sobre el informe deja de costar LLM.
- `--desde` reentra por **los puntos que el sistema real ya ofrece**, los mismos
  que usa sv4 (R32): `persistencia` republica `MensajePersistencia` con
  `force=True` (re-fetch de contratos) y `valoracion` republica
  `MensajeValoracion` (revalorar). No hay reentrada inventada: si hiciera falta
  otra, sería una capacidad nueva del sistema, no del banco.
- `evals/salidas/<pasada_id>/<caso_id>.json` guarda lo leído para rehacer el
  informe sin base. Lleva precios de proveedor: fuera de git, sin barrido, y
  **nunca** en `evals/fixtures/` (R33).

## 9. Lo que este ciclo NO vigila (y hay que decirlo en el informe)

- **sv1 y el buzón M365**: el polling de Graph, el troceado del PDF por páginas y
  el dedup por correo. El banco entra por detrás.
- **sv4**: salvo el gesto de seleccionar contrato, que el banco simula. Ni la
  edición del revisor, ni la aprobación, ni `q-feedback`.
- **SharePoint real**: la subida del PDF y la descarga del PDF de contrato no se
  ejercitan en local; lo que dependa de ellos queda sin vigilar.
- **Azure de verdad**: Azurite no es Azure Queue y la identidad gestionada no se
  ejercita. Un fallo que solo aparezca desplegado, aquí no sale.
- **Sigrid histórico**: el contrato que devuelve sigrid-api es el de HOY; para
  albaranes de 2024 puede no ser el que estaba vigente (riesgo ya medido en
  `progress/impl_F-045_contrato_lineas.md`).

## 10. Riesgos y alternativas descartadas

- **Encadenar en memoria los hand-off** (primera versión de esta spec): RECHAZADO
  por el humano el 2026-09-16. No ejecuta ninguna de las dos persistencias, que
  es donde vivían dos de los defectos que motivan la ficha.
- **Terminar por `workflow_runs.current_state`**: imposible hoy (§2). Que los
  workers transicionen es un arreglo del sistema, no del banco: ficha aparte.
- **Esperar con un `sleep` fijo**: descartado en R5; o mide a medias o alarga
  cada pasada sin motivo.
- **Borrar filas entre pasadas**: descartado. Rompe claves ajenas y no es lo que
  hace el sistema; la baja lógica sí, y además el índice único parcial está
  pensado exactamente para eso.
- **Riesgo de tiempo**: cada caso recorre seis servicios con dos llamadas LLM en
  sv2 y una o dos en sv5. Se mitiga con concurrencia acotada, `--casos` y
  `--reutilizar`; la pasada de 59 la decide el humano (T18).
- **Riesgo de contaminación**: si el humano tiene datos propios en su Postgres
  local, la baja lógica de R21 solo toca los del prefijo `eval/`. Un test ata
  que el filtro nunca se aplica sin prefijo.
