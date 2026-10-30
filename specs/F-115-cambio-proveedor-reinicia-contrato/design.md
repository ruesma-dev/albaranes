# F-115 · Cambiar el proveedor reinicia contrato y valoración — diseño (v1)

## 1. Alcance y límite de servicio

comun (una función pura), sv3 (enriquecimiento de contratos y disparo de la valoración) y sv4 (PUT de cabecera,
detalle, aprobación y `app.js`). Ninguna responsabilidad nueva: cada pieza ya es de quien la toca (sv3 busca y
selecciona contratos; sv4 guarda la cabecera y aprueba; sv6 reemplaza la valoración). Sin DDL, sin cambio de
`MensajePersistencia` ni `MensajeValoracion`, sin sigrid-api. sv5, sv6 y sv9 no cambian: la conservación de lo editado
al revalorar es de F-106 fase B (dependencia, D5).

## 2. Qué pasa hoy (leído en el código, rama `dev` a 2026-10-30)

1. **Elegir proveedor** (`services/albaranes-front/static/app.js:2117-2136`, `choose`): rellena CIF y nombre y
   auto-guarda con `sendSave(false)` ⇒ `PUT /api/documents/{id}?buscar_si_cambia=1` con
   `selected_contrato_codigo` = el que está en pantalla (el del proveedor anterior), sin confirmación.
2. **PUT** (`infrastructure/database/review_repository.py:4025-4140`, `update_document_y_transicion`): guarda
   `proveedor_cif`; acepta el código propuesto si es del documento **o existe en cualquier documento** («contrato
   compartido», `:4070-4100`), sin mirar el proveedor ⇒ la selección del anterior se conserva.
3. **Re-búsqueda** (`application/services/review_service.py:296-335`): el CIF ya no es el del rastro (`desfasada`,
   F-052 D4-A) ⇒ `ColasRefetchClient` publica `MensajePersistencia(force=True)` en `q-persistencia`.
4. **sv3** (`services/albaranes-persistencia/interface_adapters/worker/persistence_worker.py:79-95`): sin blob ⇒
   `reenrich_by_merge_id` (`application/pipelines/persist_albaran_pipeline.py:425-480`): resolver de cabecera,
   obra, guardas, contratos con `force`, valoración con `force`. **No toca líneas ni llama a IA1/IA2** ⇒ la regla del
   humano («sin regenerar líneas») ya se cumple en esa vía.
5. **Contratos** (`application/services/contrato_enrichment_service.py:106-560`): `upsert_contratos` no borra los del
   anterior (`sqlalchemy_albaran_repository.py:1270-1300`, decisión documentada); la auto-selección solo escribe con
   1 contrato o con elección del selector (`:470-505`). Con 0, varios sin elección o error de Sigrid, **la selección
   del anterior se queda**.
6. **Valoración** (`persist_albaran_pipeline.py:603-685`): `has_selected_contrato_with_lines` encuentra el contrato
   del anterior (sus filas siguen en el documento) ⇒ publica `q-valoracion` con ese código; sv5 lee también la
   selección del merge (F-075 M1). Sin selección y sin importes, SKIP ⇒ la valoración del anterior sobrevive.
7. **sv9** da de alta con `albaran_valuations.contrato_codigo` (`sql_alta_repository.py:87`) ⇒ contrato del anterior
   con CIF del nuevo: Sigrid lo rechaza (fallo visible).
8. **Aprobado / alta bloqueante**: el PUT ya responde 409 (`_exigir_editable`, F-065 R4, F-053 R25/R26) y la ficha
   sale en solo lectura. Nada nuevo que hacer salvo fijarlo con test (R18).
9. **Lo editado a mano**: vive en `albaran_line_valuations` y hoy se pierde al revalorar; F-106 fase B (en curso,
   `../albaranes-F-106`, T16–T18 hechas) lo conserva en `replace_valuation` por cualquier vía, también la de sv3 con
   `force`, y ya trata «contrato cambiado» (su R27). Por eso F-115 no toca sv6.

## 3. Enfoque

Una sola regla, «la selección debe ser un contrato del albarán» (R1), aplicada en tres puntos, más un disparo:

- **sv4, PUT** (R9–R10): coherencia inmediata en la ficha y en BBDD aunque la cola falle.
- **sv3, al empezar el enriquecimiento** (R2–R5): red para las vías que no pasan por el PUT (corrección automática de
  F-062, HTTP de `contrato_refetch_service`, duplicados) y para mensajes viejos en cola.
- **sv4, detalle** (R12): el desplegable no ofrece contratos del anterior (sus filas siguen en BBDD, D6).
- **sv3, disparo** (R7): con `force` y sin selección siempre se revalora sin contrato, para que sv6 sustituya la
  valoración del anterior (y F-106 reaplique lo editado).
- **sv4, aprobar** (R13, D4): defensa final; no se aprueba una valoración de otro contrato.

## 4. Ficheros a crear

| Fichero | Contenido |
|---|---|
| `services/albaranes-comun/ruesma_comun/contratos/pertenencia.py` | `contrato_es_del_albaran` (R1). |
| `services/albaranes-comun/tests/test_f115_pertenencia.py` | R1 (formatos de CIF y obra, legado, albarán vacío). |
| `services/albaranes-persistencia/tests/test_f115_seleccion_ajena.py` | R2–R6, R8 con dobles (`f062_dobles.py`) y SQLite. |
| `services/albaranes-persistencia/tests/test_f115_disparo_force.py` | R7 (junto a los de F-075, mismo `_Repo`). |
| `services/albaranes-front/tests/test_f115_guardar_retira_contrato.py` | R9–R11, R18, R19 (SQLite en memoria, fakes). |
| `services/albaranes-front/tests/test_f115_detalle_y_aprobar.py` | R12, R13. |
| `services/albaranes-front/tests/test_f115_js_confirmacion.py` | R14, R15 (mismo arnés de extracción de funciones JS que `test_f065_f1_js.py`). |

## 5. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/contratos/__init__.py` | exporta `contrato_es_del_albaran`. |
| `services/albaranes-comun/pyproject.toml` y `ruesma_comun/__init__.py` | versión menor +1 sobre la que haya en `dev` (0.9.0 hoy; F-106 puede subirla). |
| `services/albaranes-persistencia/domain/ports/contrato_merge_repository_port.py` | `get_pertenencia_seleccion`, `clear_selected_contrato`. |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | implementación de los dos (§7). |
| `services/albaranes-persistencia/application/services/contrato_enrichment_service.py` | `_retirar_seleccion_ajena_safely` al empezar, tras leer CIF y obra y antes de la rama `sin_datos` (R2–R5). |
| `services/albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py` | `_trigger_valuation_safely`: con `force` y sin código, publica `None` sin mirar importes (R7). |
| `services/albaranes-front/infrastructure/database/review_repository.py` | PUT (R9–R10), detalle (R12), aprobar en PUT y `set_approved` (R13). |
| `services/albaranes-front/application/services/review_service.py` / `busqueda_contratos.py` | `ResultadoGuardado` lleva `contrato_retirado`; `aviso_de_guardado` compone R11. |
| `services/albaranes-front/interface_adapters/web/app.py` | 409 de la nueva excepción (junto a `AlbaranSinValorarError`, `:1869`); `DOC_DATA` con `selected_contrato_codigo` y `tiene_valoracion` si no están. |
| `services/albaranes-front/static/app.js` | `choose` de los combos proveedor/obra: `avisoCambioCabecera(kind, previo, nuevo, doc)` y restaurar al cancelar (R14–R15). |
| `docs/ARCHITECTURE.md` | regla 26 nueva; regla 25 con R7 (R21). |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` | revisar; commit local propio si cambia (R21). |

## 6. Ficheros que NO se tocan

- `services/albaran-valoracion-persist/**` (sv6) y su `replace_valuation`: la conservación es de F-106.
- `services/albaran-valoracion-api/**` (sv5): ya da `no_contract` sin selección en el merge.
- `services/albaranes-alta-sigrid/**` (sv9) y `ruesma_comun.alta_sigrid`: usan la valoración, que ya será la buena.
- `ruesma_comun/colas/mensajes.py`: ni campos nuevos ni `force` distinto.
- `upsert_contratos` y su «no borrar» (D6); `contrato_selector.elegir_contrato_probable`; la caché `contratos_cache`.
- `header_resolver_service` (F-062/F-073): sigue sin pisar un CIF `manual`.
- `infrastructure/sigrid/local_refetch_client.py` y `replace_contratos_and_select` de sv4 (solo-front local: ya
  borran y reseleccionan, `review_repository.py:3940-4010`).
- Las líneas: `albaran_lines_merge` y todo lo de sv2.

## 7. Funciones

**comun** (sin dependencias, dominio):
```
def contrato_es_del_albaran(*, contrato_cif: str | None, contrato_obra: str | None,
                            albaran_cif: str | None, albaran_obra: str | None) -> bool
```
`normalizar_cif` a ambos CIF y `canonizar_codigo_obra` a ambas obras; albarán sin CIF o sin obra ⇒ `False`; contrato
sin CIF (o sin obra) ⇒ ese lado no descalifica.

**sv3 · puerto y repositorio** (infrastructure, SQL crudo como el resto del repositorio):
- `get_pertenencia_seleccion(*, document_id) -> tuple[str | None, list[tuple[str | None, str | None]]]`: el código
  seleccionado y los `(cif_proveedor, codigo_obra)` de sus filas: `SELECT … FROM albaran_contratos_merge WHERE
  document_id = :d AND codigo_contrato = :c`; si no hay ninguna, las de ese código en cualquier documento (`LIMIT 20`),
  igual que el detalle de sv4.
- `clear_selected_contrato(*, document_id) -> None`: `UPDATE albaran_documents_merge SET selected_contrato_codigo =
  NULL, selected_contrato_origen = NULL WHERE id = :d` (si la columna de origen no existe, solo el código, como
  `set_selected_contrato`).

**sv3 · servicio** (application): `_retirar_seleccion_ajena_safely(merge_document_id, cif_raw, obra_raw) -> str |
None` devuelve el código retirado. Ajena = hay filas y ninguna cumple R1. Retira con `clear_selected_contrato` y
`remove_review_note_prefix(prefijo=f"[AVISO] Contrato {codigo} elegido")`. Todo dentro de `try/except` con
`logger.exception` (R5). Con el enriquecimiento apagado (`_enabled = False`) no se llama: no se busca ni se toca nada.

**sv3 · disparo**: en `_trigger_valuation_safely`, rama `not has_lines`: `if codigo: SKIP (M1)`; `elif force: codigo =
None` y publica; `elif not trae_importes: SKIP`; resto igual.

**sv4 · repositorio**: helper `_es_del_albaran_in_session(session, document_id, codigo, cif, obra) -> bool | None`
(`None` = sin filas, no se sabe ⇒ se acepta como hoy). En el PUT, el código propuesto se acepta solo si no es `False`;
si se retira, `selected_contrato_origen = None`, se filtran las notas (R10) y el resultado lo dice
(`contrato_retirado`). El detalle filtra `contratos_orm` con R1 y no carga líneas de una selección ajena (R12).
`_exigir_valoracion_del_contrato_vigente(session, document_id)` lee `v.contrato_codigo` de la valoración vigente
(`ORDER BY v.id DESC LIMIT 1`) y lanza `ValoracionDeOtroContratoError` (`domain/models/alta_sigrid_models.py`, junto a `AlbaranSinValorarError`) si difiere de
la selección (R13); sin valoración no lanza (lo cubre ya R37 de F-053).

**sv4 · JS**: `avisoCambioCabecera(kind, previo, nuevo, doc) -> string | null` pura (testeable): `null` si el valor
normalizado no cambia o no hay contrato ni valoración; si no, el texto de R14/R15. `choose` la llama antes de
`sendSave`; al cancelar, repone `vEl`, `nEl`, `input.value` y `combo.dataset.label` previos.

**SQL**: ninguno nuevo de esquema. Solo las sentencias de lectura/actualización de arriba, sobre columnas existentes
(`albaran_contratos_merge.cif_proveedor`, `.codigo_obra`, `albaran_documents_merge.selected_contrato_*`,
`albaran_valuations.contrato_codigo`). Lectores acoplados: sv5 lee `selected_contrato_codigo` (pasará a NULL, que ya
soporta); sv9 no lee la selección.

## 8. Riesgos y decisiones (PARADA 1)

**PARADA 1 cerrada por el humano el 2026-10-30**: D1 y D3 a D7 = (a). D2 = (a) con una precisión: «al cambiar la obra se puede dejar el proveedor, pero hay que cambiar el contrato» (el proveedor se conserva; el contrato de la obra anterior se quita y se buscan los del mismo proveedor en la obra nueva; R15).

- **D1 · Dónde se retira la selección.** (a) **Recomendada: en sv4 (PUT) y en sv3 (al enriquecer)**: el PUT deja la
  ficha coherente al instante y sobrevive a un fallo de la cola; sv3 cubre las vías sin PUT (F-062, HTTP, duplicado).
  (b) Solo sv3: entre el PUT y el worker la ficha enseña el contrato del anterior con el proveedor nuevo, y si la
  publicación falla se queda así. (c) Solo sv4: la corrección automática de F-062 seguiría arrastrando el contrato.
- **D2 · ¿También al cambiar la obra?** (a) **Recomendada: sí**, es el mismo defecto por la misma vía (contrato de la
  obra anterior) y la misma regla lo cubre sin coste. Riesgo: un `codigo_obra` de contrato con formato raro; por eso se
  compara con `canonizar_codigo_obra` y una fila sin obra no descalifica. (b) Solo proveedor (literal de la petición).
- **D3 · Confirmación al elegir proveedor.** (a) **Recomendada: sí, con el texto de R14**, solo si hay contrato o
  valoración; hoy el combo auto-guarda sin preguntar y el cambio rehace la valoración. (b) Sin confirmación, solo el
  aviso tras guardar (R11).
- **D4 · Bloquear la aprobación con la valoración de otro contrato (R13).** (a) **Recomendada: sí**: entre el cambio
  y el fin de la revaloración (cola + IA, minutos) «Guardar y aprobar» mandaría a sv9 el contrato del anterior.
  Riesgo: documentos en producción con valoración y selección distintas por otros motivos quedarían sin poder aprobar
  hasta revalorar; se mide en la T0 (solo lectura). (b) No: se confía en que la revaloración llegue antes.
- **D5 · Orden y dependencia.** (a) **Recomendada: detrás de F-106 en `dev` (y de F-114)**: sin la fase B de F-106,
  revalorar pierde lo editado y la regla del humano no se cumpliría. (b) Antes de F-106: la confirmación de R14 diría
  «se pierden las N líneas puestas a mano» y R16 se retira.
- **D6 · Contratos del proveedor anterior en `albaran_contratos_merge`.** (a) **Recomendada: se conservan y se ocultan**
  (R12): borrarlos pone a NULL (FK `ON DELETE SET NULL`) los vínculos de las filas antes de que sv6 reaplique lo
  editado, y rompe la decisión documentada de «upsert nunca borra». (b) Borrarlos en sv3 al cambiar el CIF.
- **D7 · Alcance de R7.** (a) **Recomendada: `force` y sin selección ⇒ siempre se revalora sin contrato.** `force` solo
  llega de una acción humana en sv4; una valoración debe reflejar la selección vigente. Efecto lateral: «Solo volver a
  buscar» sin contrato elegido y sin importes deja una cabecera `no_contract` (no cuenta como valorado). (b) Solo
  cuando esa pasada de sv3 retiró la selección: no cubre el caso normal, en que la retiró antes el PUT (D1 a).
- **Fuera**: contrato seleccionado del proveedor nuevo **sin líneas** (M1 de F-075, SKIP como hoy; se anota); varios
  revisores a la vez (regla 5); borrar contratos huérfanos; cambiar el selector determinista.
- **Riesgo de solape**: F-114 también toca el combo de proveedor de `app.js`; F-115 se implementa sobre F-114 en `dev`.
