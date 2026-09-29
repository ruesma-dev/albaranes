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
