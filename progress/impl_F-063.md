<!-- progress/impl_F-063.md -->
# F-063 · Informe del implementer — El CIF de Construcciones Ruesma nunca es el proveedor

Rama `feature/F-063-cif-propio-no-es-proveedor` (worktree `../albaranes-F-063`, desde `dev` `ba72f0a`). Rigor
**critico**. Spec mínima escrita por el implementer por encargo del líder (arreglo urgente, propuesta aprobada por el
humano): `specs/F-063-cif-propio-no-es-proveedor/` (requirements 94 líneas, design 83, tasks 14).

## 1. Qué cambió

| Tarea | Commit | Qué |
|---|---|---|
| T0 | `27ae472` | Spec, F-063 en `features.json` (`in_progress`, prioridad 1, `critico`, `branch`), `BACKLOG.md`, nota en `current.md` |
| T1 | `538a21a` | comun: `ruesma_comun/proveedores/propios.py` (`CIFS_PROPIOS_POR_DEFECTO`, `cifs_propios`, `es_cif_propio`) |
| T2 | `56b4af4` | sv3: constantes `MOTIVO_PROVEEDOR_CIF_PROPIO` / `NOTA_CIF_PROPIO_PREFIJO`, puerto y `descartar_cif_propio` del repo |
| T3 | `852c925` | sv3: `_descartar_cif_propio` al principio de `_resolve_proveedor`; setting `CIFS_PROPIOS`; cableado worker y API |
| T4 | `72c7ebf` | sv3: `_no_es_propio` filtra candidatos en paso 1 (obra), paso 2 (global) y `_candidatos_puntuados` (red) |
| T5 | `78bbdcc` | Doble `fixture_f063` (obra 0694, FEYMACO, Ruesma en `prv`) y tests de pipeline en las tres rutas |
| T6 | `9af7766` | `docs/ARCHITECTURE.md` regla 18 y `CIFS_PROPIOS=` en `services/albaranes-persistencia/.env.example` |
| T7 | `cd21caa`, `7d799e7` | Cobertura, mutación (`progress/mutacion_F-063.md`), este informe, orden de imports de los tests |

Ficheros de producción: `services/albaranes-comun/ruesma_comun/proveedores/{__init__,propios}.py`;
`services/albaranes-persistencia/` → `application/services/header_resolver_service.py`, `config/settings.py`,
`domain/models/header_resolution_models.py`, `domain/ports/header_resolver_ports.py`,
`infrastructure/database/sqlalchemy_albaran_repository.py`, `interface_adapters/composition.py`,
`interface_adapters/api/app.py`. Tests: `services/albaranes-comun/tests/test_f063_cifs_propios.py` (16 casos),
`services/albaranes-persistencia/tests/test_f063_cif_propio.py` (35 casos) y `tests/doble_sigrid_api.py` (fixture).
sv4 no se toca (pinta los motivos en crudo, `proveedor_cif_propio:A81873903` incluido). `azure-apps/` no cambia: sv3 no
expone ni consume nada nuevo (y allí no se documentan sus variables de entorno).

## 2. Comportamiento resultante

- Un CIF propio (A81873903 de serie, ampliable con `CIFS_PROPIOS`, nunca reducible) con origen distinto de `manual`
  se descarta al empezar `_resolve_proveedor`, ANTES de la red por CIF: una escritura deja CIF y origen a NULL,
  `review_required=true`, motivo `proveedor_cif_propio:A81873903` y nota «[AVISO] CIF del cliente: la IA leyó el CIF
  del cliente (A81873903, Construcciones Ruesma) como CIF del proveedor; se descarta y el proveedor se busca por
  nombre.». El nombre leído no se toca. Luego sigue el camino «sin CIF» (el que acertó con FEYMACO el 2026-10-08).
- Nunca se consulta `prv` con el CIF propio ni se canoniza el nombre al del cliente; la búsqueda de contratos, que
  lee el CIF del merge después, usa el deducido.
- Un CIF propio nunca sale como candidato (obra, global, propuesta F-052, candidato claro F-062).
- Origen `manual` (el revisor lo eligió) ⇒ se respeta y se loguea. Escritura fallida ⇒ log y se sigue sin CIF.

## 3. Decisiones y desviaciones (justificadas)

- **D1 · Prefijo de la nota** (desviación del texto pedido por el líder, «[AVISO] Proveedor: …»): ese prefijo lo
  borra `_remove_nota_proveedor_safely` en la MISMA pasada cuando el camino «sin CIF» resuelve por nombre, y en cada
  re-pasada con CIF: la nota no llegaría nunca al revisor. Se usa `[AVISO] CIF del cliente` (mismo motivo y misma
  solución que `[CORREGIDO] Proveedor` de F-062 · D6). El texto de la nota conserva la frase pedida.
- **R9 (no pedido literalmente, añadido en la spec)**: excluir el CIF propio de los candidatos. Sin esto, la propia
  F-062 aplicaba Ruesma como «candidato claro» si aparecía en la lista de la obra con un nombre leído de Ruesma (lo
  prueba la traza RED de T4, §4), y un merge ya canonizado a Ruesma volvería a Ruesma por la búsqueda global.
- **Sin interruptor** (D4): la vuelta atrás es la revisión anterior de la Container App de sv3.
- **Revisor manda** (D2, recomendado por el líder): con origen `manual` no se descarta.
- La regla vive en el resolver, así que con `HEADER_RESOLVER_ENABLED=false` no actúa (como el resto de redes).

## 4. Fase RED (trazas reales; comandos desde la raíz del servicio, `PYTHONPATH` = comun del worktree)

**T1 · comun (R1, R2)** — antes de `propios.py`:
```
$ (services/albaranes-comun) python -m pytest tests/test_f063_cifs_propios.py -q
E   ImportError: cannot import name 'CIFS_PROPIOS_POR_DEFECTO' from 'ruesma_comun.proveedores' (...\ruesma_comun\proveedores\__init__.py)
ERROR tests/test_f063_cifs_propios.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.65s
```

**T2 · repositorio (R4, R10)** — antes de las constantes y de `descartar_cif_propio`:
```
$ (services/albaranes-persistencia) python -m pytest tests/test_f063_cif_propio.py -q
E   ImportError: cannot import name 'MOTIVO_PROVEEDOR_CIF_PROPIO' from 'domain.models.header_resolution_models'
1 error in 5.24s
(tras añadir solo las dos constantes de dominio)
E       AttributeError: 'SqlAlchemyAlbaranRepository' object has no attribute 'descartar_cif_propio'
FAILED tests/test_f063_cif_propio.py::test_f063_r4_repo_descarta_cif_y_origen_y_marca_revision_sin_tocar_el_nombre
FAILED tests/test_f063_cif_propio.py::test_f063_r10_repo_descartar_dos_veces_no_duplica_y_la_nota_se_sustituye
FAILED tests/test_f063_cif_propio.py::test_f063_r4_repo_descartar_sobre_un_merge_que_no_existe_lanza
3 failed, 1 passed in 5.32s
```

**T3 · resolver (R3–R8, R10)** — tests escritos con T2 ya hecho, antes de tocar el resolver:
```
$ (services/albaranes-persistencia) python -m pytest tests/test_f063_cif_propio.py -q
E       AssertionError: assert [] == [('proveedor_...por nombre.')]
E         Right contains one more item: ('proveedor_cif_propio:A81873903', '[AVISO] CIF del cliente: la IA leyó el CIF del cliente (A81873903, Construcciones Ruesma) como CIF del proveedor; se descarta y el proveedor se busca por nombre.')
E       AssertionError: assert 'A81873903' is None
E        +  where 'A81873903' = <test_f063_cif_propio.RepoF063 object at 0x000002001313C4A0>.cif
E       AssertionError: assert ['A81873903'] == []
E         Left contains one more item: 'A81873903'
E       assert 0 == 1
E       TypeError: HeaderResolverService.__init__() got an unexpected keyword argument 'cifs_propios'
E       KeyError: 'cifs_propios'
E       assert 'cifs_propios=cifs_propios(settings.cifs_propios)' in '# interface_adapters/composition.py """Composition root ...'
FAILED tests/test_f063_cif_propio.py::test_f063_r4_r5_resolver_descarta_el_cif_del_cliente_y_resuelve_feymaco_por_nombre[A81873903]
FAILED tests/test_f063_cif_propio.py::test_f063_r4_r5_resolver_descarta_el_cif_del_cliente_y_resuelve_feymaco_por_nombre[ a-81873903]
FAILED tests/test_f063_cif_propio.py::test_f063_r4_r5_resolver_descarta_el_cif_del_cliente_y_resuelve_feymaco_por_nombre[ESA81873903]
FAILED tests/test_f063_cif_propio.py::test_f063_r12_resolver_sin_candidato_deja_el_merge_sin_cif_con_nota_y_motivo
FAILED tests/test_f063_cif_propio.py::test_f063_r7_resolver_con_la_escritura_fallida_sigue_sin_cif_y_no_canoniza_al_cliente
FAILED tests/test_f063_cif_propio.py::test_f063_r10_resolver_re_pasada_no_duplica_ni_vuelve_a_descartar
FAILED tests/test_f063_cif_propio.py::test_f063_r3_resolver_usa_la_lista_que_recibe
FAILED tests/test_f063_cif_propio.py::test_f063_r3_setting_con_su_alias_y_defecto_vacio
FAILED tests/test_f063_cif_propio.py::test_f063_r3_los_dos_puntos_de_composicion_cablean_los_cif_propios[interface_adapters/composition.py]
FAILED tests/test_f063_cif_propio.py::test_f063_r3_los_dos_puntos_de_composicion_cablean_los_cif_propios[interface_adapters/api/app.py]
10 failed, 7 passed in 6.29s
(los 7 que pasan: los 4 de T2 y los controles R6, R8 «CIF normal» y R8 «sin CIF», que fijan el comportamiento previo)
```

**T4 · candidatos (R9)** — antes de los filtros (la última traza es F-062 APLICANDO a Ruesma):
```
$ (services/albaranes-persistencia) python -m pytest tests/test_f063_cif_propio.py -q -k candidato
E       AssertionError: assert 'A81873903' is None
E        +  where 'A81873903' = <test_f063_cif_propio.RepoF063 object at 0x000001E8C4ED24E0>.cif
E       AssertionError: assert 'A81873903' is None
E        +  where 'A81873903' = <test_f063_cif_propio.RepoF063 object at 0x000001E8C4F115B0>.cif
E       AssertionError: assert 'A81873903' is None
E        +  where 'A81873903' = <test_f063_cif_propio.RepoF063 object at 0x000001E8C4F11160>.cif
E       assert [{'cif': 'A81...proveedor».'}] == []
E         Left contains one more item: {'cif': 'A81873903', 'nombre': 'CONSTRUCCIONES RUESMA, S.A.', 'motivo': 'proveedor_cif_corregido:B86056201>A81873903', ...}
FAILED tests/test_f063_cif_propio.py::test_f063_r9_candidato_paso1_la_obra_nunca_devuelve_el_cif_propio
FAILED tests/test_f063_cif_propio.py::test_f063_r9_candidato_paso1_obra_con_solo_el_cif_propio_es_obra_sin_candidatos
FAILED tests/test_f063_cif_propio.py::test_f063_r9_candidato_paso2_la_busqueda_global_nunca_devuelve_el_cif_propio
FAILED tests/test_f063_cif_propio.py::test_f063_r9_candidato_red_por_cif_ni_aplica_ni_propone_el_cif_propio
4 failed, 2 passed, 17 deselected in 4.25s
(pasan el control de paso 2 con otro proveedor y el de R12, que -k también selecciona)
```

**T5 · pipeline (R11, R12)** — los tests se escribieron tras T3/T4, así que la fase RED se demuestra contra el resolver de `dev` restaurado después en bytes (control negativo):
```
$ (services/albaranes-persistencia) git show dev:services/albaranes-persistencia/application/services/header_resolver_service.py > application/services/header_resolver_service.py
$ python -m pytest tests/test_f063_cif_propio.py -q -k "pipeline"
E       AssertionError: assert ('A81873903',..., S.A.', 'ia') == ('A28733558',...eterministic')
E         At index 0 diff: 'A81873903' != 'A28733558'          (x3: nuevo, duplicado, reenrich)
E       AssertionError: assert 'A81873903' is None
E        +  where 'A81873903' = <test_f063_cif_propio.MergeF063 object at 0x00000232CC14B650>.cif   (x3)
FAILED tests/test_f063_cif_propio.py::test_f063_r11_pipeline_el_albaran_de_feymaco_acaba_con_feymaco_y_su_contrato[nuevo]
FAILED tests/test_f063_cif_propio.py::test_f063_r11_pipeline_el_albaran_de_feymaco_acaba_con_feymaco_y_su_contrato[duplicado]
FAILED tests/test_f063_cif_propio.py::test_f063_r11_pipeline_el_albaran_de_feymaco_acaba_con_feymaco_y_su_contrato[reenrich]
FAILED tests/test_f063_cif_propio.py::test_f063_r12_pipeline_sin_candidato_queda_sin_cif_con_nota_y_motivo[nuevo]
FAILED tests/test_f063_cif_propio.py::test_f063_r12_pipeline_sin_candidato_queda_sin_cif_con_nota_y_motivo[duplicado]
FAILED tests/test_f063_cif_propio.py::test_f063_r12_pipeline_sin_candidato_queda_sin_cif_con_nota_y_motivo[reenrich]
$ git checkout -- application/services/header_resolver_service.py ; git diff -- (fichero) | wc -c  ->  0 bytes
```

## 5. Controles negativos

- **Sin la regla se reproduce la incidencia** (`test_f063_r11_control_negativo_sin_la_regla_se_reproduce_la_incidencia`,
  3 rutas): con `cifs_propios=frozenset()` el merge acaba en `('A81873903', 'CONSTRUCCIONES RUESMA, S.A.')` y la
  búsqueda en `ninguno`, exactamente lo de producción.
- **Resolver de `dev` en bytes** (traza **T5 · pipeline (R11, R12)** — los tests se escribieron tras T3/T4, así que la fase RED se demuestra contra el resolver de `dev` restaurado después en bytes (control negativo):
```
$ (services/albaranes-persistencia) git show dev:services/albaranes-persistencia/application/services/header_resolver_service.py > application/services/header_resolver_service.py
$ python -m pytest tests/test_f063_cif_propio.py -q -k "pipeline"
E       AssertionError: assert ('A81873903',..., S.A.', 'ia') == ('A28733558',...eterministic')
E         At index 0 diff: 'A81873903' != 'A28733558'          (x3: nuevo, duplicado, reenrich)
E       AssertionError: assert 'A81873903' is None
E        +  where 'A81873903' = <test_f063_cif_propio.MergeF063 object at 0x00000232CC14B650>.cif   (x3)
FAILED tests/test_f063_cif_propio.py::test_f063_r11_pipeline_el_albaran_de_feymaco_acaba_con_feymaco_y_su_contrato[nuevo]
FAILED tests/test_f063_cif_propio.py::test_f063_r11_pipeline_el_albaran_de_feymaco_acaba_con_feymaco_y_su_contrato[duplicado]
FAILED tests/test_f063_cif_propio.py::test_f063_r11_pipeline_el_albaran_de_feymaco_acaba_con_feymaco_y_su_contrato[reenrich]
FAILED tests/test_f063_cif_propio.py::test_f063_r12_pipeline_sin_candidato_queda_sin_cif_con_nota_y_motivo[nuevo]
FAILED tests/test_f063_cif_propio.py::test_f063_r12_pipeline_sin_candidato_queda_sin_cif_con_nota_y_motivo[duplicado]
FAILED tests/test_f063_cif_propio.py::test_f063_r12_pipeline_sin_candidato_queda_sin_cif_con_nota_y_motivo[reenrich]
$ git checkout -- application/services/header_resolver_service.py ; git diff -- (fichero) | wc -c  ->  0 bytes
```): fichero restaurado con `git checkout`, `git diff` = 0 bytes.
- **CIF normal** (FEYMACO bien leído) en resolver y en las tres rutas: sin descarte, sin motivo, canonización y
  contrato como antes. **Sin CIF**: sin descarte. **CIF añadido por configuración** solo se descarta si se configura.

## 6. `bash harness/init.sh`

Tal cual (con `PYTHONPATH` al comun del worktree), sobre `cd21caa`: **2 KO, los dos de entorno del worktree, los
mismos que F-062 §6**: raíz 1083 passed; comun 433 passed, 3 skipped; sv1/sv2/sv4/sv5/sv6 en verde (caché);
`[KO] sv3: 1 failed, 394 passed` (`test_f052_t19_script_arranca_como_script_desde_otra_carpeta`: lanza el script de
F-052 **sin** `PYTHONPATH` y el venv del árbol principal importa el comun de `../albaranes`, que aún no tiene
`propios.py` ⇒ `ImportError: cannot import name 'CIFS_PROPIOS_POR_DEFECTO'`) y, por el `-x`, `[KO] PUERTA COBERTURA:
50.8%` (el `coverage.json` de sv3 queda a medias). Ruff subió a 1193 por el orden de imports de los dos tests
nuevos; corregido en `7d799e7` (vuelve a 1190, como `dev`).

Contraprueba sobre `7d799e7`, misma orden con `PYTEST_ADDOPTS="--deselect <ese test>"`: raíz 1083 passed; sv3 583
passed, 1 deselected; comun 433 passed, 3 skipped; `[OK] PUERTA COBERTURA: 96.6% de 59 líneas cambiadas cubiertas
(57/59, umbral 80%, nivel critico)`; `[OK] PUERTA TAMAÑO (requirements 94/150, design 83/250, impl 194/220)`;
**`ENTORNO LISTO. Puedes trabajar.`** Después se borró `.arnes_cache/suite_sv3-persistencia.ok` para que un `init.sh`
posterior no dé sv3 por verde con esa deselección. **T9 queda sin marcar**: repetir `bash harness/init.sh` tal cual
en el árbol principal tras fusionar en `dev` (con comun fusionado, el test de entorno pasa).

## 7. MANUAL pendiente (humano)

- **T8**: tras fusionar en `dev` y con `init.sh` en verde en el árbol principal, desplegar SOLO sv3
  (`cd C:\Users\pgris\PycharmProjects\albaranes\infra; . .\00_vars.ps1; .\deploy.ps1 -Only sv3; .\check_deploy.ps1`)
  y en sv4 pulsar «Solo volver a buscar» en el albarán de FEYMACO. Criterio: merge con A28733558 y contrato
  encontrado. Los merges `b1d3e179-…` y `401d9c00-…` ya tienen el nombre canonizado a «CONSTRUCCIONES RUESMA, S.A.»:
  el re-proceso descarta el CIF pero no recupera el nombre leído (sin backfill, fuera de alcance); allí el revisor
  elige FEYMACO con «Elegir proveedor» (la nota `[AVISO] Proveedor sin CIF` lista los candidatos de la obra).
- Vigilancia (solo lectura): merges con `proveedor_cif_propio:` en `review_reasons_json`.

## 8. Fuera de alcance

Backfill de merges ya canonizados; la IA leyendo también el NOMBRE del cliente (entonces la búsqueda por nombre de
la obra podría casar con otro «CONSTRUCCIONES …»; el caso no se ha visto); usar la lista en sv2 (prompt) o sv4.

## 9. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-063 | comun 16 passed (0,06 s); sv3 35 passed (3,2 s) |
| Suites completas (worktree) | comun 433 passed, 3 skipped (165 s); sv3 583 passed, 1 deselected (9,7–19,5 s; el deseleccionado es el KO de entorno de §6) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 96.6% de 59 líneas cambiadas cubiertas (57/59, umbral 80%, nivel critico)` (`python -m harness.cobertura --base dev --config harness/rigor.json`). Las 2 sin cubrir son los `import` de `cifs_propios` en `api/app.py` y `composition.py`, que ningún test importa (el venv raíz no trae `fastapi`); su cableado lo fija `test_f063_r3_los_dos_puntos_de_composicion_cablean_los_cif_propios` |
| Mutación | campaña **completa** (`critico`), `progress/mutacion_F-063.md`: 9 ficheros, 228 líneas, **14 mutantes, 14 muertos, 0 supervivientes**, 0 timeouts, 322,0 s, SHA `9af7766`. Fila añadida a `progress/inventario_mutacion_F-039.md` |
| Entorno de la campaña | en serie (`--workers 1`), `PYTHONPATH` = comun del worktree y `PYTEST_ADDOPTS="--deselect tests/test_f052_t19_supervivientes.py::test_f052_t19_script_arranca_como_script_desde_otra_carpeta"` (mismo motivo y mismo comando que F-062 §9) |
| Supervivientes | ninguno: no hay análisis pendiente |
