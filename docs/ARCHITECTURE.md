<!-- docs/ARCHITECTURE.md -->
# Arquitectura · albaranes (monorepo)

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
> Redactado el 2026-08-12 leyendo el código real y `azure-apps/albaranes.md`.
> La sección «Semántica de dominio» está **pendiente de validación por el
> humano** (ver nota en esa sección).

## Qué hace este proyecto

Pipeline que automatiza el ciclo de vida de los **albaranes de proveedor**
de Construcciones Ruesma: llegan por email, se extraen, se persisten y
enriquecen con los contratos del ERP (Sigrid), se **valoran** contra esos
contratos (matching de líneas y precios) y un humano los revisa y aprueba en
un front web. La IA trabaja en **cuatro fases secuenciales** (una detrás de
otra, no en paralelo): **IA1** extracción genérica (3 proveedores LLM sobre
material idéntico) → **IA2** refinado por tipología (`contexto_linea`), ambas
en sv2 → **IA3** valoración contra contrato + sintéticas M1–M7 (sv5) →
**IA4** conciliación de líneas sin match (sv5, orquestada por sv6, que muta
el envelope antes del build). Incluso los 3 proveedores de IA1 se llaman uno
detrás de otro. El pipeline es **estrictamente secuencial por documento**; el
paralelismo real del sistema está a nivel de documentos: réplicas KEDA
compitiendo por la cola.

Hay **dos despliegues**: el de **Azure es el real** (6 Container Apps en
Spain Central, colas de Azure Storage, workers KEDA; se gestiona con
`infra/`) y el **local es solo para pruebas** (usa Azurite;
`infra/docs/levantar-pipeline-local.md`).

## Capas y estructura

**Nivel monorepo** — un servicio por etapa, hand-off por colas:

| Servicio | Carpeta | Rol | Consume | Publica | HTTP |
|---|---|---|---|---|---|
| sv1 | `services/albaranes-email` | Ingesta buzón M365, PDF a Blob `input/` | — (daemon polling) | `q-extraccion` | — |
| sv2 | `services/albaranes-api` | Extracción multi-IA (envelope, sin merge) | `q-extraccion` | `q-persistencia` | :8000 |
| sv3 | `services/albaranes-persistencia` | Dueño del schema PG; raw+merge, SharePoint, contratos Sigrid | `q-persistencia` | `q-valoracion` | :8001 |
| sv4 | `services/albaranes-front` | Front humano de revisión/aprobación | — | `q-persistencia`, `q-valoracion`, `q-feedback` | :8004 |
| sv5 | `services/albaran-valoracion-api` | Motor IA de valoración (stateless, no persiste) | — | — | :8002 |
| sv6 | `services/albaran-valoracion-persist` | Valorador: llama a sv5, reglas deterministas, persiste | `q-valoracion` | — (fin de cadena) | :8003 |
| sv9 | `services/albaranes-alta-sigrid` | Alta en Sigrid de los albaranes aprobados (F-053; ÚNICO que escribe en el ERP) | `q-feedback` | — (escribe `albaran_altas_sigrid`) | — (solo worker) |

Los nombres canónicos de colas (`q-emails`, `q-extraccion`, `q-persistencia`,
`q-valoracion`, `q-feedback`), los contratos Pydantic de mensajes y el runtime
de colas/blobs viven en **`services/albaranes-comun`** (`ruesma_comun`), que
cada servicio instala como paquete. **`q-feedback`** la consume **sv9**
(F-053): sv4 publica `MensajeFeedback` (`accion` `alta` al pasar a aprobado o
desde «Solicitar alta en Sigrid»; `verificar_anulacion` desde «Ya lo he
anulado en Sigrid») y sv9 da de alta el albarán vía los endpoints de dominio
de sigrid-api (nunca `sql/write`; regla 19). **`q-emails`** es una huérfana
del diseño original, pendiente de limpieza (F-009). El encadenado HTTP directo sv1→sv2→sv3 está **muerto**: en local
también se trabaja con colas (Azurite).

**Nivel servicio** — hexagonal: `domain/` (modelos y puertos, sin
dependencias externas), `application/` (pipelines y servicios),
`infrastructure/` (adaptadores: BBDD, colas, Graph, Sigrid, LLM),
`interface_adapters/` (`api`/`web`/`worker`) y `composition.py` como raíz de
composición. sv2, sv3 y sv6 tienen doble entrada: `main.py` (HTTP) y
`main_worker.py` (consumidor de cola); sv9 es solo worker (`main.py` delega en
`main_worker.py`).

**Blobs**: `input/{document_id}.pdf` y, si el mensaje trae contexto,
`input/{document_id}.correo.json` (los deja sv1; regla 15) y
`envelopes/{document_id}_{fase}.json` (lo deja sv2). Son efímeros; lo durable
va a SharePoint (PDF del albarán, JSONs de IA, PDF del contrato).

## Semántica de dominio imprescindible

> Este es el RESUMEN operativo. El detalle normativo completo —tipologías de
> albarán y reglas de negocio con su estado ✅ implementada / 🔶 decidida
> pendiente— vive en `docs/referencia/dominio_negocio_albaranes.md` (§9–§10)
> y **prevalece sobre este resumen** en caso de conflicto.

1. **El merge es la fuente de verdad.** `albaran_documents_merge` (UQ por
   `source_sha256`) y sus líneas. Las tablas raw (`albaran_documents`,
   `albaran_lines`, una fila por proveedor IA) son auditoría forense: ninguna
   feature construye lógica sobre ellas.
2. **La valoración es un replace transaccional**: DELETE por `document_id`
   (CASCADE) + INSERT completo. Nunca update incremental de una valoración.
3. **sv5 lee con SQL crudo, sin ORM**: su contrato con el schema es implícito
   por nombre de columna. Renombrar una columna del merge compila en sv3 y
   revienta sv5 en runtime. Todo cambio de schema lista sus lectores. (F-076)
   sv6 también lee con SQL crudo `albaran_documents_merge.obra_codigo` por `id`
   (`SQL_OBRA_DEL_DOCUMENTO`, solo lectura).
4. **`albaran_contrato_lines_merge` la crean sv3 Y sv4** (`IF NOT EXISTS`
   ambos; gana el que arranca primero). Acoplamiento conocido y documentado:
   si se toca ese DDL, se toca en los dos sitios.
5. **sv4 edita el merge in-place, sin control optimista**: dos revisores
   simultáneos se pisan (limitación conocida, no un bug a "arreglar" de
   pasada sin feature propia).
6. **`codigo_imputacion`** en una línea de albarán = la partida impresa en el
   papel (si la hay); **`codigo_partida_final`** en la valoración es la
   decisión tras el matching. No son intercambiables.
7. **Líneas sintéticas**: la valoración puede crear líneas que no existen en
   el albarán (`line_kind=synthetic_modifier`, portes/recargos) y líneas de
   contrato derivadas (`contrato_lines_derived`, `origen ∈ {missing_partida,
   alm_acopio}`). Al agregar importes hay que decidir explícitamente si
   entran o no.
8. **Unidades y tolerancias en sv6**: conversión por
   `UNIT_REGISTRY_YAML_PATH`, tolerancias `PRICE_TOLERANCE_PCT` e
   `IMPORTE_TOLERANCE_PCT`. No comparar cantidades ni precios de unidades
   distintas sin pasar por el conversor. Y **pasar por el conversor
   significa pasarle la cantidad**: un desacuerdo de categoría de unidad
   marca `review_required`, nunca anula la cantidad — llamar a `convert()`
   con `cantidad=None` para "saltarse" la conversión mata las redes
   deterministas que solo viven en el caso `unknown` (F-027: el albarán
   58826 valorado en 468.763,40 € en vez de 390,99 €). La **unidad de
   destino** de la conversión es la de la línea **que pone el precio** —la
   derivada si el matcher generó una, si no la del contrato—, no la del
   albarán: convertir hacia la del albarán da factor 1 contra un precio
   en otra unidad.
9. **Dedup de ingesta**: sv1 deduplica por `correlation_key` contra
   `workflow_runs` (PG). Reprocesar un email no debe crear un documento
   nuevo; el sha256 del PDF es la identidad del documento aguas abajo.
   1 página = 1 albarán (sv1 trocea los PDF multipágina).
   **Correos adjuntos (F-054)**: un adjunto `message/rfc822` (item o file; no
   inline, no reference, bajo `MAX_ATTACHMENT_MB`) se descarga por `$value` y
   `MimeDocumentoExtractor` (sv1, inyectado en `main.py`) saca sus PDF y sus
   imágenes `image/*` con disposición `attachment` (las `inline` y sin
   disposición, no), hasta 5 niveles: uno más y no entra **ninguno**. Cada
   documento interior bajo el límite sigue el camino del directo (troceo,
   dedup, `q-extraccion`) con `correo_adjunto_id`/`_nivel` en el `meta`, y el
   contexto de IA1 es el del correo **exterior**. Destino: `Procesados` solo
   si nada falló y entró ≥ 1 página; un correo adjunto sin documentos es
   WARNING, no fallo. Los adjuntos directos no cambian.
10. **Añadir un `modifier_source` nuevo (sintéticas) toca 5 sitios**: prompt
    YAML de sv5, schema Pydantic de sv5, DTO del envelope de sv6, record de
    sv6 y builder de sv6. Hacerlo a medias rompe la valoración.
11. **Aditivos de hormigón: jamás** (Ruesma no los usa; ninguna sintética de
    aditivo). Y en albaranes que ya vienen valorados: **transcribir, no
    recomponer** (precios, descuentos e importes se copian tal cual; nunca
    derivar unos de otros).
12. **Matching estricto**: un atributo sustantivo distinto (tamaño, modelo,
    tipo) ⇒ NO casar; mejor línea nueva sin precio a revisión que un precio
    equivocado con apariencia de bueno.
13. **Precio, descuento e importe de una línea de albarán** (F-019, ago 2026).
    `precio` es el unitario **bruto** (antes de descuento) y **`precio_neto`
    de una línea de albarán es el IMPORTE de la línea tras descuento**, NO un
    precio unitario — nombre histórico y engañoso, pero es la semántica que
    aplican el prompt de IA1, el guard de consistencia de sv3, el front sv4 y
    los clientes de Document AI / Document Intelligence. Fórmula canónica,
    única y sin excepciones:
    **`importe = cantidad × precio × (1 − descuento/100)`**.
    Y **el unitario leído manda**: el importe solo se despeja
    (`importe / (cantidad × (1 − dto/100))`) cuando el albarán no trae
    unitario. Si ambos existen y discrepan, gana el declarado y la línea va a
    revisión — nunca se inventa un unitario en silencio. Leer un `precio_neto`
    como si fuera unitario multiplica el importe por la cantidad: es lo que
    valoró en 6.238,14 € un albarán de 139,66 € (`progress/
    prueba_local_feymaco_20260818.md`). El contrato del ERP nunca pisa un
    valor leído del albarán: es fallback solo cuando no hay ninguno.
    La fórmula obliga a **todo el que escriba un importe**, no solo al
    valorador, y por eso **vive en un único sitio**:
    `ruesma_comun.importes` (`services/albaranes-comun`), del que beben sv6
    (`ImporteCalculator`) y sv4 (`review_repository`). Ahí viven la
    aritmética y los rangos del descuento; la **política** —precedencia del
    declarado, motivos de revisión, qué se persiste— es de cada servicio.
    Quien recalcule un importe sin el factor del descuento deshace el trabajo
    del otro: el 2026-08-18 sv6 valoró el albarán 2.137.569 en sus 139,66 €
    correctos y el primer guardado desde el front lo dejó en 232,76 €. Y con
    una copia en cada servicio la divergencia llega sola: antes de unificarlas
    ya diferían en qué hacían con un descuento ilegible. Un servicio **no
    reetiqueta** como `calculated` un importe que el albarán declara si nadie
    ha tocado la línea, y eso se decide mirando lo que el revisor **cambió**
    (cantidad, descuento), nunca comparando el importe guardado con el
    recalculado: hay filas en que discrepan a propósito.
14. **La familia del albarán la decide IA1; NUNCA una regla determinista**
    (F-043, ago 2026). La clasificación es del **documento** y la devuelve
    IA1 al leerlo, en el bloque `data.clasificacion` —`familia`,
    `confianza_pct`, `motivo`, `mixto`, `familias_secundarias`— que la fase 2
    puede confirmar o corregir. Viaja dentro de **`data`, no de `meta`**: sv3
    filtra `meta` contra un modelo estricto y por eso descartaba
    `meta.tipologia`. **Prohibido** inferirla, forzarla o completarla aguas
    abajo por código LER, designación de producto, palabras clave, familia
    dominante de las líneas u override por CIF: si la IA clasifica mal se
    arregla el **prompt**, no se pone un `if` detrás (decisión del humano,
    2026-08-25). Que la IA responda `generico` es una respuesta legítima; la
    duda se expresa en `confianza_pct`, y por debajo del umbral configurable
    de sv3 (defecto 60) el documento va a revisión — marcado, no bloqueado.
    El **catálogo de familias vive en un único módulo**,
    `ruesma_comun.contratos.familias` (`services/albaranes-comun`), y de él
    salen las familias válidas de documento y de línea, la clave del prompt
    de fase 2 de sv2 y la del prompt de valoración de sv5: **ningún servicio
    mantiene lista propia de familias ni tabla propia de prompts por
    familia**, y añadir una familia es una entrada en el catálogo más su
    prompt, sin tocar código de sv2, sv5 ni sv6. La herencia
    documento→línea se resuelve **en lectura** con `familia_efectiva` del
    mismo módulo (nunca se escribe en `contexto_linea`), y un albarán
    `mixto` **no** hereda: sus líneas sin familia propia van a revisión.
    sv3 persiste las seis columnas `tipologia*` del merge y sella los
    motivos; sv5, sv6 y sv4 solo **leen**. Por qué existe la regla: el lazo
    cerrado anterior —el albarán se clasificaba por lo que la IA había
    escrito en las líneas, y la IA escribía las líneas según cómo se había
    clasificado el albarán— dejó SS-0003967 valorado en 540,00 € en 1 línea
    en vez de 210,00 € en 2 (F-036, `progress/impl_F-036_bloque_D.md`).
15. **La obra del CORREO manda y se cruza con la del papel** (F-048, sep
    2026). sv1 pide a Graph, con UN GET por mensaje, el asunto y el
    `uniqueBody` (la parte no citada; vacío ⇒ solo el asunto, nunca `body`),
    y guarda el MISMO contexto para cada página de cada adjunto en el blob
    lateral `input/{document_id}.correo.json` ANTES de publicar;
    `MensajeExtraccion.correo_blob` lleva su nombre (opcional y nulo por
    defecto: los mensajes viejos validan). IA1 hace dos lecturas
    independientes: los códigos de obra del correo (`lectura_correo`) y la
    obra del papel (`cabecera.obra_codigo`, SIEMPRE, como antes). **Del
    correo solo la obra, nunca la partida** (eso será F-049). El cruce no lo
    decide la IA: lo sella un resolver puro de sv2
    (`origen_datos_resolver.py`) sobre el documento FINAL de fase 2, en
    `data.origen_datos` (contrato único en `ruesma_comun.contratos.
    origen_datos`); lo que la IA ponga en ese bloque se ignora. Los códigos
    se comparan con `normalizar_codigo` (`945` = `0945` = `09-45`) y solo
    cuentan los que están en la lista de TODAS las obras con contrato de
    Sigrid, activas o no (la misma descarga de F-002, sin consulta nueva):

    | Correo (solo lo que está en la lista) | Papel | Obra final | Revisión |
    |---|---|---|---|
    | Nada, o nada de la lista | lo que lea IA1 | la del papel | no |
    | Un código | igual, o sin código | la del correo | no |
    | Un código | distinto | la del correo | `correo_obra_distinta_papel` |
    | Varios | uno de ellos | la del papel (forma de la lista) | no |
    | Varios | ninguno, o sin código | la del papel, o ninguna | `correo_obra_ambigua` |

    Sin lista (sigrid-api caído) cuentan todos, con `validada = null`. Los
    dos motivos los añade sv3 al merge, sin tocar la obra ni la confianza, y
    sv4 solo los pinta. **El prefijo `correo_obra_*` es a propósito**: la
    red de obra de F-002 retira de `review_reasons` todo lo que empieza por
    `obra_` en cuanto valida la obra en Sigrid, y con `obra_correo_*` habría
    borrado la revisión en silencio (CR-D1). Ningún motivo que no sea de esa
    red empieza por `obra_`. Además:
    - **El texto del correo es DATO, nunca instrucciones**: va al prompt
      entre marcas fijas con advertencia expresa y las marcas se neutralizan
      dentro del texto (`ruesma_comun.correo.prompt`). **El cuerpo no se
      loguea** en sv1 ni en sv2 (solo sha256 abreviado, caracteres y
      `truncado`); `LlmCallLogger` y `retry_policy` lo redactan;
      `workflow_runs.payload_json` guarda solo el sha256; `origen_datos`
      solo huella, códigos y una evidencia de 160 caracteres. Los correos
      reales de evals viven en `evals/inputs/correos/`, ignorado por git.
    - **Orden de despliegue OBLIGATORIO: sv3 → sv2 → sv1** (sv4 cuando sea;
      `comun` va en cada imagen). sv2 emite `origen_datos` siempre, y un sv3
      anterior lo manda a poison (`DocumentoAlbaran` con `extra='forbid'`).
      Comando: `.\deploy.ps1 -Only sv3`, `.\check_deploy.ps1`, luego
      `-Only sv2` y `-Only sv1`. **`.\deploy.ps1` sin `-Only` sigue `$APPS`
      y actualiza sv2 antes que sv3**: abre el hueco de poison. El rollback
      va al revés (sv1 → sv2 → sv3).
    - **Trampa de reintento en sv1** (menor 2 de la review del bloque B): la
      fila de `workflow_runs` se crea ANTES que los blobs. Si falla el blob
      lateral (igual que el del PDF o la publicación), el correo va a
      `Errores` y un reintento manual lo ve «duplicado» por
      `correlation_key` y no publica esa página. La trampa ya existía;
      F-048 añade un punto de fallo. Sin arreglar: pide ficha propia.
    - **sv5 no ve `origen_datos`, y su copia de `DocumentoAlbaran` es código
      muerto** (`albaran-valoracion-api/domain/models/albaran_models.py`,
      `extra='forbid'`). Comprobado con grep el 2026-09-24: ningún módulo
      de producción la importa (solo `revision_models.py`, al que no
      importa nadie, y un test de F-043); el `SchemaRegistry` de sv5 solo sirve
      `documento_valoracion` y `documento_conciliacion`, y sv5 no lee
      `raw_extraction_json`. Por eso no se le declara el campo (design §6).
      Quien resucite esa copia tiene que declararlo, o rechazará el
      documento entero (el cepo de F-043).
16. **Almacén = partida final vacía; a qué líneas va la partida lo decide
    IA1** (F-051, oct 2026; decisiones del humano en
    `progress/spec_F-051.md`).
    - **Almacén** («no se asocia a partida», D1): una línea con valoración y
      `codigo_partida_final` vacío ES almacén, **tenga o no marca**; nunca un
      literal («ALM» no existe en `obrparpar`). `partida_action` solo deja
      rastro de quién o por qué: `almacen_sin_partida` (sv6: el albarán no
      trae partida), `almacen_elegido` (sv4: el revisor eligió «Almacén» o
      vació la partida), además de `alm_new_line_created` (ALM impreso) e
      `inherited_from_base_line`. No hay estado «sin partida» distinto: sv4
      pinta «Almacén» toda partida final vacía (también las valoraciones
      legadas) y la confianza no la castiga.
    - **A qué líneas va la partida lo decide IA1 leyendo el papel**
      (`config/prompts.yaml` de sv2, «Código de imputación manuscrito»): un
      código junto a una línea (o que agrupa varias) solo a esas, aunque sea
      el único; un código de documento (cabecera, sello, margen) a las que no
      tienen uno propio, y con códigos de línea además, cada marcada el suyo
      (D9); portes, bombeo y demás complementos sin código, el de su base; una
      línea sin código propio, no complemento y sin código de documento,
      `codigo_imputacion` null (almacén). Ejemplo del humano: «03.02» escrito
      solo junto a la 2.ª de tres líneas ⇒ la 1.ª y la 3.ª, almacén. Fase 2 lo
      recibe por `{prompt_fase_1}`. **Ningún servicio copia partidas entre
      líneas** salvo la herencia base → complementaria/sintética de sv6.
    - **sv6 no inventa partida**: una línea base sin `codigo_partida_albaran`
      va a almacén (`almacen_sin_partida`) conservando la línea de contrato
      casada y el precio; ya no copia la partida de esa línea. Cualquier
      familia puede ir a almacén; las de `FAMILIAS_DESTINADAS` (por defecto
      hormigón, mortero, combustible, alquiler de maquinaria y residuos) se
      marcan `review_required` con `partida_ausente_familia_destinada`, que
      **no bloquea** la aprobación. Interruptor de vuelta atrás:
      `ALMACEN_SIN_PARTIDA_ENABLED=false`.
    - **sv4**: «Almacén (sin partida)» es la primera opción fija del combo de
      partida; elegirla, vaciar la partida o el botón «Almacén a todas las
      líneas» (que pisa también las que tienen partida, con confirmación y
      deshacer) escriben partida final NULL + `almacen_elegido` sin tocar
      importes ni la casada: **una fila Sigrid sigue siendo Sigrid** (D4).
      Elegir almacén en una base no arrastra a sus complementarias (D8). Como
      todo override de sv4, **se pierde al revalorar** (D5; lo arregla F-058).
      Fuera de almacén la ficha pinta la partida **final** de la línea, no la
      de su línea de contrato casada, y «Guardar» / «Guardar todas» solo
      envían la partida si el revisor la cambió (vaciarla = almacén; sin
      tocar, no se toca). Poner la de la casada a una fila Sigrid la deja
      Sigrid y no avisa «pasará a NUEVA» (R20).
    - **Contrato hacia Sigrid** (R24): una línea en almacén se da de alta
      **sin partida**: sv9 (F-053) no manda ninguna clave de partida y
      sigrid-api la lleva al almacén de la obra (F-009 v5.1 no tiene campo
      `almacen`); nadie la rellena desde el contrato, la plantilla ni otra
      línea.
17. **Proveedor: el candidato claro se aplica** (F-062, oct 2026; decisión
    del humano «que proponga uno, salvo que no haya ningún candidato claro»,
    Q0–Q6 en `progress/spec_F-062.md`). Sustituye a la D3 de F-002 mientras
    `RED_PROVEEDOR_CORRECCION_ENABLED=true` (defecto).
    - Cuando el CIF leído **no existe** en `prv`, la red de proveedor de sv3
      busca un **candidato claro** entre los proveedores con contrato en la
      obra (la misma consulta agregada de F-052, una vez por pasada):
      **elegible** = identificador fiscal válido (`ruesma_comun.proveedores`:
      CIF/NIF/NIE con su carácter de control) y nombre que casa con el leído
      (score de F-052 ≥ `RED_PROVEEDOR_CORRECCION_SCORE_MIN`, 1,0: un nombre
      contiene al otro o todas las palabras de 3+ letras de uno aparecen
      como subcadena en el otro; **no** exige el nombre completo:
      «Transportes» casa con «TRANSPORTES PEREZ GARCIA, S.L.»). Aceptado por
      el humano (2026-10-08): es la red de seguridad; la defensa de fondo es
      F-055 (IA2 elige de los proveedores con contrato en la obra). Uno
      solo ⇒ claro; varios ⇒
      el de CIF más cercano al leído (Levenshtein) si saca
      `RED_PROVEEDOR_CORRECCION_MARGEN_DISTANCIA` (2) al siguiente. La
      distancia solo desempata; el control del leído no cambia la regla
      (solo se cuenta en la nota).
    - Con candidato claro, sv3 escribe su CIF y su razón social de Sigrid en
      el merge (origen `deterministic`) **antes** de buscar contratos, en las
      tres rutas (nuevo, duplicado y `MensajePersistencia(force=True)` de
      sv4), y lo manda a revisión con el motivo
      `proveedor_cif_corregido:<leído>><aplicado>` y la nota `[CORREGIDO]
      Proveedor` (prefijo propio: la red borra `[AVISO] Proveedor` en cada
      pasada). Lo leído queda en motivo y nota; la fila cruda no se toca.
    - Sin candidato claro, como F-002/F-052: motivo
      `proveedor_cif_no_casa:<leído>` y nota `[AVISO] Proveedor` con o sin
      propuesta, más «el carácter de control del CIF leído no es válido»
      cuando lo es.
    - **Nunca se pisa al revisor**: solo se corrige un CIF que no existe
      (el desplegable de sv4 solo escribe `prv.cif`) y nunca con origen
      `manual`. Elegir otro proveedor retira motivo y nota de la corrección
      en la siguiente pasada; los `proveedor_cif_no_casa` de otro CIF
      también caen. `review_required` no baja nunca solo.
18. **El CIF de Construcciones Ruesma nunca es el proveedor** (F-063, oct
    2026; incidencia de FEYMACO del 2026-10-08). Ruesma es el cliente de
    todos los albaranes y su CIF (A81873903) va impreso en ellos: leído en
    el campo de proveedor es siempre un error de la IA, aunque exista en
    `prv`. La lista de CIF propios vive en `ruesma_comun.proveedores`
    (`cifs_propios`, `es_cif_propio`); sv3 la amplía con `CIFS_PROPIOS`
    (separados por comas) y no se puede reducir.
    - Al empezar la resolución del proveedor (tres rutas: nuevo, duplicado y
      `MensajePersistencia(force=True)`), ANTES de la red por CIF de la regla
      17, un CIF propio se descarta: CIF y origen a NULL, nombre leído
      intacto, a revisión con motivo `proveedor_cif_propio:<cif>` y nota
      `[AVISO] CIF del cliente` (prefijo propio, como `[CORREGIDO]
      Proveedor`). Después sigue el camino «sin CIF» (proveedores con
      contrato en la obra por nombre y familia; luego global por nombre).
      Ni se consulta `prv` con él ni se canoniza el nombre al del cliente.
    - Un CIF propio nunca es candidato: se excluye de la lista de la obra,
      de la búsqueda global y de la propuesta/candidato claro de la regla 17.
    - Si el revisor elige a mano un CIF propio (origen `manual`), se respeta.
19. **Aprobar es registrar en Sigrid** (F-053, oct 2026). Spec:
    `specs/F-053-alta-sigrid/`; decisiones P1–P7 y D1–D4 en
    `progress/spec_F-053.md`.
    - **Disparo (sv4)**: solo el PASO a aprobado (por «Aprobar» del listado o
      «Guardar y aprobar») publica el alta, y solo con
      `ALTA_SIGRID_DESDE_UTC` puesta (vacía = feature apagada: sv4 como
      antes). Sin valorar no se aprueba (`ruesma_comun.valoracion.
      esta_valorado`: `ok` de sv6 o manual completa), con DESDE o sin ella.
    - **sv9**: reclama el documento con el merge bloqueado (`FOR UPDATE`) y
      lee el alta en OTRA sentencia; valida en local (`no_admitido` /
      `revisar` sin llamar a sigrid-api), busca altas a mano por CIF +
      número (`ya_en_sigrid`), hace la previa (`commit=false`) y la compara
      con lo aprobado; en **simulación** se queda en `simulado`; en modo
      **real** (`ALTA_SIGRID_COMMIT` = literal `true`, lo pone el humano)
      graba UNA vez, sin reintento, y adjunta el PDF. Líneas: vinculadas por
      `ctrpro_ide`; sin vincular con producto genérico por familia
      (`QA9999` alquiler de maquinaria, `XA9999` medios auxiliares,
      `MA9999` el resto; `ALTA_SIGRID_PRODUCTO_POR_DEFECTO`), que el
      administrativo cambia en sv4 (`albaran_line_valuations.
      producto_sigrid`; se pierde al revalorar, F-058).
    - **Bloqueo**: con el alta `en_curso`, `incierto` o `registrado`
      (`ruesma_comun.alta_sigrid.ESTADOS_ALTA_BLOQUEANTES`) sv4 rechaza
      desaprobar, guardar, deshacer, borrar, purgar, revalorar, volver a
      buscar contratos, elegir producto y toda edición de líneas (409 / aviso
      «Registrado en Sigrid como {cod}…»), comprobándolo dentro de su
      transacción con el merge bloqueado y el alta leída en otra sentencia;
      sv3 no borra ni reprocesa un PDF reingresado con alta bloqueante (R45).
      Se desbloquea anulando en Sigrid y pulsando «Ya lo he anulado en
      Sigrid» (sv9 comprueba que el `con.ide` ya no existe ⇒ `anulado`).
    - **Usuario de Sigrid** (v8): el alta va a nombre de quien aprobó (UPN de
      Easy Auth, que manda sobre formulario y cuerpo en sv4; parte local
      casada con `dbo.usu.cod`) o, si no casa, del Respaldo
      `ALTA_SIGRID_USUARIO_RESPALDO` (`pgris`). El número del proveedor se
      compara normalizado con `dca.entref` al buscar altas a mano.
    - **Las reglas compartidas viven en comun** (`ruesma_comun.alta_sigrid`):
      DESDE, Espera, «vinculada», «línea a registrar», producto efectivo y
      estados; sv4 y sv9 deciden con las mismas funciones.
    - **El panel de la ficha** (F-077, spec `specs/F-077-guardar-y-aprobar/`)
      tiene tres fases (`domain/services/alta_sigrid.fase_alta`): «Alta en
      curso…» solo mientras sv9 procesa la aprobación vigente (sin fila, fila de
      una aprobación anterior en estado repetible, o `en_curso` del mismo
      `approved_at_utc`, comparado como instante) y como mucho **5 minutos**
      desde la aprobación, sin nada del resultado anterior ni botones; pasados,
      error de tiempo («Sigrid no ha respondido en 5 minutos…», con «Solicitar
      alta» solo si `puede_solicitar_alta`); en otro caso, el resultado, con
      `no_admitido`, `revisar` y `error` pintados como error. Una fila anterior
      `ya_en_sigrid`, `registrado` o `incierto` es la respuesta (sv9 ignora la
      aprobación nueva). En «en curso» la ficha consulta cada 3 s `GET
      /api/documents/{id}/alta-sigrid/fase` (solo lectura: ni escribe el alta ni
      publica) y recarga una vez al cambiar. Todo motivo del alta se ve con su
      texto legible (`TEXTOS_MOTIVO_ALTA`, que un test contrasta con las fuentes
      de sv9) y el código en el `title`; los de una línea sin fila en la tabla
      del panel (p. ej. un rechazo local sin petición), como «Línea N: …» con N
      la posición de la fila en la ficha.
20. **Lo editado en las líneas manda** (F-065 fase 1, oct 2026). Spec:
    `specs/F-065-lineas-editadas-y-reparto/`; decisiones en
    `progress/spec_F-065.md` §v2. Lo aprobado es lo que sv9 da de alta, así
    que lo que deja el administrativo en una fila no lo deshace ningún otro
    guardado.
    - **Guardados separados**: el PUT del documento guarda SOLO la cabecera;
      `lines` y `valuation_line_updates` se aceptan (un `app.js` en caché) y se
      ignoran, y no se recalcula nada (se retiró `_recalc_valuation_importes`,
      que devolvía las filas a la cantidad leída: METALFIRE, 23 puertas en vez
      de 18). El PUT nunca desaprueba. Cada fila se edita con su PATCH, que
      lleva **solo los campos cambiados** (ausente = no cambia; `null` =
      vaciar); sin cambios no se escribe importe, su origen, descuento ni
      revisión. El importe solo se recalcula si cambia cantidad, precio o
      descuento (editar la descripción no reetiqueta un importe declarado).
    - **Q en la unidad del precio**: la ficha enseña y edita Q =
      `cantidad_convertida ?? cantidad_albaran` e `importe = precio × Q × (1 −
      dto/100)`. Al editar Q, la convertida es Q y la del albarán se deriva
      (`Q / factor` si la conversión es reproducible; Q si no hay conversión; la
      de antes en otro caso, p. ej. contenedores de residuos):
      `review_models.cantidades_tras_editar`. Una fila editada nunca queda con
      la convertida nula (sv9 rechaza una vinculada sin ella). La ficha pinta
      el precio **aplicado** (`precio_unitario_final`), con el del contrato en
      el `title`.
    - **Aprobado = solo lectura**: toda escritura de sv4 sobre un aprobado
      (cabecera, filas, alta y borrado de filas, almacén, producto, traer,
      bloquear, revalorar, volver a buscar, deshacer) responde 409 «Albarán
      aprobado: desapruébalo para editar», comprobado en la misma sesión que el
      cerrojo de la regla 19 (`_exigir_editable`). La ficha sale en solo
      lectura con «Desaprobar para editar». Mover a la papelera y purgar no
      son edición y siguen con solo el cerrojo de la regla 19.
    - **Guardar = bloquear**: «Guardar» (o «Guardar todas», solo filas con
      cambios) aplica y marca `albaran_line_valuations.bloqueada` (DDL de sv6,
      sentencia defensiva en sv4); una fila bloqueada no se edita, reapunta,
      pasa a almacén, cambia de producto ni se borra (409 «Línea guardada:
      desbloquéala para editarla») y los masivos se la saltan. «Desbloquear»
      la libera; las dos acciones tienen «Deshacer». Aprobar no exige filas
      bloqueadas. Revalorar las deja desbloqueadas (F-058).
    - **«Guardar» y «Guardar y aprobar» guardan antes las filas** (F-077,
      sustituye al aviso «Hay N líneas con cambios sin guardar» de F-065 R19):
      el PATCH de cada fila con cambios, en orden y con la misma validación de
      partida, y solo si todos van bien el PUT de cabecera. Al primer fallo se
      para (la fila en rojo con su motivo, sin PUT); las guardadas quedan
      guardadas y bloqueadas (no es atómico). Con filas guardadas, el aviso de
      la suma se relee del servidor antes de confirmar. Las tres vías de
      guardar filas usan la misma función de `app.js` (`enviarFila`).
    - **El ⚠ de la partida** (F-077) sale solo en filas Contrato con línea del
      albarán cuya partida leída no coincide con la de su línea de contrato, con
      el `title` «descripción · [Normalizada: X → Y, F-076] · No coincide con la
      partida leída en el albarán (X)» (la nota y el ⚠ se excluyen); nunca en
      Nueva, sintéticas, `manual` ni `reparto`, que no tienen lectura que
      comparar.
    - **Aprobar valida**: no se aprueba (ficha ni listado) con filas sin
      cantidad o importe («Líneas sin cantidad o importe: 3, 5», posiciones de
      la tabla de la ficha); si la suma de las filas no cuadra con la de lo
      leído, la ficha pide confirmación (no bloquea). Revalorar, «Guardar y
      volver a buscar» o elegir otro contrato piden confirmación si hay filas
      tocadas a mano (`review_models.es_fila_manual`); también «Solo volver a
      buscar». «Traer líneas contrato» exige la cantidad de cada línea y crea
      filas válidas para sv9. El almacén (partida final vacía) nunca impide
      aprobar; una fila sin línea de contrato NI derivada sí («revalora»), porque
      la ficha no la pinta y sv9 la mandaría sin vincular.
    - **Origen Contrato / Nueva** (fase 2): la ficha dice «Contrato» (antes
      «Sigrid»). Cambiar la partida a una distinta de la de su línea de
      contrato, el precio unitario (también al editar el importe) o la unidad
      de una fila Contrato la pasa a Nueva (derivada `manual_override`) **sin
      confirmación**; vaciar la partida (almacén) o poner la de su línea no
      cambia el origen, ni la descripción, cantidad, descuento o código externo
      (`review_models.cambia_origen`). Al editar nunca se llama a la IA. El
      combo de partida ofrece «Almacén» y las partidas hoja de la OBRA
      (`/api/sigrid/partidas`, solo valores de la lista; sin partidas o con
      Sigrid caído, solo «Almacén»; mientras llegan, «Cargando partidas…»;
      elegir cierra la lista; al teclear queda marcada «Almacén» («al»…) o la
      primera partida que coincide, y Enter elige la marcada: sin marcada no
      elige nada. En la partida, Enter nunca guarda la fila ni acepta
      «Dividir»; una partida cambiada que no es de la lista no se envía por
      ningún guardado: queda en rojo; el servidor no la valida contra la
      obra). «Origen ✎» es la única vía de reapuntar:
      una línea de contrato deja la fila Contrato con su partida, unidad y
      precio (y, desde F-078, su descripción en la fila); «Nueva», Nueva con
      los valores actuales. La descripción de la fila ya no va «solo si se
      editó» (F-065 CR1/H1): la sustituye la regla 22.
    - **Dividir** (fase 3; absorbe F-016): «Dividir» (o F7; F6 es del
      navegador) reparte una fila en 2–20 partes, cada una con su cantidad y
      su partida (combo de la obra; vacía = almacén); la última se rellena
      sola con lo que falta (solo lectura, en rojo si queda a 0 o de otro
      signo) y «Aceptar» solo si suman Q. `POST
      .../lines/{vid}/dividir`: 404 si la fila no es del documento, 409 con
      alta bloqueante, aprobado o fila guardada, 422 sin cambios si es
      sintética, sin línea de contrato ni derivada, con «revisa la cantidad»
      (se resuelve antes: la Q no es de fiar), Q nula o 0, una parte nula, 0 o
      de otro signo, la suma difiere de Q en 0,005 o más, o una parte saldría a
      0,00 € con importe en la original (sv9 no registra importes 0). Un `NaN` o
      `Infinity` en el JSON de dividir, editar una fila o traer líneas es 422
      (`allow_inf_nan=False`; el manejador de 422 los devuelve como texto). Modelo M1, **sin
      DDL**: la original es la parte 1 y cada parte k ≥ 2 es una fila
      `line_kind = 'reparto'` con `merge_line_id` nulo y `parent_merge_line_id`
      de la blanca de la original, sus campos copiados y en la valoración la
      descripción que enseña la original (la fijada, la de su línea o el concepto
      de su blanca: sv9 no tiene blanca que leer; desde F-078, la de
      `fila_a_guardar`, regla 22); `cantidad_convertida
      = qk`, `cantidad_albaran = ca0 × qk / Q` e importe `round(importe0 × qk /
      Q, 2)` (la última absorbe el redondeo: la familia suma lo de antes). El
      origen sigue la regla de editar: con la partida de la original, la de su
      línea de contrato o vacía, conserva origen y vínculo; con otra, Nueva con
      derivada `manual_override` propia (las partes de una Nueva siempre llevan
      la suya). Una transacción, total con `ROUND` y UNA entrada de «Deshacer»
      que borra partes y derivadas y devuelve la original. La ficha pinta
      «Parte k de N» bajo la original y, mientras la familia no sume lo que dice
      la blanca (en la unidad del albarán), un aviso que no bloquea. sv9 no
      cambia: una parte Contrato va vinculada a su `ctrpro_ide` (N partes al
      mismo `ctrpro` son N líneas, al final de la petición) y una Nueva sin
      vincular con producto genérico. El F7 de antes (duplicar) desapareció.
      La columna «Acciones» de la ficha va fija y pegada a la derecha
      (sticky): sus botones no salen nunca de la vista.
21. **El código de obra es canónico** (F-070, oct 2026). Spec:
    `specs/F-070-obra-con-cero-inicial/`; decisiones en `progress/spec_F-070.md`.
    Regla del humano: «es crucial que añada el 0 inicial si no es VAR ni
    POSTV2» (HERMANOS SAN JUAN: merge con `686`, los combos de sv4 vacíos).
    - **Un único punto**, `ruesma_comun.obras`: `normalizar_codigo_obra` da el
      canónico o `None` (3 cifras ⇒ `0` delante, también `900` ⇒ `0900`; 4
      cifras con `0` ⇒ igual; `VAR` y `POSTV2` en cualquier caja ⇒ en
      mayúsculas; lo demás ⇒ `None`) y `canonizar_codigo_obra` el canónico o,
      si no lo hay, el valor recortado. Los códigos sin cero viven solo en
      `CODIGOS_OBRA_SIN_CERO` (un test impide repetir los literales); otros no
      numéricos de Sigrid (`GG`, `POSTV`, `0578-B`…) no son canónicos.
    - **Dónde se aplica**: sv3 al SELLAR el merge y las crudas
      (`AlbaranNormalizer.normalize_obra_codigo`, obra del correo y del papel)
      y al escribir la obra deducida por texto; sv4 en las tres consultas a
      Sigrid por obra (proveedores, contratos y partidas: lo que no encaja va
      tal cual, el vacío no consulta) y al guardar la cabecera; sv9 en
      `cod_obra` del alta y sus motivos locales. Con VAR/POSTV2 válidas, la red
      de obra de sv3 ya no las descarta, el resolver no las sustituye y la
      búsqueda de contratos las busca y sella.
    - **Lo que no cambia**: sv2 y `ruesma_comun.contratos.origen_datos.normalizar_codigo`
      (forma de COMPARACIÓN de F-048, sin ceros), las SQL de Sigrid y los
      esquemas. Los merges ya guardados con 3 cifras **no se migran** (P3):
      los cubren sv4 al consultar y guardar y sv9 al dar de alta.

22. **La fila valorada es la fuente de verdad de la línea** (F-078, oct 2026).
    Spec: `specs/F-078-linea-guarda-lo-que-se-ve/`; medición y decisiones en
    `progress/spec_F-078.md`. Principio del humano: «Lo que está en la tabla es lo
    que debería estar guardado en BBDD, ya que lo ha puesto el humano. No es que
    sv9 tenga que buscar en muchos sitios, sino que esté bien guardado todo.»
    - **Cada campo de «Líneas a Sigrid», en su columna de la fila**: concepto →
      `descripcion_linea`; unidad → `unidad_contrato` (la de Q y del precio); Q →
      `cantidad_convertida ?? cantidad_albaran`; precio → `precio_unitario_final`;
      importe → `importe_calculado`; dto → `descuento_albaran_aplicado`; código
      externo → `codigo_externo`; partida → `codigo_partida_final` (vacía =
      almacén, regla 16). sv4 pinta cada campo de su columna, sin completarlo con
      la línea de contrato, la derivada ni la blanca: vacío = vacío (el importe nulo
      ya no lo calcula la plantilla). Su línea solo da el precio del contrato del
      `title`, la medición, la descripción de la partida, los avisos ✓/⚠ y la
      partida casada.
    - **Una regla, en comun**: `ruesma_comun.linea_valorada.fila_a_guardar`.
      Concepto: Contrato, el de la fila o el de su línea; Nueva con blanca, el de
      la fila o el del papel (P1 = (b): no el de su derivada); Nueva sin blanca
      (manual, reparto, sintética), el de su derivada o el de la fila; si no hay,
      el de la blanca. Unidad: la de su línea o la de la fila. Precio: el de la
      fila o el de su línea. Sin conversión (factor = 1): `unidad_albaran` vacía ⇒
      la unidad y `cantidad_convertida` nula ⇒ Q; con conversión (o factor nulo)
      no se tocan. La aplican **sv6** a cada registro antes del replace
      (`completar_registros`: toda rama del pipeline que persista líneas pasa por
      ahí, lo exige un test), **sv4** en toda vía que crea o reapunta una fila
      (`_materializar_fila_in_session`: «Origen ✎», «+ a Sigrid», «Traer líneas
      contrato», «Dividir»; una vía nueva solo tiene que llamarlo; «Añadir línea»
      nace vacía y así se ve) y el **relleno** de lo anterior
      (`scripts/rellenar_filas_f078.py` de sv6: solo lectura por defecto;
      `--aplicar` lo lanza el humano).
    - **El PATCH de fila** toma el estado actual solo de la fila, guarda la
      descripción cambiada en `descripcion_linea` en toda fila y la unidad
      cambiada también en `unidad_albaran` sin conversión. No aplica la regla: lo
      vaciado se ve vacío.
    - **Aprobar** (ficha o listado) no deja con filas a registrar sin vincular
      (`es_linea_vinculada`) sin descripción: «Líneas sin descripción: 3, 5».
    - **sv9 no cambia** ni busca en otras tablas. El producto por defecto sigue
      sin guardarse (regla 19: sv4 y sv9 lo calculan igual). Fuera de F-078: la
      descripción editada de una Contrato vinculada no llega a Sigrid (F-079).

23. **La partida final es un código de la obra** (F-076, oct 2026). Spec:
    `specs/F-076-normalizar-partidas/`; medición y decisiones en
    `progress/spec_F-076.md`. Origen: sigrid-api rechazó con
    `partida_no_encontrada` los albaranes de T51 (leída `CI.04.18`, la obra tiene
    `CI.4.18`); sigrid-api compara sin mayúsculas ni espacios, pero no quita ceros.
    - **Dónde**: en **sv6, al valorar**, antes de IA4, de la rama `no_contract` y
      de las reglas (también al revalorar con `force`): lo que enseña la ficha es
      lo que manda sv9. `NormalizadorPartidas` resuelve la partida leída de cada
      línea contra las partidas HOJA de la obra con
      `ruesma_comun.sigrid.resolver_partida_obra`: exacta o normalizada con la
      clave `normalizar_partida` (NFKC, mayúsculas, separadores, sin ceros a la
      izquierda en segmentos numéricos) ⇒ el código TAL COMO FIGURA EN LA LISTA;
      si la clave es la de un código NO hoja (`03.02` capítulo), compuesta, sin
      candidata o con más de una ⇒ no se toca y la línea va a revisión
      (`partida_fuera_de_lista` / `partida_ambigua_en_obra`, no bloquea aprobar).
      Nunca por parecido, sufijo ni distancia (H1 de F-049).
    - **Rastro** (regla 6): `codigo_partida_albaran` de la valoración conserva la
      leída; `codigo_partida_final` es la de la lista; motivo
      `partida_normalizada:<leída>><lista>` sin revisión.
    - **Una lista, en comun**: `ruesma_comun.sigrid.partidas` (subconjunto
      aprobado de F-049: SQL de sv4 + `con_obr.emp = 1`, hojas, clave, casado) y
      `CachePartidasObra` (por réplica: 6 h, 64 obras, fallo recordado 300 s).
      sv4 lee el combo de partidas de ahí (sin copia; truncada ⇒ `ok=false`) y su
      aviso ✓/⚠ de partida compara por la misma clave (`coincide_partida`: ✓ con
      nota «Normalizada: X → Y» si solo difieren en la forma).
    - **Sin lista** (sin `SIGRID_API_*`, obra vacía, sigrid-api caído, truncado, 0
      hojas): se valora como antes, WARNING y `partidas_obra_no_disponibles` en la
      cabecera sin revisión. `PARTIDAS_OBRA_NORMALIZAR_ENABLED=false` lo apaga sin
      redesplegar. sv9 no cambia: manda `codigo_partida_final`. Lo existente se
      corrige revalorando desde sv4 (lo manual se pierde, F-058).

## Acceso a datos y sistemas externos

- **PostgreSQL `albaranes`** (Azure Flexible Server compartido
  `psql-albaranes-rs9k2`): sv3 dueño del schema (también del DDL de
  `albaran_altas_sigrid`, F-053); sv4 lectura+escritura de revisión (lee el
  alta, nunca la escribe); sv5 SOLO lectura; sv6 dueño de las 3 tablas de
  valoración (columna `producto_sigrid`, que escribe sv4) y lee `obra_codigo`
  del merge (F-076, regla 23); sv9 lee merge y
  valoración y escribe SOLO `albaran_altas_sigrid`; sv1 solo `workflow_runs`. Cambios a nivel de servidor afectan a otros
  proyectos: prohibidos desde aquí.
- **Sigrid (ERP)**: SOLO vía `sigrid-api` (function key), nunca SQL directo.
  Leer: cualquier servicio (sv3, sv4, sv9 y, desde F-076, sv6: solo `sql/read`
  de las partidas de la obra, con caché). **Escribir: SOLO sv9** (F-053), con el alta de
  albarán (`sigrid/albaran`, modo extendido) y `concepto-grafico`, nunca
  `sql/write`, y solo con `ALTA_SIGRID_COMMIT=true`, que activa el humano;
  desde local, nunca (en local `ALTA_SIGRID_COMMIT` no se pone).
  La instancia admite **500.000 filas por petición** (`MAX_ALLOWED_ROWS`,
  leído en Azure el 2026-09-30; `azure-apps/sigrid_api.md` §4.1). El 1.000
  que cortaba listas en silencio era el `max_rows` por defecto del cliente
  de sv3, no un tope de sigrid-api (F-052). El balanceador corta a los
  230 s: lo que acota una lectura es su `timeout_s` (30 s por defecto), no
  el número de filas. Reglas de lectura (F-052):
  - **`truncated` nunca en silencio**: cada consulta declara su
    `PoliticaTruncado` (`NO_TOLERA` lanza `SigridRespuestaTruncada`,
    `TOLERA` usa las filas con WARNING); se comprueba con
    `ruesma_comun.sigrid.comprobar_truncado`.
  - **Agregar en SQL antes que paginar**: pedir el grano que se usa (una
    fila por proveedor con `WITH` + `FOR XML PATH`, no una por línea).
  - **Paginar con `ruesma_comun.sigrid`** (`con_paginacion` +
    `leer_paginado`: `ORDER BY` estable, `max_rows = página + 1`, tope de
    páginas). Página máxima `PAGINA_MAXIMA` (499.999), para que ninguna
    petición pase de `MAX_FILAS_POR_PETICION` (500.000).
- **Microsoft Graph**: buzón M365 (sv1) y SharePoint (sv3/sv4/sv5) con
  `GRAPH_KEY`. SharePoint es el almacén durable de documentos.
- **APIs LLM**: Anthropic/OpenAI/Gemini (sv2 y sv5, flags `ENABLE_*`).
  Las claves llegan por entorno/Key Vault, jamás en código ni en specs.
- **Colas y blobs**: Azure Storage en la nube; **Azurite en local**
  (`COLAS_CONNECTION_STRING`) — desde local nunca contra las colas reales.
- Los unit tests no tocan NINGUNO de estos sistemas: mocks y fixtures.

## Infra y despliegue

`infra/` gestiona SOLO el despliegue de Azure (el real); el local de pruebas
no usa estos scripts. Detalle completo del despliegue, troubleshooting y
rollback: `docs/referencia/dominio_negocio_albaranes.md` §6–§7.

- Azure Container Apps (Spain Central), registro `acralbaranesdev` (admin
  deshabilitado: acceso por managed identity), secretos en Key Vault
  referenciados desde cada Container App.
- **Modo single de revisiones** (dos revisiones activas = dos consumidores
  de la misma cola con imágenes distintas) y **`comun` horneado en cada
  imagen**: tocar `ruesma_comun` obliga a reconstruir sv2, sv3, sv5 y sv6
  — un fix en comun sin rebuild no existe en Azure. Excepción conocida:
  `ruesma_comun.sigrid` y `ruesma_comun.obras` (F-052, F-070) solo los
  importan sv3, sv4, sv9 y, desde F-076 (comun 0.8.0, `sigrid.partidas`), sv6.
  F-076 despliega en orden `set_partidas_sv6.ps1` → sv6 → sv4 (sin DDL ni
  cambio de mensajes). En F-052 se reconstruyeron en orden **sv3 → sv4**
  (sv3 aplica el DDL de `contratos_busqueda_*` que el ORM de sv4 lee); el
  cambio de `obras` de F-070 no lleva DDL ni contrato de mensajes y vale en
  cualquier orden: recomendado **sv4 → sv3**, y sv9 sale con F-053 desde un
  `dev` que ya contenga F-070 (regla 21). F-053 toca
  comun ⇒ todas las imágenes, en orden **sv6 y sv3 → sv9 → sv4** (sv6 la
  columna `producto_sigrid`, sv3 la tabla del alta; sv9 sale con DESDE vacía
  y `ALTA_SIGRID_COMMIT=false`, `create_capps_sv9.ps1`, máximo 1 réplica);
  DESDE se pone después en sv9 y sv4 a la vez con `set_alta_sigrid.ps1`
  (`infra/README_capps.md`).
- Scripts en `infra/`: `fase1_infra.ps1` (provisión), `add_secrets.ps1`,
  `create_capps*.ps1`, `build_images.ps1` + `deploy.ps1` (redespliegue).
  `build_images.ps1` espera los repos como hermanos: desde el monorepo,
  pasarle `-ProjectsRoot <monorepo>\services`.
- Imágenes con **tags fechados** (`rYYYYMMDD-HHmm`), nunca reescribir tags.
- Los IDs de suscripción/tenant/MI están **redactados** en los scripts
  versionados; los valores reales viven en `infra/*.local.ps1` (gitignored).
- `.env` nunca viaja: ni a git ni a una imagen.
