Revisión completa (pasada 1): `dev...e214dec` (base de alcance `d79b3d9`) y el commit `78a67aa` de `arnes-base` (`main`, sin push)
<!-- progress/review_F-072.md -->
# F-072 · La caché de suites tiene en cuenta las dependencias · review

## Veredicto: CHANGES_REQUESTED

El código de producción está bien y **no hay que tocarlo**. Lo que se rechaza son cuatro arreglos pequeños de papeleo y
del porte, dos de ellos justo lo que el líder pidió vigilar: coherencia de versión en `arnes-base` y porte genérico.
Ninguno obliga a repetir la campaña de mutación. La pasada 2 será incremental.
**Condición de cierre que sigue en pie** (`critico`): la aceptación escrita del humano de los equivalentes 3 y 5, y
después la MANUAL T16.

## Nivel de rigor

`critico` declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de lo cambiado, campaña completa,
cero supervivientes salvo equivalentes aceptados por escrito por el humano, RM5 con una muestra y MANUAL listadas.

## Lo que verifiqué yo (no copiado del informe)

| Comprobación | Resultado |
|---|---|
| `bash harness/init.sh` en el worktree | `ENTORNO LISTO`, exit 0. Raíz: `1237 passed`; sv1 205, sv2 397, sv3 703, sv4 1427, sv5 43, sv6 295, sv9 654; comun servida de caché («verde del 2026-10-16 18:44») |
| AVISO R13 en sv1–sv6 y sv9 | Sale en los siete, con la ruta de la comun del árbol principal, y los siete ejecutan su suite |
| `PUERTA COBERTURA` | `[OK] 100.0% de 202 líneas cambiadas cubiertas (202/202, umbral 80%, nivel critico)` |
| `PUERTA TAMAÑO` | requirements 136/150, design 250/250, impl 194/220 |
| Clave en un repositorio real | Clon local disperso de la rama, `clave_de` con sonda falsa que resuelve dentro: un commit en `services/albaranes-comun` cambia la clave de sv1, sv5, sv9 y comun. Un commit en `harness/` no cambia ninguna. Crear `.env` en la raíz la cambia |
| `.env` solo por metadatos | El texto de la clave lleva `local=.env@21:<mtime_ns>` y **no** el contenido (`SECRETO` ausente). `huella_local` solo hace `os.stat`, y el test R10 bloquea `open` |
| Ficheros de caché | Solo guardan el `sha256` (64 hex); el texto de la clave no se escribe en ningún sitio |
| `ARNES_SIN_CACHE` | Aviso único fuera del bucle, `--sin-cache` por servicio y permiso en `.claude/settings.json` (P3). R25 lo ejecuta con bash real |
| Porte | `diff --strip-trailing-cr` idéntico en `servicios.py`, `cache_suites.py`, `servicios.ejemplo.json` y la §7 bis. Suite completa del payload de `arnes-base`: `509 passed, 2 skipped` |

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base presentes.
**C2** [x] una sola `in_progress` (F-072) · [x] rama `feature/F-072-cache-con-dependencias` · [x] `current.md` al día con
F-072 y su MANUAL (el bloque de F-070 sigue ahí porque está `blocked` pendiente de su MANUAL) · [x] las `done` con historia.
**C3** [x] Hexagonal: N/A justificado, es herramienta del arnés (`harness/`), fuera de los servicios (design §4) ·
[x] primera línea con ruta en los 8 ficheros de código · [x] sin `print` de debug (los de `main` son la salida de la
CLI), sin secretos, sin dependencias nuevas · [x] reglas de dominio: no toca merge, schema ni importes.
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] R1–R33 con tests `test_f072_rN_*` (tabla abajo), todos en verde. R34 es entre repositorios: un test aquí
dependería de la ruta local de `arnes-base`, así que la verificación es su comando de T15, **reproducido por mí** (ver
Automejora) · [x] sin red ni BBDD (git local en `tmp_path`, variables `GIT_*` limpias) · [x] T16 MANUAL en
`current.md` con su comando exacto y criterio VERDE/ROJO.
**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: trazas reales de T1, T3, T4, T6, T8 y T10 en `impl_F-072.md`.
- [x] Cobertura `[OK]` 100 %.
- [x] Mutación con totales recalculados por mí: `alcance_de_feature` da 2 ficheros y **488 líneas** (394 + 94), y
  `generar_mutantes` da **72** (60 + 12). Los 7 supervivientes existen con el mismo operador y el mismo texto.
- [x] Muertos: «Tiempo total» 3674,5 s > 60 s, así que **la campaña no se reejecutó** (61 min según el informe). Valen el
  recálculo puro, RM1–RM6 y la reproducción RM4 de abajo.
- [x] Coste por mutante: 3674,5 × 4 ÷ 72 = 204 s, por encima de 1 s y coherente con la línea base de 225 s.
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0, con línea base medida en los 4 workers.
- [x] **RM1:** medido sobre `576f464…`. Desde entonces, `cache_suites.py` y `servicios.py` solo cambian 4 líneas de
  comentario (de «F-072» a «1.7.16»), sin desplazar líneas. El alcance medido es el revisado.
- [x] **RM2:** media 51,0 s × 4 workers = 204 s, frente a 225 s de base, con 65 de 72 muertos en `-x`. Total =
  72 × 51,0. Coherente.
- [x] **RM5:** reproduje el **#3** (`text=False` en `_git`, L110) en una copia (`git archive`) en mi scratchpad.
  La demostración da `str 'ñ\n'`, y CPython hace `self.text_mode = encoding or errors or text or universal_newlines`.
  Con el mutante aplicado, los tests de F-072 de la copia dan `142 passed`: sobrevive, así que es equivalente.
- [x] **RM6:** ningún test se consiguió quitando una guarda; las 6 altas son tests nuevos y no cambian producción.
- N/A campaña manual: la automática dio 72 mutantes.
- [x] Supervivientes analizados (ninguno `PENDIENTE`): 5 muertos con tests nuevos y 2 equivalentes. Queda **pendiente
  la aceptación escrita del humano** de los equivalentes 3 y 5 (condición de cierre, como en F-070).
- [ ] **Evidencias:** la sección existe y declara los 4 workers, pero el número de tests es falso (CR3).
- [x] Ningún N/A sin justificar.

**RM3** (criterio): repasé los 65 muertos y ninguno es equivalente. `LIMITE_SONDA_S` 30→31 y `return 1`→`2` cambian
un contrato observable fijado por la spec (design §4 y R22).
**RM4:** reproduje en la copia aislada dos muertes por tests nuevos. L122 `or`→`and` da `2 failed`
(`test_f072_r12_git_que_*`), y L172 `check=True` da `2 failed` (`r16_sonda_con_el_interprete…`,
`r15_sonda_real_que_sale_con_error…`). La copia quedó restaurada, y el worktree estuvo limpio todo el tiempo.
**C4 ter** N/A: no toca rutas de `rutas_sensibles.json` (la puerta de init.sh no señaló nada).
**C5** [x] T1–T15 y T17 `[x]` con sus commits `F-072 Tn:`; T16 es MANUAL del humano, pendiente y listada · [x] sin
temporales (`git status` limpio) · [x] `features.json` en `in_progress`.

## Cobertura de requisitos

| Req. | Tests |
|---|---|
| R1–R6 | `test_f072_r1_*` (4, incluidas las salidas `--shell`/`--validar` idénticas) … `test_f072_r6_validar_sale_con_1_*` (50 en total) |
| R7, R8 | `r7_texto_canonico`, `r7_la_clave_es_el_sha256_del_texto`, `r7_un_commit_en_la_dependencia_cambia_la_clave`, `r7_un_commit_ajeno_no_*`, `r8_clave_independiente_del_orden` |
| R9, R10 | `r9_huella_local_es_nombre_tamano_y_mtime`, `r9_env_de_la_raiz_y_del_servicio_*`, `r10_el_contenido_del_env_no_esta_*`, `r10_huella_local_nunca_abre_el_fichero` |
| R11, R12 | `r11_servicio_sucio_*`, `r11_dependencia_con_no_rastreado_*`, `r12_dependencia_fuera_de_head_avisa_*`, `r12_git_que_*` |
| R13–R15 | `r13_modulo_fuera_del_repositorio_*`, `r13_repositorio_vecino_con_prefijo_comun_*`, `r14_*`, `r15_*` (6) |
| R16, R17 | `r16_sonda_con_el_interprete_*`, `r16_la_sonda_real_no_ejecuta_el_modulo_vigilado` (+4), `r17_dentro_de_*` (3) |
| R18–R22 | `r18_*` (4), `r19_*` (5), `r20_cache_del_formato_anterior_*`, `r21_sin_cache_nunca_sirve_*`, `r22_*` (12) |
| R23–R27 | Contrato estático (7) + §7 bis ejecutada con bash real (7): `r24_*`, `r26_fallo_del_modulo_*`, `r27_todos_los_servicios_se_procesan`, `r25_sin_cache_avisa_una_vez_*` |
| R28–R30 | `r28_los_siete_servicios_declaran_la_comun` (×7), `r28_ningun_otro_servicio_python_importa_*`, `r29_*`, `r30_*` |
| R31–R33 | `r31_commit_en_la_dependencia_cambia_la_clave_*`, `r32_modulo_de_fuera_*`, `r33_tocar_el_env_*`, `r33_tocar_el_pycache_*` |
| R34 | Sin test (entre repositorios). Lo verifiqué yo: diff idéntico y `509 passed, 2 skipped` en `arnes-base/arnes-base` |

## Cambios requeridos

1. **`arnes-base` · fecha incoherente.** `GUIA_INSTALACION.md:2171` titula la sección «(1.7.16, 2026-10-15)», pero
   `arnes-base/harness/VERSION` dice `ARNES_FECHA=2026-10-16`. En la 1.7.15 coinciden (2026-10-14 en los dos). Hay que
   igualarlas (la fecha del porte es el 16) en un commit nuevo en `main` de `arnes-base`, local y sin push.
2. **`arnes-base` · test con un nombre de albaranes.** `arnes-base/tests/test_servicios_dependencias.py` usa
   `ruesma_comun` en las líneas 118, 232, 234, 245, 256, 263 y 266. Es el paquete de este monorepo, y R34 pide los tests
   «con nombre genérico». Hay que cambiarlo por un nombre neutro (`comun`, como en `servicios.ejemplo.json`) en ese mismo
   commit. Basta en `arnes-base`: el `test_f072_r1_r6_*` de aquí puede seguir con `ruesma_comun`. El «Origen: albaranes
   F-072» de los docstrings sí vale, porque hay precedentes en los `test_mutacion_*` del taller.
3. **`progress/impl_F-072.md` · número de tests falso.** «Evidencias» dice «Tests de F-072: 160 (… con los 6 de la
   mutación); los 154 previos». En realidad hay **154** recogidos, con los 6 nuevos (50 + 43 + 26 + 14 + 12 + 9), así que
   antes eran 148. Lo confirma `arnes-base`: 142 = 154 − 12 de R28–R30. Hay que corregir esa fila y la frase de la
   sección de mutación («los 154 tests de F-072» es correcto solo con los 6 nuevos ya dentro).
4. **`specs/F-072-cache-con-dependencias/design.md:203` · AVISO permanente.** El literal `` `[ADAPTAR]` `` hace que
   `init.sh` liste este design en «Marcas [ADAPTAR] sin resolver» en cada ejecución, también cuando la feature ya esté
   `done` (pasa igual con F-034 y F-035). Hay que reescribirlo sin la marca (por ejemplo, «la cabecera adaptable») y
   comprobar que el design sigue ≤ 250 líneas.

No hay que repetir la campaña: ningún cambio toca `harness/cache_suites.py` ni `harness/servicios.py`. Tampoco hace
falta otra corrida de `init.sh` larga más allá de la de cierre del implementer.

## Observaciones (no bloquean)

- La clave no cambia si se actualizan paquetes dentro del mismo venv (`pip install`), porque la ruta del intérprete es
  la misma. Ni la spec ni el encargo 1.7.12 lo piden. Lo anoto como posible mejora del taller.
- `ruff` sigue con 1272 avisos (1271 en `dev`); el nuevo es el `TRY004` de `_lista`, que R3 obliga a lanzar como
  `ValueError`.

## Automejora (propuesta, no aplicada)

C4 exige un test por requisito, y un requisito de **porte a `arnes-base`** no puede tenerlo en el repositorio de origen
sin atarse a una ruta local. Propongo una nota en C4: «un requisito de porte entre repositorios se cubre con el
comando de verificación de su tarea, que el reviewer reproduce y cita en su informe». Hoy se resuelve con un juicio
caso por caso.
