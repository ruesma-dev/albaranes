<!-- progress/spec_F-070.md -->
# F-070 · informe del spec-author (2026-10-14)

Spec: `specs/F-070-obra-con-cero-inicial/` (requirements 18 R, design, tasks T0–T14). Rama
`feature/F-070-obra-con-cero-inicial` desde `dev` (`dcd25cc`), worktree
`C:\Users\pgris\PycharmProjects\albaranes-F-070` con *junction* de `.venv` de sv4. F-070 dada de alta
en `harness/features.json` como `spec_ready`, prioridad 1, rigor `critico`.

## 1. Dónde entra la obra sin el 0 (respuesta al punto 1 del líder)

- **Se sella en sv3**, en `AlbaranNormalizer.normalize_header` (`normalize_identifier`: espacios y
  mayúsculas, sin el 0) y de ahí `obra_codigo=cabecera.obra_codigo` en `sqlalchemy_albaran_repository`
  (merge y crudas). sv3 usa `normalizar_codigo_obra` solo para CONSULTAR (red de obra, resolver,
  grounding, contratos): encuentra `0686`, rellena nombre y dirección y **deja `686` en el merge**.
- **De dónde viene el `686`**: el resolver de sv2 (F-048) escribe el código del correo en la forma de
  la lista de Sigrid (`0686`) cuando tiene lista. Deja lo leído por IA1 cuando **no hay lista**
  (sigrid-api no respondió: `validada = null`), en la fila «confirma papel» sin lista y cuando el
  correo no aporta y manda el papel. No he podido leer `origen_datos` de los 5 pendientes (no hay
  credenciales de la BBDD de Azure en los `.env` locales, que apuntan a `localhost`): lo mide la T0
  (Anexo A). El arreglo no depende de qué camino fue: se canoniza donde se sella.
- Otros caminos que persisten la obra: el resolver de sv3 (deducción por texto, devuelve `con.cod`
  tal cual) y el guardado de cabecera de sv4. Los dos canonizan en F-070 (R7, R12).

## 2. Comprobaciones en Sigrid (sigrid-api `/api/sql/read`, solo lectura, 2026-10-14)

Scripts en el scratchpad de la sesión (`f070/sigrid_obras*.py`), con el `SigridLookupClient` de sv4 y
su `.env` (sin imprimir credenciales).

- `con.cod` de obra (`obr JOIN con`): **VAR** existe en empresa 1 («OBRAS VARIAS», ide 683806) y 28;
  **POSTV2** en empresa 1 («POSTVENTA 2», ide 1659588) y 28 («POSTVENTA»). Con `VAR`: 20 proveedores,
  24 contratos (empresa 1) y 125 partidas hoja; con `POSTV2`: 83, 123 y 234. `var` en minúsculas da lo
  mismo (colación sin mayúsculas).
- `686`, `711`, `723` no existen; `0686`, `0711` (empresas 1 y 28) y `0723` sí. `686` ⇒ 0/0/0;
  `0686` ⇒ 115 proveedores, 117 contratos, 2412 partidas (cuadra con el líder).
- 846 códigos de obra únicos: 580 de 4 dígitos con 0, 223 de 6–7 dígitos (obras viejas), 35 no
  numéricos (GG, CM, CP, OT, POSTV, POSTV2, VAR, BD…, `0578-B`, `0676B`, `150702-E`…), 4 con espacio
  final y **3 de 3 dígitos sin 0: `227` (empresa 8) y `229` (empresa 9), cuyas `0227`/`0229` existen
  en la empresa 1, y `900` (empresa 1, «Rehabilitación del Edificio del Conservatorio Mariemma»: 374
  partidas, 0 contratos, 0 proveedores; `0900` no existe)**. Ver P1.
- El combo de partidas de sv4 no filtra empresa: VAR trae 1 fila de la empresa 28 y POSTV2, 6. Ya
  pasa hoy (sv4 manda `VAR` tal cual); fuera de F-070, propuesta de ficha abajo.

## 3. Qué cambia en sv3 si VAR y POSTV2 dejan de ser `None`

Design §5. Resumen: hoy sv3 **descarta** la obra VAR/POSTV2 (red de obra, `obra_codigo_invalido:VAR`,
merge con obra nula), el resolver la **sustituye** por una deducida por texto y no se buscan
contratos (`sin_datos`). Con F-070 se valida en Sigrid, se respeta y se buscan sus contratos. En sv4,
el rastro viejo sale «desfasada» y «Guardar» relanza la búsqueda (correcto).

## 4. Decisiones del spec (sin preguntar)

- Un único punto: `ruesma_comun.obras` (`CODIGOS_OBRA_SIN_CERO`, `normalizar_codigo_obra` extendida y
  `canonizar_codigo_obra` = canónico o tal cual). Se reutiliza el módulo de F-052, no se crea otro.
- sv2 no se toca (R17): sv3 sella después; tocar sv2 obliga a reconstruirlo y no aporta.
- sv4 canoniza en `SigridLookupClient` (las tres consultas) y al guardar la cabecera; sv9, en el
  validador (domain, puro). Sin DDL, sin migración, sin escrituras en producción.
- Mayúsculas en VAR/POSTV2 (forma de Sigrid).

## 5. Tests y evals afectados

- Nuevos: `test_f070_*` en comun, sv3, sv4 y sv9 (tasks). Existentes que deben seguir en verde sin
  cambios: `test_f052_obras_codigo.py` (ningún caso usa VAR/POSTV2), `test_f002_red_obra.py`,
  `test_f048_r28_red_obra.py`, `test_f052_t19_supervivientes.py` (`abc`, `1234`, `12345` siguen
  inválidos), `test_f052_busqueda_contratos.py`, `test_f052_lookup_truncado.py` (usa `0691`),
  `test_f053_validador.py`. No hay tests con obra de 3 cifras en el merge (grep).
- **Evals: ninguna afectada.** `obra_codigo` está a NO_COMPARAR en el banco y `comparar_obra` mide la
  salida de sv2, que no cambia.

## 6. Orden de despliegue

Design §6: sv4 → sv3; sv9 con F-053, desde un `dev` que ya tenga F-070. Cualquier orden es compatible
(sin DDL ni contrato de mensajes). Ojo: `dev` arrastra lo no desplegado de sv3 (F-062, F-063 y el
código de F-053 fases 1–2): comprobar el tag con `check_deploy.ps1` antes.

## 7. Conflictos con la rama de F-053 (v8: sv4 y sv9)

Design §7. Código: sin solape textual previsto (`validador_alta.py`, `review_repository.py`,
`ARCHITECTURE.md`); el test de sv9 de F-070 necesita una línea de adaptación al fusionar (firma con
`usu`). Seguros: `harness/features.json` (las dos añaden al final: F-069 y F-070), `BACKLOG.md` y
`progress/current.md`.

## 8. Preguntas abiertas para el humano

- **P1 · Obra `900` (Conservatorio Mariemma).** La regla la convierte en `0900`, que no existe en
  Sigrid. sv3 ya la trata así hoy; F-070 lo extiende a sv4 y sv9. **Recomendación: regla tal cual**
  (no tiene contratos ni proveedores: no entra por albaranes valorados). Si es obra viva, se añade
  `900` a `CODIGOS_OBRA_SIN_CERO` (una línea y un test).
- **P2 · Otros códigos no numéricos** (GG «gastos generales», GGD, CM «centro maquinaria», CP, OT,
  POSTV, BD…, `0578-B`): hoy sv3 los descarta como inválidos y F-070 no lo cambia. **Recomendación:
  solo VAR y POSTV2, como dijo el humano**; si llegan albaranes a otra, se amplía la constante.
- **P3 · Merges ya guardados con 3 cifras.** **Recomendación: no corregirlos.** sv4 los consulta bien
  (R10), los canoniza cuando el revisor guarda (R12) y sv9 da de alta con `0686` (R14). Si se quiere
  limpiar, medir antes con la T0 y hacerlo como ficha aparte con autorización expresa.

## 9. Propuestas para el líder (no dadas de alta)

- Ficha: el combo de partidas de sv4 (y `fetch_obra_by_codigo` de sv3) no filtran por empresa:
  VAR, POSTV2 y `0711` mezclan filas de la empresa 28 (regla R-CODIGO-POR-EMPRESA del datamart).
- `azure-apps/albaranes.md` lo actualiza la T11 de esta feature.

## Anexo A · consulta de la T0 (solo lectura, BBDD `albaranes` de Azure)

Con una sesión `default_transaction_read_only=on` (como `diag_f062.py`, que aborta si
`SHOW transaction_read_only` no da `on`):

```sql
SELECT m.id, m.obra_codigo, m.obra_codigo_origen, m.approved, m.created_at_utc,
       COALESCE(j #>> '{data,origen_datos,obra,motivo}',      j #>> '{origen_datos,obra,motivo}')      AS motivo,
       COALESCE(j #>> '{data,origen_datos,obra,validada}',    j #>> '{origen_datos,obra,validada}')    AS validada,
       COALESCE(j #>> '{data,origen_datos,obra,valor_correo}', j #>> '{origen_datos,obra,valor_correo}') AS valor_correo,
       COALESCE(j #>> '{data,origen_datos,obra,valor_papel}', j #>> '{origen_datos,obra,valor_papel}') AS valor_papel
FROM albaran_documents_merge m
CROSS JOIN LATERAL (SELECT m.raw_extraction_json::jsonb AS j) x
WHERE m.is_active AND m.obra_codigo ~ '^[0-9]{3}$'
ORDER BY m.created_at_utc DESC;
```

Criterio: `validada` nula con `motivo = correo_unico` confirma el camino «sin lista» del resolver de
sv2; `motivo` de papel (`correo_sin_dato`, `sin_correo`…) indica lectura del papel. Anotar los
recuentos aquí, sin datos de proveedor.

## PARADA 1 · APROBADA (humano, 2026-10-14)

- P1: regla tal cual; `900` ⇒ `0900`, sin excepción.
- P2: solo VAR y POSTV2 en `CODIGOS_OBRA_SIN_CERO`.
- P3: los merges ya guardados con 3 cifras no se corrigen.
- Implementación tras fusionar F-053 v8 (pasada 2) y pasarla a `blocked` por la T51 (máximo una `in_progress`).
- Fuera: el filtro por empresa del combo de partidas (propuesta del §9, sin ficha todavía).
