<!-- progress/impl_F-048_bloque_C2.md -->
# F-048 · Informe del implementer, cambios de la review de C1 y bloque C2 completos

Texto íntegro del bloque C2 (sv2, T17–T22) tal como lo revisó el reviewer
(`progress/review_F-048_bloque_C2.md`, APPROVED con tres menores). Se sacó de
`progress/impl_F-048.md` el 2026-09-24 para que el informe principal quepa en su tope con los
bloques D y D bis; allí queda el resumen con las trazas RED y las evidencias. Aquí no se edita
nada salvo esta nota: **la decisión 2 («en filas 4 y 5 la cabecera no se toca») la revisó
CR-C5** (D4 bis, líder 2026-09-24): en la fila 4 la cabecera toma la forma de la lista.

## Bloque C2 · sv2 (T17–T22) — 2026-09-24

**Commits**: `909c59a` T17 · `f044067` T18 (+ `7edc6c2` ruff) · `28ebd71` T19 · `4e82365` T20 · `4e40f19` T21
· `2b40968` T22. **Producción**: nuevos `application/services/origen_datos_resolver.py` e
`interface_adapters/worker/correo_adapter.py`; cambiados `interface_adapters/worker/{ports,extraction_worker}.py`,
`application/pipelines/extract_albaran_pipeline.py`, `main_worker.py`, `encolar_extraccion.py` y, en comun,
`ruesma_comun/llm/retry_policy.py` (ruta sensible). **Tests**: seis `test_f048_*.py` (107 tests).

### Decisiones

1. **Resolver puro** `sellar_origen_datos(envelope, *, lectura, correo, obras_conocidas) -> dict`: copia el
   envelope (no muta nada), quita `data.lectura_correo`, pisa `data.origen_datos`, y solo reescribe
   `cabecera.obra_codigo` cuando cambia (sin correo, `data` idéntico salvo `origen_datos`; sin cabecera
   no inventa una). `lectura` vale como dict o como `LecturaCorreo`.
2. **Tabla de D5**: se normaliza, se deduplica (la primera forma que leyó IA1) y se descartan los vacíos;
   luego se filtra contra la lista. `{}` es «lista sin obras» (nada cuenta, `validada=false`); solo `None`
   es «sin lista». En filas 4 y 5 la cabecera no se toca, ni para darle la forma de la lista.
3. **`candidatos_correo`** = los que cuentan, también con UNO (`["0945"]`); en `correo_fuera_de_lista`, lo
   leído tal cual. **`fuente`**: `correo` solo en `correo_unico`; en `correo_confirma_papel` y
   `correo_ambiguo`, `papel` (la obra es la del papel). `valor_correo` solo en `correo_unico`.
4. **Aviso A**: el worker pasa la `lectura_correo` de `env1` (FASE 1) y sella el envelope FINAL (cabecera
   de IA2); la de IA2 se ignora y no llega al `data`. Test de resolver y de worker con IA2 cambiándola.
5. **Aviso B**: `obras_conocidas()` UNA vez por documento y SOLO si hay correo (sin correo no hace falta, y
   con sigrid-api caído cada consulta puede costar el timeout). El pipeline expone `obras_conocidas()`
   (delega en el servicio); `main_worker.py` pasa `pipeline.obras_conocidas` y `FuenteContextoCorreoBlob`.
6. **Blob**: ausente o que no valida ⇒ `None` y el documento sigue sin correo (nunca a poison por eso). Un
   fallo de RED del Blob se propaga y la cola reintenta, como con el PDF: es el contrato de
   `leer_contexto_correo` aprobado en el bloque A. Con `correo_blob` y sin fuente cableada, WARNING y sigue.
7. **Log del worker**: `correo=SI(n, sha8)/NO obra=<fuente>/<motivo> discrepancia=... validada=...`, nunca
   la evidencia.
8. **`retry_policy` (aviso A del bloque A, pasada 2)**: el RED demostró la fuga (un SDK que cita la petición
   desde la marca de inicio dejaba asunto y cuerpo en los 300 caracteres). `_mensaje_para_log` redacta con
   `redactar_correo` ANTES de recortar, en los tres logs. Toca comun (sv5 lo reexporta: 43 passed).
9. **Aviso C**: sin cambio de código. Una evidencia con `<<<INICIO_CORREO>>>`, `<<<FIN_CORREO>>>` o ángulos
   sueltos dentro de `{json_fase_1}` hace que la redacción omita de más, nunca de menos: con las cuatro
   variantes, ni `redactar_correo` ni el fichero de `LlmCallLogger` contienen el centinela.
10. **`encolar_extraccion.py`**: `argparse` compatible con el uso de hoy (`DOC` posicional, por defecto
    `DOC-PRUEBA-1`); `--correo` lee la captura de `capturar_correo.py` (`asunto`, `cuerpo`, `recibido_utc`)
    con el recorte por defecto (4.000); fichero malo ⇒ código 2 sin escribir ni publicar.

### Para el bloque D (sv3): lo que llega en `data.origen_datos`

Siempre presente en el envelope final (también sin correo). Es `OrigenDatos.model_dump(mode="json")`:
```json
{"version": 1, "correo_presente": true, "correo_sha256": "<64 hex>|null", "correo_truncado": false,
 "evidencia": "<≤160, o null>",
 "obra": {"fuente": "correo|papel", "motivo": "<uno de 7>", "valor_final": "0945|null",
          "valor_correo": "0945|null", "candidatos_correo": ["0945"], "valor_papel": "1203|null",
          "discrepancia": true, "validada": true}}
```
Motivos (`ruesma_comun.contratos.origen_datos`): `sin_correo`, `ia_sin_lectura_correo`, `correo_sin_dato`,
`correo_fuera_de_lista` (manda la IA, sin revisión); `correo_unico` (manda el correo; `discrepancia=true`
solo si el papel traía OTRO código ⇒ `obra_correo_distinta_papel`); `correo_confirma_papel` (sin revisión);
`correo_ambiguo` (⇒ `obra_correo_ambigua`). `cabecera.obra_codigo` ya viene con la forma de la lista. El
envelope NO lleva `data.lectura_correo`. **Ojo**: `debug.phase_2.debug.phase_1_json` sigue llevando la
`lectura_correo` de IA1 con su evidencia SIN recortar (es la auditoría de fase 1, como antes de F-048); si
sv3 guarda `debug` en `raw_extraction_json`, esa evidencia llega a la BBDD. No lo pide ninguna R; lo decide el líder.

### Fase RED → GREEN (`python -m pytest <fichero> -q --tb=line` en `services/albaranes-api`)

T17 y T20–T22, test antes que código; T18 y T19 prueban un resolver ya escrito en T17, así que su RED se
demuestra rompiendo una copia aislada de sv2 en el scratchpad (técnica de T6/T9/T11), mutación a mutación.
```
T17 E ModuleNotFoundError: No module named 'application.services.origen_datos_resolver'   1 error in 0.38s
    con un esqueleto que devuelve dict(envelope): E KeyError: 'origen_datos' (x23)    23 failed -> 23 passed
T18 A sin normalizar_codigo: E assert None == '0945' (x5); E assert True is False (x3)   16 failed, 14 passed
    B cabecera como la leyó IA1: E assert '09-45' == '0945'; E assert '０９４５' == '0945' 12 failed, 18 passed
    C contar antes de filtrar: E assert 'correo_ambiguo' == 'correo_unico' (x2)          2 failed, 28 passed
    D colisiones dentro del mapa: E assert 'correo_unico' == 'correo_fuera_de_lista' (x3)  4 failed, 26 passed
    HEAD                                                                                  -> 30 passed
T19 a sin quitar lectura_correo: E assert 'lectura_correo' not in {... ['1203'] ...}      7 failed, 7 passed
    b respeta el origen_datos de la IA: E assert 99 == 1                                  2 failed, 12 passed
    c muta el data de entrada: E assert ({'meta': {'p... == ({'meta': {'p...)             3 failed, 11 passed
    d lectura del documento final (IA2): E assert '1203' == '0945' (x3)                   5 failed, 9 passed
    HEAD                                                                                  -> 14 passed
T20 E ModuleNotFoundError: No module named 'interface_adapters.worker.correo_adapter'      1 error
    con puerto y adaptador: E TypeError: construir_handler_extraccion() got an unexpected keyword
    argument 'fuente_correo' (x10); ExtractAlbaranRequest ... 'contexto_correo' (x2); KeyError: 'fuente_correo'
    (main_worker); 'ExtractAlbaranPipeline' object has no attribute 'obras_conocidas'  16 failed, 6 passed -> 22 passed
T21 E assert '[correo omitido: sha256=' in 'WARNING ... retry_policy.py:211 [llm-retry] openai error NO
    retryable. type=_ErrorApi msg=...TINELA-F048\nCuerpo:\nHola, os paso el albaran de la 945.\nCENTINELA-F048 ...'
    (y retry_policy.py:236 y :220 con el mismo msg)                                     2 failed, 7 passed -> 9 passed
T22 E AttributeError: <module 'encolar_extraccion'> has no attribute '_cargar_entorno' (x9)  9 errors
    copia aislada con esos nombres: E TypeError: main() takes 0 positional arguments but 1 was given (x9)
                                                                                         9 failed -> 9 passed
```
Los 6 que ya pasaban en T20 son los de `FuenteContextoCorreoBlob`, escrita para el paso 1. Los 7 de T21: el
handler completo, el blob roto y la evidencia con marcas, que ya cumplían (el defecto estaba en retry_policy).

### Verificaciones MANUAL y lo que queda fuera

Sin MANUAL propia: el extremo a extremo con un correo real es T37 (`encolar_extraccion.py --correo`, ya
disponible). Rutas sensibles tocadas: `prompts.yaml` y `ruesma_comun/llm/retry_policy.py`; su evidencia es
T40 (se factura, visto bueno del humano). Fuera: bloques D–G. Riesgo que queda (no lo cubre R36 en sv2): el
consumidor de comun loguea la traza completa si el handler lanza, y una excepción de un SDK que citara la
petición llevaría el bloque al log del contenedor; ningún cliente de hoy lo hace (sus mensajes son fijos).

## Resultados reales

- Suites a mano, una detrás de otra: sv2 `338 passed in 3.61s` (188 de F-048); comun `259 passed, 3 skipped
  in 106.45s` (por `retry_policy`); sv5 `43 passed in 1.36s` (reexporta `retry_policy`).
- `bash harness/init.sh` (tras `89e4234`): exit 0, `ENTORNO LISTO`. Raíz `865 passed in 118.65s`; sv2
  `338 passed in 11.08s` y comun `259 passed, 3 skipped in 118.24s` corrieron de verdad; sv1, sv3–sv6 de
  caché (la clave no mira comun: por eso sv5 se corrió a mano). `PUERTA COBERTURA: 99.3% de 557 líneas
  cambiadas cubiertas (553/557)`. `[AVISO]` de rutas sensibles: 5, ahora con `retry_policy.py` (T40).
  Ruff de la raíz: 1160 avisos (uno menos: el `Callable` de `extraction_worker.py`). Impl 191/220.

## Evidencias (cambios de la review de C1 y bloque C2)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv2 338 passed (188 F-048, 107 nuevos del C2); comun 259 + 3 skipped; sv5 43; raíz 865 passed |
| Cobertura de las líneas cambiadas | 99.3 % (553/557), `PUERTA COBERTURA` de init.sh |
| Mutación | N/A en un bloque intermedio: campaña completa en T34 (`python -m harness.mutacion --feature F-048`) |
| Tiempo de las suites | sv2 3.61 s; comun 106.45 s; sv5 1.36 s |
