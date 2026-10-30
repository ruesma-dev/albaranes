# F-111 · Diseño técnico

Servicios: **sv6** (reglas de contenedor y asignación de partida), **sv5** (prompt de IA3 y un endpoint de IA
nuevo), **comun** 0.10.0 → **0.11.0** (reconocer el capítulo; F-106 sube a 0.10.0). Sin DDL, sin colas, sin cambios en
sv3, sv4 ni sv9. Va después de F-106 (§11).

## 1. Límite de servicio

Las dos reglas son de valoración: cuántas unidades y a qué partida se imputa la línea. sv6 ya decide la partida final
(`partida_matcher.py`) y ya tiene la lista de la obra (F-076, `CachePartidasObra`); sv5 es el motor de IA (IA3, IA4).
Reconocer el capítulo es leer la lista de Sigrid, que vive en comun para sv4 y sv6. Ninguna responsabilidad nueva.

## 2. Medición en producción (solo lectura, 2026-10-29)

PostgreSQL `albaranes` con `default_transaction_read_only=on` y `SHOW transaction_read_only = on`; Sigrid solo con
`POST /api/sql/read` y `SQL_PARTIDAS_POR_OBRA` de comun, sin `truncated`. Claves de Key Vault en variables del proceso,
borradas en `finally`; scripts en el scratchpad. Universo: documentos activos con valoración.

**Contenedores.** 25 líneas de residuos; 11 calculadas por volumen (m³: 7 de 6, 4 de 8). Con R1–R7 **cambian 2**, las
dos de CTSU24/0524 (obra 0686, contrato sin tamaño, `residuos_tamano_defecto_6m3`): 8 m³ ⇒ 2 de 6 hoy, 1 de 9 con
F-111; 149 € y 139 € (el 4839 B, **aprobado**). Diferencia: −288 €. Las 6 con tamaños en el contrato no cambian
(6 ⇒ 6, 8 ⇒ 8 exacto). Ninguna pasa de 9 m³.

**Sin partida.** 8 líneas de residuos `from_albaran` sin partida final, todas `almacen_sin_partida`, ninguna con
lectura; 8 documentos (1 aprobado), obras 0686 (3), 0694, 0697, 0459, 0669, 0687. Partidas finales de residuos con
partida: 0686 `32.01` (5), 0692 `CD2.07`, 0669 `12.01.03`, 0724 `CI.03.A`.

**El capítulo en las obras.** Las 17 obras con albaranes en 120 días tienen un nodo «GESTIÓN DE RESIDUOS» (variantes:
«GESTION RESIDUOS (SEGÚN EGRC)», «PLAN DE GESTIÓN DE RESIDUOS», «GESTIÓN DE LOS RESIDUOS EN OBRA/RSD-01»). **No es un
capítulo raíz** (no es el `capitulo` de F-098, que es CD/CI/CP): cuelga de CD en nivel 1 (`32`, `19`, `27`, `10`,
`18`, `20`, `23`, `02`) o 2 (`01.21`, `102.08`, `P4.35`, `32` bajo un subcapítulo de fase). Casi siempre tiene 1 hoja
(`32.01` «GRD010 Gestión de residuos», `19.01`, `01.21.01`…), más a veces una de ajuste (`32.99`, `23.03` «Ajuste
decimales»). Casos con varias candidatas tras quitar ajustes: 0459 (18 hojas: bidones, transporte, clasificación…),
0669 (`102.08.01` y `31.01`, ambas «GESTION DE RESIDUOS»), 0678 y 0693 (una por fase), 0686 (`32.01` y `37.06.01`
«OPERARIO EXCLUSIVO PARA CLASIFICACIÓN»), 0696 (P4 y P5, 3 hojas cada una), 0720 (2), 0723 (3). Falsos positivos
de «RESIDU» que la regla de R17 descarta: «SANEAMIENTO RESIDUAL», «AGUAS RESIDUALES», «CONTENEDOR RESIDUOS 45
LITROS» y «TRATAMIENTO DE RESIDUOS» (hojas sueltas, sin «GESTION» en un antecesor). Para las 8 líneas: 0687, 0694,
0697 ⇒ 1 candidata; 0686 ⇒ 2 (32.01, 37.06.01); 0669 ⇒ 2 iguales (irá a revisión); 0459 ⇒ 18.

## 3. Cómo es hoy

- **Tamaño** (`residuos_container_calc.py:97-130, 197-229`): de la tabla, el exacto; si no, el único; si no, el de 6;
  si no, `contenedor_m3` de IA3; si no, la descripción de la casada; si no, **6 por defecto**. `ceil(m³ / tamaño)`.
- **IA3** (`prompts.yaml:1077-1087`): «si NO coincide con ninguno -> la línea de 6 m3 … el valor por defecto ante
  cualquier duda». En CTSU24/0524 IA3 rellenó `contenedor_m3 = 6` por esa regla, y sv6 lo usó.
- **Partida**: sin lectura y con `ALMACEN_SIN_PARTIDA_ENABLED`, `PartidaMatcher.match` (`:98-114`) ⇒ almacén
  (F-051), sin mirar la familia; la familia destinada solo añade `partida_ausente_familia_destinada`.
- **Orden del pipeline** (`run_valuation_pipeline.py:201-259`): IA3 (sv5) ⇒ normalizar partida (F-076) ⇒ valoración
  directa ⇒ IA4 ⇒ build. La normalización solo pide la lista si alguna línea trae lectura (`necesita_obra`).

## 4. Parte A · tamaño de contenedor

`_elegir_tamano(tamanos: list[float], m3: float) -> tuple[int, float]` (pura, en `residuos_container_calc.py`):
- `tamanos` vacía ⇒ estándar `_TAMANOS_ESTANDAR = (3.0, 6.0, 9.0)`: el menor `t` con `m3 <= t + 0.01` ⇒ `(1, t)`;
  si no cabe ⇒ `(ceil(m3 / 6), 6.0)` (R1, R2).
- con tamaños ⇒ el menor `t` en que cabe ⇒ `(1, t)`; si no cabe en ninguno ⇒ D2 (R6, R7).

`calcular_contenedores_residuos` conserva firma, prioridades 1 y 3 y los motivos de hoy. En la prioridad 2: fuentes
de R8 (`_tamanos_del_contrato(contrato_lines)` = todos los m³ de líneas «contenedor» de la tabla, sin deduplicar por
tipo; si vacía, `[contenedor_m3_ia]`; si no, `[m³ de la casada]`; si no, estándar). `ResultadoContenedores` gana
`revision: bool = False` (por defecto ⇒ los llamantes de hoy no cambian), a `True` con R9. `_CONTENEDOR_ESTANDAR_M3` y
`residuos_tamano_defecto_6m3` desaparecen; motivo nuevo `MOTIVO_TAMANO_ESTANDAR = "residuos_tamano_estandar"`.

`valuation_builder.py`: una condición más junto a las de `:1345-1355`: `if residuos_calc is not None and
residuos_calc.revision: review_required = True`. Nada más del builder.

IA3: el paso 4 de `valuation_residuos` (`prompts.yaml:1077-1093`) se reescribe con R6/R7/R1/R2 y R13–R14; el
«sistema» (`:1026-1033`) no cambia (R15). El precio sigue siendo el de la línea casada (R4): ya lo es hoy.

## 5. Parte B · partida del capítulo de residuos

**comun** (`ruesma_comun/sigrid/partidas.py`): `candidatas_residuos(lista)` (R17–R19), sobre `descripcion_agregada`
(ruta `res` raíz→hoja unida por « › »): parte la ruta, quita el último tramo (la hoja), normaliza con `_comparable` y
busca `GESTION` + `\bRESIDUO`. Constantes `PATRON_CAPITULO_RESIDUOS` y `PREFIJO_AJUSTE`. Reconocer no es elegir: H1
de F-049 sigue intacta y la docstring del módulo lo dice.

**sv6** (`application/services/partida_residuos.py`, capa application, sin I/O propio):
```
class AsignadorPartidaResiduos:
    def __init__(self, *, partidas: PartidasObraPort | None, elector: EligePartidaPort | None,
                 alm_codigo_partida: str, activo: bool) -> None
    def necesita_obra(self, envelope) -> bool        # activo y alguna línea de residuos sin lectura
    def asignar(self, *, envelope, obra, clasificacion) -> AsignacionResiduos
    @staticmethod
    def anotar(header, lines, asignacion) -> None     # R23, R25–R27 en los registros
@dataclass(frozen=True)
class AsignacionResiduos: envelope; por_linea: dict[int, ResultadoPartidaResiduos]; sin_almacen: frozenset[int]
```
`asignar` copia el sobre (como `NormalizadorPartidas.normalizar`) y pone `codigo_partida_albaran = cod` en las líneas
asignadas; `anotar` devuelve la lectura vacía, añade `partida_residuos:<cod>` o el motivo de revisión y marca
`review_required` en línea y cabecera. Las líneas sin partida asignada (R25–R27) NO llevan marcador en el sobre (se
colaría como partida): `AsignacionResiduos.sin_almacen: frozenset[int]` (sus `merge_line_id`) llega al builder, que
llama a `PartidaMatcher.match(..., sin_almacen=True)` para ellas: salta la rama F-051 y cae en la de hoy «sin match y
sin partida» (`no_action`) o en la de IA casada (`existing_matched`, partida vacía); nunca `almacen_sin_partida` (D5).

Puerto nuevo `domain/ports/elige_partida_port.py` (`EligePartidaPort.elegir(document_id, lineas, candidatas) ->
dict[int, str | None]`), adaptador `infrastructure/clients/http_partida_residuos_client.py` (httpx, como
`http_conciliacion_client.py`, reintentos con tenacity). Cableado en `interface_adapters/composition.py`;
`config/settings.py`: `PARTIDA_RESIDUOS_ENABLED: bool = True`.

`run_valuation_pipeline.py`: tras `_normalizar_partidas` (`:201`), `_asignar_partida_residuos(document_id, envelope)`
con la misma guarda «nunca lanza» y la obra leída una vez (se comparte con la normalización: si ya se leyó, se
reutiliza, R30). Excepción ⇒ sobre sin tocar y todas las líneas candidatas con `partida_residuos_sin_lista` (R27).
Tras el build, `AsignadorPartidaResiduos.anotar` junto a `NormalizadorPartidas.anotar` (`:270`, `:328`).

La familia: `familia_efectiva(ctx.tipo_familia, clasificacion)` con la clasificación del sobre que ya usa el builder
(`valuation_builder.py:317`); se extrae a una función de módulo reutilizable sin cambiar su comportamiento.

**sv5**: `POST /v1/albaranes/partida-residuos` en `interface_adapters/api/app.py` (cuerpo pydantic en
`domain/models/partida_residuos_models.py`), servicio `application/services/partida_residuos_service.py` (como
`ConciliacionService`: arma el texto, llama al proveedor de `seleccionar_ia4`, valida la salida) y prompt
`partida_residuos_es` en `config/prompts.yaml` con su esquema `documento_partida_residuos`. sv5 no lee BBDD aquí.

## 6. Ficheros a crear

| Fichero | Qué |
|---|---|
| `services/albaran-valoracion-persist/application/services/partida_residuos.py` | §5 |
| `services/albaran-valoracion-persist/domain/ports/elige_partida_port.py` | puerto |
| `services/albaran-valoracion-persist/infrastructure/clients/http_partida_residuos_client.py` | adaptador |
| `services/albaran-valoracion-api/application/services/partida_residuos_service.py` | servicio IA |
| `services/albaran-valoracion-api/domain/models/partida_residuos_models.py` | cuerpo y respuesta |
| tests: sv6 `tests/test_f111_{tamano,partida_residuos,pipeline,cliente}.py`; sv5 `tests/test_f111_{prompt_residuos,partida_residuos}.py`; comun `tests/test_f111_candidatas_residuos.py` | R1–R36 |

## 7. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/albaran-valoracion-persist/application/services/residuos_container_calc.py` | §4; docstring con la regla 3/6/9 |
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | `residuos_calc.revision` ⇒ revisión; `sin_almacen` hacia el matcher; `_familia_de` reutilizable |
| `services/albaran-valoracion-persist/application/services/partida_matcher.py` | `match(..., sin_almacen: bool = False)`: con `True` no entra en la rama F-051 |
| `services/albaran-valoracion-persist/application/pipelines/run_valuation_pipeline.py` | paso de §5 y su `anotar` |
| `services/albaran-valoracion-persist/interface_adapters/composition.py`, `config/settings.py` | cableado, `PARTIDA_RESIDUOS_ENABLED`, URL de sv5 (la de IA4) |
| `services/albaran-valoracion-persist/tests/test_f036_r22_contenedores_prioridades.py` | solo los tests que fijaban el 6 por defecto (R10) |
| `services/albaran-valoracion-api/config/prompts.yaml` | paso 4 de `valuation_residuos`; prompt `partida_residuos_es` |
| `services/albaran-valoracion-api/config/prompts/svc5_prompt_valuation_es.yaml` | regla 4 del bloque de residuos (D1) |
| `services/albaran-valoracion-api/interface_adapters/api/app.py` | endpoint |
| `services/albaranes-comun/ruesma_comun/sigrid/partidas.py`, `sigrid/__init__.py`, `pyproject.toml`, `ruesma_comun/__init__.py` | R17–R19, 0.11.0 |
| `docs/ARCHITECTURE.md` | R36 |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` | solo si lista los endpoints internos de sv5 (lo comprueba el implementer) |

## 8. Ficheros que NO se tocan

sv6 `normalizador_partidas.py` (F-076), `conciliacion_orchestrator.py`, `price_reconciler.py`, `importe_calculator.py`,
`residuos_incrementos.py`, `almacen_politica.py`, el repositorio, el ORM y `schema_contribution.py` (F-106). sv5
`valuation_residuos` salvo el paso 4, `conciliacion_es`, `valuation_es`. `casar_partida`, `resolver_partida_obra` y
`CachePartidasObra` de comun. sv4 y sv9 enteros (D5, D6).

## 9. SQL

Ninguno nuevo. sv6 reutiliza `SQL_OBRA_DEL_DOCUMENTO` y la lista de `SQL_PARTIDAS_POR_OBRA` (sigrid-api, lectura,
`NO_TOLERA`). Sin DDL.

## 10. Decisiones abiertas (PARADA 1)

- **D1 · `svc5_prompt_valuation_es.yaml`.** No lo carga nadie (`settings.prompts_yaml_path = config/prompts.yaml`;
  `sv5.md:105` lo llama «versión histórica»). (a) **Recomendada**: corregir su regla 4 para que ningún fichero diga «6
  por defecto». (b) No tocarlo. (c) Borrarlo (otra feature).
- **D2 · m³ que no caben en ningún tamaño del contrato.** (a) **Recomendada**: paquetes de 6 si el contrato tiene el
  de 6 (la regla del humano para el estándar); si no, `ceil(m³ / mayor)` del mayor. (b) Siempre del mayor. (c) A
  revisión sin número. Hoy no hay ningún caso medido.
- **D3 · Quién elige con varias candidatas.** (a) **Recomendada**: 1 ⇒ esa sin IA; ≥ 2 ⇒ IA en sv5 por significado,
  restringida a las candidatas, `null` si duda (R21–R22, R31–R34; en las 8 líneas: 3 sin IA, 0686 con IA, 0669 a
  revisión, 0459 con IA). (b) Texto determinista (palabras de la descripción): choca con «la clasificación la decide la
  IA» y no separa 32.01 de 37.06.01. (c) Con ≥ 2, a revisión con las candidatas listadas, sin IA (más barato; deja 0686
  y 0459 a mano). (d) Usar la partida de la línea de contrato casada: F-051 lo prohíbe (no se copia la del contrato).
- **D4 · Partida asignada: ¿revisión?** (a) **Recomendada**: sin revisión, solo el motivo `partida_residuos:<cod>`
  (como `partida_normalizada`). (b) Revisión no bloqueante cuando la eligió la IA.
- **D5 · Sin capítulo o sin candidata («nunca a almacén»).** En F-051 almacén = partida final vacía, así que la línea
  queda vacía igualmente. (a) **Recomendada**: revisión con motivo y sin `almacen_sin_partida` (sv4 la sigue pintando
  vacía; el revisor elige partida o almacén a sabiendas; F-106 conserva su elección). (b) Además, sv4 no deja aprobar y
  sv9 la rechaza (`no_admitido`) si es de residuos y va vacía sin edición humana: toca sv4 y sv9.
- **D6 · Qué se ve en sv4.** (a) **Recomendada**: nada nuevo; los motivos salen en la traza de F-036 R23 como texto.
  (b) Textos legibles para los motivos nuevos en sv4 (una tarea más, otro servicio).
- **D7 · Lo ya valorado y lo aprobado.** No hay revaloración automática: los 2 documentos de contenedores (uno aprobado,
  ya en Sigrid con 278 €) y los 8 de partida cambian solo si se revaloran desde sv4 (aprobado = solo lectura: hay que
  desaprobar). (a) **Recomendada**: el líder lista en solo lectura los afectados tras desplegar (T13) y el humano decide
  caso a caso; el aprobado se corrige en Sigrid a mano. Con F-106, una cantidad editada a mano se conserva al revalorar.
  (b) Script de revaloración masiva (escritura en producción: no la lanza un agente).
- **D8 · Banco de evals.** (a) **Recomendada**: sin caso nuevo; el número de contenedores es determinista en sv6 y su
  test es unitario; el prompt se prueba por texto. (b) Añadir un caso RES (8 m³ sin tamaño) al banco de F-084 y
  re-medir IA3 (coste de una pasada).
- **D9 · Orden con F-100.** F-100 (blocked, espera F-106) cambia `run_valuation_pipeline.py`, `composition.py`,
  `config/settings.py`, `valuation_builder.py`, `valuation_residuos` (sintéticas) y `app.py` de sv5: **los mismos
  ficheros** que F-111. (a) **Recomendada**: F-111 antes (es pequeña y ya hay importes mal); F-100 rebasa y su prefiltro
  usa la partida asignada (su R25 lee la del sobre). (b) F-100 antes y F-111 rebasa.
- **D10 · Reconocer el capítulo.** (a) **Recomendada**: patrón fijo «GESTION» + «RESIDUO» en un antecesor (17 de 17
  obras). (b) Patrón por variable de entorno en sv6.

## 11. Encaje con F-106

F-106 toca en sv6 solo el repositorio, el ORM y `schema_contribution.py`; F-111 ninguno de los tres. comun: F-106
0.10.0, F-111 0.11.0 sobre ella (`partidas.py` no lo toca F-106). Riesgo de fusión bajo. Comportamiento: con F-106, una
línea de residuos cuya cantidad o partida editó el revisor conserva lo editado al revalorar: F-111 solo cambia lo no
editado. F-111 se rebasa sobre `dev` con F-106 antes de empezar.

## 12. Riesgos

- **R-1 · IA3 sigue rellenando `contenedor_m3 = 6`** por costumbre: sv6 lo tomaría como «tamaño del contrato» (R8).
  Mitigación: R13 en el prompt y un test con `contenedor_m3_ia=6` y contrato sin tamaño que documenta que sv6 lo usa;
  tras desplegar, T13 mide si quedan `contenedor=6` con 8 m³.
- **R-2 · Falsos capítulos.** Un antecesor «GESTION DE RESIDUOS» en una fase cerrada da candidatas de más; la IA o la
  revisión lo resuelven (0669, 0678, 0693).
- **R-3 · 0459 con 18 hojas**: la IA puede elegir «transporte» o «bidón»; R32 pide `null` ante la duda.
- **R-4 · Coste**: una llamada de IA por documento de residuos sin partida con ≥ 2 candidatas (hoy, ~4 documentos).
- Despliegue (lo lanza el humano): comun 0.11.0 ⇒ sv5 (endpoint) ⇒ sv6. sv6 sin sv5 nuevo ⇒ 404 ⇒ R26
  (`partida_residuos_ia_fallo`), sin romper. Rigor **critico**: fase RED, cobertura y mutación completa.
