<!-- progress/review_F-045.md -->
# F-045 · Review de la CAPA 1 (T1–T12, T17, T18)

Revisión completa (pasada 1) — `feature/F-045-banco-evals-revision-manual`, HEAD
`3d01f5f`, diff `946752d..HEAD`.

## Veredicto: CHANGES_REQUESTED

Casi todo verifica: el banco pasa de 7 a 59 casos con los recuentos exactos que
declara el implementer, la suite está verde y la campaña es real y reproducible.
**Bloquean DOS de las 19 justificaciones de equivalencia: son falsas y lo
demuestro ejecutando.** En `critico` eso es un hueco de test disfrazado.

**Nivel de rigor: `critico`**, declarado en `harness/features.json`: fase RED,
cobertura ≥ 80 %, campaña completa sin muestreo, cero supervivientes
injustificados y las MANUAL listadas con su comando.

## Lo que verifiqué por mi cuenta, no leyendo el informe

- `bash harness/init.sh` → **exit 0**: 807 tests en 110 s, cobertura
  `[OK] 98,2 % de 912 líneas`, tamaño `impl 217/220`.
- **Alcance recalculado** (`harness.alcance`): 2371 líneas en 11 ficheros,
  idéntico fichero a fichero. **Mutantes recalculados** (`generar_mutantes`,
  puro): **266**, mismo reparto; seis supervivientes muestreados existen con el
  mismo operador y el mismo texto original→mutado.
- **Campaña NO reejecutada**: declara 6381 s (106 min), muy por encima de los
  60 s; RM2 coherente (media 24,0 s × 4 workers = 96 s frente a línea base
  141,6 s, con 66 % de muertos que abortan con `-x`), sin «⚠ CAMPAÑA NO VÁLIDA».
  **RM1**: SHA medido `1c3e8d7`, y `1c3e8d7..HEAD` toca **solo** `tests/` y
  `progress/`. **RM6**: por lo mismo, ningún mutante murió quitando defensa.
- `python -m evals.conversor` → 6 libros, 264 fixtures, sin hallazgos y
  `git status` limpio después (R18, R19). Barrido propio de lo versionado
  (correo, `api[_-]?key`, `secret`, `passw`, `token`, `AccountKey=`,
  `DefaultEndpointsProtocol`, GUID) → **cero hallazgos**; ningún original
  traqueado y `.gitignore` cubre `evals/inputs/`.
- Recuentos: 59 casos en `mapa_casos.json` (21 RES, 17 HOR, 10 GEN, 4 MOR, 3 FER,
  2 GRA, 1 ALQ, 1 COM), 11 no regresión + 48 defecto, fixtures 59/9/59/13/59/59.

**Criterio 1 · el cierre por reinyección: LO ACEPTO, y lo firmo.** No por el
precedente de F-043 (allí fueron 3 timeouts, no 90 veredictos), sino por tres
razones propias: (1) el conjunto de mutantes **no cambió** —recalculado hoy da
los mismos 266, porque desde la medición solo entraron tests—; (2) añadir tests
es **monótono**: mata más, nunca resucita a los 176 muertos, y matar con la suite
acotada a F-045 es MÁS exigente que con la entera; (3) **lo comprobé sobre una
copia** (worktree aparte, RM4): reinyecté cinco de los 71 declarados muertos
—`__main__`:29, escritura:295, informe:68, reparto:214, vocabulario:72— y
**mueren los cinco** (8–11 s cada uno; la base acotada son 238 tests en 9,8 s).

**Criterio 2 · las 19 equivalencias: 17 se sostienen, 2 NO.** Leídas una a una
contra el código. G1 (19, 21, 22, 24, 33): cierto, las celdas de una fila de
openpyxl comparten `.row`. G2 (15–17): cierto, `localizar_bloques` asigna los
tres campos juntos y sin encabezados levanta `ErrorEscritura` antes. G3 (31):
cierto, `_ultima_con_datos` tiene un único llamador y su valor solo se compara
con `> 0`. G4 (6): cierto, la clave la escribe antes `asignar_casos_id`. G5 (9,
18, 44, 71) y G6 (10, 45, 72): ciertos; verifiqué **ejecutando** que openpyxl
rellena las filas cortas con `read_only` True y False, de lo que dependían 44 y
45. **Caen 49 y 8.**

## Checkpoints

- **C1** [x] exit 0 y ficheros obligatorios. **C2** [x] una feature
  `in_progress`, rama correcta, estado coherente (`current.md` arrastra secciones
  antiguas, marcadas «arrastrado» a propósito).
- **C3** [x] dominio puro (`modelos`, `vocabulario`, `reparto`, `albaranes` sin
  openpyxl; `lectura`/`escritura` con import perezoso), ruta en la primera línea
  de los 10 ficheros, sin prints de debug, TODOs, secretos ni dependencias.
- **C3 bis** N/A **justificado**: no toca `docs/referencia/` (barrido hecho igual).
- **C4** [x] requisitos con test trazable, pasan los 238; T19 y T20 (MANUAL)
  listadas con su comando en `current.md`.
- **C4 bis** [ ] rigor declarado, fase RED con trazas reales (T1, T4, T7 bis,
  T11 bis, emparejado), cobertura `[OK]`, totales verificados, RM1–RM4 y RM6
  correctos… pero **RM5 falla**: dos «equivalentes» no lo son. Y «Evidencias» no
  declara el nº de workers que el bloque exige (el de mutación sí: 4).
- **C4 ter** [ ] la puerta de rutas sensibles salió `N/A (sin feature en curso
  con rama)` porque F-045 **no declara `branch`**, no porque no hubiera qué
  cotejar. A mano: el diff no toca prompts, schemas, clientes LLM ni redes de sv6
  —mismo resultado—, pero la puerta no llegó a correr.
- **C5** [ ] `tasks.md` con TODAS las tareas en `[ ]` pese a que T1–T12, T17 y
  T18 están hechas y committeadas; sin temporales sospechosos.

## Trazabilidad requisito → test (ficheros `tests/test_f045_*`)

Comprobado uno a uno: **R1–R18, R20–R22 y R24 tienen fichero propio**, y el
nombre de cada `tests/test_f045_r*.py` dice qué requisito cubre (19 ficheros,
238 tests, todos verdes). **R19 es el único sin test: lo verifiqué ejecutando el
conversor.** R23 y R25–R32 son capa 2. La política de vacíos **no confunde los
dos convenios**: comentario vacío = celda vacía en campo laxo y caso de no
regresión (48 con texto, 11 vacíos, **cero `?`**); el `?` solo nace de un valor
esperado ausente, y `INPUTS` no lleva ni uno (decisión 7).

## Cambios requeridos

1. **`mapa.py:64`, superviviente 49: NO es equivalente.** Dice «el fichero sale
   byte a byte igual con `True` y con `False`»: falso. `guardar` monta cada
   registro en el orden de `CAMPOS` (…`nombre_original`, `formato`, `gemelo_de`,
   `pestana`, `familia_documento`) y el `mapa_casos.json` versionado está en
   orden **alfabético**: con `sort_keys=False` sale otro fichero y una
   reimportación lo reescribe entero. Comprobado con `json.dumps` en las dos
   opciones sobre un registro real → `IGUALES: False`. Falta el test que fije el
   contenido escrito del mapa, que es el «mismo byte» de su propio docstring.
2. **`__main__.py:198`, superviviente 8: NO es equivalente.** Con `ejecutar=True`
   la pasada de comprobación escribe y **guarda** el libro ANTES de
   `copia_de_seguridad(ruta)`: la copia deja de ser el estado previo y se
   incumple R16, con ella la mitigación de D5. Un test de 12 líneas que compara
   los bytes de `copias/*.xlsx` con los del libro antes de importar **pasa con el
   código actual y falla con el mutante** (`AssertionError: la copia de
   IA1_extraccion.xlsx NO es el libro previo`). Ese test va al banco.
3. **`tasks.md`**: marcar `[x]` T1–T12, T17 y T18, o decir por qué no.
4. **`harness/features.json`**: declarar `branch` en F-045 como F-036…F-043; sin
   él `harness.alcance --feature F-045` aborta y la puerta de rutas sensibles se
   declara N/A por el motivo equivocado (ver C4 ter).
5. **«Evidencias»**: añadir los **4 workers** de la campaña (C4 bis los exige).
6. **Segunda desviación de §3 sin declarar**: `IA1.lineas.codigo_imputacion` sale
   `?` en las 114 líneas (`reparto.py:417-420` lo razona por D4). Defendible, pero
   §3 es normativa y deja **sin vigilar la mitad de extracción del patrón 1**: que
   conste en los «Avisos» y entre las decisiones del humano, como `tipologia`.
7. **`progress/import_F-045.md` es la salida de un `--dry-run`** («Libros
   escritos: (ninguno: en seco)», 0 copias): como evidencia de R14 documenta una
   pasada que no escribió nada. Regenerarlo con la real.

## No bloquea, pero el humano lo cierra

- **La desviación de `tipologia` es correcta: la spec es la que está mal.**
  `MAPA_TIPO_FAMILIA` (`evals/procesos/sv6_build.py:69`) está indexado por
  PESTAÑA (`"Hormigon"`, `"Residuos"`, `"Generico-Suministros"`) y
  `sv5_valoracion.py:82` lo consulta con `inputs["tipologia"]`: escribir la
  familia dejaría todos los casos en `tipo_familia='otro'`. Corregir §3.
- Siguen abiertas las tres decisiones del humano: copiar los documentos de
  entrada (los 59 salen `fila_sin_fichero`, uno a uno, como pide R21),
  `tipologia` y la contradicción de RES-004.
- **Rojos esperados bien separados** bajo «Rojos que nacen esperados»:
  `combustible`/`ferreteria`/`grava` y `minimo_1_tn`/`incremento_por_ano`.
- `mapa.py` e `informe.py` no están en §2; la rama trae un commit ajeno del
  humano (`34f3929`).

**Automejora (propuesta, no aplicada).** RM5 pide «demostración ejecutable» del
equivalente pero no exige que **pueda fallar**; las dos que caen aquí eran prosa
plausible. Propongo que en `critico` cada equivalente traiga su fragmento
ejecutado con su salida, y que el reviewer elija la muestra **entre los que
afirman igualdad de un artefacto en disco**.
