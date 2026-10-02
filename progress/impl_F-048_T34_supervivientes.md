<!-- progress/impl_F-048_T34_supervivientes.md -->
# F-048 · T34 · Los 26 supervivientes, uno por uno

Cierre de **T34** (R44): campaña de mutación completa y **cero supervivientes sin justificar**.
La campaña **no se ha vuelto a lanzar**: se trabaja sobre la que midió `e7fe2c0`
(`progress/mutacion_F-048.md`), **reinyectando a mano** cada superviviente en una copia aislada.

| | |
|---|---|
| Informe de la campaña | `progress/mutacion_F-048.md`, versionado en `70f9498` tal cual salió; después, sus 26 análisis completados (ninguno `PENDIENTE`) |
| HEAD medido | `e7fe2c0750cf8c8417cbd5f9e44c955842529474` |
| Alcance | 34 ficheros, 1883 líneas; 175 mutantes, sin muestreo, 4 workers, 617,2 s |
| Veredicto de la campaña | 149 muertos · 26 supervivientes · 0 timeouts · 0 sin veredicto |
| **Veredicto tras T34** | **172 muertos · 3 supervivientes, los 3 equivalentes justificados** |
| **Supervivientes sin justificar** | **0** |
| Defectos de producción encontrados | **Ninguno**. No se ha tocado código de producción |

Commits: `70f9498` (informe) · `a29fa68` (tests sv2 y comun) · `7317fc6` (tests y guardas sv1 y sv4)
· `7b8adab` (demostración diferencial de 22 y 23) · el de este informe (análisis, inventario, tasks).

## 1. Cómo se ha verificado cada uno

Script `reinyectar.py` en el scratchpad (no versionado). Para cada mutante:

1. copia limpia del servicio (`shutil.copytree` sin `.venv`, `__pycache__` ni `.env`); para los
   tres equivalentes, **`git worktree add --detach` de HEAD**, porque la suite de sv1 tiene tests
   que preguntan a `git check-ignore` y fuera de un repositorio fallan dos (comprobado: 2 failed,
   95 passed en la copia plana, SIN mutante);
2. tests **sin** mutante → deben pasar;
3. sustitución del texto exacto **solo en la línea indicada** (el script aborta si el original no
   está exactamente una vez en esa línea) → tests **con** mutante;
4. borrado de la copia o `git worktree remove --force`. El árbol real no se toca.

Huecos: se lanza el fichero de test nuevo del servicio (si lo mata el fichero, lo mata la suite).
Equivalentes: se lanza la **suite entera** de sv1. Intérprete: el del arnés, salvo sv4 (su `.venv`).

## 2. Los 26

M = muerto con el mutante puesto; «sin» = resultado sin mutante. Tests nuevos, en
`services/<servicio>/tests/test_f048_t34_supervivientes.py`.

| # | Fichero:línea | Mutante | Veredicto | Test que lo mata o justificación | Sin → con mutante |
|---|---|---|---|---|---|
| 1 | `albaran_extraction_service.py:454` | `and` → `or` | Hueco | `r14_con_marcador_de_sigrid_el_grounding_sale_una_sola_vez`, `r14_sin_marcador_y_sin_grounding_no_se_anade_la_nota` (sv2) | 6 passed → 2 failed |
| 2 | `origen_datos_resolver.py:174` | `cabecera or {}` → `and` | Hueco | `r19_el_correo_cambia_la_obra_y_conserva_el_resto_de_la_cabecera`, `r19_sin_cabecera_el_correo_la_crea_con_la_obra` | 6 → 2 failed |
| 3 | `encolar_extraccion.py:57` | `or` → `and` | Hueco | `r42_una_captura_sin_asunto_para_con_error_de_uso` | 6 → 1 failed |
| 4 | `encolar_extraccion.py:88` | `[:8]` → `[:9]` | Hueco | `r42_por_pantalla_la_huella_abreviada_son_ocho_caracteres` | 6 → 1 failed |
| 5 | `correo/contexto.py:105` | `<= 0` → `<= 1` | Hueco | `r1_un_maximo_de_un_caracter_es_valido` (comun) | 2 → 1 failed |
| 6 | `llm_call_logger.py:120` | `ensure_ascii` F→T | Hueco | `r37_el_fichero_del_logger_es_json_utf8_legible_con_sangria_2` | 2 → 1 failed |
| 7 | `llm_call_logger.py:121` | `indent=2` → `3` | Hueco | el mismo | 2 → 1 failed |
| 8 | `polling_pipeline.py:399` | `[:8]` → `[:9]` | Hueco | `r36_el_log_del_pipeline_lleva_la_huella_de_ocho_caracteres` (sv1) | 26 → 1 failed |
| 9 | `capturar_correo.py:69` | `check` F→T | **Equivalente** | §3.1 · guarda `r38_guarda_el_resultado_solo_depende_del_codigo_de_git` | suite sv1: 98 → **98 passed** |
| 10 | `capturar_correo.py:70` | `capture_output` T→F | Hueco | `r38_git_check_ignore_no_ensucia_la_consola` (`capfd`) | 26 → 1 failed |
| 11 | `capturar_correo.py:71` | `timeout=30` → `31` | Hueco | `r38_git_check_ignore_tiene_un_tope_de_30_segundos` | 26 → 1 failed |
| 12 | `capturar_correo.py:99` | `parents` T→F | Hueco | `r39_la_captura_crea_los_directorios_que_falten` | 26 → 1 failed |
| 13 | `capturar_correo.py:100` | `ensure_ascii` F→T | Hueco | `r39_el_fichero_de_captura_es_utf8_legible_con_sangria_2` | 26 → 1 failed |
| 14 | `capturar_correo.py:100` | `indent=2` → `3` | Hueco | el mismo | 26 → 1 failed |
| 15 | `capturar_correo.py:117` | `required` T→F | Hueco | `r39_el_cli_exige_message_id_y_caso[sin_message_id]` | 26 → 1 failed |
| 16 | `capturar_correo.py:118` | `required` T→F | Hueco | `r39_el_cli_exige_message_id_y_caso[sin_caso]` | 26 → 1 failed |
| 17 | `capturar_correo.py:144` | `[:8]` → `[:9]` | Hueco | `r39_por_pantalla_la_huella_de_ocho_caracteres` | 26 → 1 failed |
| 18 | `config/settings.py:48` | `gt=0` → `gt=1` | Hueco | `r1_correo_max_caracteres_admite_1` | 26 → 1 failed |
| 19 | `email_models.py:26` | `frozen` T→F | Hueco | `r6_el_contenido_del_correo_es_inmutable` | 26 → 1 failed |
| 20 | `intake_cola_adapter.py:89` | `ensure_ascii` F→T | Hueco | `r10_sin_correo_el_payload_es_byte_a_byte_el_de_antes_tambien_con_acentos`, `r10_con_correo_el_payload_añade_la_huella_sin_escapar_el_resto` | 26 → 2 failed |
| 21 | `intake_cola_adapter.py:178` | `[:8]` → `[:9]` | Hueco | `r36_el_log_del_intake_lleva_la_huella_de_ocho_caracteres` | 26 → 1 failed |
| 22 | `mail_client.py:39` | `+= 1` → `-= 1` | **Equivalente** | §3.2 · guarda + demostración diferencial | suite sv1: 98 → **98 passed** |
| 23 | `mail_client.py:45` | `- 1` → `- 2` | **Equivalente** | §3.2, lo mismo | suite sv1: 98 → **98 passed** |
| 24 | `mail_client.py:305` | `>= 300` → `> 300` | Hueco | `r5_un_3xx_al_pedir_el_contenido_es_un_fallo[300]` | 26 → 1 failed |
| 25 | `mail_client.py:305` | `>= 300` → `>= 301` | Hueco | el mismo | 26 → 1 failed |
| 26 | `review_models.py:928` | `replace(..., 1)` → `2` | Hueco | `r32_la_historia_solo_cambia_el_prefijo_del_aviso` (sv4) | 1 → 1 failed |

Por qué vivían los huecos (el porqué completo de cada uno está en su sección de `mutacion_F-048.md`):

- **Huella abreviada (4, 8, 17, 21).** Los tests buscaban `sha256[:8] in salida`, que también está
  contenido en 9 caracteres. Los nuevos fijan el token con lo que lo rodea (`sha=<8> caracteres=`).
  Es salida observable (pantalla y logs, R36), y la abreviatura es la misma, 8, en todos los sitios.
- **`ensure_ascii` e `indent` (6, 7, 13, 14, 20).** Los tests usaban textos ASCII y releían con
  `json.loads`, que no ve el escapado. Ninguno es equivalente: cambian bytes que alguien lee
  (la captura y el log de llamadas se abren a mano) o que R7/R10 exigen iguales a los de antes de
  F-048 (`payload_json` se serializaba con `ensure_ascii=False`, `1807e83`). 7 y 14 (solo sangría)
  podían defenderse como formato de depuración; se prefirió matarlos: no hay entrada que los
  iguale y fijarlos cuesta una línea (`texto == json.dumps(json.loads(texto), ensure_ascii=False, indent=2)`).
- **Límites (5, 18, 24, 25, 11).** 1 es un máximo positivo válido; un 300 es posible (httpx no sigue
  redirecciones por defecto) y se leería como el correo; un git que tarde entre 30 y 31 s distingue.
- **Ramas sin caso (1, 2, 3, 12, 15, 16, 19, 26, 10).** Combinaciones que ningún test montaba:
  plantilla CON marcador y grounding; cabecera con más campos o sin cabecera; captura sin asunto;
  directorio anidado inexistente; CLI sin cada argumento obligatorio (código 2 frente a traza con 1
  o, sin `--message-id`, llegar a Graph con id `None`); `ContenidoCorreo` reasignado; `Obra: `
  dentro de la lectura del papel (texto libre de la IA); `fatal:` de git en la consola.

Traza real de uno (mutante 20, copia aislada, `-k r10_sin_correo`):
```
E  At index 0 diff: '{"email_message_id": "msg-1", "subject": "Albar\\u00e1n n\\u00ba 12 \\u2014 Hormig\\u00f3n", ...}'
     != '{"email_message_id": "msg-1", "subject": "Albarán nº 12 — Hormigón", ...}'
1 failed, 25 deselected in 1.43s
```

## 3. Los 3 equivalentes, con demostración ejecutable (RM5)

### 3.1 · Mutante 9: `check=False` → `check=True` en `ruta_ignorada_por_git`

No hay código de salida de git que distinga. Con `check=True` y código ≠ 0, `subprocess.run` lanza
`CalledProcessError`, subclase de `SubprocessError`, que cae en `except (OSError,
subprocess.SubprocessError): return False`; con `check=False` se devuelve `returncode == 0`, que
también es `False`. Con 0, `True` en los dos. `TimeoutExpired` y `OSError` dan `False` en los dos. La
excepción no se loguea ni se imprime (el `stderr` va capturado en los dos, ver mutante 10).

- **Guarda** (`7317fc6`): `test_f048_r38_guarda_el_resultado_solo_depende_del_codigo_de_git`, con
  0/1/128 y un doble de `subprocess.run` que respeta `check` como el real; y comprueba
  `issubclass(CalledProcessError, SubprocessError)`. Si el `except` se estrecha, cae.
- **Con git real**, en un worktree con el mutante puesto, la suite de sv1 entera da **98 passed**
  con y sin él. Esa suite recorre los tres códigos reales: 0 (`la_ruta_por_defecto_la_confirma_git`),
  1 (la misma, sobre `capturar_correo.py`, versionado) y 128 (`main_rechaza_un_directorio_que_git_no_confirma`,
  `tmp_path` fuera del repositorio).

### 3.2 · Mutantes 22 (`+= 1` → `-= 1`) y 23 (`- 1` → `- 2`): el contador de `script`/`style`

No hay HTML que distinga. `HTMLParser` trata el contenido de `script` y `style` como CDATA: tras
abrir uno, el siguiente evento de etiqueta es **su** cierre (o el fin del documento); `<style/>`
llama a apertura y cierre seguidos. Así el contador vale 0 o 1 en el original y 0 o -1 con el 22:
1 y -1 son los dos «verdadero» en `if not self._dentro_sin_texto`, y al cerrar `max(0, …)` deja 0 en
los dos. Como nunca pasa de 1, `max(0, c - 1)` y `max(0, c - 2)` son 0 para c ∈ {0, 1} (el 23).

- **Guarda** (`7317fc6`): `test_f048_r4_guarda_dentro_de_script_y_style_no_hay_etiquetas`, 6 casos
  (script con style dentro y al revés, dos seguidos, cierre suelto, autocerrado, mayúsculas).
- **Demostración diferencial versionada** (`7b8adab`):
  `test_f048_r4_demostracion_los_mutantes_22_y_23_no_cambian_ninguna_salida` toma el extractor del
  `mail_client.py` real, fabrica las variantes mutadas sustituyendo el texto y compara `html_a_texto`
  sobre **25.620** secuencias (todas las de hasta 4 fichas de un alfabeto de 12, más 3.000
  aleatorias de 5 a 20): **0 discrepancias**; un control (`if True:`, no equivalente) sí se detecta.
  Compara siempre «la otra forma» de la línea: con el mutante inyectado en el propio fichero sigue
  comparando original contra mutante, así que **un equivalente no sale muerto por leer su fuente**
  (RM3) — comprobado: suite de sv1 con el 22 y con el 23 en worktree, **98 passed**.
- **Versión larga** (scratchpad, `demo_m22_m23.py`, misma técnica): todas las secuencias de hasta 5
  fichas más 50.000 aleatorias de 6 a 25, **321.452 casos en 10,7 s: m22 0 discrepancias, m23 0
  discrepancias**, control detectado.

**Para reproducir uno (RM5)**: `cd services/albaranes-email; python -m pytest -q
tests/test_f048_t34_supervivientes.py -k "guarda or demostracion"`; o, para ver que sobrevive,
`git worktree add --detach <tmp> HEAD`, cambiar la línea 39 de
`infrastructure/graph/mail_client.py` en `<tmp>` y lanzar allí la suite de sv1.

## 4. Recuento final

| | Nº |
|---|---|
| Supervivientes de la campaña | 26 |
| Huecos reales cerrados con test nuevo (reinyectados: mueren) | **23** |
| Equivalentes con guarda y demostración ejecutable (reinyectados: sobreviven a la suite entera) | **3** (9, 22, 23) |
| Sin justificar | **0** |
| Tests nuevos | sv2 6 · comun 2 · sv1 26 (incluidas 3 + 6 filas de guarda y 1 demostración) · sv4 1 |

Además: fila de `progress/mutacion_F-048.md` en `progress/inventario_mutacion_F-039.md` (el test
`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario` de la raíz lo exige al versionar el
informe; su recuento decía 17 con 19 filas y pasa a 20).

**Fuera de alcance / notas.** Hay 28 worktrees de campañas de F-047 colgados en
`AppData/Local/Temp/mutacion_F-047_*` (anteriores a esta sesión; no son de T34 y no se han tocado).
