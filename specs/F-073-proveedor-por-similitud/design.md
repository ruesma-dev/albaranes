# F-073 · Proveedor por nombre: un criterio con similitud y sin elegir en empates — diseño

Solo **sv3-persistencia**. Sin DDL, sin `ruesma_comun`, sin cambios en mensajes ni en lo que sv3
expone o consume (no hay que tocar `azure-apps/albaranes.md`). Despliegue: solo sv3.

## 1. Diagnóstico verificado (dev `d79b3d9`)

`services/albaranes-persistencia/application/services/header_resolver_service.py`:

- `_norm` (l. 69) no quita puntuación y `_match_score` (l. 77) cuenta como acierto cada palabra
  de ≥ 3 caracteres del leído que aparece como subcadena del candidato. «feymaco, s.a.» frente a
  «ferreteria … construccion, s.a. (feymaco)»: «feymaco,» no está («(feymaco)» no lleva coma
  detrás) y «s.a.» sí ⇒ 1/2 = 0,50; frente a «hierros rodrigo, s.a.», igual ⇒ 0,50. «teymaco» no
  casa nunca. Reproducido con el prototipo (§5): 0,50 / 0,50 y el atajo devuelve A19004589.
- Atajo del paso 1 (l. 1035–1046): `max(candidatos, key=score_nombre)` y `>= min_score` ⇒ en
  empate gana el primero de la lista (la agregada viene ordenada por CIF: A19… < A28…).
- Paso 2, fallback global (l. 464–478): `score > best_score` ⇒ también el primero en empate, entre
  3.543 proveedores; con «FEYMACO, S.A.» casaba cualquier «…, S.A.» a 0,50.
- `_score_razon_social` (l. 103, F-052/F-062) sí trata la puntuación como separador y es simétrico,
  pero deja «s», «l» y «a» como restos y solo lo usa la red por CIF: hoy hay **dos criterios**.

## 2. Ficheros a crear

- `services/albaranes-persistencia/application/services/similitud_proveedor.py` — criterio único
  (R1–R9). Puro, sin E/S ni dependencias nuevas (stdlib + `ruesma_comun.proveedores.normalizar_cif`).
  Va en `application/services/` como `familia_detector.py` y `contrato_selector.py` (precedente de
  sv3 para lógica pura; `domain/` solo tiene `models/` y `ports/`).
- `services/albaranes-persistencia/tests/test_f073_similitud.py` — R2–R8 (unidad).
- `services/albaranes-persistencia/tests/test_f073_eleccion.py` — R9–R14 y R20 (resolver con
  dobles en memoria).
- `services/albaranes-persistencia/tests/test_f073_incidencia_0694.py` — R18 (tres rutas con el
  doble de sigrid-api y `fixture_f073`).
- `services/albaranes-persistencia/tests/test_f073_corpus.py` — R19 (corpus de §5, versionado).

## 3. Ficheros a modificar

- `application/services/header_resolver_service.py`:
  - Fuera `_PUNTUACION_RAZON`, `_score_razon_social` y `_distancia_edicion` (pasan a
    `similitud_proveedor`); se importan `similitud_razon_social`, `distancia_edicion` y
    `elegir_por_nombre`.
  - `_match_score` y `_norm` se quedan **solo para la obra** (R16); su docstring lo dice.
  - Constructor: `margen_nombre: float = MARGEN_NOMBRE_POR_DEFECTO` (R20), se guarda y se loguea en
    «INSTANCIADO». Las dos composiciones (`interface_adapters/composition.py` y
    `interface_adapters/api/app.py`) **no cambian**: usan el defecto.
  - `_candidatos_puntuados`: `similitud_razon_social` en vez de `_score_razon_social` (R1, R15).
  - `_candidato_claro`: `distancia_edicion` (R8).
  - `_resolver_por_obra_y_familia`: `score_nombre = similitud_razon_social(leído, r.nombre)`; el
    atajo pasa a `elegir_por_nombre(...)` (R9). Si elige ⇒ como hoy (`deterministic`, retira la
    nota). Si `empate` ⇒ sigue el paso por puntos **intacto** (R10); si los puntos tampoco
    deciden y hubo empate ⇒ `_marcar_revision_safely(motivo=MOTIVO_PROVEEDOR_NOMBRE_AMBIGUO,
    nota=…)` en vez de `_nota_proveedor_safely` (R11). Sin empate, la nota de hoy.
  - `_resolve_proveedor`, paso 2: `elegir_por_nombre` sobre la lista global filtrada (R9, R10,
    R14); sin nota ni motivo en empate, solo log.
- `domain/models/header_resolution_models.py`: `MOTIVO_PROVEEDOR_NOMBRE_AMBIGUO =
  "proveedor_nombre_ambiguo"` (sin sufijo: no lleva CIF; ningún `depurar_motivos_proveedor` lo
  toca, como `proveedor_cif_propio:`).
- `tests/doble_sigrid_api.py`: sección nueva `fixture_f073()` (§4), sin tocar las de F-052,
  F-062 ni F-063.
- `tests/test_f062_r3_candidato_claro.py` y `tests/test_f062_r10_sin_candidato_claro.py`: el
  `import` de `_distancia_edicion`/`_score_razon_social` pasa al módulo nuevo (con alias local
  para no tocar los cuerpos). Única expectativa que cambia, **tras el visto bueno del humano
  (P0)**: el caso `solo-forma-juridica` de `CASOS_OPCION_B` sale de esa lista y pasa a un test
  propio de F-073 que fija lo contrario («S.L.» = 0 ⇒ sin corrección, `proveedor_cif_no_casa`);
  el comentario de `CASOS_OPCION_B` cita la decisión y la fecha.
- `tests/test_f052_resumen_obra.py`: el caso `nombre-debil-y-familia` (R17) y
  `marcar_revision_cabecera` en su `_RepoFake` (hoy no lo tiene; sin él el best-effort se tragaría
  el error y no habría nota).
- `scripts/verificar_f052_proveedores_obra.py`: `similitud_razon_social` en vez de
  `_score_razon_social` (R1); y en `tests/test_f052_script_verificacion.py`, el assert del mejor de
  «PROVEEDOR OBRA 07» (R17, tercer caso, humano 2026-10-17).
- `docs/ARCHITECTURE.md`: regla 24 nueva (la 22 y la 23 ya son de F-078 y F-076) (criterio único, sin elegir en empate, motivo nuevo) y
  una línea en la 17 («score de F-052» ⇒ «similitud de F-073»).

## 4. Fixture `fixture_f073` (obra 0694, razones sociales reales)

Del log de producción y de `evals/fixtures/final/FER-00*.json`:
`A28733558` «FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)» con textos de contrato
de hormigón, mortero, maquinaria y acero (las familias del log: `['acero','hormigon',
'maquinaria','mortero']`); `A19004589` «HIERROS RODRIGO, S.A.» con `ACERO CORRUGADO B500S`
(`['acero']`) y su contrato `CTSU26/0001` (el del log); en `prv`, además, Construcciones Ruesma
(A81873903). El código del contrato de FEYMACO es **ficticio** y se dice en el comentario (no se
conoce el real). Las líneas del albarán, sin familia (`DISCO CORTE 230 MM`), como en el log
(`comunes=-`).

## 5. Medición (prototipo en el scratchpad del spec-author; se versiona como `test_f073_corpus.py`)

Corpus: las 18 razones sociales distintas de `evals/fixtures/final/` (FEYMACO, HORPRESOL,
SALMEDINA…, MAHORSA) + HIERROS RODRIGO = 19 candidatos. 31 lecturas, cada una con el esperado
(índice o «ninguno»): las 3 de FEYMACO de la incidencia (`FEYMACO, S.A.`, `TEYMACO, S.A.`,
`FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.`), solo el nombre comercial (`Cubas`,
`HORPRESOL`, `SALMEDINA`, `SALTOKI`, `MAHORSA`, `PINSACON`, `VODALAND`, `DICONA`), con marca
delante (`GRUPO OTTO HORPRESOL`), una letra mal (`H0RPRESOL S.L.`, `DlCONA S.A.`), sin forma o con
otra (`MACOTRAN S.L.U.`, `PAVIMARSA S.A.`, `Saltoki Centro S.A.`…), parciales (`GRUAS ANGEL MARTIN`,
`Hormigones Paz del Barrio`, `MATERIALES Y HORMIGONES SL`, `Salmedina Tratamiento de Residuos`) y
tres que no deben elegir (`S.A.`, `HORMIGONES`, `TRANSPORTES`). La lista exacta va en el test.

| Criterio | Aciertos | Errores (CIF equivocado) | Sin decisión |
|---|---|---|---|
| Hoy (`_match_score`, máximo, ≥ 0,5) | 23 | **7** (FEYMACO×2→SALTOKI, H0RPRESOL→CUBAS, DlCONA→SALTOKI, «S.A.», «HORMIGONES», «TRANSPORTES») | 1 |
| F-073 (R2–R9, margen 0,25) | **31** | 0 | 0 |

Con los tests existentes: 23 pares de nombres de F-002, F-052, F-062, F-063 y F-070 dan la misma
similitud que `_score_razon_social` hoy (tabla en `progress/spec_F-073.md` §3); la única excepción
encontrada es «S.L.» de `CASOS_OPCION_B` (1 ⇒ 0, P0). Frente a `_match_score` (atajo y paso 2,
asimétrico) la similitud solo sube, salvo lo que aportaban formas jurídicas y palabras vacías
(«GRUPO OTTO HORPRESOL» 0,33 ⇒ 1). En la obra 0691 del doble (81 candidatos) «SALMEDINA» y
«SALMEDlNA» eligen SALMEDINA y «PROVEEDOR» no elige.

## 6. Firmas (`application/services/similitud_proveedor.py`)

```python
FORMAS_JURIDICAS: frozenset[str]      # R2, lista cerrada
PALABRAS_VACIAS: frozenset[str]       # R2
MARGEN_NOMBRE_POR_DEFECTO: float = 0.25

def palabras_razon_social(texto: str | None) -> tuple[str, ...]: ...          # R2
def similitud_razon_social(leido: str | None, candidato: str | None) -> float: ...  # R3–R7
def distancia_edicion(a: str, b: str) -> int: ...                             # R8 (la de F-062)

@dataclass(frozen=True)
class CandidatoNombre:
    cif: str
    nombre: str | None
    similitud: float

@dataclass(frozen=True)
class EleccionPorNombre:
    elegido: CandidatoNombre | None   # R9
    empatados: tuple[CandidatoNombre, ...]  # R11: best − sim < margen, orden (−sim, cif)
    segunda: float                    # R13 (0.0 sin segundo)

def elegir_por_nombre(
    leido: str | None,
    candidatos: Iterable[tuple[str | None, str | None]],   # (cif, razón social)
    *, umbral: float, margen: float,
) -> EleccionPorNombre: ...
```

- Agrupación por `normalizar_cif(cif) or (cif or "").strip()`; un CIF vacío se ignora. El
  orden de salida no depende del de entrada (R12).
- `empatados` solo se rellena cuando el mejor llega al umbral y no saca el margen; con mejor <
  umbral, `elegido=None` y `empatados=()` (no es empate, es «nadie casa»: el paso por puntos de hoy).
- En el paso 1 el resolver necesita los puntos de cada empatado para ordenar la nota (R11): toma
  los CIF de `empatados` y los busca en su lista de `_CandidatoObra`, orden (−puntos, cif).

**Tests existentes y R17.** Si al implementar otro test cambia de resultado, el implementer PARA y
lo anota: solo es aceptable si el test fijaba un empate resuelto por orden de llegada, y lo decide
el humano. Pasó una vez (T3, 2026-10-17): el script de F-052 y su test, aceptado como tercer caso de
R17 (opción a de `progress/impl_F-073.md` §1).

## 7. Riesgos y decisiones

- **D1 · Levenshtein ≤ 1 con ≥ 5 caracteres, no `difflib.ratio`.** Las dos son stdlib; la
  distancia ya existe (F-062), es explicable en una nota («una letra») y no depende de la longitud
  de forma implícita (ratio 0,857 para 7 letras con un error, 0,8 para 5). ≥ 5 evita aproximar
  siglas y números («2000»/«2001»); ≤ 1 cubre la letra mal leída de la incidencia y del corpus.
- **D2 · Sin tratamiento aparte del paréntesis.** Con la puntuación como separador el nombre
  comercial ya es una palabra del candidato, y la contención/dirección casa «FEYMACO» con él
  (§5). Un tratamiento aparte añadía variantes y mutantes sin caso que lo pida.
- **D3 · Se conserva la subcadena de hoy** (R5): «mat» casa con «materiales» y el empate de la 0720
  de F-062 sigue igual (su fixture lo fija). Quitarla rompería F-062, que el humano dio por buena
  (2026-10-08: «la comparación que hace actualmente está bien»). De los 4 casos de la «opción B»
  de F-062 (`CASOS_OPCION_B`), 3 siguen a 1; solo «S.L.» cae a 0, que es justo la causa de la
  incidencia (una forma jurídica que casa con cualquiera): P0.
- **D4 · Empate ⇒ paso por puntos, no revisión directa.** El paso por puntos ya tiene mínimo y
  margen (3 y 2 puntos) y solo decide si la familia separa a los empatados, con origen
  `det_familia_obra` y aviso (sv4 penaliza la confianza). Coherente con el selector de contratos.
  Alternativa descartada: revisión directa en todo empate (perdería deducciones con familia
  inequívoca). Es la P6 del informe.
- **D5 · Revisión explícita en el empate (R11).** La confianza del documento se calcula antes del
  resolver: sin el motivo, un albarán sin CIF por empate podía no ir a revisión.
- **D6 · Paso 2 sin nota (R14).** Su nota sustituiría (mismo prefijo) a la del paso 1, que es la
  útil (candidatos con contrato en la obra). Un empate global de verdad («HORMIGONES») no aporta
  lista utilizable entre 3.543.
- **D7 · Margen 0,25 inclusivo.** Una palabra de diferencia en nombres de hasta 4 palabras. Con
  5+ palabras y una distinta, a revisión (seguro). Más fino: P2.
- **D8 · sv3 y no comun (P1).** El único consumidor es sv3; la propuesta de sv4 es JavaScript en
  el navegador y no puede importar Python. Meterlo en comun obligaría a reconstruir imágenes que no
  lo usan. Se moverá cuando lo pida F-055 (sv2) o un endpoint de sv4.
- **Riesgo · más empates ⇒ más revisión.** Nombres genéricos que hoy «ganaba el primero» quedarán
  sin CIF y a revisión. Es el efecto buscado: un CIF equivocado con contrato equivocado es peor
  que un hueco visible. La subcadena y la aproximación solo SUBEN similitudes (salvo quitar formas
  jurídicas y palabras vacías), así que no se pierden aciertos claros (§5: 0 de 23 perdidos).
- **Riesgo · `«del»` deja de contar.** Hoy «del» (3 letras) sumaba; ahora es palabra vacía. Ningún
  test lo usa como única coincidencia (tabla del informe §3).

## 8. Coordinación con otras ramas

- `feature/F-049-partida-de-la-lista` toca el constructor y `_resolve_obra` del mismo fichero
  (parámetro `canonizar`): conflicto textual trivial en la firma del constructor.
- `harness/features.json`: F-064, F-071 y F-072 se dan de alta en sus ramas al final del array;
  la fusión tendrá el conflicto habitual de cierre del array.
- F-063 (`fixture_f063`) usa una razón de FEYMACO sin «(FEYMACO)»: no se toca; la real va en
  `fixture_f073`.
