<!-- progress/impl_F-064.md -->
# F-064 · informe del implementer

Rama `feature/F-064-proveedor-en-prompts` (worktree `../albaranes-F-064`, spec `4b71baa`). Rigor `critico`, RUTA
SENSIBLE (prompts de sv2). PARADA 1 aprobada (Q1–Q6 según el encargo; Q4: sin albarán nuevo en el banco).

**ESTADO (2026-10-18): `blocked`, solo falta la MANUAL T12 (§6).** T1–T11 hechas; review de O1 APPROVED
(`81f386b`); T9 y T10 del humano en VERDE sobre `e0ee65c` (§9); `dev` fusionado de nuevo (§9). #28 aceptado.

Entorno: venv raíz del árbol principal (`albaranes/.venv`: sv2 no declara venv en `harness/servicios.json`, así que
init.sh usa el del arnés) con `PYTHONPATH=…\albaranes-F-064\services\albaranes-comun` (verificado:
`ruesma_comun.__file__` sale del worktree). Sin `.env`, sigrid-api, Azure, BBDD ni LLM real.

## 1. Commits

Arranque `0004102` · T1 `c45ff9b` (`empresas_cliente.py`) · T2 `cf6ed91` (`CIFS_PROPIOS`, sustitución, cableado) · T3
`219129e` (viñetas IA1, design §4) · T4 `21dbcce` (regla `proveedor_emisor`, design §5) · T5 `87affe8` (R11–R13) · T6
`c437e49` (comparador) · T7 `8814e4f` (rutas sensibles + ARCHITECTURE) · `576ad6a` (ruff I001) · T8 `ef44381`…`910b59b`
+ `cd3b681` (inventario) + `6cabbe3` (RM5 del #28) · T11 `84146bb` · review `9388383` · fusión de `dev` `b06d251` ·
O1 `bea97f4` (§8).

## 2. Ficheros tocados

- **sv2**: `application/services/empresas_cliente.py` (nuevo); `application/services/albaran_extraction_service.py` (argumento `empresas_cliente`, sustitución de `{empresas_cliente}` en `_render_task_fase_1` tras el catálogo y ANTES del
  correo; sin marcador, nada); `config/settings.py` (`cifs_propios`, alias `CIFS_PROPIOS`, defecto `""`); `interface_adapters/composition.py` y `interface_adapters/api/app.py` (`empresas_cliente=empresas_cliente(settings.cifs_propios)`);
  `config/prompts.yaml` (solo las viñetas del proveedor de `albaran_factura_es`); `config/revision_rules.yaml` (regla `proveedor_emisor` + una línea de comentario, ver §3 D2).
- **Tests sv2**: `tests/test_f064_empresas_cliente.py` (R1–R4), `test_f064_prompt_ia1_proveedor.py` (R5–R8), `test_f064_prompt_ia2_proveedor.py` (R9–R12).
- **evals**: `evals/comparar_proveedor.py`, `evals/procesos/sv2_proveedor.py` (nuevos).
- **Tests raíz**: `tests/test_f064_comparar_proveedor.py` (R14–R17), `test_f064_comparar_proveedor_base.py` (R15 byte a byte contra el código de `544113b`), `test_f064_r18_rutas_sensibles.py` (R18); `tests/test_f011_r19_r20_declaracion.py`
  (las dos rutas nuevas en `RUTAS_ANADIDAS_DESPUES`, como F-043/F-048).
- **Arnés/docs**: `harness/rutas_sensibles.json` (R18), `docs/ARCHITECTURE.md` (regla 18, viñeta «Prompts (F-064)»), `harness/features.json`, `BACKLOG.md`, `progress/current.md`, `specs/…/tasks.md` (T1–T7 `[x]`).
- **Sin tocar**: sv3 y `ruesma_comun` (`git diff dev --stat -- services/albaranes-persistencia services/albaranes-comun` vacío), los cuatro prompts de fase 2, `review_phase_2`, `phase_merge.py`, schemas.

## 3. Decisiones y desviaciones (justificadas)

- **D1 · Bloque sin empresas**: `render_empresas_cliente(())` pinta `  - (ninguna)` bajo la cabecera. La spec no lo define; hoy no ocurre (siempre hay una de serie). Una cabecera huérfana confundiría a la IA.
- **D2 · Comentario de `revision_rules.yaml`**: R5 prohíbe «Ruesma» en los dos YAML sin distinguir mayúsculas. El único resto era un comentario de la plantilla de ideas («En Construcciones Ruesma el obra_codigo…»), que no llega al prompt.
  Se cambió por «En la constructora…» y el test de R5 lee el fichero ENTERO (un comentario descomentado volvería al prompt). Cambio de una línea de comentario; design §3 no lo excluía.
- **D3 · El comparador para también sin CIF esperado** (código 2, antes del LLM). R17 enumera tres paradas; esta cuarta evita facturar casos que no se pueden juzgar. Los 19 casos por defecto lo tienen (test).
- **D4 · Error de ejecución = categoría `error`**: R14 define `emisor/cliente/nulo/otro` para el CIF; un fallo de IA1/IA2 (o sin albarán) cuenta como `error`, y la mayoría con empate es `inestable` (design §6). Si IA1 falla, IA2 no se llama
  (`SinFase1`); si IA2 falla, se conserva IA1.
- **D5 · Base fija en los tests**: los tests que leen YAML de la base usan `544113b` (el `dev` de antes de F-064), no `dev`, que se moverá al fusionar (mismo criterio que F-048 con `1807e83`).
- **D6 · Orden de commits**: los tests de R2/R6 que leen el `prompts.yaml` REAL (4) estaban en rojo en el commit de T2 y pasan desde T3 (el marcador llega con T3). Los de R11/R12 (T5) van en el fichero de IA2, commiteado en T4.
- El texto de IA1 e IA2 es el literal de design §4 y §5; los tests fijan sus frases clave (espacios colapsados).

## 4. Fase RED (trazas reales) y controles negativos

Comando base (desde `services/albaranes-api`, salvo T6/T7 desde la raíz):
`C:/Users/pgris/PycharmProjects/albaranes/.venv/Scripts/python.exe -m pytest <fichero> -q`.

**T1** (`tests/test_f064_empresas_cliente.py`, antes del módulo):
```
E   ModuleNotFoundError: No module named 'application.services.empresas_cliente'
ERROR tests/test_f064_empresas_cliente.py
1 error in 0.25s
```
**T2 · R6** (`tests/test_f064_prompt_ia1_proveedor.py::test_f064_r6_un_correo_que_escribe_el_marcador_no_recibe_la_lista`, servicio sin la sustitución):
```
E   AssertionError: assert 0 == 1
E    +  where 0 = <built-in method count of str object ...>('EMPRESAS DEL CLIENTE (CIF — razón social):')
E    +    where ... = '## Cabecera\n\n{empresas_cliente}\n\n## Familias\n\n- `generico` (Generico / suministro)...
1 failed in 1.12s
```
**T2 · R2** (`-k r2`, sin setting ni argumento):
```
...test_f064_prompt_ia1_proveedor.py:142: TypeError: AlbaranExtractionService.__init__() got an unexpected keyword argument 'empresas_cliente'
FAILED tests/test_f064_empresas_cliente.py::test_f064_r2_cifs_propios_es_opcional_y_vacio_por_defecto
FAILED tests/test_f064_empresas_cliente.py::test_f064_r2_worker_y_api_pasan_la_lista_de_cifs_propios
5 failed, 18 deselected in 1.22s
```
**T3 · R5/R8** (YAML de `cf6ed91` restaurado temporalmente con `git checkout cf6ed91 -- config/…`):
```
E   AssertionError: proveedor_nombre: RAZÓN SOCIAL del EMISOR del alba
FAILED tests/test_f064_prompt_ia1_proveedor.py::test_f064_r5_el_task_lleva_el_marcador_una_sola_vez
FAILED tests/test_f064_prompt_ia1_proveedor.py::test_f064_r8_salen_la_trampa_del_cif_y_la_frase_a_mano
11 failed, 4 passed in 1.21s
```
**T4 · R9/R10** (`tests/test_f064_prompt_ia2_proveedor.py`, sin la regla):
```
E   AssertionError: assert 'Esta regla prevalece sobre cualquier otra de la cabecera, también sobre el contexto del ERP Sigrid aunque dé ese CIF por validado.' in 'Eres un revisor experto de albaranes de obra en Espana, ESPECIALIZADO en HORMIGON ...'
FAILED ...::test_f064_r9_la_regla_se_carga_tras_las_existentes
FAILED ...::test_f064_r10_fase_2_recibe_la_lista_y_la_regla[albaran_revision_fase2_es]
12 failed, 14 passed in 1.78s
```
**T6** (`tests/test_f064_comparar_proveedor.py`, antes del módulo):
```
E   ImportError: cannot import name 'comparar_proveedor' from 'evals' (...\albaranes-F-064\evals\__init__.py)
1 error in 0.48s
```
**T7 · R18** (`tests/test_f064_r18_rutas_sensibles.py`, sin las rutas): `4 failed, 1 passed in 0.17s`.

**Controles negativos** (código mutado a mano, test en rojo, restaurado con `git checkout`; `git diff` = 0 bytes):
- **R12** · filtro `es_cif_propio` en `phase_merge.construir_envelope_final` ⇒ `3 failed, 23 deselected` (envelope, worker y el de imports).
- **R6** · sustituir `{empresas_cliente}` DESPUÉS del correo ⇒ falla `test_f064_r6_un_correo_que_escribe_el_marcador…` (`assert '{empresas_cliente} aqui' in '<<<INICIO_CORREO>>>…Ojo: EMPRESAS DEL CLIENTE…'`).
- **R7** · añadir el bloque al final sin marcador ⇒ `FAILED test_f064_r7_sin_marcador_el_task_queda_como_el_de_entrada`.

## 5. Verificación (fichero a fichero, resultado real)

| Fichero | Resultado |
|---|---|
| sv2 `test_f064_empresas_cliente.py` | 23 passed |
| sv2 `test_f064_prompt_ia1_proveedor.py` | 15 passed |
| sv2 `test_f064_prompt_ia2_proveedor.py` | 26 passed |
| raíz `test_f064_comparar_proveedor.py` | 55 passed |
| raíz `test_f064_comparar_proveedor_base.py` | 7 passed (IA1 y fase 2 `es`/`hormigon` idénticos a `544113b`) |
| raíz `test_f064_r18_rutas_sensibles.py` | 5 passed |
| sv2 de prompts existentes (`f051_prompt_partida`, `f048_r12`, `f048_r14`, `f043_prompt_fase1/2`, `f048_r16`, `f002_prompt_obras`, `f048_t34`) | 23, 9, 21, 15, 5, 19, 17, 6 passed |
| raíz `f011_r19_r20` (tras registrar las rutas), `f011_r21_r22`, `f011_r23_r25`, `f027_r18_r22`, `estructura_monorepo` | 16, 6, 16, 34, 4 passed |
| sv3 F-063/F-062 (R13): `f063_cif_propio`, `f062_r3`, `r6`, `r8`, `r10`, `r14` | 35, 44, 26, 16, 16, 26 passed |

`harness.rutas_sensibles --validar`: 22 rutas, en verde. ruff: 19 `ISC004` en tuplas de frases (patrón de F-051).

## 5 bis. T8 y T11 (suites, tras la señal del líder)

- **Entorno**: el primer `init.sh` dio KO en `harness/servicios.json` (el worktree no tiene el venv de sv4). Se creó la *junction* de F-062/F-063 `services\albaranes-front\.venv` → la del árbol principal (ignorada por git); **quitarla con
  `cmd /c rmdir services\albaranes-front\.venv` ANTES de `git worktree remove`.** Sin `PYTHONPATH` (comun no cambia); el KO de entorno de F-062/F-063 (`test_f052_t19…`) ya no aparece.
- **`bash harness/init.sh` final** (tras `910b59b` + inventario): `ENTORNO LISTO. Puedes trabajar.` Raíz `1162 passed in 109.69s`; servicios en verde (última medición sin caché: sv1 205, sv2 462, sv3 584, sv4 458, sv5 43, sv6 283, comun 433
  + 3 skipped); `PUERTA COBERTURA: 98.9% de 354 líneas cambiadas cubiertas (350/354, umbral 80%, nivel critico)`; AVISO (no bloquea) de `PUERTA RUTAS SENSIBLES [evals]`: falta `progress/evals_F-064.md` (T10, humano). Las 4 líneas sin
  cubrir: `montar_servicio → _servicio` (solo en el subproceso del test de la base) y su import.
- **Mutación** (`python -m harness.mutacion --feature F-064`, 4 workers, sobre `0ffa0d4`): **145 mutantes, 115 muertos, 30 supervivientes**, 0 timeouts, 5711,7 s. **Ningún superviviente en el código de sv2** (todos en `evals/`). Análisis
  completo en `progress/mutacion_F-064.md` (0 `PENDIENTE`): 29 eran huecos de los informes del comparador (aviso, cabecera con commits, celdas del detalle, directorios anidados, recuento de llamadas, modelos, `git show` vacío, posición de
  sv2 en `sys.path`) y se cierran con tests nuevos en `tests/test_f064_comparar_proveedor.py`; **verificado reinyectando cada uno a mano** y corriendo ese fichero (bytes restaurados, `git diff` vacío): 29 MUERTO. El **#28 es equivalente**
  (`"error" not in (x or {"error": True})` frente a `{"error": False}`: se comprueba la clave, no el valor; demostración ejecutable RM5 en `test_f064_demostracion_el_mutante_28_es_equivalente`) — **aceptado por escrito por el humano el 2026-10-15** (§8). Una primera
  campaña en serie se paró a mano (≈ 2 h estimadas) tras 2 supervivientes (`_categoria`, cerrados con `test_f064_r14_clasificar_…`); `--restaurar` y `git diff` vacío antes de relanzar.

## 6. MANUAL del humano (PowerShell; claves por `Read-Host`, nunca del `.env`)

T9 y T10 ya ejecutadas por el humano (comandos en `progress/spec_F-064.md` §5; resultado en §9). Queda T12:

**T12 · tras fusionar en `dev` e `init.sh` en verde: desplegar SOLO sv2** (sin orden: ni schema ni comun cambian):
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
.\deploy.ps1 -Only sv2
.\check_deploy.ps1
```
Vigilancia (solo lectura, BBDD `albaranes`), criterio 0 filas en una semana:
```sql
SELECT m.id, m.numero_albaran, m.created_at_utc, m.obra_codigo, m.proveedor_nombre
FROM albaran_documents_merge m
WHERE m.is_active AND m.review_reasons_json LIKE '%proveedor_cif_propio:%'
  AND m.created_at_utc >= '<fecha-hora UTC del despliegue de sv2, ISO>'
ORDER BY m.created_at_utc DESC;
```

## 7. Qué falta (orden)

1. Fusionar la rama en `dev` (líder/humano) y `bash harness/init.sh` en el árbol principal.
2. Humano: T12 (desplegar solo sv2 y vigilar `proveedor_cif_propio:` una semana, §6).
3. Quitar la *junction* de sv4 antes de borrar el worktree (§5 bis).
4. Decisión del humano pendiente: el albarán real de F-063 en el banco del comparador (§9).
Fuera de alcance (spec): lista de proveedores de la obra para IA2 (F-055), `header-grounding`, comun, sv3, backfill.

## 8. Pasada O1 (2026-10-15, tras la review pasada 1 APPROVED)

Encargo del líder con dos decisiones del humano: **#28 aceptado por escrito** («Acepto los dos») y **O1 aprobada**. Sin `init.sh` ni suites (restricción: el árbol principal está corriendo `init.sh`); solo tests de un fichero.

- **Fusión de `dev` `d79b3d9`** (`b06d251`). Conflictos resueltos conservando todo lo de `dev`: `features.json` (el de `dev` + la entrada de F-064; F-053 y F-070 `blocked`, F-064 **única `in_progress`**), `BACKLOG.md` regenerado con
  `harness/backlog.py` (`--comprobar` rc 0), `current.md` (bloque de F-064 condensado arriba, resuelve O4; el resto, el de `dev`), `ARCHITECTURE.md` (viñeta de F-064 en la regla 18 + reglas 19–21 de `dev`) e inventario de mutación (37
  filas: las 36 de `dev` + F-064). La fusión no toca sv2 ni `evals/` (`git diff --stat 9388383 b06d251 -- services/albaranes-api evals` vacío). **F-071 y F-072 no existen** ni en `dev` `d79b3d9` ni en el árbol principal.
- **#28**: aceptación anotada en `progress/review_F-064.md` §«Aceptación del humano» (condición 3 de §5 cumplida) y en `progress/mutacion_F-064.md` #28. Para respetar el tope de 140 líneas de la review se unieron 4 líneas partidas, sin
  quitar texto.
- **O1** (`bea97f4`): viñeta nueva en «Acción:» de `proveedor_emisor` (`revision_rules.yaml:130-132`), entre «corrígelos» y «Si son correctos»: «Si no puedes leer con seguridad al emisor, conserva lo de fase 1, salvo que sea una empresa del
  cliente: entonces deja proveedor_cif en null.» Redacción: la del humano con el vocabulario de la regla («proveedor_cif», viñeta en imperativo); mismo sentido. Al día: design §5 (literal + nota), R9 y ARCHITECTURE regla 18. Tests nuevos en
  `test_f064_prompt_ia2_proveedor.py` (3 funciones, 6 casos): la viñeta en el YAML y en su sitio; una vez en la checklist renderizada; una vez y dentro de la regla en las instructions de los cuatro prompts de fase 2, con y sin contexto de
  Sigrid.

**RED** (desde `services/albaranes-api`, antes de tocar el YAML):
`PYTHONPATH=…\albaranes-F-064\services\albaranes-comun …\albaranes\.venv\Scripts\python.exe -m pytest tests/test_f064_prompt_ia2_proveedor.py -q -k o1 -p no:cacheprovider`
```
E           AssertionError: assert 0 == 1
E            +  where 0 = <built-in method count of str object at 0x000002793CBC0E50>('Si no puedes leer con seguridad al emisor, conserva lo de fase 1, salvo que sea una empresa del cliente: entonces deja proveedor_cif en null.')
tests\test_f064_prompt_ia2_proveedor.py:218: AssertionError
FAILED tests/test_f064_prompt_ia2_proveedor.py::test_f064_o1_la_regla_conserva_lo_de_fase_1_si_el_emisor_es_ilegible
FAILED tests/test_f064_prompt_ia2_proveedor.py::test_f064_o1_la_clausula_llega_renderizada_a_la_checklist
FAILED tests/test_f064_prompt_ia2_proveedor.py::test_f064_o1_la_clausula_llega_a_los_cuatro_prompts_de_fase_2[albaran_revision_fase2_es]
(… y los otros tres prompts de fase 2: hormigon, mortero, residuos)
6 failed, 26 deselected in 3.83s
```
**Verde** (un fichero por pytest): `test_f064_prompt_ia2_proveedor` 32 passed; `_ia1_proveedor` 15; `empresas_cliente` 24; los 12 ficheros de sv2 que leen `revision_rules.yaml` (f002, f043 ×2, f048 ×9, f051) en verde; raíz
`test_f064_comparar_proveedor` 68, `_base` 7, `r18` 5, `f048_comparar_obra_prompt_dev` 4, `f011_r19_r20` 16, `f039_r1_r2…` 9, `f038_r17_r21` 17, `f038_r13_r16_tamano` 22. **Control negativo**: la viñeta movida tras «Si son correctos» ⇒
`1 failed, 5 passed` (el del orden); restaurado con `git checkout`, `git diff` vacío.

**Mutación**: `alcance_de_feature("F-064", base="bea97f4~1", rama="bea97f4")` ⇒ `0 fichero(s), 0 línea(s) de producción` (solo YAML, tests y docs; el YAML no es mutable, lo cubren las evals). Sin campaña nueva, sin equivalentes nuevos (RM5
no aplica). **Efecto en T9/T10**: O1 toca `revision_rules.yaml`, ruta sensible ⇒ T9 y T10 se miden sobre `bea97f4` o posterior y `progress/evals_F-064.md` debe ser posterior a `bea97f4` (ya no a `8814e4f`).

## 9. Fusión de dev y T9/T10, 2026-10-18

**T9** (humano, HEAD `e0ee65c`, `progress/comparar_proveedor_F-064.md`, sin valores; revisado: solo recuentos y
caso_id): **VERDE**, C1/C2/C3 OK. Mayoría emisor base 8 → rama 9 (IA1 e IA2); CIF cliente 0/0. **AVISO**: la base
no dio ningún CIF cliente, así que el banco no reproduce el incidente y C1 no prueba la corrección. Movimientos:
GEN-002 mejora (nulo → emisor), HOR-005 mejora (CIF ajeno → nulo), MOR-003 empeora (nulo → CIF ajeno; C3 no lo
marca porque la base tampoco daba el emisor).
**T10** (humano, `progress/evals_F-064.md`, fuera de git): criterio cumplido, IA1 **152** críticos (≤ 154; 57
casos, RES-020/RES-021 omitidos sin fichero; gemini), IA2 **2** (≤ 4; openai); F-051: 147 y 2. Veredicto global ROJO
esperado (IA3 408, IA4 27, E2E 537: fuera de F-064, que solo toca sv2).

**Propuesta (decisión del humano, sin crear feature)**: meter el albarán real de la incidencia F-063 en el banco
de `evals.comparar_proveedor` (design §7), para que C1 pruebe la corrección. Es un PDF con datos reales: entra
solo si el humano lo autoriza y por la vía de `evals/inputs` (no versionada), con su CIF esperado.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests nuevos de F-064 | 150 (sv2 71 + raíz 79; 6 de ellos de O1), en verde fichero a fichero |
| Suite raíz / servicios | `1162 passed in 109.69s`; sv2 `462 passed in 12.22s`, sv3 `584 passed in 14.82s` y resto en verde |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (0 KO) tras T11; **no reejecutado tras la fusión y O1** (restricción del líder) |
| Cobertura de líneas cambiadas | **98,9 %** (350/354; umbral 80 %, `critico`) |
| Mutantes generados / supervivientes | **145 / 30** en la campaña; tras los tests nuevos, 29 cazados (verificado uno a uno) y 1 equivalente |
| Tiempo de la campaña de mutación | 5711,7 s con 4 workers |
| Pasada O1 | RED 6 failed → 32 passed (`test_f064_prompt_ia2_proveedor`, 5,1 s); alcance de mutación de `bea97f4` vacío (0 líneas de producción) |
