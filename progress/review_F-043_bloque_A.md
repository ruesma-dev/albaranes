<!-- progress/review_F-043_bloque_A.md -->
# F-043 · BLOQUE A (T1-T4) — review

Revisión acotada al diff `b60a18e..HEAD` (pasada 1 del bloque; `af550a2`,
`d5e5994`, `31817bf`, `44707c5`, `e7e0d24`). NO se juzga el código de F-036 que
arrastra `git diff dev...HEAD`. **177 líneas: 37 por encima del tope de 140 de
`harness/rigor.json`**, tras dos pasadas de recorte; lo que queda son las razones
de los dos `[ ]`, los remedios exactos y las tres preguntas del encargo.

**Veredicto: CHANGES_REQUESTED (2 bloqueantes).** Ambos baratos —un renombrado y
un test de coherencia—; el catálogo, `familia_efectiva` y la campaña están bien y
verificados de primera mano, no creídos. **Rigor `critico`**: C1-C5 + fase RED +
cobertura ≥ 80 % + mutación con **cero supervivientes** + MANUAL listadas.

## Verificado de primera mano

- `bash harness/init.sh` **verde**: 556 passed (187 s), 6 suites de servicio OK,
  **COBERTURA [OK] 98,7 %** (367/372), TAMAÑO OK, árbol limpio.
- **Recálculo puro** (`alcance_de_ficheros` + `generar_mutantes`): 477 líneas
  (86+391) y **12 mutantes**, uno a uno los que describe §6 del informe.
- **Muertos comprobados por muestra (RM4)**: espejo de `comun` en el scratchpad
  (+ `albaranes-api/domain/models/tipologia.py`, que un test de F-036 exige por
  ruta); base 117 passed/3 skipped en 119 s, coherente con los 109,4 s
  declarados. Tres mutantes aplicados a mano, los tres mueren: `familia.id ==`→
  `!=` (16,5 s), `le=100`→`le=101` (15,8 s), `mixto` `False`→`True` (14,4 s).
  **Campaña NO reejecutada**: 239,4 s > 60 s.
- **Claves de prompt**: `albaran_revision_fase2_hormigon|mortero|residuos`
  existen en el YAML de sv2 y `valuation_residuos` en el de sv5: R3/R15 enrutan
  a algo real.
- **Prohibición del humano (2026-08-25), por `grep`**: LER/CIF/producto solo
  aparecen en docstrings y en `definicion`/`no_es`/`senales`, que son TEXTO PARA
  EL PROMPT (diseño §1.1: «evidencia, NO regla»). Cero código que los lea;
  `familias.py` importa `annotations`, `dataclass` y `Optional`. **Cumplida.**
- **Fase RED real**: las trazas cuadran con el estado del fichero en cada commit
  por aritmética independiente — T1 verde 21 (hoy ese `-k` selecciona 23: T2 y T3
  añadieron dos que casan «catalogo» y «prompt»), T2 12/33 (hoy 13), T3 10/42, T4
  sv2 5+2 de 65 y sv3 4+2 de 131. Un informe inventado no cuadra a este nivel.
- **La corrección del test en T1 es legítima**: el fallo era real (`otro` aparece
  en `residuos.no_es`, «de un punto a otro») y conserva la intención —que las
  familias de solo línea no salgan en el render de documento— buscando el id
  entrecomillado, que es como `render_catalogo_markdown` lista cada entrada, con
  el formato fijado por la aserción positiva del mismo test.
- **Las cuatro ramas de `familia_efectiva` contra §1.1** `[x]`, en ese orden:
  `if de_la_linea: return` · `if clasificacion is None` ·
  `bool(_campo(...,"mixto",False))` · `in familias_linea()`. `otro` no hereda
  (duda 2); el mixto bloquea la herencia, no la rama 1; no escribe nada (R21);
  acepta objeto o `dict` (R20). El normalizado de la rama 1 es inocuo:
  `ContextoLinea.tipo_familia` ya es un `Literal`.

## Checkpoints

- **C1** `[x]` exit 0 y los siete ficheros. **C2** `[x]` una sola `in_progress`,
  rama correcta, `current.md` sin restos. **C3** `[x]` ruta en la primera línea de
  los 6 ficheros nuevos, dominio puro, sin `print()`, secretos ni dependencias
  nuevas (sv2/sv3 ya instalaban `comun` y ya importaban `ruesma_comun.contratos`
  en `domain/`). **C3 bis** `N/A` justificado: no toca `docs/referencia/`.
- **C4** `[ ]` — **hallazgo 1**: R8 sin test `test_f043_r8_*`; el resto trazado.
  Unit tests sin red/BBDD/LLM `[x]`. MANUAL de este bloque: ninguna, bien
  declarado (T30/T31/T32 son de la feature y están en `current.md`).
- **C4 bis** `[x]`: rigor declarado, RED, cobertura `[OK]`, mutación recalculada,
  coste/mutante 239,4×1÷12 = **19,9 s** ≫ 1 s, sin «⚠ CAMPAÑA NO VÁLIDA» y «base
  rota» = 0. **RM1** `[x]` con nota: SHA medido `44707c5` (T4) ≠ HEAD `e7e0d24`,
  pero el delta toca solo `progress/` y `tasks.md`, ni un fichero del alcance.
  **RM2** `[x]`: media×W = 20,0 s frente a base 109,4 s (18 %, por encima de la
  décima parte); 12/12 muertos con `-x` lo explican y mis tres reproducciones
  (12-16 s) lo confirman. **RM3/RM5** `N/A` justificado: cero supervivientes,
  ningún equivalente declarado. **RM6** `N/A` justificado: código nuevo, no se
  retiró ninguna guarda.
- **C4 ter** `[x]` justificado: la puerta es **aviso** y de las 7 rutas listadas
  solo `albaranes-api/domain/models/albaran_models.py` es del bloque; la evidencia
  es **T30**, que `tasks.md` deja para el cierre y la **duda 6** reserva al
  humano, y con `evals/fixtures/*_indice.json` vacíos daría NO_EVALUABLE.
- **C5** `[x]` para el bloque: T1-T4 `[x]`, un commit `F-043 Tn:` cada una, árbol
  limpio, `features.json` coherente. «Todas las tareas `[x]`» es `N/A` justificado
  en review de bloque: quedan T5-T33.

## Trazabilidad requisito → test

En `services/albaranes-comun/tests/test_f043_familias.py`, con el nº de tests:
R1 `_r1_catalogo_*` (6) · R2 `_r2_catalogo|render_*` (6) · R3
`_r3_catalogo_una_familia_nueva_se_enruta_sin_tocar_servicios` (+2) · R4
`_r4_catalogo_generico_*` (2) · R5 `_r5_catalogo_*` (2) · R7 `_r7_contrato_*`
(6) · R18 `_r18_..._rama1|rama4_*` (4) · R19 `_r19_..._rama3_*` (2) · R20
`_r20_*` (4) · R21 `_r21_..._no_escribe_nada_en_la_linea` · R27
`_r27_..._rama2_*`. **R8 → 13 tests `test_f043_schema_sv2|sv3_*`, ninguno con
`r8` en el nombre.**

## Hallazgos

**1 · BLOQUEANTE — R8 no tiene test con nombre trazable.** Los 13 tests que lo
cubren se llaman `test_f043_schema_sv2|sv3_documento_*`; no existe ningún
`test_f043_r8_*` en el repositorio. Incumple R31 de la propia spec, el §Tests de
`docs/CONVENTIONS.md` y la primera casilla de C4: `grep test_f043_r8` no encuentra
la cobertura de R8, que es justo lo que la regla evita, en nivel `critico`.
**Cambiar**: prefijar `r8_` en `services/albaranes-api/tests/
test_f043_schema_sv2_documento.py` y `services/albaranes-persistencia/tests/
test_f043_schema_sv3_documento.py` (p. ej. `test_f043_r8_schema_sv2_documento_
acepta_el_bloque_clasificacion`), salvo `..._meta_sigue_sin_admitir_la_tipologia`,
que es de R9 y pide `r9_`.

**2 · BLOQUEANTE — el catálogo no es «un solo sitio» para las familias de LÍNEA.**
`ruesma_comun/contratos/contexto_linea.py:35` declara `TipoFamilia =
Literal["hormigon","mortero","combustible","alquiler_maquinaria","residuos",
"otro"]`: una segunda lista de familias de línea, en el mismo paquete, y **ya
divergente** — `familias_linea()` devuelve siete e incluye `generico` (el diseño
§1.1 le da alcance documento+línea); `TipoFamilia` tiene seis y no lo admite.
Consecuencias reales: (a) **R3 se cumple a medias** — dar de alta una familia la
enruta en fase 2 y valoración, pero una línea con ese `tipo_familia` la rechaza la
validación de `ContextoLinea`: siguen siendo dos sitios, la trampa de F-023 que
R1-R3 venían a cerrar; (b) `familia_efectiva` puede devolver un valor fuera del
dominio de `TipoFamilia` (`'generico'` por rama 4, imposible por rama 1), y las
seis puertas de sv6 de **T22** deben saberlo. **Cambiar** (mínimo, no un
refactor): 1) test de coherencia en el fichero que creó T1, p. ej.
`test_f043_r2_las_familias_de_linea_del_catalogo_coinciden_con_tipo_familia`,
comparando `set(get_args(TipoFamilia))` con `set(cat.familias_linea())`; 2)
decidir por escrito qué pasa con `generico` como familia de línea —añadirlo al
`Literal`, o quitarle el alcance de línea en el catálogo, sabiendo que entonces la
rama 4 devolverá `None` para documentos genéricos y eso cambia lo que verá T22—.
Si tocar `contexto_linea.py` excede el bloque, vale `xfail` documentado más la
decisión escrita; sin señal, no.

**3 · Menores.** (a) El `__init__.py` de T3 dice existir «para que los servicios
importen de UN solo sitio», pero T4 usa la ruta interna
`ruesma_comun.contratos.clasificacion`, y el patrón de la casa es un *shim* de
dominio (`services/*/domain/models/contexto_linea.py`): elegir uno. (b) Dos
imprecisiones del informe: en sv2 el segundo test que ya pasaba en RED no es de
no-regresión sino `..._rechaza_una_clasificacion_mal_formada`, que pasaba por
`extra_forbidden` y no por `le=100`; y el 98,7 % de §6 se mide sobre el diff
contra `dev`, que arrastra F-036. (c) Aserciones flojas o frágiles:
`_r1_catalogo_es_inmutable` usa `pytest.raises(Exception)` (usar
`FrozenInstanceError`); `_r13_familia_efectiva_no_mira_el_ler_ni_el_texto` fija la
lista exacta de imports y se rompe al añadir uno legítimo (mejor lista negra);
`_r2_catalogo_las_listas_se_derivan_no_se_declaran` reimplementa la comprensión
del código y no puede detectar un error (lo salva su test hermano). (d) `ruff`:
16 avisos en los 6 ficheros nuevos, 14 auto-corregibles.

## Las tres preguntas del encargo

**La desviación de T4 es cierta y previa a F-043.** Reproducida: el comando muere
al RECOGER `test_f002_obras_cache.py` porque `infrastructure.sigrid` de sv3 tapa
al de sv2. **No lo causa ni lo agrava el bloque A**: el mismo error sale con `-k
zzz_nada_de_nada` (157 deselected + 1 error) y el diff no toca
`infrastructure/sigrid`, ese test ni ningún `conftest.py` (no hay). Lanzar las
suites por separado es lo correcto. **Al líder**: partir en dos comandos la
verificación de T4 y de T13-T17 en `tasks.md`.

**El aviso del bloque D es aceptable como deuda declarada.** Confirmado:
`albaran-valoracion-api/domain/models/albaran_models.py:56` conserva su
`DocumentoAlbaran` sin `clasificacion`, usado solo por su `RevisionAlbaranFase2`;
sv5 no valida documentos de sv2, lee con SQL crudo, y ni T4 ni el diseño §2 lo
incluían. **Debe cerrarse en T18-T20**: si el bloque B emite `clasificacion` en
`data` y algo de sv5 llegase a validar ese documento, el `extra='forbid'` lo
rechaza entero.

**El alcance `--ficheros` es defendible, y lo probé.** Control con
`generar_mutantes` sobre lo excluido: los dos `*_models.py` de sv2/sv3 dan 2
mutantes cada uno, **todos sobre una línea preexistente** (`confianza_pct:
Optional[float] = Field(default=None, ge=0, le=100)`), ninguno sobre lo que añadió
T4; `contratos/__init__.py` da **0**. Las ~30 líneas nuevas de T4 son inmutables:
el alcance cubrió el **100 % del código nuevo mutable del bloque**. La campaña
completa sigue siendo T28.

## Cambios requeridos

1. Renombrar los tests de R8 con `r8_` en los dos ficheros de schema (h. 1).
2. Cerrar la divergencia `familias_linea()` / `TipoFamilia`: test de coherencia +
   decisión escrita sobre `generico` como familia de línea (h. 2).
3. No bloqueantes: unificar la ruta de import de `ClasificacionAlbaran`, corregir
   las dos frases del informe y endurecer `pytest.raises(Exception)` (h. 3).

## Automejora propuesta (no aplicada)

`.claude/agents/reviewer.md` manda recalcular alcance y mutantes, pero no dice
nada de **qué quedó fuera** cuando la campaña se acota con `--ficheros`. Propongo
añadir, junto a la prueba de control del cero mutantes: «si la campaña se acotó
con `--ficheros`, el reviewer ejecuta `generar_mutantes` sobre los ficheros del
diff excluidos; si sus líneas cambiadas producen mutantes, el alcance no vale».
