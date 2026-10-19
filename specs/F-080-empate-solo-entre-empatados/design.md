# F-080 · Tras un empate por nombre, la familia solo elige entre los empatados — diseño

Solo **sv3-persistencia**, y dentro de sv3 solo `header_resolver_service.py`. Sin DDL, sin
`ruesma_comun`, sin cambios en mensajes ni en lo que sv3 expone o consume (no se toca
`azure-apps/albaranes.md`). Despliegue: solo sv3, después del de F-073 (T12 de F-073).

## 1. Diagnóstico y medición (dev `bee817d`, solo dobles, sin red ni BBDD)

`services/albaranes-persistencia/application/services/header_resolver_service.py`,
`_resolver_por_obra_y_familia`:

- El atajo por nombre (l. 1003) llama a `elegir_por_nombre`. Si no elige, el paso por puntos
  (l. 1014–1042) ordena **todos** los `candidatos` de la obra y toma `candidatos[0]` si tiene ≥ 3
  puntos y saca 2 al segundo. No mira `eleccion.empatados`: solo lo usa después (l. 1053) para
  decidir entre la nota de R11 y la nota «no deducible».
- Puntos: `round(4 × similitud) + 3 × familias comunes`, −2 si las dos partes tienen familias y no
  comparten ninguna. Un ajeno con similitud 0 y dos familias comunes saca 6, y un empatado con
  similitud 1 y otra familia, 2: el ajeno gana con margen (H4).

Prototipo en el scratchpad del spec-author: un plugin de pytest que sustituye el método por
dos variantes, sin tocar el repo. Casos (puntos entre paréntesis):

| Caso | Candidatos | Hoy | (a) solo entre empatados | (b) el ganador debe ser empatado |
|---|---|---|---|---|
| H4 | SUR (2), NORTE (2) empatados; ARIDOS (6) | ARIDOS, `det_familia_obra` | revisión R11 | revisión R11 |
| P1 | SUR (7), NORTE (2) empatados; ARIDOS (9, hormigón+mortero+acero) | ARIDOS | **SUR** | **revisión R11** |
| Ajeno cerca | SUR (7), NORTE (2); ARIDOS (6) | revisión R11 (margen 1) | **SUR** | revisión R11 |
| Ajeno lejos | SUR (7), NORTE (2); ARIDOS (3) | SUR | SUR | SUR |
| Penalización | SUR sin familias (4), NORTE gasóleo (2) | SUR | SUR | SUR |

Con las dos variantes, la suite completa de sv3 da **1496 passed** (la misma de `dev`): ningún test
existente fija el comportamiento de H4, así que R13 no exige cambiar expectativas.

Datos de los casos (los fixtures de los tests). Leído «HORMIGONES»; B1 «HORMIGONES DEL SUR, S.L.»,
B2 «HORMIGONES DEL NORTE, S.L.» (contrato «GASOLEO A» en todos), B9 «ARIDOS PEPE, S.L.»:
- H4: líneas «HORMIGON HA-25» y «MORTERO M-5»; B1 «GASOLEO A»; B9 «HORMIGON HA-25 MORTERO M-5».
- P1: las de H4 y «ACERO CORRUGADO B500S»; B1 «HORMIGON HA-25»; B9 «HORMIGON HA-25 MORTERO M-5
  ACERO CORRUGADO».
- Ajeno cerca: líneas de H4; B1 «HORMIGON HA-25»; B9 «HORMIGON HA-25 MORTERO M-5».
- Ajeno lejos: línea «HORMIGON HA-25»; B1 y B9 «HORMIGON HA-25».
- Penalización: línea «HORMIGON HA-25»; B1 sin texto de contrato; sin B9.

**Nombre solo no separa a los empatados**: dos empatados difieren en similitud < 0,25, y
`round(4·s)` no puede abrir 2 puntos con esa diferencia (con 0,875 frente a 0,625 ya no es empate:
el margen es inclusivo). Solo la familia o la penalización separan.

## 2. Preguntas para el humano (PARADA 1) — RESUELTAS el 2026-10-19

**Decisión del humano:** P1 = **(b)** (la carrera de hoy, y el ganador tiene que ser empatado); P2 y P3 según la
recomendación de abajo (el líder las anunció como opción por defecto y el humano no las cambió). R2 y R4 quedan como
están; D1 confirmada.


**P1 · ¿Contra quién compite el empatado?** (R2, R4.) La decisión dice «la familia solo puede
elegir entre los empatados», y admite dos lecturas que se separan en los casos P1 y «ajeno cerca»
de §1:
- **(a) Carrera solo entre empatados.** Los ajenos desaparecen del paso por puntos; mínimo 3 y
  margen 2 frente al segundo **empatado**. Puede deducir donde hoy va a revisión («ajeno cerca»).
- **(b) La carrera de hoy, y el ganador tiene que ser empatado.** Mismo paso por puntos sobre toda
  la obra; si gana un ajeno, revisión con R11.
- **Recomendación: (b).** Es monótona: F-080 solo convierte deducciones de hoy en revisión, nunca
  crea una nueva, y «fuera de ese caso, todo sigue como hoy» se cumple también dentro del empate.
  Un ajeno con más familia que el empatado es una señal real de duda: un albarán de hormigón,
  mortero y acero de un «HORMIGONES …» cuyo contrato es de hormigón puede ser de ARIDOS. Además, el
  cambio es más pequeño (una comprobación de pertenencia) y la nota «entre N proveedor(es) con
  contrato en la obra» sigue siendo cierta. Con (a), R2 pasaría a «la carrera es entre empatados» y
  R4 esperaría SUR; el resto no cambia.

**P2 · ¿Quiénes son «los empatados»?** Recomendación: los de `EleccionPorNombre.empatados` (los que
quedan a menos del margen 0,25 del mejor, agrupados por CIF normalizado), el mismo conjunto que
lista la nota de R11, ya aprobada. Alternativa descartada: solo los de similitud idéntica al mejor.
Con ella, el que queda a 0,1 del mejor no elegiría por nombre (no saca el margen), pero tampoco
podría salir por familia: quedaría en tierra de nadie.

**P3 · Si la familia deja dos o más empatados igualados arriba** (o separa a unos empatados de
otros sin decidir). Recomendación: R11 de F-073 sin cambios. Revisión con la nota de **todos** los
empatados por nombre, ordenados por puntos y CIF (los que la familia favorece salen primero, y el
tope `nota_max_candidatos` se aplica igual). Es lo que ya hace hoy
(`test_f073_r11_nota_ordenada_por_puntos_y_cif_y_con_el_tope_de_candidatos`). Alternativa: listar
solo los igualados arriba; se descarta porque cambia R11 y su test.

## 3. Ficheros a crear

- `services/albaranes-persistencia/tests/test_f080_empate_solo_entre_empatados.py` — R1–R12 con
  dobles en memoria. Reutiliza `_paso1`, `_resumen`, `_RepoConLineas` y `_ClienteRed` importados de
  `test_f073_eleccion` (sin tocar ese fichero), y `pasada`/`resolver` de `f062_dobles`. Para R9, un
  `_ClienteRed` con `search_proveedores` que devuelve los tres de la obra (empate global). Nombres
  `test_f080_rN_…`.

## 4. Ficheros a modificar

- `services/albaranes-persistencia/application/services/header_resolver_service.py`:
  - Función pura de módulo, junto a `_clave_cif`:
    ```python
    def _es_empatado(cif: str | None, eleccion: EleccionPorNombre) -> bool:
        """F-080 · R1, R8: ``cif`` es uno de los empatados por nombre (clave
        de CIF normalizada, la de ``elegir_por_nombre``)."""
        clave = _clave_cif(cif)
        return any(_clave_cif(e.cif) == clave for e in eleccion.empatados)
    ```
  - `_resolver_por_obra_y_familia`, en el bloque de la decisión por puntos (variante (b)):
    calcular `decide = mejor.puntos >= _PUNTOS_MINIMOS and (mejor.puntos - segundo_puntos) >=
    _MARGEN_MINIMO` como hoy. Si `decide and eleccion.empatados and not _es_empatado(mejor.cif,
    eleccion)` ⇒ log de R6 y `decide = False`. Si `decide` ⇒ la rama de hoy, intacta (log
    «DEDUCIDO», nota, `ORIGEN_DET_FAMILIA_OBRA`). Si no ⇒ el código de hoy tal cual: log «NO
    deducido», y R11 (con `eleccion.empatados`, que en el caso ajeno siempre existe) o la nota «no
    deducible».
  - Log de R6, `logger.info`:
    `"%s proveedor NO deducido por familia+obra: el ganador por puntos %s (%s puntos) es AJENO al
    empate por nombre (%d empatados) obra=%s"`.
  - Docstring de la clase (paso 1, «si gana por familia»): una línea, «tras un empate por nombre,
    solo si el ganador es uno de los empatados (F-080)».
- `docs/ARCHITECTURE.md`, regla 24, viñeta «Empate» (R15). Cambia «siguen los puntos de nombre y
  familia sin cambios (si la familia separa, `det_familia_obra` con aviso)» por «siguen los puntos
  de nombre y familia sin cambios, pero el ganador solo se acepta si es uno de los empatados
  (F-080): si la familia lo separa, `det_familia_obra` con aviso; si gana un ajeno o nadie, va a
  revisión…». El resto de la viñeta sigue igual.

## 5. Ficheros que NO se tocan

- `application/services/similitud_proveedor.py` (`elegir_por_nombre`, `EleccionPorNombre`): ya da
  `empatados`; no hace falta el módulo puro (R14).
- `_resolve_proveedor` (paso 2), `_red_proveedor_por_cif`, `_candidato_claro`,
  `_descartar_cif_propio`, `_resolve_obra`, `_nota_empate_nombre`, `_log_eleccion`, constructor y
  constantes de puntos (R12, R14).
- `domain/models/header_resolution_models.py`: el motivo `proveedor_nombre_ambiguo` ya existe.
- `interface_adapters/composition.py`, `interface_adapters/api/app.py`, `config/settings.py`: sin
  parámetro ni variable nuevos.
- Tests de F-073 (`test_f073_*.py`), de F-052, F-062, F-063 y F-070: ninguna expectativa cambia (R13).
  `test_f073_r10_p6_…` sigue valiendo tal cual: allí el ganador (B1) es uno de los empatados.
- `services/albaranes-persistencia/sv3.md` y `azure-apps/`: no cambia lo que sv3 expone.

**Observación O1 (fuera de alcance, sin cambio).** Cuando el paso 1 acaba en R11, el paso 2 global
corre igual (F-073). Si un proveedor de fuera de la obra casa por nombre con margen sobre los
empatados, el paso 2 lo elige y retira la nota, pero el motivo `proveedor_nombre_ambiguo` queda.
No es «la familia elige», existe desde F-073 y R9 solo fija el caso de empate global. Si el humano
quiere cerrarlo, va en otra ficha.

**Lo ya deducido en producción.** Los albaranes que un ajeno ganó tras un empate (con F-073
desplegado) llevan `det_familia_obra` y el aviso «deducido AUTOMATICAMENTE»: ya están en la
penalización de confianza de sv4. Localizarlos exige leer producción: no lo hace esta feature.

## 6. Riesgos y decisiones

- **D1 · Variante (b)**, salvo que el humano elija (a) en P1 (§2).
- **D2 · Pertenencia por `_clave_cif`**, la misma de `elegir_por_nombre` y de la nota de R11. Así,
  una grafía distinta del mismo CIF no convierte a un empatado en ajeno (R8). El CIF que se escribe
  en el merge sigue siendo el de la fila ganadora, como hoy (R1).
- **D3 · La nota de `det_familia_obra` no cambia.** Con (b) la carrera sigue siendo entre todos los
  de la obra, y «entre N proveedor(es) con contrato en la obra» sigue siendo cierto. sv4 no lee ese
  texto: solo el origen (`albaranes-front/domain/services/confianza.py`).
- **D4 · Sin interruptor de vuelta atrás.** Como F-073 (P3): la vuelta atrás es la imagen anterior
  de sv3. Un interruptor duplicaría la rama y los mutantes, y el cambio solo manda más casos a
  revisión.
- **D5 · Sin tocar `similitud_proveedor.py`.** Una función `elegir_entre_empatados` pura allí
  movería lógica de puntos, que es del resolver, a un módulo de nombres.
- **Riesgo · más revisión.** Cada empate que hoy resolvía un ajeno va a revisión. Es el efecto
  buscado (un CIF equivocado con su contrato es peor que un hueco visible), y los empates por
  nombre ya son la minoría que F-073 deja sin elegir.
- **Riesgo · mutantes de la pertenencia.** `not _es_empatado` → `_es_empatado`, `==` → `!=` en la
  clave y `and eleccion.empatados` → `or`. Los matan R1 (empatado gana), R2/R3 (ajeno no gana), R8
  (grafía) y R10 (sin empate, el ajeno sí gana).

## 7. Coordinación con otras ramas

- **F-075** (`feature/F-075-importe-leido`, sv3): no toca `header_resolver_service.py` ni los
  tests de proveedor. Comparte `docs/ARCHITECTURE.md` (añade la regla 25 justo después de la 24
  que edita F-080: conflicto textual posible en el borde, trivial), `harness/features.json`,
  `BACKLOG.md` (generado) y `progress/current.md`. También toca `sv3.md`, que F-080 no toca.
- **F-049** (`feature/F-049-partida-de-la-lista`): toca el constructor y `_resolve_obra` del mismo
  `header_resolver_service.py`, y `docs/ARCHITECTURE.md`. F-080 no toca ninguno de los dos
  métodos. El cambio está en `_resolver_por_obra_y_familia` y en una función nueva junto a
  `_clave_cif`: sin solape de líneas.
- Despliegue: sv3 después de la T12 de F-073 (la imagen de F-080 lleva F-073 dentro).
