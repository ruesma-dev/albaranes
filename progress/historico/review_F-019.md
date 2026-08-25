<!-- progress/review_F-019.md -->
# F-019 · Informe de review

**Feature**: Importe de línea: manda el unitario leído; el importe solo se
despeja si faltan campos.
**Rama revisada**: `feature/F-019-importe-unitario-manda`.
**Spec**: `specs/F-019-importe-unitario-manda/` (requirements, design, tasks).
**Informe del implementer**: `progress/impl_F-019.md`.
**Diagnóstico de origen**: `progress/prueba_local_feymaco_20260818.md`.

> **VEREDICTO VIGENTE: APPROVED** (cuarta pasada, HEAD `678ea90`).
> Este documento conserva las **cuatro** pasadas de review, en orden: primera
> (CHANGES_REQUESTED sobre `38cfa04`), segunda (APPROVED sobre `8c6aa82`),
> tercera (CHANGES_REQUESTED sobre `3add86e`) y cuarta —la que manda— en
> «**Cuarta pasada — una sola fórmula, un solo criterio**», al final.
>
> Resumen de la cuarta: los **tres cambios requeridos** en la tercera están
> hechos y verificados uno a uno con evidencia propia, no con la del
> implementer. Mi sonda bloqueante —la línea `declared_albaran` con declarado
> ≠ recálculo— ahora **sobrevive intacta**. Quedan cuatro tareas de cierre,
> todas documentales o de backlog, listadas al final: no requieren otra pasada
> de review, pero sí aplicarse antes de marcar la feature `done`.

---

# Primera pasada — 2026-08-18, HEAD `38cfa04` (11 commits sobre `dev` = `cd904cd`)

## Veredicto (primera pasada)

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

---

# Segunda pasada — round trip de R18 · 2026-08-18, HEAD `8c6aa82`

**Commit revisado**: `8c6aa82` («F-019: round trip de review - R18 con test
automatico») sobre `38cfa04`, misma rama. Árbol limpio
(`git status --porcelain` sin salida).

Alcance de esta pasada: **solo lo que cambió en `8c6aa82`** más lo que el
veredicto anterior dejaba pendiente. El resto de la feature quedó verificado
contra el diff real en la primera pasada y no se repite.

## Veredicto

**APPROVED.**

El único punto que bloqueaba —R18 sin ningún test automático— está cerrado, y
cerrado mejor de lo que pedía el informe: con cinco tests, con la spec
corregida y con una **objeción bien fundada a mi propia redacción** que el
reviewer acepta y recoge más abajo.

## Qué cambió en `8c6aa82`

Seis ficheros, **ninguno de producción**:

| Fichero | Cambio |
|---|---|
| `services/albaran-valoracion-api/tests/test_f019_r4_r7_importe_select.py` | +2 tests de R18 y la fixture `LINEA_2139643` |
| `services/albaran-valoracion-persist/tests/test_f019_r16_r17_feymaco.py` | +3 tests de R18 y la fixture homónima con comentario cruzado |
| `specs/.../requirements.md` | R18 reescrito |
| `specs/.../tasks.md` | trazabilidad de R18 y enunciados de T1 y T6 |
| `progress/impl_F-019.md` | sección de round trip + «Evidencias» actualizadas |
| `progress/review_F-019.md` | este informe, incluido para dejar rastro |

Confirmado que **no se tocó código de producción**: el alcance recalculado con
`harness.alcance.alcance_de_feature("F-019")` sigue dando **los mismos 3
ficheros y las mismas 144 líneas** (64 + 63 + 17) que en la primera pasada.
De ahí que la campaña de mutación de T8 (4 mutantes, 0 supervivientes, ya
verificada de forma independiente) **siga vigente sin repetirla**, y que la
puerta de rutas sensibles no cambie de estado.

## Los cinco tests · existen, se ejecutan, pasan y muerden

Abiertos uno a uno, no leídos del informe.

### sv5 — `test_f019_r4_r7_importe_select.py`

- `test_f019_r18_el_albaran_2139643_vale_1941_euros`: inserta la fila real
  (código `1 11 00353`, cantidad 50, precio 0,647, dto 40, neto 19,41,
  imputación `CI.4.18`) y ejecuta **`_SQL_ALBARAN_LINES` importado del módulo
  de producción**. Afirma `importe_albaran == 19.41`, `!= 970.50`, y de paso
  el concepto y el unitario. **Muerde de verdad**: con el `cantidad *` fuera
  del `COALESCE` —el bug— este SELECT devuelve `50 × 19,41 = 970,50` y el
  test cae. Es el test que le faltaba al segundo albarán del incidente.
- `test_f019_r18_la_derivacion_del_2139643_coincide_con_su_neto`: la misma
  fila sin `precio_neto` ⇒ la rama derivada del `COALESCE` da el mismo 19,41
  (`50 × 0,647 × 0,6` exacto). Buen añadido: demuestra que el dato transcrito
  y la fórmula canónica del dominio cuadran entre sí, que es justo lo que
  hace confiable a la fixture.

### sv6 — `test_f019_r16_r17_feymaco.py`

- `test_f019_r18_el_albaran_2139643_conserva_su_unitario_leido`:
  `final_price == 0.647`, `source == "albaran_declared"`,
  `agreement != "mismatch"` y el `precio_1a` ruidoso de 4.000 €/ud no entra.
- `test_f019_r18_el_albaran_2139643_vale_1941_euros`: encadena
  `ImporteCalculator` ⇒ `importe_calculado == 19.41` y `!= 970.50`.
- `test_f019_r18_el_importe_del_2139643_tambien_sale_del_calculo`: llama a
  `compute` con **`importe_albaran_declarado=None`**, así que el importe se
  **calcula** desde `cantidad × precio × (1 − dto/100)` en vez de recibirlo
  regalado, y exige además `importe_source == "calculated"`. **Cierra la
  observación no bloqueante nº 1 de la primera pasada**, que era exactamente
  este hueco en el test equivalente de R16. Es la clase de respuesta que uno
  quiere de un round trip: no solo tapa el agujero señalado, tapa el que se
  señaló de pasada.

Nota honesta sobre el reparto: los tres de sv6 habrían pasado también con la
precedencia vieja (el derivado 0,647 coincidía con el declarado), así que son
**regresión de valores**, no de precedencia — la precedencia ya la cubren los
`test_f019_r8_*` y `_r10_*`. **El que caza el bug del 970,50 es el de sv5**, y
existe. R18 queda cubierto «hasta donde llega el test», que era la exigencia.

### Ejecución (por el reviewer, no leída del informe)

```
sv5:  python -m pytest tests -q -k r18   ->  2 passed, 9 deselected
sv6:  python -m pytest tests -q -k r18   ->  3 passed, 37 deselected
sv5:  python -m pytest tests -q          ->  11 passed
sv6:  python -m pytest tests -q          ->  40 passed
```

`grep` de control sobre los `.py` del árbol: `19.41` / `970.50` / `0.647`
aparecen ahora **15 veces**, frente a las **0** que motivaron el rechazo.

## Corrección aceptada: los números NO son una reconstrucción aritmética

La primera pasada pedía documentar la fixture como «reconstrucción aritmética
a partir del total conocido (`970,50 / 19,41 = 50`)». **Esa parte de mi
informe era incorrecta y queda rectificada.** El líder verificó la composición
de la línea en dos fuentes independientes que coinciden campo a campo:

- el PDF `Feymaco_2139643.pdf` del lote `alvaro_17082026` — línea única,
  código `1 11 00353`, `DISCO ESPECIAL ACERO INOX. 115X1X22`, cantidad 50,00,
  precio 0,647, dto 40,0, neto 19,41;
- el ground truth del administrativo `alvaro_17082026.xlsx` — misma fila,
  partida `CI.4.18`, descuento en fracción (0,4).

El razonamiento del implementer para no copiar mi redacción es correcto y
mejor que la mía: **un dato deducido del propio bug no puede después usarse
para juzgar el bug**. Deducir la cantidad de `970,50 / 19,41` da por buena
precisamente la fórmula rota. Que el número salga igual es una coincidencia
afortunada, no una fuente.

- [x] **Los docstrings lo dicen así**, comprobado abriendo los dos ficheros:
      ambos abren su bloque de R18 con «TRANSCRITA de dos fuentes
      independientes que coinciden campo a campo (**no** es una reconstrucción
      aritmética)» y citan el PDF y el ground truth con sus campos. En sv6 se
      añade además que la prueba local del 18-08 registró 970,50 = 50 × 19,41.
- [x] Ninguna de las dos fuentes entra al repositorio: `git log --diff-filter=A`
      sobre `*.pdf`, `*.xlsx` y `*.docx` en la rama no devuelve nada, y el
      único fichero nuevo de `8c6aa82` es este informe. Se citan por nombre,
      que es lo correcto.

## La spec ya no afirma que R18 sea solo manual

- [x] **`requirements.md` R18**: fuera «*Solo se conoce el total: verificación
      MANUAL (humano)*». Ahora incorpora la composición completa de la línea,
      nombra las dos fuentes, aclara que no es una deducción y declara que se
      cubre con **tests automáticos** (`test_f019_r18_*` en T1 y T6)
      **«y además»** con la verificación MANUAL. Redacción correcta: el test
      acompaña, no sustituye.
- [x] **`tasks.md`**: la tabla de trazabilidad pasa R18 de `T10 (MANUAL)` a
      `T1 (tramo sv5) + T6 (tramo sv6) + T10 (MANUAL)`, y los enunciados de T1
      y T6 recogen la fila del 2.139.643 con sus números y sus asertos. La
      verificación de T6 pasa a exigir `_r18_*` en verde.
- [x] La incoherencia que delató el fallo —el guion §T10 afirmando la
      composición mientras la spec decía que solo se conocía el total— queda
      resuelta por el lado correcto: la composición era cierta y verificable;
      lo que estaba mal era la spec.

## T10 sigue en pie como verificación MANUAL

- [x] `tasks.md:121` conserva `- [ ] **T10**: MANUAL (humano) — **PENDIENTE
      del humano**`, con sus cuatro puntos y su guion de comandos y SQL
      exactos en `progress/impl_F-019.md` §T10, sin recortes.
- [x] La trazabilidad mantiene T10 en R18 y en R19/R20/R21. Los tests nuevos
      cubren las dos piezas deterministas de la cadena; **no** cubren el
      extremo a extremo con IA real, PostgreSQL y Azurite, que es lo que T10
      comprueba. La distinción está escrita tanto en la spec como en el
      informe del implementer.
- [x] `progress/current.md` sigue listando los cuatro puntos MANUAL como
      pendientes del humano.

## `bash harness/init.sh` sigue en verde

Re-ejecutado por el reviewer sobre `8c6aa82`:

```
248 passed in 68.96s   (suite raiz)
[OK] PUERTA COBERTURA: 100.0% de 5 lineas cambiadas cubiertas (5/5, umbral 80%, nivel critico)
[AVISO] PUERTA RUTAS SENSIBLES [evals]: aviso (2 rutas, sin cambio respecto a la primera pasada)
[OK] Rama actual: feature/F-019-importe-unitario-manda
ENTORNO LISTO. Puedes trabajar.
```

La puerta de cobertura sigue midiendo las mismas 5 líneas de producción al
100 % porque el round trip no tocó producción. Los `[AVISO]` son los mismos de
la primera pasada (ruff como deuda previa, sv1/sv4/infra sin tests, y la
puerta de rutas sensibles en `aviso` con su motivo ya justificado por escrito
en C4 ter).

## Checkpoints — estado final

| Checkpoint | Estado | Nota |
|---|---|---|
| C1 · arnés en verde | **[x]** | `init.sh` exit 0 re-ejecutado sobre `8c6aa82` |
| C2 · estado coherente | **[x]** | una sola feature `in_progress`, rama correcta, árbol limpio |
| C3 · arquitectura y convenciones | **[x]** | verificado en la primera pasada; el round trip solo añade tests con su cabecera de ruta |
| C3 bis · documentos de fuera | **N/A justificado** | no se toca `docs/referencia/`; ni PDF ni ofimática entran al repo (comprobado también en el histórico de la rama) |
| C4 · verificación real | **[x]** | **R18 pasa de `[ ]` a `[x]`**: la tabla requisito→test de la primera pasada queda completa, R1-R22 sin huecos |
| C4 bis · rigor `critico` | **[x]** | fase RED con tres trazas reales; cobertura 100 % (5/5); mutación 144 líneas / 4 mutantes / 0 supervivientes, recalculada y re-ejecutada por el reviewer, con la prueba de control del cero superada; «Evidencias» con los cuatro números, actualizados tras el round trip |
| C4 ter · rutas sensibles | **[x]** | exigencia `aviso`; informe existe y es fresco; no cumple `exige_lineas` y **el motivo consta por escrito**, verificado de primera mano (claves LLM ausentes + `evals/fixtures/inputs/_indice.json` con `"casos": []`) |
| C5 · sesión cerrada | **[x]** | T1-T9 y T11 `[x]` con un commit cada una; **T10 `[ ]` es correcto** (MANUAL del humano, convención de F-002); árbol limpio; `features.json` real |

Ningún checkbox vacío en C1-C5. Los dos N/A están justificados por escrito.

## Lo que queda pendiente, y no es del implementer

Nada de esto bloquea el cierre, pero el humano debe verlo antes de mergear:

1. **Las cuatro verificaciones MANUAL de T10** (los dos albaranes, el chequeo
   de que ninguna línea arrastra `unitario_declarado_vs_derivado_mismatch` y
   el albarán de hormigón por contrato). Guion listo en
   `progress/impl_F-019.md` §T10. Es la única prueba que ejerce la cadena
   entera con IA, BBDD y colas reales.
2. **R20 — histórico**: las valoraciones anteriores conservan sus importes
   inflados hasta que se re-valoren. No hay backfill, por decisión cerrada;
   qué documentos se reprocesan y cuándo lo decide el humano. Hay consulta
   para dimensionarlo en §T10.
3. **F-003 hay que reconciliarla antes de arrancarla**: su R4 manda conservar
   la derivación que F-019 acaba de corregir.
4. **`evals/ground_truth/`** sigue sin casos: hasta que se rellene, la puerta
   de rutas sensibles no puede pasar de `aviso` a `bloqueo`.
5. Las **tres observaciones no bloqueantes** de la primera pasada. La nº 1
   quedó de hecho mitigada por el tercer test de R18; las nº 2 y 3 son de una
   línea cada una y no son regresión de esta feature.
6. La **propuesta de mejora del protocolo** (extender la prueba de control del
   cero a «cero mutantes en cualquier fichero del alcance», y portarla a
   `arnes-base`) sigue sobre la mesa, sin aplicar.

## Nota final del reviewer

La feature entra con: 57 tests nuevos, los 22 requisitos trazados, cobertura
del 100 % de lo cambiado, cero supervivientes de mutación verificados de forma
independiente, los dos albaranes del incidente con sus números clavados por
test automático, y una corrección al propio reviewer que era correcta. El
código de producción son **dos cambios**: un paréntesis en un `COALESCE` y el
orden de dos bloques `if`. El resto es la explicación de por qué, escrita
donde se consume.

---

# Tercera pasada — el importe persistido · 2026-08-18, HEAD `3add86e`

Alcance revisado: **solo** `git diff acb97ee..HEAD` (8 commits). Todo lo
aprobado hasta `acb97ee` queda dado por bueno y no se vuelve a mirar.

## Veredicto (tercera pasada)

**CHANGES_REQUESTED** — por un defecto **demostrado y reproducible**, no por
una sospecha: el guardián de **R24** decide «esta fila no ha cambiado»
comparando el **resultado** (importe anterior vs importe recalculado) en vez
de las **entradas** (cantidad y descuento). Consecuencia: una línea que sv6
dejó en `declared_albaran` con un importe declarado que **no** coincide con
`cantidad × precio × (1 − dto/100)` —caso que sv6 produce a propósito y marca
con `declared_vs_calculated_mismatch`— es pisada y reetiquetada a `calculated`
en el primer guardado, **aunque el revisor no toque esa línea**. Es la misma
familia de fallo que motivó este round trip, más estrecha pero viva.

El resto del trabajo es bueno y así consta abajo: el fix del descuento es
correcto, el criterio del humano (139,66 €) queda fijado por test sobre el
valor **persistido**, la campaña de mutación se sostiene contra verificación
independiente y sv4 pasa de 0 a 44 tests.

## Nivel de rigor

`harness/features.json` declara **`rigor: critico`** para F-019. Exige: fase
RED con salida real, puerta de cobertura en OK, campaña de mutación **sin
supervivientes** salvo justificación escrita aceptada, sección «Evidencias» y
ningún N/A sin motivo.

## Alcance real del diff (verificado con `--stat`)

Un solo fichero de **producción**:
`services/albaranes-front/infrastructure/database/review_repository.py`
(+226 líneas). Lo demás son tests (3 ficheros, 863 líneas), spec (G6,
R23-R26), `docs/ARCHITECTURE.md` (+8), `harness/features.json`, `progress/`.

## Checkpoints

| Checkpoint | Estado | Nota |
|---|---|---|
| C1 · Arnés completo y en verde | **[x]** | Ver «Sobre `init.sh`» abajo. |
| C2 · Estado coherente | **[x]** | `features.json` reabre F-019 a `in_progress`; `tasks.md` añade T12-T16 marcadas y con commits `F-019 Tn: ...`; `progress/current.md` al día. |
| C3 · Arquitectura y convenciones | **[ ]** | Fórmula duplicada **entre servicios** (sv4 y sv6) teniendo `ruesma_comun` como dependencia real de sv4. Cambio requerido 2. |
| C3 bis · Documentos de fuera | **N/A** | *Justificado*: este round trip no incorpora ningún PDF ni ofimática; no hay nada que convertir con `markitdown`. |
| C4 · Verificación real | **[ ]** | Los tests muerden (comprobado), pero **R24 no está cubierto en su caso difícil** y el cableado `payload → new_line_discounts` no lo ejecuta ningún test. Cambios requeridos 1 y 3. |
| C4 bis · Rigor declarado | **[x]** | Mutación verificada de forma independiente (sección propia). Fase RED presente (commit `bc54043`, «T13-T14: fase RED del round trip 2») con salida real en `impl_F-019.md`. Sección «Evidencias» con los cuatro números. |
| C4 ter · Rutas sensibles | **N/A (AVISO)** | *Justificado*: las dos rutas en aviso (`price_reconciler.py`, `valuation_envelope.py`) son de sv5/sv6 y **este diff no las toca** — verificado con `--stat`: el único fichero de producción del diff es de sv4, que no figura en `harness/rutas_sensibles.json`. El aviso viene del trabajo original y de que `evals/ground_truth/` sigue vacío; decisión D5 de F-011. **No hay ninguna ruta sensible nueva.** |
| C5 · Sesión cerrada | **[x]** | Informe, `current.md` e informe de mutación actualizados en el commit de cierre `3add86e`. |

## Sobre `init.sh`

- Medición del coordinador sobre `3add86e`: **verde en 1m26s**, con
  `PUERTA COBERTURA: 89.1% de 55 líneas cambiadas cubiertas (49/55, umbral
  80%, nivel critico)` en OK y las suites por servicio en verde.
- Mi propia ejecución, lanzada en paralelo con la del coordinador sobre el
  mismo árbol, **terminó en rojo** tras 46 min:
  `tests/test_f012_r1_r5_r11_coordinador.py::test_f012_r1_evalua_todos_los_mutantes_una_sola_vez`
  abortó con `git init` devolviendo `3221225794` (`0xC0000142`,
  *STATUS_DLL_INIT_FAILED* de Windows: fallo al crear proceso por presión de
  recursos, no un fallo lógico). **Reejecutado en aislamiento: 13 passed en
  8,63 s.** Queda como incidencia de entorno, no del código; el fichero
  afectado es del arnés (F-012) y no tiene relación con el diff de F-019.

## C4 bis · Mutación · verificado de forma independiente

No me creí los totales del informe: los recalculé.

```
harness.alcance.alcance_de_feature('F-019') + harness.mutacion.generar_mutantes
F-019: 4 fichero(s), 328 línea(s) (rama, cd904cd..feature/F-019-importe-unitario-manda)
  64 líneas |  0 mutantes | sv5 sqlalchemy_valuation_context_repository.py
  63 líneas |  4 mutantes | sv6 price_reconciler.py
  17 líneas |  0 mutantes | sv6 valuation_envelope.py
 184 líneas | 20 mutantes | sv4 review_repository.py
TOTAL 328 líneas | 24 mutantes
```

Coincide **exactamente** con `progress/mutacion_F-019.md` (328 líneas, mismo
reparto por fichero, 24 mutantes). La campaña no declara cero mutantes, así
que la prueba de control por exclusión de alcance no aplica.

**Los dos supervivientes existen como mutantes reales**, con el mismo operador
y el mismo texto, comprobado listando los 20 mutantes de sv4:

- `review_repository.py:115` `[logico]` — `if precio_unitario is None or cantidad is None:` → `... and ...`
- `review_repository.py:3737` `[logico]` — `if a is None or b is None:` → `... and ...`

**La equivalencia la verifiqué yo ejecutando ambas versiones**, y sobre una
tabla más amplia que la del implementer (no sus 8 casos: 15 pares × 8
descuentos = 120 combinaciones para el primero, incluyendo tipos que revientan
`float()` con `ValueError` y con `TypeError`; y 11 × 11 = 121 para el segundo):

```
mutante 115:  diferencias = 0
mutante 3737: diferencias = 0
```

El razonamiento se sostiene además por construcción: en el 115 el `and` deja
pasar el único `None` a `float(...)`, que lanza `TypeError` y cae en el
`except` que devuelve `None` igualmente; en el 3737 la guarda mutada es
**inalcanzable**, porque la línea anterior ya devolvió `True` para el caso
`(None, None)`. **Equivalentes ambos, justificación aceptada.** Ningún
superviviente queda en `PENDIENTE`. C4 bis se cumple para nivel `critico`.

Nota sobre `--workers 1`: la campaña paralela tropieza con
`progress/revision_hormigones_20260818.md` y
`progress/revision_resto_lote_20260818.md`, sin versionar y ajenos a esta
feature (siguen sin versionar: `git status` los muestra). No afecta al
resultado —la campaña serie evalúa los mismos 24 mutantes—, pero es fricción
real del arnés; propuesta al final.

## La suite nueva de sv4 · sí muerde

`python -m pytest tests -q` en `services/albaranes-front`: **44 passed in
1.10s**. Ni red, ni BBDD real, ni LLM: SQLite en memoria con el subconjunto
del schema del que es dueño sv6.

Lo importante es **de dónde salen los números**: la fixture `LINEAS_2137569`
son los cinco importes medidos en la BBDD local (35,19 / 20,53 / 55,63 /
13,19 / 15,12), y los tests afirman a la vez el valor bueno **y la negación
del valor equivocado** (`!= 232,76`, `!= 58,64`, `!= 54,30`). Eso es morder:
un test que solo dijera «== 139,66» pasaría con la fórmula rota si alguien
tocara la fixture; estos no.

**¿Cubren el pisado o solo el cálculo?** Cubren el pisado en lo esencial: los
tests siembran las filas **tal como las dejó sv6** (`importe_source =
'declared_albaran'`, total 139,66), invocan el recálculo real y **releen de la
tabla** el importe, la fuente y `total_valorado`. No es aritmética aislada.
Además hay una capa unitaria de la fórmula
(`test_f019_r23_formula_canonica.py`) y un **guardián estructural** que detecta
por regex una multiplicación `float(precio) * float(cantidad)` fuera de
`_importe_de_linea`, con su **prueba de control** que verifica que el patrón
reconoce las dos líneas exactas del bug. Buen trabajo: eso es lo que faltaba.

Los agujeros están en los bordes, y son los cambios requeridos 1 y 3.

## R25 · el test del total del documento persistido · existe

`services/albaran-valoracion-persist/tests/test_f019_r25_r26_total_documento.py`
(sv6) con `test_f019_r25_el_total_del_2137569_es_13966`,
`..._las_cinco_lineas_del_2137569_y_su_suma`,
`..._el_total_del_2139643_es_1941` y
`..._el_total_no_arrastra_ruido_de_coma_flotante`; y en sv4
`test_f019_r25_el_total_lo_recalcula_sv4_y_vale_13966` +
`test_f019_r26_el_total_recalculado_no_arrastra_ruido_float`. El agujero por
el que se coló el fallo —los 139,66 € viviendo solo en un guion manual—
**queda tapado en los dos servicios que escriben el total**.

R26 también: el `SUM()` de sv4 pasa a `ROUND(CAST(... AS numeric), 2)` y el
test lo fija con la suma que arrastra cola binaria (3392.7200000000003).

## La regla 13 de `docs/ARCHITECTURE.md` · existe y dice lo que él dice

Verificado leyendo el fichero, no el informe. La regla 13 **ya existía** antes
de este diff (la introdujo el trabajo original de F-019) y ya decía: «Fórmula
canónica, **única y sin excepciones**: `importe = cantidad × precio × (1 −
descuento/100)`». Este diff le añade 8 líneas que **explicitan a quién obliga**
(«a todo el que escriba un importe, no solo al valorador»), nombran los dos
puntos que la aplican y cierran con «Un servicio **no reetiqueta** como
`calculated` un importe que el albarán declara si nadie ha tocado la línea».

La invocación es **legítima**: no inventa una regla para justificar el cambio,
extiende una que ya estaba y que ya cubría el caso. La ampliación de alcance a
sv4 está además **declarada por escrito** en la spec (G6) invocando la regla
LÍMITE DE SERVICIO de `CLAUDE.md`, que es exactamente lo que esa regla pide.

Detalle incómodo: la última frase que el implementer añadió a la regla 13 es
justo la que su propio código **no cumple del todo** (cambio requerido 1).

## Cambios requeridos

### 1. R24 se decide por el resultado, no por lo que el revisor tocó · BLOQUEANTE

`services/albaranes-front/infrastructure/database/review_repository.py:3338-3350`:

```python
importe_anterior = row["importe_calculado"]
sin_cambios = (
    importe_anterior is not None
    and self._num_iguales(importe_anterior, nuevo_importe)   # <-- este
    and self._num_iguales(row["cantidad_albaran"], nueva_cant_albaran)
    and self._num_iguales(row["cantidad_convertida"], nueva_cant_conv)
)
```

El conjunto `_num_iguales(importe_anterior, nuevo_importe)` hace que la fila se
**actualice siempre que el importe guardado difiera del recalculado**, aunque el
revisor no haya tocado ni la cantidad ni el descuento. Y sv6 produce esas filas
**a propósito**: `ImporteCalculator.compute` devuelve
`importe_source='declared_albaran'` con el importe **declarado** cuando
declarado y calculado discrepan, dejando el motivo
`declared_vs_calculated_mismatch` (`importe_calculator.py:150-170`), en
aplicación de la regla de jul 2026 y de la propia regla 13 («si ambos existen y
discrepan, gana el declarado y la línea va a revisión»).

**Demostrado, no deducido.** Sonda ejecutada con las fixtures de este mismo
diff (línea declarada 100,00 €; cantidad 100, unitario 1,00, dto 40 % ⇒
recálculo 60,00 €; el revisor **no toca nada**):

```
RESULTADO: {'importe_calculado': 60.0, 'importe_source': 'calculated'} total: 60.0
AssertionError: R24: el importe declarado fue pisado — assert 60.0 == 100.0
```

Es decir: el importe que el albarán DECLARA se pisa y se reetiqueta a
`calculated` en el primer guardado. Eso incumple, a la vez:

- **R24** de la spec, en su letra: «MIENTRAS el revisor no cambie ni la
  cantidad ni el descuento de una línea, el recálculo de sv4 NO debe modificar
  esa fila: ni su `importe_calculado`, ni su `importe_source`»;
- la frase que este mismo diff añade a la **regla 13** de `ARCHITECTURE.md`.

Y no es un caso exótico: basta con que el importe impreso en el albarán difiera
del producto por más de medio céntimo (redondeos por línea del proveedor,
descuentos en cascada) para que la línea entre en este camino. El Feymaco
2.137.569 se salva **por casualidad**, porque sus cinco líneas cuadran al
céntimo — por eso los tests actuales no lo ven.

**Remedio concreto** (decidir por las ENTRADAS, que es lo que dice R24):
eliminar el conjunto del importe y añadir el del descuento, de modo que
`sin_cambios` sea «cantidad_albaran igual **y** cantidad_convertida igual **y**
descuento igual» (comparando el descuento ya saneado, para que `0` y `NULL` no
cuenten como cambio). Con eso los tests existentes siguen pasando:
`guardar_sin_tocar_nada` salta la fila, `cambiar_la_cantidad` la actualiza y
`el_descuento_editado_por_el_revisor_manda` también, porque ahí el descuento sí
cambia.

**Y un test que lo fije**: línea `declared_albaran` con declarado ≠ recálculo,
guardado sin tocar esa línea ⇒ `importe_calculado` e `importe_source` intactos.
Sirve la sonda de arriba tal cual.

### 2. La fórmula sigue duplicada ENTRE servicios · BLOQUEANTE (o deuda que decida el humano)

Dentro de sv4 la unificación es real y está bien hecha (4 copias → 1, con
guardián estructural). Lo que queda es la duplicación **entre servicios**:

- sv6: `services/albaran-valoracion-persist/application/services/importe_calculator.py`
  (`ImporteCalculator._sanitize_descuento` + `compute`).
- sv4: `services/albaranes-front/infrastructure/database/review_repository.py:64-124`
  (`_sanear_descuento` + `_importe_de_linea`), cuyo propio docstring admite que
  es «la misma que aplica `ImporteCalculator` en sv6».

`CLAUDE.md`, Reglas duras, LÍMITE DE SERVICIO: «la lógica compartida va a
`services/albaranes-comun`, **nunca copiada entre servicios**». Y sv4 **ya
depende** de `ruesma_comun` (`requirements.txt`, e imports reales en
`infrastructure/colas/` y `interface_adapters/web/app.py`), así que el vehículo
existe y no hay excusa técnica.

**No es teórico: las dos copias YA divergen** en tres puntos observables,
comprobados leyendo ambas:

1. un descuento ilegible (`'x'`) devuelve `None` en sv4 (`try/except`) y
   **lanza `ValueError`** en sv6 (`float(descuento_pct)` sin proteger);
2. sv6 deja traza auditable (`reasons: descuento_fuera_de_rango_ignorado:...`),
   sv4 solo un `logger.warning`;
3. el borde: sv6 `if d < 0.0 or d > 100.0` devolviendo `0.0` para el cero; sv4
   `if d <= 0.0 or d > 100.0` devolviendo `None`. Hoy el importe sale igual,
   pero lo que se **persiste** en `descuento_albaran_aplicado` no: sv4 escribe
   `NULL` donde sv6 escribiría `0.0`.

El guardián estructural nuevo no protege de esto: mira **un solo fichero de
sv4** y solo el patrón `float(x) * float(y)`. Nada detecta que sv4 y sv6 se
separen.

**Resolución admisible, cualquiera de las dos:**

- **(a)** mover la fórmula y el saneado del descuento a `ruesma_comun` (p. ej.
  `ruesma_comun/importes.py`) y que `ImporteCalculator` y `_importe_de_linea`
  la consuman, cada uno con su política propia encima (precedencia del
  declarado en sv6, `reasons`, etc.); o
- **(b)** si el humano prefiere no tocar sv6 en esta feature, **dejarlo escrito
  como deuda explícita** donde él la vea —entrada nueva en
  `harness/features.json` (backlog) referenciada desde la regla 13— con el
  motivo y el riesgo. Esta decisión **la toma el humano, no el reviewer**: no
  puedo aprobar por mi cuenta el incumplimiento de una regla dura.

Respondiendo a lo que se me pidió valorar: **que sv4 recalcule importes es
aceptable** —el revisor edita cantidades y descuentos, y el importe tiene que
seguir a lo que él escribe; obligar a re-valorar por sv6 en cada guardado no
tendría sentido—, pero **solo** si la fórmula es una y vive en un sitio del que
los dos beben. Tal como está hoy, el arreglo elimina la divergencia dentro de
sv4 y **aplaza** la de sv4 contra sv6.

Aparte, y sin ser bloqueante: la afirmación del docstring «Regla: **NINGÚN**
sitio de este servicio vuelve a multiplicar precio por cantidad por su cuenta»
no es exacta. `templates/document_detail.html:619-621` y
`static/app.js:1003-1030` tienen cada uno su copia de la fórmula (ambas **sí**
con el descuento, así que no hay defecto). Conviene rebajar la frase a «ningún
sitio del **backend**» o extender el guardián.

### 3. El cableado `payload → descuento` no lo ejecuta ningún test · BLOQUEANTE (barato)

La línea que conecta el arreglo con la realidad es
`review_repository.py:3212-3218`:

```python
new_line_discounts={
    int(line.id): line.descuento
    for line in payload.lines
    if line.id is not None
},
```

Ningún test la ejecuta: `grep` sobre `services/albaranes-front/tests/` solo
encuentra `new_line_discounts=` pasado **a mano** al método privado, y no hay un
solo test de `update_document`. Si esa comprensión se escribiera como la de las
cantidades —con `if line.descuento is not None`—, el incidente volvería entero
y en silencio: es justo el matiz que aquí se ha resuelto **al revés a propósito**
(incluir los `None` para que el revisor pueda borrar el descuento) y que nadie
protege.

Basta un test que construya `payload.lines` real y compruebe el mapa resultante
(o que llame a `update_document` con una sesión falsa que capture los
argumentos). Relacionado: `new_line_discounts` **confía** en que el cliente mande
siempre `descuento`; hoy `static/app.js:1776` lo reenvía intacto
(`descuento: pick("descuento")`), así que no hay defecto — pero es una
dependencia implícita entre el JS y el repositorio que merece quedar fijada por
test.

## Observaciones no bloqueantes

1. **Motivos (`reasons`) obsoletos tras el recálculo.** Cuando sv4 sí actualiza
   una fila legítimamente, deja intactos los motivos que escribió sv6
   (`descuento_aplicado:40%`, `declared_vs_calculated_mismatch:...`). Es la
   misma «contradicción aparente» que el implementer describe tan bien como
   firma del culpable (descuento 40 registrado y no aplicado). No entra en
   R23-R26, pero es la siguiente piedra para quien lea la BBDD.
2. **`_num_iguales` con 5e-3** es medio céntimo: correcto para dinero de dos
   decimales, y fijado por test en sus dos bordes. Bien.
3. **El `ROUND(CAST(... AS numeric), 2)`** se prueba sobre SQLite; en producción
   es PostgreSQL. La sintaxis es válida en ambos y el `CAST` a `numeric` es
   justo lo que hace falta en PG (no existe `round(double, int)`), así que el
   test no es una falsa seguridad. Anotado por transparencia.
4. **sv4 tenía 0 tests y ahora tiene 44**, con `conftest.py` que ancla el
   servicio en `sys.path` igual que sv2/sv5/sv6. El aviso de `init.sh` («NADIE
   está comprobando los tests de sv4-front») desaparece. Es la mejor
   consecuencia colateral de este round trip.

## Cobertura requisito → test (solo los requisitos nuevos)

| Requisito | Test que lo cubre | Estado |
|---|---|---|
| R23 · fórmula canónica con descuento en sv4 | `sv4/test_f019_r23_r26_recalculo_importe.py` (7 tests, incl. los 5 parametrizados por línea) + `sv4/test_f019_r23_formula_canonica.py` (10 tests) + guardián estructural con prueba de control | **[x]** |
| R24 · lo que el revisor no toca, no se toca | `..._r24_una_linea_intacta_conserva_su_importe_source`, `..._r24_cambiar_la_cantidad_si_marca_la_linea_como_calculada` (+5 unitarios de `_num_iguales`) | **[ ]** — solo el caso fácil (declarado == recalculado). El caso difícil falla: ver cambio requerido 1 |
| R25 · total del documento persistido | sv6 `test_f019_r25_r26_total_documento.py` (4 tests) + sv4 `..._r25_el_total_lo_recalcula_sv4_y_vale_13966` | **[x]** |
| R26 · total redondeado a 2 decimales | sv6 `..._el_total_no_arrastra_ruido_de_coma_flotante` + sv4 `..._r26_el_total_recalculado_no_arrastra_ruido_float` | **[x]** |

## Propuesta de mejora del protocolo (no aplicada, para el humano)

1. **`CHECKPOINTS.md` C4** debería pedir explícitamente que, cuando un
   requisito diga «MIENTRAS X no cambie, no se toca Y», exista un test del
   **caso difícil**: el que distingue «no ha cambiado la entrada» de «no ha
   cambiado el resultado». Los dos tests de R24 de esta pasada solo cubren el
   caso fácil, en el que ambas lecturas coinciden, y por ahí se coló el hueco.
2. **`harness/mutacion_paralela.py`** no debería tropezar con ficheros sin
   versionar ajenos a la feature: o los ignora, o avisa y sigue. Obligar a
   `--workers 1` multiplica el coste de la puerta más cara.
3. **`tests/test_f012_r1_r5_r11_coordinador.py`** crea repos git reales con
   `subprocess`; bajo carga eso falla en Windows con `0xC0000142` y tumba
   `init.sh` entero (corre con `-x`). Merece un reintento o un `skip` marcado
   ante ese código de salida concreto, para que un problema de recursos no se
   lea como un entorno en rojo.
4. Las tres son genéricas: si se aceptan, se portan a `arnes-base` en el mismo
   trabajo (regla de propagación de `CLAUDE.md`).

---

# Cuarta pasada — una sola fórmula, un solo criterio · 2026-08-18, HEAD `678ea90`

Alcance revisado: **solo** `git diff 3add86e..HEAD` (4 commits: T18, T19-T20,
T21 ×2). Lo anterior queda como lo dejó la tercera pasada.

## Veredicto (cuarta pasada)

**APPROVED**.

Los **tres cambios requeridos** están hechos, y los he verificado **con
evidencia propia**, no leyendo el informe:

1. **R24 por entradas** — mi sonda bloqueante de la tercera pasada, ejecutada
   sin cambios contra este HEAD, **pasa**:
   `{'importe_calculado': 100.0, 'importe_source': 'declared_albaran'}`. La
   línea que el albarán declara sobrevive intacta a un guardado que no la
   toca. Antes daba `60.0` / `calculated`.
2. **La fórmula a `ruesma_comun`** — existe `ruesma_comun/importes.py`, y sv4
   y sv6 la **consumen de verdad**: lo fijan dos tests de **identidad de
   objeto** (`review_repository.importe_de_linea is compartida`,
   `importe_calculator.importe_de_linea is importe_de_linea`), que caen aunque
   alguien reescriba una copia correcta.
3. **El cableado `payload → descuento`** — extraído a `_cantidades_del_payload`
   y `_descuentos_del_payload`, con la asimetría del filtrado de `None` fijada
   por `test_f019_r23_los_dos_mapas_no_se_filtran_igual`.

Suites ejecutadas por mí, en serie: sv4 **59 passed** (eran 44), comun **49
passed**, sv6 **53 passed**.

Quedan **cuatro tareas de cierre** (sección propia al final): una deuda que
decide el humano y tres correcciones documentales. Ninguna toca código ni
tests, ninguna justifica otra pasada de review — pero todas deben aplicarse
antes de marcar la feature `done`, porque tres de ellas son afirmaciones
escritas que el código no respalda, y esta feature ya ha costado tres round
trips por creer una afirmación en vez de medirla.

## Checkpoints

| Checkpoint | Estado | Nota |
|---|---|---|
| C1 · Arnés completo y en verde | **[x]** | `init.sh` verde sobre `678ea90` (medición del coordinador), cobertura **93,1 % (81/87)**, umbral 80, nivel `critico`. |
| C2 · Estado coherente | **[x]** | `features.json`: F-019 `in_progress`, `rigor: critico`, rama correcta. `tasks.md` añade T18-T21 marcadas, con trazabilidad requisito → tarea (R24 reformulado, R27-R28 → T19, R29 → T20). Salvedad documental: ver cierre 2. |
| C3 · Arquitectura y convenciones | **[x]** | El `[ ]` de la tercera pasada queda **levantado**: la lógica compartida vive en `services/albaranes-comun` y la política se queda en cada servicio, que es justo lo que pedía LÍMITE DE SERVICIO. Ver «Qué se movió y qué no». |
| C3 bis · Documentos de fuera | **N/A** | *Justificado*: este round trip no incorpora ningún PDF ni ofimática. |
| C4 · Verificación real | **[x]** | Los dos `[ ]` de la tercera pasada quedan **levantados**: R24 tiene ahora su caso difícil y sus tres simétricos; el cableado tiene 7 tests propios. |
| C4 bis · Rigor declarado | **[x]** | Mutación recalculada de forma independiente y los **tres** supervivientes verificados por ejecución (sección propia). Fase RED con salida real (`RED 7`, 4 failed / 46 passed, con el `60.0` frente a `100.0` de mi sonda). Sección «Evidencias» con los cuatro números. |
| C4 ter · Rutas sensibles | **N/A (AVISO)** | *Justificado, con matiz nuevo*: ver sección propia. |
| C5 · Sesión cerrada | **[x]** | Informe, `current.md` y análisis de mutación actualizados en `678ea90`. |

## C4 bis · Mutación · recalculada, no leída

Recalculé el alcance y el número de mutantes con `harness.alcance` y
`harness.mutacion.generar_mutantes` (cálculo puro):

```
F-019: 6 fichero(s), 515 línea(s) de producción (rama, cd904cd..feature/F-019-…)
  64 líneas |  0 mutantes | sv5 sqlalchemy_valuation_context_repository.py
  32 líneas |  3 mutantes | sv6 importe_calculator.py
  63 líneas |  4 mutantes | sv6 price_reconciler.py
  17 líneas |  0 mutantes | sv6 valuation_envelope.py
 107 líneas | 11 mutantes | comun ruesma_comun/importes.py
 232 líneas | 13 mutantes | sv4 review_repository.py
TOTAL 515 líneas | 31 mutantes
```

**Coincide exactamente** con `progress/mutacion_F-019.md`: 515 líneas, mismo
reparto por fichero, 31 mutantes. La campaña no declara cero mutantes, así que
la prueba de control por exclusión de alcance no aplica.

**Los tres supervivientes existen como mutantes reales**, con el mismo
operador y el mismo texto original→mutado, comprobado listando los mutantes de
cada fichero:

- `ruesma_comun/importes.py:72` `[comparacion]` — `if 0.0 < valor <= 100.0:` → `if 0.0 <= valor <= 100.0:`
- `ruesma_comun/importes.py:101` `[logico]` — `if cantidad is None or precio_unitario is None:` → `... and ...`
- `review_repository.py:3780` `[logico]` — `if a is None or b is None:` → `... and ...`

**Equivalencia verificada por mí, ejecutando original y mutante**, con tablas
de entradas más amplias que las del informe:

```
superv.1 (importes:72):            24 valores  → diferencias = 0
superv.2 (importes:101):        1.152 combinaciones → diferencias = 0
superv.3 (review_repository:3780): 144 pares  → diferencias = 0
```

Y los tres se sostienen además por construcción: en el 72 el único valor que
separaría `<` de `<=` es el `0.0`, que ya ha vuelto en la línea anterior (y
`-0.0 == 0.0` en Python, así que también sale por ahí); en el 101 el `and`
deja pasar el único `None` a `float(...)`, que lanza `TypeError` y cae en el
`except` que devuelve `None` igual; el 3780 es el de la pasada anterior,
inalcanzable porque la línea previa ya devolvió `True` para `(None, None)`.

**Equivalentes los tres, justificación aceptada.** Ningún superviviente queda
en `PENDIENTE`. C4 bis se cumple para nivel `critico`.

Dato relevante: los mutantes del guardián de R24
(`review_repository.py:3385` y `:3386`, los dos `and` de `sin_cambios`)
**mueren**. Es la confirmación de que los tests distinguen cada conjunto del
criterio nuevo y no se limitan a ejercitarlo.

## C4 ter · Rutas sensibles · de 2 a 3, y la tercera sí es del diff

La puerta sigue en **AVISO** por decisión D5 de F-011 y porque
`evals/ground_truth/` está vacío: la pasada completa de evals no puede dar
VERDE porque no hay nada que evaluar. Eso justifica el N/A, como en las tres
pasadas anteriores.

Pero hay un matiz que no había antes y conviene dejar escrito. Las dos rutas
de siempre (`price_reconciler.py`, `valuation_envelope.py`) estaban en aviso
por el trabajo original y **sin cambios** en los round trips 2 y 3. La
tercera, `services/albaran-valoracion-persist/application/services/importe_calculator.py`,
**sí la modifica este diff**, y encaja en el patrón
`…/application/services/**` («redes deterministas de sv6»), que es
exactamente lo que la lista quiere proteger. Además el cambio **altera
comportamiento observable**: un descuento o un precio ilegible pasaban de
reventar con `ValueError` a ignorarse.

Lo que compensa el aviso es que ese comportamiento nuevo **sí tiene test**
(`test_f019_r27_un_descuento_ilegible_ya_no_revienta`,
`..._un_precio_ilegible_no_revienta_la_valoracion`), y que el cambio es
estrictamente más tolerante: donde antes se caía una valoración por cola,
ahora se devuelve el declarado o `None`. Con eso, **N/A justificado**. Cuando
`evals/ground_truth/` reciba sus primeros libros, la ruta del importe debería
estar entre los primeros casos: queda anotado para el humano.

`ruesma_comun/importes.py` **no** es ruta sensible, y está bien que no lo sea:
la lista cubre lo que los tests unitarios no pueden cubrir (prompts, schemas
que rellena la IA, clientes LLM), y esta función es aritmética pura con 19
tests propios.

## Cambio 1 · R24 por entradas · verificado con mi propia sonda

El guardián queda así (`review_repository.py:3379-3390`):

```python
sin_cambios = (
    self._num_iguales(row["cantidad_albaran"], nueva_cant_albaran)
    and self._num_iguales(row["cantidad_convertida"], nueva_cant_conv)
    and self._num_iguales(
        _sanear_descuento(row["descuento_albaran_aplicado"]),
        _sanear_descuento(descuento),
    )
)
```

Compara **solo entradas**, que es lo que pedía R24, y compara el descuento ya
**saneado** — detalle que no es adorno: el front reenvía el descuento en cada
guardado, y `0` y `NULL` significan lo mismo; sin sanear, todo guardado vería
un cambio inexistente y el guardián no protegería nada.

Verificación propia, la sonda del informe anterior **sin tocar una coma**:

```
RESULTADO: {'importe_calculado': 100.0, 'importe_source': 'declared_albaran'} total: 100.0
1 passed
```

Y los tests que ya existían siguen pasando y **siguen mordiendo**: los seis
nuevos incluyen los tres simétricos que fijan que la línea **sí** cede cuando
el revisor cambia la cantidad (`..._si_cede_si_cambia_la_cantidad`) o el
descuento (`..._si_cede_si_cambia_el_descuento`). Eso es lo que impide que el
arreglo se convierta en «no tocar nunca nada», que habría pasado los tests de
R24 igual de bien y habría roto R23.

La fase RED está documentada con salida real (`RED 7`): 4 failed / 46 passed,
con el `60.0` frente a `100.0` de mi sonda reproducido exactamente.

## Cambio 2 · La fórmula a `ruesma_comun` · qué se movió y qué NO

Esto era lo que más podía torcerse —mover de más y llevarse la política de un
servicio a una librería compartida— y **está bien resuelto**.

**A `ruesma_comun/importes.py` fue solo la función pura**: `clasificar_descuento`
(`ausente` / `cero` / `aplicable` / `invalido`), `factor_descuento` e
`importe_de_linea`. Aritmética y rangos. Leído el módulo entero: no hay
precedencia declarado-vs-calculado, ni motivos de revisión, ni nada que
persista.

**La política se quedó donde estaba**, y lo comprobé leyendo ambos consumidores:

- **sv6** conserva `_close_enough`, la precedencia del declarado con su motivo
  `declared_vs_calculated_mismatch`, el `descuento_aplicado:X%`, el
  `descuento_fuera_de_rango_ignorado:X` auditable y el `0.0` explícito.
  Fijado por `test_f019_r27_la_precedencia_del_declarado_sigue_siendo_de_sv6`
  y `..._sv6_conserva_su_politica_del_cero_explicito`.
- **sv4** conserva la suya, opuesta y también correcta: un `0 %` se persiste
  como `NULL` porque su columna no distingue «0 %» de «sin descuento».

Que las dos políticas sean **distintas sobre el mismo dato** y las dos
correctas es la mejor prueba de que el corte está en el sitio bueno.

**No quedan restos de las copias.** Búsqueda de la multiplicación en el
backend de los tres servicios: solo aparece dentro de `importes.py` —y en un
cuarto punto de sv6 que es tarea de cierre 1, ajeno a este diff—. Los cuerpos
de `_importe_de_linea` (sv4) y del cálculo de `ImporteCalculator` (sv6) han
desaparecido y delegan.

**La divergencia que menciona el implementer es real y está cubierta.** La
verifiqué yo mismo en la tercera pasada leyendo el código anterior: sv6 hacía
`float(descuento_pct)` sin proteger, así que un `'x'` leído de un PDF
**reventaba con `ValueError` en mitad de una valoración por cola**, mientras
sv4 devolvía `None`. Ahora las dos rutas pasan por `clasificar_descuento`, que
no lanza nunca, y hay test de ello en los dos servicios y en `comun`
(`test_un_valor_ilegible_no_produce_importe_ni_excepcion`,
`test_descuento_ilegible_es_invalido_sin_valor`).

## Cambio 3 · El cableado del payload · cubierto

`_cantidades_del_payload` y `_descuentos_del_payload`, con 7 tests
(`test_f019_r23_cableado_payload.py`). El que importa es
`..._los_dos_mapas_no_se_filtran_igual`: fija por test que las cantidades se
filtran con `is not None` y los descuentos **no**, porque un `None` significa
«el revisor ha borrado el descuento» y tiene que llegar al recálculo. Era un
cambio de una palabra que habría devuelto el incidente entero y en silencio;
ahora tiene quien lo vigile.

## Cobertura requisito → test (requisitos nuevos de este round trip)

| Requisito | Test que lo cubre | Estado |
|---|---|---|
| R24 (reformulado: por ENTRADAS) | `..._r24_el_declarado_discrepante_no_se_pisa` + los 2 simétricos (`..._si_cede_si_cambia_la_cantidad` / `..._el_descuento`) + `..._reenviar_el_mismo_descuento_no_es_un_cambio` + `..._cero_y_nulo_son_el_mismo_descuento[0.0/None]` | **[x]** |
| R27 · una única implementación | Identidad en los dos consumidores: sv4 `..._r27_sv4_no_tiene_su_propia_formula`, sv6 `..._r27_sv6_no_tiene_su_propia_formula`; + igualdad de resultado en ambos; + 19 tests de `comun/test_importes.py` | **[x]** |
| R28 · la política NO se comparte | sv6 `..._la_precedencia_del_declarado_sigue_siendo_de_sv6`, `..._sv6_conserva_su_politica_del_cero_explicito`; sv4, su política del `NULL` en los tests de recálculo | **[x]** |
| R29 · cableado cubierto | `test_f019_r23_cableado_payload.py` (7 tests, incl. `..._los_dos_mapas_no_se_filtran_igual`) | **[x]** |

## Tareas de cierre (no requieren otra pasada de review)

### 1. Hay un CUARTO punto que calcula el importe, y es de sv6 · deuda o migración

`services/albaran-valoracion-persist/application/services/valuation_builder.py:1359-1373`
escribe la fórmula a mano para las líneas **sintéticas** (M1-M7):

```python
bruto = float(cantidad) * float(precio_final)
if descuento_heredado is not None and descuento_heredado > 0.0:
    importe_calc = round(bruto * (1.0 - descuento_heredado / 100.0), 2)
```

Está **fuera de este diff** y **no tiene defecto vivo**: lo comprobé
rastreando `descuento_heredado`, que sale de
`parent_record.descuento_albaran_aplicado`, es decir de un valor que
`ImporteCalculator` ya saneó, así que no puede llegar fuera de rango ni
ilegible. Y aplica el descuento correctamente.

Pero **contradice lo que este diff acaba de escribir**: la regla 13 dice ahora
que la fórmula «vive en un único sitio», el módulo dice que «la escriben dos
servicios: sv6 (`ImporteCalculator`) y sv4», y R27 habla de «una única
implementación». Con este site en pie, las tres frases son inexactas, y los
dos guardianes de identidad no lo cubren (miran `importe_calculator` y
`review_repository`, no `valuation_builder`).

Resolución, cualquiera de las dos —**la elige el humano**, igual que ofrecí en
la tercera pasada:

- **(a)** que `valuation_builder` consuma `ruesma_comun.importes` (le sobra
  además el `if descuento > 0.0`, que la función ya resuelve), o
- **(b)** dejarlo como **deuda escrita**: entrada en `harness/features.json`
  y una frase en la regla 13 nombrando el caso de las sintéticas como
  excepción conocida, para que quien lo lea no crea que no existe.

Lo que no es admisible es dejar la afirmación «un único sitio» sin ninguna de
las dos.

### 2. R26 quedó huérfano bajo la sección equivocada

En `specs/F-019-importe-unitario-manda/requirements.md`, el bloque **G7
(R27-R29) se insertó ENTRE R25 y R26**, así que R26 —que es de G6, «el importe
PERSISTIDO»— aparece ahora bajo el título «G7 — Una sola fórmula, un solo
criterio». Mover el encabezado de G7 detrás de R26 lo arregla.

### 3. R24 quedó con dos paréntesis encadenados

Mismo fichero: el párrafo nuevo del round trip 3 se empalmó delante del
paréntesis viejo, y el requisito termina con `…)* *(Hoy un guardado que solo`.
Se lee, pero es un empalme, no una redacción.

### 4. La aritmética de la nota de la campaña de mutación

`progress/mutacion_F-019.md` dice: «Los 7 mutantes nuevos salen de
`ruesma_comun/importes.py`: 6 mueren y el séptimo es el equivalente». El +7 es
el **neto** de la campaña (24 → 31). `importes.py` genera **11** mutantes, de
los que mueren 9 y sobreviven 2; a la vez `review_repository.py` baja de 20 a
13 (la extracción se llevó lógica) e `importe_calculator.py` aporta 3. Los
totales de la tabla son correctos; la frase que los narra, no.

## Observaciones no bloqueantes

1. **Un borde del guardián nuevo cambió de comportamiento sin que conste.** Al
   caer el conjunto `importe_anterior is not None`, una fila con precio y
   cantidad presentes pero `importe_calculado` **NULL** y entradas sin cambios
   ya no se rellena. Medido con una sonda propia:
   `RESULTADO: {'importe_calculado': None, 'importe_source': 'none'}` — antes
   habría quedado en 20,00. No he encontrado camino que produzca esa fila (sv6
   con precio y cantidad siempre calcula; las sintéticas se saltan el bucle
   por `merge_line_id IS NULL`), así que lo doy por inalcanzable hoy. Pero el
   informe lo despacha con «ya no hace falta: una fila sin importe previo
   tampoco tiene entradas distintas», y eso no es exacto: sí cambia, en la
   dirección buena (no tocar), pero cambia.
2. **`clasificar_descuento` trata el `NaN` como inválido** explícitamente
   (`if valor != valor`), con test. Es el detalle que suele faltar cuando un
   número viene de un PDF; bien visto.
3. **`ruesma_comun/importes.py` no exporta nada mutable ni depende de nada**:
   sin imports del proyecto, sin estado, tipado con `object` en la frontera
   para no mentir sobre lo que llega de un PDF. Es la forma correcta de una
   librería compartida y no arrastra a `comun` ninguna dependencia nueva.
4. **La suite de sv4 pasa de 44 a 59 tests** y sigue tardando 0,6 s. El coste
   de la red de seguridad es nulo; el de no haberla tenido fueron tres round
   trips.

## Propuesta de mejora del protocolo (no aplicada, para el humano)

1. **`CHECKPOINTS.md`, C3**: cuando una feature declare que unifica lógica
   compartida, el reviewer debería exigir un **inventario de los puntos que la
   implementan**, no solo de los que el implementer nombra. La tarea de cierre
   1 de esta pasada apareció con un `grep` de treinta segundos sobre los tres
   servicios; sin ese barrido, la afirmación «un único sitio» habría quedado
   escrita en `ARCHITECTURE.md` como verdadera.
2. **Tests de identidad como patrón del arnés.** El
   `assert modulo.funcion is compartida` de esta pasada es mejor red que
   cualquier comparación de resultados: cae aunque la copia nueva sea correcta
   el primer día, que es como empiezan todas las divergencias. Merece estar en
   `docs/CONVENTIONS.md` como forma recomendada de fijar «esto no se copia».
3. Ambas son genéricas: si se aceptan, se portan a `arnes-base` en el mismo
   trabajo (regla de propagación de `CLAUDE.md`).
