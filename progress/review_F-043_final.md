<!-- progress/review_F-043_final.md -->
# F-043 · review FINAL (bloques A-E) — pasada 2 y última

Revisión **completa** sobre `git diff b60a18e..HEAD` (HEAD `6c120c1`); no se juzga
el código de F-036 que arrastra `dev...HEAD`. Incluye los CR del bloque A
(`74c80be`, `d3d195b`, `2c438b4`), que no tuvieron review propia.

**Veredicto: CHANGES_REQUESTED (4 bloqueantes).** Los cuatro son baratos: un
render de prompt, un test y dos ficheros de texto. El grueso de la feature es
sólido y está verificado de primera mano. **Rigor `critico`**: C1-C5 + fase RED +
cobertura ≥ 80 % + mutación con cero supervivientes + MANUAL con comando y
resultado.

## Verificado de primera mano (no leído del informe)

- `bash harness/init.sh` **exit 0**: raíz 556 passed (167 s), `COBERTURA [OK]
  98.8%` (595/602), `TAMAÑO [OK]`, árbol limpio. init.sh dio las seis suites «por
  caché»: **las relancé una a una** — sv2 139 · sv3 169 · sv4 157 · sv5 43 · sv6
  212 · comun 118+3skip. Cuadran con los informes. Cero fallos.
- **La prohibición del humano, por `grep` sobre los seis servicios**: no queda
  `tipologia_resolver`, `override_por_cif`, `texto_contiene_hormigon/mortero` ni
  el enum `Tipologia` (solo docstrings y tests que vigilan su ausencia);
  `_derivar_tipologia_valoracion` borrado de sv5; el `tipologia` de
  `contrato_selector` sigue **huérfano**, como manda diseño §5.
- **Los guardianes de R13 son reales, medido.** En una COPIA de sv2 reinyecté la
  regla LER→residuos leyendo `contexto_linea.codigo_ler` (donde de verdad vive):
  **3 failed**, los tres del informe; y una regla por texto: cae
  `..._el_texto_de_hormigon_no_fuerza_hormigon`. No son decorativos.
- **La cadena sv2→sv6, eslabón a eslabón**: resolver → `data.clasificacion` →
  `_sanear_envelope` (solo filtra `meta`) → `build_merge_analysis` copia
  `openai.data.clasificacion` (**segundo hueco**, el que el bloque C encontró y no
  estaba en `tasks.md`; `openai=envelope`, comprobado en `save()`) →
  `campos_clasificacion_merge` → 6 columnas → `_SQL_MERGE_HEADER` → los **dos**
  sobres (`ok` y `no_contract`) → `ValuationContextDto` → `self._clasificacion` en
  `build()` → las ocho puertas. **Sin rotura.**
- **La inyección manual de mutantes es evidencia buena**: reproduje tres en copias
  del scratchpad — sv6 `:1215 ==→!=` (37 failed), sv6 `:897 !=→==` (38 failed),
  sv4 `String(32)→String(33)` (cae `..._el_orm_declara_las_mismas_longitudes…`).
- **Recálculo puro** de la única campaña: **12 mutantes**, uno a uno los del
  informe. **Falso verde reproducido**: `harness.cobertura --feature F-043` →
  `N/A` con **exit 0**; **ninguna cifra declarada está contaminada** (los seis
  bloques citan la puerta de `init.sh`, y yo mido lo mismo).
- **Barrido C3 bis** sobre lo añadido a `docs/referencia/` (correo, IPv4, GUID,
  `password|passwd|secret|token|api[_-]?key|Bearer|AccountKey|subscription|
  tenant|pwd=|sk-`): **sin coincidencias**; ningún PDF/ofimática añadido jamás
  (`git log --diff-filter=A`). Sin `print()`, TODOs ni secretos en el diff; ruta
  en la primera línea de los 49 `.py`.

## Checkpoints

- **C1** `[x]`. **C2** `[x]` (una `in_progress`, rama correcta, `current.md` solo
  esta sesión, las 11 `done` con resumen en `history.md`, comprobado por script).
- **C3** `[x]` hexagonal respetada (dominio puro; `config`→`application` es
  outer→inner, sin ciclo). Las tres trampas: columnas SOLO en la merge `[x]`;
  lectores del schema listados y tocados —sv5 SQL crudo, sv4 ORM— `[x]` pero ver
  hallazgo 8; ni unidades ni importes tocados `[x]`.
- **C3 bis** `[x]` — sí aplica (nota nueva en `dominio_negocio_albaranes.md §9`);
  barrido arriba, sin hallazgos, nada redactado.
- **C4** `[ ]` — **hallazgo 2**: R17 sin test `test_f043_r17_*`. **Hallazgo 5**:
  las MANUAL están nombradas en `current.md` pero **sin su comando exacto**. Sin
  red/BBDD/LLM `[x]`.
- **C4 bis** `[ ]` — rigor declarado `[x]`; **fase RED** `[x]` (trazas reales, dos
  reproducidas por mí); **cobertura** `[x]`. **Mutación** `[ ]`: solo existe
  `mutacion_F-043_bloque_A.md`, que cubre 2 de los ~20 ficheros de producción;
  B-E aportan inyección manual (buena, comprobada) pero **no una campaña**. Es
  **T28, del humano**: condición de cierre, no cargo contra el implementer. Del
  informe que sí existe: sin «⚠ CAMPAÑA NO VÁLIDA», «base rota» = 0,
  coste/mutante 239,4×1÷12 = **19,9 s** ≫ 1 s. **RM1** `[~]`: SHA medido
  `44707c5` ≠ HEAD y los dos ficheros del alcance **cambiaron después** (CR-3,
  anotaciones); recalculé y el conjunto de mutantes es idéntico, así que la
  campaña vale, pero T28 la rehace. **RM2** `[x]` (media×W 20,0 s vs base
  109,4 s; 12/12 muertos con `-x`). **RM3** `[x]` sin equivalentes. **RM5** `N/A`
  justificado: cero supervivientes. **RM6** `[x]` con matiz: SÍ se retiró código
  defensivo —el `ctx is None or…` de las ocho puertas— pero **no para matar un
  mutante**: es el objetivo de la feature (SS-0003967 traía `contexto_linea =
  NULL`). Verifiqué el invariante en el origen: `calcular_contenedores_residuos` y
  `regla_incremento_ler` leen todo con `getattr(..., None)` y sin volumen
  devuelven `residuos_sin_volumen_m3` con la línea a revisión. **Evidencias**
  `[x]` en los seis informes, con workers.
- **C4 ter** `[x]` justificado: la exigencia es **`aviso`** y la evidencia
  (`progress/evals_F-043.md`) **falta** porque es **T30**, se factura y la duda 6
  la reserva al humano; con los seis `evals/fixtures/*_indice.json` a `casos = 0`
  daría `NO_EVALUABLE`. Las 13 rutas en aviso son correctas.
- **C5** `[ ]` — **T28, T30, T31 y T32 sin marcar**: son del humano y no se exigen
  hechas, pero impiden `done` hoy. Las 29 restantes `[x]` con su commit
  `F-043 Tn:` (43 commits). Árbol limpio; `features.json` coherente.

## Trazabilidad requisito → test (`test_f043_rN_`)

R1 7·R2 9·R3 4·R4 3·R5 2·R6 6·R7 10·R8 14·R9 12·R10 5·R11 7·R12 11·R13 8·R14 1·
R15 9·R16 10·**R17 0**·R18 6·R19 6·R20 7·R21 2·R22 17·R23 9·R24 4·R25 8·R26 9·
R27 11·R28 6·R29 2·R30 24. R31-R34 son de proceso: se juzgan en C4 bis y C4 ter.

## R26 · ¿basta la honestidad del bloque D?

**Sí: R26 se cumple tal y como está escrito** (verificado leyendo el test). Con
clasificación de documento `residuos` y la línea **sin `tipo_familia`**, contra
CTSU24/0228: **210,00 € en 2 líneas** (120 contenedor + 90 incremento LER 170604),
y `..._el_unico_campo_que_cambia_es_la_clasificacion` aísla el efecto (720 → 210,
mismo sobre). R26 no dice contra qué línea casa IA3, así que la precondición
`casa_con=CAMBIO_6M3` no lo incumple: **R26 no está escrito de forma imposible**.

Pero R26 **no equivale a «SS-0003967 ya vale 210 € en el sistema real»**: con el
match real (la 26481, el incremento) la guarda de F-036 R15 anula el casado y el
albarán sale en **90,00 € a revisión**. El bloque D lo declara y lo fija como
test, que es lo correcto. Lectura para el humano: **F-043 entrega lo que F-036 le
pedía** —la maquinaria de residuos ya es alcanzable sin `tipo_familia`— y lo que
queda vivo es el prompt de IA3, o sea T30. Cerrar F-036 sobre esa base es
defendible; hacerlo esperando 210 € en pantalla, no.

## Los CR del bloque A (sin review previa) — `[x]` los tres

`grep test_f043_r8` da 12 nombres donde daba 0, y el de meta pasó a `r9_`.
`generico` entra en `TipoFamilia` con el test de coherencia que compara
`set(get_args(TipoFamilia))` con `set(familias_linea())` en las dos direcciones;
**efecto colateral revisado**: `familia_efectiva` puede devolver `'generico'` por
rama 4, ninguna puerta de sv6 compara contra él y
`familia_detector.normaliza_tipo_familia` ya lo trata como `None` — sin regresión.
Ruta de import única, `FrozenInstanceError`, lista negra y `ruff` 0 en los seis.

## Hallazgos

**1 · BLOQUEANTE — el prompt de fase 2 lleva `{catalogo_familias}` SIN
renderizar.** Medido, no deducido: `_render_catalogo_familias` solo se aplica en
`extract_phase_1` (`albaran_extraction_service.py:144`), y `review_phase_2:294`
mete el task de fase 1 **en crudo** vía `_build_instructions(prompt_fase_1_spec)`.
Lo que recibe IA2 en los cuatro `albaran_revision_fase2_*`:

```
… clasificar el albarán COMPLETO … en UNA de las familias de la lista siguiente…
{catalogo_familias}
- familia: el identificador EXACTO de una de las familias de la lista de arriba…
```

La lista **no está**. No es cosmético: R16 hace que la clasificación de fase 2
**prevalezca**, así que la decisión central de la feature la toma la IA que NO ha
leído el catálogo — justo las distinciones de R5 (hormigón/mortero,
residuos/alquiler de contenedor). Fallo concreto: IA2 devuelve una etiqueta fuera
de catálogo → el resolver la degrada a `generico` con confianza 0 → un documento
bien clasificado por IA1 acaba en `generico` y las puertas de residuos no se
abren. Ningún test lo ve. **Cambiar**: renderizar el catálogo también en el camino
de fase 2 (o añadir `{catalogo_familias}` a los cuatro tasks y sustituirlo en
`review_phase_2`), más un test de que las instructions de fase 2 no llevan
marcadores colgantes.

**2 · BLOQUEANTE — R17 sin test trazable.** No existe `test_f043_r17_*` (solo una
mención en un docstring de `test_f043_contexto_clasificacion.py:492`). Incumple la
primera casilla de C4 y el R31 de la spec, en `critico`; es el mismo hallazgo por
el que se rechazó la pasada 1 con R8. **Cambiar**: un `test_f043_r17_*` que fije
las dos mitades —la clasificación es del DOCUMENTO (hoy lo cubre R21 sin nombrar
R17) y la fase 2 **sigue rellenando** `contexto_linea.tipo_familia`—.

**3 · BLOQUEANTE — la verificación T31 de `tasks.md` no puede dar verde.** Dice
«revalorar SS-0003967 y ver `tipologia='residuos'` y 210,00 € en 2 líneas» con
`curl … :8003/…/value`. Falla por **dos** motivos que están en `current.md` y en
el bloque D §2.1 pero **no en `tasks.md`, que es lo que el humano ejecuta**: (a)
esa vía **no re-extrae**, el merge sigue con las seis columnas a NULL y
`tipologia` no será `residuos` — hay que volver a pasarlo por sv2
(`q-extraccion`); (b) aun re-extraído, con el match real sale **90,00 € a
revisión**. El bloque E corrigió T4 y T27 y dejó T31 intacta. **Cambiar**:
reescribir T31 con la vía real y el criterio de verde correcto.

**4 · BLOQUEANTE — `azure-apps/albaranes.md` no recoge el cambio de schema.** Ese
documento lista columna a columna `albaran_documents_merge` —incluidas las
«Añadidas por sv4 (ALTER idempotente)» y sus índices— y **no** tiene las seis
`tipologia*` ni `ix_albaran_documents_merge_tipologia`. `CLAUDE.md` (global y de
proyecto) lo exige «como parte de ese trabajo, no después», y la tabla vive en el
PostgreSQL **compartido** `psql-albaranes-rs9k2`: es el documento que otro
proyecto lee antes de tocarlo. **Cambiar**: un bullet «Añadidas por sv3 (F-043,
ALTER idempotente)» con las seis columnas, sus tipos y el índice.

**5 · Menor — C4: MANUAL sin comando exacto en `current.md`.** T28/T30/T31/T32
están nombradas; sus comandos viven solo en `tasks.md`. Copiarlos.

**6 · Menor — R27 y R24 se contradicen y la spec no lo zanja.** El código elige
R24 y lo **fija como test**: `test_f043_r24_el_prompt_ya_no_se_deriva_de_la_
familia_de_las_lineas` afirma que un envelope sin clasificación **con línea
`tipo_familia='residuos'`** usa `valuation_es`, no `valuation_residuos`. Un
albarán antiguo de residuos revalorado sin re-extraer se lee ahora con el prompt
genérico. Está declarado en `current.md` («conocido y querido»), pero
`requirements.md` sigue diciendo «exactamente como hoy». **Cambiar**: acotar R27
por escrito («…salvo la elección del prompt de valoración, que R24 retira»).

**7 · Observación** — `_motivos_de_clasificacion(None)` da `clasificacion_ausente`
y `review_required=True`: **todo documento anterior a la feature se marca a
revisión al re-persistir**. Es lo que pide R11 y las columnas quedan a NULL (R27 a
salvo), pero puede marcar en masa si se relanza `q-persistencia` sobre histórico.

**8 · Observación — orden de despliegue**: sv5 lee las seis columnas con SQL crudo
y sv4 las declara en su ORM; el DDL lo aplica sv3 al arrancar. Si sv5 o sv4
arrancan antes que sv3, sus SELECT fallan para todos los documentos. No está
escrito: cabe en la regla 14 de `ARCHITECTURE.md`.

**9 · Observación** — `{obras_activas}` tiene la misma fuga del hallazgo 1 y es
**previa** a F-043 (F-002). Medido de paso; ficha aparte, y el arreglo del 1 la
cierra.

**10 · Deuda declarada, revisada y ACEPTABLE.** (a) `DocumentoAlbaran` muerto de
sv5: confirmado que no lo importa nadie y que su `SchemaRegistry` solo sirve
`documento_valoracion`/`documento_conciliacion`; el campo evita el cepo que mató a
`meta.tipologia` y hay test que cae el día que se registre — la poda, tarea
propia. (b) `ruff` 1138: **cero nuevos** en `valuation_builder.py`, el resto
`UP045/UP006/ISC004/I001` en ficheros que ya los incumplen, medido fichero a
fichero. (c) 13 rutas sensibles en aviso: correcto, evidencia = T30.

## Qué falta para poder marcar `done`

1. Los **cuatro bloqueantes** (y, si el humano quiere, los menores 5 y 6).
2. **T28** · campaña de mutación COMPLETA, 0 supervivientes — **del humano**.
   Ojo: `--feature F-043` arrastra F-036 entera (la rama sale de F-036, no de
   `dev`). Rehacerla cubre además el `[~]` de RM1.
3. **T30** · evals con LLM real: **se factura y no está autorizado** (duda 6). Es
   la única red que dice si IA1 clasifica bien y si IA3 casa el contenedor. **El
   hallazgo 1 debería estar corregido ANTES** de gastarla.
4. **T31** · el caso real, con T31 ya reescrita (hallazgo 3).
5. **T32** · la ficha en sv4 (`http://localhost:8004`).
6. Una pasada de reviewer sobre los cuatro bloqueantes. El arnés admite dos ciclos
   y este es el segundo: **decide el humano** si los cierra sin review o abre un
   tercero.

## Automejora propuesta (no aplicada)

`CHECKPOINTS.md` no comprueba la regla de `CLAUDE.md` sobre `azure-apps/`: el
hallazgo 4 se coló en cinco bloques y dos reviews. Propongo un checkbox en **C3**:
«Si la feature cambia lo que el proyecto expone o consume (tabla, columna,
endpoint, cola, variable de entorno), el documento del proyecto en `azure-apps/`
está actualizado en esta misma rama». Genérico salvo el nombre del repositorio:
portable a `arnes-base` parametrizado.

---

*Tamaño*: **235** líneas frente al tope de 140. Recortado en dos pasadas; lo que
no se sacrifica por norma del rol es el veredicto, la razón de cada `[ ]` y los
cambios requeridos, que suman ya ~120. Lo resumido —trazas, listados de tests y
prosa— vive en los seis informes de `progress/impl_F-043_*.md` y en los commits.
