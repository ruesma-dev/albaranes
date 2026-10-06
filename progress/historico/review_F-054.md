<!-- progress/review_F-054.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (merge-base `ddc3847` = `dev`), HEAD `243c68c`

# F-054 · Review de cierre — sv1 ingiere los PDF e imágenes de correos adjuntos encadenados

**Veredicto: APPROVED, condicionado al papeleo de cierre del líder (abajo).** Código, tests, RED, cobertura y
campaña están bien; no pido cambios de código. Única pega: `progress/current.md` arrastra dos líneas de antes de la
implementación que contradicen el estado (C2); se arreglan en el papeleo de cierre, como en F-048 y F-052.

**Rigor:** `estandar` (declarado en `features.json`). Exige RED en los centrales, cobertura ≥ 80 % de lo cambiado
y campaña muestreada (20, semilla `20260820`) con supervivientes analizados; sin cero obligatorio ni RM5.

## Qué ejecuté (resultados reales, 2026-10-02)

- `bash harness/init.sh`: **exit 0, ENTORNO LISTO**. Raíz `1067 passed in 260.51s`. `PUERTA COBERTURA: 100.0 %`
  (184/184). `RUTAS SENSIBLES`: N/A (impreso: no toca ninguna). `TAMAÑO` OK (req 150/150, design 246/250, impl
  156/220). Avisos previos y ajenos: ruff 1167 (+1 `BLE001`, el `except Exception` de la descarga del correo
  adjunto, gemelo del de directos), `infra` sin tests, `[ADAPTAR]` de F-034/F-035.
- sv1 salió de caché en `init.sh`; la relancé sin caché: `205 passed in 8.72s` (`-k f054`: 107 passed).
- RM4 sobre una COPIA de sv1 en el scratchpad (árbol real intacto, `git status` limpio): ver «Campaña».

## Alcance y diseño

- Solo `services/albaranes-email/` + párrafo de la regla 9 de `docs/ARCHITECTURE.md` (10 líneas, fiel a design §7,
  DH3, DH5) + papeleo (`features.json`, `BACKLOG.md`, `progress/`, `specs/`). Nada de `ruesma_comun`, sv2–sv6,
  `infra/`, `evals/`, colas ni blob de F-048. `azure-apps/albaranes.md` no cambia (mismos endpoints, permisos,
  colas y blobs): correcto.
- Hexagonal: modelos y puerto (`Protocol` + `CorreoAdjuntoIlegible`) en `domain/` sin imports de infra; extractor
  en `infrastructure/document/` solo con stdlib + dominio (R12, test por `ast`); el pipeline importa solo el
  puerto y `main.py` inyecta `MimeDocumentoExtractor()` como argumento obligatorio (R27, 3 tests).
- **No regresión de directos**: `_is_eligible` intacto; R3 (tabla de 13 tipos) y R16 (dict literal del `meta`,
  PDF, imagen y multipágina) escritos en verde contra el pipeline sin tocar (T5) y siguen verdes; los 98 tests de
  F-048 pasan sin cambiar aserciones (solo reciben `extractor_correo=`). `correlation_key` sigue
  `email:{msg.id}:{sha página}` para directos e interiores (R13, R19 con duplicado = aceptada).
- **Extractor**: recursión propia con nivel; tope `nivel + 1 > 5` ⇒ `tope_excedido` y el pipeline no ingiere
  nada del correo adjunto (R9 todo-o-nada probado con PDF/PNG en niveles bajos); PDF por tipo o `.pdf`, imagen
  solo `image/*` + `attachment` (DA8); sin bytes ⇒ ignorada; nombre base o `documento_<n>.<ext>` (R10).
  Límite `MAX_ATTACHMENT_MB` por documento interior con WARNING (R14, incluido «justo en el límite entra»).
- **Destino R21**: `Procesados` sii todos los `_ResultadoAdjunto.ok` y ≥ 1 página aceptada; 9 escenarios
  parametrizados (descarga, ilegible, tope, troceo, intake falla/rechaza, sin página, directo falla). Mixto en
  orden de Graph (R20). Contexto F-048 del exterior, pedido una vez (R17/R18); `ContextoCorreo` sin cambios.
- **Logs (R25/DA6)**: el `name` de Graph del correo adjunto no se loguea en ninguna rama (`_es_correo_adjunto` y
  `_process_correo_adjunto` solo id/tipo/tamaño); fallo de descarga solo con el tipo de la excepción; el
  extractor no lee cabeceras del interior (test). Test con centinela en `name`, cabeceras, cuerpo y nombre del
  `.eml` anidado, a DEBUG, en 8 ramas incluidas las de error; R36 de F-048 sigue verde.
- Desviaciones del implementer (`_ingerir` con `att_id`, `_submit_page_to_orchestrator` sin `attachment`, log de
  R23 que conserva «sin adjuntos elegibles»): menores, justificadas y anotadas. Aceptadas.

## Checkpoints

- **C1** [x] `init.sh` exit 0. [x] Ficheros base existen.
- **C2** [x] Una sola `in_progress` (F-054). [x] Rama `feature/F-054-correo-adjunto-encadenado`.
  [x] `current.md`: la sección F-054 y la MANUAL están bien, **pero** «LO PRIMERO…» aún dice «Ninguna feature
  `in_progress`» y «F-054 `spec_ready`… 4 decisiones DA por confirmar», y la línea «F-051, F-053 y F-054 viven en
  sus ramas» ya no vale para F-054. Lo marco [x] **solo** porque el cierre lo reescribe: condición 1.
  [x] Toda `done` con resumen en `history.md` (F-054 aún no es `done`: condición 2).
- **C3** [x] Hexagonal. [x] Primera línea con ruta en los 14 ficheros de código tocados. [x] Sin `print`, TODO,
  secretos ni dependencias nuevas (stdlib `email`; `pypdf` ya estaba). [x] Reglas de ARCHITECTURE: las tres
  trampas (merge/raw, schema, unidades) no aplican (sv1 no toca BBDD ni importes); regla 9 respetada.
- **C3 bis** N/A: no añade ni toca nada en `docs/referencia/`. Barrido igualmente sobre los `.md` y tests nuevos
  (`[A-Za-z0-9._%+-]+@…`, ids Graph `AAMk|AQMk`, GUID, IPs, `password|secret|AccountKey|sig=`): solo `@ejemplo.test`.
- **C4** [x] R1–R25 y R27 con ≥ 1 test `test_f054_rN_*` en verde; **R26** sin test por diseño (design §8: «lo
  verifica el reviewer leyendo los tests»): verificado, todo en memoria (`eml_sinteticos.py`), `@ejemplo.test`,
  textos inventados, sin red ni BBDD. [x] Unit tests sin red ni BBDD (dobles de buzón e intake).
  [x] MANUAL T12 en `current.md` con comandos exactos (`.\deploy.ps1 -Only sv1`, `.\check_deploy.ps1`), la línea
  de log a buscar y el criterio; no bloquea el `done` (tasks.md lo dice).
- **C4 bis** [x] `rigor: estandar` declarado. [x] **RED** real pegada para R7 y R9 (`ModuleNotFoundError`, T3) y
  R1, R15, R21, R25 (aserciones fallidas con pipeline sin tocar, T6), más totales en rojo; R3/R16 verdes a
  propósito como no-regresión. [x] **Cobertura** `[OK]` 100 %. [x] **Mutación** con informe de la herramienta,
  recalculado (abajo). [x] Muertos comprobados: campaña de 142,8 s > 60 s ⇒ **no reejecutada entera**; recálculo
  puro + RM1–RM6 + RM4 sobre copia. [x] Coste por mutante 142,8 × 4 ÷ 20 = 28,6 s (> 1 s, ≥ base). [x] Sin
  «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea base medida en los 4 worktrees. [x] RM1.
  [x] RM2. N/A RM5 por nivel `estandar` (basta justificación escrita). [x] RM6: no se quitó código defensivo (los
  dos huecos se mataron añadiendo tests). N/A campaña manual: fue automática con 77 mutantes. [x] Superviviente
  analizado, ninguno `PENDIENTE`. [x] «Evidencias» con los cuatro números y workers (4). [x] Ningún N/A sin motivo.
- **C4 ter** N/A: la puerta imprime que F-054 no toca rutas sensibles declaradas.
- **C5** [x] `tasks.md` T1–T11 y T13 `[x]`, T12 MANUAL posterior al cierre (abierta a propósito); commits
  `F-054 Tn:` por tarea (T10 en 3, más 2 de papeleo/ruff sin `Tn`, aceptable). [x] Árbol limpio, sin temporales.
  [x] `features.json` = `in_progress` mientras se revisa (pasa a `done` en el cierre).

## Campaña de mutación · RM1–RM6

- **Recálculo independiente** (`alcance_de_feature` + `generar_mutantes`, cálculo puro): en `3fb2bb8`, 6 ficheros,
  **538 líneas, 77 mutantes**, y el sorteo `random.Random(20260820).sample(·, 20)` da los **mismos 20** del
  informe. En HEAD: 537 líneas (una en blanco menos), 77 mutantes, los mismos 20 con la línea desplazada. El
  superviviente existe tal cual: `mime_documento_extractor.py:155` [entero] `split("/", 1)` → `split("/", 2)`.
- **RM1** [x] SHA `3fb2bb8fd649…`. De ahí a HEAD en producción solo cambia `polling_pipeline.py` quitando una línea
  en blanco entre imports (commit de ruff); en tests, orden de imports, un `noqa` y una variable. No invalida nada.
- **RM2** [x] Workers 4; media 7,1 s × 4 = 28,4 s frente a bases 23,3–23,8 s: coherente (sin salto de orden de
  magnitud; algo por encima de la base, lógico con 4 suites compitiendo).
- **RM3** [x] El equivalente salió vivo, no muerto. Ninguno de los 19 muertos que repasé es equivalente.
- **RM4** [x] Sobre la copia: `:96` `>` → `>=` (tope) **2 fallos**; pipeline `:437` `==` → `!=` (recuento de PDF)
  **1 fallo**; extractor `:138` `+= 1` → `+= 2` **8 fallos**; el equivalente `:155` **0 fallos** (185 passed).
- **Equivalente, ¿aceptable?** Sí, y sin aceptación humana (nivel `estandar`). Lo comprobé además: con
  `email.policy.default`, `image/png/x`, `image//png` caen a `text/plain`; `image/` da `image/` (ambos split →
  `''`). Ese código solo se alcanza con maintype `image`, así que nunca hay dos barras.
- **Muestreo 20 de 77** (26 %): es lo que fija `rigor.json` para `estandar`; el sorteo cubre clasificación,
  destino, tope, PDF/imagen, nombres y recuento. Los dos huecos reales de la primera pasada se mataron con tests
  nuevos, reverificados por el implementer. Suficiente para el rigor declarado.

## Cobertura · requisito → test (todos en `services/albaranes-email/tests/`)

| Req | Test(s) | Req | Test(s) |
|---|---|---|---|
| R1 | `test_f054_r1_message_rfc822_no_inline_…[*]`, `…_un_eml_como_file_attachment…` | R14 | `…_r14_…excede…`, `…_justo_en_el_limite_entra`, `…_si_todos_exceden…` |
| R2 | `test_f054_r2_*` (3, incl. `sin_limite_configurado`) | R15 | `…_r15_meta_de_*` (PDF e imagen) |
| R3 | `…_r3_adjuntos_directos_con_la_regla_de_hoy` (13 casos) | R16 | `…_r16_*` (4) |
| R4 | `…_r4_*` | R17/R18 | `…_r17_r18_…`, `…_r18_*` (3) |
| R5 | `…_r5_*` | R19 | `…_r19_el_mismo_fichero…duplicado_no_fallo` |
| R6 | `…_r6_*` (2) | R20 | `…_r20_mixto_en_el_orden…` |
| R7 | `…_r7_*` (7: PDF tipo/nombre, PNG/JPEG attachment, inline y sin disposición fuera) | R21 | `…_r21_procesados_si_y_solo_si…[9]`, `…_r9_r21_…`, `…_log_final…` |
| R8 | `…_r8_*` (3) | R22 | `…_r22_*` (2) |
| R9 | `…_r9_*` (5 + `r9_r21`) | R23 | `…_r23_*` |
| R10 | `…_r10_*` (4) | R24 | `…_r24_*` |
| R11 | `…_r11_*` (3) | R25 | `…_r25_ningun_log…[8 ramas]`, `…_r25_el_exito_registra…` |
| R12 | `…_r12_*` (2, `ast`) | R26 | revisión del reviewer (design §8): OK |
| R13 | `…_r13_*` (3: multipágina, solo imágenes ⇒ Procesados, mixto PDF+imagen) | R27 | `…_r27_*` (3) |

## Observaciones (no bloquean)

- **O1** · R11 «no son un mensaje»: `message_from_bytes` casi nunca lanza; unos bytes basura no vacíos se leen
  como `text/plain` y van por R22 (WARNING), no por R11 (ERROR). El destino final es el mismo (`Errores` si es lo
  único) y design §5 lo define así. Conocerlo al leer logs de T12.
- **O2** · `Content-Type: image/` (sin subtipo) con `attachment` daría `documento_<n>.` sin extensión. Cosmético.
- **O3** · `tasks.md` cita el worktree `../albaranes-F-054`; se trabajó en el árbol principal por orden del líder
  (anotado en el informe). Si el worktree existe, limpiarlo tras el merge.

## Papeleo de cierre del líder (condiciones para `done`)

1. **`progress/current.md`**: quitar de «LO PRIMERO…» «Ninguna feature `in_progress`» y la viñeta de F-054
   `spec_ready` con «4 decisiones DA por confirmar»; ajustar «F-051, F-053 y F-054 viven en sus ramas» (F-054 ya
   está en esta rama); dejar F-054 como `done` con la MANUAL T12 pendiente del humano y su procedimiento intacto.
2. **`progress/history.md`**: resumen de F-054 (alcance, DH1–DH5, DA4 v2/DA8, campaña 19/20 + 1 equivalente,
   T12 pendiente, O1–O2).
3. **`harness/features.json`**: F-054 → `done`; `bash harness/init.sh` para regenerar `BACKLOG.md` y comprobar verde.
4. Archivar `impl_F-054.md` y este `review_F-054.md` en `progress/historico/` (la campaña `mutacion_F-054.md` NO se
   mueve: F-039 la vigila por ruta).
5. Al humano: merge de la rama a `dev` y luego `.\deploy.ps1 -Only sv1` + `.\check_deploy.ps1` desde `infra/`, y la
   T12 tal como está en `current.md`.
