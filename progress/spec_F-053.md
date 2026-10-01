<!-- progress/spec_F-053.md -->
# Spec F-053 · Alta en Sigrid de los albaranes aprobados (spec-author)

Rama `feature/F-053-alta-sigrid` (worktree `../albaranes-F-053`, desde `dev` c8a295e).
Estado `spec_ready`, rigor `critico`, prioridad 1. v1 del 2026-09-30; v2 y **v3
del 2026-10-01** con las respuestas del humano (preguntas 4, 5, 8, 16 y 17–20).

## Qué hay en la rama

- `specs/F-053-alta-sigrid/requirements.md` — R1–R37 en EARS (148/150 líneas).
- `specs/F-053-alta-sigrid/design.md` — sv9, PRE-1 (sigrid-api), flujo, DDL,
  configuración, orden y cambio de reglas propuesto (247/250).
- `specs/F-053-alta-sigrid/tasks.md` — T0–T30 (+T21b); T0, T22 y T26–T29 MANUAL.
- `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py` y
  `tests/test_f053_medicion_admisibilidad.py` (12 tests en verde; `compileall` ok).
  **No se ha ejecutado contra ninguna BBDD.**
- No se ha llamado a sigrid-api ni a Azure.

## Decisiones del humano (2026-10-01), cerradas

- **4 → «medir antes».** El alcance se fija tras la medición (T0).
- **5 → partida o almacén obligatorio; casar con el contrato, no.**
- **8 → empleado fijo y configurable** (`ALTA_SIGRID_EMPIDE`); «quien aprueba», otra ficha.
- **16 → la clave de siempre.** Riesgo aceptado (design §11).
- **Segunda tanda**, literal: «se deben registrar solo las lineas con importe, se
  pueden registrar lineas que casen en sigrid (se vinculan a lineas de contrato y
  aporta la medicion de esa linea, consume) o que no casen (sin vincular). el
  producto es el de sigrid. [...] negativos, entran ahora. los albaranes no
  valorados no se pueden aprobar ni registrar». Y la regla de producto: «de
  momento siempre va a ser suministro de materiales». Aplicado así:
  - Solo líneas con **importe** = `albaran_line_valuations.importe_calculado`
    no nulo y ≠ 0 (es el importe final, el que suma `total_valorado`) (R13).
  - Un mismo albarán mezcla **vinculadas** (con `ctrpro`; consumen medición:
    `canser`) y **sin vincular** (cierra la 20 a favor de esa lectura) (R11–R12).
  - **Producto**: vinculadas, el de su línea de contrato; sin vincular,
    `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` = `MA9999` («SUMINISTRO DE MATERIALES»),
    por **código**. Elegir entre MA9999, SM9999, SB9999 y QA9999 por familia o
    tipo de contrato queda como mejora futura. Ya no hace falta ficha previa (17, cerrada).
  - **Negativas entran ya** (18, cerrada): sin motivo `cantidad_negativa`; PRE-1
    tiene que admitirlas (design §2: stock, PMP, `canser`).
  - **Sin valorar no se aprueba ni se registra** (19, cerrada): R37 en sv4 y
    `valoracion_no_ok` en sv9. Ver pregunta 21.

## Requisito previo: PRE-1 en sigrid-api

Hoy `sigrid/albaran` solo admite líneas de contrato y copia del `ctrpro` precio,
partida y almacén; `albaran-directo` exige `proide`, no vincula y **hereda** la
partida de la última `dcapro` del producto; ninguno es idempotente ni admite
cantidades negativas. PRE-1 (feature del repo sigrid-api, siguiente id allí:
F-009; detalle en design §2) necesita: `cod_contrato` opcional;
`referencia_externa` → `dca.synckey` con idempotencia; por línea `partida`
(código) o `almacen: true` y `referencia_linea`; vinculadas (`ctrpro_ide`,
consumen `canser`, varias al mismo `ctrpro`) y `lineas_sin_contrato[]` con
**producto por código** (MA9999), descripción, unidad, cantidad y precio;
**cantidades negativas** replicando al escritorio de Sigrid (stock, PMP —hay que
medir si lo recalcula—, `canser` y `estser/estfac`); respuesta por línea y
errores con código. Sin PRE-1 desplegada, F-053 no pasa a `in_progress`.

## Medición (T0): comando para PowerShell

Solo lectura (`SET TRANSACTION READ ONLY`, solo SELECT). El worktree no tiene
`.venv` ni `.env`: se usan los del árbol principal sin tocarlos. El `.env` de
sv3 decide a qué BBDD va; para que la cifra valga, la de Azure (solo lectura).

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-053\services\albaranes-persistencia
$sv3 = "C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-persistencia"
& "$sv3\.venv\Scripts\python.exe" -m scripts.medir_admisibilidad_f053 --env "$sv3\.env" --csv "$env:TEMP\f053_aprobados.csv"
& "$sv3\.venv\Scripts\python.exe" -m scripts.medir_admisibilidad_f053 --env "$sv3\.env" --todos --csv "$env:TEMP\f053_todos.csv"
```

Saca el agregado y un CSV por albarán (UTF-8 BOM, `;`). Cuenta solo líneas con
importe (y aparte las que no tienen, que no se registran), negativas y líneas
con importe sin cantidad; las clasifica en `casa_misma_partida`,
`casa_partida_distinta`, `partida_sin_casar`, `almacen_sin_casar` y
`sin_partida_ni_almacen`; da valorados, con contrato, cabecera completa, cuántas
irían con MA9999 y el % registrable **(a)** con sigrid-api tal cual y **(b)** con
el criterio del humano (valoración `ok`, partida o almacén en todas, negativas
admitidas). Antes de F-051 casi no hay marcas de almacén: (b) sale **por debajo**.

## Hallazgos que siguen vigentes

1. sigrid-api: 400 con texto libre (salvo `concepto-grafico`), 500 lo inesperado.
2. **Ya existe F-013**, pensada con `sql/write`: pregunta 3.
3. Nombre **sv9**: `sv7` = orquestador retirado, `sv8` = `ca-sv8-aprendizaje`.
4. sv4 pone `approved_at_utc = ahora` en cada guardado aprobado: el disparo es
   solo el paso de no aprobado a aprobado (R1–R2).
5. El deshacer de sv4 restaura la fila del merge: el estado del alta va en
   `albaran_altas_sigrid`, que solo escribe sv9.
6. `features.json` de esta rama no tiene F-051 ni F-052: conflicto trivial al fusionar.

## Orden

**Medición → PRE-1 en sigrid-api → F-052 → F-051 → F-053** (design §8).

## Preguntas abiertas (PARADA 1)

Cerradas: 4, 5, 8, 16, 17, 18, 19 y 20. El resto sigue con la propuesta por
defecto; las respuestas de hoy solo cambian lo que se indica.

1. **Servicio nuevo sv9 dentro del monorepo** (propuesta) o proyecto aparte.
2. **Cola**: sv9 consume `q-feedback`; un futuro servicio de aprendizaje
   necesitaría su propia cola. ¿De acuerdo, y con el nombre sv9?
3. **F-013**: ¿se cierra como sustituida por F-053? No se ha tocado su estado.
6. **Duplicados por CIF + «Referencia» (`entref`)**: ¿al dar de alta a mano se
   pone el número del proveedor en «Referencia»? Lo nuestro se reconoce por
   `synckey` (PRE-1); la búsqueda queda para las altas hechas a mano.
7. **Tolerancia** 0,05 € por línea y avisos bloqueantes («plantilla de otro
   proveedor», «sin histórico de dcapro»; ¿también «supera lo pendiente de
   servir»?). Ahora se compara línea a línea, también las sin vincular y negativas.
9. **Adjunto**: ¿qué usuario de Sigrid va en `usu`? Y confirmar en solo lectura
   que `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` incluye `0` y la firma de PDF está en
   `SIGRID_DOCUMENT_ALLOWED_MAGIC`.
10. **Simulados al pasar a real**: no se graban solos; uno a uno desde la ficha.
11. **Re-aprobación de históricos**: desaprobar y aprobar cuenta como nueva.
12. **F-015** (tachadas): se excluyen cuando llegue. El «solo llevar» de F-006
    ya queda fuera por no tener importe.
13. **DDL en sv3** (propuesta) o sv9 dueño de su tabla, como sv6.
14. **Registrado = bloqueado en sv4**; se corrige anulando en Sigrid y «Ya lo he
    anulado».
15. **Documentación ajena**: fila de `azure-apps/sigrid_api.md` §10 y regla del
    `CLAUDE.md` (redacción en design §9), con tu visto bueno.
21. **Nueva — no aprobar sin valorar (R37).** (a) ¿Va dentro de F-053 (propuesta:
    es pequeño y sv4 ya se toca) o en una ficha previa? (b) «Valorado» =
    valoración en `status` `ok`; ¿`partial` cuenta como valorado? (propuesta: no).
    (c) Se aplica siempre, aunque el alta esté apagada: cambia el comportamiento
    de hoy. (d) Consecuencia: sv6 solo valora contra un contrato, así que **un
    albarán sin contrato no se podrá aprobar**; ¿es lo que quieres, o hay que
    valorar sin contrato (ficha de sv5/sv6)?

## Riesgo residual

Ninguna escritura real hasta PRE-1 desplegada y `ALTA_SIGRID_COMMIT=true`. Con
la clave de siempre, el único control de quién escribe es el código y la revisión.
