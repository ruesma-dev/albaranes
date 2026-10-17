<!-- progress/impl_F-076.md -->
# F-076 · Normalizar partidas contra las de la obra · Informe del implementer (2026-10-17)

Rama `feature/F-076-normalizar-partidas` (worktree `../albaranes-F-076`), `dev` fusionado (`b40aab0`: F-053,
F-072, F-078, F-079). Spec APROBADA (P1–P11 por defecto + ampliación R23–R25/T5b). Rigor `critico`. Tareas
T1–T17 y T5b hechas (T17 en §5), un commit cada una (`d0aff5a`…`fda7f9a`); T18–T20 son del humano (§6). *Junction* `.venv` de
sv4 en el worktree → `..\albaranes\services\albaranes-front\.venv` (quitarla con `cmd /c rmdir` antes de
`git worktree remove`).

## 1. Qué cambió

- **comun 0.8.0** · `ruesma_comun/sigrid/partidas.py` (nuevo): portado de F-049 `224f64e` sin cambios de semántica
  (SQL de sv4 + `emp = 1`, `PartidaObra`, `ListaPartidasObra`, `hojas_de_filas`, `LectorSql`, `normalizar_partida`,
  `partes_de_partida`, `casar_partida`, `CasePartida`, `MOTIVO_*`); `leer_partidas_obra(leer, obra)` con
  `canonizar_codigo_obra` (F-070); nuevos `ResolucionPartida`/`resolver_partida_obra` (guarda de no hoja, compuesta ⇒
  fuera) y `CachePartidasObra` (TTL, LRU, caducada ante fallo, fallo recordado, 0 hojas ⇒ `None`, nunca lanza, con
  candado). Exportes en `ruesma_comun.sigrid`, versión y README.
- **sv4** · `sigrid_lookup_client.fetch_partidas_por_obra` delega en comun (empresa 1, `NO_TOLERA`, 500.000 filas);
  fuera la SQL y el cálculo de hojas propios; `_post_sql_read(max_rows=None)`. `review_models.coincide_partida` +
  campo `partida_normalizada_desde`; `review_repository` la usa en los dos `agree_partida`; la plantilla añade
  «Normalizada: X → Y» al `title` de la casilla de partida (editable y solo lectura).
- **sv6** · `SigridApiLector` (solo `sql/read`, tenacity 3 intentos ante 5xx/timeout/conexión, sin clave ni cuerpo en
  el log); settings de R17 (+ `sigrid_api_configurada`); `PartidasObraPort`; `obra_del_documento`
  (`SQL_OBRA_DEL_DOCUMENTO`, sin inicializar schema); `NormalizadorPartidas` (`necesita_obra`, `normalizar`,
  `degradada`, `anotar`); `RunValuationPipeline` normaliza tras el sobre de sv5 (antes de `no_contract` e IA4),
  anota tras `completar_registros` y persiste el sobre normalizado; `construir_normalizador_partidas` en
  `composition.py`, usado por el worker y por `app.py`; `scripts/medir_f076_partidas.py`; `tenacity>=8.2` en
  `requirements.txt`.
- **sv9** · sin código: test de contrato `test_f076_partida_final.py`.
- **infra** · `infra/set_partidas_sv6.ps1` (UTF-8 BOM, CRLF; parse 0 errores con el Parser de PowerShell 5.1:
  no hay `pwsh` en la máquina) y bloque sv6 de `create_capps.ps1`. Grep de GUID/`subscriptions/`/URL: 0.
- **docs** · ARCHITECTURE regla **23** (la 22 ya es de F-078), regla 3 (sv6 lector de `obra_codigo`), «Acceso a
  datos», «Infra y despliegue»; `sv6.md` (§8 variables, §9 bis, §11, §14, §15); `azure-apps/albaranes.md` §1 y §11
  (commit `8a6f63c` en `azure-apps`, sin push; `git status` limpio antes y después).

## 2. Decisiones y desviaciones (justificadas)

1. **R11 frente a design §5.2 «sin puerto ⇒ sin motivos»**: R11 dice que sin configuración de sigrid-api hay WARNING
   y `partidas_obra_no_disponibles`. Se sigue R11 (el requisito manda; T18 espera ese motivo en el log si falta
   algo). Apagado (R12) sí es «sin motivos».
2. **R5, guarda de no hoja**: se aplica a toda lectura no exacta (R5 literal), también a la que sería `ambigua`; el
   design la cita con `normalizada`. Ambas acaban a revisión; solo cambia el nombre del motivo.
3. **Lectura** (R7/R13): partida con clave (`normalizar_partida` no vacía) y distinta de `ALM_CODIGO_PARTIDA`. Un
   sobre solo con vacías/ALM no lee la obra ni consulta.
4. **`anotar`**: una `exacta` que solo difería en espacios exteriores también recupera la leída en
   `codigo_partida_albaran` (regla 6), sin motivo. En R10 la cabecera recibe además
   `at_least_one_line_requires_review` si no lo tenía (el mismo invariante que pone el builder).
5. **Copia profunda** del sobre al normalizar: IA4 muta el sobre en su sitio; así el de sv5 nunca se toca.
6. **sv4 conserva el nombre `_SQL_PARTIDAS_POR_OBRA`** como alias de la SQL de comun (no copia): los tests de F-052 y
   F-070 reconocen la consulta por él; el test de R15 comprueba que es el mismo objeto y que en el fichero no queda
   `obrparpar`, `padide` ni `parent_ides`.
7. **Tests de otras features tocados (con motivo)**: `test_f052_lookup_truncado.py` (partidas pasan de tolerar a lanzar
   el truncado y piden 500.000 filas: P7 aprobado, mismo ajuste que hizo F-049) y `test_f052_sigrid_lectura.py` (fijaba
   `0.7.0`; ahora «≥ 0.7.0» y paquete = pyproject). La verificación de T5 decía «sin tocar otros tests»: con P7 es
   imposible; se tocaron solo las aserciones que fijaban el comportamiento que R15 cambia.
8. **`tenacity` en `requirements.txt` de sv6**: R18 exige tenacity y sv6 no la tenía (sí sv9).
9. **app.py de sv6**: el intérprete del arnés (raíz) no trae FastAPI, así que su test de cableado se salta allí; un test
   AST comprueba siempre `normalizador=construir_normalizador_partidas(settings)`. Además se verificó a mano con el
   venv de sv6 (con FastAPI): sin `SIGRID_API_*` ⇒ `puerto=None activo=True`; con ellas ⇒ `CachePartidasObra`.
10. **Título de la casilla**: separador « · » de design §5.4 («Costes indirectos de obra · Normalizada: CI.04.18 →
    CI.4.18»); sin descripción, solo la nota. Escapado por Jinja (test).

## 3. Fase RED (comandos y salida real; trazas completas recortadas)

`export PYTHONPATH=C:/Users/pgris/PycharmProjects/albaranes-F-076/services/albaranes-comun` en todas.

- **T1** `python -m pytest tests/test_f076_partidas.py -q -k "r1 or r2 or r4"` (comun):
  `E   ModuleNotFoundError: No module named 'ruesma_comun.sigrid.partidas'` — `1 error in 0.22s`.
- **T3 (R5, central)**: resolver sin la guarda, `pytest tests/test_f076_partidas.py -q -k r5 --tb=line`:
  ```
  E   AssertionError: assert ResolucionPar...leida='03.02') == ResolucionPar...leida='03.02')
  E     Differing attributes: ['codigo', 'motivo']
  E   AssertionError: assert 'ambigua' == 'fuera_de_lista'
  5 failed, 24 passed, 83 deselected in 0.21s
  ```
- **T5 (R15)** `.venv/Scripts/python.exe -m pytest tests/test_f076_partidas_sv4.py -q --tb=line` (sv4), antes de
  delegar:
  ```
  E   AssertionError: assert 'SELECT\n ... WHERE con_obr.cod = ?\nORDER BY p.cod\n' is 'SELECT\n ... AND con_obr.emp = 1\nORDER BY p.cod\n'
  E   assert 5000 == 500000
  E   Failed: DID NOT RAISE SigridRespuestaTruncada
  E   assert True is False            (endpoint con lista truncada: ok seguía en true)
  6 failed, 6 passed, 1 warning in 1.96s     (los 6 verdes: «mismos items que hoy», ancla antes y después)
  ```
- **T5b (R23/R24, central)** `pytest tests/test_f076_aviso_partida.py -q --tb=line`, con `coincide_partida` ya en el
  dominio pero sin cablear:
  ```
  E   AssertionError: assert False is True   (test_f076_r23_leida_normalizada_es_coincidente: hoy ⚠)
  E   assert ('cedit-warn' not in 'class="conc...')
  E   AssertionError: assert [''] == ['Normalizada...18 → CI.4.18']
  7 failed, 40 passed in 1.67s
  ```
- **T6** `pytest tests/test_f076_lector.py`: `ModuleNotFoundError: No module named 'infrastructure.sigrid'`.
  **T7**: `No module named 'domain.ports.partidas_obra_port'`. **T8**: `No module named
  'application.services.normalizador_partidas'`. **T11**: `cannot import name 'construir_normalizador_partidas'`.
- **T9 (R9/R10, central)**, con un `anotar` vacío: `pytest tests/test_f076_normalizador.py -k "r9 or r10" --tb=line`:
  ```
  E   AssertionError: assert 'CI.4.18' == 'CI.04.18'        (codigo_partida_albaran: se perdía la leída)
  E   AssertionError: assert 'partida_fuera_de_lista' in ['contract_unit_unknown', ..., 'ia_no_match']
  E   AssertionError: assert 'partida_ambigua_en_obra' in [...]
  6 failed, 4 passed, 19 deselected in 0.74s
  ```
- **T10 (R7/R8/R14, central)**, pipeline que acepta y descarta `normalizador`: `pytest tests/test_f076_pipeline.py`:
  ```
  E   AssertionError: assert [] == ['doc-f076']             (no lee la obra)
  E   AssertionError: assert 'CI.04.18' == 'CI.4.18'        (derivada y sintética con la leída)
  E   AssertionError: assert ['CI.04.18'] == ['CI.4.18']    (IA4 recibía la leída)
  E   assert 'partidas_obra_no_disponibles' in []
  12 failed, 4 passed in 0.80s
  ```
  `test_f076_r8_sin_f076_la_misma_linea_sale_nueva` fija la regresión: sin normalizar, `CI.04.18` frente a la línea
  `CI.4.18` sale `new_line_created`; con F-076, `existing_matched`.
- **T12** (sv9) y **T15** (script): sin RED de comportamiento. T12 es un test de contrato de código que NO cambia
  (pasa a la primera por diseño: R16 es «sv9 sigue igual»). En T15 el test y el script se escribieron seguidos sin
  ejecutar el test entre medias: su RED habría sido el `ImportError` del módulo.

## 4. Resultados de los tests (reales)

`bash harness/init.sh` (Git Bash, `PYTHONPATH` a la comun del worktree), tras `fda7f9a` + inventario:

| Suite | Resultado | Tiempo | Antes de F-076 (init del inicio) |
|---|---|---:|---|
| raíz | 1237 passed | 136,8 s | 1237 passed |
| sv4 | 1549 passed, 1 warning | 129,9 s | 1487 |
| sv6 | 444 passed, 1 skipped (test de `app.py` sin FastAPI, §2.9) | 11,1 s | 340 |
| sv9 | 670 passed | 31,8 s | 660 |
| comun | 818 passed, 3 skipped | 125,8 s | 684 |
| sv1, sv2, sv3, sv5 | 205, 397, 703, 43 passed (sin cambios) | — | iguales |

Nuevos de F-076: comun `test_f076_partidas.py` (134), sv4 `test_f076_partidas_sv4.py` (12) y
`test_f076_aviso_partida.py` (50), sv6 `test_f076_{lector,obra_documento,normalizador,pipeline,cableado,medicion}.py`
(104), sv9 `test_f076_partida_final.py` (10). La primera pasada de `init.sh` (T17) cayó en rojo por
`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`: faltaba la fila de `mutacion_F-076.md` en
`progress/inventario_mutacion_F-039.md`; añadida (40 informes) y raíz en verde. Resultado final de `init.sh`: §5.

## 5. Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 6.066 passed, 4 skipped, 0 failed (todas las suites, tabla §4) |
| Cobertura de las líneas cambiadas | **97,3 %** (583/599, umbral 80 %, nivel `critico`): `PUERTA COBERTURA` de `init.sh` |
| Mutación | **173 generados, 173 muertos, 0 supervivientes**, 0 timeouts, 0 sin veredicto, 1242,2 s, 4 workers, campaña completa sobre `fdb9c58` (`progress/mutacion_F-076.md`). Pasada 1 (`121524c`): 180/154/26; los 26 resueltos con tests o quitando la rama equivalente (tabla en el informe) |
| Tiempo de las suites | raíz 136,8 s · sv4 129,9 s · comun 125,8 s · sv9 31,8 s · sv6 11,1 s |
| Rutas sensibles | `normalizador_partidas.py` (redes deterministas de sv6): AVISO sin `progress/evals_F-076.md`. Sin evals de pago por P8 (aprobado); exigencia «aviso», no bloquea |
| `init.sh` final | **VERDE** («ENTORNO LISTO», exit 0) sobre `b506507`: raíz 1237 passed (190,9 s); los 8 servicios en verde por caché de suite (verdes de 07:44–07:50 del mismo día, sin cambios desde entonces); avisos: `blocked` (F-078), ruff (deuda previa), infra sin tests, rutas sensibles (P8) y [ADAPTAR] ajenos |

## 6. MANUAL del humano (no las ejecuta ningún agente)

Están también, con el mismo texto, en `progress/current.md` («F-076 · MANUAL del humano»).

Cuándo: tras el APPROVED del reviewer, la fusión de `feature/F-076-normalizar-partidas` en `dev` y `init.sh` en
verde en el árbol principal. **Si las MANUAL T12–T14 de F-078 siguen pendientes**, el despliegue de sv6 y sv4 de
F-076 lleva también F-078 (está en `dev`): sigue entonces el orden de F-078 (sv6 → relleno → sv4) con estos mismos
despliegues.

**T18 · variables de sv6 → sv6 → sv4** (misma consola):

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
. .\00_capps_vars.ps1
.\set_partidas_sv6.ps1
.\deploy.ps1 -Only sv6
.\deploy.ps1 -Only sv4
.\check_deploy.ps1
```

VERDE si `set_partidas_sv6.ps1` dice `OK` en las 8 variables (7 valores + `SIGRID_API_FUNCTION_KEY` con
`secretref:'sigrid-key'`) y en `secreto sigrid-key`, y termina en «Ajustes de F-076 aplicados a ca-sv6-valorador»;
`check_deploy.ps1` con sv6 y sv4 en el tag nuevo. Tras la primera valoración (T19), el log de sv6 no debe decir
`partidas_obra_no_disponibles`:

```powershell
az containerapp logs show -n ca-sv6-valorador -g $RG --tail 300 | Select-String "partidas-obra|partidas_obra_no_disponibles"
```

Debe salir `[partidas-obra] obra=… hojas=… segundos=…` y ninguna línea con `partidas_obra_no_disponibles`. Vuelta
atrás sin redesplegar: `az containerapp update -n ca-sv6-valorador -g $RG --set-env-vars PARTIDAS_OBRA_NORMALIZAR_ENABLED=false`.

**T19 · revalorar los pendientes y medir (solo lectura).** En la ficha de sv4 de cada uno, «Valorar ahora»:
`2792cf3b`, `53337da7`, `54b82479`, `dedf011a` (0694); `41ab0dc1` (0711); `09643c2b`, `89e463a7`, `bef66bce`,
`f96c6dbe` (0720); `ca609aee` (0723); `25c5d647` (0724). **`355449d9` NO se revalora** (6 filas guardadas: se
perderían, F-058): su partida se corrige a mano en la ficha (`CI.04.18` ⇒ `CI.4.18`, `CI.03A.02` ⇒ `CI.03A.2`).
Después, la medición (sv6 del árbol principal; PostgreSQL con el `.env` de sv6, en solo lectura; las tres
`SIGRID_API_*` se toman del `.env` de sv3 SOLO para esta consola, sin imprimirlas):

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\services\albaran-valoracion-persist
.\.venv\Scripts\python.exe -m pip install "tenacity>=8.2"
Get-Content ..\albaranes-persistencia\.env | Where-Object { $_ -match '^(SIGRID_API_(BASE_URL|FUNCTION_KEY|DATABASE))=(.*)$' } | ForEach-Object { Set-Item -Path "env:$($Matches[1])" -Value $Matches[3].Trim('"') }
.\.venv\Scripts\python.exe -m scripts.medir_f076_partidas
```

VERDE si «normalizable sin normalizar» da **0** en pendientes y las 6 sin candidata de `progress/spec_F-076.md`
§2.2 cuentan en «fuera de lista» con el motivo `partida_fuera_de_lista` (pendientes). Los aprobados antes de DESDE
(12 líneas `CI.4.18`) pueden seguir en «normalizable sin normalizar / aprobado»: sv9 los ignora (R6 de F-053).

**T20**: `bash harness/init.sh` en verde en el árbol principal tras T18–T19; con eso, F-076 `done`.

## 7. Fuera de alcance y pendiente

Fuera (spec): elegir por parecido/sufijo o repartir compuestas y la lista en el prompt (F-049); normalizar en sv9/sv3;
validar en servidor lo que teclea el revisor; que lo manual sobreviva a revalorar (F-058); migrar por script (P5).
Pendiente: review; T18–T20 (humano). Notas para quien fusione después (F-049, F-075, F-077), en `current.md`.
