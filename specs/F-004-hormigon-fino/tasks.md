<!-- specs/F-004-hormigon-fino/tasks.md -->
# F-004 · Tanda 3 — Hormigón fino y veto de mortero · Tareas

Rama: `feature/F-004-hormigon-fino`. Un commit por tarea
(`F-004 Tn: ...`). Rigor `estandar`: fase RED en los requisitos centrales
(T2, T4, T5, T6), cobertura de líneas cambiadas y campaña de mutación.

**Precondición:** las preguntas P1–P4 de `requirements.md` respondidas por
el humano (afectan a T7, T8 y al alcance de la red M1).

- [ ] T1: Crear `services/albaran-valoracion-persist/tests/` y
  `services/albaran-valoracion-api/tests/` (conftest.py + helpers de
  fixture de envelope) y verificar que los venvs de ambos servicios tienen
  pytest (instalarlo en el venv si falta, NO en requirements de
  producción).  |  Verificación: `bash harness/init.sh` — la sección 7 bis
  recoge ambos servicios sin errores de intérprete.

- [ ] T2: (RED→GREEN) Re-apuntado determinista de incrementos —
  `test_f004_r1_...`/`r2`/`r3`/`r4`/`r6` en
  `tests/test_f004_reapuntado_incrementos.py` de sv6: escribirlos primero
  contra el comportamiento actual (fallan: hoy deriva sin re-apuntar);
  después `familia_base` en `ModifierContractMatcher.match()`, cableado en
  `composition.py`/`app.py` e integración en `_build_synthetic_line`
  (precio 1a = match efectivo).  |  Verificación: los tests nuevos pasan y
  la suite previa de sv6 no se rompe (`python -m pytest tests -q` en sv6).

- [ ] T3: Regresión del guard de año sobre el re-apuntado —
  `test_f004_r5_...` en `tests/test_f004_regresiones.py`: un
  `incremento_year` re-apuntado jamás queda casado con tarifa de otro año
  (caso Horpresol reproducido en fixture).  |  Verificación:
  `python -m pytest tests/test_f004_regresiones.py -q` en sv6.

- [ ] T4: (RED→GREEN) Veto de partida inexistente — `test_f004_r7_...`/
  `r8` en `tests/test_f004_veto_partida.py`; después implementar en
  `_build_synthetic_line` (partida heredada ∉ partidas del contrato →
  `codigo_partida_final=None` + `modifier_partida_not_in_contract:<p>` +
  `review_required`).  |  Verificación: tests en verde; el caso base-ALM
  (heredada None) sigue intacto.

- [ ] T5: (RED→GREEN) Veto mortero — `test_f004_r11_...`/`r12`/`r15` en
  `tests/test_f004_veto_mortero.py`; después crear
  `application/services/vetos_sinteticas.py::vetar_sinteticas_mortero`,
  flag `VETO_MORTERO_ENABLED` en settings y aplicación en `build()` (antes
  de las redes). Incluye la regresión R12 (redes M1/código no generan para
  mortero).  |  Verificación: tests en verde.

- [ ] T6: (RED→GREEN) Guard M6/M7 sin señal — `test_f004_r18_...`/`r19`/
  `r20` en `tests/test_f004_guard_m6m7.py`; después
  `vetos_sinteticas.py::vetar_m6m7_sin_senal`, flag
  `M6M7_SENAL_GUARD_ENABLED` y aplicación en `build()`.  |  Verificación:
  tests en verde; `test_f004_r22_...` (envelope antiguo válido sigue
  validando) en verde.

- [ ] T7: sv5 — rama `mortero` en `_derivar_tipologia_valoracion` —
  `test_f004_r9_...`/`r13` en `tests/test_f004_tipologia_mortero.py`
  (prioridad residuos > hormigon > mortero > generico; mixto → hormigon).
  |  Verificación: `python -m pytest tests -q` en sv5.

- [ ] T8: sv5 — prompts: nueva clave `valuation_mortero` y retoques de
  `valuation_es` (M6/M7 con señal explícita, nota de mortero para
  documentos mixtos, schema_hint) según design. Tests
  `test_f004_r10_...`/`r16`/`r17` en `tests/test_f004_prompts_yaml.py`
  (asserts de frases normativas sobre el YAML cargado con
  `YamlPromptRepository`).  |  Verificación: tests en verde.

- [ ] T9: Verificación funcional local del circuito completo (opcional
  pero recomendada): inyectar un albarán de hormigón y otro de mortero con
  el flujo de `docs/referencia/dominio_negocio_albaranes.md` §7.4 y
  comprobar en la valoración persistida: incrementos casados en la partida
  de la base (no derivados), sin sintéticas prohibidas en mortero, sin
  M6/M7 de cantidad 0 sin señal.  |  Verificación: MANUAL (humano) —
  requiere BBDD local y claves LLM; comandos exactos en §7.4.

- [ ] T10: Puertas de rigor `estandar`: cobertura de líneas cambiadas
  (init.sh) y campaña de mutación con supervivientes documentados.  |
  Verificación: `python -m harness.mutacion --feature F-004` y
  `bash harness/init.sh` (puerta de cobertura en verde o N/A justificado
  impreso por init.sh).

- [ ] T11: Puerta de rutas sensibles (F-011): registrar en
  `evals/ground_truth/IA3_valoracion.xlsx` (pestañas HOR y MOR) los casos
  de esta tanda — sintéticas esperadas, sintéticas PROHIBIDAS (mortero),
  M6/M7 con y sin señal, incremento re-apuntado a la partida de la base.
  |  Verificación: MANUAL (humano) — los .xlsx no se versionan; anotar en
  `progress/` que quedó hecho.

- [ ] T12: Actualizar documentación en el mismo trabajo:
  `docs/referencia/dominio_negocio_albaranes.md` — pasar de 🔶 a ✅ las
  reglas implementadas de §10.2 (re-apuntado, M6/M7 con señal, partida de
  incremento) y §10.3 (veto mortero), y §9.3 (mortero ya separado).  |
  Verificación: diff del documento revisado por el reviewer contra lo
  realmente implementado.

- [ ] T13: Ejecutar `bash harness/init.sh` en verde.  |  Verificación:
  exit code 0 con tests (raíz y sección 7 bis) en verde.
