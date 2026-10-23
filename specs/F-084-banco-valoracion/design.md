<!-- specs/F-084-banco-valoracion/design.md -->
# F-084 · El banco de evals valora de verdad — diseño

## 1. Diagnóstico, con evidencia (sin una sola llamada de pago)

Medido sobre `efd73b7`: corrida determinista, doble de LLM por la costura `fabrica`, código.

1. **INPUTS no tiene contrato.** 52 de los 59 fixtures de
   `evals/fixtures/inputs/` traen `contrato_lineas: []` y `condiciones: []`.
   Solo RES-001…RES-007 los tienen (escritos a mano en F-011). `ALQ-001`
   espera precio 170 «de contrato» y su contrato llega vacío.
2. **El determinista falla igual que el LLM.** Sin llamar a ningún modelo, IA3
   da 401 fallos y 390 son «obtenido None»; en los 15 casos de la prueba
   rápida, 14 tienen el mismo número de fallos que con `gpt-6-luna`, y el
   único distinto, RES-001, es uno de los que sí tienen contrato.
3. **El LLM sí se llama, pero no tiene nada que decidir.** Con el doble: 2
   llamadas por caso (IA3 `DocumentoValoracion`, IA4 `DocumentoConciliacion`);
   el texto lleva `"lineas_contrato": []` y la nota `_NOTA_SIN_PDF`. Todo sale
   `no_match`; sv6 deja `precio_unitario_source = none` (`no_price_available`,
   `ia_no_match`…). IA4 concilia contra una lista vacía. Por eso IA3, IA4 y
   E2E salen idénticos con cualquier modelo.
4. **Ya se sabía**: F-045 dejó fuera `CONTRATO_LINEAS` y midió el agujero
   (`progress/impl_F-045_contrato_lineas.md`); nunca tuvo ficha.
5. **El adaptador de sv5 tampoco reproduce producción** (tapado por lo anterior):
   - **Descuento.** No pasa `descuento_albaran` ni `precio_neto_albaran`.
     FER-001 espera 19,41 = 50 × 0,647 × 0,60 y obtiene 32,35 = 50 × 0,647
     (los 9 fallos «con valor» de FER-001/FER-002). `importe_albaran` va crudo;
     sv5 lo deriva en su `SELECT`.
   - **Clasificación.** Sin `clasificacion`, sv5 usa siempre `valuation_es`; en
     producción los 21 RES van con `valuation_residuos`.
   - **Unidad, fecha y cabecera.** `unidad_categoria = unknown` (producción pasa
     por `UnitCategoryPrefilter`), `fecha_albaran = None` y la cabecera del
     contrato (nombre, proveedor, obra) a `None`.
   - **Documento del contrato.** Producción pasa a IA3 el MD (o el PDF) que sv3
     dejó en SharePoint; el banco, nada, y le dice «solo fase 1a».
6. **F-075 midió con `gemini-2.5-flash`**, el defecto del runner, sin registrarlo.

**Conclusión:** el fallo está en el banco (fixtures y adaptador), no en sv5 ni sv6.

## 2. Encaje y límite

- Todo vive en `evals/` (herramienta de desarrollo). Ficha: `servicios =
  ["evals"]`. sv5 se reutiliza **dentro de su subproceso**, como ya hace el
  banco, sin tocar su código.
- **Lo que lee el importador, siempre en solo lectura y lanzado por el humano**:
  sigrid-api (líneas, como ya hace `evals.comparar_obra`), la BBDD `albaranes`
  (`albaran_contratos_merge`, la misma fila que lee sv5) y SharePoint (el
  documento que sv3 ya subió y sv4 sirve en `/documents/{id}/contrato-pdf`).
  No hay integración nueva con documentos de Sigrid ni llamada aparte de fase
  1b: el documento entra en la misma llamada de IA3, como en el pipeline. P1 y
  el límite de servicio no cambian. Se anota en `azure-apps/albaranes.md` §8.
- La SQL de Sigrid es propia (D2 de F-052); se reutiliza
  `ruesma_comun.sigrid.lectura`. La de la BBDD es la de sv5
  (`_SQL_CONTRATO_HEADER`), importada en el subproceso; un test la fija.
- Las líneas entran por el **libro** `INPUTS.xlsx`: el conversor regenera los
  fixtures desde los libros y pisaría el JSON. Los documentos se cachean en
  local (§6) para que la corrida no dependa de la red.
- **El banco no empareja** (P2 = (b), «la IA4 es la que debe encargarse de
  emparejar»): las líneas de contrato llegan a IA3/IA4 como en producción y el
  emparejamiento solo lo mide la corrida con LLM (R36).

## 3. Ficheros a crear

- `evals/contratos.py` — CLI `python -m evals.contratos {lineas,documentos}
  [--dry-run] [--casos A,B]`; escribe `progress/import_F-084.md` (R1–R11, R29–R31, R34).
- `evals/procesos/sv5_documentos.py` — subproceso con sv5 en `sys.path`: lee la
  fila del contrato y descarga el documento (R29, R31, R34).
- `evals/fixtures/contratos/_indice.json` — lo genera `documentos` (R30).
- `tests/test_f084_{contratos,contexto_valoracion,runner}.py` (R1–R36, R25).

## 4. Ficheros a modificar

- `evals/procesos/sv6_build.py` — `lineas_albaran_de(inputs)` y
  `clasificacion_de(inputs)` (puras); `construir_envelope_estimulado` las usa y
  mete `clasificacion` en `context`. Su estímulo de matches NO cambia.
- `evals/procesos/sv5_valoracion.py` — `construir_contexto` usa las dos de
  arriba, la cabecera del índice y `documento_contrato` (§6); `_contexto_de_dict`
  pasa por `RawAlbaranLine` / `RawContratoLine` + `UnitCategoryPrefilter` +
  `ClasificacionAlbaran`; `preparar_contexto(dict) -> dict` (subproceso) deja la
  `unidad_categoria` de producción para el envelope; `valorar` lee el documento
  local y lo pasa a `extract` como `contrato_markdown` o `pdf_attachment`;
  `ejecutar_trabajo` aplica `preparar_contexto` y devuelve además `modelo`.
- `evals/procesos/sv5_modelos.py` (**de F-083**, tras fusionarla): aplica
  `preparar_contexto` igual. Una línea.
- `evals/runner.py` — R18 (determinista y real) y R33 (solo la real, antes de
  montar el trabajo de sv5: el determinista no lee el documento), R19, R20,
  R21 y R36.
- `evals/comparar_modelos.py` (**de F-083**) — R33 en `casos_de_fase` de IA3 e
  IA4: el caso con el documento ausente queda fuera, con su motivo.
- `evals/comparador.py` — R37: `TOLERANCIA_IMPORTE_EUR` = 0,05 y
  `CAMPOS_CON_TOLERANCIA_EUR` (tabla, campo) en `equivalentes_en`. El libro anota
  el importe del papel en céntimos y sv6 no redondea si INPUTS no trae el de la
  línea (FER-002 17,59 frente a 17,5932; total 139,65 frente a 139,66). Sin tocar
  producción ni `criticidad.json` (solo una nota): la criticidad no cambia.
- `evals/modelos.py` (`ResultadoFase.modelos`, `documentos`) y
  `evals/informe.py` (`- Modelo: …`, recuento md/pdf/ninguno y la advertencia
  de R36; las líneas parseables no cambian).
- `evals/revision/escritura.py` — `CLAVES_DE_TABLA["contrato_lineas"]` =
  (`caso_id`, `codigo_producto`, `linea_sigrid`) (R11).
- `evals/README.md` (R26) y `azure-apps/albaranes.md` §8 (commit allí).
- `evals/fixtures/inputs/*.json` — los regenera el conversor tras T12.

## 5. Ficheros que NO se tocan

- `services/**` entero (R23), incluido el descargador y la SQL de sv5, que se
  reutilizan tal cual.
- `evals/revision/reparto.py` (la revisión manual sigue sin alimentar
  `CONTRATO_LINEAS`, decisión de F-045) y `evals/conversor.py` (lee columnas por
  encabezado: acepta `linea_sigrid` sin cambios, se comprueba en T3).
- Los libros IA1–IA4 y `RESULTADO_FINAL`, `evals/criticidad.json`,
  `harness/rutas_sensibles.json`, `MODELOS_POR_PROVEEDOR` (es de F-085) y `.gitignore`
  (`evals/inputs/` ya cubre la caché).

## 6. Funciones y datos (en `evals/`, fuera de la hexagonal de los servicios)

```python
# evals/contratos.py
SQL_LINEAS_CONTRATO: str                                        # §7
def contratos_de_casos(inputs) -> dict[str, list[str]]          # código -> casos SIN líneas (R6)
def filas_de_respuesta(columnas, filas, codigo) -> list[dict]   # 0 o >1 ctr.ide -> ErrorContrato (R5)
def filas_por_caso(lineas, caso_ids, fecha_import) -> list[dict]  # R1, R11
def condiciones_fecha(inputs, ia1) -> list[dict]                # R9
def precios_presentes(ia3, lineas) -> tuple[int, int]           # R10: control, no empareja
class LectorSigrid:                                             # httpx, transport inyectable (R2–R4)
    def lineas(self, codigo: str) -> tuple[list, list]
def entrada_de_indice(codigo, fila, documento) -> dict          # R30, R31 (pura)
def main(argv=None) -> int                                      # 0 ok, 1 algún contrato falló, 2 uso

# evals/procesos/sv5_documentos.py (subproceso: sv5 en sys.path)
def ejecutar_trabajo(trabajo, sesion=None, descargador=None) -> dict  # costuras de test (R25)

# evals/procesos/sv6_build.py
MAPA_FAMILIA_DOCUMENTO = {"Residuos": "residuos", "Hormigon": "hormigon", "Mortero": "mortero",
                          "Combustible": "combustible", "Alquiler": "alquiler_maquinaria"}  # resto: generico
def lineas_albaran_de(inputs) -> list[dict]                     # R12; DescuentoCompuesto (R13)
def clasificacion_de(inputs) -> dict                            # R14; confianza 100, origen "banco_evals"

# evals/procesos/sv5_valoracion.py
def documento_de(codigo, indice, raiz) -> dict | None           # R32/R33 (pura): {tipo, ruta} o falta
def preparar_contexto(contexto: dict) -> dict                   # R15 (subproceso)
```

**Caché del documento (R30).** `evals/inputs/contratos/<código saneado>.md` o
`.pdf`, no versionado: un contrato trae precios de proveedor y datos personales
de firmantes, y los PDF no se versionan nunca. Lo versionado es el índice, sin
contenido: `{codigo: {tipo, sha256, bytes, motivo, nombre_contrato,
cif_proveedor, nombre_proveedor, codigo_obra, nombre_obra, leido_utc}}`. Con el
índice y sin fichero local (clon limpio), el caso sale OMITIDO en la corrida
con LLM y en el comparador (R33): mejor no medir que medir otra cosa. El
determinista no lo lee y no cambia. Preferencia MD > PDF y tope `MAX_PDF_MB` = las de
`ValueAlbaranPipeline`. La sesión de BBDD se abre con
`default_transaction_read_only=on`.

`DescuentoCompuesto`: ERROR de IA3 (y de E2E en el determinista) solo de ese caso.
La `clasificacion` con `origen = "banco_evals"` es el ground truth de IA1: aísla
IA3 de IA1 y no contradice que en producción la decida la IA.

## 7. SQL (solo lectura)

**Sigrid** (sigrid-api, base de negocio): mismas uniones que
`_SQL_HEADER_AND_LINES` de sv3, para que cada columna signifique lo que acaba en
`albaran_contrato_lines_merge`.

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

`max_rows = MAX_FILAS_POR_PETICION`, `timeout_seconds` de `SIGRID_API_TIMEOUT_S`.

**BBDD `albaranes`**: `_SQL_CONTRATO_HEADER` de sv5 (la fila más reciente del código). Sin DDL.

## 8. Coordinación con F-083 (rama `feature/F-083-comparar-modelos`)

| Fichero | F-083 | F-084 |
|---|---|---|
| `evals/procesos/sv5_valoracion.py` | `cliente_llm`, `_clientes_reales(modelo…)`, `servicios()` | contexto, `preparar_contexto`, documento en `valorar`, `modelo` |
| `evals/runner.py` | `comparar_sv2`, `evaluar_valoracion` pública, `_build_sv6(build=)` | R18–R21, R33, R36 |
| `evals/procesos/sv5_modelos.py` | nuevo | una línea: `preparar_contexto` |

**Orden (P7, decidido):** F-083 fusiona primero su código en `dev`; F-084 hace
T1–T6 (no se pisan), fusiona `dev` en su rama y sigue con T7–T10. **Los pagos
de IA3/IA4 de F-083 (la parte IA3 de su T13, y T14–T15) esperan a F-084 en
`dev` con los contratos importados.** El comparador hereda contexto y
documento. F-085 va después de las dos.

## 9. MANUAL del humano (PowerShell, desde el worktree)

Los comandos exactos y vigentes de T12 y T14 están en `progress/current.md`
(bloque «F-084 · MANUAL del humano»): claves y contraseña con
`Read-Host -AsSecureString`, nunca en fichero; nada escribe en Sigrid, la BBDD
ni SharePoint.

**T12 · Importar** (gratis, solo lee; escribe el libro, la caché y el índice
locales): `evals.contratos lineas --dry-run` y `lineas` (sigrid-api),
`documentos` (`PG_*` de Azure en la consola: el `.env` apunta a local;
`SHAREPOINT_*` las del contenedor de sv5; requiere `az login`), conversor y
determinista. Criterio: informe sin contratos fallidos (o con motivo
aceptado), `tipo` por contrato en el índice y R27.

**T14 · Línea base con LLM** (cuesta dinero), con el modelo de producción tras
F-085: `openai` `gpt-6.1-sol` (D1, R20; **pendiente de confirmación del
humano**): estimación sin claves (`evals.comparar_modelos --fase IA3 --modelos
gpt-6.1-sol --estimar`), humo de 3 casos (ALQ-001, GEN-002, RES-010) y los 59,
sin `--proveedores`. Criterio: R28 (puede salir ROJO). Con el documento el
prompt crece: el humo da el coste.

## 10. Riesgos y alternativas descartadas

- **Contrato de hoy, albarán de ayer**: Sigrid da el precio vigente; R10 lo
  enseña caso a caso. **Contratos grandes** (`CTSB23/0964`, 10 casos): prompt
  mayor, como en producción. **Barrido de sensibles**: se redacta, no se apaga.
- **Descartado**: escribir los fixtures JSON a mano (el conversor los pisa);
  sintetizar el contrato desde el ground truth (vía A de F-045); leer las
  líneas de `albaran_contrato_lines_merge` (vía C, circular); versionar los
  documentos (datos personales y PDF); emparejar en el determinista (P2);
  tocar sv5 o sv6 (no es donde está el fallo).

## 11. Decisiones de la PARADA 1 (el humano, 2026-10-20)

- **P1 = (a)**: las líneas, de sigrid-api por código, con el control de R10.
- **P2 = (b)**: sin estímulo por precio ni emparejamiento en el banco; empareja
  IA3/IA4 y lo mide la corrida con LLM; el determinista lo declara (R36).
- **P3 = (a)**: sin contrato tras importar ⇒ OMITIDO (R18).
- **P4 = (a)**: clasificación desde la tipología (R14).
- **P5 = dentro**: IA3 recibe el documento que sv3 ya guardó, en la misma
  llamada (R29–R33); sin integración nueva ni llamada de fase 1b aparte.
- **P6 = (a)**: proveedor de producción por defecto (R20). Tras F-085 es
  `openai` `gpt-6.1-sol` (D1, review 1); el modelo de la línea base de pago
  queda pendiente de confirmación del humano.
- **Review 1 (2026-10-23), opción (a)** propuesta por el líder: R33 solo en la
  corrida con LLM y en el comparador; el determinista no lee el documento.
- **Redondeo (2026-10-23), opción (a) del humano**: «se puede tolerar varios
  céntimos sin problema» → R37, 0,05 € en importes y precios valorados.
- **P7**: F-083 primero en código; sus pagos de IA3/IA4, después de F-084 (§8).
