<!-- progress/impl_F-048.md -->
# F-048 · Informe del implementer

Rigor `critico`. Rama `feature/F-048-correo-contexto-ia1`. Una sección por bloque. El texto
íntegro de los bloques ya revisados está en `progress/impl_F-048_bloque_A.md`,
`progress/impl_F-048_bloque_B.md`, `progress/impl_F-048_bloque_C1.md`,
`progress/impl_F-048_bloque_C2.md`, `progress/impl_F-048_bloque_D.md`, `progress/impl_F-048_bloque_E.md`
y `progress/impl_F-048_evals.md`; aquí queda su resumen.

## Bloque A · comun (T1–T5) — resumen

**Commits**: `c351b18` T1 · `57516d6` T2 · `bd5a341` T3 · `940031e` T4 · `64eaf13` T5 · `172d514` ruff.
Review pasada 1: `32b3a57` CR-A1 · `87972da` CR-A2 · `606da58` CR-A3 · `56ad7f0` CR-A4 · `8568cec`.
Pasada 2: APPROVED (`4a6802b`). Nuevos `ruesma_comun/correo/{__init__,contexto,prompt}.py` y
`contratos/origen_datos.py`; cambiados `colas/mensajes.py`, `llm/llm_call_logger.py`.

**RED** (`python -m pytest tests/<fichero> -q --tb=line` en `services/albaranes-comun`):
```
T1  E   ModuleNotFoundError: No module named 'ruesma_comun.correo'          -> 1 error in 1.10s
T2  E   AttributeError: 'MensajeExtraccion' object has no attribute 'correo_blob'
    E   AssertionError: assert set() == {'correo_blob'}                      -> 5 failed, 2 passed in 1.00s
T3  E   ModuleNotFoundError: No module named 'ruesma_comun.correo.prompt'   -> 1 error in 0.95s
T4  E   assert 'CENTINELA-F048' not in '{\n  "times...true\n  }\n}'  (x2)     -> 2 failed, 3 passed in 4.07s
T5  E   ImportError: cannot import name 'OrigenCampo' from 'ruesma_comun.contratos' -> 1 error in 1.34s
CR-A1 E assert 'CENTINELA-F048' not in '{\n  "times..."{}"\n  }\n}'  (x4)     -> 4 failed, 5 passed in 0.90s
CR-A4 E AssertionError: assert '０９４５' == '945'  (y 3 más)                  -> 4 failed, 44 deselected in 1.73s
```
GREEN: T1 35 · T2 7 · T3 17 · T4 5 (9 tras CR-A1) · T5 44 (48 tras CR-A4).

| Evidencia (bloque A, tras la review) | Valor real |
|---|---|
| Tests F-048 del bloque | 116 passed (5 ficheros), 8.06 s |
| Suite comun / raíz | 259 passed + 3 skipped, 155.95 s / 865 passed, 362.91 s (init.sh) |
| Cobertura de las líneas cambiadas | 100.0 % (173/173), `PUERTA COBERTURA` |
| Mutación | en T34, con la feature completa |

## Bloque B · sv1 (T6–T12) — resumen

**Commits**: `e0e0a82` T6 · `2e6bf67` T7 · `bf9d983` T8 · `4a81304` T9 · `501b0fd` T10 · `97d6cf6` T11
· `8e2a309` T12 · `26a9496` imports. Review: APPROVED (`63cc1fc`), seis menores. Decisiones,
trazas completas y lo que el bloque B deja a sv2 (blob lateral `input/{id}.correo.json`,
`correo_blob`, huella en `payload_json`): `progress/impl_F-048_bloque_B.md`.
**RED** (T7, T8, T10, T12 con el test antes del código; T6, T9, T11 rompiendo una copia aislada):
```
T7  E   ImportError: cannot import name 'ContenidoCorreo' ...          -> 1 error in 0.73s
T8  E   TypeError: PollingPipeline.__init__() got an unexpected keyword argument 'correo_max_caracteres'
                                                                        -> 7 failed, 2 passed in 1.11s
T10 E   Failed: DID NOT RAISE OrchestratorError  (y 5 más)              -> 6 failed, 3 passed in 1.31s
T11 E   assert 'CENTINELA-F048' not in 'INFO     ht...Procesados\n' (x3) -> 3 failed, 1 passed in 1.39s
T12 E   ModuleNotFoundError: No module named 'capturar_correo'         -> 1 error in 0.23s
```

## Menores del bloque B y bloque C1 (T13–T16 bis) — resumen

Texto íntegro (decisiones, «Para quien haga T17–T22», trazas completas): `progress/impl_F-048_bloque_C1.md`.
**Commits**: `ecac419` CR-B1 · `8a7a46e` CR-B3 · `79a1485` CR-B5 · `51111b7` CR-B6 · `1f30462` T13 ·
`b0483c7` T14 · `8cb9db6` T15 · `adb488d` T16 · `1ef98fe` T16 bis. Review: CHANGES_REQUESTED (1 bloqueante).
```
T13 E ModuleNotFoundError: No module named 'domain.models.lectura_correo'       1 error    -> 7 passed
T14 E TypeError: ..._render_task_fase_1() takes 2 positional arguments but 3 were given  8 failed -> 8 passed
T15 E assert 'ATENCION: ... {json_fase_1} ... <<<FIN_CORREO>>>' in 'Eres un revisor...' 1 failed, 17 passed -> 21 passed
T16 E assert 'del correo solo se lee el código de obra' in '## convenciones generales ...' 13 failed -> 14 passed
T16 bis E AttributeError: 'AlbaranExtractionService' object has no attribute 'obras_conocidas' 22 failed, 4 passed -> 26 passed
```

## Bloque C1 · cambios de la review — 2026-09-24

**Commits**: `fe99db0` CR-C1 · `0efedb7` CR-C2. Solo `config/prompts.yaml` (ruta sensible) y su test.
- **CR-C1** (bloqueante 1): la viñeta de `obra_codigos` pide TODOS los códigos del correo, «estén o no en
  la lista de obras de arriba. Esa lista es solo para cabecera.obra_codigo; los códigos del correo los
  comprueba el sistema». Cuatro frases nuevas en el `parametrize` de `test_f048_r16_prompt_yaml.py`.
- **CR-C2** (menor 1): «Si el papel no permite identificar la obra, cabecera.obra_codigo es null, como
  hasta ahora», con su frase en el test. Que T40 compare la rama SIN correo con `dev` queda para T40.
- Menores 2 y 3 y aviso A: los resolvió el líder en design (`d4b51fb`); se fijan con tests en T18/T19.
```
CR-C1 E AssertionError: assert 'esa lista es solo para cabecera.obra_codigo' in '## convenciones generales ...' (y 3 más)
      4 failed, 14 passed in 1.25s                               -> 18 passed; con r12 y r14: 47 passed
CR-C2 E AssertionError: assert 'si el papel no permite identificar la obra, cabecera.obra_codigo es null, como hasta ahora' in ...
      1 failed, 18 passed in 1.34s                               -> 48 passed in 2.73s (r12 + r14 + r16)
```

## Bloque C2 · sv2 (T17–T22) — resumen

**Commits**: `909c59a` T17 · `f044067` T18 · `28ebd71` T19 · `4e82365` T20 · `4e40f19` T21 · `2b40968` T22.
Review: APPROVED (`c6709ff`), tres menores. Decisiones, la forma exacta de `data.origen_datos` para sv3
y las trazas completas (T18 y T19 con RED por copia rota, mutación a mutación):
`progress/impl_F-048_bloque_C2.md`.
```
T17 E ModuleNotFoundError: No module named 'application.services.origen_datos_resolver'  -> 23 passed
T18 A/B/C/D (copia rota): 16 / 12 / 2 / 4 failed                                          -> 30 passed
T19 a/b/c/d (copia rota): 7 / 2 / 3 / 5 failed                                            -> 14 passed
T20 E TypeError: construir_handler_extraccion() got an unexpected keyword argument 'fuente_correo'
    16 failed, 6 passed                                                                    -> 22 passed
T21 E assert '[correo omitido: sha256=' in 'WARNING ... retry_policy.py:211 ... CENTINELA-F048 ...'
    2 failed, 7 passed                                                                     -> 9 passed
T22 E TypeError: main() takes 0 positional arguments but 1 was given (x9)                 -> 9 passed
```

## Review de C2, bloque D (sv3) y D bis (sv4) — resumen

`43bc9b9..f68b510`: CR-C3..CR-C5, T23–T26 (sv3 acepta, conserva y marca `origen_datos`) y T27–T28
(ficha de sv4, solo lectura). Detalle, trazas RED y el bloqueo original en
[`progress/impl_F-048_bloque_D.md`](impl_F-048_bloque_D.md).

## CR-D1 · la red de obra ya no borra los motivos del origen — resumen

**Commit** `6356ad7`. Solo los VALORES de los dos motivos de comun (`correo_obra_distinta_papel`,
`correo_obra_ambigua`); la red de obra de sv3 no se toca. RED `4 failed` (sv3) y `1 failed` (comun)
-> verde. Resultados de entonces: init.sh verde, cobertura 99.5 % (639/642). Texto íntegro (tests,
trazas, MANUAL y evidencias de CR-D1): `progress/impl_F-048_bloque_D.md`, sección «CR-D1».

## Menores del bloque D y bloque F (T32, T33, T35) — resumen

`c909c59` CR-D2 · `5bae02e` CR-D3 · `fb54c05` CR-D4 · `cf00a08`/`2227889` T32 · `e362df6` T33; `azure-apps` `96bbdb6`
(sin push). Solo sv4 en producción. CR-D4 añade `obra_cambiada_tras_extraer`; T32 escribe la regla 15 de
`docs/ARCHITECTURE.md` y amplía `rutas_sensibles.json`; T33 cobertura 99.5 % (661/664); T35 tamaño OK.
Decisiones, RED y evidencias íntegras: `progress/impl_F-048_bloque_F.md`, primera sección.

## Bloque F · cambios de la review (pasada 1) — resumen

`9886281` CR-F1 · `768d559` CR-F2 · `739d80a` CR-F3 · `03bd912` CR-F4 (solo sv4 en producción): aviso de obra
sin sujeto, `albaran_extraction_service.py` en rutas sensibles, regla 15 corregida y estilo de `obra-cambiada`.
Resultado: sv4 246 passed, raíz 865, cobertura 99.5 % (661/664). Texto íntegro, RED y evidencias:
`progress/impl_F-048_bloque_F.md`.

## T34 · mutación completa, 0 supervivientes sin justificar — 2026-09-24 y 25
1.ª (`e7fe2c0`, 175): 26 vivos → 23 huecos con test y 3 equivalentes (9, 22, 23): `progress/impl_F-048_T34_supervivientes.md`.
**2.ª, con `evals/`** (`14cee8a`, 410 mutantes, sin muestreo, 2 workers, 21051 s): 330 muertos, 80 vivos. Reinyectados
uno a uno en worktrees: **71 huecos cerrados** (`tests/test_f048_t34b_supervivientes.py`, 46 passed; 71/71 mueren), **6 de
`GestoRevisor`** en bloque (los mata el test de F-047, comprobado en su worktree; el 45 no, y se cierra aquí) y los **3
equivalentes** ya aceptados (78-80). 0 sin justificar; sin tocar producción ni `evals/`: `progress/impl_F-048_T34b_supervivientes.md`.

## Runner de evals (fallos aislados) y comparador de obra dev/rama — resumen

Texto íntegro (decisiones, comando y entorno del comparador, RED y evidencias): [`progress/impl_F-048_evals.md`](impl_F-048_evals.md).
- **Runner** (`77b4bc2` · `3470648`): cada caso de sv2/sv5/sv6 en su `try`; el caso roto sale `OMITIDO` con
  motivo (`evals/procesos/errores.py` describe la FORMA del error, nunca el texto). RED: `ModuleNotFoundError:
  No module named 'evals.procesos.errores'` y `20 failed, 5 passed` → `31 passed`. Cobertura 99.7 % (872/875).
- **Comparador** (`a264c36` · `8b37675`): `evals/comparar_obra.py` + `evals/procesos/sv2_obra.py`, obra de IA1
  con el prompt de `dev` y el de la rama; la variante `dev` manda al LLM lo mismo que `dev`, byte a byte.
  RED: `ImportError: cannot import name 'comparar_obra'` → `32 passed`; test de `dev` `2 failed`/`1 failed` →
  `4 passed`. Raíz entonces `932 passed in 404.61s`; cobertura 98.7 % (1158/1173).
- **MANUAL (líder)**: relanzar T40; lanzar el comparador (se factura). Mutación de ambos: la decide el líder.

## Bloque E (T29–T31) · evals: el correo del caso y la inyección — 2026-09-24

**Commits**: `01c4b13` T30 · `10fd14b` T29 · `00b60ab` T31. Solo `evals/` y `tests/`; producción intacta. **Nada
contra LLM, Azurite ni Azure.** Texto íntegro: [`progress/impl_F-048_bloque_E.md`](impl_F-048_bloque_E.md).
- **T30**: traídos de F-047 SOLO `evals/inyeccion.py` y `tests/test_f047_r2_r16_inyeccion.py` (dependencias:
  estándar y `ruesma_comun`). `git diff feature/F-047-evals-ciclo-completo -- evals/inyeccion.py` vacío y
  `17 passed` **en el commit de T30**; tras T31 difiere a propósito. **No se trae** `test_f047_r5_seleccion_contrato.py`:
  importa `evals/lectura_bbdd.py`, la capa de lectura del ciclo (623 líneas, siete tests de F-047 detrás).
  `GestoRevisor` queda sin cubrir aquí hasta que llegue F-047.
- **T29**: `evals/correos.py`. `cargar_correo` lee `evals/inputs/correos/{caso}.json` (captura v1 o copia
  manual con `asunto`/`cuerpo`) con `construir_contexto_correo`; sin fichero `None`; mal formado
  `CapturaInvalida` con ruta y motivo, sin contenido y sin causa. R38: `versionados_con_correo` recorre
  `git ls-files` de `evals/` y `tests/` con la firma `asunto`+`cuerpo` (→ `[]`), y `git check-ignore` confirma la carpeta.
- **T31**: `inyectar(..., correo=)` → huella a `payload_json`, PDF → `guardar_contexto_correo` → mensaje con
  `correo_blob`; si el blob falla, `ErrorCorreo` (solo el tipo) y no se publica. `Inyector(sin_correo=True)`
  lo descarta. **Desviación**: sin el CLI del ciclo de F-047 en la rama, `--sin-correo` queda en
  `anadir_opcion_sin_correo(analizador)`; el cableado (`montaje.py`, `ciclo.py`) llega con F-047.
```
python -m pytest tests/test_f048_evals_correos.py -q --tb=line -p no:cacheprovider
E   ImportError: cannot import name 'correos' from 'evals' (...\evals\__init__.py)   1 error in 1.65s -> 33 passed in 3.44s
python -m pytest tests/test_f048_r40_r41_inyeccion.py -q --tb=line -p no:cacheprovider
E   TypeError: Inyector.__init__() got an unexpected keyword argument 'sin_correo'   (x12)
E   AttributeError: module 'evals.inyeccion' has no attribute 'anadir_opcion_sin_correo'
13 failed in 3.16s                                          -> 13 passed, 982 deselected (-k "f048 and inyeccion")
```

| Evidencia (bloque E) | Valor real |
|---|---|
| Tests | 63 del bloque (17 F-047 + 33 T29 + 13 T31); raíz `995 passed in 456.87s` en `bash harness/init.sh` (ENTORNO LISTO) |
| Cobertura de las líneas cambiadas | 97.0 % (1313/1354). `correos.py` 100 %; `inyeccion.py` 79 % (falta `GestoRevisor`, de F-047) |
| Mutación | campaña no relanzada; 9 mutantes a mano sobre `correos.py` e `inyeccion.py`, 9 muertos. Campaña nueva: la decide el líder |
| Tiempo de la suite | raíz 456.87 s; los tres ficheros del bloque, 12.07 s + 3.44 s + 7.90 s |

## Bloque E · cambios de la review — 2026-09-24

Review `progress/review_F-048_bloque_E.md` (CHANGES_REQUESTED). Bloqueante 4: líder (`6558755`). Bloqueante 3
(relanzar la mutación): la lanza el líder DESPUÉS de esto; no se lanzó aquí. Solo `evals/` y `tests/`.
- **CR-E1** (`fc91569`, `evals/procesos/errores.py`): la `loc` de pydantic pasa por `_ubicacion`: en
  `extra_forbidden` se quita la última parte; del resto pasan los enteros y los nombres `^[a-z_][a-z0-9_]*$`,
  lo demás sale `<clave>`. Residuo aceptado por la review: una clave de `dict` en minúsculas pasa tal cual.
- **CR-E2** (`a3c870a`, `modelos.py`, `runner.py`, `informe.py`): nuevo estado `ERROR`
  (`ResultadoCaso.con_error`); no cuenta como evaluado ni como omitido (`ResultadoFase.con_error`). Veredicto:
  ROJO si hay un ROJO; si no, NO_EVALUABLE si hay algún ERROR o ningún evaluado. El informe cuenta «con ERROR: N»
  por fase y la explicación lista «N casos con ERROR: fase caso, …». **Decisión**: también «sv2/sv5/sv6 no
  devolvió resultado» (hijo vivo que se salta el caso) es ERROR: es un fallo nuestro, no «no había con qué
  evaluar». `OMITIDO` queda solo para «no existe el fichero» y «sin caso en el libro». Aislamiento intacto.
- **CR-E3** (`e00bc41`, `evals/correos.py`): R38 cuenta todo `.eml`/`.msg` (sin distinguir mayúsculas) bajo
  `evals/` y `tests/`, y la firma admite `subject`+`uniqueBody`. Comprobado además en una copia (worktree en el
  scratchpad, `git add -f` de `tests/fixtures/copia.eml`, `evals/datos/copia.msg`, `evals/datos/graph.json`):
  `['evals/datos/copia.msg', 'evals/datos/graph.json', 'tests/fixtures/copia.eml']`. Worktree quitado.
- **CR-E4** (`1ec5853`): sin `sort_keys` en el test del schema de `dev` (`4 passed`). **CR-E5** (`fc3ee60`): el
  README avisa de que el stderr de un hijo muerto no va a `progress/`. Fuera: menores 4 y 5 de la review.

Fase RED (comandos exactos; salida real, recortada a las líneas `E`):
```
python -m pytest tests/test_f048_evals_fallos_aislados.py -q --tb=line -p no:cacheprovider -k "cr_e1 and (documento_real or dict)"
E   AssertionError: assert 'ValidationEr...BARAN-7731 SL' == 'ValidationEr...n en cabecera'
E   AssertionError: assert 'ValidationEr...-ALBARAN-7731' == 'ValidationEr... mapa.<clave>'
2 failed, 34 deselected in 6.86s          (-k cr_e1 entero: 4 failed, 1 passed)          -> 36 passed
python -m pytest tests/test_f048_evals_fallos_aislados.py -q --tb=line -p no:cacheprovider   (solo la constante ERROR)
E   assert 0 == 2          <- runner.main con un caso roto salía VERDE (código 0)
E   AttributeError: type object 'ResultadoCaso' has no attribute 'con_error'   (x6)
E   AssertionError: assert 'OMITIDO' == 'ERROR'   (x8, los tests viejos ya reescritos)
16 failed, 31 passed in 13.16s                                                     -> 48 passed
python -m pytest tests/test_f048_evals_correos.py -q --tb=line -p no:cacheprovider -k cr_e3
E   AssertionError: assert False is True   (x2, la firma de Graph)
E   AssertionError: assert [] == ['evals/datos...s/correo.eml']
3 failed, 3 passed, 33 deselected in 3.30s                                         -> 39 passed
```

| Evidencia (cambios de la review del bloque E) | Valor real |
|---|---|
| Tests | +23 (5 CR-E1, 12 CR-E2, 6 CR-E3); raíz `1018 passed in 514.76s` en `bash harness/init.sh` (ENTORNO LISTO, exit 0) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA`: 96.9 % (1350/1393) |
| Mutación | no lanzada (bloqueante 3: la relanza el líder sobre este HEAD) |
| Tiempo de la suite | raíz 514.76 s; los tres ficheros tocados, `91 passed in 11.58s` |
