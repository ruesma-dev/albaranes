<!-- progress/impl_F-113.md -->
# F-113 · Informe del implementer (T1–T8)

Rama `feature/F-113-mime-adjuntos-octet-stream`, worktree `../albaranes-F-113`, base `dev` `5dd1f45`. Rigor
`estandar`. Spec v1 con PARADA 1 cerrada (D-1 a D-4 y D-6 a D-8 = a; D-5 retirada). Hecho: T1–T8. **Fuera de este
trabajo**: T9, T10 y T11 (MANUAL del líder o del humano) y T12 (`init.sh` de cierre tras la review).

## 1. Qué cambió (un commit por tarea)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `638f0d8` | `ruesma_comun/mime.py` nuevo: `detectar_mime` (firma > declarado específico > extensión con tabla fija > `application/octet-stream`), `nombre_coherente`, `es_mime_generico`, `MIME_PDF`, `MIME_GENERICO`. Solo stdlib. |
| T2 | `3dde790` | `llm_client.normalizar_adjuntos` pasa cada adjunto por `_con_mime_real`: copia con MIME real y `kind` coherente, WARNING `declarado=… real=… kind=…` sin nombre, el MISMO objeto si no cambia. |
| T3 | `08d976d` | comun `0.9.0` ⇒ `0.9.1` (`__init__.py`, `pyproject.toml`); README con la fila de `ruesma_comun.mime` y la entrada 0.9.1. |
| T4 | `07a8f37` | sv1 `PollingPipeline._ingerir`: MIME real y nombre coherente ANTES del sha y del troceo; `attachment_content_type_declarado` en el meta solo si el MIME cambia; WARNING con ids y tipos. |
| T5 | `796ec70` | sv2 `_build_attachments`: `detectar_mime` + `nombre_coherente` tras `filename or "document.bin"`; el resto intacto. |
| T6 | `9fa6166` | `services/albaranes-email/scripts/medir_f113_octet_stream.py` (+ `scripts/__init__.py`), solo lectura, y su test sin BBDD. |
| T7 | `ce9d004` | `docs/ARCHITECTURE.md` (regla de blobs de `input/`). `azure-apps` `cff9063` (`albaranes.md`, l. 30), **local, sin push**. |
| T8 | `d506021` | Campaña de mutación + test que mata su superviviente; este informe. `tasks.md` marcado en `be9439c`. |

Ficheros de código tocados: `services/albaranes-comun/ruesma_comun/{mime.py, llm/llm_client.py, __init__.py}`,
`services/albaranes-comun/pyproject.toml`, `services/albaranes-email/application/pipelines/polling_pipeline.py`,
`services/albaranes-email/scripts/{__init__.py, medir_f113_octet_stream.py}`,
`services/albaranes-api/application/pipelines/extract_albaran_pipeline.py`. Tests nuevos:
`albaranes-comun/tests/test_f113_mime.py` (110), `test_f113_llm_adjuntos.py` (15),
`albaranes-email/tests/test_f113_mime_real.py` (14), `test_f113_medicion.py` (17),
`albaranes-api/tests/test_f113_build_attachments.py` (11). Test viejo tocado: uno (desviación 2).

## 2. Decisiones y desviaciones (justificadas)

1. **`normalizar_mime` público en `ruesma_comun.mime`** (T4). sv1 tiene que comparar el real con el declarado
   normalizado; design §5.2 pide «no duplicar la lógica» pero solo nombra un `_normalizar` privado. Se expone
   `normalizar_mime` (en `__all__`, con test) en vez de importar un privado entre paquetes. R6 pide «exportar» cuatro
   nombres, no «solo» cuatro.
2. **Test de versión de F-098** (`test_f098_t5_version_090`): exigía `0.9.0` exacta y R6 sube a 0.9.1. Pasa a «desde
   0.9.0 y pyproject = `__version__`», como hizo F-098 con el de F-076. Solo esa aserción. **Aviso para fusionar
   F-106**: su rama (0.10.0) seguramente toca el mismo test; conflicto trivial en el merge.
3. **R15 por encima de design §5.2** en un caso límite: design añade el declarado al meta también si solo cambia
   el nombre (`… or nombre_real != nombre`); R15 dice que, si el MIME coincide, el meta NO lleva el declarado. Se
   sigue R15: el nombre se corrige igualmente y deja su propio WARNING (`nombre corregido a la extension de …`,
   sin el nombre). Test `test_f113_r13_jpeg_declarado_jpeg_con_nombre_pdf_tampoco_se_trocea`.
4. **Declarado equivalente se conserva tal cual** (R15/R16): si `real == normalizar_mime(declarado)` (p. ej.
   `Image/PNG; name=…`), sv1 no toca el `content_type` y el flujo queda byte a byte como hoy. Solo cuando difiere
   pasa a ser el real.
5. **Script de medición** (T6): además de lo de design §6, filtra `correlation_key LIKE 'email:%'`. Sin eso, la rama
   `coalesce(..., '') = ''` contaría cualquier fila de otro tipo de workflow, que no lleva
   `attachment_content_type`. Normaliza también `; parámetros` con `split_part`. Doble candado de solo lectura:
   `default_transaction_read_only=on` en la sesión y `SET TRANSACTION READ ONLY` como primera sentencia. Las `PG_*`
   requeridas no tienen defecto (`PG_PORT` sí, 5432). Errores de conexión: solo el tipo.
6. **El blob de `input/`**: clave `.pdf` intacta (D-7); `IntakeColaClient`, `PdfPageSplitter`, `mail_client.py` y
   los tres clientes de IA, sin tocar (design §7). Ni DDL, ni mensajes de cola, ni variables de entorno.

## 3. Fase RED (comando y salida real del fallo, antes del código)

Todas con `$env:PYTHONPATH='C:\Users\pgris\PycharmProjects\albaranes-F-113\services\albaranes-comun'` y
`python -m pytest <fichero> -q -p no:cacheprovider` desde la raíz del worktree.

**T1** `services/albaranes-comun/tests/test_f113_mime.py`:
```
services\albaranes-comun\tests\test_f113_mime.py:11: in <module>
    from ruesma_comun.mime import (
E   ModuleNotFoundError: No module named 'ruesma_comun.mime'
ERROR services\albaranes-comun\tests\test_f113_mime.py
1 error in 1.15s
```
GREEN: `105 passed in 0.39s`.

**T2** `services/albaranes-comun/tests/test_f113_llm_adjuntos.py` (R7–R10):
```
>       assert bloque["image_url"].startswith("data:image/jpeg;base64,")
E       AssertionError: assert False
services\albaranes-comun\tests\test_f113_llm_adjuntos.py:161: AssertionError
E       AssertionError: assert 'input_file' == 'input_image'
FAILED ...::test_f113_r10_openai_jpeg_octet_stream_va_como_image_jpeg
FAILED ...::test_f113_r10_openai_jpeg_declarado_pdf_no_va_como_input_file
12 failed, 3 passed in 13.00s
```
(Los 3 que pasaban son R9, la identidad y la regla de hoy: no regresión, verdes antes y después.) GREEN:
`15 passed`; `pytest services/albaranes-comun -k llm`: `28 passed, 1172 deselected`.

**T3** `-k version` en `test_f113_mime.py`:
```
FAILED tests/test_f113_mime.py::test_f113_r6_version_091 - AssertionError: as...
1 failed, 105 deselected in 0.90s
```
GREEN: `462 passed` (test_f113_mime + f098 + f076 + f052).

**T4** `services/albaranes-email/tests/test_f113_mime_real.py` (R11–R16):
```
E       AssertionError: assert 'application/octet-stream' == 'image/jpeg'
E       assert [1] == [1, 2, 3]
E       ValueError: not enough values to unpack (expected 1, got 0)
E       assert 0 == 1
FAILED ...::test_f113_r12_whatsapp_octet_stream_sube_como_image_jpeg
FAILED ...::test_f113_r11_pdf_multipagina_sin_extension_y_generico_se_trocea
FAILED ...::test_f113_r13_jpeg_con_nombre_pdf_va_como_imagen
FAILED ...::test_f113_r14_warning_sin_nombre
9 failed, 5 passed in 5.34s
```
(Los 5 verdes son R15/R16, de no regresión.) GREEN: `14 passed`; `pytest services/albaranes-email -k "f054 or f048
or intake or f113"`: `219 passed`.

**T5** `services/albaranes-api/tests/test_f113_build_attachments.py` (R17–R19):
```
E           mime_type: 'application/octet-stream' != 'image/jpeg'
E         Drill down into differing attribute kind:
E           kind: 'pdf' != 'image'...
FAILED ...::test_f113_r17_jpeg_octet_stream_sin_preproceso_va_como_image_jpeg
FAILED ...::test_f113_r17_jpeg_octet_stream_pasa_por_el_realce
FAILED ...::test_f113_r17_jpeg_con_nombre_pdf_no_va_como_pdf[application/pdf]
FAILED ...::test_f113_r18_pdf_generico_sin_extension_pdf_va_como_pdf[documento.bin-application/octet-stream]
7 failed, 4 passed in 3.88s
```
(Los 4 verdes son R19, de no regresión.) GREEN: `11 passed`; tests de sv2 que usan el pipeline: `82 passed`.

**T6** `services/albaranes-email/tests/test_f113_medicion.py`:
```
    from scripts import medir_f113_octet_stream as medir
E   ImportError: cannot import name 'medir_f113_octet_stream' from 'scripts' (unknown location)
1 error in 1.20s
```
GREEN: `16 passed`; con el test de la mutación, `17 passed`.

## 4. `bash harness/init.sh` (T8) y el entorno del worktree

- **Tal cual, 1.ª pasada: rojo** por el entorno: el worktree no tenía `services/albaranes-front/.venv` (KO de
  `servicios.json`). Creada la *junction* de siempre al `.venv` de sv4 del árbol principal (como F-086, F-098 y
  F-104). **Quitarla con `cmd /c rmdir` antes de `git worktree remove`.**
- **Tal cual, 2.ª pasada: rojo, solo sv1 y sv2**: `ModuleNotFoundError: No module named 'ruesma_comun.mime'`, porque
  importan la comun 0.9.0 del árbol principal (el arnés lo avisa: «su suite prueba ESA copia»). Mismo caso que
  F-086/F-098.
- **Con `PYTHONPATH` a la comun del worktree** (forma Windows, desde Git Bash): **verde, exit 0** → ver §6.
- **`harness/features.json` de esta rama no tiene la ficha de F-113** (vive en `chore/alta-F-111-F-112`, `51c9195`, y
  no estaba en `dev`). No se ha tocado (orden del líder). Consecuencias: las puertas de cobertura, rutas sensibles y
  tamaño miden la feature `in_progress` (F-106, nivel `critico`) sobre el diff de ESTA rama; el umbral es el mismo
  (80 %). La mutación necesitó `--rama feature/F-113-mime-adjuntos-octet-stream --max-mutantes 20 --semilla
  20260820` (los valores de `estandar`), porque sin la ficha abortaba: «no existe la rama (sin declarar)».

## 5. Verificaciones MANUAL pendientes (no hechas aquí)

- **T9** (líder o humano, solo lectura): `medir_f113_octet_stream.py` contra Azure ANTES de desplegar, con las
  `PG_*` de Azure en la consola (el `.env` de sv1 apunta a local), y anotar el recuento aquí. Comando:
  `cd services\albaranes-email; python -m scripts.medir_f113_octet_stream [--csv f113.csv]`.
- **T10** (humano): fusionar en `dev` ANTES que F-106 (D-8) y desplegar sv1 y luego sv2:
  `Set-DeployTag; .\deploy.ps1 -Only sv1`, `.\deploy.ps1 -Only sv2`, `.\check_deploy.ps1`.
- **T11** (líder, solo lectura): el script a las 24 h: 0 casos nuevos.
- Push de `azure-apps` (`cff9063`): lo decide el humano.
- La recuperación de los 5 documentos del 2026-10-30 queda fuera (D-5): a mano.

## 6. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados (`init.sh` final, `PYTHONPATH` al worktree y `ARNES_SIN_CACHE=1`, HEAD `2019480`) | raíz 1919 passed; sv1 236; sv2 496; sv3 1576; sv4 1933 (1 warning); sv5 125; sv6 480 (1 skipped); sv9 1027; comun 1202 (3 skipped) — **0 fallos** |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.4% de 168 líneas cambiadas cubiertas (167/168, umbral 80%)` (la que falta es el cuerpo de `_conectar` del script, `pragma: no cover`: solo con BBDD real, MANUAL) |
| Mutantes | 44 generados, **20 evaluados** (muestreo `estandar`, semilla 20260820): **19 muertos, 1 superviviente**, 0 timeouts, 0 sin veredicto, 650,2 s, 4 workers. El superviviente (`--help` del script, `splitlines()[1]`) lo mata el test nuevo `test_f113_r20_la_ayuda_dice_que_mide` (comprobado a mano: `1 failed` con el mutante). Análisis en `progress/mutacion_F-113.md`. |
| Tiempo de la suite (pasada final) | raíz 256,07 s; sv1 32,71 s; sv2 22,54 s; sv3 15,34 s; sv4 239,64 s; sv5 42,84 s; sv6 30,69 s; sv9 86,28 s; comun 165,38 s |

## 7. `init.sh` final

- `export PYTHONPATH='C:\…\albaranes-F-113\services\albaranes-comun' ARNES_SIN_CACHE=1; bash harness/init.sh` en
  Git Bash sobre `2019480`: **exit 0, «ENTORNO LISTO»**. Avisos de siempre: ruff (1392, deuda previa), features
  `blocked`, marcas `[ADAPTAR]` de F-034/F-035.
- La pasada anterior (sobre `6a8c6e6`) salió roja por **un fallo real mío**: `test_f039_r2_…_inventario` exige una
  fila por informe de mutación. Añadida la de `mutacion_F-113.md` a `progress/inventario_mutacion_F-039.md` (58
  informes), commit `2019480`.
- Tal cual (sin `PYTHONPATH`): rojo SOLO en sv1 y sv2 por el entorno del worktree (§4), como F-086/F-098.
