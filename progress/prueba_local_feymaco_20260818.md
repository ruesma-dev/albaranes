# Prueba local 18-08-2026 — lote FERRETERIA (Feymaco 2.139.643 y 2.137.569)

Ejecutada por el humano contra el pipeline local (Azurite + PG local), con los
dos PDFs del lote `alvaro_17082026` enviados a `dev@ruesma.es`, y repetida
contra producción (`albaranes@ruesma.es`) con el mismo resultado.

Revisado con el humano el 18-08. **Se descuentan como diferencias las que
corresponden a features aún no implementadas** (reparto multipartida F-016,
líneas tachadas F-015): no son fallos, son trabajo pendiente. La unidad de las
líneas finales (UD) es correcta, y la fecha del 2.137.569 (2026-06-01) también.

## 1. Dónde está la salida de cada IA (en local)

| Qué | Dónde |
|---|---|
| Llamada completa a cada IA (request + response + duración) | `services/<servicio>/logs/ia/AAAAMMDD/HHMMSS_mmm_<proveedor>_<hash>.json` |
| Traza de ejecución del servicio | `services/<servicio>/logs/*.log` |
| Envelope de IA1+IA2 persistido | `albaran_documents_merge.raw_extraction_json` (`debug.phase_1` / `debug.phase_2`) |
| Envelope de IA3 (valoración) | `albaran_valuations.raw_ia_envelope_json` |

De la ejecución del 18-08: 4 volcados en sv2 (`085914`, `085922`, `085929`,
`085936`, todos `gemini`) y 3 en sv5 (`090043`, `090102`, `090109`, todos
`claude-opus-4-8`; el tercero es la **conciliación IA4**, que sí corre aunque
no deje rastro en BBDD).

## 2. Diagnóstico: la lectura es correcta, la aplicación no

La extracción de IA1 es **exacta** en los dos albaranes: códigos de artículo,
cantidades, precios, descuento y neto de línea coinciden con el PDF. Lo que
falla es cómo esos campos se aplican a las líneas finales.

**Regla del negocio (humano, 18-08)**: cuando el PDF trae cantidad, precio
unitario y descuento, el importe es

```
importe = cantidad × precio_unitario × (1 − descuento/100)
```

y el unitario leído **manda**. Solo cuando faltan esos campos y sí hay importe
final se despeja el unitario de esa misma fórmula.

### Causa raíz (encadenada)

1. **sv5 fabrica mal el importe.**
   `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py`
   (~líneas 100-123, comentado como «FIX jun 2026») calcula
   `importe_albaran = cantidad × precio_neto`, dando por hecho que
   `precio_neto` es un **unitario neto**. Pero el prompt de IA1
   (`services/albaranes-api/config/prompts.yaml:75`) define `precio_neto` como
   `cantidad*precio*(1 - descuento/100)`, es decir el **importe de la línea**
   — que es justo lo que trae la columna NETO de Feymaco. Resultado:
   108 × 35,19 = **3.800,52 €** donde el albarán dice 35,19 €.

2. **sv6 da prioridad al importe sobre el unitario leído.**
   `application/services/price_reconciler.py` (prioridad 1) usa el importe y
   deriva `unitario = importe / (cantidad × (1 − dto/100))`; el unitario
   declarado solo se respeta si coincide. Con el importe inflado sale
   3.800,52 / (108 × 0,6) = **58,65 €/ud** en vez de 0,543.

Corrigiendo **solo el punto 1**, la cadena cuadra sola: importe 35,19,
cantidad 108, dto 40 % → derivado 0,543 = declarado → `albaran_declared`,
importe 35,19. El punto 2 queda como decisión de diseño a alinear con la regla
del humano (el unitario leído debe mandar, no solo empatar).

### Efecto medido

| Albarán | Total correcto | Total obtenido |
|---|---|---|
| 2.139.643 | 19,41 € | 970,50 € |
| 2.137.569 | 139,66 € | 6.238,14 € |

Líneas del 2.137.569 (precio aplicado / importe):

| Concepto | Correcto | Obtenido |
|---|---|---|
| PAPEL HIGIENICO (SACO 108) | 0,543 / 35,19 | 58,6500 / 3.800,52 |
| LTS. JABON LIQUIDO PH NEUTRO | 3,422 / 20,53 | 34,2167 / 205,30 |
| ROLLO PAPEL IND. | 7,726 / 55,63 | 92,7167 / 667,56 |
| KGS AÑIL ESPECIAL FEYMACO | 5,497 / 13,19 | 21,9833 / 52,76 |
| BOLSA BASURA 52X58 | 0,252 / 15,12 | 25,2000 / 1.512,00 |

## 3. Segundo fallo: la partida «P4/P5.36.01» se lee como «PJ.36.01»

El manuscrito agrupa con una llave las tres primeras líneas hacia
**P4/P5.36.01** y las dos últimas hacia **CI.4.18**. La IA leyó «P4/P5» como
«PJ» y no propagó la llave a las líneas 2 y 3 (les puso CI.04.18).

**Regla del humano**: la **barra siempre significa que la línea se separa en
dos o más partidas** (aquí, en el primer nivel). Idea a estudiar: pasar al
prompt la lista de capítulos/partidas de primer nivel del contrato para que la
lectura se apoye en un catálogo cerrado en vez de adivinar los caracteres.

Encaja con F-016 (reparto multipartida), que hoy no está implementada: la
lectura correcta del código es requisito previo del reparto.

## 4. Etiquetado incorrecto del proveedor (ruido de revisión)

El diseño de sv2 es **una IA por fase**, no tres en paralelo: el log de wiring
dice `Proveedores LLM cargados: ['openai','gemini','claude'] | FASE 1=gemini .
FASE 2=gemini`. Pero sv3 clasifica el resultado como `openai_fallback`, guarda
`provider_origin='openai'` con `model_name='gemini-3.7-flash'`, capa la
confianza a 84 % y añade `single_provider_openai`,
`document_confidence_below_threshold` y `line_only_in_openai:N`.

Consecuencia: **todos** los documentos van a revisión con motivos que no
describen lo que pasó. O el confidence service aprende que el modo normal es
una IA por fase, o hay que decidir volver a multi-proveedor en fase 1.

## 5. Otros datos de la ejecución

- **F-002, check 5 (la K)**: el log de sv2 dice `obras_activas=275` en las dos
  extracciones. 275 < `OBRAS_ACTIVAS_MAX=300`, así que **el prompt no está
  recortando la lista** y no aparece el aviso de truncado.
- **La fecha del 2.139.643** sigue mal: el PDF y el ground truth dicen
  `05/06/2026` y la IA devolvió `2026-09-05`.
- **obra_nombre del 2.139.643**: la IA devolvió «88+88 VIVIENDAS KODAK-LAS
  ROZAS» (nombre de la lista de obras activas) en vez del impreso «176 VIV.
  LAS ROZAS». En el 2.137.569 sí devolvió el impreso.
- **`unidad_medida` llega NULL** desde IA1 en todas las líneas; sv6 la resuelve
  a UD por el contrato (por eso el bloque final se ve correcto), pero mientras
  tanto marca `unit_category_partially_unknown` / `ia_unit_category_mismatch`.
- **Matching semántico contra partida alzada**: sv5 casó el papel higiénico con
  «MATERIAL DE FERRETERIA» del contrato (4.000 €/ud, confianza 30 %). El precio
  se descartó correctamente, pero conviene revisar si ese match debe producirse.
- **IA2 no aporta**: `razonamientos: []` y `review_phase2_status/summary/
  changes_count` en NULL para los dos documentos.

## 6. Qué sale de aquí para el backlog

1. **Nueva feature (crítica)**: el importe de línea. Alinear la semántica de
   `precio_neto` entre el prompt de IA1 y el consumidor de sv5, y hacer que el
   unitario leído mande cuando existan cantidad + precio + descuento.
   Es un fallo de producción con efecto directo en el importe valorado.
2. **F-016** (multipartida): añadir a su alcance la lectura del separador «/»
   y la propuesta de pasar el catálogo de partidas de primer nivel al prompt.
3. **Revisar** el etiquetado de proveedor y la penalización de confianza de sv3
   (hoy describe mal lo que ocurre y manda todo a revisión).
