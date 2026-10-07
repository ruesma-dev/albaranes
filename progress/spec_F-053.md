<!-- progress/spec_F-053.md -->
# Spec F-053 · Alta en Sigrid de los albaranes aprobados (spec-author)

Rama `feature/F-053-alta-sigrid` (worktree `../albaranes-F-053`, desde `dev` c8a295e). Rigor `critico`,
prioridad 1. v1 del 2026-09-30; v2–v5 del 2026-10-01; v6 del 2026-10-05 (producto genérico por línea, F-051 v4 y
huecos del contrato); **v7 del 2026-10-06**: respuestas del humano a P1–P7 («si» a todas las recomendaciones) y
alineación con **F-009 v8 de sigrid-api** (`8a6ecab`, que fija la forma definitiva del contrato; solo le queda medir
`mov.prepma`, M14e, que no la cambia). Estado: **`spec_ready`**, sin preguntas abiertas; siguiente, la PARADA 1.

## Qué hay en la rama

- `specs/F-053-alta-sigrid/requirements.md` — R1–R44 en EARS (**150/150** líneas).
- `specs/F-053-alta-sigrid/design.md` — sv9, códigos → estados (§2, enlaza el contrato), producto, flujo, DDL,
  configuración, orden (**250/250**).
- `specs/F-053-alta-sigrid/tasks.md` — T0d, T0a, T0b, T0c, T0, T1–T30 con T2b, T19b y T21b; T0b, T0c, T0, T22 y
  T26–T29 son MANUAL del humano.
- `progress/propuestas_a_sigrid_api_F-053.md` (**nuevo**) — lo que el contrato de sigrid-api da aún por abierto y
  F-053 ya ha cerrado. Conclusión: **F-053 no necesita nada nuevo de F-009 v8**. En sigrid-api no se ha editado nada
  (regla del humano del 2026-10-06: «el contrato solo se toca para actualizar consumos»).
- `harness/features.json` — F-053 a `spec_ready` y **F-061 registrada** (P1; id libre comprobado en `albaranes`,
  `albaranes-F-049`, `albaranes-F-051` y en todas las ramas locales). `BACKLOG.md` regenerado.
- Ningún fichero de código tocado. No se ha llamado a sigrid-api, Azure ni BBDD.

## v7 · decisiones del humano (2026-10-06) y qué cambió

| P | Decisión | Dónde |
|---|---|---|
| P1 | Familia `medios_auxiliares` (XA9999) en ficha propia **F-061** (`pending`, prioridad 2, `critico`; alcance de la v6: `CATALOGO`, señales, `TipoFamilia` y copias, prompt de fase 1, evals). Mientras, XA9999 a mano en sv4 | glosario, design §1, §8, §10; `features.json` |
| P2 | Signos opuestos (cantidad > 0 e importe < 0, o al revés) ⇒ `revisar` con `signo_incoherente`, sin llamar a sigrid-api; el descuento, a mano en Sigrid (H8) | R12, R39; design §2, §5, §11; T5, T9, T26 |
| P3 | Cerrada por M17b de F-009: anular **borra**; tras `anulado`, misma `referencia_externa`. Solo se retiran las marcas [P3] | R14, R28; design §2 |
| P4 | Sin `paride` hasta que F-049 conserve el `ide` de la partida; `partida_ambigua` ⇒ `no_admitido` (otra partida o sin partida). Nota de evolución, no requisito condicionado (no cabe y aún no hay nada que probar) | R12; design §8 |
| P5 | Vinculadas con cantidad y sin importe: no se mandan (H29) | R13; T5 |
| P6 | «ALM» impreso: sin vincular, como hoy; vincularlo es de F-060/F-007 (H30) | glosario; design §8 |
| P7 | Cerrada: XA9999 medido en T0b-ter de F-009 (`tipmov` 1, genera `mov`; cuenta = `cuacomcod` de la naturaleza, 97,9 %) | — |

**Alineación con F-009 v8** (forma definitiva del contrato; mensaje de la sesión de sigrid-api del 2026-10-06):
- sv9 no manda `naturaleza` (el campo se retira en la v8; mandarlo da 400 sin código): la pone sigrid-api con
  `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO` (`MA99`, `QA99`, `XA99`; H34). `naturaleza_no_valida` ⇒ `error`
  (configuración). La App Setting nueva se cita en design §2 y en T0c.
- `cod2`, `dncide` y `dncproide` de las vinculadas los copia sigrid-api del `ctrpro` (H35, M19: `cod2` 100 %, enlace
  98,8 %); sin vincular, vacíos. sv9 no manda nada nuevo; T29 lo revisa en la UI.
- `analitica_no_resuelta` ⇒ `no_admitido` (la obra no tiene `<obra>.<caagascod sin MOD.>`; XA9999 100 % desde 2025).
- H9 cerrado (anular borra), H20 cerrado sin puerta dura (`mov` según `pro.tipmov`).
- `fecha_no_valida` ya no existe en sigrid-api (v5.1). La validación **local** de formato de F-053 (R10) se mantiene
  —sin fecha válida no se puede construir `fecha_albaran`, y `null` sería «hoy» en sigrid-api— pero se **renombra a
  `fecha_ilegible`** para no confundirla con el código retirado.
- `referencia_linea` = `str(id)` de la línea valorada (entero): siempre ≤ 24 (R12, T5).
- Los códigos `precio_negativo`, `obra_de_empresa_no_permitida`, `paride_no_valido` y los avisos
  `iva_de_otro_proveedor` y `sin_partida_en_linea_con_partida` ya estaban mapeados (v6); T7 los cita uno a uno.

**Orden** (design §8, tasks): la implementación empieza cuando **F-051 esté en `dev`**; **T0d** (primera tarea)
fusiona `dev` en la rama. Los tests no necesitan sigrid-api; T26 y T28 (previa contra sigrid-api) y T29 (modo
real) esperan a **F-009 desplegada**. F-049 (`paride`) y F-061 son evolución, no bloqueo.

## Plan de implementación (para la PARADA 1)

**PARADA 1 aprobada por el humano (2026-10-06, «adelante»).** Arranca la implementación en cuanto F-051 esté en `dev` (T0d).


1. **T0d** — con F-051 en `dev`, fusionar `dev` en la rama; `init.sh` en verde.
2. **T0a** — script de medición sin `MARCAS_ALMACEN` (F-051 v4). T0b, T0c y T0: MANUAL del humano (solo lectura).
3. **comun** (T1) — `MensajeFeedback.accion`, `esta_valorado`, `alta_sigrid` (mapeo y producto efectivo).
4. **sv3 y sv6** (T2, T2b) — DDL de `albaran_altas_sigrid` (sv3) y columna `producto_sigrid` (sv6, solo DDL y ORM).
5. **sv9 nuevo** (T3–T16) — esqueleto y modelos; dominio puro (validador con R10–R13 y R39, comparador,
   clasificador con la tabla de design §2); servicio (reclamar, validar, duplicados, previa, simulación, grabación
   única, adjunto, anulación); adaptadores (cliente de sigrid-api, repositorio SQL, PDF de SharePoint, worker).
6. **sv4** (T17–T21b) — publicar al aprobar, cerrojo de R25–R27 (con `asignar_almacen` de F-051), producto
   elegible por línea, no aprobar sin valorar, panel del alta y estado en el listado.
7. **infra y docs** (T22, T23) — sv9 en los scripts (KEDA, 1 réplica, secreto de Key Vault); `ARCHITECTURE.md`,
   dominio de negocio y `azure-apps/albaranes.md`.
8. **Puertas** (T24, T25, T30) — cobertura ≥ 80 %, mutación completa, `init.sh` en verde.
9. **Verificación real** (T26–T29, humano) — con F-009 desplegada: local en simulación, cerrojo, Azure en
   simulación unos días y primera grabación real con autorización expresa.
Riesgo: rigor `critico`, escribe en el ERP; ninguna escritura real hasta F-009 desplegada y `ALTA_SIGRID_COMMIT=true`.
Fuera: F-061, `paride` (F-049), conservar el producto al revalorar (F-058), ALM impreso (F-060/F-007).

## v6 · qué cambia y por qué

### 1. Producto genérico por línea (decisión del humano, 2026-10-05)

Medición del líder en Sigrid (solo lectura, histórico de albaranes de compra `dca`/`dcapro`, emp 1): la cuenta
analítica (`dcapro.caaide`) de una línea **vinculada** es la de su `ctrpro` en el 99,8 %; en las **sin vincular**
no sale de la partida (`obrparpar.caaide`) ni del almacén (`alm.caaproide`/`caaseride`): hay ≈ una por par
(obra, producto genérico) — MA9999 sin vincular 154 obras / 201 pares obra-caa; QA9999 148/166; XA9999 80/101;
`dcaproana` vacío en todas. Genéricos (tip 3, emp 1): MA9999 «SUMINISTRO DE MATERIALES», QA9999 «ALQUILER DE
MAQUINARIA», XA9999 «ALQUILER MEDIOS AUXILIARES (ANDAMIOS, PUNTALES…)»; SM9999/SB9999 (subcontratas) no aplican.

| Pieza | Diseño v6 |
|---|---|
| Producto por defecto | Mapeo `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (JSON, clave `*` obligatoria; defecto `alquiler_maquinaria`→QA9999, `medios_auxiliares`→XA9999, `*`→MA9999) aplicado a la `familia_efectiva` de **cada línea** (la de `contexto_linea.tipo_familia`; si no, la del documento salvo mixto; sin familia, `*`). Función pura compartida `ruesma_comun.alta_sigrid.producto_efectivo` (R38) |
| Dónde se guarda lo elegido | `albaran_line_valuations.producto_sigrid VARCHAR(24)`, `NULL` = por defecto. El defecto **no se guarda**: se calcula al leer (sv4 al pintar, sv9 al construir) |
| Dueño del DDL | **sv6**, no sv3: `docs/ARCHITECTURE.md` hace a sv6 dueño de las tres tablas de valoración y su `schema_contribution.py` crea `albaran_line_valuations`. Solo DDL + ORM; ninguna lógica de sv6 cambia. El encargo decía sv3: corregido con la arquitectura |
| Cómo lo ve y cambia el administrativo | Columna «Producto Sigrid» en la tabla de líneas valoradas de la ficha (solo con DESDE): selector de los admitidos en cada sin vincular a registrar, «por defecto» marcado; vinculadas, el del contrato sin selector (R40). Ruta `POST /api/documents/{id}/lineas-valoradas/{lv_id}/producto-sigrid`, con deshacer, 400 si no procede y 409 con alta bloqueante (R41, R25) |
| Cómo lo manda sv9 | `producto` = el elegido o el por defecto; en vinculadas se ignora (R12, R43). Elegido fuera del mapeo ⇒ `producto_no_admitido` (R10) |
| Al revalorar | Se pierde (el replace de sv6 inserta la fila con `NULL`), como el almacén elegido (F-051 D5). Conservarlo es de **F-058**: el líder debe añadir «producto elegido» a su alcance (la ficha vive en la rama de F-051) (R42) |
| Lista blanca | `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` = `["MA9999","QA9999","XA9999"]`; los valores del mapeo deben estar en ella |
| Familia `medios_auxiliares` | No existe; va en la ficha F-061 (P1, decidido el 2026-10-06). Mientras tanto la clave del mapeo no casa y los andamios salen MA9999 salvo que el administrativo elija XA9999 |

### 2. Alineación con F-051 v4

Toda línea con `codigo_partida_final` vacío es almacén, tenga o no marca: desaparece `linea_sin_partida` (R10),
el glosario deja de mirar `partida_action` y T0a quita `MARCAS_ALMACEN` del script de medición.
**Corrección al encargo y a F-051 v4**: ambos dicen «`almacen: true` sin partida», pero el contrato v5.1 y F-009
R6 **eliminaron el campo `almacen`** (con `extra="forbid"`, mandarlo da 400 sin código). Una línea sin partida
viaja **sin la clave `partida`**; así lo dicen R12 y T5. Conviene corregir la frase en la spec de F-051 (R24) al
retomarla.

### 3. Huecos del contrato que F-053 incorpora sin decisión del humano

| H | Incorporado | Dónde |
|---|---|---|
| H1 | `usu` = `ALTA_SIGRID_USUARIO` en la cabecera; `usuario_no_valido` → `error` | R12, design §2 |
| H5 | Sin partida = sin clave `partida`; fuera `linea_sin_partida` | R10–R12 |
| H6 | Partida > 24 en `campo_demasiado_largo`; `descripcion` a 128; `falta_descripcion` local | R10, R12 |
| H7 | Vinculadas sin `unidad` ni `descripcion` (F-009 toma las del `ctrpro`) | R12 |
| H12 | `sin_partida_en_linea_con_partida` informativo | design §2 |
| H13 | `almacen_de_obra_no_resuelto` → `no_admitido` (alta a mano) | design §2 |
| H14 | `precio` redondeado a 6 decimales | R12 |
| H16 | De la respuesta solo `estado`, `con_ide`, `cod`, `avisos`, `lineas`, `totales`; nunca bancarias | R16, R35 |
| H18 | En `idempotente` se comparan totales: `registrado` + motivo `registrado_distinto` (**no `revisar`** como proponía el contrato: desbloquearía un albarán que ya está en Sigrid y el reintento volvería a dar `idempotente`; se corrige anulando, R28) | R15, design §11 |
| H19 | `fecha_no_plausible` (futura o anterior a hoy − 365) → `revisar` sin llamar a sigrid-api | R39 |
| H21 | CIF normalizado (mayúsculas, sin espacios/guiones/puntos, sin `ES` delante de 9) y `cif_no_valido` | R10, R12, R14 |
| H22 | `demasiadas_lineas` → `no_admitido` | design §2 |
| H24 | `producto_no_encontrado` → `error` | design §2 |
| H25 | Avisos bloqueantes por defecto `producto_sin_historico`; código desconocido → `error`; nuevos de F-009 v5/v6 mapeados (`obra_de_empresa_no_permitida`, `usuario_no_valido`, `precio_negativo` → `error`; `paride_no_valido` → `no_admitido`) | R18, design §2 |
| H26 | Orden por `line_index`, manuales al final por `id`; se casa por `referencia_linea` | R12 |

Ya cerrados fuera de F-053 (el encargo los listaba como del humano): **H4** (decidido: F-009 conserva
«imputable»; lo alinea F-049), **H31** (N4 aprobada en F-009: `cod_contrato` siempre que la valoración lo tenga;
R12) y **H20** (cerrado en F-009 v7: `mov` según `pro.tipmov`, sin puerta dura). `precio_negativo`
→ `error` y no `revisar`: sv9 nunca manda precio negativo, así que si llega es un fallo, no un dato que revisar.
`analitica_no_resuelta` (H10, F-009 v8: la obra no tiene la cuenta `<obra>.<sufijo>`): `no_admitido`.
`naturaleza_no_valida` (H34): `error`, porque sv9 no manda `naturaleza` (el campo no existe en F-009 v8).

## Preguntas de la v6 (P1–P7)

Respondidas por el humano el 2026-10-06 («si» a todas las recomendaciones): tabla de la sección v7. El texto de las
preguntas, con sus motivos, queda en el historial de git de este fichero (commit `07fd7a5`).

## Decisiones del humano vigentes (2026-10-01 salvo indicación)

| Tema | Decisión |
|---|---|
| Aprobar | ES registrar; los dos botones de sv4 (2026-09-30) |
| Vía | Solo endpoints de dominio de sigrid-api, nunca `sql/write` (2026-09-30) |
| Servicio | sv9 nuevo en el monorepo, consume `q-feedback` |
| F-013 | Sustituida por F-053 (sigue `pending` con el prefijo `[SUSTITUIDA POR F-053]`: el arnés no tiene ese estado) |
| Alcance | «Medir antes» (T0) |
| Líneas | Solo con importe; vinculadas y sin vincular en el mismo albarán; con partida o sin ella (= almacén, F-051 v4) |
| Producto (**2026-10-05**) | Vinculada: el del contrato. Sin vincular: por familia de la línea (QA9999 maquinaria, XA9999 medios auxiliares, MA9999 el resto), cambiable en sv4 antes de aprobar |
| `cod2` y planificación de compras (**2026-10-05**; H35, absorbido en F-009 v8 `8a6ecab`) | «el cod2 hay que traerlo, así como la vinculación a planificación de compras. si no viene originalmente se deja vacío». Medido en Sigrid (solo lectura, emp 1): `dcapro.cod2` («código alternativo», lo usa el jefe de obra para filtrar en el DPC) = `ctrpro.cod2` en el 99,9 % de las vinculadas que lo llevan; enlace DNC (`dncide` → `dnc`, `dncproide` → `dncpro`) en el 86 % de las vinculadas. Regla: en vinculadas, sigrid-api copia `cod2`, `dncide` y `dncproide` del `ctrpro` (vacíos si no los tiene; hoy F-009 los heredaría de la plantilla); sin vincular, vacíos. Absorbido en F-009 v8 (`8a6ecab`; M19: `cod2` 100 %, enlace 98,8 %); sv9 no manda nada nuevo |
| Analítica y naturaleza de las sin vincular (**2026-10-05/06**; H10 y H34, absorbidos en F-009 v8 `8a6ecab`) | Confirmado por el director de Administración y Control de Costes (correo del 2026-10-05) y medido: cuenta analítica = código de obra + `.` + `auxpronat.caagascod` de la naturaleza sin el prefijo `MOD.` (`MA99` `MOD.CDSB37`, obra `0678` ⇒ `0678.CDSB37`; `QA99` ⇒ `.CDQA12`; `XA99` ⇒ `.CDXA01`); cumplimiento QA9999 99,8 %, MA9999 con `MA99` 98 %, XA9999 87 %; 38 de 39 obras recientes tienen las cuentas. Naturaleza: el maestro de MA9999 está mal (`MA1501` cerámico; a mano se cambia a `MA99` en el 81 %) ⇒ mapeo producto → naturaleza en la configuración de sigrid-api (`MA9999`→`MA99`, `QA9999`→`QA99`, `XA9999`→`XA99`). En F-053: no se manda `naturaleza`; `analitica_no_resuelta` → `no_admitido` (alta a mano o crear la cuenta); `naturaleza_no_valida` → `error`. Hallazgo para Administración: corregir el maestro de MA9999 (no es de F-009 ni de F-053) |
| Negativas | Entran (cantidad e importe negativos); signos opuestos ⇒ `revisar` `signo_incoherente` (P2, 2026-10-06) |
| Sin valorar | No se aprueba ni se registra (R37); `partial` no cuenta |
| Valorado | `ok` de sv6, o valoración manual completa (`manual`/`no_contract` con importes y ninguno nulo) |
| Empleado / usuario | `ALTA_SIGRID_EMPIDE` fijo y configurable; `ALTA_SIGRID_USUARIO` (T0c) |
| Clave | La de siempre; riesgo anotado (design §11) |
| DDL | Tabla del alta en sv3; columna del producto en sv6 |
| Tolerancia | 0,05 € por línea; aviso bloqueante por defecto `producto_sin_historico` |
| Simulados | No se graban solos al pasar a real; uno a uno desde la ficha |
| Re-aprobación | Desaprobar y aprobar cuenta como aprobación nueva |
| Registrado | Bloqueado en sv4; se corrige anulando en Sigrid y «Ya lo he anulado» |
| Documentación ajena | Redacción propuesta de design §9 |
| Reingreso con alta (**D1**, 2026-10-06) | Opción a: sv3 no borra un merge con alta bloqueante (`en_curso`, `incierto`, `registrado`) al reingresar su PDF (mismo `source_sha256`); lo trata como duplicado, conserva documento, merge y alta, no lo reprocesa y lo deja en el log. Sin alta o con otro estado, como hoy (R45, T35) |
| Línea de otro contrato (**D2**, 2026-10-06) | Opción a, con el matiz del humano: «no debería ocurrir nunca lo de casar con otro contrato diferente». Una línea casada con una línea de otro contrato ⇒ `revisar` con `linea_de_otro_contrato`, sin llamar a sigrid-api, y ANOMALÍA en el log (fallo aguas arriba, sv5/sv6; no se tocan). La medición cuenta cuántas hay ya (R46, T36, T37) |
| Reingreso de un activo y SharePoint (**D3**, 2026-10-07; hallazgos 1 y 3 de la pasada 2) | «Un albarán no se puede pisar». (1a) Si el documento reingresado está ACTIVO y tiene un alta bloqueante, la rama de duplicado de sv3 no reescribe clasificación ni contexto de líneas, no resuelve cabecera, no re-enriquece obra ni contratos y no revalora: devuelve duplicado sin tocar nada, con log (mismo criterio que `save` con el de la papelera). (1c) La mirada del alta va **antes de subir el PDF a SharePoint**: en un duplicado conservado no se sube nada, ni activo ni en la papelera (R45, T38, T39) |
| Conciliación manual en sv4 (**D4**, 2026-10-07; hallazgo 2 de la pasada 2) | sv4 **no se cambia**: «la conciliación ya está hecha, el albarán puede o no ir contra líneas de contrato; unas sí y otras no». La conciliación manual con cualquier línea de contrato se queda como está; R46 (`linea_de_otro_contrato` ⇒ `revisar` + ANOMALÍA) sigue como red de seguridad |

## Medición (T0): comando para PowerShell

Solo lectura (`SET TRANSACTION READ ONLY`, solo SELECT). El worktree no tiene `.venv` ni `.env`: se usan los del
árbol principal sin tocarlos. El `.env` de sv3 decide a qué BBDD va; para que la cifra valga, la de Azure (solo
lectura). Según `progress/current.md` ya se ejecutó (3 albaranes activos); repetirla tras T0a es opcional.

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-053\services\albaranes-persistencia
$sv3 = "C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-persistencia"
& "$sv3\.venv\Scripts\python.exe" -m scripts.medir_admisibilidad_f053 --env "$sv3\.env" --csv "$env:TEMP\f053_aprobados.csv"
& "$sv3\.venv\Scripts\python.exe" -m scripts.medir_admisibilidad_f053 --env "$sv3\.env" --todos --csv "$env:TEMP\f053_todos.csv"
```

## Orden

**Medición y F-052 hechas → F-051 en `dev` → F-053** (design §8). F-009 de sigrid-api desplegada antes de T26, T28
y T29. F-061 (medios auxiliares) y F-049 (`paride`) no bloquean.

## Hallazgos que siguen vigentes

1. sv4 pone `approved_at_utc = ahora` en cada guardado aprobado: el disparo es solo el paso de no aprobado a
   aprobado (R1–R2).
2. El deshacer de sv4 restaura filas enteras (`SELECT *`) de merge y valoración: el estado del alta va en
   `albaran_altas_sigrid`, que solo escribe sv9; el producto elegido sí va en la línea valorada (se restaura bien).
3. `features.json` de esta rama no tiene F-051, F-058 ni F-060 y sí F-061: conflicto trivial al fusionar (T0d).
4. «Valorado» comprobado en código (v4): sv4 ya permite valorar a mano sin contrato
   (`add_standalone_valuation_line`, `add_conciliacion_for_merge_line`, cabecera `manual`); «Valorar ahora» borra
   lo manual.

## Riesgo residual

Ninguna escritura real hasta F-009 desplegada y `ALTA_SIGRID_COMMIT=true`. Con la clave de siempre, el único
control de quién escribe es el código y la revisión. El producto por defecto depende de que IA1 clasifique bien
la familia: si se equivoca, lo corrige el administrativo en sv4 antes de aprobar.
