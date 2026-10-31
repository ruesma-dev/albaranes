<!-- progress/impl_F-115.md -->
# F-115 · informe del implementer

Al cambiar el proveedor (o la obra) se retira el contrato que no es del albarán, se rebusca y se revalora sin
regenerar las líneas. Rama `feature/F-115-cambio-proveedor-reinicia-contrato`, worktree `../albaranes-F-115`, `dev`
(`ba3542b`) fusionado en `15a8624`. Rigor `estandar`.

## T0 · medición en producción (líder, 2026-10-31, solo lectura con `default_transaction_read_only=on`)

- (1) No aprobados con `selected_contrato_codigo` cuyo contrato del documento es de otro CIF (normalizado): **0**
  (62 no aprobados, 49 con contrato elegido).
- (2) No aprobados valorados: 52; con la última valoración en un contrato distinto de la selección: **0 (0 %)**, por
  debajo del 5 % de D4 ⇒ D4 = (a) sin parar.

## Qué cambió

| Servicio | Fichero | Cambio |
|---|---|---|
| comun | `ruesma_comun/contratos/pertenencia.py` (nuevo), `contratos/__init__.py` | `contrato_es_del_albaran` (R1), reexportada |
| comun | `pyproject.toml`, `ruesma_comun/__init__.py`, `README.md` | **0.11.0** (sobre 0.10.0), fila de tabla y entrada de versión |
| sv3 | `domain/ports/contrato_merge_repository_port.py`, `infrastructure/database/sqlalchemy_albaran_repository.py` | `get_pertenencia_seleccion`, `clear_selected_contrato` (SQL crudo) |
| sv3 | `application/services/contrato_enrichment_service.py` | `_retirar_seleccion_ajena_safely` al empezar, antes de `sin_datos`/caché/Sigrid (R2–R5) |
| sv3 | `application/pipelines/persist_albaran_pipeline.py` | `_trigger_valuation_safely`: `force` y sin contrato ⇒ publica sin contrato aunque no haya importes (R7) |
| sv4 | `infrastructure/database/review_repository.py` | PUT: solo contratos del albarán, retira origen y nota (R9, R10); detalle filtrado y sin líneas de una selección ajena (R12); `_exigir_valoracion_del_contrato_vigente` en PUT-aprobar y `set_approved` (R13) |
| sv4 | `domain/models/alta_sigrid_models.py`, `interface_adapters/web/app.py` | `ValoracionDeOtroContratoError` ⇒ 409 (API) o aviso en el listado; aviso de R11 |
| sv4 | `domain/models/review_models.py`, `application/services/review_service.py`, `application/services/busqueda_contratos.py` | `contrato_retirado` (detalle del PUT y `ResultadoGuardado`), `cambio`, `cambio_de_cabecera`, `aviso_de_guardado` (R11); el rastro compara CIF con `normalizar_cif` de comun (R19) |
| sv4 | `static/app.js` | `_normCif`, `_normObra`, `avisoCambioCabecera`; `choose` confirma antes de tocar nada (R14, R15) |
| docs | `docs/ARCHITECTURE.md` | regla 26 nueva; regla 25 con R7 (R21) |
| azure-apps | `albaranes.md` | párrafo «El contrato elegido es del albarán», commit local `7c6081b` (sin push) |

Sin DDL, sin cambios de mensajes de cola, sv5/sv6/sv9/sv2 sin tocar.

## Decisiones de diseño y desviaciones (justificadas)

1. **`contrato_retirado` viaja en `DocumentDetailPayload`** (campo opcional, solo lo rellena el PUT con
   `model_copy`), en vez de cambiar el retorno de `update_document_y_transicion`: ese par
   `(detalle, paso_a_aprobado)` lo desempaquetan 10 ficheros de tests y 2 dobles. `ResultadoGuardado` lo lleva
   como pide el diseño.
2. **R11 con dos textos**: «Proveedor cambiado: …» y, si solo cambió la obra (mismo CIF que el rastro),
   «Obra cambiada: se ha quitado el contrato X y se buscan los contratos del mismo proveedor en la nueva obra;
   después se vuelve a valorar». Motivo: R15/D2 (el proveedor se conserva); decir «nuevo proveedor» sería falso.
3. **R19 exigió tocar `estado_busqueda`**: comparaba el CIF solo sin espacios (`b-123` ≠ `B123` ⇒ `desfasada` ⇒
   relanzaba). Ahora normaliza los dos lados con `normalizar_cif` de comun. Los tests de F-052 siguen en verde.
4. **Código sin ninguna fila**: el PUT lo descarta como hoy (no se puede saber) y no lo anuncia como retirado.
   sv3 no lo toca (R2: «no es ajena»).
5. **sv3 tolera repositorios sin `get_pertenencia_seleccion`** (no-op silencioso, como la canonización del
   nombre): los dobles de F-052/F-062/F-070 no lo tienen y si no cada test dejaría un `ERROR` en el log.
6. **R7 lee primero los importes y luego mira `force`** (`importes or force`): `test_f075_r3_…` exige que se
   lean con `force=True`; así no se relaja.
7. **R13 usa `ORDER BY v.id DESC LIMIT 1`** (diseño §7). Con `replace_valuation` de sv6 hay una valoración por
   documento; sv9 la lee con un JOIN sin orden.
8. **R20 · tests anteriores retocados (sin cambiar ninguna aserción)**:
   - `test_f106_cuadre.py::test_f106_t2_version_0100`: «== 0.10.0» ⇒ «≥ 0.10.0» (comun 0.11.0), como hicieron
     F-098 y F-113; la exacta la exige `test_f115_t2_version_0110`.
   - Fixtures `f053_sv4_bbdd.construir` y `f065_bbdd.construir`: el merge tiene seleccionado el contrato de su
     valoración (`CT/1`, `CTSU25/0359`); antes la selección era NULL con una valoración de contrato, justo lo
     que R13 rechaza. Constante `CABECERA` (CIF, obra, contrato) en los dos.
   - 6 llamadas de «guardar y aprobar» (`test_f053_t19_cerrojo`, `test_f053_t21b_valorado`,
     `test_f065_f1_cabecera` ×2, `test_f065_f2_pasada2`) mandan `**CABECERA`, como la ficha: el PUT guarda la
     cabecera entera y sin CIF ni contrato lo quitaba.
   - `test_f114_js.py`: el arnés saca también `_normCif`, `_normObra`, `avisoCambioCabecera` y define
     `DOC_DATA = {}` (sin contrato: no pregunta, como hoy).
   - Ningún test dependía de aceptar un contrato «compartido» de OTRO proveedor (R20).
9. **`DOC_DATA` no cambia**: ya lleva `selected_contrato_codigo`, `valuation` y `n_filas_manuales`
   (`document.model_dump()`).

## Fuera de alcance / pendiente

- **T13** (líder, Chrome con sv4 local y Azurite): sin hacer.
- **T16** (humano): desplegar **sv3 primero y luego sv4** (comun 0.11.0 en las dos imágenes).
- Fuera por diseño §8: contrato del proveedor nuevo sin líneas (SKIP M1); borrar contratos huérfanos.
- Junction `.venv` de sv4 en el worktree: quitarla con `cmd /c rmdir` antes de `git worktree remove`.
- `azure-apps` `7c6081b` local sin push.

## Fase RED

### T1 · comun (R1)

```
$ PYTHONPATH=<worktree>\services\albaranes-comun python -m pytest tests/test_f115_pertenencia.py -q --tb=short
tests\test_f115_pertenencia.py:13: in <module>
    from ruesma_comun.contratos import contrato_es_del_albaran as reexportada
E   ImportError: cannot import name 'contrato_es_del_albaran' from 'ruesma_comun.contratos'
ERROR tests/test_f115_pertenencia.py
1 error in 1.93s
```

### T3 · sv3, selección ajena (R2–R6, R8)

```
$ cd services/albaranes-persistencia; PYTHONPATH=<worktree comun> python -m pytest tests/test_f115_seleccion_ajena.py -q --tb=line
...test_f115_seleccion_ajena.py:359: AttributeError: 'SqlAlchemyAlbaranRepository' object has no attribute 'get_pertenencia_seleccion'
E   AttributeError: type object 'ContratoMergeRepository' has no attribute 'get_pertenencia_seleccion'
...test_f115_seleccion_ajena.py:435: AssertionError: assert 'clear_selected_contrato' in {'get_existing_pdf_paths', ...}
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r2_r6_a_proveedor_b_sin_contratos_deja_la_seleccion_nula
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r6_b_proveedor_b_con_dos_sin_eleccion_deja_nula
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r4_d_sigrid_en_error_deja_nula
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r4_sin_datos_tambien_retira[None-0686]
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r5_fallo_al_leer_la_pertenencia_se_registra_y_sigue
(... 19 en total)
19 failed, 6 passed in 14.38s
```
Los 6 que pasan son los casos que NO deben retirar (e, f, sin filas, sin selección, apagado, fila del albarán):
fijan que la regla nueva no se pasa de frenada.

### T5 · sv3, disparo con `force` (R7)

```
$ cd services/albaranes-persistencia; PYTHONPATH=<worktree comun> python -m pytest tests/test_f115_disparo_force.py tests/test_f075_disparo.py -q --tb=line
...test_f115_disparo_force.py:51: AssertionError: assert [] == [('doc-f115-d..., None, True)]
FAILED tests/test_f115_disparo_force.py::test_f115_r7_a_force_sin_contrato_sin_importes_publica_sin_contrato[sin_lineas]
FAILED tests/test_f115_disparo_force.py::test_f115_r7_a_force_sin_contrato_sin_importes_publica_sin_contrato[sin_importes]
2 failed, 13 passed in 1.92s
```
`test_f075_disparo.py` en verde en la misma pasada.

### T7 · sv4, el PUT retira el contrato ajeno (R9–R11, R18, R19)

```
$ cd services/albaranes-front; PYTHONPATH=<worktree comun> .venv/Scripts/python.exe -m pytest tests/test_f115_guardar_retira_contrato.py -q --tb=line
E   AssertionError: assert ('CTA/0001', 'auto_multiple') == (None, None)
E   AssertionError: assert 'CTA/0001' is None
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'contrato_retirado'
...test_f115_guardar_retira_contrato.py:172: AssertionError: assert not True      (R19: b-/ES relanzaban)
E   TypeError: aviso_de_guardado() got an unexpected keyword argument 'contrato_retirado'
E   AttributeError: 'ResultadoGuardado' object has no attribute 'contrato_retirado'
17 failed, 6 passed in 1.71s
```
Pasan ya: R18 (aprobado y alta bloqueante: 409 sin tocar, como hoy), la fila legada y el R19 con espacios.

### T9 · sv4, detalle filtrado y aprobar con otro contrato (R12, R13)

```
$ cd services/albaranes-front; PYTHONPATH=<worktree comun> .venv/Scripts/python.exe -m pytest tests/test_f115_detalle_y_aprobar.py -q --tb=line
E   AssertionError: assert ['CTA/0001', ...', 'CTX/0700'] == ['CTSU25/0359']
E   AssertionError: assert [ContratoLine...producto='X')] == []
E   AssertionError: assert [ContratoPayl...web_url=None)] == []
E   ImportError: cannot import name 'ValoracionDeOtroContratoError' from 'domain.models.alta_sigrid_models'
(... 9 failed, 5 passed)
```

### T11 · JS de la ficha, confirmación (R14, R15)

```
$ cd services/albaranes-front; .venv/Scripts/python.exe -m pytest tests/test_f115_js_confirmacion.py -q --tb=line
E   ValueError: substring not found        (x18: `function avisoCambioCabecera(` no existe en app.js)
18 failed in 0.23s
```
