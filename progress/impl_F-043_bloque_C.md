<!-- progress/impl_F-043_bloque_C.md -->
# F-043 · BLOQUE C (T13-T17) — informe del implementer

Rama `feature/F-043-clasificacion-por-ia1`. Rigor `critico`. Cinco tareas,
cinco commits + uno de refuerzo. Sin `git push`. **Solo sv3.**

`db205a2` T13 · `bf59902` T14 · `0ea80ff` T15 · `d745533` T16 · `794d35d` T17
· `6dd6844` refuerzo (§5).

## 1 · Qué cambió

**Creado** — `…-persistencia/tests/test_f043_persistencia_clasificacion.py`
(704 líneas, **38 tests**). Único fichero nuevo; lo demás son cambios.

**Modificado** (todos bajo `services/albaranes-persistencia/`)

- `phase2_ddl.py` — las seis columnas y el índice (§3). El espejo en
  `schema_contribution.py` sale **solo** (`_phase2_alters()` reusa la lista
  canónica `_PHASE2_DDL`); ahí solo se actualizó un docstring.
- `orm_models.py` — las seis columnas en `AlbaranDocumentMergeOrm`, **no** en
  `_DocumentColumnsMixin`.
- `sqlalchemy_albaran_repository.py` — `campos_clasificacion_merge()`, el
  parámetro `campos_clasificacion` de `_build_document_orm` y su cableado en
  `save()`; el constructor acepta el umbral.
- `application/services/albaran_confidence_service.py` — **el arreglo que no
  estaba en la lista** (§2.1), los tres motivos con su umbral y
  `_motivos_de_linea_sin_familia` (R19).
- `config/settings.py` — `CLASIFICACION_CONFIANZA_MINIMA_PCT`, defecto 60, y
  los **dos** puntos de composición (`api/app.py`, `composition.py`) que lo
  inyectan.

**NO se tocó, a propósito**: `ExtractionMeta` (la clasificación ya no viaja
por `meta`), `contexto_linea_merger`, `familia_detector`, `contrato_selector`,
y sv2, sv4, sv5 y sv6 enteros. **Ningún fallo encontrado en el catálogo ni en
lo que emite sv2.**

## 2 · Decisiones de diseño (y por qué)

### 2.1 · Había un SEGUNDO hueco, y no estaba en `tasks.md`

`_sanear_envelope` no era el único sitio donde se perdía el dato.
`AlbaranConfidenceService.build_merge_analysis` **rehace `data` campo a campo**
y construía el documento del merge SIN la clasificación: sobrevivía al saneado
y moría dos pasos después, con las seis columnas a NULL. El primer test de T15
lo enseña en rojo. Se copia la del envelope final (`openai.data.clasificacion`)
y **no se fusiona entre proveedores**: eso sería volver a DECIDIR la familia.

### 2.2 · Las otras seis decisiones

1. **Las columnas cuelgan del merge, no del mixin** que comparte con
   `albaran_documents`: auditoría forense por proveedor, y la clasificación es
   UNA por documento. Con test de que no se cuela en la raw.
2. **Sin clasificación, columnas a NULL** (`campos_clasificacion_merge(None)`
   → `{}`). Descartado escribir `generico`/0/`ausente` para un documento
   anterior a la feature: sv5 leería una clasificación donde no la hay y esos
   documentos **dejarían de comportarse como hoy** (R27). Quien sella
   `origen='ausente'` es el resolver de sv2, que sí sabe que pasó por él.
3. **El hueco se nombra UNA vez.** Con `origen='ausente'` la confianza es 0 y
   el umbral dispararía también `clasificacion_confianza_baja`: se emite solo
   `clasificacion_ausente`, porque la confianza 0 es CONSECUENCIA del hueco y
   dos motivos para una causa entrenan al revisor a no leerlos.
4. **El motivo por línea lleva índice** (`…_mixto:3`, el de la línea en el
   merge, el orden que enseña sv4), como los seis motivos por línea que este
   servicio ya emite. Sin índice, hay que buscar cuál de las quince.
5. **El umbral vive en un solo sitio**: la constante está en el servicio que la
   aplica y `config/settings.py` la importa, con un test que compara los dos
   valores (F-023: el mismo número en cuatro sitios es la trampa que la feature
   cierra). Sin ciclo: nada de `application`/`domain` importa `config`.
6. **Recorte defensivo** a `VARCHAR(32)`/`VARCHAR(16)`: un valor más largo
   tumbaría el INSERT del albarán entero por un campo informativo, como ya
   previene `update_merge_resolved_header` con su `VARCHAR(24)`.

**Lo que NO se hizo, a propósito**: ni una regla que infiera o corrija la
familia por LER, producto, texto o CIF. sv3 persiste y marca; no reclasifica.
Quién hereda lo decide `familia_efectiva` del catálogo (R20), con un test que
lo fija por inspección y comprueba que ahí dentro no se mira nada del papel.

## 3 · El DDL exacto, y por qué es idempotente

```sql
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia VARCHAR(32);
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_confianza_pct DOUBLE PRECISION;
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_motivo TEXT;
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_origen VARCHAR(16);
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_mixta BOOLEAN;
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_secundarias_json TEXT;
CREATE INDEX IF NOT EXISTS ix_albaran_documents_merge_tipologia ON albaran_documents_merge(tipologia);
```

`apply_phase2_ddl` se ejecuta en **cada arranque** de sv3 sobre bases que ya
existen. Es idempotente porque las siete sentencias llevan `IF NOT EXISTS`,
todas las columnas admiten NULL (nada de `NOT NULL` sobre filas ya escritas) y
no hay un solo `DROP`, `RENAME`, `DELETE` ni `UPDATE`. Un test lo comprueba
sentencia a sentencia en vez de fiarse de la lectura.

**No se ejecutó contra ninguna base**: regla dura del repo (contra Azure, solo
lectura) y R33. Se prueba sobre el texto de `_PHASE2_DDL`, su espejo en
`get_ddl_statements()` y el ORM —no había test de DDL previo en sv3—. El índice
del ORM lleva **el mismo nombre** que el del DDL (`index=True` sobre `tipologia`
genera `ix_albaran_documents_merge_tipologia`): si divergieran, la base acabaría
con dos índices sobre la misma columna. `Float` compila a `FLOAT` y el ALTER
dice `DOUBLE PRECISION`: en PostgreSQL son lo mismo, como en
`confidence_pct_calc`.

## 4 · Fase RED → GREEN, tarea a tarea

### T13 · la clasificación sobrevive al saneado (R9)

El código ya existía (bloque A): la RED se **provocó** retirando el campo
`clasificacion` de `DocumentoAlbaran` de sv3.

```
$ (sv3) python -m pytest tests/test_f043_persistencia_clasificacion.py -k sanear -q
E       pydantic_core._pydantic_core.ValidationError: 1 validation error for ExtractionEnvelope
E       data.clasificacion
E         Extra inputs are not permitted [type=extra_forbidden, input_value={'familia': 'residuos', ...}]
E       AttributeError: 'DocumentoAlbaran' object has no attribute 'clasificacion'
FAILED ...::test_f043_r9_sanear_y_validar_deja_viva_la_clasificacion
FAILED ...::test_f043_r27_sanear_un_envelope_anterior_sigue_validando_sin_ella
2 failed, 3 passed in 3.53s
```
Mismo `extra_forbidden` que mataba a `meta.tipologia`: lo que salva el dato es
que `data` lo declare. Campo restaurado (`git diff` vacío), verde: `5 passed`.

### T14 · el DDL (R22)

```
$ (sv3) python -m pytest tests -k ddl -q
E           AssertionError: falta el ALTER de tipologia
E       AssertionError: assert 'CREATE INDEX IF NOT EXISTS ix_albaran_documents_merge_tipologia ...' in (...)
E       assert 0 == 7
E           AssertionError: el ORM no declara tipologia
E       AssertionError: assert 'ix_albaran_documents_merge_tipologia' in {'ix_..._provider_origin', ...}
5 failed, 3 passed, 136 deselected in 3.24s
```
Los 3 que pasaban lo hacían en vacío (filtro sobre una lista sin `tipologia`).
Verde: `8 passed`.

### T15 · la persistencia (R22)

```
$ (sv3) python -m pytest tests/test_f043_persistencia_clasificacion.py -k persiste -q
E       AssertionError: assert None is not None
E        +  where None = DocumentoAlbaran(cabecera=..., clasificacion=None).clasificacion
E       ImportError: cannot import name 'campos_clasificacion_merge' from
                     'infrastructure.database.sqlalchemy_albaran_repository'   (×5)
6 failed, 14 passed in 2.84s
```
El primero es el hueco de §2.1. Verde: `20 passed` (`-k persiste` coge el
fichero entero: «persistencia» empieza por «persiste»).

### T16 · umbral y motivos (R11, R28, R29)

```
$ (sv3) python -m pytest tests -k motivos -q
E       AssertionError: assert 'clasificacion_confianza_baja' in ['single_provider_openai',
        'document_confidence_below_threshold', 'header_missing:fecha', ...]
E       TypeError: AlbaranConfidenceService() takes no arguments
E       ImportError: cannot import name 'UMBRAL_CLASIFICACION_CONFIANZA_POR_DEFECTO'
E       AssertionError: assert 'clasificacion_mixta' in [...]
E       AssertionError: assert 'clasificacion_ausente' in [...]   (×2)
7 failed, 9 passed, 146 deselected in 2.58s
```
Los 9 que pasaban son los del caso contrario (clasificación sólida, ningún
motivo), que tenían que pasar antes y después. Verde: `16 passed`.

### T17 · la línea que no hereda (R19)

```
$ (sv3) python -m pytest tests -k "mixto or r20_el_criterio" -q
E       AssertionError: assert 'linea_sin_familia_en_albaran_mixto:1' in
        ['single_provider_openai', ..., 'clasificacion_mixta']
E       AssertionError: assert [] == ['linea_sin_f...aran_mixto:3']
E       AttributeError: module 'application.services.albaran_confidence_service'
                        has no attribute '_motivos_de_linea_sin_familia'
3 failed, 3 passed, 162 deselected in 2.91s
```
Verde: `6 passed`. (`-k mixto` no coge el test de R20: de ahí el segundo
filtro, para no dejarlo fuera de la traza.)

## 5 · El commit de refuerzo (`6dd6844`)

`generar_mutantes` (generación, sin campaña: mutar el árbol es **T28**) dio
**17 mutantes**. Revisados uno a uno, **tres habrían sobrevivido**:

- **ORM `String(32)`→`String(33)` y `String(16)`→`String(17)`.** El ORM crea la
  tabla en una base nueva y el ALTER la parchea en una que ya existe: con
  longitudes distintas, el sistema acaba con **dos schemas según por dónde
  entró**. El test del ORM compara ahora la longitud contra la del DDL.
- **`ensure_ascii=False`→`True`.** Las familias del catálogo son ASCII, pero
  sv3 **no** normaliza `familias_secundarias` contra el catálogo: puede llegar
  texto con tilde y acabar en la columna como `\uXXXX`, que es lo que vería el
  revisor en sv4. Test con una tilde.

Tras el refuerzo se **inyectaron los 17 uno a uno**: **17 MUERTOS, ninguno
vivo**, árbol restaurado. No es «se revisaron»: cada mutación se escribió, se
lanzó la suite entera y se revirtió (1 a 8 tests caídos por mutante).

## 6 · Fuera de alcance, avisos y MANUAL

- **T18-T27 no se tocaron.** sv5 sigue sin leer las columnas nuevas (T18) y
  sv4 sin pintarlas (T24): hasta entonces el dato se persiste y no lo ve nadie.
  `docs/ARCHITECTURE.md` es **T26**.
- **Verificaciones de `tasks.md`**: las de T13-T17 apuntan a una sola suite, no
  hizo falta partirlas; se lanzaron desde el directorio de sv3, como `init.sh`.
  El defecto previo (sv2 y sv3 comparten el paquete `infrastructure/sigrid` y
  en un proceso uno tapa al otro) sigue ahí, ajeno a F-043.
- **`ruff` +9** (1118 → 1127): **7 `ISC004`** por las siete sentencias DDL y
  **2 `UP006`** (`Dict` en vez de `dict`). Las dos reglas ya las incumplen esos
  mismos ficheros (10 `ISC004` en `phase2_ddl.py`, 10 `UP006` en el
  repositorio) y escribir mis líneas con otro estilo las dejaría cantando en
  medio del fichero; cerrarlo es podar el fichero entero, fuera de alcance.
  **Cero avisos nuevos** en el fichero de tests y en los otros seis tocados
  (medido fichero a fichero contra `a5e831c`).
- **MANUAL de este bloque: ninguna** (sin red, sin BBDD, sin LLM). Las de la
  feature siguen siendo T30, T31 y T32.
- **Lo que este bloque NO demuestra**: que las columnas queden bien escritas
  en PostgreSQL de verdad — eso es **T31**. Aquí se comprueba lo comprobable
  sin BBDD: que el objeto ORM sale con los seis valores, que el DDL los
  declara y que ORM y DDL dicen lo mismo.

## 7 · Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests nuevos de F-043 en el bloque | **38**, todos en verde (5 T13 · 8 T14 · 7 T15 · 11 T16 · 6 T17 · 1 del refuerzo). Ningún test viejo retirado ni relajado |
| Suites (una a una, nada en paralelo) | raíz **556 passed** (436,2 s) · sv2 **139** (7,7 s) · sv3 **169** (14,1 s) · sv4 **131** (7,9 s) · sv5 **18** (1,6 s) · sv6 **185** (6,7 s) · comun **118 passed, 3 skipped** (146,0 s). **Cero fallos, cero skips nuevos** |
| Cobertura de líneas cambiadas | **98,6 %** (500/507, umbral 80 %, nivel `critico`). Las que faltan están **fuera de este bloque** —`ler.py:98`, `review_repository.py:1134-1135,3244`, `contexto_linea_merger.py:92`, de F-036 y del bloque A—: de los ocho ficheros de producción de este bloque, **ninguna línea cambiada queda sin cubrir** |
| Mutantes generados en el alcance | **17** (9 `albaran_confidence_service` · 5 repositorio · 3 ORM; **0** en `phase2_ddl.py`, `schema_contribution.py`, `settings.py`, `app.py` y `composition.py`, que son datos y cableado) |
| Mutantes ejecutados / supervivientes | **17 ejecutados uno a uno, 0 supervivientes.** No es la campaña —esa es T28, del humano, y muta el árbol— sino la inyección manual de cada mutante generado, con la suite completa de sv3 cada vez |
| Tiempo de la suite | el de cada suite, fila 2; el fichero nuevo solo: **4,6 s** |
| `ruff` en los ficheros nuevos | **0** en el fichero de tests; +9 en dos ficheros preexistentes, explicado en §6 |

## 8 · `bash harness/init.sh` — resultado real

**Verde**: `ENTORNO LISTO. Puedes trabajar.` — raíz **556 passed in 436.16s**,
sv3 **169 passed** (sin caché: el árbol cambió), las otras cinco suites en
verde, `PUERTA COBERTURA [OK] 98.6%` (500/507, umbral 80 %, nivel `critico`),
`PUERTA TAMAÑO [OK]`, rama correcta y árbol limpio tras los seis commits.

Avisos, **todos previos y ninguno bloqueante**: F-036 en `blocked`; `ruff`
1127 (§6); sv1-email e `infra` sin tests; marcas `[ADAPTAR]` en las specs de
F-034/F-035; y `PUERTA RUTAS SENSIBLES` en aviso con las **mismas 8 rutas**
que dejó el bloque B —**este bloque no tocó ninguna ruta sensible**—, cuya
evidencia es T30 y la autoriza el humano.

---

*Tamaño*: **245** líneas frente al tope de 220. La puerta mide
`progress/impl_F-043.md` (nombre exacto), no los informes por bloque, y sale
`[OK]`; el bloque A quedó en 221 y el B en 261 por lo mismo. Lo que no se
recortó, por norma del rol: las trazas de la fase RED, la sección «Evidencias»
y el resultado real de `init.sh` —que ya suman 145 líneas—. Lo que sí, en tres
pasadas: los listados `FAILED` largos y la prosa de las decisiones, que están
enteros en sus commits.
