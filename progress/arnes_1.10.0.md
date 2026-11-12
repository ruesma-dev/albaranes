# Arnés 1.10.0 en albaranes (2026-11-12)

Rama `chore/arnes-1.10.0` (desde `dev`, 1e4ca0f). Desde la 1.7.2 con piezas de la
1.7.16 (caché de F-072, `backlog.py`) hasta la 1.10.0 de `arnes-base`. Ni merge ni push.

## Qué entró (instalador, `-Modo actualizar`)

- Salida: 79 nuevos, 23 actualizados, 6 conservados, 5 protegidos, 3 iguales y 2
  iguales salvo fin de línea. La entrada no era interactiva, así que el instalador
  conservó solo los 6 adaptados («Sin consola de la que leer: se CONSERVA»), que es
  lo que se buscaba.
- Copia del instalador: `%LOCALAPPDATA%\arnes-base\backups\albaranes\20261112-201817`
  (23 ficheros).
- Nuevos: `qa-e2e.md`, `harness/{estados,carril,e2e,mapa_tests,tiempos}.py`,
  `harness/pytest_arnes/`, `harness/plantillas_e2e/` y 71 tests genéricos.
- `harness/rigor.json` no estaba afinado (frente a la 1.7.2 publicada solo cambian
  los finales de línea y una frase de antes de la 1.7.5), así que no hace falta
  `rigor.local.json`.

## Los 6 adaptados, fusionados a mano

| Fichero | Qué se hizo |
|---|---|
| `CLAUDE.md` | Se conserva el local. Entra lo genérico: `qa-e2e` en la autorización, la frase de la primera parada, la sección «Ritmo de trabajo» de la 1.10.0, la prioridad de los ocho estados (paso 3), merges a `dev`/`main` y la regla del push, la regla «tal cual» con `ARNES_SIN_CACHE=1`, y en el bloque de Ruesma el protocolo de `azure-apps` compartido y las cuentas de GitHub. Se mantiene todo lo propio: mapa del monorepo, reglas de Azure, Sigrid, Azurite y despliegue, markitdown y `arnes-base`. |
| `CHECKPOINTS.md` | Base 1.10.0, con lo propio repuesto: las tres trampas de dominio en C3 y el bloque de evals/fixtures en C4 ter (entre marcas GENÉRICO/FIN). |
| `harness/init.sh` | Base 1.10.0, con lo propio repuesto: cabecera «adaptada al monorepo», `REQUIERE_ENV=0` y su comentario, el comentario de rutas sensibles (evals) y el título de la sección 9. Lo demás del local era genérico viejo; `PYTHONPATH`, servicios y caché viven en `servicios.json`, que no se tocó. |
| `docs/CONVENTIONS.md` | Solo cambia la regla de Git: quién hace cada merge y quién el push. El DDL inline y lo de Python se quedan como estaban. |
| `.claude/settings.json` | El de la 1.10.0: `model`, `effortLevel: high` y 8 permisos más para el reviewer (`harness.*`, `backlog.py`, `git checkout -b`). Sale el hook `PostToolUse` local (y su `$nota_monorepo`). Mantenerlo daba rojo en `test_f004`, y además escondía el código de salida con `| tail`. Ningún permiso local se pierde. `settings.local.json` no se tocó. |
| `docs/referencia/README.md` | Sin cambios: la 1.10.0 no trae nada genérico nuevo. |

## Adaptaciones perdidas y repuestas

- Agentes, `harness/*.py`, `SPECS.md` y los 4 tests actualizados: cada copia se
  comparó con las versiones publicadas de `arnes-base`. 16 coinciden exactamente
  con una versión publicada. Las otras 7 solo difieren en redacción o formato
  genéricos, salvo uno.
- La excepción: `tests/test_mutacion_operadores.py`. El local llevaba
  `test_f034_r14` con dos asserts propios (`evals/fixtures/` sí, `ground_truth`
  no). Se repuso en `tests/test_f034_r14_puerta_evals_versionada.py`, un fichero
  del proyecto que el instalador no pisa.

## Tests borrados (decisión a) y su equivalente

La comparación se hizo por nombre (sin el prefijo `fXXX_rN_`), por cuerpo (AST)
y por número de casos de `pytest --collect-only`.

| Borrado | Genérico | Casos |
|---|---|---|
| `test_f038_r1_r4_ejecutor_raiz` | `test_mutacion_ejecutor_raiz` | 10/10, cuerpos idénticos |
| `test_f038_r5_r9_muestreo_por_nivel` | `test_mutacion_muestreo_por_nivel` | 23/24 (4 fijaban valores del rigor.json 1.7.2 → análogo de forma) |
| `test_f038_r10_r12_informe` | `test_mutacion_informe_trazabilidad` | 14/14, idénticos |
| `test_f038_r13_r16_tamano` | `test_tamano` | 22/24 (1 análogo de forma) |
| `test_f038_r17_r21_documentos` | `test_documentos_del_arnes` | 17/18, idénticos |
| `test_f039_r15_r16_alcance_por_ficheros` | `test_mutacion_alcance_por_ficheros` | 13/13 (solo F-039 → F-999) |
| `test_f040_r11_r17_honestidad` / `r18_r26_huecos` / `r1_r10_dimensionado` | `test_mutacion_honestidad` / `huecos` / `dimensionado` | 20/20, 40/40, 50/50 |
| `test_f072_r1_r6`, `r7_r17`, `r18_r22`, `r23_r27`, `r31_r33` | `test_cache_suites`, `test_cache_suites_init_sh`, `test_servicios_dependencias` | 110 tests con equivalente nominal (79 cuerpos idénticos y 31 retocados por F-028) |

No equivalentes, que se conservan:

- `test_f039_r1_r2_r23_r25_documentos`: el inventario de informes de mutación,
  propio del repositorio.
- `test_f072_r28_r30_declaracion`: los servicios declaran la librería común. Se
  le quitó R30, que exigía `ARNES_VERSION=1.7.2` y queda obsoleto.
- `test_f039_r3_r7_filas_de_reloj` → `test_f039_r7_paridad_f012`: R3–R6 eran
  copia vieja del genérico y R5 daba rojo con las filas de F-019. Queda R7, el
  único caso propio.

Se actualizó la referencia a `test_f040_r1_r10_dimensionado.py` en un docstring
de `test_f012_r7_r8_cli.py`.

## Rojos tras la actualización y su arreglo

En la suite raíz, antes de `init.sh`: 3 rojos sobre 3744.

1. `test_backlog_md`: es el esperado y lo regenera `init.sh`.
2. `test_f019_r22`: `test_f085_infra.py` tenía `timeout=120` literal y pasa a
   `escalar_timeout(120)`, lo que pide la guía para F-019.
3. `test_f039_r5`: ver la tabla de arriba.

## Resultado real de `bash harness/init.sh`

- Termina con **ENTORNO LISTO**, código 0: 30 OK, 5 AVISO y 0 KO.
- Suite raíz: 3741 passed y 46 skipped, en 22 min 33 s.
- Servicios: sv1 a sv6 y `comun` servidos de caché (los cambios no los tocan),
  `sv9-alta-sigrid` ejecutado en verde (1188 passed, 82,6 s), `infra` sin
  comando.
- Los avisos ya existían: features en `blocked`, ruff con 1530 avisos, `infra`
  sin tests, PUERTA TAMAÑO N/A y marcas `[ADAPTAR]` citadas en las specs
  F-034/F-035 (mismo detector que antes).
- `BACKLOG.md` se regeneró con las columnas nuevas.

## Commits (rama `chore/arnes-1.10.0`)

`5f6351d` genérico del instalador · `64e7843` fusión de los 6 adaptados · `e1e8de4`
tests duplicados fuera y ARNES_VERSION · `ea90b90` dos rojos de la suite raíz ·
`a4fdc8c` BACKLOG regenerado · y el de este informe.

## Riesgos y pendientes

- **Cambio de conducta**: con la 1.10.0, el líder hace los merges a `dev` sin
  preguntar tras el OK al resumen final, y a `main` preguntando. Antes, en
  albaranes, «push, merge a dev y PRs: siempre el humano». Si el humano quiere
  seguir haciendo él los merges, hay que decidirlo; mantener la regla vieja da
  un rojo en `test_f070_d3`.
- `settings.json` fija `model: claude-opus-5-5` y `effortLevel: high`. El
  esfuerzo por rol exige Claude Code ≥ v2.1.292.
- Por `rigor.json`, sin preguntar: `estandar` ya no bloquea por mutación,
  `critico` muestrea, y los informes de mutación nuevos no son comparables con
  los anteriores (avisos reunidos en `ARNES_VERSION.md`).
- Para `arnes-base` (no portado: no es una mejora hecha aquí): el genérico de
  `test_mutacion_operadores` absorbe tests con aserciones de proyecto. Conviene
  avisar en la guía de que hay que mudar lo propio antes de actualizar.
- Falta: revisar el diff de la rama y fusionarla en `dev`; el push lo hace el
  humano.
