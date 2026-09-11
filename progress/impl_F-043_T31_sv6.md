<!-- progress/impl_F-043_T31_sv6.md -->
# F-043 · T31 — el último eslabón: sv6 valoraba sin el contexto de la LÍNEA

Segundo defecto REAL de la misma tarde, medido el 2026-09-11 contra el
pipeline local con LLM de verdad. Albarán **SS-0003967**, `document_id`
`1dc06154-00ce-4c80-9de3-7a41cc0a08c3`, BBDD **local**, contrato CTSU24/0228.
Rama `feature/F-043-clasificacion-por-ia1`. Rigor `critico` → fase RED.

## 1 · Diagnóstico: la clasificación NO se pierde entre sv5 y sv6

Los tres candidatos del encargo quedan **descartados con evidencia**, no por
lectura de código:

**T20 · sv5 serializa la clasificación.** El sobre que sv6 guardó en
`albaran_valuations.raw_ia_envelope_json` (valuation_id
`0220e926-1919-4f9a-a055-69b6fa102de6`, el de la corrida de las 14:58) es el
volcado del **DTO ya parseado** (`envelope.model_dump_json()` en
`run_valuation_pipeline.py`). Leído de la BBDD local:

```
CLAVES context: ['lineas_albaran', 'lineas_contrato', 'clasificacion']
context.clasificacion = {"familia": "residuos", "confianza_pct": 100.0,
  "motivo": "... código LER 170604 ...", "mixto": false,
  "familias_secundarias": [], "origen": "ia2"}
meta.prompt_key = valuation_residuos
```

**T21 · `ValuationContextDto` la recibe.** Ese JSON *es* el DTO parseado: si el
default `None` se la hubiera comido, el volcado diría `null`. Dice residuos.

**T22 · las puertas se abrieron.** La fila real de `albaran_line_valuations`
trae entre sus motivos **`residuos_sin_volumen_m3`**, y esa razón solo la emite
`calcular_contenedores_residuos`, a la que únicamente se llega **dentro** de
`if _familia_de(ctx, self._clasificacion) == "residuos"`. Con la línea sin
`tipo_familia`, esa familia solo puede venir del DOCUMENTO. **La puerta de
familia estaba abierta.** Lo que F-043 entrega funciona de punta a punta.

```
merge_line_id 401 | cantidad_albaran 6.0 | cantidad_convertida 6.0 |
importe 720.0 | matched 26523 | review_reasons_json =
["ia_unit_category_mismatch","ia_match_trusted",
 "no_albaran_unit_assumed_same","residuos_sin_volumen_m3"]
```

### Lo que sí faltaba: `contexto_linea` de la línea, a NULL en el merge

```
albaran_lines_merge id=401 line_index=1 codigo='170604' cantidad=6.0
  contexto_linea_json = None      source_phase = 'phase_1'
```

Sin `volumen_m3` no hay contenedores que contar —la regla devuelve
`num_contenedores=None` y el builder cae a la cantidad cruda, 6 × 120 = **720**—
y sin `codigo_ler` la red de `_sinteticas_residuos_faltantes` no tiene qué
inyectar: **1 línea en vez de 2**. La propia IA3 lo dejó escrito en su
`razon_corta` de esa corrida: *«El incremento por LER 170604 (90/ud) lo inyecta
sv6 de forma determinista, no lo emito aquí»*. Y sv6 no pudo.

**El dato no es viejo por diseño: sv3 lo tiró hoy.** El envelope de la corrida
(`envelopes/1dc06154-..._phase_1.json`, bajado de Azurite) trae el contexto
ENTERO que IA2 emitió con el prompt de residuos:

```
"contexto_linea": {"tipo_familia": "residuos", "rol_linea": "base",
  "codigo_ler": "170604", "volumen_m3": 6.0, "peso_toneladas": 0.18, ...}
```

Causa: **la misma rama de DUPLICADO de `PersistAlbaranPipeline.run`** del
arreglo de esta mañana (`progress/impl_F-043_T31_defecto.md`). `repository.
save()` —dentro del cual `_build_lines` es la ÚNICA escritura de
`contexto_linea_json`— no corre cuando el PDF ya está persistido. Aquel arreglo
cubrió las seis columnas del DOCUMENTO; el contexto de las LÍNEAS seguía
perdiéndose, así que la fila 401 seguía siendo la del 2026-08-19.

O sea: la nota 4 del encargo acierta a medias. El dato del merge **sí** estaba
viejo, pero no por la rama 1 de `familia_efectiva` (la línea no tenía
`tipo_familia` distinto: no tenía contexto ninguno) ni porque el criterio esté
mal, sino porque el re-proceso no lo refresca. Es un defecto de código.

**Alcance, más allá del caso:** afecta a todo documento ya persistido que
vuelva a pasar por `q-persistencia`. Es exactamente la vía de revalidación de
T31, y también la del saneado del histórico mal valorado.

## 2 · Fase RED

Test nuevo en sv3: `tests/test_f043_t31_contexto_linea_en_duplicado.py`.
Comando y salida REALES, antes de tocar producción:

```
$ .venv/Scripts/python.exe -m pytest \
    services/albaranes-persistencia/tests/test_f043_t31_contexto_linea_en_duplicado.py -q
FFF...FFFF                                                               [100%]
_______ test_f043_t31_el_duplicado_persiste_el_contexto_de_las_lineas _______
        assert resultado.duplicate is True
>       assert len(repo.contextos) == 1
E       assert 0 == 1
E        +  where 0 = len([])
...
___ test_f043_t31_el_contexto_trae_los_tres_campos_que_usan_las_puertas ___
>       ctx = repo.contextos[0][1][0].contexto_linea
E       IndexError: list index out of range
...
___ test_f043_t31_update_merge_lineas_contexto_escribe_por_line_index ___
E       AttributeError: 'SqlAlchemyAlbaranRepository' object has no
        attribute 'update_merge_lineas_contexto'

7 failed, 3 passed in 3.40s
```

Los 3 que ya pasaban en RED son los guardianes de que el arreglo no se pase de
frenada: R27 (sin contexto no se escribe nada) y los dos de best-effort.

**GREEN, mismo comando tras el arreglo:** `10 passed in 1.79s`.

### El camino real sv5 → sobre → sv6 → puertas

El encargo pedía un test que recorriera la cadena, «que es justo lo que ningún
test recorría». Está en sv6:
`tests/test_f043_t31_cadena_merge_a_puertas.py` (6 tests, verdes), armado con
los **artefactos reales** de la corrida: el `data` literal de IA3, las 7 líneas
del contrato y la clasificación, cambiando UNA sola cosa —el
`contexto_linea_json` de la fila del merge— y midiendo el euro de salida:

- como estaba el 2026-09-11 (NULL) → **720,00 € en 1 línea**, y con
  `residuos_sin_volumen_m3` entre los motivos: reproduce el número medido y
  **prueba que la puerta de residuos estaba abierta**;
- con el contexto que IA2 sí había emitido → **210,00 € en 2 líneas**, 1
  contenedor a 120 + `INCREMENTO LER 170604` a 90 contra la 26528.

Ese fichero **no es la fase RED** y no se disfraza de ella: sv6 no tiene ningún
defecto que arreglar, el defecto es de sv3 y ahí está el RED. Es la medición que
ata el arreglo de sv3 al importe final.

**Por qué son dos ficheros y no uno:** sv3, sv5 y sv6 tienen los tres un paquete
de primer nivel `domain` (y `application`), así que **ningún proceso de pytest
puede importar dos de ellos a la vez** — es la misma colisión que ya documentó
T4 con `infrastructure/sigrid`. Los dos tests se tocan en el punto exacto donde
se tocan los servicios: el JSON de `albaran_lines_merge.contexto_linea_json`,
que sv3 escribe y sv5 valida contra el `ContextoLinea` de `ruesma_comun`. La
constante de los dos ficheros es **byte a byte la que producción escribió** en
la revalidación (§4).

## 3 · El arreglo

Mínimo y general, los mismos dos ficheros de sv3 que esta mañana:

1. `…/sqlalchemy_albaran_repository.py` — método nuevo
   `update_merge_lineas_contexto(document_id, lineas) -> int`. Reutiliza
   `_dump_contexto_linea`, el mismo serializador que `_build_lines` (sin
   duplicar la traducción). Tres reglas conservadoras, cada una con su test:
   - empareja **por posición** (línea *n* del sobre ↔ fila `line_index = n`,
     que es como las numera `_build_lines`) y **solo si los recuentos
     coinciden**; si no, no escribe nada y avisa por WARNING: meter el contexto
     de otra línea es peor que no meter ninguno;
   - un contexto `None` **nunca pisa** lo que ya hubiera escrito (R27: esto
     enriquece, no destruye);
   - **no toca ningún otro campo** de la línea — cantidad, concepto y precios
     son el dato del albarán y de la revisión humana. Verificado con grep que
     sv4 solo LEE `contexto_linea_json`.
2. `…/persist_albaran_pipeline.py` — `_persist_contexto_lineas_safely(...)` en
   la rama de duplicado, justo detrás de la clasificación y **antes del
   trigger** de valoración (hay un test que fija ese orden: escribirlo después
   es una carrera que sv6 pierde). Best-effort con `WARNING`/`logger.exception`
   y duck-typing, igual que su hermano.

**Lo que NO se ha hecho, a propósito:** ninguna regla determinista de familia
(ni por LER, ni por producto, texto o CIF); no se ha abierto ninguna puerta de
sv6 al `codigo_ler`; no se ha tocado `familia_efectiva` ni sus cuatro ramas; y
la rama de duplicado **sigue sin llamar a `save()`** — re-escribir las líneas
enteras borraría el trabajo del revisor y arrastraría en cascada
`albaran_line_valuations.merge_line_id`.

## 4 · Revalidación (sin gastar un euro de LLM)

No se re-extrajo ni se re-valoró nada con IA. Tres pasos, todos con el código
real contra el PostgreSQL **local**:

**(a) sv3** — re-proceso del envelope ya guardado en Azurite por
`PersistAlbaranPipeline.run()`, sin trigger cableado (no se republica en
`q-valoracion`). Traza real:

```
INFO | persist_albaran_pipeline | Documento duplicado detectado. sha256=15219ac1...
INFO | sqlalchemy_albaran_repository | [clasificacion][repo] doc=1dc06154-... residuos 100.0 ia2
INFO | sqlalchemy_albaran_repository | [contexto-linea][repo] doc=1dc06154-... líneas=1 actualizadas=1
INFO | persist_albaran_pipeline | [contexto-linea][pipeline] OK ... lineas_actualizadas=1
RESULTADO: PersistAlbaranResult(ok=True, duplicate=True, selected_contrato_codigo='CTSU24/0228')
```

PostgreSQL local, después:

```
albaran_lines_merge id=401 line_index=1 contexto_linea_json =
  {"tipo_familia": "residuos", "rol_linea": "base", "codigo_ler": "170604",
   "volumen_m3": 6.0, "peso_toneladas": 0.18}
albaran_documents_merge tipologia='residuos' confianza=100.0 origen='ia2'
```

**(b) sv5** — su repositorio real + el prefilter + `_albaran_line_to_dict`,
leyendo esa BBDD (cero llamadas a LLM). Lo que entrega ahora:

```
"contexto_linea": {"tipo_familia": "residuos", "rol_linea": "base",
  "codigo_ler": "170604", "volumen_m3": 6.0, "peso_toneladas": 0.18}
"clasificacion": {"familia": "residuos", ..., "origen": "ia2"}
```

**(c) sv6** — el `ValuationBuilder` REAL con sus cinco colaboradores, el
`data` **literal de IA3** de la corrida de hoy (match 26523, 120 €/contenedor) y
ese contexto recién leído:

```
TOTAL: 210.0   LINEAS: 2   REVIEW: True   ['at_least_one_line_requires_review']
 - from_albaran       merge=401 cant=1.0 precio=120.0 importe=120.0 contrato=26523
   motivos=[... 'residuos_contenedores=1 (m3=6 / contenedor=6 m3)']
 - synthetic_modifier INCREMENTO LER 170604 cant=1.0 precio=90.0 importe=90.0 contrato=26528
```

**210,00 € en 2 líneas**: el ground truth del administrativo (§8.1 de
`progress/revision_residuos_salmedina_20260819.md`), 120 del contenedor + 90 del
incremento por el LER. Con el match REAL de IA3 de hoy, no bajo hipótesis.

## 5 · Estado de T31 y lo que queda para el humano

- **La cadena de F-043 está VERDE de punta a punta**: IA1 clasifica → IA2
  confirma → sv3 persiste documento **y líneas** → sv5 lee y elige
  `valuation_residuos` → sv6 abre sus puertas y valora **210,00 € en 2 líneas**.
- **La fila de `albaran_valuations` sigue con los 720,00 € de las 14:58**: no se
  ha re-valorado porque `force=true` llama a sv5 → IA3 y **se factura**. El
  210,00 de arriba está medido con la salida de IA3 **ya pagada**, no simulado.
- **Hay que reiniciar el worker de sv3** (y solo ese): el proceso levantado
  tiene en memoria el código anterior a este arreglo. No se ha tocado nada del
  pipeline levantado.

Para cerrar T31 del todo, **el humano**, en este orden:

```powershell
# 1) reiniciar el worker de sv3 (ventana donde corre main_worker.py)
# 2) la valoracion definitiva — ESTA LLAMADA A IA3 SE FACTURA
curl.exe -X POST http://localhost:8003/v1/valuation/run -H "Content-Type: application/json" -d "{\"document_id\": \"1dc06154-00ce-4c80-9de3-7a41cc0a08c3\", \"force\": true}"
```

**Verde**: `total_valorado = 210.0`, `total_lines = 2`, `review_required = true`
(el criterio de `tasks.md` decía 90,00 € porque asumía que IA3 casaría el
INCREMENTO; hoy casó el CONTENEDOR y sale el 210,00 completo). IA3 no es
determinista: si en esa corrida casara otra línea de contrato, el número puede
volver a los 90,00 € a revisión — eso sería T30, no este arreglo.

## 6 · Ficheros tocados

Producción (2, ambos de sv3): `infrastructure/database/
sqlalchemy_albaran_repository.py`, `application/pipelines/
persist_albaran_pipeline.py`. Tests (2 nuevos): `services/
albaranes-persistencia/tests/test_f043_t31_contexto_linea_en_duplicado.py`,
`services/albaran-valoracion-persist/tests/test_f043_t31_cadena_merge_a_puertas.py`.
Commit: `07d1518`. Ningún `git push`.

## 7 · Observación que se reporta y NO se parchea

Cuando `calcular_contenedores_residuos` no puede contar (`num_contenedores=None`
y razón `residuos_sin_volumen_m3`), el builder **cae a la cantidad cruda del
albarán** y la valora igualmente: son los 720,00 € de hoy. El docstring del
módulo dice que ahí «NUNCA se inventa un número», y no lo inventa, pero el
importe sale como si los m³ fueran unidades. Va a revisión, así que no es
silencioso, pero es un número grande que puede pasar por bueno. Cambiarlo es una
decisión de negocio fuera del alcance de T31: **queda anotado, no tocado**.

## 8 · Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (sv3) | **191 passed** en 3,59 s (suite completa del servicio) |
| Tests ejecutados (sv6) | **230 passed** en 2,82 s (suite completa del servicio) |
| Tests nuevos | **16** (10 en sv3 + 6 en sv6) |
| Fase RED | **7 failed, 3 passed** antes del arreglo → **10 passed** después |
| Cobertura de líneas cambiadas | ver §8.1 (línea `PUERTA COBERTURA` de `init.sh`) |
| Mutación | ver §8.1 |
| `bash harness/init.sh` | ver §8.1 |

### 8.1 · Pendiente de rellenar al cerrar

Los tres huecos de arriba se rellenan con la salida de `bash harness/init.sh` y
con `python -m harness.mutacion --ficheros …` acotado a los dos módulos tocados.
