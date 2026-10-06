# Implementación F-053 · fase 1 (implementer, 2026-10-06)

Rama `feature/F-053-alta-sigrid` (worktree `../albaranes-F-053`), rigor `critico`, spec v7. Alcance del encargo:
fusionar `dev`, T0a, T1, T2, T2b y T3–T16 (comun, DDL de sv3 y sv6, sv9 completo). **Hecho todo**, un commit por
tarea (`618227e`…`ca6dde7`, sin push). T17 en adelante (sv4, infra, docs, puertas finales) quedan fuera.
Contrato con sigrid-api: F-009 **v8.2 `13fd99d`** (misma forma, campos, códigos y estados que la v8 `8a6ecab`;
leído en solo lectura con `git show`, nada editado en sigrid-api). Nada contra sigrid-api, Azure, SharePoint ni BBDD.

## 1. Entorno

- Sin venv nuevo. Todo con el `.venv` raíz del árbol principal (es el intérprete que `harness/servicios.json` asigna a
  comun, sv3, sv6 y sv9) y `PYTHONPATH=…\albaranes-F-053\services\albaranes-comun`; comprobado que `ruesma_comun` se
  importa del worktree. sv9 no necesita nada que no esté ya en ese venv (httpx, tenacity, sqlalchemy, psycopg).
- Ni `git` ni servicios ni BBDD en el árbol principal; ningún `.env` leído ni tocado.

## 2. Fusión de `dev` (dos veces)

1. `5f82998`: `dev` con F-054. Conflictos en `features.json` (conviven F-053, F-061 y F-054), `current.md` y
   `BACKLOG.md` (regenerado con `python harness/backlog.py`). F-053 → `in_progress`.
2. `f8a9519` (aviso del líder): `dev` ya trae F-051 (`e7d7507`, `blocked` solo por pruebas manuales; se conserva así).
   Conflictos solo en `current.md` y `BACKLOG.md`. Ningún conflicto en código. Comprobado que existen las rutas de
   F-051 `asignar_almacen_linea_api` y `asignar_almacen_todas_api` (sv4 `app.py`) para R25 en T19–T20.
   F-051 no aporta nada a comun: la regla «partida final vacía = almacén» es, en sv9, no mandar `partida`.

## 3. Ficheros

| Dónde | Qué |
|---|---|
| sv3 `scripts/medir_admisibilidad_f053.py` + test | T0a: fuera `MARCAS_ALMACEN`; `sin_partida_sin_casar` |
| comun `colas/mensajes.py`, `valoracion.py`, `alta_sigrid.py` + `tests/test_f053_comun.py` | T1 |
| sv3 `infrastructure/database/phase2_ddl.py`, `schema_contribution.py` + test | T2 |
| sv6 `schema_contribution.py`, `orm_valuation_models.py` + test | T2b |
| `harness/servicios.json` | T3: `sv9-alta-sigrid` |
| `services/albaranes-alta-sigrid/` (nuevo) | T3–T16: `config/`, `domain/models/alta_models.py`, `domain/ports/` (3), `domain/services/` (`validador_alta`, `comparador_previa`, `clasificador`, `reclamacion`), `application/alta_sigrid_service.py`, `infrastructure/{database,sigrid,sharepoint}/`, `interface_adapters/{composition,worker/alta_worker}.py`, `main.py`, `main_worker.py`, `Dockerfile`, `requirements.txt`, `sv9.md`, `.env.example` (sin valores), `.gitignore`, 14 ficheros de test |
| `specs/F-053-alta-sigrid/tasks.md` | `[x]` T0a, T1–T16 |
| `progress/current.md`, `harness/features.json`, `BACKLOG.md` | estado |

## 4. Decisiones y desviaciones (justificadas)

1. **T2: el DDL va en `phase2_ddl._PHASE2_DDL`**, no solo en `schema_contribution.py` como dice la tarea. En sv3,
   `schema_contribution` solo EXPORTA (lo consumía sv7, retirado); lo que sv3 aplica al arrancar (API y worker) es
   `apply_phase2_ddl`. Mismo patrón que F-052 R20. `schema_contribution` lo exporta igual y declara la tabla propia.
   En sv6 sí se aplica su `schema_contribution` (`get_ddl_statements` en `initialize`): ahí va el `ALTER`.
2. **`main.py` en sv9** que delega en `main_worker.main`: el test de estructura del monorepo (F-001 R3) exige
   `main.py` o `pyproject.toml`; el `Dockerfile` ejecuta `python main.py` como el resto.
3. **Firmas de los puertos ampliadas** respecto a design §3: `reclamar(…, accion, ahora, desde, espera, modo)` (la
   decisión `verificar_anulacion` necesita la acción), `buscar_albaranes(cif, referencia, referencia_externa)` (la SQL
   de §6 excluye nuestro `synckey`) y `guardar(…, ahora)`. `Motivo` lleva `referencia_linea` opcional (R39, R17,
   `details.lineas`).
4. **R5–R8 como función pura** `domain/services/reclamacion.decidir`, que el repositorio llama dentro de la
   transacción con `FOR UPDATE OF m`; el doble de los tests usa la misma función.
5. **La petición se guarda en `en_curso` antes de llamar** («cada paso guarda petición», design §5) y un `incierto`
   pasada la Espera se retoma **reenviando la petición guardada** (R15), sin revalidar: así no la cambia, p. ej., que
   la fecha deje de ser plausible mientras está bloqueada. Sin petición guardada se rehace entera.
6. **Lo `creado` también se compara** como en `idempotente`: si difiere de lo pedido queda `registrado` con
   `registrado_distinto` (no cambia el estado; solo lo enseña).
7. **200 con `estado` inesperado**: en la previa ⇒ `error`; en la grabación `previsto` ⇒ `error` (sigrid-api dice
   que no escribió) y desconocido ⇒ `incierto`. 200 ilegible u `ok=false` (`respuesta_invalida`) se trata como fallo
   transitorio: `incierto` en la grabación, `error` en la previa. Motivo `respuesta_inesperada`.
8. **Vinculada** exige además que la línea de contrato sea del contrato de la valoración (glosario: «una línea del
   contrato de la valoración»), igual que la medición; si no, va sin vincular.
9. **`leer_mapeo` rechaza productos vacíos** (R44): un producto en blanco daría un 400 en cada alta.
10. **Variables vacías = su defecto** (`env_ignore_empty`): `ALTA_SIGRID_COMMIT=` es simulación, `DESDE=` apagada,
    `ALTA_SIGRID_AVISOS_BLOQUEANTES=` = `producto_sin_historico` (lista vacía: `" , "`). `ALTA_SIGRID_USUARIO` vacío
    no impide arrancar (aviso en el log): la spec no lo pide.
11. **Avisos bloqueantes por defecto: solo `producto_sin_historico`** (design §2). El líder citó también
    `plantilla_de_otro_proveedor`: ese código no existe desde F-009 v3 (H25) y la spec lo saca del defecto.
12. «Hoy» de R39 en Europe/Madrid con `zoneinfo`; sin base de zonas, la hora local (`TZ=Europe/Madrid` en Docker).
13. Adjunto: `nom` = `res` = `ALB-{document_id}.pdf` (40 caracteres ≤ 48); fallo ⇒ motivo `adjunto_no_colgado`.
    Verificación de anulación: motivos `sigue_en_sigrid` / `verificacion_fallida` (sustituyen, no se acumulan);
    `anulado` conserva `con_ide`/`cod` para el historial.
14. **T0a**: «registrable en (a) y (b)» leído como «ya no bloquea»: (b) no mira categorías; (a) sigue exigiendo que
    todas casen con la misma partida (sin partida casa con una línea de contrato sin partida).

## 5. Peticiones del líder durante la fase

- Aviso de sigrid-api (`pre`/`tot` de las vinculadas): `precio_distinto_del_contrato` es informativo; test
  `test_f053_r17_precio_distinto_del_contrato_es_informativo_por_defecto` (con los ajustes por defecto) y el
  parametrizado de T6.
- Misma `referencia_linea` varias veces en `details.lineas`: tres tests en `test_f053_clasificador.py` (gana `error`,
  también con el código de error primero; dos `no_admitido` ⇒ `no_admitido`; un motivo por entrada) y su control
  negativo (indexar por referencia ⇒ 3 failed). `lineas[].producto` nulo en vinculadas: sv9 no lo lee.
- Cita del contrato a `13fd99d` en `sv9.md` y en el docstring del test del clasificador.
- `progress/propuestas_a_sigrid_api_F-053.md`: nada nuevo que pedir.

## 6. Fase RED (comando: `python -m pytest -q -p no:cacheprovider -k "<filtro de la tarea>"` desde el servicio)

Para cada tarea, el test antes que el código. Donde el módulo no existía, primero un esqueleto que lanza
`NotImplementedError` para ver cada test fallar (no un error de colección). Salida real, recortada:

```
T0a (sv3, -k f053_medicion): 8 failed, 9 passed
  E KeyError: 'sin_partida_sin_casar' | E AssertionError: assert not True (hasattr(m, 'MARCAS_ALMACEN'))
T1  (comun, -k f053): E ImportError: cannot import name 'alta_sigrid' from 'ruesma_comun' … 1 error in 24.65s
T2  (sv3, -k f053_r36): 5 failed, 1 passed
  E AssertionError: assert 'CREATE INDEX IF NOT EXISTS ix_albaran_altas_sigrid_estado ON …' in []
T2b (sv6, -k "f053_r36 or f053_r42 or drift"): 4 failed, 2 passed
  E AssertionError: assert [] == ['ALTER TABLE... VARCHAR(24)'] | E KeyError: 'producto_sigrid'
T3  (sv9): 24 failed, 1 passed (sin settings, sin ficheros; sv9 ausente de servicios.json)
T4  (sv9, -k f053_modelos): E ModuleNotFoundError: No module named 'domain.models.alta_models'
T5  (sv9, -k "f053_r10 … f053_r43"): 83 failed (esqueleto) | E NotImplementedError
T6  (-k "f053_r17 or f053_r15_distinto"): 30 failed | FAILED …test_f053_r17_previa_identica_sin_motivos
T7  (-k "f053_r15 or f053_r18 or f053_r20 or f053_r21"): 76 failed, 4 passed
  E AssertionError: assert {} == {'obra_no_enc...mitido'>, ...}
T8  (-k "f053_r5 … f053_r9"): 39 failed | FAILED …test_f053_r9_excepcion_antes_de_grabar_deja_error_y_no_se_propaga
T9  (test_f053_servicio_duplicados.py): 15 failed
  E AssertionError: assert <EstadoAlta.ERROR: 'error'> is <EstadoAlta.YA_EN_SIGRID: 'ya_en_sigrid'>
T10 (test_f053_servicio_previa.py): 20 failed, 6 passed
  E AssertionError: assert <EstadoAlta.ERROR: 'error'> is <EstadoAlta.SIMULADO: 'simulado'>
T11 (test_f053_servicio_real.py): 20 failed, 3 passed
  E AssertionError: assert <EstadoAlta.ERROR: 'error'> is <EstadoAlta.REGISTRADO: 'registrado'>
T12 (-k f053_r28): 7 failed, 7 passed | E NotImplementedError: R28: T12
T13 (test_f053_cliente_sigrid.py): 32 failed, 1 passed | E NotImplementedError
T14 (test_f053_repositorio.py): 18 failed
T15 (-k f053_pdf): 6 failed, 1 passed
T16 (-k f053_worker): 14 failed, 1 passed | tests\test_f053_worker.py:197: AttributeError
```

Los «passed» de T7/T12 son tests ya en verde de tareas anteriores que el filtro `-k` también recoge.

## 7. Controles negativos (a mano, restaurando; `git diff` vacío tras cada uno)

| Qué se rompió | Resultado |
|---|---|
| **No escribir sin `ALTA_SIGRID_COMMIT=true`**: la simulación sigue a la grabación | 3 failed |
| **Grabación única**: reintento en el servicio / tenacity en la grabación del cliente | 6 failed / 5 failed |
| **Idempotencia**: el incierto no reenvía la petición guardada / sin comparar totales | 1 / 1 failed |
| R14 sin buscar altas a mano | 3 failed |
| **Validador**: sin filtrar R13 · borde de R39 · vinculada sin exigir el contrato · cantidad sin signo · `ES` siempre · R39 apagado | 4 · 1 · 1 · 1 · 2 · 6 failed |
| **Clasificador**: gana `no_admitido` · 5xx en grabación a `error` · desconocido a `no_admitido` · `naturaleza_no_valida` a `no_admitido` · indexar `details.lineas` por referencia | 2 · 4 · 3 · 3 · 3 failed |
| Comparador: float y `>=` · sin partida · idempotente con `importe_distinto` · idempotente mira avisos | 2 · 5 · 1 · 1 failed |
| Reclamación: Espera estricta · R8 reprocesa · sin DESDE · registrado nunca reintenta adjunto | 2 · 5 · 2 · 2 failed |
| R9 sin «en vuelo» · R22 adjunta en simulación · R28 anula si sigue · R28 fallo de lectura = anulado | 2 · 2 · 5 · 1 failed |
| Cliente: `truncated` tolerado · clave en el log | 1 · 1 failed |
| Repositorio: sin `FOR UPDATE` · sin `intentos + 1` · reclamar fuera de transacción | 1 · 1 · 1 failed |
| Composición sin el modo / con la Espera fija · `esta_valorado` sin mirar nulos | 1 · 1 · 2 failed |

## 8. Verificaciones MANUAL pendientes del humano (solo lectura; comandos en `tasks.md` y `progress/spec_F-053.md`)

- **T0b** (`dca.entref` de las altas a mano), con autorización, `sql/read`:
  `SELECT TOP 50 c.cod, d.entcif, d.entref FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = 14 AND
  c.fec >= 20260901 ORDER BY c.ide DESC` contra 5 albaranes en papel.
- **T0c**: login de `ALTA_SIGRID_USUARIO` (en `dbo.usu`) y App Settings de sigrid-api
  (`az functionapp config appsettings list`, solo lectura): `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` con `0`,
  `SIGRID_DOCUMENT_ALLOWED_MAGIC` con la firma de PDF, `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` con los tres genéricos y
  `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO` (`MA99`, `QA99`, `XA99`).
- **T0** (opcional tras T0a), PowerShell:
  ```powershell
  cd C:\Users\pgris\PycharmProjects\albaranes-F-053\services\albaranes-persistencia
  $sv3 = "C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-persistencia"
  & "$sv3\.venv\Scripts\python.exe" -m scripts.medir_admisibilidad_f053 --env "$sv3\.env" --csv "$env:TEMP\f053_aprobados.csv"
  & "$sv3\.venv\Scripts\python.exe" -m scripts.medir_admisibilidad_f053 --env "$sv3\.env" --todos --csv "$env:TEMP\f053_todos.csv"
  ```
- **T14**: el SQL del repositorio se ha probado con sesión simulada; contra PostgreSQL de verdad lo prueba T26.

## 9. Qué falta y avisos para la fase 2

- **T0d**: el merge está hecho y la ruta `asignar_almacen` comprobada; su verificación (`bash harness/init.sh` en
  verde) **no se ha ejecutado**: el worktree no tiene el venv de sv4 que declara `harness/servicios.json`
  (`--validar` falla por eso, ajeno a F-053) y, sin `PYTHONPATH`, `init.sh` importaría `ruesma_comun` del árbol
  principal. En su lugar, las suites pedidas una a una (§10) y la puerta de cobertura.
- **T17–T30** (sv4, infra, docs, cobertura/mutación finales, MANUAL T22 y T26–T29).
- Para **T19b**: el ORM de sv4 de `albaran_line_valuations` y su deshacer (`SELECT *`) deberán incluir
  `producto_sigrid`; el producto por defecto se pinta con `ruesma_comun.alta_sigrid.producto_efectivo` y
  `cabecera.clasificacion` (`{"familia": tipologia, "mixto": tipologia_mixta}`), igual que sv9.
- Despliegue (cuando toque): comun cambia ⇒ reconstruir todas las imágenes; sv6 (columna) y sv3 (tabla) antes que sv9.

## 10. Evidencias

| Evidencia | Valor |
|---|---|
| Tests (una suite tras otra, bajo `coverage`) | comun **374 passed** (72,3 s) · sv3 **444 passed** (36,8 s) · sv6 **289 passed** (19,2 s) · sv9 **430 passed** (16,7 s) · raíz **1083 passed** (248,4 s) |
| Tests nuevos de F-053 | comun 42 · sv3 6 (DDL) + 4 de T0a (y 5 ajustados) · sv6 6 · sv9 430 (todos) |
| Cobertura de líneas cambiadas | `python -m harness.cobertura --base dev --config harness/rigor.json` → `PUERTA COBERTURA: 96.1% de 1401 líneas cambiadas cubiertas (1346/1401, umbral 80%, nivel critico)` |
| Mutación | **No ejecutada en esta fase**: es T25, fuera del encargo (las puertas finales esperan a T17–T24). Se lanzará con la feature completa (`python -m harness.mutacion --feature F-053`) |
| Tamaño | `python -m harness.tamano --feature F-053` → dentro de los topes (requirements 150/150, design 250/250) |
| Lint | `ruff check` limpio en todo sv9 y en lo nuevo de comun; en ficheros viejos, la misma deuda de antes (ISC004 del estilo existente) |
| `bash harness/init.sh` | no ejecutado (motivo en §9) |
