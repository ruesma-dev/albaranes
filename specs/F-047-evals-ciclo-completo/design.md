<!-- specs/F-047-evals-ciclo-completo/design.md -->
# F-047 · Diseño técnico — el ciclo completo por el pipeline real

## 1. El recorrido, y por qué las persistencias no se saltan

El banco inyecta por la puerta de sv1 y deja que el pipeline LOCAL lo recorra
entero, con sus colas y sus dos persistencias:

```
evals (hace de sv1) ──q-extraccion──▶ sv2 ──q-persistencia──▶ sv3
   blob input/ + workflow_runs          IA1+IA2                persiste raw+merge
                                                               + contratos (sigrid-api)
        ┌──────────────────q-valoracion──────────────────────────┘
        ▼
       sv6 ──HTTP :8002──▶ sv5 (IA3+IA4) ──▶ sv6 aplica reglas y PERSISTE
```

Los dos defectos que justifican la ficha son **de persistencia**: el
`contexto_linea` perdido en el reproceso —que dejaba la red de sintéticas sin
`codigo_ler`— y la rama de duplicado que no llamaba a `save()`, con las seis
`tipologia*` en NULL. Un ciclo encadenado en memoria no ejecutaría sv3 ni el
replace de sv6 y no vería ninguno: **medir lo persistido es parte de lo medido**.

## 2. El hallazgo que condiciona el diseño: `workflow_runs` no avanza

`ruesma_comun.workflows` ofrece `transicionar`, pero **ningún worker la llama**:
solo la mueven los tests de humo del paquete, así que la fila se queda en
`email_received` todo el recorrido y la terminación NO puede decidirse por el
estado (R4). Se decide por el **dato persistido**, en cinco hitos:

| Hito | Evidencia observable (solo `SELECT`) |
|---|---|
| H1 · extracción persistida | filas en `albaran_documents` / `albaran_lines` del `document_id` |
| H2 · merge escrito | fila en `albaran_documents_merge` con sus seis columnas `tipologia*` y `albaran_lines_merge.contexto_linea_json` |
| H3 · contrato resuelto | filas en `albaran_contratos_merge` + `albaran_contrato_lines_merge`; `selected_contrato_codigo` no nulo |
| H4 · valoración persistida | fila en `albaran_valuations` (trae `raw_ia_envelope_json`) |
| H5 · líneas valoradas | filas en `albaran_line_valuations` + `contrato_lines_derived` |

H4/H5 son el fin del caso; las lecturas van por sesión propia y solo `SELECT` (R3).

## 3. La espera: por avance, nunca por reloj

`evals/espera.py` sondea los hitos con retroceso exponencial y **cuenta el plazo
desde el último avance**, no desde el arranque (R4): un caso que acaba de pasar H2
arranca el de H3 de cero, así que un albarán lento no consume el presupuesto del
siguiente. **Avanza a H5** y el caso se evalúa; **aparece en una `-poison`** (se vigilan las
tres del recorrido) y falla en el acto, sin agotar el plazo; **agota el plazo de un
hito** y queda NO_EVALUABLE con el hito y lo último visto —nunca ROJO, que no
sabemos si el sistema falló, ni VERDE—.

**El caso especial de H3.** Si sv3 encuentra más de un contrato no auto-selecciona:
deja `selected_contrato_codigo` nulo esperando a sv4 y el caso no llegaría a H4. El
banco lo detecta (filas en `albaran_contratos_merge` sin selección), **hace el gesto
del revisor** —fija el de `INPUTS.CASOS.contrato_codigo` y publica
`MensajeValoracion`— y marca el caso «selección no medida» (R5). Cuando sv3 sí
elige solo, el código se compara y ese fallo es `PROPIO` del contrato.

## 4. Entrada, aislamiento y reproceso

`evals/inyeccion.py` reproduce `IntakeColaClient.submit_email_received` llamando a
`RepositorioWorkflows`, `AlmacenBlobs` y `PublicadorColas` (R2): fila de
`workflow_runs`, subida a `input/{document_id}.pdf` y `MensajeExtraccion`. No se
copia lógica: se llaman las mismas piezas.

- **Identidad**: `pasada_id` con fecha y contador; por caso, `document_id` UUID y
  `correlation_key = eval/{pasada_id}/{caso_id}`, UNIQUE (R16).
- **El dedup por `source_sha256` sí choca**, y es el interruptor del reproceso: la
  unicidad es un índice parcial `WHERE is_active`, justo para que la baja lógica
  permita re-ingerir. Por eso una pasada normal empieza dando de **baja lógica**
  los documentos de pasadas anteriores del banco —la vía de sv4, nunca un `DELETE`
  (R17)—, reconocibles por el prefijo `eval/` de su `source_document_id`.
- **`--reproceso`** hace lo contrario: reinyecta sin dar de baja, para ejercitar
  duplicado y re-fetch, y comprueba lo que esos defectos rompían —que
  `contexto_linea_json` sigue y las seis `tipologia*` no se anulan (R18)—.
- **Al terminar no se borra nada**: la base queda consultable en :8004 y limpiarla
  es `--limpiar <pasada_id>`, acción aparte (R17).

## 5. Ficheros

### A crear

- `evals/ciclo.py` — la pasada: preparar, inyectar, esperar, leer y comparar, con
  concurrencia acotada.
- `evals/inyeccion.py` — la puerta de entrada (§4) y el gesto de revisor de §3.
- `evals/espera.py` — hitos, sondeo, plazos y vigilancia de `-poison` (§3).
- `evals/lectura_bbdd.py` — los `SELECT` de cada hito y la proyección al
  vocabulario de los libros (reutiliza las `proyectar_*` que ya existen).
- `evals/atribucion.py` + `evals/atribucion.json` — la atribución (§6).
- `evals/preflight.py` (§7), `evals/salidas.py` (§8), `evals/ficha.py` (§9),
  `evals/revision_manual.py` + `.json` (§10), y `tests/test_f047_*.py`.

### A modificar

- `evals/modelos.py` — `Discrepancia` gana `atribucion`, `fase_origen` y `causa`;
  fase ROJA solo por propios, pasada NO_EVALUABLE con indeterminados (R11).
- `evals/runner.py` — `corrida_ciclo()`; `corrida_completa()` pasa a
  `corrida_por_fases()` sin cambiar conducta; `--por-fases`, `--reutilizar`,
  `--desde`, `--reproceso`, `--limpiar`, `--fichas`; `--casos` filtra todo.
- `evals/informe.py` — `MODO_CICLO`, eje de atribución, cuadro por fase, «dónde
  nace cada fallo», «costuras que NO vigila», estado de la revisión manual y la
  PODA de valores (§9).
- `evals/mapa_casos.json` y `evals/revision/{reparto,escritura,informe}.py` — el
  mapa gana `clasificacion`, `familia_en_catalogo` y `criterios_residuos`, que la
  ficha y el informe del ciclo necesitan para agrupar por los ejes de hoy.
- `.gitignore` (`evals/salidas/`), `evals/README.md` e `infra/docs/levantar-pipeline-local.md`.

### Que NO se tocan

`evals/conversor.py` (única puerta a los fixtures y único sitio del barrido de
sensibles), `evals/comparador.py`, `evals/criticidad.py`, los seis libros, los 264
fixtures, `infra/local/arrancar_local.ps1` y **ningún fichero bajo `services/`**.

## 6. La atribución del fallo

**El mapa** (`evals/atribucion.json`) declara, por campo de aguas abajo, de qué
campos de aguas arriba depende **en la misma línea del mismo caso**:

```json
{"IA3.lineas_valoradas.importe_calculado":
   ["IA1.lineas.cantidad", "IA3.lineas_valoradas.precio_unitario_final"]}
```

Se valida contra las tablas `OBSERVABLES`: un campo que ninguna proyección
produce ABORTA la carga (R12). Lo no declarado es `PROPIO`.

**La regla** (`evals/atribucion.py`), en este orden:

1. **Línea ausente en IA1** → lo posterior de esa línea es `ARRASTRADO` a IA1 (R10).
2. **Identidad dudosa** → si la línea existe pero su `descripcion_esperada`
   discrepa, con fallo o con aviso, el emparejado por `num_linea` ya no es fiable
   y lo posterior de esa línea es `INDETERMINADO` (R10): atribuir mal sería peor.
3. **Dependencia declarada que falló** → `ARRASTRADO` a esa fase, con el campo
   como causa; si fallaron varias, gana la fase MÁS TEMPRANA.
4. **Todo lo demás** → `PROPIO`. En cabecera la ligadura es por caso y la regla 2
   no aplica.

Efecto: `PROPIO` con severidad `fallo` pone ROJA su fase; `ARRASTRADO` no tumba a
nadie y suma en la fase de ORIGEN —un error de IA1 deja de contarse cuatro veces—;
`INDETERMINADO` no tumba a nadie pero impide el VERDE de la pasada (R11).

**IA4 es best-effort en sv6**: si ninguna línea la necesitaba, o falló y se ignoró,
queda OMITIDO en ese caso (R15). Sus líneas se reconocen en `raw_ia_envelope_json`
por `match_method='semantic'` y el sufijo `| IA4:` de `razon_corta`, con un test
que ata ese reconocimiento al código de sv6.

## 7. Entorno y preflight

El ciclo corre **solo en local**, con `infra/local/arrancar_local.ps1 -SinSv1`
(sv1 sobra: el banco hace su papel), como describe
`infra/docs/levantar-pipeline-local.md`. `evals/preflight.py` corre ANTES del
primer caso (R21) y nombra lo que falte:

- Azurite (10001) y Postgres (5432) escuchando y las colas creadas; sv2, sv3 y sv6
  consumiendo y sv5 en :8002; claves LLM y `SIGRID_API_*`; el fichero de albarán y
  los fixtures de cada caso pedido.
- **Guardarraíl**: si la cadena de colas, blobs o BBDD no son las locales, se
  NIEGA a arrancar (R7), con el criterio que `arrancar_local.ps1` ya aplica a sv4.

sigrid-api la consulta sv3, no el banco: sigue siendo solo lectura y con sus topes
(R22); el preflight solo comprueba que las credenciales están.

## 8. Coste, reaprovechamiento y reentrada

- `--casos` acota el ciclo entero (R23): hoy solo filtraba `inputs`, `IA1` e `IA2`.
  `--reutilizar <pasada_id>` no reinyecta los casos que ya llegaron a H5: los lee
  de la base (R24), así que iterar sobre el informe deja de costar LLM.
- `--desde` reentra por **los puntos que el sistema ya ofrece**, los de sv4 (R24):
  `persistencia` republica `MensajePersistencia` con `force=True` (re-fetch) y
  `valoracion` republica `MensajeValoracion`. Otra sería capacidad nueva del
  sistema, no del banco.
- `evals/salidas/<pasada_id>/<caso_id>.json` guarda lo leído para rehacer informe
  y fichas sin base (R25). Lleva precios: fuera de git y nunca en `fixtures/`.

## 9. La ficha por caso: contrastar contra el papel

En F-045 el **37 % de los fallos eran artefactos del banco** y solo salieron
cuando el humano miró casos concretos; con cuatro fases y dos persistencias el
riesgo crece. Cada caso deja una **ficha**:

- **Cabecera con el papel** (R28): `caso_id`, código, `nombre_original`, formato,
  familia y pestaña de `evals/mapa_casos.json`, y la ruta local del original.
- **Tabla por fase con la COSTURA** (R27): `ENTRÓ | SALIÓ | ESPERADO |
  ATRIBUCIÓN`. Lo que entró a IA3 es el contexto que sv3 dejó en la base: se ve si
  valoró mal con lo que recibió o si ya recibió basura.
- **Volumen y caso suelto** (R29, R30): por defecto solo ficha de los no limpios
  (`--fichas todas` para el resto), un fichero por caso; `python -m evals.ficha
  --caso HOR-003` la rehace desde el volcado de §8, sin base ni LLM.

**Dónde vive.** Lleva precios, así que va a
`evals/salidas/<pasada_id>/fichas/<caso_id>.md`, fuera de git (R31), y el informe
agregado deja de imprimir valores y apunta a ella.

> **Hallazgo, y es una fuga real**: `evals/informe.py` imprime hoy `esperado …,
> obtenido …` campo a campo, y `progress/evals_F-045.md` **está versionado con
> importes de proveedor dentro**. R31 corta la fuga hacia adelante; lo ya
> commiteado no lo borra —git no suelta lo que entra— y lo decide el humano.

## 10. Que la revisión manual no se pierda

Una revisión que no se captura caduca. **No hace falta un Excel nuevo** —el de
F-045 es ground truth, esto es juicio sobre UNA pasada—, sino
`evals/revision_manual.json` (R32), versionado, con entrada por caso/fase/campo:

```json
{"HOR-003/IA1/cabeceras.proveedor_nombre": {"veredicto": "artefacto_banco",
   "nota": "el libro trae el nombre comercial", "fecha": "2026-09-18",
   "arreglo": "normalizar razón social en el conversor",
   "pasada": "2026-09-18-01", "huella_esperado": "9f2c…"}}
```

- **Lleva juicio, no datos** (R32): campo y conclusión, nunca importes; por eso SÍ
  puede versionarse. **No cambia ningún veredicto** (R34): declara y agrupa, porque
  silenciar rojos desde un fichero sería la vía fácil para blanquear el banco.
- **`artefacto_banco` obliga a nombrar el arreglo** (R33) y el informe lo agrupa
  aparte, con los dos recuentos: deja de ser ruido y pasa a ser deuda con dueño.
- **Caducidad** (R35): `huella_esperado` es el sha256 del valor esperado —del
  valor, no el valor—; si el libro cambia deja de casar y la anotación vuelve a
  pendiente, CADUCADA. **Cobertura** (R36): el informe lista revisados y sin
  revisar. La escribe `python -m evals.revision_manual`, que rellena fecha, pasada
  y huella solo.

## 11. Lo que este ciclo NO vigila (y hay que decirlo en el informe)

- **sv1 y el buzón M365**: polling de Graph, troceado por páginas y dedup por
  correo; el banco entra por detrás.
- **sv4**: salvo el gesto de contrato, que el banco simula; ni edición del revisor,
  ni aprobación, ni `q-feedback`.
- **SharePoint real**: la subida del PDF y la descarga del de contrato no se
  ejercitan en local.
- **Azure de verdad**: Azurite no es Azure Queue ni se ejercita la identidad
  gestionada; un fallo que solo aparezca desplegado aquí no sale.
- **Sigrid histórico**: el contrato es el de HOY y para albaranes de 2024 puede no
  ser el vigente (medido en `progress/impl_F-045_contrato_lineas.md`).

## 12. Riesgos y alternativas descartadas

- **Encadenar en memoria los hand-off** (1.ª versión de esta spec): RECHAZADO por
  el humano. No ejecuta ninguna de las dos persistencias, donde vivían dos de los
  defectos que motivan la ficha.
- **Terminar por `workflow_runs.current_state`**: imposible hoy (§2); que los
  workers transicionen es arreglo del sistema, no del banco, y va en ficha aparte.
- **`sleep` fijo**: descartado en R4. **Borrar filas entre pasadas**: rompe claves
  ajenas y no es lo que hace el sistema; la baja lógica sí, y el índice único
  parcial está pensado para eso.
- **Un Excel nuevo para la revisión**: descartado (§10). El de F-045 es ground
  truth; esto es juicio sobre UNA pasada, y una anotación nunca pone verde un rojo.
- **Riesgo de tiempo**: seis servicios por caso, con dos llamadas LLM en sv2 y una
  o dos en sv5; se mitiga con concurrencia acotada, `--casos` y `--reutilizar`.
- **Riesgo de contaminación**: si el humano tiene datos propios en su Postgres, la
  baja lógica solo toca el prefijo `eval/`, y un test ata que nunca corre sin él.
