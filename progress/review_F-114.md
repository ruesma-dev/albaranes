# progress/review_F-114.md

Revisión completa (pasada 1) — `git diff dev...HEAD` sobre `05d2cb5` (rama `feature/F-114-proveedor-todos-sigrid`).

- **Veredicto:** APPROVED
- **Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige fase RED, puerta de cobertura y
  mutación muestreada (20, semilla `20260820`). RM5 no aplica (solo `critico`).
- **Fuera de esta review (por encargo del líder):** T8 (navegador del líder) y el despliegue (humano). No se ha
  consultado producción ni sigrid-api.

## 1. `bash harness/init.sh` (tal cual, en el worktree)

Exit 0, «ENTORNO LISTO». Arnés 1919 passed; sv1 236; sv2 496; sv3 1576; **sv4 2186 passed, 1 warning**; sv5 125;
sv6 506 (1 skipped); sv9 1073; comun en verde. Puertas: COBERTURA 100,0 % (54/54), RUTAS SENSIBLES N/A, TAMAÑO dentro.

## 2. Lo que el líder pidió mirar

| Punto | Resultado |
|---|---|
| SQL de `/api/sigrid/proveedores/todos` de solo lectura | `[x]` `SELECT TOP (?) … FROM prv JOIN con … GROUP BY … ORDER BY` por `_post_sql_read` (`sql/read`). Nada más. |
| Parametrizada, sin concatenar la búsqueda | `[x]` seis `?`: límite+1, tip 5, emp 1, fecbaj 0, patrón nombre, patrón CIF (`sigrid_lookup_client.py` l.240-247). La SQL es una constante; el texto del usuario solo entra como valor. `test_f114_r15_la_sql_lleva_todo_por_parametro`. |
| Escape de `!`, `%`, `_`, `[` | `[x]` `_patron_like` antepone `!` a los cuatro (el propio `!` incluido, imprescindible con `ESCAPE '!'`); `]`, `^` y `-` no son comodines fuera de corchetes, no hace falta escaparlos. Parametrizado con 6 casos (`%![x]%`, `%!!!%!_![%`…) y comprobado en los dos patrones. `ESCAPE '!'` en los dos `LIKE`; T0 del líder: con `!` funciona, con `\` da 506. |
| Mínimo 3, tope 50, «Hay más» | `[x]` mínimo en cliente (vacío sin llamar), endpoint (`ok=false` sin llamar) y JS (aviso sin `fetch`); `TOP 51` y `mas = len(rows) > 50` (cuenta filas SQL, no las que quedan tras propios/dedupe: R18 literal); línea «Hay más proveedores: escribe más para afinar» no elegible. |
| Una entrada por CIF con «N fichas» | `[x]` `GROUP BY v.cif` + dedupe Python por `normalizar_cif` sumando fichas; etiqueta « · N fichas en Sigrid» y `title` de «proveedor ambiguo» con `fichas > 1`. |
| CIF propios fuera | `[x]` `es_cif_propio(cif, cifs_propios(None))` de `ruesma_comun` (regla 18), y filas sin CIF fuera. |
| Check marcado por defecto, lista de la obra intacta (R21) | `[x]` `checked` en la plantilla, solo dentro de `{% if editable %}`, sin `localStorage`. `_SQL_PROVEEDORES_POR_OBRA`, `fetch_proveedores_por_obra` y `/api/sigrid/proveedores` sin una línea cambiada en el diff; dos tests de guarda (cliente y endpoint). En modo marcado el JS solo añade R10 y el descarte por `secuencia`, que no cambia si no se toca el check. |
| `azure-apps` | `[x]` commit local `7109c68` (`albaranes.md` §8, 12 líneas, trailer correcto), sin push. Sin secretos; da un recuento agregado (CIF vivos), no datos de terceros. |

### Desviaciones 1–4 del informe §2

1. **Foco con la etiqueta actual ⇒ aviso de 3 letras sin llamar.** Correcta: buscar «NOMBRE — CIF» no casaría con
   nada; respeta design §5 («focus llama a `buscarGlobal()`»).
2. **Blur cancela lo pendiente.** Correcta y con test propio; es consecuencia de R4.
3. **Lista de la obra en vuelo al cambiar el check.** Correcta (R8); con test propio.
4. **R10 «sin código de obra» detectado por el texto del error** (`/Falta el codigo de obra/` en `app.js` l.2383).
   Funciona hoy: es el texto exacto de `app.py` l.540 y el único error que lo dice. **Es frágil, pero no
   bloquea:** si alguien cambia ese texto en `app.py`, ningún test cae (el test JS lleva la cadena escrita a
   mano) y R10 se degrada a «⚠ Falta …» sin la invitación a desmarcar; no se pierde ni se guarda nada. Además el
   JS ya sabe que no hay obra sin preguntar (`currentObra()` vacío). Ver observación O1.

## 3. Checkpoints

- **C1** `[x]` init.sh exit 0 (§1); ficheros del arnés presentes.
- **C2** `[x]` una sola `in_progress` (F-114); rama correcta; `current.md` solo con la sesión activa;
  `history.md` sin cambios (la feature no está `done`).
- **C3** `[x]` hexagonal: modelo en `domain/models`, SQL en `infrastructure/sigrid`, ruta en
  `interface_adapters/web`; el dominio no importa infraestructura. `[x]` primera línea con ruta en los cuatro
  tests nuevos; los demás ficheros ya la tenían. `[x]` sin `print`, sin TODOs, sin secretos (los `console.log`
  del diff son el canal de salida de los scripts de node de `test_f114_js.py`). `[x]` reglas 17 y 18 de
  `ARCHITECTURE.md` respetadas.
- **C3 bis** N/A: la feature no trae documentos de fuera.
- **C4** `[x]` R1–R21 con test `test_f114_rN_*` (tabla §4), R22–R23 verificados por lectura; `[x]` tests sin
  red ni BBDD (`sigrid_api` falso, `TestClient`, node con `dom_falso.js`); `[x]` T8 (MANUAL, líder) y el
  despliegue listados en `progress/current.md` y en `tasks.md` con su comando.
- **C4 bis**
  - `[x]` `rigor: estandar` declarado.
  - `[x]` Fase RED con salida real por tarea (T1 25 failed, T2 7, T3 4, T4 3, T5 6) en `impl_F-114.md` §3.
  - `[x]` Cobertura: `PUERTA COBERTURA` `[OK]` 100,0 % de 54 líneas cambiadas (umbral 80 %).
  - `[x]` Mutación: `progress/mutacion_F-114.md` de `harness.mutacion`. **Recalculado de forma independiente:**
    `alcance_de_feature("F-114")` da 11 + 108 + 33 = 152 líneas en los tres mismos ficheros y
    `generar_mutantes` da 28 mutantes, como el informe. Reproducido el sorteo (`random.Random(20260820)`): los 20
    evaluados son 13 del cliente y 7 de `app.py`; el superviviente existe tal cual (`app.py:555`, `booleano`,
    `include_in_schema=False` → `True`).
  - `[x]` Muertos comprobados: «Tiempo total» 1.713 s > 60 s ⇒ **campaña no reejecutada (28,6 min según el
    informe)**; se queda en recálculo puro + RM1–RM6.
  - `[x]` Tiempo coherente: 20 × 85,7 s = 1.714 s ≈ total; media 85,7 frente a línea base ~228 s con 19/20
    muertos y `-x`: el caso legítimo de RM2, no un salto de orden de magnitud.
  - `[x]` Sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto (base rota)» = 0, línea base declarada por worker.
  - `[x]` **RM1**: medido sobre `46eeeef` (T6). Desde ahí hasta HEAD solo cambian `test_f114_endpoint.py` (+7, el
    test del superviviente) y ficheros de `progress/`/`specs/`: ningún fichero del alcance. No hay que repetir.
  - `[x]` **RM3**: repasados los 19 muertos del sorteo; ninguno equivalente. Los más dudosos se matan con tests
    concretos: `fichas or 1`→`or 2` (fichas `None` en `test_f114_r17_fichas_ausentes_cuentan_como_una`),
    `mas=False`→`True` del corte (`mas is False` en el test del mínimo), `or`→`and` en l.262 (CIF propio). El
    único equivalente candidato del alcance (`previo.fichas or 0`→`or 1`, l.271) no salió en el sorteo.
  - N/A **RM5**: rigor `estandar`.
  - `[x]` **RM6**: el superviviente se mató con un test nuevo (`/openapi.json` no lista la ruta), sin quitar
    código defensivo.
  - N/A campaña manual / cero mutantes: la automática dio 28.
  - `[x]` El superviviente tiene su análisis (test nuevo, comprobado a mano con el mutante aplicado).
  - `[x]` «Evidencias» con los cuatro números (§6 del informe).
- **C4 ter** N/A: la puerta dice «F-114 no toca ninguna ruta sensible declarada».
- **C5** `[x]` T0–T7 y T9 `[x]` con commit `F-114 Tn:` por tarea (T0 del líder, en `spec_F-114.md`). T8 `[ ]` por
  diseño: MANUAL del líder, excluida de esta review por encargo; no bloquea la review pero sí el `done`.
  `[x]` sin ficheros temporales sin trackear en el worktree. `[x]` `features.json` en `in_progress`: es el
  estado real (falta T8).

## 4. Trazabilidad requisito → test

| R | Test(s) |
|---|---|
| R1 | `test_f114_r1_editable_pinta_el_check_marcado`, `_r1_el_check_no_va_dentro_de_un_label…`, `_r1_solo_lectura_no_pinta…` |
| R2 | `test_f114_r2_marcado_es_el_combo_de_hoy` |
| R3 | `test_f114_r3_minimo_de_tres_caracteres_utiles`, `_r3_desmarcado_busca_en_el_servidor_sin_refiltrar` |
| R4 | `test_f114_r4_debounce_de_300_ms…`, `_r4_salir_de_la_caja_cancela…` |
| R5 | `test_f114_r5_r6_hay_mas_y_varias_fichas`, `_r5_sin_mas_no_hay_linea_final` |
| R6 | `test_f114_r6_etiqueta_con_varias_fichas`, `_r5_r6_hay_mas_y_varias_fichas` |
| R7 | `test_f114_r7_elegir_rellena_y_guarda_como_hoy` |
| R8 | `test_f114_r8_cambiar_el_check_vacia…`, `_r8_la_lista_de_la_obra_en_vuelo…` |
| R9 | `test_f114_r9_nada_en_localstorage`, `_r9_el_check_sale_marcado_en_cada_carga` |
| R10 | `test_f114_r10_mensaje_lista_de_la_obra_vacia`, `_r10_lista_de_la_obra_vacia_o_sin_obra` |
| R11 | `test_f114_r11_errores_de_la_busqueda_global` |
| R12 | `test_f114_r12_responde_items_con_fichas_y_mas` |
| R13 | `test_f114_r13_q_corto_no_llama`, `_r13_sin_q_no_llama`, `_r13_bajo_el_minimo_no_llama`, `_r13_justo_el_minimo_llama` |
| R14 | `test_f114_r14_sin_cliente`, `_r14_excepcion_del_cliente` |
| R15 | `test_f114_r15_la_sql_lleva_todo_por_parametro`, `_r15_constantes` |
| R16 | `test_f114_r16_patron_like_escapa_comodines` (6 casos), `_r16_cif_sin_espacios…`, `_r16_comodines_del_texto_escapados…` |
| R17 | `test_f114_r17_un_proveedor_por_cif…`, `_r17_dos_grafias…`, `_r17_fichas_ausentes…` |
| R18 | `test_f114_r18_con_la_fila_de_mas…`, `_r18_justo_el_limite…`, `_r18_mas_cuenta_filas_sql…` |
| R19 | `test_f114_r19_fuera_cif_propio_y_filas_sin_cif` |
| R20 | `test_f114_r20_truncado_lanza`, `_r20_log_con_etiqueta…sin_clave`, `_r20_max_rows_del_cliente` |
| R21 | `test_f114_r21_proveedores_por_obra_intacto`, `_r21_la_lista_de_la_obra_no_cambia` |
| R22 | Lectura: `git diff --stat dev...HEAD` sin ficheros de sv3/sv5/sv6/sv9 ni `ruesma_comun` (solo se importa). |
| R23 | Lectura: viñeta en la regla 17 de `ARCHITECTURE.md`, fila en `sv4.md` §4.2, `azure-apps` `7109c68`. |

## 5. Cambios requeridos

Ninguno.

## 6. Observaciones (no bloquean)

- **O1 (desviación 4).** Cambiar en `static/app.js` l.2383 la condición `/Falta el codigo de obra/.test(error)` por
  `obraInputId && !currentObra()` (el JS ya lo sabe antes de llamar), o, si se quiere mantener el texto, añadir un
  test que lea la cadena de `app.py` l.540 y la case con la regex del JS. Puede ir en F-115 o en un `chore`.
- **O2.** Tras elegir en modo global, la caja enseña la etiqueta con « · N fichas en Sigrid» hasta que la recarga
  del guardado (R9) la repinta. Cosmético.
- **O3.** `ruff` no está en el venv de sv4 del worktree (informe §2.8): no se ha pasado el linter. Igual que en
  features anteriores; conviene instalarlo en el venv de sv4.

## 7. Automejora (propuesta, no aplicada)

Ninguna.
