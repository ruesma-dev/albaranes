<!-- progress/impl_F-048_bloque_E.md -->
# F-048 · Bloque E (T29–T31) · evals: el correo del caso y la inyección — texto íntegro

Rigor `critico`. Rama `feature/F-048-correo-contexto-ia1`. 2026-09-24. Resumen en
`progress/impl_F-048.md`, sección «Bloque E (T29–T31)». **No se lanzó nada contra LLM, Azurite ni Azure.**

## Commits

| Tarea | Commit | Qué |
|---|---|---|
| T30 | `01c4b13` | `evals/inyeccion.py` y `tests/test_f047_r2_r16_inyeccion.py` traídos de F-047 con `git checkout`, sin cambios |
| T29 | `10fd14b` | `evals/correos.py` (nuevo) y `tests/test_f048_evals_correos.py` (33 tests) |
| T31 | `00b60ab` | `evals/inyeccion.py` (parámetro `correo`, `sin_correo`, `--sin-correo`) y `tests/test_f048_r40_r41_inyeccion.py` (13 tests) |

## T30 · lo traído de F-047 (decisión del humano del 2026-09-24)

- **Ficheros traídos**: `evals/inyeccion.py` y `tests/test_f047_r2_r16_inyeccion.py`. Ninguno más.
- **Dependencias de `inyeccion.py`** (por AST): `__future__`, `dataclasses`, `hashlib`, `json`, `logging`,
  `uuid` y `ruesma_comun.{blobs.conexion, colas.conexion, colas.mensajes}`. Su test usa además
  `ruesma_comun.workflows.repositorio.ResultadoCreacion` y `pytest`. Nada de `evals/` de F-047.
- **Verificación** (en el commit de T30): `git diff feature/F-047-evals-ciclo-completo -- evals/inyeccion.py`
  → 0 bytes; `python -m pytest tests/test_f047_r2_r16_inyeccion.py -q` → `17 passed in 12.07s`.
  **Tras T31 el fichero ya difiere de F-047, a propósito**: la verificación de T30 vale para `01c4b13`.
- **Decisión: NO se trae `tests/test_f047_r5_seleccion_contrato.py`** (el test de `GestoRevisor`, que vive
  en `inyeccion.py`). Importa `LecturaCaso` de `evals/lectura_bbdd.py`, la capa de lectura del ciclo de F-047:
  623 líneas, depende de `evals/procesos/sv2_extraccion` y `sv6_build` en su versión de F-047, y la usan
  `ciclo.py`, `espera.py`, `aislamiento.py`, `atribucion.py`, `montaje.py` y siete ficheros de test. Traerla
  es empezar a traer el ciclo, que es justo lo que el humano descartó. Consecuencia: `GestoRevisor`
  (líneas 346–401 de `inyeccion.py`, más 126 y 177) queda **sin cubrir en esta rama**; nada lo usa aquí.
  Su test llega con F-047. Se ve en la cobertura: `inyeccion.py` 79 %, la feature 97.0 %.
- `tests/test_f011_r17_secuencial.py` de F-047 también nombra `inyeccion`, pero es un test de F-011 que F-047
  modificó: no es de la inyección y no se trae.

## T29 · `evals/correos.py`

- `DIRECTORIO_CORREOS = evals/inputs/correos` (la de `capturar_correo.py`; git la ignora por `.gitignore:36`).
- `cargar_correo(caso_id, directorio) -> ContextoCorreo | None`: sin fichero, `None`. Con fichero, valida y
  construye con `construir_contexto_correo(asunto, cuerpo, recibido_utc=...)`, la función de sv1.
- **Qué es mal formado** (`CapturaInvalida`, subclase de `ValueError`): no UTF-8 o no JSON, no es objeto,
  faltan `asunto` o `cuerpo`, `version` presente y distinta de 1, `caso_id` presente y distinto del pedido,
  `asunto`/`cuerpo`/`recibido_utc` que no son texto ni null. El mensaje lleva la ruta y el problema, nunca el
  contenido, y se lanza `from None` (la causa de `json` o de UTF-8 puede citar el texto).
- **Decisión: mal formado es error, no `None`.** Un «sin correo» silencioso daría por medida con correo una
  pasada que no lo llevó. Sin fichero sí es `None`: hoy ningún caso lo trae.
- **Decisión: copia manual válida.** §7 del design admite copiar el correo a mano: basta `asunto` y `cuerpo`.
- **Nombre de caso**: la misma expresión que `capturar_correo.py` (`[A-Za-z0-9][A-Za-z0-9_.-]*`); con `/`,
  `\`, `..` o vacío, `ValueError`.
- **R38**: `tiene_firma_de_correo(datos)` = un objeto con `asunto` y `cuerpo` a cualquier profundidad (lo que
  comparten captura, copia manual y contexto del blob lateral). `versionados_con_correo(raiz)` recorre
  `git ls-files -z -- evals tests`: cuenta todo lo versionado bajo `evals/inputs/correos/` y todo `.json` con
  la firma. El test sobre el repositorio real da `[]`; otro, sobre un repositorio de juguete en `tmp_path`,
  comprueba que encuentra lo versionado y solo eso (ni lo no indexado ni lo que está fuera de `evals/`/`tests/`).
  Un tercero confirma con `git check-ignore -q` que la carpeta de capturas está ignorada.
- **Parecido con `leer_captura` de sv2** (`encolar_extraccion.py`, T22): ambos leen el mismo formato. No se
  comparte porque es un script de sv2 fuera del paquete; si crece, el sitio es `ruesma_comun.correo`. Menor
  para el reviewer.

## T31 · la inyección con correo

- `Inyector.inyectar(caso_id, contenido, nombre_fichero, content_type, *, correo=None)`. Con correo:
  `payload_json.correo_sha256` (como R10 de sv1, sin texto), PDF → `guardar_contexto_correo(almacen,
  document_id, correo)` → `MensajeExtraccion(correo_blob=...)`. El `Inyeccion` devuelto lleva `correo_blob`
  (campo nuevo con defecto `None`: lo que ya construyera F-047 sigue valiendo).
- Si guardar el blob falla: `ErrorCorreo` con el `document_id` y el TIPO de la excepción, `from None`, y el
  mensaje no se publica (como `OrchestratorError("blob correo: <tipo>")` en sv1).
- Duplicado: ni blob de correo ni mensaje, como sv1. Log: `correo=SI(sha=<8>)` o `NO`, nunca texto.
- **`--sin-correo`** → `Inyector(sin_correo=True)`: descarta el correo aunque se lo pasen, lo dice en el log
  y no pone ni blob ni huella. **Desviación justificada**: el CLI que monta el `Inyector` es el `runner
  --ciclo` + `montaje.py` de F-047, que NO está en esta rama. Aquí queda `anadir_opcion_sin_correo(analizador)`
  para que ese CLI registre la opción y pase `sin_correo=opciones.sin_correo`; `ciclo.py` tendrá que pasar
  `correo=correos.cargar_correo(caso_id)`. Ese cableado es trabajo de la integración de F-047.
- **R41, con y sin correo**: el mismo caso en la misma pasada es la misma `correlation_key` (duplicado), así
  que «con y sin» son dos pasadas: el test lo fija (claves y documentos distintos, uno con blob, otro sin).
- Los 17 tests de F-047 siguen verdes sin tocarlos: sin `correo`, el comportamiento es el de F-047.

## Fase RED (test antes del código)

```
python -m pytest tests/test_f048_evals_correos.py -q --tb=line -p no:cacheprovider
E   ImportError: cannot import name 'correos' from 'evals' (C:\Users\pgris\PycharmProjects\albaranes\evals\__init__.py)
ERROR tests/test_f048_evals_correos.py
1 error in 1.65s                                           -> 33 passed in 3.44s

python -m pytest tests/test_f048_r40_r41_inyeccion.py -q --tb=line -p no:cacheprovider
E   TypeError: Inyector.__init__() got an unexpected keyword argument 'sin_correo'   (x12)
E   AttributeError: module 'evals.inyeccion' has no attribute 'anadir_opcion_sin_correo'
13 failed in 3.16s                                         -> 13 passed, 982 deselected in 7.90s  (-k "f048 and inyeccion")
```

**Mutantes a mano** (modificar, ejecutar el fichero de test, restaurar; árbol limpio después):
```
inyeccion.py  M1 sin_correo ignorado           -> 2 failed, 11 passed
              M2 huella fuera del payload      -> 1 failed, 12 passed
              M3 correo_blob no viaja          -> 1 failed, 12 passed
              M4 ErrorCorreo encadena la causa -> 1 failed, 12 passed
correos.py    C1 firma solo con asunto         -> 1 failed, 32 passed
              C2 sin mirar evals/inputs/correos/ -> 1 failed, 32 passed
              C3 sin control de versión        -> 1 failed, 32 passed
              C4 sin control de tipos          -> 2 failed, 31 passed
              C5 firma no anidada              -> 1 failed, 32 passed
```

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests del bloque | 63: 17 (F-047) + 33 (T29) + 13 (T31) passed |
| Suite raíz | `995 passed in 456.87s` en `bash harness/init.sh` (ENTORNO LISTO) |
| Cobertura de las líneas cambiadas | 97.0 % (1313/1354), `PUERTA COBERTURA`. `correos.py` 100 %; `inyeccion.py` 79 %: lo que falta es `GestoRevisor` (F-047, ver T30) |
| Mutación | campaña no relanzada (T34 es anterior); 9 mutantes a mano, 9 muertos. Campaña nueva: la decide el líder |
| Tiempo | los tres ficheros, 12.07 s + 3.44 s + 7.90 s |

## Verificaciones MANUAL pendientes y fuera de alcance

- **Fuera**: el ciclo de F-047 (`ciclo.py`, `montaje.py`, `runner --ciclo`), así que en esta rama nadie llama
  todavía a `inyectar(..., correo=...)` ni registra `--sin-correo`. La medición con correo de §7 necesita
  F-047 integrada y las capturas de T36.
- **Pendiente del líder/humano**: decidir si `test_f047_r5_seleccion_contrato.py` espera a F-047 (propuesta)
  o se trae con `lectura_bbdd.py`.
