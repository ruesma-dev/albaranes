<!-- progress/spec_F-052.md -->
# Spec F-052 · Proveedores de la obra truncados · Informe del spec-author

Fecha: 2026-09-29 · Rama `feature/F-052-proveedores-truncados` (worktree
`albaranes-F-052`) · Estado: **spec_ready** · Rigor: **critico**.

> **Vigente: la sección «v2 (2026-09-29)» del final.** Lo de arriba es la v1:
> se conserva como rastro, pero D1, D2, D3 y D7 quedan sustituidas.
Spec: `specs/F-052-proveedores-truncados/` (requirements 150/150, design
250/250 según `python -m harness.tamano --feature F-052`; tasks: 23 tareas).

**No se ha ejecutado `bash harness/init.sh` ni ninguna suite**, por orden
del líder: había una review corriendo en la máquina y dos suites a la vez
tumban Windows. Solo se ha pasado `harness.backlog` y `harness.tamano`.

## Resumen

Parte de `progress/explore_salmedina_proveedor.md` (causa raíz demostrada).
Servicios: sv3 (resolver, cliente Sigrid, DDL), sv4 (bloque de contrato,
selector) y `ruesma_comun` (módulo nuevo `sigrid`, lógica pura).

1. **Candidatos completos** (R1–R5): los dos caminos del resolver toman los
   candidatos de la lista `DISTINCT cif, raz` de la obra, la misma SQL que el
   selector de sv4. El texto de familia se lee **paginado** con
   `OFFSET/FETCH` y cada proveedor de la lista tiene su resumen, tenga o no
   líneas. Si se alcanza el tope de páginas, no hay deducción por familia.
2. **`truncated` nunca en silencio** (R6–R12): `_post_sql_read` exige una
   política por llamada. La tabla de las 7 consultas del cliente está en
   `design.md` §3: 5 no toleran (3 de ellas paginadas) y 2 toleran con
   WARNING (documentos del PDF del contrato).
3. **Nota veraz** (R13–R17): distingue consulta fallida, sin obra, sin nombre
   y «ninguno de los N casa». Se mantienen el motivo y el prefijo que sv4
   retira.
4. **sv4** (R18–R25): el merge **no guarda** con qué CIF y obra se buscó
   contrato. Con 0 contratos no queda ni rastro en `albaran_contratos_merge`,
   y si Sigrid falla, `enrich_merge_document` devuelve 0 y deja los
   contratos viejos. Se proponen 4 columnas `contratos_busqueda_*` (DDL en
   sv3) que selle sv3 en cada salida del enriquecimiento. El bloque de sv4
   pinta la verdad: vigente, desfasada, error, sin datos o sin rastro.
5. **Tests RED** con un doble de sigrid-api (`httpx.MockTransport`) que
   respeta `max_rows`, `OFFSET/FETCH` y `truncated`. El fixture de la obra
   0691 tiene 2.083 filas y deja al bueno más allá de la fila 1.000. El
   caso real va como MANUAL (T20 y T21) con su comando.
6. **Saneamiento** (`design.md` §8): se hace en dos pasos de solo lectura.
   Primero, en sigrid-api, las obras de más de 1.000 filas. Después, en la
   BBDD `albaranes`, los albaranes con «ningún proveedor casa», los
   `det_familia_obra` y los «sin CIF: no deducible» de esas obras. Sin
   backfill.
7. **Despliegue sv3 → sv4** (el DDL primero). sv2, sv5 y sv6 no importan el
   módulo nuevo de comun.

## Hallazgos que no estaban en el diagnóstico

- **El 1.000 no es de sigrid-api**: la instancia `dev` admite 500.000 filas
  (`azure-apps/sigrid_api.md` §4.1). Es el `max_rows` por defecto del
  cliente de sv3. Dos documentos están desfasados: `docs/ARCHITECTURE.md`
  dice «10.000» (se corrige en T17) y el `CLAUDE.md` transversal de
  `PycharmProjects` dice «como máximo 1.000». Este último no es de este
  repositorio y no se toca: queda para el humano.
- **`search_proveedores` (el fallback global por nombre) también corta a
  1.000**: declara `max_rows=5000`, pero `_post_sql_read` usa siempre
  `self._max_rows`. Entra en la feature (R10).
- **Sigrid es SQL Server 2012**: no hay `STRING_AGG`. Por eso el texto por
  contrato no se agrega en SQL.
- sv3 ya tenía un `fetch_proveedores_por_obra` con `DISTINCT` (lo usa el
  grounding de fase 2), pero no el resolver. El arreglo lo reutiliza.
- **Hay 3 copias sin control de `truncated`**, además de la de sv3:
  `SigridApiObraClient` de sv3, el cliente de contratos de sv4 (fallback
  solo-front) y el lookup de sv4. Este último entra en la feature; los otros
  dos, ver D6.

## Decisiones abiertas para el humano

**D1 · Cómo leer el texto de familia sin truncar.** Recomiendo **paginar con
`OFFSET/FETCH`**, que es el patrón obligatorio de `sigrid_api.md` §6.4 y no
depende del tamaño de la obra. Alternativas descartadas:
- Subir `max_rows` a 10.000 en una sola llamada: es más simple, pero solo
  mueve el precipicio.
- Agregar por contrato con `FOR XML PATH`: es frágil (columnas `text`, lista
  blanca de prefijos de sigrid-api).

**D2 · SQL de proveedores de la obra en `ruesma_comun`.** Recomiendo **sí**:
es la regla del monorepo, hoy hay dos copias (la de sv4 es la buena) y sv4
ya entra en la feature por el bloque de contrato. El coste es tocar el lookup
de sv4 (T15), sin reconstruir sv2, sv5 ni sv6. La alternativa es que sv3 use
su `fetch_proveedores_por_obra` y sv4 no se toque en esta parte, con la
duplicación anotada como deuda.

**D3 · Tamaño de página y tope.** Recomiendo 5.000 filas por página y 20
páginas (100.000 filas), configurables por entorno. La obra más grande
medida, 0691, cabe en una página.

**D4 · sv4 y la búsqueda de contrato tras cambiar CIF u obra.** La spec
diseña la **opción B**: el rastro de la búsqueda más un bloque que dice con
qué CIF y obra se buscó y si los datos actuales están sin buscar. La
**alternativa A** es que «Guardar» relance sola la búsqueda (re-fetch por
`q-persistencia`, como «Guardar y volver a buscar») cuando cambian el CIF o
la obra. Recomiendo **B en esta feature**:
- Es la única que hace veraz el mensaje también en la ventana asíncrona de
  la cola y cuando Sigrid falla.
- A sola seguiría mintiendo en esos dos casos.

A es compatible con B: si la quieres además, cuesta una tarea en `app.js`
más su test.

**D5 · Saneamiento de producción.** Recomiendo **sin backfill**, como en
F-043. Tras desplegar, el humano ejecuta los dos SELECT de `design.md` §8
(solo lectura) y corrige a mano en sv4 los que salgan: proveedor, «Guardar y
volver a buscar», contrato y revalorar. Límite: el atajo por nombre dentro
de la obra sella `deterministic` y no se distingue del fallback global.

**D6 · Clientes colindantes con el mismo defecto.** Son `SigridApiObraClient`
de sv3 (`search_obras` con 5.000 filas, sin mirar `truncated`) y el cliente
de contratos del fallback solo-front de sv4 (`max_rows=1000`). Recomiendo
dejarlos **fuera** y abrir una feature pequeña que los pase a
`ruesma_comun.sigrid`:
- El primero no tiene hoy riesgo medido (las obras son muchas menos de
  5.000).
- El segundo solo corre en local.

**D7 · Efecto esperado en la deducción por familia.** Con la lista completa
habrá **menos** proveedores deducidos (`det_familia_obra`) y más avisos «no
deducible» en las obras grandes, porque el margen sobre el segundo se
estrecha. Es conservador, pero sube la carga del revisor. Hay que
confirmarlo como aceptable.

## v2 (2026-09-29)

Rehecha a partir de `progress/explore_F-052_grano.md` (medición de solo
lectura contra sigrid-api). El humano objetó que una obra tiene 100–200
proveedores y no debería hacer falta pedir miles de filas. Tenía razón: **el
problema era el grano de la consulta, no el tamaño de la obra**. Topes:
requirements 150/150, design 250/250 (`python -m harness.tamano --feature
F-052`); tasks: 24 tareas, una por línea. No se ha ejecutado `init.sh` ni
ninguna suite.

### Qué cambia

1. **`fetch_contratos_resumen_por_obra` = una consulta agregada** (`WITH` +
   `FOR XML PATH`, una fila por proveedor; design §4), **sin paginar**, una
   llamada, `NO_TOLERA`. En las 74 obras de más de 1.000 líneas da 0
   diferencias de familias, máx. 163 filas, `truncated=false`, ≤ 5 s y 133 KB.
   Se añaden dos `ORDER BY` internos para que texto y códigos sean
   deterministas; la verificación manual T21 revalida la medición con ellos.
   Si falla (incluido el error de XML), se trata como hoy: la red por nombre
   dice «no se pudo consultar» (R6, R15) y el paso obra + familia cae al
   fallback global. La alternativa sin XML (Q1 + Q2 de la exploración) queda
   **documentada y no se implementa**. Un test con el modo `error_xml` del
   doble fija que ese error acaba en «consulta fallida» y no en «nadie casa».
2. **Los candidatos salen de la misma consulta.** La v1 separaba la lista
   `DISTINCT` y el texto para que los candidatos no dependieran del texto
   paginado. Con la agregada, la lista es completa por construcción: el puerto
   `ProveedorReverseLookupClient` no cambia y el resolver sigue llamando a
   `fetch_contratos_resumen_por_obra` en sus dos caminos.
3. **Equivalencia**: `test_f052_equivalencia_familias.py` (R4, T6) compara por
   CIF las familias del texto agregado con las del texto por líneas sobre el
   mismo fixture. Fija la semántica en Python; que la SQL real la cumple lo
   comprueba T21 (MANUAL, solo lectura, 0691 y 0696).
4. **Paginan solo dos consultas**: `header_and_lines` (CIF + obra; alimenta la
   valoración, la mayor pareja tiene 989 líneas) y `search_proveedores`.
   **Hallazgo nuevo**: medido hoy, `search_proveedores` devuelve **3.543**
   proveedores (`SELECT COUNT(*)` sobre su `DISTINCT`, solo lectura, script
   `cuenta_global.py` del scratchpad), así que el fallback global por nombre
   **ya se corta a 1.000 en producción** sin que nadie lo vea.
5. **Sale de la v1**: `ruesma_comun.sigrid.consultas.py` (la SQL compartida
   con sv4), `config/settings.py` y el paso por las raíces de composición, el
   cambio de puerto y el tope de páginas del texto de familia (antiguo R4).
6. **Saneamiento**: las obras afectadas ya se conocen, son las 74. El SELECT
   de sospechosos de la BBDD `albaranes` pasa al Anexo de este informe para
   que el design quepa en su tope.

### Script de la exploración (para T14)

Sigue en el scratchpad de la sesión:
`C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-albaranes\f36c80f5-0cba-463e-95e9-161d51e3f583\scratchpad\`
(`grano.py` es el helper `q()` y `familias_de_texto` real; `agg.py`, la
comparación agregada frente a la consulta por líneas sin tope; `obras.py`, las
obras de más de 1.000 líneas). No se versiona: `grano.py` lee el `.env` a mano.
Si el scratchpad ya no existe, T14 lo rehace así:
1. Construye el cliente de sv3 desde su `.env`, como en `composition.py`.
2. Para cada `--obra`, lanza la consulta por líneas de hoy con
   `max_rows=20000` y agrupa por CIF los tres campos no vacíos en orden de
   llegada.
3. Lanza la agregada.
4. Por CIF, calcula `familias_de_texto` de los dos textos y la diferencia de
   conjuntos.
5. Compara los CIF de la agregada con los de `fetch_proveedores_por_obra`.
6. Registra filas, `truncated`, bytes y segundos.

### Decisiones para el humano (v2)

**D1 · Cómo obtener proveedores y texto de familia.** Recomiendo la
**consulta agregada en SQL**, sin paginar: 0 diferencias medidas en las 74
obras y una llamada de ≤ 163 filas. Alternativas:
- Paginar (v1): funciona, pero trae hasta 5.558 filas para 163 proveedores.
- Q1 + Q2 sin XML: elimina el riesgo de XML, pero Q2 vuelve a necesitar
  paginar. Queda documentada como salida si ese riesgo aparece.

El motivo con que la v1 descartó `FOR XML PATH` era falso: con el `CAST`
funciona a través de sigrid-api y la lista blanca no lo rechaza. Riesgos que
se aceptan (design §10): un carácter de control en una descripción, que
sigrid-api o su validador dejen de aceptar `WITH` o `FOR XML`, y 5 s en la
obra más lenta. Los tres degradan igual que hoy, de forma visible y sin
elegir mal.

**D2 · SQL de proveedores de la obra compartida en `ruesma_comun`.**
Recomiendo **no compartirla**: cada servicio se queda con la suya.
- El selector de sv4 necesita `cif, raz`: ≤ 193 filas y unos pocos KB.
- sv3 necesita además el texto de familia: hasta 133 KB por obra.
- Compartir obligaría a sv4 a cargar un texto que no usa, o a sv3 a hacer dos
  llamadas, que es lo que la agregada evita.

Lo que tienen en común es **la definición de candidato** (contratos `emp=1`
de la obra, por `con_obr.cod`). Eso se protege con T21, que exige el mismo
conjunto de CIF en las dos, y no con código compartido. Sí se comparte
`ruesma_comun.sigrid.lectura` (truncado y paginación), que usan sv3 y sv4
(R28). Deuda anotada: sv3 tiene además su propio `fetch_proveedores_por_obra`
(grounding), con la misma semántica que el de sv4. Solo recibe su política
aquí; unificarlo iría con D6.

**D3 · Paginación de `header_and_lines` y de `search_proveedores`.**
Recomiendo **paginar las dos**, con 1.000 y 5.000 filas por página y un tope
de 20 páginas. Van como kwargs con valor por defecto del cliente, sin
variables de entorno.
- `header_and_lines`: paginar es mejor que solo detectar el truncado y
  avisar. Detectar convertiría un contrato grande en rastro `error` sin
  contratos, y el albarán se quedaría sin valorar. Paginar no cuesta ninguna
  llamada extra en el caso normal (989 < 1.000).
- `search_proveedores`: 3.543 hoy. Cabe en una página de 5.000 y crece sin
  precipicio.

Alternativa mínima, si se prefiere no paginar: `NO_TOLERA` con
`max_rows=5000` en las dos. Falla de forma visible, pero vuelve a poner un
precipicio.

**D4, D5 y D6** se mantienen como en la v1. En D5 la lista de obras ya se
conoce (74) y el script de T14 la recalcula.

**D7 · Efecto en la deducción por familia (cambia).** Fuera de las 74 obras
grandes **no hay ningún cambio**: la lista ya estaba completa y el texto
agregado da las mismas familias (R4, medido). Dentro de esas 74, hoy el
resolver ve solo lo que cabe en las primeras 1.000 filas, en un orden que la
SQL no fija, así que su resultado ya era en parte aleatorio. Con la lista
completa, el efecto va **en los dos sentidos**:
- **Menos deducciones** cuando aparece un competidor de la misma familia que
  estrecha el margen.
- **Más deducciones, y correctas**, cuando el bueno faltaba o tenía el texto
  incompleto.

La regla del margen sigue siendo conservadora: ante la duda, el albarán va a
revisión. Pido aceptarlo sin medir el saldo, que solo se ve tras desplegar
(T23).

### Anexo · SELECT de sospechosos (BBDD `albaranes`, solo lectura; T23)

`:obras_grandes` = la salida de `--listar-obras-grandes` (74 obras el 2026-09-29).

```sql
SELECT d.id, d.source_filename, d.numero_albaran, d.obra_codigo,
       d.proveedor_cif, d.proveedor_cif_origen, d.approved, d.created_at_utc,
       CASE WHEN d.review_notes ILIKE '%ningun proveedor con contrato en la obra casa%' THEN 'nadie_casa'
            WHEN d.proveedor_cif_origen = 'det_familia_obra' THEN 'familia_obra'
            WHEN d.review_notes ILIKE '%sin CIF: no deducible con seguridad%' THEN 'sin_cif_ambiguo'
       END AS sospecha
FROM albaran_documents_merge d
WHERE d.is_active
  AND ( d.review_notes ILIKE '%ningun proveedor con contrato en la obra casa%'
     OR ( d.obra_codigo = ANY(:obras_grandes)
          AND ( d.proveedor_cif_origen = 'det_familia_obra'
             OR d.review_notes ILIKE '%sin CIF: no deducible con seguridad%')))
ORDER BY sospecha, d.created_at_utc;
```
