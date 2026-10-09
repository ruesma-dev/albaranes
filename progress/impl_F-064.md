<!-- progress/impl_F-064.md -->
# F-064 · informe del implementer

Rama `feature/F-064-proveedor-en-prompts` (worktree `../albaranes-F-064`, spec `4b71baa`). Rigor `critico`, RUTA
SENSIBLE (prompts de sv2). PARADA 1 aprobada (Q1–Q6 según el encargo; Q4: sin albarán nuevo en el banco).

**ESTADO: T1–T8 y T11 hechas. `bash harness/init.sh` en verde en el worktree («ENTORNO LISTO», §5 bis).** T1–T7 se
hicieron con tests fichero a fichero (F-053 tenía la máquina); las suites, tras «puedes lanzar suites». Pendiente:
review, y del humano T9, T10 y T12 (§6) y aceptar el mutante equivalente (§5 bis).

Entorno: venv raíz del árbol principal (`albaranes/.venv`: sv2 no declara venv en `harness/servicios.json`, así que
init.sh usa el del arnés) con `PYTHONPATH=…\albaranes-F-064\services\albaranes-comun` (verificado:
`ruesma_comun.__file__` sale del worktree). Sin `.env`, sigrid-api, Azure, BBDD ni LLM real.

## 1. Commits

| Commit | Tarea |
|---|---|
| `0004102` | arranque: F-064 `in_progress`, BACKLOG regenerado, nota en `current.md` |
| `c45ff9b` | T1 · `empresas_cliente.py` (lista desde `ruesma_comun.proveedores` + bloque) |
| `cf6ed91` | T2 · `CIFS_PROPIOS`, argumento `empresas_cliente`, sustitución antes del correo, cableado worker y API |
| `219129e` | T3 · viñetas del proveedor de IA1 (literal de design §4) |
| `21dbcce` | T4 · regla `proveedor_emisor` (literal de design §5) + tests de IA2 (incluye R11/R12) |
| `87affe8` | T5 · contrato (R11, R12, R13) y tareas marcadas |
| `c437e49` | T6 · `evals/comparar_proveedor.py` + `evals/procesos/sv2_proveedor.py` |
| `8814e4f` | T7 · rutas sensibles + ARCHITECTURE regla 18 |
| `576ad6a` | orden de imports (ruff I001) en los ficheros nuevos |
| `ef44381`…`910b59b` | T8 · tests de líneas sin cubrir y de los supervivientes; informe de mutación analizado |
| `+1` | T8 · fila de F-064 en `progress/inventario_mutacion_F-039.md` (lo exige `test_f039_r2`) |

## 2. Ficheros tocados

- **sv2**: `application/services/empresas_cliente.py` (nuevo); `application/services/albaran_extraction_service.py`
  (argumento `empresas_cliente`, sustitución de `{empresas_cliente}` en `_render_task_fase_1` tras el catálogo y
  ANTES del correo; sin marcador, nada); `config/settings.py` (`cifs_propios`, alias `CIFS_PROPIOS`, defecto `""`);
  `interface_adapters/composition.py` y `interface_adapters/api/app.py` (`empresas_cliente=empresas_cliente(
  settings.cifs_propios)`); `config/prompts.yaml` (solo las viñetas del proveedor de `albaran_factura_es`);
  `config/revision_rules.yaml` (regla `proveedor_emisor` + una línea de comentario, ver §3 D2).
- **Tests sv2**: `tests/test_f064_empresas_cliente.py` (R1–R4), `test_f064_prompt_ia1_proveedor.py` (R5–R8),
  `test_f064_prompt_ia2_proveedor.py` (R9–R12).
- **evals**: `evals/comparar_proveedor.py`, `evals/procesos/sv2_proveedor.py` (nuevos).
- **Tests raíz**: `tests/test_f064_comparar_proveedor.py` (R14–R17), `test_f064_comparar_proveedor_base.py` (R15
  byte a byte contra el código de `544113b`), `test_f064_r18_rutas_sensibles.py` (R18);
  `tests/test_f011_r19_r20_declaracion.py` (las dos rutas nuevas en `RUTAS_ANADIDAS_DESPUES`, como F-043/F-048).
- **Arnés/docs**: `harness/rutas_sensibles.json` (R18), `docs/ARCHITECTURE.md` (regla 18, viñeta «Prompts
  (F-064)»), `harness/features.json`, `BACKLOG.md`, `progress/current.md`, `specs/…/tasks.md` (T1–T7 `[x]`).
- **Sin tocar**: sv3 y `ruesma_comun` (`git diff dev --stat -- services/albaranes-persistencia
  services/albaranes-comun` vacío), los cuatro prompts de fase 2, `review_phase_2`, `phase_merge.py`, schemas.

## 3. Decisiones y desviaciones (justificadas)

- **D1 · Bloque sin empresas**: `render_empresas_cliente(())` pinta `  - (ninguna)` bajo la cabecera. La spec no lo
  define; hoy no ocurre (siempre hay una de serie). Una cabecera huérfana confundiría a la IA.
- **D2 · Comentario de `revision_rules.yaml`**: R5 prohíbe «Ruesma» en los dos YAML sin distinguir mayúsculas. El
  único resto era un comentario de la plantilla de ideas («En Construcciones Ruesma el obra_codigo…»), que no llega
  al prompt. Se cambió por «En la constructora…» y el test de R5 lee el fichero ENTERO (un comentario descomentado
  volvería al prompt). Cambio de una línea de comentario; design §3 no lo excluía.
- **D3 · El comparador para también sin CIF esperado** (código 2, antes del LLM). R17 enumera tres paradas; esta
  cuarta evita facturar casos que no se pueden juzgar. Los 19 casos por defecto lo tienen (test).
- **D4 · Error de ejecución = categoría `error`**: R14 define `emisor/cliente/nulo/otro` para el CIF; un fallo de
  IA1/IA2 (o sin albarán) cuenta como `error`, y la mayoría con empate es `inestable` (design §6). Si IA1 falla, IA2
  no se llama (`SinFase1`); si IA2 falla, se conserva IA1.
- **D5 · Base fija en los tests**: los tests que leen YAML de la base usan `544113b` (el `dev` de antes de F-064),
  no `dev`, que se moverá al fusionar (mismo criterio que F-048 con `1807e83`).
- **D6 · Orden de commits**: los tests de R2/R6 que leen el `prompts.yaml` REAL (4) estaban en rojo en el commit de
  T2 y pasan desde T3 (el marcador llega con T3). Los de R11/R12 (T5) van en el fichero de IA2, commiteado en T4.
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
**T2 · R6** (`tests/test_f064_prompt_ia1_proveedor.py::test_f064_r6_un_correo_que_escribe_el_marcador_no_recibe_la_lista`,
servicio sin la sustitución):
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
- **R12** · filtro `es_cif_propio` en `phase_merge.construir_envelope_final` ⇒ `3 failed, 23 deselected` (envelope,
  worker y el de imports).
- **R6** · sustituir `{empresas_cliente}` DESPUÉS del correo ⇒ falla `test_f064_r6_un_correo_que_escribe_el_marcador…`
  (`assert '{empresas_cliente} aqui' in '<<<INICIO_CORREO>>>…Ojo: EMPRESAS DEL CLIENTE…'`).
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

- **Entorno**: el primer `init.sh` dio KO en `harness/servicios.json` (el worktree no tiene el venv de sv4). Se creó
  la *junction* de F-062/F-063 `services\albaranes-front\.venv` → la del árbol principal (ignorada por git); **quitarla
  con `cmd /c rmdir services\albaranes-front\.venv` ANTES de `git worktree remove`.** Sin `PYTHONPATH` (comun no
  cambia); el KO de entorno de F-062/F-063 (`test_f052_t19…`) ya no aparece.
- **`bash harness/init.sh` final** (tras `910b59b` + inventario): `ENTORNO LISTO. Puedes trabajar.` Raíz `1162 passed
  in 109.69s`; servicios en verde (última medición sin caché: sv1 205, sv2 462, sv3 584, sv4 458, sv5 43, sv6 283,
  comun 433 + 3 skipped); `PUERTA COBERTURA: 98.9% de 354 líneas cambiadas cubiertas (350/354, umbral 80%, nivel
  critico)`; AVISO (no bloquea) de `PUERTA RUTAS SENSIBLES [evals]`: falta `progress/evals_F-064.md` (T10, humano).
  Las 4 líneas sin cubrir: `montar_servicio → _servicio` (solo en el subproceso del test de la base) y su import.
- **Mutación** (`python -m harness.mutacion --feature F-064`, 4 workers, sobre `0ffa0d4`): **145 mutantes, 115
  muertos, 30 supervivientes**, 0 timeouts, 5711,7 s. **Ningún superviviente en el código de sv2** (todos en
  `evals/`). Análisis completo en `progress/mutacion_F-064.md` (0 `PENDIENTE`): 29 eran huecos de los informes del
  comparador (aviso, cabecera con commits, celdas del detalle, directorios anidados, recuento de llamadas, modelos,
  `git show` vacío, posición de sv2 en `sys.path`) y se cierran con tests nuevos en `tests/test_f064_comparar_
  proveedor.py`; **verificado reinyectando cada uno a mano** y corriendo ese fichero (bytes restaurados, `git diff`
  vacío): 29 MUERTO. El **#28 es equivalente** (`"error" not in (x or {"error": True})` frente a `{"error": False}`:
  se comprueba la clave, no el valor) — **pide la aceptación del humano** (nivel `critico`: «justificación escrita
  aceptada por el humano»). Una primera campaña en serie se paró a mano (≈ 2 h estimadas) tras 2 supervivientes
  (`_categoria`, cerrados con `test_f064_r14_clasificar_…`); `--restaurar` y `git diff` vacío antes de relanzar.

## 6. MANUAL del humano (PowerShell; claves por `Read-Host`, nunca del `.env`)

Las claves se piden ocultas y se borran al final. Proveedores por defecto: IA1 `gemini` (`GEMINI_API_KEY`), IA2
`openai` (`OPENAI_API_KEY`); si cambias `IA_PRIMERA_FASE`/`IA_SEGUNDA_FASE`, pide también la de ese proveedor.
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-064
$env:PYTHONPATH = 'C:\Users\pgris\PycharmProjects\albaranes-F-064\services\albaranes-comun'
$s = Read-Host -AsSecureString 'GEMINI_API_KEY'; $env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new('', $s).Password
$s = Read-Host -AsSecureString 'OPENAI_API_KEY'; $env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $s).Password
```
**T9 · comparador base/rama** (≈ **228 llamadas**: 114 a gemini en IA1 y 114 a openai en IA2; 19 casos × 2
variantes × 3 repeticiones; el importe en euros lo da la consola de cada proveedor). `--base 544113b` = `dev` de
antes de F-064 (inmutable; con `dev` vale igual mientras F-064 no esté fusionada):
```powershell
& C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe -m evals.comparar_proveedor --variante ambas --repeticiones 3 --base 544113b --albaranes C:\Users\pgris\PycharmProjects\albaranes\evals\inputs\albaranes
```
Criterio: `progress/comparar_proveedor_F-064.md` con `C1 · OK`, `C2 · OK`, `C3 · OK` y `VEREDICTO: VERDE`. Si sale
el AVISO «la base no dio ningún CIF cliente», el banco no reproduce el incidente (design §7: añadir el albarán real).

**T10 · pasada completa de la puerta** (≈ **190 llamadas**: ≈ 59 × 2 de sv2 + 59 de IA3 + ~13 de IA4):
```powershell
Copy-Item -Recurse C:\Users\pgris\PycharmProjects\albaranes\evals\inputs C:\Users\pgris\PycharmProjects\albaranes-F-064\evals\inputs
& C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe -m evals.runner --con-llm --feature F-064
Remove-Item Env:GEMINI_API_KEY, Env:OPENAI_API_KEY
```
Criterio: `progress/evals_F-064.md` con IA1 ≤ 154 e IA2 ≤ 4 fallos críticos (base 147 y 2 de `evals_F-051.md`).

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

1. Review (reviewer contra `CHECKPOINTS.md`).
2. Humano: aceptar el mutante equivalente #28; T9 y T10 (antes de fusionar); T12 (tras fusionar).
3. Tras fusionar: `bash harness/init.sh` en el árbol principal y quitar la *junction* de sv4 antes de borrar el worktree.
Fuera de alcance (spec): lista de proveedores de la obra para IA2 (F-055), `header-grounding`, comun, sv3, backfill.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests nuevos de F-064 | 144 (sv2 65 + raíz 79), en verde |
| Suite raíz / servicios | `1162 passed in 109.69s`; sv2 `462 passed in 12.22s`, sv3 `584 passed in 14.82s` y resto en verde |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (0 KO) |
| Cobertura de líneas cambiadas | **98,9 %** (350/354; umbral 80 %, `critico`) |
| Mutantes generados / supervivientes | **145 / 30** en la campaña; tras los tests nuevos, 29 cazados (verificado uno a uno) y 1 equivalente |
| Tiempo de la campaña de mutación | 5711,7 s con 4 workers |
