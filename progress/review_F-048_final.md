<!-- progress/review_F-048_final.md -->
Pasada 2 (al final): revisión incremental desde 88085cb hasta 4d94ba2. Pasada 1 (compactada): revisión completa de 1807e83..63571a6

# F-048 · Review final

## Pasada 1 (2026-09-24, `1807e83..63571a6`) · CHANGES_REQUESTED, solo papeleo · compactada

- Código, tests y primera campaña, bien. Tres arreglos de papeleo, ya hechos por el líder: `current.md` con lo
  pendiente, el comando `-Only sv3 → sv2 → sv1` (`ARCHITECTURE.md`, `azure-apps`) y T37 sin el falso rojo.
- `init.sh` exit 0, raíz `865 passed`, cobertura 99,5 %; a mano comun 274, sv1 98, sv2 374, sv3 233, sv4 247.
- Primera campaña (`e7fe2c0`, 175 mutantes): recalculada, RM1–RM6 [x], 3 huecos reinyectados, y los equivalentes 9,
  22 y 23 demostrados y aceptados. Extremo a extremo sin desajustes. sv2 antes que sv3 manda todo a poison.

## Pasada 2 (2026-09-25, `88085cb..4d94ba2`) · rigor `critico`

**Veredicto: CHANGES_REQUESTED**, solo papeleo. El código, los tests, la segunda campaña y la trazabilidad están
**listos**. Faltan dos arreglos de texto: `current.md` da por pendientes decisiones que el humano ya tomó y T40 no
refleja la decisión (a). Hechos esos dos, solo queda G y el veredicto pasa a `APPROVED_PENDIENTE_HUMANO`.
**Rigor** `critico` (declarado): RED, cobertura ≥ 80 %, 0 supervivientes sin justificación aceptada, RM1–RM6, MANUAL.

### Decisiones del humano (2026-09-24), que no cuento como defecto

- **(a) T40**: la puerta de rutas sensibles pide `VEREDICTO: VERDE`. **Queda sustituido por aceptación explícita del
  humano** de dos evidencias. La primera, la pasada `completa` SIN correo (`progress/evals_F-048.md`, ignorado por git,
  `fac6b10`, ROJO por defectos previos del banco). La segunda, el comparador de obra
  (`progress/comparar_obra_F-048.md`: 7 idénticos, 1 difiere, 2 inestables, 0 con errores; `analisis_evals_F-048.md` §6:
  la rama deduce la obra donde `dev` daba null y no empeora ningún caso). Dos notas: esa pasada es anterior a CR-E2, pero
  sus 2 omitidos son «no existe el fichero», que siguen siendo OMITIDO, así que el veredicto no cambia. La parte CON
  correo de T40 queda sin medir: la cubren T37–T39, que son manuales.
- **(b)** Los 3 equivalentes (9, 22, 23 = 78, 79, 80 de la segunda campaña): aceptados.
- **(c)** De F-047 solo `evals/inyeccion.py`. Los 6 de `GestoRevisor` (43, 44, 46–49) se justifican en bloque como código de F-047.

### Qué ejecuté (resultados reales)

- `bash harness/init.sh`: **exit 0, ENTORNO LISTO**. Raíz `1064 passed in 152.23s`. `PUERTA COBERTURA 98.3 %`
  (1369/1393). `TAMAÑO` OK (impl 220/220). `[AVISO] RUTAS SENSIBLES`: 11 rutas y sin `VEREDICTO: VERDE`, que cubre la
  decisión (a). Los 7 servicios salen de caché, y es válido: `git diff 88085cb..HEAD -- services/` está vacío.
- `git diff 14cee8a..HEAD --stat -- services/ evals/ ':!**/tests/**'` **vacío** (RM1). Worktrees del scratchpad
  (`wt_rev` en HEAD, `wt_14c` en `14cee8a`) retirados; `git status` limpio.

### Bloqueantes y menores de la review del bloque E

| Punto | Cierre | Comprobación propia |
|---|---|---|
| B1 `loc` con clave del LLM | `fc91569` `_ubicacion` + 5 tests `cr_e1` | RED: vuelvo a `str(parte)` → **4 failed, 1 passed**, igual que el informe (`...extra_forbidden en CENTINELA-VALOR-DEL-ALBARAN-7731`). Residuo aceptado: una clave de `dict` en minúsculas pasa |
| B2 ERROR escondido como OMITIDO | `a3c870a` estado `ERROR` + 12 tests `cr_e2` | RED: vuelvo a `if not self.evaluados:` → **3 failed, 9 passed**: `'VERDE' == 'NO_EVALUABLE'` ×2 y `assert 0 == 2` (`runner.main` con un caso roto). Los `omitido(` que quedan en `runner.py` son solo «no existe el fichero» (:271-272) y «sin caso en el libro» |
| B3 campaña sin `evals/` | 2.ª campaña, `14cee8a` | Sección siguiente |
| B4 cableado para F-047 | `6558755` | `current.md` («Aparcada: F-047») y `specs/F-047-…/tasks.md` «Nota de integración desde F-048» |
| Menores 1–3 | `e00bc41` · `1ec5853` · `fc3ee60` | `.eml`/`.msg` y firma de Graph con test (6); `sort_keys` fuera; aviso en el README. Los menores 4 y 5 quedan fuera, y no bloquean |

### Segunda campaña (T34) · RM1–RM6

- **Recálculo puro** (`alcance_de_feature` + `generar_mutantes`): **45 ficheros, 3.771 líneas, 410 mutantes**
  (235 de `evals/` y 175 de `services/`), igual que el informe. **Los 80 supervivientes existen** con su fichero,
  línea, operador y texto original→mutado: 0 discrepancias. Las cuentas cuadran: services 175 − 3 = 172 y
  evals 235 − 77 = 158, que suman los 330 muertos.
- Ni «⚠ CAMPAÑA NO VÁLIDA» ni base rota, y la línea base se corrió (filas por suite). **0 `PENDIENTE`**.
- **Tiempo total 21.051,1 s > 60 s ⇒ campaña no reejecutada** (5,8 h según el informe). Aplico el recálculo, RM1–RM6 y
  la reinyección. Coste por mutante: 21.051,1 × 2 / 410 = **102,7 s**.
- **RM1** [x] Medido `14cee8ac07a4…` y sin producción ni `evals/` cambiados desde entonces.
- **RM2** [x] La media de 51,3 s es de reloj: 51,3 × 410 ≈ 21.033 ≈ total. Con los 2 workers da 102,7 s, frente a
  líneas base de raíz de 521–534 s (las dos medidas a la vez; sola tarda 152 s), comun de 156–159 s y de 15 a 26 s el
  resto. Con `-x`, los muertos cortan antes. Mis 4 muertos de raíz tardaron 71–78 s: no hay salto de orden de magnitud.
- **Muertos comprobados** (RM4, en `wt_14c` y con los tests de `14cee8a`, raíz `-x`). Cuatro muertos de `evals/`
  elegidos al azar con semilla 20260925, y los cuatro mueren (1 failed cada uno): `informe.py:203` (`== ROJO` → `!=`) ·
  `comparar_obra.py:315` (`*` → `//`) · `sv2_obra.py:85` (`!= 0` → `== 0`) · `comparar_obra.py:314` (`+` → `-`).
- **RM3** [x] Revisé los 158 muertos de `evals/` uno por uno y ninguno es equivalente. Los dudosos no lo son:
  `__name__ != "__main__"` ejecuta `main` al importar, y `capture_output=False` deja `stdout=None`. Los 172 de
  `services/` son los 175 de la primera campaña, ya revisados y con el código sin cambios.
- **RM4** [x] Reinyecto 4 huecos cerrados sobre HEAD, con `46 passed` sin mutante. **#35** `correos.py:139`
  (`check=False`): 1 failed, `DID NOT RAISE CalledProcessError`. **#77** `runner.py:210` (`or` → `and`): 2 failed.
  **#45** `inyeccion.py:357`: 1 failed. **#53** `errores.py:80` (`include_input=True`): 1 failed. Los cuatro coinciden
  con el informe.
- **RM5** [x] 78–80 = 9, 22 y 23: `git diff e7fe2c0 HEAD` de `capturar_correo.py` y `mail_client.py` sale vacío, y
  `pytest tests/test_f048_t34_supervivientes.py -k "guarda or demostracion"` (sv1) da `10 passed`. Aceptados, (b).
- **RM6** [x] No se quitó ninguna guarda: después de `14cee8a` solo hay tests, y CR-E1 a CR-E3 añaden defensas.
- **`GestoRevisor`** [x] `class GestoRevisor` está en `inyeccion.py:324`, y el fichero tiene 401 líneas. Los 6 caen en
  :349, 350, 374, 386, 393 y 400, **dentro de 324–401**. La clase es idéntica byte a byte a la de
  `feature/F-047-evals-ciclo-completo` (`1d34afb`) desde `class GestoRevisor` hasta el final. El 45 (:357) NO lo mata
  el test de F-047: se cierra aquí con un test propio, reinyectado arriba. Decisión (c).
- **Sin justificar: 0** (71 con test + 6 de F-047 + 3 equivalentes = 80).

### Checkpoints (pasada 2)

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés. **C3 bis** N/A: no se toca `docs/referencia/`.
- **C2** [x] una sola `in_progress` · [x] rama correcta · N/A `history.md` (F-048 aún no pasa a `done`) ·
  **[ ] `current.md`**: el bloque de F-048 describe un estado que ya pasó (cambio 1).
- **C3** [x] Hexagonal: `evals/` está fuera de los servicios. [x] Primera línea con la ruta en los ficheros tocados.
  [x] Sin prints de depuración. [x] Sin secretos ni dependencias nuevas. [x] R31: el motivo sale sin la clave del
  LLM (B1).
- **C4** [x] Las 44 R tienen test en verde o son MANUAL (tabla). [x] Sin red ni BBDD: el escáner de R38 solo usa
  git local. [x] Los MANUAL T36–T39 y T41 están en `current.md` con su comando.
- **C4 bis** [x] Rigor declarado. [x] RED pegado y reproducido (CR-E1, CR-E2). [x] Cobertura 98,3 %. [x] Mutación
  recalculada y muertos muestreados. [x] Ni campaña no válida ni base rota. [x] RM1, RM2, RM5 y RM6. [x] 0 sin
  justificar, con aceptación del humano (b, c). [x] Evidencias en `impl_F-048.md` («Bloque E · cambios…») y en
  `impl_F-048_T34b_supervivientes.md` §5, con los workers.
- **C4 ter**: AVISO con motivo, cubierto por la decisión (a).
- **C5** [x] Los CR con commits `F-048 CR-En:` y T34 con `F-048 T34:` · [x] árbol limpio ·
  **[ ] T40 en `tasks.md:74` sigue `[ ]`** y no cita la decisión (cambio 2). Quedan T36–T39 y T41, a propósito.

### Trazabilidad final (las 44 R)

| R | Cobertura |
|---|---|
| R1 · R8–R9 · R13 · R24 · R37 | comun `r1_contexto`, `r8_r9_mensaje`, `r13_prompt`, `r24_origen_datos`, `r37_llm_logger`, `t34_*` |
| R2–R7 · R10 · R36 · R39 | sv1 `r2_r4_graph`, `r3_r5_pipeline`, `r6_*`, `r7_r10_intake`, `r36_logs`, `r39_captura`, `t34_*` (R36 también en sv2 y comun) |
| R11–R25 · R42 | sv2 `r11_worker`, `r12_render_fase1`, `r14_*`, `r15_schema`, `r16_prompt_yaml`, `r18_*`, `r19_r22_tabla_d5`, `r23_r25_sellado`, `r24_lectura_tolerante`, `r42_encolar` |
| R26–R31 · R32–R35 | sv3 `r26_modelo`, `r27_merge`, `r28_red_obra`, `r29_r31_motivos_revision` · sv4 `r32_r34_vista_avisos`, `r35_vista_modelo` |
| R38 | raíz `test_f048_evals_correos.py::r38_*` + `cr_e3_*` · sv1 `r39_captura` (`git check-ignore`) |
| R40 · R41 | raíz `test_f048_r40_r41_inyeccion.py` + `test_f048_evals_correos.py::r40_*` (`-k "f048 and (r38 or r40 or r41 or inyeccion)"`: **52 passed**) |
| R43 | **MANUAL** T36–T39 (bloque G) |
| R44 | RED + `PUERTA COBERTURA` 98,3 % + T34, dos campañas |

### Cambios requeridos

1. **`progress/current.md:10-60`** (bloque de F-048). Escribir las decisiones del humano del 2026-09-24, (a), (b) y (c)
   de arriba. Retirar lo que ya no es verdad: «Falta la parte CON correo … y que el humano acepte» (:23-25), «(a)
   Bloque E bloqueado por F-047 … Decidir» (:29-31), «Comparador … sin lanzar» (:49), «Pendiente: aceptar en bloque
   los 6» (:55) y «review incremental desde `63571a6`» (:57). Debe quedar: E y 2.ª campaña cerradas, **solo G pendiente**.
2. **`specs/F-048-correo-contexto-ia1/tasks.md:74` (T40)**: marcarla `[x]` y citar la decisión (a) del
   2026-09-24 y las dos evidencias (`progress/evals_F-048.md` a `fac6b10` y `progress/comparar_obra_F-048.md`).

### Qué falta después: bloque G, todo del humano (comandos de `tasks.md:70-75`)

- **T36** (Graph, solo lectura), ×3 (directo, `RE:`, `RV:`): `cd services\albaranes-email; .\.venv\Scripts\python.exe
  capturar_correo.py --message-id <ID> --caso <CASO>`, y abrir `evals\inputs\correos\<CASO>.json`.
- **T37**: `infra\local\arrancar_local.ps1 -SinSv1`; `cd services\albaranes-api; .\.venv\Scripts\python.exe seed_input.py <DOC_ID>
  "<pdf>"`; `.\.venv\Scripts\python.exe encolar_extraccion.py <DOC_ID> --correo ..\..\evals\inputs\correos\<CASO>.json`; el SHA con
  `Get-FileHash`, y el `psql … SELECT` de `tasks.md:71` + ficha en `:8004` + `Select-String` de una frase que no sea la evidencia.
- **T38**: «Volver a buscar» en `http://localhost:8004` sobre el documento de T37 y el mismo SELECT: el motivo tiene que salir UNA vez.
- **T39**: dar de baja lógica el de T37 y reinyectar el mismo PDF SIN `--correo` con `<DOC_ID2>`. El mismo SELECT debe dar `motivo='sin_correo'`.
- **T41**: `bash harness/init.sh`. Después viene la review de G, incremental desde el HEAD que la preceda, y el despliegue
  `.\deploy.ps1 -Only sv3` → `check_deploy.ps1` → `-Only sv2` → `-Only sv1`.

### Automejora (propuesta, no aplicada)

- **RM2 (`reviewer.md`, `CHECKPOINTS.md`, `arnes-base`)**: la «Media por mutante» es de reloj (total ÷ mutantes).
  51,3 s frente a la base de raíz de 534 s queda bajo la décima parte: al pie de la letra, RM2 rechazaría una campaña
  sana. Que compare el **coste por mutante** (media × workers) con la base **de la suite que corre cada mutante**.
- **`reviewer.md`**: si el humano sustituye una puerta (C4 ter) por una aceptación, exigirla escrita en `current.md` y en la tarea.
