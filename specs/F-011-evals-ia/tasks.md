<!-- specs/F-011-evals-ia/tasks.md -->
# F-011 · Evals de IA con ground truth y puerta en el arnés — Tareas

Rama: `feature/F-011-evals-ia`. Un commit por tarea (`F-011 Tn: ...`).
Rigor `estandar`: fase RED con traza real en los requisitos centrales
(R2, R4, R10, R17–R22), cobertura de líneas cambiadas y campaña de mutación.

**Antes de T1**: resolver con el humano las preguntas abiertas P1–P5 de
`requirements.md` (en especial P4, exigencia inicial, y P5, dependencias).

- [ ] T1: `evals/requirements.txt` + instalación en el venv raíz, y
      `evals/modelos.py` + `evals/barrido.py` (patrones C3 bis).
      | Verificación: `tests/test_f011_r4_barrido.py` en RED y luego verde
      (correo, IP, GUID, token detectados; texto limpio pasa).
- [ ] T2: `evals/conversor.py`: localización de tablas, convenios de celda,
      salida determinista, fallos por libro/pestaña ausente y aborto por
      barrido sin escritura parcial.
      | Verificación: `tests/test_f011_r1_r2_r3_conversor.py`,
      `tests/test_f011_r5_determinismo.py`, `tests/test_f011_r6_ausencias.py`
      (libros sintéticos construidos con openpyxl en el propio test).
- [ ] T3: ejecutar el conversor real sobre los 5 libros y versionar
      `evals/fixtures/` (hoy sin casos: estructura + metadatos).
      | Verificación: `python -m evals.conversor` exit 0; `git status`
      muestra solo JSON bajo `evals/fixtures/`; ningún xlsx en el commit.
- [ ] T4: `evals/comparador.py` + `evals/informe.py` (render y
      `parsear_veredicto`).
      | Verificación: `tests/test_f011_r2_comparador.py`,
      `tests/test_f011_r12_informe.py`.
- [ ] T5: `evals/procesos/ia34.py` modo determinista (envelope estimulado con
      prohibidas inyectadas, redes reales de sv6, stubs de IA y repositorio;
      ejecución secuencial).
      | Verificación: `tests/test_f011_r10_determinista.py` (asserta además
      cero llamadas de red con clientes-trampa) y
      `tests/test_f011_r14_secuencial.py`.
- [ ] T6: `evals/procesos/ia12.py` (composición mínima sv2) y modo real de
      `ia34.py` (contexto sv5 desde fixtures); fallo temprano sin claves.
      | Verificación: `tests/test_f011_r8_ia12.py`,
      `tests/test_f011_r11_ia34_real.py` (clientes LLM falsos inyectados),
      `tests/test_f011_r9_omitidos.py`.
- [ ] T7: `evals/runner.py`: CLI, subprocesos por servicio, agregación,
      informe en `progress/`, exit codes y NO_EVALUABLE sin casos.
      | Verificación: `tests/test_f011_r7_cli.py`,
      `tests/test_f011_r13_exit_codes.py`, `tests/test_f011_r15_sin_casos.py`.
- [ ] T8: `harness/rutas_sensibles.py` (genérico) +
      `harness/rutas_sensibles.json` (declaración de albaranes).
      | Verificación: `tests/test_f011_r16_r17_declaracion.py`,
      `tests/test_f011_r18_r19_ausente_o_rota.py`,
      `tests/test_f011_r20_r21_r22_puerta.py` (EjecutorGit falso; sin git
      real), y `python -m harness.rutas_sensibles --validar` exit 0.
- [ ] T9: sección 7 ter en `harness/init.sh` + bloque C4 ter en
      `CHECKPOINTS.md` + actualización de `evals/README.md`.
      | Verificación: `bash harness/init.sh` imprime la línea de la puerta
      ([OK] N/A con motivo en esta rama, que no toca rutas sensibles);
      borrar temporalmente `rutas_sensibles.json` en el árbol de trabajo y
      comprobar que la sección desaparece (R18), restaurar.
- [ ] T10: portar a `C:\Users\pgris\PycharmProjects\arnes-base`:
      `harness/rutas_sensibles.py`, `harness/rutas_sensibles.ejemplo.json`,
      sección 7 ter de su `init.sh`, párrafo genérico de su `CHECKPOINTS.md`
      y registro en su versionado. Commit local en arnes-base; SIN push.
      | Verificación: MANUAL (humano) — revisar el diff en arnes-base:
      `git -C C:/Users/pgris/PycharmProjects/arnes-base diff HEAD~1` y
      decidir el push.
- [ ] T11: corrida de humo del runner determinista y de la puerta con la
      declaración real.
      | Verificación: `python -m evals.runner --fases IA3,IA4 --feature F-011`
      exit 2 (NO_EVALUABLE: libros sin casos) e informe
      `progress/evals_F-011.md` escrito y coherente; salida pegada en
      `progress/impl_F-011.md`. Cuando el humano rellene los libros, la
      corrida real con casos es MANUAL (humano).
- [ ] T12: campaña de mutación y cierre.
      | Verificación: `python -m harness.mutacion --feature F-011` con
      supervivientes analizados en `progress/mutacion_F-011.md`.
- [ ] T13: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: exit 0, sin KO ni features rotas.
