<!-- progress/spec_F-053.md -->
# Spec F-053 · Alta en Sigrid de los albaranes aprobados (spec-author)

Rama `feature/F-053-alta-sigrid` (worktree `../albaranes-F-053`, desde `dev` c8a295e).
Estado `spec_ready`, rigor `critico`, prioridad 1. v1 del 2026-09-30; **v2 del
2026-10-01** con las respuestas del humano a las preguntas 4, 5, 8 y 16.

## Qué hay en la rama

- `specs/F-053-alta-sigrid/requirements.md` — R1–R36 en EARS (144/150 líneas).
- `specs/F-053-alta-sigrid/design.md` — sv9, PRE-1 (sigrid-api), flujo, DDL,
  configuración, orden y cambio de reglas propuesto (245/250).
- `specs/F-053-alta-sigrid/tasks.md` — T0–T30; T0, T22 y T26–T29 MANUAL del humano.
- `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py` y
  `tests/test_f053_medicion_admisibilidad.py` (10 tests en verde; `compileall` ok).
  **No se ha ejecutado contra ninguna BBDD.**
- No se ha llamado a sigrid-api ni a Azure.

## Decisiones del humano (2026-10-01), cerradas

- **Pregunta 4 → «medir antes».** El alcance se fija tras la medición (T0).
- **Pregunta 5 → criterio de partida.** Literal: «aunque no casa con el contrato
  no pasa nada. sin registrar sin vincular con lineas de contrato. lo importante
  es que si no es almacen se vincule a partida». Lectura aplicada (la del líder):
  casar con el contrato NO es requisito; las líneas que casan se vinculan a su
  línea de contrato, las demás se dan de alta sin vínculo; requisito duro: cada
  línea con partida, salvo almacén (F-051). Otra lectura posible: pregunta 20.
- **Pregunta 8 → empleado fijo y configurable** (`ALTA_SIGRID_EMPIDE`); «quien
  aprueba» será otra ficha, fuera de F-053.
- **Pregunta 16 → la clave de siempre.** Riesgo aceptado y anotado (design §11):
  quien tenga la clave por defecto puede grabar en Sigrid.

## Consecuencia: F-053 depende de una feature de sigrid-api (PRE-1)

**Con el criterio del humano, sigrid-api no basta hoy** (leído en su código,
`dev` 2a5ac24; `sigrid-api-v2` es una copia de julio sin git):
- `sigrid/albaran` solo admite líneas de contrato y copia del `ctrpro` precio,
  partida (`paride`) y almacén: no hay forma de elegir la partida de una línea ni
  de meter líneas sin contrato.
- `sigrid/albaran-directo` exige el `proide` de Sigrid por línea (no lo tenemos),
  no vincula con contrato y con `paride` nulo **hereda** la partida de la última
  `dcapro` del producto (convertiría almacén en una partida ajena).
- Ninguno es idempotente (`dca.synckey` existe y no se usa).

Requisito previo **PRE-1**, a especificar e implementar en el repositorio
sigrid-api (allí el siguiente id libre es F-009): detalle de campos en
design §2. En resumen: `cod_contrato` opcional; `referencia_externa` →
`dca.synckey` con idempotencia; por línea `partida` (código resuelto contra la
obra) o `almacen: true`, y `referencia_linea`; `lineas_sin_contrato[]` con
descripción, unidad, cantidad, precio y producto; respuesta por línea y errores
con código. Sin PRE-1 desplegada, F-053 no pasa a `in_progress`.

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

Saca el agregado por pantalla y el detalle por albarán en CSV (UTF-8 BOM, `;`):
líneas con cantidad, `casa_misma_partida`, `casa_partida_distinta`,
`partida_sin_casar`, `almacen_sin_casar`, `sin_partida_ni_almacen`, almacén,
negativas, con/sin contrato, cabecera completa, y el % registrable **(a)** con
sigrid-api tal cual y **(b)** con el criterio del humano. Avisos: antes de F-051
casi no hay marcas de almacén, así que (b) sale **por debajo** de lo real; los
albaranes sin líneas valoradas (`no_contract`) se miden con las líneas del merge
y su partida impresa.

## Hallazgos (v1, siguen vigentes)

1. Errores de sigrid-api: 400 con texto libre (salvo `concepto-grafico`), 500 lo
   inesperado. El docstring de `sigrid/albaran` dice «todas las líneas»; el
   código solo incluye las pedidas (R17 vigila las líneas en cada previa).
2. **Ya existe F-013**, pensada con `sql/write`: pregunta 3.
3. Nombre **sv9**: `sv7` = orquestador retirado, `sv8` = `ca-sv8-aprendizaje`.
4. sv4 pone `approved_at_utc = ahora` en cada guardado aprobado: el disparo es
   solo el paso de no aprobado a aprobado (R1–R2).
5. El deshacer de sv4 restaura la fila del merge: el estado del alta va en tabla
   aparte, `albaran_altas_sigrid`, que solo escribe sv9.
6. `features.json` de esta rama no tiene F-051 ni F-052: conflicto trivial al fusionar.

## Orden

**Medición → PRE-1 en sigrid-api → F-052 → F-051 → F-053** (design §8).

## Preguntas abiertas (PARADA 1)

Siguen con la propuesta por defecto salvo lo indicado. Cerradas: 4, 5, 8 y 16.

1. **Servicio nuevo sv9 dentro del monorepo** (propuesta) o proyecto aparte.
2. **Cola**: sv9 consume `q-feedback`; un futuro servicio de aprendizaje
   necesitaría su propia cola. ¿De acuerdo, y con el nombre sv9?
3. **F-013**: ¿se cierra como sustituida por F-053? No se ha tocado su estado.
4. ~~Alcance~~ — **cerrada 2026-10-01**: medir antes (T0).
5. ~~Aprobar lo no admisible~~ — **cerrada 2026-10-01**: casar no es requisito;
   partida o almacén sí. Lo que aun así no sea admisible (sin partida ni almacén,
   cabecera incompleta) se deja aprobar y queda `no_admitido` visible: es la
   propuesta por defecto y la respuesta no la cambia.
6. **Duplicados por CIF + «Referencia» (`entref`)**: ¿al dar de alta a mano se
   pone el número del proveedor en «Referencia»? Cambia con PRE-1: lo nuestro se
   reconoce por `synckey`; la búsqueda queda solo para las altas hechas a mano.
7. **Tolerancia** 0,05 € por línea y avisos bloqueantes («plantilla de otro
   proveedor», «sin histórico de dcapro»; ¿también «supera lo pendiente de
   servir»?). Sin cambios: ahora vale también para las líneas sin contrato.
8. ~~Empleado~~ — **cerrada 2026-10-01**: fijo y configurable.
9. **Adjunto**: ¿qué usuario de Sigrid va en `usu`? Y confirmar en solo lectura
   que `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` incluye `0` y la firma de PDF está en
   `SIGRID_DOCUMENT_ALLOWED_MAGIC`.
10. **Simulados al pasar a real**: no se graban solos; uno a uno desde la ficha.
11. **Re-aprobación de históricos**: desaprobar y aprobar cuenta como nueva.
12. **F-006 / F-015** (no registrar / tachadas): se excluyen en R13 cuando lleguen.
13. **DDL en sv3** (propuesta) o sv9 dueño de su tabla, como sv6.
14. **Registrado = bloqueado en sv4**; se corrige anulando en Sigrid y «Ya lo he
    anulado».
15. **Documentación ajena**: fila de `azure-apps/sigrid_api.md` §10 y regla del
    `CLAUDE.md` (redacción en design §9), con tu visto bueno.
16. ~~Clave propia~~ — **cerrada 2026-10-01**: la de siempre; riesgo anotado.
17. **Nueva — producto de Sigrid de las líneas sin contrato.** Toda `dcapro`
    lleva `proide`, y nosotros no lo tenemos. Opciones para PRE-1: el código de
    producto que traiga el albarán (rara vez es el de Sigrid), un producto
    genérico por partida o familia, o el que diga el maestro de la obra. Decide
    negocio; condiciona el diseño de PRE-1.
18. **Nueva — devoluciones** (cantidad negativa, palets): hoy `no_admitido`
    (`cantidad_negativa`). ¿Entran en F-053 (PRE-1 tendría que admitirlas) o después?
19. **Nueva — albaranes sin contrato seleccionado.** sv6 no valora sus líneas
    (`no_contract`), así que no hay partida final ni marca de almacén: en v1
    quedan `no_admitido` (`valoracion_no_ok`). ¿Se aceptan así, o tendría que
    valorarlos sv6 (otra ficha) para poder darlos de alta?
20. **Nueva — otra lectura de la frase de la pregunta 5**: «no pasa nada. sin
    registrar» podría querer decir que el albarán que no casa **se queda sin
    registrar** (y no pasa nada), y que solo los registrados exigen partida. Con
    esa lectura no harían falta las líneas sin contrato de PRE-1, pero sí la
    partida por línea y la idempotencia. La spec sigue la lectura del líder;
    confírmalo.

## Riesgo residual

Ninguna escritura real hasta PRE-1 desplegada y `ALTA_SIGRID_COMMIT=true`. Con
la clave de siempre, el único control de quién escribe es el código y la revisión.
