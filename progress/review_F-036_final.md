<!-- progress/review_F-036_final.md -->
# F-036 · Review FINAL

Revisión **incremental desde `465d295`** (último commit aprobado, pasada 2) para el delta `CR-10..CR-13`
(`bf6139f`, `b7662f7`, `bb203af`, `1ebb597`; cierre `7eb9da6`), **más** recorrido completo de `CHECKPOINTS.md`
y juicio de la evidencia de **T23**, que es nueva. El bloque A y lo aprobado en la pasada 2 no se releen.

**VEREDICTO: APROBADO.** Cero bloqueantes. **No autoriza `done`**: cuatro condiciones al final.
**Rigor `critico`** (declarado en `features.json`): fase RED, cobertura, mutación sin supervivientes sin
justificar, RM1–RM6 y los `MANUAL (humano)` con su resultado real. **Ejecutado por mí, nada en paralelo:**
`bash harness/init.sh` → **exit 0**, raíz **556 passed in 370,81 s**, seis suites de servicio en verde,
`PUERTA COBERTURA [OK] 89,3 %` (604/676, umbral 80); más recálculo puro del alcance, un worktree desechable y
una copia en scratchpad, ambos retirados y el árbol limpio al acabar.

## Pregunta 1 · ¿vale la campaña de F-043 como T23? — **SÍ, con dos condiciones**

Verificado de primera mano, sin fiarme del informe:

- **Alcance recalculado** (`harness.alcance` + `mutacion.generar_mutantes`, cálculo puro): **38 ficheros, 3123
  líneas, 347 mutantes**, *exactamente* lo que dice el informe. **Cubre F-036 entera**: el diff de F-036
  (`e29ab4a..7eb9da6`) son 10 ficheros de producción y **los 10 están en el alcance**, con más líneas medidas
  en todos (`valuation_builder` 258/201, `review_repository` 301/288, `ler.py` 144/144).
- **RM1**: SHA medido `48e3d17`; de ahí a `18aa9a8` el diff toca **solo tests y `progress/`**, ni una línea de
  producción del alcance: la medición sigue válida y los supervivientes son cota superior. **RM2**: `Workers
  4`, total 6895,6 s, media 19,9 s → **79,6 s reales por mutante** contra líneas base de 4,5 a 137,1 s
  (`comun` domina, con 124 mutantes): coherente, sin «⚠ CAMPAÑA NO VÁLIDA» y `Sin veredicto = 0`. **Total >
  60 s → NO reejecuto**: recálculo puro + RM1–RM6, y **lo digo**, como exige C4 bis.
- **Muestreo**: nueve supervivientes contrastados contra los mutantes que genera la herramienta (los de
  `modifier_contract_matcher`, `residuos_container_calc`, `valuation_builder`, `ler.py`,
  `contexto_linea_merger`, `review_models` y `review_repository`) — existen todos, **mismo operador y mismo
  texto original→mutado**.
- **RM5** (obligatorio en `critico`): reproduje **uno** de los siete «equivalentes»,
  `contexto_linea_merger.py:92` `return True → return False`, en worktree aislado → **170 passed**, sobrevive.
  Y la justificación se sostiene: `_tiene_valor` solo se llama con `getattr(ctx, campo, None)` sobre
  `_CAMPOS_RESIDUOS` (`:114/:139/:143`) y los nueve campos son `Optional[str|float|bool]`
  (`contexto_linea.py:89-159`): rama inalcanzable. **RM3**: ningún equivalente figura como muerto.
- **163 = 96 huecos cerrados con test + 7 equivalentes con guarda + 60 en bloque** (scripts de diagnóstico de
  sv3, fuera del pipeline, autorizados el 2026-09-10): **0 en `PENDIENTE`** y el reparto cuadra con las 163
  secciones. **Los análisis no son de relleno**, salvo la forma de dos (hallazgo 3): verifiqué el grupo A
  reinyectando, sobre **copia en scratchpad**, los dos supervivientes peor documentados (`ler.py:133` y
  `:135`) → **los dos MUEREN** (1 failed de 25; base 25 passed). Y `test_f036_r14_catalogo_ler_exhaustivo.py`
  transcribe la Decisión 2014/955/UE **a mano**, sin importar `_CAPITULOS_LER`, barriendo 0-21 en capítulo y
  subcapítulo: mata por construcción cualquier mutación del catálogo.

**Dictamen: satisface T23; no hace falta campaña propia de F-036.** Dos condiciones: (a) T23 se marca `[x]`
citando `mutacion_F-043.md` + `impl_F-043_T28_supervivientes.md`; (b) la evidencia vale para **el árbol de
F-043**, no para el tip de F-036 (hallazgo 5).

## Pregunta 2 · `CR-10..CR-13` — **APROBADOS los cuatro**

Comprobados en el código, no en el informe. **CR-10**: `test_f036_r14_ler_reexportado.py:4-8` ya dice «sv2 y
sv6; sv5 NO, R13 retirada en `7ca2ffc`» (doc, sin RED: correcto). **CR-11**: `valuation_builder.py:1731` es
`if padre_residuos and cantidad is None`, con `padre_residuos` calculado en el cuerpo (`:1443-1448`) y no
atado a `modifier_source`: la «línea muda» queda cerrada. **CR-12**: `tests/test_f027_r18_r22_contrato.py`
trae `MotivoIlegible(AssertionError)` (`:145`), `_alias_de_modulo` (`:115`) y `_METODOS_QUE_ANADEN` (`:216`):
ya no calla. **CR-13**: `residuos_incrementos.py:152` usa `ler_creible`, y los dos `normalizar_ler` restantes
(`:125`, `:221`) van sobre `codigo_ler`, campo de código. Los tres con comportamiento traen **RED real**.

## Defectos, decisiones del humano y los dos «no se hizo»

**D1** (`review_repository.py:3559-3588` + `sin_cambios` `:3639-3645`, que solo compara entradas), **D2**
(`_score_contexto` `:113-115` y `_completar_campos_objetivos`) y **D3** (`REGLAS_SINTETICAS_RESIDUOS`,
`_sinteticas_residuos_faltantes` `:895-899`, forma C sin tarifa, guarda anti-incremento `:1033-1037`):
resueltos, los tres con test trazable. **Decisiones**: el volumen manda sobre la resta y los explícitos siguen
siendo prioridad 1 → `residuos_container_calc.py:155-190` y `prompts.yaml:1029-1036` / `:1022-1026`.
**Ninguna regla clasifica por LER**: las **siete** puertas de sv6 van por `_familia_de(ctx, clasificacion)`
(`:343, :670, :754, :897, :1035, :1215, :1445`), que no mira LER, texto ni CIF (`:302-310`);
`clasificacion_resolver.py:25-27` lo declara y `tipologia_resolver.py` ya no existe. **`ModifierContractMatcher`
no cableado**: solo se instancia en su test. **Deuda aceptable, no impide cerrar**: R20 está probado, hoy no
mueve un euro, y cablearlo es F-004 — donde debe juzgarse su efecto, con el hallazgo 1 delante.

**SS-0003967 no cambia el veredicto.** Con el match real de IA3 (línea 26481, el INCREMENTO) la guarda de R15
anula el match y el albarán sale en **90,00 € y a revisión**, no en 210,00. Está **declarado y fijado por
test** (`..._con_el_match_real_de_ss_0003967_no_se_llega_a_210`), con sus dos precondiciones en la docstring:
F-043 entrega la 1; la 2 —que IA3 case la base contra el CONTENEDOR— es política de match, fuera de F-036. Lo
que no sería aceptable es ejecutar T24 esperando 210,00.

## Checkpoints

- **C1** [x] `init.sh` exit 0 ejecutado por mí; los diez documentos obligatorios. **C2** [x] una sola
  `in_progress` (F-043); rama correcta; `current.md` solo de la sesión viva; F-036 no está `done`.
- **C3** [x] hexagonal respetada (`review_models.py` es dominio puro —pydantic y `ruesma_comun`, cero
  `infrastructure`—; `ler.py` solo `re`); primera línea con ruta en los nueve ficheros tocados; sin `print`,
  TODOs, secretos ni dependencias nuevas. Las tres trampas: sin SQL nuevo (las columnas ya estaban en
  `schema_contribution.py:92-93`/`:179-180`), lógica sobre merge, y la sintética sin precio **no mueve el
  total**. **C3 bis** **N/A justificado**: no toca `docs/referencia/`, así que no hay barrido que hacer.
- **C4** [x] R1-R12 y R14-R25 con test trazable `test_f036_rN_*` en verde, ninguno toca red, BBDD ni LLM; R13
  retirada; **R26** verificado (`git diff e29ab4a..HEAD -- '*test_f019*'` → **vacío**); **R27** satisfecho.
- **C4 bis** [x] rigor declarado; RED con traza real (bloque A, CR-2..CR-6, CR-11..CR-13); cobertura `[OK]`;
  mutación **verificada de forma independiente**; campaña >60 s **no reejecutada y dicho aquí**; RM1, RM2,
  RM3, RM5 y RM6 comprobados (RM6: no se quitó ninguna guarda — CR-11 y CR-13 **añaden** defensa); sin N/A.
- **C4 ter** [x] con motivo escrito. La puerta salió **`[AVISO] evals`** nombrando 13 rutas, cuatro de ellas
  de F-036, y falta `progress/evals_F-XXX.md`. **Motivo**: gasta LLM real (decisión del humano) y los
  fixtures no dan para una pasada completa (hallazgo 6). Exigencia declarada `aviso`: no bloquea.
- **C5** [ ] **a propósito**: `tasks.md` con **T23 y T24 en `[ ]`** y T11 en `[~]`, y `features.json` en
  `blocked`. Árbol limpio. Los commits del delta van `F-036 CR-n:` y no `F-036 Tn:`: correcciones de review,
  criterio aceptado en la pasada 2.

## Hallazgos

1. **MENOR** · `modifier_contract_matcher.py:284` llama a `normalizar_ler(desc)` sobre **texto libre**
   (`desc = _normalize(line.descripcion_linea)`, `:255`): misma familia de defecto que cerró CR-13, y contra
   el contrato de `ler.py:117-124` («quien decide sobre TEXTO LIBRE debe usar `ler_creible`»). Medido:
   `normalizar_ler("INCREMENTO TARIFA DESDE 01-01-25") → "010125"`, y `01 01` existe en el catálogo: una
   sintética de IA3 con una fecha exigiría ese falso LER en vez de caer al `"RESIDUOS" in d` que manda R20.
   **No bloquea**: el matcher no está cableado y el efecto sería `no_match`, no euros. Toca a F-004.
2. **MENOR** · Dos docstrings mienten sobre quién consume el catálogo LER, el defecto de CR-10 otra vez:
   `ruesma_comun/ler.py:7` dice «sv2 la usa en `tipologia_resolver`» —módulo que F-043 borró— y
   `albaranes-api/domain/models/tipologia.py:13`, «lo consumen sv2 y sv6». Grep: **ningún** módulo de
   producción de sv2 lo importa. El único consumidor real es sv6.
3. **OBSERVACIÓN** · Dos de los 163 análisis llevan prosa del grupo A que no les corresponde: **#92
   (`ler.py:133`)** y **#93 (`ler.py:135`)** están en `ler_creible`, no en `_CAPITULOS_LER`. El veredicto sí
   es correcto —los reinyecté y mueren— y la docstring del test nuevo dice 82, no 84.
4. **OBSERVACIÓN** · `test_f036_r25_salmedina_importes.py` cita aún `valuation_builder.py:1165/:846/:985`
   como puertas `tipo_familia == 'residuos'`; F-043 las sustituyó por `_familia_de(...)` y **ya cumple** la
   precondición 1 que esa docstring da por imposible.
5. **OBSERVACIÓN (condición de merge)** · Los tests que matan **96** supervivientes de código de F-036 viven
   **solo en la rama de F-043** (`9568ac2`, `8f36c77`, `cd35efb`, `805cccb`, `78d1c6e`): `git cat-file -e
   7eb9da6:<ruta>` → **no existen** en el tip de F-036, así que **F-036 no puede mergearse a `dev` por su
   cuenta**: va con F-043 o detrás, el orden que impone su `blocked`.
6. **OBSERVACIÓN** · **El árbol cambió durante esta review, por trabajo ajeno de F-043**: a las 10:57 se
   sembraron `evals/fixtures/{IA3,final,inputs}` con los 7 casos de SALMEDINA (`0 → 7`), ya commiteado, y solo
   toca `evals/` y `progress/`: **no afecta a lo que verifiqué a `18aa9a8`**. **IA1, IA2 e IA4 siguen a 0.**

## Qué falta EXACTAMENTE para marcar `done`

1. **F-043 cerrada y aprobada**: F-036 está `blocked` a su espera y su evidencia de mutación depende del árbol
   de F-043 (hallazgo 5).
2. **T24 · MANUAL (humano)**, solo lectura, los 7 albaranes de SALMEDINA, comando de `tasks.md:55`, con tres
   avisos: SS-0003967 dará **90,00 € y a revisión**, no 210,00; los tres invariantes 120/120/136 **ganan** una
   sintética sin precio y pasan a revisión, y eso es lo querido; y que ninguna línea real escriba `INCREMENTO
   170802` (pegado y sin `LER`), grafía que desde CR-3 da `None`.
3. **Evals · condición, no hecho.** `python -m evals.runner --con-llm --feature F-036`. Con IA1/IA2/IA4 a
   **0 casos** esa pasada no sería completa; mientras siga así, C4 ter se cierra con el motivo escrito.
4. **Papeleo**: T23 a `[x]` citando la campaña de F-043 (dictamen 1), `features.json` a `done`, resumen en
   `history.md` y limpieza de F-036 en `current.md`. Los hallazgos 1-4 son opcionales para cerrar F-036; el 1
   **no** lo es para F-004.

## Automejora (propuesta, no aplicada)

`harness.mutacion` debería **avisar cuando el alcance de una feature arrastra el de otra** (rama que sale de
otra rama, no de `dev`): aquí ahorró dos horas, pero solo se ve leyendo los 38 ficheros uno a uno. Repito la
de las dos pasadas anteriores: `harness.rutas_sensibles --feature F-XXX` explícito.
