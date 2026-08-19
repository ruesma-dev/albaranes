<!-- progress/current.md -->
# Trabajo en curso

## Spec escrita — F-034 (2026-08-19, rama `chore/specs-F-034-F-035`)

`specs/F-034-mutacion-is-y-coherencia-evals/` con sus tres ficheros. La spec
está **pendiente de aprobación del humano** y trae tres decisiones abiertas:

1. **D1 · ¿Se remide el histórico?** (sección propia en `requirements.md`).
   Al mutar `is`/`is not` cambia la vara de medir y los informes de las seis
   features cerradas dejan de ser comparables. Costes **medidos** por cálculo
   puro: F-027 pasa de 0 a **1** mutante (< 1 min), F-019 de 31 a **49**
   (≈ 5,8 min), F-002 +18 (1 min), F-011 +42 (**≈ 70 min**), F-012 +10
   (≈ 24 min, y su alcance incluye `harness/mutacion.py`, que ya no es el
   mismo). Opciones: **A** no remedir y solo anotar el cambio de vara; **B**
   remedir F-019 y F-027; **C** remedirlas todas (≈ 101 min de máquina).
   **Recomendación: B** — esas dos campañas hay que lanzarlas igual como
   prueba de que el cambio funciona, así que la re-medición sale casi gratis,
   y son justo las dos features cuyo defecto vivía en una guarda `is`.
2. **D2 · ¿1.5.3 o 1.6.0?** Recomendación: **1.6.0** (cambia qué se mide y
   puede volver roja una campaña verde en cualquier proyecto). Si entra
   primero, F-035 pasaría a ser 1.6.1.
3. **D3 · ¿Se corrige la descripción de F-034 en `features.json`?** Dice que
   `evals/ground_truth/` no existe, y **sí existe** (seis libros `.xlsx`, no
   versionados por `.gitignore`; `evals/conversor.py:39` los usa). El defecto
   real es que la puerta se condiciona a un artefacto invisible en vez de a
   los fixtures versionados de `evals/fixtures/`, que es lo que lee el runner.
   Recomendación: corregir esa frase (`BACKLOG.md` se regenera solo).

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
proyecto. Incluye dos incoherencias más (el `evals/ground_truth/` inexistente y
el rastro de las campañas manuales) y **se porta a `arnes-base`**.

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
   puede demostrar nada. Ojo: F-034 arregla que la documentación diga
   `evals/ground_truth/`, que no existe.
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
