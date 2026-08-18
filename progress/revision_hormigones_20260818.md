# Revisión de 4 albaranes de hormigón/mortero — lote `alvaro_17082026`

- **Fecha del análisis**: 2026-08-18
- **Alcance**: albaranes 1229 y 1167 (FABRICACION DE HORMIGONES PAZ DEL
  BARRIO, S.L.) y 225137 y 224964 (HORMIGON SIERRA MADRID, S.L.),
  procesados por el pipeline local entre las 13:35 y las 13:36 UTC del
  2026-08-18.
- **Naturaleza**: análisis de **solo lectura**. No se ha modificado código,
  base de datos, rama ni `harness/features.json`. Este fichero es el único
  añadido.

## Fuentes cruzadas

| Fuente | Referencia |
|---|---|
| BBDD local | PostgreSQL `albaranes` @ localhost:5432 — `albaran_documents_merge`, `albaran_lines_merge`, `albaran_valuations`, `albaran_line_valuations`, `contrato_lines_derived`, `albaran_contrato_lines_merge` |
| Logs IA1/IA2 | `services/albaranes-api/logs/ia/20260818/1335*.json`, `1336*.json` |
| Logs IA3/IA4 | `services/albaran-valoracion-api/logs/ia/20260818/1337*.json`, `1338*.json` |
| PDFs | `C:\Users\pgris\OneDrive - Ruesma\Documentos\albaranes\evals\alvaro_17082026\*.pdf` (escaneados sin texto; leídos renderizando a PNG con `pymupdf` a 200/600 dpi) |
| Ground truth | `alvaro_17082026.xlsx`, hoja `Hoja1`, filtrando por columna `codigo alabran` |
| Derivados (referencia secundaria, pendientes de aprobación) | `derivados_ia\IA1_esperado.xlsx`, `IA2_esperado.xlsx`, `IA3_esperado.xlsx`, `IA4_esperado.xlsx`, `DUDAS_REVISION.xlsx` |
| Reglas | `docs/referencia/dominio_negocio_albaranes.md` §9.2, §9.3, §10.2, §10.3, §10.5, §10.7, §10.8 |

### Correspondencia documento ↔ fichero de log

| Nº albarán | `albaran_documents_merge.id` | IA1 (fase 1) | IA2 (fase 2) | IA3 (valoración) | IA4 (conciliación) |
|---|---|---|---|---|---|
| 224964 | `9e017519-817c-42e0-ba54-4610df70c994` | `133503_218_gemini_8258799b.json` | `133519_748_gemini_b66f376d.json` | `133708_004_claude_a7e83f49.json` | `133715_933_claude_97387a9a.json` |
| 225137 | `4a782d26-ba5f-4e80-afe0-57fb69848b81` | `133527_987_gemini_27825a60.json` | `133540_125_gemini_663e78ed.json` | `133751_136_claude_b618f7af.json` | `133759_991_claude_0808bb8a.json` |
| 1167 | `8dd19cbe-79a5-47ab-9f0a-c0e300f7e365` | `133546_492_gemini_240663f5.json` | `133556_563_gemini_b613f091.json` | `133820_172_claude_05bff10b.json` | `133824_833_claude_63d32d3c.json` |
| 1229 | `76bc23b9-7c37-45b3-a77a-c052e131d237` | `133605_851_gemini_d20a3d6d.json` | `133617_237_gemini_c54777a6.json` | `133840_970_claude_94ec9e17.json` | **no hubo llamada** |

---

## Resumen ejecutivo

| Nº albarán | Total esperado (GT) | Total obtenido (`albaran_valuations.total_valorado`) | Δ | Veredicto |
|---|---|---|---|---|
| 224964 | 475,60 € | 475,60 € | 0,00 € | **Total correcto** (con reparos en partida y líneas de ruido) |
| 225137 | 980,10 € | 980,10 € | 0,00 € | **Total correcto** (idem) |
| 1167 | 871,20 € | 871,20 € | 0,00 € | **Total correcto** (idem) |
| 1229 | 307,50 € | 210,00 € | **−97,50 €** | **Total incorrecto** |

**Los tres albaranes de hormigón cuadran al céntimo con el administrativo.**
El de mortero (1229) se queda a −97,50 € porque el pipeline pierde dos de las
tres líneas y usa un precio que no es el del comparativo.

**Defecto transversal a los cuatro**: el **código de partida manuscrito se lee
mal en los cuatro documentos** (0/4 aciertos). No afecta al importe, pero sí a
la imputación contable, y provoca que sv6 derive líneas de contrato con
literales de partida inexistentes en el catálogo.

---

## 1. Albarán 224964 — HORMIGON SIERRA MADRID, S.L.

PDF: `Hormigon Sierra Madrid_224964.pdf` (1 página, escaneado).

### 1.1 Cabecera

| Campo | Esperado (GT / PDF) | Obtenido (`albaran_documents_merge`) | Veredicto |
|---|---|---|---|
| `numero_albaran` | 224964 (PDF: «Nº ALBARAN 224964») | `224964` | OK |
| `proveedor_nombre` | HORMIGON SIERRA MADRID, S.L. | `HORMIGON SIERRA MADRID, S.L.` | OK |
| `proveedor_cif` | B86738812 (PDF: «C.I.F. B-86738812») | `B86738812` | OK |
| `fecha` | 2026-05-18 (PDF: «FECHA: 18/05/2026») | `2026-05-18` | OK |
| `obra_codigo` | 696 (PDF: «OBRA 696 88+88 VIV KODAK») | `0696` | OK |
| `obra_nombre` | — (canónico de Sigrid) | `88+88 VIVIENDAS KODAK PARC.04/05 - EL QUINTANAR (LAS ROZAS)` | OK |
| `selected_contrato_codigo` | CTSU24/0518 | `CTSU24/0518` (`selected_contrato_origen='auto_unico'`) | OK |
| `confidence_pct_calc` | — | 64,1 · `review_required=true` | Ver §5 (F-020) |

### 1.2 Líneas

Ground truth (3 filas) frente a lo persistido en `albaran_line_valuations`
(6 filas: 1 `from_albaran` + 5 `synthetic_modifier`).

| # | Campo | Esperado (GT / PDF) | Obtenido (BBDD) | Veredicto |
|---|---|---|---|---|
| 1 | concepto | `HORMIGÓN HA-25/B/20/XC2` (PDF: «HA-25/B/20/XC2») | `albaran_lines_merge.concepto` = `HA-25/B/20/XC2` | OK |
| 1 | cantidad | 4 | `cantidad_albaran` = 4.0 | OK |
| 1 | unidad | `M3` (PDF: columna «M³») | `albaran_lines_merge.unidad_medida` = **NULL** | **MAL** → §5.2 |
| 1 | precio unitario | 99,90 (CONTRATO) | `precio_unitario_final` = 99.9, `precio_unitario_source='both_agreed'` | OK |
| 1 | descuento | (vacío) | NULL | OK |
| 1 | importe | 399,60 (CONTRATO) | `importe_calculado` = 399.6 | OK |
| 1 | partida | `P5.03.04` (PDF, manuscrito arriba a la derecha) | `codigo_partida_final` = **`03.04`** | **MAL** → §5.1 |
| 2 | concepto | `CARGA INCOMPLETA` (el Excel pone «INCREM. PRECIO 2026», errata ya conocida) | `descripcion_linea` = `INCREMENTO POR CARGA INCOMPLETA` | OK |
| 2 | cantidad | 2 | `cantidad_albaran` = 2.0 | OK |
| 2 | precio unitario | 20,00 (CONTRATO) | `precio_unitario_final` = 20.0 | OK |
| 2 | importe | 40,00 | `importe_calculado` = 40.0 | OK |
| 2 | partida | `P5.03.04` | `03.04` (heredada de la base) | **MAL** (arrastre de §5.1) |
| 3 | concepto | `INCREM. PRECIO 2026` | `INCREMENTO POR AÑO 2026 EN HORMIGÓN` | OK (equivalente) |
| 3 | cantidad | 4 | 4.0 | OK |
| 3 | precio unitario | 9,00 (CONTRATO) | 9.0 | OK |
| 3 | importe | 36,00 | 36.0 | OK |
| — | **líneas de más** | — | `INCREMENTO POR AÑO 2025 EN HORMIGÓN` (importe NULL), `INCREMENTO POR GESTIÓN DE RESIDUOS EN HORMIGÓN` (importe NULL), `INCREMENTO POR EXCESO DE TIEMPO DE DESCARGA` (0 min, importe 0,00) | Ruido, ver §5.3 y §5.4 |

### 1.3 Total

| | Valor |
|---|---|
| Esperado (GT: 399,60 + 40,00 + 36,00) | **475,60 €** |
| Obtenido (`total_valorado`) | **475,60 €** |
| Diferencia | 0,00 € |

Las tres líneas sintéticas sobrantes salen con importe NULL o 0,00, así que no
alteran el total.

**Este documento es el caso de referencia de carga incompleta y sale
correcto**: `ia_reasoning` de la línea 611 dice literalmente
«cantidad 4 m3 < umbral 6 m3; cargo carga incompleta a 20,00 €/m3 (línea
25716); cantidad = 6-4 = 2 m3». La tarifa existe en el contrato
(`CARGAS INCOMPLETAS`, 20,00 €/m3, partidas P5.98.01 y P5.99.03) y el mínimo
de 6 m³ lo dedujo la IA3 del PDF del contrato.

---

## 2. Albarán 225137 — HORMIGON SIERRA MADRID, S.L.

PDF: `Hormigon Sierra Madrid_225137.pdf` (1 página, escaneado).

### 2.1 Cabecera

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| `numero_albaran` | 225137 | `225137` | OK |
| `proveedor_nombre` | HORMIGON SIERRA MADRID, S.L. | idem | OK |
| `proveedor_cif` | B86738812 | `B86738812` | OK |
| `fecha` | 2026-05-25 (PDF: «FECHA: 25/05/2026») | `2026-05-25` | OK |
| `obra_codigo` | 696 | `0696` | OK |
| `selected_contrato_codigo` | CTSU24/0518 | `CTSU24/0518` | OK |
| `confidence_pct_calc` | — | 62,9 · `review_required=true` | Ver §5 (F-020) |

### 2.2 Líneas

Ground truth (2 filas) frente a 5 filas persistidas.

| # | Campo | Esperado (GT / PDF) | Obtenido (BBDD) | Veredicto |
|---|---|---|---|---|
| 1 | concepto | `HORMIGÓN HA-25/B/20/XC2` | `HA-25/B/20/XC2` | OK |
| 1 | cantidad | 9 (PDF: casilla «M³ = 9») | 9.0 | OK |
| 1 | unidad | `M3` | **NULL** | **MAL** → §5.2 |
| 1 | precio unitario | 99,90 (CONTRATO) | 99.9 (`both_agreed`) | OK |
| 1 | descuento | (vacío) | NULL | OK |
| 1 | importe | 899,10 | 899.1 | OK |
| 1 | partida | `P5.03.09` (PDF, manuscrito) | **`PT.03.09`** | **MAL** → §5.1 |
| 2 | concepto | `INCREM. PRECIO 2026` | `INCREMENTO POR AÑO 2026 EN HORMIGÓN` | OK (equivalente) |
| 2 | cantidad | 9 | 9.0 | OK |
| 2 | precio unitario | 9,00 (CONTRATO) | 9.0 | OK |
| 2 | importe | 81,00 | 81.0 | OK |
| 2 | partida | `P5.03.09` | `PT.03.09` (heredada) | **MAL** (arrastre) |
| — | **líneas de más** | — | `INCREMENTO POR AÑO 2025 EN HORMIGÓN` (NULL), `GESTIÓN DE RESIDUOS (INCLUIDA EN PRECIO)` (NULL), `INCREMENTO POR EXCESO DE TIEMPO DE DESCARGA` (0 min, 0,00 €) | Ruido, §5.3/§5.4 |

Nota de corroboración: la partida real `P5.03.09` del contrato CTSU24/0518
tiene `descripcion_partida` = «H.ARM. HA-25/B/20/XC2 EN ZAPATAS CORRIDAS Y
VIGAS BAJO MURO», y las observaciones manuscritas del PDF dicen «ZAPATA
APOYO LADRILLO BLOQUE D PORTAL 1». Coinciden — el ground truth es sólido.
(Lo mismo en el 224964: `P5.03.04` = «SOLERA HA-25, e=20 cm + ENCACHADO» y el
PDF dice «SOLERA BLOQUE D ZONA SAN JOSE».)

### 2.3 Total

| | Valor |
|---|---|
| Esperado (899,10 + 81,00) | **980,10 €** |
| Obtenido | **980,10 €** |
| Diferencia | 0,00 € |

---

## 3. Albarán 1167 — FABRICACION DE HORMIGONES PAZ DEL BARRIO, S.L.

PDF: `Hormigones Paz del Barrio_1167.pdf` (1 página, escaneado).

### 3.1 Cabecera

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| `numero_albaran` | 1167 | `1167` | OK |
| `proveedor_nombre` | FABRICACION DE HORMIGONES PAZ DEL BARRIO,S.L. (el PDF imprime solo «HORMIGONES PAZ DEL BARRIO») | `FABRICACION DE HORMIGONES PAZ DEL BARRIO,S.L.` (canonizado por CIF en sv3) | OK |
| `proveedor_cif` | B86362290 | `B86362290` | OK |
| `fecha` | 2026-06-05 (PDF: «FECHA DE ENTREGA 05/06/2026») | `2026-06-05` | OK |
| `obra_codigo` | 696 (PDF: «OBRA KODAK LAS ROZAS», sin número) | `0696` | OK |
| `selected_contrato_codigo` | CTSU25/0001 | `CTSU25/0001` | OK |
| `confidence_pct_calc` | — | 66,2 · `review_required=true` | Ver §5 (F-020) |

### 3.2 Líneas

Ground truth (2 filas) frente a 3 filas persistidas.

| # | Campo | Esperado (GT / PDF) | Obtenido (BBDD) | Veredicto |
|---|---|---|---|---|
| 1 | concepto | `HORMIGÓN HA-25/B/20/XC2` | `HA-25/B/20/XC2` | OK |
| 1 | cantidad | 8 (PDF: «CANTIDAD M³ = 8») | 8.0 | OK |
| 1 | unidad | `M3` | **NULL** | **MAL** → §5.2 |
| 1 | precio unitario | 99,90 (CONTRATO) | 99.9 (`both_agreed`) | OK |
| 1 | descuento | (vacío) | NULL | OK |
| 1 | importe | 799,20 | 799.2 | OK |
| 1 | partida | `P4.03.05` (PDF, manuscrito) | **`04.03.05`** | **MAL** → §5.1 |
| 2 | concepto | `INCREM. PRECIO 2026` | `INCREMENTO POR AÑO 2026 EN HORMIGÓN` (derivada `INCREM. AÑO 2026`) | OK (equivalente) |
| 2 | cantidad | 8 | 8.0 | OK |
| 2 | precio unitario | 9,00 (CONTRATO) | 9.0 | OK |
| 2 | importe | 72,00 | 72.0 | OK |
| 2 | partida | `P4.03.05` | `04.03.05` (heredada) | **MAL** (arrastre) |
| — | **línea de más** | — | `INCREMENTO POR EXCESO DE TIEMPO DE DESCARGA` (13 min de descarga, 0 min de exceso, importe 0,00 €) | Ruido, §5.4 |

Aquí IA3 no emitió incremento de 2025 (contrato CTSU25 → solo hay un año de
salto), que es exactamente lo que dice §10.2: «Incremento por año: UNO solo».

### 3.3 Total

| | Valor |
|---|---|
| Esperado (799,20 + 72,00) | **871,20 €** |
| Obtenido | **871,20 €** |
| Diferencia | 0,00 € |

---

## 4. Albarán 1229 — FABRICACION DE HORMIGONES PAZ DEL BARRIO, S.L. (MORTERO)

PDF: `Hormigones Paz del Barrio_1229.pdf` (1 página, escaneado). **Es el único
de los cuatro que no es hormigón: el producto es MORTERO M-7,5.**

### 4.1 Cabecera

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| `numero_albaran` | 1229 | `1229` | OK |
| `proveedor_nombre` | FABRICACION DE HORMIGONES PAZ DEL BARRIO,S.L. | idem (canonizado) | OK |
| `proveedor_cif` | B86362290 | `B86362290` | OK |
| `fecha` | 2026-06-09 (PDF: «FECHA DE ENTREGA 09/06/2026») | `2026-06-09` | OK |
| `obra_codigo` | 696 | `0696` | OK |
| `selected_contrato_codigo` | CTSU25/0001 | `CTSU25/0001` | OK |
| Tipología | MORTERO (columna B del GT) | IA2 usó `prompt_key='albaran_revision_fase2_mortero'` y puso `contexto_linea.tipo_familia='mortero'` | OK |
| `confidence_pct_calc` | — | 70,2 · `review_required=true` | Ver §5 (F-020) |

### 4.2 Líneas

Ground truth: **3 filas**. Persistidas: **1 fila**.

| # | Campo | Esperado (GT / PDF) | Obtenido (BBDD) | Veredicto |
|---|---|---|---|---|
| 1 | concepto | `MORTERO 7,5 - 48H` (PDF: «TIPO DE HORMIGÓN: M-7,5/B/04 48H», consistencia «BLANDA») | `M-7,5/B/04 48H BLANDA` | OK (transcripción literal del impreso) |
| 1 | cantidad | 3 (PDF: «CANTIDAD M³ = 3») | 3.0 | OK |
| 1 | unidad | `M3` | **NULL** | **MAL** → §5.2 |
| 1 | precio unitario | **73,50** (fuente: **OFERTA** = comparativo) | **70,00** (`precio_unitario_source='contract_line_match'`, línea de contrato 25939 `MORTERO M-5`) | **MAL** → §4.4.a |
| 1 | descuento | (vacío) | NULL | OK |
| 1 | importe | **220,50** (OFERTA) | **210,00** | **MAL** (−10,50 €) |
| 1 | partida | `P4.14.01.02.02` (PDF: manuscrito «P4.14.01.02.02») | **`15.01.02.02`** | **MAL** → §5.1 |
| 2 | concepto | `INCREM. PRECIO 2026` | **NO EXISTE** | **FALTA** → §4.4.b |
| 2 | cantidad / precio / importe | 3 · 9,00 (CONTRATO) · **27,00** | — | **FALTA (−27,00 €)** |
| 3 | concepto | `CARGAS INCOMPLETAS` — **impreso en el formulario** («CARGAS INCOMPLETAS: 3») | **NO EXISTE** | **FALTA** → §4.4.c |
| 3 | cantidad / precio / importe | 3 · 20,00 (OFERTA) · **60,00** | — | **FALTA (−60,00 €)** |

### 4.3 Total

| | Valor |
|---|---|
| Esperado (220,50 + 27,00 + 60,00) | **307,50 €** |
| Obtenido | **210,00 €** |
| **Diferencia** | **−97,50 €** |

Desglose de la diferencia:

| Origen | Δ |
|---|---|
| Precio unitario de la base: 70,00 en vez de 73,50 (× 3 m³) | −10,50 € |
| Falta la línea `INCREM. PRECIO 2026` (3 × 9,00) | −27,00 € |
| Falta la línea `CARGAS INCOMPLETAS` (3 × 20,00) | −60,00 € |
| **Total** | **−97,50 €** |

### 4.4 Causa raíz de cada diferencia del 1229

**a) Precio 70,00 en vez de 73,50 — fase IA3.**
El contrato CTSU25/0001 tarifa `MORTERO M-5` a 70,00 €/m³ pero **no** tarifa
M-7,5. IA3 casó por familia con la hermana M-5 y lo dejó explícito en
`pdf_inference_reasoning`: «El PDF/Anexo I no tarifa mortero M-7,5; el pedido
Amp1 solo tarifa MORTERO M-5 a 70,00 €/m3». Puso confianza 40 y
`review_required=true`. El GT toma 73,50 de **OFERTA (comparativo)**, fuente
que hoy el pipeline no consulta.
→ **Cubierto por F-017** («El comparativo como fuente de precio (1c) en la
valoración»). El comportamiento de IA3 es el correcto dado lo que tiene:
según §10.5, «atributo sustantivo distinto ⇒ NO casar», así que dejarlo a
revisión con precio de referencia es defendible; lo que falta es la fuente 1c.

**b) Falta el incremento de año 2026 — fases IA3 y sv6.**
La tarifa **sí existe** en el contrato: `INCREMENTO PRECIO MORTERO 2026`,
9,00 €/m³, partida P4.39.03 (línea de contrato 25921), y además
`INCREM. AÑO 2026` 9,00 €/m³ en P4.99.10. No se emitió por dos vetos
encadenados:
1. El prompt de IA3 (`valuation_es`, Paso 7) dice literalmente «Se aplica
   **SOLO** cuando la línea base tiene `tipo_familia='hormigon'`»
   (`services/albaran-valoracion-api/config/prompts/svc5_prompt_valuation_es.yaml:306`).
   Con `tipo_familia='mortero'`, IA3 devolvió **una sola línea** y ninguna
   sintética.
2. La red determinista de respaldo de sv6 tiene el mismo veto:
   `if ctx is None or getattr(ctx, "tipo_familia", None) != "hormigon": continue`
   en `_sinteticas_m1_faltantes`
   (`services/albaran-valoracion-persist/application/services/valuation_builder.py:602`;
   idéntico en la línea 686 para las sintéticas de código).

Además, `albaran_valuations.prompt_key` = `valuation_es` para el 1229: **el
prompt `valuation_mortero` no existe todavía**.
→ **Cubierto por F-004**, requisito **R24** («Incrementos por año (M1) también
en mortero») y R9/R10 (prompt `valuation_mortero`). No es un defecto nuevo.

**c) Falta la línea CARGAS INCOMPLETAS — fases IA1, IA2 e IA3.**
El formulario de Paz del Barrio **imprime** un campo «CARGAS INCOMPLETAS» con
el valor manuscrito/impreso **3** (verificado en el PNG a 200 dpi del PDF).
El `IA1_esperado.xlsx` lo pide como línea 1 («CARGAS INCOMPLETAS (campo del
formulario)», 3 M3) y el `IA2_esperado.xlsx` como línea 2.
- **IA1** (`133605_851_gemini_d20a3d6d.json`) devolvió **una sola línea** y no
  leyó el campo.
- **IA2** (`133617_237_gemini_c54777a6.json`) **sí lo vio**: puso
  `contexto_linea.carga_incompleta = true` y en `razonamientos` escribió «la
  indicación de carga incompleta marcada con 3 m3». Pero lo dejó como flag de
  contexto: no emitió línea y dejó `m3_no_transportados = null`. El flag está
  persistido en `albaran_lines_merge.contexto_linea_json` (línea id 379).
- **IA3** recibió ese `carga_incompleta: true` en el payload y no emitió M7,
  por el veto de mortero del punto (b).

Nota adicional: el contrato CTSU25/0001 **no tarifa** carga incompleta
(revisadas las 62 líneas enviadas a IA3 — no hay ninguna `CARGAS
INCOMPLETAS`), y M7.1 del prompt ordena no emitir línea si el contrato no la
tarifa. El GT toma los 20,00 €/m³ de **OFERTA**. Es decir, aunque se levantase
el veto de mortero, esta línea seguiría sin salir sin F-017.
→ **Cubierto por F-018** (la línea de carga incompleta la genera siempre IA2)
**+ F-004 R17/P2** (la cantidad impresa cuenta como señal explícita) **+
F-017** (el precio sale del comparativo).

Coincidencia que conviene no confundir: aquí `cantidad impresa = 3` y
`max(0, 6 − 3) = 3` dan el mismo número, así que este documento **no
discrimina** entre «usar la cantidad impresa» y «aplicar la fórmula del
mínimo». El 224964 sí discrimina (4 servidos → 2).

**d) IA4 no llegó a ejecutarse para el 1229.**
No hay ningún fichero `DocumentoConciliacion` posterior a
`133840_970_claude_94ec9e17.json`. Es consecuencia directa de (b): sin líneas
sintéticas sin match, no hay nada que conciliar. **No es un defecto propio de
IA4.**

---

## 5. Hallazgos transversales a los cuatro documentos

### 5.1 El código de partida manuscrito se lee mal en los 4 de 4

| Albarán | Manuscrito en el PDF | Leído por IA1 (`codigo_imputacion`) | Persistido (`codigo_partida_final`) | ¿Existe el leído en el catálogo? | ¿Existe el real? |
|---|---|---|---|---|---|
| 224964 | `P5.03.04` | `03.04` | `03.04` | **No** (0 filas) | Sí (2 filas, CTSU24/0518) |
| 225137 | `P5.03.09` | `PT.03.09` | `PT.03.09` | **No** (0 filas) | Sí (6 filas) |
| 1167 | `P4.03.05` | `04.03.05` | `04.03.05` | **No** (0 filas) | Sí (8 filas) |
| 1229 | `P4.14.01.02.02` | `15.01.02.02` | `15.01.02.02` | **No** (0 filas) | Sí (2 filas, pero solo en CTSU24/0518) |

(Conteos obtenidos con `select count(*) from albaran_contrato_lines_merge
where codigo_partida = ...`.)

El patrón es sistemático: el prefijo `P4.` / `P5.` (parcela 04 / parcela 05 de
la obra «88+88 VIVIENDAS KODAK PARC.04/05») se pierde o se transforma —
`P5` → `03.04` (se cae), `P5` → `PT` (5 leído como T), `P4` → `04` (P leída
como 0), `P4.14` → `15` (colapso de dos grupos). **Todas las partidas del
catálogo de contrato llevan el prefijo `P4.`/`P5.`/`CI.`**, así que un
código sin prefijo es reconocible como inválido sin ambigüedad.

Consecuencia aguas abajo: sv6 no encuentra la partida, marca
`partida_action='new_line_created'` y **crea líneas derivadas con el literal
inválido** en `contrato_lines_derived` (ids 389–394, 395–399, 400–402, 403;
`origen='missing_partida'`), en vez de apuntar a la línea real del contrato,
que existe y tiene el mismo precio.

- **Fase que falla**: IA1 (lectura). IA2 la revisó y la dio por buena sin
  corregirla, así que también es un fallo de IA2. sv6 la propaga sin validar.
- **Clasificación**: **cubierto por F-021** («el código de partida no se
  valida contra el catálogo del contrato»). **AVISO: F-021 no figura en
  `harness/features.json`** (el backlog llega hasta F-020). Si el humano
  quiere que quede registrada, hay que darla de alta.
- Matiz importante: **F-004 R7 no cubre este caso.** R7 solo veta la partida
  de las **sintéticas**; aquí la partida inválida es la de la **línea base**,
  y de ella la heredan las sintéticas. Falta el guard equivalente para la
  base.
- **Lectura incierta declarada**: en el 225137 el glifo manuscrito es
  genuinamente ambiguo entre `5` y `T`/`J` (zoom a 600 dpi guardado en el
  scratchpad). Lo resuelvo como `P5` porque (i) el GT lo dice, (ii) su
  hermano 224964 lleva `P5.03.04`, (iii) `PT.*` no existe en el catálogo y
  `P5.03.09` sí, y (iv) la descripción de `P5.03.09` («ZAPATAS CORRIDAS Y
  VIGAS BAJO MURO») coincide con las observaciones del albarán. No es una
  lectura directa del trazo.

### 5.2 `unidad_medida` sale NULL en las 4 líneas base

Los cuatro PDFs imprimen la unidad en la cabecera de la casilla («CANTIDAD M³»
en Paz del Barrio, «M³» en Sierra Madrid) y los cuatro esperados de IA1 piden
`unidad = M3`. Sin embargo, `albaran_lines_merge.unidad_medida` es NULL en las
cuatro, y `field_scores_json.unidad_medida.status` = `both_empty_optional`.

Efecto en cascada, verificable en `albaran_line_valuations`:
1. `unidad_categoria` queda `unknown` frente al `m3` del contrato →
   `UnitCategoryGuard` devuelve `unit_category_partially_unknown` y
   `unidad_category_match = false`
   (`services/albaran-valoracion-persist/application/services/unit_category_guard.py:61`).
2. Con `category_match=false`, `ValuationBuilder` llama al conversor con
   `cantidad=None` a propósito
   (`valuation_builder.py:1021-1025`), lo que genera el motivo
   **`no_quantity_in_albaran` aunque la cantidad exista** (4, 9, 8 y 3 m³
   respectivamente) — motivo engañoso para el revisor.
3. El importe se salva porque cae al fallback
   `importe_using_albaran_quantity_fallback` con factor 1.

Es decir: los importes salen bien **por suerte** (albarán y contrato están
ambos en m³), pero las cuatro líneas base arrastran 4 motivos de revisión de
los cuales 2 son falsas alarmas.

- **Fase que falla**: IA1 (no extrae la unidad); IA2 tampoco la repone.
- **Clasificación**: **defecto nuevo** (ver §6, H-1 y H-2).

### 5.3 Sintéticas de año 2025 con importe NULL (224964 y 225137)

IA3 emitió, para los dos albaranes de contrato CTSU24, una línea
`INCREMENTO POR AÑO 2025 EN HORMIGÓN` además de la de 2026, siguiendo M1.3 del
prompt («para CADA año entre año_contrato+1 y año_albarán, emite UNA línea»).
IA4 la revisó y la dejó sin casar, con el razonamiento correcto: «Regla dura
de años: no se puede casar 2025 con 2026». Importe NULL → no afecta al total.

El ground truth **no tiene** esa fila, y §10.2 del documento de dominio dice
✅ «**Incremento por año: UNO solo**, salvo dos años consecutivos declarados».
Hay contradicción entre M1.3 del prompt de sv5 y §10.2.

- **Fase**: IA3 (prompt), con IA4 comportándose correctamente.
- **Clasificación**: **duda que debe resolver el humano.**
  *Pregunta concreta*: cuando entre el año del contrato y el del albarán hay
  más de un salto (CTSU24 → albarán 2026), ¿debe emitirse una línea por cada
  año intermedio aunque el contrato no la tarife (M1.3 del prompt actual, deja
  rastro para el revisor), o debe emitirse solo la del año del albarán (§10.2)?
  Hoy el pipeline hace lo primero y el administrativo espera lo segundo.

### 5.4 Sintéticas de tiempo y residuos que el GT no contempla

- `INCREMENTO POR EXCESO DE TIEMPO DE DESCARGA`: emitida en los 4 documentos
  con 0 min de exceso e importe 0,00 o NULL. Es **conforme a §10.2** («el
  exceso de descarga se lee pero NO se valora... emitir con precio null a
  revisión») y a M6.3. No afecta al total. El GT no la lista.
- `INCREMENTO POR GESTIÓN DE RESIDUOS` / `GESTIÓN DE RESIDUOS (INCLUIDA EN
  PRECIO)`: emitida en 224964 y 225137 con importe NULL, razonando que el
  anexo I incluye la gestión de residuos en los precios unitarios. Es la
  respuesta correcta de negocio pero M5 dice «emítelo SIEMPRE... si el PDF
  incluye un cargo», luego emitir una línea para decir «no hay cargo» es
  ruido.
- **Clasificación de ambas**: **duda que debe resolver el humano.**
  *Pregunta concreta*: ¿quiere el administrativo ver estas líneas informativas
  a 0,00/NULL en la pantalla de revisión (trazabilidad de que el sistema las
  consideró), o deben omitirse cuando no generan importe para que la tabla
  cuadre línea a línea con su Excel?

### 5.5 Etiquetado de proveedor de IA (F-020) — confirmado en los 4

En los cuatro documentos:
- `albaran_documents_merge.provider_origin` = `openai_fallback`
- `comparison_summary_json.providers_available` = `{openai: true, gemini:
  false, claude: false}`
- pero `model_name` = `gemini-3.7-flash` y los logs de IA1/IA2 son
  `*_gemini_*.json` con `provider: "gemini"`.
- `review_reasons_json` = `["single_provider_openai",
  "document_confidence_below_threshold", "line_only_in_openai:1"]`
- `confidence_pct_calc`: 64,1 / 62,9 / 66,2 / 70,2 — todos por debajo del
  umbral, con los scores por campo capados a 76,0 por ser «openai_only».

→ **Cubierto por F-020**. Confirmación adicional: los cuatro documentos van a
revisión humana **por el etiquetado**, no por su calidad real de extracción.

### 5.6 F-019 (descuento no aplicado al importe) — NO se manifiesta aquí

Ninguna de las 15 líneas valoradas trae descuento
(`albaran_line_valuations.descuento_albaran_aplicado` = NULL en todas,
`albaran_lines_merge.descuento` = NULL en las 4), y el GT tiene la columna
`descuento` vacía en las 10 filas. En todos los casos `importe_calculado =
cantidad × precio_unitario_final` exactamente. **Este lote no aporta ni
confirma ni desmiente F-019.**

### 5.7 F-015 y F-016 — no aplican a este lote

No hay líneas tachadas a mano ni códigos de partida con separador «/» en
ninguno de los cuatro PDFs.

---

## 6. Hallazgos nuevos candidatos a feature (por gravedad)

### H-1 (ALTA) — La unidad de medida no se extrae de los albaranes de hormigón/mortero

**Qué pasa**: `unidad_medida` sale NULL en las 4 líneas base pese a estar
impresa («CANTIDAD M³» / «M³») y pese a que los 4 esperados de IA1 piden `M3`.

**Por qué importa**: no es cosmético. Rompe la cadena de unidades de sv6
(`unidad_categoria='unknown'` → `unidad_category_match=false` → conversión
saltada → fallback), y aquí solo se salva porque contrato y albarán están
ambos en m³. Con un contrato en TN o en kg el importe saldría mal, y el propio
`UnitConverter` documenta un caso real de ese tipo (árido «M 20/40», 29920 sin
unidad, 298.302 €).

**Fase**: IA1 principalmente; IA2 tampoco lo repone.

**Propuesta**: en estos formatos la unidad no está en la fila sino en la
**etiqueta de la casilla** (mismo patrón que la regla ya implementada de
residuos, §10.6: «volumen y peso por ETIQUETA de casilla»). Extender esa
lección a hormigón/mortero, o poner una red determinista en sv6 que asuma la
unidad del contrato para líneas de familia hormigón/mortero sin unidad.

### H-2 (MEDIA) — El motivo `no_quantity_in_albaran` es una falsa alarma sistemática

**Qué pasa**: las 4 líneas base tienen cantidad (4, 9, 8, 3) y aun así llevan
el motivo `no_quantity_in_albaran`, porque `ValuationBuilder` invoca el
conversor con `cantidad=None` cuando `category_match` es falso
(`valuation_builder.py:1021-1025`), y `UnitConverter.convert` devuelve ese
motivo para `cantidad is None` (`unit_converter.py:64-70`).

**Por qué importa**: es información falsa en la pantalla del revisor. El motivo
correcto sería algo como `conversion_skipped_unit_category_mismatch`. Con el
100 % de las líneas de este lote marcadas así, el revisor aprende a ignorar el
motivo, que es justo lo contrario de lo que se busca.

**Fase**: reglas deterministas de sv6.

**Propuesta**: motivo propio para «conversión omitida por categoría», dejando
`no_quantity_in_albaran` solo para cantidad realmente ausente. Cambio pequeño
y de bajo riesgo.

### H-3 (MEDIA) — La partida inválida de la línea BASE no tiene guard (hueco entre F-004 R7 y F-021)

**Qué pasa**: F-004 R7 veta la partida inexistente **de las sintéticas**. En
este lote la partida inválida está en la **base** (4 de 4), y las sintéticas
la heredan legítimamente: R7 no se dispara porque la partida heredada es «la
de la base». El resultado son 13 líneas derivadas en `contrato_lines_derived`
con literales `03.04`, `PT.03.09`, `04.03.05`, `15.01.02.02`, ninguno
existente en el catálogo.

**Por qué importa**: es contaminación persistente de una tabla de referencia,
no un dato de una valoración concreta, y la línea de contrato correcta existía
con el mismo precio.

**Propuesta**: extender la validación de partida a la línea base antes de
derivar (esto es lo que el humano llama F-021, hoy sin entrada en
`features.json`), y explicitar en la spec de F-004 que R7 no cubre este
camino.

### H-4 (BAJA) — Errata aritmética en §10.7 del documento de dominio (bombeo)

`docs/referencia/dominio_negocio_albaranes.md:761-763` dice: «m³ a facturar =
horas de bombeo × rendimiento mínimo del contrato (ej. **20 m³/h → 5 h = 210
m³**)». 20 × 5 = 100, no 210. Según el dato que maneja el humano (210 / 20 =
**10,5 h** a 20 m³/h), el ejemplo debería decir 10,5 h.

**Por qué importa**: §10.7 es la única fuente escrita de la regla de bombeo y
alimentará el prompt de F-005. Un ejemplo con la aritmética rota es
exactamente el tipo de cosa que un LLM copia.

**Nota**: ninguno de los cuatro albaranes de este lote lleva bombeo, así que
esto sale de la lectura del documento, no de los datos.

### H-5 (BAJA / duda) — `review_phase2_status` y `review_phase2_changes_count` quedan NULL

En los 4 documentos (y también en los 2 de Feymaco del mismo día) las columnas
`review_phase2_status`, `review_phase2_summary` y
`review_phase2_changes_count` de `albaran_documents_merge` están a NULL, pese
a que IA2 devolvió `review_status: "ok_with_changes"` con `razonamientos`
poblados (visible en `raw_extraction_json.debug.phase_2` y en el log
`133617_237_gemini_c54777a6.json`).

**Duda para el humano**: ¿son columnas de la revisión **humana** de sv4 (y por
tanto NULL es correcto hasta que alguien revise en el front), o deberían
recoger el veredicto de la fase 2 de IA? Si es lo segundo, es un fallo de
persistencia en sv3 que deja el rastro de IA2 solo dentro del JSON.

---

## 7. Tabla resumen de diferencias y clasificación

| # | Albarán(es) | Diferencia | Fase que falla | Clasificación |
|---|---|---|---|---|
| 1 | 1229 | Falta línea `CARGAS INCOMPLETAS` (3 × 20,00 = 60,00 €) | IA1 (no la lee) + IA2 (la marca en contexto pero no emite línea) + IA3 (veto mortero) | Cubierto por **F-018** + **F-004 R17/P2** + **F-017** (precio) |
| 2 | 1229 | Falta línea `INCREM. PRECIO 2026` (3 × 9,00 = 27,00 €) | IA3 (Paso 7 solo hormigón) + sv6 (red M1 determinista con el mismo veto) | Cubierto por **F-004 R24** |
| 3 | 1229 | Precio 70,00 en vez de 73,50 (−10,50 €) | IA3 (no tiene fuente comparativo) | Cubierto por **F-017** |
| 4 | 1229 | IA4 no se ejecuta | Consecuencia de #2 | Cubierto por **F-004** (desaparece al arreglar #2) |
| 5 | los 4 | Partida leída mal (`03.04`, `PT.03.09`, `04.03.05`, `15.01.02.02`) | IA1 + IA2 (no corrige) + sv6 (no valida) | Cubierto por **F-021** (¡sin entrada en `features.json`!) + **H-3** |
| 6 | los 4 | `unidad_medida` NULL | IA1 + IA2 | **Defecto nuevo → H-1** |
| 7 | los 4 | Motivo `no_quantity_in_albaran` con cantidad presente | sv6 (determinista) | **Defecto nuevo → H-2** |
| 8 | los 4 | `provider_origin='openai_fallback'` con modelo gemini + penalización de confianza | sv2/sv3 (merge) | Cubierto por **F-020** |
| 9 | 224964, 225137 | Línea `INCREMENTO POR AÑO 2025` que el GT no tiene (importe NULL) | IA3 (M1.3 del prompt vs §10.2) | **Duda para el humano** (§5.3) |
| 10 | los 4 | Líneas de tiempo/residuos a 0,00 o NULL que el GT no tiene | IA3 (M5/M6 del prompt) | **Duda para el humano** (§5.4) |
| 11 | — | Errata aritmética en §10.7 (bombeo) | Documentación | **Hallazgo nuevo → H-4** |
| 12 | los 4 | `review_phase2_*` a NULL | sv3 (persistencia) o por diseño | **Duda para el humano → H-5** |

---

## 8. Lecturas inciertas declaradas

Para no dar por bueno nada que no se lea con seguridad:

1. **225137, código de partida manuscrito**: el segundo carácter es
   genuinamente ambiguo entre `5` y `T`/`J` incluso a 600 dpi. Se resuelve
   como `P5` por convergencia de cuatro indicios (GT, hermano 224964,
   inexistencia de `PT.*` en el catálogo, coincidencia de la descripción de
   `P5.03.09` con las observaciones del albarán), no por el trazo.
2. **224964, código de partida manuscrito**: se lee «PJ.0304» / «P5.0304»;
   mismo razonamiento, se resuelve como `P5.03.04`.
3. **1229, campo CARGAS INCOMPLETAS**: el valor `3` se lee con claridad en la
   casilla impresa. Lo que **no** se puede determinar desde el documento es si
   el `3` significa «3 m³ de carga incompleta a facturar» o «3 m³ hasta el
   mínimo»: en este albarán ambas interpretaciones dan 3. Este documento no
   sirve para decidir esa regla; el 224964 sí.
4. **1229, precio 73,50 del GT**: no aparece en el PDF del albarán ni en las
   62 líneas del contrato CTSU25/0001 enviadas a IA3. Sale del comparativo /
   oferta, documento que no se ha consultado en este análisis.
