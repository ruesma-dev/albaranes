<!-- progress/review_F-027.md -->
# F-027 · Error de ×1000 en el importe: la red KG→TN de `UnitConverter` es código muerto · Review

- **Veredicto: APPROVED**
- Fecha: 2026-08-19
- Rama revisada: `feature/F-027-conversion-kg-tn-muerta`, HEAD `136f69a`,
  11 commits sobre `e95549d`.
- Worktree: `scratchpad/wt-dev`. **Todo lo que aquí se afirma se ejecutó en ese
  worktree.** El árbol principal no se ha tocado ni se ha cambiado su rama.
- Diff revisado: `git diff e95549d..HEAD` (17 ficheros; 2 de producción).

## Nivel de rigor

**`critico`**, declarado en `harness/features.json` y confirmado por
`init.sh` (`niveles: … por defecto critico; umbral de cobertura 80%`).

Puertas que exige: C1–C5 + **fase RED** en los requisitos centrales +
**cobertura** de las líneas cambiadas ≥ 80 % + **campaña de mutación** con
**cero supervivientes** salvo justificación escrita + verificaciones
`MANUAL (humano)` listadas con su comando exacto.

---

## 1. Lo primero: no se ha roto lo que funcionaba

Es el riesgo real de esta feature —el cambio vive en el camino por el que hoy
salen los importes correctos de 17 de 17 líneas del lote— y está cubierto.

| Caso verificado contra el administrativo | Fijado por test | Estado |
|---|---|---|
| Hormigón 224964 · línea base 4 m³ × 99,90 = **399,60 €** | `test_f027_r14_el_hormigon_en_m3_da_exactamente_el_mismo_importe[224964…]` | **pasa** |
| Hormigón 225137 · 9 m³ = **899,10 €** | ídem `[225137…]` | **pasa** |
| Hormigón 1167 · 8 m³ = **799,20 €** | ídem `[1167…]` | **pasa** |
| Mortero 1229 · 3 m³ = **210,00 €** | ídem `[1229…]` | **pasa** |
| Feymaco 2.137.569 · total documento **139,66 €** | `test_f027_r15_los_dos_albaranes_de_feymaco_dan_lo_mismo_que_en_f019` | **pasa** |
| Feymaco 2.139.643 · total documento **19,41 €** | ídem | **pasa** |
| VODALAND A261584 · total **3.393,00 €** | `test_f027_r16_el_a261584_de_vodaland_sigue_valiendo_3393_euros` | **pasa** |

Dos comprobaciones de fondo que el reviewer hace y que no bastaba con leer del
informe:

1. **Las cifras son trazables al origen, no inventadas.** `399,60` y `99,90`
   salen de `progress/revision_hormigones_20260818.md:82,84`; `871,20` y
   `475,60` de las líneas 39, 101-102 y 213-214 del mismo informe; `3.393,00`
   de `progress/revision_resto_lote_20260818.md:55,609`.
2. **Los totales de documento 475,60 € y 871,20 € NO se fijan por test, y es
   correcto que no se fijen**: son `399,60 + 40,00 + 36,00` y `799,20 + 72,00`,
   donde los sumandos extra son líneas sintéticas (incremento por año, carga
   incompleta) que F-027 no toca y que tienen features propias. El test fija la
   parte que el cambio puede mover —la línea base— y el informe del implementer
   lo dice. Los totales completos quedan en el guion MANUAL T10 punto 4, que es
   donde se pueden comprobar de verdad (con la BBDD delante).
   *Reparo menor, no bloqueante: los tests de R15/R16 sí fijan total de
   documento; los de R14 no pueden. Está explicado en el propio fichero.*

**Reutilización en vez de copia**: R15 importa `TOTAL_2137569` / `TOTAL_2139643`
de la suite de F-019 en lugar de copiar los números. Es lo correcto — copiarlos
permitiría que las dos verdades divergieran en silencio, que es la lección que
F-019 pagó cara.

## 2. La segunda mitad del ×1000 (lo más valioso del trabajo)

Con línea derivada, el destino de la conversión pasa de `unidad_albaran` a
`derived_line.unidad_medida`. Verificado en el diff (`valuation_builder.py`
líneas 1033-1044) y por test:

- `test_f027_r6_la_derivada_lleva_la_unidad_del_contrato` — precondición
  medida: la derivada lleva `TN` y 15,43 €/TN.
- `test_f027_r6_se_convierte_hacia_la_unidad_de_la_derivada` — factor 0,001.
- `test_f027_r7_con_kg_leido_el_importe_ya_no_es_de_cientos_de_miles` —
  **468,76 €** de línea y de cabecera, con aserción explícita `!= 468763.4`.
- `test_f027_r6_derivada_sin_linea_de_contrato_se_comporta_igual_que_antes` y
  `test_f027_r6_sin_derivada_el_destino_sigue_siendo_la_unidad_de_contrato` —
  los dos casos de compatibilidad. El cambio es un **superconjunto correcto**
  del comportamiento anterior, no una inversión.

Además lo confirmé **rompiéndolo**: el mutante M5 (destino de la derivada →
`unidad_albaran`, es decir, volver al código de antes) mata 14 tests. Ver §6.

Comprobación adicional del reviewer sobre los caminos vecinos que el diff no
menciona: la derivada de fallback `nueva_derived` (`valuation_builder.py:964-
1005`, `origen='nueva_no_match'`) **no** participa en la decisión de destino —
la conversión mira `partida_result.derived_line`. Revisadas sus dos ramas: (a)
cuando la IA sí casó línea de contrato, `unidad_contrato` es la de esa misma
línea, que es también la unidad y el precio de la derivada, así que el destino
es el correcto; (b) cuando no casó nada, `contrato_line` es `None`, el destino
es `None`, el conversor devuelve factor 1 y el precio es el del albarán, que es
coherente. No hay un tercer ×1000 escondido por ahí.

## 3. La guarda de cantidad ausente sigue protegiendo

- `test_f027_r8_sin_cantidad_no_hay_nada_que_reinterpretar` (conversor).
- `test_f027_r8_sin_linea_de_albaran_la_cantidad_sigue_siendo_ausente`.
- `test_f027_r8_una_linea_sin_contexto_de_albaran_no_inventa_cantidad` — el
  caso duro: la línea de IA3 apunta a un `merge_line_id` ausente del contexto,
  `albaran_line is None`, y la línea queda **sin importe**
  (`importe_source == "none"`), no con 0,00 € «calculado».

Ese último test no estaba en la spec: lo escribió la campaña de mutación (M7
sobrevivía). Es exactamente para lo que sirve la puerta.

## 4. Los dos riesgos asumidos, fijados por test (no en prosa)

Era condición de aprobación y se cumple:

- **D2** (se convierte también cuando IA3 declara desacuerdo de unidades):
  `test_f027_d2_se_convierte_aunque_ia3_declare_desacuerdo_de_categoria`, con
  `unidad_category_match_ia=False` → convierte a 30,38, importe 468,76 € **y**
  `review_required is True` con `ia_unit_category_mismatch`.
- **D3** (el umbral de 1000 reinterpretaría un albarán legítimo de 1.200 TN):
  `test_f027_d3_mil_unidades_legitimas_contra_un_contrato_en_tn_se_dividen`,
  que fija el comportamiento **y** su contrapartida (`review_required is True`).
  El docstring dice literalmente que el test «no celebra el comportamiento: lo
  deja escrito para que cambiarlo sea una decisión explícita». Correcto.

## 5. Los motivos distinguen los cuatro estados (R19)

`test_f027_r19_cada_estado_emite_su_motivo_y_solo_el_suyo`, parametrizado con
los cuatro casos, comprueba **el motivo propio y la ausencia de los otros
tres**, más `cantidad_convertida` y `factor_conversion`:

| Estado | Motivo | convertida / factor |
|---|---|---|
| Se convirtió con la red de plausibilidad | `cantidad_sin_unidad_reinterpretada_kg_a_tn` | 30,38 / 0,001 |
| Sospechosa pero no se tocó | `cantidad_tn_implausible_revisar` | 500 / 1,0 |
| No se pudo convertir | `unit_category_mismatch_in_conversion` (+ `importe_using_albaran_quantity_fallback`) | None / None |
| La cantidad falta de verdad | `no_quantity_in_albaran` | None / None |

El revisor humano ve la reinterpretación además en números: R20 comprueba las
tres columnas y su coherencia aritmética
(`cantidad_albaran × factor == cantidad_convertida`), y sv4 ya las lee.

## 6. C4 bis · mutación — verificada de forma independiente

**No me he fiado del informe. Recalculado y muestreado:**

**a) Alcance.** `harness.alcance.alcance_de_feature('F-027')` → origen `rama`;
`unit_converter.py` 24 líneas, `valuation_builder.py` 34, total **58**.
Coincide exacto con `progress/mutacion_F-027.md`.

**b) Mutantes en alcance.** `harness.mutacion.generar_mutantes` (cálculo puro)
sobre esas líneas → **0 y 0**. Coincide.

**c) Prueba de control del cero (obligatoria).** El mismo generador sobre los
**ficheros enteros**, ignorando la exclusión de alcance: **15 mutantes** en
`unit_converter.py` y **213** en `valuation_builder.py`. El generador funciona;
el cero es legítimo, no un fallo de la herramienta ni un informe falso.

**d) Por qué el cero es legítimo, comprobado y no aceptado de palabra.**
`ast.Is` y `ast.IsNot` **no están** en `harness.mutacion.COMPARACIONES`
(verificado: `['Eq','Gt','GtE','Lt','LtE','NotEq']`), y las líneas del diff que
no son comentario son exactamente **nueve renglones / cuatro sentencias**:
un `if … is not None`, dos asignaciones y una llamada con un `IfExp`. Además,
de las 24 líneas en alcance de `unit_converter.py`, **0 son código**: T6 fue
documentación pura. Lo verifiqué línea a línea, no leyendo la tabla del
informe.

**e) «Manuales» está justificado**, por (c) y (d): la herramienta no llega a
ese código, y arreglarla dentro de F-027 habría cambiado la vara de medir de
todas las features de todos los proyectos. Queda propuesto al humano en
`progress/current.md` y en §9 de este informe.

**f) Muestreo de supervivientes/mutantes declarados.** Los 7 mutantes se
declaran muertos; muestreé **cuatro** aplicándolos a una copia aislada de sv6
en el scratchpad (nunca al árbol real) y ejecutando su suite entera, en serie.
Los recuentos de fallos coinciden **exactamente** con los declarados:

| Mutante | Declarado | Medido por el reviewer |
|---|---|---|
| M1 `derived_line is not None` → `is None` | MUERTO (17 fallos) | **17 failed, 93 passed** |
| M2 `cantidad=… if albaran_line else None` → `cantidad=None` (restaura el defecto) | MUERTO (26 fallos) | **26 failed, 84 passed** |
| M5 destino de la derivada → `unidad_albaran` (la otra mitad del ×1000) | MUERTO (14 fallos) | **14 failed, 96 passed** |
| M7 `else None` → `else 0.0` | MUERTO (1 fallo) | **1 failed, 109 passed**, y el que falla es justo `test_f027_r8_una_linea_sin_contexto_de_albaran_no_inventa_cantidad` |

Control previo: la copia sin mutar sale **110 passed**. Copia borrada al
terminar; `git status` del worktree limpio.

**M7 merece constar**: sobrevivió en la primera pasada del implementer y el
informe lo cuenta en vez de esconderlo. Es honestidad verificable — el test que
lo mata existe, y sin él el mutante vuelve a sobrevivir (medido: con el test
presente, 1 fallo; el agujero era real).

**Cero supervivientes, nivel `critico`: cumplido.**

## 7. C4 ter · rutas sensibles — `NO_EVALUABLE` legítimo

El diff toca 2 rutas declaradas en `harness/rutas_sensibles.json`
(`unit_converter.py` y `valuation_builder.py`, patrón
`services/albaran-valoracion-persist/application/services/**`, motivo «redes
deterministas de sv6»). Comprobado por el reviewer:

- **Existe** `progress/evals_F-027.md`, con veredicto `NO_EVALUABLE`.
- **No cumple** `exige_lineas` (`MODO: completa`, `FASES: IA1,IA2,IA3,IA4,E2E`,
  `VEREDICTO: VERDE`): trae `MODO: determinista` y `FASES: IA3,IA4,E2E`.
- **El motivo consta por escrito** y lo verifiqué de forma independiente:
  `evals/fixtures/inputs/` contiene **solo `_indice.json`**, es decir **cero
  casos**, así que la pasada completa daría `NO_EVALUABLE` igual aunque
  hubiera claves. (Las claves `GEMINI_API_KEY` / `OPENAI_API_KEY` faltan por
  ser secretos, correctamente ausentes del repositorio.)
- **Es FRESCO**: se generó en `cee5fb2` y se commiteó en `e75ddab` (T9), ambos
  posteriores al último commit que tocó ruta sensible (`fcf88b0`, T6; el código
  se cambió antes, en `e24a0d9`, T5). No es un verde de antes del cambio.
- Exigencia declarada **`aviso`** (decisión D5 de F-011): no bloquea, y el
  motivo queda escrito aquí, que es lo que C4 ter pide. **No se marca N/A a
  secas.** Mismo estado en que cerró F-019.

## 8. Alcance — ni se ha salido ni ha invadido a las vecinas

- **F-031 (el precio)**: el 58826 queda en **468,76 €**, no en los 390,99 € del
  administrativo, y así lo fijan los tests **con los dos precios** (15,43 y
  12,87), de modo que en la prueba local se podrá separar qué feature produjo
  qué euro. `partida_matcher.py` no aparece en el diff. Correcto según D4/R23.
- **F-024 (la unidad que IA1 no extrae)**: ningún prompt ni schema tocado
  (verificado con `git diff --name-only`). La feature deja el camino
  **preparado**, no resuelto: R24 y el informe insisten en que la revisión
  razonada de IA2 sigue siendo necesaria.
- **F-025 (`no_quantity_in_albaran` falso)**: no se renombra, añade ni retira
  ningún motivo — y no es una promesa, lo vigila
  `test_f027_r22_el_builder_no_introduce_ni_retira_motivos`, que compara por
  AST el inventario de literales del fichero contra un conjunto congelado. El
  implementer demostró que ese test **no es vacuo** inyectando en una copia el
  motivo que F-025 proponía (§6.5 del informe): falla como debe.
- Ficheros tocados = los previstos en `design.md` §2 (más los tests y los
  informes). Ninguno de la lista «NO se tocan» de §3 aparece en el diff.

## 9. Recorrido de CHECKPOINTS.md

### C1 — Arnés completo y en verde
- [x] `bash harness/init.sh` → **ENTORNO LISTO**, exit 0. Ejecutado por el
      reviewer en el worktree.
- [x] Existen los ocho ficheros obligatorios.
- Avisos no bloqueantes que arrastra el repositorio y no introduce F-027: ruff
  (1101, deuda previa), sv1-email sin tests, infra sin `comando_tests`.

### C2 — Estado coherente
- [x] Una sola feature `in_progress`: F-027.
- [x] Rama `feature/F-027-conversion-kg-tn-muerta`.
- [x] `progress/current.md` describe solo la sesión activa; el bloque
      «Pendientes del humano» es cola de decisiones, no resto de sesión.
- [x] No hay `done` nueva sin resumen en `history.md` (F-027 aún no es `done`).

### C3 — Arquitectura y convenciones
- [x] Hexagonal: el cambio vive entero en `application/services/`; no añade un
      solo import de infraestructura al dominio ni a la aplicación.
- [x] Primera línea con la ruta relativa en los 8 `.py` del diff (verificado
      uno a uno).
- [x] Sin `print()`, sin TODO/FIXME, sin secretos (grep sobre las líneas `+`
      del diff: `print(`, `TODO`, `FIXME`, `password`, `api_key`, `secret`,
      `conn_str` → **cero**). Sin dependencias nuevas.
- [x] Reglas de dominio: la trampa (3) de C3 —«no mezclar unidades sin pasar
      por el conversor»— es literalmente el objeto de la feature, y la regla 8
      de `docs/ARCHITECTURE.md` se amplía para que «pasar por el conversor»
      signifique **pasarle la cantidad**. Las trampas (1) y (2) no aplican: no
      se toca schema ni se lee de tablas raw.
- Nota menor de estilo, no bloqueante: ruff señala 4 avisos `I001` (orden de
  imports) en los ficheros de test nuevos. `docs/CONVENTIONS.md` no exige ruff
  limpio y el proyecto arrastra 1101 avisos; se deja anotado, no se exige.

### C3 bis — Documentos de fuera
- **N/A justificado**: el diff no añade ni modifica ningún fichero de
  `docs/referencia/` (verificado con `git diff --name-only`). No hay PDF ni
  ofimática en el árbol ni en el historial de la rama, y por tanto no hay
  barrido de datos sensibles que ejecutar sobre documentos nuevos.

### C4 — La verificación es real
- [x] Cada requisito EARS tiene ≥ 1 test trazable y todos pasan (tabla en §10).
- [x] Los unit tests no tocan red, BBDD ni LLM: el único fichero de disco es
      `config/unit_registry.yaml`, dato versionado del propio servicio.
      Verificado leyendo `f027_escenarios.py` (monta los cinco colaboradores
      reales a mano) y los cuatro ficheros de test.
- [x] `MANUAL (humano)`: T10 listada en `progress/current.md` con sus seis
      puntos y el guion completo (comandos + SQL) en `impl_F-027.md` §8.
      T10 sigue en `[ ]`, que es lo correcto: marcarla `[x]` sería falso.
      Misma convención aceptada en F-002 y F-019.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "critico"` declarado en `features.json`.
- [x] **Fase RED**: cinco trazas reales pegadas en `impl_F-027.md` §6, con la
      salida literal de pytest. Las centrales:
      `assert 468763.4 != 468763.4 ± 0.468763` (R11) y
      `assert 30380.0 == 30.38` (R7). Para T1 y T7, cuyo entregable es el
      propio test, la RED se demuestra rompiendo lo vigilado **en copia
      aislada** (umbral a 100000, motivo inyectado), como manda C4 bis.
      Contraprueba del reviewer: al restaurar el defecto en copia aislada
      (mutantes M2 y M5) la suite se pone roja como describe el informe.
- [x] **Cobertura**: `PUERTA COBERTURA: 100.0% de 4 líneas cambiadas cubiertas
      (4/4, umbral 80%, nivel critico)`, en `[OK]`.
- [x] **Mutación**: `progress/mutacion_F-027.md` existe, generado por la
      herramienta, con totales **recalculados por el reviewer** (§6 a-c).
- [x] **Cero supervivientes**, con 4 de 7 mutantes muestreados y confirmados
      (§6 f). Ninguna sección en `PENDIENTE`.
- [x] **Evidencias**: la sección existe en `impl_F-027.md` con los cuatro
      números — 635 tests / 100 % (4/4) / 7 mutantes 0 supervivientes / 58,5 s.
- [x] Ningún punto marcado N/A.

### C4 ter — Rutas sensibles
- [x] Existe `progress/evals_F-027.md`.
- [ ] No cumple `exige_lineas` — **y es correcto que no las cumpla**: cero
      casos en `evals/fixtures/inputs/`, exigencia declarada `aviso`, motivo
      escrito aquí y en el informe. Ver §7. No bloquea el cierre.
- [x] El informe es **FRESCO** (posterior a los commits de ruta sensible).
- [x] El motivo del `aviso` incumplido consta por escrito (§7).

### C5 — La sesión se cerró bien
- [x] `tasks.md`: T1-T9 y T11 en `[x]`, un commit `F-027 Tn:` por tarea (11
      commits, todos con el prefijo). T10 en `[ ]` por ser MANUAL del humano.
- [x] Árbol limpio: `git status --short` sin salida; ningún artefacto suelto.
      (La copia que usé para muestrear la mutación vivía en el scratchpad y
      está borrada.)
- [x] `features.json` refleja el estado real (`in_progress`) y `BACKLOG.md`
      está al día — lo valida `init.sh`.

---

## 10. Cobertura requisito → test

| R | Test(s) | Dónde |
|---|---|---|
| R1 | `test_f027_r1_el_builder_convierte_aunque_el_guard_diga_que_no`, `test_f027_r1_sin_unidad_de_destino_la_cantidad_pasa_con_factor_1` | sv6 builder |
| R2 | `test_f027_r2_el_desacuerdo_de_categoria_sigue_mandando_a_revision` | sv6 builder |
| R3 | `test_f027_r3_cantidad_sin_unidad_contra_tn_se_reinterpreta_como_kg[58826/58878]`, `…_el_umbral_de_1000_es_inclusivo`, `…_la_red_reconoce_los_literales_de_tonelada[TN,tn,Tn.,t,TM,Ton]` | sv6 conversor |
| R4 | `test_f027_r4_cantidad_entre_100_y_1000_solo_avisa`, `test_f027_r4_cantidad_plausible_de_toneladas_no_se_toca_ni_se_avisa`, `test_f027_r4_desde_el_builder_la_cantidad_implausible_solo_se_avisa` | conversor + builder |
| R5 | `test_f027_r5_unidades_de_categorias_distintas_no_se_convierten`, `test_f027_r5_kg_contra_tn_con_ambas_unidades_si_se_convierte`, `test_f027_r19_no_convertible_cae_al_fallback_con_la_cantidad_cruda` | conversor + no-regresión |
| R6 | `test_f027_r6_la_derivada_lleva_la_unidad_del_contrato`, `…_se_convierte_hacia_la_unidad_de_la_derivada`, `…_derivada_sin_linea_de_contrato_se_comporta_igual_que_antes`, `…_sin_derivada_el_destino_sigue_siendo_la_unidad_de_contrato` | sv6 unidad-destino |
| R7 | `test_f027_r7_con_kg_leido_el_importe_ya_no_es_de_cientos_de_miles`, `test_f027_r7_la_cantidad_cruda_se_conserva_junto_a_la_convertida` | sv6 unidad-destino |
| R8 | `test_f027_r8_sin_cantidad_no_hay_nada_que_reinterpretar`, `…_sin_unidad_de_contrato_la_cantidad_se_devuelve_tal_cual`, `…_sin_linea_de_albaran_la_cantidad_sigue_siendo_ausente`, `…_una_linea_sin_contexto_de_albaran_no_inventa_cantidad` | conversor + builder |
| R9 | `test_f027_r9_cantidad_cero_es_cantidad_presente` | sv6 conversor |
| R10 | `test_f027_r10_una_linea_con_cantidad_no_puede_decir_que_no_la_tiene` | sv6 builder |
| R11 | `test_f027_r11_el_58826_no_vale_468763_euros`, `test_f027_r11_el_58826_con_el_precio_correcto_da_el_numero_del_gt` | sv6 builder |
| R12 | `test_f027_r12_el_58878_no_vale_462282_euros`, `test_f027_r12_el_58878_con_el_precio_correcto_da_38559` | sv6 builder |
| R13 | `test_f027_r13_el_total_del_documento_esta_en_centenas_de_euros[58826, 58878]` | sv6 builder (`build` completo) |
| R14 | `test_f027_r14_el_hormigon_en_m3_da_exactamente_el_mismo_importe[×4]`, `…_pasa_a_convertirse_con_factor_1[×4]`, `…_con_partida_cruzada_tampoco_mueve_el_importe` | sv6 no-regresión |
| R15 | `test_f027_r15_los_dos_albaranes_de_feymaco_dan_lo_mismo_que_en_f019` (reutiliza los datos de F-019) | sv6 no-regresión |
| R16 | `test_f027_r16_el_a261584_de_vodaland_sigue_valiendo_3393_euros` | sv6 no-regresión |
| R17 | `test_f027_r17_unidad_ambigua_convierte_con_factor_1_y_marca_revision`, `test_f027_r17_desde_el_builder_el_saco_convierte_con_factor_1_y_revisa` | conversor + no-regresión |
| R18 | `test_f027_r18_los_umbrales_de_la_red_de_toneladas_no_cambian[×2]`, `…_la_firma_publica_de_convert_no_cambia`, `…_la_categoria_mass_del_registro_de_unidades_no_cambia` | suite raíz |
| R19 | `test_f027_r19_cada_estado_emite_su_motivo_y_solo_el_suyo[×4]`, `…_no_convertible_cae_al_fallback_con_la_cantidad_cruda`, `test_f027_r19_los_cuatro_motivos_de_la_tabla_existen_en_el_conversor` | sv6 + raíz |
| R20 | `test_f027_r20_la_reinterpretacion_deja_las_tres_columnas_coherentes` | sv6 no-regresión |
| R21 | `test_f027_r21_la_reinterpretacion_deja_traza_en_el_log` (`caplog`) | sv6 conversor |
| R22 | `test_f027_r22_el_builder_no_introduce_ni_retira_motivos`, `…_el_conversor_no_introduce_ni_retira_motivos` (inventario por AST) | suite raíz |
| R23 | `test_f027_r23_el_matcher_sigue_dando_a_la_derivada_la_unidad_del_contrato`, `test_f027_r23_r24_la_feature_no_toca_ni_el_matcher_ni_ningun_prompt` | suite raíz |
| R24 | `test_f027_r23_r24_la_feature_no_toca_ni_el_matcher_ni_ningun_prompt` | suite raíz |
| R25 | Puerta de `init.sh` + `progress/evals_F-027.md` (§7) | arnés |
| R26 | Sin código por diseño (D5). Decisión anotada en `current.md` | — |
| R27 | **MANUAL (humano)**, T10 punto 5 | pendiente |
| D2 | `test_f027_d2_se_convierte_aunque_ia3_declare_desacuerdo_de_categoria` | sv6 builder |
| D3 | `test_f027_d3_mil_unidades_legitimas_contra_un_contrato_en_tn_se_dividen` | sv6 builder |

**Sin requisitos huérfanos.** 66 tests de F-027 (57 en sv6, 9 en la raíz),
todos verdes; suites completas: sv6 **110 passed**, raíz **262 passed**, total
del arnés en verde.

---

## 11. Observaciones para el humano (no bloquean el cierre)

1. **Las decisiones abiertas D2 y D3** (`design.md` §9) pedían validación
   explícita del humano. Están **implícitamente aprobadas** al aprobar la spec
   —R1 obliga a convertir «con independencia de `unidad_category_match`» (D2) y
   R3/R18 congelan el umbral de 1000 (D3)— y ahora están fijadas por test. Aun
   así conviene que el humano las confirme al leer el cierre: si algún día
   quiere revertirlas, tendrá que tocar un test, que es justo lo que se buscaba.
2. **T10 sigue pendiente y es la que cierra el círculo.** El nivel `critico`
   exige el resultado real de las verificaciones MANUAL; lo que hay hoy es el
   guion. La feature puede aprobarse (los números están fijados por test, no
   solo por guion — lección de F-019 aplicada), pero el punto 4 de T10 (los
   totales 475,60 € y 871,20 € de documento) es el único sitio donde se
   comprueban esos dos agregados completos.
3. **El histórico sigue mal en BBDD** (468.763,40 € y 462.282,80 €
   persistidos). Por diseño (R26/D5) no hay backfill: se sanean revalorando
   desde sv4. Falta decidir cuáles y cuándo.

## 12. Automejora del arnés (propuestas, no aplicadas)

1. **`harness/mutacion.py` no muta `is` / `is not`.** Confirmado por el
   reviewer sobre la propia tabla `COMPARACIONES`. En Python, `x is None` es
   **la** guarda de ausencia: el punto ciego afecta a cualquier feature de
   cualquier proyecto, y en esta ha obligado a una campaña manual. **Propuesta:
   añadir `ast.Is`/`ast.IsNot` a `COMPARACIONES` y portarlo a `arnes-base`.**
   Coincido con el implementer en que hacerlo dentro de F-027 habría sido
   incorrecto: cambia la vara de medir de todas las features. Lo decide el
   humano.
2. **`CHECKPOINTS.md` C4 ter habla de `evals/ground_truth/`, que no existe en
   este repositorio**: los casos se buscan en `evals/fixtures/inputs/`. La
   misma referencia aparece en `current.md` y en `rutas_sensibles.json`.
   Propuesta: unificar el nombre en los tres sitios para que la puerta se pueda
   comprobar sin adivinar dónde mirar.
3. **La campaña manual de mutación no deja rastro reproducible en el
   repositorio** (el guion vive en el scratchpad de la sesión). Aquí ha
   bastado porque las siete sustituciones están escritas con su texto exacto y
   he podido reproducir cuatro al pie de la letra. Propuesta para
   `CHECKPOINTS.md`: cuando la campaña automática dé 0 mutantes y se sustituya
   por una manual, exigir que la tabla incluya el **texto exacto original →
   mutado** de cada sustitución (como aquí), que es lo que la hace verificable.

---

**Veredicto final: APPROVED.** El defecto de tres órdenes de magnitud está
corregido en sus dos mitades, con la cantidad real llegando al conversor y el
destino apuntando a quien pone el precio; lo que funcionaba no se mueve y hay
test que lo vigila; los riesgos asumidos están escritos en tests y no en prosa;
y la puerta de mutación, aunque la herramienta no llegue a este código, se ha
cruzado de verdad — muestreada y reproducida por el reviewer.
