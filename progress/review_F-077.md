<!-- progress/review_F-077.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (base `20bf230`, HEAD `df9c862`)

# F-077 · Ficha: guardar y aprobar de una vez · Review (2026-10-17)

**Veredicto: CHANGES_REQUESTED.** El **código queda aprobado** (spec, tests, arquitectura, rigor). Fallan el texto de
la MANUAL T14 en `current.md` (C4) y dos notas de spec que la fusión con F-076 pedía. Todo es documentación: la
pasada 2 será incremental y sin código.

**Rigor:** `estandar` (declarado): RED en los centrales, cobertura ≥ 80 % y mutación con supervivientes analizados.

## 1. Verificación ejecutada (resultados reales)

- `bash harness/init.sh` (Git Bash, worktree): todo verde salvo `PUERTA TAMAÑO`, que solo marcaba el borrador de esta
  review (176 > 140; recortado y reejecutado, ver la última línea de esta sección). Raíz 1237 passed; sv1 205, sv2
  397, sv3 703, **sv4 1715 passed sin caché** (152,5 s), sv5 43, sv6 444 (+1 skip), sv9 670; comun por caché.
  `PUERTA COBERTURA` [OK] 100,0 % (92/92).
- **Mutación, recálculo puro.** `alcance_de_feature('F-077')` da 6 ficheros y **301 líneas**; `generar_mutantes` da
  **39** (4+4+11+17+0+3). Coincide con el informe. El superviviente existe tal cual: `app.py:1761`, `booleano`,
  `include_in_schema=False→True`. **Campaña no reejecutada: 980,8 s según el informe** (> 60 s).
- **RM1.** Medido sobre `e1d9937`; después solo cambian tests, `progress/` y `tasks.md`: alcance medido = revisado. **RM2.** Base 169–170 s, media 49,0 s × 4 workers = 196 s reales por mutante: coherente con 19 de 20 muertos con
  `-x`; 20 × 49 = 980 s, el total. Sin «⚠ CAMPAÑA NO VÁLIDA»; sin veredicto = 0.
- RM3 N/A (sin equivalentes) · RM5 N/A (`estandar`) · RM6: no se quitó ninguna guarda.
- `init.sh` final, con esta review ya recortada: **exit 0, «ENTORNO LISTO»**, todas las suites ejecutadas (sv4 1715 passed; `PUERTA TAMAÑO` [OK], review 140/140).

## 2. Juicio de los puntos que pidió el líder

**2.1 · Desviaciones de `impl` §3.** Todas caben en la spec y ninguna exige volver al humano antes de fusionar. La #1,
la #2 y la #3 deben ir en el resumen de la PARADA 2.
- **#1 · « · » frente al salto de línea.** Cabe: la nota de F-076 (`current.md:152-158`) delega el separador en quien
  fusione F-077, y « · » es el que F-076 ya tiene aprobado. Pero la misma nota pedía «**ajusta R22 de F-077**» y no se
  hizo: R22 sigue con «en línea aparte», y `spec_F-077.md` §5 y design §5/§9 con «⏎» → cambio 2.
- **#2 · Motivos.** Cabe: R27 manda cubrir todo código que sv9 escribe. Los cuatro nuevos están en
  `alta_sigrid_service.py:59-64,430-442`. Los dos textos cambiados los permitía el Anexo A, y concuerdan con
  `azure-apps/sigrid_api.md` (líneas 320, 863).
- **#3 · «Dividir».** Cabe. R13 se ciñe a F-065 R19 y design §8 deja fuera `wireDividir`; lo erróneo era la premisa
  de design §3 («sin otros usos»). Que «Dividir» siga avisando es correcto, porque recarga la ficha.
  `contarFilasConCambios`, que ahora excluye las filas sin vid, no cambia nada: `concilia-editable` exige
  `valuation_line_id` (`document_detail.html:718`). Falta una nota en design §3 → cambio 2.
- **#4 a #8:** correctas. `enMarcha` tiene el mismo efecto que una variable del bloque. El `disabled` previo se
  respeta y está probado. El error de red en el PUT ya avisa. Con DESDE vacía, `resultado` (design §4). `data-estado`
  no lo lee nadie.

**2.2 · Panel del alta, según las palabras del humano.** Cumple.
- «En curso» solo en tres casos (`fase_alta`, `domain/services/alta_sigrid.py:97-134`): sin fila; fila anterior en
  un estado de `ESTADOS_ALTA_REPETIBLES` (los que sv9 vuelve a PROCESAR en `reclamacion.py`); o `en_curso` del mismo
  instante UTC.
- El resultado de la vigente es `resultado`. `no_admitido`/`revisar`/`error` salen como `error`, «Error en el alta en
  Sigrid: …», nunca «en curso» (`r17`).
- Sondeo de 3000 ms con `setTimeout` encadenado (`r19`). A los 5 min, `sin_respuesta`, borde exacto probado: error de
  tiempo sin sondear.
- **No sondea para siempre:** el servidor da `sin_respuesta` a los 5 min, la ficha recarga y deja de sondear; un 404
  lo corta. Solo un servidor que dé 500 sin parar sigue sondeando mientras la pestaña esté abierta (R19).
- **No sondea si sv9 va a ignorar la aprobación:** con `ya_en_sigrid`, `registrado`, `incierto` o `en_curso`
  anteriores, la fase es `resultado` (`r14_no_repetible_anterior…`).
- **La ruta GET es de solo lectura:** `estado_aprobacion` (`session.get`) y `leer_alta_sigrid` (SELECT sin `FOR
  UPDATE`). No publica, y el doble del servicio falla ante cualquier otro método (`r18`, `r20`).
- Observación, no bloquea: un `incierto`/`en_curso` anterior **pasada la Espera** sí lo reprocesa sv9. El panel
  enseña el viejo sin sondear hasta que se recarga. Lo decidió design §4.

**2.3 · «Guardar y aprobar».** Cumple (node sobre el `app.js` real): guarda antes las filas, en orden, y luego hace
el PUT (`r1`); si una falla, para sin PUT, con la fila en rojo y «No se ha aprobado…» (`r4`: 409, red caída, 422); D2:
la guardada se consolida y el reintento no la reenvía (`r5`); doble clic = un solo flujo, con los botones desactivados
durante el PATCH (`r10`); un único `?bloquear=1`, en `enviarFila` (`r12`). Observación: R6 relee el aviso solo si se
guardaron filas «en este intento»; tras un intento fallido que sí guardó, un reintento sin filas confirma con el
`data-aviso-suma` viejo. Cumple la letra; si importa, para otra feature.

**2.4 · ⚠ de partida.** Cumple: `aviso_partida_texto` exige `agree is False`, `kind == "assigned"` y lectura no vacía,
y solo se asigna en la rama `from_albaran` (`review_repository.py:4756`). `title` = `[descripción, nota F-076, aviso]
| select | join(' · ')`, escapado. Sin ⚠ en `manual`, `reparto`, sintéticas y Nueva (`r21`).

**2.5 · Integración tras la fusión.** F-078 R17: `test_f077_r11…` aprueba con `descripcion_linea` NULL y espera
«Líneas sin descripción: 3». F-076 R23–R25: el ⚠ sale del `agree_partida` de `coincide_partida`, sin tocarlo; la nota
y el ⚠ se excluyen; `test_f076_r24_literal_o_aviso_sin_nota`, adaptado.

**2.6 · T14 en `current.md`.** No basta → cambio 1.

## 3. Checkpoints

- **C1** [x] `init.sh` en verde · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` (F-076 `blocked`) · [x] rama de la feature · [x] `current.md` lleva solo trabajo
  vivo (MANUAL pendientes de F-078/F-076/F-077) · [x] las `done` tienen su resumen en `history.md`.
- **C3** [x] hexagonal (el dominio solo importa dominio y `ruesma_comun`; la ruta está en `interface_adapters`) ·
  [x] primera línea con ruta · [x] sin `print`/TODO/secretos (`console.log` solo en el arnés node de los tests) y
  sin dependencias nuevas · [x] reglas 19 y 20: solo merge, sin schema y sin agregados nuevos.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: la puerta de rutas sensibles da N/A con motivo.
- **C4** [x] R1–R28 con su `test_f077_rN_*` en verde (§4); R29 (RED, §4 del impl) y R30 (docs) revisados ·
  [x] sin red ni BBDD (dobles, `TestClient`, SQLite de `f065_bbdd`, node) ·
  **[ ] MANUAL con pasos exactos: el texto de T14 tiene errores (cambio 1).**
- **C4 bis** [x] `rigor` declarado · [x] RED con traza real de A, B (servidor y front), C y D · [x] cobertura [OK]
  100 % · [x] mutación verificada de forma independiente · [x] más de 60 s: recálculo puro, dicho en §1 ·
  [x] coste por mutante 196 s, más de 1 s · [x] sin cabecera de no válida · [x] RM1 · [x] RM2 · N/A RM5 (`estandar`) ·
  [x] RM6 · N/A campaña manual (no la hubo) · [x] superviviente analizado y cerrado · [x] «Evidencias» con los cuatro
  números y los workers · [x] ningún N/A sin motivo.
- **C5** [x] T1–T13 y T15 `[x]`, cada una con su commit `F-077 Tn:`; T14 es MANUAL pendiente · [x] árbol limpio ·
  [x] `features.json` dice `in_progress`, que es el estado real.

## 4. Cobertura requisito → test (`services/albaranes-front/tests/test_f077_*.py`; prefijo `test_f077_` omitido)

R1 `r1_guardar_y_aprobar…`, `r1_guardar_de_la_cabecera…` · R2 `r2_sin_cambios…` · R3 `r3_partida_mala…` · R4
`r4_falla_la_segunda_fila`, `r4_error_de_red…`, `r4_…422…` · R5 `r5_…consolidan…` · R6 `r6_con_filas_guardadas…` · R7
`r7_cancelar_*` (2) · R8 `r8_si_falla_la_lectura…` · R9 `r9_falla_el_put_*` (2) · R10 `r10_*` (3) · R11
`r11_el_servidor_sigue_rechazando…` · R12 `r12_una_sola_peticion…` · R13 `r13_ya_no_avisa…` · R14 `r14_*` (10) · R15
`r15_en_curso_sin_nada…` · R16 `r16_sin_respuesta…` · R17 `r17_*` (3) · R18 `r18_ruta_*`, `r18_servicio_*`,
`r18_…openapi` · R19 `r19_*` (5) · R20 `r20_la_ruta_es_get…` · R21 `r21_*` (6) · R22 `r22_*` (3) · R23 `r23_*` (3) ·
R24 `r24_*` (3) · R25 `r25_*` (3) · R26 `r26_*` (4) · R27 `r27_*` (3) · R28 `r28_*` (2). Todos en verde.

## 5. Cambios requeridos

1. **`progress/current.md`, bloque «F-077 · MANUAL del humano (T14)» (líneas 11-44).**
   - a) **Punto 1, «⇒ vuelve al listado», es falso:** el PUT redirige a la propia ficha (`app.py:1235`,
     `redirect_url=f"/documents/{detail.id}?…"`). Debe decir que la ficha se recarga aprobada (solo lectura), con el
     mensaje de guardado y las filas guardadas. El punto 3 («nada más aprobar») es esa misma ficha: hay que decirlo,
     porque sv9 responde en segundos.
   - b) **Quién la hace y qué escribe.** La hará el líder en el navegador, no el humano: hay que escribirlo así.
     Marcar las acciones que escriben en producción, cada una con el sí expreso del humano:
     - el punto 1: PATCH de fila con `?bloquear=1`, PUT de aprobación y publicación en `q-feedback` hacia sv9;
     - el punto 2, que no escribe nada si sale verde.
   - c) **Punto 1, datos reales.** «Cambia la cantidad de las dos» deja un albarán real aprobado con cantidades
     inventadas. Con `COMMIT=false` sale `simulado`, pero un «Solicitar alta» posterior con `COMMIT=true` las
     escribiría en Sigrid. Debe decir que la ficha y los valores los elige el humano, y que son correcciones que ese
     albarán necesita de verdad.
   - d) **Encaje en la secuencia combinada.**
     - En el paso 4 del bloque de F-076 (líneas 80-84): si F-077 ya está en `dev`, ese `deploy.ps1 -Only sv4` la lleva
       también, y su T14 va justo después.
     - El punto 5 (`86c13097` en `no_admitido`) va **antes del paso 6** (F-078 T14), que lo deja en `simulado`. La
       salida de hoy, «cualquier `no_admitido` con motivo de línea», no se puede verificar sin buscarlo en la BBDD.
   - e) **Punto 3, «un `no_admitido` sale en rojo…».** No tiene criterio de verde: con `COMMIT=false` lo esperable es
     `simulado`. Hay que ligar esa comprobación al documento del punto 5.
2. **Notas de spec que pidió la fusión**, con fecha y «(implementación, aceptado en review)»:
   - R22 de `requirements.md`: «en línea aparte» → « · », `title` «descripción · [nota F-076] · aviso».
   - Lo mismo en `spec_F-077.md` §5 y en design §5/§9.
   - Design §3: `avisoFilasSinGuardar` y `contarFilasConCambios` se quedan para «Dividir» (F-065 R29).
3. **`services/albaranes-front/sv4.md` §11 (líneas 549-553).** La cita «> F-077: …» quedó dentro del bloque
   ```` ``` ````, así que se pinta como código. Hay que sacarla encima de la valla.

## 6. Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C4, punto MANUAL: «cada acción que escriba en producción va marcada, con quién la ejecuta y su
autorización». Cambiar datos reales para probar no lo caza hoy ningún checkbox.
