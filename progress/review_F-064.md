<!-- progress/review_F-064.md -->
Revisión completa (pasada 1) · `544113b..6cabbe3` (merge-base con `dev`; la fusión de F-053 en `dev` queda fuera)

# F-064 · review

**Veredicto: APPROVED, con el CIERRE CONDICIONADO** a cuatro cosas del humano (§5). Lo que puede verificarse sin LLM
está verificado. Que la IA deje de leer el CIF del cliente solo lo dirán T9 y T10.

**Rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de lo cambiado, mutación
con 0 supervivientes salvo equivalente aceptado por el humano, RM1–RM6 y las MANUAL con su comando. RUTA SENSIBLE
(prompts de sv2): C4 ter.

**Restricción de máquina (impuesta por el líder):** no he ejecutado `init.sh`, ni suites completas, ni cobertura
global, ni la campaña. Me baso en el informe (`ENTORNO LISTO`, cobertura 98,9 %) y lo digo en cada punto. Ejecutado,
un fichero por pytest (venv del árbol principal, `PYTHONPATH` = comun del worktree): sv2 `test_f064_empresas_cliente`
24 passed, `test_f064_prompt_ia1_proveedor` 15, `test_f064_prompt_ia2_proveedor` 26, `test_f051_prompt_partida` 23;
raíz `test_f064_comparar_proveedor` 68, `_base` 7, `test_f064_r18_rutas_sensibles` 5, `test_f011_r19_r20` 16; sv3
`test_f063_cif_propio` 35. Árbol limpio después (`git status` vacío).

## 1. Los seis puntos del encargo

1. **Sin duplicación de la lista.** `empresas_cliente.py:24-28` importa de `ruesma_comun.proveedores`, la misma
   fuente que sv3 (`header_resolver_service.py:27-28`); el diff de sv3 y comun sale vacío. En los dos servicios solo
   está la variable `CIFS_PROPIOS`, que es configuración (el parseo vive en comun) y está justificada en design D6.
   El render del bloque solo sirve al prompt de sv2: LÍMITE DE SERVICIO respetado.
2. **Formato del prompt.** `str.replace` (`albaran_extraction_service.py:245-249`) y una sola pasada de regex en fase
   2, sin `.format()` y sin llaves en el bloque ni en la regla. He renderizado el task real con `CIFS_PROPIOS` sin
   pasar, `""` y `"B12345674 ; x"`: no queda ningún marcador y la sangría es coherente. Sin variable se usa la lista
   de serie; con el diccionario vacío, `(ninguna)`; sin marcador, el texto queda byte a byte (R7). Ver O3.
3. **¿Puede IA2 inventar el proveedor?** Sv2 no filtra nada (R12, D2): lo que devuelva IA2 llega a sv3. Un CIF
   inventado no lo valida la red por CIF de sv3 (F-062), y uno del cliente lo descarta F-063 con su motivo. La regla
   cubre el caso del CIF del emisor ausente (lo deja en null). Lo que **no** cubre es la duda: si IA2 discrepa sin un
   candidato claro, nada le dice «conserva lo de fase 1». Lo detallo en O1, que no bloquea porque C3 de T9 lo mide.
4. **Comparador.** Sin `--con-llm`: cuesta dinero por diseño, como `comparar_obra` (F-048), y ningún arnés lo
   invoca. Las claves salen solo de `os.environ` (:640): ni `Settings` ni dotenv, así que no lee `.env`. Las cuatro
   paradas con código 2 (:536-544) van antes de `montar_extractor`, y los tests solo usan dobles. C1–C3 (:211-248)
   cuadran con design §7; en C3, `inestable` o `error` cuentan como pérdida (lectura estricta). El resumen
   versionable va sin valores y `evals/salidas/` está ignorado (`.gitignore:53`).
5. **#28 y RM5.** Es el único equivalente declarado. `"error" not in {...}` mira la clave, no el valor. Reproducido
   en un clon (`git clone --shared`, scratchpad): con el mutante, 68 passed; con el control `{"ok": True}`, la
   demostración falla, así que discrimina. **Falta que el humano lo acepte** (nivel `critico`).
6. **Puerta de rutas sensibles.** El AVISO por falta de `progress/evals_F-064.md` es el esperado: T9 y T10 son del
   humano. Por eso el cierre queda condicionado (§5).

## 2. Checkpoints

- **C1** `[x]` `init.sh`: no lo he reejecutado por la restricción. El informe dice `ENTORNO LISTO` tras
  `910b59b`+`cd3b681`; después solo cambian `progress/` y un test, que he ejecutado. `[x]` Los ficheros base existen.
- **C2** `[x]` En la rama solo F-064 está `in_progress` (ojo, O5). `[x]` Rama `feature/F-064-proveedor-en-prompts`.
  `[x]` `current.md`: los bloques que añade la rama son de la feature activa y apuntan a los comandos (convención del
  repositorio). Hay un resto que limpiar al fusionar (O4). `[x]` F-063 `done` con su historia.
- **C3** `[x]` Hexagonal: `empresas_cliente.py` en application, puro, solo importa comun; el cableado está en
  `interface_adapters`. `[x]` Primera línea con la ruta en todos los ficheros nuevos. `[x]` Sin prints de depuración
  (los de `comparar_proveedor.py:574-575,644` son la salida del CLI), sin secretos (A81873903 es el CIF público del
  cliente, que ya está en comun; los de los tests son inventados) y sin dependencias nuevas. `[x]` Regla 18 de
  ARCHITECTURE escrita. Las trampas de merge, schema y unidades no aplican: no hay SQL, schema ni importes.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** `[x]` Trazabilidad (§3), todo en verde. `[x]` Sin red ni BBDD: dobles de cliente de visión y extractor
  doble. `[x]` MANUAL T9, T10 y T12 con su comando exacto en `impl_F-064.md` §6, referenciado desde `current.md`.
- **C4 bis** `[x]` `rigor` declarado. `[x]` Fase RED con trazas reales (T1, T2 R6/R2, T3, T4, T6, T7) y controles
  negativos. `[x]` Cobertura 98,9 % (350/354) según el informe, sin reejecutar. `[x]` Mutación recalculada por mi
  cuenta (§4). `[x]` Campaña de 5711,7 s > 60 s: **campaña no reejecutada (95 min según el informe)**, y además
  estaba prohibido por la restricción; me he quedado en el recálculo puro, RM1–RM6 y la reinyección (RM4). `[x]` Coste
  por mutante 5711,7 × 4 ÷ 145 = 157,6 s. `[x]` Sin «CAMPAÑA NO VÁLIDA»; «Sin veredicto» = 0. `[x]` RM1–RM6 (§4).
  `[x]` 0 `PENDIENTE`, con el equivalente pendiente de que lo acepte el humano. `[x]` «Evidencias» con los cuatro
  números y 4 workers. La campaña manual no aplica: hubo campaña automática.
- **C4 ter** `[ ]`→**condición de cierre**: falta `progress/evals_F-064.md`. La exigencia es `aviso`; el motivo es
  que T10 es del humano y va antes de fusionar. Cuando llegue, debe ser FRESCO: con commit posterior a `8814e4f`, el
  último que tocó rutas sensibles.
- **C5** `[x]` T0–T8 y T11 `[x]`, con commit `F-064 Tn:` cada una. T9, T10 y T12 siguen `[ ]` porque son MANUAL del
  humano, que es lo correcto en `critico` (§5). `[x]` Sin artefactos sin trackear: la junction de sv4 está ignorada
  y documentada. `[x]` `features.json` dice `in_progress`, que es lo real.

## 3. Cobertura requisito → test

| R | Test (todos `test_f064_…`) | R | Test |
|---|---|---|---|
| R1 | `r1_sin_extra_son_las_de_serie_…` (+5) | R10 | `r10_hay_cuatro_prompts_de_fase_2` (+3) |
| R2 | `r2_cifs_propios_es_opcional_…`, `r2_worker_y_api_…` (+3) | R11 | `r11_los_schemas_no_cambian` |
| R3 | `r3_bloque_con_cabecera_…` (+9) | R12 | `r12_el_envelope_final_lleva_el_cif_…` (+2) |
| R4 | `r4_lee_el_diccionario_en_cada_llamada` (+1) | R13 | sin `r13_*`: es un requisito de «no cambia», trazado por el diff vacío de sv3/comun y `test_f063_cif_propio` (35) y F-062 en verde |
| R5 | `r5_el_task_lleva_el_marcador_una_sola_vez` (+2) | R14 | `r14_clasificar_cif` (+13) |
| R6 | `r6_un_correo_que_escribe_el_marcador_…` (+4) | R15 | `r15_ficheros_de_base_…` (+8), `_base` (7) |
| R7 | `r7_sin_marcador_el_task_queda_como_…` | R16 | `r16_mayoritaria` (+22) |
| R8 | `r8_el_nombre_es_la_razon_social_…` (+5) | R17 | `r17_para_sin_la_clave_…` (+6) |
| R9 | `r9_la_regla_se_carga_tras_las_existentes` (+3) | R18 | `r18_la_puerta_de_evals_cubre_…` (+2) |

**He falseado los tests en una copia (scratchpad), 10 de 10 detectados:** bloque sin razón social; añadidas sin
quitar las de serie; API sin la lista; worker con `None`; defecto `()`; regla sin «prevalece sobre Sigrid»; regla sin
«proveedor_cif en null»; vuelve «Busca el código por un campo que ponga CIF»; IA1 sin «proveedor_cif es null»; id de
regla cambiado. Los textos de IA1 e IA2 coinciden al pie de la letra con design §4 y §5.

## 4. Mutación: verificación independiente

- **Recálculo puro** (`alcance_de_feature("F-064")` + `generar_mutantes`): 7 ficheros, **961 líneas, 145 mutantes**.
  Coincide con el informe. **RM1:** el SHA medido es `0ffa0d4`; de ahí a HEAD solo cambian `tests/` y `progress/`
  (`git diff --stat 0ffa0d4..HEAD`), así que el alcance es el mismo. **RM2:** la media de 39,4 s × 4 workers da 157,6
  s reales por mutante, frente a una base de ~190 s (raíz) + ~15 s (sv2). Es coherente con `-x`, y 145 × 39,4 ≈
  5712 s.
- **Muestra de supervivientes:** #1 (245 `entero`), #2 (298 `logico`), #10 (440 `logico`) y #28 (577 `booleano`)
  existen como mutantes reales, con el mismo texto original→mutado.
- **RM4 (reinyección en el clon):** #1, #10, #29 y #30 caen, cada uno con el test que el informe dice que lo mata.
  #28 sobrevive, como debe.
- **RM3:** los 19 mutantes de sv2 y `sv2_proveedor.py` cambian algo observable; ningún equivalente sale muerto.
- **RM5:** reproducido (§1.5). **RM6:** N/A justificado: tras T6 solo hay `576ad6a` (imports) y tests; no se quitó
  ninguna guarda.

## 5. Condiciones de cierre (no se marca `done` sin ellas)

1. **T9** (humano): `progress/comparar_proveedor_F-064.md` con C1, C2 y C3 en OK y `VEREDICTO: VERDE`. Si sale el
   AVISO «la base no dio ningún CIF cliente», el VERDE no prueba la incidencia: hace falta la decisión escrita del
   humano o añadir el albarán real (design §7).
2. **T10** (humano): `progress/evals_F-064.md` con IA1 ≤ 154 e IA2 ≤ 4 fallos críticos, con commit posterior a `8814e4f`.
3. **Aceptación escrita del humano del equivalente #28** (rigor `critico`).
4. Tras fusionar, `init.sh` en verde en el árbol principal; quitar la junction antes de `git worktree remove`.

## 6. Observaciones (no bloquean; numeradas con su severidad)

- **O1 · media** · `revision_rules.yaml:126-131`. Le falta a la regla un «en la duda, no cambies». La cláusula «o no
  son los del emisor» invita a IA2 a reescribir un proveedor correcto de fase 1 por una duda subjetiva, y nada dice
  qué hacer con `proveedor_nombre` cuando no se identifica al emisor. Compárese con `unidad_medida_camion`: «Si no
  puedes confirmar… NO cambies nada». El literal es el de la spec aprobada (§5) y C3 de T9 lo mide. **Recomendación
  al líder:** proponer al humano, ANTES de pagar T9, añadir «Si no puedes leer con seguridad al emisor, conserva lo
  de fase 1 salvo que sea una empresa del cliente (entonces CIF null)». Hacerlo después obliga a repetir T9 y T10.
- **O2 · baja** · Las dos instrucciones se declaran prioritarias a la vez. El párrafo fijo «GROUNDING CONTRA EL ERP
  SIGRID… MANDAN sobre cualquier otra regla de la cabecera» (`prompts.yaml:331-336` y los otros tres prompts de fase
  2) choca con «Esta regla prevalece… también sobre el contexto del ERP Sigrid». Hoy no tiene efecto:
  `main_worker.py:69` usa `GroundingNulo` y el bloque dice «no disponible». Pero `/extract/phase-2` acepta
  `sigrid_context_json` (`api/app.py` ~385). Lo tiene que resolver F-049 o F-055 al reescribir ese párrafo
  (contrato de design §8): conviene añadir allí la excepción `proveedor_emisor`.
- **O3 · baja** · Lo que no es un CIF en `CIFS_PROPIOS` llega al prompt como si lo fuera: `"x"` se pinta como
  `X — empresa del grupo…`, porque `normalizar_cif` no valida. Es el mismo comportamiento que tiene sv3 desde F-063.
  Para el futuro, en comun: filtrar con `identificador_fiscal_valido`.
- **O4 · baja** · `current.md`: el bloque «F-064 · SPEC ESCRITA» está superado y sigue el de «F-063 · EN CURSO»
  heredado de `544113b` (`dev` ya lo podó). Condensar al resolver el conflicto de la fusión.
- **O5 · info** · `dev` tiene F-053 `in_progress`: fusionar F-064 aún `in_progress` deja dos e `init.sh` lo rechaza.
  **O6 · baja** · `azure-apps/albaranes.md` no menciona `CIFS_PROPIOS` (ni sv3 ni sv2). Decide el humano.

**Automejora (propuesta, sin aplicar):** en `reviewer.md`, exigir que toda regla de IA2 que mande «corregir» un
campo diga qué hacer en la duda (la asimetría de O1, que ningún test unitario ve).
