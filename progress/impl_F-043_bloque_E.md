<!-- progress/impl_F-043_bloque_E.md -->
# F-043 · BLOQUE E (T24-T27, T29, T33) — informe del implementer

Rama `feature/F-043-clasificacion-por-ia1`. Rigor `critico`. Seis tareas,
seis commits + uno de refuerzo. Sin `git push`. **Solo sv4, arnés y docs.**
`f989563` T24 · `277fc16` T25 · `5cee3fb` T26 · `0d490f1` T27 ·
`4d1b24f` refuerzo (§5) · `f3fd682` T29 · T33 con este informe.

> **Es el último bloque de implementación.** Lo que queda de F-043 es del
> humano: T28 (campaña de mutación completa), T30 (evals con LLM real, que se
> factura) y las dos verificaciones manuales T31 y T32. Detalle en §8.

## 1 · Qué cambió

**Creado** — `services/albaranes-front/tests/test_f043_vista_clasificacion.py`
(**26 tests**). Único fichero nuevo. **Modificado · sv4**:

- `infrastructure/database/orm_models.py` — las seis columnas de sv3 en
  `AlbaranDocumentMergeOrm`, **solo lectura** (§2.1).
- `domain/models/review_models.py` — los seis campos en
  `DocumentDetailPayload` con el **nombre exacto** de las columnas, y tres
  propiedades calculadas: `clasificacion` (inverso de
  `campos_clasificacion_merge` de sv3), `clasificacion_nombre` (del catálogo)
  y `clasificacion_en_duda`; más `MOTIVOS_CLASIFICACION_EN_DUDA`.
- `…/review_repository.py` — las seis columnas de la fila del merge al
  payload en `_build_merge_detail`.
- `templates/document_detail.html` — el bloque «Clasificación del albarán»
  encima del de «Motivos de revisión» de F-036 R23; `static/styles.css`,
  `.clasificacion-motivo`; `tests/conftest.py`, la factoría
  `documento_detalle` acepta las seis columnas.

**Modificado · arnés y documentación** — `harness/rutas_sensibles.json`
(+2 rutas) y `tests/test_f011_r19_r20_declaracion.py` (§2.3);
`docs/ARCHITECTURE.md`, regla **14** de «Semántica de dominio»;
`docs/referencia/dominio_negocio_albaranes.md`, nota al frente del §9;
`specs/…/tasks.md`, T4 (encargo de la review del bloque A) y T27 (§2.4),
además de las marcas `[x]`.

**NO se tocó, a propósito**: sv2, sv3, sv5, sv6 y el catálogo de
`ruesma_comun`, enteros. **Ningún fallo encontrado en ellos.**

## 2 · Decisiones de diseño (y por qué)

### 2.1 · sv4 declara las columnas, pero NO las crea

`_review_schema_statements` lleva ALTER defensivos para las columnas que sv4
**escribe** (`approved`, el soft-delete). Las seis de clasificación las
escribe sv3, dueño del schema, y sv4 solo las lee: mismo trato que
`confidence_pct_calc` o `review_reasons_json`. Con un ALTER propio y sus
propias longitudes, una base creada por sv3 y otra parcheada por sv4 tendrían
**schemas distintos según por dónde entró el sistema** — el riesgo que el
bloque C cazó dentro de sv3. Hay test de que `tipologia` no aparece en el DDL
de sv4; lo que sí se fija es que las **longitudes** coincidan (§5).

### 2.2 · Las otras cinco decisiones

1. **sv4 PINTA, no decide.** Ni una regla que infiera, corrija o complete la
   familia por LER, producto, texto o CIF (R12, R13). El front es el sitio
   más tentador para «arreglarlo» con un `if` —tiene delante todo el papel—:
   hay test de inspección del módulo que cae si alguien lo intenta.
2. **El umbral NO se recalcula aquí.** `clasificacion_en_duda` sale de los
   motivos que **ya selló sv3**, no de comparar la confianza contra 60: con
   una copia del número, el día que se cambie el de sv3 la ficha diría una
   cosa y la BBDD otra (F-023). Test de lo contraintuitivo: confianza 5 % sin
   motivo de sv3 ⇒ sv4 **no** marca duda.
3. **El nombre legible sale del catálogo** (`obtener`), no de una lista
   propia (R2). Y una familia fuera del catálogo se enseña **tal cual**: sv2
   ya normaliza lo que la IA se invente (R10) y taparla aquí sería decidir.
4. **Dos recortes defensivos**, con el criterio con que sv3 recorta a
   `VARCHAR(32)`: JSON corrupto en las secundarias ⇒ lista vacía, y la
   confianza se acota a 0..100 porque `ClasificacionAlbaran` valida
   `ge=0, le=100`: sin acotar, un `150.0` en la columna haría saltar Pydantic
   al montar el payload y el revisor **no podría ni abrir la ficha**.
5. **La vista cruda de un proveedor no trae clasificación**: es trazabilidad
   de la extracción, igual que no trae motivos ni confianza calculada.

### 2.3 · El guarda de F-011 y por qué se toca su test

`tests/test_f011_r19_r20_declaracion.py` fija el CONJUNTO de rutas
declaradas: añadir dos lo pone en rojo, que es su trabajo. No se mete nada en
`RUTAS_DE_LA_SPEC` —eso es lo que aprobó F-011 y sigue leyéndose tal cual—:
las nuevas van en `RUTAS_ANADIDAS_DESPUES`, con quién las añadió y por qué.
La autoridad es **R34**, que nombra «el catálogo nuevo».

### 2.4 · Un falso verde en la verificación de T27

`tasks.md` mandaba `python -m harness.cobertura --feature F-043`. Ese módulo
**no tiene** `--feature` (deduce la feature de la rama) y el comando **no da
error**: argparse lo abrevia a `--features`, busca el catálogo de features en
un fichero llamado `F-043`, no lo encuentra y la puerta imprime `N/A (la rama
… no corresponde a ninguna feature declarada)` **con exit code 0**: parecía
pasar sin medir nada. Corregido al comando que lanza `init.sh`; el de T29 sí
funciona.

## 3 · Fase RED → GREEN, tarea a tarea

### T24 · sv4 enseña la clasificación (R30)

```
$ (sv4) python -m pytest tests/test_f043_vista_clasificacion.py -q
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'clasificacion_en_duda'   (×6)
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'clasificacion'           (×5)
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'clasificacion_nombre'    (×2)
E       AssertionError: el payload no expone tipologia
E       AssertionError: el ORM de sv4 no declara tipologia
E   TypeError: 'tipologia' is an invalid keyword argument for AlbaranDocumentMergeOrm
E   assert 'Clasificación' in '<!-- templates/document_detail.html --> …'
E   assert 'clasificacion-duda' in '…'   ·   E   assert '&lt;script&gt;' in '…'
21 failed, 4 passed in 3.62s
```
Los 4 que pasaban son los de **prohibición**, que tenían que pasar antes y
después: que sv4 no infiera la familia (R13), que no escriba DDL de las
columnas de sv3, que sin clasificación no se pinte bloque y que los motivos
nuevos usen el de F-036. Verde: `25 passed` (26 tras §5).

### T25 · el catálogo es ruta sensible (R34)

```
$ python -m pytest tests/test_f011_r19_r20_declaracion.py -q
E   AssertionError: faltan: ['services/albaranes-comun/ruesma_comun/contratos/clasificacion.py',
                             'services/albaranes-comun/ruesma_comun/contratos/familias.py'] · sobran: []
E   AssertionError: assert 14 == 16
2 failed, 14 passed in 25.73s
```
RED con la expectativa escrita y la declaración **sin tocar** (se revirtió a
propósito para provocarla). Tras declararlas: `72 passed` en los cuatro
ficheros que leen `rutas_sensibles.json`, y la puerta pasa de **11 a 13**
rutas tocadas, con las dos nuevas listadas.

### T26 · documentación

Sin test (verificación: revisión del reviewer). Lo verificable de su encargo
adicional sí se midió: el comando de T4 tal cual estaba **muere al RECOGER**
—`ModuleNotFoundError: No module named 'interface_adapters.worker.extraction_worker'`,
`2 errors during collection`, `241 deselected`—, y partido en dos da
`7 passed` (sv2) y `6 passed` (sv3).

### T27 · cobertura (R32)

La primera medición honesta —tras regenerar el `coverage.json` de sv4, que
era anterior al bloque— destapó **una línea descubierta de este bloque**: el
`return None` de `clasificacion_nombre` sin clasificación. Se cubrió con
test, no relajando nada: 98,7 % → **98,8 %**. T29 y T33, en §6 y §7.

## 4 · Qué ve el revisor (R30, y lo que T32 confirmará)

Encima del bloque «Motivos de revisión» de F-036 R23:

> **Clasificación del albarán** · Familia: **Residuos / gestion de RCD**
> (`residuos`) · Confianza: **82.0 %** · Decidida por: `ia1`
> *Motivo de la IA:* Gestor autorizado de residuos en el membrete, códigos
> LER 170504 y 170604 en las líneas y retirada de contenedor de 6 m³.

En azul (`alert info`) con la clasificación sólida y en **ámbar** (`alert
warning clasificacion-duda`) cuando sv3 selló uno de sus tres motivos; un
albarán `mixto` añade «**Albarán mixto** (también: `hormigon`)». El motivo lo
escribe un LLM y entra **escapado**: hay test de que un `<script>` ahí no
inyecta nada.

## 5 · El commit de refuerzo (`4d1b24f`)

`generar_mutantes` sobre las líneas de producción **del bloque E** (no la
campaña: mutar el árbol es T28) dio **8 mutantes**. Inyectados uno a uno, con
la suite entera de sv4 cada vez y el árbol restaurado después: **6 muertos y
2 VIVOS**, los dos de longitud de columna del ORM (`String(32)→33`,
`String(16)→17`), con `156 passed` los dos. Es el mismo par que sobrevivió en
sv3 (bloque C) pero **por otro motivo**: allí el ORM crea la tabla y la
divergencia parte el schema; aquí sv4 nunca la crea, así que el efecto no es
un fallo en ejecución sino **documentación que miente** a quien lea este ORM
para saber cómo es la columna. No son equivalentes: se matan con test contra
los valores del DDL de sv3. Los 8 reinyectados tras el refuerzo: **8 MUERTOS,
0 vivos**, árbol limpio.

## 6 · Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests nuevos del bloque | **26**, todos en verde (25 de T24 + 1 del refuerzo). sv4 pasa de **131** a **157**. Ningún test viejo retirado ni relajado; los dos de F-011 se ajustaron sin aflojar (§2.3) |
| Suites (una a una, nada en paralelo) | raíz **556 passed** (161,2 s) · sv4 **157 passed** (11,2 s) · sv2, sv3, sv5, sv6 y comun **en verde por caché** (árbol sin cambios desde su último verde: este bloque no los tocó). **Cero fallos, cero skips nuevos** |
| Cobertura de líneas cambiadas | **98,8 %** — 595/602 (umbral 80 %, nivel `critico`). Las 7 que faltan son **ajenas al bloque E**: `ler.py:98`, `review_repository.py:1134-1135` y `:3257`, `contexto_linea_merger.py:92` (F-036) y el cableado del umbral en `app.py:94` y `composition.py:62` de sv3 (bloque C). De los tres ficheros de producción Python tocados aquí, **ninguna línea cambiada queda sin cubrir** |
| Mutantes generados en el alcance | **8** (6 en `review_models.py`, 2 en `orm_models.py`; **0** en `review_repository.py`, que aquí solo cablea campos) |
| Mutantes ejecutados / supervivientes | **8 ejecutados uno a uno, 0 supervivientes** tras el refuerzo (6/8 antes). No es la campaña —esa es T28, del humano— sino la inyección manual de cada mutante generado, con la suite completa de sv4 cada vez |
| Tiempo de la suite | fila 2; el fichero nuevo solo: **1,6 s** |
| `ruff` | **0 avisos nuevos**. Medido fichero a fichero contra `420618e`: `review_models.py` 2→2, `orm_models.py` 3→3, `review_repository.py` 35→35, `conftest.py` 0→0, y **0** en el fichero de tests nuevo. El total del repositorio (1138) sube por el bloque D, no por éste |
| Puerta de tamaño | `[OK]` — requirements 150/150, design 250/250 |

## 7 · `bash harness/init.sh` — resultado real

**Verde**: `ENTORNO LISTO. Puedes trabajar.` — raíz **556 passed in 161.19s**,
sv4 **157 passed** (sin caché: el árbol cambió), las otras cinco suites en
verde, `PUERTA COBERTURA [OK] 98.8%` (595/602, umbral 80 %, nivel `critico`),
`PUERTA TAMAÑO [OK]`, rama correcta y árbol limpio tras los commits. Avisos,
**todos previos y ninguno bloqueante**: F-036 en `blocked`; `ruff`
1138; sv1-email e `infra` sin tests; marcas `[ADAPTAR]` en F-034/F-035; y
`PUERTA RUTAS SENSIBLES` en aviso, ahora con **13** rutas (las 11 de los
bloques B-D más las 2 que este declara). Que suba es el efecto buscado de
T25: la evidencia de todas ellas es **T30**.

## 8 · Fuera de alcance y lo que queda (todo del humano)

- **T28 · campaña de mutación completa**, sin tope y con 0 supervivientes. Lo
  de §5 es la inyección manual del alcance de ESTE bloque: no la sustituye.
- **T30 · evals con LLM real.** SE FACTURA y no hay autorización previa
  (duda 6): al llegar se presentan casos, proveedores y coste.
- **T31 · el caso real SS-0003967.** Aviso heredado del bloque D §2.1, aún
  vigente: revalorar desde sv4 **no basta**, porque esa vía no re-extrae y el
  merge sigue con las seis columnas a NULL. Hay que volver a pasarlo por sv2.
- **T32 · la ficha en sv4**, la verificación manual de lo que hace este
  bloque: `http://localhost:8004`. §4 dice qué debe aparecer.
- **Lo que NO demuestra este bloque**: que las seis columnas lleguen llenas
  desde PostgreSQL. Aquí se prueba lo probable sin BBDD (R33): que el ORM las
  declara, que el lector las lleva al payload y que la plantilla las pinta.
- **MANUAL de este bloque: ninguna** (sin red, sin BBDD, sin LLM).

---

*Tamaño*: **220** líneas, el tope del rol. La puerta mide
`progress/impl_F-043.md` (nombre exacto), que no existe, y sale `[OK]`. No se
recortó, por norma: las trazas RED, «Evidencias» y la salida de `init.sh`. Sí:
los `FAILED` completos y la prosa, enteros en sus commits.
