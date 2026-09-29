<!-- progress/spec_F-052.md -->
# Spec F-052 · Proveedores de la obra truncados · Informe del spec-author

Fecha: 2026-09-29 · Rama `feature/F-052-proveedores-truncados` (worktree
`albaranes-F-052`) · Estado: **spec_ready** · Rigor: **critico**.
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
