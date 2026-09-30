<!-- progress/review_F-048_final.md -->
Pasada 3 (cierre): APPROVED condicionado a la confirmación de T38 y T39 por el humano. Revisión incremental desde 4a906a8 (pasada 3) hasta 14fa99d

# F-048 · Review final

## Pasada 1 (2026-09-24, `1807e83..63571a6`) · CHANGES_REQUESTED, solo papeleo · compactada

- Código, tests y primera campaña, bien. Tres arreglos de papeleo, ya hechos por el líder: `current.md` con lo
  pendiente, el comando `-Only sv3 → sv2 → sv1` (`ARCHITECTURE.md`, `azure-apps`) y T37 sin el falso rojo.
- `init.sh` exit 0, raíz `865 passed`, cobertura 99,5 %; a mano comun 274, sv1 98, sv2 374, sv3 233, sv4 247.
- Primera campaña (`e7fe2c0`, 175 mutantes): recalculada, RM1–RM6 [x], 3 huecos reinyectados, y los equivalentes 9,
  22 y 23 demostrados y aceptados. Extremo a extremo sin desajustes. sv2 antes que sv3 manda todo a poison.

## Pasada 2 (2026-09-25, `88085cb..4d94ba2`) · CHANGES_REQUESTED, solo papeleo · compactada

**Rigor** `critico` (declarado): RED, cobertura ≥ 80 %, 0 supervivientes sin justificación aceptada, RM1–RM6, MANUAL.

### Decisiones del humano (2026-09-24), que no cuento como defecto

- **(a) T40**: la puerta de rutas sensibles pide `VEREDICTO: VERDE`. **Queda sustituido por aceptación explícita del
  humano** de dos evidencias: la pasada `completa` SIN correo (`progress/evals_F-048.md`, ignorado por git, `fac6b10`,
  ROJO por defectos previos del banco) y el comparador de obra (`progress/comparar_obra_F-048.md`: 7 idénticos, 1
  difiere, 2 inestables, 0 con errores; `analisis_evals_F-048.md` §6: la rama deduce la obra donde `dev` daba null y
  no empeora ningún caso). La parte CON correo de T40 queda sin medir: la cubren T37–T39, que son manuales.
- **(b)** Los 3 equivalentes (9, 22, 23 = 78, 79, 80 de la segunda campaña): aceptados.
- **(c)** De F-047 solo `evals/inyeccion.py`. Los 6 de `GestoRevisor` (43, 44, 46–49) se justifican en bloque como
  código de F-047 (aceptado por el humano el 2026-09-25, `8896bd4`).

### Lo que se comprobó (resultados reales de la pasada 2)

- `init.sh` exit 0, raíz `1064 passed`, `PUERTA COBERTURA 98.3 %` (1369/1393), `TAMAÑO` OK, AVISO de rutas sensibles
  cubierto por (a). `git diff 14cee8a..HEAD -- services/ evals/ ':!**/tests/**'` vacío (RM1).
- **Bloque E**: B1 (`fc91569`, `_ubicacion`) y B2 (`a3c870a`, estado `ERROR`) con RED reproducido por mí (4 failed / 3
  failed al revertir). B3 = segunda campaña. B4 (`6558755`) anotado para F-047. Menores 1–3 cerrados; 4 y 5 no bloquean.
- **Segunda campaña (T34, `14cee8a`)**: recálculo puro con 45 ficheros, 3.771 líneas y **410 mutantes** (235 de
  `evals/` + 175 de `services/`), igual que el informe; los **80 supervivientes existen** tal cual (0 discrepancias);
  330 muertos cuadran. Ni «⚠ CAMPAÑA NO VÁLIDA» ni base rota, 0 `PENDIENTE`. **Tiempo total 21.051,1 s > 60 s ⇒
  campaña no reejecutada** (5,8 h); en su lugar, recálculo + RM1–RM6 + muestreo.
- RM1 [x] SHA `14cee8ac07a4…` sin producción cambiada después. RM2 [x] coste por mutante 102,7 s (2 workers) frente a
  bases de 15–534 s, sin salto de orden de magnitud. RM3 [x] los 158 muertos de `evals/`, uno a uno, sin equivalentes.
  RM4 [x] 4 muertos de `evals/` al azar (semilla 20260925) mueren, y 4 huecos cerrados reinyectados (#35, #77, #45,
  #53) fallan como dice el informe. RM5 [x] 78–80 sin cambios desde `e7fe2c0`, demostración `10 passed`. RM6 [x] no se
  quitó ninguna guarda. `GestoRevisor` idéntico byte a byte al de F-047 (`1d34afb`). **Sin justificar: 0** (71 con
  test + 6 de F-047 + 3 equivalentes = 80).
- Cambios que pidió: (1) `current.md` con las decisiones (a)–(c) y solo G pendiente; (2) T40 `[x]` citando (a).

## Cierre (pasada 3) · 2026-09-29 · incremental `4a906a8..14fa99d` · rigor `critico`

**Veredicto: APPROVED condicionado a que el humano confirme T38 y T39.** No es un APPROVED pleno: la feature no pasa a
`done` hasta que consten esas dos verificaciones MANUAL (R43) y se haga el papeleo de cierre de abajo.

### Qué ha cambiado desde la pasada 2 (solo papeleo)

| Commit | Ficheros | Contenido |
|---|---|---|
| `9143cbf` | `progress/current.md`, `tasks.md` (T40) | Los dos cambios pedidos en la pasada 2 |
| `8896bd4` | `progress/current.md` | (c): aceptación en bloque de los 6 de `GestoRevisor`, fechada el 2026-09-25 |
| `14fa99d` | `tasks.md` (T36, T37) | T36 y T37 `[x]`, verificadas por el humano el 2026-09-29 con correos reales |

- `git diff 4a906a8..HEAD --stat -- services/ evals/ tests/` **vacío**; también `harness/ infra/ docs/`. Todo lo
  aprobado en la pasada 2 (código, tests, las dos campañas, trazabilidad) sigue valiendo sin volver a leerlo: el delta
  no toca firmas, ficheros de alcance ni lo medido por la campaña.
- **Cambio 1 de la pasada 2** [x]: `current.md` recoge (a), (b) y (c) con sus evidencias, da E y la 2.ª campaña por
  cerradas (410 = 401 muertos tras el análisis + 9 justificados, cuadra con 330 + 71 y 6 + 3) y deja solo G. Retiradas
  las cinco frases obsoletas que cité.
- **Cambio 2 de la pasada 2** [x]: `tasks.md:74` T40 `[x]` con la decisión (a), `evals_F-048.md` a `fac6b10` y
  `comparar_obra_F-048.md`.

### Qué ejecuté (T41)

- `bash harness/init.sh`: **exit 0, ENTORNO LISTO**. Raíz `1064 passed in 294.59s` (mismo número que en la pasada 2).
  `PUERTA COBERTURA: 98.3 %` (1369/1393, umbral 80 %). `TAMAÑO` OK (requirements 150/150, design 249/250, impl
  220/220). Los 7 servicios Python salen de caché, y es válido: el árbol de `services/` no ha cambiado desde el último
  verde. `[AVISO] RUTAS SENSIBLES`: las mismas 11 rutas, sin `VEREDICTO: VERDE`; lo cubre la decisión (a). Avisos de
  ruff (1164, deuda previa) e `infra` sin tests: previos y ajenos a F-048.
- `git status` limpio antes y después.

### `azure-apps` y orden de despliegue

- `azure-apps/albaranes.md` (commits `96bbdb6` y `f9a8c15`, 2026-09-24; el repositorio no tiene remoto) describe lo que
  se despliega: blob lateral `input/{id}.correo.json`, `correo_blob` en `MensajeExtraccion`, `correo_sha256` en
  `payload_json`, `data.origen_datos` sin DDL y los motivos `correo_obra_distinta_papel` / `correo_obra_ambigua`, y el
  GET de Graph solo lectura con `uniqueBody`. Contrastado con el código: `mensajes.py:58`, `origen_datos.py:70-71,117`,
  `contexto.py:49` (4.000 caracteres). §7 fija **sv3 → sv2 → sv1 (sv4 cuando sea)**, con el comando `-Only` y el
  rollback al revés.
- `docs/ARCHITECTURE.md` regla 15, líneas 224-228: el mismo orden y el mismo comando, y el aviso de que `deploy.ps1`
  sin `-Only` actualiza sv2 antes que sv3.

### Checkpoints (cierre)

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una sola `in_progress` (F-048) · [x] rama `feature/F-048-correo-contexto-ia1` · [x] `current.md` describe
  la sesión activa (véase la observación 1) · N/A `history.md`: F-048 aún no está en `done`; pasa a ser obligatorio al
  cerrarla (condición 3).
- **C3** [x] Sin cambios de código desde la pasada 2, donde quedó en [x]. **C3 bis** N/A: no se toca `docs/referencia/`.
- **C4** [x] Las 44 R con test en verde o MANUAL (tabla de abajo). [x] Tests sin red ni BBDD. [x] MANUAL: T36 y T37
  **hechas por el humano** (2026-09-29, `14fa99d`, «está funcionando bien»); T38 y T39 siguen listadas en
  `current.md` y con su comando exacto en `tasks.md:72-73`, **pendientes: son la condición de este veredicto**.
- **C4 bis** [x] Todo en [x] en la pasada 2 y sin cambios de alcance después (RM1 sigue valiendo: `14cee8a` y sin
  producción ni `evals/` cambiados). Cobertura 98,3 % reconfirmada hoy.
- **C4 ter** AVISO con motivo por escrito: decisión (a) del humano, recogida en `current.md` y en T40.
- **C5** [x] árbol limpio · [x] `features.json` refleja el estado real (`in_progress` mientras falten T38/T39) ·
  **condicionado**: `tasks.md` tiene T38, T39 y T41 en `[ ]`. T41 queda cumplida con esta ejecución y el líder la marca
  al cerrar. T36/T37 (manuales) se cerraron con commit `F-048:`, no `F-048 T36:`: lo acepto por ser verificaciones del
  humano sin código.

### Trazabilidad final (las 44 R)

| R | Cobertura |
|---|---|
| R1 · R8–R9 · R13 · R24 · R37 | comun `r1_contexto`, `r8_r9_mensaje`, `r13_prompt`, `r24_origen_datos`, `r37_llm_logger`, `t34_*` |
| R2–R7 · R10 · R36 · R39 | sv1 `r2_r4_graph`, `r3_r5_pipeline`, `r6_*`, `r7_r10_intake`, `r36_logs`, `r39_captura`, `t34_*` (R36 también en sv2 y comun) |
| R11–R25 · R42 | sv2 `r11_worker`, `r12_render_fase1`, `r14_*`, `r15_schema`, `r16_prompt_yaml`, `r18_*`, `r19_r22_tabla_d5`, `r23_r25_sellado`, `r24_lectura_tolerante`, `r42_encolar` |
| R26–R31 · R32–R35 | sv3 `r26_modelo`, `r27_merge`, `r28_red_obra`, `r29_r31_motivos_revision` · sv4 `r32_r34_vista_avisos`, `r35_vista_modelo` |
| R38 | raíz `test_f048_evals_correos.py::r38_*` + `cr_e3_*` · sv1 `r39_captura` (`git check-ignore`) |
| R40 · R41 | raíz `test_f048_r40_r41_inyeccion.py` + `test_f048_evals_correos.py::r40_*` |
| R43 | **MANUAL**: T36 y T37 hechas (humano, 2026-09-29); **T38 y T39 pendientes** |
| R44 | RED + `PUERTA COBERTURA` 98,3 % + T34, dos campañas |

### Condiciones para pasar F-048 a `done` (no son cambios de código)

1. **T38** (humano): «Volver a buscar» en `http://localhost:8004` sobre el documento de T37 y el SELECT de
   `tasks.md:71`: `origen_datos` sigue en el merge y el motivo de revisión sale **UNA** sola vez.
2. **T39** (humano): baja lógica del documento de T37 y reinyección del mismo PDF SIN `--correo` con otro `<DOC_ID2>`:
   `origen_datos.obra.motivo='sin_correo'`, obra del papel y sin motivos `correo_obra_*`.
3. **Papeleo de cierre del líder**, en el mismo commit que registre T38/T39: T38, T39 y T41 `[x]` en `tasks.md` (T41
   citando esta ejecución: `1064 passed`, 98,3 %); `current.md` sin el bloque de F-048 como trabajo vivo y con la
   observación 1 resuelta; resumen en `progress/history.md`; F-048 a `done` en `features.json` (y `init.sh` en verde
   después de ese cambio).
4. Si T38 o T39 **no** salen como se espera, el veredicto decae: hay que abrir un CR y volver a revisar.

### Observaciones (no bloquean)

1. `progress/current.md:30-33` sigue listando T36 y T37 como pendientes («Solo falta el bloque G… T36: …»), aunque
   `14fa99d` las marcó hechas en `tasks.md`. No falta nada por listar, sobra; se corrige en el papeleo de cierre
   (condición 3).
2. (T40 y despliegue: resueltos en el papeleo de cierre del líder.)
