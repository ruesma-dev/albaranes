<!-- specs/F-005-bombeo/design.md -->
# F-005 · Tanda 4a — Tipología bombeo · Diseño

Toca CUATRO piezas: **comun** (`ruesma_comun`, modelo `ContextoLinea`),
**sv2** (`services/albaranes-api`, tipología + prompt fase 2), **sv5**
(`services/albaran-valoracion-api`, routing + prompt + schema) y **sv6**
(`services/albaran-valoracion-persist`, regla determinista + builder).
No toca schema de BBDD: los datos nuevos viajan dentro de
`contexto_linea_json` (columna existente) y del envelope de valoración.

## Contexto del código real (leído, no supuesto)

- `ContextoLinea` es canónico en
  `services/albaranes-comun/ruesma_comun/contratos/contexto_linea.py` y
  está **reexportado** en sv2, sv3, sv5 y sv6
  (`domain/models/contexto_linea.py` de cada uno). Un campo nuevo en
  comun lo ven los cuatro sin tocar más ficheros. Es `extra="ignore"`:
  los campos nuevos son retrocompatibles. **Comun va horneado en cada
  imagen**: tocarlo obliga a reconstruir sv2, sv3, sv5 y sv6 en el
  despliegue (nota operativa, no tarea de esta feature).
- sv2 consolida la tipología en
  `application/services/tipologia_resolver.py` (prioridad actual:
  LER → override CIF → familia dominante `residuos` > `hormigon` >
  `mortero` > `generico`), con las detecciones de texto en
  `domain/models/tipologia.py`. **Ojo**: `texto_contiene_hormigon`
  dispara con el substring «hormig» — un albarán de PUMPING TEAM
  («SERVICIO DE BOMBEO DE HORMIGÓN») caería hoy en `hormigon`. El
  worker (`interface_adapters/worker/extraction_worker.py`) elige el
  prompt de fase 2 con `prompt_key=f"albaran_revision_fase2_{tipologia}"`
  y cae al genérico si la clave no existe: añadir la clave al YAML basta.
  `phase_merge.construir_envelope_final` sella `meta.tipologia` de forma
  genérica (acepta el valor nuevo sin cambios).
- sv5 deriva la tipología de valoración en
  `application/services/valuation_extraction_service.py::_derivar_tipologia_valoracion`
  (hoy `residuos` > `hormigon` > `generico`) y usa `valuation_{tipologia}`
  si existe (`self._prompts.has(...)`). El contexto que recibe del PG:
  cabecera del merge, líneas del albarán (con `contexto_linea_json`),
  cabecera del contrato (con rutas SharePoint del PDF y del markdown) y
  líneas del contrato (`albaran_contrato_lines_merge`: codigo_producto,
  descripcion, unidad_medida, precio_unitario, codigo_partida). El PDF o
  markdown del contrato SÍ se adjunta a la llamada LLM
  (`value_albaran_pipeline` / `LlmAttachment`). **No llega ninguna tabla
  de condiciones estructuradas del contrato** — relevante para D1.
- sv6 tiene el patrón exacto a replicar: residuos.
  `application/services/residuos_container_calc.py` es una función PURA
  (sin I/O) que transforma la cantidad valorada; el builder
  (`application/services/valuation_builder.py`, paso «4.bis») la invoca
  solo si `ctx.tipo_familia == 'residuos'`, sobreescribe
  `_cant_conv_final`/`_cant_alb_final`, arrastra `reasons` y fuerza
  revisión en los casos no calculables/implausibles. El DTO del envelope
  (`domain/models/valuation_envelope.py::LineValuationDto`) ya tiene el
  precedente del campo por-tipología `contenedor_m3` emitido por la IA.
- `UnitCategoryGuard` (sv6): si la IA emite `unidad_category_match=false`
  o las categorías reales difieren (horas=`time` vs m³=`volume`),
  `category_match=False` y `review_required` se fuerza vía
  `not category_match`. Para bombeo ese desacuerdo es ESPERADO: hay que
  neutralizarlo cuando el cálculo determinista tuvo éxito (R13).
- El registro de unidades de sv6 (`config/unit_registry.yaml`) ya tiene
  la categoría `time` con `hora`/`horas`: no se toca.
- Sin líneas sintéticas nuevas ⇒ NO aplica la regla de los «5 sitios» de
  `modifier_source` (ARCHITECTURE §dominio 10).

## Ficheros a modificar

1. `services/albaranes-comun/ruesma_comun/contratos/contexto_linea.py`
   — añadir `"bombeo"` al Literal `TipoFamilia` y dos campos opcionales
   con description: `horas_bombeo: Optional[float]` (horas de servicio de
   bombeo declaradas) y `m3_bombeados: Optional[float]` (m³ realmente
   bombeados si constan). Capa: contrato compartido (domain).
2. `services/albaranes-api/domain/models/tipologia.py` — `Tipologia.BOMBEO
   = "bombeo"`; `texto_contiene_bombeo(texto) -> bool` (palabras «bombeo»,
   «bombeado» NO — ver D2 —, «bomba» con frontera de palabra; regex
   `\b(bombeo|bomba)\b`, case-insensitive); y
   `texto_contiene_designacion_hormigon(texto) -> bool` que exponga SOLO
   el match de `_HORMIGON_REGEX` (designación posicional, sin la palabra
   «hormig»). Capa: domain.
3. `services/albaranes-api/application/services/tipologia_resolver.py` —
   `_hay_bombeo_en_linea` (familia del ctx o texto de código/concepto) y
   consolidación con la prioridad nueva: LER → override CIF → `residuos`
   → **`bombeo` si hay señal de bombeo Y ninguna línea con designación
   posicional de hormigón** → `hormigon` → `mortero` → `generico`
   (R2–R4). Capa: application.
4. `services/albaranes-api/config/prompts.yaml` — clave nueva
   `albaran_revision_fase2_bombeo` (R5), con la misma estructura
   system/task/placeholders (`{prompt_fase_1}`) que
   `albaran_revision_fase2_hormigon`. Contenido mínimo: qué es un albarán
   de servicio de bombeo, `tipo_familia='bombeo'`, `horas_bombeo` en la
   línea base, `m3_bombeados` si constan, desplazamiento con
   `rol_linea='desplazamiento'`, prohibido calcular m³ a facturar.
5. `services/albaran-valoracion-api/domain/models/valuation_models.py` —
   campo `rendimiento_minimo_m3h: Optional[float] = Field(default=None,
   description=...)` en `LineValuation` (patrón `contenedor_m3`). Capa:
   domain.
6. `services/albaran-valoracion-api/application/services/valuation_extraction_service.py`
   — `_derivar_tipologia_valoracion`: insertar `'bombeo'` entre residuos
   y hormigon (R6). Capa: application.
7. `services/albaran-valoracion-api/config/prompts.yaml` — clave nueva
   `valuation_bombeo` (R8), estructura de `valuation_residuos` como
   plantilla (mismo `schema: documento_valoracion`): match €/m³ sin
   bloqueo por unidad, lectura del rendimiento mínimo (tabla o PDF/MD)
   → `rendimiento_minimo_m3h`, prohibido calcular m³/importes, sin
   sintéticas, desplazamiento tarifado con normalidad.
8. `services/albaran-valoracion-persist/domain/models/valuation_envelope.py`
   — `rendimiento_minimo_m3h: Optional[float] = None` en
   `LineValuationDto` (R7; réplica del schema de sv5). Capa: domain.
9. `services/albaran-valoracion-persist/application/services/valuation_builder.py`
   — paso nuevo «4.ter Bombeo» inmediatamente después del «4.bis
   Residuos», espejo del patrón: si `ctx.tipo_familia == 'bombeo'` y rol
   base, invocar el calc (fichero nuevo, abajo); si devuelve m³,
   sobreescribir `_cant_conv_final`/`_cant_alb_final`, neutralizar el
   efecto de `category_match=False` sobre `review_required` (variable
   local `bombeo_ok`, misma técnica que las excepciones residuos al
   final del método), extender `reasons`, y aplicar R12/R10 forzando
   revisión cuando el calc lo pida. Además: detección de la línea de
   horas separada (R14, unidad de categoría `time` en un documento cuya
   base bombeo ya se transformó → cantidad 0 e importe 0 con razón) y
   paso limpio de la complementaria de desplazamiento (R15, sin cambios
   de código esperados: verificarlo con test). Capa: application.

## Ficheros a crear

- `services/albaran-valoracion-persist/application/services/bombeo_minimo_calc.py`
  — función PURA `calcular_bombeo_minimo(*, contexto_linea, cantidad_albaran,
  unidad_albaran, contrato_line, rendimiento_ia) -> ResultadoBombeo`
  (dataclass frozen: `m3_a_facturar: float | None`, `horas: float | None`,
  `rendimiento_m3h: float | None`, `rendimiento_fuente:
  Literal['contrato','ia'] | None`, `reasons: list[str]`,
  `forzar_revision: bool`). Lógica: horas por prioridad R9; rendimiento
  por R10 con regex sobre `contrato_line.descripcion` tipo
  `(\d+(?:[.,]\d+)?)\s*m\s*[3³c]\s*(?:/|por\s+)?\s*h(?:ora)?` (afinable
  con textos reales, como `_M3_REGEX` de residuos); plausibilidad R12
  (constantes `_RENDIMIENTO_MIN_M3H = 5.0`, `_RENDIMIENTO_MAX_M3H =
  150.0`, `_HORAS_MAX_PLAUSIBLES = 24.0`); faltantes R11. Capa:
  application. Cabecera con la regla de negocio y el caso 10,5 × 20 =
  210 documentado.
- `services/albaran-valoracion-persist/tests/` — `conftest.py` (vacío,
  ancla rootdir; primer test suite del servicio: la sección 7 bis de
  init.sh empezará a ejecutarla, comprobar pytest en su venv),
  `test_f005_bombeo_calc.py`, `test_f005_bombeo_builder.py`,
  `test_f005_envelope_dto.py`.
- `services/albaran-valoracion-api/tests/` — `conftest.py` (ídem),
  `test_f005_tipologia_valoracion.py`, `test_f005_prompt_bombeo.py`,
  `test_f005_schema_rendimiento.py`.
- `services/albaranes-api/tests/test_f005_tipologia_bombeo.py` y
  `test_f005_prompt_fase2_bombeo.py` (el directorio `tests/` +
  `conftest.py` los crea F-002 si llega antes; si no, crearlos aquí
  igual que describe su design).
- `services/albaranes-comun/tests/test_f005_contexto_linea_bombeo.py`
  — R1 (el directorio ya existe).

## Ficheros que NO se tocan

- **sv3** (`services/albaranes-persistencia`): ningún cambio de código.
  `contexto_linea` fluye como JSON y el modelo viene de comun
  (reexport); el merge de contextos es genérico. `familia_detector.py`
  (selección de contrato por familia) NO se amplía en esta feature —
  ver D6. Sí requiere rebuild en despliegue (comun horneado).
- **sv1, sv4**: nada.
- Schema PG: ninguna tabla ni columna nueva (regla ARCHITECTURE §3:
  no hay renames, sv5 no se ve afectado como lector).
- `residuos_container_calc.py`, prompts de hormigón/mortero/residuos,
  `unit_registry.yaml`, `modifier_source` (sin sintéticas nuevas),
  `json_coercion` de comun.

## Riesgos y decisiones

- **D1 — Fuente del «rendimiento mínimo del contrato» (PREGUNTA ABIERTA
  para el humano).** Hoy NO existe ninguna fuente estructurada: a sv5
  solo llegan las líneas de contrato (descripcion, unidad, precio,
  partida) y el PDF/markdown del contrato; no hay tabla de condiciones.
  Opciones:
    - **A (elegida, híbrida)**: la IA lo lee del contrato (línea o PDF)
      y lo emite estructurado (`rendimiento_minimo_m3h`), y sv6 lo
      verifica/prefiere deterministamente con regex sobre la descripción
      de la línea casada; sin verificación determinista → revisión
      (R10). Es el patrón `contenedor_m3` de residuos y no exige tocar
      sv3 ni Sigrid.
    - B: solo regex determinista en sv6 — descartada como única vía: si
      el rendimiento consta solo en el cuerpo del PDF, no hay dato.
    - C: traer condiciones estructuradas del contrato desde Sigrid
      (ampliar el enriquecimiento de sv3 + columna nueva) — descartada
      aquí: cambio de schema con lectores acoplados y sin evidencia de
      que Sigrid tenga el dato estructurado; si el humano confirma que
      existe, es feature aparte.
    **El humano debe confirmar antes de implementar**: ¿dónde consta el
    rendimiento mínimo en el contrato real de PUMPING TEAM — descripción
    de la línea, cláusula del PDF, o en ningún sitio (acuerdo no
    escrito)? Si no consta en el contrato, la opción A degrada a
    «siempre revisión» (R11) y habría que decidir C o un dato manual.
- **D2 — Prioridad bombeo vs hormigón (R3/R4).** La designación
  posicional (`HA-25`...) identifica SUMINISTRO de central y gana sobre
  la señal de bombeo; la palabra «hormig» sola no gana (un albarán de
  bombeo dice «bombeo de hormigón» sin designación). «bombeado» NO es
  señal de bombeo: «HORMIGÓN BOMBEADO» es un suministro. Riesgo
  residual: un albarán mixto real (central que factura suministro +
  servicio de bomba en el mismo papel) caerá en `hormigon`; las líneas
  de bomba irían por el flujo de complementarias de hormigón, como hoy.
  Aceptado: es el comportamiento actual y no hay caso real mixto en el
  feedback.
- **D3 — Transformación de cantidad, no sintética.** Alternativa
  descartada: emitir una sintética `bombeo_minimo` con `modifier_source`
  nuevo — tocaría los 5 sitios de la regla de sintéticas, complica el
  ground truth y no aporta: el negocio factura LA línea de bombeo por
  m³ mínimos, igual que residuos factura LA línea por contenedores.
- **D4 — Política de revisión (R10/R13).** Rendimiento confirmado por
  regex sobre la línea de contrato → línea limpia (sin revisión forzada
  por la unidad); rendimiento solo-IA o discrepante → revisión. Primera
  tipología nueva con importes «inflados» por contrato (se facturan m³
  no bombeados): la trazabilidad (`bombeo_minimo_aplicado:...`) es
  obligatoria para que el revisor vea el cálculo en sv4.
- **D5 — Despliegue.** Tocar comun ⇒ rebuild de sv2, sv3, sv5 y sv6
  (imágenes con comun horneado). Nota para el humano en el cierre; no
  hay variables de entorno nuevas ni cambios de lo que el proyecto
  expone/consume (no hay que tocar `azure-apps/albaranes.md`).
- **D6 — Selección de contrato en sv3.** `contrato_selector` puntúa por
  familia con `familia_detector.FAMILIAS` (sin «bombeo»). La selección
  primaria por CIF del proveedor (PUMPING TEAM tiene contrato propio)
  debería bastar; si la verificación manual muestra `no_contract`,
  añadir `"bombeo": ("bombeo", "bomba")` a `FAMILIAS` será un follow-up
  de una línea, fuera del alcance de esta feature.
- **Puerta de rutas sensibles (F-011).** Esta feature toca DOS prompts
  (fase 2 de sv2 y valoración de sv5) y DOS schemas de IA: cuando la
  puerta de F-011 exista, este diff la dispararía. Se incluye la tarea
  de ground truth (T8) ya en esta feature para no dejar la deuda.
- **Límite de microservicio**: respetado — extracción en sv2, lectura de
  contrato en sv5, regla determinista y persistencia en sv6, cada uno en
  su responsabilidad actual. Nada exige un servicio nuevo.
