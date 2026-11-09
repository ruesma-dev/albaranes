<!-- progress/review_F-112.md -->
Revisión completa (pasada 1) · `852fa93..88cbd3f` (commits del implementer `e14700b`…`88cbd3f`)

# F-112 · Review del reviewer

**Veredicto: APPROVED** (bloque de código T1–T8). Condición de cierre (`done`), no de esta review: T9–T14,
incluida la pasada de evals de T11 (`progress/evals_F-112.md`) o la renuncia escrita del humano (ver C4 ter).

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige fase RED en los requisitos centrales,
cobertura de líneas cambiadas ≥ 80 % y campaña de mutación muestreada con supervivientes analizados.

## Entorno y ejecución

`bash harness/init.sh` en el worktree con `ARNES_SIN_CACHE=1` y `PYTHONPATH` a la comun del worktree: **EXIT 0**.
Suites: raíz 2011 passed (431 s); sv1 236; sv2 586 (1 warning); 1608; 2562; 149; 706; 1186; 1492 + 2 skipped.
`PUERTA COBERTURA [OK] 99.8 %` (545/546). `PUERTA TAMAÑO [OK]`. `PUERTA RUTAS SENSIBLES [evals]` AVISO: 3 rutas
tocadas sin evidencia (`prompts.yaml`, `albaran_extraction_service.py`, `fecha_recepcion.py`). `git status`
limpio tras la ejecución. Nada contra Azure, BBDD, Blob, Sigrid ni LLM.

## Checkpoints

**C1** [x] init.sh EXIT 0 · [x] ficheros del arnés presentes.
**C2** [x] una sola `in_progress` (F-112) · [x] rama `feature/F-112-anio-fecha-albaran` · [x] `current.md` describe
la sesión activa (F-112 en curso; el resto son bloqueadas vivas) · [x] las `done` tienen su resumen (no cambia aquí).
**C3** [x] hexagonal: `fecha_recepcion.py` en `application/`, puro, `ContextoCorreo` solo bajo `TYPE_CHECKING`;
dominio e infraestructura sin tocar · [x] primera línea con ruta en todos los `.py` nuevos (los `.json` no admiten
comentario: N/A por formato) · [x] sin prints de debug (los `print` de `comparar_fecha.py`/`sinteticos_fecha.py` son
salida de CLI, como en `comparar_proveedor.py`), sin secretos, sin TODOs; dependencias: `tzdata` prevista (R30) y
Pillow prevista en design §7 (ver O3) · [x] trampas del monorepo: sin merge/raw, sin schema, sin importes: N/A por
alcance (solo prompt y fecha de referencia de sv2).
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] cada requisito con test trazable (tabla abajo), todos pasan · [x] tests sin red ni BBDD (cliente LLM
falso, extractor falso, `tmp_path`) · [x] MANUAL listadas con comando exacto en `tasks.md` T9–T13 y en
`impl_F-112.md` §6; `current.md` solo las nombra (ver O4).
**C4 bis**
- [x] rigor declarado `estandar`.
- [x] Fase RED: traza real en impl §4 para T1 (R1–R5), T2 (R6–R11), T3 (R12–R14), T4 (R15–R18), T5 (R25). En
  T6/T6b (comparador, sintéticos) la traza se obtuvo apartando el módulo (D-6): lo acepto, no son los requisitos
  centrales de producción y la fuerza de esos tests la mide la mutación.
- [x] Cobertura `[OK] 99.8 %`.
- [x] Mutación: `progress/mutacion_F-112.md` generado por la herramienta. **Recalculado por mí** con
  `harness.alcance.alcance_de_feature` + `harness.mutacion.generar_mutantes` (puro): origen `rama`
  `6c7707f..feature/F-112`, **1300 líneas y 236 mutantes**, fichero a fichero igual que el informe
  (comparar_fecha 866/199, sv2_fecha 122/5, sinteticos 131/22, pipeline 8/0, servicio 42/1, fecha_recepcion 122/9,
  worker 9/0).
- [x] Muertos: «Tiempo total» 4662,9 s > 60 s ⇒ **campaña no reejecutada** (≈ 78 min según el informe); vale el
  recálculo puro más RM1–RM6.
- [x] Coste por mutante = 4662,9 × 2 ÷ 20 = 466 s, muy por encima de 1 s.
- [x] Sin cabecera «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; la línea base consta (467 s / 470 s).
- [x] RM1: SHA medido `618c46c…`; HEAD `88cbd3f`. Los dos commits posteriores (`5c564bd`, `88cbd3f`) solo tocan
  `progress/` y `tasks.md`: el alcance medido es el revisado.
- [x] RM2: media 233,1 s × 2 workers = 466 s ≈ línea base 467–470 s; con 20/20 muertos y `-x` es coherente (sin
  salto de orden de magnitud). 20 × 233,1 = 4662 = Tiempo total.
- RM3: sin equivalentes declarados; nada que contradecir. RM4: no necesaria (sin veredicto dudoso).
- N/A RM5: rigor `estandar` (justificado por nivel).
- [x] RM6: ningún mutante se mató quitando código defensivo (0 supervivientes, sin cambios tras la campaña).
- N/A campaña manual: la automática dio 236 mutantes.
- [x] Supervivientes: ninguno; nada en `PENDIENTE`.
- [x] «Evidencias» con los cuatro números y workers = 2 (impl §5).
**C4 ter** [ ] → **AVISO, no bloquea esta review.** Faltan `progress/evals_F-112.md` para las 3 rutas tocadas.
Motivo escrito: la exigencia declarada es `aviso` (no `bloqueo`), y la pasada es T11, MANUAL de pago del humano,
programada después del código; no la ejecuto. Dictamen: **condición de cierre** de F-112: no puede pasar a `done`
sin `evals_F-112.md` posterior a `096e725` (último commit que toca una ruta sensible; `progress/evals_*.md` está en
`.gitignore`, así que la frescura se juzga por la fecha del informe frente a ese commit) o sin la renuncia del
humano escrita en `history.md`, como en F-117. Lo mismo para T10 (VEREDICTO VERDE del comparador).
**C5** [x] T1–T8 `[x]` con commit `F-112 Tn:` cada una; T9–T14 `[ ]` son MANUAL posteriores a la review o el init
final (N/A en esta pasada: `tasks.md` T8 dice «cierre del bloque de código, antes de la review»). El commit
`618c46c` lleva `F-112:` sin `Tn` (complemento de T5): aceptable, lo declara impl §3 D-3 · [x] sin temporales sin
trackear en el worktree · [x] `features.json` en `in_progress`, coherente.

## Cobertura requisito → test

| Req | Test(s) |
|---|---|
| R1 | `test_f112_r1_los_cuatro_ejemplos_de_madrid` (+ desfase, sin zona, fecha sola, tipo `date`) |
| R2 | `test_f112_r2_sin_fecha_valida_devuelve_none`, `_sin_contexto_`, `_un_valor_que_no_es_texto_no_lanza` |
| R3, R4 | `test_f112_r3_el_bloque_lleva_la_fecha_y_las_ordenes`, `_r3_la_regla_del_anio_…`, `_r4_sin_fecha_la_nota_fija` |
| R5 | `test_f112_r5_la_hora_no_llega_al_bloque`, `_r5_un_recibido_con_texto_anadido_no_mete_nada_en_el_prompt` |
| R6–R8 | `test_f112_r6_*` (2), `_r7_un_correo_con_el_literal_lo_conserva`, `_r8_sin_marcador_el_task_sale_identico`, `_r8_el_argumento_es_opcional` |
| R9 | `test_f112_r9_ia1_e_ia2_reciben_el_mismo_bloque`, `_r9_con_fecha_distinta_…`, `_r9_r15_ia1_recibe_el_bloque_del_yaml_real` |
| R10, R11 | `test_f112_r10_los_logs_dicen_la_fecha_o_no`, `test_f112_r11_la_fecha_de_la_ia_pasa_tal_cual` |
| R12–R14 | `test_f112_r12_*` (2), `_r13_la_misma_fecha_…`, `_r13_se_calcula_una_sola_vez`, `_r13_un_correo_sin_recibido_…`, `_r14_sin_correo_none_…` |
| R15, R16 | `test_f112_r15_el_marcador_va_una_vez_tras_la_regla_de_fecha`, `_r16_la_regla_de_fecha_dice_papel_y_recepcion` |
| R17 | `test_f112_r17_*` (YAML: sección propia, posición; código: bloque, nota, no se re-recorre, sin marcador) |
| R18 | `test_f112_r18_*` (bloque de revisión, nota, `{prompt_fase_1}`, ejemplo fijo, `revision_rules` sin regla) |
| R19–R24 | `tests/test_f112_comparar_fecha.py`: `_r19_*` (juegos A–D, banco B=20/C=13), `_r20_*`, `_r21_*`, `_r22_*` (C1–C7, NO APLICA), `_r23_*` (paradas, `--solo-validar`), `_r24_*` |
| R25 | `tests/test_f112_rutas_sensibles.py` (3) |
| R26 | lectura del reviewer: ARCHITECTURE regla 28, `sv2.md` §9, `evals/README.md` (ver D-1) |
| R27 | `tests/test_f112_sinteticos_fecha.py` (seis casos, mismos bytes, JPG, JSON versionado, Madrid) |
| R28 | `test_f112_r28_enero_y_cualquier_otra_fecha_dan_el_mismo_texto` |
| R29 | `test_f112_r29_tabla_del_efecto_de_ia2_y_lista_de_estropea` |
| R30 | `test_f112_r1_los_cuatro_ejemplos_de_madrid` (ZoneInfo, sin zona del sistema) + `_r30_tzdata_en_el_manifiesto_de_sv2` |

## Diseño y código (contra design.md)

Solo los ficheros de design §2–§3 más los tres tests viejos justificados. `_render_task_fase_1` sustituye
`{fecha_recepcion}` después de `{empresas_cliente}` y antes de `_render_contexto_correo` (R7), y solo si está el
marcador (R8). `{revision_fecha}` entra en `_MARCADORES_FASE_2` y en la pasada única (R17). El worker calcula la fecha
una vez y la pasa a las dos requests. `tzdata` está en el manifiesto que copia el Dockerfile de sv2. La variante
`base` del comparador usa el YAML de `dev` con el código de la rama: es válida porque, sin marcadores, el código no
añade nada (R8, probado).

## Juicio de las desviaciones (impl §3)

- **D-1 · regla 28 en vez de 26: aceptada.** La 26 y la 27 son de F-115 y F-111, que entraron después de la spec. El
  contenido es el de R26. El líder corrige el número en R26/T7 al cerrar (O1).
- **D-2 · ancla de `test_f064_prompt_ia1_proveedor.py`: aceptada.** R16 cambia la viñeta a propósito. El prefijo
  `- fecha: la del albarán` sigue siendo único en `prompts.yaml` (línea 65, comprobado) y ninguna aserción se relaja.
- **D-3 · ruta en `test_f011_r19_r20_declaracion.py`: aceptada.** Es la lista que fija las rutas declaradas, y F-064
  hizo lo mismo con `empresas_cliente.py`.
- **D-4 · sintéticos sin tildes: aceptada.** La fecha, que es el único dato variable, no cambia.
- **D-5 · R5 con texto basura ⇒ `None`: aceptada.** R2 (v1.3) manda que lo que no sea ISO válido dé `None`, y la
  propiedad de seguridad de R5 se cumple y está probada con inyección. El paréntesis de R5 («produce el mismo bloque
  que la fecha sola») viene de la v1.0 y contradice R2: hay que retocar la spec (O2).
- **D-6 · RED de T6/T6b obtenida apartando el módulo: aceptada** (ver C4 bis).

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- O1. `specs/F-112-anio-fecha-albaran/requirements.md:130` y `tasks.md` T7 dicen «regla 26»: pasar a 28.
- O2. `requirements.md:44-45`: el paréntesis de R5 contradice R2. Proponer «un `recibido_utc` con hora produce el
  mismo bloque que la fecha sola; uno con texto añadido no es ISO válido y da la Nota sin recepción».
- O3. Pillow (para `evals/sinteticos_fecha.py`) no está declarado en ningún manifiesto: llega al `.venv` de la raíz
  como dependencia transitiva de reportlab y pdfplumber. Si un día cae, T10 no generará el juego D.
- O4. `progress/current.md` debería copiar los comandos exactos de T9–T13 (están en `tasks.md` e impl §6).
- O5. `fecha_recepcion_de` con 10 caracteres admite también una fecha ISO de semana (`2026-W44-3`). Es inocuo: Graph
  nunca la envía.

## Automejora (propuesta, no aplicada)

C4 ter pide que el informe de evals sea «FRESCO: su commit pertenece a la rama», pero en este repositorio
`progress/evals_*.md` está en `.gitignore` y no tiene commit. Propongo que `CHECKPOINTS.md` diga, para ese caso, que
la frescura se compara por la fecha-hora que imprime el informe frente al último commit que tocó una ruta sensible.
