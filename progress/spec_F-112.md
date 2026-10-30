# F-112 · Informe del spec-author (2026-10-29)

Spec en `specs/F-112-anio-fecha-albaran/` (requirements, design, tasks). Rigor `estandar`, servicio sv2. Estado en
`features.json` sin tocar (`pending`). Va después de F-106.

## 1. Medición en producción (solo lectura)

Sesión PostgreSQL de Azure con `options=-c default_transaction_read_only=on` y `SHOW transaction_read_only = on`
comprobado antes de cada consulta; clave de Key Vault a variables del proceso, borradas en `finally`. Scripts en el
scratchpad de la sesión, no en el repositorio. Base: `albaran_documents_merge` activos (`is_active`).

- Activos: 163; sin fecha: 5; sin `email_received_datetime`: 0; comparables: 158.
- Distancia |fecha − recepción|: ≤ 30 días 135; 31–90 0; 91–365 4; **> 365 días 19 (12 %)**. Octubre: 17 de 155.
- Los 19, **todos con la fecha ANTERIOR** a la recepción. **16 de 19** tienen día y mes coherentes con la recepción
  (con el año de la recepción caen a ≤ 60 días): es el año lo que está mal.
- Año leído: 2006 (1), 2016 (1), 2020 (5), 2023 (3), 2024 (4), 2025 (5). Diferencia en años: 1 (5), 2 (4), 3 (3),
  6 (5), 10 (1), 20 (1): casa con la última cifra (y a veces la penúltima) de «2026» mal leída.
- Por proveedor (lejos / comparables): FEYMACO 6/15, MACOTRAN 4/4, HERMANOS SAN JUAN 3/6, CARGA Y TRANSPORTE DE CUBAS
  2/2, GRÚAS Y TRANSPORTES TRAURA 1/2, SALMEDINA TRATAMIENTO DE RESIDUOS INERTES 1/2, HORMIGONES Y CEMENTOS ANDALUCES
  1/1, ÁRIDOS ANFERSA 1/17.
- Por familia: **residuos 10/15**, generico 7/76, hormigon 2/61.
- Sin el patrón de año (posible otra fecha del papel): 3, todos de residuos (CARGA Y TRANSPORTE DE CUBAS 2, SALMEDINA 1).
- **Qué IA falla**: en los 19, la fecha de IA1 (`raw_extraction_json → debug.phase_2.debug.phase_1_json`) es igual
  que la final: IA1 lee mal e IA2 lo confirma. En el total, IA2 cambia la fecha de IA1 en 21 de 158 documentos.
- Nota: de los 5 de HERMANOS SAN JUAN de la ficha, en activos quedan 3 a más de un año.

## 2. Lo que se ha encontrado en el código

- IA1 usa `albaran_factura_es` de `config/prompts.yaml`; `config/prompts/svc2_prompt_albaran_factura_es.yaml` no lo
  carga nadie (corrige la premisa del encargo). La regla de cabecera es solo «fecha: la del albarán».
- La recepción ya llega a sv2: `ContextoCorreo.recibido_utc` en el blob lateral desde F-048. sv2 no lee
  `raw_context_json` (es de sv3) ni lo necesita.
- IA2 recibe el task de fase 1 renderizado (`{prompt_fase_1}`) y la checklist en sus cuatro prompts: un marcador y una
  regla llegan a las dos IAs sin tocar los prompts de fase 2.
- El banco cubre `fecha` (campo crítico, 59 casos de IA1) pero sin correo ni recepción y sin ningún caso del fallo:
  hace falta el comparador nuevo con tres juegos (design §7).

## 3. Enmienda v1.1 (2026-10-30, respuesta del humano a la PARADA 1)

Cita literal: «añade que ia2 revisara tambien la fecha. el problema vendra cuando estemos en un cambio de año
(diciembre o enero)». Y sobre D7: «mejor 416 lecturas».

- **IA2 revisa SIEMPRE la fecha** en una sección propia de sus cuatro prompts (`{revision_fecha}`, R17–R18), en lugar de
  la regla de checklist de la v1; su efecto (fecha de IA1 frente a la final) se mide aparte (R21, R29, C5).
- **Cambio de año**: la referencia ya no es «el año del correo» sino la Regla del año (fecha igual o algo anterior a la
  recepción; día y mes posteriores ⇒ año anterior; 28-12 con correo del 03-01 ⇒ año anterior; un año legible y
  plausible manda). Va igual en IA1 e IA2 y con cualquier fecha (R28). Juego D con cinco sintéticos (R27, C6). Riesgo
  en design §9 y repetición de la medición en enero de 2027.
- **D7 = 416** (decidida). **D8**: la cierra el líder leyendo los 19 en Blob (permiso de lectura del humano).
- D1–D6 y D9 siguen como propuestas recomendadas, pendientes de que el humano las confirme.

## 4. Enmienda v1.2 (2026-10-30): juego A y cierre de la PARADA 1

- Juego A leído en el papel por el líder (`progress/juego_a_F-112.md`): 14 errores de año, 1 dudoso, 4 fechas
  antiguas de verdad (controles de D4, criterio C7). D8 cerrada: los 3 «sin patrón» eran antiguos de verdad.
- Pista nueva: 5 de los 14 dieron 2020 por el «R.D. 553/2020» impreso; la Regla del año dice que el año nunca sale
  de una referencia normativa (R.D., Orden, Ley).
- Decisiones: D1–D6 y D9 = (a), dadas por buenas por el humano («doy por bueno a»); D7 = 416.
- **Señalada al líder (resuelta en la v1.3, D2 = b)**: D2 (a) (fecha UTC) choca con la regla del cambio de año en la primera hora
  o dos del 1 de enero (fecha UTC 31-12 ⇒ un albarán del 01-01 iría al año anterior). La (b), fecha de Madrid, lo
  evita. Detalle en design §9.

## 5. Enmienda v1.3 (2026-10-30): D2 = (b) y PARADA 1 cerrada

- El humano elige **D2 = (b)**: la referencia es el día de recepción del correo pasado a Europe/Madrid, no la fecha
  UTC. Cambian R1, R2 y R27; nuevo R30 (`tzdata` en sv2). Caso de Nochevieja SIN-006: correo a las 23:30 UTC del
  31-12, que en Madrid ya es 01-01.
- **PARADA 1 de F-112 cerrada**: D1 y D3–D9 en (a) (D8 cerrada con el juego A), D7 = 416, D2 = (b).
- El estado de `features.json` no se ha tocado (lo pasa el líder).

## 6. Decisiones de la v1 (historial; estado actual en el §5)

- **D1** dónde entra la referencia: IA1 + regla de IA2 (recomendada), solo IA1, o solo IA2.
- **D2** fecha UTC (recomendada) u hora de Madrid. **D3** sin correo: sin referencia (recomendada) u «hoy».
- **D4** albarán con fecha antigua impresa de verdad: la IA la devuelve tal cual, sin campo nuevo; sv3, sv9 y F-108
  cubren el resto (recomendada).
- **D5** sin marcador no se añade nada (permite medir `base`).
- **D6** umbral de C1: 80 % del juego A con mayoría exacta tras IA2.
- **D7** tamaño de la medición de pago: decidida en la v1.1, 416.
- **D8** los 3 de residuos sin patrón de año: ¿otra fecha del papel? Lo dice el humano al montar el juego A.
- **D9** versionar `evals/casos_fecha.json` (solo fechas y tipología).
- Para montar el juego A el humano tiene que leer en el papel la fecha verdadera de los 19 (design §7.1).
