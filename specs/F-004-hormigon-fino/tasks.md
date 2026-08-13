<!-- specs/F-004-hormigon-fino/tasks.md -->
# F-004 · Tanda 3 — Hormigón fino y veto de mortero · Tareas

Rama: `feature/F-004-hormigon-fino`. Un commit por tarea
(`F-004 Tn: ...`). Rigor `estandar`: fase RED en los requisitos centrales
(T2, T4, T5, T6, T7, T8), cobertura de líneas cambiadas y campaña de
mutación. Las preguntas P1–P4 están respondidas (ver «Decisiones tomadas»
en requirements.md): no queda ninguna precondición humana.

- [ ] T1: Crear `services/albaran-valoracion-persist/tests/` y
  `services/albaran-valoracion-api/tests/` (conftest.py + helpers de
  fixture de envelope) y verificar que los venvs de ambos servicios tienen
  pytest (instalarlo en el venv si falta, NO en requirements de
  producción).  |  Verificación: `bash harness/init.sh` — la sección 7 bis
  recoge ambos servicios sin errores de intérprete.

- [ ] T2: (RED→GREEN) Re-apuntado determinista de incrementos —
  `test_f004_r1_...`/`r2`/`r3`/`r4`/`r6`/`r14` en
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
  de las redes). Incluye la regresión R12 (la red de CÓDIGO no genera para
  mortero).  |  Verificación: tests en verde.

- [ ] T6: (RED→GREEN) Guard M6/M7 sin señal — `test_f004_r18_...`/`r19`/
  `r20` en `tests/test_f004_guard_m6m7.py`; después
  `vetos_sinteticas.py::vetar_m6m7_sin_senal`, flag
  `M6M7_SENAL_GUARD_ENABLED` y aplicación en `build()`.  |  Verificación:
  tests en verde; `test_f004_r22_...` (envelope antiguo válido sigue
  validando) en verde.

- [ ] T7: (RED→GREEN) Consistencia a precio cero (decisión P3) —
  `test_f004_r23_...` en `tests/test_f004_consistencia_cero.py` de sv6
  (sintética de consistencia sin tarifa → precio 0, importe 0, sin
  `modifier_identified_no_tariff` ni revisión; con tarifa → sin cambios);
  después la normalización en `_build_synthetic_line` (punto 5 del
  design).  |  Verificación: tests en verde.

- [ ] T8: (RED→GREEN) Red M1 extendida a mortero (decisión P1) —
  `test_f004_r24_...` en `tests/test_f004_m1_mortero.py` de sv6 (base
  mortero + contrato CTSU{AA}: genera los años que faltan con descripción
  «...EN MORTERO»; tarifa solo entre líneas con token MORTERO; sin tarifa
  → Forma C; dedupe y guard de año operativos); después aflojar el filtro
  de familia de `_sinteticas_m1_faltantes` según el punto 6 del design.
  |  Verificación: tests en verde y regresión hormigón intacta.

- [ ] T9: sv5 — rama `mortero` en `_derivar_tipologia_valoracion` —
  `test_f004_r9_...`/`r13` en `tests/test_f004_tipologia_mortero.py`
  (prioridad residuos > hormigon > mortero > generico; mixto → hormigon).
  |  Verificación: `python -m pytest tests -q` en sv5.

- [ ] T10: sv5 — prompts: nueva clave `valuation_mortero` (con reglas M1
  de año y consistencia-a-cero) y retoques de `valuation_es` (M6/M7 con
  señal explícita, M2 sin Forma C, nota de mortero para documentos mixtos,
  schema_hint). Tests `test_f004_r10_...`/`r16`/`r17` (y los asserts de
  prompt de R23/R24) en `tests/test_f004_prompts_yaml.py`.  |
  Verificación: tests en verde.

- [ ] T11: Verificación funcional local del circuito completo (opcional
  pero recomendada): inyectar un albarán de hormigón y otro de mortero con
  el flujo de `docs/referencia/dominio_negocio_albaranes.md` §7.4 y
  comprobar en la valoración persistida: incrementos casados en la partida
  de la base (no derivados), sin sintéticas prohibidas en mortero, M1 de
  año presente en mortero, consistencia sin tarifa a 0, sin M6/M7 de
  cantidad 0 sin señal.  |  Verificación: MANUAL (humano) — requiere BBDD
  local y claves LLM; comandos exactos en §7.4.

- [ ] T12: Puertas de rigor `estandar`: cobertura de líneas cambiadas
  (init.sh) y campaña de mutación con supervivientes documentados.  |
  Verificación: `python -m harness.mutacion --feature F-004` y
  `bash harness/init.sh` (puerta de cobertura en verde o N/A justificado
  impreso por init.sh).

- [ ] T13: Puerta de rutas sensibles (F-011): registrar en
  `evals/ground_truth/IA3_valoracion.xlsx` (pestañas HOR y MOR) los casos
  de esta tanda — sintéticas esperadas, sintéticas PROHIBIDAS (mortero),
  M6/M7 con y sin señal, consistencia sin tarifa a precio 0, M1 de año en
  mortero, incremento re-apuntado a la partida de la base.  |
  Verificación: MANUAL (humano) — los .xlsx no se versionan; anotar en
  `progress/` que quedó hecho.

- [ ] T14: Actualizar documentación en el mismo trabajo:
  `docs/referencia/dominio_negocio_albaranes.md` — pasar de 🔶 a ✅ las
  reglas implementadas de §10.2 (re-apuntado, M6/M7 con señal, partida de
  incremento) y §10.3 (veto mortero), reflejar las decisiones P1/P3
  (M1 en mortero; consistencia sin tarifa a precio cero) y §9.3 (mortero
  ya separado).  |  Verificación: diff del documento revisado por el
  reviewer contra lo realmente implementado.

- [ ] T15: Ejecutar `bash harness/init.sh` en verde.  |  Verificación:
  exit code 0 con tests (raíz y sección 7 bis) en verde.
