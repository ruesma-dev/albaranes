# F-111 · Diseño técnico

Servicios: **sv6** (reglas de contenedor y asignación de partida; parte C en §13), **sv5** (prompt de IA3 y un
endpoint de IA nuevo), **comun** 0.10.0 → **0.11.0** (reconocer el capítulo; F-106 sube a 0.10.0). Sin DDL, sin colas, sin cambios en
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
| sv6 `tests/test_f111_partida_contrato.py` | parte C, R37–R47 (§13) |
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
| `docs/ARCHITECTURE.md` | R36; R47 (parte C) |
| `services/albaran-valoracion-persist/application/services/partida_residuos.py` | parte C (§13), ya creado en B |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` | solo si lista los endpoints internos de sv5 (lo comprueba el implementer) |

## 8. Ficheros que NO se tocan

sv6 `normalizador_partidas.py` (F-076), `conciliacion_orchestrator.py`, `price_reconciler.py`, `importe_calculator.py`,
`residuos_incrementos.py`, `almacen_politica.py`, el repositorio, el ORM y `schema_contribution.py` (F-106). sv5
`valuation_residuos` salvo el paso 4, `conciliacion_es`, `valuation_es`. `casar_partida`, `resolver_partida_obra` y
`CachePartidasObra` de comun. sv4 y sv9 enteros (D5, D6).

## 9. SQL

Ninguno nuevo. sv6 reutiliza `SQL_OBRA_DEL_DOCUMENTO` y la lista de `SQL_PARTIDAS_POR_OBRA` (sigrid-api, lectura,
`NO_TOLERA`). Sin DDL.

## 10. Decisiones de la PARADA 1 de A y B (cerradas)

**Cerrada por el humano el 2026-10-30 («doy por bueno a»): D1–D10 = (a).** Texto completo de las alternativas en el
historial de git de este fichero (commit de la spec, 2026-10-29) y resumen en `progress/spec_F-111.md` §3.
D1 corregir también `svc5_prompt_valuation_es.yaml` · D2 m³ fuera de los tamaños del contrato ⇒ paquetes de 6 si el
contrato tiene el de 6, si no del mayor · D3 1 candidata sin IA, ≥ 2 IA en sv5 · D4 partida asignada sin revisión ·
D5 sin partida ⇒ revisión sin `almacen_sin_partida` (sin tocar sv4/sv9) · D6 nada nuevo en sv4 · D7 lo ya valorado,
caso a caso tras desplegar (T13) · D8 sin caso nuevo en el banco de evals · D9 F-111 antes de F-100 · D10 patrón fijo
«GESTION» + «RESIDUO». La D3 (d) descartada entonces («usar la partida de la línea de contrato») la reabre la parte C.

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

## 13. Parte C · primero la partida del contrato (2026-11-05/06; PARADA 1: D1=b, D2=a, D3=a)

**Medición (líder, producción, solo lectura, 2026-11-05).** Las 8 líneas de §2, por obra: 0686 (3 docs) contrato con
`32.01` (120 líneas) y `CI.03A.7` ⇒ `32.01` sin IA (hoy: capítulo con 2 ⇒ IA); 0669 (1) `31.01`, `102.08.01`,
`CI.03A.7` ⇒ IA entre las 2 del capítulo; 0694 y 0697 (1 y 1) solo `CI.03A.7` (MAQUINARIA AJENA › CONTENEDORES) ⇒
`CI.03A.7` (paso 2); 0459 y 0687 (1 y 1) sin partidas en el contrato ⇒ capítulo (0459: 19 candidatas ⇒ IA; 0687: 1 ⇒
`19.01`). Detalle en `progress/spec_F-111.md` §5.

**Cambio, solo en `application/services/partida_residuos.py`** (application, sin I/O):
- Función pura nueva `partidas_del_contrato(lineas_contrato, lista, alm) -> tuple[PartidaObra, ...]` (R37): por cada
  `codigo_partida` con `normalizar_partida` no `None`, `resolver_partida_obra(lista, cod, alm)`; vale si el motivo es
  `exacta`/`normalizada` y `not lista.cod_repetido(codigo)`; la hoja es la de `lista.hojas` con ese código; sin
  duplicados, orden de primera aparición. Nada de parecido ni prefijos: lo que no casa, fuera.
- `asignar`, tras obtener la lista: `contrato = partidas_del_contrato(...)`; `capitulo = candidatas_residuos(lista)`;
  `paso1 = [c for c in contrato if c.codigo in {k.codigo for k in capitulo}]`. Conjunto y prefijo:
  `paso1` ⇒ (`paso1`, `partida_residuos_contrato:`); si no, `contrato` ⇒ (`contrato`, `partida_residuos_contrato_hoja:`);
  si no, (`capitulo`, `partida_residuos:`). Con el conjunto elegido, la lógica de hoy sin cambios: 0 ⇒
  `sin_capitulo` (solo posible en el paso 3), 1 ⇒ esa sin IA, ≥ 2 ⇒ `_elegir_con_ia` con ESE conjunto (R38–R43).
- `ResultadoPartidaResiduos` no cambia (el motivo ya lleva el prefijo); `anotar` no cambia: los motivos de asignación
  no van a cabecera ni a revisión, y la cabecera de revisión sigue partiendo por «:» (R42, R43).
- Constantes nuevas `PREFIJO_PARTIDA_RESIDUOS_CONTRATO = "partida_residuos_contrato:"` y
  `PREFIJO_PARTIDA_RESIDUOS_CONTRATO_HOJA = "partida_residuos_contrato_hoja:"` (R46); el log añade `paso=`.
- `alm_codigo_partida` deja de descartarse (`del`): se guarda para `partidas_del_contrato` (un `ALM` del contrato es
  `no_aplica`, no una hoja). La docstring del módulo explica los tres pasos.

**No cambia:** pipeline (`asignar` ya recibe el sobre con `lineas_contrato`, la obra y la lista de la caché; R30),
composición, settings (mismo `PARTIDA_RESIDUOS_ENABLED`, R45), matcher, builder, comun (todo lo necesario ya existe:
`resolver_partida_obra`, `cod_repetido`, `candidatas_residuos`; sin subir versión), sv3, sv4, sv9, DDL.

**sv5 (D-C1, abierta).** El prompt `partida_residuos_es` dice que las candidatas son «las partidas hoja del capítulo de
gestión de residuos»; en el paso 2 no lo son. (a) **Recomendada**: cambiar solo esa frase a «partidas hoja de la obra
(del contrato del proveedor o del capítulo de gestión de residuos)», sin tocar reglas ni esquema (R48; redespliegue
de sv5). (b) No tocar sv5: hoy no hay ningún caso medido de paso 2 con ≥ 2 partidas (0694/0697 tienen una). Si (b),
R48 y T18 se quitan.

**Interpretaciones a validar** (`progress/current.md`): (i) R43: la IA que no elige en el paso 1/2 manda a revisión, no
cae al paso siguiente (lectura literal de D2=a); (ii) R37: «partidas del contrato» son las de TODAS las líneas del
contrato del sobre, no solo la casada (D1=b lo pide para `CI.03A.7`); (iii) los motivos de revisión del paso 1/2 son
los mismos de la parte B (sv4 no los distingue; el código del conjunto en el motivo sí).

**Riesgos.** C-1: un contrato con muchas partidas ajenas a residuos (proveedor multiproducto) lleva al paso 2 con IA
entre partidas que no son de residuos; la IA puede devolver `null` (revisión). C-2: la parte C confía en el
`codigo_partida` de `lineas_contrato`, que rellena sv5 de `cl.codigo_partida`
(`sqlalchemy_valuation_context_repository.py:215,375`): sin cambio, pero si llega vacío, paso 3. C-3: es una
excepción explícita a F-051 («sv6 no copia la partida del contrato»), acotada a residuos sin lectura (R47).
Despliegue (lo lanza el humano): sv6; sv5 solo si D-C1 = (a). Rigor **critico**: RED, cobertura y mutación de lo nuevo.
