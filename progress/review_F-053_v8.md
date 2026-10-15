Revisión incremental desde `93f24e9` (v8, Bloque H, pasada 1): `93f24e9..b845541`. Lo aprobado hasta `93f24e9` queda dado por bueno.
<!-- progress/review_F-053_v8.md -->
# Review F-053 v8 · Bloque H (T41–T50, T52) · reviewer, 2026-10-14

## Veredicto: CHANGES_REQUESTED

El código de la v8 está bien y cumple la spec: `usu` resuelto en un único punto, R48 sin llamar con `usu` vacío, R49
por los dos caminos, R14 igual en SQL y Python, «Reintentar adjunto» solo en sus condiciones y ningún camino nuevo
hacia Sigrid con `ALTA_SIGRID_COMMIT` distinto de `true`. Se rechaza **solo por las puertas de mutación de `critico`**:
(1) la verificación de T50, `python -m harness.mutacion --feature F-053`, no se ejecutó; (2) la tabla manual no es
reproducible; (3) el equivalente 38 no lo es; (4) ningún equivalente trae demostración ejecutable (RM5).

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige: fase RED, cobertura ≥ 80 %, campaña de mutación de la
herramienta con 0 supervivientes sin test o sin justificación aceptada por el humano, RM5 y MANUAL con su comando.

## Lo que he ejecutado (el árbol queda limpio: `git status` vacío)

- **`bash harness/init.sh`** en el worktree: `ENTORNO LISTO`, exit 0. Raíz **1083 passed**; `PUERTA COBERTURA:
  100.0% de 128 líneas (critico)`; `PUERTA TAMAÑO` 150/150 y 250/250. sv4 y sv9 salieron «por caché», así que los
  ejecuté enteros y sin caché: **sv9 621 passed** (43 s) y **sv4 1350 passed** (150 s).
- **Fase RED reproducida en una COPIA del scratchpad** (código anterior a la tarea, tests de HEAD). T41 sin
  `usuario_sigrid.py`: `ModuleNotFoundError`. T45 con validador y cliente de `0cb760f`: `ImportError:
  SEPARADORES_REFERENCIA`; con un stub que no normaliza, `assert '2.172.946' == '2172946'` y otros. T43 con
  `candidato = None`: `('buscar_alba…') == ('buscar_usuario', 'Ana')` y `SIMULADO is ERROR`. T46 con el `app.py` de
  `9d4a5e3`: **5 failed**, todos con cabecera más el caso `"   "` que añadió T50. T48 con el modelo de `568600e`:
  `'AltaSigridVista' object has no attribute 'usu'`. Coincide con el §3 del informe.
- **Muestra de 10 filas de la campaña manual** sobre una COPIA, con su mismo método (sin `-x`; sv9 entero y los 7
  ficheros de sv4). Línea base **sv9 621 passed (56 s), sv4 231 passed (60 s)**. Fallos, informe → míos: #1 1→1,
  #10 1→1, #17 8→8, #22 74→74, #25 1→1, #38 0→0, #48 1→1, #50 0→0, #56 1→1, #57 1→1. Todas cuadran. Los muertos de
  la muestra caen por tests de conducta; #10 por el cuerpo exacto de `sql/read`, que es conducta en la frontera del
  cliente y no un test textual (RM3 no aplica). 35–73 s por mutante, coherente con la línea base (RM2).
- **RM1**: medida en `1b3c8e51db2692d9e1bc0c8ef395b8cba833f077`; después solo cambian tests y `progress/`
  (`git diff --stat 1b3c8e5..HEAD`). El alcance medido es el que reviso.
- **Recálculo con la herramienta** (`harness.alcance` + `generar_mutantes`, cálculo puro): alcance
  `dcd25cc..feature/F-053-alta-sigrid`, 16 ficheros y **64 mutantes**. Desglose: sv4 `alta_sigrid.py` 22,
  `alta_sigrid_models.py` 8, `review_service.py` 6; sv9 `usuario_sigrid.py` 8, servicio 7, cliente 5; resto ≤ 3.
  **La campaña automática no da 0 mutantes**: no procede sustituirla por una manual.

## Checkpoints

- **C1** [x] `init.sh` en verde · [x] ficheros del arnés. **C2** [x] una sola `in_progress` (F-053) · [x] rama `feature/F-053-alta-sigrid` · [x] `current.md` abre con la
  v8 y la MANUAL T51 (los bloques de otras features que siguen debajo guardan MANUAL pendientes del humano y son
  anteriores a la v8) · [x] lo `done` está en `history.md`.
- **C3** [x] hexagonal: `usuario_sigrid` y `alta_sigrid.py` puros; `buscar_usuario` en el puerto · [x] primera línea
  con ruta en los 9 ficheros nuevos · [x] sin `print`, sin TODO, sin dependencias nuevas · [x] sin secretos: barrido
  del diff con GUID, IPv4, `password`, `AccountKey`, `sig=`, base64 de 40 o más caracteres y CIF; solo salen SHA y un
  `pg_password="x"` en un doble. `00_capps_vars.ps1` entero: solo `pgris`, que es un login (U5) · [x] trampas del
  monorepo: sin DDL; sv9 lee `approved_by` del merge con `FOR UPDATE` (`sql_alta_repository.py:53-56`).
- **C4** [x] trazabilidad (tabla de abajo, todo en verde) · [x] sin red: `httpx.MockTransport`,
  `https://sigrid.invalid`, dobles y SQLite en memoria · [x] T51 en `current.md` con sus comandos PowerShell y el
  criterio VERDE/ROJO.
- **C4 bis**
  - [x] `rigor` declarado · [x] RED real y reproducida · [x] cobertura `[OK]` 100 %.
  - [ ] **Mutación generada por la herramienta**: no existe. «Pisaría `mutacion_F-053.md`» no es motivo: `--salida`
    existe (`harness/mutacion.py:1838`), y T50 fija ese comando como verificación.
  - [ ] **Campaña manual reproducible**: 32 de las 64 filas van recortadas con «…» (8, 10–12, 14–16, 24–32, 35, 36,
    38–44, 49–54, 58). En 5 (11, 30, 35, 39, 49) original y mutado salen IGUALES en la tabla. `mutar_v8.py` vivía en
    un scratchpad ajeno.
  - [ ] «Tiempo total» y nº de workers: no están en el informe de mutación ni en «Evidencias», así que el coste por
    mutante no se puede comprobar con sus propios datos. Mi muestra sí es coherente.
  - [x] sin «⚠ CAMPAÑA NO VÁLIDA»; base declarada y en verde · [x] RM1 · [x] RM2: base de 24,5 s / 45,4 s frente a
    mis 56 s / 60 s, misma escala.
  - [ ] **RM5**: ni el 38 ni el 50 traen demostración ejecutable. El 50 solo tiene prosa. El 38 remite a tests que
    pasan con y sin el mutante, y eso demuestra que la suite no lo distingue, no que sea equivalente. Además el 38 **no
    es equivalente** (cambio 3).
  - [x] RM6: 25, 35, 54, 57 y 59 se mataron con tests nuevos, sin quitar ninguna guarda (`77b6257` solo toca tests).
  - [x] ninguno en `PENDIENTE` · [ ] en `critico`, los equivalentes 38 y 50 no constan aceptados por el humano (lo
    aceptado el 2026-10-13 son los 10 de la v7) · [x] «Evidencias» con los cuatro números · [ ] sin los workers.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: la puerta imprime «F-053 no toca ninguna ruta sensible».
- **C5** [x] T41–T50 y T52 `[x]`, cada una con su commit `F-053 Tn:`; las abiertas son MANUAL del humano · [x] nada
  sin trackear · [x] `features.json` `in_progress`.

## Lo que se pidió comprobar (todo [x] salvo la mutación)

- **`usu` en un único punto.** `_resolver_usuario` (`alta_sigrid_service.py:231-257`) es el único que llama a
  `candidato_usuario` y `buscar_usuario`. El docstring dice dónde entra F-069 y no hay código especulativo.
  `approved_by` sale del merge bajo el cerrojo (`reclamacion.py:78`), nunca del mensaje.
- **`usuario_no_resuelto`.** Se decide antes de validar. Sin `usu`, ni previa ni grabación. El adjunto sin `usu` en la
  petición no llama (`:394-402`). El respaldo se recorta y no tiene defecto en código.
- **R49** (`app.py:465-471`): por el listado (`:757`) y por el PUT (`:1209`). El PUT sin aprobar no escribe
  `approved_by` (`review_repository.py:3904-3907`).
- **R14.** `UPPER(REPLACE×4(d.entref))` se construye desde `SEPARADORES_REFERENCIA`, los mismos de
  `normalizar_referencia`; que el orden sea UPPER y luego REPLACE da igual. Un número que queda vacío no busca.
- **«Reintentar adjunto».** sv4 lo ofrece solo con alta `registrado` + `real` + adjunto sin colgar y el documento
  dentro de DESDE; sv9 `_solo_adjunto` vuelve a exigir `REAL` (`:453`).
- **Escritura en Sigrid.** Los únicos `commit=True` son los de la v7 (grabación tras `if SIMULACION: return`;
  `concepto-grafico` solo en `REAL`). La lectura nueva es `sql/read`. Ningún script pone `COMMIT`.
- **sigrid-api intacto** (último commit `838a94a`, 2026-10-07; la propuesta va en `propuestas_…` §C). **`azure-apps`
  `77c6bf6`**: solo `albaranes.md` §10; el barrido no encuentra secretos, IDs, IPs ni claves.

## Cobertura de requisitos (v8)

| R | Tests (servicio) |
|---|---|
| R12 | `test_f053_r12_*` (22; `validar_y_construir(..., usu)`), sv9 |
| R14 | `test_f053_r14_*` (10; SQL = Python, número vacío no busca), sv9 |
| R15 | `test_f053_r15_incierto_retomado_reenvia_su_usu_sin_leer_dbo_usu` y 12 más, sv9 |
| R22/R23 | `test_f053_r22_*` (13), `test_f053_r23_*` (6, también solo adjunto en simulación), sv9/sv4 |
| R29 | `test_f053_r29_*` (17; `usu`, «(respaldo)», recorte), sv4 |
| R30 | `test_f053_r30_*` (17; reintentar adjunto, DESDE vacía no lee nada), sv4 |
| R47 | `test_f053_r47_*` (23; candidato, cliente, servicio, config), sv9 |
| R48 | `test_f053_r48_*` (5; lectura caída, respaldo vacío, sin llamar a nadie), sv9 |
| R49 | `test_f053_r49_listado` y `_ficha` (8+8 casos), `_ficha_sin_aprobar_no_publica…`, sv4 |

## Cambios requeridos

1. **Campaña de la herramienta.** `python -m harness.mutacion --feature F-053 --salida
   progress/mutacion_F-053_v8_arnes.md`, entera (en `critico` sin tope); no pisa `mutacion_F-053.md`. Cada
   superviviente, con un test o como equivalente demostrado (cambio 4). Ese informe pasa a ser la evidencia de C4 bis.
   La manual puede quedarse como complemento (cubre la plantilla y el texto SQL), pero entonces cumple el cambio 2.
2. **Si la manual se mantiene** (`progress/mutacion_F-053_v8.md`): texto exacto original → mutado de las 32 filas
   recortadas, empezando por 11, 30, 35, 39 y 49 (vale un anexo o pegar el bloque de sustituciones de `mutar_v8.py`);
   arreglar la fila 25 de «Supervivientes … cerrados con test», que es una copia de la tabla principal; declarar el
   «Tiempo total» y que corrió en serie (1 worker). Lo mismo en «Evidencias» de `impl_F-053_v8.md`.
3. **El mutante 38 no es equivalente.** En una COPIA, con `test_f053_r49_revisor.py` y `DEFECTO = " revisor-local "`:
   el original pasa 17/17 y el mutante falla `test_f053_r49_listado[None-   - revisor-local ]` y
   `test_f053_r49_ficha[None-   - revisor-local ]`. Causa: `_reviewer_from_request` devuelve `settings.default_reviewer`
   sin recortar, mientras el servicio usa `_default_reviewer` recortado. El merge queda igual (`_clean_text`), pero el
   `MensajeFeedback` publicado cambia. Propuesta: `return (settings.default_reviewer or "").strip() or None` en
   `app.py:471`, con un test de `DEFAULT_REVIEWER` con espacios por los dos caminos (merge y mensaje recortados).
   Con eso el 38 sí pasa a ser equivalente.
4. **RM5: demostración ejecutable de cada equivalente** (38 tras el cambio 3, 50 y los que deje el cambio 1), con el
   patrón de `test_f053_t25_equivalentes.py`: cargar el módulo REAL, fabricar la variante con el texto exacto,
   comparar sobre un dominio amplio y añadir un control no equivalente que dé `> 0`. Para el 50 basta recorrer
   `ConfigAltaSigrid(desde=None|fecha)` × aprobado × activo × `approved_at_utc` (válida, ilegible, `None`).

**Para el líder y el humano (no son del implementer):** aceptación escrita de los equivalentes nuevos en `critico`;
MANUAL T51 tras el APPROVED y la fusión; la §C de la propuesta, con la sesión de sigrid-api.

## Observaciones (no bloquean)

- **O1.** Un número que solo tiene separadores no busca altas a mano (R14 no actúa) y sigue a la previa. Está
  documentado en `sv9.md`; si se quiere más prudencia, `revisar`.
- **O2.** `init.sh` dio sv4 y sv9 por caché. Para el cierre, las suites deben correr enteras en el árbol principal
  tras la fusión (T30).

**Automejora (propuesta, no aplicada):** en `CHECKPOINTS.md` C4 bis, «campaña MANUAL» solo sustituye a la herramienta
si esta da 0 mutantes sobre el alcance de la feature; «pisaría el informe anterior» no es motivo (existe `--salida`).
