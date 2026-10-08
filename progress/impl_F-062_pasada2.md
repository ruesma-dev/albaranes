<!-- progress/impl_F-062_pasada2.md -->
# F-062 · implementer · Pasada 2 (correcciones de la review pasada 1)

Fichero aparte porque `progress/impl_F-062.md` va por 204/220 líneas. Rama `feature/F-062-proveedor-aplicado`,
worktree `../albaranes-F-062`. Encargo: H1 y M1 de `progress/review_F-062.md` (CHANGES_REQUESTED), con la
**decisión del humano sobre H1 (2026-10-08): opción B**, literal: «la comparación que hace actualmente está bien, el
tema es que no debe quedarse en informativa sino cambiar el proveedor. Este paso será solo defensa, porque en la
revisión del sv2 le pasaremos los proveedores filtrados» (F-055: IA2 elegirá de los proveedores con contrato en la
obra). Entorno: venvs del árbol principal sin tocar, `PYTHONPATH` = comun del worktree; sin `.env`, sigrid-api,
Azure ni BBDD reales; sin git en el árbol principal; suites una tras otra.

## 1. Qué cambió

Commit `c904609` · **F-062 (review): H1 opción B**. La comparación (`_score_razon_social` de F-052) y la regla de
aplicación NO cambian. Cambia el texto, para que diga lo que hace:
- `header_resolver_service.py:624-625`: la nota `[CORREGIDO] Proveedor` dice «…con contrato en la obra 0720 y
  **nombre que casa con el leído**» en vez de «…y nombre completo». Es la única línea de producción tocada (un
  literal de cadena).
- `requirements.md` R3: el score es el de F-052 sin cambios (contención o todas las palabras de 3+ letras de
  cualquiera de los dos como subcadena del otro), **no exige el nombre completo**, con dos ejemplos y la decisión del
  humano. 128/150 líneas.
- `design.md` D2: «Elegible = identificador válido + score de nombre 1,0», qué significa 1,0 y qué no, los
  contraejemplos de H1, la decisión y el test que la fija. 189/250 líneas.
- `docs/ARCHITECTURE.md` regla 17 y `docs/referencia/dominio_negocio_albaranes.md` §10.1: «nombre que casa con el
  leído», qué es, que no exige el nombre completo y que F-062 es la red de seguridad de F-055.
- `progress/spec_F-062.md`: subsección «Q3 revisada tras la review» con la tabla de H1, la decisión literal del
  humano, que F-062 es la red de seguridad de F-055 y que donde §3/Q3 dicen «nombre completo» se lea «score 1,0 de
  F-052» (lo histórico no se reescribe).
- Tests: `test_f062_r3_candidato_claro.py` (docstring + test nuevo, abajo), `test_f062_r6_aplica_candidato.py`
  (R7: la nota dice «nombre que casa con el leído» y no dice «nombre completo»), docstring de
  `test_f062_r10_sin_candidato_claro.py`.

Commit `d4e5691` · **F-062 (review): M1**. `progress/current.md`, subsección «F-062 · MANUAL del humano (comandos
exactos, PowerShell)»:
- **T0b**: `& "<venv de sv3 del árbol principal>\python.exe" "<scratchpad del líder>\diag_f062.py" "<ruta del .env
  con los PG_* de Azure>"` (rutas absolutas escritas en `current.md`). Solo lectura: el script fuerza
  `default_transaction_read_only=on` y aborta si `SHOW transaction_read_only` no da `on`. Criterio: ningún
  `otro_proveedor` en A.1 donde la regla habría dado candidato claro.
- **T12**: `cd …\albaranes\infra`, `. .\00_vars.ps1`, `.\deploy.ps1 -Only sv3`, `.\check_deploy.ps1`, y la
  vigilancia con A.3 (mismo script y comando, bloque `==== A.3 correcciones F-062`), con su criterio y la vuelta atrás
  (`RED_PROVEEDOR_CORRECCION_ENABLED=false`).
- Estado de F-062 al día (review pasada 1 → correcciones → siguiente paso: review pasada 2).

## 2. Test que fija la semántica aceptada (opción B)

`test_f062_r3_opcion_b_un_unico_candidato_con_nombre_que_casa_se_aplica`, parametrizado con **los cuatro casos de la
tabla de H1** (`Hormigones Mat SL`/`HORMIGONES MATERIALES, S.A.`, `Transportes`/`TRANSPORTES PEREZ GARCIA, S.L.`,
`Grupo Hormigones Mat`/`HORMIGONES, S.A.`, `S.L.`/`ARIDOS ANFERSA, S.L.`): comprueba que `_score_razon_social` da
1,0 y que, con el CIF leído `B86056201` inexistente y un único candidato de CIF válido en la obra, la pasada completa
**aplica** el candidato («es el único candidato», `review_required`, nota con «nombre que casa con el leído»). El
comentario del test cita la decisión literal del humano: si alguien endurece el score o la elegibilidad, rompe aquí
y tiene que volver al humano.

## 3. Fase RED (traza real)

Desde `services/albaranes-persistencia`, `PYTHONPATH=<worktree>/services/albaranes-comun`, antes de tocar
`header_resolver_service.py`:
`python -m pytest tests/test_f062_r3_candidato_claro.py tests/test_f062_r6_aplica_candidato.py -q -p no:cacheprovider`
```
>           assert trozo in nota, trozo
E           AssertionError: nombre que casa con el leído
E           assert 'nombre que casa con el leído' in "[CORREGIDO] Proveedor: leído B18437421 → B18487421 (ARIDOS ANFERSA, S.L.). Nombre leído: 'ARIDOS ANFERSA SL'. El CIF ...nico candidato con contrato en la obra 0678 y nombre completo. Si no es el proveedor, cámbialo con «Elegir proveedor»."
FAILED tests/test_f062_r3_candidato_claro.py::test_f062_r3_opcion_b_un_unico_candidato_con_nombre_que_casa_se_aplica[subcadena-mat]
FAILED tests/test_f062_r3_candidato_claro.py::test_f062_r3_opcion_b_un_unico_candidato_con_nombre_que_casa_se_aplica[una-palabra]
FAILED tests/test_f062_r3_candidato_claro.py::test_f062_r3_opcion_b_un_unico_candidato_con_nombre_que_casa_se_aplica[contiene-al-otro]
FAILED tests/test_f062_r3_candidato_claro.py::test_f062_r3_opcion_b_un_unico_candidato_con_nombre_que_casa_se_aplica[solo-forma-juridica]
FAILED tests/test_f062_r6_aplica_candidato.py::test_f062_r7_motivo_y_nota_de_la_correccion[19407]
FAILED tests/test_f062_r6_aplica_candidato.py::test_f062_r7_motivo_y_nota_de_la_correccion[19394]
FAILED tests/test_f062_r6_aplica_candidato.py::test_f062_r7_motivo_y_nota_de_la_correccion[1790636816]
7 failed, 63 passed in 3.74s
```
Con `-k opcion_b`, los cuatro fallan **solo** en la aserción de la nota
(`assert "nombre que casa con el leído" in aplicada["nota"]`): el score 1,0 y la aplicación ya eran así, que es lo
que el humano acepta. GREEN tras cambiar la frase: `test_f062_r3_*`, `r6_*`, `r10_*`, `r14_*`: **112 passed in
2.70s**.

## 4. Resultado real de las suites (2026-10-08, una tras otra)

- **sv3** (`coverage run -m pytest -q`, sin deselección): **548 passed, 1 failed** in 93.91 s. El KO es el de entorno
  ya conocido y verificado por el reviewer: `test_f052_t19_script_arranca_como_script_desde_otra_carpeta`
  (`ModuleNotFoundError: No module named 'ruesma_comun.proveedores'`: lanza el script sin `PYTHONPATH` y el venv del
  árbol principal importa el comun de `dev`). 548 = 544 de la pasada 1 + 4 nuevos.
- **comun**: no se toca; no se reejecuta (pasada 1: 417 passed, 3 skipped).
- **raíz** (`python -m pytest tests -q`): **1083 passed** in 521.20 s.
- `python -m harness.cobertura --base dev --config harness/rigor.json`: **`PUERTA COBERTURA: 100.0% de 203 líneas
  cambiadas cubiertas (203/203, umbral 80%, nivel critico)`**.
- `python -m harness.tamano --feature F-062`: dentro de los topes (requirements 128/150, design 189/250, impl
  204/220, review 138/140).
- `ruff` desde la raíz de sv3 sobre los tests tocados: limpio (se ordenó el bloque de imports del test de R3); los
  avisos de `header_resolver_service.py` (I001, RUF023, RUF100) son anteriores y no se tocan.
- `bash harness/init.sh` **no** se lanzó en el worktree: daría los mismos 2 KO de entorno de la pasada 1 (§6 de
  `impl_F-062.md`); la definitiva es la del árbol principal tras fusionar (T13).

## 5. Mutación (C4 bis): la campaña de `f3d4174` sigue valiendo

Solo cambia un literal de cadena en producción y `harness.mutacion` no tiene operador sobre `str` (solo comparación,
aritmética, lógicos, `not`, booleanos y enteros). Recálculo con `harness.alcance` + `generar_mutantes`, `dev..f3d4174`
frente a `dev..HEAD`: **9 ficheros, 612 líneas, 104 mutantes en ambos**, e **idénticos** comparando (fichero, texto
de la línea, columna, original, mutado, operador). Los tests solo crecen, así que los 104 siguen muertos. No se
relanzó la campaña (20,5 min). Si el reviewer exige el SHA de HEAD en RM1, el comando es el de §9 de
`impl_F-062.md`.

## 6. Fuera de alcance y lo que falta

- **B1 y B2** (BAJA, «recomendado» en la review): no están en el encargo de esta pasada; siguen abiertos.
- `harness/features.json` (y por tanto `BACKLOG.md`): la descripción de F-062 todavía dice «nombre completo»; no la
  toco (la ficha la mantiene el líder).
- `progress/impl_F-062.md` §1 cita la nota antigua («…y nombre completo»): es el informe de la pasada 1 y queda como
  histórico; la vigente es la de §1 de este fichero.
- MANUAL del humano: T0b (opcional) y T12, con comando en `progress/current.md`. T13: `init.sh` en el árbol
  principal tras fusionar.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv3 548 passed + 1 KO de entorno conocido (93.9 s, con coverage); raíz 1083 passed (521.2 s); comun sin cambios. Nuevos en esta pasada: 4 (parametrizados) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 203 líneas cambiadas cubiertas (203/203, umbral 80%, nivel critico)` |
| Mutación | Campaña de `f3d4174` válida para HEAD: 104 generados, 104 muertos, 0 supervivientes; recálculo HEAD = 104 mutantes idénticos (§5) |
| Tiempo de la suite | sv3 93.9 s con coverage (pasada 1: 14 s; no investigado, sin otra suite en paralelo); raíz 521.2 s |
