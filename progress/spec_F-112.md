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

## 3. Decisiones abiertas para el humano (PARADA 1, design §9)

- **D1** dónde entra la referencia: IA1 + regla de IA2 (recomendada), solo IA1, o solo IA2.
- **D2** fecha UTC (recomendada) u hora de Madrid. **D3** sin correo: sin referencia (recomendada) u «hoy».
- **D4** albarán con fecha antigua impresa de verdad: la IA la devuelve tal cual, sin campo nuevo; sv3, sv9 y F-108
  cubren el resto (recomendada).
- **D5** sin marcador no se añade nada (permite medir `base`).
- **D6** umbral de C1: 80 % del juego A con mayoría exacta tras IA2.
- **D7** tamaño de la medición de pago: 728 llamadas (B completo) o 416 (B a 20 casos).
- **D8** los 3 de residuos sin patrón de año: ¿otra fecha del papel? Lo dice el humano al montar el juego A.
- **D9** versionar `evals/casos_fecha.json` (solo fechas y tipología).
- Para montar el juego A el humano tiene que leer en el papel la fecha verdadera de los 19 (design §7.1).
