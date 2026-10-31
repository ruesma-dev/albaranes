# progress/review_F-114.md

Revisión incremental desde 1c4b8fb (pasada 2) — delta `1c4b8fb..d8dac4b` (7 commits: `3272e04` … `d8dac4b`).

- **Veredicto:** CHANGES_REQUESTED (solo contabilidad del arnés: el código queda aprobado; ver §4)
- **Nivel de rigor:** `estandar` (declarado). Exige fase RED, cobertura y mutación muestreada. RM5 no aplica.
- **Pasada 1:** APPROVED sobre `05d2cb5` (commit `0ddac57`; texto completo con `git show 0ddac57:progress/review_F-114.md`).
  Lo aprobado entonces queda dado por bueno salvo `_SQL_PROVEEDORES_TODOS`, que el delta cambia y se revisa aquí.
- **Fuera:** no se ha consultado producción ni sigrid-api; las mediciones de tiempo (0,7–1,1 s frente a 4,5–5,2 s
  de la subconsulta) son del líder y se toman como dato.

## 1. `bash harness/init.sh` (tal cual, en el worktree, sobre `d8dac4b`)

Exit 0, «ENTORNO LISTO». Arnés 1919 passed; sv1 236; sv2 496; sv3 1576; **sv4 2190 passed, 1 warning** (+4 de la
T8, coincide con lo declarado en `impl_F-114.md` §8); sv5 125; sv6 506 (1 skipped); sv9 1073.
`PUERTA COBERTURA` N/A con motivo impreso («las líneas cambiadas no contienen sentencias ejecutables»: solo el
literal SQL y su comentario). `PUERTA RUTAS SENSIBLES` N/A (la feature está `blocked`, sin rama en curso; el
fichero tocado no es ruta sensible, como en la pasada 1). `PUERTA TAMAÑO` dentro (impl 198/220). **El init.sh
declarado es real.**

## 2. El arreglo de D2 (lo que pidió mirar el líder)

| Punto | Resultado |
|---|---|
| El fallo | `[x]` Confirmado leyendo la SQL de `1c4b8fb`: el `LIKE` iba en el `WHERE`, antes del `GROUP BY v.cif`, así que `COUNT(*)` y `MIN(v.raz)` solo veían las fichas que casaban. Contradice D2/R6/R17. |
| SQL nueva | `[x]` Mismo `SELECT TOP (?) … FROM prv JOIN con … WHERE <vivo> GROUP BY v.cif`, con el texto en `HAVING MAX(CASE WHEN <nombre LIKE ? ESCAPE '!'> OR <cif LIKE ? ESCAPE '!'> THEN 1 ELSE 0 END) = 1`. Válida en T-SQL (columnas no agrupadas solo dentro de un agregado). Una pasada, sin subconsulta. |
| Solo lectura | `[x]` Un único `SELECT`, por `_post_sql_read` (`sql/read`). |
| Parametrizada | `[x]` La SQL es una constante; el texto del usuario solo entra como valor. 6 `?` en orden posicional: `TOP`, `tip`, `emp`, `fecbaj` (WHERE), patrón nombre, patrón CIF (HAVING). La lista de Python no cambia: `[51, 5, 1, 0, nombre, cif]`, **la de design §3**. `test_f114_r15` fija ahora `count("?") == 6`, el `HAVING` y que el `LIKE` va tras el `GROUP BY`. |
| `ESCAPE '!'` | `[x]` En los dos `LIKE` (`count("LIKE ? ESCAPE '!'") == 2` sigue en el test); `_patron_like` sin tocar. Ahora además se **ejecuta**: `test_f114_t8_d2_escape_y_limite_ejecutados` busca `50%_!` (casa el literal) y `5_%` (no casa nada). |
| Vivo | `[x]` Las fichas de baja, de otro `tip` o de otra empresa siguen fuera antes de agrupar: ni cuentan ni traen su CIF (`test_f114_t8_d2_una_ficha_de_baja_o_ajena_no_trae_su_cif`). |
| Efecto visible | Aceptable: el nombre mostrado es `MIN(raz)` de todas las fichas vivas y puede no contener lo escrito (buscar «zeta» enseña «ALFA OBRAS SL · 2 fichas»). Es justo lo que pide D2 (una entrada por CIF) y lo declara el informe §8. |

### Fase RED del caso D2

`[x]` El informe trae la salida real (`2 failed, 2 passed`). **Reproducida por mí** sin tocar el árbol: un plugin de
pytest en el scratchpad sustituye `_SQL_PROVEEDORES_TODOS` por la SQL de `1c4b8fb` y ejecuta
`-k "t8 or r15"`: `3 failed, 3 passed`. Caen `test_f114_t8_d2_buscar_por_nombre_cuenta_todas_las_fichas_vivas_del_cif`
(`('B00000001', 1) == ('B00000001', 2)`), `test_f114_t8_d2_nombre_y_cif_dan_lo_mismo`
(`('B00000001', 'ZETA SUMINISTROS SL', 1) != (…'ALFA OBRAS SL', 2)`) y `test_f114_r15` (falta el `HAVING`). Con
la SQL actual, `4 passed`. El RED fija el caso de D2. La traducción a SQLite (`TOP (?)` ⇒ `LIMIT ?` con el
parámetro al final, sin `COLLATE`) es mínima y no altera la lógica del `GROUP BY`/`HAVING`, que es lo que se prueba.

### Mutación (RM1–RM6 sobre el delta)

- `progress/mutacion_F-114_T8.md` es de la **versión 1** (`3272e04`, subconsulta): 1 mutante, 1 muerto, 446,9 s,
  campaña completa. **RM1:** su SHA no es HEAD y `4630aad` cambia después el fichero del alcance. Recalculado
  sobre el delta real (`alcance_de_feature("F-114", base="1c4b8fb")`): 11 líneas de `sigrid_lookup_client.py`
  (57–64 y 75–77, comentario y literal SQL) y **`generar_mutantes` = 0**. **Prueba de control** (mismo fichero sin
  exclusión de alcance): 51 mutantes ⇒ el cero es legítimo (el generador funciona; un literal SQL no se muta). No
  hace falta relanzar; la SQL la cubren los 4 tests que la ejecutan sobre SQLite.
- **RM2:** el «Tiempo total» de 446,9 s es línea base (157,9 s) + un mutante con 1 worker: coherente. Supera 60 s ⇒
  campaña no reejecutada; además la versión 2 la deja atrás.
- **RM3/RM6:** nada que analizar (0 supervivientes; no se quitó código defensivo). La fila del inventario de F-039
  (61 informes) dice que es de la versión 1 y por qué no se repite.

## 3. Checkpoints (delta)

- **C1** `[x]` init.sh exit 0 (§1).
- **C2** `[x]` rama correcta; F-114 `blocked` y ninguna otra `in_progress`.
- **C3** `[x]` el cambio sigue en `infrastructure/sigrid`; comentario en español con fecha y motivo; tests con datos
  inventados, sin secretos ni datos de terceros (CIF `B0000000x`).
- **C3 bis** N/A: sin documentos de fuera.
- **C4** `[x]` R6/R17 (D2) con test que ejecuta la SQL; tests sin red ni BBDD (SQLite en memoria).
- **C4 bis** `[x]` RED real y reproducida; cobertura N/A con motivo impreso por la puerta; mutación con 0 mutantes
  legítimos (control = 51); «Evidencias» de §6 del informe vigentes más §8.
- **C4 ter** N/A: ninguna ruta sensible tocada.
- **C5** `[ ]` **T8 sigue `[ ]` en `tasks.md` (l.41)**, aunque el informe §8 la da por hecha (resultado, fallo,
  arreglo y medición) y hay commits `F-114 T8: …`. `[ ]` **`features.json` dice `blocked`**, que ya no es el
  estado real: el bloqueo era el fallo de la T8 y está resuelto. `[x]` árbol limpio (mi verificación del RED
  vivió en el scratchpad).

## 4. Cambios requeridos

1. `specs/F-114-proveedor-todos-sigrid/tasks.md` l.41: marcar **T8 `[x]`**, con una nota corta del resultado
   («fallo D2 encontrado y arreglado en `4630aad`; ver `impl_F-114.md` §8»). Si el líder quiere ver la versión del
   `HAVING` en Chrome antes de marcarla (el arreglo solo toca la SQL y las mediciones fueron vía sigrid-api), que
   lo haga ahora; no lo exijo.
2. `harness/features.json`, entrada F-114: `status` de `blocked` a `in_progress` (o el estado que corresponda), y
   quitar el motivo del bloqueo de `progress/current.md` si sigue ahí.

Con esos dos cambios (sin tocar código), la pasada 3 es una comprobación de `tasks.md`, `features.json` e
`init.sh`.

## 5. Observaciones de la pasada 1 que siguen abiertas (no bloquean)

- **O1:** R10 «sin obra» detectado por el texto del error (`app.js` l.2383); mejor `obraInputId && !currentObra()`
  o un test que ate la cadena de `app.py` l.540.
- **O2:** tras elegir en modo global, la etiqueta enseña « · N fichas» hasta la recarga. Cosmético.
- **O3:** `ruff` sin instalar en el venv de sv4.

## 6. Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4 bis: cuando una SQL se prueba por texto (`assert "…" in sql`), pedir al menos un test que la
  **ejecute** sobre datos (SQLite o fixture) si su lógica de agrupado o filtrado es requisito. Los tests de texto
  de la pasada 1 pasaban con la SQL equivocada; los de SQLite de esta pasada la cazan. Vale para cualquier
  proyecto: candidata a `arnes-base`.
