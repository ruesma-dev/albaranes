<!-- progress/impl_F-077.md -->
# F-077 · Ficha: guardar y aprobar de una vez · informe del implementer (2026-10-17)

Rama `feature/F-077-guardar-y-aprobar` (worktree `../albaranes-F-077`), rigor `estandar`, solo **sv4**. Spec v2:
`specs/F-077-guardar-y-aprobar/`. T1–T13 y T15 hechas (un commit por tarea); **T14 es MANUAL del humano** (pasos
exactos y criterio de verde en `progress/current.md`, bloque «F-077 · MANUAL del humano (T14)»). sv9 no cambia.

## 1. Antes de empezar

- `git merge dev` (`76c07c7`): F-053, F-072, F-078, F-076 y F-079. Conflictos solo en `features.json` (se conservan
  todas las entradas de `dev` y se añade F-077), `current.md` (el de `dev` + la línea de F-077) y `BACKLOG.md`
  (regenerado). Sin conflictos de código: F-077 aún no tocaba sv4.
- F-077 en `in_progress` (`7647e70`). *Junction* `services/albaranes-front/.venv` → venv de sv4 del árbol principal
  (quitarla con `cmd /c rmdir` antes de `git worktree remove`).
- Notas de F-078/F-076 aplicadas: el ⚠ se deriva del `agree_partida` de F-076 (`coincide_partida`, sin tocarlo); el
  `title` queda «descripción · [nota F-076] · [aviso F-077]»; R11 incluye la R17 de F-078 (test R11 con la fila 13).

## 2. Qué cambió (ficheros)

| Fichero (sv4) | Cambio | R |
|---|---|---|
| `static/app.js` | `filasConCambios`, `motivoDeRespuesta`, `enviarFila` (único PATCH de fila), `consolidarFila`; `guardarFilasPendientes`, `avisoSumaVigente`, `marcarFilaNoGuardada`/`limpiarFilasNoGuardadas` y el nuevo `guardarCabecera`; fuera `partidasInvalidas`; bloque autónomo `sondearAltaEnCurso` (3 s) | R1–R13, R19 |
| `templates/_alta_sigrid.html` | tres fases (`data-fase`, `data-document-id`), clase `error`, motivos con texto y código en `title`, «Línea N: …» | R15–R17, R24–R28 |
| `templates/document_detail.html` | `cedit-warn` y ⚠ de solo lectura con `c.aviso_partida`; `title` compuesto con `select`+`join(' · ')` | R21–R23 |
| `static/styles.css` | `.alert.error`/`.alta-sigrid.error`, `.alta-sigrid-en-curso`, `tr.fila-no-guardada` | R4, R15–R17 |
| `domain/services/alta_sigrid.py` | `FASE_*`, `TOPE_RESPUESTA_ALTA` (5 min), `fase_alta`, `motivos_linea_vista` | R14, R24, R25 |
| `domain/models/alta_sigrid_models.py` | `ESTADOS_ALTA_ERROR`, `es_error`, `TEXTOS_MOTIVO_ALTA`, `texto_motivo_alta`, `texto` en los motivos, `motivos_linea_sueltos` | R17, R24, R26–R28 |
| `domain/models/review_models.py` | `aviso_partida_texto`, `posiciones_filas_ficha`, `ConciliacionDisplay.aviso_partida`, `DocumentDetailPayload.alta_fase`/`alta_motivos_linea` | R14, R21–R25 |
| `infrastructure/database/review_repository.py` | `aviso_partida` solo en la rama con blanca | R21, R22 |
| `application/services/review_service.py` | `fase_alta(document_id, *, ahora=None)`; `get_document` añade `alta_fase` y `alta_motivos_linea` | R14, R18 |
| `interface_adapters/web/app.py` | `GET /api/documents/{id}/alta-sigrid/fase` (fuera del esquema OpenAPI) | R18, R20 |
| `docs/ARCHITECTURE.md`, `sv4.md` | regla 19 (panel por fases, motivos) y 20 (guardado previo, ⚠); tabla de endpoints y nota en §11 | R30 |

Tests nuevos: `test_f077_aviso_partida.py` (32), `test_f077_alta_fase.py` (88), `test_f077_motivos_alta.py` (25),
`test_f077_guardar_y_aprobar_js.py` (23). Tests existentes adaptados (design §7): `test_f065_f1_js.py` (fuera los dos
R19; R18 a `filasConCambios`; R8 mira `enviarFila` en vez de `?bloquear=1` en cada bloque), `test_f065_f3bis_front.py`
(`_GUARDAR` con las funciones compartidas y sin `partidasInvalidas`; `test_f065_r27v5_guardar_y_aprobar_marca_la_
partida_mala` espera la alerta de R3), `test_f076_aviso_partida.py::test_f076_r24_literal_o_aviso_sin_nota` (con ⚠
el `title` lleva ahora el aviso de F-077). Ningún test de F-053 cambió de expectativas. `azure-apps` no cambia (ruta
interna, design §1).

## 3. Decisiones y desviaciones (para el reviewer y el humano)

1. **Separador del `title` de la partida: « · », no «en línea aparte»** (R22 decía salto de línea). Lo pidió el líder
   al fusionar F-076 («descripción · [nota F-076] · [aviso F-077]») y es el que ya usa la nota «Normalizada» de F-076.
2. **Cuatro textos de motivo que no estaban en el Anexo A**: el test de R27 (fuentes de sv9 leídas como texto)
   encontró códigos que sv9 escribe hoy y la tabla no tenía: `adjunto_no_colgado`, `usuario_no_resuelto`
   (`alta_sigrid_service.py`, adjunto) y `verificacion_fallida`, `sigue_en_sigrid` («Ya lo he anulado»). Se les dio
   texto (R27 manda sobre la lista). Además, con `azure-apps/sigrid_api.md` §8.6, `peticion_mixta` («mezcla los dos
   modos de alta de sigrid-api») y `referencia_no_permitida` («no admite el prefijo de la referencia») tienen un texto
   más preciso que el del Anexo, como la propia spec permitía.
3. **`avisoFilasSinGuardar` y `contarFilasConCambios` NO se borran** (design §3 decía «sin otros usos»): los usa la
   confirmación de «Dividir» (`wireDividir`, F-065 R29: «Hay N líneas con cambios sin guardar: dividir recarga la ficha
   y se perderán. ¿Continuar?»), y design §8 deja `wireDividir` fuera. «Guardar» y «Guardar y aprobar» ya no la usan
   (R13, test que lo comprueba en `guardarCabecera`/`guardarFilasPendientes` y fuera de `wireDividir`). Si el humano
   quiere que Dividir también guarde antes, es otra feature (F-068 toca esa zona).
4. **Bandera de «intento en marcha» como propiedad de la función** (`guardarCabecera.enMarcha`) en vez de una
   variable del bloque: mismo efecto, y la función se puede ejecutar sola con node sin declarar nada fuera.
5. Al parar sin navegar, cada botón vuelve a **su** estado anterior (el de aprobar puede venir desactivado de la
   plantilla sin valorar): test `test_f077_r10_al_parar_respeta_el_aprobar_desactivado_de_la_plantilla`.
6. Un fallo de red en el PUT (que hoy era una promesa rechazada sin aviso) ahora avisa «Error al guardar: error de
   red» y sigue R9. El «Guardar» de fila con la red caída dice «error de red» en vez del «Failed to fetch» del
   navegador (única diferencia visible de R12).
7. `fase_alta` con la feature apagada devuelve `resultado` **sin leer nada** (design §4), así que con DESDE vacía la
   ruta responde 200 `resultado` aunque el documento no exista; el JS nunca sondea en ese caso (no hay panel).
8. En `en_curso`/`sin_respuesta` el panel no lleva `data-estado` (sería el estado viejo); en `resultado`, el de hoy.

## 4. Fase RED (traza real, antes del código de cada bloque)

**C (T1)** — `.venv/Scripts/python.exe -m pytest tests/test_f077_aviso_partida.py -q --tb=line` (tras `597073e`):
```
E   AttributeError: module 'domain.models.review_models' has no attribute 'aviso_partida_texto'
E   AttributeError: 'ConciliacionDisplay' object has no attribute 'aviso_partida'. Did you mean: 'agree_partida'?
FAILED tests/test_f077_aviso_partida.py::test_f077_r21_sin_blanca_con_agree_false_sin_aviso[True-manual]
E   assert ('cedit-warn' not in 'class="conc...            '      <- hoy una fila manual con agree false lleva ⚠
FAILED tests/test_f077_aviso_partida.py::test_f077_r21_nueva_con_agree_false_sin_aviso[True]
30 failed, 3 passed in 4.26s
```
**B servidor (T3)** — `pytest tests/test_f077_alta_fase.py -k "r14 or r17 or r18 or r20" --tb=line` (tras `68b830b`):
```
E   AttributeError: module 'domain.services.alta_sigrid' has no attribute 'fase_alta'
E   ImportError: cannot import name 'ESTADOS_ALTA_ERROR' from 'domain.models.alta_sigrid_models'
E   AttributeError: 'ReviewService' object has no attribute 'fase_alta'
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'alta_fase'
E   assert 404 == 200                                             <- la ruta no existía
62 failed, 1 passed, 1 warning in 2.11s
```
**B front (T5)** — `pytest tests/test_f077_alta_fase.py -k "r15 or r16 or r17 or r19" --tb=line` (tras `5a5bc6e`):
```
E   assert 'Alta en curso…' in '<section class="alert alta-sigrid warning"\n id="alta-sigrid" data-estado="registrado">…Ya lo he anulado e
E   assert 'error' in ['alert', 'alta-sigrid', 'warning']        <- no_admitido/revisar/error salían como warning
E   AttributeError: 'NoneType' object has no attribute 'group'    <- no había SONDEO_ALTA_MS en app.js
17 failed, 16 passed, 54 deselected, 1 warning in 4.38s          (los 16: R17 «resto de estados como hoy»)
```
**D (T7)** — `pytest tests/test_f077_motivos_alta.py --tb=line` (tras `7b7065b`):
```
E   AttributeError: module 'domain.models.alta_sigrid_models' has no attribute 'texto_motivo_alta'
E   AssertionError: assert [{'codigo': '...'2025-01-01'}] == [{'codigo': '...do antigua)'}]   <- sin clave texto
E   AttributeError: 'AltaSigridVista' object has no attribute 'motivos_linea_sueltos'
E   ImportError: cannot import name 'posiciones_filas_ficha' from 'domain.models.review_models'
E   AttributeError: module 'domain.models.alta_sigrid_models' has no attribute 'TEXTOS_MOTIVO_ALTA'
24 failed, 1 passed in 0.80s                                       (el 1: la extracción de códigos de sv9)
```
**A (T9)** — `pytest tests/test_f077_guardar_y_aprobar_js.py --tb=line` (tras `3dd0b4c`):
```
E   AssertionError: faltan en app.js: ['filasConCambios', 'motivoDeRespuesta', 'enviarFila', 'consolidarFila',
    'marcarFilaNoGuardada', 'limpiarFilasNoGuardadas', 'guardarFilasPendientes', 'avisoSumaVigente']
E   assert 2 == 1                                                  <- dos PATCH de fila copiados
E   assert 'con cambios sin guardar' not in '// static/a...'
21 failed, 2 passed in 1.15s
```
Y la misma escena de R1 ejecutada con node contra el `guardarCabecera` de antes (para ver el defecto, no un import):
`{'peticiones': [], 'alertas': ['Hay 2 líneas con cambios sin guardar'], 'recargas': 0, 'href': None}`.

Tras cada implementación, en verde: T2 `172 passed` (aviso + F-051 + F-076 + F-078 ficha), T4 `212 passed` (fase +
F-053 t21/t20/r29), T6 `225 passed`, T8 `218 passed` y `705 passed` (`-k "f053 or f077 or f076 or f078"`), T10 `85
passed` (F-065 f1 + f3bis) y `grep -c "conciliacion/campos?bloquear=1" static/app.js` = **1**, T11 `106 passed` y la
suite entera de sv4 `1714 passed`.

## 5. Resultado de `bash harness/init.sh`

Primera pasada (tras T13): **rojo** solo por la suite de la raíz,
`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario` (`progress/mutacion_F-077.md` sin fila en
`progress/inventario_mutacion_F-039.md`). Añadida la fila (41 informes). El resto, ya en verde entonces: sv1 205, sv2 397, sv3
703, **sv4 1715 passed** (149,55 s), sv5 43, sv6 444 (+1 skip), sv9 670, comun (caché); **PUERTA COBERTURA: 100.0 %
de 92 líneas cambiadas (92/92)**; PUERTA TAMAÑO dentro. Pasada final: §7.

## 6. MANUAL pendiente

**T14** la hace **el líder en el navegador**, con el humano: bloque «F-077 · MANUAL T14» de `progress/current.md`
(rehecho en la pasada 1 de la review). Encaje: tras el paso 4 de la secuencia combinada F-078 + F-076 (su `deploy
sv4` lleva F-077 si ya está en `dev`); el punto 1 (`86c13097` en `no_admitido`, «Línea N: La línea no tiene
descripción», solo lectura) antes del paso 6. Solo el punto 5 escribe en producción (PATCH de fila, PUT de
aprobación, `q-feedback`), con el sí expreso del humano y con correcciones reales que elija él; si no hay ninguna,
queda cubierto por los tests y se anota. Resultado: **HECHA, cerrada el 2026-11-11** (abajo).

**Resultado de T14 (líder):**

- Punto 1 VERDE y punto 2 VERDE (2026-10-18, sv4 `r20261018-1741`; el 2 tras F-078 T14).
- Punto 3 VERDE en lo negativo (12 de 12 albaranes con filas Contrato, sin ⚠ indebido; ningún caso positivo que mirar).
- Punto 4 (2026-10-22 y repetido el 2026-11-11 en sv4 `r20261108-1033`, albarán IV00098067 `00c344e2`, pendiente,
  con toda escritura bloqueada en la página: fetch no GET, XHR, formularios, `alert`/`confirm`): `zzzz` en la partida
  de la línea 510 y «Guardar y aprobar» ⇒ al salir de la casilla el combo devuelve la partida anterior
  (`volverSiNoVale`, `app.js:1138`, F-065 O6 del 2026-10-13); la fila queda sin cambios, no hay PATCH de fila, no
  sale el aviso y se intenta el PUT de aprobación (bloqueado por la prueba: nada escrito). El aviso de la spec es
  inalcanzable por diseño del combo; una partida no válida nunca se guarda. **Dado por bueno por el humano el
  2026-11-11** («f77 lo doy por bueno, cierra»). Sin probar en producción: el aviso con una fila que llegue con
  partida inválida (cubierto por `tests/test_f077_guardar_y_aprobar_js.py`).
- Punto 5 aceptado por el humano con el uso real (19 aprobaciones de Óscar Domingo con filas guardadas, registradas
  en Sigrid).

## 7. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-077 | **168 passed** (`pytest tests/test_f077_*.py`, 12,47 s) |
| Suite de sv4 | **1715 passed** en 149,55 s (con cobertura, `init.sh`); 1714 en 86,1 s sin el test del superviviente ni cobertura |
| Cobertura de las líneas cambiadas | **100,0 %** (92/92, umbral 80 %, `PUERTA COBERTURA` de `init.sh`) |
| Mutación | `python -m harness.mutacion --feature F-077` sobre `e1d9937`: **39 generados, 20 evaluados (muestreo `estandar`, semilla 20260820), 19 muertos, 1 superviviente**, 0 timeouts, 0 sin veredicto, 980,8 s, 4 workers |
| Superviviente | `app.py` `include_in_schema=False→True`: hueco real, cerrado con `test_f077_r18_la_ruta_queda_fuera_del_esquema_openapi` (falla con el mutante aplicado a mano). Análisis en `progress/mutacion_F-077.md` |
| JS | No lo mide la herramienta (solo Python): lo cubren los 23 tests con node de A y los de sondeo/marcado de B y C (node v24.14.1) |
| `bash harness/init.sh` final | ver la línea siguiente |

`bash harness/init.sh` final (sobre `1fd1cb4`): **VERDE**, «ENTORNO LISTO». Raíz 1237 passed (161,14 s); sv1 205, sv2 397, sv3 703, **sv4 1715 passed
(173,38 s)**, sv5 43, sv6 444 (+1 skip), sv9 670, comun (caché); PUERTA COBERTURA 100,0 % (92/92); PUERTA TAMAÑO
dentro (impl 146/220).

## 8. Review pasada 1 (CHANGES_REQUESTED, solo documentación)

`git merge dev` (`current.md` de `24c8bd9`: `.env` de sv6 a localhost, `Usar-PgAzure`/`Quitar-PgAzure`; se conservan
y se añade el bloque de F-077). Cambio 1: bloque T14 rehecho (a–e: la ficha se recarga aprobada, la hace el líder,
acciones que escriben marcadas con su sí expreso, datos reales elegidos por el humano, encaje en los pasos 4 y 6,
verde ligado a `86c13097`) y dos notas en la secuencia combinada (paso 4 y paso 6). Cambio 2: notas «(implementación,
aceptado en review)» del 2026-10-17 en R22, `spec_F-077.md` §5, design §3 («Dividir»), §5 y §9. Cambio 3: la cita de
F-077 de `sv4.md` §11, fuera del bloque de código. Sin cambios de código. `bash harness/init.sh` sobre `861aa70`: **VERDE**, «ENTORNO LISTO» (raíz 1237, sv4 1715 passed, el resto igual; COBERTURA 100,0 % de 92 líneas; TAMAÑO dentro, impl 160/220).
