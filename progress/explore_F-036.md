<!-- progress/explore_F-036.md -->
# F-036 — exploración de código (solo lectura, 2026-08-21)

Rutas relativas a la raíz del monorepo. sv2=albaranes-api, sv3=albaranes-persistencia,
sv5=albaran-valoracion-api, sv6=albaran-valoracion-persist.

## 1. Por qué `cantidad_convertida` sale null con cantidad_albaran=6,0 — CONFIRMADO (parcial)

La afirmación de §9.2 de la evidencia ("la única rama que devuelve None es `cantidad is None`")
es **REFUTADA**. Hay una segunda rama, y es la que aplica aquí:

- `services/albaran-valoracion-persist/application/services/unit_converter.py:149-156` —
  si `result.category_match` es False devuelve `cantidad_convertida=None`.
- `services/albaran-valoracion-persist/config/unit_registry.yaml:47-50` (m3 → categoría
  `volume`) y `:91-95` (ud → categoría `count`): m3 contra ud/contenedor es **hard mismatch**.
  Un albarán de residuos en m³ contra una línea de contrato en UD cae SIEMPRE por esa rama.
- Luego `importe_calculator.py:82-85` usa `cantidad_albaran` como fallback → 6 × 120 = 720.

Enumeración COMPLETA de ramas por las que la línea se queda sin nº de contenedores:

A. `valuation_builder.py:1051-1052` — el bloque 4.bis solo se ejecuta si `ctx is not None`
   **y** `ctx.tipo_familia == "residuos"`. Si el `contexto_linea` no llegó (ver §2) o la
   familia no es exactamente 'residuos', el cálculo **ni se intenta** y no se emite ninguna
   `reason` con prefijo `residuos_`.
B. `residuos_container_calc.py:142-151` — prioridad 1 solo dispara con `contenedores >= 1`.
C. `residuos_container_calc.py:153-169` — prioridad 2 exige que vengan **ambas**
   (`contenedores_entregados` y `contenedores_retirados`) y que la resta sea >= 1.
D. `residuos_container_calc.py:171-178` — **única** rama interna que devuelve
   `num_contenedores=None`: `volumen_m3` ausente, no numérico o <= 0 → reason
   `residuos_sin_volumen_m3`.
E. NO existe rama de None por falta de tamaño de contenedor: `:207-212` cae siempre al
   estándar de 6 m³ (`residuos_tamano_defecto_6m3`). O sea, **el tamaño del contrato no
   puede causar el null**; sí puede causar un número equivocado.
F. `valuation_builder.py:1059-1064` — al no haber número, `_cant_conv_final` pasa a ser
   `converted.cantidad_convertida`, que es None por la rama de categoría de arriba.

Dependencia con datos de los 2 albaranes fallidos: A depende de `tipo_familia`, D depende de
`volumen_m3`; el tamaño de contenedor del contrato **no** interviene. Los dos son datos que
produce la IA (fase 2 de sv2) y que viajan en `contexto_linea`.

**Discriminador barato (no lo puedo resolver leyendo código — NO CONCLUYENTE cuál de las dos
ocurrió):** mirar las `reasons`/`review_reasons_json` de la línea de SS-0003967 y SS-0801977.
Si contienen `residuos_sin_volumen_m3` → rama D (faltó `volumen_m3`). Si **no** contienen
ninguna reason `residuos_*` → rama A (el `contexto_linea` no llegó o `tipo_familia` no era
'residuos'), que es la hipótesis que las §2 y §3 hacen mucho más probable. Basta una consulta
a la valoración persistida; no hace falta reproducción instrumentada.

Nota: en ambos casos `review_required` debería salir True (`valuation_builder.py:1133-1145`
por `not category_match`, y `:1147-1148` si el cálculo dio None), así que la afirmación de la
ficha de que no hay señal de revisión conviene verificarla también en esa misma consulta.

## 2. El scorer de `contexto_linea` — CONFIRMADA

- `services/albaranes-persistencia/application/services/contexto_linea_merger.py:23-38` —
  `_score_contexto()` puntúa **exactamente cinco** campos: `tipo_familia`, `rol_linea`,
  `descripcion_extendida`, `notas_tiempo`, `ref_linea_base`. Nada más.
- El modelo tiene hoy nueve campos más:
  `services/albaranes-comun/ruesma_comun/contratos/contexto_linea.py:77-154` — `codigo_ler`,
  `volumen_m3`, `peso_toneladas`, `contenedores`, `contenedores_entregados`,
  `contenedores_retirados`, `carga_incompleta`, `m3_no_transportados`,
  `exceso_declarado_min`. **Ninguno puntúa.**
- La consecuencia descrita es real y tiene dos caras:
  - `contexto_linea_merger.py:55-58` — solo entran como candidatos los contextos con
    `score > 0`; `:60-61` si no queda ninguno devuelve **None**. Un contexto que solo trajera
    datos de residuos se descarta ENTERO y la línea se queda sin `contexto_linea` → rama A del
    punto 1 y, además, prompt genérico en sv5 (punto 3).
  - Aunque el contexto sobreviva, un candidato pobre pero con `tipo_familia`+`rol_linea`
    (score 2) **gana** a otro con `tipo_familia`+`codigo_ler`+`volumen_m3` (score 1): se elige
    el contexto íntegro por score, `:64-65`, y se pierden los m³. Esto explica exactamente un
    `volumen_m3` ausente (rama D) con el resto del pipeline intacto.
- Está en la ruta viva: `albaran_confidence_service.py:804` lo usa al fusionar proveedores.

## 3. Enrutado del prompt de fase 2 — CONFIRMADO, y hay DOS enrutados, no uno

Fase 2 de extracción (sv2):
- `services/albaranes-api/interface_adapters/worker/extraction_worker.py:69` calcula la
  tipología con `resolver_tipologia(env1["data"])` y `:87` pide
  `prompt_key=f"albaran_revision_fase2_{tip.tipologia.value}"`.
- `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py:114-116` — si esa
  clave **no está registrada**, cae al genérico `prompt_key_phase_2`
  (`services/albaranes-api/config/settings.py:147` → `albaran_revision_fase2_es`).
  Las claves existentes están en `services/albaranes-api/config/prompts.yaml:152` (`_es`),
  `:300` (`_residuos`), `:472` (`_hormigon`), `:633` (`_mortero`). Ojo: para tipología
  `generico` la clave construida (`albaran_revision_fase2_generico`) **no existe**, así que el
  fallback al `_es` es el camino normal, no un error.
- Condición exacta para el prompt de residuos: `resolver_tipologia`
  (`services/albaranes-api/application/services/tipologia_resolver.py:115-187`) devuelve
  RESIDUOS si (a) alguna línea de **fase 1** trae un LER válido (`:65-76`, `:157-168`), o
  (b) alguna línea de fase 1 trae `contexto_linea.tipo_familia == 'residuos'` (`:147-148`),
  o (c) override por CIF. **El override por CIF nunca se usa hoy**: el worker llama a
  `resolver_tipologia` sin `override_por_cif` (`extraction_worker.py:69`).
- Sí: un albarán de residuos **puede** acabar con el prompt genérico — basta con que la fase 1
  (modelo barato, `albaran_factura_es`) no emita ni LER ni `tipo_familia='residuos'`. Y con el
  prompt genérico la fase 2 no extrae `volumen_m3`/`contenedores*`, cerrando el círculo con §1.

Segundo enrutado, en la valoración (sv5) — el que más importa aquí:
- `services/albaran-valoracion-api/application/services/valuation_extraction_service.py:206-210`
  elige `valuation_{tipologia}` si existe; si no, `settings.prompt_key` = `valuation_es`
  (`services/albaran-valoracion-api/config/settings.py:210-212`).
- `_derivar_tipologia_valoracion` (`:316-335`) mira **solo** `contexto_linea.tipo_familia` de
  las líneas persistidas. **No tiene la regla dura de LER** que sí tiene sv2. Si el contexto se
  perdió en el merger (§2), sv5 valora un albarán de residuos con `valuation_es`, que es el
  prompt de hormigón/genérico y no contiene ninguna de las reglas de contenedor.

## 4. El matcher de línea de contrato y el `exact_concept` — CONFIRMADA la mecánica

- `exact_concept` **no lo decide código determinista**: es un campo que emite la IA3 y que sv6
  se limita a validar/transportar (`services/albaran-valoracion-persist/domain/models/
  valuation_records.py:21`, `domain/models/valuation_envelope.py:60`). La definición vive en el
  prompt: `services/albaran-valoracion-api/config/prompts.yaml:115` ("descripción idéntica o
  muy similar (>90%)").
- El prompt de residuos (`prompts.yaml:1008` `valuation_residuos`) pide match **semántico** por
  tipo+partida (`:1046-1065`) y admite `exact_concept` "si coincide el tipo" (`:1077-1078`).
- Con el prompt `valuation_es` (caso del punto 3) esas reglas no existen. Una línea de contrato
  "INCREMENTO LER 170604 …" contiene el LER **literal**, que es el mismo string que la IA ve en
  la línea del albarán → similitud textual >90% → `exact_concept` sobre el incremento, mientras
  que "MOVIMIENTO DE CONTENEDOR DE 6 M CUBICOS …" solo casa por significado. **Sí, es cierto que
  el incremento puede ganar al contenedor**, y con `valuation_es` es el resultado esperable.
- Aguas abajo nada lo corrige: `partida_matcher.py:100-134` **respeta el match de la IA**
  ("ia_match_trusted") y como mucho lo re-apunta a la misma descripción en otra partida
  (`:120-133`). No hay ninguna comprobación de que la línea casada en residuos sea un contenedor.
- El único matcher determinista de incrementos es `modifier_contract_matcher.py:112-239`, y para
  `rol == "incremento_residuos"` su predicado es `"RESIDUOS" in d` (`:273-274`): no sabe nada de
  códigos LER. Además solo se invoca sobre líneas `synthetic_modifier`, que en residuos no
  existen (ver §5).

## 5. Líneas sintéticas — CONFIRMADO: el mecanismo EXISTE, pero está cerrado a hormigón

- Existe inyección determinista de líneas que no vienen del albarán, dentro de sv6:
  `valuation_builder.py:422-444` añade a la lista de sintéticas los DTOs que devuelven
  `_sinteticas_m1_faltantes` (`:563-656`) y `_sinteticas_codigo_faltantes` (`:658-770`), y
  luego reutilizan toda la maquinaria normal (partida heredada, reconciliación, importe) vía
  `_build_synthetic_line` (`:1213`).
- Ambas están explícitamente limitadas a hormigón: `valuation_builder.py:602` y `:686`
  (`if ctx is None or ctx.tipo_familia != "hormigon": continue`).
- Y los prompts prohíben sintéticas en residuos:
  `services/albaran-valoracion-api/config/prompts.yaml:1017-1018`, `:1035-1036` y el
  `schema_hint` (`:1113-1118`). Por eso los incrementos LER **no se emiten nunca**: ni la IA
  puede, ni hay red determinista que los cubra.
- Punto natural para F-036(2) y para F-006 (canon de vertedero): un
  `_sinteticas_residuos_faltantes` hermano de los otros dos, llamado desde
  `valuation_builder.py:430-434`, más un predicado por LER en
  `modifier_contract_matcher._build_predicate` (`:273`) que exija el código LER de la línea base
  además del token RESIDUOS/INCREMENTO. Es el mismo enganche para ambas features.

## 6. Tests hoy

Sobre la regla de contenedores: **NINGUNO**. No hay test de `residuos_container_calc` ni en
`tests/` ni en `services/*/tests/`; la única aparición de "contenedor" es un dato de fixture del
arnés (`tests/test_f011_r5_determinismo.py:31`) y una fila de `services/albaran-valoracion-api/
tests/test_f019_r4_r7_importe_select.py`. Tampoco hay tests de `tipologia_resolver` ni de
`contexto_linea_merger`.
Sobre el matcher: solo cobertura indirecta del `PartidaMatcher` vía builder en
`services/albaran-valoracion-persist/tests/test_f027_r1_r2_r11_r13_builder.py`,
`.../test_f027_r6_r7_unidad_destino.py`, `.../test_f019_r25_r26_total_documento.py` y el
escenario compartido `.../f027_escenarios.py`; del `ModifierContractMatcher` y de
`exact_concept` en residuos, nada específico.

---

Nota de procedencia: informe producido por un subagente de exploración lanzado el 2026-08-21
en modo solo lectura; lo persistió el líder porque ese rol no tiene herramienta de escritura.

---

# APÉNDICE · confirmación contra la BBDD real (2026-08-22, solo lectura)

Consulta del humano sobre `albaran_documents_merge` + `albaran_valuations` +
`albaran_line_valuations` para los 2 disparados, el del LER y 2 de control.
**Corrige la conclusión de «raíz única» del cuerpo de este informe: son TRES
defectos independientes, y el que más euros mueve está en sv4, no en sv6.**

| Albarán | prompt_key | contexto_linea_json | cant_conv | factor | pu | importe |
|---|---|---|---|---|---|---|
| SS-0000168 | valuation_residuos | completo | **1.0** | NULL | 120 | 120 ✅ |
| SS-0000589 | valuation_residuos | completo | **1.0** | NULL | 120 | 120 (falta LER) |
| SS-0003967 | **valuation_es** | **NULL** | None | NULL | **90** | 540 ✗ |
| SS-0801977 | valuation_residuos | completo | **None** | NULL | 120 | **720 ✗** |

## D1 · sv4 destruye la cantidad valorada de residuos al guardar — CONFIRMADO

La fila de SS-0801977 trae a la vez la reason `residuos_contenedores=1 (m3=6 /
contenedor=6 m3)` —que solo escribe sv6 cuando `num_contenedores` vale 1— y
`cantidad_convertida = None`. `valuation_builder.py:1181` persiste
`cantidad_convertida=_cant_conv_final`, así que esa combinación es **imposible en
una sola pasada de sv6**: la escribió otro después.

Ese otro es `review_repository._recalc_valuation_importes` (sv4):

- `:3329-3333` — `nueva_cant_conv = factor × cantidad` y, si `factor` es None,
  **None**. En residuos `factor_conversion` es NULL SIEMPRE: m³ contra UD es hard
  mismatch (`unit_registry.yaml:47-50`, `:91-95`), confirmado NULL en las cuatro
  filas. La fórmula del front no puede reproducir un nº de contenedores.
- `:3335-3339` — sin `nueva_cant_conv`, `cantidad_efectiva` pasa a ser la cantidad
  CRUDA del albarán (6) → 6 × 120 = **720**.
- `:3399-3417` — el UPDATE pisa `cantidad_convertida`, `importe_calculado` e
  `importe_source`.
- **El guardián de R24 (F-019) no protege aquí**: `:3386-3392` compara la
  `cantidad_convertida` guardada (1.0) con la recalculada (None) y **siempre**
  difieren, así que la rama «la fila NO se toca» nunca entra en residuos. En vez
  de proteger, garantiza que se pise en el primer guardado.

Explica el patrón que desconcertaba a la ficha —mismo proveedor, mismo contrato,
misma cantidad, unos sí y otros no—: **la diferencia no está en el dato de
entrada sino en si el revisor guardó esa ficha**. SS-0000168 y SS-0000589
conservan su 1.0 porque el recálculo no llegó a sus filas.

Consecuencia operativa, valga o no para F-036: **hoy revisar en sv4 un albarán de
residuos ya valorado lo estropea**. Los 720 € no los produjo el pipeline.

## D2 · la cadena de sv3 → sv5 → matcher — CONFIRMADO en SS-0003967

Único albarán con `contexto_linea_json` NULL, y el único valorado con
`valuation_es`. Su `precio_unitario_final` es **90**, el del INCREMENTO LER
170604, con `match_method='exact_concept'`: el incremento sustituyó al
contenedor, tal como predice §4. Su importe (540 = 6 × 90) sale del fallback de
sv6 (`importe_using_albaran_quantity_fallback`), no de sv4. `rol_linea` es NULL,
coherente con un contexto que nunca llegó.

## D3 · los incrementos LER no se emiten — CONFIRMADO en SS-0000589

Regla de contenedores aplicada (1 contenedor, 120 €) y contrato con el incremento
del LER 170802 cargado, pero no hay segunda línea: faltan los 51 € hasta 171.
Ninguna línea del lote tiene `line_kind` distinto de `from_albaran`.

## Lo que ya NO hay que investigar

La ficha pedía «instrumentar sv6 y reproducirlo» para el `cantidad_convertida=null`.
No hace falta: la causa está identificada en las dos filas y son dos causas
distintas (D1 en 977, D2 en 3967).
