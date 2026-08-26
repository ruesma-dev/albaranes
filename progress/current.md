<!-- progress/current.md -->
# Trabajo en curso

> Podado el 2026-08-26. El relato de la sesión del 25-26 de agosto —los cuatro
> bloques de F-036, sus dos ciclos de review y los hallazgos— está en
> `progress/history.md`. Aquí solo queda lo vivo.

## LO PRIMERO AL ABRIR LA PRÓXIMA SESIÓN

**Estás en `feature/F-043-clasificacion-por-ia1`**, que sale de la rama de
F-036 (no de `dev`). **56 commits locales, ninguno subido.**

**F-043 está en `spec_ready`, con la spec APROBADA y sus seis dudas resueltas
por el humano** (al final de `specs/F-043-clasificacion-por-ia1/requirements.md`).
El plan de implementación **también está aprobado**. Lo siguiente, sin volver a
preguntarlo:

1. Poner F-043 en `in_progress` (`harness/features.json`) y regenerar el backlog.
2. ~~Lanzar el implementer del **BLOQUE A (T1-T4)**~~ → **HECHO** el 2026-08-26,
   revisado y con los cambios requeridos aplicados. Informes:
   `progress/impl_F-043_bloque_A.md` + `progress/impl_F-043_bloque_A_cr.md`.
3. ~~**BLOQUE B (T5-T12)**~~ → **HECHO** el 2026-08-26. Informe:
   `progress/impl_F-043_bloque_B.md`. Nueve commits (`230fc22` … `3a10fce`),
   `init.sh` verde, 556 passed en la raíz y 139 en sv2, cobertura 98,9 %.
   **`tipologia_resolver` ya no existe**: el `grep` de T10 sale sin
   resultados. **Falta su review.**
4. ~~**BLOQUE C (T13-T17)**~~ → **HECHO** el 2026-08-26. Informe:
   `progress/impl_F-043_bloque_C.md`. Seis commits (`db205a2` … `6dd6844`),
   `init.sh` verde, 556 passed en la raíz y **169 en sv3**, cobertura 98,6 %,
   38 tests nuevos y **17 mutantes inyectados uno a uno, 0 supervivientes**.
5. ~~**BLOQUE D (T18-T23)**~~ → **HECHO** el 2026-08-26. Informe:
   `progress/impl_F-043_bloque_D.md`. Seis commits (`af0846c` … `6f2599a`),
   `init.sh` verde, 27 tests nuevos y **17 mutantes inyectados uno a uno, 0
   supervivientes**. **R26 CONSEGUIDO**: SS-0003967 vale **210,00 EUR en 2
   líneas** con la línea SIN `tipo_familia`, por la clasificación del
   DOCUMENTO. Medido con el builder real, mismo albarán, mismo contrato y
   mismo match, cambiando solo `context.clasificacion`: **720,00 € / 1 línea
   → 210,00 € / 2 líneas**.
6. ~~**BLOQUE E (T24-T27, T29, T33)**~~ → **HECHO** el 2026-08-27. Informe:
   `progress/impl_F-043_bloque_E.md`. Seis commits (`f989563` … `f3fd682`),
   `init.sh` verde, **26 tests nuevos en sv4** (131 → 157), cobertura de
   líneas cambiadas **98,8 %** y **8 mutantes inyectados uno a uno, 0
   supervivientes**. sv4 ya pinta familia, confianza y motivo; el catálogo y
   el contrato son **ruta sensible** (13 en aviso, evidencia = T30); la regla
   14 de `docs/ARCHITECTURE.md` y la nota del §9 del documento de negocio
   dejan escrito que **clasifica IA1, nunca una regla determinista**.

   **La implementación de F-043 está COMPLETA.** Lo siguiente: la **review de
   los bloques B, C, D y E** y, con su APROBADO, lo que queda es del humano —
   T28, T30, T31 y T32.

### BLOQUE E · dos cosas que el reviewer tiene que saber

- **Se corrigió la verificación de T27 en `tasks.md`.** Decía
  `python -m harness.cobertura --feature F-043`, y ese módulo no tiene
  `--feature`: argparse lo abreviaba a `--features`, no encontraba el catálogo
  y la puerta salía **`N/A` con exit code 0**. Un falso verde. Ahora usa el
  comando de `init.sh`. La de T29 sí funcionaba y no se tocó.
- **Se partió en dos la verificación de T4**, como pidió la review del bloque
  A: sv2 y sv3 comparten el paquete `infrastructure/sigrid` y en un solo
  proceso de pytest la pasada muere al RECOGER. Comprobados los dos comandos.
- Se tocó `tests/test_f011_r19_r20_declaracion.py` (el guarda del conjunto de
  rutas sensibles): las dos nuevas van en `RUTAS_ANADIDAS_DESPUES`, aparte de
  `RUTAS_DE_LA_SPEC`, que sigue siendo lo que aprobó F-011.

### BLOQUE D · lo que el bloque E y el reviewer tienen que saber

- **sv5 ya lee las seis columnas** y las entrega en `ContextoValoracion.
  clasificacion` y en `context.clasificacion` del sobre hacia sv6.
  `tipologia` NULL → `clasificacion=None`, nunca un `generico` inventado.
- **Las OCHO puertas de familia de sv6** (seis de familia, el detector de
  movimiento y el padre de la sintética) abren ya por
  `familia_efectiva(tipo_familia, clasificacion)`. Sin clasificación no se
  abre ninguna: comportamiento idéntico al de hoy (R27).
- **CAMBIO DE COMPORTAMIENTO CONOCIDO Y QUERIDO (R24).** Se borró
  `_derivar_tipologia_valoracion` de sv5: un documento **anterior** a F-043
  con líneas de residuos ya **no** se valora con `valuation_residuos` sino
  con el genérico, porque sin clasificación no hay familia de documento y
  adivinarla por las líneas es el lazo cerrado que la feature desmonta.
  Consecuencia para **T31**: revalorar SS-0003967 desde sv4 **no** basta —esa
  vía no re-extrae y el merge sigue con las seis columnas a NULL—; hay que
  volver a pasarlo por sv2 (`q-extraccion`) para que IA1 lo clasifique.
- **Lo que F-043 NO arregla y sigue vivo**: el 210,00 € exige además que IA3
  case la base contra el CONTENEDOR. Con el match REAL de SS-0003967 —la
  26481, que es el INCREMENTO— la guarda de F-036 R15 lo anula y el albarán
  sale en **90,00 € a revisión**. Es mejor que los 540,00 € valorados de más
  en silencio, pero no son los 210,00. Arreglar ese match es **T30** (evals
  del prompt), no el bloque D.

### BLOQUE C · qué existe ya (T13-T17), y qué tiene que saber el bloque D

- **La clasificación llega y se persiste.** `albaran_documents_merge` tiene
  seis columnas nuevas —`tipologia`, `tipologia_confianza_pct`,
  `tipologia_motivo`, `tipologia_origen`, `tipologia_mixta`,
  `tipologia_secundarias_json`— con DDL idempotente e índice en `tipologia`.
  **Es lo que T18 tiene que meter en el SELECT de sv5.**
- **Sin clasificación, las seis columnas quedan a NULL.** sv3 NO escribe
  `generico`/0/`ausente` para un documento anterior a la feature: si lo
  hiciera, sv5 leería una clasificación donde no la hay y R27 se rompería.
  El envelope sin bloque se marca con el motivo `clasificacion_ausente`.
- **Había un segundo hueco además de `_sanear_envelope`**, no previsto en
  `tasks.md`: `AlbaranConfidenceService.build_merge_analysis` rehace `data`
  campo a campo y tiraba la clasificación. Arreglado en T15. **Si el bloque D
  toca ese merge, que no lo deshaga.**
- **Motivos nuevos en `review_reasons_json` del documento** (los pinta sv4 en
  T24): `clasificacion_confianza_baja` (umbral `CLASIFICACION_CONFIANZA_
  MINIMA_PCT`, defecto 60), `clasificacion_mixta`, `clasificacion_ausente` y
  `linea_sin_familia_en_albaran_mixto:{n}` con el índice de la línea.
- **sv3 usa `familia_efectiva` del catálogo**, no una copia: es el mismo
  punto que T22 tiene que usar en las seis puertas de sv6 (R20).

### BLOQUE A · pasada 1 revisada y CAMBIOS REQUERIDOS APLICADOS

Review: `progress/review_F-043_bloque_A.md` (CHANGES_REQUESTED, 2 bloqueantes).
Los tres cambios están hechos —`74c80be` CR-1, `d3d195b` CR-2, `2c438b4` CR-3—
y documentados en `progress/impl_F-043_bloque_A_cr.md`. `init.sh` verde,
556 passed, cobertura 98,6 %. **Falta la pasada 2 del reviewer.**

Dos cosas que el bloque D (T22) tiene que saber:

- **`generico` es ahora familia de LÍNEA válida** (entró en el `Literal`
  `TipoFamilia` por decisión del humano del 2026-08-26, con test de coherencia
  contra `familias_linea()`). `familia_efectiva` puede devolver `'generico'`
  por su rama 4; las puertas de sv6 comparan contra `'residuos'` y
  `'hormigon'`, así que **no abre ninguna: mismo efecto que el `None` de hoy**.
- `ClasificacionAlbaran` se importa **siempre** de `ruesma_comun.contratos`
  (el reexport), nunca de `ruesma_comun.contratos.clasificacion`.

### BLOQUE A · qué existe (T1-T4)

Cuatro commits, uno por tarea (`af550a2`, `d5e5994`, `31817bf`, `44707c5`).
Lo que existe ahora y el bloque B ya puede usar:

- `ruesma_comun.contratos.familias` — catálogo único (7 familias: 4 de
  documento, 3 de solo línea), `familias_documento/linea`, `obtener`,
  `render_catalogo_markdown`, `prompt_fase2_de`, `prompt_valoracion_de` y
  `familia_efectiva`.
- `ruesma_comun.contratos.clasificacion.ClasificacionAlbaran`, reexportado en
  `ruesma_comun.contratos`.
- `DocumentoAlbaran.clasificacion` (default `None`) en sv2 y en sv3.

**Dos avisos para quien siga:**

- La verificación de T4 en `tasks.md` (`pytest services/albaranes-api/tests
  services/albaranes-persistencia/tests -k f043_schema`) **no puede funcionar**:
  sv2 y sv3 tienen ambos un paquete real `infrastructure/sigrid`, y en un solo
  proceso de pytest uno tapa al otro (falla al RECOGER
  `test_f002_obras_cache.py`, nada que ver con F-043). Es previo a esta feature.
  Se verificó lanzando las dos suites por separado, que es como lo hace
  `harness/init.sh`. Mismo cuidado en las verificaciones de T13-T17.
- La campaña de mutación con `--feature F-043` **muta también todo F-036**
  (esta rama sale de la de F-036, no de `dev`: 32 ficheros de diff contra
  `dev`). Para el bloque A se acotó con `--ficheros` a los dos módulos nuevos.
  Y muta el ÁRBOL PRINCIPAL: si se corta a medias, `python -m harness.mutacion
  --restaurar` antes de nada.

### BLOQUE B · qué existe ya (T5-T12), y qué tiene que saber el bloque C

- **La clasificación viaja en `data.clasificacion`** del envelope final, con
  los seis campos del contrato y el `origen` sellado (`ia1`/`ia2`/`ausente`).
  `meta.tipologia` sigue ahí, pero solo como espejo: el dato bueno es el de
  `data`. Es justo lo que T13 tiene que ver sobrevivir a `_sanear_envelope`.
- **Confianza 0 = hueco**, y hay dos formas de llegar a ella: la IA no
  clasificó (`origen='ausente'`, motivo `ia_sin_clasificacion`) o se inventó
  una familia (`origen='ia1'`, motivo `familia fuera de catalogo: '…'`). Las
  dos tienen que caer del lado de «a revisión» con el umbral de 60 % de T16.
- `application/services/clasificacion_resolver.py` es el único punto de sv2
  que decide algo sobre la familia, y no decide: normaliza. Sin `ler`, sin
  texto, sin CIF, con dos tests que lo vigilan.
- **El prompt de fase 2 se elige con `prompt_fase2_de(familia)`**: `None`
  significa «genérico configurado». Si alguien da de alta una familia con
  clave de prompt y olvida escribirlo en el YAML, el pipeline avisa por
  `WARNING` en vez de callarse.
- **`config/prompts.yaml` de sv2 es ahora ruta sensible tocada**: `init.sh`
  lista 8 rutas en aviso en vez de 7. Su evidencia es T30.

### El plan aprobado de F-043 · cinco implementers en serie

| # | Tareas | Qué hace |
|---|---|---|
| A | T1-T4 | El **catálogo** en `ruesma_comun` (familias, definiciones, `familia_efectiva`) y el contrato `ClasificacionAlbaran`. Base de todo lo demás |
| B | T5-T12 | **sv2**: fase 1 clasifica, fase 2 confirma, nace `clasificacion_resolver` y **se borra `tipologia_resolver`** |
| C | T13-T17 | **sv3**: que la clasificación sobreviva a `_sanear_envelope`, DDL, persistencia, umbral 60 % y motivos — **HECHO** |
| D | T18-T23 | **sv5 y sv6**: el contexto la lleva, las puertas de familia pasan a `familia_efectiva`, y **T23 prueba SS-0003967 → 210,00 €** — **HECHO** |
| E | T24-T27, T29, T33 | **sv4** la pinta, rutas sensibles, docs, cobertura, tamaños e `init.sh` — **HECHO** |

**T28** (mutación completa, sin tope), **T30** (evals), **T31** y **T32** son del
humano.

### El riesgo declarado y ACEPTADO por el humano

El bloque B **borra `tipologia_resolver` entero**. Es lo correcto —es la pieza
que crea el lazo donde una regla decide qué puede concluir la IA— pero es lo que
enruta hoy el prompt de fase 2 de **todos** los albaranes, no solo los de
residuos. Si IA1 clasifica peor que el resolver en alguna familia, se nota en
todo el pipeline y **los tests no lo verán**: eso solo lo detectan las evals con
LLM real, que son T30 y siguen sin autorizar. La red que protege este cambio es
la que se dejó para el final. Se dijo, y se aceptó.

---

## F-036 · `blocked` a la espera de F-043

**Todo su código está implementado y aprobado**: bloque A aprobado en su review,
y bloques B, C y D rechazados en la pasada 1 y **aprobados en la pasada 2**.
`init.sh` exit 0, raíz **556 passed**, cobertura de líneas cambiadas 98,2 %.

**Por qué sigue bloqueada.** Toda la maquinaria de residuos de sv6 está cerrada
tras `contexto_linea.tipo_familia == 'residuos'`, y ese campo no llega al merge.
Medido con el builder real, mismo albarán y mismo contrato: **sin el campo
540,00 €, con él 210,00 €**. Eso lo arregla F-043 (su T22/T23).

**Lo que NO se hizo, a propósito**: no se reintrodujo la regla de T11 ni se
abrieron los gates de sv6 al `codigo_ler`. Sería clasificar por LER, prohibido
por el humano el 2026-08-25.

### Para cerrarla, cuando F-043 esté

1. **T23** · `python -m harness.mutacion --feature F-036`, cero supervivientes o
   justificación escrita por superviviente (rigor `critico`). **La lanza el
   humano**: muta el árbol principal.
2. **T24** · BBDD real en SOLO LECTURA, los 7 albaranes de SALMEDINA. **Añadir
   ahí**: comprobar que ninguna línea real escribe el incremento como
   `INCREMENTO 170802` —pegado y sin la palabra `LER`—, grafía que antes casaba y
   que desde `CR-3` devuelve `None`.
3. **Evals** (`progress/evals_F-036.md`). Hoy darían `NO_EVALUABLE`: los seis
   `_indice.json` siguen con `casos = 0`.
4. **Reviewer final** contra `CHECKPOINTS.md`. Tiene que juzgar además los
   **cuatro `CR-10`..`CR-13`**, que se hicieron sin review propia porque el arnés
   admite dos ciclos y ya se habían gastado.
5. Y entonces `features.json` a `done`.

### Dos cosas de F-036 que hay que recordar

- **`ModifierContractMatcher` NO está cableado en producción** (verificado con
  grep por el reviewer): nadie lo instancia ni lee su flag. T19/R20 está bien
  hecho pero **hoy no cambia ninguna valoración**. Cablearlo es F-004.
- **Deuda de entorno**: `pytest` y `coverage` están instalados en
  `services/albaranes-front/.venv`, que desde T25 es el venv declarado de sv4 en
  `harness/servicios.json`. En otra máquina sin ellos, `init.sh` sale en rojo en
  sv4. Documentado en el README de sv4.

---

## Estado del arnés

| Repositorio | Versión | Estado |
|---|---|---|
| `arnes-base` | **1.7.2** | `main` sincronizado con `origin` |
| `albaranes` | **1.7.2** (2026-08-21) | Al día. Aplicado a mano; consta en `harness/ARNES_VERSION.md` |
| `porcentajes`, `postventa-incidencias` | 1.5.2 | sin actualizar |
| `datamart-seg-anual` | 1.5.0 | sin actualizar |
| `partes` | 1.4.0 | sin actualizar; se saltaría **siete** versiones |

### Mejoras del arnés propuestas y NO aplicadas (las levantó el reviewer)

1. **Una ficha en `blocked` apaga una puerta de contenido**: `PUERTA RUTAS
   SENSIBLES` sale `N/A` («sin feature en curso») aunque el diff sí toque rutas
   sensibles. Propuesta: que `harness.rutas_sensibles` acepte `--feature F-XXX`
   explícito, y que `CHECKPOINTS.md` mande cotejar el diff a mano ante ese `N/A`.
2. **`CHECKPOINTS.md` no contempla la review por bloques** de una feature grande:
   obliga a recorrer C1-C5 aunque el bloque revisado no pueda satisfacer C1 ni C5.
3. Si se aceptan, **son genéricas: hay que portarlas a `arnes-base`** en el mismo
   trabajo (regla de propagación).

---

## Pendientes del humano

1. **Actualizar los otros cuatro proyectos** a la 1.7.2 con el instalador.
   `partes` es donde más ficheros aparecerán «distintos»; desde F-035 el
   instalador ya no puede pisar estado.
2. **Verificaciones MANUAL arrastradas**: las 4 de F-002 (liberan el merge de
   F-003, aprobada en su rama desde hace días), y las de F-019 y F-027.
3. **Reconciliar F-003 y F-004 antes de arrancarlas** (su R4 conserva el cálculo
   que F-019 corrigió).
4. **Histórico mal valorado en BBDD**: sin backfill por diseño; se sanea
   revalorando desde sv4. Falta decidir cuáles. **Misma política confirmada para
   F-043** (decisión 5 de su spec).
5. **NADA está desplegado**: producción corre imágenes del 24 de julio, o sea
   **sin F-002, F-019 ni F-027** — y sin nada de F-036.
6. **`evals/fixtures/inputs/` vacío**: mientras lo esté, la puerta de rutas
   sensibles se queda en `aviso` y las evals dan `NO_EVALUABLE`.
7. **Retirar de la F-010 del otro proyecto** las dos reglas del arnés (hoy en la
   ficha de F-038).
8. **`progress/historico/mutacion_F-011.md` sigue invalidada** y
   **`mutacion_F-002.md` en cuarentena** (sellada en su primera pantalla el
   2026-08-25). La decisión de F-002 sigue abierta: relanzarla con la caché
   limpia, o anotar allí que su evidencia no vale.

---

## Notas operativas (valen para cualquier sesión)

- **Los `impl_`, `review_` y `evals_` de features cerradas viven en
  `progress/historico/`** (archivados el 2026-08-25: 29 ficheros, 639 KB). Las
  **campañas de mutación NO se archivan**: F-039 las vigila por ruta fija y
  moverlas pone 8 tests en rojo. El porqué, en `progress/historico/README.md`.
- **Nada en paralelo**: dos suites a la vez tumban el proceso en Windows
  (`0xC0000142`). Y **una campaña de mutación muta el árbol principal**: mientras
  corra, no lanzar `init.sh` ni tests.
- **Un agente con demasiado contexto se cuelga en bucle.** Lanzar uno **nuevo y
  acotado** —diciéndole exactamente qué leer— lo resuelve y sale más barato. Toda
  la sesión del 25-26 de agosto se hizo así, por bloques, sin un solo cuelgue.
- **Un agente que se cuelga no pierde el trabajo commiteado.** Ayuda que
  commiteen por tarea.
- **No ensuciar el árbol mientras un agente trabaja**: C5 exige árbol limpio, y
  además tus cambios pueden colarse en el commit de otro.
- **Los agentes no deben usar scripts que reescriban ficheros versionados**;
  copias en el scratchpad.
- **Cuidado con las rutas de Windows en heredocs de Python**: `\U` de `C:\Users`
  se interpreta como escape unicode y mata el script.
- **La máquina es compartida y se nota**: otra sesión corriendo triplica los
  tiempos y puede invalidar una campaña. Antes de lanzar una, comprueba que no
  hay nada más corriendo.
- **Un comando de verificación guardado en `progress/` puede caducar**: si
  guardas un comando, guarda también de qué depende.
- **El humano ejecuta él mismo** los `push`, los merges y las verificaciones
  MANUAL. Dale el comando listo para **PowerShell**, con `git -C <ruta>`, sin
  `&&` (su PowerShell 5.1 da error de parser) y diciendo cuál es el criterio de
  verde.

---

## Deudas menores que sobreviven (ninguna bloquea)

1. **RM2 solo dispara a 10×** y, con «Tiempo total» > 60 s, tampoco se reejecuta:
   un informe «solo» cinco veces demasiado rápido pasaría. Aire deliberado.
2. **Marcas `[ADAPTAR]` sin resolver** en las specs de F-034 y F-035 (aviso de
   `init.sh`, no bloquea).
3. **`ruff`: 1138 avisos** de deuda previa en el monorepo (+9 del bloque C de
   F-043: 7 `ISC004` de las sentencias DDL nuevas y 2 `UP006`, ambas reglas ya
   incumplidas por esos mismos ficheros; el detalle, en su informe §6). El
   bloque E no añadió ninguno, medido fichero a fichero.
4. **sv1-email e `infra` sin directorio de tests**: nadie comprueba lo suyo.
