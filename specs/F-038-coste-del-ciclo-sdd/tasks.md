<!-- specs/F-038-coste-del-ciclo-sdd/tasks.md -->
# F-038 · Tareas

Una tarea por línea. Cada una = un commit `F-038 Tn: ...`. Los tests van antes
del código (fase RED obligatoria: rigor `estandar`).

- [x] T0: `EjecutorPytest` gana `ruta` (aplicada en `correr` y en la línea base) y entra en `identidad()`; `ejecutor_para` devuelve `ruta="tests"` para lo que no cae en servicio Python si existe `<raiz>/tests`, y `None` si no (R1–R4)  |  Verificación: `python -m pytest tests/test_f038_r1_r4_ejecutor_raiz.py -q` en verde, con la traza del fallo previo pegada en `progress/impl_F-038.md`
- [x] T1: `harness/rigor.py` añade `max_mutantes_nivel`, `semilla_nivel` y `topes_tamano` (claves opcionales: ausente o inválido → `None`/`{}`) (R5, R13)  |  Verificación: `python -m pytest tests/test_f038_r5_r9_muestreo_por_nivel.py tests/test_f038_r13_r16_tamano.py -q -k rigor`
- [x] T2: `harness/rigor.json` — `nivel_por_defecto` a `estandar`, `max_mutantes`/`semilla` por nivel (estandar 20 + semilla fija; critico sin tope) y bloque `tamano` con 120/200/150/100 (R5, R8, R13)  |  Verificación: `python -m harness.rigor --validar` sale 0 e imprime `por defecto estandar`
- [x] T3: `resolver_muestreo` (función pura con la precedencia `--max-mutantes` > nivel > sin tope, y `0` = sin tope) y `_muestreo_configurado`; el CLI de `harness/mutacion.py` los usa (R6, R7)  |  Verificación: `python -m pytest tests/test_f038_r5_r9_muestreo_por_nivel.py -q`
- [x] T4: `comprobar_linea_base` devuelve `{etiqueta: segundos}`; `InformeMutacion` gana `sha_head` y `segundos_linea_base`; `harness/mutacion_paralela.py` los propaga al agregar (R10–R12)  |  Verificación: `python -m pytest tests/test_f038_r10_r12_informe.py tests/test_f012_r3_r4_reparto_agregacion.py -q`
- [x] T5: `escribir_informe` imprime SHA de HEAD medido, línea base por ejecutor (o `n/d`), media de segundos por mutante evaluado y, si procede, la línea de muestreo (R9–R12)  |  Verificación: `python -m pytest tests/test_f038_r10_r12_informe.py tests/test_mutacion_informe.py -q`
- [x] T6: crear `harness/tamano.py` (`medir`, `slug_de_feature`, `main`) con sus códigos de salida 0/1/2 (R14, R16)  |  Verificación: `python -m pytest tests/test_f038_r13_r16_tamano.py -q` y `python -m harness.tamano --feature F-038` sale 0
- [x] T7: sección **7 quater** en `harness/init.sh`: mide SOLO la feature en curso, `N/A` con motivo impreso si no hay feature, ficheros o configuración; código 1 → `init.sh` en rojo (R15, R16)  |  Verificación: `bash harness/init.sh` en verde e imprime la línea `PUERTA TAMAÑO`
- [x] T8: topes en `specs/SPECS.md`, `.claude/agents/spec-author.md` (120/200 + una tarea por línea) y `.claude/agents/implementer.md` (informe ≤ 150), con la regla «lo que no cabe se resume y se enlaza» (R17)  |  Verificación: `python -m pytest tests/test_f038_r17_r21_documentos.py -q`
- [x] T9: `.claude/agents/reviewer.md` — informe ≤ 100 líneas, umbral de reejecución de 5 min a **60 s**, revisión incremental por defecto declarando el SHA base, y RM1–RM6 (RM3 y RM4 como criterio, RM5 solo en `critico` con muestra de uno) (R18–R20)  |  Verificación: `python -m pytest tests/test_f038_r17_r21_documentos.py -q`
- [x] T10: `CHECKPOINTS.md` — C4 bis con el umbral de 60 s y un checkbox por RM1, RM2, RM5 (condicionado a `critico`) y RM6; sin puertas automáticas nuevas (R20, R21)  |  Verificación: `python -m pytest tests/test_f038_r17_r21_documentos.py -q`
- [x] T11: cabecera de invalidez en los `progress/mutacion_*.md` cuyo alcance incluye ficheros fuera de `services/` (al menos `mutacion_F-012.md`), diciendo que se midieron con la invocación rota y que hay que repetirlos (R22)  |  Verificación: `grep -l "CAMPAÑA NO VÁLIDA" progress/mutacion_F-012.md` devuelve el fichero; el resto de informes se listan en `progress/impl_F-038.md` con su decisión
- [x] T12: campaña de mutación de la feature (`python -m harness.mutacion --feature F-038`), análisis de cada superviviente y sección «Evidencias» en `progress/impl_F-038.md`  |  Verificación: `progress/mutacion_F-038.md` existe, sin `PENDIENTE`, con su SHA y su línea base impresos
- [x] T13: anotar en `progress/current.md` las tres preguntas abiertas de `requirements.md` y la deuda de remedición (D5)  |  Verificación: MANUAL (humano) — el humano responde 1, 2 y 3 antes del cierre
- [ ] T14: Ejecutar `bash harness/init.sh` en verde  |  Verificación: exit code 0

## Fuera de esta rama (después del merge en `dev`)

- [ ] P1: portar a `arnes-base` como **1.7.0** con su entrada en `GUIA_INSTALACION.md`, avisando de que `nivel_por_defecto` pasa a `estandar` y las campañas de ese nivel quedan **muestreadas**, con números no comparables con los anteriores (D6)  |  Verificación: MANUAL (humano) — `harness/VERSION` en `arnes-base` marca `1.7.0` y el diff se revisa antes de commitear
