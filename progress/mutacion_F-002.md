<!-- progress/mutacion_F-002.md -->
# F-002 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-002` el 2026-08-14 21:01.
> **Medida con el arnés 1.5.2, que NO mutaba `is`/`is not`: NO es comparable con las campañas posteriores a la 1.6.0 (F-034), que generaría +18 mutantes aquí. Decisión del humano (D1, opción B): no se remide; solo se remidieron F-019 y F-027.**

> ## ⚠ CAMPAÑA EN CUARENTENA · su evidencia no vale mientras no se decida
>
> Sellado el 2026-08-25. **108 mutantes en 54,8 s en serie = 0,51 s por
> mutante**, por debajo del segundo que la regla del coste por mutante
> (arnés 1.7.x) declara **sospechoso por construcción**: un tiempo así
> indica que la suite no llegó a juzgar de verdad a cada mutante.
>
> Mientras la cuarentena siga abierta, **no cites estos números como
> evidencia de nada**. Para levantarla hay dos salidas y las dos son del
> humano: relanzar la campaña con la caché limpia, o anotar aquí que su
> evidencia de mutación se da por no válida. Ver `progress/current.md`.


## Alcance

Origen del diff: **rama** (`89bc79d62e97bcd5f70b8e60d2ffc4b2f2ce40cc` .. `feature/F-002-obra-proveedor`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-api/application/services/albaran_extraction_service.py` | 88 |
| `services/albaranes-api/config/settings.py` | 37 |
| `services/albaranes-api/domain/ports/obras_activas_provider.py` | 27 |
| `services/albaranes-api/infrastructure/sigrid/__init__.py` | 1 |
| `services/albaranes-api/infrastructure/sigrid/obras_activas_cache.py` | 71 |
| `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py` | 185 |
| `services/albaranes-api/interface_adapters/api/app.py` | 30 |
| `services/albaranes-api/interface_adapters/composition.py` | 30 |
| `services/albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py` | 28 |
| `services/albaranes-persistencia/application/services/fecha_guard_service.py` | 141 |
| `services/albaranes-persistencia/application/services/header_resolver_service.py` | 216 |
| `services/albaranes-persistencia/application/services/obra_enrichment_service.py` | 78 |
| `services/albaranes-persistencia/config/settings.py` | 21 |
| `services/albaranes-persistencia/domain/ports/header_resolver_ports.py` | 36 |
| `services/albaranes-persistencia/domain/ports/obra_merge_repository_port.py` | 30 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 267 |
| `services/albaranes-persistencia/interface_adapters/api/app.py` | 11 |
| `services/albaranes-persistencia/interface_adapters/composition.py` | 11 |
| `services/albaranes-persistencia/interface_adapters/worker/persistence_worker.py` | 21 |
| `services/albaranes-persistencia/interface_adapters/worker/ports.py` | 18 |
| `services/albaranes-persistencia/interface_adapters/worker/workflow_context_adapter.py` | 118 |
| `services/albaranes-persistencia/main_worker.py` | 19 |
| **Total** | **1484** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 108 |
| Mutantes evaluados | 108 |
| Muertos | 95 |
| Supervivientes | 13 |
| Timeouts | 0 |
| Tiempo total | 54.8 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py:180` [logico]

- Original: `f"{(response.text or '')[:300]}"`
- Mutado:   `f"{(response.text and '')[:300]}"`

#### Análisis (completado)

> Por qué ningún test lo caza: la expresión solo compone el TEXTO del
> `RuntimeError` que `obtener()` captura y loguea; el valor de retorno es
> `None` con mensaje o sin él, y eso sí está probado
> (`test_f002_r2_un_error_http_no_propaga_y_devuelve_none`).
> Decisión: **mutante equivalente**. Fijar en un test el recorte exacto del
> cuerpo de la respuesta sería congelar el formato de un log, no una regla
> del sistema.

### 2. `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py:180` [entero]

- Original: `f"{(response.text or '')[:300]}"`
- Mutado:   `f"{(response.text or '')[:301]}"`

#### Análisis (completado)

> Por qué ningún test lo caza: mismo caso que el superviviente 1 — 300 o
> 301 caracteres del cuerpo de error acaban en el mismo log y en el mismo
> `None`.
> Decisión: **mutante equivalente** (longitud de un mensaje de diagnóstico).

### 3. `services/albaranes-persistencia/application/services/header_resolver_service.py:102` [logico]

- Original: `if not a or not b:`
- Mutado:   `if not a and not b:`

#### Análisis (completado)

> Por qué ningún test lo caza: es una guarda defensiva ANTES de puntuar. Con
> `and`, un nombre vacío pasa a `_match_score`, que ya devuelve `0.0` para
> cadena vacía: el resultado final (`0.0`) es idéntico por los dos caminos.
> Decisión: **mutante equivalente**. La guarda se conserva porque hace
> explícito lo que si no habría que ir a comprobar dentro de `_match_score`.

### 4. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:147` [booleano]

- Original: `return json.dumps(motivos, ensure_ascii=False, indent=2)`
- Mutado:   `return json.dumps(motivos, ensure_ascii=True, indent=2)`

#### Análisis (completado)

> Por qué ningún test lo caza: `ensure_ascii` solo cambia cómo se ESCAPAN
> los caracteres no ASCII dentro del JSON; el valor que se recupera con
> `json.loads` —la lista de motivos, que es lo que lee sv4— es el mismo. Los
> motivos que genera esta feature (`obra_inexistente:`, `obra_codigo_invalido:`,
> `proveedor_cif_no_casa:`, `fecha_albaran_fuera_de_rango:`) son ASCII puro,
> así que ni siquiera cambia el texto almacenado.
> Decisión: **mutante equivalente** (serialización cosmética).

### 5. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:147` [entero]

- Original: `return json.dumps(motivos, ensure_ascii=False, indent=2)`
- Mutado:   `return json.dumps(motivos, ensure_ascii=False, indent=3)`

#### Análisis (completado)

> Por qué ningún test lo caza: `indent` solo afecta al sangrado del JSON
> almacenado. `json.loads` devuelve la misma lista con 2 o con 3.
> Decisión: **mutante equivalente** (formato de almacenamiento).

### 6. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:164` [booleano]

- Original: `return json.dumps(motivos, ensure_ascii=False, indent=2)`
- Mutado:   `return json.dumps(motivos, ensure_ascii=True, indent=2)`

#### Análisis (completado)

> Por qué ningún test lo caza: idéntico al superviviente 4, en la función que
> RETIRA motivos (`quitar_motivos_con_prefijo`).
> Decisión: **mutante equivalente** (serialización cosmética).

### 7. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:164` [entero]

- Original: `return json.dumps(motivos, ensure_ascii=False, indent=2)`
- Mutado:   `return json.dumps(motivos, ensure_ascii=False, indent=3)`

#### Análisis (completado)

> Por qué ningún test lo caza: idéntico al superviviente 5, en
> `quitar_motivos_con_prefijo`.
> Decisión: **mutante equivalente** (formato de almacenamiento).

### 8. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1672` [entero]

- Original: `return fila[0] if fila else None`
- Mutado:   `return fila[1] if fila else None`

#### Análisis (completado)

> Por qué ningún test lo caza: está dentro de `_leer_notas`, que ejecuta
> `SELECT review_notes ...` contra PostgreSQL. Ningún test unitario puede
> entrar ahí: el `SessionFactory` de sv3 CREA la base de datos al construirse
> y la columna `review_notes` no vive en el ORM (la añade un `ALTER TABLE`
> idempotente con SQL de PostgreSQL), así que no hay forma de levantarlo
> sobre SQLite en memoria. `design.md` ya declaró este riesgo y lo compensó
> con verificación MANUAL.
> Decisión: **hueco real, cubierto por control compensatorio**: la mutación
> (`fila[1]`) reventaría con `IndexError` en la PRIMERA nota de revisión que
> se escribiera, y los cuatro escenarios de T12 (obra 0937, HORPRESOL, fecha
> de 2023, `email_received_datetime`) escriben notas. Queda anotado como
> verificación MANUAL del humano en `progress/impl_F-002.md`.

### 9. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1697` [comparacion]

- Original: `if nuevas == actuales:`
- Mutado:   `if nuevas != actuales:`

#### Análisis (completado)

> Por qué ningún test lo caza: mismo motivo que el superviviente 8 (código de
> `_sustituir_nota`, que necesita PostgreSQL). La mutación invierte el
> cortocircuito de «no escribas si no cambia nada»: el sistema seguiría
> siendo correcto salvo por un UPDATE de más (o de menos) por documento.
> Decisión: **hueco real de bajo impacto, cubierto por T12**. La lógica pura
> que decide el nuevo texto (`sustituir_nota_por_prefijo`) SÍ está probada,
> incluida su idempotencia.

### 10. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1722` [booleano]

- Original: `document.review_required = True`
- Mutado:   `document.review_required = False`

#### Análisis (completado)

> Por qué ningún test lo caza: es el `review_required = True` de
> `marcar_revision_cabecera`, dentro de la transacción PostgreSQL. Es la
> línea MÁS importante de la feature (sin ella nada llega al revisor) y es
> justo la que ningún test unitario puede alcanzar.
> Decisión: **hueco real, cubierto por control compensatorio**. Los tres
> servicios que la invocan comprueban con dobles que la llaman con el motivo
> y la nota correctos; que la columna se ponga a `true` de verdad lo verifica
> el humano en T12 (escenarios 1, 2 y 3, mirando `review_required` en
> `albaran_documents_merge`). ES EL PUNTO A MIRAR PRIMERO en la prueba
> local.

### 11. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1760` [booleano]

- Original: `document.review_required = True`
- Mutado:   `document.review_required = False`

#### Análisis (completado)

> Por qué ningún test lo caza: idéntico al superviviente 10, en
> `descartar_obra_no_valida` (la red de obra).
> Decisión: **hueco real, cubierto por T12 escenario 1** (albarán con la obra
> inventada 0937: el merge debe quedar sin obra Y con `review_required`).

### 12. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1771` [logico]

- Original: `f"'{codigo_leido or '—'}' no corresponde a ninguna obra "`
- Mutado:   `f"'{codigo_leido and '—'}' no corresponde a ninguna obra "`

#### Análisis (completado)

> Por qué ningún test lo caza: compone el texto de la nota `[AVISO] Obra`
> dentro del método que necesita PostgreSQL. Con la mutación, un
> `codigo_leido` nulo escribiría `'None'` en vez de `'—'`.
> Decisión: **hueco real cosmético**. El caso solo se da si se descarta una
> obra sin código leído, que la red no produce (sin código no hay descarte:
> `test_f002_r6_sin_codigo_leido_no_marca_revision`). Se deja documentado en
> vez de forzar un test contra BBDD.

### 13. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1797` [comparacion]

- Original: `cambio_motivos = nuevos != document.review_reasons_json`
- Mutado:   `cambio_motivos = nuevos == document.review_reasons_json`

#### Análisis (completado)

> Por qué ningún test lo caza: es el «¿ha cambiado algo?» de
> `retirar_revision_obra`, también en la transacción PostgreSQL. Invertirlo
> escribiría cuando no hace falta y no escribiría cuando sí: la retirada del
> aviso (R7) dejaría de funcionar.
> Decisión: **hueco real, cubierto por T12 escenario 1 (segunda parte)**:
> corregir la obra en el portal y volver a buscar debe dejar el documento sin
> nota `[AVISO] Obra` y sin motivos `obra_*`. La lógica pura que calcula la
> lista resultante (`quitar_motivos_con_prefijo`) sí está probada.

