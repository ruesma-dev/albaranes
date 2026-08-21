<!-- specs/F-040-campana-dimensionada-y-honesta/requirements.md -->
# F-040 · Requisitos — la campaña se dimensiona sola y deja de mentir

Notación EARS. Cada R se traduce a >= 1 test. Los bloques D1..D5 son los de la
ficha de `harness/features.json`; el detalle de campo está en
`progress/verificacion_paralela_F-039.md`, sección «RESULTADO REAL — 2026-08-21».

## D1 · El timeout sale de lo medido, no de un número fijo

- **R1.** El sistema debe calcular el **timeout efectivo por mutante** a partir
  de la línea base ya medida: `max(suelo, ceil(peor_linea_base_s × MARGEN))`,
  donde `suelo` es `mutacion.timeout_por_mutante_s` de `harness/rigor.json` y
  `peor_linea_base_s` es el mayor de los tiempos que devuelve
  `comprobar_linea_base`.
- **R2.** El sistema debe conceder a la **línea base** un timeout propio y más
  holgado que el de mutante: `suelo × FACTOR_HOLGURA_BASE`. Se corre una vez por
  worker, no una vez por mutante, así que su coste está acotado.
- **R3.** CUANDO se resuelve el timeout efectivo, el sistema debe imprimirlo por
  pantalla diciendo de dónde sale (línea base medida y margen aplicado).
- **R4.** El informe de mutación debe declarar el **timeout efectivo por
  mutante**, el **suelo configurado** y el **nº de workers** con que se midió.
- **R5.** SI la línea base expira incluso con la holgura de R2, ENTONCES el
  sistema debe abortar sin escribir informe y el mensaje debe nombrar los
  workers en juego y el timeout concedido, no solo «sube el timeout».
- **R6.** DONDE se pase `--timeout N`, el sistema debe usar N como timeout por
  mutante sin calcular nada, y decir por pantalla que el cálculo queda anulado.
- **R7.** MIENTRAS el timeout se calcule, `mutacion.timeout_por_mutante_s` debe
  comportarse como **suelo** (mínimo garantizado), nunca como techo, y su `$doc`
  en `harness/rigor.json` debe decirlo.

## D2 · El default de workers deja de suponer que el cuello es la CPU

- **R8.** El sistema debe calcular los workers por defecto como
  `min(max(1, (núcleos - 2) // 2), TOPE_WORKERS)` con `TOPE_WORKERS = 4`. Cada
  worker arranca **una suite completa** —intérprete, importaciones, E/S—, no un
  hilo: se reservan ~2 núcleos por worker más los 2 que ya se dejaban libres.
- **R9.** El sistema NO debe declarar `mutacion.workers` en `harness/rigor.json`
  (decisión del humano del 2026-08-20: no cablear el límite de una máquina en un
  arnés que viaja). La precedencia `--workers > mutacion.workers > default` se
  mantiene intacta.
- **R10.** El tope calculado no debe limitar lo que se pida a mano: `--workers N`
  con N mayor que el tope debe seguir siendo posible.

## D3 · Una base que expira no es una base rota

- **R11.** CUANDO la línea base de cierre **expira** (código -1), el sistema debe
  emitir un aviso que diga que la suite **no falló**, que se quedó sin tiempo, y
  que la acción es bajar workers o subir el suelo — NO «arregla la suite».
- **R12.** CUANDO la línea base de cierre **falla** (roja, sin expirar), el
  sistema debe emitir el aviso actual, con los tests fallidos nombrados.
- **R13.** En ambos casos el informe debe quedar marcado como no fiable y la
  ejecución salir con código 3 y `CAMPAÑA NO VÁLIDA` (comportamiento de hoy: no
  cambia, cambia el texto).

## D4 · Cero mutantes no puede salir en verde (tercera puerta)

- **R14.** SI una campaña termina con **cero mutantes generados**, ENTONCES el
  sistema NO debe escribir informe y debe salir con **código 3**, con un mensaje
  que diga que no se ha juzgado nada y por qué (alcance vacío o alcance sin
  código mutable).
- **R15.** R14 debe cumplirse por **cualquier** vía de alcance —`--feature`,
  `--ficheros` y las futuras—, porque la guarda vive en el único punto por el
  que todas pasan (`main`), no en cada constructor de alcance.
- **R16.** CUANDO el alcance no tenga ni una línea de producción, el sistema debe
  abortar por el mismo camino de R14 **antes** de correr ninguna línea base.
- **R17.** La guarda de entrada de `alcance_de_ficheros` (CR-2 de F-039) debe
  seguir existiendo con su mensaje propio: es la que explica *qué* ruta sobra.
  R14 es la red final, no su sustituta.

## D5 · Los ocho huecos

- **R18.** (A1) SI al arrancar hay un centinela de una campaña anterior y la
  restauración deja ficheros **irrecuperables**, ENTONCES el sistema debe
  abortar con código 3 sin empezar la campaña: medir encima de un mutante viejo
  es medir el mutante.
- **R19.** (A2) `python -m harness.mutacion --restaurar` debe salir con código 0
  cuando no queda nada que restaurar o se restaura todo, y con 2 si algo queda
  irrecuperable.
- **R20.** (B1) CUANDO el informe contenga al menos un timeout, la sección
  `## Timeouts` debe escribirse con una línea por mutante que nombre el fichero
  y la línea **una sola vez**.
- **R21.** (B2) El aviso de `_base_rota_al_final` debe estar cubierto por test en
  sus dos ramas (R11 y R12) y en la de «base verde al cerrar» (sin aviso).
- **R22.** (D1) SI `mutacion.timeout_por_mutante_s` no es un entero estrictamente
  positivo —incluido un booleano, que hoy pasa como entero y da 1 s—, ENTONCES
  `harness.rigor` debe rechazarlo con un mensaje que distinga «falta la clave» de
  «el valor no vale».
- **R23.** (D2) SI `--timeout` recibe un valor menor o igual a cero, ENTONCES el
  sistema debe salir con código 2 y mensaje de uso, sin arrancar la campaña.
- **R24.** (E) CUANDO `git worktree remove` falle, el sistema debe borrar el
  directorio con `rmtree` y desregistrarlo con `worktree prune`, en ese orden, y
  eso debe estar probado con un git que falla, no solo con uno que funciona.
- **R25.** (F) `python -m harness.rigor` debe salir con código **1** cuando alguna
  ficha declare un nivel inexistente.
- **R26.** (G) La guarda «feature sin `rigor` **o** con `rigor` nulo» de
  `validar_features` debe estar probada por separado en sus dos ramas, con
  fichas que hoy no existen en `harness/features.json`.

## Coherencia del arnés

- **R27.** `CHECKPOINTS.md` (RM2) debe advertir que con W workers el «Tiempo
  total» del informe es aproximadamente `mutantes × media / W`: la regla de
  coherencia escrita para campañas en serie marcaría como incoherente una
  campaña paralela legítima.

## Preguntas abiertas para el humano

1. ¿`MARGEN = 2` y `FACTOR_HOLGURA_BASE = 5` son los valores que quieres, o
   prefieres declararlos en `rigor.json` (con el riesgo de volver a cablear)?
2. Con el timeout ya derivado de lo medido, ¿sigue en pie la decisión de no
   declarar `mutacion.workers`, o el tope 4 la hace innecesaria del todo?
3. ¿`TOPE_WORKERS = 4` o prefieres 3, el único punto con medición real en verde?
4. R23 cambia el significado de `--timeout 0` (hoy cae en silencio al
   configurado): ¿aceptas el cambio de comportamiento?
