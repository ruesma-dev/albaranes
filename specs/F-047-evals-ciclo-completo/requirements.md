<!-- specs/F-047-evals-ciclo-completo/requirements.md -->
# F-047 · Requisitos — el banco recorre el ciclo completo

Notación EARS. Cada R se traduce a >= 1 test. El porqué está en la ficha
(`harness/features.json`); aquí va solo lo exigible.

## A · El ciclo, por el pipeline REAL

**R1.** El sistema debe recorrer por cada caso el pipeline real y completo
—entrada → `q-extraccion` → sv2 → `q-persistencia` → **sv3** → `q-valoracion` →
sv6 → HTTP → sv5 → **sv6 persiste**—, con LAS DOS persistencias y sus colas.

**R2.** La entrada debe replicar lo que hace sv1 con `ruesma_comun` —fila en
`workflow_runs`, blob `input/`, `MensajeExtraccion`—, sin el buzón M365.

**R3.** El sistema debe leer la salida de cada fase de donde el sistema la deja
—Postgres local— y SOLO con `SELECT`: el banco no altera lo que mide.

**R4.** El sistema debe decidir que un caso terminó por EVIDENCIA observable en
la base, nunca por una espera fija.

**R5.** MIENTRAS un caso no avance de hito, el sistema debe contar un plazo por
hito desde el último avance; SI lo agota, el caso queda NO_EVALUABLE diciendo
dónde se quedó, nunca ROJO ni VERDE.

**R6.** CUANDO aparece un mensaje del caso en una cola `-poison`, el sistema debe
dar ese caso por fallado de inmediato, sin agotar el plazo.

**R7.** CUANDO sv3 deja el caso esperando selección de contrato, el sistema debe
actuar como el revisor de sv4 —elegir el declarado en `INPUTS.CASOS.contrato_codigo`
y publicar `MensajeValoracion`— y declarar que ese caso NO midió la selección.

**R8.** El ciclo debe obtener la clasificación del propio sistema y compararla
con `INPUTS.CASOS.tipologia`, en vez de inyectarla como entrada.

**R9.** SI la configuración apunta a colas, blobs o base que no sean los locales,
ENTONCES el sistema debe NEGARSE a arrancar el ciclo.

## B · Atribución del fallo

**R10.** El sistema debe etiquetar cada discrepancia como `PROPIO` (nace aquí),
`ARRASTRADO` (nace aguas arriba) o `INDETERMINADO` (no se puede ligar).

**R11.** `ARRASTRADO` si —y SOLO si— el campo tiene dependencias declaradas Y al
menos una falló en el mismo caso y línea, y debe llevar la fase de origen y el
campo causante. Que fallara la fase anterior no basta.

**R12.** CUANDO una línea del ground truth no aparece en la salida de IA1, toda
discrepancia posterior de esa línea debe ser `ARRASTRADO` a IA1.

**R13.** SI la identidad de una línea discrepa en IA1, aunque sea como aviso,
ENTONCES toda discrepancia posterior de esa línea debe ser `INDETERMINADO`.

**R14.** Una fase debe ser ROJA solo por sus fallos `PROPIO`; y MIENTRAS haya
`INDETERMINADO` sin ningún `PROPIO`, la pasada debe ser NO_EVALUABLE, no VERDE.

**R15.** El mapa de dependencias debe ser versionado y legible; SI declara un
campo que ninguna proyección produce, la carga debe ABORTAR nombrándolo.

## C · Qué ground truth se reutiliza

**R16.** IA1, IA2, IA3, IA4 y RESULTADO_FINAL siguen siendo la expectativa de su
fase, sin regenerar ni tocar los libros.

**R17.** `INPUTS.LINEAS_ALBARAN`, `INPUTS.CONTRATO_LINEAS` y las condiciones que
produce una IA dejan de inyectarse en ciclo, y el informe debe declararlas como
«entrada que ahora produce el sistema».

**R18.** SI una condición no la produce ninguna fase ni el contrato leído —caso
de `tamano_contenedor_contrato`—, ENTONCES el criterio que dependa de ella queda
NO_EVALUABLE y se declara; nunca se inyecta a mano.

**R19.** SI la conciliación IA4 no llegó a ejecutarse en un caso —ninguna línea
la necesitaba, o falló como best-effort—, IA4 queda OMITIDO ahí, nunca VERDE.

## D · Aislamiento, reproceso y limpieza

**R20.** Cada pasada debe identificarse, y sus documentos deben distinguirse de
los de otra pasada y de lo que ya hubiera en la base local; dos casos de la misma
pasada no pueden compartir documento ni clave de correlación.

**R21.** ANTES de una pasada normal, el sistema debe retirar de en medio los
documentos de pasadas anteriores del banco por la MISMA vía que usa el sistema
(baja lógica), nunca borrando filas a mano.

**R22.** DONDE se pida una corrida de reproceso, el sistema debe reinyectar a
propósito documentos ya presentes para ejercitar la rama de duplicado y el
re-fetch, y comprobar que no se pierde `contexto_linea` ni se anula la clasificación.

**R23.** El sistema debe dejar la base consultable al terminar y ofrecer la
limpieza de una pasada como acción aparte y explícita.

## E · Las dos formas de correr y el entorno

**R24.** El sistema debe conservar las corridas por fase con entradas de los
libros, pedibles explícitamente, para aislar un defecto sin pagar el ciclo.

**R25.** CUANDO se pide una pasada con LLM sin decir la forma, el sistema debe
ejecutar el CICLO: es la forma por defecto. El determinista no cambia.

**R26.** El informe debe declarar en línea parseable qué forma se corrió; solo la
del ciclo vale como evidencia de pasada completa.

**R27.** ANTES de inyectar ningún caso, el sistema debe comprobar que responden
Azurite, Postgres, sv2, sv3, sv5 y sv6, y que están las claves LLM, las
credenciales de sigrid-api, los ficheros de albarán y los fixtures.

**R28.** SI falta algo, ENTONCES el sistema debe nombrar QUÉ falta y salir
NO_EVALUABLE sin inyectar un caso ni gastar una llamada.

**R29.** El sistema debe usar sigrid-api SOLO en lectura y respetar sus topes
(1.000 filas por petición, corte a los 230 s).

## F · El coste

**R30.** `--casos` debe acotar el ciclo entero, no solo sus primeras fases.

**R31.** El sistema debe poder reaprovechar una pasada anterior leyendo de la
base los casos ya completados en vez de reinyectarlos.

**R32.** El sistema debe poder reentrar por los mismos puntos que ofrece el
sistema real —re-fetch de contratos y revaloración— sin repetir la extracción.

**R33.** El sistema debe volcar lo leído de cada caso fuera de git para rehacer el
informe sin base; lleva precios de proveedor y NUNCA se versiona ni entra en
`evals/fixtures/`, cuya única puerta sigue siendo el conversor.

## G · El informe

**R34.** El informe debe conservar los ejes de hoy —no regresión frente a defecto
conocido, y los rojos que nacen esperados aparte— y sumarles el de atribución.

**R35.** Cada fase debe traer su cuadro con propios, arrastrados, indeterminados y
omitidos por separado, y los fallos deben poder leerse agrupados por fase de ORIGEN.

**R36.** El informe debe declarar QUÉ COSTURAS NO VIGILA esta corrida, para que
nadie le suponga al banco una cobertura que no tiene.

**R37.** Las secciones de campos no observables y de campos sin clasificar deben
seguir separadas y con su texto de hoy.

## H · Verificación manual

**R38.** MANUAL: pasada de ciclo acotada a casos de familias distintas, con el
pipeline local levantado, revisando que la atribución apunta a la fase correcta.

**R39.** MANUAL: la corrida de reproceso de R22 sobre un caso ya procesado.

**R40.** MANUAL: la pasada de ciclo sobre los 59 casos, que cuesta API real y
tiempo, y que decide el humano cuándo se lanza.
