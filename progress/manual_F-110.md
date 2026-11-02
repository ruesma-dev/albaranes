# F-110 · Tareas MANUALES del líder (T1, T18, T20)

2026-11-01. Todo de **solo lectura**: PostgreSQL de Azure con `default_transaction_read_only=on` (comprobado: `on`)
y Sigrid solo por `POST /api/sql/read` de sigrid-api. Claves de Key Vault solo en variables del proceso. Los scripts
quedan en el scratchpad de la sesión (`f110\q.py`, `f110\q2.py`) y no se versionan. Resumen en `impl_F-110.md`.

## §T1 · Repetición de la medición de design §3

| Lectura | 2026-10-28 (design §3) | 2026-11-01 |
|---|---|---|
| Líneas con I ≠ 0 por d | nulo 319 (109 docs); (0,100) ≤ 2 dec 100 (39 docs) | nulo 358 (119 docs); (0,100) ≤ 2 dec **132** (48 docs); **0** cero, negativos, ≥ 100 o > 2 decimales |
| d > 0 por proveedor | FEYMACO 42 (9 vinc.), IBERFERRETERIA 28, CECOIS 22, RONDÓN 4, TEYMO 4 | FEYMACO 52 (d 40; **9 vinc.**) + «femaco, S.A.» 10 y «FERRETERÍA Y MAQUINARIA…, S. A.» 6 (d 40, el mismo proveedor con otro nombre en el merge), IBERFERRETERIA 28 (45), CECOIS 26 (7), RONDÓN 6 (10–30), TEYMO 4 (42) |
| Sin vincular con d > 0 | 91: 82 exactas, 2 a 1–2 cént., 7 no cuadran | **123**: **114** exactas, 2 a 1–2 cént., **7** no cuadran (las mismas cuentas); Qs = Q en todas |
| Vinculadas con d > 0 | 9 FEYMACO exactas, `ctrpro` `tar` = `pre` (4500, 1000, 3000), dto vacío | Las mismas 9, exactas; `dto` **vacío también leído en Sigrid** (`dbo.ctrpro`, no solo en la caché) |
| `albaran_contrato_lines_merge.descuentos` | nulo en 3198 | nulo en **4279** |
| Altas con alguna línea d > 0 | 11 `registrado` real, 1 `ya_en_sigrid` | **16** `registrado` real, 1 `ya_en_sigrid`, 2 `no_admitido` |

**Conclusiones: no cambia ninguna.** D1: el precio P sigue dando I al céntimo en 114 de 123 sin vincular (93 %) y en
las 9 vinculadas; el despejado solo hace falta en 2 + 7. D3: las únicas vinculadas con d siguen siendo las 9 de FEYMACO
contra bolsas sin dto, que sigrid-api acepta (ver §T18). D6: sigue sin haber descuentos inválidos ni con > 2 decimales:
no hay que reproponer. Crece el volumen (los proveedores son los mismos).

## §T18 · Contraste de F-018 / contrato v8.4 con design §4

Fuente: `azure-apps/sigrid_api.md` §8.6 (bloque «Desplegada el 2026-10-30 (F-018…)», `:1168-1202`) y la spec F-018
de sigrid-api (R14, R15) y F-009 R17 (opción C), solo leídos.

| Punto de §4 | Supuesto | Publicado (v8.4) | ¿Cambia una R? |
|---|---|---|---|
| Nombre y tipo | `lineas[].dto?`, número | `dto` opcional, número JSON (no texto ni booleano) | No |
| Rango | 0 < dto < 100, 2 decimales | 0 a 100 **con los bordes**, ≤ 2 decimales; fuera ⇒ 400 sin código; ausente, `null` o 0 ⇒ como hoy | No: lo que mandamos (`round(d, 2)` en (0,100)) es un subconjunto |
| Escritura | bruto + dto texto + `tot` con el redondeo de la UI | `tar` = bruto, `dto` «7%»/«1,5%», `tot` = round½↑(can·tar·(1 − dto/100), 2), `pre` = `tot`/`can` (neto), `mov`/PMP con el neto, `impbru` con el bruto | No. Nuestro `importe_de_linea` redondea con `round` de Python: como mucho 1 céntimo en un empate exacto, dentro de la tolerancia 0,05 de la previa (R-2) |
| `dto` en la previa | cada línea devuelve `dto` | `dto` (número) y `precio_bruto` (= `tar`) **solo** si la línea lleva descuento (pedido o copiado); `precio` sigue siendo el neto; en `idempotente`, nunca | No: R11 (pedido con dto y la previa sin él ⇒ `dto_distinto`) y R12 encajan; `idempotente` no compara el dto |
| Códigos nuevos | por mapear | Ningún código de error nuevo; aviso informativo nuevo `dto_distinto_del_contrato` (y el ya existente `precio_distinto_del_contrato`). Ya están en `TEXTOS_MOTIVO_ALTA` de sv4 (T19) y ninguno está en `ALTA_SIGRID_AVISOS_BLOQUEANTES` (defecto `producto_sin_historico`; `infra/` no lo cambia) | No |
| Decimales del precio | ¿con cuántos guarda? | No redondean el precio: `tot` sobre el producto exacto en `Decimal`, a 2 al final | No (mandamos 6) |
| Vinculadas | validan el dto contra el `ctrpro` si el precio cuadra | **Nunca rechazan**: se escribe lo pedido; diferencias de bruto o de dto = avisos informativos | No. Más permisivo que lo supuesto: las 9 de FEYMACO irán con dto 40 y avisos informativos, sin `revisar` |
| Rutas | — (aviso 1) | Clásico y `albaran-directo` ignoran `dto` en silencio | No: sv9 solo usa `sigrid/albaran` extendido (`sigrid_api_alta_client.py:53`) y lo fija `test_f110_peticion.py` (bloque «aviso 1») |

**Resultado: no hay que PARAR.** Nada del contrato publicado cambia una R de F-110.

### Aviso 2 · vinculada enviada sin `dto` contra un `ctrpro` con dto (su R15)

- **Qué hace sigrid-api**: si casa por la opción C (|`precio` − `ctrpro.pre`| ≤ 0,0001 **y** mismo importe a 2
  decimales) y el `ctrpro` tiene dto legible > 0 y `tar` ≠ 0, copia `tar` y `dto` y ahora escribe
  `tot` = round½↑(can·tar·(1 − dto/100), 2) en vez de can·pre. La previa devuelve `dto` y `precio_bruto` copiados.
- **Qué haría sv9** (worktree, `comparador_previa.py`): `_dto_distinto` devuelve `None` para una pedida sin `dto`
  (R12), así que el `dto` copiado no da motivo; solo `importe_distinto` si |`total` − I| > 0,05 ⇒ `revisar`, nunca
  una grabación con importe distinto. Con 0,05 o menos, graba con el `tot` de Sigrid (forma de la UI) y un
  `importe_calculado` que difiere a lo sumo 5 céntimos, lo mismo que hoy admite la tolerancia.
- **Cuántas líneas hay hoy en ese caso: 0.** Las 111 vinculadas con I ≠ 0 de producción apuntan a 41 `ctrpro`:
  leídos en Sigrid, los 41 tienen `dto` vacío (102 sin d y las 9 con d > 0 de FEYMACO). Más amplio: los **1577**
  `ctrpro` distintos de la caché de contratos de albaranes tienen todos `dto` vacío en Sigrid. Las vinculadas con
  d > 0 irían además con `dto` pedido (guarda encendida), fuera de R15.
- **Recomendación: dejarlo como está.** El fallo posible es seguro (`revisar` con el detalle «aprobado X, Sigrid Y»),
  no hay ningún caso hoy y añadir lógica sería código sin uso. Si aparece un contrato con dto, repetir la lectura de
  `q2.py` (los `ctrpro` de la caché por dto en Sigrid).

## §T20 · Altas reales grabadas en neto (SQL de design §9, tal cual)

**16 altas** `registrado`, modo `real`, con líneas d > 0 mandadas sin `dto` (design §3 decía 11): **37 líneas**.
Ninguna respuesta guardada trae aún `dto` en sus líneas (ninguna previa posterior a F-018 con descuento).

| document_id | Proveedor | Nº albarán | sigrid_cod | Líneas |
|---|---|---|---|---|
| c65a6776-73c1-4d2c-ac9c-e895edf4a7e8 | FEYMACO | 2 174.862 | AC26/31284 | 5 |
| 6cdc040a-cb1e-490a-86fc-b212c3a2d8b2 | FEYMACO | 2.175.095 | AC26/30546 | 1 |
| 4cf63661-05dd-4d4e-a95a-3ee8430a7215 | FEYMACO | 2.175.399 | AC26/31283 | 2 |
| 3d836226-c086-4898-81dd-c2b9319c869e | FEYMACO | 2.175.446 | AC26/31282 | 1 |
| d6cd0ff4-6142-47e4-ae83-bccb064f1947 | FEYMACO | 2.176.784 | AC26/31375 | 2 |
| fed34f3f-b39f-4db1-bd47-f9f7695f053a | CECOIS, S.L. | A 26017765 | AC26/30434 | 1 |
| 5024111a-67f1-4e45-89d5-e88077cf61b8 | CECOIS, S.L. | A 26017815 | AC26/30435 | 1 |
| 341eeb93-fa46-4c13-a494-29ae7a9f99c7 | CECOIS, S.L. | A 26018058 | AC26/30453 | 3 |
| 30f59f52-6d50-4096-b961-f609d8d74a78 | CECOIS, S.L. | A 26018267 | AC26/30447 | 2 |
| 47cf5be4-d5c5-4a99-84c3-65becc62a1d7 | CECOIS, S.L. | A 26018351 | AC26/30439 | 2 |
| a1eb48e1-0488-4af6-b6ab-40842c0eeec3 | CECOIS, S.L. | A 26018703 | AC26/30437 | 10 |
| 25b8a02f-edbc-4750-abad-1f291745d925 | CECOIS, S.L. | A 26018939 | AC26/31025 | 2 |
| f4dbf598-0310-4a98-89e6-9d11995b1597 | MATERIALES RONDON, S.L. | MAC977025 | AC26/30486 | 1 |
| f2b10bb2-a5aa-44ee-9d63-9c3bbd25e9f8 | MATERIALES RONDON, S.L. | MAC977620 | AC26/30472 | 2 |
| dcdb80a6-dbad-4eda-af59-698431a694b1 | MATERIALES RONDON, S.L. | MAC978448 | AC26/31026 | 1 |
| aca4dada-b383-4ae2-8f7d-313cd6c47646 | MATERIALES RONDON, S.L. | MAC979230 | AC26/31398 | 1 |

FEYMACO = «FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)» en el merge. Por D5 no se reenvían (el
importe es correcto); **decisión del humano pendiente**: corregirlas a mano en Sigrid (bruto + dto) o dejarlas en neto.

Nota: las verificaciones de `tasks.md` apuntan a §T17 (T18), §T19 (T20) y §T21 (T22); aquí se usan los nombres de la
tarea (§T18, §T20), como pidió el líder.
