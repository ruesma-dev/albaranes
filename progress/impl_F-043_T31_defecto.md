<!-- progress/impl_F-043_T31_defecto.md -->
# F-043 · T31 — la clasificación no llegaba al merge en el re-proceso

Defecto REAL medido el 2026-09-11 ejecutando T31 contra el pipeline local
con LLM de verdad. Albarán **SS-0003967**, `document_id`
`1dc06154-00ce-4c80-9de3-7a41cc0a08c3`, BBDD **local**. Rama
`feature/F-043-clasificacion-por-ia1`. Rigor `critico` → fase RED obligatoria.

## 1 · Diagnóstico

**La hipótesis de partida es FALSA.** No es
`albaran_confidence_service.py:235` (`clasificacion=openai.data.clasificacion`).
Evidencia, del envelope real que sv3 consumió
(`envelopes/1dc06154-..._phase_1.json`, bajado de Azurite):

```
=== CLAVES RAIZ: ['meta', 'data', 'debug']
data.clasificacion = {"familia": "residuos", "confianza_pct": 100.0,
  "motivo": "... LER 170604 ...", "mixto": false,
  "familias_secundarias": [], "origen": "ia2"}
```

El envelope final de sv2 es **plano**: `phase_merge.construir_envelope_final`
devuelve `{meta, data, debug}` y **nunca** cuelga sub-envelopes `gemini` /
`claude`. Por tanto `envelope.gemini is None`, `build_merge_analysis` entra
siempre por el caso 3 (`provider_origin = "openai_fallback"` — justo lo que
tiene la fila en BBDD) y el parámetro `openai` **ES** el envelope final. La
línea 235 lee la clasificación correcta sea cual sea la IA que extrajo: el
nombre del parámetro engaña, el comportamiento no.

**La causa real: la rama de DUPLICADO del pipeline.** Log de sv3 de la
corrida (`tasks/biaakf050.output`, línea 26):

```
10:55:14 | INFO | persist_albaran_pipeline.py:103 | Documento duplicado
  detectado. sha256=15219ac1... document_id=1dc06154-00ce-4c80-9de3-7a41cc0a08c3
```

El PDF ya estaba persistido (misma huella), así que
`PersistAlbaranPipeline.run()` cortó en `if existing is not None:` y ejecutó
solo los pasos de re-enriquecimiento (cabecera, obra `0687`, guarda de fecha,
contratos, trigger de valoración). **`repository.save()` no se llama en esa
rama** — y `save()` era la ÚNICA escritura de las seis columnas
(`campos_clasificacion_merge`, `sqlalchemy_albaran_repository.py:763`).

Confirmado en PostgreSQL local: la fila es de **2026-08-19**, un mes anterior
a la feature, con `prompt_key = 'albaran_revision_fase2_es'` (la corrida de
hoy usó `albaran_revision_fase2_residuos`). No se reescribió hoy.

```
  id = '1dc06154-00ce-4c80-9de3-7a41cc0a08c3'   numero_albaran = 'SS-0003967'
  provider_origin = 'openai_fallback'  prompt_key = 'albaran_revision_fase2_es'
  created_at_utc = '2026-08-19T09:42:48.060890+00:00'
  tipologia = None          tipologia_confianza_pct = None
  tipologia_origen = None   tipologia_mixta = None
  tipologia_motivo = None   tipologia_secundarias_json = None
```

**Alcance, más allá del caso**: afecta a TODO documento ya persistido —
cualquier re-publicación en `q-persistencia`, cualquier re-proceso, cualquier
adjunto repetido. Incluida, y esto es lo grave, la propia vía de revalidación
de T31. **Ningún test lo vio** porque los de
`test_f043_persistencia_clasificacion.py` atacan `build_merge_analysis` y
`campos_clasificacion_merge` por separado: nadie recorría
`PersistAlbaranPipeline.run()`, y la rama de duplicado no tenía ni un test en
toda la feature.

## 2 · Fase RED

Test nuevo: `…/tests/test_f043_t31_clasificacion_en_duplicado.py`. Comando y
salida REALES, antes de tocar producción:

```
$ .venv/Scripts/python.exe -m pytest \
    services/albaranes-persistencia/tests/test_f043_t31_clasificacion_en_duplicado.py -q
FFFFF...                                                                 [100%]
______ test_f043_r22_el_duplicado_persiste_la_clasificacion_del_envelope ______
        assert resultado.duplicate is True
>       assert len(repo.clasificaciones) == 1
E       assert 0 == 1
E        +  where 0 = len([])
...
_ test_f043_r22_el_duplicado_la_persiste_sea_cual_sea_el_proveedor[gemini-3.7-flash] _
>       assert [doc for doc, _ in repo.clasificaciones] == [_MERGE_ID]
E       AssertionError: assert [] == ['1dc06154-00...7a41cc0a08c3']
...
_______________ test_f043_r22_la_escribe_antes_de_disparar_la_valoracion _______________
>       assert orden.index("clasificacion") < orden.index("valoracion")
E       ValueError: 'clasificacion' is not in list

5 failed, 3 passed in 0.84s
```

Los 3 que ya pasaban en RED son los guardianes de que el arreglo no se pase de
frenada: R27 (sin clasificación no se escribe nada) y los dos de best-effort.
El test de proveedor está parametrizado sobre `gemini-3.7-flash`, `gpt-5.2` y
`claude-opus-4-…`: cubre el hueco que pedía el encargo —la clasificación llega
al merge venga de la IA que venga—.

**GREEN, mismo comando tras el arreglo:** `8 passed in 0.76s`. Y con los 3
tests añadidos después sobre la escritura del repositorio:
`11 passed in 2.54s`.

## 3 · El arreglo

Mínimo y general, dos ficheros de sv3:

1. `…/sqlalchemy_albaran_repository.py` — método nuevo
   `update_merge_clasificacion(document_id, clasificacion) -> bool`. Reutiliza
   `campos_clasificacion_merge` (misma traducción que `save`, sin duplicar
   recortes ni el JSON de secundarias). `clasificacion=None` es NO-OP y
   devuelve `False`: **R27 intacto**. Merge inexistente: WARNING y `False`.
2. `…/persist_albaran_pipeline.py` — la rama de duplicado llama a
   `_persist_clasificacion_safely(...)` con `envelope.data.clasificacion`,
   **lo primero**, antes de re-enriquecer y sobre todo antes de
   `_trigger_valuation_safely`: sv6 lee esas columnas para abrir sus puertas
   de familia, así que escribirlas después del trigger sería una carrera. Hay
   un test que fija ese orden.

Best-effort como el resto de pasos de la rama, pero con
`WARNING`/`logger.exception` explícitos: la consecuencia de saltárselo es que
sv5/sv6 valoren sin familia. Duck-typing defensivo (`getattr` + `callable`)
porque el puerto `AlbaranRepository` solo declara `initialize`,
`get_by_sha256` y `save`.

**Lo que NO se ha hecho, a propósito:** ninguna regla determinista (la familia
la sigue decidiendo la IA; aquí solo se deja de perder lo decidido); no se
fusiona la clasificación entre proveedores (se toma la del envelope final,
sellada por el resolver de sv2); y los motivos de revisión R28/R29
(`clasificacion_confianza_baja`, `clasificacion_mixta`) siguen calculándose
solo en `save()` — en la rama de duplicado no se recalculan: **fuera de
alcance**, anotado como deuda.

## 4 · Revalidación (sin gastar un euro de LLM)

No se re-extrajo nada. Se re-procesó el envelope YA guardado en Azurite
(`envelopes/1dc06154-..._phase_1.json` + `input/1dc06154-....pdf`) por el
camino real: `_sanear_envelope` + `SqlAlchemyAlbaranRepository` +
`PersistAlbaranPipeline.run()` con el código actual, contra el PostgreSQL
local. Sin trigger de valoración cableado, para no re-publicar en
`q-valoracion`. Traza real del re-proceso:

```
INFO | persist_albaran_pipeline | Documento duplicado detectado. sha256=15219ac1...
INFO | sqlalchemy_albaran_repository | [clasificacion][repo] doc=1dc06154-...
       tipologia=residuos confianza=100.0 origen=ia2 mixta=False
INFO | persist_albaran_pipeline | [clasificacion][pipeline] OK document_id=1dc06154-...
       familia=residuos confianza=100.0 origen=ia2
RESULTADO: PersistAlbaranResult(ok=True, document_id='1dc06154-...', duplicate=True, ...)
```

**Consulta a PostgreSQL local, resultado literal, después:**

```
  id = '1dc06154-00ce-4c80-9de3-7a41cc0a08c3'  numero_albaran = 'SS-0003967'
  tipologia = 'residuos'       tipologia_confianza_pct = 100.0
  tipologia_origen = 'ia2'     tipologia_mixta = False
  tipologia_secundarias_json = '[]'
  tipologia_motivo = 'Documento de identificación y control de traslado de
      residuos de construcción con código LER 170604 (materiales de
      aislamiento), entrega y retirada de contenedores por parte de gestor
      autorizado de residuos inertes.'
```

Las seis columnas rellenas, con los valores exactos que pedía el encargo.

### 4.1 · Lo que ve sv4 NO es una segunda vía: es esta escritura

Durante el trabajo llegó el dato de que la ficha de sv4
(`/documents/1dc06154-...`) pinta «Familia: Residuos… · Confianza: 100.0 % ·
Decidida por: ia2», con la hipótesis de que la clasificación viajaba por otro
sitio (el JSON del documento o el payload de fase 2). **No es así.**

`services/albaranes-front/infrastructure/database/orm_models.py:66-71` mapea
las seis columnas `tipologia_*` y dice literalmente «sv4 SOLO LAS LEE»;
`domain/models/review_models.py:737` construye la propiedad `clasificacion`
**solo** desde ellas y devuelve `None` si `tipologia` es NULL; y
`templates/document_detail.html:116` envuelve todo el bloque en
`{% if document.clasificacion %}`. No hay otra fuente.

Es decir: **si sv4 lo pinta, es porque las columnas ya están escritas** — por
este arreglo, en la revalidación de arriba. Re-consultado después:
`tipologia='residuos'`, `100.0`, `ia2`, `mixta=False`, `'[]'`, motivo con el
LER. La lectura previa a NULL era anterior a la revalidación.

Lo que sigue sin moverse es la valoración (540,00 € en 1 línea): esa fila es
de 2026-08-19 y sv6 no la rehace sin `force=true` — la mitad 2 de T31, §5.

## 5 · Estado de T31 y verificaciones MANUALES pendientes

T31 tiene dos mitades (`specs/F-043-.../tasks.md:56`):

- **Mitad 1 — la clasificación, que es lo que entrega F-043: VERDE.**
  `tipologia='residuos'`, `origen='ia2'`, `confianza=100.0` y motivo que cita
  el papel (LER 170604).
- **Mitad 2 — la valoración (`total_lines=2`, `review_required=true`,
  `total_valorado` 90,00 € ó 210,00 €): PENDIENTE, la hace el humano.** Hoy
  `albaran_valuations` sigue con la fila de 2026-08-19: `status='ok'`,
  `total_valorado=540.0` — las puertas de residuos no se habían abierto porque
  sv6 leía `tipologia` a NULL. Re-valorar exige `force=true`, y eso llama a
  sv5 (IA3): **se factura**, por eso no se ha lanzado aquí.

**Dos cosas para el humano, en este orden.** (1) **Reiniciar el worker de
sv3**: el proceso levantado tiene en memoria el código ANTERIOR al arreglo, y
sin relanzarlo la corrección no aplica al tráfico real de `q-persistencia`
(no se ha tocado nada del pipeline levantado). (2) **Cerrar la mitad 2**, ya
con las columnas puestas:

```powershell
curl.exe -X POST http://localhost:8003/v1/valuation/run -H "Content-Type: application/json" -d "{\"document_id\": \"1dc06154-00ce-4c80-9de3-7a41cc0a08c3\", \"force\": true}"
```

y leer `SELECT total_valorado, total_lines, review_required FROM
albaran_valuations WHERE document_id='1dc06154-00ce-4c80-9de3-7a41cc0a08c3';`

## 6 · Ficheros tocados

Los tres bajo `services/albaranes-persistencia/`:
`application/pipelines/persist_albaran_pipeline.py` (paso nuevo
`_persist_clasificacion_safely` + su llamada en la rama de duplicado),
`infrastructure/database/sqlalchemy_albaran_repository.py` (método nuevo
`update_merge_clasificacion`) y
`tests/test_f043_t31_clasificacion_en_duplicado.py` (**nuevo**, 11 tests).

Más `progress/inventario_mutacion_F-039.md`: la campaña nueva necesita su fila
con veredicto o `test_f039_r2_...` pone la suite en rojo (F-039 · R2).

Commits: `818850c` (RED), `ffeb2c3` (arreglo), `279655c` (tests del repo),
`a32851e` (informe + mutación), `d73967c` (inventario).

## 7 · Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados (raíz, `harness/init.sh`) | **556 passed**, 0 failed |
| Tests ejecutados (sv3) | **181 passed**, 0 failed (11 nuevos) |
| Tiempo de la suite | raíz **198,28 s**; sv3 **5,32 s** |
| Cobertura de líneas cambiadas | **89,8 %** (633/705, umbral 80 %, nivel `critico`) — línea `PUERTA COBERTURA` de `init.sh` |
| Mutación | 7 generados, **0 supervivientes** — §7.1 |
| `bash harness/init.sh` | **ENTORNO LISTO. Puedes trabajar.** |

Tamaño: 261 líneas. La `PUERTA TAMAÑO` de `init.sh` mide
`progress/impl_F-043.md` (el informe de la feature) y sale en verde; este es
un informe de defecto aparte. Por encima del tope de 220 de `rigor.json`: lo
que sobra son las trazas RED, los volcados de PostgreSQL y §4.1, que el
protocolo prohíbe resumir.

Avisos de `init.sh` que NO son de este trabajo y siguen igual que antes:
ruff (1140, deuda previa), `PUERTA RUTAS SENSIBLES [evals]` de F-043 (13 rutas,
pendiente `python -m evals.runner --con-llm --feature F-043`), F-036 `blocked`,
marcas `[ADAPTAR]` de F-034/F-035, sv1-email e infra sin tests.

### 7.1 · Campaña de mutación

Acotada al diff de este arreglo (`--base HEAD~3 --rama HEAD --workers 1`, en
serie porque el árbol tenía un fichero sin versionar ajeno a este trabajo).
Informe completo: `progress/mutacion_F-043_T31_defecto.md`.

```
F-043: 2 fichero(s), 114 línea(s) de producción
[base] services/albaranes-persistencia: en verde (5.3 s)
7 mutantes evaluados, 7 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto
```

**Mutantes generados 7 · supervivientes 0**: no hay ninguno que analizar. Los
7 son las decisiones del arreglo (`if clasificacion is None`,
`if not callable(escribir)`, `if not campos`, `if document is None` y los tres
`return True/False`), y cada uno lo caza al menos un test del fichero nuevo.

La campaña grande de la feature (`progress/mutacion_F-043.md`) NO se ha
re-lanzado: este trabajo no toca las líneas que cubría.
