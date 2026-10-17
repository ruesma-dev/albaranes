<!-- specs/F-076-normalizar-partidas/design.md -->
# F-076 · La partida se normaliza contra las de la obra · Diseño (v1, 2026-10-16)

Medición, decisiones abiertas (P1–P11) y propuesta para la PARADA 1: `progress/spec_F-076.md`.

## 1. Encaje y límite de servicio

La regla «la partida final es un código que existe en la obra» es una regla determinista de la **valoración**: sv6
ya fija `codigo_partida_final` (`PartidaMatcher`) y es la fuente que leen la ficha (sv4) y el alta (sv9). Por eso se
normaliza **en sv6, antes de las reglas**: lo que la ficha enseña es lo que sv9 manda (petición del humano), el
casado con la línea de contrato mejora solo (hoy `CI.04.18` ≠ `CI.4.18` del contrato ⇒ derivada «Nueva») y cada
revaloración vuelve a aplicarlo (también tras cambiar la obra en sv4). Ninguna responsabilidad nueva fuera del
pipeline: sv6 pasa a **leer** de sigrid-api (como ya hacen sv3, sv4 y sv9), sin escribir nada.

Alternativas descartadas (detalle en `progress/spec_F-076.md` §3):
- **sv9 antes del alta**: lo enviado dejaría de ser lo que enseña la ficha y lo aprobado (regla 19/20); sv9 solo
  escribe `albaran_altas_sigrid` y no puede corregir la valoración. sigrid-api ya valida (`partida_no_encontrada`).
- **sv3 al persistir** (reescribir `codigo_imputacion`): no se re-ejecuta al revalorar ni al cambiar la obra, y
  `codigo_imputacion` es lo impreso (regla 6). Es lo que hará F-049 en sv2 con la lista; no lo duplicamos.
- **Esperar a F-049**: lleva prompts de IA2 (evals de pago), reparto y seis servicios; está `blocked` y 88 commits
  por delante de `dev`. F-076 porta solo sus funciones puras ya APROBADAS (§8).

## 2. Hallazgos que fijan el diseño

- **sigrid-api** (`create_albaran_compra_use_case.resolver_partida`) busca la partida entre las IMPUTABLES de la obra
  comparando como el ERP: `strip().casefold()` (`Modern_Spanish_CI_AS`). Mayúsculas y espacios de cola ya no fallan;
  **los ceros a la izquierda sí**. Imputables ≈ hojas en las 7 obras medidas (2341 frente a 2343 en la 0678).
- Confirmado con la previa real: los dos albaranes de T51 pasaron a `simulado` con `CI.4.18` (el humano la puso a
  mano el 2026-10-16 08:22). La 0678 tiene la hoja `CI.4.18` y no `CI.04.18`.
- sv6 no conoce la obra: el sobre de sv5 no la trae (`ValuationContextDto`, `extra='forbid'`). Se lee del merge
  por `document_id` (sv6 ya comparte BBDD; añadir el campo al sobre obligaría a desplegar sv6 antes que sv5).
- La lista: 0,1–4,7 s por obra; 64 obras × ~3.000 filas caben en memoria. Caché por réplica (§6).

## 3. Ficheros

**Crear**
| Ruta | Qué |
|---|---|
| `services/albaranes-comun/ruesma_comun/sigrid/partidas.py` | §5.1 (porta de F-049 `224f64e` lo marcado; añade R5 y R6) |
| `services/albaranes-comun/tests/test_f076_partidas.py` | R1–R6 (casos de §2 y de la medición; reloj falso) |
| `services/albaran-valoracion-persist/domain/ports/partidas_obra_port.py` | `PartidasObraPort` (Protocol) |
| `services/albaran-valoracion-persist/application/services/normalizador_partidas.py` | `NormalizadorPartidas` (§5.2) |
| `services/albaran-valoracion-persist/infrastructure/sigrid/__init__.py` + `sigrid_api_lector.py` | `SigridApiLector` (§5.3) |
| `services/albaran-valoracion-persist/tests/test_f076_*.py` | R7–R14, R17, R18 (sobres de fixture, puertos falsos) |
| `services/albaranes-front/tests/test_f076_partidas_sv4.py` | R15 (mismas filas ⇒ mismos `items`) |
| `services/albaranes-front/tests/test_f076_aviso_partida.py` | R23–R25 (función pura + render de la plantilla) |
| `services/albaranes-alta-sigrid/tests/test_f076_partida_final.py` | R16 |
| `infra/set_partidas_sv6.ps1` | R19 (UTF-8 BOM, CRLF; patrón de `set_alta_sigrid.ps1`) |
| `services/albaran-valoracion-persist/scripts/medir_f076_partidas.py` | R22: script puntual de medición (`print` permitido) |

**Modificar**
| Ruta | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` | exporta lo de §5.1; docstring: excepción a D2 de F-052 (como F-049) |
| `services/albaranes-comun/pyproject.toml`, `ruesma_comun/__init__.py`, `README.md` | versión 0.8.0 y una línea |
| `services/albaran-valoracion-persist/application/pipelines/run_valuation_pipeline.py` | §6: normalizar tras recibir el sobre; anotar tras el build |
| `services/albaran-valoracion-persist/domain/ports/valuation_repository.py` | `obra_del_documento(document_id) -> str \| None` |
| `services/albaran-valoracion-persist/infrastructure/database/sqlalchemy_valuation_repository.py` | su SELECT (§4) |
| `services/albaran-valoracion-persist/config/settings.py` | R17 |
| `services/albaran-valoracion-persist/interface_adapters/composition.py` y `interface_adapters/api/app.py` | cablear lector, caché y normalizador (los dos puntos de entrada) |
| `services/albaran-valoracion-persist/sv6.md` | sección corta F-076 |
| `services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py` | `fetch_partidas_por_obra` usa comun (R15); fuera `_SQL_PARTIDAS_POR_OBRA` y el cálculo de hojas |
| `services/albaranes-front/domain/models/review_models.py` | `coincide_partida` (§5.4) y campo `partida_normalizada_desde` en `ConciliacionDisplay` |
| `services/albaranes-front/infrastructure/database/review_repository.py` | `_agree_txt` (~L4567, uso ~L4641) y `_txt` (~L4780, uso ~L4787) solo para la partida: `coincide_partida` |
| `services/albaranes-front/templates/document_detail.html` | `title` de la casilla de partida (~L742 editable, ~L750 y ~L752 solo lectura): nota de R24 |
| `infra/create_capps.ps1` | bloque sv6: secreto `sigrid-key` y variables de R17 |
| `docs/ARCHITECTURE.md` | regla 22 (nueva) y «Acceso a datos» |
| `harness/features.json`, `progress/` | estado e informes |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` | sv6 consume `sql/read` de sigrid-api (repo propio; commit allí, sin push) |

**NO se tocan**: `partida_matcher.py` y `valuation_builder.py` (reciben el sobre ya normalizado: cero cambios en
sus reglas); sv5 (sus modelos y prompts); sv9 (`validador_alta.py` ya manda `codigo_partida_final`); sv3 y sv2;
`ruesma_comun.obras` (se usa `canonizar_codigo_obra` de F-070 tal cual); `ruesma_comun.alta_sigrid`; los combos y
el guardado de sv4 (F-065), el JS de la ficha (✓/⚠ los pinta el servidor) y los demás `agree_*`; `harness/rutas_sensibles.json` (ya cubre `application/services/**` de sv6).

## 4. SQL

Sin DDL. Dos lecturas:
- **Sigrid** (vía `POST /api/sql/read`, comun): `SQL_PARTIDAS_POR_OBRA` de F-049 = la de sv4 + `AND con_obr.emp = 1`
  (`ide, padide, cod, res` de `obrparpar` por `con_obr.cod = ?`). Hojas en Python.
- **PostgreSQL** (sv6, solo lectura, nuevo lector acoplado a una columna de sv3):
  `SELECT obra_codigo FROM albaran_documents_merge WHERE id = :document_id`. Se declara en ARCHITECTURE regla 3
  («todo cambio de schema lista sus lectores»).

## 5. Clases y funciones

### 5.1 comun · `ruesma_comun.sigrid.partidas` (puro; el HTTP lo pone cada servicio)

Portado de F-049 sin cambios de semántica: `SQL_PARTIDAS_POR_OBRA`, `PartidaObra`, `ListaPartidasObra`
(`hojas`, `no_hojas`, `codigos`, `desde_filas`), `hojas_de_filas`, `LectorSql` (Protocol), `normalizar_partida`,
`partes_de_partida`, `casar_partida`, `CasePartida` y los `MOTIVO_*`. **Cambia solo** `leer_partidas_obra(leer,
obra)`: canoniza con `canonizar_codigo_obra` de `dev` (F-070) en vez de `obra_a_consultar` (F-049 A2, no está en
`dev`); vacío ⇒ `None`. No se portan `repartir`, `hojas_por_sufijo` ni el índice de obras.

Nuevo (F-076):
- `ResolucionPartida` (frozen): `codigo: str | None`, `motivo: Literal["exacta","normalizada","fuera_de_lista",
  "ambigua","no_aplica"]`, `leida: str | None`; propiedad `cambia` (`codigo != leida`).
- `resolver_partida_obra(lista, lectura, alm) -> ResolucionPartida`: `casar_partida` + guarda de no hoja (R5):
  con `normalizada`, si `normalizar_partida(lectura)` es la clave de algún `lista.no_hojas` ⇒ `fuera_de_lista`.
  `compuesta` ⇒ `fuera_de_lista`; `alm`/`sin_partida` ⇒ `no_aplica`.
- `CachePartidasObra(lector: LectorSql, *, ttl_s, max_obras, ttl_fallo_s, reloj=time.monotonic)` con
  `lista(obra) -> ListaPartidasObra | None` (R6). Clave = obra canonizada. Una lista con 0 hojas cuenta como
  «sin lista» (`None`), como en el remate de F-049. Log: obra, hojas, segundos; en fallo, WARNING con la causa.

### 5.2 sv6 · `application/services/normalizador_partidas.py`

```python
@dataclass(frozen=True)
class NormalizacionSobre:
    envelope: ValuationEnvelope                    # copia con las lecturas ya normalizadas
    por_linea: dict[int, ResolucionPartida]        # merge_line_id -> resolución (solo líneas con lectura)
    motivos_cabecera: tuple[str, ...]              # p. ej. ("partidas_obra_no_disponibles",)

class NormalizadorPartidas:
    def __init__(self, *, partidas: PartidasObraPort | None, alm_codigo_partida: str, activo: bool) -> None
    def normalizar(self, *, envelope: ValuationEnvelope, obra: str | None) -> NormalizacionSobre
    @staticmethod
    def anotar(header: ValuationHeaderRecord, lines: list[LineValuationRecord], n: NormalizacionSobre) -> None
```
- `normalizar`: inactivo, sin puerto o sin lecturas ⇒ sobre intacto y sin motivos. Sin lista ⇒ sobre intacto +
  `partidas_obra_no_disponibles` (R11). Con lista: por cada `context.lineas_albaran[i]` con lectura, R5; si
  `cambia`, sustituye `codigo_partida_albaran` en una copia (`model_copy(update=...)`, nunca muta el original).
- `anotar` (tras el build, sobre las líneas con `merge_line_id` de `por_linea` y `line_kind == "from_albaran"`):
  `normalizada` ⇒ añade `partida_normalizada:<leída>><lista>` y devuelve `codigo_partida_albaran` a la leída (R9);
  `fuera_de_lista`/`ambigua` ⇒ añade `partida_fuera_de_lista`/`partida_ambigua_en_obra`, `review_required=True`
  en línea y cabecera (R10). Los motivos de cabecera se añaden sin duplicar. No toca importes, casado ni almacén.

### 5.3 sv6 · infraestructura y puertos

- `PartidasObraPort.lista(obra: str | None) -> ListaPartidasObra | None` (lo implementa `CachePartidasObra`).
- `SigridApiLector(base_url, function_key, database, timeout_s)`: `__call__` = `LectorSql`. `httpx` POST a
  `/api/sql/read` con `x-functions-key`; tenacity (3 intentos, exponencial, solo 5xx/timeout/conexión);
  `ok=false` o 4xx ⇒ excepción; `comprobar_truncado(body, politica=...)`. Log: etiqueta, estado, filas; nunca
  la clave ni el cuerpo (R18).
- `ValuationRepository.obra_del_documento`: §4; sin fila ⇒ `None`.

### 5.4 sv4 · aviso ✓/⚠ por la clave (ampliación aprobada, R23–R25)

`review_models.coincide_partida(declarada, esperada) -> tuple[bool | None, str | None]` (pura, dominio de sv4):
vacías ⇒ `(None, None)`; `normalizar_partida(d) == normalizar_partida(e)` ⇒ `(True, d.strip())` si difieren
literalmente, `(True, None)` si son iguales; si no ⇒ `(False, None)`. El repositorio la usa para la partida en los
dos sitios (`agree_partida` y `partida_normalizada_desde`); `_agree_txt` y `_txt` siguen para los otros campos. La
plantilla compone el `title`: `descripcion_partida` y, si hay `partida_normalizada_desde`, « · Normalizada:
{desde} → {codigo_partida}» (escapado por Jinja). Por qué en sv4 y no en sv6: el aviso compara la leída del merge,
que F-076 conserva a propósito (regla 6); la clave es la de comun, así que ✓ significa lo mismo que lo que sv6
normaliza. Sin lista de la obra: no hace falta, compara dos códigos entre sí.

## 6. Flujo en `RunValuationPipeline.run`

1. (igual) duplicado sin `force` ⇒ devuelve la existente; llamada a sv5 y sus errores.
2. **Nuevo**: `obra = repository.obra_del_documento(id)` (solo si hay lecturas y el normalizador está activo) y
   `n = normalizador.normalizar(envelope=envelope, obra=obra)`; desde aquí se usa `n.envelope`.
3. (igual) rama `no_contract` (hoy sin líneas: no se anota; F-075 debe anotar sus líneas, §8), IA4, `build`.
4. **Nuevo**: `NormalizadorPartidas.anotar(header, lines, n)` antes de `replace_valuation`; `raw_ia_envelope_json`
   = `n.envelope` (R14).
Cualquier excepción del paso 2 se captura: WARNING y se sigue con el sobre original + `partidas_obra_no_disponibles`.

Cableado (composition y app): `SigridApiLector` solo si hay URL y clave; si no, puerto `None` (R11, WARNING al
arrancar). `CachePartidasObra` una por proceso.

## 7. Configuración e infra

Settings (R17) con `Field(..., alias=...)`; `PARTIDAS_OBRA_NORMALIZAR_ENABLED=false` es el interruptor de vuelta
atrás sin redesplegar. `infra/set_partidas_sv6.ps1`: `az containerapp secret set` (`sigrid-key=keyvaultref:...
SIGRID-API-FUNCTION-KEY,identityref:$MI_ID`) + `az containerapp update --set-env-vars` con
`SIGRID_API_BASE_URL=$SIGRID_BASE_URL`, `SIGRID_API_DATABASE=$SIGRID_DB`, `SIGRID_API_FUNCTION_KEY=secretref:
sigrid-key` y los `PARTIDAS_OBRA_*`; al final lee la app y dice OK/KO por variable. La identidad gestionada ya lee
ese secreto (sv3, sv4 y sv9 lo usan). Lo lanza el humano.

## 8. Interacción con otras features

- **F-049** (`blocked`, rama propia): F-076 porta a `dev` el subconjunto de §5.1. Al retomarla, F-049 rebasa sobre
  `dev`: el `partidas.py` de F-049 es superconjunto (conflicto add/add, se queda el suyo conservando
  `resolver_partida_obra`, `CachePartidasObra` y la guarda de no hoja); su sv4 ya hace lo de R15; su versión de comun
  pasa a 0.9.0. Recomendación para F-049: adoptar la guarda de no hoja en su sello.
- **F-053** (sv9): sin código. Menos `no_admitido` por partida; el `no_admitido` + reaprobar sigue igual.
- **F-065** (combo de la obra): la final ya es un código de la lista ⇒ el combo la reconoce. Una línea que con
  F-076 casa con su línea de contrato sale «Contrato» en vez de «Nueva».
- **F-075** (spec aprobada, sin código): su `ValoracionDirectaBuilder` («la partida se copia tal cual») recibirá
  `n.envelope` porque el paso 2 va antes de la rama `no_contract`; debe llamar a `anotar` con sus líneas. Quien
  fusione segundo lo integra (nota en `progress/spec_F-076.md`).
- **F-058**: revalorar para corregir lo existente pierde lo manual (P5). **F-067**: sin solape (no tiene código).
- **F-077** (`../albaranes-F-077`, solo sv4, `spec_ready`): sus R20–R22 ponen en el ⚠ de partida el `title` «No
  coincide con la partida leída en el albarán (X)» con `aviso_partida` y dicen que «el cálculo de `agree_partida` no
  cambia». F-076 sí lo cambia (R23): con las dos, el ⚠ (y su texto de F-077) sale solo con clave distinta y el ✓
  normalizado lleva la nota de R24. Mismas líneas de `review_repository.py` y `document_detail.html`: quien fusione
  segundo compone los dos `title` (⚠ ⇒ el de F-077; ✓ normalizado ⇒ el de R24) y ajusta R22 de F-077. F-077 no
  se toca desde aquí.

## 9. Despliegue

comun 0.8.0 va en cada imagen. Orden: **`infra\set_partidas_sv6.ps1`** (variables antes que el código: sin ellas
R11 y nada cambia) → **sv6** → **sv4** (`.\deploy.ps1 -Only sv6`, `-Only sv4`, `.\check_deploy.ps1`). Sin DDL ni
cambio de mensajes: vale cualquier orden entre sv6 y sv4. Rollback: `PARTIDAS_OBRA_NORMALIZAR_ENABLED=false`.

## 10. Riesgos y decisiones

- **Cambian valoraciones** al revalorar: líneas que pasan de «Nueva» a «Contrato» (0723: 2 líneas), y a revisión
  las 6 de la medición sin candidata. Es el objetivo; se ve en la MANUAL final.
- **Ruta sensible** (`application/services/**` de sv6, exigencia «aviso»): IA4 recibe la lectura normalizada.
  Sin evals de pago salvo que el humano lo pida (P8).
- **Caché vieja** (6 h): una partida nueva en Sigrid tarda hasta el TTL en contar; el caso dañino (que cree una
  ambigüedad) es teórico y se arregla revalorando. Fallo recordado 300 s para no martillear sigrid-api.
- **Separadores** (P2): la clave de F-049 unifica `.`, `-`, espacio; medido 0 casos hoy, la ambigüedad lo protege.
- **sv4 cambia** (P7): 0517/0581 dejan de mezclar partidas de dos empresas; lista truncada ⇒ `ok=false`.
