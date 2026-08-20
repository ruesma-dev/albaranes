<!-- progress/current.md -->
# Trabajo en curso

## F-035 · instalador que no pisa estado — `in_progress` (2026-08-20)

Rama `feature/F-035-instalador-no-pisa-estado`. **El código NO vive aquí**:
está en `arnes-base`, commits `1e67231`..`b6ac623`, versión **1.6.1**, sin
`push`. Esta rama sostiene spec, informe y rastro documental.

T1-T15 hechas. Review con **CHANGES_REQUESTED** (`progress/review_F-035.md`):
CR-1, CR-2 y CR-3 en curso en `arnes-base`; CR-4 (este cierre documental) lo
hace el líder.

**El hallazgo del review**: un mutante que anula el atajo del arnés puro
—`if ($cat -eq 'puro' -and ...)` a `if ($false)`, línea 473— **sobrevive a las
47 comprobaciones**, porque todos los casos que tocan arnés puro usan `-Forzar`
y con `-Forzar` el diálogo dice que sí igualmente. R11 y R12 quedaban sin
verificar. El producto está bien; faltaba la red. Se cierra con un caso P14 sin
`-Forzar`.

### VERIFICACIÓN MANUAL PENDIENTE (T16, la ejecuta el HUMANO)

Ya está hecha la mitad: `-SoloDiff` contra este repositorio, sin tocarlo, y
**los cuatro `[PROTEGIDO]` que salieron son exactamente los cuatro ficheros que
el incidente del 19-ago destruyó** (`docs/ARCHITECTURE.md`,
`harness/features.json`, `progress/current.md`, `progress/history.md`).

Falta repetirlo **desde una rama limpia creada desde `dev`** (en la rama de
F-034 seis de los doce diffs eran trabajo en vuelo, no diferencias reales con
el arnés, así que el número de «distintos» será menor). Comando exacto:

```powershell
cd C:\Users\pgris\PycharmProjects\arnes-base
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\albaranes" -Modo actualizar -SoloDiff
```

`-SoloDiff` **no escribe nada** (lo prueba el caso P13), así que es seguro
lanzarlo contra el repositorio real. Qué hay que comprobar: que los cuatro
protegidos siguen apareciendo como `[PROTEGIDO]` y que no se ofrece ningún
fichero de estado del proyecto.

**Aplicar de verdad la 1.6.1 a otros proyectos NO es parte de F-035**: es
decisión posterior del humano, y es lo que desbloquea actualizar `porcentajes`
y `postventa-incidencias` (1.5.2), `datamart-seg-anual` (1.5.0) y `partes`
(1.4.0).

---


## F-034 · CR-2 cerrado, a la espera de la tercera pasada (2026-08-20)

Rama `feature/F-034-mutacion-is-y-coherencia-evals`, feature `in_progress`.
**Las catorce tareas T0–T14 están en `[x]`**, incluida T12. `bash harness/init.sh`
en verde: **280 passed en 86,30 s**, `PUERTA COBERTURA: 100.0% de 12 líneas
cambiadas`.

### El CR-2 reabierto de la segunda pasada: cerrado (§T16 del informe)

De los cinco cambios requeridos del review, cuatro ya estaban cerrados y solo
quedaba **CR-2: la campaña de mutación no reproducía sus números**. El reviewer
la reejecutó y obtuvo 9 muertos / 8 supervivientes / 2 timeouts donde el
informe declaraba 18 / 1 / 0. **Tenía razón**, y su argumento no se discute: un
superviviente exige que la suite termine en verde, así que una máquina cargada
puede inventar *muertos* falsos pero nunca *supervivientes* falsos.

Lo hecho, en este orden:

1. **Tres tests nuevos** en `tests/test_mutacion_operadores.py`, con **fase RED
   pegada mutante a mutante**, que cierran los **cuatro huecos reales** de los
   ocho supervivientes (`208 [logico]`, `208 [entero]`, `220 [entero]`,
   `221 [aritmetico]`). El más grave era el cuarto: con él, el delimitador
   **derecho** de `_delimitado` no se comprobaba nunca y el mutante volvía a
   caer dentro del comentario. El test que ya existía usaba «anal**is**is», que
   el byte ANTERIOR ya rechaza; el nuevo usa «**isla**», que empieza por `is` y
   obliga a mirar el byte SIGUIENTE.
2. **Campaña rehecha** con el método documentado (ejecutor por API,
   `--workers 1`): **19 generados, 14 muertos, 4 supervivientes, 1 timeout en
   1.063,1 s**. Números pegados en `progress/mutacion_F-034.md`.
3. **Los 4 supervivientes que quedan son equivalentes**, comprobados uno a uno
   por barrido exhaustivo antes de firmarlos —incluidos los tres que el
   reviewer ya había identificado—. **Ninguno queda en `PENDIENTE`.**
4. **El quinto «hueco» no lo era**: `251 [entero]` es equivalente, con
   demostración. La línea solo se ejecuta con un token de palabra, cuyo primer
   byte es de palabra; cualquier coincidencia en `posicion + 1` estaría
   precedida por él y `_delimitado` la rechazaría igual. Saltársela no cambia
   nada.
5. **Los timeouts, medidos en vez de declarados**: `251 [aritmetico]` es un
   bucle infinito de verdad (`exit=124` a los 200 s). `207 [logico]` **no lo
   es**: muere en 48,28 s. Aquel timeout era la máquina cargada del reviewer
   (63 min de campaña frente a los 17,7 min de ésta).
6. **Corregida la frase falsa** del informe de mutación —que el gemelo de la
   línea 208 moría con `test_f034_r7`—, con lo medido: hoy muere, pero por el
   test nuevo, y antes sobrevivía.

**No se ha propagado la 1.6.0 a esta rama**, que fue el error del primer
rechazo. `harness/mutacion.py` sigue sin diff contra HEAD tras la campaña
(comprobado con `git status`).

> Esta sección sustituye a la que titulaba «F-034 · BLOQUEADA en el porte a
> `arnes-base`». **Ese bloqueo ya no existe** y la afirmación que hacía —
> «`arnes-base/harness/VERSION` sigue en 1.5.2 a propósito»— es falsa hoy.

### T12 (porte a `arnes-base`): resuelto, y cómo

El bloqueo era real —otro trabajo en vuelo y sin commitear sobre el mismo
`harness/mutacion.py`— y lo resolvió el **humano**: decidió incorporar los dos
encargos a la **misma versión**. La **1.6.0 de `arnes-base`** lleva las cuatro
piezas del encargo de «mutación fiable» **y** el porte de `is`/`is not` de
F-034. Commits allí, ya **pusheados** a `origin/main`: `860902e`, `b7dce9d`,
`febb51d` (el porte de F-034), `3ceb95b`, `89a9ba9`.

Verificado en solo lectura (hay otro agente trabajando en ese repositorio, así
que desde aquí **no se escribe** en él): `arnes-base/harness/VERSION` →
`ARNES_VERSION=1.6.0`, y `grep -c "ast.Is" arnes-base/harness/mutacion.py` → 2.

### La propagación de la 1.6.0 a `albaranes` está REVERTIDA, y es a propósito

El commit `e97f9b9` trajo la 1.6.0 de vuelta a `albaranes` **dentro de la rama
de F-034**. Eso metió ~1.000 líneas de producción ajenas en el alcance de la
feature **después** de medir sus puertas: el informe de mutación declaraba 56
líneas / 19 mutantes y la rama pasaba a tener 1.057 / 172, y la cobertura
saltaba de 12 líneas cambiadas a 392. Fue la causa de CR-1 y CR-2.

**Se ha revertido** (`163846b`). Con el revert, el alcance de la rama vuelve a
ser el que el informe declara —recomprobado, ver abajo— y la propagación se
rehará **después del merge de F-034, en su propia rama `chore/`**.

Efecto colateral consciente: `harness/VERSION` de `albaranes` dice **1.6.0**
mientras el código de `harness/` es el de la **1.5.2**. Es incoherente y **se
deja así a propósito**: lo arregla la rama de propagación, no ésta. Quien lea
esto antes de ese merge, que no lo «arregle» aquí.

### Comprobación de que el informe de mutación de F-034 sigue siendo válido

Recalculado tras el revert, cálculo puro (`harness.alcance.alcance_de_feature`
+ `harness.mutacion.generar_mutantes`, sin ejecutar ninguna suite):

```
harness/mutacion.py: 56 lineas, 19 mutantes
TOTAL: 1 fichero(s), 56 lineas, 19 mutantes
```

Coincide **exactamente** con lo que declara `progress/mutacion_F-034.md`. Y el
método documentado en su aviso al reviewer **vuelve a reproducirse**: el
`harness/mutacion.py` de esta rama no lleva comprobación de línea base (esa es
de la 1.6.0, revertida), así que ya no aborta. Muestra de 3 mutantes con
`--max-mutantes 3 --semilla 7`: `3 mutantes evaluados, 3 muertos, 0
supervivientes, 0 timeouts en 82.7 s`, árbol limpio después.

### El hallazgo del ejecutor de la raíz: ya tiene feature propia

**Las campañas de mutación sobre ficheros de la RAÍZ de este repositorio dan un
falso verde con el CLI a secas.** `ejecutor_para` manda lo que no es de ningún
servicio a `python -m pytest` **sin ruta**, y como no hay configuración de
pytest en la raíz, esa invocación recoge `services/**/tests` y **revienta en la
recolección en 0,81 s** pase lo que pase: exit 1, que el mutador cuenta como
MUERTO. Por eso la campaña buena de F-034 se lanzó pasando el ejecutor por API.

Afecta también a `progress/mutacion_F-012.md` (61 mutantes sobre `harness/`).
**No se arregla en F-034**: está fuera de su alcance y toca la puerta de todas
las features. Está dado de alta en **F-038** (`harness/features.json`, commit
`73a6b1d`), junto al coste del ciclo SDD.

## Cierre de sesión — 2026-08-19

Sesión larga (18 y 19 de agosto). `dev` al día, árbol limpio, **ninguna feature
`in_progress` ni `blocked`**. El backlog tiene **34 features, 28 abiertas**.

### Lo que se cerró en esta sesión

- **F-019 · Importe de línea** (done, APPROVED en **cuarta** pasada). El fallo
  apareció en tres capas sucesivas: el SELECT de sv5 multiplicaba por la
  cantidad un `precio_neto` que ya era el importe de línea; la precedencia de
  sv6 daba prioridad al importe sobre el unitario leído; y **sv4 recalculaba
  sin descuento y pisaba en BBDD lo que sv6 escribía bien**. La fórmula
  canónica vive ahora en `ruesma_comun/importes.py`, consumida de verdad por
  sv4 y sv6 (fijado con tests de **identidad de objeto**). Al unificarlas se
  descubrió que las dos copias **ya divergían**.
- **F-027 · Error de ×1000 kg→TN** (done, APPROVED a la primera). MAHORSA
  58826: de **468.763,40 €** a **468,76 €**. Incluye la *segunda mitad* del
  error, que se habría activado al implementar F-024.
- **Arnés 1.5.0**: `BACKLOG.md` generado desde `features.json` y regenerado por
  `init.sh`; y la sección de subagentes de `CLAUDE.md` dice ahora que delegar
  es la vía normal. Propagado a `arnes-base` (commit `3b46d55`).
- **Backlog**: altas de F-021 a F-034 desde las dos revisiones del lote.

### Lo primero al abrir la próxima sesión

**F-034 (prioridad 1)**: el mutador del arnés no muta `is` / `is not`. Cambia
la **vara de medir** de todas las features, así que va antes que cualquier otra
cosa: cada feature cerrada hasta que se arregle se mide con una campaña ciega
justo en el patrón (`x is None`) que ha causado los dos defectos más caros del
proyecto. Incluye dos incoherencias más (la puerta de evals condicionada a los
libros `.xlsx` de `evals/ground_truth/`, que existen pero **no se versionan**,
en vez de a los fixtures versionados de `evals/fixtures/` que es lo que lee el
runner; y el rastro de las campañas manuales) y **se porta a `arnes-base`**.

Después, por orden: F-024 (unidad + revisión razonada de unidades en IA2),
F-028 y F-029 (los dos casos en que el albarán **no llega a valorarse**), F-030,
F-031…

### Pendientes del humano (ninguno bloquea, pero varios llevan tiempo)

1. **Prueba local de F-002** — 4 de las 5 verificaciones siguen sin hacer (la K
   ya salió: `obras_activas=275`). Es lo que libera el **merge de F-003**, que
   está implementada y aprobada en su rama desde hace días.
2. **Reconciliar F-003 antes de arrancarla**: su R4 manda conservar el cálculo
   `cantidad × precio_neto` que **F-019 acaba de corregir**, y su R6 es la
   evolución del R10 de F-019. Igual que **F-004**, que tiene absorbidos por
   F-023 su R24 y sus R9/R10, y contradicha por F-018 su regla de «M7 solo con
   señal».
3. **Verificaciones MANUAL de F-019 (T17) y F-027 (T10)**: los números están
   fijados por test, pero los totales de documento completo solo se comprueban
   ahí.
4. **Histórico mal valorado en BBDD**: 468.763,40 € y 462.282,80 € del lote de
   MAHORSA, y los importes sin descuento anteriores a F-019. Por diseño no hay
   backfill: se sanean **revalorando desde sv4**. Falta decidir cuáles y cuándo.
5. **Derivados por IA del lote de Álvaro** (cierran F-014) y las dudas abiertas:
   precios manuscritos de Pavimarsa (¿fuente `ALBARAN` o `MANUSCRITO`?), unidad
   de Vodaland (377 u. en papel frente a MT en el Excel), partidas P4/P5, y las
   erratas del Excel (fecha del 09256 como texto `11/08/20205`, concepto del
   224964).
6. **Rellenar `evals/fixtures/inputs/`**: mientras esté vacío, la puerta de
   rutas sensibles se queda en `aviso` y ninguna feature que toque prompts
   puede demostrar nada. Ojo: F-034 arregla que la condición de la puerta
   apuntase a los libros `.xlsx` de `evals/ground_truth/` —que existen, pero
   `.gitignore` los excluye y quien clona el repositorio no los ve— en vez de a
   estos fixtures, que son los que consume `evals.runner`.
7. **Despliegue**: NADA está desplegado. Producción corre las imágenes
   `r20260724-1632` (24 de julio), es decir **sin F-002, F-019 ni F-027** — el
   ×1000 y el importe sin descuento siguen vivos en Azure. Cuando se autorice:
   secret `SIGRID_API_FUNCTION_KEY` en `ca-sv2-extraccion`, `set_models.ps1
   -Anthropic claude-opus-4-8`, y actualizar `azure-apps/albaranes.md`.
8. **Modelos en local**: sv5 tenía `ENABLE_CLAUDE=false` y `ANTHROPIC_MODEL=
   claude-opus-4-7`; sv2, `claude-sonnet-4-5`. Lo decidido es `claude-opus-4-8`
   en ambos. El humano edita los `.env` (los agentes no los tocan).

### Notas operativas de la sesión (útiles para la siguiente)

- **No lanzar suites ni campañas de mutación en paralelo**: hubo abortos por
  presión de recursos de Windows (`git init` devolviendo `0xC0000142`) y varios
  agentes colgados. En serie, y `--workers 1` si la mutación paralela protesta
  por ficheros sin versionar.
- **Worktree de `dev`** en `scratchpad/wt-dev`: permitió trabajar en el backlog
  y en el arnés mientras el árbol principal estaba ocupado con una rama de
  feature. Vale la pena mantener la costumbre.
- La API dio muchos **529 (sobrecarga)** y cuelgues de watchdog. Los agentes se
  reanudan con el trabajo intacto; si uno acumula demasiadas pasadas, sale más
  barato lanzar uno nuevo con contexto acotado.

---

## Spec escrita — F-035 (2026-08-19, rama `chore/specs-F-034-F-035`)

`specs/F-035-instalador-no-pisa-estado/` con los tres ficheros. Sin tocar
código, ni aquí ni en `arnes-base`.

**Particularidad**: el código de F-035 **no vive en este repositorio**. Vive en
`C:\Users\pgris\PycharmProjects\arnes-base` (`instalar_arnes.ps1` y
`GUIA_INSTALACION.md`, en su raíz). En `albaranes` solo se escribe la spec y el
rastro de `progress/`. El diseño lo dice en su §0, con el aviso de que las
puertas de cobertura y mutación **no tienen sujeto aquí** (0 líneas Python
cambiadas) y de que la evidencia real es la prueba de fuego en `arnes-base`.

Hallazgos de la lectura del instalador 1.5.2 que sostienen el diseño:

- No existe lista de ficheros del payload: es un barrido
  (`Get-ChildItem -Recurse`, línea 112) con **una sola** exclusión
  (`harness/gitignore.arnes`, línea 32). El `Copy-Item -Force` sin red está en
  la **línea 179**. El literal `ADAPTAR` **no aparece** en el script: la
  distinción entre arnés y estado hoy es prosa, no código.
- **Ruido CRLF medido**: de los 13 ficheros que el instalador marca como
  distintos entre el payload y `albaranes`, **8 son idénticos salvo el final de
  línea** (el payload está en LF por `.gitattributes`; `albaranes` **no tiene
  `.gitattributes`** y hace checkout en CRLF). Es causa contribuyente directa
  del incidente: 13 diffs, 8 aparentemente vacíos, invitan a pulsar `T`.
- El payload arrastra `__pycache__/`, `*.pyc` y `.pytest_cache/` (no
  versionados, pero el barrido sí los ve) y los copia al destino.
- `arnes-base` **no tiene ninguna prueba del instalador**: la carpeta `tests/`
  que se ve está **dentro del payload** y son tests de `harness/backlog.py` y
  `harness/mutacion.py` que se instalan en el destino. Tampoco hay CI. Pester
  disponible es el **3.4.0** de Windows, incompatible con la 5.x ⇒ la spec
  propone PowerShell puro sin framework.

**Decisiones abiertas que necesita validar el humano** (todas en `design.md`
§9, y todas de una línea de cambio si discrepa):

1. **D1 · `.claude/settings.json`**: la spec lo pone en categoría (b)
   *adaptado*, no en los intocables como decía `features.json`. Motivo: su
   versión del payload es configuración **mejorable** (los hooks
   `SessionStart`/`SessionEnd` llegaron a los proyectos por esa vía), no una
   plantilla vacía. Hacerlo intocable congela esas mejoras para siempre.
2. **D2 · `docs/CONVENTIONS.md`**: igual, categoría (b) y no intocable (el
   payload trae 65 líneas de convenciones reales; en `albaranes` la diferencia
   es de 5 líneas, no de 150 como en `ARCHITECTURE.md`).
3. **D3 · Vía de escape de las precondiciones**: `-IgnorarPrecondiciones`
   separado de `-Forzar`, porque el incidente ocurrió **sin** `-Forzar`.
4. **D4 · Normalización CRLF (R23)**: es lo único que no se deduce literalmente
   del enunciado de la feature. Se puede sacar sin tocar el resto del diseño.
5. **D5 · Rigor**: F-035 está declarada `estandar`, pero aquí no hay código. La
   spec propone mantenerlo y aceptar como equivalente la fase RED (la prueba
   falla contra el instalador de hoy) y una campaña de mutación **manual** de 6
   mutantes sobre el `.ps1`, con texto exacto original → mutado.
6. **Versión de `arnes-base`**: la spec propone **MINOR, no 1.5.3** —hay tres
   parámetros nuevos, cambia el comportamiento por defecto de `actualizar` y
   aparece un artefacto del que el script depende para arrancar—. Como F-034
   también sube MINOR, el número no se cablea: el implementer lee
   `arnes-base/arnes-base/harness/VERSION` al empezar y sube el siguiente
   (1.7.0 si F-034 ya cerró como 1.6.0).

**Criterio de diseño que conviene revisar**, porque es el que decide la lista
entera: un fichero es *estado del proyecto* (intocable) cuando su versión en el
payload es una **plantilla semilla** —aceptarla no aporta nunca nada y destruye
siempre—, no por llevar marcas `[ADAPTAR]`. Con ese criterio salen intocables
`harness/features.json`, `docs/ARCHITECTURE.md` y `progress/**`, y se quedan en
«pregunta con default CONSERVAR» `CLAUDE.md`, `CHECKPOINTS.md`,
`harness/init.sh`, `docs/CONVENTIONS.md`, `docs/referencia/README.md` y
`.claude/settings.json`.
