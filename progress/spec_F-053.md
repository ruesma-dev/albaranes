<!-- progress/spec_F-053.md -->
# Spec F-053 · Alta en Sigrid de los albaranes aprobados (spec-author)

Rama `feature/F-053-alta-sigrid` (worktree `../albaranes-F-053`, desde `dev` c8a295e). Rigor `critico`,
prioridad 1. v1 del 2026-09-30; v2–v5 del 2026-10-01; **v6 del 2026-10-05** (producto genérico por línea,
F-051 v4 y huecos del contrato con sigrid-api). Estado: **vuelve a `pending`** con las **7 preguntas** de abajo
(P1–P7); con ellas respondidas, `spec_ready` y PARADA 1.

## Qué hay en la rama

- `specs/F-053-alta-sigrid/requirements.md` — R1–R44 en EARS (149/150 líneas).
- `specs/F-053-alta-sigrid/design.md` — sv9, códigos → estados (§2, la forma del contrato ya no se copia: se
  enlaza), producto, flujo, DDL, configuración, orden (250/250).
- `specs/F-053-alta-sigrid/tasks.md` — T0a, T0b, T0c, T0, T1–T30 con T2b, T19b y T21b; T0b, T0c, T0, T22 y
  T26–T29 son MANUAL del humano.
- Script de medición y sus tests (sin cambios en v6; T0a los alinea con F-051 v4). Ningún fichero de código
  tocado en v6. No se ha llamado a sigrid-api, Azure ni BBDD.
- Contrato con sigrid-api actualizado en su repositorio (commit aparte en `sigrid-api`, rama
  `feature/F-009-alta-albaran-compra`): `specs/F-009-alta-albaran-compra/contrato_albaranes.md` **v6.1**.

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
| Familia `medios_auxiliares` | No existe; no va en F-053 (P1). Mientras tanto la clave del mapeo no casa y los andamios salen MA9999 salvo que el administrativo elija XA9999 |

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
R12) y **H20** (cerrado por la decisión de producto de este 2026-10-05; queda la puerta M9, P7). `precio_negativo`
→ `error` y no `revisar`: sv9 nunca manda precio negativo, así que si llega es un fallo, no un dato que revisar.
El nombre `analitica_no_resuelta` (H10) es propuesta del contrato a F-009; si elige otra salida, se ajusta la fila.

## Preguntas abiertas al humano (cerradas, con recomendación)

- **P1 · Familia `medios_auxiliares` (XA9999)**: ¿dentro de F-053, ficha previa propia, o con F-060?
  **Recomendación: ficha propia** (id libre comprobado en los worktrees locales: F-061), **ni dentro de F-053 ni
  previa ni fusionada con F-060**. Motivos: es ruta sensible (prompt de IA1, `contexto_linea.TipoFamilia`
  copiado idéntico en sv2/sv3/sv5, evals) con otro ritmo y otro rigor; F-053 está en su tope de tamaño; F-053 no
  la necesita (el administrativo elige XA9999 a mano y la clave del mapeo espera); F-060 (acopiables) es una
  política **sobre** las familias y la usará, así que F-061 conviene antes de F-060 y en serie con ella (las dos
  tocan el prompt). F-007 no se ve afectada. Alcance propuesto: entrada en `CATALOGO` (documento y línea), señales
  (andamio, puntal, plataforma…; qué la distingue de `alquiler_maquinaria`), `TipoFamilia`, prompt de fase 1 y
  casos de evals; sin prompt de fase 2 ni de valoración propios (cae al genérico) y fuera de
  `FAMILIAS_DESTINADAS` hasta F-060.
- **P2 · H8, signos**: descuento (cantidad > 0, importe < 0) o lectura incoherente (cantidad < 0, importe > 0).
  Hoy R12 pone el signo del importe y el descuento viajaría como **devolución** (resta `canser` y stock).
  **Recomendación**: `revisar` con motivo `signo_incoherente` sin llamar a sigrid-api (el descuento comercial, a
  mano en Sigrid, como ya decidió el humano para F-009). Descartado: excluir la línea y grabar el resto (aproximado).
- **P3 · H9, reintento tras anular**: depende de M17b de F-009 (¿anular en Sigrid borra el `con` o lo marca?).
  **Recomendación**: esperar a M17b; si borra, nada cambia; si marca, F-053 usa `ALB-{document_id}-{n}` tras cada
  `anulado` y R14/R28 excluyen la marca. Hasta entonces R14, R28 y `referencia_en_conflicto` quedan como están.
- **P4 · H17, `paride`**: con 4.312 códigos de partida repetidos entre imputables (M3), sin `paride` puede salir
  `partida_ambigua`. **Recomendación**: F-053 manda `paride` en cuanto F-049 conserve el `ide` de la partida
  elegida; mientras, no lo manda y `partida_ambigua` → `no_admitido` (el revisor elige otra o la deja sin
  partida). ¿Se acepta esa salida provisional o F-053 espera a F-049?
- **P5 · H29**: confirmar que una **vinculada** con cantidad y sin importe (precio 0 o «solo llevar») no se manda
  (no consume medición ni stock). **Recomendación**: sí, como ya se decidió «solo líneas con importe» (R13).
- **P6 · H30, ALM impreso**: sv6 la deja sin vincular (va con el producto por defecto) aunque casara con el
  contrato. **Recomendación**: dejarlo así en F-053; si debe vincular, es cambio de sv6 en F-060/F-007.
- **P7 · H28 y puerta H20**: las mediciones pendientes de F-009 (T0b-bis: M9, M11, M14b, M16b, M17b) deben
  cubrir ahora **XA9999** y M16b debe medir la regla del contrato H10 (analítica = la de la última sin vincular del
  mismo producto en la misma obra). **Urgente**: en sigrid-api (`a7517af`) T0b-bis está lista para que la lance
  el humano y su script (`scripts/medir_f009_t0.py`) **no** incluye `XA9999` (`PRODUCTOS_GENERICOS`,
  `LISTA_BLANCA_GENERICOS`) ni esa regla en M16b. **Recomendación**: ampliarlo en sigrid-api antes de lanzar
  T0b-bis (una sola repetición); sin M9 cerrada para los tres productos no hay modo real.

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
| Negativas | Entran ya (signos incoherentes: P2) |
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

**Medición → F-009 de sigrid-api → F-052 → F-051 → F-053** (design §8). La ficha de medios auxiliares (P1) no
bloquea. F-009 debe absorber en su próxima versión lo del contrato §8 (lista blanca con XA9999, regla H10, M9/M11/
M16b con XA9999, H5 cerrado).

## Hallazgos que siguen vigentes

1. sv4 pone `approved_at_utc = ahora` en cada guardado aprobado: el disparo es solo el paso de no aprobado a
   aprobado (R1–R2).
2. El deshacer de sv4 restaura filas enteras (`SELECT *`) de merge y valoración: el estado del alta va en
   `albaran_altas_sigrid`, que solo escribe sv9; el producto elegido sí va en la línea valorada (se restaura bien).
3. `features.json` de esta rama no tiene F-051, F-052 ni F-058/F-060: conflicto trivial al fusionar.
4. «Valorado» comprobado en código (v4): sv4 ya permite valorar a mano sin contrato
   (`add_standalone_valuation_line`, `add_conciliacion_for_merge_line`, cabecera `manual`); «Valorar ahora» borra
   lo manual.

## Riesgo residual

Ninguna escritura real hasta F-009 desplegada y `ALTA_SIGRID_COMMIT=true`. Con la clave de siempre, el único
control de quién escribe es el código y la revisión. El producto por defecto depende de que IA1 clasifique bien
la familia: si se equivoca, lo corrige el administrativo en sv4 antes de aprobar.
