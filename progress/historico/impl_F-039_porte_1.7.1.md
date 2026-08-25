<!-- progress/impl_F-039_porte_1.7.1.md -->
# F-039 · T17: porte de las mejoras genericas a `arnes-base` (1.7.1)

Origen: `albaranes`, rama `dev`, merge `a05c693`.
Destino: `C:\Users\pgris\PycharmProjects\arnes-base`, rama `main`, payload
`arnes-base/`. Version **1.7.0 -> 1.7.1** (correctivo y aditivo menor).

Dos commits locales en el destino. **No hay `git push` ni PR.**

| Commit | Contenido |
|---|---|
| `31d608c` | `--ficheros`, la guarda de alcance vacio y `lineas_comparables` |
| `224957d` | `harness/VERSION` y la entrada de `GUIA_INSTALACION.md` |

---

## 1. Que se porto

### 1.1 `FILAS_DE_RELOJ` + `lineas_comparables()`

En `arnes-base/harness/mutacion.py`, justo encima de `escribir_informe`, que es
quien escribe esas filas. Copia literal del origen salvo el comentario: en
`albaranes` cita «F-012» y «F-038 T5», y en el destino esas features no
existen, asi que se cuenta el mismo hecho sin los identificadores («un test de
paridad serie/paralelo», «una version posterior anadio una fila mas»).

**El test de paridad serie/paralelo NO existe en el destino** — comprobado con
`grep -rln "paridad\|lineas_comparables\|serie.*paralel"` sobre
`arnes-base/tests/` y `arnes-base/harness/`: cero coincidencias, y
`arnes-base/tests/` no tiene ningun equivalente de
`tests/test_f012_r1_r5_r11_coordinador.py`. Coincide con lo que anoto el porte
de la 1.7.0. **No se invento**: se porto la constante y la funcion, y se
elimino el test R7 del origen (`..._el_test_de_paridad_de_f012_usa_lineas_comparables`),
que solo tiene sentido donde hay un filtro propio que sustituir. Queda anotado
como pendiente en la seccion 5.

**La guarda R5 sigue viva en el destino**, que es la razon de ser del porte:
`test_dos_informes_que_solo_difieren_en_tiempos_son_comparables_iguales`
escribe el mismo informe con dos relojes distintos y exige que las lineas
comparables coincidan. Una fila nueva cuyo valor dependa del reloj y no se
declare en `FILAS_DE_RELOJ` rompe ese test en el acto — no revisa la constante,
revisa el informe. La acompanan
`test_todo_prefijo_declarado_sigue_apareciendo_en_el_informe` (un prefijo que
ya no casa con ninguna fila no protege nada) y
`test_una_fila_de_reloj_sin_declarar_rompe_la_comparacion` (la guarda
demostrada al reves).

### 1.2 `alcance_de_ficheros()` + `SIN_DIFF` + `ORIGEN_FICHEROS`

En `arnes-base/harness/alcance.py`, copia literal del origen incluido el
comentario de por que la guarda va donde va. Unico retoque: la firma cabe en
una linea (84 caracteres, por debajo del limite de ruff).

En `arnes-base/harness/mutacion.py`: el `import` ampliado, el flag `--ficheros`
en `_analizar_argumentos`, su rama en `main` y la rama de `escribir_informe`
para el origen `ficheros`.

**El arreglo de CR-2 va incluido y es lo importante**: la guarda de alcance
vacio esta **despues** del filtrado de entradas en blanco, no antes. Los tres
casos comprobados en el destino, y **via `main`**, que era el hueco (por
llamada directa la lista `[]` nunca llega desde el CLI):

```
assert main(["--feature", "F-999", "--ficheros", ","])     == 2
assert main(["--feature", "F-999", "--ficheros", ",,,"])   == 2
assert main(["--feature", "F-999", "--ficheros", "   "])   == 2
```

Mas `test_el_aborto_por_alcance_vacio_no_escribe_informe`, que ademas afirma
`not destino.exists()`: codigo 2 **y sin informe**. Los tres pasan.

### 1.3 Los dos tests, adaptados a la estructura del destino

| Origen (`albaranes`) | Destino (`arnes-base`) |
|---|---|
| `tests/test_f039_r3_r7_filas_de_reloj.py` | `tests/test_mutacion_filas_de_reloj.py` |
| `tests/test_f039_r15_r16_alcance_por_ficheros.py` | `tests/test_mutacion_alcance_por_ficheros.py` |

Adaptaciones, todas por convencion del destino (verificada contra
`test_mutacion_muestreo_por_nivel.py`, portado en la 1.7.0):

- **Nombre de fichero topico**, no por feature: `arnes-base` no tiene backlog
  propio y sus tests se llaman por lo que protegen.
- **Nombres de funcion sin el prefijo `f039_rN_`**; las referencias R3–R7 y
  R15–R16 se conservan en los comentarios de seccion, que es como lo hacen los
  tests ya portados.
- `F-039` -> `F-999` en los datos de prueba: `F-039` no existe en el
  `features.json` semilla del destino y era un identificador prestado.
- `ESTE_TEST` apunta al nombre nuevo del propio fichero (el caso «no es codigo
  de produccion» se prueba contra si mismo).
- `FICHERO_REAL = "harness/rigor.py"`, `harness/alcance.py` y
  `docs/CONVENTIONS.md` existen los tres en el payload: los casos reales del
  origen valen tal cual.
- Se anade `",,,"` a los separadores probados (el origen probaba `","` y
  `"   "`; el encargo pedia los tres).

## 2. Como se integro: verificar antes de aplicar

El destino ya estaba mas cerca del origen que en el porte anterior. Se diffeo
fichero a fichero **antes** de tocar nada (`diff -u --strip-trailing-cr`, porque
`albaranes` guarda CRLF y `arnes-base` fuerza LF por `.gitattributes`).

- `harness/alcance.py`: identico salvo lo de F-039. Nada mas que integrar.
- `harness/mutacion.py`: la 1.7.0 ya traia `--max-mutantes`, el muestreo por
  nivel, `ejecutor_para` con ruta acotada y las filas de trazabilidad.

**Divergencia detectada y respetada**: `arnes-base` pasa
`env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}` al subproceso de la suite
(el arreglo de la 1.6.3, con su `tests/test_mutacion_sin_bytecode.py`) y
`albaranes` **no** lo tiene. Un copiado en bloque de `mutacion.py` habria
borrado esa mejora del arnes generico. Se aplicaron los cambios uno a uno con
ediciones puntuales; el bloque sigue intacto. Queda apuntado en la seccion 5:
es deuda del origen, no del destino.

Ficheros escritos en LF y verificados con `file` antes de commitear.

## 3. Fase RED (nivel `estandar`)

Los dos tests se anadieron al destino **antes** que el codigo. Traza real:

```
$ cd /c/Users/pgris/PycharmProjects/arnes-base/arnes-base
$ python -m pytest tests/test_mutacion_filas_de_reloj.py \
      tests/test_mutacion_alcance_por_ficheros.py -q --tb=short

___________ ERROR collecting tests/test_mutacion_filas_de_reloj.py ____________
tests\test_mutacion_filas_de_reloj.py:22: in <module>
    from harness.mutacion import (
E   ImportError: cannot import name 'FILAS_DE_RELOJ' from 'harness.mutacion'
    (C:\Users\pgris\PycharmProjects\arnes-base\arnes-base\harness\mutacion.py)
________ ERROR collecting tests/test_mutacion_alcance_por_ficheros.py _________
tests\test_mutacion_alcance_por_ficheros.py:17: in <module>
    from harness.alcance import Alcance, alcance_de_ficheros
E   ImportError: cannot import name 'alcance_de_ficheros' from 'harness.alcance'
    (C:\Users\pgris\PycharmProjects\arnes-base\arnes-base\harness\alcance.py)
=========================== short test summary info ===========================
ERROR tests/test_mutacion_filas_de_reloj.py
ERROR tests/test_mutacion_alcance_por_ficheros.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 0.22s
```

Tras portar el codigo, mismo comando: `19 passed in 1.95s`.

## 4. Lo que NO se porto, y por que

- **Inventario de campanas** (`progress/inventario_mutacion_F-039.md`),
  **cabeceras de invalidez**, `tests/test_f039_r1_r2_r23_r25_documentos.py` e
  **informes de campana**: material de `albaranes`, no del arnes generico. Lo
  excluia el encargo.
- **El cambio de `tests/test_f012_r1_r5_r11_coordinador.py`**: no hay test
  equivalente en el destino (ver 1.1).
- **`politica_ficheros.json`**: no hace falta tocarlo. Los dos tests nuevos
  caen bajo `arnes_puro` -> `tests/**`, y los dos ficheros modificados bajo
  `arnes_puro` -> `harness/**`, que ya existian. `.coverage` y `coverage.json`
  siguen en `excluidos` desde la 1.7.0 — **verificado**, no se toco.

## 5. Pendiente (no bloquea el porte)

1. **`arnes-base` no tiene test de paridad serie/paralelo.** `lineas_comparables`
   esta ahi y protegida, pero el consumidor que motivo su extraccion no existe
   en el destino. Si algun dia se porta el coordinador paralelo con su test de
   paridad, ese test debe usar `lineas_comparables` y no un filtro propio.
2. **`albaranes` no lleva el `PYTHONDONTWRITEBYTECODE` de la 1.6.3.** Deuda en
   sentido contrario: el arnes generico esta por delante. Merece una feature
   propia en `albaranes`; no entra aqui.
3. **No se ejecuto `bash harness/init.sh` dentro del payload del destino** a
   proposito: genera `.coverage`, `coverage.json` y reescribe `BACKLOG.md`
   dentro de `arnes-base/`, y ya tumbo al instalador una vez. La puerta real de
   `arnes-base` son sus dos suites, ambas en verde (seccion 6).
4. **Este informe no se ha commiteado en `albaranes`**: queda en el arbol de
   `dev` sin anadir, para que el lider decida. F-039 ya esta cerrada y
   mergeada.

## 6. Evidencias

Todos los numeros son medidos en el **destino**, no estimados.

| Evidencia | Valor real | Como se obtuvo |
|---|---|---|
| Suite del destino, antes de tocar nada | **134 passed, 1 skipped in 18.03s** | `python -m pytest tests -q` en `arnes-base/arnes-base` |
| Suite del destino, al terminar | **153 passed, 1 skipped in 18.89s** | idem, tras los dos commits |
| Tests nuevos aportados | **19** (7 de filas de reloj, 12 de alcance por ficheros) | 153 − 134 |
| Suite del instalador | **TODO VERDE: 65 comprobaciones** (P1–P16) | `.\tests_instalador\prueba_instalador.ps1` |
| Lint del destino | **40 -> 39** errores ruff | `python -m ruff check . --statistics`, comparado contra la version en `git stash` |
| Arbol del destino al terminar | limpio; sin `.coverage` ni `coverage.json` | `git status --short` |

Sobre el lint: los 39 son **deuda previa** del destino (`UP031`, `TRY004`,
`UP020`…), ninguna introducida aqui. Baja uno porque extraer
`origen_del_alcance` a una variable elimina un `ISC004` que existia en el
literal de lista. Comparacion hecha guardando mis dos ficheros en `git stash` y
volviendo a medir, no de memoria.

**Cobertura de lineas cambiadas y campana de mutacion: NO aplican aqui.**
`arnes-base` es el repositorio del arnes generico y su payload no se mide a si
mismo: `harness/init.sh` vive dentro del payload como plantilla, y ejecutarlo
ahi genera los artefactos del punto 5.3. La puerta de cobertura y la campana de
mutacion las corre cada proyecto **instalado**, sobre su propio codigo. Se dice
asi en vez de omitir la fila.
