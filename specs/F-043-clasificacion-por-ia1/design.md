<!-- specs/F-043-clasificacion-por-ia1/design.md -->
# F-043 · Diseño técnico

## 0 · El defecto

La clasificación se decide **dos veces y la primera manda**: el
`tipologia_resolver` de sv2 la deduce con reglas y con ella **elige el prompt
de fase 2**, así que la regla decide qué puede concluir la IA. Y el dato ni
sobrevive: `phase_merge` lo sella en `meta.tipologia` y
`persistence_worker._sanear_envelope` de sv3 lo **descarta** (`ExtractionMeta`
es `extra='forbid'` y no lo declara). Por eso sv5 y sv6 lo exigen sin
recibirlo. El diseño invierte el orden: **IA1 clasifica el documento**, el
determinismo queda en un `dict` (familia → clave de prompt), y la
clasificación viaja **dentro de `data`**, que sí se persiste.

## 1 · Ficheros a CREAR

| Ruta | Qué es |
|---|---|
| `services/albaranes-comun/ruesma_comun/contratos/familias.py` | Catálogo único (R1–R5) + `familia_efectiva` (R20) |
| `services/albaranes-comun/ruesma_comun/contratos/clasificacion.py` | Contrato Pydantic `ClasificacionAlbaran` (R7) |
| `services/albaranes-api/application/services/clasificacion_resolver.py` | Sustituye a `tipologia_resolver` (R12) |
| `…-comun/tests/test_f043_familias.py` | R1–R5, R18–R21 |
| `…-api/tests/test_f043_clasificacion_resolver.py` | R10–R16 |
| `…-api/tests/test_f043_prompt_fase1.py` | R6, R7 (render del catálogo) |
| `…-persistencia/tests/test_f043_persistencia_clasificacion.py` | R9, R22, R28, R29 |
| `…valoracion-api/tests/test_f043_contexto_clasificacion.py` | R23, R24, R27 |
| `…valoracion-persist/tests/test_f043_familia_efectiva.py` | R25, R27 |
| `…valoracion-persist/tests/test_f043_r26_ss0003967.py` | R26 (desbloquea F-036) |
| `…-front/tests/test_f043_vista_clasificacion.py` | R30 |

### 1.1 · El catálogo (capa `domain` compartida, sin I/O)

```python
@dataclass(frozen=True)
class Familia:
    id: str; nombre: str
    definicion: str          # QUÉ es (va al prompt)
    no_es: str               # en qué se diferencia de sus vecinas
    senales: str             # qué mirar en el documento (evidencia, NO regla)
    alcance: frozenset[str]  # {"documento"} | {"linea"} | ambas
    prompt_fase2: str | None
    prompt_valoracion: str | None

CATALOGO: tuple[Familia, ...]
def familias_documento() -> tuple[str, ...]
def familias_linea() -> tuple[str, ...]
def obtener(id: str) -> Familia | None          # None si fuera de catálogo
def render_catalogo_markdown(alcance="documento") -> str
def prompt_fase2_de(familia: str) -> str | None
def prompt_valoracion_de(familia: str) -> str | None
def familia_efectiva(tipo_familia_linea, clasificacion) -> str | None
```

Contenido inicial (de `docs/referencia/dominio_negocio_albaranes.md` §9):

| id | alcance | `prompt_fase2` | `prompt_valoracion` |
|---|---|---|---|
| `generico` | documento + línea | — (cae a `albaran_revision_fase2_es`) | — (cae a `valuation_es`) |
| `hormigon` | documento + línea | `albaran_revision_fase2_hormigon` | — |
| `mortero` | documento + línea | `albaran_revision_fase2_mortero` | — (`valuation_mortero` lo crea F-023) |
| `residuos` | documento + línea | `albaran_revision_fase2_residuos` | `valuation_residuos` |
| `combustible` | **solo línea** | — | — |
| `alquiler_maquinaria` | **solo línea** | — | — |
| `otro` | **solo línea** | — | — |

`generico` NO es el cajón: su `definicion` es «albarán de suministro de
materiales o productos que se valoran línea-a-contrato, sin reglas de familia
propias» (prefabricados, cerámica, ferretería), y su `no_es` separa
«genérico» de «no lo sé», que se expresa bajando `confianza_pct`. Añadir una
familia = **una entrada aquí** (F-023 documenta la trampa: hoy, cuatro sitios).

`familia_efectiva(tipo_linea, clasificacion)`:
1. `tipo_linea` no vacío → ése (lo que la IA dijo por LÍNEA manda).
2. `clasificacion` ausente → `None` (comportamiento de hoy, R27).
3. `clasificacion.mixto` → `None` (R19: en mixto NO se hereda).
4. si no → `clasificacion.familia` si es familia de línea, si no `None`.

**No es una regla que infiere la familia**: propaga a la línea la decisión que
tomó la IA sobre el documento. No mira LER, ni texto, ni CIF.

### 1.2 · El contrato `ClasificacionAlbaran`

`extra="ignore"` (como `ContextoLinea`: tolera prompts que evolucionen).
Campos: `familia: str`, `confianza_pct: float` (0–100),
`motivo: str`, `mixto: bool = False`,
`familias_secundarias: list[str] = []`, `origen: str = "ia1"`
(`ia1` | `ia2` | `ausente`, lo sella el resolver, no la IA).

### 1.3 · `clasificacion_resolver` (application, sv2, función pura)

`resolver_clasificacion(data_fase1, data_fase2=None) -> ClasificacionAlbaran`:
toma el bloque de fase 2 si existe (R16), si no el de fase 1; normaliza la
familia contra `familias_documento()`; fuera de catálogo → `generico` con el
valor original dentro del motivo (R10); ausente → `generico`,
`confianza_pct=0`, `motivo="ia_sin_clasificacion"`, `origen="ausente"` (R11).
**Cero heurística**: no importa `ruesma_comun.ler`, ni las funciones de texto,
ni el CIF.

## 2 · Ficheros a MODIFICAR

**sv2 · `services/albaranes-api/`**
- `domain/models/albaran_models.py` — `DocumentoAlbaran.clasificacion:
  Optional[ClasificacionAlbaran] = None` (R8; el `extra='forbid'` no estorba
  porque el campo se declara).
- `domain/models/tipologia.py` — **se borra el enum `Tipologia`** y
  `texto_contiene_hormigon` / `texto_contiene_mortero` (solo las usaba el
  resolver); queda la reexportación de `ruesma_comun.ler`, que sí usa sv6.
- `application/services/tipologia_resolver.py` — **se BORRA** (R12, R14).
- `application/services/phase_merge.py` — `construir_envelope_final` recibe
  `clasificacion: ClasificacionAlbaran` y la escribe **en `data`**, no solo en
  `meta` (R9). Se mantiene `meta.tipologia` como espejo para el log.
- `application/services/albaran_extraction_service.py` — sustituye
  `{catalogo_familias}` en el `task` de fase 1 con
  `render_catalogo_markdown("documento")`, junto al `{obras_activas}` que ya
  existe (R6).
- `interface_adapters/worker/extraction_worker.py` — llama a
  `resolver_clasificacion(env1)`, elige el prompt con `prompt_fase2_de(...)`
  con caída al genérico configurado (R15), y tras la fase 2 vuelve a resolver
  con `data_fase2` para que IA2 pueda corregir (R16).
- `config/prompts.yaml` — **RUTA SENSIBLE**. En `albaran_factura_es`: bloque
  «Clasificación del albarán» con `{catalogo_familias}`, la obligación de
  devolver siempre `clasificacion` y la instrucción de que `generico` es una
  respuesta legítima y la duda se expresa bajando `confianza_pct`. En los
  cuatro `albaran_revision_fase2_*`: IA2 confirma o corrige `clasificacion` en
  `documento_revisado` y explica el cambio.

**sv3 · `services/albaranes-persistencia/`**
- `domain/models/extraction_models.py` — mismo campo `clasificacion` en su
  `DocumentoAlbaran`. `ExtractionMeta` **no se toca**: la clasificación ya no
  viaja por `meta`.
- `infrastructure/database/orm_models.py` + `phase2_ddl.py` +
  `schema_contribution.py` — columnas nuevas (§3); el servicio que escribe el
  merge copia los seis campos a esas columnas (R22).
- `application/services/albaran_confidence_service.py` (o el punto donde hoy
  se componen `review_reasons`) — motivos `clasificacion_confianza_baja` y
  `clasificacion_mixta` (R28, R29).
- `config/settings.py` — `clasificacion_confianza_minima_pct: float = 60`.

**sv5 · `services/albaran-valoracion-api/`**
- `infrastructure/database/sqlalchemy_valuation_context_repository.py` —
  `_SQL_MERGE_HEADER` (o `_SQL_DOC_HEADER`) suma las columnas nuevas y las
  monta en `ClasificacionAlbaran`. **Regla 3 de ARCHITECTURE**: sv5 lee con
  SQL crudo, así que este SELECT es lector acoplado de sv3.
- `domain/models/valuation_context.py` — `ContextoValoracion.clasificacion:
  Optional[ClasificacionAlbaran] = None` (R23).
- `application/services/valuation_extraction_service.py` — se retira
  `_derivar_tipologia_valoracion`; el prompt sale de
  `prompt_valoracion_de(context.clasificacion.familia)` con caída a
  `self._prompt_key` (R24, R27).
- El serializador del `context` del envelope añade `clasificacion`.

**sv6 · `services/albaran-valoracion-persist/`**
- `domain/models/valuation_envelope.py` — `ValuationContextDto.clasificacion:
  Optional[ClasificacionAlbaran] = None` (con default, los envelopes viejos
  validan pese al `extra='forbid'`).
- `application/services/valuation_builder.py` — las puertas de familia pasan
  de `getattr(ctx, "tipo_familia", None) != X` a
  `familia_efectiva(getattr(ctx,'tipo_familia',None), clasificacion) != X` en
  **las seis** (líneas actuales 305, 620, 704, 847, 986, 1166, 1227) y en el
  padre de la línea sintética (1397). Ningún otro criterio cambia.

**sv4 · `services/albaranes-front/`**
- El lector que arma el modelo de vista del documento expone `clasificacion`;
  `templates/document_detail.html` la pinta junto al bloque «Motivos de
  revisión» de F-036 R23 (R30). sv4 **no decide** ni recalcula nada de ella.

**Arnés / documentación**
- `harness/rutas_sensibles.json` — añadir `familias.py` y `clasificacion.py`
  de `ruesma_comun/contratos/**` como rutas sensibles: sus textos entran en el
  prompt.
- `docs/ARCHITECTURE.md` §Semántica — regla nueva: «la familia del albarán la
  decide la IA y viaja en `data.clasificacion`»; y
  `docs/referencia/dominio_negocio_albaranes.md` §9 — puntero al catálogo.

## 3 · SQL (schema `public`, tabla propiedad de sv3)

DDL **inline en Python** (CONVENTIONS: no hay `.sql` en el repo), idempotente,
en `infrastructure/database/phase2_ddl.py` y espejado en
`schema_contribution.py`:

```sql
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia VARCHAR(32);
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_confianza_pct DOUBLE PRECISION;
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_motivo TEXT;
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_origen VARCHAR(16);
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_mixta BOOLEAN;
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS tipologia_secundarias_json TEXT;
CREATE INDEX IF NOT EXISTS ix_albaran_documents_merge_tipologia ON albaran_documents_merge(tipologia);
```

Solo en la **merge**: las raw son auditoría forense (regla 1). Lectores
acoplados a avisar: sv5 (SQL crudo) y sv4.

## 4 · Cómo queda DESBLOQUEADA F-036

`progress/impl_F-036_bloque_D.md` §2 midió con el builder real que, mismo
albarán y mismo contrato, el único campo que separa **540,00 € / 1 línea** de
**210,00 € / 2 líneas** es `contexto_linea.tipo_familia='residuos'` — y en
SS-0003967 **ningún proveedor lo puso**. Con este diseño IA1 clasifica el
documento como `residuos` (motivo: gestor de residuos, LER y contenedores en
el papel), sv3 lo persiste, sv5 lo mete en el envelope y `familia_efectiva`
lo hereda a las líneas sin familia: se abren el cálculo de contenedores
(`valuation_builder.py:1166`), la red de sintéticas del LER (`:847`) y la
guarda anti-incremento (`:986`). El test **R26** reproduce esa medición con
fixtures, sin BBDD ni LLM, y la T24 de F-036 (verificación manual del humano)
pasa a poder ejecutarse.

## 5 · Ficheros que NO se tocan (y por qué)

- `ruesma_comun/ler.py`, `residuos_container_calc.py`, `residuos_incrementos`,
  `modifier_contract_matcher` — la maquinaria de residuos de F-036 ya está en
  la rama; aquí solo se abre su puerta, no se rehace lo de dentro.
- `contexto_linea_merger.py` (sv3) — el scorer ampliado de F-036 sigue igual:
  la clasificación es de DOCUMENTO y no pasa por él.
- `familia_detector.py` / `contrato_selector.py` (sv3) — detectan familia por
  TEXTO, pero para puntuar **contratos y proveedores candidatos**, no para
  clasificar el albarán: no son el lazo cerrado. Alimentar su parámetro
  `tipologia` (hoy huérfano) con la clasificación de la IA **NO ENTRA**: mueve
  dinero por otra vía y merece feature propia.
- `unit_registry.yaml`, `ImporteCalculator`, `ruesma_comun.importes`
  (F-024/F-019) y `harness/features.json` (lo gestiona el líder).

## 6 · Riesgos y decisiones

- **Descartado: conservar el resolver como red de seguridad.** Prohibido por
  decisión expresa del 2026-08-25 (reversión de la T11 de F-036: *«los
  residuos no se deben clasificar solo porque contenga LER, es una regla de
  mierda»*). Si IA1 no clasifica, el sistema dice `generico` con confianza 0 y
  **manda a revisión**; nunca adivina.
- **Descartado: escribir la familia heredada en `contexto_linea` al
  persistir.** Borraría la diferencia entre «la IA lo dijo por línea» y «se
  heredó del documento». La herencia se resuelve en lectura (R21).
- **Límite reconocido del albarán mixto.** El prompt de fase 2 se elige por
  DOCUMENTO: en un albarán mixto las líneas de la familia minoritaria se leen
  con las instrucciones de la mayoritaria. No se disimula: IA1 lo declara,
  sv3 lo marca `clasificacion_mixta` y las líneas sin familia no heredan
  (R19). Resolverlo de verdad —segunda pasada de fase 2— es otra feature.
- **Riesgo de radio de impacto.** Cambia el enrutado de todo el pipeline. Se
  mitiga con R27 (envelope sin clasificación ⇒ comportamiento de hoy) y con la
  caída al prompt genérico cuando la clave no existe.
- **Coste real.** `config/prompts.yaml` de sv2 y sv5 son RUTA SENSIBLE del
  arnés: el cierre exige `python -m evals.runner --con-llm --feature F-043`
  con informe `progress/evals_F-043.md` y las líneas `MODO: completa`,
  `FASES: IA1,IA2,IA3,IA4,E2E` y `VEREDICTO: VERDE`. Es una pasada con LLM
  real sobre los fixtures: **se factura**, y la autoriza el humano (duda 6).
- **LÍMITE DE SERVICIO.** Nada de esto pide un servicio nuevo: cada pieza cae
  donde ya vive su responsabilidad (sv2 extrae y clasifica, sv3 persiste, sv5
  valora, sv6 aplica reglas). Lo compartido —catálogo y contrato— va a
  `albaranes-comun`, nunca copiado entre servicios.
