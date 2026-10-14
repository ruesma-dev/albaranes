Revisión incremental desde `3257b60` (v8, Bloque H, pasada 2): `3257b60..40eaf41`. Lo aprobado en la pasada 1 queda dado por bueno.
<!-- progress/review_F-053_v8_p2.md -->
# Review F-053 v8 · Bloque H · pasada 2 · reviewer, 2026-10-14

## Veredicto: APPROVED

Los cuatro cambios de `progress/review_F-053_v8.md` están resueltos y los he verificado ejecutando, no leyendo:
campaña de la herramienta 66/66 sobre el commit que dice y sin cambios de código después; tabla manual reproducible
(las 64 sustituciones del anexo existen una sola vez en HEAD); el 38 ya es equivalente tras recortar `DEFAULT_REVIEWER`;
los equivalentes 38 y 50 traen demostración ejecutable con control.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige RED, cobertura ≥ 80 %, campaña de la herramienta con 0
supervivientes sin test o sin justificación aceptada por el humano, RM5 y MANUAL con su comando.

## Delta revisado

Código: solo `services/albaranes-front/interface_adapters/web/app.py:471-473` (`return (settings.default_reviewer or
"").strip() or None`). Tests: `test_f053_r49_revisor.py` (+6 casos), `test_f053_v8_supervivientes_arnes.py` y
`test_f053_v8_equivalentes.py` (nuevos). Informes: `impl_F-053_v8.md`, `mutacion_F-053_v8.md`,
`mutacion_F-053_v8_arnes.md` e `inventario_mutacion_F-039.md`. sv9 no cambia en esta pasada.

## Lo que he ejecutado (en una COPIA del scratchpad, `git archive HEAD`; el árbol queda limpio)

- **`bash harness/init.sh`** en el worktree, tal cual: `ENTORNO LISTO`, exit 0. Raíz **1083 passed** (466 s);
  `PUERTA COBERTURA: 100.0% de 129 líneas (critico)`; `PUERTA TAMAÑO` 150/150 y 250/250. sv4 salió por caché, así
  que lo ejecuté **entero y sin caché: 1366 passed** (167 s). sv9 sin cambios desde la pasada 1 (621 passed míos).
  Nunca dos suites a la vez.
- **RED del cambio 3**: con `return settings.default_reviewer` y los tests de HEAD, `test_f053_r49_revisor.py` da
  **6 failed, 17 passed** (`assert [' revisor-local '] == ['revisor-local']`, listado y ficha × `None`/`""`/`"   "`).
  Coincide con el informe.
- **RED de los 3 supervivientes de la primera campaña**, cada mutante aplicado y `test_f053_v8_supervivientes_arnes.py`:
  `review_models.py:1456` `False→True` ⇒ **2 failed**; `app.py:473` `or None→and None` ⇒ **4 failed**;
  `app.py:1771` `include_in_schema=False→True` ⇒ **1 failed** (la ruta sale en el OpenAPI). Además
  `(default_reviewer or "")→(… and "")` ⇒ 3 failed. Coincide con el informe.
- **Mutante 38 con el código nuevo** (`if propuesto:`): `test_f053_r49_revisor.py` + supervivientes + equivalentes
  ⇒ **33 passed**. Ya no hay diferencia observable: con `"   "` el mutante devuelve `""`, y el servicio, construido
  con el mismo `settings.default_reviewer` (`app.py:380-382`), lo trata como falso y pone el defecto recortado
  (`review_service.py:101`, `:195-196`, `:319`) en el merge y en el mensaje. Equivalente de verdad.
- **Equivalentes (RM5)**: `test_f053_v8_equivalentes.py` pasa en HEAD (2 passed). Muestra elegida: **el 38**, reproducido
  aparte como arriba. El 50 lo razoné además: `ConfigAltaSigrid.activa` es `desde is not None` y la línea 46 ya
  devuelve `False` con `config.desde is None`; `_instante` no lanza con `None`, `""` ni texto ilegible (están en el
  dominio del test). Los dos controles (`return propuesto` sin recortar; `<`→`<=`) dan `> 0`.
- **Muestra de la tabla manual**, al pie de la letra: **fila 39** (`return propuesto.strip()`→`return propuesto`)
  ⇒ 1 fallo (`test_f053_r49_listado[None-  pepe  -pepe]`), la tabla dice 1; **fila 11** (`"f053-usuario", 2)`→`1)`)
  ⇒ 1 fallo propio (`test_f053_r47_cliente_buscar_usuario_cuerpo_exacto_y_cod_de_sigrid`), la tabla dice 1. Los 4
  fallos de `test_f053_r47_config_infra_*` en la copia son del montaje (la copia no lleva `infra/`) y salen igual sin
  mutante. **Anexo**: script propio sobre las 64 líneas JSON ⇒ ids 1–64, cada `orig` aparece **exactamente una vez** en
  su fichero de HEAD y ninguna fila tiene `orig == mut`. Ya no hay «…» en la tabla.
- **Recálculo puro** (`harness.alcance` + `generar_mutantes`): `dcd25cc..feature/F-053-alta-sigrid`, **16 ficheros,
  334 líneas, 66 mutantes**, igual que el informe. Los 3 supervivientes de la primera campaña existen con el mismo
  operador y el mismo texto original→mutado. De 64 (pasada 1) a 66: los dos `logico` nuevos de `app.py:473`.
- **Campaña no reejecutada**: 2416,6 s según el informe (> 60 s). Me quedo en el recálculo, las RED de arriba y RM1–RM6.

## Reglas de campaña

- **RM1** [x] Medida en `a558b02460d113e41dbc4bacb53f4a6b4ccf84ab`; `git diff --stat a558b02..HEAD` solo toca
  `progress/`. Ningún fichero mutado cambia después.
- **RM2** [x] `Tiempo total` = 66 × 36,6 s exacto (la media es reloj total entre mutantes). Con 4 workers y una base
  de ~493 s por worker (sv9 111 s + sv4 381 s, en paralelo), quedan ~117 s por mutante y worker: misma escala que la
  base, con `-x`. La primera campaña (1864,5 s) y esta difieren por carga de la máquina, que el informe declara.
- **RM3** [x] Recorrí los 66 mutantes: ninguno es equivalente. Los dudosos (`alta_sigrid.py:43` con `and`,
  `:46` con `config.desde is None and …`, `sigrid_api_alta_client.py:218` `2→3`) cambian conducta observable: el
  primero deja pasar un documento no aprobado con DESDE puesta; el segundo admite lo aprobado antes de DESDE; el
  tercero cambia el cuerpo enviado a sigrid-api (frontera del cliente, como la fila 10 de la pasada 1).
- **RM4** No hizo falta: las RED y la muestra ya dan un veredicto por mutante sobre la copia.
- **RM5** [x] (ver arriba). **RM6** [x] El cambio 3 añade normalización; no quita ninguna guarda. Los otros dos
  commits solo tocan tests.

## El cambio 3 en los otros caminos de `approved_by` / `_reviewer_from_request`

Callers en `app.py`: 759 (listado), 808 y 840 (borrado y borrado en bloque, `deleted_by.strip() or …`), 887 y 971
(`purged_by`), 1211 (PUT), 1375 (`selected_by`), 1765/1777/1788 (`solicitado_por`). El único cambio de valor es
`DEFAULT_REVIEWER` en blanco ⇒ `None` (antes `""`/`"   "`) y con espacios ⇒ recortado. `Settings.default_reviewer`
ya vale `None` por defecto (`config/settings.py:91`), así que `None` era un valor que todos esos caminos recibían; los
puertos lo tipan `str | None` (`orchestrator_port.py`, `colas_orchestrator_client.py:77,146`,
`review_service.py:928,956,968,981`) y el servicio aplica `or self._default_reviewer`. Nada se rompe: sv4 entero en verde.

## Checkpoints (lo afectado; el resto, como en la pasada 1)

- **C1** [x] `init.sh` verde. **C2** [x] una sola `in_progress` (F-053) · [x] rama `feature/F-053-alta-sigrid`.
- **C3** [x] hexagonal: el cambio vive en el adaptador web · [x] primera línea con ruta en los 2 tests nuevos · [x] sin
  `print` ni TODO · [x] sin secretos (solo `pg_password="x"` en dobles y `ana@ruesma.es` de ejemplo).
- **C4** [x] trazabilidad: R49 gana `test_f053_r49_default_reviewer_recortado` (6); R30 gana los 8 de
  `test_f053_v8_supervivientes_arnes.py` · [x] sin red: `TestClient` con dobles.
- **C4 bis**
  - [x] `rigor` declarado · [x] RED real y reproducida (cambio 3 y los 3 supervivientes) · [x] cobertura `[OK]` 100 %
    (129/129).
  - [x] **Mutación de la herramienta**: `progress/mutacion_F-053_v8_arnes.md`, completa, 66/66, 0 supervivientes,
    0 timeouts, 0 sin veredicto, sin «⚠ CAMPAÑA NO VÁLIDA», base declarada por ejecutor, SHA y workers (4).
  - [x] **Campaña manual reproducible**: texto completo en las 64 filas, anexo JSON verificado, fila 25 de
    «cerrados con test» arreglada, «Tiempo total» 2965,6 s y 1 worker; también en «Evidencias».
  - [x] RM1, RM2, RM5, RM6 · [x] ninguno en `PENDIENTE`.
  - [x] **Cero supervivientes en `critico`**: la campaña de la herramienta no deja ninguno. Los equivalentes 38 y 50
    son de la campaña manual complementaria (la herramienta no genera esos dos mutantes), están demostrados con test
    ejecutable y esperan la aceptación escrita del humano: lo anoto para el líder, no bloquea el código.
  - [x] «Evidencias» con los cuatro números, workers y tiempos de las dos campañas.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: la puerta imprime «F-053 no toca ninguna ruta sensible».
- **C5** [x] T50 y T52 `[x]`; commits `F-053 T50 (pasada 2…)`; T51 abierta es MANUAL del humano · [x] `git status`
  vacío · [x] inventario de mutación con la fila nueva y recuento 34 (lo comprueba `test_f039_r2_*`, en verde).

## Cobertura de requisitos (delta)

| R | Tests nuevos o ampliados (servicio) |
|---|---|
| R49 | `test_f053_r49_default_reviewer_recortado[listado o ficha × None, "", "   "]` (merge y mensaje), sv4 |
| R30 | `test_f053_r30_sin_desde_la_ficha_no_ofrece_reintentar_adjunto`, `…_vista_de_proveedor_…`, `…_solicitar_alta_publica_el_revisor_recortado` (5), `…_rutas_de_formulario_del_alta_fuera_del_openapi`, sv4 |
| RM5 | `test_f053_v8_equivalente_50_activa_es_desde_no_vacia`, `test_f053_v8_equivalente_38_propuesto_en_blanco_acaba_en_el_defecto`, sv4 |

## Cambios requeridos

Ninguno.

## Para el líder y el humano

1. **Aceptación escrita de los equivalentes 38 y 50** de la campaña manual (`critico`), con su demostración en
   `services/albaranes-front/tests/test_f053_v8_equivalentes.py`.
2. MANUAL T51 tras la fusión y el despliegue de sv4 y sv9 de la v8; la §C de la propuesta, con la sesión de sigrid-api.

## Observaciones (no bloquean)

- **O3.** «Evidencias» de `impl_F-053_v8.md` dice cobertura 128/128; `init.sh` de esta pasada da 129/129 (la línea
  nueva de `app.py:473`). Errata del informe.
- **O1 y O2** de la pasada 1 siguen vigentes (O2: correr las suites enteras en el árbol principal tras la fusión, T30).

**Automejora (propuesta, no aplicada):** en `CHECKPOINTS.md` C4 bis, aclarar que los equivalentes de una campaña
manual COMPLEMENTARIA no cuentan como supervivientes de la puerta `critico` si la de la herramienta da 0, pero sí
necesitan demostración ejecutable (RM5) y aceptación del humano antes de `done`.

## Aceptación del humano (2026-10-14)

El humano acepta por escrito («ok») los equivalentes **38 y 50** de la campaña manual de la v8, con su
demostración en `services/albaranes-front/tests/test_f053_v8_equivalentes.py`.
