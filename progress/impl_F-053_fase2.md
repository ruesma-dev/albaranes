# Implementación F-053 · fase 2 (implementer, 2026-10-08)

Rama `feature/F-053-alta-sigrid` (worktree `../albaranes-F-053`), rigor `critico`, spec v7. Encargo del líder (fase 2
aprobada por el humano, «si», 2026-10-08): T0d, T17–T21b, T24b, T22, T23, T24, T25 y T30; las MANUAL no se ejecutan.
**Hecho todo** salvo lo que depende del humano. Un commit por tarea (`7ec02a6`…`61143e4` + el de este informe), sin push.
Nada contra Azure, sigrid-api, SharePoint ni BBDD reales; ningún `.env`.

## 1. Qué cambió

| Tarea | Commit | Qué |
|---|---|---|
| T0d | `7ec02a6`, `d53d059` | Dos fusiones de `dev` (F-062 y F-063, `done`). Conflictos solo de papeleo (`current.md`, `BACKLOG.md` regenerado). Código de sv3 fusionado solo; el doble `MergeEnMemoria` de F-062 gana `buscar_conservado_por_alta` (→ `None`, como hoy). F-051 `blocked`, F-062/F-063 `done`; F-049 sigue `pending`, como en `dev` (el encargo decía `blocked`: no la toco). |
| T17 | `cc46f5b`, `373a441` | sv4 lee `ALTA_SIGRID_DESDE_UTC`, `_ESPERA_INCIERTO_MIN`, `_PRODUCTO_POR_DEFECTO` (vacía = defecto, como sv9); mapeo roto ⇒ `main.py` no arranca y lo registra sin valores (R44, lección H1). Colas: `notify_document_approved` devuelve si publicó; `solicitar_alta_sigrid(document_id, accion)`. comun: `leer_instante_utc`, `espera_pasada`, `es_linea_vinculada`, `es_linea_a_registrar`, `ESTADOS_ALTA_REPETIBLES`, `configuracion.motivos_configuracion`; sv9 delega en ellas (sin copias entre servicios). |
| T18+T19 | `ee936f3` | `ReviewService` publica el alta SOLO en el paso a aprobado (lo dice el repositorio dentro de su transacción), por los dos caminos; DESDE vacía ⇒ nada; fallo ⇒ aprobación intacta y aviso (R1–R4). `_exigir_desbloqueado` en **dos sentencias** (cerrojo `FOR UPDATE` del merge y, después, el alta) al empezar la sesión de cada método de R26 (`update_document_y_transicion`, `set_approved(False)`, borrar, purgar, deshacer, ediciones de líneas, `asignar_almacen` de F-051); sin tabla = sin alta. |
| T19b | `5d01c7e` | Producto: `lineas_producto_sigrid`, `guardar_producto_sigrid` (cerrojo, línea ajena, vinculada) y `elegir_producto_sigrid` (admitidos, `NULL` = por defecto, deshacer, DESDE vacía ⇒ `apagada`). |
| T20 | `1a5c591` | Rutas: 409 con el aviso en API y redirección en formularios (R25); revalorar y re-buscar miran el alta antes de publicar; R27 cuenta los saltados; rutas de R28, R30 y R41. |
| T21b | `9a2c84b` | R37: tests del rechazo (la comprobación entró con T18/T19, ver §3), `valorado` en ficha y listado, botones deshabilitados. |
| T21 | `79626c9` | `_alta_sigrid.html`, columna «Producto Sigrid», pastilla del alta en el listado, JS del selector; nada con DESDE vacía. |
| T24b | `8752869` | `reclamar` de sv9 en dos sentencias (decisión del humano). |
| T22 | `b5f5cf6` | `infra/`: sv9 en `$REPO/$APPS/$IMG` (orden sv6, sv3 → sv9 → sv4), `build_images.ps1`, `manifests/sv9`, `create_capps_sv9.ps1` (KEDA `q-feedback`, máx. 1 réplica, Key Vault, **`ALTA_SIGRID_COMMIT=false`** y se niega a otra cosa), `set_alta_sigrid.ps1` (DESDE/Espera/mapeo a sv9 y sv4 desde una sola variable; relee y compara; no toca `COMMIT`), aviso de `COMMIT` en `deploy.ps1`, `README_capps.md`. |
| T23 | `0e73ca6` | `ARCHITECTURE.md` (sv9, regla 19, acceso a Sigrid, despliegue; corrige el `almacen: true` de F-051 R24), dominio §5.2/§5.1, design §4 y tasks (T27b con el cerrojo de T24b, **T27c** nueva), Parte B de `propuestas_a_sigrid_api_F-053.md`; `azure-apps/albaranes.md` en su repo (`d43f200`). |
| T24 | `070813a` | Cobertura y lint de los tests nuevos. |
| T25 | `5a01be3`, `7dad2a0` | Campaña de mutación completa y tests que matan sus supervivientes (§6). |

Ficheros de sv4 tocados: `config/settings.py`, `main.py`, `domain/models/{alta_sigrid_models.py (nuevo), review_models.py}`,
`domain/services/alta_sigrid.py` (nuevo), `domain/ports/orchestrator_port.py`, `application/services/review_service.py`,
`infrastructure/{colas/colas_orchestrator_client.py, database/review_repository.py}`, `interface_adapters/web/app.py`,
`templates/{_alta_sigrid.html (nuevo), document_detail.html, documents_list.html}`, `static/{app.js, styles.css}`.
Tests nuevos de sv4: `test_f053_t17…t21b` (7 ficheros, 336 tests) y el doble `tests/f053_sv4_bbdd.py` (SQLite real).

## 2. Decisiones de diseño

1. **`ReviewService(repo, reviewer, orquestador, config)` posicional y opcional**: los dobles `lambda *_` de F-051/F-052
   siguen valiendo; sin config, feature apagada.
2. **El paso a aprobado lo decide el repositorio** en su transacción (`set_approved` devuelve `bool`;
   `update_document_y_transicion` devuelve `(detalle, paso)`; `update_document` delega). Así R2 no tiene carrera.
3. **R37 dentro de la transacción**, DESPUÉS de aplicar las ediciones de líneas del propio guardado (una valoración
   manual completada en el mismo PUT cuenta); si no está valorado, la sesión se cierra sin confirmar: nada cambia.
   Solo en el PASO a aprobado: guardar uno ya aprobado no se rechaza. Vale con DESDE vacía (R37 lo dice).
4. **Cerrojo portable**: `select(...).with_for_update()` (SQLAlchemy lo omite en SQLite) y `inspect(...).has_table`
   para «sin tabla». Probado además en un PostgreSQL 16 efímero (§5).
5. **`set_approved(True)` toma el cerrojo pero no mira el alta**: aprobar no está en R25 (no cambia nada del alta).
6. **Familia de la línea la interpreta el servicio**, no el repositorio: el guardián de F-036 R6 prohíbe `tipo_familia`
   en el código del repositorio.
7. **Producto con DESDE vacía ⇒ 400 «desactivada»** (R3: con la feature apagada no se ofrece; la ruta tampoco escribe).
8. **Revalorar / re-buscar**: comprobación sin cerrojo (design §11), unconditional de DESDE (un bloqueante sigue
   bloqueando aunque se apague la feature, igual que el cerrojo del repositorio).
9. **Mapeo en infra**: vacío = defecto del código (igual en sv4 y sv9); si el humano lo cambia, se pasa con las
   comillas escapadas para PowerShell 5.1 y se relee. Así un JSON roto por el shell no tumba sv4 (R44).
10. **`$APPS` reordenado** para que el despliegue completo siga design §8 (sv4 el último).

## 3. Desviaciones (justificadas)

- **T18 y T19 en un commit** (`ee936f3`): el paso a aprobado (T18) sale del repositorio con cerrojo (T19); partirlos
  dejaba un commit roto en ejecución. **R37** (T21b) entró en ese mismo commit por el mismo motivo; su RED se
  enseña quitando la comprobación (§4), no antes de escribirla.
- **Dobles de otras features actualizados** (no su intención): `_RepositorioFalso` de F-052 gana
  `update_document_y_transicion`, `_ServicioFalso` de F-052 T19 gana `guardar`, el guardián de F-036 R24 mira
  `update_document_y_transicion` (y que `update_document` delega).
- **comun crece** (no estaba en design §3): las reglas que sv4 y sv9 deben decidir igual (DESDE, Espera, vinculada,
  línea a registrar, estados repetibles, clasificación del documento, motivos de configuración). Regla del monorepo.
- **T22 marcada `[x]` con su MANUAL pendiente** (leer el diff; `deploy.ps1` no admite `-WhatIf`).
- **T27c nueva** en `tasks.md` (carrera sv9 ↔ sv4 en el PostgreSQL local), como pidió la review fase 1 pasada 3 §7.1.

## 4. Fase RED (comando: `python -m pytest -q -p no:cacheprovider <fichero>` desde el servicio; salida real)

```
T17 comun : E   ModuleNotFoundError: No module named 'ruesma_comun.configuracion' … 1 error
T17 sv4   : 21 failed — 6× DID NOT RAISE ValidationError · 4× 'ColasOrchestratorClient' object has no attribute
            'solicitar_alta_sigrid' · 4× 'Settings' object has no attribute 'config_alta_sigrid' ·
            AssertionError: assert {'action': 'queued', …} is True
T18       : 15 failed, 1 passed — 14× TypeError: ReviewService.__init__() takes 3 positional arguments but 5 were given
T19       : 27× Failed: DID NOT RAISE AlbaranBloqueadoError · 4× no attribute 'update_document_y_transicion'
T19b      : 24 failed — no attribute 'elegir_producto_sigrid' / 'guardar_producto_sigrid' / 'productos_sigrid'
T20       : 21× no attribute 'solicitar_alta_sigrid' · 16× 404 (rutas nuevas) · 12× AlbaranBloqueadoError sin
            traducir (500) · 3× assert 200 == 409
T21b      : 6× 'DocumentDetailPayload' object has no attribute 'valorado' · assert 'disabled' in '<button … Aprobar'
T21b repo : (sin la comprobación de R37) set_approved: 5 failed, 5 passed · update: 5 failed, 5 passed
T21       : 55 failed, 5 passed — 42× "DocumentDetailPayload" object has no field "alta_sigrid_activa"
T24b sv9  : E AssertionError: assert <Decision.PROCESAR: 'procesar'> is <Decision.IGNORAR: 'ignorar'> · 2 failed
```

Controles negativos a mano (`control.py` del scratchpad: muta, ejecuta UN fichero, restaura byte a byte con sha256;
`git status` limpio tras cada uno):

| Control | Resultado |
|---|---|
| T19 N1: `_exigir_desbloqueado` en UNA sentencia (`FOR UPDATE OF m` + `LEFT JOIN`) | test H4: 1 failed (90 en el fichero: SQLite no sabe `OF m`) |
| T19 N2: `asignar_almacen` sin cerrojo · N3: solo `registrado` bloquea · N4: paso = `approved` | 7 · 29 · 2 failed |
| T19b: repo sin mirar vinculada · servicio sin lista blanca · vinculada con el elegido (R43) | 2 · 3 · 1 failed |
| T20: valorar sin mirar el alta · bloqueados como fallidos (R27) · verificar sin `registrado` · R30 sin DESDE · API sin 409 | 1 · 2 · 3 · 1 · 13 failed |
| T21: panel sin DESDE · listado sin DESDE · selector en vinculada · servicio lee el alta sin DESDE | 1 · 1 · 1 · 1 failed |
| T24b: alta leída antes del cerrojo | 3 failed |

## 5. Carreras en un PostgreSQL 16 EFÍMERO (scratchpad, `127.0.0.1:5546`, `trust`; parado y borrado al terminar)

Scripts `pg_carrera_sv4.py`, `pg_carrera_sv9.py` y `pg_humo_sv4.py` del scratchpad; código REAL de los repositorios.

```
sv4 (A = cerrojo de sv9 + INSERT en_curso sin COMMIT; B = soft_delete_document real):
  dos sentencias (código real): {'b_esperaba': True, 'b': 'RECHAZADO (en_curso)', 'espera_s': 2.0, 'is_active': True}
  control, una sentencia:       {'b_esperaba': True, 'b': 'BORRÓ', 'espera_s': 2.0, 'is_active': False}
sv9 (A = primer reclamar sin COMMIT; B = SqlAltaRepository.reclamar real):
  dos sentencias (código real): {'b_esperaba': True, 'b': 'ignorar'}
  control, sentencia única:     {'b_esperaba': True, 'b': 'procesar'}
Humo sv4: R37 partial rechazado (approved=False) · ok ⇒ paso_a_aprobado True · lineas_producto (sigrid_ide, contrato,
  contexto) · guardar_producto 12 ⇒ guardado, 11 ⇒ vinculada · leer_alta registrado bloqueante · producto con
  registrado ⇒ AlbaranBloqueadoError · listado ('doc-humo', valorado True, 'registrado')
```

## 6. Mutación (T25)

`python -m harness.mutacion --feature F-053 --workers 1` (en serie: «nunca dos suites a la vez»), `PYTHONPATH` a la
comun del worktree, lanzada desacoplada (`Start-Process`) para que sobreviva a las caídas de sesión. Informe:
**`progress/mutacion_F-053.md`** (alcance completo de la feature: fases 1 y 2, 41 ficheros, 5148 líneas).

| Campaña | HEAD | Mutantes | Muertos | Supervivientes | Tiempo |
|---|---|---|---|---|---|
| 0 (cortada por una caída de la sesión en 126/628) | `070813a` | 126 | 81 | 42 en sv9 (+3 timeouts al caer) | — |
| 1 completa | `5a01be3` | 628 | 526 | **102** | 7607,3 s |
| 2 completa (la del informe) | `7dad2a0` | 628 | **618** | **10, todos equivalentes** | 5625,0 s |

- **Huecos cerrados con tests** (`5a01be3` y `7dad2a0`; cada mutante comprobado a mano con `control.py`: el test
  falla con él y pasa sin él): sv9 `test_f053_t25_supervivientes{,_2}.py` (64: modelos congelados, salida sin estado
  final de R9, detalle del adjunto, importes de una petición retomada, avisos de línea, código sin 400, orden H26,
  bordes de R10/R39 y del signo, fechas con zona, JSON sin escapar, topes de filas, reintentos, recortes, composición,
  visibilidad EXACTA de `main_worker` (1409 s / 1740 s y 1508 s / 1860 s) y avisos de arranque); sv4 (24: modelos y
  defectos, aviso de R4 en el log, descripción del deshacer, R30 sin DESDE y en el borde de DESDE, el cerrojo sobre EL
  documento pedido, «valorado» sin tabla, con una línea o con dos valoraciones, revisor del formulario, redirecciones,
  recuentos de R27, rutas fuera del OpenAPI); sv3 (20: líneas del conservado de R45 y el script de medición); comun (3).
- **Los 10 equivalentes** (análisis completo en el informe): el `en_vuelo = False` muerto tras cerrar el paso (sv9);
  dos variantes de la clave de orden de las manuales (no cambian el orden; `id` es único); tres bordes en importe 0 que
  `lineas_a_registrar` ya excluye (R13); `_json` con `and`, que acaba en el mismo `except`; tres del script de
  medición en cantidad/importe 0 o nulo que `con_importe` ya excluye.
- Fila nueva en `progress/inventario_mutacion_F-039.md` (F-039 R2).

## 7. Seguridad

- Ninguna ruta graba sin la llave: sv4 solo publica en `q-feedback`; sv9 sigue con `commit=true` solo si
  `ALTA_SIGRID_COMMIT` es el literal `true` (tests de la fase 1 intactos). `create_capps_sv9.ps1` crea sv9 con
  `false` y aborta si no; `set_alta_sigrid.ps1` no toca la llave; `deploy.ps1` la enseña antes de desplegar sv9.
- Ningún test ni script llama a sigrid-api real. Los logs nuevos no llevan valores de configuración (R44).

## 8. Verificaciones MANUAL pendientes (humano; comandos exactos en `tasks.md`)

- **T0b, T0c, T0** (de la fase 1; comandos en `progress/impl_F-053_fase1.md` §8). T0c fija `ALTA_SIGRID_USUARIO`.
- **T22**: leer el diff de `infra/` (`git -C C:\Users\pgris\PycharmProjects\albaranes-F-053 diff dev -- infra`).
- **T26, T27, T27b, T27c** (PostgreSQL LOCAL + Azurite; T27c es la carrera de sv4 en el navegador), **T28**
  (simulación en Azure tras desplegar en orden sv6, sv3 → sv9 → sv4, `infra/README_capps.md`) y **T29** (grabación
  real, con autorización).

## 9. Qué falta y avisos para el líder

- `init.sh` en el árbol principal tras fusionar (§10: en el worktree los KO son de entorno).
- **Parte B** de `progress/propuestas_a_sigrid_api_F-053.md`: coordinar con la sesión de sigrid-api (consumo).
- `CLAUDE.md` y `sigrid_api.md`: propuesta de design §9, sin aplicar (los decide el humano).
- Hallazgo menor: con un alta `registrado` y el adjunto en error, R30 no ofrece «Solicitar alta» (R23 dice que otro
  mensaje lo reintentaría): hoy el reintento del adjunto solo llega publicando a mano. Decisión del humano.
- **Junction** `services/albaranes-front/.venv` → venv de sv4 del árbol principal (ignorada por git): quitarla con
  `cmd /c rmdir services\albaranes-front\.venv` ANTES de `git worktree remove`.

## 10. `bash harness/init.sh` (T30)

`bash harness/init.sh` tal cual en el worktree (2026-10-09 04:08, salida completa en el scratchpad
`init_f053.log`): **4 comprobaciones fallidas, todas de ENTORNO, ninguna del código**:

```
[OK] pytest en verde (con medición de cobertura)          ← raíz
[OK] servicio sv1-email / sv2-api / sv5 / sv6 / comun: pytest en verde
[KO] servicio sv3-persistencia: E ModuleNotFoundError: No module named 'ruesma_comun.alta_sigrid'
[KO] servicio sv4-front:        E ModuleNotFoundError: No module named 'ruesma_comun.valoracion'
[KO] servicio sv9-alta-sigrid:  E ModuleNotFoundError: No module named 'ruesma_comun.alta_sigrid'
[KO] PUERTA COBERTURA: 4.4% de 2085 líneas cambiadas cubiertas (92/2085, umbral 80%, nivel critico)
[OK] PUERTA RUTAS SENSIBLES: N/A · [OK] PUERTA TAMAÑO: 150/150, 250/250 · [OK] Rama actual
```

- Los tres KO de servicio: los venvs del árbol principal tienen `ruesma_comun` instalado editable desde
  `../albaranes/services/albaranes-comun` (en `dev`, sin `alta_sigrid`, `valoracion` ni `configuracion`), y `init.sh`
  no admite el `PYTHONPATH` al comun del worktree (los agentes lo lanzan sin variables). La comun del worktree en sí
  pasa (516 passed). Es el mismo KO que dio F-062 y que la review de la fase 1 aceptó (C1 N/A).
- La puerta de cobertura cae por lo mismo: las tres suites no llegan a ejecutarse. Con `PYTHONPATH`, una suite tras
  otra, todas verdes y **96,2 %** (§11).
- **Verificación definitiva**: `bash harness/init.sh` en el árbol principal tras fusionar en `dev` (T30 y la de T0d
  quedan abiertas hasta entonces).

## 11. Evidencias

| Evidencia | Valor |
|---|---|
| Tests (una suite tras otra, bajo `coverage`, comun del worktree) | comun **513 passed, 3 skipped** (152,9 s) · sv3 **645** (25,6 s) · sv6 **289** (15,3 s) · sv9 **451** (17,2 s) · sv4 **794** (115,8 s) · raíz **1083** (6224,9 s: máquina cargada) |
| Tests nuevos de la fase 2 | sv4 336 + 24 (T25) · comun 37 + 3 · sv9 3 (T24b) + 64 (T25) · sv3 20 (T25) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 96.2% de 2054 líneas cambiadas cubiertas (1976/2054, umbral 80%, nivel critico)` |
| Mutación | campaña completa: **628 mutantes, 618 muertos, 10 supervivientes equivalentes justificados**, 0 timeouts, 5625 s (`progress/mutacion_F-053.md`) |
| Tamaño | requirements 150/150, design 250/250 (sin crecer) |
| Lint | `ruff` limpio en lo nuevo de sv4 (tests, `alta_sigrid_models`, `alta_sigrid`), sv9 y comun nuevo |
