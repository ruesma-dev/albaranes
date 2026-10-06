<!-- progress/spec_F-051.md -->
# F-051 · Almacén por línea · Informe del spec-author

Fecha: 2026-09-29. Worktree `albaranes-F-051`, rama
`feature/F-051-almacen-por-linea` (desde `dev`). Spec en
`specs/F-051-almacen-por-linea/` (requirements 128/150, design 245/250,
tasks 22 tareas). Solo lectura sobre código, `azure-apps` y el repositorio
`sigrid-api`.

## 1. Cómo llega hoy un albarán aprobado a Sigrid — **no llega**

- Aprobar en sv4 (`ReviewService.approve_document` → `ColasOrchestratorClient.
  notify_document_approved`) publica `MensajeFeedback` en `q-feedback` con
  **solo** `document_id` y `approved_by`
  (`ruesma_comun/colas/mensajes.py:85`). **No hay consumidor** en el monorepo
  ni en el ecosistema: `docs/ARCHITECTURE.md`, `azure-apps/albaranes.md` §1
  («nada del pipeline escribe allí») y `dominio_negocio_albaranes.md` lo dicen,
  y el grep lo confirma. El consumidor es **F-013** (`pending`, `critico`,
  servicio nuevo). sv4 no tiene export (ni CSV ni Excel).
- Por tanto el alta en Sigrid es **externa al sistema**: presumiblemente la
  hace administración a mano leyendo el portal. **No consta en ningún
  documento**: es la decisión D6.
- **sigrid-api sí tiene escritura de dominio** (`sigrid_api.md` §7–§8, §13):
  `POST /api/sigrid/albaran` (desde contrato) y `/api/sigrid/albaran-directo`
  (sin contrato), validados contra `CTSU16/0206`; el roadmap (§13.4) prevé que
  el pipeline los llame. Leyendo su código (repo `sigrid-api`, solo lectura):
  - `sigrid/albaran`: cada `ReceivedLine` es solo `ctrpro_ide` + `cantidad`;
    `paride` se copia de la línea de contrato. **No admite override.**
  - `sigrid/albaran-directo`: `DirectLine.paride: int | None`; con `None` la
    fila se clona de la **última `dcapro` del producto** y conserva su
    `paride` — **puede ser la partida de otra obra**. No hay forma de pedir
    «sin partida». Hallazgo para el dueño de sigrid-api y para F-013.
- En Sigrid (`sigrid_tablas.md`): `dcapro.paride` → `obrparpar` (partida del
  presupuesto de la obra); desglose opcional en `dcapropar`. Una línea sin
  imputar es `paride` vacío; por la convención de índices de Sigrid (0 = sin
  referencia: `padide`, `ctride`) será **0**, no NULL — a confirmar con una
  lectura (`SELECT COUNT(*) FROM dcapro WHERE paride = 0`). **Ojo**:
  `dcapro.almide` es el almacén FÍSICO de stock (tabla `alm`) y va siempre
  relleno; el «Almacén» del humano no es eso, es no imputar partida.

## 2. Cómo se representa hoy la partida por línea

- **Merge**: `albaran_lines_merge.codigo_imputacion` = la partida impresa
  (sv2 la pide null si no aparece). sv5 la lee con SQL crudo como
  `codigo_partida_albaran`; sv4 permite editarla en la fila blanca.
- **Valoración** (sv6): `albaran_line_valuations.codigo_partida_albaran`,
  `codigo_partida_final`, `partida_action` (`VARCHAR(32)`, sin CHECK; valores
  `existing_matched`, `new_line_created`, `alm_new_line_created`,
  `no_action`, `inherited_from_base_line`). `casa_con_contrato` no existe
  como columna: es el `matched_contrato_line_id`.
- **sv4**: la fila salmón pinta la partida de la **línea de contrato** (o de
  la derivada), no `codigo_partida_final`. El input de partida abre el combo
  de **líneas de contrato** (elegir una re-concilia la fila). El combo de
  partidas HOJA de la obra (`/api/sigrid/partidas`) está en `app.js` pero sin
  enganchar. Cambiar la partida de una fila Sigrid la convierte en «Nueva»
  (`manual_override`). Los overrides se pierden al revalorar.

## 3. Qué pasa hoy con una línea SIN partida

- **sv6 le pone una**: si la IA casó una línea de contrato, `PartidaMatcher`
  devuelve `existing_matched` con **la partida de esa línea de contrato**
  (`ia_match_trusted`) — es exactamente lo que el humano no quiere. Sin match:
  `no_action`, partida NULL, derivada `nueva_no_match`.
- **Nadie la manda a revisión** por falta de partida (ni sv3, ni sv6). Solo
  sv4 la castiga en la confianza (factor partida 0).
- La valoración económica casa igual con el contrato: la partida no interviene
  en el precio de una línea base sin partida impresa.

## 4. Encaje con F-007, F-049, F-021 y F-013

- **F-007** (`spec_ready`, 2026-08-13): su mitad «almacén» (R1–R7 regla ALM
  por defecto en sv6; R15 pintar «Almacén» en sv4) **la absorbe y la supera
  F-051**: misma representación (NULL + `partida_action`, sin literal, ya
  confirmada por el humano en su D2) pero sin restringir a suministros y con
  elección manual por línea y en bloque. Su otra mitad —selector de
  **candidatas** (R8) y **memoria** obra+producto (R9–R14)— sigue viva y es
  independiente. Propuesta (D7): re-alcanzar F-007 a candidatas + memoria,
  volverla a `pending` y reescribir su spec encima de F-051. Ojo: su spec cita
  líneas de código de agosto que ya se han movido (`~938` → `~1101`).
- **F-049** (rama de F-048): cuando IA2 elija la partida de la lista de la
  obra, la lista debe admitir «sin partida» como respuesta válida y un papel
  sin partida debe seguir saliendo null: **nunca forzar una elección**. Si
  F-049 lleva la lista de partidas al combo de sv4, «Almacén» sigue siendo el
  primer ítem fijo (R13). Anotarlo en su ficha al fusionar F-048 (su ficha no
  está en `dev`).
- **F-021**: una partida vacía no es un código a validar ni a buscar entre
  candidatos: es almacén.
- **F-013**: contrato fijado en R24 — `paride` vacío para las líneas en
  almacén; exige el cambio de sigrid-api descrito en §1.

## Resumen de la spec

- **sv6**: con `codigo_partida_albaran` vacío, `almacen_sin_partida` +
  partida NULL + motivo, conservando el match y el precio (R1–R3). Revisión
  solo si la familia efectiva es destinada (`FAMILIAS_DESTINADAS`, R4–R5).
  Regresión de partida impresa, «ALM» y herencia (R6–R7). Interruptor
  `ALMACEN_SIN_PARTIDA_ENABLED` (R8). Lógica en un módulo puro nuevo.
- **sv4**: `estado_partida` ∈ {partida, almacen, sin_partida} (R10); «Almacén»
  pintado sin resucitar la partida del contrato (R11), «Sin partida» con aviso
  (R12); opción fija primera en el combo (R13); elegirla escribe
  `almacen_elegido` sin tocar importes ni convertir la fila Sigrid (R14–R15);
  botón «Almacén a todas las líneas» con confirmación, una transacción y un
  deshacer (R16–R18); guardar otros campos no rompe el almacén (R19–R20);
  confianza (R21).
- Sin DDL, sin `ruesma_comun`, sin sv2/sv3/sv5. Despliegue sv6 → sv4 (ambos
  órdenes seguros). Rutas sensibles de sv6 ⇒ pasada de evals (aviso).
- `servicios` de la ficha: `sv6-valoracion-persist`, `sv4-front` (sale sv3).

## Decisiones abiertas para el humano

1. **D1 · Representación.** Recomendado: `codigo_partida_final` NULL + marca
   en `partida_action` (`almacen_sin_partida` / `almacen_elegido`), nunca un
   literal. Y borrar el campo a mano **no** equivale a elegir almacén: queda
   «Sin partida» con aviso, para distinguir fallo de decisión.
2. **D2 · Alcance.** La petición dice «si no hay partida se deje en blanco».
   Recomendado: almacén para **toda** línea sin partida impresa, en cualquier
   familia, y revisión (no bloqueo) solo si es de familia destinada (hormigón,
   mortero, combustible, alquiler de maquinaria, residuos — los valores que
   el humano confirmó para F-007). Alternativa: solo suministros (política de
   F-007) y las demás siguen heredando la partida del contrato. Confirmar
   también si el ground truth del administrativo deja en blanco esas líneas.
3. **D3 · Botón «todas».** Recomendado: pisa también las líneas con partida
   (es lo literal), avisando del número en la confirmación y con deshacer.
   Alternativa: solo las vacías.
4. **D4 · Fila Sigrid en almacén.** Recomendado: sigue siendo Sigrid (mismo
   contrato, precio y servido; solo cambia la imputación). Hoy cambiar la
   partida la convierte en «Nueva». Depende de que en Sigrid una línea desde
   contrato pueda llevar `paride` vacío (ver D6).
5. **D5 · Revalorar.** Recomendado: el almacén elegido se pierde al pulsar
   «Valorar ahora», como cualquier override de sv4 hoy (las líneas sin partida
   impresa vuelven solas a almacén). Persistirlo en el merge es otra feature
   (sv3 DDL + sv5 + sv6).
6. **D6 · El camino a Sigrid.** Confirmar cómo se da de alta hoy el albarán
   (¿a mano, leyendo el portal?). Propuesta: añadir a la ficha de F-013 el
   contrato «almacén ⇒ `paride` vacío» y avisar al dueño de sigrid-api de que
   `albaran-directo` hereda la partida de otra `dcapro` cuando no se le pasa
   (y `sigrid/albaran` no deja cambiarla).
7. **D7 · F-007.** Recomendado: re-alcance a candidatas + memoria, vuelta a
   `pending` y nueva spec tras F-051.
8. **D8 · Propagación.** Recomendado: elegir almacén en una línea base **no**
   arrastra a sus complementarias ni sintéticas (el almacén es por línea; para
   todo el albarán está el botón). Alternativa: arrastrar, como hace sv6 con
   la herencia.

## Estado del entorno

`python -m harness.tamano --feature F-051`: dentro de los topes (128/150,
245/250). `BACKLOG.md` regenerado.

`bash harness/init.sh` en el worktree (2026-09-29): **1 KO, y es solo el
esperado** — `harness/servicios.json` declara el venv
`services/albaranes-front/.venv` y el worktree no lo tiene (no se ha creado,
por instrucción). Todo lo demás en verde: features.json válido, BACKLOG al
día, compileall limpio, **865 tests passed** (194,85 s), puerta de tamaño
dentro de topes, cobertura y rutas sensibles N/A (no hay código cambiado).

## v2 (2026-09-29) — a qué líneas va la partida

**Respuesta del humano, literal**: «si hay una partida en el documento esta
aplica a todas las lineas, si hay partidas por linea, en general aplica a las
que esten marcadas». Y, mientras se redactaba: «hasta ahora ia1 lo hace como
decimos excepto que no sabe qué hacer con línea sin partida». Lectura del
líder aplicada (lo no literal, **a confirmar**): partida única de documento ⇒
todas; partidas por línea ⇒ las que marca o agrupa; línea sin marca ⇒ vacía
(almacén); sin partida en ningún sitio ⇒ todas en almacén. Supera lo que el
v1 decía de sv2 («no se toca») en §Resumen.

### Hallazgo (a): ¿extrae hoy la IA una partida de DOCUMENTO?

- **No hay campo de cabecera**: `CabeceraAlbaran` (sv2
  `domain/models/albaran_models.py`) no tiene partida; solo
  `LineaAlbaran.codigo_imputacion`. Ningún código de sv2, sv3 ni sv6 copia
  `codigo_imputacion` entre líneas (grep: sv3 solo normaliza y compara
  proveedores en `albaran_normalizer.py` / `albaran_confidence_service.py`).
- **La propagación ya la hace IA1 por prompt** (`config/prompts.yaml`,
  `albaran_factura_es.task`, «## Código de imputación manuscrito», ~81-97):
  asociación por cercanía/raya/flecha/llave; «si solo hay un código claro en
  todo el documento, se aplica a todas las líneas»; «si no puede asociarse
  con claridad, devuelve null»; márgenes superior/inferior aplican a todo;
  «varios sin relación clara ⇒ el primero a todo». Coincide con lo que dice
  el humano. Los cuatro prompts de fase 2 incrustan el de fase 1
  (`{prompt_fase_1}`, líneas 263/487/671/809), así que IA2 ve las mismas
  reglas; los de familia piden además el mismo código para base y
  complementos.
- **El hueco** (confirmado por el humano): nada dice qué hacer con la línea
  sin partida cuando otras la tienen, y la regla del «código único» empuja a
  copiárselo aunque esté escrito junto a una sola línea.
- `config/prompts/svc2_prompt_albaran_factura_es.yaml` no lo carga ningún
  código (settings apunta a `config/prompts.yaml`): no se toca.
- **sv6 confirma el otro lado**: `partida_matcher.py:108` da a la línea sin
  partida la de la línea de contrato casada (`ia_match_trusted`). Eso lo
  corrige R1 (ya en v1).

### Hallazgo (b): dónde vive la regla — opción elegida

**Solo en el prompt de IA1, con dos frases** (design.md, «sv2»): condicionar
el código único a que no esté junto a una línea concreta, y decir que la línea
sin partida marcada sale null sin copiarle la de otra («irá a almacén»).
Descartado un campo `cabecera.codigo_imputacion` con propagación determinista
en sv3/sv6: cambia el contrato sv2 → sv3 (`extraction_models.py` estricto,
columna en el merge) → sv6, y seguiría necesitando saber si hay marcas por
línea, que es leer el papel (espíritu de ARCHITECTURE regla 14). Resultado:
**sin DDL, sin cambio de contrato, sin sv3**.

### Qué cambia en la spec

- `servicios`: + `sv2-api` (queda sv2, sv6, sv4). Descripción de la ficha con
  la decisión. Sigue `spec_ready`.
- requirements (150/150): cabecera con la regla literal y la lectura;
  sección sv2 con **R25** (línea sin partida marcada ⇒ null, sin copiar),
  **R26** (regresión de las reglas que IA1 ya cumple), **R27** (fase 2 la
  recibe por `{prompt_fase_1}`); **R28** en sv6 (una hermana con partida no
  se la pasa). Numeración v1 intacta. Vocabulario, R22 y R24 condensados.
- design (249/250): contexto de sv2, sección «dónde vive la regla», sección
  sv2 con el texto exacto de las dos frases, riesgo de conflicto con F-048
  (su rama añade texto a `prompts.yaml` en ~60 y ~144, fuera de la sección),
  evals también por sv2, docs (+ `sv2.md`), decisiones. Contexto de Sigrid y
  sv4 resumido y enlazado a §1–§3 de este informe.
- tasks (25): **T7** tests RED del prompt (R25/R27 en rojo, R26 verde) y
  **T8** el cambio del YAML; R28 en T5 (guarda, verde tras T4; su RED es
  contra `dev`); **T23** MANUAL con LLM real sobre tres albaranes (partida de
  cabecera, partida junto a una de varias líneas, sin partida); docs, mutación
  y evals ajustados. sv4 renumerado T9–T18.
- **Despliegue sv6 → sv4 → sv2**; cualquier orden es seguro, sv2 el último
  porque mueve las métricas de evals. Rollback de sv2: imagen anterior (el
  prompt no tiene interruptor).

### Decisiones

- **D1, D3, D4, D5, D7, D8**: recomendación aceptada por omisión
  (2026-09-29), **a confirmar en la PARADA 1**.
- **D2**: la parte «a qué líneas» la resuelve el humano (aplicada en sv2 y
  sv6); la parte «todas las familias, revisión solo en destinadas», aceptada
  por omisión, a confirmar.

### Preguntas que quedan para el humano

1. **D6 (explícita)**: ¿cómo se da de alta hoy el albarán aprobado en
   Sigrid? ¿Lo teclea administración a mano leyendo el portal? De eso depende
   si el almacén llega a Sigrid ya (a mano) o solo con F-013 + sigrid-api.
2. **Confirmar la lectura** con un ejemplo: albarán de tres líneas con
   «03.02» escrito solo junto a la segunda ⇒ la 1 y la 3 en almacén (hoy IA1
   pondría 03.02 en las tres por la regla del código único).
3. **D9 (nueva)**: partida en cabecera **y** otra junto a alguna línea.
   Recomendado: las marcadas llevan la suya y el resto la de cabecera; el
   prompt no se toca para esto.
4. El «en general» de la respuesta: ¿hay excepciones conocidas (p. ej.
   portes o complementos sin marca que deban seguir a su línea base)? Los
   prompts de familia ya dan a los complementos el código de su base.

### Estado del entorno

`python -m harness.tamano --feature F-051` y `python harness/backlog.py`
ejecutados: «BACKLOG.md regenerado» y «PUERTA TAMAÑO: F-051 dentro de los topes (requirements 150/150, design 249/250)». **No se ha ejecutado `bash harness/init.sh` ni
ninguna suite** por instrucción del líder (otra review corriendo en la
máquina; dos suites a la vez tumban Windows). Cambio solo de spec, ficha y
progress: ningún fichero de código tocado.

## v3 (2026-10-02) — respuestas del humano y alineación con F-053

### Decisiones del humano (2026-10-02), cerradas

1. **D6 · Alta en Sigrid.** Hoy es **MANUAL**: la teclea administración
   leyendo el portal. Por eso lo que pinta sv4 («Almacén») es lo que llega hoy a
   Sigrid. El alta automática la hará **F-053** (spec cerrada en
   `../albaranes-F-053`, rama `feature/F-053-alta-sigrid`; depende de **F-009**
   de sigrid-api): una línea de almacén se da de alta **sin partida y con
   almacén**. F-013 queda sustituida por F-053 en toda la spec.
2. **Ejemplo confirmado**: tres líneas con «03.02» escrito solo junto a la
   segunda ⇒ la 1.ª y la 3.ª van a **almacén** (no se aplica el código único a
   las tres).
3. **D9**: partida en cabecera **y** otra junto a alguna línea ⇒ las marcadas
   llevan la suya y el resto la de cabecera (la recomendada).
4. **Excepciones al «aplica a las marcadas»**: sí. Portes, complementos y
   similares sin marca siguen la partida de su línea base (como ya hacen los
   prompts de familia).

### Qué cambia en la spec

- **Prompt de IA1** (la IA decide; sin reglas deterministas, coherente con la
  regla 14 de ARCHITECTURE y la decisión del 2026-08-25): la viñeta «si solo hay
  un código claro en todo el documento, se aplica a todas las líneas» —que es la
  que hacía copiar «03.02» a las tres— se **sustituye** por cuatro viñetas con
  texto literal en `design.md` §sv2: (1) código de línea ⇒ solo sus líneas,
  aunque sea el único; (2) código de documento ⇒ las líneas sin código propio, y
  con códigos de línea además, las marcadas la suya (D9); (3) complementos sin
  código ⇒ el de su base; (4) línea sin código propio, no complemento y sin
  código de documento ⇒ null, sin copiar, con el ejemplo del punto 2 dentro del
  prompt. El resto de la sección y la línea `~147` («mismo vertido o servicio»)
  no se tocan; fase 2 lo hereda por `{prompt_fase_1}`.
- **requirements** (150/150): R25 reescrito (código de línea y ejemplo), **R29**
  (complementos) y **R30** (D9) nuevos, R26 amplía la regresión, R27 cubre R25,
  R29 y R30; **R7** ampliado: una complementaria declarada sin partida con base
  con partida hereda la de la base (ya lo hace `resolve_partida_for_
  complementaria`; se fija con test). R24 apunta a F-053/F-009. Vocabulario con
  «código de documento» y «código de línea».
- **design** (250/250): contexto con el alta manual; sección sv2 con las cuatro
  viñetas literales; sección nueva «Contrato con F-053»; riesgo «complementos no
  declarados»; contexto y «Límite» de sigrid-api resumidos (F-009 ya resuelve
  `almacen: true` y la partida nunca heredada).
- **tasks** (25): T5 añade el caso (c) en R7; T7 cubre R25–R27, R29, R30 y que
  la viñeta vieja ya no está; T8 sustituye una viñeta por cuatro; T19 docs con
  las concreciones; **T23** pasa a cinco albaranes (cabecera, «03.02» junto a la
  2.ª, D9, complemento sin marca, sin partida).
- Ficha: nota v3 en la descripción; sigue `spec_ready`, servicios sin cambio
  (sv2, sv6, sv4).

### Alineación con F-053 (leída en solo lectura)

- Coincide: F-053 define «Almacén = partida final vacía con marca de F-051» y
  manda `almacen: true` sin `partida` (R12); una vinculada en almacén conserva
  `ctrpro_ide` (coherente con R15/D4, que dejan de depender de sigrid-api: F-009
  lo admite); una línea vacía sin marca da `no_admitido` (`linea_sin_partida`),
  coherente con D1. Orden F-052 → F-051 → F-053.
- **Diferencias, anotadas en `design.md` para F-053** (no se tocan desde aquí):
  1. `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py`
     (`MARCAS_ALMACEN`) incluye `alm_acopio`, que es el `origen` de la derivada
     del ALM impreso, nunca un `partida_action`. Inofensivo; conviene quitarlo.
  2. sv9 necesitará el mismo conjunto `ACCIONES_ALMACEN` que F-051 define en sv4
     (`domain/services/almacen.py`). Para no copiarlo entre servicios, F-053 —que
     ya toca `ruesma_comun` y reconstruye todas las imágenes— debería moverlo a
     `ruesma_comun.valoracion` y que sv4 lo importe. F-051 no toca `comun`.
  3. `asignar_almacen` y los dos `POST` nuevos de sv4 entran en el bloqueo
     R25–R26 de F-053 al fusionar (su design §8 ya lo prevé).

### Preguntas que quedan

Ninguna bloqueante. Para la PARADA 1, confirmar las aceptadas por omisión
(D1, D2 en «todas las familias, revisión solo en destinadas», D3, D4, D5, D7 y
D8; D8 ya cerrada, ver abajo). Una observación sobre **D8**: con la excepción (c) del humano (los
complementos siguen a su base en el papel), cabría que elegir «Almacén» en sv4
sobre una línea base arrastrase también a sus complementarias declaradas. La
spec mantiene D8 (no arrastra; para todo el albarán está el botón): si el humano
prefiere arrastrar, es ampliar R14 a las líneas con `ref_linea_base_merge_id` de
esa base, sin DDL.

**Actualización (2026-10-02, tras el merge de `dev` 3da1d60)**: el humano
**confirma D8 tal cual**: elegir «Almacén» en sv4 sobre una línea NO arrastra a
sus complementarias; para todo el albarán está el botón. Cerrada. Siguen
**pendientes de confirmar en la PARADA 1, antes de implementar**, las aceptadas
por omisión: D1, D2 (en «todas las familias, revisión solo en destinadas»), D3,
D4, D5 y D7. Spec ajustada (design «Decisiones», cabecera de tasks y de
requirements); sin cambio de requisitos ni de tareas.

### Estado del entorno

`python -m harness.tamano --feature F-051`: «PUERTA TAMAÑO: F-051 dentro de
los topes (requirements 150/150, design 250/250)». `python harness/backlog.py`:
«BACKLOG.md regenerado». **No se ha ejecutado `bash harness/init.sh` ni
ninguna suite**, por instrucción del líder. Solo spec, ficha y progress.

## v4 (2026-10-05) — PARADA 1: todas las decisiones cerradas

### Decisiones del humano (2026-10-05), literales donde las hay

- **D1 · rehecha.** «no se asocia a partida» (almacén = sin partida, nunca un
  literal) y «en el visor cuando una línea no tenga partida que sea almacén.
  aunque eso sea realmente que la partida está vacía. negocio ya funciona así a
  mano actualmente». Sustituye a la v3, donde vaciar la partida a mano dejaba
  «Sin partida» con aviso para distinguir fallo de decisión: **ya no se
  distingue**.
- **D2.** «cualquier línea puede ir a almacén» (todas las familias). Confirmado
  por el líder con el humano: **se mantiene la revisión NO bloqueante** cuando
  una línea sin partida es de familia destinada. Verificado en código que
  `review_required` no impide aprobar (`approve_document` no lo mira).
- **D3** ok (el botón pisa también las que tienen partida, con el número en la
  confirmación y deshacer). **D4** ok (la fila Sigrid sigue Sigrid). **D5** ok (el
  almacén elegido se pierde al revalorar) **y ficha nueva F-058**. **D7** ok
  (F-007 vuelve a `pending` con nota de re-alcance). D6, D8, D9 y el ejemplo ya
  estaban cerrados.

### Qué cambia por la nueva D1 (consecuencias revisadas)

- **Estado**: almacén = línea con valoración y `codigo_partida_final` vacío,
  **tenga o no marca**. Desaparece el tercer estado `sin_partida` (R10 pasa a
  dos valores y no mira `partida_action`; R12 viejo —aviso «Sin partida»— se
  elimina).
- **Marcas (`partida_action`)**: se siguen escribiendo (`almacen_sin_partida`
  sv6, `almacen_elegido` sv4), pero **solo como trazabilidad** (quién o por
  qué). Nadie las necesita para saber si una línea es almacén. Se cae
  `ACCIONES_ALMACEN` de sv4 (y con él la propuesta de v3 de moverlo a
  `ruesma_comun` para sv9).
- **Vaciar la partida en sv4 = elegir almacén** (R12 nuevo): hoy, vaciar la
  partida de una fila Sigrid la convierte en «Nueva» (derivada
  `manual_override` con partida NULL); con v4 escribe `almacen_elegido`, no crea
  derivada y la fila sigue Sigrid (coherente con D4). Sintéticas: su edición usa
  `COALESCE` (vaciar no borra); su almacén se elige con la opción del combo o el
  botón (anotado en «NO se tocan»).
- **Visor (R11 ampliado)**: también la tabla de líneas valoradas
  (`document_detail.html:~889` y `_build_display_lines ~4283`), que hoy pinta
  `final or codigo_imputacion`: con final vacía mostraría la leída por IA1 tras
  elegir almacén. Ahora «Almacén».
- **Confianza (R21)**: con valoración la partida puntúa 1 siempre (vacía =
  almacén resuelto); sin valoración, 0 como hoy. Consecuencia: la confianza deja
  de castigar la partida vacía; el aviso en familias destinadas lo da sv6 (R4).
- **Legado**: valoraciones anteriores a F-051 con partida final vacía
  (`no_action`, sin match) salen «Almacén» en cuanto se despliega sv4, aunque sv6
  no se haya redesplegado. Es lo que pide D1.
- **Alta en Sigrid (R24 y F-053)**: toda línea con partida final vacía ⇒
  `almacen: true` sin partida. **F-053 debe cambiar** su glosario, R10 y R12:
  desaparece `no_admitido` por `linea_sin_partida`; `MARCAS_ALMACEN` de
  `medir_admisibilidad_f053.py` sobra. Anotado en design «Contrato con F-053 y
  con F-049»; la rama de F-053 no se toca desde aquí.
- **F-049, bloque C** (anotado en el mismo apartado del design): la regla de su
  columna «Origen partida» para «Sin partida → almacén» pasa a ser **valoración
  con `codigo_partida_final` vacío, sin mirar la marca**; no hay
  `ACCIONES_ALMACEN` que importar. Cierra su O4 por construcción (un complemento
  `inherited_from_base_line` con partida heredada no está vacío ⇒ no es almacén;
  test de ese caso en su T31). Su fila «Sin partida» (motivo `sin_partida` sin
  marca) desaparece; recomendado que, sin valoración, también diga «Sin partida
  → almacén». Sus §10 y §12 no cambian.

### Qué cambia en la spec

- **requirements** (150/150): cabecera v4; vocabulario (D1 literal, marcas solo
  trazabilidad, sin estado «sin partida»); R4 dice que la línea sigue en almacén
  (D2, aviso no bloqueante); R10 (dos valores), R11 (toda vista), R12 (vaciar =
  almacén), R21, R24 reescritos; trazabilidad R12 con R14.
- **design** (250/250): representación «NULL, nunca un literal», sin marca en el
  estado; `almacen.py` sin `ACCIONES_ALMACEN` y `estado_partida(final)`;
  repositorio (`_build_display_lines`, vaciar en `update_line_conciliacion`);
  confianza; plantilla `~889`; sintéticas en «NO se tocan»; SQL; sección
  «Contrato con F-053 y con F-049»; riesgos (F-058, legado, confianza); orden de
  despliegue corregido (un sv4 viejo pinta la de la casada); decisiones.
  Contexto comprimido para no pasar del tope.
- **tasks** (25, sin tareas nuevas): cabecera v4; T9 (dos valores, factor de
  confianza), T11 (+R12), T13 (sin aviso; legado y `_build_display_lines`), T14,
  T17 (sin «Sin partida»; tabla `~889`), T19 (R24 con D1 v4), T24 (vaciar).

### Fichas en `harness/features.json` (esta rama)

- **F-007** → `pending`, nota de re-alcance (D7): queda candidatas + memoria; se
  reescribe encima de F-051 y se decide junto con F-060 o fusionada.
- **F-051** → `spec_ready` (sigue), nota v4.
- **F-058** (nueva, `pending`, prioridad 2, `critico`; sv3, sv5, sv6, sv4):
  «Revalorar no pierde las partidas ni el almacén asignados a mano».
- **F-059** (nueva, `pending`, prioridad 3, `estandar`; sv4): «Etiquetas legibles
  para los motivos de revisión en sv4» (F-036 R23; review del bloque B de F-049).
- **F-060** (nueva, `pending`, prioridad 2, `critico`; sv2, sv6, sv4, comun),
  pedida por el humano en la misma pasada: «Tipología de líneas acopiables».
  Solo ficha; dice explícitamente que F-060 y la nueva spec de F-007 se deciden
  juntas o se fusionan.
- IDs F-058, F-059 y F-060 comprobados libres en todas las ramas locales y
  remotas y en los worktrees `albaranes`, `albaranes-F-049` y `albaranes-F-053`.

### Preguntas que quedan

**Ninguna.** F-051 queda `spec_ready` lista para implementar (orden F-052 →
F-051 → F-053). Para el humano, solo a título informativo (consecuencias
directas de D1, no preguntas): la confianza deja de restar por partida vacía y
las valoraciones legadas con partida vacía pasan a «Almacén» al desplegar sv4.

### Estado del entorno

`python -m harness.tamano --feature F-051`: «PUERTA TAMAÑO: F-051 dentro de
los topes (requirements 150/150, design 250/250)». `python harness/backlog.py`:
«BACKLOG.md regenerado». No se ha ejecutado `bash harness/init.sh` ni ninguna
suite: cambio solo de spec, fichas y progress; ningún fichero de código tocado.
