<!-- progress/revision_residuos_salmedina_20260819.md -->
# Revisión del lote de residuos SALMEDINA · 2026-08-19

Siete albaranes de **SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L.**
enviados por el humano a la app local el 2026-08-19 (creados entre las 09:41
y las 09:43 UTC). Revisión hecha **por HTTP contra sv4 en local**
(`GET /documents`, `GET /api/documents/{uuid}`), sin tocar la BBDD ni ningún
recurso de Azure. Datos crudos en el scratchpad de la sesión
(`sal_SS-*.json`).

**Contrastado contra el Excel del administrativo** (`OneDrive - Ruesma/
Documentos/albaranes/evals/Copia de valoracion_alabranes.xlsx`), convertido con
la herramienta MCP `markitdown` tras reconectarla. Ver §8, que es la sección
que más importa: el ground truth cambia dos conclusiones de este informe.

## 1. Cuadro del lote

| Albarán | Fecha | LER | Cant. | Ud | Concepto | Obra | Contrato | Valorado |
|---|---|---|---|---|---|---|---|---|
| SS-0000168 | 2024-07-03 | 170201 | 6,0 | — | Madera | **0687** | **CTSU24/0228** | **120,00 €** |
| SS-0000589 | 2024-07-08 | 170802 | 6,0 | — | Mat. Yeso | — | — | — |
| SS-0003935 | 2024-07-16 | 170107 | 6,0 | — | Horm_Ladr_Cerám. | — | — | — |
| SS-0003967 | 2024-07-10 | 170604 | 6,0 | — | Mat. Aislamiento | — | — | — |
| SS-0801977 | 2024-07-18 | 170604 | 6,0 | — | Mat. Aislamiento | — | — | — |
| SS - 0025146 | 2024-11-05 | 170904 | 6,0 | — | Mat. Mezclados | 0623 | — | — |
| SS-0026122 | 2024-11-05 | 170802 | 9,0 | — | Mat. Yeso | 0623 | — | — |

Los siete: una sola línea, `single_provider_openai`,
`document_confidence_below_threshold`, `line_only_in_openai:1` y
`fecha_albaran_fuera_de_rango`. Confianza 71,3 – 82,5 %.

## 2. La valoración del SS-0000168 es CORRECTA, y por el motivo correcto

El humano seleccionó obra y contrato a mano y salió **120,00 €**. Verificado
paso a paso:

- Línea del albarán: LER `170201` «Madera», **cantidad 6,0**, `unidad_medida`
  **null**.
- Línea de contrato que casó (`26473`): **«LLEVADA CONTENEDOR 6M3» = 120 €/UD**,
  por `match_method: semantic`, confianza 70 %.
- `cantidad_convertida = 1.0`, `factor_conversion = null`,
  `importe_calculado = 120,00 €`.

El `1.0` **no** es el fallback ciego del `UnitConverter` (que con
`unidad_albaran=None` y contrato en `UD` habría devuelto 6,0 con factor 1,0, y
el importe habría sido 720 €). Sale de la regla de residuos ya implementada en
`valuation_builder.py:1046` (§4.bis): *la cantidad valorada es el nº de
CONTENEDORES, no los m³ del albarán*. `calcular_contenedores_residuos` divide
los 6 m³ del albarán entre los 6 m³/contenedor que declara el contrato → **1
contenedor × 120 € = 120 €**.

Es decir: el `6` del albarán es **la capacidad del contenedor**, no una
cantidad de material, y el sistema lo entiende. Conviene dejarlo escrito
porque invita a confusión: arreglar F-024 (extraer `unidad_medida`) **no** debe
hacer que este caso pase a valorar 720 €.

### 2.1 Lo que queda por comprobar de esa valoración

- **`lines_matched_exact: 0`**, casó por semántica al 70 %. El contrato tiene
  a la vez «CAMBIO CONTENEDOR 6M3» (120 €) y «LLEVADA CONTENEDOR 6M3» (120 €).
  Aquí da igual al importe —mismo precio— pero **no da igual a la partida**, y
  es justo la distinción LLEVAR/RETIRAR de F-006.
- **Los «INCREMENTO LER» del contrato no se han sumado.** CTSU24/0228 tarifa
  incrementos por tipo de residuo: 170202 vidrio (120 €), 170302 bituminosas
  (30 €), **170604 aislamiento (90 €)**, 170802 const. (51 €). Para el 170201
  madera **no hay incremento**, así que los 120 € parecen completos. Pero
  cuando se valore el **SS-0003967 o el SS-0801977 (ambos LER 170604)** el
  resultado esperado sería **120 + 90 = 210 €**, no 120 €. Sin caso valorado
  todavía, no se puede afirmar que el pipeline lo haga.

## 3. Por qué no encontró obra: NO es que no esté indicada

Los **siete** albaranes traen `obra_codigo` y `obra_nombre` a null en la
extracción, pero **los siete traen dirección de obra**. El resolutor por texto
acertó en tres y falló en cuatro **que son la misma obra** que uno de los
aciertos:

| Albarán | Dirección leída | Obra |
|---|---|---|
| SS-0000168 | `M-401 - S/N, FUENLABRADA` | **0687** ✔ |
| SS-0000589 | `CTRA. M-401 km 1'800, FUENLABRADA` | — ✘ |
| SS-0003935 | `M 401 S/N, FUENLABRADA` | — ✘ |
| SS-0003967 | `CRTA 401 MADRID TOLEDO P.K. 1800, FUENLABRADA` | — ✘ |
| SS-0801977 | `CTRA M-401 PK 1.800, FUENLABRADA` | — ✘ |
| SS - 0025146 | `c/ Futbol Sala 4, Leganes` | 0623 ✔ |
| SS-0026122 | `CALLE FUTBOL SALA 4, LEGANES` | 0623 ✔ |

La obra 0687 es **CENTRO PRIMERA ACOGIDA DE MENORES «LA CANTUEÑA»**, con
dirección registrada *Carretera A42 Madrid-Toledo, Km. 18., 28947 FUENLABRADA*.
Las cuatro direcciones fallidas son esa misma carretera escrita de otra forma
(`CTRA.`/`CRTA`/`M 401`/`M-401`, `km 1'800`/`P.K. 1800`/`PK 1.800`).

**Conclusión**: el dato está, es deducible, y el matching de dirección lo
resuelve o no según la grafía. Entra de lleno en **F-029** (obra resuelta por
texto), que hoy está redactada sobre el problema contrario —score 1,00 a la
obra equivocada—; este lote aporta el **falso negativo**: cuatro documentos sin
obra teniendo la dirección delante. Nótese que 0623 sí casó con dos grafías
distintas (`c/ Futbol Sala 4` y `CALLE FUTBOL SALA 4`), así que el matcher
normaliza algo, pero no las abreviaturas de carretera ni los puntos
kilométricos.

## 4. El CIF se lee mal en 3 de 7

CIF real de SALMEDINA: **B82899550** (el que casó en el SS-0000168).

| Albarán | CIF leído | Desviación |
|---|---|---|
| SS-0000168, SS-0000589, SS-0003967 | `B82899550` | correcto |
| SS-0003935 | `null` | no se leyó |
| SS - 0025146 | `B823**05**550` | 2 dígitos |
| SS-0026122 | `B828**39580**` | 3 dígitos |
| SS-0801977 | `B828**90**550` | 1 dígito |

Los tres mal leídos arrastran `proveedor_cif_no_casa`. Es la causa directa de
que **SS - 0025146 y SS-0026122 no tengan contrato pese a tener obra (0623)**:
sin proveedor resuelto no hay contrato que buscar. Material para **F-030**
(IA2 busca el proveedor parecido cuando el CIF no casa): aquí la distancia es
de 1 a 3 dígitos sobre un CIF que además aparece bien leído en otros tres
documentos **del mismo lote y el mismo proveedor**.

### 4.1 Cruce de causas

| Situación | Albaranes | Causa que bloquea |
|---|---|---|
| Obra ✔ + CIF ✔ | SS-0000168 | ninguna — valorado |
| Obra ✘ + CIF ✔ | SS-0000589, SS-0003967 | **solo la obra** |
| Obra ✔ + CIF ✘ | SS - 0025146, SS-0026122 | **solo el CIF** |
| Obra ✘ + CIF ✘/null | SS-0003935, SS-0801977 | las dos |

Es decir: **arreglar el matching de dirección (F-029) desbloquea 2 albaranes;
arreglar el CIF (F-030) desbloquea otros 2**; los otros 2 necesitan ambas.

## 5. Otros hallazgos del lote

- **Una sola IA extrajo los siete.** Todos con `provider_origin:
  openai_fallback` y a la vez `model_name: gemini-3.7-flash`, y motivo
  `single_provider_openai`. Sin segunda opinión no hay contraste, y de ahí que
  los siete caigan por `document_confidence_below_threshold` (71-82 %). Es
  exactamente **F-020** (el pipeline debe ser agnóstico al proveedor de IA); el
  lote es evidencia nueva y además muestra que la etiqueta `openai_*` se aplica
  a una extracción hecha con Gemini, con lo que el motivo de revisión que ve el
  humano es engañoso.
- **`unidad_medida` null en las 7 líneas** → **F-024**. Aquí no daña porque la
  regla de contenedores no la usa, pero es el mismo agujero.
- **`fecha_albaran_fuera_de_rango` en los 7**: son albaranes de 2024 procesados
  en 2026 (777 días en el SS-0000168). Esperable en un lote de prueba; conviene
  no leerlo como señal de calidad del documento.
- **SS-0026122 trae cantidad 9,0** frente al 6,0 de los demás: contenedor de
  9 m³. Cuando se le asigne contrato habrá que comprobar qué hace
  `calcular_contenedores_residuos` si el contrato solo tarifa contenedores de
  6 m³ (¿1,5 contenedores? ¿línea de 9 m³ sin tarifa?). Es un caso límite que
  hoy no está cubierto por ningún test conocido.

## 6. El Excel del administrativo: RESUELTO

La MCP `markitdown` no estaba disponible al empezar la revisión: el servidor
arrancó tarde (descarga de `uvx markitdown-mcp`) y sus herramientas no llegaron
a registrarse en la sesión, aunque `claude mcp list` lo daba por conectado. El
humano lo reconectó con `/mcp` y la conversión se hizo por el camino normal que
manda `CLAUDE.md`.

El Markdown resultante **no se versiona**: el libro trae precios de proveedor.
El contraste está en §8; el fichero convertido no se ha guardado en
`docs/referencia/`.

Nota para la próxima vez: si `markitdown` aparece como «still connecting» al
arrancar la sesión, hay que reconectarla con `/mcp` antes de trabajar con
documentos. Ya está en caché de `uv`, así que no debería repetirse.

## 7. Qué haría con esto

Ninguna de estas features es nueva; el lote **refuerza y precisa** cuatro que
ya están en el backlog:

- **F-029** — añadir el falso negativo: normalizar abreviaturas de vía
  (`CTRA`/`CRTA`/`CARRETERA`) y puntos kilométricos (`km 1'800` / `P.K. 1800`
  / `PK 1.800`) antes de comparar. Cuatro casos reales de la misma obra.
- **F-030** — el CIF con 1-3 dígitos de diferencia respecto a uno que el mismo
  lote lee bien tres veces.
- **F-020** — evidencia de que la etiqueta de proveedor de IA no corresponde al
  modelo que trabajó.
- **F-006** — LLEVAR/RETIRAR y, sobre todo, **los incrementos por LER**, que
  este lote permite probar de verdad (170604 con incremento de 90 € en el
  contrato).

Y una comprobación que no cuesta nada y hoy nadie hace: **un test de regresión
con el SS-0000168** que fije 120 € — un contenedor, no seis m³ — para que el
arreglo de F-024 no lo convierta en 720 €.

---

# 8. Contraste contra el Excel del administrativo (ground truth)

Convertido con la MCP `markitdown` (reconectada por el humano). El Excel trae
los siete albaranes de residuos **al final de la Hoja1**, con la valoración que
el administrativo da por buena.

## 8.1 Lo que dice el ground truth

| Albarán (Excel) | Obra | Contrato | Partida | Líneas esperadas | **Total** |
|---|---|---|---|---|---|
| 168 | 687 | CTSU24/0228 | CI.03A.7 | CAMBIO CONTENEDOR 6M3 · 1 UD · 120 € | **120,00 €** |
| 3935 | 687 | CTSU24/0228 | CI.03A.7 | CAMBIO CONTENEDOR 6M3 · 120 € | **120,00 €** |
| 589 | 687 | CTSU24/0228 | CI.03A.7 | CAMBIO 120 € + **INCR. LER 170802** 51 € | **171,00 €** |
| 3967 | 687 | CTSU24/0228 | CI.03A.7 | CAMBIO 120 € + **INCR. LER 170604** 90 € | **210,00 €** |
| 1977 | 687 | CTSU24/0228 | CI.03A.7 | CAMBIO 120 € + **INCR. LER 170604** 90 € | **210,00 €** |
| 25146 | **691** | **CTSU24/0402** | CI.03A.7 | CONTENEDOR RESIDUOS 6 M3 · 136 € | **136,00 €** |
| 26122 | **691** | **CTSU24/0402** | CI.03A.7 | CONTENEDOR 9 M3 · 183 € (OFERTA) + **INCR. LER 170802** 77 € (OFERTA) | **260,00 €** |

**En los siete la cantidad correcta es `1,00 UD`**, no los 6 (ni los 9) del
albarán. Queda confirmado por el ground truth lo que §2 dedujo del código: el
número que trae la línea es la **capacidad del contenedor**, y la cantidad
valorada es **el número de contenedores**. La regla 4.bis del
`valuation_builder` hace lo correcto.

## 8.2 Los 120,00 € del SS-0000168 coinciden… con el concepto equivocado

El total cuadra con el ground truth. Pero la línea que el sistema eligió es
**«LLEVADA CONTENEDOR 6M3»** y la que el administrativo valora es **«CAMBIO
CONTENEDOR 6M3»**. Las dos cuestan 120 € en CTSU24/0228, así que **el acierto
del importe tapa un error de match**. Con otra tarifa —o en otro contrato— ese
mismo fallo daría un importe equivocado sin que nada lo señalara.

Súmese que **la partida esperada es `CI.03A.7`** y el sistema dejó
`codigo_partida_final: null`. Es decir: importe correcto, concepto equivocado y
partida ausente. Un test que solo mire el total daría este caso por bueno; hay
que fijar también **concepto casado y partida**. Esto refuerza F-006
(LLEVAR/RETIRAR) y F-021 (validación de partida contra el catálogo).

## 8.3 CONFIRMADO: los incrementos por LER no se están sumando

§2.1 lo planteó como hipótesis y el ground truth lo confirma. Tres de los siete
llevan una **segunda línea de incremento según el código LER del residuo**:

- **SS-0000589** (LER 170802): 120 + **51** = **171,00 €**
- **SS-0003967** (LER 170604): 120 + **90** = **210,00 €**
- **SS-0801977** (LER 170604): 120 + **90** = **210,00 €**

Esas líneas de incremento **existen en el contrato CTSU24/0228** —el sistema
las tiene cargadas, se ven en `contrato_lines`— pero el pipeline no las emite:
el albarán trae UNA línea y la valoración produce UNA línea. Falta la regla que
dice «si la familia es residuos y el LER de la línea tiene incremento tarifado
en el contrato, emite la línea sintética del incremento».

Coste del fallo: **infravalora un 43 % en el 170604** (120 € frente a 210 €) y
un 30 % en el 170802. Sin ninguna señal de revisión que lo advierta.

Nótese que el **SS-0000168 (LER 170201 madera) no tiene incremento tarifado**,
y por eso sus 120 € son completos. Es decir: el único albarán que el humano
valoró a mano es, por casualidad, **el único de los siete cuyo caso no ejercita
esta regla**.

## 8.4 CORRECCIÓN a §3: no es solo falso negativo, hay obra EQUIVOCADA

§3 dio por buenos los dos aciertos de la obra 0623 (SS-0025146 y SS-0026122).
**El ground truth dice que la obra de esos dos es la 691, no la 0623**, y su
contrato el **CTSU24/0402**, no el CTSU24/0228.

Así que el balance real del lote es peor de lo que decía §3:

| Documento | Obra del sistema | Obra real | Veredicto |
|---|---|---|---|
| SS-0000168 | 0687 | 687 | correcta |
| SS-0000589, SS-0003935, SS-0003967, SS-0801977 | — | 687 | **falso negativo** (×4) |
| SS - 0025146, SS-0026122 | **0623** | **691** | **FALSO POSITIVO** (×2) |

Un falso positivo es mucho peor que un falso negativo: el documento **no queda
esperando**, entra en el circuito con una obra ajena y con un contrato que no
es el suyo. Esto ya no es material para F-029 «también»: **es exactamente el
caso que F-029 describe** (score alto a la obra equivocada), con dos ejemplos
reproducibles.

No he podido comprobar en Sigrid qué obra es la 691 ni si comparte dirección
con la 0623 (desde local solo se consulta vía sigrid-api, y el listado del
front local únicamente muestra obras que ya tienen albaranes). Queda como
verificación para el humano: **si la 691 y la 0623 comparten la dirección de
c/ Fútbol Sala 4 (Leganés), el matcher no tiene forma de distinguirlas por
texto** y hará falta otro criterio —fecha, contrato vigente del proveedor,
elección asistida (F-007)—.

## 8.5 Otros contrastes

- **La numeración del Excel no lleva prefijo ni ceros**: `168`, `589`, `1977`,
  `3935`, `3967`, `25146`, `26122`. Ojo con `1977`: el sistema leyó
  **`SS-0801977`**. O el administrativo lo abrevió, o la IA leyó de más. Hay
  que decidir cuál es el número bueno antes de usar esto como caso de evals.
- **El SS-0026122 se valora contra OFERTA, no contra contrato**: el contenedor
  de 9 m³ (183 €) y su incremento (77 €) vienen marcados como `OFERTA` en el
  ground truth. Es decir, el caso del contenedor de 9 m³ que §5 señalaba como
  límite **no se resuelve prorrateando 9/6**: se resuelve con **otra tarifa**,
  que además no está en el contrato sino en la oferta. Esto es **F-017** (el
  comparativo como fuente de precio) y es condición para valorar bien ese
  albarán.
- **El CIF del Excel es `B82899550`** en los siete, lo que confirma §4: el CIF
  bueno es ese y los tres que el sistema leyó distinto son errores de lectura.

## 8.6 Qué cambia en el plan

Además de lo dicho en §7:

1. **La regla de incrementos por LER es el defecto de más impacto del lote**
   (3 de 7 albaranes, hasta un 43 % de infravaloración) y no está cubierta por
   ninguna feature con ese nombre. Encaja en **F-006** (residuos: canon y
   lógica de pago), cuya spec conviene releer antes de arrancarla para ver si
   la contempla; si no, hay que ampliarla o dar de alta una feature propia.
2. **El caso de regresión que §7 proponía (SS-0000168 = 120 €) es insuficiente
   por sí solo**: es el único de los siete que no ejercita los incrementos.
   El caso bueno para evals es el **SS-0003967 (210 €)**, que ejercita
   contenedor + incremento LER; y el **SS-0026122 (260 €)**, que además
   ejercita oferta y contenedor de 9 m³.
3. **Fijar en el test el concepto y la partida, no solo el total** (§8.2).

---

# 9. Segunda pasada: con obra y contrato puestos a mano (2026-08-19, ~12:44)

El humano seleccionó obra y contrato en los siete y se revaloraron. Datos en el
scratchpad (`despues/*.json`); la foto previa se conserva (`sal_*.json`), lo que
permite comparar antes/después.

## 9.1 Resultado frente al ground truth

| Albarán | Obra | Contrato | **Total ahora** | **GT** | |
|---|---|---|---|---|---|
| SS-0000168 | 0687 | CTSU24/0228 | 120,00 € | 120,00 € | ✔ |
| SS-0003935 | 0687 | CTSU24/0228 | 120,00 € | 120,00 € | ✔ |
| SS-0025146 | 0691 | CTSU24/0402 | 136,00 € | 136,00 € | ✔ |
| SS-0000589 | 0687 | CTSU24/0228 | 120,00 € | **171,00 €** | ✘ corto (−51) |
| SS-0026122 | 0691 | CTSU24/0402 | 272,00 € | **260,00 €** | ✘ (+12) |
| SS-0003967 | 0687 | CTSU24/0228 | **540,00 €** | **210,00 €** | ✘✘ ×2,6 |
| SS-0801977 | 0687 | CTSU24/0228 | **720,00 €** | **210,00 €** | ✘✘ ×3,4 |

**Obra y contrato quedan correctos en los siete** una vez puestos a mano
(incluida la 0691 que §8.4 señalaba). Lo que falla ahora es **la valoración**.

## 9.2 La regla de contenedores se aplica en 5 de 7 — y en 2 no

| Albarán | `cantidad_albaran` | `cantidad_convertida` | precio | importe |
|---|---|---|---|---|
| SS-0000168 | 6,0 | **1,0** | 120 | 120,00 € |
| SS-0003935 | 6,0 | **1,0** | 120 | 120,00 € |
| SS-0000589 | 6,0 | **1,0** | 120 | 120,00 € |
| SS-0025146 | 6,0 | **1,0** | 136 | 136,00 € |
| SS-0026122 | 9,0 | **2,0** | 136 | 272,00 € |
| SS-0003967 | 6,0 | **null** | 90 | **540,00 €** |
| SS-0801977 | 6,0 | **null** | 120 | **720,00 €** |

Cuando `cantidad_convertida` es `null`, el `importe_calculator` cae a
`cantidad_albaran` y multiplica por la capacidad del contenedor: **6 × 120 =
720**, **6 × 90 = 540**. Es la sobrevaloración que §2 advertía como riesgo
teórico de F-024 — solo que **ya está ocurriendo**, sin necesidad de tocar nada.

Lo que hace el caso difícil: entrada idéntica a la de los que sí funcionan
(mismo proveedor, mismo contrato `CTSU24/0228`, misma cantidad 6, mismo tipo de
documento). Y leyendo `unit_converter.convert()`, la única rama que devuelve
`cantidad_convertida=None` es `cantidad is None`, que aquí **no se cumple**
(vale 6,0). Es decir: **la explicación no está en la lectura del fichero**; hay
que instrumentar sv6 y reproducirlo. No lo doy por diagnosticado.

## 9.3 El incremento LER: ausente en uno, y usurpando la línea buena en otro

- **SS-0000589** (LER 170802): 120,00 € y debía ser **171,00 €**. Falta la línea
  `INCREMENTO LER 170802 ... 51 €`, que **está cargada** en `contrato_lines`.
- **SS-0003967** (LER 170604): casó `match_method: exact_concept` con la línea
  de **incremento** (90 €) **en lugar de** con el contenedor. El código LER
  aparece literal en la descripción de la línea de incremento, así que gana el
  match exacto sobre el semántico del contenedor. El incremento no solo falta:
  **a veces sustituye a la línea principal**.

## 9.4 El contenedor de 9 m³ (SS-0026122): 272 € vs 260 €

El sistema hace `9 / 6 = 1,5` y redondea a **2 contenedores × 136 € = 272 €**.
El ground truth no prorratea: usa **otra tarifa**, la de contenedor de 9 M3
(**183 €**) más su incremento (**77 €**) = 260 €, **ambas de OFERTA, no del
contrato**. O sea que el redondeo de contenedores no es solo impreciso: **es el
enfoque equivocado** cuando existe tarifa para ese tamaño. Depende de **F-017**.

## 9.5 Sobre el CIF: NO estaba bien en ninguno de los tres

Respuesta a la duda del humano, con la foto previa delante:

| Albarán | CIF leído (antes) | Correcto | Diferencia |
|---|---|---|---|
| SS-0801977 | `B82890550` | `B82899550` | **1 dígito** |
| SS-0025146 | `B82305550` | `B82899550` | 3 dígitos |
| SS-0026122 | `B82839580` | `B82899550` | 4 dígitos |
| SS-0003935 | `null` | `B82899550` | no se leyó |

Los tres traían `proveedor_cif_no_casa:<cif>` en `review_reasons_json`, o sea
que **el sistema sabía que el CIF no casaba**. Por qué «parecía correcto» en el
front: **`proveedor_nombre` se muestra siempre bien** —«SALMEDINA TRATAMIENTO DE
RESIDUOS INERTES, S.L.»— porque se lee del documento, no de la resolución
contra Sigrid. Con el nombre correcto a la vista, un CIF con un dígito cambiado
(`B82890550`) pasa desapercibido.

**Esto es un defecto de interfaz, no solo de extracción**: el front debería
mostrar el CIF como *no resuelto* cuando `proveedor_cif_no_casa` está presente,
en vez de enseñar un nombre que da confianza. Añádase a **F-030**.

Caso del **SS-0025146**: el humano observa que «el CIF parecía bien pero el
proveedor no está en la obra original». Los dos datos estaban mal a la vez
—CIF `B82305550` **y** obra `0623` en lugar de `691`—, así que aunque el CIF se
hubiera leído bien, buscar contrato del proveedor en la obra 0623 no habría
dado nada: **el CTSU24/0402 pertenece a la obra 691**.

## 9.6 Los IDs de línea de contrato cambian en cada re-fetch

Hallazgo lateral con consecuencias. En la foto previa el CTSU24/0228 tenía las
líneas `26471`-`26479`; ahora las mismas siete líneas son `26465`-`26516`. Las
valoraciones guardan `matched_contrato_line_id` apuntando a filas **que ya no
existen**: el SS-0000168 apunta a `26473` y esa fila ya no está.

Consecuencia práctica: **no se puede auditar contra qué línea de contrato se
valoró un albarán** en cuanto se re-fetchean los contratos. Toda la trazabilidad
precio -> línea de contrato se rompe en silencio. No tiene feature: decidir si
se arregla con IDs estables (upsert en vez de borrar+insertar) o guardando la
descripción junto al id.

## 9.7 Altas en el backlog

- **F-036** (prioridad 3, rigor `critico`) - los dos defectos de §9.2 y §9.3.
  Reconciliar con **F-006** antes de arrancarla.
- **F-037** (prioridad 4) - guardado inmediato al seleccionar contrato, pedido
  por el humano. Lleva anotado el riesgo de F-019: cada guardado del revisor
  pasa por `_recalc_valuation_importes`, y automatizarlo multiplica la
  frecuencia con que se ejecuta ese camino.
