# F-117 · Diseño técnico

Servicios: **comun** 0.13.0 → **0.14.0** (la regla, pura) y **sv6** (aplicarla en la normalización de F-076). Sin DDL,
sin colas, sin endpoints, sin IA nueva. sv4, sv5, sv9 y sv3 no se tocan.

## 1. Límite de servicio y dónde vive hoy la lógica

Decidir la partida final al valorar es de sv6, y desde F-076 lo hace ANTES de IA4 y de las reglas
(`normalizador_partidas.py`, paso 2 bis de `run_valuation_pipeline.py:252-254`); la lista de la obra la da
`CachePartidasObra` de comun. `partida_fuera_de_lista` solo lo escribe `NormalizadorPartidas.anotar`
(`normalizador_partidas.py:47, 192-198`) cuando `resolver_partida_obra` (comun `partidas.py:652`) da `fuera_de_lista`.
La equivalencia es una regla de comparación de códigos ⇒ comun, junto a `normalizar_partida`; aplicarla es un paso más
en el normalizador. Ninguna responsabilidad nueva. El precedente de F-111 parte B (IA de sv5 que elige entre
candidatas, `POST /v1/albaranes/partida-residuos`) NO se reutiliza (D4): hoy no hay ningún caso que lo necesite.

## 2. Medición en producción (solo lectura, 2026-11-05)

`scripts/medicion_F-117/` (`run.ps1` + `comun_ro.py` como F-111: claves de Key Vault a variables del proceso,
borradas en `finally`; PG con `default_transaction_read_only=on`, comprobado; Sigrid solo `POST /api/sql/read` con
`SQL_PARTIDAS_POR_OBRA`, sin `truncated`). Universo: documentos activos con valoración. Detalle: `progress/spec_F-117.md`.

- **31 líneas en 21 documentos** con `partida_fuera_de_lista` (ninguna con `partida_ambigua_en_obra`). 5 ya casan hoy
  (valoradas antes de F-098: `CD.07.14` ⇒ `07.14`…): se arreglan revalorando, sin F-117. Quedan **26**.
- **Regla de la letra (R2)**: **1 línea**, la de 0719 `CI.03.08` ⇒ `CI.03A.8` «CAMION GRUA» (aprobada, alta
  `no_admitido` por `partida_no_encontrada`). Su hermana `CI.03.18` («grua pk 44», misma obra) la corrigió el revisor
  a mano a `CI.03A.8`: el humano elige lo mismo que la regla.
- **La letra al revés**: 1 línea más, y es un **falso positivo** (0694 `01.03A.02`, un taburete ⇒ `01.03.02`
  «ESTRUCT. FORJADO LOSA»). Por eso R3.
- **Regla del sufijo (R4)**: **5 líneas** de 0719, `04.01.07` ⇒ `02.04.01.07` única; las 5 aprobadas y el revisor las
  corrigió a mano a **exactamente** `02.04.01.07`. 0 falsos positivos en el universo.
- **Lectura = capítulo** (no hoja): 8 líneas de 0692 con `CD.02` (18 hojas debajo); 5 son las otras altas
  `no_admitido`. El revisor eligió `CD2.07` en 3, que **no cuelga de `CD.02`**: ni el árbol ni una IA restringida a
  él lo habrían acertado ⇒ fuera de alcance (R8, D8).
- **Sin equivalente**: 12 líneas (0694 `CI.14.18` ×2, `CI.14.12`, `CI.04.01.08`, `01.03A.02`; 0696 ×3 `P4.PJ.36.01`, `PY.03.05`; 0724
  `CI.03.A`; 0669 `12.01.03`; 0719 `02.01.01.07`, `CI.03.18`): siguen como hoy.
- **Ambigüedad de la letra** en las 19 obras con albaranes en 120 días: 16 tienen hojas con letra; de 261 esqueletos,
  **33 tienen 2 o más hojas** (0459: `CI.03A.n` y `CI.03P.n` para n = 1…12). Es el falso positivo que preocupaba:
  R16 lo manda a revisión. 17 esqueletos coinciden con una hoja sin letra: ahí gana la normalización de hoy (R7).
- **Altas `no_admitido` con `partida_no_encontrada`** hoy: 6 líneas; F-117 resuelve 1 (la de 0719); las 5 de `CD.02`
  no.

## 3. Reglas (comun, `ruesma_comun/sigrid/partidas.py`)

```
def equivalentes_partida(lista: ListaPartidasObra, lectura: Any, alm: str | None) -> tuple[str, ...]
```
1. `resolver_partida_obra(lista, lectura, alm).motivo != "fuera_de_lista"` ⇒ `()`; compuesta (`/`) ⇒ `()` (R7).
2. `_choca_con_no_hoja(lista, lectura)` ⇒ `()` (R8; ya existe, `partidas.py:643`).
3. `seg = normalizar_partida(lectura).split(".")`. Por cada hoja y forma (`codigo`, `codigo_completo`), `hs` = sus
   segmentos normalizados:
   - **letra** (R2, R3): ningún `s ∈ seg` casa `RE_SEGMENTO_CON_LETRA`, alguno de `hs` sí, y `_sin_letra(hs) == seg`
     ⇒ equivalente. `_sin_letra` cambia cada `03A` por `3` (dígitos sin ceros) y deja el resto.
   - **sufijo** (R4, R5): `len(seg) >= MIN_SEGMENTOS_SUFIJO`, `len(hs) > len(seg)` y `hs[-len(seg):] == seg`.
4. Cods sin duplicados en el orden de `lista.hojas` (R6).

Constantes nuevas: `RE_SEGMENTO_CON_LETRA = re.compile(r"^(\d+)([A-Z]+)$")`, `MIN_SEGMENTOS_SUFIJO = 3`. Docstring del
módulo: el párrafo «REGLA DE FONDO (H1…)» gana «salvo (F-117) `equivalentes_partida`, que PROPONE con dos reglas
cerradas y nunca decide sola: quien la usa la manda a revisión» (R11). Nunca devuelve algo que no sea un cod de la lista.

## 4. Aplicarla (sv6, `application/services/normalizador_partidas.py`)

`NormalizadorPartidas.__init__(..., equivalente: bool = False)`: con `False` nada cambia (R19; los llamantes y tests de
hoy siguen igual). `NormalizacionSobre` gana `equivalencias: dict[int, tuple[str, ...]]` (defecto vacío;
`merge_line_id` ⇒ cods).

En `normalizar` (`:124-146`), tras `resolver_partida_obra`:
```
if self._equivalente and resolucion.motivo == "fuera_de_lista":
    cods = equivalentes_partida(lista, linea.codigo_partida_albaran, self._alm)
    if cods: equivalencias[linea.merge_line_id] = cods
    if len(cods) == 1: nuevas[posicion] = cods[0]
```
La copia profunda del sobre ya existe (`:143-145`); IA4, la valoración directa y el builder trabajan con ella sin
cambios. El log INFO (`:134`) suma `equivalentes=` y `ambiguas=` (R22).

En `anotar` (`:183-200`), para las líneas con `merge_line_id` en `n.equivalencias`:
- 1 cod ⇒ `codigo_partida_albaran = leída`; motivo `PREFIJO_PARTIDA_EQUIVALENTE + f"{leída}>{cod}"`
  (`"partida_equivalente:"`); **sin** `partida_fuera_de_lista`; revisión en línea y cabecera (R14, R15).
- ≥ 2 ⇒ lo de hoy (`partida_fuera_de_lista`, revisión) más `PREFIJO_EQUIVALENTE_AMBIGUA + ",".join(cods[:5])`
  (`"partida_equivalente_ambigua:"`, `,+N` si hay más) (R16).
El resto de `anotar` no cambia; `_anadir` ya evita duplicados (R21).

`config/settings.py`: `partida_equivalente_enabled: bool = Field(True, alias="PARTIDA_EQUIVALENTE_ENABLED")`, en el
bloque de F-076. `interface_adapters/composition.py:163`: `equivalente=settings.partida_equivalente_enabled`.
`run_valuation_pipeline.py` NO cambia: ya llama a `normalizar` y a `anotar` en las dos ramas (`:253`, `:327`, `:388`).

**Cómo lo ve sv4** (D6): la partida final ya es una hoja ⇒ el combo la pinta válida (hoy, roja). El motivo sale como
texto en la traza de F-036 R23; en filas de origen Contrato el ⚠ de F-077 sigue diciendo «No coincide con la partida
leída (CI.03.08)». sv9 manda `codigo_partida_final`: sigrid-api la encuentra.

## 5. Ficheros a crear

| Fichero | Qué |
|---|---|
| `services/albaranes-comun/tests/test_f117_equivalentes_partida.py` | R1–R12 |
| `services/albaran-valoracion-persist/tests/test_f117_partida_equivalente.py` | R13–R23 (normalizador y `anotar`) |
| `services/albaran-valoracion-persist/tests/test_f117_pipeline.py` | R24–R26 (pipeline con fakes, rama directa) |
| `scripts/medicion_F-117/{run.ps1,comun_ro.py,m1_fuera_de_lista.py,m2_estrategias.py}` | ya en la rama (§2) |

## 6. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/sigrid/partidas.py` | §3 y docstring |
| `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` | exportar `equivalentes_partida` |
| `services/albaranes-comun/pyproject.toml`, `ruesma_comun/__init__.py` | 0.14.0 |
| `services/albaran-valoracion-persist/application/services/normalizador_partidas.py` | §4 y docstring |
| `services/albaran-valoracion-persist/config/settings.py`, `interface_adapters/composition.py` | interruptor |
| `docs/ARCHITECTURE.md` | regla 23: «nunca por sufijo» ⇒ salvo F-117; reglas y motivos (R27) |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` | §11: `PARTIDA_EQUIVALENTE_ENABLED` (R27) |

## 7. Ficheros que NO se tocan

comun: `casar_partida`, `resolver_partida_obra`, `normalizar_partida`, `misma_partida`, `mostrar_partida`,
`candidatas_residuos`, `CachePartidasObra` (R10). sv6: `run_valuation_pipeline.py`, `partida_matcher.py`,
`valuation_builder.py`, `partida_residuos.py` (F-111), `almacen_politica.py` (F-051), repositorio, ORM,
`schema_contribution.py`. sv5 entero (sin IA nueva). sv4 entero (D6, D8). sv9 entero. Tests de F-049/F-076/F-098/F-111
sin tocar: si alguno cambia, es un error de F-117.

## 8. SQL

Ninguno. La lista sale de la misma consulta y caché de F-076 (`SQL_PARTIDAS_POR_OBRA`, `NO_TOLERA`). Sin DDL.

## 9. Decisiones abiertas (PARADA 1)

- **D1 · Levantar H1 de F-049 para esto.** H1 (2026-10-02): «se verifica y se normaliza, nunca se elige; ni sufijo, ni
  prefijo, ni distancia». La petición la contradice. (a) **Recomendada**: excepción acotada a las dos reglas de D2, en
  una función aparte que propone y manda a revisión (D3); el resto del módulo sigue igual. (b) No levantarla: F-117 se
  cancela y la línea se arregla a mano en sv4.
- **D2 · Qué reglas.** (a) **Recomendada**: letra (solo en la hoja) + sufijo de ≥ 3 segmentos, y solo si la
  equivalente es única: 6 líneas medidas, las 6 coinciden con lo que eligió el revisor, 0 falsos positivos. (b) Solo la
  letra (lo pedido al pie de la letra): 1 línea. (c) La letra en los dos sentidos: descartada, 1 falso positivo medido.
- **D3 · Una equivalente única, ¿a revisión?** (a) **Recomendada**: sí, no bloqueante: la partida ya va puesta (sv9 la
  manda bien si se aprueba sin tocar) y el revisor la ve. Es la diferencia con `partida_normalizada` (misma partida,
  otra forma: sin revisión). (b) Sin revisión, como la normalizada.
- **D4 · Dos o más equivalentes.** (a) **Recomendada**: revisión con las candidatas en el motivo, sin IA. Hoy 0
  líneas, pero 33 esqueletos ambiguos (0459). (b) IA de sv5 que elige por la descripción entre las candidatas
  (generalizar el endpoint de F-111): llamada de pago y sv5 en el alcance; si aparece el caso, feature aparte.
- **D5 · Formato del motivo.** (a) **Recomendada**: `partida_equivalente:<leída>><cod>`, el separador `>` de
  `partida_normalizada` (F-076). (b) `->`.
- **D6 · sv4.** (a) **Recomendada**: nada nuevo (§4). (b) Nota «Equivalente: X → Y» en el `title` como F-076 R24 (toca
  sv4: otra tarea).
- **D7 · Lo ya valorado.** No hay revaloración automática. (a) **Recomendada**: tras desplegar, el líder lista en solo
  lectura (T9) y el humano decide. Hoy solo cambiaría la de 0719 `CI.03.08` (aprobada, alta `no_admitido`): se puede
  corregir ya a mano en sv4 sin esperar a F-117. Las 5 de `04.01.07` ya están corregidas a mano (F-106 lo conserva al
  revalorar). (b) Revaloración masiva (escritura en producción: no la lanza un agente).
- **D8 · Fuera de alcance.** Que sv4 avise o impida aprobar con `partida_fuera_de_lista` (el humano eligió esta vía,
  no esa); la lectura que es un capítulo (`CD.02`, 5 de las 6 altas `no_admitido`); los errores de lectura
  (`CI.03.18`, `CI.14.18`). (a) **Recomendada**: dejarlos fuera y, si el humano quiere, abrir una feature para el
  capítulo leído. (b) Meter aquí el capítulo leído con IA (no lo habría acertado, §2).
- **D9 · Interruptor.** (a) **Recomendada**: `PARTIDA_EQUIVALENTE_ENABLED` en sv6, defecto `true` (vuelta atrás sin
  redesplegar). (b) Sin interruptor (`PARTIDAS_OBRA_NORMALIZAR_ENABLED=false` apaga también F-076).

## 10. Riesgos

- **R-1 · Falso positivo del sufijo** en obras con numeración repetida por fase (0686 tiene `xx.14` en 46 hojas). Lo
  acotan los ≥ 3 segmentos, la unicidad y la revisión (D3). Tras desplegar, T9 lo mide.
- **R-2 · IA4 casa distinto**: con la partida equivalente, su casado estricto por partida (regla del 2026-10-23) puede
  encontrar línea de contrato donde hoy no; es el efecto buscado y queda a revisión.
- **R-3 · Encaje con F-100** (blocked): toca `run_valuation_pipeline.py`, `composition.py` y `settings.py`; F-117 solo
  añade una línea en los dos últimos ⇒ fusión trivial. Con F-111 (blocked, ya en `dev`) no comparte código.
- Despliegue (lo lanza el humano): comun 0.14.0 ⇒ **sv6** (`.\deploy.ps1 -Only sv6` → `.\check_deploy.ps1`). sv4 y
  sv9 usan comun pero no la función nueva: no hace falta redesplegarlos. Rigor **critico**: RED, cobertura y mutación.
