<!-- progress/impl_F-051_t21_previa.md -->
# F-051 · T21 (previa) · Ground truth del banco a almacén

Worktree `albaranes-F-051`, rama `feature/F-051-almacen-por-linea`. Encargo del líder tras la review
de la pasada 2 (`progress/review_F-051_pasada2.md`, «Para el humano» 2). Viene de `impl_F-051_pasada2.md` §8.

Decisión del humano (opción a): actualizar el ground truth a la regla de F-051. Commits `93e23e2`
(RES-001…006) y `a6b9bef` (RES-007, aparte para poder revertirlo solo).

**Representación: `null` (celda vacía), no `ALMACEN`.** El comparador (`evals/comparador.py`,
`equivalentes`) solo da por buena una partida vacía si el esperado es `null`; no normaliza `ALMACEN`.
Las 12 líneas de almacén del banco que usan el literal (ALQ-001 L1-L3, GEN-002 L8, GEN-010 L1,
HOR-005 L1-L5 y su sintética, MOR-003 L1-L2) **ya salían ROJO** contra el `None` del sistema, antes y
después de F-051. Con `ALMACEN`, las 24 discrepancias seguirían allí con otro texto. `null` es lo que
dicen el README (celda vacía ⇒ `null`) y ARCHITECTURE (partida final vacía = almacén). Esas 12 no las he
tocado: fuera del encargo (ver «Para el humano»).

**Búsqueda del patrón en todo el banco.** Las 110 líneas de `inputs` llevan `codigo_imputacion` null, e
IA1 tiene `?` en todas. Por tanto el banco no dice qué partida va impresa: solo se puede saber si el
esperado sale del contrato. Solo RES-001…007 traen líneas de contrato (lo dice también el `_doc` de la
instantánea de F-045 R17). Los siete esperaban `CI.03A.7`, la partida del contrato:
- RES-001…006: la línea casa con su línea de contrato. Es el patrón exacto.
- RES-007: según el ground truth la línea NO casa (precio `oferta`), pero su partida solo puede salir del
  contrato CTSU24/0402, el mismo de RES-006. Con F-051 va a almacén por R1 y, si no casa, por R3.
- RES-010…019 (`CI.03A.7`), RES-008/009 y los demás no tienen contrato en el banco. No se puede afirmar
  el patrón y no los he tocado.

| Caso | Línea | Campo (fase) | Antes → después |
|---|---|---|---|
| RES-001…RES-007 (cada uno) | 1 | `IA3.lineas_valoradas.codigo_partida_final` | `CI.03A.7` → `null` |
| ídem | 1 (sintética de residuos) | `IA3.sinteticas_esperadas.codigo_partida` | `CI.03A.7` → `null` |
| ídem | 1 | `final.lineas.partida_final` | `CI.03A.7` → `null` |
| ídem | 1 (añadida) | `final.lineas_anadidas.partida` | `CI.03A.7` → `null` |

28 campos en total (24 de RES-001…006 y 4 de RES-007). En cada fila tocada, el motivo va al final de su
`comentario`, separado por « | ». Ese campo es laxo y no es observable. Del fixture no ha cambiado nada más.

**Efecto en otra feature (F-045 R17).** `tests/datos/afirmado_por_el_humano_RES.json` pierde esas 28
claves. Es el procedimiento que pide el propio test ante un cambio legítimo del humano. Sin ese cambio, el
guardián falla: `1 failed, 4 passed`, «24 valor(es) afirmados por el humano han desaparecido». Con él:
`5 passed`.

**Verificación (evals deterministas, sin LLM, en el scratchpad).** Comando: `python -m evals.runner
--informes <scratchpad>`. Comparo el detalle FALLO/AVISO, ordenado, antes y después:
- Base `ab73395`: 1025 entradas.
- Tras `93e23e2`: 1001. Desaparecen las 24 de RES-001…006 y no aparece ninguna nueva. RES-001…006 pasan
  a VERDE en IA3 y E2E, y el resto del informe es idéntico.
- Tras `a6b9bef`: 997. Desaparecen 4 de RES-007 (eran previas a F-051) y no aparece ninguna nueva.
  RES-007 sigue ROJO por precio y cantidad.

El veredicto global sigue ROJO por la deuda previa: casos sin contrato en el banco, IA3 sin LLM.

`bash harness/init.sh` (tal cual, en el worktree, sobre `a6b9bef` más este papeleo): **«ENTORNO LISTO»**, ningún
`[KO]`. Raíz `1083 passed in 236.09s`, que incluye el guardián de F-045. Los servicios salen `[OK]` desde la caché.
`PUERTA COBERTURA` 98,5 % y `PUERTA TAMAÑO` dentro. Avisos, los de siempre: ruff 1181,
`RUTAS SENSIBLES [evals]` (falta `progress/evals_F-051.md`, que es T21), infra sin tests y `[ADAPTAR]` ajenos.

**Para el humano.** (1 y 2 resueltos el mismo día: ver «2.ª tanda» al final.)
1. **Los libros `.xlsx` mandan.** Hay que poner las mismas 28 celdas vacías en `IA3_valoracion.xlsx`
   (`codigo_partida_final`, `codigo_partida`) y `RESULTADO_FINAL.xlsx` (`partida_final`, `partida`). Si no,
   el próximo `python -m evals.conversor` devuelve `CI.03A.7` y el guardián de F-045 salta.
2. **¿`ALMACEN` = vacío?** Las 12 líneas con el literal fallan siempre. Hay dos salidas: vaciarlas en el
   libro (como aquí) o que el comparador trate `ALMACEN` como `null`, que es cambiar código de evals.
3. **Hueco del guardián:** trata `null` como «no afirmado», así que no vigila que esas 28 sigan vacías.
4. RES-007: si no se da por bueno, `git revert a6b9bef`.

**Comandos (PowerShell, desde la raíz del worktree; se facturan, autorizar antes).** Los PDF de los casos
no se versionan y el worktree no los tiene: sin ellos, IA1/IA2 salen OMITIDO. Se enlazan con una
*junction* (`evals/inputs/` está en `.gitignore`), que se quita con `cmd /c rmdir evals\inputs` ANTES de
`git worktree remove` (H6).
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-051
cmd /c mklink /J evals\inputs C:\Users\pgris\PycharmProjects\albaranes\evals\inputs
$env:GEMINI_API_KEY = Read-Host 'GEMINI_API_KEY'   # IA1 (primario) e IA3/IA4
$env:OPENAI_API_KEY = Read-Host 'OPENAI_API_KEY'   # IA2 (primario)
C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe -m evals.runner --con-llm --feature F-051
```
- El runner no lee `.env`: las claves tienen que estar en el entorno de la sesión. Si falta una, para sin
  consumir ningún caso.
- Opcionales: `IA_PRIMERA_FASE`/`IA_SEGUNDA_FASE` (por defecto `gemini`/`openai`) y
  `GEMINI_MODEL`/`OPENAI_MODEL`.
- Salida: `progress/evals_F-051.md`.

**T23** (sv2 del worktree, que lleva el prompt de F-051, con el venv de sv2 del árbol principal). El
worktree no tiene `.env` y no se copia: todo va por variables de sesión. Primera consola:
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-051\services\albaranes-api
$env:GEMINI_API_KEY = Read-Host 'GEMINI_API_KEY'; $env:OPENAI_API_KEY = Read-Host 'OPENAI_API_KEY'
$env:ENABLE_CLAUDE = 'false'
C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-api\.venv\Scripts\python.exe main.py
```
Segunda consola, por cada uno de los cinco albaranes:
`(curl.exe -s -F "file=@C:\ruta\albaran.pdf" http://127.0.0.1:8000/v1/albaranes/extract/phase-1 | ConvertFrom-Json).data.lineas | Select-Object codigo_imputacion, descripcion`

## 2.ª tanda (2026-10-05): almacén = partida vacía en el banco y libros sincronizados

Decisión del humano sobre «Para el humano» 1 y 2: el literal de almacén también pasa a `null`, y los libros mandan.
Commits `d1a061c` (fixtures de almacén) y `016b063` (fixtures regenerados desde los libros).

**1. Fixtures (`d1a061c`).** Hay 10 ficheros, no 6: HOR-005 y MOR-003 llevan `almacen` en minúscula. Son 12
líneas, 26 campos y ningún otro cambio. El motivo va al final del `comentario`, separado por « | »: «F-051 (decision
del humano 2026-10-05): almacen = partida vacia, tambien en el banco; antes esperaba el literal ALMACEN|almacen».

| Caso | Líneas | IA3 | final |
|---|---|---|---|
| ALQ-001 | L1-L3 | `lineas_valoradas.codigo_partida_final` | `lineas.partida_final` |
| GEN-002 | L8 | ídem | ídem |
| GEN-010 | L1 | ídem | ídem |
| HOR-005 | L1-L5 + sintética (base 4) | ídem + `sinteticas_esperadas.codigo_partida` | ídem + `lineas_anadidas.partida` |
| MOR-003 | L1-L2 | ídem | ídem |

Los demás libros no tienen partida esperada para estos casos. IA1 `codigo_imputacion` está en `?`. En INPUTS,
`contrato_lineas.codigo_partida` es entrada, no esperado, y no se toca. El guardián de F-045 solo vigila los RES:
`5 passed`, sin regenerar `afirmado_por_el_humano_RES.json`.

**2. Libros (árbol principal, no versionados).** Antes de tocar nada, comprobé que `python -m evals.conversor
--ground-truth <libros> --fixtures <scratch>` reproducía byte a byte los fixtures de `ab73395`.
- La copia de seguridad la hace `evals.revision.escritura.copia_de_seguridad`, la función del repo.
  - `ground_truth/copias/IA3_valoracion.xlsx.20261005-1759.xlsx`
  - `ground_truth/copias/RESULTADO_FINAL.xlsx.20261005-1759.xlsx`
  - Su sha256 (`5df41714…`, `9a0869b9…`) es el `sha256_libro` que llevaban los fixtures, así que son el libro de antes.
- La escritura usa openpyxl celda a celda (`cell.value`), sin insertar ni borrar filas. Los libros no tienen
  fórmulas, validaciones ni formato condicional.
- El script de un solo uso está en el scratchpad y no se versiona. Localiza las tablas por su título, igual que
  el conversor, y empareja cada fila del libro con la de su fixture. Aborta ante cualquier diferencia que no sea
  partida → vacía o comentario.
- Celdas escritas: 108 (54 por libro). Sin el comentario, el conversor revertiría el motivo de los fixtures.

| Libro | Partida → vacía | Comentario con motivo |
|---|---|---|
| `IA3_valoracion.xlsx` | 27: RES-001…007 (E y H en `Residuos`), ALQ/GEN/HOR/MOR (columna E; HOR-005 sintética H60) | 27 (J/I) |
| `RESULTADO_FINAL.xlsx` | 27: RES-001…007 (H y F en `Residuos`), ALQ/GEN/HOR/MOR (columna H; HOR-005 añadida F95) | 27 (M/H) |

Las 54 son las 28 de RES-001…007 y las 26 de almacén. Al repetir la simulación después, quedan 0 celdas pendientes.

**3. Regeneración (`016b063`).** `python -m evals.conversor --ground-truth C:\...\albaranes\evals\ground_truth`,
lanzado en el worktree. Escribe 264 ficheros. `git diff`: 120 ficheros, una línea cada uno. Solo cambia el
`sha256_libro` de IA3 y final (59 casos + `_indice.json` cada uno; ahora `5370ea49…` y `37257822…`). IA1, IA2, IA4
e INPUTS no cambian. Libros y fixtures quedan sincronizados. Un `git diff` sin `--strip-trailing-cr` marca enteros
los 10 ficheros de `d1a061c`, pero es solo el fin de línea de la copia de trabajo (LF en lugar de CRLF; el índice es
LF en ambos casos). La regeneración los deja como los demás.

**4. Verificación (evals deterministas, sin LLM, `--informes <scratch>`).** Detalle FALLO/AVISO ordenado:
- Antes (sobre `8be1f49`): 997.
- Tras `d1a061c`: 972. Desaparecen las 26 de partida de almacén. HOR-005 suma 1 y resta 1: es la misma
  `sinteticas_esperadas[4]`, que sigue sin casar con la producida por otro motivo y ahora enseña
  `'codigo_partida': None` en su esperado. No hay ninguna discrepancia nueva. FALLOS por caso: ALQ-001 12→9,
  GEN-002 23→22, GEN-010 4→3, HOR-005 21→16, MOR-003 8→6 (IA3). El resto del informe es idéntico.
- Tras `016b063`: el detalle es idéntico byte a byte al de `d1a061c`.

Guardián F-045 + tests del conversor (`test_f045_r17…`, `test_f011_r5…`, `test_f011_r1_r2_r3…`): `22 passed`.

**Para el humano.**
- **El importador puede deshacerlo.** `python -m evals.revision` funde con `fundir`, que solo se niega a degradar
  a `?`. Si el Excel de revisión de origen sigue trayendo `CI.03A.7` o `ALMACEN` en esas filas, la próxima
  importación los vuelve a escribir. Hay que corregirlo también en ese Excel, o revisar el diff tras importar.
- Sigue abierto el punto 3 de arriba: el guardián no vigila que las 54 sigan vacías.

**`bash harness/init.sh`** (tal cual, en el worktree, sobre `016b063` + este papeleo): **«ENTORNO LISTO»**, ningún `[KO]`. Raíz
`1083 passed in 281.38s` (incluye el guardián de F-045 y los tests del conversor); servicios `[OK]` desde caché;
`PUERTA COBERTURA` 98,5 %; `PUERTA TAMAÑO` dentro. Avisos, los de siempre (ruff 1181, `RUTAS SENSIBLES [evals]` = T21,
infra sin tests, `[ADAPTAR]` ajenos).
