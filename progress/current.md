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

## Pendientes señalados por F-001 (decisión humana)

1. `init.sh` sección 7: acotar la recolección de pytest de la raíz
   (`testpaths` o argumento) — hoy ejecuta la suite de comun dos veces,
   ~100 s de peaje por portero. Mejora genérica: propagar a arnes-base.
2. Instalar `coverage` y `ruff` en el venv de la raíz antes de la primera
   feature que toque código de producción (F-002 lo necesitará).
3. Automejoras de protocolo propuestas por el reviewer
   (`progress/review_F-001.md`, sección final): fase RED para features cuyo
   entregable es un test, y control del cero en la verificación de mutación.
