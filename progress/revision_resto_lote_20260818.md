# Revisión de los 7 albaranes restantes — lote `alvaro_17082026`

- **Fecha del análisis**: 2026-08-18
- **Alcance**: 58826 y 58878 (MAHORSA), 225225 (HORMIGON SIERRA MADRID,
  mortero), 2026/01/007181 y 2026/01/007378 (PAVIMARSA), 09256
  (TRANSPORTES Y GRUAS ANGEL MARTIN) y A261584 (VODALAND). Procesados por
  el pipeline local entre las **14:39 y las 14:41 UTC** del 2026-08-18.
- **Naturaleza**: análisis de **solo lectura**. No se ha modificado código,
  base de datos, rama ni `harness/features.json`. Este fichero es el único
  añadido.
- **Complementa** a `progress/revision_hormigones_20260818.md` (los otros 4
  documentos del mismo lote). Se reutiliza su método y no se repiten sus
  hallazgos salvo cuando este lote los confirma o los matiza.

## Fuentes cruzadas

| Fuente | Referencia |
|---|---|
| BBDD local | PostgreSQL `albaranes` @ localhost:5432 — `albaran_documents_merge`, `albaran_lines_merge`, `albaran_valuations`, `albaran_line_valuations`, `albaran_contratos_merge`, `albaran_contrato_lines_merge`, `contrato_lines_derived`, `contratos_cache` |
| Logs IA1/IA2 (sv2) | `services/albaranes-api/logs/ia/20260818/1439*.json`, `1440*.json` |
| Logs IA3/IA4 (sv5) | `services/albaran-valoracion-api/logs/ia/20260818/1440*.json`, `144135_*.json` |
| Logs de servicio | `services/albaranes-persistencia/logs/albaranes_persistence.log`, `services/albaran-valoracion-api/logs/albaranes_valuation_api.log`, `services/albaran-valoracion-persist/logs/albaranes_valuation_persistence.log` (marcas horarias en **hora local CEST = UTC+2**) |
| PDFs | `C:\Users\pgris\OneDrive - Ruesma\Documentos\albaranes\evals\alvaro_17082026\*.pdf` (escaneados sin texto; renderizados a PNG con `pymupdf` a 170/400/900 dpi). Los 7 son de **una sola página** |
| Ground truth (GT) | `alvaro_17082026.xlsx`, hoja `Hoja1`, filtrando por `codigo alabran` |
| Reglas | `docs/referencia/dominio_negocio_albaranes.md` §9, §10.2, §10.5, §10.7, §10.8 y la nota de cabecera sobre el lote |

### Correspondencia documento ↔ fichero de log

| Nº albarán | `albaran_documents_merge.id` | IA1 (fase 1) | IA2 (fase 2) | IA3 (valoración) | IA4 |
|---|---|---|---|---|---|
| 58826 | `95d9ea84-9d49-40f5-99af-8396e6bfcd78` | `143902_640_gemini_b8019e01.json` | `143907_398_gemini_2246b1c6.json` | `144000_610_claude_bb6b315a.json` | **no hubo llamada** |
| 58878 | `32d2b1c0-69e2-4968-bb39-ab620b6b18be` | `143917_780_gemini_d564bdad.json` | `143922_326_gemini_aa33401f.json` | `144012_621_claude_8265dc55.json` | **no hubo llamada** |
| 225225 | `70c52f72-f6d9-4242-a237-67360b607ffc` | `143929_410_gemini_9a3aa734.json` | `143937_159_gemini_7e89fb11.json` | `144029_255_claude_e82d0bae.json` | **no hubo llamada** |
| 2026/01/007181 | `b08b194b-c469-480d-8071-b965e5321c84` | `143944_909_gemini_42b90796.json` | `143951_301_gemini_4cc0ea7b.json` | **no se llamó** | — |
| 2026/01/007378 | `3a7c510e-bb8c-4f04-8f68-b79b37c5be67` | `144002_533_gemini_c7163c1b.json` | `144010_540_gemini_5948c71b.json` | **no se llamó** | — |
| 09256 | `74aa1802-f849-4de6-9b71-41287534b528` | `144017_039_gemini_9e531a9a.json` | `144021_637_gemini_f9df3981.json` | **no se llamó** | — |
| A261584 | `d0f68b37-ef71-45d0-8e27-8abff31ae542` | `144027_611_gemini_f40cb3ec.json` | `144032_519_gemini_239bb914.json` | `144135_359_claude_0dece61a.json` | **no hubo llamada** |

En ningún caso hubo IA4: las 4 valoraciones emitieron **una sola línea, casada
y sin sintéticas**, así que no había nada que conciliar. No es un defecto de
IA4.

---

## Resumen ejecutivo

| Nº albarán | Total esperado (GT) | Total obtenido | Δ | Veredicto |
|---|---|---|---|---|
| 58826 | **390,99 €** | **468.763,40 €** | **+468.372,41 €** | **Catastrófico** (×1000 de unidad + precio equivocado) |
| 58878 | **385,59 €** | **462.282,80 €** | **+461.897,21 €** | **Catastrófico** (idem) |
| 225225 | **567,00 €** | **490,00 €** | **−77,00 €** | Incorrecto |
| 2026/01/007181 | **521,07 €** | — (sin valorar) | **−521,07 €** | Sin valorar |
| 2026/01/007378 | **20.111,40 €** | — (sin valorar) | **−20.111,40 €** | Sin valorar |
| 09256 | **1.129,00 €** | — (sin valorar) | **−1.129,00 €** | Sin valorar |
| A261584 | **3.393,00 €** | **3.393,00 €** | **0,00 €** | **Total correcto** |

Tres titulares:

1. **Los 468.763 € de Mahorsa son un factor 1000 de unidad más un precio
   equivocado.** La red determinista que existe para exactamente este caso
   (`cantidad_sin_unidad_reinterpretada_kg_a_tn`) **está muerta**: nunca se
   ejecuta. Ver §4 y H-1.
2. **Los tres documentos sin valorar no fallaron: nunca se les publicó
   mensaje en `q-valoracion`**, porque sv3 no llegó a seleccionar contrato.
   Dos causas distintas (Pavimarsa: dos contratos candidatos; TyG: obra mal
   resuelta y sin CIF). Ver §5.
3. **El código de partida manuscrito vuelve a fallar en 6 de 7 documentos**
   (el único acierto es Vodaland). Confirma el patrón de la revisión de
   hormigones y lo amplía: aquí el error de partida **sí cuesta dinero**
   (Mahorsa), porque la partida correcta apuntaba a la línea de contrato con
   el precio bueno.

---

## 1. Albarán 58826 — MATERIALES Y HORMIGONES, S.L. (MAHORSA)

PDF: `Mahorsa_58826.pdf` (1 página, escaneado).

### 1.1 Cabecera

| Campo | Esperado (GT / PDF) | Obtenido (`albaran_documents_merge`) | Veredicto |
|---|---|---|---|
| `numero_albaran` | 58826 (PDF: «ALBARÁN Nº 58826») | `58826` | OK |
| `proveedor_nombre` | MATERIALES Y HORMIGONES, S.L. (MAHORSA) | idem (canonizado por CIF en sv3) | OK |
| `proveedor_cif` | B86615549 (PDF: «B86615549») | `B86615549` | OK |
| `fecha` | 2026-05-25 (PDF: «FECHA 25/05/2026») | `2026-05-25` | OK |
| `obra_codigo` | 696 (PDF: «DESTINO 0696 88 V.V. LAS ROZAS PARC 4») | `0696` | OK |
| `selected_contrato_codigo` | CTSU25/0085 | `CTSU25/0085` (`auto_unico`) | OK |
| `confidence_pct_calc` | — | 70,2 · `review_required=true` | Ver §7.5 |

### 1.2 Línea

GT: 1 fila. Persistido: 1 fila `from_albaran` (id 621), 0 sintéticas.

| Campo | Esperado (GT / PDF) | Obtenido (BBDD) | Veredicto |
|---|---|---|---|
| concepto | `GRAVA 20/40` (PDF: «MATERIAL: M-20/40-S EN 12620:2002H») | `albaran_lines_merge.concepto` = `ARIDO M-20/40-S EN 12620:2002H` | OK (transcripción literal) |
| cantidad | **30,38** | `cantidad_albaran` = **30380.0** | **MAL** → §4.1 |
| unidad | `TN` (PDF: casillas «PESO BRUTO / TARA 12500 / **NETO 30380**», sin literal «kg») | `unidad_medida` = **NULL** | **MAL** → F-024 / H-1 |
| precio unitario | **12,87** (fuente CONTRATO) | `precio_unitario_final` = **15.43** (`both_agreed`) | **MAL** → §4.2 |
| descuento | (vacío) | NULL | OK |
| importe | **390,99** | `importe_calculado` = **468763.4** | **MAL** |
| partida | `P5.22.01.03.07` (GT) · **`P4.22.01.0307`** (manuscrito en el PDF) | `codigo_partida_final` = `P4.22.01.03.07` | Ver §7.2 (duda) |

`partida_action` = `new_line_created`; se creó `contrato_lines_derived` id **404**
(`ARIDO CALIZA MACHAQUEO T-20/40-C EN 12620:2002H`, TN, 15,43, partida
`P4.22.01.03.07`, `origen='missing_partida'`) **pese a que esa partida sí existe
en el contrato** (línea 25972).

`review_reasons_json` de la línea: `["unit_category_partially_unknown",
"ia_match_partida_missing_derived", "no_quantity_in_albaran",
"importe_using_albaran_quantity_fallback"]` — obsérvese `no_quantity_in_albaran`
con `cantidad_albaran = 30380`.

### 1.3 Total y desglose de la diferencia

| | Valor |
|---|---|
| Esperado (30,38 TN × 12,87) | **390,99 €** |
| Obtenido (`albaran_valuations.total_valorado`) | **468.763,40 €** |
| **Diferencia** | **+468.372,41 €** |

| Origen | Δ |
|---|---|
| Precio 15,43 en vez de 12,87 (× 30,38 TN) | +77,77 € |
| Cantidad en KG tratada como TN (× 1000) | +468.294,64 € |
| **Total** | **+468.372,41 €** |

---

## 2. Albarán 58878 — MATERIALES Y HORMIGONES, S.L. (MAHORSA)

PDF: `Mahorsa_58878.pdf` (1 página). Documento gemelo del anterior.

### 2.1 Cabecera

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| `numero_albaran` | 58878 | `58878` | OK |
| `proveedor_cif` | B86615549 | `B86615549` | OK |
| `fecha` | 2026-05-26 (PDF: «26/05/2026») | `2026-05-26` | OK |
| `obra_codigo` | 696 (PDF: «DESTINO 0696 88 V.V. LAS ROZAS PARC 4») | `0696` | OK |
| `selected_contrato_codigo` | CTSU25/0085 | `CTSU25/0085` (`auto_unico`) | OK |
| `confidence_pct_calc` | — | 70,2 · `review_required=true` | Ver §7.5 |

### 2.2 Línea

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| concepto | `GRAVA 20/40` (PDF: «M-20/40-S EN 12620:2002H») | `ARIDO M-20/40-S EN 12620:2002H` | OK |
| cantidad | **29,96** | **29960.0** (PDF: «TARA 12700 / NETO 29960») | **MAL** → §4.1 |
| unidad | `TN` | **NULL** | **MAL** |
| precio unitario | **12,87** | **15.43** | **MAL** → §4.2 |
| importe | **385,59** | **462282.8** | **MAL** |
| partida | `P5.03.04` (GT y PDF manuscrito) | **`PT.03.04`** | **MAL** → §7.1 |

Derivada creada: `contrato_lines_derived` id **405**, misma descripción y precio
que la 404, partida `PT.03.04` (inexistente en el catálogo).

### 2.3 Total y desglose

| | Valor |
|---|---|
| Esperado (29,96 × 12,87) | **385,59 €** |
| Obtenido | **462.282,80 €** |
| **Diferencia** | **+461.897,21 €** |

| Origen | Δ |
|---|---|
| Precio 15,43 en vez de 12,87 (× 29,96 TN) | +76,69 € |
| Cantidad en KG tratada como TN (× 1000) | +461.820,52 € |
| **Total** | **+461.897,21 €** |

---

## 3. Albarán 225225 — HORMIGON SIERRA MADRID, S.L. (MORTERO)

PDF: `Mortero Sierra Madrid_225225.pdf` (1 página).

### 3.1 Cabecera

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| `numero_albaran` | 225225 | `225225` | OK |
| `proveedor_cif` | B86738812 | `B86738812` | OK |
| `fecha` | **2026-05-28** (GT: `datetime(2026,5,28)`; PDF: «FECHA: 28/05/2026») | `2026-05-28` | **OK — la duda «Excel dice 18/05» queda descartada**, ver §7.6 |
| `obra_codigo` | 696 (PDF: «OBRA 696 88+88 VIV KODAK») | `0696` | OK |
| `selected_contrato_codigo` | CTSU24/0518 | `CTSU24/0518` (`auto_unico`) | OK |
| Tipología | MORTERO | `prompt_key='albaran_revision_fase2_mortero'`, `contexto_linea.tipo_familia='mortero'` | OK |

### 3.2 Líneas

GT: 2 filas. Persistido: **1 fila**.

| # | Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|---|
| 1 | concepto | `MORTERO PREP. M-7,5` (PDF: «TIPO DE HORMIGON M-7,5/B/4») | `M-7,5/B/4` | OK (literal) |
| 1 | cantidad | 7 (PDF: casilla «M³ = 7») | 7.0 | OK |
| 1 | unidad | `M3` (PDF: etiqueta «M³» de la casilla) | **NULL** | **MAL** (F-024) |
| 1 | precio unitario | **72,00** (fuente CONTRATO) | **70,00** (`both_agreed`, ref. línea 26083 `MORTERO M-5`) | **MAL** → §3.4.a |
| 1 | importe | **504,00** | **490,00** | **MAL** (−14,00 €) |
| 1 | partida | `P5.14.01.02.02` (GT; PDF manuscrito, glifo tipo «RJ»/«PJ») | **`RJ.14.01.02.02`** | **MAL** → §7.1 |
| 2 | concepto | `INCREM. PRECIO 2026` | **NO EXISTE** | **FALTA** → §3.4.b |
| 2 | cantidad / precio / importe | 7 · 9,00 (CONTRATO) · **63,00** | — | **FALTA (−63,00 €)** |

Derivada creada: `contrato_lines_derived` id **406** (`MORTERO M-5`, M3, 70,00,
partida `RJ.14.01.02.02`, `origen='missing_partida'`).

Tiempos leídos del PDF (carga 07:36, llegada 08:05, inicio 08:10, fin 08:40,
límite 1 h 30 min): no hay exceso de descarga y el pipeline no emitió línea de
exceso. **Correcto.** El formulario de Sierra Madrid **no** tiene campo «cargas
incompletas», y 7 m³ ≥ 6 m³, así que tampoco procede M7. Correcto.

### 3.3 Total

| | Valor |
|---|---|
| Esperado (504,00 + 63,00) | **567,00 €** |
| Obtenido | **490,00 €** |
| **Diferencia** | **−77,00 €** |

| Origen | Δ |
|---|---|
| Precio 70,00 en vez de 72,00 (× 7 m³) | −14,00 € |
| Falta `INCREM. PRECIO 2026` (7 × 9,00) | −63,00 € |
| **Total** | **−77,00 €** |

### 3.4 Causa raíz

**a) Precio 70,00 en vez de 72,00 — fase IA3 (con reserva).**
Las **95 líneas** de contrato de CTSU24/0518 en BBDD (ids 26034–26128) **no
contienen ningún precio 72,00** (`select ... where precio_unitario=72` → 0 filas)
ni ninguna descripción «M-7,5»: todo el mortero está a 70,00 (`MORTERO M-5`,
`MORTERO M-7 EN ESCOCIAS`, `MORTERO PREP. M-5`). IA3 **sí recibió el PDF del
contrato adjunto** (`144029_255_claude_e82d0bae.json`, `attachment.kind='pdf'`,
`CTSU24_0518_277120_HORMIGONES_SIERRA_MADRID.PED1_COMBINADO.pdf`) y respondió:
«El albarán es M-7,5/B/4 …; el contrato no tarifa M-7,5 pero sí MORTERO M-5
(70 €/m3) y MORTERO M-7 EN ESCOCIAS (70 €/m3)».
El GT marca el 72,00 como fuente **CONTRATO** (no OFERTA), lo que apunta a que
la tarifa de M-7,5 está en el Anexo I del PDF y **IA3 no la encontró**.
**No he podido verificar el PDF del contrato** (vive en SharePoint; el log de IA
no guarda el base64 del adjunto). → **Lectura incierta declarada, §8.3.**
Nótese el contraste con el 1229 de la revisión de hormigones, donde el mismo
producto M-7,5 se tarifa a 73,50 con fuente **OFERTA**: allí el GT dice que no
está en contrato, aquí dice que sí.

**b) Falta el incremento de año 2026 — fases IA3 y sv6. Cubierto por F-023.**
La tarifa **existe** en el contrato: línea **26114**
`INCREMENTO PRECIO MORTERO 2026`, 9,00 €/m³, partida `P5.39.03`. No se emitió
por el veto `tipo_familia != 'hormigon'` del prompt de IA3
(`svc5_prompt_valuation_es.yaml`, Paso 7: «Se aplica **SOLO** cuando la línea
base tiene `tipo_familia='hormigon'`») y por el mismo veto en la red
determinista de sv6 (`valuation_builder.py:602` y `:686`). `prompt_key` de la
valoración = `valuation_es` (el prompt `valuation_mortero` sigue sin existir).
Este documento es **el caso limpio de F-023**: a diferencia del 1229, aquí la
tarifa de incremento sí está en las líneas de Sigrid, así que basta con
levantar el veto — no hace falta F-017.

---

## 4. De dónde salen los 468.763 € y los 462.282 € de Mahorsa

Es el hallazgo más grave del lote. Son **dos errores independientes que se
multiplican**.

### 4.1 El factor 1000: la red de KG→TN existe y está muerta

Cadena verificada, paso a paso:

1. **IA1** (`143902_640_gemini_b8019e01.json`) lee la casilla «NETO» del albarán
   y devuelve `cantidad: 30380.0`, `unidad_medida: null`. El PDF **no imprime el
   literal «kg»**: la unidad está implícita en las etiquetas PESO BRUTO / TARA /
   NETO (TARA = 12500, coherente con un camión).
2. **IA2** (`143907_398_gemini_2246b1c6.json`) da la fase 1 por buena con
   `review_status: "ok"` y escribe literalmente en `explicacion_global`:
   «los datos de cabecera, material, **peso neto (30380)** y código de
   imputación manuscrito coinciden con el documento». **Reconoce que es un peso
   y aun así no rellena `unidad_medida`.**
3. **IA3** recibe `unidad_medida: null`, `unidad_categoria: "unknown"`,
   `cantidad: 30380.0` y responde `unidad_categoria_albaran: "mass"`,
   `unidad_category_match: true`, razonando (58878):
   «Unidad albarán 'unknown' interpretada como masa (TN) por coherencia con toda
   la familia de áridos del contrato». **IA3 asume que 30380 ya son toneladas.**
4. **sv6 descarta ese juicio.** `UnitCategoryGuard.resolve()`
   (`services/albaran-valoracion-persist/application/services/unit_category_guard.py:56-70`)
   reclasifica con el registro determinista: albarán `None` → `unknown`,
   contrato `TN` → `mass` → **caso 3** → devuelve `("unknown", False,
   ["unit_category_partially_unknown"])`. El campo
   `line.unidad_categoria_albaran` de IA3 **no se usa nunca**.
5. Con `category_match = False`, `ValuationBuilder` llama al conversor **con la
   cantidad puesta a `None` a propósito**
   (`valuation_builder.py:1020-1030`).
6. `UnitConverter.convert()` tiene su **primera** guarda en `cantidad is None`
   (`unit_converter.py:64-70`) y devuelve `no_quantity_in_albaran`.
   **El bloque de plausibilidad de toneladas nunca se alcanza.**

Ese bloque (`unit_converter.py:20-33` y `:83-101`) es exactamente la red
escrita para este caso, con el caso real documentado en el propio comentario:

> «Caso real: albarán de árido "M 20/40" con cantidad 29920 sin unidad,
> contrato en TN a 9,97 €/TN → 298.302 € … >= 1000: es KG con certeza
> → se reinterpreta /1000 y se marca revisión.»

30380 y 29960 superan el umbral `_TN_UMBRAL_CONVERTIR = 1000` con holgura. **La
red habría convertido a 30,38 y 29,96 TN.** No se ejecuta porque la condición
que la habría activado (albarán sin unidad + contrato en TN) es la **misma** que
pone `category_match=False` y anula la cantidad un paso antes.

Evidencia en BBDD (`albaran_line_valuations` ids 621 y 622):
`unidad_albaran` NULL · `unidad_contrato` `TN` · `unidad_categoria` `unknown` ·
`unidad_category_match` `false` · `cantidad_convertida` NULL ·
`factor_conversion` NULL · `importe_source` `calculated` ·
reasons `no_quantity_in_albaran` + `importe_using_albaran_quantity_fallback`.
El importe sale del *fallback* que usa la cantidad cruda del albarán.

**Fase que falla**: IA1 (no extrae la unidad) → IA2 (la nombra y no la repone) →
**sv6 (reglas deterministas: la red correcta es inalcanzable)**. El fallo
económico lo comete sv6.

### 4.2 El precio: 15,43 en vez de 12,87

El contrato CTSU25/0085 tiene **dos familias de árido 20/40**:

| Descripción de contrato | Unidad | Precio | Partidas |
|---|---|---|---|
| `SUMINISTRO DE GRAVA 20/40` / `GRAVA 20/40` | TN | **12,87** | P4/P5.03.\*, P4/P5.22.01.\*, P4/P5.06.\* … (incluye **P4.22.01.03.07** id 25972 y **P5.22.01.03.07** id 25952, y **P5.03.04** id 25950) |
| `ARIDO CALIZA MACHAQUEO T-20/40-C EN 12620:2002H` | TN | **15,43** | solo P4.14.01.02.01 (id 25980) y P5.14.01.02.01 (id 25982) |

El albarán dice `M-20/40-S EN 12620:2002H` (**S = silíceo**), el contrato tarifa
`T-20/40-C` (**C = caliza**). IA3 casó por el literal de la norma
«EN 12620:2002H» y se llevó los 15,43 €/TN. **Y lo dijo en su propio
razonamiento** (`albaran_line_valuations.ia_reasoning` id 621, verbatim):

> «Match por familia: árido T-20/40 EN 12620:2002H. El albarán dice 'M-20/40-S'
> (silíceo) y el contrato tarifa 'T-20/40-C' (caliza machaqueo) a 15,43; misma
> granulometría 20/40 y norma. Variante de naturaleza no idéntica -> confianza
> baja, precio de referencia. **Existe también GRAVA 20/40 a 12,87 en misma
> partida P4.22.01.03.07 (id 25972); revisar cuál procede.**»

Es decir: **IA3 vio la línea correcta, la citó por id, y aun así devolvió la
otra**, con `match_confidence_pct = 45`.

El prompt de IA3 se lo ordena explícitamente
(`144000_610_claude_bb6b315a.json`, `request.user_text`):

> «Recuerda que **NO decides partida**: solo casas producto y precio.»

Y después sv6 tampoco lo arregla: `PartidaMatcher`
(`services/albaran-valoracion-persist/application/services/partida_matcher.py:118-153`)
ve que la partida del albarán (`P4.22.01.03.07`) no es la de la línea que casó
IA3 (`P4.14.01.02.01`), intenta re-apuntar **por descripción idéntica** dentro
de la partida del albarán, no la encuentra («ARIDO CALIZA MACHAQUEO…» no existe
en esa partida) y cae al caso (c): **crea una línea derivada con el precio malo**
en vez de usar la línea real 25972 que sí está en esa partida.

Esto es coherente con §10.8 del documento de dominio tal como está escrita
(«re-apuntado **por descripción** o derivada si la IA casó otra partida»), pero
produce el resultado contrario al del administrativo, que resuelve por
**partida + familia** y toma la línea existente.

**Fase que falla**: IA3 (elección de línea) + sv6 (`PartidaMatcher` no usa la
línea existente de la partida). Un tercer eslabón lo agrava en el 58878: la
partida se leyó mal (`PT.03.04`), así que ahí ni siquiera existe la partida
contra la que re-apuntar.

### 4.3 Nota lateral: los dos gemelos recibieron el contrato en formatos distintos

Para el 58826, sv5 usó el **Markdown** del contrato
(`albaranes_valuation_api.log:5613` «[pipeline] contrato -> MD (18005 chars); no
se adjunta PDF», `attachment.kind='text_only'`). Para el 58878, 23 segundos
después y con el **mismo contrato**, usó el **PDF**
(`:5622` «pdf=yes`). El motivo está en BBDD:
`albaran_contratos_merge.md_sharepoint_relative_path` está relleno para la fila
251 (58826) y vacío para la 252 (58878). No cambió el resultado —ambos
devolvieron 15,43— pero es una inconsistencia de enriquecimiento que hace que
dos documentos idénticos no sean comparables.

---

## 5. Por qué NO se valoraron los tres documentos

**Respuesta corta: no falló sv5 ni sv6. Nunca se publicó el mensaje en
`q-valoracion`.** sv3 solo dispara la valoración si hay contrato seleccionado
con líneas (`persist_albaran_pipeline.py:_trigger_valuation_safely`, líneas
444-462).

Evidencia directa en `services/albaranes-persistencia/logs/albaranes_persistence.log`
(hora local CEST):

```
24510  16:40:50 [valuation-trigger][pipeline] SKIP: no hay contrato seleccionado
       con líneas. document_id=b08b194b-... codigo=None      (Pavimarsa 007181)
24595  16:41:05 ... document_id=3a7c510e-...  codigo=None    (Pavimarsa 007378)
24644  16:41:12 ... document_id=74aa1802-...  codigo=None    (TyG 09256)
```

frente a los cuatro que sí se dispararon (`trigger resultado=ACCEPTED`, líneas
24230, 24301, 24371 y 24762). El log de sv6
(`albaranes_valuation_persistence.log`) registra exactamente **4** consumos de
`q-valoracion` en la ventana, sin ninguna excepción ni reintento. No hay
mensajes muertos.

### 5.1 Pavimarsa (007181 y 007378): **dos contratos candidatos y ninguno elegido**

Sigrid devolvió **2 contratos** para el par (CIF A28800597, obra 0696)
—`sigrid_api_contrato_client.py:262` «Agrupado cabecera+líneas: contratos=2
total_lineas=108»— y ambos quedaron persistidos en `albaran_contratos_merge`
(ids 254/255 para el 007181 y 256/257 para el 007378):

- **CTSU25/0317** (PED1 Parcela 4, 21/10/2025) — 168 líneas, 40 partidas.
- **CTSU26/0187** (PED2 Parcela 4, 19/05/2026) — 48 líneas, 10 partidas.

Con más de un candidato, sv3 llama al selector determinista
(`contrato_enrichment_service.py:458-470`). Su veredicto está en el log:

```
24509  16:40:50 [contrato-selector] sin familia detectable en el albaran;
       no se auto-selecciona (decide el humano).
```

`elegir_contrato_probable` (`contrato_selector.py:95-106`) deduce «familias» del
texto del albarán; con azulejos («60X60 BOREAL GREY», «RODAPIE…») no hay familia
reconocible y devuelve `None` sin puntuar. Además, el parámetro `tipologia` —la
señal más fuerte según su propio docstring— **no se le pasa** desde
`contrato_enrichment_service` (la llamada solo envía `contratos` y
`lineas_albaran`), y aunque se pasara, `generico` está excluido en la línea 98.

**Lo que llama la atención**: el albarán trae la señal decisiva escrita a mano.
Las partidas manuscritas (`P5.09.03`, `P5.09.04`, `P5.09.05`, `P5.09.06`,
`P5.38.07.02`, `P4.09.04`, `P4.08.21`) **existen todas en CTSU25/0317 con la
descripción y el precio del GT** —comprobado en `albaran_contrato_lines_merge`
para `contrato_id=254`: `P5.09.03 · SOLADO BOREAL WHITE 60X60 cm - COCINA (OP1)
· M2 · 14,38`, `P4.09.04 · SOLADO BOREAL GREY 60X60 · 14,38`, `P4.08.21 ·
RODAPIÉ BOREAL GREY C/BISELADO · UD · 2,76`, etc.— y el GT elige justamente
CTSU25/0317. El selector no mira las partidas.

**Clasificación**: comportamiento *conforme al diseño* («si no está claro, decide
el humano») pero **defecto de cobertura → H-3**. Ninguna feature abierta lo
cubre.

### 5.2 TyG 09256: **obra resuelta a la obra equivocada y sin CIF**

El papel es un «CONFORME DE SERVICIO», no un albarán: **no lleva número de obra**
(el campo «Núm. Obra:» está en blanco), **no lleva CIF** y **no lleva ningún
precio**. Lo único que identifica el destino es la palabra manuscrita
«Valdebebas» en el campo Domicilio.

IA1 (`144017_039_gemini_9e531a9a.json`) devolvió, correctamente,
`obra_codigo: null`, `proveedor_cif: null`, `obra_nombre: "Valdebebas"`.

Entonces actuó el `HeaderResolver` de sv3:

```
16:41:09 [header-resolver] obra resuelta por texto: codigo=0351 score=1.00
16:41:10 [contrato-enrichment][sigrid-client] contratos_resumen_por_obra
         obra=0351 -> 0 proveedores
16:41:11 [header-resolver] proveedor NO resuelto (mejor score global=0.40 < 0.50)
16:41:12 [contrato-enrichment] Faltan datos o no validan; se OMITE.
         cif=None obra='0351'
```

El GT dice **obra 686** y contrato **CTSB25/0708**. La obra 0351 de Sigrid es
`VIV. PRADO VALDEBEBAS (UTE): 98 VIVIENDAS…`; la 0686 —que sí está en la caché
local (`contratos_cache`, contrato CTSU24/0524)— es
`HOTEL "CIUDAD AEROPORTUARIA" VALDEBEBAS (MADRID)`. **Las dos contienen
«VALDEBEBAS».**

El mecanismo del error está en `_match_score`
(`header_resolver_service.py:57-70`): devuelve **1.00 si un texto contiene al
otro**, así que cualquier obra cuyo nombre incluya «valdebebas» puntúa 1,00; y
el bucle de selección usa `if score > best_score` (línea 269), estrictamente
mayor, de modo que **gana la primera candidata del listado de 918 obras y los
empates no se detectan ni se registran**. El resultado es una obra
*inventada con score 1.00* que además arrastra el resto: 0 proveedores con
contrato en 0351 → la red de familia se omite → CIF no resuelto → enriquecimiento
de contrato omitido → sin contrato → sin valoración.

**Clasificación**: **defecto nuevo → H-2** (empate de obra por texto no
detectado). El hecho de que el documento se quede sin valorar es, dado el papel,
razonable; lo que no lo es, es afirmar obra `0351` con confianza 1,00.

---

## 6. Los tres documentos sin valorar: qué se esperaba de ellos

Aunque no llegaron a valorarse, la extracción sí se puede contrastar.

### 6.1 Albarán 2026/01/007181 — PAVIMARSA

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| `numero_albaran` | 2026/01/007181 | `2026/01/007181` | OK |
| `proveedor_cif` | A28800597 | `A28800597` | OK |
| `fecha` | 2026-06-09 (PDF: «09/06/26») | `2026-06-09` | OK |
| `obra_codigo` | 696 (PDF: «OBRA 0696 88 VIV.KODAK PARC-04») | `0696` | OK |
| `codigo contrato` | **CTSU25/0317** | **NULL** | **MAL** → §5.1 |

| # | Campo | Esperado | Obtenido (`albaran_lines_merge` 383/384) | Veredicto |
|---|---|---|---|---|
| 1 | código | 28-GT842010 | `28-GT842010` | OK |
| 1 | concepto | `SOLADO BOREAL GREY 60X60 cm` (PDF impreso: «60X60 BOREAL GREY») | `60X60 BOREAL GREY` | OK |
| 1 | cantidad | 23,76 | 23.76 | OK |
| 1 | unidad | `M2` (PDF: columna UM = M2) | **NULL** | **MAL** (F-024) |
| 1 | precio unitario | **14,38** (manuscrito en la columna NETO) | `precio` = 14.38 | **OK — el precio manuscrito se lee bien** |
| 1 | importe | 341,67 | `precio_neto` = 341.67 | OK |
| 1 | partida | `P4.09.04` (GT y manuscrito en la columna PRECIO) | `codigo_imputacion` = **`14.09.04`** | **MAL** (`P4` → `14`) |
| 2 | código | 567-1460-RBGB-30 | idem | OK |
| 2 | concepto | `RODAPIÉ BOREAL GREY C/BISELADO 14,8x60` | `14,8X60 RODAPIE BOREAL GREY BISELADO` | OK |
| 2 | cantidad / unidad | 65 · `UD` (PDF: UM = PZ) | 65.0 · **NULL** | cantidad OK, unidad **MAL** |
| 2 | precio unitario | **2,76** (manuscrito) | 2.76 | OK |
| 2 | importe | 179,40 | `precio_neto` = 179.4 | OK |
| 2 | partida | `P4.08.21` | **`14.08.21`** | **MAL** |

**Total esperado: 341,67 + 179,40 = 521,07 €. Obtenido: sin valoración
(−521,07 €).**

Observación relevante para la duda abierta de Pavimarsa: en el PDF, el
administrativo escribe **la partida dentro de la columna PRECIO** y **el precio
unitario dentro de la columna NETO**. El impreso del proveedor llega **sin
precios**. IA1 desenreda las dos columnas correctamente.

### 6.2 Albarán 2026/01/007378 — PAVIMARSA

Cabecera: nº `2026/01/007378`, CIF `A28800597`, fecha `2026-06-11` (PDF
«11/06/26»), obra `0696` (PDF «88 VIV.KODAK **PARC-05**» → de ahí las partidas
`P5.*`). Contrato: **NULL** (esperado CTSU25/0317).

| # | Código | Concepto (impreso) | Cant. | Unid. esperada | Precio (manuscr.) | Importe esperado | Partida esperada | Partida obtenida |
|---|---|---|---|---|---|---|---|---|
| 1 | 28-GT842000 | 60X60 BOREAL WHITE | 43,20 | M2 (obt. NULL) | 14,38 ✓ | 621,22 | `P5.09.03` | **`P05.09.03`** |
| 2 | 30-P0007387 | 60X60 SAN FRANCISCO SAND | 388,80 | M2 (NULL) | 14,38 ✓ | 5.590,94 | `P5.09.03` | **`P05.09.03`** |
| 3 | 30-P0007389 | 60X60 SAN FRANCISCO GREY | 43,20 | M2 (NULL) | 14,38 ✓ | 621,22 | `P5.09.03` | **`P05.09.03`** |
| 4 | 28-GT842010 | 60X60 BOREAL GREY | 43,20 | M2 (NULL) | 14,38 ✓ | 621,22 | `P5.09.04` | **`P05.09.04`** |
| 5 | 28-G434200K | 60X60 NATURE BONE | 43,20 | M2 (NULL) | 14,38 ✓ | 621,22 | `P5.09.05` | **`P05.09.05`** |
| 6 | 30-P0008073 | 60X60 RC ESSEN GREY | 43,20 | M2 (NULL) | 14,38 ✓ | 621,22 | `P5.09.06` | **`P05.09.06`** |
| 7 | 28-G555C001 | 24,8X150 ROMANCE ROBLE | 500,64 | M2 (NULL) | 22,44 ✓ | 11.234,36 | `P5.38.07.02` | **`P05.38.07.02`** |
| 8 | 9999-EUROPALET | EUROPALET | 22 (ver §8.2) | UD (NULL) | 9,00 ✓ | **180,00** (GT) | `ALMACEN` | **NULL** |

**Total esperado: 20.111,40 €. Obtenido: sin valoración (−20.111,40 €).**

Aciertos: los 8 códigos, las 8 cantidades y los 8 precios manuscritos (14,38 ×6,
22,44 y 9,00) son correctos. Errores: la unidad (NULL en las 8) y la partida
(cero de 8: `P5` se transcribe como `P05`).

Defecto adicional en este documento: **`precio_neto` se rellenó con el precio
unitario** (14,38) en vez de con el importe. En el 007181, el mismo IA1 lo
rellenó con el **importe** (341,67). El validador de sv3 lo detecta y marca
`line_net_mismatch:1..8` en `review_reasons_json`, restando 12 puntos por línea
(`albaran_confidence_service.py:377-382`) — de ahí que este documento sea el de
menor confianza del lote (67,69). → **H-5.**

### 6.3 Albarán 09256 — TRANSPORTES Y GRUAS ANGEL MARTIN

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| `numero_albaran` | 09256 | `09256` | OK |
| `proveedor_nombre` | TRANSPORTES Y GRUAS ANGEL MARTIN, S.L. | `TRANSPORTES Y GRUAS ANGEL MARTIN S.L.` | OK |
| `proveedor_cif` | B84535764 | **NULL** (no está en el papel) | Ver §5.2 |
| `fecha` | **2025-08-11** (PDF: «Madrid, 11 de Agosto de 2025») | `2025-08-11` | **OK** |
| `obra_codigo` | **686** | **`0351`** | **MAL** → §5.2 / H-2 |
| `codigo contrato` | CTSB25/0708 | **NULL** | **MAL** |

| # | Concepto GT | Cant. GT | Precio GT | Importe GT | Obtenido (`albaran_lines_merge` 393-395) |
|---|---|---|---|---|---|
| 1 | `SALIDA CAMIÓN GRÚA 100 TN` | 1 UD | 170,00 (CONTRATO) | 170,00 | `Desplazamiento`, 1.0, sin precio |
| 2 | `CAMIÓN GRÚA 100 TN` | 7 UD | 115,00 (CONTRATO) | 805,00 | `Horas normales`, 7.0, sin precio |
| 3 | `HHEE CAMIÓN GRÚA 100 TN` | 1 UD | 157,00 (OFERTA) | **154,00** | `Horas extras`, **1.5**, sin precio |

**Total esperado: 170,00 + 805,00 + 154,00 = 1.129,00 €. Obtenido: sin
valoración (−1.129,00 €).**

La lectura del PDF por IA1 es literalmente correcta (los conceptos impresos son
«Desplazamiento», «Horas normales», «Horas extras» y las cifras manuscritas son
1, 7 y 1,5). El GT hace tres saltos que **no están en el papel**:
- renombra los conceptos a los del contrato («… CAMIÓN GRÚA 100 TN»); el
  tonelaje del camión está en blanco en el impreso;
- pone **1** en horas extras donde el papel dice **1,5**;
- añade el aviso «EN ALBARAN PERO DEDUCE AUMENTO POR "JIB"», señal que tampoco
  aparece en el documento.
Y contiene una **incoherencia interna**: 1 × 157,00 = 157,00 ≠ 154,00 (importe
declarado). → **Duda para el humano, §7.4.**

Nota: la duda conocida sobre la fecha del Excel (`'11/08/20205'`) **ya no
existe** en el fichero actual: la celda F36:F38 es un `datetime(2025, 8, 11)`
con formato `mm-dd-yy`. El pipeline extrajo la misma fecha, aunque la marcó
`fecha_albaran_fuera_de_rango:2025-08-11` (correcto: el albarán es de hace un
año).

---

## 7. Albarán A261584 — VODALAND ESPAÑA, S.L. (el único que cuadra)

PDF: `Vodaland_A261584.pdf` (1 página, PDF nativo legible).

### 7.0 Cabecera y línea

| Campo | Esperado (GT / PDF) | Obtenido | Veredicto |
|---|---|---|---|
| `numero_albaran` | A261584 | `A261584` | OK |
| `proveedor_cif` | B98976111 | `B98976111` | OK |
| `fecha` | 2026-04-16 (PDF: «Fecha: 16/04/2026») | `2026-04-16` | OK |
| `obra_codigo` | 696 (PDF: «Cod Obra.: 696») | `0696` | OK |
| `selected_contrato_codigo` | CTSU26/0058 | `CTSU26/0058` (`auto_unico`) | OK |
| concepto | `CANAL DE PLÁSTICO BASE DN100 H60` | `Canal de Plástico Base DN100 H60 modernizado` | OK |
| código | — | `8050-M` | OK |
| cantidad | 377 (PDF: «UNIDADES 377» / «TOTAL UNIDADES: 377u.») | 377.0 | OK |
| unidad | **`MT`** (GT) · **`u.`** (PDF) · `UD` (contrato, líneas 26345/26348) | **NULL** | **MAL** (F-024) + duda §7.3 |
| precio unitario | 9,00 (CONTRATO) | 9.0 (`contract_line_match`, línea 26345) | OK |
| importe | 3.393,00 | 3393.0 | OK |
| partida | `P4.22.02.03.01.07` | `P4.22.02.03.01.07` (`existing_matched`) | **OK — único acierto de partida del lote** |

**Total esperado 3.393,00 € · obtenido 3.393,00 € · Δ 0,00 €.**

Este documento es el contraejemplo útil: es el único **PDF nativo con texto**,
el único con partida manuscrita legible sin ambigüedad, y el único donde
`PartidaMatcher` devuelve `existing_matched` con `ia_match_trusted`. Resultado:
importe exacto.

Reparo: aunque el total cuadra, la línea arrastra 4 motivos de revisión
(`unit_category_partially_unknown`, `only_1a_available`, `ia_match_trusted`,
`no_quantity_in_albaran`, `importe_using_albaran_quantity_fallback`) y el
documento muestra **`confidence_pct_calc = 100.0`**. Ver §7.5.

---

## 8. Hallazgos transversales

### 8.1 El código de partida manuscrito falla en 6 de 7 documentos (9 de 14 líneas con partida)

| Albarán | Manuscrito en el PDF | Leído por IA1 | ¿Existe en el catálogo? | Esperado (GT) |
|---|---|---|---|---|
| 58826 | `P4.22.01.0307` | `P4.22.01.03.07` | **Sí** (id 25972) | `P5.22.01.03.07` (ver §7.2) |
| 58878 | `P5.03.04` (glifo «5» tipo T/J) | **`PT.03.04`** | No | `P5.03.04` (id 25950) |
| 225225 | `P5.14.01.02.02` (mismo glifo) | **`RJ.14.01.02.02`** | No | `P5.14.01.02.02` (id 26090) |
| 007181 L1 | `P4.09.04` | **`14.09.04`** | No | `P4.09.04` |
| 007181 L2 | `P4.08.21` | **`14.08.21`** | No | `P4.08.21` |
| 007378 L1-L7 | `P5.09.03/04/05/06`, `P5.38.07.02` | **`P05.09.03/04/05/06`, `P05.38.07.02`** | No | idem sin el 0 |
| 007378 L8 | (sin partida) | NULL | — | `ALMACEN` |
| 09256 | (sin partida en el papel) | NULL | — | `ALMACEN` |
| A261584 | `P4.22.02.0301.07` | `P4.22.02.03.01.07` | **Sí** (id 26345) | `P4.22.02.03.01.07` |

Tres modos de fallo distintos, todos sistemáticos:
- **`P5` → `PT` / `RJ`**: el «5» de este administrativo tiene un trazo superior
  horizontal largo. Ya documentado en la revisión de hormigones (225137).
- **`P4` → `14`**: la «P» se lee como «1» (Pavimarsa 007181).
- **`P5` → `P05`**: se normaliza el número a dos dígitos (Pavimarsa 007378).
  Éste es especialmente barato de arreglar: es una transformación mecánica.

Todas las partidas del catálogo llevan prefijo `P4.`/`P5.`/`CI.` (y según la
nota de cabecera del documento de dominio, los prefijos válidos del lote son
`CI`, `CD`, `CP` además de los `P4`/`P5` de parcela), así que **un código sin
prefijo válido o con `P0` es reconocible como inválido sin ambigüedad**.

Aquí, a diferencia del lote de hormigones, **el error cuesta dinero**: en el
58878 la partida correcta `P5.03.04` apunta a `GRAVA 20/40 @ 12,87` (id 25950),
que es justo el precio del GT.

**Fase**: IA1 (lectura) + IA2 (la valida como «ok» sin corregirla; ver
`143922_326_gemini_aa33401f.json`: «código de imputación manuscrito (PT.03.04)
… coinciden fielmente») + sv6 (no valida contra el catálogo).
**Clasificación**: **cubierto por F-021** y por **H-3 de la revisión de
hormigones** (falta guard en la línea base). Este lote añade la evidencia de que
también afecta al **importe**, no solo a la imputación.

### 8.2 `unidad_medida` es NULL en las 17 líneas del lote

Cero aciertos en 17 líneas, incluidas las 10 de Pavimarsa donde la unidad está
**impresa en una columna propia** («UM»: M2 / PZ / UD) y la de Vodaland
(«UNIDADES», «377u.»). Consecuencias verificadas:

1. `unidad_categoria = unknown` → `UnitCategoryGuard` → `unidad_category_match
   = false` en las 4 líneas valoradas.
2. Conversión saltada → `no_quantity_in_albaran` **con cantidad presente** en
   las 4 (F-025 confirmado).
3. Importe por `importe_using_albaran_quantity_fallback` en las 4.
4. **Y en Mahorsa, el factor 1000** (§4.1).

**Clasificación**: **cubierto por F-024**, pero este lote **eleva su gravedad**:
en el lote de hormigones el efecto era cosmético (contrato y albarán en m³);
aquí produce un error de 468.372 € en un solo documento.

### 8.3 F-025 (`no_quantity_in_albaran` falsa alarma) — confirmado en 4/4

Las 4 líneas valoradas llevan el motivo teniendo cantidad (30380, 29960, 7 y
377). Mismo mecanismo descrito en la revisión de hormigones. **Cubierto por
F-025.** Se añade un matiz: el motivo no solo es engañoso, **es el síntoma
visible del bug de §4.1**; arreglar el motivo sin arreglar el camino de
conversión ocultaría el error de importe.

### 8.4 F-020 (etiquetado de proveedor IA) — confirmado en 7/7

Los 7 documentos: `provider_origin = 'openai_fallback'`,
`comparison_summary_json.providers_available = {openai: true, gemini: false,
claude: false}`, `model_name = 'gemini-3.7-flash'` y logs de IA1/IA2
`*_gemini_*.json` con `provider: "gemini"`. Los 7 llevan
`single_provider_openai` y `document_confidence_below_threshold` en
`review_reasons_json`, con los scores por campo capados a 76,0 por
«openai_only». **Cubierto por F-020.**

### 8.5 F-019 (descuento) y F-015/F-016 — no se manifiestan

`descuento` es NULL en las 17 líneas de merge, `descuento_albaran_aplicado` es
NULL en las 4 valoradas, y la columna `descuento` del GT está vacía en las 15
filas del lote. En las 4 líneas valoradas `importe_calculado = cantidad ×
precio_unitario_final` exactamente. **Este lote no aporta ni confirma ni
desmiente F-019.** No hay líneas tachadas (F-015) ni reparto multipartida
(F-016) en ninguno de los 7 PDFs.

### 8.6 `review_phase2_*` sigue a NULL en 7/7

`review_phase2_status`, `review_phase2_summary` y `review_phase2_changes_count`
son NULL en los 7, pese a que IA2 devolvió `review_status` (`ok` en 6,
`ok_with_changes` en el 225225) con `explicacion_global` y `razonamientos`
poblados. Idéntico a la H-5 de la revisión de hormigones. **Duda ya abierta, no
se repite.**

---

## 9. Clasificación de cada diferencia

| # | Albarán(es) | Diferencia | Fase que falla | Clasificación |
|---|---|---|---|---|
| 1 | 58826, 58878 | Cantidad en KG valorada como TN (×1000) | **sv6 (reglas deterministas)**; origen en IA1/IA2 | **Defecto nuevo → H-1** (agravante de F-024 y F-025) |
| 2 | 58826, 58878 | Precio 15,43 en vez de 12,87 (+77,77 / +76,69 €) | IA3 (elige línea) + sv6 (`PartidaMatcher` no usa la línea existente de la partida) | **Defecto nuevo → H-4** |
| 3 | 225225 | Falta `INCREM. PRECIO 2026` (7 × 9,00 = 63,00 €) | IA3 (veto `tipo_familia!='hormigon'` en el prompt) + sv6 (mismo veto en `valuation_builder.py:602/686`) | **Cubierto por F-023** |
| 4 | 225225 | Precio 70,00 en vez de 72,00 (−14,00 €) | IA3 (no localiza M-7,5 en el PDF del contrato) | **Duda para el humano** (§7.1) + lectura incierta §10.3 |
| 5 | 007181, 007378 | Sin valorar (−521,07 € y −20.111,40 €) | sv3 (selector de contrato entre 2 candidatos) | **Defecto nuevo → H-3** |
| 6 | 09256 | Sin valorar (−1.129,00 €) | sv3 (`HeaderResolver`: obra por texto con empate no detectado) | **Defecto nuevo → H-2** |
| 7 | 6 de 7 docs | Partida manuscrita mal leída (`PT`, `RJ`, `14.`, `P05.`) | IA1 + IA2 (valida sin corregir) + sv6 (no valida contra catálogo) | **Cubierto por F-021** (+ H-3 de la revisión de hormigones) |
| 8 | 17/17 líneas | `unidad_medida` NULL | IA1 + IA2 | **Cubierto por F-024** (gravedad revisada al alza) |
| 9 | 4/4 líneas valoradas | `no_quantity_in_albaran` con cantidad presente | sv6 | **Cubierto por F-025** |
| 10 | 7/7 docs | `provider_origin='openai_fallback'` con modelo gemini | sv2/sv3 (merge) | **Cubierto por F-020** |
| 11 | 007378 | `precio_neto` = precio unitario (en 007181 = importe) → 8 × `line_net_mismatch` | IA1 (esquema ambiguo) | **Defecto nuevo → H-5** |
| 12 | A261584 | `confidence_pct_calc = 100` con 5 motivos de revisión en la línea | sv4 (`_compute_and_persist_confianza`) | **Duda para el humano** (§7.5) |
| 13 | 58826 vs 58878 | Mismo contrato enviado a IA3 como MD en uno y como PDF en el otro | sv3 (enriquecimiento no determinista) | **Defecto nuevo → H-6** |
| 14 | 58826 | Partida manuscrita `P4.…` frente a `P5.…` del GT | — | **Duda para el humano** (§7.2) |
| 15 | A261584 | Unidad: papel `u.`, contrato `UD`, GT `MT` | — | **Duda para el humano** (§7.3) |
| 16 | 09256 | GT internamente incoherente (1 × 157 ≠ 154) y con datos que no están en el papel | — | **Duda para el humano** (§7.4) |
| 17 | 007378 | GT: cantidad 22 pero importe 180 (= 20 × 9) | — | **Duda para el humano** (§7.6) |
| 18 | 7/7 docs | `review_phase2_*` a NULL | sv3 o por diseño | Duda ya abierta (H-5 revisión hormigones) |

---

## 10. Dudas concretas para el humano

**§7.1 — El mortero M-7,5 de Sierra Madrid a 72,00 €/m³.**
Las 95 líneas de CTSU24/0518 en Sigrid no tarifan M-7,5 (todo mortero a 70,00) y
el GT marca los 72,00 como fuente **CONTRATO**, no OFERTA. *Pregunta*: ¿está el
M-7,5 a 72,00 en el Anexo I del PDF `CTSU24_0518_277120_HORMIGONES_SIERRA_
MADRID.PED1_COMBINADO.pdf` (y entonces IA3 falló al leerlo, teniendo el PDF
adjunto), o los 72,00 salen del comparativo y la columna «CONTRATO» del Excel es
una errata? La respuesta decide si esto es un defecto de IA3 o un caso más de
F-017.

**§7.2 — La partida del 58826: ¿P4 o P5?**
El manuscrito del PDF dice `P4.22.01.0307` sin ambigüedad (trazo de «4» claro a
500 dpi), el campo DESTINO impreso dice «LAS ROZAS **PARC 4**» y la nota
manuscrita del pie dice «PARA PISCINA **PARC 4**». El GT dice
`P5.22.01.03.07`. Ambas partidas existen en el contrato y **ambas al mismo
precio (12,87)**, así que no cambia el importe. *Pregunta*: ¿es errata del
Excel, o el administrativo reimputa deliberadamente a la parcela 5?

**§7.3 — La unidad de Vodaland.**
El papel dice `377` bajo la columna «UNIDADES» y «TOTAL UNIDADES: 377u.»; las
líneas de contrato 26345/26348 dicen `UD`; el GT dice `MT`. *Pregunta*: ¿debe
extraerse la unidad **tal como aparece en el papel** (`UD`) y dejar que la
conversión a metros la haga quien conoce que el canal viene en piezas de 1 m, o
debe IA2 normalizar a `MT`? Si es lo segundo, hay que decir con qué fuente
(ficha de producto) porque el documento no la trae.

**§7.4 — El GT del 09256.**
El papel no lleva ningún precio, no lleva tonelaje de camión, dice «Horas
extras 1,5» y no menciona «JIB». El GT lleva conceptos del contrato, 1 hora
extra, y un importe de 154,00 € que no cuadra con su propio precio (157,00).
*Pregunta*: (a) ¿el importe correcto es 154, 157 o 235,50 (1,5 × 157)?; (b)
¿qué se espera del pipeline en un documento sin precios ni obra — que lo deje
sin valorar y a revisión (lo que hoy hace), o que lo valore contra el contrato
CTSB25/0708 una vez el humano fije la obra 686?

**§7.5 — Confianza 100 % con línea a revisión.**
`albaran_documents_merge.confidence_pct_calc` lo **reescribe sv4** con la
confianza de *valoración*
(`review_repository.py:_compute_and_persist_confianza` →
`domain/services/confianza.py:compute_confianza_pct`), que ignora los motivos de
revisión de línea. Vodaland sale a 100,0 mientras
`comparison_summary_json.document_confidence_pct` sigue diciendo 74,0 y la línea
lleva 5 motivos, entre ellos `no_quantity_in_albaran`. *Pregunta*: ¿es aceptable
que la lista de sv4 muestre 100 % en un documento con `review_required=true` y
motivos activos, o la confianza de valoración debe penalizar los motivos de
línea?

**§7.6 — El EUROPALET del 007378.**
El GT dice cantidad **22**, precio **9,00** e importe **180,00** (= 20 × 9). En
el PDF la cantidad impresa está tapada por una corrección manuscrita que se lee
«22». *Pregunta*: ¿22 uds (198,00 €) o 20 uds (180,00 €)? Del total esperado del
documento (20.111,40 €) dependen 18,00 €.

*(Descartada: la duda «el Excel dice 18/05 para el 225225» — el Excel dice
`datetime(2026, 5, 28)`. Descartada también: «la fecha del 09256 es el texto
'11/08/20205'» — la celda es `datetime(2025, 8, 11)`. Ambas están corregidas en
la versión actual del fichero.)*

---

## 11. Hallazgos nuevos candidatos a feature (por gravedad)

### H-1 (CRÍTICA) — La red KG→TN de `UnitConverter` es código muerto: error de ×1000 en el importe

**Qué pasa**: cuando el albarán no trae unidad y el contrato está en TN,
`ValuationBuilder` llama al conversor con `cantidad=None`
(`valuation_builder.py:1020-1030`, rama `else` de `if category_match`), y
`UnitConverter.convert` sale por la guarda `cantidad is None`
(`unit_converter.py:64-70`) **antes** de llegar al bloque de plausibilidad de
toneladas (`unit_converter.py:83-101`), que existe precisamente para eso desde
julio de 2026. Luego el importe cae al fallback con la cantidad cruda.

**Evidencia**: 30380 kg × 15,43 €/TN = **468.763,40 €** (albarán 58826) y
29960 kg × 15,43 = **462.282,80 €** (58878). El propio comentario del código
documenta el caso gemelo («29920 sin unidad … 298.302 €»). Los umbrales
(`_TN_UMBRAL_CONVERTIR = 1000`) habrían cazado ambos.

**Por qué importa**: es un error de tres órdenes de magnitud que llega
persistido a `albaran_valuations.total_valorado` y de ahí al front. Con un
documento de 468.763 € en la bandeja, la confianza en el sistema se pierde de
golpe. Y no es un caso raro: **todos** los albaranes de árido a granel vienen en
kg sin literal de unidad.

**Fase**: sv6 (reglas deterministas). Contribuyen IA1 (F-024) e IA2.

**Propuesta**: que el orden sea *convertir primero, decidir revisión después*.
Llamar siempre a `convert()` con la cantidad real y usar `category_match=False`
solo para marcar revisión, no para anular la cantidad. Alternativamente, mover
la comprobación de plausibilidad de TN a un guard previo e independiente. Añadir
un test de regresión con el caso 30380/TN.

### H-2 (ALTA) — El resolver de obra por texto no detecta empates y devuelve score 1,00

**Qué pasa**: `_match_score` (`header_resolver_service.py:57-70`) devuelve
**1.00 si un texto contiene al otro**, y el bucle de selección
(`:266-284`) usa `if score > best_score`, de modo que con varias obras empatadas
a 1,00 gana la primera del listado y el empate no se registra en ningún sitio.

**Evidencia**: el albarán 09256 solo dice «Valdebebas»; Sigrid tiene al menos
`0351 · VIV. PRADO VALDEBEBAS (UTE)…` y `0686 · HOTEL "CIUDAD AEROPORTUARIA"
VALDEBEBAS (MADRID)` (esta última verificable en `contratos_cache`). El log dice
«obra resuelta por texto: codigo=0351 score=1.00». El GT dice 686.

**Por qué importa**: la obra manda en toda la cadena (contratos, partidas,
imputación). Una obra falsa con confianza máxima es peor que no resolverla: el
documento se queda sin contrato **y** con un dato incorrecto persistido en
`obra_codigo` / `obra_nombre` que el revisor puede dar por bueno. Aquí además
arrastró la resolución de proveedor (0 proveedores en la obra 0351 → red de
familia omitida).

**Propuesta**: detectar empates (contar candidatos con `score == best_score`); si
hay más de uno, no resolver y dejar constancia (`obra_codigo_origen` +
`review_note`). Sustituir el `contains → 1.00` por una puntuación que premie la
cobertura del nombre completo, no la aparición de una sola palabra.

### H-3 (ALTA) — El selector de contrato ignora las partidas del albarán

**Qué pasa**: con 2+ contratos candidatos, `elegir_contrato_probable`
(`contrato_selector.py:79-160`) puntúa solo por **familia de producto** y
**tokens técnicos** del texto. Si no detecta familia devuelve `None` y el
documento se queda sin valorar. Además, `contrato_enrichment_service` **no le
pasa el parámetro `tipologia`** (la llamada de la línea ~466 solo envía
`contratos` y `lineas_albaran`), pese a ser «la señal más fuerte» según el
propio docstring del selector.

**Evidencia**: los dos Pavimarsa. Log: «[contrato-selector] sin familia
detectable en el albaran; no se auto-selecciona». Sin embargo las 7 partidas
manuscritas del 007378 y las 2 del 007181 existen **todas** en CTSU25/0317 con
la descripción y el precio del GT, y CTSU26/0187 solo tiene 10 partidas. Un
criterio de «cobertura de partidas del albarán en el catálogo del contrato»
habría acertado sin ambigüedad.

**Por qué importa**: dos documentos y 20.632,47 € que ni siquiera llegan a
valorarse. Los albaranes de acabados (azulejos, carpintería, sanitarios) no
tienen «familia» detectable por palabras, así que este camino se va a repetir en
todo el bloque de acabados de la obra.

**Propuesta**: añadir al selector una señal de **partidas** (fracción de las
partidas del albarán presentes en el catálogo de cada contrato) con más peso que
las familias; y pasarle `tipologia` desde sv2. Si aun así hay empate, mantener
el comportamiento actual.

### H-4 (ALTA) — La partida del albarán no se usa para elegir la línea de contrato cuando la descripción no coincide

**Qué pasa**: el prompt de IA3 le dice explícitamente «NO decides partida: solo
casas producto y precio», y `PartidaMatcher`
(`partida_matcher.py:118-153`) solo re-apunta a la partida del albarán si
encuentra **la misma descripción** dentro de ella; si no, crea una derivada con
el precio de la línea que eligió IA3.

**Evidencia**: 58826. IA3 casó `ARIDO CALIZA MACHAQUEO T-20/40-C` (15,43,
partida P4.14.01.02.01) y escribió en su razón «Existe también GRAVA 20/40 a
12,87 en misma partida P4.22.01.03.07 (id 25972); revisar cuál procede». sv6
creó `contrato_lines_derived` id 404 con 15,43 en la partida P4.22.01.03.07,
**donde ya vive la línea 25972 con el precio correcto**. Δ +77,77 € en un
documento, +76,69 € en el otro.

**Por qué importa**: contamina `contrato_lines_derived` con líneas fantasma que
duplican partidas reales (ids 404, 405, 406 en este lote; 400-403 en el
anterior), y usa un precio que el propio sistema sabe que probablemente no
procede. Es exactamente el caso que §10.8 del documento de dominio no cubre:
«re-apuntado **por descripción**» falla cuando el albarán nombra el producto de
otra manera.

**Propuesta**: antes de derivar, si la partida del albarán existe en el catálogo
y contiene **una sola** línea de la misma familia de producto, re-apuntar a ella
y marcar revisión con el motivo. Y actualizar §10.8 para decir qué manda cuando
la descripción no coincide.

### H-5 (MEDIA) — `precio_neto` no tiene una semántica única y genera `line_net_mismatch` masivo

**Qué pasa**: el mismo IA1, con el mismo prompt, rellenó `precio_neto` con el
**importe** en el 007181 (341,67 y 179,40) y con el **precio unitario** en el
007378 (14,38 en las seis primeras líneas). El validador de sv3
(`albaran_confidence_service.py:377-382`) marca `line_net_mismatch` y resta 12
puntos por línea: el 007378 acumula 8 marcas y baja a 67,69 de confianza, la más
baja del lote, por un problema de definición, no de lectura (las cantidades y
precios de ese documento son todos correctos).

**Propuesta**: fijar la semántica en el esquema y el prompt (`precio_neto` =
precio unitario neto tras descuento, y que el importe vaya a su propio campo), o
al revés — pero de forma explícita y con ejemplo. Es barato y limpia mucho ruido
de la pantalla de revisión.

### H-6 (BAJA) — Dos documentos del mismo contrato reciben el contrato en formatos distintos

**Qué pasa**: el 58826 recibió el contrato CTSU25/0085 como **Markdown**
(18.005 caracteres, `attachment.kind='text_only'`) y el 58878, 23 segundos
después, el **mismo** contrato como **PDF** de 676 KB. El motivo es que
`albaran_contratos_merge.md_sharepoint_relative_path` está relleno en la fila
251 y vacío en la 252. El log de sv5 lo dice: «[pipeline] contrato -> MD (18005
chars); no se adjunta PDF» vs «pdf=yes».

**Por qué importa**: dos ejecuciones del mismo caso no son comparables, lo que
inutiliza el banco de pruebas de modelos (§10.9 del documento de dominio pide
«mismos docs, 2 pasadas por doc»). También cambia el coste: 39.969 tokens de
entrada con MD frente a 51.700 con PDF.

**Propuesta**: hacer determinista la elección (siempre MD si existe, y
garantizar que el MD se genera **antes** de disparar la valoración, igual que ya
se hace con el PDF en el «Paso 9 — GARANTÍA de PDF» de
`contrato_enrichment_service`).

---

## 12. Lecturas inciertas declaradas

1. **58878 y 225225, código de partida manuscrito.** El segundo carácter es el
   mismo glifo ambiguo ya descrito en la revisión de hormigones (se lee entre
   `5`, `T` y `J`) incluso a 600 dpi. Se resuelven como `P5.03.04` y
   `P5.14.01.02.02` por convergencia de indicios (GT, inexistencia de `PT.*` /
   `RJ.*` en el catálogo, existencia de la partida `P5.*` con el producto y el
   precio correctos), **no por el trazo**.
2. **007378, cantidad del EUROPALET.** La cifra impresa está tapada por una
   corrección manuscrita. La corrección se lee «22»; lo impreso debajo no se
   determina ni a 800 dpi. El GT anota 22 pero su importe (180,00) implica 20.
   Ver §7.6.
3. **225225, precio 72,00 del GT.** No aparece en ninguna de las 95 líneas de
   contrato de CTSU24/0518 en BBDD, ni en el payload enviado a IA3
   (`"precio_unitario": 72` → 0 ocurrencias en
   `144029_255_claude_e82d0bae.json`). **No se ha podido inspeccionar el PDF del
   contrato**: vive en SharePoint y el log de IA no persiste el base64 del
   adjunto. Ver §7.1.
4. **09256, matrícula y referencias manuscritas.** Los campos «Camión matrícula»
   («2031 HCH» o similar) y la referencia bajo «Ha transportado» («CDL-5002-1300»
   / «PK 8500Z-1300») no se leen con seguridad. No afectan a ningún importe y
   ninguna fuente los reclama.
5. **58826, partida `P4` vs `P5`.** El trazo del PDF es un «4» inequívoco; la
   discrepancia con el GT (`P5`) se declara como duda (§7.2), no como error de
   lectura del pipeline: IA1 transcribió exactamente lo que hay escrito.
