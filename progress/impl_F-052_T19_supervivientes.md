<!-- progress/impl_F-052_T19_supervivientes.md -->
# F-052 T19 · Supervivientes de la primera campaña y cómo murieron

Detalle de T19 (implementer, 2026-10-01). El informe válido para la puerta es
`progress/mutacion_F-052.md` (campaña final, en serie, sobre el commit con los
tests); aquí queda lo que esa campaña ya no enseña: los 44 supervivientes de la
primera, qué test mata a cada uno y la traza RED.

## 1. Primera campaña (paralela, 4 workers, HEAD `07f89cf`)

`python -m harness.mutacion --feature F-052` → 220 generados, 176 muertos,
**44 supervivientes**, 0 timeouts, 0 sin veredicto, 801,9 s. Coste por mutante
= 801,9 × 4 ÷ 220 = 14,6 s (bases: sv3 ≈ 12 s, sv4 ≈ 19 s, comun ≈ 42 s).

**Anomalía: 2 de los 44 eran falsos supervivientes.** Reevaluados en serie con
la propia maquinaria del arnés (`ejecutar_campania` sobre un worktree de
`07f89cf`, sin tests nuevos) **mueren** con los tests que ya existían:

| Mutante | Test que ya lo mataba |
|---|---|
| `sigrid_api_contrato_client.py:1081` `if self._transport is not None` → `is None` | `test_f052_doble_cliente_con_transport_inyectado_habla_con_el_doble` (`httpx.ConnectError`, va a la red) |
| `verificar_f052_proveedores_obra.py:331` `if cif and …` → `if cif or …` | `test_f052_r29_normaliza_la_obra_como_sv3` (espera código 0) |

Los otros 42 sobrevivieron también en serie: el resultado de la paralela no es
de fiar en esos dos casos y no he encontrado la causa (mismo intérprete, mismo
comando, worktree propio por worker). Error en la dirección «conservadora»
(supervivientes de más), pero por eso la campaña final se lanzó con
`--workers 1`. **Hallazgo para el arnés** (posible mejora de `arnes-base`):
no lo toco aquí.

## 2. Tests nuevos (commit `dcca978`, sin cambios de producción)

Tres ficheros `tests/test_f052_t19_supervivientes.py` (comun, sv4, sv3).

| Fichero:línea (mutantes) | Test que lo mata |
|---|---|
| `lectura.py:172` (`<= 1`, `< 2`) | comun `test_f052_t19_pagina_de_una_fila_es_valida` |
| `lectura.py:176` (`+ 2`, `- 1`) | comun `test_f052_t19_pagina_por_encima_del_tope_dice_el_max_rows_que_pediria` |
| `lectura.py:180` (`<= 1`, `< 2`) | comun `test_f052_t19_una_sola_pagina_como_tope_es_valida` |
| `lectura.py:193` (`+ 2`, `- 1`) | comun `test_f052_t19_pagina_de_mas_dice_su_numero_1_based` |
| `lectura.py:204` (`+ 2`, `- 1`) | comun `test_f052_t19_pagina_marcada_truncada_dice_su_numero_1_based` |
| `review_service.py:152` (`count=1`) | sv4 `test_f052_t19_si_relanzar_falla_el_outcome_no_trae_contratos` |
| `review_models.py:1126` (default `True`) | sv4 `test_f052_t19_save_response_por_defecto_no_relanzo_la_busqueda` |
| `app.py:913` (`buscando` default `True`) | sv4 `test_f052_t19_detalle_sin_buscando_en_la_url_no_marca_buscando` |
| `app.py:1114` (`buscar_si_cambia` default `True`) | sv4 `test_f052_t19_put_sin_buscar_si_cambia_no_pasa_cliente_de_refetch` |
| `app.py:1142` (`is None`) | sv4 `test_f052_t19_put_*` (los tres) |
| `header_resolver_service.py:290` (`is None`, `or`) | sv3 `test_f052_t19_obra_valida_no_se_busca_por_texto`, `…_obra_invalida_se_deduce_por_texto` |
| `sigrid_api_contrato_client.py:250` (`21`) | sv3 `test_f052_t19_tope_de_paginas_por_defecto_es_20` |
| `sigrid_api_contrato_client.py:261`, `:265` (`1 <`, `2 <=`) | sv3 `test_f052_t19_cliente_admite_una_fila_por_peticion_y_por_pagina` |
| `sigrid_api_contrato_client.py:934` (`and ""`) | sv3 `test_f052_t19_agregada_con_dos_nombres_se_queda_el_primero_por_nombre` |
| script `:46` (`parents[2]`) | sv3 `test_f052_t19_script_arranca_como_script_desde_otra_carpeta` (subproceso) |
| script `:109`, `:117` (`frozen`, `compare`) | sv3 `test_f052_t19_medicion_es_inmutable_y_se_compara_sin_la_sql` |
| script `:122` (`retries=2`) | sv3 `test_f052_t19_transporte_real_con_un_reintento` |
| script `:298` (`and '-'`) | sv3 `test_f052_t19_r29_cabecera_con_y_sin_cif` |
| script `:329` (`+`) | sv3 `test_f052_t19_r29_cuenta_las_llamadas_fallidas` |
| script `:332` (`+`) | sv3 `test_f052_t19_r29_cuenta_las_respuestas_sin_el_cif` |
| script `:352` (`[:6]`) | sv3 `test_f052_t19_r29_lista_los_cinco_mejores_por_nombre` |
| script `:359` (`>`) | sv3 `test_f052_t19_r29_score_igual_al_umbral_es_propuesta` |
| script `:385` (`and ''`) | sv3 `test_f052_t19_r29_lista_cada_contrato_con_su_nombre` |
| script `:388` (`or 1`) | sv3 `test_f052_t19_r29_filas_de_header_and_lines_suman_las_reales` |
| script `:413` (`-=`, `+= 2`) | sv3 `test_f052_t19_r30_resultado_con_error_cuenta_una_obra` |
| script `:422` (`lineas[1]`) | sv3 `test_f052_t19_r30_obra_con_una_sola_linea` |
| script `:441`, `:442` (×3) | sv3 `test_f052_t19_r30_resultado_cuenta_diferencias_y_cif_distintos` |
| script `:490` (`default=2`) | sv3 `test_f052_t19_r29_por_defecto_una_repeticion` |
| script `:48` (`insert(1)`) | ninguno: **EQUIVALENTE, PROPUESTA** (ver `progress/mutacion_F-052.md`) |

RM6: ningún mutante se mató quitando código defensivo; solo se añadieron tests.

## 3. Fase RED (trazas reales)

**Por lotes, con la maquinaria del arnés.** Script de apoyo (scratchpad) que
reconstruye cada superviviente con `generar_mutantes` y lo juzga con
`ejecutar_campania` (suite COMPLETA de su servicio, `-x`, sin bytecode) sobre un
worktree de `07f89cf`:

- sin los tests nuevos: `SUPERVIVIENTES 42 MUERTOS 2` (los dos falsos del §1);
- con los tres ficheros de tests copiados al worktree:
  `SUPERVIVIENTES 1 MUERTOS 43` — el único vivo es
  `[24/44] superviviente …verificar_f052_proveedores_obra.py:48 [entero] sys.path.insert(0, …) -> sys.path.insert(1, …)`.

**Una a una, tres centrales** (mutante aplicado a mano en el worktree,
`python -m pytest -q --tb=line -p no:cacheprovider tests/test_f052_t19_supervivientes.py`):

```
# comun, lectura.py:172  if pagina < 1: -> if pagina < 2:
…lectura.py:173: ValueError: leer_paginado: pagina debe ser >= 1, no 1
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_pagina_de_una_fila_es_valida
1 failed, 4 passed in 0.03s

# sv3, header_resolver_service.py:290  ... is not None: -> ... is None:
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_obra_valida_no_se_busca_por_texto
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_obra_invalida_se_deduce_por_texto[12345]
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_obra_invalida_se_deduce_por_texto[1234]
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_obra_invalida_se_deduce_por_texto[abc]
4 failed, 17 passed in 1.61s

# sv4, app.py:1142  busqueda_relanzada=busqueda is not None -> is None
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_put_sin_buscar_si_cambia_no_pasa_cliente_de_refetch
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_put_con_buscar_si_cambia_relanza_y_lo_dice
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_put_con_buscar_si_cambia_sin_relanzar_no_lo_dice
3 failed, 3 passed in 2.04s
```

Sin mutantes, verde: comun `5 passed`, sv4 `6 passed`, sv3 `21 passed`; suites
completas `421 passed` (sv3), `378 passed` (sv4), `332 passed` (comun).

## 4. Campaña final (en serie, `--workers 1`, HEAD `dcca978`)

`python -m harness.mutacion --feature F-052 --workers 1` → 220 generados, **218
muertos, 2 supervivientes**, 0 timeouts, 0 sin veredicto, 1.368,7 s; bases
comun 19,4 s, sv4 9,7 s, sv3 5,5 s; media 6,2 s × 1 worker. Informe:
`progress/mutacion_F-052.md`. Los dos supervivientes, ambos como PROPUESTA
para el humano:

- `verificar_f052_proveedores_obra.py:48` `insert(0` → `insert(1`:
  **equivalente** (argumento y demostración en el informe).
- `ruesma_comun/obras/codigo.py:39` `"0" + limpio` → `"0" - limpio`: **falso
  superviviente**. Lo matan tests que ya existían; reevaluado aislado en un
  worktree limpio de `dcca978` sale muerto, y en la campaña paralela también.
  Es el mismo fenómeno del §1, ahora en serie: un muerto contado como vivo de
  vez en cuando, sin causa encontrada.
