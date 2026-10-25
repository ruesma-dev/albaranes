<!-- progress/impl_F-098.md -->
# F-098 · Informe del implementer (T1–T17, T19)

Rama `feature/F-098-partidas-por-capitulo` (worktree `../albaranes-F-098`), `dev` `3ae37eb` fusionado (`7de22d8`).
Spec v2 (`1cd3cfa`), PARADA 1 cerrada por el humano el 2026-10-24 («ok a f98»). Rigor `critico`.
Hecho: T1–T17 y T19, un commit por tarea (T12 y T13 juntas en `410b13f`, ver desviación 5). Pendiente: T18, T20 y
T21 (MANUAL / cierre). Sin DDL, sin cambios de mensajes de cola ni de sigrid-api; no se ha llamado a ningún sistema real.

## 1. Qué cambió

- **comun 0.9.0** (`ruesma_comun/sigrid/partidas.py`, `__init__.py`, `pyproject.toml`, README): `PartidaObra` con
  `ide`, `capitulo`, `capitulo_descripcion`, `codigo_completo` (`compare=False`); `CapituloObra` y
  `ListaPartidasObra.capitulos`, `cod_repetido`, `no_hojas_completos`; `codigo_completo()` con las reglas R3 (a)–(d) y la
  raíz alfabética de P9; motivo `completa` en `casar_partida` (índice por cod y por completo en toda la lista, exacta
  primero) que `resolver_partida_obra` trata como `normalizada` con el cod; guarda de no hoja con completos;
  `misma_partida`, `mostrar_partida`; `CachePartidasObra.consultar -> (lista, ok)`, que nunca lanza.
- **sv4**: settings `PARTIDAS_OBRA_TTL_S` (600), `PARTIDAS_OBRA_MAX_OBRAS` (64), `PARTIDAS_OBRA_FALLO_TTL_S` (60);
  `CachePartidasObra` propia en `app.py`, pasada a `ReviewService` (5.º argumento posicional) por el puerto nuevo
  `domain/ports/partidas_obra_port.py`; `/api/sigrid/partidas` con `ide`, `codigo_completo`, `capitulo`,
  `cod_repetido` y `capitulos`; `domain/services/partidas_ficha.py` (`presentar_partidas`: mapa cod → completo y ⚠→✓
  cuando son `misma_partida`; `traducir_partida`: completo → cod); `ReviewService` pinta con la lista y traduce lo que
  guarda en `update_line_conciliacion` y `dividir_linea`; plantilla con `partida_mostrada` (casilla, solo lectura,
  «Origen ✎», `contrato-lines-json` con `partMostrada`, «Líneas a Sigrid», `data-partida` de «Dividir», nota F-076) y
  `data-partida-cod`; `app.js`: chips «Todas»/capítulos (mousedown + preventDefault), capítulo compartido y recordado
  en `localStorage["f098.capitulo." + obra]` con try/catch, tope 100 + «N partidas más: escribe para afinar»,
  etiqueta «completo · descripción agregada» (+ «(código repetido en la obra)»), `pick` con completo y
  `dataset.partidaCod`, `partidaValida` con completo o cod, `codigoParaEnviar`, `partidaParaEnviar(inp, items)`; los
  tres guardados y «Dividir» mandan el cod; CSS `.combo-chips`, `.chip`, `.chip.on`.
- **sv6**: sin cambio de código de valoración (R29 solo tests); `scripts/medir_f076_partidas.py` cuenta aparte
  `completa` y lista solo de esas `document_id`, estado y el par final → cod (R31).
- **sv9**: solo test de no regresión R30.
- **Docs**: `docs/ARCHITECTURE.md` regla 23 + «Infra y despliegue» (comun 0.9.0, sv6 → sv4); `azure-apps/albaranes.md`
  §11.1 (commit local `ddbe825` en `azure-apps`, rama `master`, **sin push**).

Ficheros de producción: los 11 del alcance de `progress/mutacion_F-098.md` + `app.js`, `styles.css`,
`document_detail.html`. Tests nuevos: comun `test_f098_partidas_capitulo.py` (187), sv4 `test_f098_lista_sv4.py`,
`test_f098_ficha_partida.py`, `test_f098_combo_js.py` (95 entre los tres), sv6 `test_f098_normaliza_completa.py` (7),
sv9 `test_f098_partida_cod.py` (9).

## 2. Decisiones y desviaciones (justificadas también en `progress/current.md`)

1. R5 pide no tocar los tests de F-076, pero la spec cambia lo que tres fijan literalmente:
   `test_f076_r4_motivos_declarados` (+`completa`), `test_f076_t4_version_080` (→ «desde 0.8.0») y, en sv4,
   `test_f076_r15_el_endpoint_sirve_los_items_de_hoy` (compara los tres campos de siempre). Solo esa aserción.
2. Campos nuevos de `PartidaObra` con `compare=False` (los tests de hojas de F-076 comparan con 3 campos).
3. `PartidasObraPort` nace en T8, no en T9 (lo pide la firma de `ReviewService`). `consultar` sin obra ⇒ `(None, False)`.
4. `DocumentDetailPayload.partida_mostrada()` es método del modelo y no un global de Jinja: el render de los tests
   (`conftest.render_detalle`) no lleva globales propios.
5. **T12 y T13 en un commit**: el mismo cambio de `app.js` toca `opcionesPartida` (T12) y el envío (T13).
6. Tests viejos de JS que sacan funciones de `app.js` por nombre: se añade `codigoParaEnviar` a su lista
   (`test_f065_f3bis_front.py` `_DIVIDIR`, `_GUARDAR`; `test_f077_guardar_y_aprobar_js.py`); `test_f065_f2_origen.py`
   acepta la forma nueva de design §5.3 (`capitulos` en `partidasDeRespuesta`, `{shown, resto}` en `opcionesPartida`);
   `test_f051_almacen_front.py` y `test_f065_f1_js.py` buscan `_camposCambiados(tr` (ahora `(tr, lista.items)`). Ninguna
   aserción de comportamiento se ha relajado.
7. Sin capítulos (lista caída, sv4 vieja) no se pinta la barra de chips; capítulo nulo ⇒ chip «Sin capítulo».
   El aviso «(código repetido en la obra)» no entra en la búsqueda (`norm` = completo · descripción + cod).
8. `codigoParaEnviar`: cod de la lista ⇒ tal cual; completo de UNA sola hoja ⇒ su cod; si no, el valor (lo frena
   `partidasMalas`, o lo traduce sv4 al guardar).
9. R31: «el par leída → cod» se implementa como **final → cod** (la final es lo que casa por el completo).

## 3. Fase RED (trazas reales; desde la raíz de cada servicio, `PYTHONPATH` = comun del worktree)

Copia completa de cada traza en el scratchpad de la sesión (`.../scratchpad/red/T*.txt`).

- **T1** `python -m pytest tests/test_f098_partidas_capitulo.py -p no:cacheprovider -q` (comun, antes de T2):
  `E   AttributeError: 'PartidaObra' object has no attribute 'ide'` … `92 failed, 2 passed in 0.32s`
- **T3** `... -k "r6 or r7 or r8 or r9"`: `AssertionError: assert ('fuera_de_lista', ()) == ('completa', ('99.01.64',))`
  … `20 failed, 28 passed, 94 deselected in 0.16s`
- **T4** `... -k "r10 or r11"`: `AttributeError: module 'ruesma_comun.sigrid.partidas' has no attribute
  'misma_partida'` … `33 failed, 142 deselected in 0.42s`
- **T5** `... -k r13`: `AttributeError: 'CachePartidasObra' object has no attribute 'consultar'` … `12 failed, 175 deselected`
- **T6** sv6 `python -m pytest tests/test_f098_normaliza_completa.py -k r29` con comun 0.8.0:
  `AssertionError: assert 'new_line_created' == 'existing_matched'` … `2 failed, 1 passed in 1.05s`
- **T8** sv4 `.venv/Scripts/python.exe -m pytest tests/test_f098_lista_sv4.py`:
  `AttributeError: 'Settings' object has no attribute 'partidas_obra_ttl_s'` … `15 failed, 3 passed`
- **T9** `... tests/test_f098_ficha_partida.py -k "presentar or traducir"`: `ImportError: cannot import name
  'partidas_ficha' from 'domain.services'` … `34 failed in 1.55s`
- **T10** `... -k servicio`: `AssertionError: assert 'CD.01.01' == '01.01'` … `5 failed, 11 passed, 34 deselected`
- **T11** `... -k render` (plantilla y modelo guardados con `git stash`): `assert 'value="CD.99.01.64"' in '<td
  class="concilia-td" data-col="partida" data-sort-value="99.01.64">…'` … `6 failed, 50 deselected in 3.97s`
- **T12–T13** `... tests/test_f098_combo_js.py` (node + `dom_falso.js`): `ValueError: substring not found` (las funciones
  nuevas no existían en `app.js`) … `18 failed in 2.00s`
- **T15** sv6 `... tests/test_f098_normaliza_completa.py -k r31`: `AssertionError: assert Counter({('no...ndiente'): 1})
  == {('completa',...nte'): 1, ...}` … `4 failed, 3 deselected in 1.10s`
- T2 (código de T1), T7 (no regresión de sv9: ya verde por diseño, R30), T14 (CSS) y T16 (docs) no tienen RED propia.

Tras cada tarea, el mismo comando en verde (p. ej. T12–T13: `18 passed in 2.71s`; T11: `7 passed`).

## 4. Verificación

- Suites (una tras otra, nunca dos a la vez): comun 1050 passed / 3 skipped; sv4 1928 passed; sv6 480 passed /
  1 skipped; sv9 1026 passed. JS de la ficha: `test_f098_combo_js.py` + `test_f065_f1_js`, `f065_f3bis_front`,
  `f065_f3_dividir`, `f077_guardar_y_aprobar_js`, `f065_f2_origen`, `f065_f2_pasada2`, `f051_almacen_front`:
  410 passed. Plantilla: `test_f098_ficha_partida.py` + `test_f076_aviso_partida`, `test_f077_aviso_partida`,
  `test_f078_ficha_pinta_fila`: 151 passed.
- `python -m harness.tamano --feature F-098`: `PUERTA TAMAÑO: F-098 dentro de los topes (requirements 131/150,
  design 227/250)`.
- **`bash harness/init.sh`** (T19), dos ejecuciones:
  - **tal cual** (sin variables): **ROJO**, dos motivos. (a) Faltaba la fila de `mutacion_F-098.md` en
    `progress/inventario_mutacion_F-039.md`: corregido (`d30979a`). (b) **Entorno del worktree**: sv4 y sv6 importan
    `ruesma_comun` del árbol principal (0.8.0, instalación editable), `ImportError: cannot import name 'misma_partida'`
    / `'MOTIVO_COMPLETA'`; por eso la cobertura salía 55,7 %. No es del código: pasará igual en `dev` tras fusionar.
  - **con `PYTHONPATH` a la comun del worktree** (como F-076 y F-053, ver sus informes) sobre `d30979a`: **VERDE**,
    `ENTORNO LISTO. Puedes trabajar.`, exit 0. Raíz 1883 passed (322,7 s); sv1 205; sv2 485; sv3 1576; sv4 1928
    (181,5 s); sv5 96; sv6 480 + 1 skipped; sv9 1026; comun en verde (caché del verde de 02:32);
    `PUERTA COBERTURA: 100.0% de 243 líneas cambiadas cubiertas (243/243, umbral 80%, nivel critico)`.

## 5. Pendiente (MANUAL, no lo hace el implementer)

- **T18 (líder, Chrome, sv4 local con Azurite y BBDD local; sigrid-api solo lectura)**: ficha de la 0686 (chips
  «Todas/ANT./CD/CI/CP», CD ⇒ solo CD, `cd.99.01` encuentra `CD.99.01.64`, elegirla pinta `CD.99.01.64`, Guardar ⇒
  PATCH con `99.01.64`, recarga con ✓; «Dividir» igual) y de la 0692 (`CD2.01` y `CI.01.01` tal cual, chip `CI.F2`).
  Lo que los tests no ven: aspecto de los chips (CSS sticky dentro del panel), foco real del navegador.
- **T20 (humano)**: tras fusionar en `dev` y con F-076 T18 hecha: `.\deploy.ps1 -Only sv6` → `.\deploy.ps1 -Only sv4`
  → `.\check_deploy.ps1`; corregir a mano las 2 líneas de la 0686 con `CD.21.02.21` (reelegir la partida).
- **T21**: `bash harness/init.sh` de cierre tras T20.
- Antes de `git worktree remove`: quitar la *junction* `.venv` de sv4 con `cmd /c rmdir`.
- `azure-apps` `ddbe825`: commit local, falta el push (lo decide el humano).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | init.sh (con `PYTHONPATH`): raíz 1883, sv1 205, sv2 485, sv3 1576, sv4 1928, sv5 96, sv6 480 (+1 skip), sv9 1026, comun 1050 (+3 skip); 0 fallos. Tests nuevos de F-098: 298 (187 comun, 95 sv4, 7 sv6, 9 sv9) |
| Cobertura de líneas cambiadas | **100,0 %** (243/243, umbral 80 %, `critico`) — `PUERTA COBERTURA` |
| Mutación | campaña completa (`--max-mutantes 0`, 4 workers, sobre `f63ec2e`): **118 generados, 117 muertos, 1 superviviente**, 0 timeouts, 0 sin veredicto, 4664,3 s. Superviviente `app.py:574` (`or` → `and`): hueco real, matado por `test_f098_r14_basta_que_falte_el_cliente_o_la_cache` (con el mutante a mano: **2 failed**, sin `-x`). **0 supervivientes sin justificar**. Detalle: `progress/mutacion_F-098.md`. No mutados por la herramienta: `app.js`, `styles.css`, plantilla (cubiertos por los tests de node y de render) |
| Tiempo de la suite | sv4 181,5 s; raíz 322,7 s; comun 128,4 s (primera ejecución de init.sh); sv6 12,6 s; sv9 36,2 s |
