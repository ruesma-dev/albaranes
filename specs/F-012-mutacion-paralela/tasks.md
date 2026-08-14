<!-- specs/F-012-mutacion-paralela/tasks.md -->
# F-012 · Campaña de mutación en paralelo — Tareas

Rama: `feature/F-012-mutacion-paralela`. Un commit por tarea
(`F-012 Tn: ...`). Fase RED obligatoria (rigor `estandar`): la traza del
fallo previo de los tests centrales va pegada en `progress/impl_F-012.md`.

- [x] **T1**: Reparto y agregación puros en `harness/mutacion_paralela.py`
      (`repartir` round-robin determinista, `fusionar` con reorden por clave
      estable y metadatos de muestreo del coordinador). Tests primero (RED).
      | Verificación: `python -m pytest tests/test_f012_r3_r4_reparto_agregacion.py -q`

- [x] **T2**: Gestor `Worktrees` (prune de arranque, `add --detach` en temp,
      limpieza garantizada en `__exit__` con fallback `prune + rmtree`) y
      guarda `arbol_limpio`. Tests sobre repos git temporales en `tmp_path`:
      éxito, excepción en vuelo, huérfanos de campañas muertas, árbol sucio.
      | Verificación: `python -m pytest tests/test_f012_r2_r9_r10_worktrees.py -q`

- [x] **T3**: Coordinador `ejecutar_campania_paralela` (hilos que reutilizan
      `ejecutar_campania` con `raiz=<worktree>` y `mutantes=<partición>`,
      eco con lock, cancelación cooperativa) + `resolver_interpretes` con
      fallo temprano por venv inexistente + parámetro `raiz_venvs` en
      `ejecutor_para` de `harness/mutacion.py`. Tests con ejecutores falsos
      que registran raiz/ejecutable; sin pytest real anidado.
      | Verificación: `python -m pytest tests/test_f012_r1_r5_r11_coordinador.py tests/test_f012_r6_timeout.py -q`

- [x] **T4**: CLI: `--workers` en `_analizar_argumentos`, helper
      `workers_mutacion` en `harness/rigor.py`, `$doc` de `rigor.json`,
      resolución del default (CLI > `mutacion.workers` >
      `min(max(1, núcleos − 2), 16)`), número
      efectivo `min(workers, mutantes)` y camino en serie intacto con
      efectivo ≤ 1.
      | Verificación: `python -m pytest tests/test_f012_r7_r8_cli.py -q`

- [ ] **T5**: Comparación serie-vs-paralelo sobre feature real (criterio de
      éxito). Comandos exactos, salidas reales en `progress/impl_F-012.md`:
      1. `python -m harness.mutacion --feature F-011 --workers 1 --max-mutantes 60 --semilla 20260813 --salida progress/tmp_mutacion_serie.md`
      2. `python -m harness.mutacion --feature F-011 --max-mutantes 60 --semilla 20260813 --salida progress/tmp_mutacion_paralelo.md`
      3. Diff de ambos informes ignorando SOLO la línea «Generado por…» y la
         fila «Tiempo total»: cero diferencias restantes; tiempos y speedup
         anotados. Borrar los `progress/tmp_mutacion_*.md` tras pegar la
         evidencia (no son informes de campaña oficiales).
      4. Campaña completa en paralelo: `python -m harness.mutacion --feature F-011`
         (sin `--workers`, default con tope: aquí 16), tiempo total frente a
         los 3.694 s históricos, totales contrastados con
         `progress/mutacion_F-011.md` a título informativo. Solo
         informativa: el criterio de éxito es el diff limpio del punto 3.
      | Verificación: diff limpio del punto 3 pegado en `progress/impl_F-012.md`

- [x] **T6**: Portar a arnes-base: copiar `mutacion.py`,
      `mutacion_paralela.py`, `rigor.py` y `rigor.json` a
      `C:\Users\pgris\PycharmProjects\arnes-base\arnes-base\harness\` y
      commit local allí (sin push).
      | Verificación: `git -C C:/Users/pgris/PycharmProjects/arnes-base status` limpio tras el commit y diff vacío entre ambos `harness/` para esos 4 ficheros

- [ ] **T7**: Campaña de mutación de la PROPIA F-012
      (`python -m harness.mutacion --feature F-012`) con supervivientes
      analizados en `progress/mutacion_F-012.md`, y sección «Evidencias»
      completa en `progress/impl_F-012.md`.
      | Verificación: existe `progress/mutacion_F-012.md` sin análisis `PENDIENTE`

- [ ] **T8**: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: `bash harness/init.sh` → exit 0
