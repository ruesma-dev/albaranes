<!-- specs/F-084-banco-valoracion/design.md -->
# F-084 · El banco de evals valora de verdad — diseño

## 1. Diagnóstico, con evidencia (sin una sola llamada de pago)

Medido sobre `efd73b7` con la corrida determinista, un doble de cliente LLM
metido por la costura `fabrica` de `sv5_valoracion.ejecutar_trabajo`, y el código.

1. **INPUTS no tiene contrato.** 52 de los 59 fixtures de
   `evals/fixtures/inputs/` traen `contrato_lineas: []` y `condiciones: []`.
   Solo RES-001…RES-007 los tienen (6 o 1 líneas, escritas a mano en F-011).
   `ALQ-001` espera precio 170 «de contrato» y su contrato llega vacío.
2. **El determinista falla igual que el LLM.** Sin llamar a ningún modelo, IA3
   da 401 fallos y 390 son «obtenido None»; en los 15 casos de la prueba
   rápida, 14 tienen el mismo número de fallos que con `gpt-6-luna`, y el
   único distinto, RES-001, es uno de los que sí tienen contrato.
3. **El LLM sí se llama, pero no tiene nada que decidir.** Con el doble: 2
   llamadas por caso (IA3 `DocumentoValoracion`, IA4 `DocumentoConciliacion`);
   el texto lleva `"lineas_contrato": []` y la nota `_NOTA_SIN_PDF` («solo fase
   1a, no emitas sintéticas»). Todo sale `no_match`; sv6 deja
   `precio_unitario_source = none` con `no_price_available`, `ia_no_match`,
   `contract_unit_unknown`… (traza de ALQ-001). IA4 concilia contra una lista
   vacía. Por eso IA3, IA4 y E2E salen idénticos con cualquier modelo.
4. **Ya se sabía y no tuvo ficha.** F-045 dejó fuera `CONTRATO_LINEAS` a
   propósito (su design §3; `evals/revision/reparto.py`, `TABLAS["INPUTS"]`) y
   el 2026-09-16 midió ~865 fallos sin información y recomendó leer los
   contratos por sigrid-api (`progress/impl_F-045_contrato_lineas.md`, vía B).
5. **El adaptador de sv5 tampoco reproduce producción** (tapado por lo
   anterior):
   - **Descuento.** `construir_contexto` no pasa `descuento_albaran` ni
     `precio_neto_albaran` (el doble los ve `null`). FER-001 espera
     19,41 = 50 × 0,647 × 0,60 y obtiene 32,35 = 50 × 0,647: son los 9 fallos
     «con valor» de FER-001/FER-002. Y `importe_albaran` va crudo; sv5 lo
     deriva en su `SELECT` si el albarán no lo trae.
   - **Clasificación.** Sin `clasificacion`, sv5 usa siempre `valuation_es`; en
     producción los 21 RES van con `valuation_residuos`
     (`familias.prompt_valoracion_de`): se mide un prompt que no corre.
   - **Unidad y fecha.** Todo llega `unidad_categoria = unknown` (producción
     pasa por `UnitCategoryPrefilter`) y `fecha_albaran = None` (M1 por año).
   - **Documento del contrato.** Producción pasa a IA3 el MD (o el PDF) del
     contrato; el banco ninguno: fase 1b y sus sintéticas fuera (P5).
6. **La línea base de F-075 no usó el modelo de producción**: sin
   `--proveedores`, `_corrida_valoracion_real` usa `gemini`
   (`gemini-2.5-flash`) y el informe no registra el modelo (también en F-083).

**Conclusión:** el fallo está en el banco (fixtures y adaptador), no en sv5 ni sv6.

## 2. Encaje y límite

- Todo vive en `evals/` (herramienta de desarrollo, no servicio). La ficha
  lista sv5 y sv6 en `servicios`; no se toca ninguno (el líder puede corregirlo).
- **Consumo nuevo de sigrid-api**: una lectura por código de contrato, desde
  local, lanzada por el humano, como ya hace `evals.comparar_obra` con las
  obras. Se anota en `azure-apps/albaranes.md` §8 en el mismo trabajo.
- SQL propia del importador (D2 de F-052: la SQL no se comparte); se reutiliza
  `ruesma_comun.sigrid.lectura` (`comprobar_truncado`, `PoliticaTruncado`,
  `MAX_FILAS_POR_PETICION`).
- Las líneas entran por el **libro** `INPUTS.xlsx`, no por los fixtures: el
  conversor regenera los fixtures desde los libros y pisaría el JSON.

## 3. Ficheros a crear

- `evals/contratos_sigrid.py` — escribe `progress/import_F-084.md`; CLI `python -m evals.contratos_sigrid
  [--dry-run] [--casos A,B] [--ground-truth DIR] [--informe RUTA]` (R1–R11).
- `tests/test_f084_contratos_sigrid.py` — R1–R11, R25 (sigrid-api con
  `httpx.MockTransport`, libro de prueba en `tmp_path` con openpyxl).
- `tests/test_f084_contexto_valoracion.py` (R12–R17, R22, R24) y
  `tests/test_f084_runner.py` (R18–R21).

## 4. Ficheros a modificar

- `evals/procesos/sv6_build.py` — `lineas_albaran_de(inputs)` y
  `clasificacion_de(inputs)` (puras); `construir_envelope_estimulado` las usa,
  mete `clasificacion` en `context` y aplica el estímulo por precio (R22).
- `evals/procesos/sv5_valoracion.py` — `construir_contexto` usa las dos de
  arriba; `_contexto_de_dict` construye `RawAlbaranLine` / `RawContratoLine`,
  los pasa por `UnitCategoryPrefilter` y valida la `ClasificacionAlbaran`;
  `preparar_contexto(dict) -> dict` (subproceso) deja la `unidad_categoria` de
  producción también para el envelope; `ejecutar_trabajo` la aplica a cada
  caso y devuelve además `modelo`.
- `evals/procesos/sv5_modelos.py` (**de F-083**, solo tras fusionarla): su
  `ejecutar_trabajo` aplica `preparar_contexto` igual. Una línea.
- `evals/runner.py` — R18 en `corrida_determinista` y en
  `_corrida_valoracion_real` (antes de montar el trabajo de sv5), R19 en
  `corrida_completa`, R20 (proveedor por defecto) y R21 (modelo a la fase).
- `evals/modelos.py` (`ResultadoFase.modelos`) y `evals/informe.py`
  (`- Modelo: …` y «Entradas no reproducidas», R17, R21; parseables iguales).
- `evals/revision/escritura.py` — `CLAVES_DE_TABLA["contrato_lineas"]` =
  (`caso_id`, `codigo_producto`, `linea_sigrid`) (R11).
- `evals/README.md` — sección «Líneas de contrato desde Sigrid» (R26).
- `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` §8 (otro
  repositorio, commit local allí): la lectura por código desde `evals`.
- `evals/fixtures/inputs/*.json` — los regenera el conversor tras la MANUAL
  T11; se versionan en T12.

## 5. Ficheros que NO se tocan

- `services/**` entero: sv5 y sv6 hacen lo correcto con lo que reciben (§1).
  Ni prompts, ni schemas, ni clientes LLM, ni redes (R23).
- `evals/revision/reparto.py`: la revisión manual sigue sin alimentar
  `CONTRATO_LINEAS` (decisión de F-045); el importador nuevo es otro módulo.
- `evals/conversor.py`: lee columnas por encabezado y acepta `linea_sigrid`
  sin cambios (se comprueba en T3).
- Los libros IA1–IA4 y `RESULTADO_FINAL` (solo se escribe INPUTS),
  `evals/criticidad.json`, `harness/rutas_sensibles.json` y
  `MODELOS_POR_PROVEEDOR` (el modelo va por entorno; el defecto es de F-085).

## 6. Funciones (en `evals/`, fuera de la hexagonal de los servicios)

```python
# evals/contratos_sigrid.py
SQL_LINEAS_CONTRATO: str                                        # §7
def contratos_de_casos(inputs) -> dict[str, list[str]]          # código -> casos SIN líneas (R6)
def filas_de_respuesta(columnas, filas, codigo) -> list[dict]   # >1 ctr.ide -> ErrorContrato (R5)
def filas_por_caso(lineas, caso_ids, fecha_import) -> list[dict]  # R1, R11
def condiciones_fecha(inputs, ia1) -> list[dict]                # R9
def cobertura(ia3, lineas) -> dict[int, str]                    # num_linea -> unica|varias|ninguna (R10)
class LectorSigrid:                                             # httpx, transport inyectable (R2–R4)
    def lineas(self, codigo: str) -> tuple[list, list]
def ejecutar(opciones, entorno, lector=None) -> InformeImport   # con escritura.* (R6–R8)
def main(argv=None) -> int                                      # 0 ok, 1 contrato fallido, 2 uso

# evals/procesos/sv6_build.py
MAPA_FAMILIA_DOCUMENTO = {"Residuos": "residuos", "Hormigon": "hormigon", "Mortero": "mortero",
                          "Combustible": "combustible", "Alquiler": "alquiler_maquinaria"}  # resto: generico
def lineas_albaran_de(inputs) -> list[dict]                     # R12; DescuentoCompuesto (R13)
def clasificacion_de(inputs) -> dict                            # R14; confianza 100, origen "banco_evals"
def estimulo_por_precio(fila_ia3, lineas_contrato) -> tuple[int | None, str]  # R22

# evals/procesos/sv5_valoracion.py (subproceso)
def preparar_contexto(contexto: dict) -> dict                   # R15
```

`DescuentoCompuesto` sube por `valorar` y `procesar_casos` lo aísla como ERROR
de IA3; en el determinista el runner lo da como ERROR de IA3 y E2E del caso.

La `clasificacion` con `origen = "banco_evals"` es el ground truth de IA1 (la
tipología la puso el humano), no una regla: aísla IA3 de IA1 y no contradice
que en producción la clasificación la decida la IA.

## 7. SQL (sigrid-api, base de negocio, solo lectura)

Sin DDL. Una sentencia en `evals/contratos_sigrid.py`, con las mismas uniones
que `_SQL_HEADER_AND_LINES` de sv3, para que cada columna signifique lo mismo
que lo que acaba en `albaran_contrato_lines_merge` y lee sv5:

```sql
SELECT ctr.ide AS contrato_ide, ctrpro.ide AS linea_sigrid,
       con_pro.cod AS codigo_producto, ctrpro.res AS descripcion_recurso,
       ctrpro.unimed AS unidad, ctrpro.pre AS precio_unitario,
       obrparpar.cod AS codigo_partida
FROM ctr
JOIN con AS con_ctr      ON ctr.ide = con_ctr.ide
JOIN ctrpro              ON ctrpro.docide = ctr.ide
LEFT JOIN pro            ON ctrpro.proide = pro.ide
LEFT JOIN con AS con_pro ON pro.ide = con_pro.ide
LEFT JOIN obrparpar      ON ctrpro.paride = obrparpar.ide
WHERE con_ctr.cod = ? AND con_ctr.emp = 1
ORDER BY ctr.ide, ctrpro.pos, ctrpro.ide
```

`max_rows = MAX_FILAS_POR_PETICION`, `timeout_seconds` de
`SIGRID_API_TIMEOUT_S` (30 por defecto); ~20 contratos, una petición cada uno.

## 8. Coordinación con F-083 (rama `feature/F-083-comparar-modelos`)

| Fichero | F-083 | F-084 |
|---|---|---|
| `evals/procesos/sv5_valoracion.py` | `cliente_llm`, `_clientes_reales(modelo…)`, `servicios()` | `construir_contexto`, `_contexto_de_dict`, `preparar_contexto`, `ejecutar_trabajo` (+`modelo`) |
| `evals/runner.py` | `comparar_sv2`, `evaluar_valoracion` pública, `_build_sv6(build=)` | R18–R21 |
| `evals/procesos/sv5_modelos.py` | nuevo | una línea: `preparar_contexto` |
| `sv6_build.py`, `contratos_sigrid.py`, `escritura.py`, `informe.py`, `modelos.py` | no | sí |

**Orden recomendado (P7):** F-083 fusiona primero su código en `dev`; F-084
hace T1–T5 (no se pisan), fusiona `dev` en su rama y sigue con T6–T9. **Los
pagos de IA3/IA4 de F-083 (la parte IA3 de su T13, y T14–T15 en IA3/IA4)
esperan a F-084 en `dev` con los fixtures importados**: hoy medirían la tabla
vacía y todos los modelos saldrían iguales. IA1/IA2 de F-083 no dependen de
F-084. El comparador usa `construir_contexto` y `servicios()`, así que hereda
los arreglos con solo la línea de `sv5_modelos.py`. F-085 va después de las dos.

## 9. MANUAL del humano (PowerShell, desde el worktree)

**T11 · Importar** (solo lee Sigrid; escribe el libro local, que no se versiona):

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-084
$env:SIGRID_API_BASE_URL = "<url de sigrid-api>"
$env:SIGRID_API_DATABASE = "ruesma"
$s = Read-Host -AsSecureString "SIGRID_API_FUNCTION_KEY"
$env:SIGRID_API_FUNCTION_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
python -m evals.contratos_sigrid --dry-run
python -m evals.contratos_sigrid
python -m evals.conversor
python -m evals.runner --feature F-084
Remove-Item Env:SIGRID_API_FUNCTION_KEY
```

Criterio: `progress/import_F-084.md` sin contratos fallidos (o con motivo
aceptado) y R27. Las coberturas «ninguna» se miran a mano: precio cambiado
desde el albarán o ground truth a corregir.

**T13 · Línea base con LLM** (cuesta dinero; si F-083 ya está en `dev`, antes
`python -m evals.comparar_modelos --fase IA3 --modelos claude-opus-4-8
--estimar`). Humo con 3 casos y luego los 59:

```powershell
$s = Read-Host -AsSecureString "ANTHROPIC_API_KEY"
$env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$env:ANTHROPIC_MODEL = "claude-opus-4-8"
python -m evals.runner --con-llm --fases IA3,IA4,E2E --proveedores claude --casos ALQ-001,GEN-002,RES-010 --feature F-084-humo
python -m evals.runner --con-llm --fases IA3,IA4,E2E --proveedores claude --feature F-084
Remove-Item Env:ANTHROPIC_API_KEY
```

Criterio: R28. El veredicto puede ser ROJO: se exige que mida, no que acierte.

## 10. Riesgos y alternativas descartadas

- **Contrato de hoy, albarán de ayer.** Sigrid da el precio vigente y hay casos
  de 2023 a 2026. La cobertura de R10 lo enseña caso a caso en vez de
  esconderlo en un rojo; si pesa, se replantea P1.
- **Contratos grandes** (`CTSB23/0964`, 10 casos): las líneas se repiten por
  caso y el prompt crece, como en producción. **Barrido de sensibles** del
  conversor: si salta, se redacta en el libro, nunca se desactiva.
- **Descartado**: escribir los fixtures JSON directamente (el conversor los
  pisa); sintetizar el contrato desde el ground truth (vía A de F-045: da la
  respuesta como entrada y mata los señuelos); leer
  `albaran_contrato_lines_merge` de producción (vía C: circular); tocar sv5 o
  sv6 (no es donde está el fallo).

## 11. Preguntas abiertas (PARADA 1), con recomendación

- **P1 · Fuente de las líneas de contrato.** (a) sigrid-api por código;
  (b) sintetizarlas del ground truth; (c) lo persistido en producción.
  **(a)**, con la cobertura de R10 como control de la fecha.
- **P2 · Estímulo por precio en el determinista (R22).** (a) sí, solo si la
  línea es única; (b) no. **(a)**: mide gratis partida, descuento e importe de
  sv6 en los 52 casos, y lo ambiguo se declara.
- **P3 · Casos sin contrato tras importar (R18).** (a) OMITIDO con motivo;
  (b) ROJO, como hoy. **(a)**: un rojo que no dice nada del sistema tapa los
  que sí, y no se paga por él.
- **P4 · Clasificación desde la tipología (R14).** (a) sí; (b) sin ella, como
  hoy. **(a)**: sin ella, los 21 RES se miden con un prompt que no corre.
- **P5 · Documento del contrato (fase 1b).** (a) fuera, declarado (R17), con
  ficha nueva para traer el MD; (b) dentro. **(a)**: es otra integración
  (documentos de Sigrid, conversión Word/PDF) y dobla la feature.
- **P6 · Proveedor por defecto de IA3/IA4 (R20).** (a) el de producción; (b) `gemini`.
  **(a)**: el defecto tiene que medir lo que corre.
- **P7 · Orden con F-083 (§8).** F-083 primero en código; sus pagos de IA3/IA4, después.
