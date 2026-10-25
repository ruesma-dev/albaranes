<!-- progress/review_F-098.md -->
Revisión incremental desde 9e78a3c (pasada 2) · delta `9e78a3c..3c602aa` (7 commits)
# F-098 · Review

**Veredicto: APPROVED.** Los cambios 1–6 que pedía la pasada 1 (§7) están hechos y los 5 mutantes de plantilla que
sobrevivían mueren. Los dos añadidos del líder, (a) y (b), cumplen R21 y R18, cada uno con su RED y con un mutante
muerto. init.sh sale como en la pasada 1: rojo tal cual solo por el entorno del worktree, verde con la comun del worktree.

**Rigor:** `critico`, declarado. Exige RED, cobertura ≥ 80 %, mutación completa con 0 supervivientes sin justificar y
MANUAL listadas. Alcance T1–T17 y T19. T18, T20 y T21 quedan fuera a propósito.

**Lo aprobado en la pasada 1 se da por bueno hasta `9e78a3c`:** comun, sv4 Python, sv6, sv9, docs, azure-apps
`ddbe825`, desviaciones y R3/P9. El delta toca solo `app.js` (dos funciones), dos ficheros de test, `impl_F-098.md` y
`current.md`. Ninguna línea de Python de producción cambia, así que el alcance de la campaña sigue igual (626 líneas,
118 mutantes, SHA `f63ec2e`) y no hay que repetirla (RM1). `app.js` queda fuera de la herramienta.

## 1. init.sh (C1), sobre HEAD `3c602aa`

- **Tal cual**: **exit 1**, los mismos 3 KO de la pasada 1. sv4 `cannot import name 'misma_partida'` y sv6
  `'MOTIVO_COMPLETA'` desde `C:\…\albaranes\services\albaranes-comun` (la editable 0.8.0 del árbol principal), y
  cobertura 55,7 %. El resto en verde: raíz 1883, sv1 205, sv2 485, sv3 1576, sv5 96, sv9 1026.
- **Con `PYTHONPATH` = comun del worktree y `ARNES_SIN_CACHE=1`**: **exit 0, «ENTORNO LISTO»**. Raíz 1883 · sv1 205 ·
  sv2 485 · sv3 1576 · **sv4 1933** · sv5 96 · sv6 480+1s · sv9 1026 · comun 1050+3s.
  `PUERTA COBERTURA: 100.0% de 243 líneas`. TAMAÑO OK.
- Juicio: vale para C1, como en la pasada 1 (precedentes F-076 y F-053). **El líder repite `bash harness/init.sh`
  tal cual en `dev` tras fusionar, y antes no marca `done`.**

## 2. Los 5 mutantes de plantilla (punto 1)

Hice una copia nueva del sv4 en HEAD, en el scratchpad, y reproduje **los cinco** (no solo dos) con el mismo texto
exacto de la pasada 1 (§4). Los pasé contra `test_f098_ficha_partida.py` + `test_f098_combo_js.py`, que sin mutar dan 80 passed:

| # | Sitio (original → mutado, texto de la pasada 1) | Resultado | Lo mata |
|---|---|---|---|
| 1 | casilla `value="{{ _partida_pintada }}"` → `c.codigo_partida or ''` | 1 failed | `render_pinta_el_completo_y_guarda_el_cod` |
| 2 | `⚠</span> {{ _partida_pintada or '—' }}` → `c.codigo_partida` | 1 failed | `render_solo_lectura_con_aviso_pinta_el_completo` |
| 3 | `<span class="concilia-val" …>{{ _partida_pintada … }}` → `c.codigo_partida` | 1 failed | `render_solo_lectura_pinta_el_completo` |
| 4 | `<option value="{{ cl.id }}">{{ document.partida_mostrada(…) }}` → `cl.codigo_partida` | 1 failed | `render_origen_ofrece_la_linea_con_el_completo` |
| 5 | `eff_codimp = (document.partida_mostrada(…) or '') or 'Almacén'` → sin `partida_mostrada` | 1 failed | `render_lineas_a_sigrid_con_el_completo_o_almacen` |

Las aserciones ya no se pueden cumplir por una subcadena de otro atributo:
- `_valor_del_input` lee el `value` del propio `<input>`;
- en solo lectura se compara el texto del `<span>`;
- en «Origen ✎» se busca la `<option value="7">` dentro de su `<select>`;
- en «Líneas a Sigrid» se comparan las filas (n.º, partida, concepto), incluido `Almacén` con la final en blanco.

## 3. (a) y (b) (punto 2)

- **(a) R21.** `codigoParaEnviar` junta los cod sin repetirlos. Con `P4.08.05` ×2 (0696) manda el cod, no
  `CD.P4.08.05`. Si dos cod distintos comparten completo sigue sin adivinar: manda el valor y lo frena `partidasMalas`
  o lo traduce sv4 (R25). Los 14 casos de `r21_codigo_para_enviar` siguen en verde. Mi mutante,
  `if (it.completo === v && cods.indexOf(it.code) === -1)` → `if (it.completo === v)`: **1 failed**
  (`r21_…_dos_hojas_mismo_cod_y_mismo_completo`). La RED del implementer (`impl` §6):
  `{'repetido': 'CD.P4.08.05'} != {'repetido': 'P4.08.05'}`.
- **(b) R18 en «Traer líneas contrato».** El texto en que se busca es `part + partMostrada + desc`. Sin
  `partMostrada` (ficha sin lista) se añade «» y no cambia nada; lo cubre la fila `21.02.21` del test. El test ejecuta
  de verdad `wireTraerContrato` (node + `dom_falso.js`): `CD.99` y `cd.99.01` encuentran la línea `99.01.64`, y `CP.`
  no encuentra ninguna. Mi mutante, quitar `partMostrada`: **1 failed**. La RED, en `impl` §6.
- No rompe nada: sv4 entero da 1933 passed (+5, los tests nuevos), con las suites JS viejas (f051, f065, f077) en verde.

## 4. Tabla de `impl_F-098.md` (punto 3)

`impl` §6 trae una fila por mutante, con el **texto exacto original → mutado**, los fallos (`1 failed, 59 passed`,
`test_f098_ficha_partida.py` entero y sin `-x`) y el test que lo mata. Coincide con lo que reproduje, fila a fila y
test a test. Mi cuenta da 79 passed porque suma `test_f098_combo_js.py`: 60 + 20 = 80 tests. Cumple el punto de C4 bis
sobre campañas manuales. «Evidencias» está al día (sv4 1933, 303 tests nuevos).

## 5. Checkpoints (pasada 2)

- C1 [x] (§1) · ficheros del arnés [x].
- C2 [x] una `in_progress` · [x] rama correcta · [x] `current.md` con la pasada 1 atendida (las `blocked` vivas,
  como es práctica del repo) · [x] ninguna `done` nueva.
- C3 [x] el delta es presentación (`app.js`) y tests · [x] ruta en la 1.ª línea · [x] sin `console.log` fuera de
  tests, sin TODO ni secretos. C3 bis N/A: no toca `docs/referencia/`. C4 ter N/A: la puerta dice que no hay rutas sensibles.
- C4 [x] **R23 con tests reales (§2)**, R21 y R18 ampliados (§3) · [x] sin red ni BBDD · [x] MANUAL: el comando exacto de
  T20 está en `tasks.md` e `impl` §5; el líder lo copia a `current.md` al pasar a `blocked`.
- C4 bis [x] rigor · [x] RED de (a) y (b), con su traza · [x] cobertura 100 % · [x] alcance y totales sin cambio
  (recalculados en la pasada 1) · [x] «Tiempo total» 4664 s > 60 s: **campaña no reejecutada (78 min según el informe)**;
  recálculo puro + RM1–RM6 · [x] coste por mutante 158 s · [x] sin «NO VÁLIDA» · [x] RM1: el delta no toca Python de
  producción · [x] RM2 · RM5 N/A: no hay equivalentes declarados · [x] RM6: ninguna guarda quitada · [x] JS y plantilla:
  14 mutantes manuales reproducibles (7 + 5 + 2), todos muertos · [x] superviviente `app.py:574` analizado y muerto ·
  [x] «Evidencias» completa, con 4 workers.
- C5 [x] T1–T17 y T19 `[x]`, cambios de la review en commits `F-098 review 1 · …`, uno por cambio · [x] árbol limpio
  · [x] `features.json` coherente.

## 6. Cobertura requisito → test

Como en la pasada 1, salvo tres cosas:
- **R23, completa**: `render_pinta_…`, `render_sin_lista_…`, `render_solo_lectura_…`,
  `render_solo_lectura_con_aviso_…`, `render_origen_…`, `render_lineas_a_sigrid_…`, `render_dividir_…` y
  `render_contrato_json_…`.
- R21: más `r21_…_dos_hojas_mismo_cod_y_mismo_completo`.
- R18 («Traer líneas contrato»): `traer_lineas_contrato_busca_por_el_completo`.

## 7. Para el cierre (no bloquea)

1. Tras fusionar en `dev`: `bash harness/init.sh` tal cual en el árbol principal, en verde.
2. T18 (líder, Chrome): el aspecto de los chips y el foco real.
3. T20 (humano), con F-076 T18 hecha: `.\deploy.ps1 -Only sv6` → `.\deploy.ps1 -Only sv4` → `.\check_deploy.ps1`.
   Después, las 2 líneas de la 0686, a mano.
4. Automejora (propuesta, sin aplicar): en C4 bis, con rigor `critico` y JS o plantilla tocados, que el reviewer pruebe
   a mano un mutante por cada sitio donde se pinta el dato de la spec. Aquí cazó 5 falsos verdes que nadie más veía.
