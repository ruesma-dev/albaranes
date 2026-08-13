<!-- specs/F-011-evals-ia/tasks.md -->
# F-011 · Evals de IA con ground truth y puerta en el arnés — Tareas

Rama: `feature/F-011-evals-ia`. Un commit por tarea (`F-011 Tn: ...`).
Rigor `estandar`: fase RED con traza real en los requisitos centrales
(R2, R4, R7, R13, R20–R25), cobertura de líneas cambiadas y campaña de
mutación. Las preguntas abiertas están resueltas (Decisiones D1–D7 en
`requirements.md`, 2026-08-13): no hay nada pendiente del humano para
empezar.

- [x] T1: `evals/requirements.txt` + instalación en el venv raíz, y
      `evals/modelos.py` + `evals/barrido.py` (patrones C3 bis; precios,
      razones sociales y CIF fuera del barrido por D1).
      | Verificación: `tests/test_f011_r4_barrido.py` en RED y luego verde
      (correo, IP, GUID, token detectados; texto limpio con precios y CIF
      pasa).
- [x] T2: `evals/criticidad.json` + `evals/criticidad.py` (clasificación por
      defecto crítico/laxo, ajuste por campo, campo sin clasificar =
      crítico con aviso).
      | Verificación: `tests/test_f011_r7_r8_criticidad.py`.
- [x] T3: `evals/conversor.py`: los 6 libros (incluido `RESULTADO_FINAL` →
      `fixtures/final/`), localización de tablas, convenios de celda
      (incluido el literal `REVISIÓN`), salida determinista, fallos por
      libro/pestaña ausente y aborto por barrido sin escritura parcial.
      | Verificación: `tests/test_f011_r1_r2_r3_conversor.py`,
      `tests/test_f011_r5_determinismo.py`, `tests/test_f011_r6_ausencias.py`
      (libros sintéticos construidos con openpyxl en el propio test).
- [x] T4: ejecutar el conversor real sobre los 6 libros y versionar
      `evals/fixtures/` (hoy sin casos: estructura + metadatos).
      | Verificación: `python -m evals.conversor` exit 0; `git status`
      muestra solo JSON bajo `evals/fixtures/`; ningún xlsx en el commit.
- [x] T5: `evals/comparador.py` (convenios R2 + criticidad + sentinela
      `ESPERA_REVISION`) + `evals/informe.py` (render, `parsear_veredicto`,
      `es_pasada_completa`).
      | Verificación: `tests/test_f011_r2_comparador.py`,
      `tests/test_f011_r15_informe.py`.
- [x] T6: `evals/procesos/sv6_build.py`: modo determinista (envelope
      estimulado con prohibidas inyectadas, redes reales de sv6, stubs de
      IA y repositorio, ejecución secuencial) y comparación extremo-a-extremo
      determinista contra `fixtures/final/`.
      | Verificación: `tests/test_f011_r13_determinista.py` (asserta además
      cero llamadas de red con clientes-trampa) y
      `tests/test_f011_r17_secuencial.py`.
- [x] T7: `evals/procesos/sv2_extraccion.py` (composición mínima sv2,
      proveedor primario por defecto y `--proveedores` — D3) y
      `evals/procesos/sv5_valoracion.py` (contexto desde fixtures, IA3+IA4
      reales, emisión del envelope para el extremo-a-extremo); fallo
      temprano sin claves LLM.
      | Verificación: `tests/test_f011_r11_ia12.py`,
      `tests/test_f011_r14_e2e_real.py` (clientes LLM falsos inyectados,
      hand-off de envelope verificado), `tests/test_f011_r12_omitidos.py`.
- [x] T8: `evals/runner.py`: CLI de las dos corridas (pasada completa con
      `--con-llm`, determinista por defecto; rechazo de IA1/IA2 sin
      `--con-llm`), subprocesos por servicio, agregación, informe en
      `progress/`, exit codes y NO_EVALUABLE sin casos.
      | Verificación: `tests/test_f011_r9_r10_cli.py`,
      `tests/test_f011_r16_exit_codes.py`,
      `tests/test_f011_r18_sin_casos.py`.
- [ ] T9: `harness/rutas_sensibles.py` (genérico) +
      `harness/rutas_sensibles.json` (declaración de albaranes, exigencia
      `aviso` — D5, sin campo de fases — D2).
      | Verificación: `tests/test_f011_r19_r20_declaracion.py`,
      `tests/test_f011_r21_r22_ausente_o_rota.py`,
      `tests/test_f011_r23_r24_r25_puerta.py` (EjecutorGit falso; sin git
      real), y `python -m harness.rutas_sensibles --validar` exit 0.
- [ ] T10: sección 7 ter en `harness/init.sh` + bloque C4 ter en
      `CHECKPOINTS.md` + actualización de `evals/README.md` (6º libro,
      dos corridas, criticidad).
      | Verificación: `bash harness/init.sh` imprime la línea de la puerta
      ([OK] N/A con motivo en esta rama, que no toca rutas sensibles);
      borrar temporalmente `rutas_sensibles.json` en el árbol de trabajo y
      comprobar que la sección desaparece (R21), restaurar.
- [ ] T11: portar a `C:\Users\pgris\PycharmProjects\arnes-base`:
      `harness/rutas_sensibles.py`, `harness/rutas_sensibles.ejemplo.json`,
      sección 7 ter de su `init.sh`, párrafo genérico de su `CHECKPOINTS.md`
      y registro en su versionado. Commit local en arnes-base; SIN push.
      | Verificación: MANUAL (humano) — revisar el diff en arnes-base:
      `git -C C:/Users/pgris/PycharmProjects/arnes-base diff HEAD~1` y
      decidir el push.
- [ ] T12: corrida de humo del runner determinista y de la puerta con la
      declaración real.
      | Verificación: `python -m evals.runner --feature F-011` exit 2
      (NO_EVALUABLE: libros sin casos) e informe `progress/evals_F-011.md`
      escrito y coherente; salida pegada en `progress/impl_F-011.md`.
      Cuando el humano rellene los libros, la pasada completa
      (`python -m evals.runner --con-llm --feature F-XXX`) es
      MANUAL (humano): cuesta llamadas LLM.
- [ ] T13: campaña de mutación y cierre.
      | Verificación: `python -m harness.mutacion --feature F-011` con
      supervivientes analizados en `progress/mutacion_F-011.md`.
- [ ] T14: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: exit 0, sin KO ni features rotas.
