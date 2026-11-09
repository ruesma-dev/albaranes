<!-- progress/impl_F-111_partes_AB.md -->
# Informe del implementer · F-111 partes A y B (2026-11-03, aprobado; copia íntegra sacada de impl_F-111.md el 2026-11-06 por el tope de 220 líneas)

- Rama: `feature/F-111-residuos-contenedores-y-partida` (worktree `../albaranes-F-111`).
- Spec: `specs/F-111-residuos-contenedores-y-partida/`. PARADA 1: D1–D10 = (a), 2026-10-30.
- Rigor: `critico`. Servicios: **sv6** (valorador), **sv5** (endpoint nuevo), **comun 0.13.0**.
- Estado: T0–T12 y T14 hechas. **T13 MANUAL pendiente** (humano/líder, tras desplegar y revalorar).

## 0. Fusión de dev y validez de la spec

- `git merge dev` (8d5b702), commit `678c865`. Conflictos solo de papeleo (`progress/current.md`,
  `BACKLOG.md` regenerado, inventario de mutación), resueltos sin tocar código.
- Lo que entró en dev desde la spec (F-106, F-115, F-108, F-110, F-113, F-116, comun 0.12.0) **no choca**
  con la spec: nada de eso toca `residuos_container_calc`, el `PartidaMatcher` ni el normalizador de F-076.
  **Única desviación**: comun ya iba por 0.12.0 (F-110), así que `candidatas_residuos` sale en **0.13.0**
  y no en la 0.11.0 que decía T5. El test de versión de F-110 pasa a `>= 0.12.0`.

## 1. Qué cambió

### Parte A · tamaño del contenedor (sv6 + prompt de IA3)
- `sv6 application/services/residuos_container_calc.py`. La lógica nueva está en `_elegir_tamano`:
  - Con tamaños en el contrato, elige el más pequeño en el que caben los m³ (1 contenedor). Si no caben en ninguno, hace paquetes de 6 cuando el contrato tiene el de 6 y, si no, del mayor.
  - Sin tamaños: 3/6/9 m³. Con más de 9 m³, `ceil(m³/6)` de 6.
  - Fuentes por orden: tabla del contrato (`_tamanos_del_contrato`, todas las líneas «contenedor») > `contenedor_m3` de IA3 > m³ de la descripción de la casada > estándar.
  - Motivos nuevos:
    - `residuos_tamano_estandar=<t>m3`.
    - `residuos_tamano_distinto_de_casada=<t>/<c>`, que además pone `revision=True`.
  - `residuos_tamano_defecto_6m3` deja de escribirse.
  - La comparación es a 0,01 m³: redondeo a 2 decimales.
- `valuation_builder.py`: `residuos_calc.revision` ⇒ `review_required` en la línea y la cabecera (R9). El precio sigue siendo el de la casada: cambia la cantidad, nunca el precio.
- sv5 `config/prompts.yaml`, paso 4 de `valuation_residuos`:
  - Regla 3/6/9: «manda el contrato».
  - `contenedor_m3 = null` cuando el contrato no da el tamaño.
  - Precio general de la casada.
- sv5 `svc5_prompt_valuation_es.yaml`: la regla 4 ya no dice «el por defecto».

### Parte B · partida de residuos (comun + sv5 + sv6)
- comun `ruesma_comun/sigrid/partidas.py`: `candidatas_residuos(lista)` devuelve las hojas con un **antecesor** «GESTIÓN … RESIDUO…».
  - Compara sin tildes (NFKD) y deja fuera las de `AJUSTE`.
  - Si la ruta acaba en la propia hoja, la descarta; si no, no.
  - Exportada en `ruesma_comun.sigrid`. Versión 0.13.0, con nota en el README.
- sv5, endpoint nuevo `POST /v1/albaranes/partida-residuos`:
  - Ficheros: `partida_residuos_models.py`, `partida_residuos_service.py`, el esquema `documento_partida_residuos` y el prompt `partida_residuos_es`.
  - Usa el proveedor y el modelo de IA4.
  - Devuelve un resultado por línea, en el orden de entrada. Un código fuera de las candidatas ⇒ `null` (`codigo_fuera_de_candidatas:<x>`).
  - Sin proveedor ⇒ 503; cualquier otro error ⇒ 500. No persiste nada ni pone precios.
- sv6, ficheros nuevos:
  - `domain/ports/elige_partida_port.py`.
  - `infrastructure/clients/http_partida_residuos_client.py`: tenacity con 3 intentos ante 5xx, timeout o error de transporte; un 4xx falla sin reintentar; el cuerpo del error se recorta a 200 caracteres.
- sv6 `application/services/partida_residuos.py`, `AsignadorPartidaResiduos`:
  - Busca las líneas de familia efectiva `residuos` cuya partida leída está vacía. `ALM` cuenta como lectura y no se busca.
  - 0 candidatas ⇒ `partida_residuos_sin_capitulo`.
  - 1 candidata ⇒ esa, sin IA.
  - 2 o más ⇒ una sola llamada a la IA por documento. Respuesta inválida ⇒ `_sin_candidata`; la IA caída ⇒ `_ia_fallo`; sin obra o sin lista ⇒ `_sin_lista`.
  - `anotar` deja el rastro:
    - `codigo_partida_albaran` vuelve a la lectura.
    - Sin revisión, el motivo `partida_residuos:<cod>`.
    - Con revisión, `review_required` en la línea y la cabecera, y `almacen_sin_partida` pasa a `no_action`.
- `partida_matcher.py`: `match(..., sin_almacen=False)`. Con `sin_almacen` y sin partida:
  - con la casada de la IA ⇒ `existing_matched` sin partida;
  - sin ella ⇒ `no_action`;
  - nunca `almacen_sin_partida`.
  El builder lo pasa por línea con `build(..., sin_almacen=)`.
- `run_valuation_pipeline.py`:
  - Orden de pasos: normalizar (F-076) ⇒ asignar residuos ⇒ valoración directa / IA4 ⇒ build ⇒ `anotar`. `anotar` se llama en las **dos** ramas que persisten.
  - La obra se lee **una vez** por valoración con `_obra` y su `memo`; los fallos también se recuerdan.
  - `_asignar_partida_residuos` nunca lanza: si algo falla, devuelve `degradada`.
- Cableado:
  - `settings.py`: `PARTIDA_RESIDUOS_ENABLED` (defecto `true`).
  - `composition.py`:
    - `_puerto_partidas_obra` da la **misma** `CachePartidasObra` al normalizador y al asignador, una por configuración.
    - `construir_asignador_partida_residuos`. Apagado ⇒ ni puerto ni cliente. Sin sigrid-api ⇒ puerto `None` y un WARNING.
  - Lo usan el worker y `api/app.py`.
- Documentación:
  - `docs/ARCHITECTURE.md`: regla 27 y la excepción de residuos en la regla 16.
  - `sv6.md`: variable y §9 ter.
  - `sv5.md`: §5.3.
  - `azure-apps/albaranes.md` §15 (repositorio `azure-apps`, commit `ab78985`, «sin desplegar»): endpoint interno de sv5, variable de sv6 y motivos nuevos.

### Tests de otras features retocados (solo lo que la regla nueva cambia)
- `test_f036_r22_contenedores_prioridades.py`: «los nombres…» pasa de 7 m³ ⇒ 2 × 6 a **1 × 9** (`residuos_tamano_estandar=9m3`); R10.
- `test_f110_linea_a_sigrid.py`: versión de comun `>= 0.12.0`.
- `test_f043_contexto_clasificacion.py`: añade el esquema `documento_partida_residuos` al conjunto esperado.
- `test_f078_fila_completa.py`: el `_Builder.build` falso acepta `sin_almacen`.

### Ficheros de test nuevos
- sv6: `test_f111_tamano.py`, `test_f111_cliente.py`, `test_f111_partida_residuos.py`, `test_f111_pipeline.py`.
- sv5: `test_f111_prompt_residuos.py`, `test_f111_partida_residuos.py`.
- comun: `test_f111_candidatas_residuos.py`.

## 2. Decisiones de diseño y desviaciones (justificadas)
1. **comun 0.13.0** en lugar de 0.11.0: dev ya estaba en 0.12.0 (ver §0).
2. **Tolerancia redondeando a 2 decimales** en vez de `±0,01/2`. Es el mismo criterio de 0,01 m³ (6,004 cabe en el de 6) y lo pidió la mutación: la aritmética de tolerancia tenía mutantes indistinguibles.
3. `alm_codigo_partida` se acepta en `AsignadorPartidaResiduos` por simetría con F-076, pero se descarta (`del`). `ALM` es una lectura no vacía y por eso nunca se busca (R28). El atributo `_alm` era código muerto.
4. La importación de `construir_asignador_partida_residuos` en `api/app.py` va en **su propia línea**: el test de F-076 que busca la importación literal del normalizador sigue pasando.
5. sv5 se prueba con el stub de FastAPI de siempre (el intérprete de tests no trae FastAPI). La lógica del endpoint vive en la función de módulo `atender_partida_residuos`, que el test llama directamente.

## 3. Fase RED (trazas reales)

Todos los comandos se lanzan desde la carpeta del servicio, con `PYTHONPATH=<worktree>/services/albaranes-comun` y `ARNES_SIN_CACHE=1`. Las trazas completas están en el scratchpad de la sesión (`f111/red_t*.txt`).

**T1 (parte A, R1–R11)**: `python -m pytest tests/test_f111_red_tmp.py -q --tb=line`. Es el fichero RED que luego pasó a `test_f111_tamano.py`.
```
E   AttributeError: 'ResultadoContenedores' object has no attribute 'revision'
E   AssertionError: assert '3, 6 o 9' in 'Cálculo determinista de la valoración por CONTENEDORES (residuos)...'
E   assert 2.0 == 1.0   (…cantidad_convertida: 4839 B, 8 m³ sin tamaño daba 2 × 6)
E   AssertionError: assert 'residuos_tamano_distinto_de_casada=8/6' in [..., 'residuos_contenedores=2 (m3=7 / contenedor=6 m3)']
FAILED ...test_f111_r1_el_estandar_es_el_mas_pequeno_en_el_que_caben[0.5-3.0]   (… y [2.0-3.0] … [9.0-9.0])
FAILED ...test_f111_r7_sin_el_6_paquetes_del_mayor
FAILED ...test_f111_r4_builder_4839b_8m3_sin_tamano_es_1_por_139
27 failed, 19 passed in 1.05s
```
**T3 (R9 en el builder)**: `python -m pytest tests/test_f111_tamano.py -k builder -q --tb=line`
```
E   assert False is True   (LineValuationRecord(...7101...).review_required)
FAILED tests/test_f111_tamano.py::test_f111_r9_builder_la_revision_del_tamano_marca_la_linea_y_la_cabecera
1 failed, 4 passed, 43 deselected in 0.99s
```
**T4 (prompt de IA3, R12–R16)**: `python -m pytest tests/test_f111_prompt_residuos.py -q --tb=line` (sv5)
```
tests\test_f111_prompt_residuos.py:92: assert 'el por defecto' not in 'valuation_e..._valoracion '
FAILED tests/test_f111_prompt_residuos.py::test_f111_r12_el_prompt_no_dice_6_por_defecto
FAILED tests/test_f111_prompt_residuos.py::test_f111_r13_contenedor_m3_null_sin_tamano_en_el_contrato
6 failed in 0.56s
```
**T5 (comun, R17–R19)**: `python -m pytest tests/test_f111_candidatas_residuos.py -q --tb=line` (comun)
```
E   ImportError: cannot import name 'candidatas_residuos' from 'ruesma_comun.sigrid'
1 error in 0.33s
```
**T6 (endpoint de sv5, R31–R33)**: `python -m pytest tests/test_f111_partida_residuos.py -q --tb=line` (sv5)
```
E   ModuleNotFoundError: No module named 'application.services.partida_residuos_service'
1 error in 0.83s
```
**T7 (cliente sv6, R33–R34)**: `python -m pytest tests/test_f111_cliente.py -q --tb=line`
```
E   ModuleNotFoundError: No module named 'domain.ports.elige_partida_port'
1 error in 0.53s
```
**T8 (asignador, R20–R29, R35)**: `python -m pytest tests/test_f111_partida_residuos.py -q --tb=line`
```
E   ModuleNotFoundError: No module named 'application.services.partida_residuos'
1 error in 0.46s
```
**T9 (matcher `sin_almacen`, R24–R25)**: `python -m pytest tests/test_f111_partida_residuos.py -k "matcher or sintetica" -q --tb=line`
```
E   TypeError: PartidaMatcher.match() got an unexpected keyword argument 'sin_almacen'
E   TypeError: ValuationBuilder.build() got an unexpected keyword argument 'sin_almacen'
FAILED ...test_f111_r25_matcher_sin_almacen_conserva_la_casada_sin_partida
FAILED ...test_f111_r24_sintetica_ler_hereda_la_partida_asignada
7 failed, 1 passed, 23 deselected in 1.51s
```
**T10 (pipeline, R20/R27/R29/R30)**: `python -m pytest tests/test_f111_pipeline.py -q --tb=line`
```
FAILED tests/test_f111_pipeline.py::test_f111_r20_la_linea_sin_partida_va_a_la_del_capitulo
FAILED tests/test_f111_pipeline.py::test_f111_r30_la_obra_se_lee_una_vez_con_f076_tambien
FAILED tests/test_f111_pipeline.py::test_f111_r25_valoracion_directa_sin_capitulo_no_queda_en_almacen
FAILED tests/test_f111_pipeline.py::test_f111_t10_anotar_va_antes_de_persistir_en_las_dos_ramas
13 failed in 3.95s
```
**T10 (cableado)**: el mismo comando, después del cambio del pipeline y antes del de `composition`:
```
     +    where None = <...RunValuationPipeline object ...>._asignador_residuos
FAILED tests/test_f111_pipeline.py::test_f111_r30_el_asignador_comparte_la_cache_de_f076
FAILED tests/test_f111_pipeline.py::test_f111_t10_el_worker_y_la_api_cablean_el_asignador
6 failed, 13 passed in 4.07s
```
Tras cada RED se escribió el código y el mismo comando quedó en verde (commits T1–T10).

## 4. Tests (salida real)

Las suites se lanzaron de una en una, sin otra en paralelo:
- sv6: **627 passed, 1 skipped**.
- sv5: **148 passed**.
- comun: **1424 passed**.

`bash harness/init.sh` (entorno del worktree), 2026-11-03: **ENTORNO LISTO**, salida 0. Raíz 1919 passed · sv1 236 ·
sv2 496 · sv3 1608 · sv4 2562 · sv5 148 · sv6 627 (+1 skipped) · sv9 1186 · comun 1424; todas en verde.
La 1.ª pasada salió roja solo por `test_f039_r2…`: faltaba la fila de `mutacion_F-111.md` en
`progress/inventario_mutacion_F-039.md` (añadida, recuento 66). Avisos no bloqueantes: **PUERTA RUTAS SENSIBLES [evals]**
(7 rutas de prompts/redes de sv5/sv6, falta `progress/evals_F-111.md`): **no lanzado** porque
`python -m evals.runner --con-llm --feature F-111` llama a LLM reales con coste; queda para el líder/humano.

## 5. Mutación (rigor `critico`)

`python -m harness.mutacion --feature F-111` dejó el informe en `progress/mutacion_F-111.md`. Cubre `residuos_container_calc.py`, `partida_residuos.py`, `candidatas_residuos` (partidas.py) y `partida_residuos_service.py`, con cliente y matcher incluidos.

- **Pasada 1**: 28 supervivientes. Se mataron todos en T12 (`e33da75`), simplificando código (redondeo, `_alm` muerto, `tramos and` redundante) y con tests nuevos. El detalle está en el anexo del informe de mutación.
- **Pasada 2** (definitiva): **113 mutantes, 110 muertos, 3 supervivientes, 0 timeouts, 1300,6 s**. Los 3 son **equivalentes** y están justificados en el informe:
  - `indent` 2→3 (×2): sangría del JSON del prompt, cosmético.
  - `split(":",1)` → `split(":",2)`: el elemento `[0]` es idéntico.

## 6. Fuera de alcance y pendiente

- **T13 MANUAL** (humano o líder, solo lectura, tras desplegar y revalorar): repetir la medición de `progress/spec_F-111.md` §2 y listar los documentos de D7. Sin marcar.
- **Orden de despliegue**: **comun 0.13.0 ⇒ sv5 ⇒ sv6**. sv6 llama a un endpoint de sv5 que antes no existía; con sv6 desplegado antes, esas líneas irían a revisión con `partida_residuos_ia_fallo`, nunca a almacén. Sin DDL, sin colas nuevas y sin variables obligatorias (`PARTIDA_RESIDUOS_ENABLED` vale `true` por defecto).
- **Lo ya valorado** cambia solo al revalorar (D7).
- **Entorno**: `services/albaranes-front/.venv` del worktree es una **junction** a la `.venv` de sv4 del árbol principal (`C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-front\.venv`), creada el 2026-11-02 para que `init.sh` corra la suite de sv4. No se versiona. Se quita al borrar el worktree.
- Ningún cambio en `.env`, ningún push, ningún despliegue, nada contra producción.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suites tocadas) | sv6 627 passed + 1 skipped · sv5 148 passed · comun 1424 passed |
| `bash harness/init.sh` | verde (ENTORNO LISTO, salida 0); aviso evals sin lanzar |
| Cobertura de las líneas cambiadas | **99,7 %** (397/398, umbral 80 %, `critico`), línea PUERTA COBERTURA |
| Mutantes generados / muertos / supervivientes | 113 / 110 / 3 (equivalentes, justificados); pasada 1: 28 supervivientes, todos resueltos |
| Tiempo de la campaña de mutación | 1300,6 s (4 workers, media 11,5 s por mutante) |
| Tiempo de las suites (init.sh) | sv6 32,8 s · sv5 83,9 s · comun 138,6 s · raíz 639,5 s · sv4 574,2 s |
