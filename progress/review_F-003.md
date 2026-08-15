<!-- progress/review_F-003.md -->
# F-003 · Tanda 2 — Albaranes valorados, match estricto y coherencia · Review

- **Veredicto: APPROVED**
- Fecha: 2026-08-15. Rama revisada: `feature/F-003-valorados-match-estricto`
  (HEAD `946afa1`, 14 commits sobre `dev`).
- Worktree de la review: `scratchpad/wt-f003`. **El árbol principal
  (`C:\Users\pgris\PycharmProjects\albaranes`) no se ha tocado**: ni un
  comando, ni una lectura de escritura. Verificado `git branch --show-current`
  antes de empezar.
- **Nivel de rigor: `estandar`** (declarado en `harness/features.json`, valor
  válido). Exige: C1–C3 + C3 bis + C5, tests trazables (C4), **fase RED**,
  **cobertura del diff ≥ 80 %** y **campaña de mutación** con supervivientes
  analizados. NO exige cero supervivientes (eso es `critico`).

## Evidencia de primera mano (ejecutada por el reviewer, no leída del informe)

| Comprobación | Comando | Resultado real |
|---|---|---|
| Arnés | `bash harness/init.sh` | **ENTORNO LISTO**, `EXIT_CODE=0` |
| Cobertura | (puerta de init.sh) | `[OK] PUERTA COBERTURA: 96.6% de 268 líneas cambiadas (259/268, umbral 80%)` |
| Suite raíz | (init.sh) | `242 passed in 40.62s` |
| sv2 | `pytest tests -q` | `79 passed` |
| sv3 | `pytest tests -q` | `135 passed` |
| sv5 | `pytest tests -q` | `44 passed` |
| sv6 | `pytest tests -q` | `88 passed` |
| Evals | `python -m evals.runner --feature F-003` | `NO_EVALUABLE`, **exit 2** (el esperado con los libros vacíos) |
| Rutas sensibles | `python -m harness.rutas_sensibles --validar` | `1 verificación(es), 14 ruta(s) sensible(s) declaradas: evals (aviso)`, exit 0 |

Las cuatro suites de servicio se ejecutaron **a mano**: init.sh las dio por
buenas desde caché (`árbol sin cambios desde el último verde`), y una caché no
es evidencia. Los cuatro números coinciden exactamente con los del informe del
implementer (79 / 135 / 44 / 88).

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0 (ejecutado por mí, sin pipes ni decoración).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` (los verifica init.sh, todos `[OK]`).

### C2 — El estado es coherente
- [x] UNA sola feature `in_progress`: `['F-003']`.
- [x] Rama `feature/F-003-valorados-match-estricto`, nunca `main`/`dev`.
- [x] `progress/current.md` describe la sesión activa. Conserva un bloque
      «Estado tras el cierre de F-002» y una lista «Pendientes del humano»:
      **no son restos**, son puntos genuinamente abiertos (verificaciones
      MANUAL de F-002 sin ejecutar, push pendiente). Aceptado.
- [x] F-001, F-002, F-011, F-012 `done` con su resumen en `history.md`.

### C3 — El código respeta arquitectura y convenciones
- [x] **Hexagonal.** Los dos servicios nuevos de sv6
      (`guard_aritmetico.py`, `atributo_sustantivo_guard.py`) viven en
      `application/services/` y son **puros**: sin BBDD, sin red, sin estado
      (solo `logging` y `typing`). El DDL vive en sv3, dueño del schema.
- [x] **Primera línea con la ruta relativa** en los 16 ficheros nuevos:
      comprobado uno a uno con `head -1`. Todos correctos.
- [x] Sin `print()` de debug (grep sobre el diff: ninguno), sin secretos, sin
      dependencias nuevas.
- [x] **Las tres trampas de dominio del monorepo, verificadas:**

  1. **Lógica sobre tablas merge, nunca raw.** `grep "FROM albaran"` sobre
     `sqlalchemy_valuation_context_repository.py` da **cinco** consultas y las
     cinco son merge: `albaran_documents_merge` (×2), `albaran_lines_merge`,
     `albaran_contratos_merge`, `albaran_contrato_lines_merge`. Ninguna raw.
  2. **Columnas NUEVAS sin renames; sv5 lee con SQL crudo.** El DDL de sv3 son
     cuatro `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (`importe`,
     `descuentos_json`, `importe_total`, `importe_total_incluye_iva`), en raw
     y merge por mixin compartido. **Ningún SELECT existente se rompe**: leí el
     diff completo de sv5 y los cambios son estrictamente aditivos — a
     `_SQL_DOC_HEADER` se le suman dos columnas conservando `fecha` y
     `numero_albaran`; en `_SQL_ALBARAN_LINES` el alias `importe_albaran`
     **se mantiene** y solo cambia su fuente a
     `COALESCE(importe, <derivación de siempre>)`, con la derivación intacta
     como fallback. Filas anteriores a F-003 → `importe` NULL → COALESCE cae al
     cálculo previo → comportamiento idéntico al de hoy (R4/R14).
  3. **El guard no inventa importes.** Confirmado leyendo el código:
     `verificar_linea` devuelve **solo motivos** (`list[str]`), nunca un
     importe; el descuadre fuerza `review_required` y el importe persistido
     sigue siendo el LEÍDO. `verificar_total` devuelve
     `(motivos, exige_revision)`, tampoco toca importes. La ÚNICA inyección de
     un número es `importe_efectivo_linea_unica` (caso ORE OIL), que es
     **exactamente lo que R8 pide**, aprobado por el humano, y está acotada:
     exige total presente, `!= 0`, `incluye_iva is not False` → `return None`,
     **una sola** línea, y esa línea **sin** `importe_leido`. Con total con IVA
     no inyecta nada, que es la salvaguarda correcta (los importes de línea son
     base imponible).
- [x] **Las sintéticas conservan la herencia del descuento (decisión D4/P1 del
      humano).** `_build_synthetic_line` **no aparece modificado** en el diff.
      Y no me quedo en «no está tocado»: hay test que lo fija, y lo ejecuté —
      `test_f003_r5_la_sintetica_hereda_el_descuento_del_padre` asserta
      `descuento_albaran_aplicado == 20.0`, `importe_calculado == 40.0` (o sea,
      el descuento SÍ se aplica) y que el motivo de R5 **no** aparece.
      `3 passed`. R5 queda correctamente limitado a `from_albaran`.

### C3 bis — Documentos que entran de fuera
Aplica de forma **parcial y leve**: el diff toca `docs/referencia/`, pero
**solo modifica** un documento ya existente
(`M docs/referencia/dominio_negocio_albaranes.md`, marcas 🔶→✅ de §10.4/§10.5).
- [N/A justificado] Cabecera de origen y fecha: **no hay documento nuevo**, así
  que no hay cabecera nueva que exigir. La del documento existente no se altera.
- [x] Sin originales PDF/ofimática. Verificado que no están ahora **y que nunca
      entraron**: `git log --diff-filter=A --name-only dev..HEAD` filtrado por
      `pdf|docx|xlsx|pptx|doc|xls` → **ninguno**.
- [x] **Barrido de datos sensibles ejecutado por mí** (no leído del informe)
      sobre el diff completo, patrones: `password|passwd|secret|api[_-]?key|`
      `token|connectionstring|AccountKey|BEGIN … PRIVATE KEY|` GUID
      `[0-9a-f]{8}-…-[0-9a-f]{12}` | IPv4 | `@ruesma.es` |
      `.database.windows.net` | `blob.core.windows.net`.
      **Resultado: cero hallazgos reales.** Las coincidencias son todas ruido
      léxico: la palabra «token» del extractor de tokens dimensionales, y
      `GEMINI_API_KEY, OPENAI_API_KEY` citados como **nombres de variable
      ausentes** en un mensaje de error, sin valor alguno.

### C4 — La verificación es real
- [x] **R1–R14 con tests trazables `test_f003_rN_*`, todos en verde.** Conteo
      real sobre los ficheros `test_f003_*.py`:

| Req | Tests | Req | Tests | Req | Tests |
|---|---|---|---|---|---|
| R1 | 12 | R6 | 16 | R11 | 25 |
| R2 | 11 | R7 | 11 | R12 | 4 |
| R3 | 38 | R8 | 9 | R13 | 8 |
| R4 | 15 | R9 | 9 | R14 | 7 |
| R5 | 8 | R10 | 5 | R15 | 0 → ver abajo |

- [x] **R15 sin test: N/A JUSTIFICADO**, no un hueco. R15 pide rellenar el
      ground truth de evals, y la propia spec prevé la vía MANUAL «si aún no».
      Lo he comprobado en el sistema de ficheros, no en el informe:
      **`evals/ground_truth/` NO EXISTE**, y `evals/README.md` dice que los
      `.xlsx` **no se versionan** (ofimática) y que el flujo es
      libros Excel → `python -m evals.conversor` → fixtures. Sin los libros de
      partida, que son del humano, el implementer **no puede** generar
      fixtures: la dependencia va en ese sentido. Correctamente escalado como
      pendiente del humano en `current.md` y en el informe. Que F-011 esté
      `done` no cambia nada: F-011 construyó la maquinaria, no los libros.
- [x] **Los unit tests no tocan red ni BBDD.** Verificado por grep sobre todos
      los `test_f003_*.py` y `ayudas_f003.py`:
      `create_engine|psycopg|requests.|httpx.|socket.|urlopen` → **cero
      coincidencias**.
- [x] Verificaciones MANUAL listadas: 6 en `progress/impl_F-003.md` con su SQL
      exacto y su resultado esperado, referenciadas desde `current.md`.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "estandar"` declarado y válido (init.sh valida `rigor.json`).
- [x] **Fase RED con salida REAL pegada**, no una frase. El informe trae la
      traza de las **nueve** tareas con lógica (T1–T9), y son trazas creíbles y
      específicas, no genéricas: `extra_forbidden` de Pydantic en T1,
      `ModuleNotFoundError` en T3/T7/T8, `TypeError: … unexpected keyword
      argument 'importe_total_albaran'` en T4, `AttributeError` en T5. La de T6
      es la mejor evidencia de todas: `assert 80.0 == 100.0 ± 1.0e-04` — ese
      `80.0` **es** el bug de R5 (el descuento del albarán mordiendo un precio
      de contrato) capturado en rojo antes de arreglarlo.
- [x] **Cobertura: `[OK]` con porcentaje impreso**, 96,6 % de 268 líneas
      cambiadas, umbral 80 %.
- [x] **Mutación verificada de forma INDEPENDIENTE** (lo exige el protocolo:
      no fiarse del informe). Recalculé el alcance con `harness.alcance` y los
      mutantes con `harness.mutacion.generar_mutantes` (cálculo puro, sin
      ejecutar la suite ni escribir en disco):
  - `ref_diff` = `c9bd5df…` .. `feature/F-003-valorados-match-estricto`,
    **idéntico** al declarado en el informe.
  - **997 líneas en alcance y 87 mutantes**, contra los **997 y 87** del
    informe. Y no solo el total: **las 19 filas de la tabla por fichero
    coinciden una a una** (17, 2, 13, 18, 59, 229, 191, 139, 23, 27, 6, 6, 23,
    66, 75, 22, 22, 18, 41).
  - No hay campaña de cero mutantes que investigar (87 > 0), así que la prueba
    de control por exclusión de alcance no aplica. Los ficheros que dan 0
    mutantes son legítimos: declaraciones puras de campos Pydantic, mixins ORM
    y wiring, donde no hay operador que mutar.
- [x] **Los 3 supervivientes existen como mutantes reales** y sus análisis se
      sostienen. Los muestreé **los tres** (no dos), confirmando fichero,
      línea, operador y el texto original→mutado exactos:

  1. `atributo_sustantivo_guard.py:180` `[logico]`,
     `... is None or ...` → `and`. **Equivalente: CONFIRMADO por ejecución.**
     No me creí el argumento, lo probé: importé el módulo y
     `extraer_tokens_dimension(None)` devuelve `set()`. Con una sola línea a
     `None`, el mutante entra al cuerpo, los `getattr(None, …, None)` dan
     `None`, los tokens salen vacíos, no hay conflicto y la línea se salta
     igual. Comportamiento idéntico.
  2. `guard_aritmetico.py:94` `[comparacion]`, `<` → `<=`. **Equivalente:
     confirmado leyendo el código.** El cuerpo de la rama es `descuento = 0.0`
     y la línea previa es `descuento = _num(descuento_pct) or 0.0`; con
     `descuento == 0.0`, entrar o no entrar deja el mismo valor. No hay
     observación posible. Los bordes que sí importan (fuera de rango, 100 %)
     tienen test.
  3. `sqlalchemy_albaran_repository.py:89` `[booleano]`, `ensure_ascii=False`
     → `True`. **Equivalente: confirmado.** `_dump_descuentos` filtra a
     `valores` desde `descuentos: Optional[List[float]]` (Pydantic coacciona a
     float), y `ensure_ascii` solo altera el volcado si hay caracteres no
     ASCII, imposible en una lista de números.
- [x] **Ninguna sección en PENDIENTE.** Nivel `estandar`: 3 supervivientes
      equivalentes y analizados es suficiente; la exigencia de cero es de
      `critico` y no aplica aquí.
- [x] Sección **«Evidencias»** con los cuatro números: tests (242+79+135+44+88),
      cobertura (96,6 %), mutantes/supervivientes (87 / 3) y tiempos de suite.
- [x] Ningún punto marcado N/A sin justificación escrita.

Mención aparte, porque habla de la calidad del trabajo: la campaña empezó con
**21 supervivientes y acabó en 3**, y los 18 cerrados lo fueron **escribiendo
los tests que faltaban**, no relajando el alcance. Dos de esos huecos apuntaban
a código y se corrigieron (importe leído 0 = ausente; retirada de la rama
`0 contra 0`, redundante con el `1e-9` del denominador). Eso es usar la
mutación para lo que sirve.

### C4 ter — Verificaciones extra por rutas sensibles (APLICA)
El diff toca **8 rutas sensibles**, entre ellas los prompts de sv2 y de sv5
(IA1, IA3, IA4), tal y como señala la puerta de init.sh.
- [x] Existe el informe declarado: `progress/evals_F-003.md`.
- [x] `exige_lineas` **no se cumplen** (`MODO: completa`,
      `FASES: IA1,IA2,IA3,IA4,E2E`, `VEREDICTO: VERDE`) — comprobado leyendo el
      fichero, no el resumen del implementer. **Es lo esperado y no bloquea**:
      la exigencia declarada es `aviso` (decisión D5 de F-011) precisamente
      porque los libros de ground truth están vacíos y una pasada sin casos no
      puede dar VERDE. Sube a `bloqueo` cuando haya casos.
- [x] **Frescura: OBSERVACIÓN detectada y RESUELTA por mí.** El informe
      commiteado se generó en `fae488b` (T9), pero **`d6d90a3` volvió a tocar
      rutas sensibles después** (los servicios de sv6 de la campaña de
      mutación). Según la letra de C4 ter, ese informe estaba **obsoleto**. En
      vez de darlo por bueno, **relancé el runner yo mismo** sobre el HEAD
      real: `NO_EVALUABLE`, exit 2, y el diff del informe regenerado es de
      **dos líneas — fecha y commit**. El contenido sustantivo (cero casos,
      NO_EVALUABLE en IA3/IA4/E2E) es **idéntico**. La obsolescencia era, por
      tanto, **inmaterial**: con los libros vacíos el resultado no depende del
      commit. Queda constancia escrita, como exige la cláusula de `aviso`.
- [x] Justificación del **modo aviso con libros vacíos**: correcta y
      consistente con F-002, que se cerró con el mismo escenario.

### C5 — La sesión se cerró bien
- [x] `tasks.md`: T1–T12 en `[x]`, cada una con su commit `F-003 Tn: ...`
      (verificado en `git log dev..HEAD`: los 12 mensajes están y en orden).
- [x] **T13 en `[~]`, no en `[x]`: correcto y honesto.** Es la tarea MANUAL del
      humano (verificación local + despliegue). Marcarla `[x]` sin que el
      humano la haya hecho sería falsear el estado. Hay **precedente aceptado**:
      F-002 usó `[~]` en su T9 (`PENDIENTE-DE-DESPLIEGUE`) y se cerró
      `done`.
- [x] `features.json` refleja el estado real (`in_progress`; nadie lo ha
      marcado `done`, como debe ser hasta este veredicto).
- [x] Sin artefactos sospechosos sin trackear. **Salvedad, y es mía**: dejo
      `progress/evals_F-003.md` **modificado** en el worktree — lo regeneró mi
      propia comprobación de frescura. No es basura: es la versión **fresca**
      contra el HEAD real. Ver «Nota para el líder».

## REGLA DURA «SIN DESPLIEGUE» — cumplida
- [x] **Cero ejecución contra Azure.** Grep sobre el diff completo de
      `az login|az acr|az containerapp|deploy.ps1|build_images|docker push`:
      las **únicas** coincidencias son las frases del propio informe declarando
      que NO se ejecutó nada. Ningún comando, ningún script de despliegue
      tocado, ningún secreto nuevo.
- [x] **Las tareas de despliegue están pendientes y justificadas**: T13 en
      `[~]`, con la nota de despliegue completa (4 imágenes: sv2, sv3, sv5,
      sv6) y sus variables nuevas (los dos flags, ambos opcionales).
- [x] **Coherencia del despliegue futuro documentada donde corresponde.** El
      orden **sv3 → sv5 → sv6** consta en **tres** sitios: `design.md`
      (Riesgos), `progress/impl_F-003.md` (Nota de despliegue) y
      `progress/current.md` (Pendientes del humano). Y el motivo está bien
      explicado: sv5 empieza a hacer `SELECT importe, importe_total,
      importe_total_incluye_iva` con **SQL crudo** sobre columnas que crea sv3
      al arrancar; al revés revienta en runtime **sin aviso de compilación**.
      Es exactamente la regla 3 de `docs/ARCHITECTURE.md`.

## Cobertura requisito → test (muestra representativa)

| Req | Test que lo cubre | Servicio |
|---|---|---|
| R1 | `test_f003_r1_el_prompt_ya_no_manda_calcular_el_precio_neto` | sv2 |
| R2 | `test_f003_r2_*` (schema + retrocompatibilidad) | sv2 |
| R3 | `test_f003_r3_la_fila_deriva_el_descuento_efectivo_en_cascada` | sv3 |
| R4 | `test_f003_r4_el_importe_efectivo_prefiere_el_leido` | sv5 |
| R5 | `test_f003_r5_precio_de_contrato_no_recibe_el_descuento` | sv6 |
| R5/D4 | `test_f003_r5_la_sintetica_hereda_el_descuento_del_padre` | sv6 |
| R6 | caso ×120 en `test_f003_guard_aritmetico.py` | sv6 |
| R7 | total base → revisión / con IVA → solo aviso | sv6 |
| R8 | caso ORE OIL (y no-inyección con IVA) | sv6 |
| R9/R10 | `test_f003_prompts_match_estricto.py` sobre el YAML real | sv5 |
| R11 | 25 tests, incluidos los falsos positivos | sv6 |
| R12 | línea anulada → nueva sin precio + revisión | sv6 |
| R13 | flags a false → comportamiento previo | sv6 |
| R14 | sobres antiguos validan y se valoran | sv6 |
| R15 | — (N/A justificado: ground truth del humano) | — |

**Verificación extra de R11 por mi cuenta**, porque es la red con más riesgo de
falso positivo y no basta con que sus tests pasen. Importé el extractor y lo
probé en vivo: `0,5 mm` y `0.50 mm` producen **el mismo** token
(`Decimal('0.5')`); `0,6 mm` produce **otro**; `D-300` y `D300` producen **el
mismo** (`diametro, 3E+2`). Es decir: la red **caza** el mismatch real de
espesor y **no salta** por diferencias tipográficas, que era justo la condición
que R11 impone.

## Cambios requeridos

**Ninguno.** No hay nada que bloquee el cierre.

## Observaciones (NO bloquean; para el humano)

1. **Los evals siguen sin evaluar nada.** Es el punto ciego conocido y
   heredado: los prompts de IA1/IA3/IA4 cambian en esta feature y **ninguna
   pasada de evals los mide**, porque no hay casos. Los tests de prompt
   comprueban que el texto está en el YAML, no que el modelo se comporte. La
   red determinista R11 cubre lo numérico, pero D5 reconoce que CETOSA y
   «BOLSA DE CUÑAS» dependen **solo** del prompt. Rellenar
   `evals/ground_truth/` y subir la exigencia a `bloqueo` es la deuda más
   valiosa que tiene el repo ahora mismo.
2. **Hallazgo lateral del implementer que conviene no perder**: los clientes
   OCR opcionales de sv2 (`azure_document_intelligence_client.py`,
   `google_document_ai_client.py`, **desactivados por defecto**) siguen mapeando
   `LineAmount`/`TotalPrice` a `precio_neto` — **la misma confusión
   importe/unitario que causó el ×120**. Fuera de alcance y bien dejado
   quieto, pero si alguien los activa sin remapearlos a `importe`, reintroduce
   el bug que esta feature elimina. Merece entrada propia en `features.json`.
3. **`.gitignore` de sv6 ignora `*.example`**: su `.env.example` con los flags
   nuevos no entra en git. Mismo descuido ya detectado en sv2 en F-002. Sigue
   sin decidirse.
4. **Riesgo operativo de R7, ya previsto en el design**: albaranes con líneas
   que la extracción no capture sumarán distinto del total y caerán a revisión.
   Es el comportamiento querido, pero puede subir el volumen; el flag
   `GUARD_ARITMETICO_ENABLED` permite apagarlo si satura.

## Nota para el líder (acción concreta)

`progress/evals_F-003.md` queda **modificado sin commitear** en el worktree.
Lo regeneré yo al verificar la frescura de C4 ter; el cambio son **dos líneas**
(fecha `11:14:58Z`→`11:41:06Z`, commit `fae488b`→`946afa1`) y el veredicto sigue
siendo `NO_EVALUABLE`. **Recomiendo commitearlo** al cerrar: deja el informe de
evals apuntando al HEAD real y cierra de forma permanente la observación de
frescura. Si se prefiere el árbol limpio, `git checkout -- progress/evals_F-003.md`
lo revierte sin pérdida de información sustantiva.

## Propuesta de mejora del protocolo (NO aplicada — para que el humano decida)

**C4 ter no dice qué hacer cuando el informe está obsoleto pero la exigencia es
`aviso`.** Me ha pasado aquí: el informe era formalmente viejo y la letra del
checkpoint pedía tratarlo como no fresco, pero regenerarlo demostró que el
contenido era idéntico. Sugiero añadir a `CHECKPOINTS.md` (bloque genérico, y
por tanto **portable a `arnes-base`**):

> Si el informe de una verificación en `aviso` no es fresco, el reviewer
> **relanza el comando** en vez de limitarse a marcar el checkbox. Si el
> resultado sustantivo no cambia, se anota «obsolescencia inmaterial» con el
> diff observado y no bloquea. Si cambia, es CHANGES_REQUESTED.

Convierte un checkbox ambiguo en una acción barata y verificable, y evita el
falso positivo de rechazar una feature por un timestamp.
