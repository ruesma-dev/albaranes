<!-- progress/current.md -->
# Trabajo en curso

## Estado tras la sesión del 2026-08-13 (líder)

- **F-001 done** (APPROVED sin cambios). Su cierre vive en la rama
  `feature/F-001-test-estructura`, pendiente de merge a `dev` por el humano.
- **F-011 spec_ready** — spec en `specs/F-011-evals-ia/` (rama
  `feature/F-011-evals-ia`); 5 preguntas abiertas en su requirements.md.
- **F-002 spec_ready** — spec en `specs/F-002-obra-proveedor/` (rama
  `feature/F-002-obra-proveedor`); preguntas y decisiones abajo.
- Orden de merge sugerido al humano: F-001 → F-011 → F-002. En
  `features.json` deben quedar F-001 done, F-011 spec_ready, F-002
  spec_ready; en `progress/current.md` gana esta versión.
- NO avanzar ninguna spec a in_progress sin aprobación humana explícita.

## F-002 — decisiones abiertas que debe validar el humano

1. **P1 — Criterio de «obra activa» en Sigrid.** `search_obras` de sv3
   devuelve TODAS las obras (`obr JOIN con`) sin filtro de vigencia. Falta
   el criterio o el visto bueno al provisional: lista completa capada a
   `OBRAS_ACTIVAS_MAX` (300).
2. **P2 — Volumen real de obras** que devuelve la query (calibrar el cap y
   el aviso de truncado a 1.000 filas de sigrid-api). Consulta MANUAL.
3. **P3 — Umbral de la propuesta de proveedor** (R9): se propone reutilizar
   `HEADER_RESOLVER_MIN_SCORE` (0.5). ¿Umbral propio?
4. **D1 — sv2 pasa a llamar a sigrid-api directamente** (nuevo secret
   `SIGRID_API_FUNCTION_KEY` en `ca-sv2-extraccion` + actualización de
   `azure-apps/albaranes.md`). Alternativas descartadas en design.md.
5. **Gap detectado y resuelto en la spec**: en modo colas
   `email_received_datetime` queda NULL en el merge (el contexto de email
   vive en `workflow_runs.payload_json` y el worker de sv3 no lo recupera).
   La spec lo corrige (R12) porque el guard de año lo necesita.

### Notas para el implementer de F-002

- Sin DDL nuevo: columnas existentes (`review_required`,
  `review_reasons_json`, `review_notes`, `obra_codigo_origen`,
  `email_received_datetime`).
- `ruesma_comun` NO se toca (rebuild de 4 imágenes).
- Crear `tests/` en sv2 y sv3 activa la sección 7 bis de init.sh: comprobar
  `pytest` en los venvs de esos servicios antes de la primera tarea de tests.
- Compatibilidad con F-011 (evals): bloque de obras determinista (orden por
  código, formato fijo) y schema de salida de IA1 sin cambios.

## F-005 (bombeo) — spec escrita; D1 RESUELTA por el humano (2026-08-13)

Spec en `specs/F-005-bombeo/` (rama `feature/F-005-bombeo`). Sin
bloqueantes: la fuente del rendimiento mínimo (D1) quedó decidida por el
humano — la extracción (IA1/IA2, sv2) caza horas/m³/rendimiento impresos
en el albarán (`horas_bombeo`, `m3_bombeados`, `rendimiento_m3h_albaran`
en `contexto_linea`); la valoración lee el mínimo del CONTRATO (sv5 lo
emite en `rendimiento_minimo_m3h`; sv6 verifica con regex y aplica
m³ = horas × rendimiento). Caso canónico con errata §10.7 corregida:
10,5 h × 20 m³/h = 210 m³ (PUMPING TEAM).

Decisiones de diseño que el humano puede vetar al aprobar la spec:

1. **D2** — designación posicional (HA-25) gana sobre señal de bombeo;
   la palabra «hormigón» sola no; un albarán mixto suministro+bomba
   seguiría cayendo en hormigón (comportamiento actual).
2. **D4** — política de revisión: rendimiento confirmado por regex sobre
   la línea de contrato → línea limpia; rendimiento solo-IA o
   discrepante → revisión.
3. Nota despliegue: se toca `ruesma_comun` → rebuild de sv2, sv3, sv5 y
   sv6. Sin env vars nuevas; `azure-apps/` no cambia. T8 deja anotado el
   caso PUMPING TEAM para el ground truth de F-011 (dos prompts nuevos =
   ruta sensible).

## F-004 (hormigón fino y veto de mortero) — spec escrita; P1–P4 RESUELTAS (2026-08-13)

Spec en `specs/F-004-hormigon-fino/` (requirements EARS R1–R24, design, 15
tareas). Sin preguntas abiertas: las cuatro decisiones del humano están
incorporadas — P1: M1 de años también en mortero, DENTRO de la feature
(R24); P2: cantidad impresa < umbral tarifado = señal explícita de M7
(R17); P3: consistencia se emite en AMBAS familias y sin tarifa va a
precio CERO, ni revisión ni omisión (R23, normalizada en el builder de
sv6); P4: M5 en mortero si el contrato la tarifa (R10(c)).

Alcance: sv5 (prompts `valuation_es` + nueva `valuation_mortero`, rama
mortero en la derivación de tipología) y sv6 (cablear el
`ModifierContractMatcher` — escrito pero nunca conectado —, re-apuntado de
incrementos a la partida de la base antes de derivar, veto de partida
inexistente, veto mortero, guard M6/M7 sin señal, consistencia a cero y
red M1 extendida a mortero). Sin cambio de schema Pydantic (la regla de
los 5 sitios no se dispara) ni de BBDD.

Avisos al implementer: crear `tests/` en sv5/sv6 activa la sección 7 bis
de init.sh (pytest en esos venvs); rutas sensibles de F-011 → T13 exige
actualizar el ground truth de IA3 (pestañas HOR/MOR, se rellena a mano,
los .xlsx no se versionan); D3 elimina la línea informativa M6 de 0
minutos (manda §10.2).

## F-003 — spec escrita y decisiones incorporadas (2026-08-13, spec-author)

Spec en `specs/F-003-valorados-match-estricto/` (requirements EARS R1–R15,
design, 13 tareas). Hallazgo clave, trazado en el código: el importe de
línea impreso NO existe en el pipeline (sv2 no lo extrae, sv3 no tiene
columna, sv5 lo recompone como `cantidad × precio_neto`), y el prompt de
IA1 ordena calcular `precio_neto = cantidad*precio*(1-dto/100)` — ese es
el mecanismo exacto del caso ×120 (23.073,60 € por 191,40 €). Alcance:
sv2 (prompt + schema: `importe`, `descuentos` lista, `importe_total` +
`importe_total_incluye_iva`), sv3 (4 columnas nuevas idempotentes), sv5
(contexto + prompts IA3/IA4 con match estricto) y sv6 (guard aritmético de
línea y de total, regla ORE OIL, dto no sobre precio de contrato, red
determinista de atributo sustantivo). Sin tocar `ruesma_comun`.

Las tres preguntas abiertas están RESPONDIDAS por el humano (2026-08-13) e
incorporadas a la spec («Decisiones tomadas» en design.md):

1. **P1** — las sintéticas M1–M7 mantienen la herencia del descuento del
   padre; R5 limitado a `from_albaran`.
2. **P2** — ampliación de alcance a sv2/sv3 confirmada («sí, hay que
   extraer el importe y persistirlo»); rebuild de 4 imágenes y orden de
   arranque sv3 → sv5.
3. **P3** — cambio sobre la propuesta: el total CON IVA se transcribe y se
   marca (`importe_total_incluye_iva=true`); el guard de total deja aviso
   `guard_aritmetico_total_con_iva` sin forzar revisión (R2/R7/R8 y D2
   ajustados).

Avisos al implementer: crear `tests/` en sv5/sv6 activa la sección 7 bis
de init.sh; los prompts tocados (IA1, IA3, IA4) son ruta sensible de
F-011 → T10 exige actualizar el ground truth (×120, ORE OIL, CETOSA,
elemento base 0,5 mm, bolsa de cuñas); la red de atributo sustantivo solo
detecta atributos numéricos con unidad — los modelos no numéricos (CETOSA)
los cubren los prompts (limitación documentada, D5).

## F-007 — spec escrita y decisiones P1–P3 incorporadas (2026-08-13, spec-author)

Spec en `specs/F-007-partida-alm-selector/` (requirements EARS R1–R15,
design con «Decisiones tomadas», 10 tareas). Alcance: sv6 (almacén por
defecto para suministros en `partida_matcher`/`valuation_builder`,
`partida_action` nuevo `alm_default`, sin DDL) y sv4 (etiqueta «Almacén»,
grupo «Candidatas (mismo recurso)» en el combo de partida existente, tabla
nueva `partida_memoria` para prerrellenar por obra+producto). No toca
sv2/sv3/sv5 ni `ruesma_comun`.

Respuestas del humano (2026-08-13) incorporadas:

1. **P1** — suministro = `tipo_familia` nulo u «otro» (familias destinadas
   configurables), con aclaración semántica clave: **ALM no es un código
   de partida real** — almacén = `codigo_partida_final` NULL; la marca es
   `partida_action`; la vista muestra «Almacén» y hacia Sigrid la partida
   irá EN BLANCO. Regla anotada como contrato semántico para **F-013**
   (registro en Sigrid): recogerla en su spec cuando se escriba.
2. **P2** — SÍ: «Traer líneas de contrato» y «+ a Sigrid» también
   alimentan la memoria (cuatro caminos, mismo upsert; R10 y T6).
3. **P3** — retención sin límite ni caducidad (last-writer-wins, solo
   prerrellena UI).

Avisos al implementer: crear `tests/` en sv6/sv4 activa la sección 7 bis
de init.sh (pytest en esos venvs); `partida_memoria` la crea sv4
(precedente `undo_log`) y hay que anotar la doble propiedad en
ARCHITECTURE (T9); el detalle de sv4 debe dejar de resucitar la partida
del contrato cuando la línea está en estado almacén (R15) — sin eso el
almacén no se ve; kill-switch `ALM_DEFAULT_ENABLED` por entorno.

## Pendientes señalados por F-001 (decisión humana)

1. `init.sh` sección 7: acotar la recolección de pytest de la raíz
   (`testpaths` o argumento) — hoy ejecuta la suite de comun dos veces,
   ~100 s de peaje por portero. Mejora genérica: propagar a arnes-base.
2. Instalar `coverage` y `ruff` en el venv de la raíz antes de la primera
   feature que toque código de producción (F-002 lo necesitará).
3. Automejoras de protocolo propuestas por el reviewer
   (`progress/review_F-001.md`, sección final): fase RED para features cuyo
   entregable es un test, y control del cero en la verificación de mutación.
