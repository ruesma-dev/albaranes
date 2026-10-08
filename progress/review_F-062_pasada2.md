<!-- progress/review_F-062_pasada2.md -->
Revisión incremental desde 8583ad2 (pasada 2) · delta `8583ad2..20d840f` (c904609, d4e5691, 20d840f)

# F-062 · review pasada 2 (reviewer)

**Veredicto: APPROVED.** H1 resuelto por la opción B que eligió el humano y M1 resuelto. Quedan tres notas BAJAS que
no bloquean (abajo). Lo aprobado en la pasada 1 (`progress/review_F-062.md`) hasta `8583ad2` se da por bueno.

**Rigor:** `critico`, el declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de las líneas
cambiadas, mutación completa con 0 supervivientes y las MANUAL con su comando exacto.

**Entorno:** venvs del árbol principal sin tocar y `PYTHONPATH` apuntando a la comun del worktree. Sin `.env`,
sigrid-api, Azure ni BBDD reales. Las suites se lanzaron una detrás de otra. El RM4 se hizo sobre una copia
(`git archive HEAD`) en el scratchpad. No ejecuté git en el árbol principal. El worktree termina limpio
(`git status --porcelain` vacío antes del commit de este informe).

## H1 · opción B (decisión del humano del 2026-10-08): resuelto

- **La comparación y la regla de aplicación no cambian.** `git diff 8583ad2..HEAD -- services/` toca una sola línea
  de producción: el literal de la nota en `header_resolver_service.py:624-625` («…y nombre completo» pasa a «…y
  nombre que casa con el leído»). `_score_razon_social`, `_match_score`, `_candidato_claro` y la comun no se han
  tocado (el diffstat de `services/albaranes-comun` sale vacío).
- **La documentación dice ahora lo que hace el código.** Contrasté cada texto con `_match_score:66-80` y
  `_score_razon_social:93-114`:
  - R3 (`requirements.md:53-60`): contención, o todas las palabras de 3+ letras de cualquiera de los dos nombres
    como subcadena del otro. Es exacto.
  - D2 (`design.md:143-151`): dice lo mismo y añade los contraejemplos de H1 y la decisión del humano.
  - ARCHITECTURE regla 17 (`:312-319`): igual que R3.
  - Dominio §10.1 (`:688-695`): versión simplificada para negocio («todas las palabras de uno aparecen en el
    otro»). Es correcta: no promete el nombre completo.
  - `spec_F-062.md`: gana la subsección «Q3 revisada», con la decisión literal. Lo histórico no se reescribe.
  - Barrido de «nombre completo» en `.py`, `.md` y `.json`: ya no aparece en código, spec vigente ni docs. Solo
    queda en textos históricos (`impl_F-062.md` §1, §3/Q3 de `spec_F-062.md` con su nota de lectura) y en la
    descripción de `features.json`/`BACKLOG.md` (nota B3).
- **Hay un test que fija la semántica aceptada.**
  `test_f062_r3_opcion_b_un_unico_candidato_con_nombre_que_casa_se_aplica` está parametrizado con los cuatro casos
  de mi tabla de H1 y comprueba tres cosas: que el score es 1,0, que con el resolver real (`f062_dobles.pasada`) el
  candidato se **aplica**, y que la nota dice «es el único candidato» y «nombre que casa con el leído», con
  `review_required`. Además, `test_f062_r7_*` exige que la nota no contenga «nombre completo».
  Recalculé los cuatro scores por mi cuenta: 1,0 en todos. El control «Hormigones»/«ARIDOS» da 0,0.
- **Fase RED:** el informe (`impl_F-062_pasada2.md` §3) trae la traza real: 7 fallos y 63 tests en verde antes del
  cambio de la frase, y los 4 casos de la opción B fallan solo en la aserción de la nota. Encaja con lo esperado:
  el comportamiento ya existía y solo cambia el texto.

## M1 · comandos de las MANUAL en `current.md`: resuelto

`progress/current.md` tiene ahora la subsección «F-062 · MANUAL del humano (comandos exactos, PowerShell)»:
- **T0b:** el comando completo con el python del venv y `diag_f062.py`. Comprobé que el script existe en esa ruta.
  El comando lleva el criterio y el aviso de solo lectura (`default_transaction_read_only=on` con aborto).
- **T12:** `cd …\infra`, `. .\00_vars.ps1`, `.\deploy.ps1 -Only sv3` y `.\check_deploy.ps1`, más la vigilancia con
  A.3, su criterio y la vuelta atrás (`RED_PROVEEDOR_CORRECCION_ENABLED=false`).
- En las rutas no hay secretos: el `.env` va como marcador.

## Verificación propia (resultados reales)

- **`bash harness/init.sh` en el worktree** (con `PYTHONPATH`): da los **mismos 2 KO de entorno que en la
  pasada 1** y nada más:
  - sv3 `test_f052_t19_script_arranca_como_script_desde_otra_carpeta`;
  - la puerta de cobertura al 59,6 %, porque `-x` corta la suite de sv3.
  
  En verde: raíz **1083 passed** (491,7 s); sv1, sv2, sv4, sv5, sv6 y comun en verde (caché); puerta de tamaño OK;
  rutas sensibles N/A. **Lo verifiqué de nuevo:** el script lanzado desde otra carpeta con la comun del worktree
  sale con `rc=2` y «'12' no es un código de obra válido», que es lo que pide el test.
- **sv3** con coverage, deseleccionando solo ese test: **548 passed** (23,6 s; 544 + 4 nuevos).
  `python -m harness.cobertura --base dev --config harness/rigor.json` da **`PUERTA COBERTURA: 100.0% de 203
  líneas cambiadas cubiertas (203/203, umbral 80%, nivel critico)`**.
- La comun no cambia en el delta. En la pasada 1 dio 417 passed, 3 skipped.

## Mutación (C4 bis) y RM1–RM6

- **RM1:** el SHA medido es `f3d4174`, no HEAD. Desde entonces, en el alcance solo cambia un literal `str` de
  `header_resolver_service.py`, y `harness.mutacion` no tiene operador sobre cadenas. Recalculé
  (`harness.alcance` + `generar_mutantes`, `dev..HEAD` frente a `dev..f3d4174`): **9 ficheros, 612 líneas y 104
  mutantes en los dos**, **idénticos** campo a campo (fichero, texto de línea, columna, original, mutado y
  operador).
  En los tests solo se añaden aserciones y un test nuevo; ninguno comprobaba el literal antiguo, porque si no la
  suite estaría en rojo en HEAD. Por eso todo mutante que mataba un test en `f3d4174` sigue muerto, y no hace falta
  repetir la campaña. Lo dejo escrito como desviación justificada de la letra de RM1 («si toca el alcance, se
  repite»).
- **RM4 (tercera vía, copia en scratchpad, subconjunto `-k f062` de sv3):** muestreé tres mutantes de HEAD junto a
  lo cambiado y los tres mueren:
  - L613 `via == VIA_UNICO`→`!=`: 1 fallo;
  - L782 `score < …score_min`→`<=`: 1 fallo, porque endurecer el umbral rompe la opción B;
  - L622 `proveedor_nombre or '—'`→`and`: 1 fallo.
  
  La base de la copia da 128 passed, y la copia se restauró byte a byte (`cmp`).
- **Campaña no reejecutada: 20,5 min según el informe** (más de 60 s). Me quedo en recálculo puro, RM4 y RM1–RM6.
- **RM2:** sin cambios respecto a la pasada 1 (1227,7 s, media 11,8 s, cuadra). **RM3:** el delta no añade
  mutantes, así que no hay equivalentes nuevos. **RM5:** N/A, hay 0 supervivientes y 0 equivalentes declarados.
  **RM6:** N/A, no se quita ninguna guarda.

## Checkpoints

- **C1** init.sh exit 0: **N/A en el worktree, justificado.** Los dos únicos KO son de entorno y los verifiqué
  arriba (el venv del árbol principal carga la comun de `dev` cuando el test quita `PYTHONPATH`). La comprobación
  definitiva es T13: `init.sh` en el árbol principal tras fusionar, a cargo del líder. **Si ahí no sale en verde,
  este APPROVED no vale.** Ficheros del arnés: [x].
- **C2:** [x] una sola feature `in_progress` · [x] rama `feature/F-062-proveedor-aplicado` · [x] `current.md` al día
  (estado tras la pasada 1 y siguiente paso) · [x] history.
- **C3:** [x] hexagonal; el delta no mueve nada de capa · [x] primera línea con la ruta en los ficheros tocados ·
  [x] sin prints, secretos ni dependencias nuevas.
- **C3 bis:** N/A. Solo se edita un documento existente (dominio §10.1) y se barrió igual: sin datos sensibles.
- **C4:** [x] R1–R16 con tests en verde; R3 con la semántica de la opción B fijada por test · [x] sin red ni BBDD
  · [x] MANUAL T0b y T12 con comando exacto en `current.md` (M1).
- **C4 bis:** [x] rigor `critico` · [x] fase RED con traza (§3 del informe de la pasada 2) · [x] cobertura 100 % ·
  [x] mutación verificada (recálculo idéntico y RM4) · [x] RM1 (justificado arriba) · [x] RM2 · RM5 y RM6 N/A
  justificados · [x] 0 supervivientes · [x] Evidencias con los cuatro números.
- **C4 ter:** N/A. init.sh dice: «F-062 no toca ninguna ruta sensible declarada».
- **C5:** [x] commits `F-062 (review): …` por corrección · T0b y T12 son MANUAL del humano y T13 es del líder
  (justificados) · [x] sin temporales · [x] `features.json` coherente (`in_progress`, `critico`).

## Cobertura (requisito → tests)

Sin cambios respecto a la pasada 1, con dos añadidos:
- **R3:** gana `test_f062_r3_opcion_b_*` (4 casos).
- **R7:** `test_f062_r7_motivo_y_nota_de_la_correccion` exige «nombre que casa con el leído» y prohíbe «nombre
  completo».

## Notas BAJAS (no bloquean; para el líder)

1. **B1 y B2 de la pasada 1 siguen abiertas.** Eran recomendadas y quedaban fuera del encargo:
   - B1: se aplica el CIF normalizado en vez del literal de `prv`.
   - B2: la retirada de `proveedor_cif_no_casa` en la rama «sin candidato» está sin declarar.
   
   Propongo dejarlas anotadas en `current.md` o en una ficha nueva.
2. **B3.** La descripción de F-062 en `harness/features.json` (y por tanto en `BACKLOG.md`) sigue diciendo «nombre
   completo» en la interpretación de Q0. La ficha la mantiene el líder: conviene añadir «(revisado: opción B, score
   1,0 de F-052)» antes de cerrar.
3. **B4.** El comando de T0b apunta a `diag_f062.py` en el scratchpad de una sesión, que es efímero. `current.md`
   ya da la alternativa (el SQL íntegro en el Anexo de `spec_F-062.md`), pero si el script se pierde, el humano se
   queda sin comando ejecutable. Si T0b se va a hacer, conviene versionar el script o lanzarlo pronto.

## Automejora (propuesta, no aplicada)

**`reviewer.md`, RM1:** añadir una excepción explícita. Si el delta posterior al SHA medido solo cambia literales
de cadena o comentarios y `generar_mutantes` produce el mismo conjunto de mutantes, campo a campo, no hace falta
repetir la campaña. Para usarla, el reviewer deja escrita la comparación y hace un RM4 sobre los mutantes cercanos
al cambio. Así se evitan 20 minutos de CPU sin perder la garantía.
