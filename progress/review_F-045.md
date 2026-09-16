<!-- progress/review_F-045.md -->
# F-045 · Review final: los dos supervivientes y el repaso del patrón

**Revisión incremental desde `e7ca7e5` (pasada 5)** — HEAD `758b151`, 1 commit.
Lo aprobado en las pasadas anteriores queda dado por bueno; aquí se revisa
`e7ca7e5..HEAD` (solo tests y papeleo: **ni una línea de producción**, así que
la campaña del lote sigue midiendo el alcance que se revisa), más las puertas
enteras.

## Veredicto: APROBADO

Los dos puntos que bloqueaban están cerrados y lo he comprobado ejecutando: el
superviviente 3 **muere** con el test reescrito y el 7 **es equivalente de
verdad**, demostrado sobre la huella real y no sobre un ejemplo. El repaso del
patrón se sostiene: he buscado yo el mismo defecto por todo el banco de tests de
F-045 y no queda ningún sitio donde comparar una proyección pueda tapar el
resultado.

## Las puertas, ejecutadas enteras

`bash harness/init.sh` → **exit 0**: **865 tests** en 116 s; COBERTURA `[OK]
98,3 % de 115 líneas (113/115)`; RUTAS SENSIBLES `N/A` con su motivo; TAMAÑO
todo dentro. Árbol limpio, sin `push`, `README.md` sin tocar.

## Superviviente 3: muere, y el test ya mira lo que debe

Reinyectado sobre el código de hoy (`escritura.py`, `if nueva is None and
campo_prefijo:` → `or`) con la suite acotada de 296 tests: **MUERE**, y lo mata
`test_f045_r17_el_casado_por_prefijo_no_duplica_la_sintetica_del_humano`. El
test ya no colapsa las filas en un `dict` por descripción: compara **la lista
entera**, `[("INCREMENTO", 10), ("INCREMENTO LER 170604", 99)]`, que es donde se
ve la tercera fila que el mutante añadía —la del humano conservada **y** la del
importador añadida, el banco esperando dos sintéticas donde el sistema emite
una—. El nombre nuevo dice lo que vigila, que antes tampoco.

## Superviviente 7: equivalente, y comprobado sobre la huella real

No me fié del ejemplo: cargué la **huella real del repositorio** (10 tablas,
717 filas) y serialicé con `sort_keys=True` y con `False` desde la misma
estructura que construye `guardar`.

- Ambas salidas: **35.673 bytes, idénticas** (`IDENTICOS: True`), y coinciden
  byte a byte con `evals/huella_importacion.json` versionado.
- El argumento estructural se sostiene donde importa: dentro de `tablas` **todo
  son listas**, no `dict`, así que `sort_keys` no tiene nada que reordenar. Es
  justo lo contrario de `mapa.py`, donde los registros se montaban en el orden
  de `CAMPOS` y esa misma justificación era falsa.

Y la etiqueta ya está corregida donde se lee: `mutacion_F-045_lote2.md`
(«**8 cerrados con test y 1 equivalente justificado**»), la tabla de Evidencias
del informe y el inventario de campañas dicen lo mismo, con la historia de las
dos correcciones escrita en vez de tapada.

## El repaso del patrón: lo he rehecho por mi cuenta

No conté lo que él cuenta; busqué el defecto. Recorrí los ficheros
`tests/test_f045_*` buscando dónde una **proyección** puede tapar el resultado:

- **`dict` por un campo sobre filas fundidas**: cero ocurrencias. Era el único
  sitio y está arreglado.
- **`set(...)`**: 13 usos, todos sobre **nombres** —columnas, tablas, campos del
  mapa, extensiones, familias, `caso_id`— donde el duplicado es imposible o no
  significa nada; uno de ellos (`len(claves) == len(set(claves))`) es
  precisamente una comprobación de duplicados.
- **`assert len(...)` como única comprobación de una lista de filas**: quedan
  seis, y en todos la lista de entrada **no admite altas** (se funde con
  `nuevas=[]`) o el propio recuento ES la propiedad —«no se eligió ninguno
  candidato»: 2 + 1 = 3 filas—. Ninguno puede esconder una fila duplicada.
- **Comparaciones contra literal de `set`/`dict`**: sobre etiquetas y recuentos,
  y las que proyectan `plan.copias` van acompañadas del recuento o del `fallos
  == []` que hace imposible el duplicado.
- Los tres tests de fusión que solo miraban el número ahora fijan **qué fila
  queda y con qué valores** (`[(descripcion, precio, comentario)] == [...]`),
  incluido el del `modifier_source` que sobrevive a la refundición.

Mi conclusión coincide con la suya, pero medida por separado: **no queda ningún
falso verde de esta familia** en el banco de F-045.

## Checkpoints

- **C1** [x] exit 0 y ficheros obligatorios. **C2** [x] una feature
  `in_progress`, rama correcta, `current.md` al día.
- **C3** [x] este lote no toca producción; lo aprobado en las pasadas anteriores
  sigue en pie (dominio puro, ruta en la primera línea, sin prints ni secretos).
- **C3 bis** N/A **justificado**: no toca `docs/referencia/`.
- **C4** [x] 865 en verde; cada requisito con su test trazable, y los que
  comprobaban de mentira ya no lo hacen.
- **C4 bis** [x] **cerrado**: fase RED con trazas, cobertura `[OK]`, dos
  campañas con sus totales recalculados por mí (capa 1: 266 mutantes;
  lote 2: 325 líneas y 44 mutantes, más los **11 posteriores al SHA medido que
  reinyecté yo y mueren**), RM1 comprobado en las dos, RM2 coherente (871 s ×
  4 workers ÷ 44 = 79 s frente a línea base 88 s), RM3 sin equivalentes muertos,
  RM4 usado en cada pasada, **RM5 con muestra reproducida** —el único
  equivalente del lote, demostrado sobre el dato real— y RM6 sin defensa
  eliminada.
- **C4 ter** [x] la puerta corre y sale N/A con su motivo.
- **C5** [x] commits por tarea, `tasks.md` marcado, sin temporales, estado real
  en `features.json`; informes de campaña separados por lote, como F-043.

## Lo que este review deja atado, para que no se pierda

1. **La restauración de los 38 valores** (35 + los 3 `modifier_source`) está
   verificada valor a valor contra `5132bdc` y `697f00e`: **cero degradados** y
   ninguna fila del original sin pareja hoy.
2. **El guardián** `tests/datos/afirmado_por_el_humano_RES.json` fija 496
   valores —433 idénticos al estado sano previo, ninguno centinela— y **falla
   nombrando el campo** cuando degrado uno a mano. Es la red que faltaba,
   porque los libros `.xlsx` no se versionan.
3. **La guarda de retirada** es más estricta que la anterior y sus 11 mutantes
   mueren. Riesgo residual anotado y **no bloqueante**: un valor del humano en
   una columna que el importador nunca escribe ni deja en `?` no protege su
   fila; si algún día se retiran filas fuera de los 7 RES, conviene ampliar
   `interrogantes` a todas las columnas que el importador produce en esa tabla.

## Condiciones de cierre que siguen siendo del humano

- **Los documentos que faltan**: RES-020 y RES-021 siguen sin papel y salen
  OMITIDOS; los otros 57 ya están renombrados a su `caso_id`.
- **`codigo_imputacion` en `?`** en las 114 líneas: columna nueva en el Excel o
  aceptar la ceguera de la mitad de extracción del patrón 1.
- **`INPUTS.CONTRATO_LINEAS` y `CONDICIONES`**: sin ellas IA3, IA4 y el E2E no
  miden nada; las tres vías están medidas en `impl_F-045_contrato_lineas.md`.

Y fuera de este lote, anotados para su ficha y **sin efecto en el veredicto**:
`ALBARAN VALORADO` leído al revés (9 líneas, 17 fallos falsos) y la
consolidación de FER-002 (37 fallos que no son defectos).
