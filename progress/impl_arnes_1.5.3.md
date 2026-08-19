<!-- progress/impl_arnes_1.5.3.md -->
# Arnés · encargo «1.5.3 mutación fiable» — **entregado como 1.6.0**

> El fichero conserva el nombre `impl_arnes_1.5.3.md` porque ya estaba
> referenciado, pero **la versión entregada es la 1.6.0**: por decisión del
> humano, absorbe además el porte de F-034 de `albaranes` (el mutador pasa a
> mutar `is` / `is not`) y el conjunto cambia la vara de medir lo bastante como
> para no ser un parche.

- **Repositorio de trabajo**: `C:\Users\pgris\PycharmProjects\arnes-base`
  (rama `main`). En `albaranes` no se ha tocado ni un fichero de código: solo
  este informe.
- **Spec**: `arnes-base/ENCARGO_1.5.3_mutacion_fiable.md`, más el cambio de
  alcance del coordinador (1.6.0 + porte de F-034).
- **Estado**: terminado. `git status` limpio en `arnes-base`, sin worktrees
  vivos, sin centinela huérfano, árbol **no** mutado.

## 1 · Qué había hecho ya el intento previo, y qué he añadido yo

### Ya estaba (sin commitear, lo he revisado y commiteado tal cual)

Las **cuatro piezas del §6** estaban implementadas y funcionando, con sus 19
tests unitarios en verde:

1. **Línea base obligatoria** (`comprobar_linea_base`, `mensaje_base_rota`,
   `BaseRota`), corrida en cada worktree en paralelo y en el árbol en serie,
   con deduplicación por identidad `(directorio, intérprete)` para no repetirla
   por cada fichero del mismo servicio.
2. **Veredicto no binario**: `INDETERMINADO` para los códigos 2/3/4 de pytest,
   resuelto reejecutando la base; `BASE_ROTA` como veredicto propio;
   `InformeMutacion.fiable`, `aviso_base`, cabecera «⚠ CAMPAÑA NO VÁLIDA» en el
   informe y reejecución de la base al cerrar la campaña.
3. **Restauración a prueba de muerte**: `restauracion_ante_senales` (SIGINT y
   SIGTERM), clase `Centinela` con volcado a
   `.arnes_cache/mutacion_en_curso.json`, `--restaurar`, `--estado`, y
   `guardia_arbol_limpio` (`ArbolSucio`).
4. **`init.sh` sección «1 bis»**, que lee el centinela y sale en KO si el árbol
   principal tiene un mutante escrito.

Revisado según el §9 del encargo: leí los tres ficheros enteros y el test.
No encontré nada que deshacer. Dos detalles que comprobé expresamente porque
son fáciles de equivocar y estaban bien: el `case "$?"` de `init.sh` tras la
asignación con sustitución de órdenes (lee el estado de la sustitución, que es
lo que se quiere), y el `__main__` de `mutacion.py`, que delega en el módulo
importado para que `except CampaniaAbortada` cace la excepción de la campaña
paralela y no salga un traceback pelado.

### Lo que he añadido yo

- **La prueba de verdad del §7** (`tests/test_mutacion_prueba_de_verdad.py`,
  6 tests): repositorio git de juguete, suite real, pytest real, y la
  comparación ANTES/DESPUÉS medida. Detalle en §2.
- **Dos defectos más de la misma familia**, encontrados AL montar esa prueba, y
  su arreglo (§3). Los dos producían el mismo pecado: un mutante contado como
  muerto sin que ningún test lo cazara.
- **La ampliación del §5** (tercer caso, en serie), reflejada donde manda: la
  entrada de `GUIA_INSTALACION.md`, el propio encargo y el mensaje de aborto de
  la herramienta, que ahora enumera las causas que muerden en cualquier modo.
- **El porte de F-034** injertado sobre mi `mutacion.py` (§4).
- **La entrega**: `VERSION` a 1.6.0, entrada en `GUIA_INSTALACION.md`.

## 2 · La prueba de verdad: evidencia ANTES/DESPUÉS

El montaje: repositorio git de juguete con `app.py` (dos funciones, una cubierta
por los tests y otra que **nadie** comprueba), `test_app.py` con un test que
depende de `datos.local` —fichero **no versionado**, excluido por `.gitignore`,
el `.env` del escenario real— y un commit inicial. El árbol se ve limpio, así
que la campaña paralela arranca.

El **ANTES** se reproduce devolviendo al mutador sus dos comportamientos de la
1.5.2 —veredicto binario y sin línea base— porque el código de hoy **se niega**
a producir el número falso: sin volver atrás no habría con qué comparar, y una
comparación contra un recuerdo no es una comparación.

### Escenario A · paralelo con un fichero no versionado

Salida real de `python evidencia.py` (script de captura, mismo montaje que los
tests):

```
==============================================================================
ESCENARIO A · CONTROL (serie, arbol principal, base verde)
==============================================================================
generados=5 muertos=2 supervivientes=3 fiable=True
   SUPERVIVIENTE: app.py:3 [entero] if importe > 100: -> if importe > 101:
   SUPERVIVIENTE: app.py:9 [comparacion] if cantidad > 5: -> if cantidad >= 5:
   SUPERVIVIENTE: app.py:9 [entero] if cantidad > 5: -> if cantidad > 6:

==============================================================================
ESCENARIO A · ANTES (paralelo, comportamiento 1.5.2)
==============================================================================
generados=5 muertos=5 supervivientes=0 fiable=True
```

Ahí está el defecto, medido: los **3 supervivientes que el control acaba de
demostrar desaparecen**, la campaña declara 5/5/0 y —lo peor— el informe se
considera **fiable**. Es la misma huella que el `108/108/0` de
`datamart-seg-anual`.

Y el DESPUÉS, sobre el mismo árbol:

```
==============================================================================
ESCENARIO A · DESPUES (paralelo, 1.6.0)
==============================================================================
LÍNEA BASE EN ROJO en C:/Users/pgris/AppData/Local/Temp/mutacion_F-999_kcczsebm/wk_0: la suite falla SIN mutar nada.
Campaña abortada sin escribir informe: sobre una base roja TODO mutante saldría «muerto» y el cero de supervivientes sería falso.

  Tests que fallan sin mutar:
    - test_app.py::test_hay_datos_locales

  Causas conocidas SOLO del modo paralelo (cada worker corre en un
  `git worktree` desechable creado desde HEAD):
    - ficheros NO versionados que la suite necesita (.env, datos locales, fixtures generadas): no existen dentro de un git worktree
    - detached HEAD: el worktree no está en ninguna rama, así que un test que lea `git branch --show-current` recibe cadena vacía
    - instalación editable apuntando al árbol principal: la suite del worker importaría el código de fuera del worktree, sin mutar

  Causas que muerden en CUALQUIER modo, también con --workers 1:
    - la suite se invoca SIN ruta —`python -m pytest` desde la raíz— porque el fichero mutado no cae en ningún servicio de harness/servicios.json: si la raíz no tiene configuración de pytest (testpaths, rootdir), esa invocación recoge lo que no debe y muere en la recolección
    - la suite necesita un servicio externo (base de datos, cola, API) que en esta máquina no está levantado

  Arregla la base. Si la tuya es de las primeras, --workers 1 la esquiva: en
  serie la suite corre sobre el propio árbol y no hay worktree que valga.
```

Aborta, nombra el test culpable y no escribe informe. **El encargo queda
cerrado con esta comparación.**

### Escenario B · el tercer caso, en SERIE

Sin worktrees ni paralelismo: un fichero de test que ni se puede recoger (exit 2
de pytest), que es lo que le pasa a un fichero de `harness/` juzgado con
`python -m pytest` sin ruta.

```
==============================================================================
ESCENARIO B · ANTES (serie, recoleccion rota, comportamiento 1.5.2)
==============================================================================
generados=5 muertos=5 supervivientes=0 en 5.97 s

==============================================================================
ESCENARIO B · DESPUES (serie, 1.6.0)
==============================================================================
LÍNEA BASE EN ROJO en .../b_despues: la suite falla SIN mutar nada.
[...]
  Tests que fallan sin mutar:
    - tests/test_irrecolectable.py
```

## 3 · Dos defectos más, encontrados al montar la prueba

### 3.1 · El aborto no nombraba nada cuando la suite muere en la recolección

**Fase RED, salida real** (el test escrito antes del arreglo):

```
FAILED arnes-base/tests/test_mutacion_prueba_de_verdad.py::test_B_despues_una_recoleccion_rota_aborta_la_campania

>       assert "tests/test_irrecolectable.py" in mensaje
E       AssertionError: assert 'tests/test_irrecolectable.py' in 'LÍNEA BASE EN
        ROJO en .../juguete: la suite falla SIN mutar nada. [...] (pytest salió
        con código 2 sin nombrar tests) [...]'
1 failed, 4 passed in 21.57s
```

La línea base corría con `-rf`, que resume solo los FAILED. Una suite que muere
en la **recolección** no tiene ni un FAILED que enseñar, así que el mensaje
decía «código 2» a secas — y ése es justo el caso más frecuente en modo serie,
el tercero del §5. Arreglado pasando a `-rfE`, y añadiendo el bloque de causas
«que muerden en cualquier modo».

### 3.2 · Bytecode rancio: un mutante juzgado con el `.pyc` del anterior

Apareció como una discrepancia entre dos ejecuciones del mismo control: 3
supervivientes en una, 2 en otra, sobre el mismo repositorio y el mismo código.
El que desaparecía se contaba **MUERTO**.

Causa: CPython da por válido un `.pyc` cuando el fuente conserva el **tamaño** y
el **mtime truncado a segundos enteros**. Dos mutantes consecutivos del mismo
fichero cumplen las dos cosas más a menudo de lo que parece: se escriben en el
mismo segundo y muchas mutaciones cambian el mismo número de bytes (`*`→`//` y
`>`→`>=` añaden uno cada una). El segundo mutante se juzgaba con el bytecode del
primero.

**Fase RED, reproducción mínima con su salida real:**

```
$ printf 'VALOR = 1\n' > m.py && printf 'import m\nprint("VALOR =", m.VALOR)\n' > usar.py
$ python usar.py
VALOR = 1
$ python -c "reescribe m.py con 'VALOR = 9' (mismo tamaño) y restaura su mtime"
tam nuevo: 10
--- con pyc rancio (sin nada) ---
VALOR = 1        <-- se ejecuta el bytecode viejo, no el fuente en disco
--- con PYTHONDONTWRITEBYTECODE=1 ---
VALOR = 1        <-- tampoco basta: el .pyc rancio se sigue LEYENDO
```

Arreglo: `_escribir` tira el `.pyc` del fichero que acaba de escribir
(`_purgar_bytecode`). Se descartó `PYTHONDONTWRITEBYTECODE=1` porque, como
muestra la traza, no evita la **lectura** del `.pyc` que ya está en disco.
Fijado con `test_C_un_mutante_nunca_se_juzga_con_el_bytecode_del_anterior`, que
fuerza la coincidencia con `os.utime` en vez de esperar a que el reloj la
regale: así es reproducible.

Tras el arreglo, el control da **3 supervivientes de forma determinista** en los
dos entornos donde antes discrepaba.

## 4 · El porte de F-034 (`is` / `is not`)

Injertado, no copiado: mi `mutacion.py` ya llevaba las cuatro piezas y el de
`albaranes` no. Del diff de F-034 entra exactamente lo suyo:

- `ast.Is → ("is", "is not")` y `ast.IsNot → ("is not", "is")` en
  `COMPARACIONES`, con su nota de límite conocido (`is  not` no canónico).
- `_es_palabra`, `_delimitado` y el bucle de `_localizar` que exige **palabra
  entera** para los tokens alfabéticos.

No hubo choque real entre los dos cambios: tocan zonas distintas del fichero
(`COMPARACIONES` y `_localizar` estaban idénticos a los de `albaranes`).

**Dos desviaciones, declaradas:**

1. `tests/test_mutacion_operadores.py` se copia, pero su último test
   (`test_f034_r14_...`) comprobaba que la puerta de evals se condiciona a
   `evals/fixtures/`. Eso es **política de `albaranes`**: en cualquier otro
   proyecto con `rutas_sensibles.json` fallaría exigiendo un directorio que no
   existe. En `arnes-base` se queda la mitad genérica —una exigencia que
   arranca en `aviso` debe declarar UNA condición para subir a `bloqueo`— y la
   lección (condicionar una puerta a algo **versionado**, no a lo que el
   `.gitignore` esconde) pasa a `harness/rutas_sensibles.ejemplo.json`, que es
   lo que lee cada proyecto al instalar el arnés. El test se salta en
   `arnes-base` porque ahí no hay `rutas_sensibles.json`.
2. `harness/rutas_sensibles.json` **no se porta**: en `arnes-base` solo existe
   el `.ejemplo.json`, y el contenido del de `albaranes` (evals, sv6, fixtures,
   los seis `_indice.json`) es del proyecto. Lo transferible es la regla, y ahí
   está.

Los retoques de `CHECKPOINTS.md` y `.claude/agents/reviewer.md` sí se injertan
(campaña MANUAL con una fila por mutante y el texto exacto de la sustitución), y
les he añadido lo que pide esta versión: **un informe con «CAMPAÑA NO VÁLIDA» o
con mutantes «sin veredicto» se rechaza sin más análisis**.

## 5 · Entrega

- `arnes-base/harness/VERSION` → `ARNES_VERSION=1.6.0`, `ARNES_FECHA=2026-08-19`.
- Entrada única en `GUIA_INSTALACION.md`, con el formato de la 1.5.1 y la
  1.5.2, contando las dos mitades y abriendo con el aviso destacado de que
  **esta versión cambia la vara de medir**: una campaña verde en cualquier
  proyecto puede volverse roja al actualizar, y los informes anteriores no son
  comparables.
- Su apartado «qué hay que revisar en cada proyecto» **corrige el alcance del
  §5 del encargo**: no basta con las campañas paralelas desde el 2026-08-18;
  hay que repetir **toda** campaña cuyo informe diga cero supervivientes,
  porque el modo serie tiene su propio agujero. Se nombra expresamente el caso
  de `albaranes` (los 19 mutantes de F-034 y los 61 de
  `progress/mutacion_F-012.md`, todos sobre `harness/`), y se da la pista
  práctica: **el tiempo** — una campaña de decenas de mutantes que termina en
  segundos no ha ejecutado ninguna suite.
- `ENCARGO_1.5.3_mutacion_fiable.md` actualizado: cabecera con la entrega real
  y §5 bis con los dos casos nuevos.

## 6 · Commits en `arnes-base` (locales, ningún push, ninguna PR)

| Hash | Qué |
|---|---|
| `860902e` | 1.6.0 (1/4): las cuatro piezas (trabajo previo, revisado y commiteado) |
| `b7dce9d` | 1.6.0 (2/4): la prueba de verdad, y los dos defectos que ha destapado |
| `febb51d` | 1.6.0 (3/4): `is` / `is not` (porte de F-034) |
| `3ceb95b` | 1.6.0 (4/4): entrega — VERSION, guía y §5 ampliado |
| `89a9ba9` | 1.6.0: ruff ordena los imports de los tres tests de mutación |

> Ojo: entre `860902e` y `b7dce9d` aparece `c5b258d` («Ignora los artefactos de
> cobertura desde el bloque gestionado del .gitignore»), que **no es mío**: lo
> commiteó otra sesión en el mismo repositorio mientras trabajaba. No toca
> ninguno de mis ficheros y no ha hecho falta integrarlo a mano.

## 7 · Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`arnes-base/tests`) | **43 passed, 1 skipped, 1 failed** |
| Único fallo | `test_backlog_md.py::test_backlog_md_existe_y_esta_al_dia` — **preexistente y ajeno** (viene del commit `3b46d55`, 1.5.0: el payload no lleva `BACKLOG.md` aunque sí `features.json`). Fuera de alcance por indicación expresa |
| Único skip | `test_la_declaracion_de_rutas_sensibles_dice_cuando_sube_a_bloqueo`: `arnes-base` no declara `harness/rutas_sensibles.json` (solo el `.ejemplo.json`) |
| Punto de partida | 29 passed, 1 failed → **+14 tests** (6 de la prueba de verdad, 8 de operadores) |
| Tiempo de la suite | **22,8 s** (antes 7,2 s: la prueba de verdad lanza pytest de verdad dentro de worktrees de verdad) |
| Cobertura de líneas cambiadas | **No disponible**: `arnes-base` es el repositorio del arnés genérico, no lleva `harness/init.sh` propio ejecutable sobre sí mismo ni puerta de cobertura configurada |
| Campaña de mutación | **No ejecutada**: `arnes-base` no tiene `harness/features.json` de proyecto ni rama `feature/F-XXX`, así que `harness.alcance` no puede calcular alcance. La verificación equivalente aquí es la prueba de verdad del §2, que ejerce el mutador de extremo a extremo |
| Árbol tras la verificación | **No mutado**. `git status` limpio, `git worktree list` con una sola entrada, sin `.arnes_cache/mutacion_en_curso.json` en ningún sitio |

## 8 · Qué queda abierto

1. **`test_backlog_md` sigue en rojo en `arnes-base`** (deuda preexistente,
   `3b46d55`). El payload no incluye `BACKLOG.md` pero sí `features.json`, y el
   test exige el primero. Hay dos salidas razonables —generar un `BACKLOG.md` de
   ejemplo en el payload, o que el test se salte cuando el `features.json` sea
   el de plantilla— y ninguna es mía de decidir.
2. **Los informes de mutación a repetir en `albaranes`**: los de F-034 (19
   mutantes) y F-012 (61), ambos sobre ficheros de `harness/`, más cualquier
   otro con cero supervivientes. Está escrito en la guía, pero **repetirlos es
   trabajo aparte**, no hecho aquí.
3. **41 avisos de `ruff` en `arnes-base`**, de los cuales 3 los añaden mis
   cambios (2 `ISC004` y 1 `DTZ005`), todos siguiendo el estilo ya presente en
   el mismo fichero (`escribir_informe` tenía 4 `ISC004` de antes). `arnes-base`
   no lleva `pyproject.toml`, así que ruff corre con sus reglas por defecto y no
   es representativo de lo que verá un proyecto instalado. No lo he tocado para
   no ensuciar el diff con cambios de estilo.
4. **595 directorios vacíos `mutacion_*` en el temp del sistema**, 94 de hoy.
   Los deja `Worktrees._retirar`, cuyo `shutil.rmtree(..., ignore_errors=True)`
   del directorio padre falla en silencio en Windows. **Ninguno es de mis
   ejecuciones** (las mías, etiquetadas `F-999`, se limpiaron todas: quedan 0);
   590 llevan la etiqueta por defecto `mutacion`, o sea vienen de otro sitio.
   Es basura de temp, no afecta a ningún resultado, y arreglarlo sin entender
   por qué falla el `rmtree` sería improvisar: lo dejo señalado.
