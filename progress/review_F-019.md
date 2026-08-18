<!-- progress/review_F-019.md -->
# F-019 · Informe de review

**Feature**: Importe de línea: manda el unitario leído; el importe solo se
despeja si faltan campos.
**Rama revisada**: `feature/F-019-importe-unitario-manda` (11 commits sobre
`dev` = `cd904cd`).
**Spec**: `specs/F-019-importe-unitario-manda/` (requirements, design, tasks).
**Informe del implementer**: `progress/impl_F-019.md`.
**Diagnóstico de origen**: `progress/prueba_local_feymaco_20260818.md`.

## Veredicto

**CHANGES_REQUESTED** — por UN solo punto, concreto y barato: el requisito
**R18** (albarán Feymaco **2.139.643**, total **19,41 €**) no tiene ni un test
automático, y la justificación que lo excusa («solo se conoce el total») la
desmiente el propio informe del implementer, que sí publica la composición de
la línea. Detalle y remedio exacto en «Cambios requeridos».

Todo lo demás está verificado y en verde. El fondo técnico de la feature —la
corrección de sv5, la precedencia de sv6, la protección contra partidas
alzadas, la campaña de mutación y la puerta de rutas sensibles— **se sostiene
punto por punto contra el diff real**, no contra el resumen. Es un round trip
de un test, no una reelaboración.

## Nivel de rigor

`rigor: "critico"` declarado en `harness/features.json` (comprobado leyendo el
fichero, no el informe). Exige, sobre `estandar`: fase RED en los requisitos
centrales, cobertura de las líneas cambiadas ≥ 80 %, campaña de mutación con
**cero supervivientes** salvo justificación escrita, y verificaciones
`MANUAL (humano)` listadas con su comando exacto.

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` → **ENTORNO LISTO**, exit 0. Ejecutado por el
      reviewer tal cual. Suite raíz **248 passed** en 64,36 s. Puertas:
      `[OK] PUERTA COBERTURA: 100.0% de 5 líneas cambiadas (5/5, umbral 80%,
      nivel critico)`; `[AVISO] PUERTA RUTAS SENSIBLES` (ver C4 ter).
      Los avisos de `ruff` (1067) son deuda previa declarada y no bloquean;
      los avisos de sv1/sv4/infra sin tests son previos a esta feature.
- [x] Existen los ficheros obligatorios del arnés.

Suites de servicio re-ejecutadas a mano por el reviewer (init.sh las sirvió de
caché): sv5 **9 passed** en 0,46 s; sv6 **37 passed** en 0,07 s.

## C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `F-019`.
- [x] Rama actual `feature/F-019-importe-unitario-manda`, la de la feature.
- [x] `progress/current.md` describe la sesión activa; el bloque «Pendientes
      del humano (arrastrados)» está etiquetado como tal, no es resto.
- [x] No hay features `done` nuevas: nada que exigir en `history.md`.

## C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal**: el cambio de sv5 vive en `infrastructure/database/`
      (adaptador, donde toca) y el de sv6 en `application/services/`
      (`PriceReconciler` sigue siendo una clase pura, sin IO). El único
      fichero de `domain/` tocado (`valuation_envelope.py`) cambia **solo
      comentarios** — verificado en el diff, ni un campo, ni un tipo, ni un
      default (esto es lo que hace cierto R21 por construcción).
- [x] **Primera línea con ruta relativa** en los 6 ficheros nuevos, con el
      patrón por servicio ya vigente en el repo (`# tests/conftest.py`, igual
      que `services/albaranes-api/tests/conftest.py`).
- [x] Sin `print()` de debug, sin TODO/FIXME reales (los dos hits del grep son
      la palabra «TODOS» en prosa castellana), sin secretos, sin dependencias
      nuevas: los tests solo usan `pytest`, `sqlalchemy` y `yaml`, ya en el
      árbol.
- [x] **Reglas de dominio**: se trabaja sobre `albaran_lines_merge` (nunca
      raw); no hay cambio de schema que obligue a listar lectores; la fórmula
      canónica queda escrita en `docs/ARCHITECTURE.md` regla 13 y no se mezcla
      ninguna unidad sin pasar por el conversor de sv6 (no se tocó).
- [x] **Límite de servicio**: sv5 sigue construyendo el contexto y sv6
      decidiendo precio e importe. No se mueve lógica ni se duplica nada que
      debiera vivir en `albaranes-comun`.

## C3 bis — Documentos de fuera

**N/A justificado**: el diff no añade ni modifica ningún fichero bajo
`docs/referencia/` (comprobado con `git diff dev...HEAD --stat`: los 18
ficheros tocados son código, tests, specs, `progress/` y documentación
normativa de servicio). No hay PDF ni ofimática en el árbol ni en el
histórico de la rama. No procede barrido de datos sensibles.

## C4 — La verificación es real

- [x] Los unit tests **no tocan red ni BBDD**: sv6 construye DTOs a mano sobre
      dos clases puras; sv5 ejecuta el SQL de producción contra
      `create_engine("sqlite://")` con la tabla creada al vuelo; el test de
      contrato de la raíz lee ficheros como texto y no importa paquetes de
      sv5/sv6 (evita la colisión de `application`/`domain` homónimos).
- [x] Verificaciones `MANUAL (humano)` listadas en `progress/current.md`
      (los cuatro puntos) con el guion de comandos y SQL exactos en
      `progress/impl_F-019.md` §T10, pendientes del humano.
- [ ] **Cada requisito EARS con >= 1 test trazable**: se cumple para R1-R17 y
      R19-R22; **falla para R18** (ver «Cambios requeridos»).

### Cobertura requisito → test (verificada abriendo cada test, no el informe)

| R | Test(s) que lo cubre(n) | Fichero |
|---|---|---|
| R1 | `test_f019_r1_el_prompt_de_ia1_define_precio_neto_como_importe`, `..._define_precio_como_unitario` | `tests/test_f019_r1_r2_r3_semantica_precio_neto.py` |
| R2 | `test_f019_r2_la_clave_del_prompt_de_ia1_sigue_siendo_la_vigilada`, `..._no_multiplica_el_coalesce_por_cantidad`, `..._usa_la_formula_canonica` | ídem |
| R3 | `test_f019_r3_architecture_documenta_la_semantica_de_precio_neto` (+ `sv5.md` §9, `sv6.md` §5.3/§6.1/§6.4 y el DTO, verificados en el diff) | ídem |
| R4 | `test_f019_r4_importe_leido_no_se_multiplica_por_la_cantidad`, `test_f019_r4_el_resto_de_columnas_del_select_no_cambian` | sv5 `test_f019_r4_r7_importe_select.py` |
| R5 | `test_f019_r5_sin_precio_neto_se_deriva_del_precio_con_descuento`, `..._ni_descuento_usa_precio_por_cantidad`, `..._ni_precio_pero_con_cantidad_nula` | ídem |
| R6 | `test_f019_r6_sin_precio_ni_precio_neto_el_importe_es_nulo` | ídem |
| R7 | `test_f019_r7_precio_neto_sin_cantidad_conserva_el_importe_leido`, `..._sin_precio_unitario_tambien_manda` | ídem |
| R8 | 4 tests `test_f019_r8_*` (con importe, sin importe, sin cantidad, `line_already_valued`) | sv6 `test_f019_r8_r15_precedencia.py` |
| R9 | `test_f019_r9_sin_declarado_se_despeja_el_unitario_del_importe`, `..._y_sin_descuento_el_despeje_es_directo` | ídem |
| R10 | 4 tests `test_f019_r10_*` (gana el declarado + mismatch, vía a revisión, dentro y fuera de tolerancia) | ídem |
| R11 | 5 tests `test_f019_r11_*` (1a+1b media, discrepan, solo 1a, solo 1b, nada) | ídem |
| R12 | 3 tests `test_f019_r12_*` (importe leído, unitario declarado, y el 960.000 € exacto) | ídem |
| R13 | 3 tests `test_f019_r13_*` | ídem |
| R14 | 4 tests `test_f019_r14_*` | ídem |
| R15 | 3 tests `test_f019_r15_*` (incl. `descuento_fuera_de_rango_ignorado:150.0` del `ImporteCalculator`) | ídem |
| R16 | `test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco` (sv5) + `test_f019_r16_cada_linea_conserva_su_unitario_y_su_importe` (5 casos parametrizados) + `test_f019_r16_el_total_del_albaran_es_13966_euros` + contraprueba con el importe inflado | sv5 + sv6 `test_f019_r16_r17_feymaco.py` |
| R17 | `test_f019_r17_el_derivado_confirma_al_declarado_sin_marcar_revision`, `test_f019_r17_ninguna_linea_queda_marcada_por_mismatch` | sv6 |
| **R18** | **NINGUNO** | — |
| R19-R21 | Sin código; R21 garantizado por construcción (el envelope solo cambia comentarios, verificado en el diff) | — |
| R22 | T9, exigencia `aviso`; ver C4 ter | — |

## C4 bis — El rigor declarado se cumple

- [x] **Rigor declarado**: `critico` en `harness/features.json`.
- [x] **Fase RED**: el informe trae **tres trazas reales pegadas**, no una
      frase. RED 1 (sv5): `4 failed, 5 passed`, con
      `assert 3800.5199999999995 == 35.19` y el `None == 35.19` de R7. RED 2
      (sv6): `5 failed, 23 passed`, con el `58.65` inventado. RED 3 (R3):
      `1 failed, 5 passed`. Las tres son salidas de pytest con fichero, línea
      y valores obtenidos: cumplen la exigencia.
- [x] **Cobertura**: `[OK] PUERTA COBERTURA: 100.0% de 5 líneas cambiadas
      cubiertas (5/5, umbral 80%, nivel critico)`, leído de la ejecución
      propia de `init.sh`.
- [x] **Mutación, verificada de forma INDEPENDIENTE** (no creída del informe):

  1. **Alcance recalculado** con `harness.alcance.alcance_de_feature("F-019")`:
     3 ficheros, **64 + 63 + 17 = 144 líneas**, origen `rama`, ref_diff
     `cd904cd..feature/F-019-importe-unitario-manda`. Coincide exactamente con
     la tabla del informe.
  2. **Mutantes recalculados** con `harness.mutacion.generar_mutantes`
     (cálculo puro): **4**, todos en `price_reconciler.py`, con el mismo
     operador y el mismo texto original→mutado que declara la campaña:
     `L135 logico and→or`, `L135 not (elimina el not)`,
     `L166 aritmetico + → -`, `L175 aritmetico + → -`.
  3. **Campaña re-ejecutada** por el reviewer: `4 mutantes evaluados, 4
     muertos, 0 supervivientes, 0 timeouts en 3.9 s`. El informe regenerado
     era idéntico salvo la marca de tiempo; se restauró el original con
     `git checkout --` para no ensuciar la rama (`git status` limpio).
  4. **Prueba de control del cero** (los dos ficheros que aportan 0 mutantes):
     se ejecutó `generar_mutantes` sobre el fichero ENTERO, ignorando la
     exclusión de alcance. `sqlalchemy_valuation_context_repository.py` da
     **7 mutantes** fuera del diff (L224, L236, L244, L283, L299×2, L345) y
     `valuation_envelope.py` da **1** (L64). Es decir: **el generador
     funciona sobre esos ficheros**; el cero dentro del alcance es legítimo,
     porque las líneas del diff son comentarios (sv5 61-105, envelope
     109-125) y el bloque `text("""…""")` del SQL (sv5 134-153), donde un
     mutador AST de Python no tiene nada que morder. La justificación del
     implementer **se sostiene y es reproducible**.

- [x] **Cero supervivientes** (nivel `critico`), sin ninguna sección en
      `PENDIENTE`.
- [x] **Sección «Evidencias»** presente con los cuatro números: tests
      (248 + 9 + 37, 0 fallos), cobertura (100 %, 5/5), mutantes
      (4 generados / 0 supervivientes), tiempo (65,30 s + 0,79 s + 0,12 s).
- [x] Ningún punto de este bloque marcado N/A sin justificación escrita.

**Sobre el SQL sin cobertura de mutación** (el punto que más apretar): es
cierto que la corrección de sv5 —el corazón del bug— queda fuera del alcance
del mutador. **No queda por ello sin vigilancia**, y esto sí lo compensa el
implementer con dos redes que el reviewer ha comprobado que existen y que
muerden:

1. Los tests de sv5 **importan `_SQL_ALBARAN_LINES` del módulo de producción**
   y lo ejecutan contra SQLite. Un test que copiara el SQL a mano habría
   pasado con el bug dentro; este no. Es el equivalente funcional de matar el
   mutante: si alguien devuelve el `cantidad *` a su sitio, cuatro tests caen
   con el `3800.52` en la traza.
2. `test_f019_r2_el_select_de_sv5_no_multiplica_el_coalesce_por_cantidad`
   vigila el texto del SQL **con los comentarios eliminados** (`_sql_sin_comentarios`),
   para que la prosa explicativa no dé verde falso. Detalle bien pensado.

Conclusión: la justificación del número bajo de mutantes es legítima y el SQL
corregido **no** queda descubierto.

## C4 ter — Rutas sensibles

La puerta señaló **2 rutas** tocadas (`price_reconciler.py` — redes
deterministas de sv6; `valuation_envelope.py` — envelope DTO), exigencia
declarada **`aviso`**.

- [x] **Existe** el informe declarado: `progress/evals_F-019.md`.
- [ ] **No cumple** `exige_lineas`: trae `MODO: determinista`,
      `FASES: IA3,IA4,E2E` y `VEREDICTO: NO_EVALUABLE`, frente a las
      `MODO: completa` / `FASES: IA1,IA2,IA3,IA4,E2E` / `VEREDICTO: VERDE`
      que exige `harness/rutas_sensibles.json`. Leído del fichero.
- [x] **Es FRESCO**: se commitea en `7e6c210` (T9) y el último commit que tocó
      una ruta sensible es `e4fc01a` (T7), anterior en la rama. El informe se
      generó con HEAD `d9c52e6`, también posterior a T7. Comprobado con
      `git log dev..HEAD -- <rutas>`.
- [x] **Motivo por escrito** (exigencia `aviso`): recogido aquí y
      **verificado de forma independiente**, no aceptado de palabra:
  - `python -m evals.runner --con-llm --feature F-019`, relanzado por el
    reviewer, responde literalmente `no se puede lanzar la pasada completa:
    faltan en el entorno GEMINI_API_KEY, OPENAI_API_KEY. No se ha consumido
    ningún caso.` Son secretos: `CLAUDE.md` prohíbe escribirlos en el repo y
    el implementer hizo bien en NO improvisar una vía alternativa.
  - **Y aunque las hubiera, la pasada daría `NO_EVALUABLE` igual**:
    `evals/fixtures/inputs/` contiene un único `_indice.json` con
    `"casos": []`. Comprobado leyendo el fichero. Es exactamente el supuesto
    que R22 anticipa y por el que la exigencia arranca en `aviso` (D5 de
    F-011).
  - Lo que sí ejecutó (la variante determinista) **no demuestra que el cambio
    de sv6 sea correcto** —ni pretende hacerlo— pero sí demuestra el motivo
    de fondo, que es lo que C4 ter pide por escrito. La corrección de sv6 la
    respaldan los 37 tests unitarios y la campaña de mutación, no los evals.

**Valoración del reviewer**: el motivo es legítimo y está probado. Con la
exigencia en `aviso`, **esto no bloquea**. El pendiente real sigue siendo del
humano: rellenar `evals/ground_truth/` para poder subir la puerta a `bloqueo`.

## C5 — La sesión se cerró bien

- [x] Un commit por tarea, con el formato `F-019 Tn: ...`: 11 commits, T1-T11
      sin saltos ni mezclas.
- [x] **T10 queda `[ ]` y está bien que quede así**: es una verificación
      MANUAL del humano; marcarla `[x]` sería falso. Sigue la convención de
      F-002. El resto (T1-T9, T11) está `[x]`.
- [x] Árbol limpio: `git status --porcelain` sin salida, sin ficheros
      temporales ni artefactos sueltos.
- [x] `features.json` refleja el estado real (`in_progress`, `rigor: critico`,
      `branch` correcta).

## Los puntos que el líder pidió apretar — resultado

### 1. La corrección de sv5 · CORRECTA

El `cantidad *` sale de fuera y entra en la segunda rama:

```sql
COALESCE(
    precio_neto,
    cantidad * precio * (1 - COALESCE(descuento, 0) / 100.0)
) AS importe_albaran,
```

- La **cascada del `COALESCE` no se rompe**: la rama derivada conserva la
  fórmula del «FIX 2 (jul 2026)» byte a byte, incluido el
  `COALESCE(descuento, 0)` que hace funcionar los albaranes sin descuento
  (R5, dos tests).
- **`precio_neto` presente y sin cantidad → devuelve el importe leído**, no
  NULL (R7): el `COALESCE` resuelve por la primera rama y la cantidad ausente
  ya no envenena el producto. Test `test_f019_r7_precio_neto_sin_cantidad_...`,
  que en RED daba `None == 35.19`.
- Sin `precio_neto` ni `precio` sigue saliendo **NULL** (R6, caso hormigón):
  test propio.
- El comentario que mentía («precio_neto es el unitario NETO») se borra y se
  sustituye por la semántica correcta con su motivo y su fecha. Bien hecho:
  ese comentario era parte del bug.

### 2. La precedencia de sv6 · CORRECTA, leída en el código

Verificado sobre `price_reconciler.py:133-176`, no sobre el informe:

- **Bloque 1** `if declarado is not None:` → devuelve SIEMPRE
  `final_price=float(declarado)`, `source="albaran_declared"`, en los dos
  caminos (coincide y discrepa). Con cantidad + precio + descuento leídos,
  manda el unitario leído. Es la regla del humano.
- **Bloque 2** `if derivado_bruto is not None:` → solo se alcanza cuando
  `declarado is None`, es decir cuando falta el unitario. El importe **solo se
  despeja cuando faltan esos campos**. Es la segunda mitad de la regla.
- El `derivado_bruto` se calcula **antes** de decidir (línea 126), lo que
  conserva los motivos de auditoría de R13/R14 aunque gane el bloque 1. Es una
  decisión del implementer, está anotada en su informe, y el reviewer la
  suscribe: calcularlo dentro del bloque 2 habría enmudecido la auditoría
  justo en las líneas mejor leídas.
- `_no_cero`, `_derivar_bruto` y `_match` **intactos**, como exigía el diseño
  (diff verificado). La firma de `reconcile` no cambia (R21).

### 3. La protección contra partidas alzadas · NO se ha perdido

- **En el código**: los bloques 1 y 2 devuelven antes de llegar al bloque 3.
  Ninguna ruta con valor leído del albarán alcanza el fallback de contrato.
  El docstring conserva el párrafo original de jul 2026 palabra por palabra y
  añade el de F-019 encima, dejando explícito que lo que cambia es la
  precedencia **interna** entre dos valores del propio albarán.
- **En los tests**: hay **tres** de regresión propios, no uno:
  `test_f019_r12_partida_alzada_no_pisa_el_importe_leido` (18,84 € leídos
  frente a PA de 8.000 €, gana 18,84), `..._no_pisa_el_unitario_declarado`
  (la misma protección por la rama NUEVA, que es justo lo que había que
  demostrar) y `test_f019_r12_los_960000_euros_no_vuelven`, que encadena
  `PriceReconciler` + `ImporteCalculator` y afirma
  `importe_calculado != 960000.0` con el número exacto del incidente.
- Los cinco casos de Feymaco pasan además `precio_1a=4.000 €/ud` a propósito
  como ruido, y afirman que ese precio no entra por ningún lado.

Verificado también que las líneas **sintéticas** no se ven afectadas:
`valuation_builder._build_synthetic_line` llama a `reconcile` con
`precio_albaran_declarado=None`, `cantidad_albaran=None` e
`importe_albaran=None`, así que siguen cayendo al bloque 3 igual que antes.

### 4. C4 bis (mutación) · Verificado, y la justificación se sostiene

Ver C4 bis: recuento independiente idéntico (144 líneas, 4 mutantes, mismos
operadores y textos), campaña re-ejecutada (4/4 muertos) y prueba de control
del cero superada (el generador sí produce mutantes en esos ficheros fuera del
alcance: 7 y 1). El SQL corregido no queda descubierto porque los tests
ejecutan el SQL real del módulo de producción y hay un test de texto que
vigila la reaparición de `cantidad * COALESCE(`.

### 5. C4 ter (rutas sensibles) · Motivo legítimo, no bloquea

Ver C4 ter: las dos causas (claves ausentes y ground truth vacío) están
comprobadas de primera mano por el reviewer. Exigencia `aviso`.

### 6. R16/R17/R18 · Los números, uno a uno

- **R16 · cubierto en los dos tramos.** sv5:
  `test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco` inserta las 5 filas
  reales y afirma 35,19 / 20,53 / 55,63 / 13,19 / 15,12 y el total
  **139,66 €** (`abs=0.005`). sv6: las 5 líneas parametrizadas, cada una con
  `final_price == precio declarado` y `source == "albaran_declared"`, más
  `test_f019_r16_el_total_del_albaran_es_13966_euros`, que suma y compara
  contra 139,66 y contra el 6.238,14 inflado. Hay incluso contraprueba: si sv5
  volviera a inflar el importe, la línea saldría `mismatch` y el unitario
  seguiría siendo 0,543.
- **R17 · cubierto.** El test calcula el derivado
  `35,19 / (108 × 0,6) = 0,543055…` (`abs=1e-6`), confirma
  `agreement != "mismatch"` y exige el motivo
  `albaran_unitario_manda_derivado_coincide`. Un segundo test recorre las
  cinco líneas y afirma que ninguna arrastra
  `unitario_declarado_vs_derivado_mismatch` — el equivalente unitario del
  punto 3 de la verificación MANUAL.
- **R18 · NO cubierto.** Ver «Cambios requeridos».

### 7. Decisiones cerradas por el humano · TODAS respetadas

| Decisión | Estado | Cómo se verificó |
|---|---|---|
| El desacuerdo viaja como `precio_unitario_agreement="mismatch"` sin tocar `valuation_builder.py` | **Respetada** | `valuation_builder.py` no aparece en el diff; `review_required` lo lee en la línea 1116 (`or reconciliation.agreement == "mismatch"`) |
| No hay backfill | **Respetada** | No hay script nuevo en el diff; R20 queda documentado como decisión del humano en `current.md` y en §T10 |
| sv2 no se toca | **Respetada** | Ningún fichero de `services/albaranes-api/` en el diff; el prompt se vigila con un test de contrato, no se modifica |
| El campo con nombre no ambiguo queda para F-003 | **Respetada** | Documentado en spec e informe; el test de contrato lleva cabecera explícita para quien venga a cambiarlo en F-003 |

Además queda anotado en `current.md` el aviso de que **F-003 R4 hay que
reescribirla antes de arrancarla** (manda conservar la derivación que F-019
acaba de corregir). Bien visto.

## Cambios requeridos

**1. R18 sin ningún test automático (`services/albaran-valoracion-persist/tests/test_f019_r16_r17_feymaco.py` y `services/albaran-valoracion-api/tests/test_f019_r4_r7_importe_select.py`).**

`grep` sobre todos los `.py` del repo: **cero apariciones** de `19.41`,
`970.50`, `2139643` o `0.647`. El segundo albarán del incidente —el que abre
el diagnóstico del 18-08 y da nombre a la mitad de la feature— no tiene red de
seguridad automática de ninguna clase.

La excusa del spec («*Solo se conoce el total: verificación MANUAL*») **la
desmiente el propio informe del implementer**, que en §T10 escribe: «*De este
albarán solo se conoce el total: 50 ud × 0,647 con 40 % → 19,41 €*». O se
conoce la composición —y entonces es testeable exactamente igual que R16— o no
se conoce, y entonces no debería afirmarse como dato en el guion que el humano
va a usar para validar. Las dos cosas a la vez, no.

Y la composición **sí es deducible con certeza aritmética**, que es de donde
sale: bajo el bug el importe se multiplicaba por la cantidad, y
`970,50 / 19,41 = 50` exacto ⇒ línea única de cantidad 50; de ahí
`19,41 / (50 × 0,6) = 0,647` exacto. Es la misma calidad de dato que la
fixture de las cinco líneas del 2.137.569.

**Qué hacer** (dos tests pequeños, mismo patrón que los que ya existen):

- En la suite de **sv5**: una fila `cantidad=50, precio=0.647, descuento=40,
  precio_neto=19.41` ejecutada contra `_SQL_ALBARAN_LINES` ⇒
  `importe_albaran == 19.41` y `!= 970.50`.
- En la suite de **sv6**: `reconcile(precio_albaran_declarado=0.647,
  cantidad_albaran=50, importe_albaran=19.41, descuento_pct=40, precio_1a=<ruido>)`
  ⇒ `final_price == 0.647`, `source == "albaran_declared"`, y encadenando
  `ImporteCalculator` ⇒ `importe_calculado == 19.41` y `!= 970.50`.
- Nombrarlos `test_f019_r18_*` para que la trazabilidad los recoja, y dejar en
  el docstring que los números de línea son una **reconstrucción aritmética**
  a partir del total conocido (`970,50 / 19,41 = 50`), no una transcripción
  del PDF. Con eso el requisito queda cubierto «hasta donde llegue el test» y
  el guion MANUAL deja de afirmar como leído lo que es deducido.
- Ajustar en consecuencia la tabla de trazabilidad de `tasks.md` (R18 pasa a
  T1/T6 + T10) y la nota de R18 en `requirements.md`, para que la spec no
  siga diciendo que R18 es solo manual.

T10 (la verificación MANUAL del humano) **se mantiene igual**: el test no la
sustituye, la acompaña.

## Observaciones no bloqueantes

1. **`test_f019_r16_cada_linea_conserva_su_unitario_y_su_importe` es en parte
   tautológico en su mitad del importe**: se pasa `importe_albaran_declarado =
   importe_efectivo` y el `ImporteCalculator` prefiere el declarado, así que
   la igualdad final está medio garantizada por la entrada. No es un fallo —el
   calculado (`108 × 0,543 × 0,6 = 35,1864`) sí se computa y sí se contrasta
   contra el declarado dentro de `IMPORTE_TOLERANCE_PCT`, y la parte que de
   verdad se juega esta feature (`final_price == declarado`,
   `source == "albaran_declared"`) sí es sustantiva. Solo conviene saberlo
   para no leer ese test como más fuerte de lo que es.
2. **La descripción de `price_tolerance_pct` en
   `services/albaran-valoracion-persist/config/settings.py:48` sigue diciendo
   «para considerar que precio 1a y 1b coinciden»**, cuando desde F-019 esa
   tolerancia gobierna además el contraste declarado-vs-derivado, que es el
   que manda una línea a revisión. Una frase. (Ya se usaba para eso antes de
   F-019, así que no es regresión de esta feature.)
3. **`TOLERANCIA_PRECIO_PCT = 2.0` y `TOLERANCIA_IMPORTE_PCT = 5.0` están
   fijados a mano en el `conftest.py` de sv6.** Comprobado que coinciden con
   los defaults reales de `config/settings.py` (2.0 y 5.0). Es la decisión
   correcta —no depender de ningún `.env`— pero si alguien cambia el default
   nada avisa de que el conftest ha quedado desfasado. Un test que compare
   ambos valores costaría tres líneas.

## Propuesta de mejora del protocolo (no aplicada)

Esta review ha necesitado un paso que `CHECKPOINTS.md` no pide explícitamente
y que ha resultado ser el más informativo de C4 bis: cuando la campaña de
mutación da un número **bajo pero no cero**, el protocolo actual solo obliga a
la prueba de control si el total es **cero**. Aquí el total era 4, pero **dos
de los tres ficheros del alcance aportaban cero cada uno**, y es ahí donde
estaba el fichero que contiene el bug corregido.

**Propuesta para el humano**: extender la prueba de control del cero en el
punto 4 de C4 bis / `.claude/agents/reviewer.md` de «si la campaña declara
cero mutantes» a «si la campaña declara cero mutantes **en cualquier fichero
del alcance**». Es la misma comprobación, cuesta un `generar_mutantes` sobre
el fichero entero, y es la única forma de distinguir «no había nada que mutar»
de «el mutador no llega a esta clase de código» — que es información que el
reviewer necesita para juzgar si hace falta exigir otra red (aquí: ejecutar el
SQL real de producción en el test). Como el bloque es genérico, si se acepta
debería portarse a `arnes-base`.
