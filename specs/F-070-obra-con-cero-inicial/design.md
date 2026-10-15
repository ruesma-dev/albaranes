# F-070 · La obra siempre con el 0 inicial (salvo VAR y POSTV2) — diseño

Requisitos: `requirements.md`. Diagnóstico completo y mediciones en Sigrid: `progress/spec_F-070.md`.

## 1. Por dónde entra la obra sin el 0 (diagnóstico de código)

| Camino | Qué hace hoy | ¿Escribe `obra_codigo`? |
|---|---|---|
| sv2 · `origen_datos_resolver._resolver_obra` (F-048) | Con lista de obras, el código del correo se escribe COMO FIGURA EN LA LISTA (`686` ⇒ `0686`). **Sin lista** (sigrid-api caído, `validada = null`) o en la fila «confirma papel» sin lista, deja lo que leyó IA1 (`686`). | En el envelope |
| sv2 · papel (`cabecera.obra_codigo` de IA1/IA2) | Si el correo no aporta, queda lo leído en el papel, sin normalizar. | En el envelope |
| sv3 · `AlbaranNormalizer.normalize_header` | `normalize_identifier`: colapsa espacios y pasa a mayúsculas. **No pone el 0.** | **Sí: aquí se sella el merge** (`sqlalchemy_albaran_repository.py`, `obra_codigo=cabecera.obra_codigo` al construir merge y crudas) |
| sv3 · `HeaderResolverService._resolve_obra` | Solo si el código no es válido: deduce por texto y devuelve `con.cod` de Sigrid tal cual. | Sí (`update_merge_resolved_header`) |
| sv3 · `ObraEnrichmentService` | Consulta Sigrid con `normalizar_codigo_obra` (`0686`), la encuentra y escribe nombre y dirección, **pero deja `obra_codigo = "686"`**. Con `VAR`/`POSTV2` (hoy `None`) **descarta la obra** (`obra_codigo_invalido:VAR`, red R6 de F-002). | Solo `NULL` al descartar |
| sv4 · `review_repository.update_document_y_transicion` | Guarda `payload.obra_codigo` recortado. | Sí |
| sv4 · `SigridLookupClient` (proveedores, contratos, partidas) | Manda `codigo_obra` recortado: con `686`, 0 filas. | No |
| sv9 · `validador_alta.validar_y_construir` | `cod_obra = _texto(cab.obra_codigo)`: mandaría `686`. | No (petición) |

Conclusión: el `686` llega al merge porque **sv3 sella la cabecera sin canonizar** (venga del correo
sin lista o del papel) y nadie lo corrige después: sv3 normaliza solo para consultar. El arreglo va
en el punto donde se sella (sv3) y, para lo ya guardado, en los que consumen (sv4 y sv9). Qué camino
exacto tomaron los 5 pendientes (`motivo` y `validada` de `origen_datos`) lo dice la T0, solo
lectura; el arreglo no depende de la respuesta.

## 2. Ficheros a crear

- `services/albaranes-comun/tests/test_f070_codigo_obra.py` — R1–R5.
- `services/albaranes-persistencia/tests/test_f070_obra_canonica.py` — R6–R9.
- `services/albaranes-front/tests/test_f070_obra_canonica.py` — R10–R13.
- `services/albaranes-alta-sigrid/tests/test_f070_cod_obra.py` — R14–R15.

## 3. Ficheros a modificar

**comun** — `services/albaranes-comun/ruesma_comun/obras/codigo.py` y `obras/__init__.py`:

```python
#: Códigos de obra válidos SIN el 0 inicial (regla del humano, F-070). Único sitio.
CODIGOS_OBRA_SIN_CERO: frozenset[str] = frozenset({"VAR", "POSTV2"})

def normalizar_codigo_obra(valor: str | None) -> str | None:
    """Canónico o None (R1–R3). Nuevo: si limpio.upper() está en CODIGOS_OBRA_SIN_CERO,
    devuelve limpio.upper(); el resto, igual que hoy."""

def canonizar_codigo_obra(valor: str | None) -> str | None:
    """R4: normalizar_codigo_obra(valor) o, si es None, str(valor).strip() or None."""
```

`__init__` exporta las tres. El docstring del módulo añade F-070 y la diferencia con
`origen_datos.normalizar_codigo` (comparación, sin ceros), que NO cambia.

**sv3** (capa application):
- `application/services/albaran_normalizer.py` — en `normalize_header`, `"obra_codigo":
  self.normalize_obra_codigo(header.obra_codigo)`; nuevo `@staticmethod normalize_obra_codigo(value)
  = canonizar_codigo_obra(normalize_identifier(value))` (R6). Como `_normalize` del pipeline lo
  aplica a `data` y a cada proveedor ANTES de `repository.save`, merge y crudas salen canónicas.
- `application/services/header_resolver_service.py` — `_resolve_obra` devuelve
  `canonizar_codigo_obra(best.codigo_obra)` en vez de `(best.codigo_obra or "").strip() or None` (R7).
- R8 no toca código de sv3: `ObraEnrichmentService`, `HeaderGroundingService`, `_resolve_obra` (su
  guarda «la IA ya trajo un código válido»), `ContratoEnrichmentService` y `ContratoRefetchService`
  ya llaman a `normalizar_codigo_obra` y heredan VAR/POSTV2. Los tests lo fijan.

**sv4**:
- `infrastructure/sigrid/sigrid_lookup_client.py` — en `fetch_proveedores_por_obra`,
  `fetch_contratos` y `fetch_partidas_por_obra`, `codigo = canonizar_codigo_obra(codigo_obra)` en vez
  de `(codigo_obra or "").strip()`; `if not codigo: return []` se queda (R10, R11). Los endpoints de
  `app.py` no cambian: el cliente es el único punto de sv4 que habla con sigrid-api por obra.
- `infrastructure/database/review_repository.py` — en `update_document_y_transicion`,
  `document.obra_codigo = canonizar_codigo_obra(self._clean_text(payload.obra_codigo))` (R12), e
  import en el bloque `ruesma_comun` (líneas 25–27).
- R13 no toca código: `busqueda_contratos.estado_busqueda` ya usa `normalizar_codigo_obra`.

**sv9** (capa domain, que ya importa `ruesma_comun`):
- `domain/services/validador_alta.py` — función privada `_cod_obra(cab) -> str` =
  `canonizar_codigo_obra(cab.obra_codigo) or ""`, usada en `_motivos_cabecera` (en lugar de
  `_texto(cab.obra_codigo)`, R15) y en `PeticionAlbaran(cod_obra=_cod_obra(cab), ...)` (R14). No se
  toca el docstring del módulo (líneas 1–28): F-053 v8 lo edita (ver §7).

**docs**:
- `docs/ARCHITECTURE.md` — regla nueva **21. El código de obra es canónico** (tras la 20): regla del
  humano, `ruesma_comun.obras` como único punto, dónde se aplica (sv3 al sellar, sv4 al consultar y
  guardar, sv9 al dar de alta), qué no cambia (sv2 y su forma de comparación) y que los merges viejos
  no se migran. En «Infra y despliegue», la excepción pasa a «`ruesma_comun.sigrid` y
  `ruesma_comun.obras` los importan sv3, sv4 y sv9» con el orden de §6.
- `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` — junto a la lista de columnas del merge
  (§ «albaran_documents_merge»), una línea: `obra_codigo` canónico desde F-070. Commit propio en
  ese repositorio (regla de mantenimiento de `azure-apps`).

## 4. Ficheros que NO se tocan

- sv2 entero: `origen_datos_resolver.py`, `albaran_extraction_service.obras_conocidas`, prompts y
  `ruesma_comun.contratos.origen_datos.normalizar_codigo` (forma de COMPARACIÓN de F-048: `0686` y `686`
  ya cuentan igual). Canonizar ahí obligaría a reconstruir sv2 y a cambiar tests de F-048 sin ganar
  nada: sv3 sella después. Las evals no cambian (`obra_codigo` está a NO_COMPARAR y se mide en sv2).
- `ObraEnrichmentService` y `update_merge_obra_fields`: no reescriben `obra_codigo` de merges viejos
  (R9). Descartado que la red «arregle» el código al validarlo: sería una migración encubierta en cada
  reproceso, justo lo que el humano pidió no hacer sin decidirlo (P3 de `progress/spec_F-070.md`).
- Las SQL de Sigrid (sv3, sv4, sv9): mismos `WHERE con_obr.cod = ?`. El combo de partidas no filtra
  por empresa (VAR y POSTV2 traen 1 y 6 partidas de la empresa 28): **anterior a F-070**, ya pasa hoy
  con `VAR` tal cual. Propuesto como ficha aparte en el informe.
- `app.py` de sv4, `app.js`, plantillas, `sv4.md`, `sv9.md`, `sql_alta_repository.py` de sv9, sv1,
  sv5, sv6, `infra/`. Sin DDL.

## 5. Qué cambia en sv3 con VAR y POSTV2 válidos (pedido por el líder)

Hoy `normalizar_codigo_obra("VAR")` es `None`, y eso tiene tres efectos en sv3 que desaparecen:

1. **Red de obra** (`ObraEnrichmentService`, R6 de F-002): con `RED_OBRA_ENABLED` el merge con `VAR`
   pierde la obra (`obra_codigo = NULL`) y va a revisión con `obra_codigo_invalido:VAR`. Con F-070
   consulta Sigrid con `VAR` (2 filas: empresas 1 y 28, mismo nombre «OBRAS VARIAS»; con POSTV2,
   «POSTVENTA 2» y «POSTVENTA») y rellena nombre y dirección con la más rica (regla de hoy de
   `sigrid_api_obra_client`, que no filtra empresa; igual que con `0711`, duplicada en 1 y 28).
2. **Resolver de cabecera**: hoy trata `VAR` como «sin obra» y la sustituye por una deducida por texto
   (origen `deterministic`). Con F-070 la respeta y la usa como obra efectiva para resolver el
   proveedor dentro de la obra.
3. **Búsqueda de contratos**: hoy no busca (falta obra), deja `[ACCION REQUERIDA]` y sella
   `sin_datos`. Con F-070 busca contratos de `VAR` (24 en Sigrid, empresa 1) y sella `VAR`. En sv4,
   un rastro viejo `sin_datos` con obra nula frente al merge `VAR` sale «desfasada» y «Guardar» relanza
   la búsqueda (D4-A de F-052): es lo correcto.

## 6. Orden de despliegue (lo pide y lo lanza el humano)

Tocar `ruesma_comun.obras` solo cambia el comportamiento de quien lo importa: **sv3, sv4 y sv9**
(sv2, sv5 y sv6 llevan comun horneado, pero no importan `obras`: no hace falta reconstruirlas). Sin
DDL ni contrato de mensajes: **cualquier orden es compatible** (sv4 nuevo con sv3 viejo canoniza al
consultar; sv3 nuevo con sv4 viejo guarda `0686`, que el viejo ya sabe usar). Recomendado:

1. **sv4** primero: arregla en el acto los combos de los 5 pendientes (`.\deploy.ps1 -Only sv4`,
   `.\check_deploy.ps1`).
2. **sv3**: los albaranes nuevos entran canónicos y VAR/POSTV2 dejan de descartarse.
3. **sv9**: no está desplegado; sale con F-053, que debe desplegarse desde un `dev` que ya contenga
   F-070. Si F-053 llegara antes a producción, sv9 manda `686` y Sigrid lo rechaza (obra no encontrada,
   `no_admitido`, sin escribir).

Antes de desplegar sv3 desde `dev`, mirar con `check_deploy.ps1` qué tag lleva: `dev` arrastra lo no
desplegado (F-062/F-063 pendientes de despliegue de sv3 según `progress/current.md`, y el código de
F-053 fases 1–2). Rollback: tag anterior; no hay datos que deshacer (un merge ya guardado como `0686`
funciona con el código viejo).

## 7. Coordinación con F-053 (rama `feature/F-053-alta-sigrid`, v8 en review)

F-070 parte de `dev` (sv9 de F-053 fases 1–2). Diff de v8 contra `dev` revisado el 2026-10-14:

- `validador_alta.py` (sv9): v8 cambia el docstring (líneas 13–18), `ConfigAlta` (sin `usu`), añade
  `normalizar_referencia` tras `normalizar_cif` y la firma `validar_y_construir(datos, config, hoy, usu)`
  con `usu=usu`. F-070 toca el import, `_motivos_cabecera` y la línea `cod_obra=`: separados de los
  hunks de v8 por líneas sin cambios ⇒ fusión automática esperable; revisarla igualmente.
- **Test de sv9 de F-070**: llama a `validar_y_construir` desde UN helper local `_validar(d)`. Quien
  fusione segundo lo adapta en una línea (`CONFIG` sin `usu` y `USU` de `tests/f053_datos.py`).
- `review_repository.py` (sv4): v8 cambia una SQL (~l. 188) y el mapeo del alta (~l. 4194); F-070 el
  import (l. 25–27) y ~l. 3863. Sin solape. `sigrid_lookup_client.py`: v8 no lo toca.
- `docs/ARCHITECTURE.md`: v8 añade 5 líneas a la regla 19; F-070 añade la 21 y edita «Infra y
  despliegue» (la excepción de comun, que v8 no toca). Sin solape.
- **Conflictos seguros, a mano**: `harness/features.json` (v8 añade F-069 al final; F-070 también
  añade al final: quedarse con las dos), `BACKLOG.md` (regenerarlo con `init.sh`) y
  `progress/current.md`.

## 8. Riesgos y decisiones

- **Obra `900` de Sigrid** (empresa 1, «Conservatorio Mariemma», 374 partidas, 0 contratos, sin
  `0900`): la regla la convierte en `0900`, que no existe. sv3 ya la trata así hoy; F-070 lo extiende
  a sv4 y sv9. Pregunta P1 del informe (recomendación: regla tal cual; si es obra viva, una línea en
  `CODIGOS_OBRA_SIN_CERO`).
- **Otros códigos no numéricos** de Sigrid (GG, CM, CP, OT, POSTV, BD…, `0578-B`): siguen sin ser
  canónicos (R3); sv4 y sv9 los mandan tal cual y sv3 los sigue descartando. P2 del informe.
- **Mayúsculas**: VAR/POSTV2 se devuelven en mayúsculas; SQL Server compara sin distinguirlas
  (`var` = `VAR` en la prueba del 2026-10-14), pero el merge y el alta deben llevar la forma de Sigrid.
- **Descartado**: canonizar en sv2 (§4), en el endpoint de sv4 en vez del cliente (dos sitios por
  consulta) y en `sql_alta_repository.leer_datos` de sv9 (la regla de qué se manda a Sigrid es del
  validador, capa domain, y es puro).
- **Rigor `critico`**: fase RED de cada tarea en `progress/impl_F-070.md`, cobertura ≥ 80 % de lo
  cambiado y campaña de mutación completa con 0 supervivientes sin test o justificación aceptada.
