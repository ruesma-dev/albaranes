<!-- progress/review_F-098.md -->
Revisión completa (pasada 1) · `3ae37eb..816797c` (rama `feature/F-098-partidas-por-capitulo`)

# F-098 · Review

**Veredicto: CHANGES_REQUESTED** · el código está bien; lo que falla es la prueba de R23. Cinco de los sitios donde la
plantilla pinta el código completo **no los vigila ningún test**: la casilla editable, el ⚠, la vista de solo lectura,
«Origen ✎» y «Líneas a Sigrid». R23 es justo la queja del humano («he tenido que poner 99.01.64 y no
cd.99.01.64»), y la feature es `critico`. Arreglarlo cuesta poco, solo tests (abajo).

**Rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura ≥ 80 %, mutación completa con
0 supervivientes sin justificar, MANUAL listadas. Alcance T1–T17 y T19. T18, T20 y T21 quedan fuera a propósito.

## 1. init.sh (C1)

- **Tal cual** (`bash harness/init.sh`, worktree): **exit 1**, 3 KO. sv4 `ImportError: cannot import name
  'misma_partida'` y sv6 `'MOTIVO_COMPLETA'` desde `C:\…\albaranes\services\albaranes-comun` (la instalación
  editable del árbol principal, 0.8.0), y cobertura 55,7 %. Las otras suites en verde (raíz 1883, sv1 205,
  sv2 485, sv3 1576, sv5 96, sv9 1026).
- **Con `PYTHONPATH` = comun del worktree y `ARNES_SIN_CACHE=1`** (como en las reviews de F-076 y F-053): **exit 0,
  «ENTORNO LISTO»**. Raíz 1883 · sv1 205 · sv2 485 · sv3 1576 · sv4 1928 · sv5 96 · sv6 480+1 skip · sv9 1026 ·
  comun 1050+3 skip. `PUERTA COBERTURA: 100.0% de 243 líneas (243/243)`. TAMAÑO OK.
- Juicio: la evidencia vale para C1. El rojo es del entorno del worktree: el código de la rama nunca llega a
  importarse. Una primera pasada con caché, sin `ARNES_SIN_CACHE`, salió KO en cobertura porque reutilizaba los
  `coverage.json` del intento rojo. Que el líder vuelva a pasar init.sh tal cual en `dev` tras fusionar es obligatorio.

## 2. Checkpoints

- C1 [x] (§1) · ficheros del arnés presentes [x].
- C2 [x] una `in_progress` · [x] rama · [x] `current.md`: lleva también las features `blocked` vivas, que es la
  práctica del repo · [x] ninguna `done` nueva.
- C3 [x] hexagonal: `partidas_ficha.py` y el puerto son dominio puro, la regla vive en comun y no se copia;
  la caché entra por `PartidasObraPort` · [x] ruta en la primera línea · [x] sin prints, TODO ni secretos
  (barrido del diff) · [x] trampas: sin DDL, sin raw, sin importes.
- C3 bis N/A: no toca `docs/referencia/`.
- C4 [ ] **R23 sin test real (§4)** · [x] sin red ni BBDD · [x] MANUAL: el comando exacto de T20 está en `tasks.md`
  y en `impl` §5. `current.md` solo dice «sv6 → sv4»: que el líder lo copie al pasar a `blocked`.
- C4 bis [x] rigor declarado · [x] RED real (T1, T3–T6, T8–T13, T15, con trazas). La de T11 es real, pero el test
  que la vigila pasa por la razón equivocada (§4) · [x] cobertura OK · [x] mutación: totales recalculados (abajo) ·
  [x] «Tiempo total» 4664 s > 60 s: **campaña no reejecutada, 78 min según el informe**. Valen el recálculo puro y
  RM1–RM6 · [x] coste por mutante 4664,3 × 4 / 118 = 158 s, coherente con las líneas base (22–351 s) · [x] sin «⚠ NO
  VÁLIDA», 0 sin veredicto · [x] RM1: SHA `f63ec2e`; después solo cambian `progress/`, `tasks.md` y el test nuevo,
  nada del alcance · [x] RM2 coherente · RM5 N/A: no hay equivalentes declarados · [x] RM6: no se quitó ninguna
  guarda; el superviviente lo mata un test · [x] manual N/A: la automática dio 118 · [x] superviviente analizado ·
  [x] «Evidencias» con los 4 números y 4 workers.
- C4 ter N/A: la puerta dice que no hay rutas sensibles.
- C5 [x] T1–T17 y T19 `[x]`, con un commit por tarea (T12+T13 en `410b13f`, justificado) · [x] sin artefactos
  (solo ignorados de init) · [x] `features.json` coherente.

## 3. Mutación: verificación independiente

`harness.alcance.alcance_de_feature("F-098", base="3ae37eb")` sobre HEAD da 11 ficheros y **626 líneas**, igual
que el informe. `generar_mutantes` da **118** (70 de `partidas.py`, 24 de `partidas_ficha.py`, 10 de `app.py`…).
El superviviente existe tal cual: `app.py:574`, `logico`,
`… is None or cache is None:` → `… is None and cache is None:`.
**RM4 sobre JS y plantilla, copia en scratchpad** (la herramienta no los muta). En `app.js` probé 7 mutantes y
murieron los 7: `codigoParaEnviar` (`return conEse.length === 1 ? … : v;` → `return v;`, 3 fallos), `pick`
(`it.completo || it.code` → `it.code`, 1), el filtro de capítulo (`===` → `!==`, 5), `TOPE = 100` → `101` (2),
`partidaParaEnviar` (1), el envío de «Dividir» (2) y `partidaValida` sin el completo (1). En la plantilla mueren 4:
`data-partida`, `data-partida-cod`, `data-sort-value` y la nota «Normalizada». **Sobreviven 5** (§4).

## 4. Hueco de R23

`test_f098_render_pinta_el_completo_y_guarda_el_cod` comprueba `'value="CD.99.01.64"' in celda`. Esa cadena ya
está dentro de `data-sort-value="CD.99.01.64"`, así que la aserción se cumple aunque el `<input>` pinte el cod:
lo vi renderizando con el mutante, que da `value="99.01.64"`. Pasa lo mismo en `…_sin_lista_pinta_el_cod`
(`value="99.01.64"`) y en `…_solo_lectura_pinta_el_completo` (`"CD.99.01.64" in celda`). Probé los 5 mutantes de
abajo juntos contra la **suite entera de sv4** en la copia: los mismos 7 fallos ajenos de ruta que da la copia sin
mutar, y **ningún fallo nuevo** (1921 passed en los dos casos):

1. `value="{{ _partida_pintada }}"` → `value="{{ c.codigo_partida or '' }}"` (la casilla editable; además es el
   `defaultValue` de R23).
2. `⚠</span> {{ _partida_pintada or '—' }}` → `{{ c.codigo_partida or '—' }}`.
3. `<span class="concilia-val" …>{{ _partida_pintada or '—' }}` → `{{ c.codigo_partida or '—' }}` (solo lectura).
4. `<option value="{{ cl.id }}">{{ document.partida_mostrada(cl.codigo_partida) or '—' }}` → `{{ cl.codigo_partida
   or '—' }}` («Origen ✎»).
5. `eff_codimp = (document.partida_mostrada((v.codigo_partida_final or '') | trim) or '') or 'Almacén'` →
   `((v.codigo_partida_final or '') | trim) or 'Almacén'` («Líneas a Sigrid»).

## 5. Puntos pedidos por el líder

- **Desviaciones §2.** De la 1 a la 9, ninguna relaja una aserción de comportamiento. `test_f076_r4` sigue
  comparando el conjunto exacto, ahora con `completa`. `t4_version` pasa a «≥ 0.8.0» y la exacta 0.9.0 la fija
  `test_f098_t5_version_090`. `r15` compara los tres campos de siempre, en orden, y lo nuevo lo cubre
  `test_f098_r14_endpoint_…`. Los JS cambian solo el patrón de búsqueda textual, y
  `test_f098_r21_los_guardados_mandan_el_cod_de_la_lista` exige las tres llamadas `(tr, lista.items)`.
- **R3 con P9** (ejecuté `codigo_completo` y `casar_partida` a mano): `ANT.`+`98.01` ⇒ `ANT.98.01`, nunca `..`;
  `CD2.01` en CD ⇒ `CD2.01` por (b); `CI.01.01` en `CI.F2` ⇒ `CI.01.01` por (c); `P4.01.01` en CD ⇒
  `CD.P4.01.01` por (d). En la 0692, `2.01` y `CD.CD2.01` dan `fuera_de_lista`, y `CI.1.01` da `ambigua`. Lo que se
  guarda es siempre el cod: `traducir_partida` solo devuelve `resolucion.codigo` con exacta o normalizada
  (completa ⇒ normalizada) y, si no, el valor tal cual, sin recortar. sv9 manda `codigo_partida_final` tal cual
  (`test_f098_r30_*`, con `CD2.01`, `CI.01.01` y `98.01`).
- **azure-apps `ddbe825`** (local, `master`, sin push): §11.1 con variables, endpoint y orden de despliegue
  correctos. Sin secretos.

## 6. Cobertura requisito → test

R1–R5, R12: `test_f098_r1_*`…`r5_*`, `r12_*` (comun) · R6–R9: `r6_*`…`r9_*` · R10, R11: `r10_*`, `r11_*` ·
R13: `r13_*` · R14, R27, R28: `test_f098_lista_sv4.py` (`r14_*`, `r27_*`, `r28_*`) · R15–R22:
`test_f098_combo_js.py` (`r15_*`…`r22_*`) · **R23: parcial** (§4) · R24: `presentar_aviso_*`, `render_nota_*` ·
R25, R26: `traducir_*`, `servicio_*` · R29, R31: `test_f098_normaliza_completa.py` · R30: `test_f098_partida_cod.py`
· R33: `t5_version_090` · R34: node + `dom_falso.js`, sin red · R35: lectura (ARCHITECTURE regla 23 y azure-apps).
Los tests de R23–R26 se llaman `presentar_` / `servicio_` / `render_` porque así los pide `tasks.md`, y la sección
de cada uno cita su R.

## 7. Cambios requeridos

1. `services/albaranes-front/tests/test_f098_ficha_partida.py:452` y `:461`. Que la aserción mire el **atributo
   `value` del `<input>`**, no una subcadena, por ejemplo `re.search(r'\svalue="CD\.99\.01\.64"', celda)`, o
   sacando el `<input …>` y leyendo su `value`. Igual para `value="99.01.64"` en `…_sin_lista_…`. Comprobar
   antes que el mutante 1 de §4 lo mata.
2. Mismo fichero, `:509`. En `…_solo_lectura_…`, que la aserción mire el texto del `<span class="concilia-val">`,
   no la celda, para que `data-sort-value` no la cumpla (mutante 3).
3. Test nuevo para el **⚠ con el completo**: una fila no editable con `aviso_partida` debe pintar
   `⚠</span> CD.99.01.64` (mutante 2).
4. Test nuevo para las **`<option>` de «Origen ✎»**: con `partidas_mostradas={"99.01.64": "CD.99.01.64"}` y una
   línea de contrato `99.01.64`, la opción empieza por `CD.99.01.64 ·` (mutante 4).
5. Test nuevo para **«Líneas a Sigrid»**: con una línea valorada de final `99.01.64` sale `CD.99.01.64`, y con
   final vacía sale `Almacén` (mutante 5).
6. En `impl_F-098.md` §3/«Evidencias», una tabla de los 5 mutantes de §4 con su texto exacto y el número de fallos
   que da cada uno con los tests nuevos. Sin código de producción.

## 8. Observaciones, no bloquean

- `codigoParaEnviar` (`app.js`): cuando hay dos hojas con el **mismo cod** y el mismo completo (`P4.08.05` ×2 de la
  0696), `conEse.length === 2` hace que por la red viaje `CD.P4.08.05`. sv4 lo traduce bien al guardar, y así lo
  pide design §5.3, pero R21 dice «nunca el completo». Se arregla deduplicando por `code`. Que lo decida el líder.
- `partMostrada` de `contrato-lines-json` no lo lee `app.js`. El buscador de «Traer líneas contrato»
  (`app.js:1803`) busca por `part` (el cod), así que escribir `CD.99` no encuentra la línea.
- Automejora (propuesta, no aplicada): en `CHECKPOINTS.md` C4 bis, para JS y plantillas con rigor `critico`, que el
  reviewer pruebe al menos un mutante a mano por cada sitio que pinta el dato que pide la spec. La subcadena dentro
  de otro atributo es un falso verde que la herramienta no ve.
