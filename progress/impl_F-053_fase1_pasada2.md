<!-- progress/impl_F-053_fase1_pasada2.md -->
# Implementación F-053 · fase 1 · pasada 2 (implementer, 2026-10-06)

Corrige `progress/review_F-053_fase1.md` (CHANGES_REQUESTED: H1, H2, H3 y O1) y aplica las decisiones del humano
D1 y D2 (2026-10-06). Rama `feature/F-053-alta-sigrid`, worktree `../albaranes-F-053`, rigor `critico`. Un commit por
punto, sin push. Nada contra sigrid-api, Azure, SharePoint ni BBDD reales; sigrid-api leído en solo lectura
(`git show 13fd99d:...`), sin editar nada allí. Entorno: `.venv` del árbol principal y `PYTHONPATH` a la comun del
worktree (comprobado: `ruesma_comun` se importa de `albaranes-F-053\services\albaranes-comun`).

## 1. Qué cambió (commit → punto)

| Commit | Punto | Cambio |
|---|---|---|
| `e7b9c3e` | H1 (R35) | `main_worker.motivos_configuracion(exc)`: el `ValidationError` de `Settings` se registra solo con `loc` y `msg` (`errors(include_input=False, include_url=False)`). El motivo de R44 sigue en el log |
| `2cd170f` | H2 (R22) | El adjunto guarda `grafico.ide_negocio`; tests de `concepto-grafico` con la forma real de `AttachConceptoGraficoResponse` |
| `5216113` | H3 | `"branch": "feature/F-053-alta-sigrid"` en F-053; `BACKLOG.md` regenerado |
| `79906d8` | O1 | `visibilidad_s` de `q-feedback` = peor caso + 300 s, redondeado al minuto (1740 s con los defectos); en el log de arranque y en `sv9.md` |
| `4a6721f` | D1 y D2 (spec) | R45 y R46 en `requirements.md` (sigue 150/150: se funden las secciones E–F y G–H y se compacta la cabecera), `design.md` (sigue 250/250, sustituyendo texto), T31–T37 en `tasks.md`, decisiones en `progress/spec_F-053.md` |
| `02f6ff1` | D1 (R45) | `ESTADOS_ALTA_BLOQUEANTES` en `ruesma_comun.alta_sigrid`; `save` de sv3 no borra un merge con alta bloqueante; el pipeline no lo reprocesa |
| `604e918` | D2 (R46) | `linea_de_otro_contrato` ⇒ `revisar` sin llamar a sigrid-api + WARNING `ANOMALIA`; recuento en la medición |

## 2. Decisiones de diseño

- **H1. Auditoría del resto de sv9** (secretos al log): no hay más fugas. (a) Cliente de sigrid-api: la clave va en
  la cabecera y nunca se registra; el log lleva ruta, estado y códigos; `SigridLecturaError` lleva el `repr` de la
  excepción de httpx, que no incluye cabeceras ni cuerpo. (b) Graph: `parse_graph_key` no repite el valor y los
  errores del token llevan el cuerpo de Azure AD, no el secreto. (c) La URL de SQLAlchemy: comprobado que sus errores
  y su `repr` ocultan la contraseña (`u:***@`). (d) `Settings` no se registra en ningún sitio. (e) Las colas de comun
  no registran la cadena de conexión.
- **H2. `ide_negocio` y no el documental.** `GraficoPreview` (`domain/models/concepto_grafico_models.py`:115) trae
  `ide_documental` (:123) e `ide_negocio` (:124), sin `ide`. `rcg` enlaza el concepto con el `gra` de negocio
  (`EnlacePreview.gra`), y en la respuesta idempotente solo viene ese (`attach_concepto_grafico_use_case.py`:404 y
  :406; en la grabación, :556–:557 y :564). Citas en el docstring del test.
- **O1. Peor caso de un mensaje**, con los tiempos de la configuración: lectura de R14, previa y adjunto con 3 intentos
  de `SIGRID_API_TIMEOUT_S` (60) y esperas de tenacity de 1 y 2 s = 183 s cada una; grabación de 240 s; PDF: token de
  Graph (5 intentos de `GRAPH_TIMEOUT_S` y hasta 20 s entre ellos = 380 s) más 4 peticiones (sitio, drive, descarga y
  redirección, en el peor modo) = 240 s. Total **1409 s**; con 300 s de margen (BBDD y arranque), **1740 s**. Supuesto:
  cada intento acotado por su timeout (el balanceador de sigrid-api corta a los 230 s). Los reintentos del cliente son
  ahora constantes del módulo y un test ata las de Graph a `GraphTokenProvider` de comun. Coste: si el worker muere,
  el mensaje tarda 29 min en reaparecer (R8 lo pasa a `incierto` igual).
- **D1. Cómo se conserva.** Dentro de `save`, en la misma transacción y antes de borrar: `to_regclass` (sin tabla, como
  hoy: la consulta abortaría la transacción) y `SELECT m.id, a.estado, a.sigrid_cod ... LEFT JOIN albaran_altas_sigrid
  ... FOR UPDATE OF m` (cierra la carrera con `reclamar` de sv9). Con un alta bloqueante: `rollback`, WARNING con
  `sha256`, documento, estado y `cod`, y devuelve el documento con `conservado_por_alta=True`; el pipeline responde
  `duplicate=True` sin enriquecer ni revalorar (lo que R25 prohíbe desde sv4). **Interpretación de «otros estados»**:
  solo protegen los bloqueantes del glosario; sin alta o con `no_admitido`, `ya_en_sigrid`, `simulado`, `revisar`,
  `error` o `anulado`, se borra como hoy (parametrizado). `ESTADOS_ALTA_BLOQUEANTES` va a comun (lo necesitará sv4 en
  T19) y un test lo ata a los `ESTADOS_BLOQUEANTES` de sv9. El doble de sesión de `test_f048_r27_merge.py` aprende la
  consulta nueva (responde «sin tabla»).
- **D2. Qué cuenta como «otro contrato»**: línea a registrar (importe ≠ 0) con `matched_contrato_line_id` y código de
  contrato en su línea casada distinto del de la valoración, también si la valoración no tiene contrato. Una casada sin
  código de contrato no se puede afirmar y sigue sin vincular. Es un motivo local de `revisar` como los de R39 (no se
  evalúa si hay motivos de R10); el WARNING `ANOMALIA` se escribe siempre que se valida, también con `no_admitido`.
  Dos tests viejos (`test_f053_r12_lo_que_no_casa_del_todo_va_sin_vincular[OTRO/1]` y
  `..._sin_contrato_en_la_valoracion_...`) eran la desviación 8: ahora usan una casada sin código de contrato.
- **Medición (D2)**: `lineas_de_otro_contrato` por albarán (CSV) y en el resumen, con la lista de `document_id`. Cuenta
  todas las valoradas (con o sin importe) para ver si ya ocurre; no cambia los veredictos (a) y (b).

## 3. Hallazgos para el humano (no implementados)

1. **D1 tiene un segundo camino.** Si el documento está ACTIVO, el reingreso no llega a `save`: va a la rama de
   duplicado del pipeline (`persist_albaran_pipeline.py`, `run`), que reescribe clasificación y contexto de líneas,
   resuelve cabecera, re-enriquece obra y contratos y **dispara la revaloración** (sv6 reemplaza la valoración y pierde
   el producto elegido, R42), aunque el alta esté `registrado`. No borra el alta, pero cambia lo que se registró. R45 y
   esta pasada solo cubren el borrado (documento en la papelera o carrera). Propuesta: la misma comprobación de alta
   bloqueante al principio de esa rama (devolver duplicado sin tocar nada). Decide el humano.
2. **D2 no solo viene de sv5/sv6.** sv4 deja conciliar a mano una línea con cualquier línea de contrato
   (`add_conciliacion_for_merge_line` / modo `contract_line` en `review_repository.py`) sin comprobar que sea del
   contrato de la valoración, y la valoración manual que crea sv4 nace con `contrato_codigo` NULL. Así que la anomalía
   también puede ser una conciliación manual: el WARNING lo dice. ¿Debe sv4 impedirlo (fase 2, T19–T20) o basta R46?
3. **D1 y SharePoint**: antes de `save`, el pipeline ya ha subido el PDF a SharePoint; en el caso conservado esa
   subida no se deshace (no toca el documento ni el alta).

## 4. Fase RED (comando: `python -m pytest -q -p no:cacheprovider -k "<filtro>"` desde el servicio)

```
H1 (sv9, -k "f053_r35_configuracion_invalida or f053_r35_secreto_solo"): 4 failed
  E  'input_value' is contained here: ue_error, input_value='{"sin_comodin": "MA9999"}', input_type=str]
  E  AssertionError: assert 'S3CR3T0' not in 'ERROR    ma.../v/missing\n'
  E    Field required [type=missing, input_value={'PG_PASSWORD': 'S3CR3T0'}, input_type=dict]...
  (lo mismo con GRAPH_KEY y SIGRID_API_FUNCTION_KEY)
H2 (sv9, -k f053_r22_adjunto): 2 failed, 3 passed
  E  AssertionError: assert (True is True and None == 4455)
  E   +  and   None = ResultadoAdjunto(colgado=True, gra_ide=None, codigo=None, mensaje='').gra_ide
H3 (python -m harness.rutas_sensibles --puerta --base dev):
  PUERTA RUTAS SENSIBLES: N/A (sin feature en curso con rama: no hay diff que cotejar)
O1 (sv9, -k f053_o1): 3 failed
  E  KeyError: 'visibilidad_s'   (x2)
  E  AttributeError: module 'infrastructure.sigrid.sigrid_api_alta_client' has no attribute 'INTENTOS_POR_DEFECTO'
D1 (sv3, tests/test_f053_r45_reingreso_con_alta.py): 12 failed
  E  assert ([<infrastruct...>] == []  Left contains 2 more items, first extra item: <...AlbaranDocumentMergeOrm ...>
  E  AttributeError: 'ExistingDocument' object has no attribute 'conservado_por_alta'
D1 (comun y sv9, -k f053_r45): 1 failed + 1 failed
  E  AttributeError: module 'ruesma_comun.alta_sigrid' has no attribute 'ESTADOS_ALTA_BLOQUEANTES'
  E  ImportError: cannot import name 'ESTADOS_ALTA_BLOQUEANTES' from 'ruesma_comun.alta_sigrid'
D2 (sv9, suite entera, esqueleto con NotImplementedError): 8 failed, 440 passed
  E  AssertionError: se esperaban motivos y llegó PeticionAlbaran(... cod_contrato='CTSU16/0206' ...)
  E  AssertionError: assert ['signo_incoherente'] == ['linea_de_ot..._incoherente']
  E  AssertionError: assert ('ANOMALIA' in '')
D2 medición (sv3, -k f053_medicion): 5 failed, 17 passed
  E  KeyError: 'lineas_de_otro_contrato'
```

## 5. Controles negativos (suite entera del servicio; restaurado con `git checkout --` y `git diff --quiet`)

| Qué se rompió | Resultado |
|---|---|
| H1: volver a registrar `exc` | 4 failed |
| H2: leer `ide_documental` / leer `ide` | 2 / 2 failed |
| H3: quitar `branch` | la puerta vuelve a «N/A (sin feature en curso con rama...)» |
| O1: no pasar `visibilidad_s` · sin margen · sin el PDF · timeout fijo en vez del configurado | 2 · 2 · 2 · 1 failed |
| D1: `save` no mira el alta · sin `FOR UPDATE` · conserva con cualquier alta · sin mirar si existe la tabla · el pipeline reprocesa el conservado · sin WARNING | 3 · 3 · 6 · 5 · 1 · 3 failed |
| D1: `incierto` fuera de `ESTADOS_ALTA_BLOQUEANTES` | comun 1, sv9 1, sv3 1 failed |
| D2: el motivo da `no_admitido` · no se detecta (desviación 8) · cuenta casadas sin código · valoración sin contrato no cuenta · cuenta las de importe 0 | 4 · 7 · 1 · 1 · 1 failed |
| D2: sin el WARNING · WARNING como INFO | 3 · 3 failed |
| D2 medición: no detecta · cuenta casadas sin código | 3 · 1 failed |

## 6. Verificaciones MANUAL pendientes

- **Repetir T0** (medición, solo lectura; comando en `progress/spec_F-053.md`, «Medición (T0)»): mirar la línea nueva
  «Líneas valoradas casadas con una línea de OTRO contrato (R46)» y sus `document_id`.
- R45 contra PostgreSQL real (`to_regclass`, `FOR UPDATE OF m` con `LEFT JOIN`): con la sesión simulada solo se
  prueba el SQL generado; lo cubre T26/T27 en local.
- Las de la fase 1 siguen igual (T0b, T0c, T26–T29).

## 7. Evidencias

| Evidencia | Valor |
|---|---|
| Tests (una suite tras otra, bajo `coverage`, al final) | sv9 **448 passed** (24,96 s) · sv3 **461 passed** (24,77 s) · comun **375 passed** (74,59 s) · raíz **1083 passed** (273,33 s). sv6 no se ha tocado en esta pasada (no se relanza) |
| Tests nuevos | sv9 +18 (H1 4, O1 3, R45 1, R46 10; los de H2, ajustados) · sv3 +17 (R45 12, medición 5) · comun +1 |
| Cobertura de líneas cambiadas | `python -m harness.cobertura --base dev --config harness/rigor.json` → `PUERTA COBERTURA: 96.2% de 1464 líneas cambiadas cubiertas (1409/1464, umbral 80%, nivel critico)` |
| Tamaño | `PUERTA TAMAÑO: F-053 dentro de los topes (requirements 150/150, design 250/250)` |
| Rutas sensibles | `PUERTA RUTAS SENSIBLES [evals]: N/A (F-053 no toca ninguna ruta sensible declarada)` |
| Lint | `ruff check .` limpio en sv9; en sv3, los ficheros tocados tienen las mismas faltas previas (I001, ISC004, UP035), ninguna nueva |
| Mutación | No ejecutada: es T25, puerta final (igual que en la fase 1) |
| `bash harness/init.sh` | No ejecutado en el worktree (mismo motivo que la fase 1: falta el venv de sv4); se sustituye por las suites de arriba |

## 8. Remate (implementer, 2026-10-07): decisiones D3 y D4 del humano sobre los hallazgos del §3

Decisiones: **1a** «un albarán no se puede pisar» (el duplicado ACTIVO con alta bloqueante no se reprocesa), **1c** la
mirada del alta va **antes de subir el PDF a SharePoint** (activo y papelera) = **D3**; **1b** sv4 no se cambia, R46
sigue de red = **D4**. Mismo entorno que arriba (`.venv` raíz del árbol principal, `PYTHONPATH` a la comun del
worktree, comprobado: `ruesma_comun` se importa de `albaranes-F-053\services\albaranes-comun`). Solo sv3.

| Commit | Punto | Cambio |
|---|---|---|
| `80a3d5d` | spec | R45 reescrito (activo o papelera, antes de SharePoint, sin tocar nada; D1, D3); R21 y R23 compactados para seguir en 150/150; design §4 (250/250); T38–T39; D3 y D4 en `progress/spec_F-053.md` |
| `a7d0df1` | 1a (T38) | Método nuevo del puerto `buscar_conservado_por_alta(sha)`: reutiliza `_conservar_por_alta` (misma consulta `FOR UPDATE OF m`, `to_regclass`, WARNING) en su propia sesión, sin escribir. La rama de duplicado lo mira primero y devuelve `_devolver_conservado` (duplicado, sin contratos ni selección) |
| `8e7e680` | 1c (T39) | La mirada sube al principio de `run`, antes de `get_by_sha256` y de `document_storage.upload`: un conservado activo o en la papelera no sube nada ni llama a `save`. `save` mantiene su mirada (carrera con sv9) |
| `73d9707` | lint | Los dobles nuevos sin `return None` (ruff) |

**Decisiones de diseño.** (a) Método **obligatorio** del puerto (abstracto) y llamada directa, no `getattr` con
alternativa: es una salvaguarda y debe fallar cerrada; si la BBDD falla, la excepción sube como la de `get_by_sha256`
y el mensaje se reintenta. Por eso los dobles viejos (`test_f043_t31_*` ×4, `test_f048_r26_modelo`) aprenden el
método devolviendo `None`; los dos tests «repositorio sin el método» siguen probando lo suyo (la clasificación y el
contexto son opcionales). (b) Una sola consulta para las dos miradas: la previa y la de `save` comparten
`_conservar_por_alta`, así que no pueden divergir en estados ni en «sin tabla». El `FOR UPDATE` de la previa se
suelta al cerrar la sesión (serializa con `reclamar` de sv9; no bloquea más). (c) El orden del pipeline no obliga a
nada distinto: la mirada solo necesita el `sha256`, que se calcula antes de todo.

**Fase RED** (`python -m pytest -q -p no:cacheprovider -k f053_r45 tests/test_f053_r45_reingreso_con_alta.py`, sv3):
```
1a: 13 failed, 13 passed
  E  AttributeError: 'SqlAlchemyAlbaranRepository' object has no attribute 'buscar_conservado_por_alta'. Did you mean: '_conservar_por_alta'?
  E  Left contains 9 more items, first extra item: 'repo.update_merge_clasificacion'   (activo con alta, force_refetch False/True)
1c: 2 failed, 26 passed
  E  AssertionError: assert ['sharepoint...., 'repo.save'] == []      (papelera con alta: sube el PDF y llama a save)
  E    Left contains 2 more items, first extra item: 'sharepoint.upload'
  E  AssertionError: assert ['sharepoint....rge_document'] == ['repo.buscar..., 'repo.save']   (la mirada no va primero)
```
Tests nuevos (+16 en sv3): mirada del repositorio con alta bloqueante ×3 (devuelve el conservado, solo lectura,
`FOR UPDATE`, log con documento, estado y `cod`), sin alta o no bloqueante ×7, sin tabla; activo con alta ×2
(`llamadas == []`: ni clasificación, ni contexto, ni cabecera, ni obra, ni contratos, ni fecha, ni valoración, ni
SharePoint); activo sin alta se reprocesa como hoy; papelera con alta no sube nada ni llama a `save`; documento nuevo:
orden `buscar → upload → save`. El test viejo del pipeline conservado pasa a cubrir la carrera (la previa no ve el
alta y `save` la conserva).

**Controles negativos** (suite entera de sv3; restaurado con `git checkout --`, `git diff --quiet` y `sha256sum -c`
de los ficheros mutados = OK):

| Qué se rompió | Resultado |
|---|---|
| 1a: el duplicado no mira el alta · `buscar` siempre `None` · la mirada tras escribir la clasificación · el conservado devuelve `contratos_count=1` | 2 · 3 · 2 · 2 failed |
| 1c: la mirada vuelve a la rama de duplicado (papelera sin cubrir) · la mirada entre SharePoint y `save` · sin la mirada previa (solo `save`) · `save` deja de conservar (carrera) | 2 · 4 · 4 · 1 failed |

**Seguridad (aviso del 2026-10-07).** Revisado sv9: `commit=true` solo sale en la grabación tras `ModoAlta.REAL`
(`alta_sigrid_service.py`:273/282) y el adjunto (`concepto-grafico`, que manda `commit: true`) solo con
`self._modo is ModoAlta.REAL` (:329 y :390); `ModoAlta.REAL` solo si `ALTA_SIGRID_COMMIT == "true"`
(`config/settings.py`:159). **Ninguna ruta graba sin la llave.** Nada arrancado contra sigrid-api.

**Hallazgos para el humano (no implementados, fuera de lo decidido):**
1. **Carrera residual en la rama de duplicado**: si sv9 reclama el alta entre la mirada previa y los pasos de la
   rama (cada uno en su transacción), el documento se re-enriquece igual. Ventana pequeña (el documento tiene que
   estar ya aprobado y con el alta pidiéndose en ese instante); cerrarla exigiría la mirada con cerrojo en cada paso.
2. **`POST /v1/albaranes/persist` (API HTTP de sv3)**, tras `run`, escribe los metadatos de fase 2
   (`review_phase2_*` del merge y `source_phase` de líneas) también sobre un conservado. El worker de colas no lo
   hace. No cambia lo registrado en Sigrid, pero «no tocar nada» no se cumple por esa vía.
3. **`reenrich_by_merge_id` y `POST /v1/albaranes/{id}/re-fetch-contratos`** de sv3 no miran el alta: dependen de
   que sv4 rechace el re-fetch y la revaloración (R25/R26, T19 de la fase 2, pendiente).

**Evidencias del remate.** Suites, una tras otra y bajo `coverage`: sv3 **477 passed** (42,86 s) · raíz **1083
passed** (593,65 s; la máquina iba cargada, en la pasada 2 fueron 273 s). sv9, comun y sv6 no se tocan (no se
relanzan; sus `coverage.json` de la pasada 2 siguen valiendo). `python -m harness.cobertura --base dev --config
harness/rigor.json` → `PUERTA COBERTURA: 96.2% de 1477 líneas cambiadas cubiertas (1421/1477, umbral 80%, nivel
critico)`. `PUERTA TAMAÑO: F-053 dentro de los topes (requirements 150/150, design 250/250)`. Rutas sensibles: N/A.
Lint: los ficheros tocados tienen las mismas faltas que antes (recuento igual fichero a fichero); el test nuevo,
limpio. Mutación: no ejecutada (T25, puerta final). `bash harness/init.sh`: no ejecutado en el worktree (falta el
venv de sv4, como en la fase 1).
