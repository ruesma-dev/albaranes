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
   Lo siguiente es la **pasada 2 del reviewer** sobre el bloque A y, con su
   APROBADO, el **BLOQUE B (T5-T12)**, el que borra `tipologia_resolver`
   (riesgo ya aceptado, abajo).

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

### El plan aprobado de F-043 · cinco implementers en serie

| # | Tareas | Qué hace |
|---|---|---|
| A | T1-T4 | El **catálogo** en `ruesma_comun` (familias, definiciones, `familia_efectiva`) y el contrato `ClasificacionAlbaran`. Base de todo lo demás |
| B | T5-T12 | **sv2**: fase 1 clasifica, fase 2 confirma, nace `clasificacion_resolver` y **se borra `tipologia_resolver`** |
| C | T13-T17 | **sv3**: que la clasificación sobreviva a `_sanear_envelope`, DDL, persistencia, umbral 60 % y motivos |
| D | T18-T23 | **sv5 y sv6**: el contexto la lleva, las puertas de familia pasan a `familia_efectiva`, y **T23 prueba SS-0003967 → 210,00 €** |
| E | T24-T27, T29, T33 | **sv4** la pinta, rutas sensibles, docs, cobertura, tamaños e `init.sh` |

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
3. **`ruff`: ~1112 avisos** de deuda previa en el monorepo.
4. **sv1-email e `infra` sin directorio de tests**: nadie comprueba lo suyo.
