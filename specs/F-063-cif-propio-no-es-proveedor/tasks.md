# F-063 · tareas

Rama `feature/F-063-cif-propio-no-es-proveedor`. Una tarea = un commit `F-063 Tn: …`. Rigor `critico`: fase RED registrada en `progress/impl_F-063.md`. Tests de sv3 con `services/albaranes-persistencia` como raíz; los de comun, con `services/albaranes-comun`.

- [x] T0: spec, alta de F-063 en `harness/features.json` (`in_progress`) y `BACKLOG.md` regenerado  |  Verificación: `python harness/backlog.py --check` (o `init.sh`) sin diferencias
- [x] T1: comun — `ruesma_comun/proveedores/propios.py` con `CIFS_PROPIOS_POR_DEFECTO`, `cifs_propios` y `es_cif_propio` (R1, R2)  |  Verificación: `pytest tests/test_f063_cifs_propios.py` (comun)
- [x] T2: sv3 — constantes de dominio, puerto y `descartar_cif_propio` del repositorio (R4, R10, R13)  |  Verificación: `pytest tests/test_f063_cif_propio.py -k repo`
- [x] T3: sv3 — resolver: descarte al principio de `_resolve_proveedor`, respeto al `manual`, best-effort; setting `CIFS_PROPIOS` y cableado (R3–R8, R10)  |  Verificación: `pytest tests/test_f063_cif_propio.py -k resolver`
- [x] T4: sv3 — resolver: los CIF propios nunca son candidatos (paso 1, paso 2 y red por CIF) (R9)  |  Verificación: `pytest tests/test_f063_cif_propio.py -k candidato`
- [ ] T5: sv3 — doble `fixture_f063` y pipeline con el caso real en las tres rutas, sin candidato y control negativo (R11, R12)  |  Verificación: `pytest tests/test_f063_cif_propio.py -k pipeline`
- [ ] T6: docs — `docs/ARCHITECTURE.md` regla 18 y `.env.example` de sv3  |  Verificación: el reviewer contrasta los textos con R1–R13
- [ ] T7: cobertura de lo cambiado ≥ 80 % y campaña de mutación completa (`critico`)  |  Verificación: `python -m harness.cobertura --base dev --config harness/rigor.json` y `progress/mutacion_F-063.md` válido, 0 supervivientes sin test o justificación
- [ ] T8: MANUAL (humano, tras fusionar en `dev`) — desplegar SOLO sv3 (`.\deploy.ps1 -Only sv3`, `.\check_deploy.ps1`) y re-procesar desde sv4 el albarán de FEYMACO  |  Verificación: MANUAL (humano): merge con A28733558 y contrato encontrado
- [ ] T9: `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh` termina en verde
