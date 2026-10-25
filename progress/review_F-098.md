<!-- progress/review_F-098.md -->
Revisión completa (pasada 1) · `3ae37eb..816797c` (rama `feature/F-098-partidas-por-capitulo`)
# F-098 · Review

**Veredicto: CHANGES_REQUESTED.** El código está bien; lo que falla es la prueba de R23. Cinco de los sitios donde la
plantilla pinta el código completo **no los vigila ningún test**: casilla editable, ⚠, solo lectura, «Origen ✎» y
«Líneas a Sigrid». R23 es justo la queja del humano y la feature es `critico`. Se arregla solo con tests (§7).

**Rigor:** `critico`, declarado. Exige RED, cobertura ≥ 80 %, mutación completa con 0 supervivientes sin justificar y
MANUAL listadas. Alcance T1–T17 y T19. T18, T20 y T21 quedan fuera a propósito.
## 1. init.sh (C1)

- **Tal cual**: **exit 1**, 3 KO. sv4 `cannot import name 'misma_partida'` y sv6 `'MOTIVO_COMPLETA'` desde
  `C:\…\albaranes\services\albaranes-comun` (la editable 0.8.0 del árbol principal), y cobertura 55,7 %. El resto en verde.
- **Con `PYTHONPATH` = comun del worktree y `ARNES_SIN_CACHE=1`** (precedentes: reviews de F-076 y F-053): **exit 0,
  «ENTORNO LISTO»**. Raíz 1883 · sv1 205 · sv2 485 · sv3 1576 · sv4 1928 · sv5 96 · sv6 480+1s · sv9 1026 ·
  comun 1050+3s. `PUERTA COBERTURA: 100.0% de 243 líneas`. TAMAÑO OK.
- Juicio: vale para C1. El rojo es del entorno, porque el código de la rama ni se importa. Con caché, la puerta salía
  KO porque reutilizaba los `coverage.json` del intento rojo; hay que pasarla sin caché. El líder la repite tal cual en `dev`.
## 2. Checkpoints

- C1 [x] (§1), ficheros del arnés [x]. C2 [x] una `in_progress`, rama correcta, `current.md` con las `blocked` vivas
  (práctica del repo), ninguna `done` nueva.
- C3 [x] hexagonal: `partidas_ficha.py` y el puerto son dominio puro, la regla vive en comun y no se copia, la caché
  entra por `PartidasObraPort` · [x] ruta en la 1.ª línea · [x] sin prints, TODO ni secretos · [x] sin DDL, sin raw,
  sin importes. C3 bis N/A: no toca `docs/referencia/`. C4 ter N/A: la puerta dice que no hay rutas sensibles.
- C4 [ ] **R23 sin test real (§4)** · [x] sin red ni BBDD · [x] MANUAL: el comando exacto de T20 está en `tasks.md`
  y en `impl` §5. Que el líder lo copie a `current.md` al pasar a `blocked`.
- C4 bis [x] rigor · [x] RED con trazas (T1, T3–T6, T8–T13, T15) · [x] cobertura · [x] totales recalculados (§3) ·
  [x] «Tiempo total» 4664 s > 60 s: **campaña no reejecutada (78 min según el informe)**; recálculo puro + RM ·
  [x] coste por mutante 4664,3×4/118 = 158 s, coherente con las bases (22–351 s) · [x] sin «NO VÁLIDA», 0 sin veredicto
  · [x] RM1: SHA `f63ec2e`; después solo cambian `progress/`, `tasks.md` y el test nuevo · [x] RM2 · RM5 N/A: ningún
  equivalente declarado · [x] RM6: no se quitó ninguna guarda · [x] campaña manual N/A: la automática dio 118 ·
  [x] superviviente analizado · [x] «Evidencias» completa, con 4 workers.
- C5 [x] T1–T17 y T19 `[x]`, con un commit por tarea (T12+T13 juntas, justificado) · [x] sin artefactos
  · [x] `features.json` coherente.
## 3. Mutación: verificación independiente

`alcance_de_feature("F-098", base="3ae37eb")` sobre HEAD: 11 ficheros y **626 líneas**, igual que el informe.
`generar_mutantes`: **118** (70 de `partidas.py`, 24 de `partidas_ficha.py`, 10 de `app.py`). El superviviente existe
tal cual: `app.py:574` `logico`, `… is None or cache is None:` → `… is None and cache is None:`.
**RM4 sobre JS y plantilla** (copia en scratchpad; la herramienta no los muta). `app.js`: 7 de 7 muertos.
`codigoParaEnviar` `return conEse.length === 1 ? … : v;` → `return v;` (3 fallos) · `pick` `it.completo || it.code` →
`it.code` (1) · filtro de capítulo `===` → `!==` (5) · `TOPE = 100` → `101` (2) · `partidaParaEnviar` (1) · envío de
«Dividir» (2) · `partidaValida` sin el completo (1). Plantilla: mueren `data-partida`, `data-partida-cod`,
`data-sort-value` y la nota «Normalizada». **Sobreviven 5** (§4).
## 4. Hueco de R23

`test_f098_render_pinta_el_completo_y_guarda_el_cod` comprueba `'value="CD.99.01.64"' in celda`, y esa cadena ya está
dentro de `data-sort-value="CD.99.01.64"`. La aserción se cumple aunque el `<input>` pinte el cod: lo comprobé
renderizando con el mutante, que da `value="99.01.64"`. Pasa lo mismo en `…_sin_lista_pinta_el_cod` y en
`…_solo_lectura_pinta_el_completo`. Probé los 5 mutantes juntos contra la **suite entera de sv4** en la copia:
1921 passed y los mismos 7 fallos ajenos de ruta que da la copia sin mutar. **Ningún fallo nuevo.**

1. `value="{{ _partida_pintada }}"` → `value="{{ c.codigo_partida or '' }}"` (casilla editable y su `defaultValue`).
2. `⚠</span> {{ _partida_pintada or '—' }}` → `⚠</span> {{ c.codigo_partida or '—' }}`.
3. `<span class="concilia-val" …>{{ _partida_pintada or '—' }}` → `{{ c.codigo_partida or '—' }}` (solo lectura).
4. `<option value="{{ cl.id }}">{{ document.partida_mostrada(cl.codigo_partida) or '—' }}` →
   `{{ cl.codigo_partida or '—' }}` («Origen ✎»).
5. `eff_codimp = (document.partida_mostrada((v.codigo_partida_final or '') | trim) or '') or 'Almacén'` →
   `((v.codigo_partida_final or '') | trim) or 'Almacén'` («Líneas a Sigrid»).
## 5. Puntos pedidos por el líder

- **Desviaciones §2 (1–9):** ninguna relaja comportamiento. `test_f076_r4` sigue comparando el conjunto exacto, ahora
  con `completa`. `t4_version` pasa a ≥ 0.8.0 y la exacta 0.9.0 la fija `test_f098_t5_version_090`. `r15` compara los
  3 campos de siempre, en orden, y lo nuevo lo cubre `r14_endpoint_…`. Los JS solo cambian el patrón textual, y
  `r21_los_guardados_mandan_el_cod_de_la_lista` exige las 3 llamadas `(tr, lista.items)`.
- **R3/P9**, ejecutado a mano: `ANT.`+`98.01` ⇒ `ANT.98.01` · `CD2.01` en CD ⇒ `CD2.01` (b) · `CI.01.01` en `CI.F2` ⇒
  `CI.01.01` (c) · `P4.01.01` en CD ⇒ `CD.P4.01.01` (d). En la 0692, `2.01` y `CD.CD2.01` dan `fuera_de_lista`, y
  `CI.1.01` da `ambigua`. Se guarda siempre el cod: `traducir_partida` devuelve `resolucion.codigo` solo con
  exacta/normalizada y, si no, el valor sin recortar. sv9 manda la final tal cual (`r30_*`: `CD2.01`, `CI.01.01`, `98.01`).
- **azure-apps `ddbe825`** (local, sin push): §11.1 correcto (variables, endpoint, orden sv6 → sv4), sin secretos.
## 6. Cobertura requisito → test

R1–R13: `test_f098_partidas_capitulo.py` (`r1_*`…`r13_*`) · R14, R27, R28: `test_f098_lista_sv4.py` · R15–R22:
`test_f098_combo_js.py` · **R23 parcial (§4)** · R24: `presentar_aviso_*`, `render_nota_*` · R25, R26: `traducir_*`,
`servicio_*` · R29, R31: `test_f098_normaliza_completa.py` · R30: `test_f098_partida_cod.py` · R33: `t5_version_090` ·
R34: node + `dom_falso.js` · R35: lectura. Los nombres `presentar_`/`servicio_`/`render_` los fija `tasks.md`.
## 7. Cambios requeridos (solo tests en `services/albaranes-front/tests/test_f098_ficha_partida.py`)

1. `:452` y `:461`: comprobar el **atributo `value` del `<input>`**, por ejemplo `re.search(r'\svalue="CD\.99\.01\.64"', celda)`,
   o leyendo el `value` del `<input …>`. Lo mismo con `value="99.01.64"` sin lista. Tiene que matar el mutante 1.
2. `:509` (solo lectura): comprobar el texto del `<span class="concilia-val">`, no la celda (mutante 3).
3. Test nuevo: una fila no editable con `aviso_partida` pinta `⚠</span> CD.99.01.64` (mutante 2).
4. Test nuevo: con una línea de contrato `99.01.64` y el mapa `99.01.64 → CD.99.01.64`, la `<option>` de «Origen ✎»
   empieza por `CD.99.01.64 ·` (mutante 4).
5. Test nuevo: «Líneas a Sigrid» pinta `CD.99.01.64` con final `99.01.64`, y `Almacén` con final vacía (mutante 5).
6. Añadir a `impl_F-098.md` una tabla con los 5 mutantes de §4, con su texto exacto y el número de fallos de cada uno
   con los tests nuevos.
## 8. Observaciones (no bloquean)

- `codigoParaEnviar`: con dos hojas del mismo cod y el mismo completo (`P4.08.05` ×2, 0696), por la red viaja
  `CD.P4.08.05`. sv4 lo traduce bien y así lo pide design §5.3, pero R21 dice «nunca el completo». Se arregla
  deduplicando por `code`. Lo decide el líder.
- `partMostrada` no lo lee `app.js`, y «Traer líneas contrato» (`app.js:1803`) filtra por el cod: `CD.99` no encuentra nada.
- Automejora (propuesta): en C4 bis, con rigor `critico` y JS o plantilla tocados, que el reviewer pruebe a mano al
  menos un mutante por cada sitio que pinta el dato de la spec. Una subcadena dentro de otro atributo da un falso verde.
