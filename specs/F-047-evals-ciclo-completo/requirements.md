<!-- specs/F-047-evals-ciclo-completo/requirements.md -->
# F-047 · Requisitos — el banco recorre el ciclo completo

Notación EARS; cada R se traduce a >= 1 test. El porqué, en la ficha.

## A · El ciclo, por el pipeline REAL

**R1.** Cada caso debe recorrer el pipeline real —entrada → `q-extraccion` → sv2 →
`q-persistencia` → **sv3** → `q-valoracion` → sv6 → sv5 → **sv6 persiste**—, con
LAS DOS persistencias y sus colas.

**R2.** La entrada replica lo de sv1 con `ruesma_comun` —`workflow_runs`, blob
`input/`, `MensajeExtraccion`—, sin buzón M365.

**R3.** El sistema debe leer la salida de cada fase de donde el sistema la deja
—Postgres local— y SOLO con `SELECT`: el banco no altera lo que mide.

**R4.** Un caso termina por EVIDENCIA observable, no por espera fija: MIENTRAS no
avance de hito corre un plazo desde el último avance, agotarlo es NO_EVALUABLE con
su hito, y salir en una cola `-poison` es fallar en el acto.

**R5.** CUANDO sv3 deja el caso esperando contrato, el sistema hace el gesto del
revisor de sv4 —elegir el de `INPUTS.CASOS.contrato_codigo` y publicar
`MensajeValoracion`— y declara que ese caso NO midió la selección.

**R6.** El ciclo debe obtener la clasificación del propio sistema y compararla con
`INPUTS.CASOS.tipologia`, en vez de inyectarla como entrada.

**R7.** SI la configuración apunta a colas, blobs o base no locales, el sistema
debe NEGARSE a arrancar el ciclo.

## B · Atribución del fallo

**R8.** El sistema debe etiquetar cada discrepancia como `PROPIO` (nace aquí),
`ARRASTRADO` (nace aguas arriba) o `INDETERMINADO` (no se puede ligar).

**R9.** `ARRASTRADO` si —y SOLO si— el campo tiene dependencias declaradas Y una
falló en el mismo caso y línea; llevará fase de origen y campo causante.

**R10.** CUANDO una línea del ground truth falta en IA1, lo posterior de esa línea
es `ARRASTRADO` a IA1; SI su identidad discrepa allí, es `INDETERMINADO`.

**R11.** Una fase debe ser ROJA solo por sus fallos `PROPIO`; y MIENTRAS haya
`INDETERMINADO` sin ningún `PROPIO`, la pasada debe ser NO_EVALUABLE, no VERDE.

**R12.** El mapa de dependencias debe ser versionado y legible; SI declara un
campo que ninguna proyección produce, la carga debe ABORTAR nombrándolo.

## C · Qué ground truth se reutiliza

**R13.** Los cinco libros de expectativa valen sin regenerarse; lo que ahora
produce el sistema —`LINEAS_ALBARAN`, `CONTRATO_LINEAS`, condiciones— deja de
inyectarse y se declara.

**R14.** SI una condición no la da ninguna fase ni el contrato leído —caso de
`tamano_contenedor_contrato`—, su criterio queda NO_EVALUABLE; nunca se inyecta.

**R15.** SI la conciliación IA4 no llegó a ejecutarse en un caso, IA4 queda
OMITIDO ahí, nunca VERDE.

## D · Aislamiento, reproceso y limpieza

**R16.** Cada pasada debe identificarse y sus documentos distinguirse de los de
otra y de lo ya existente; dos casos no comparten documento ni clave.

**R17.** ANTES de una pasada debe retirar los documentos anteriores del banco por
la vía del sistema (baja lógica); la base queda consultable y limpiarla es aparte.

**R18.** DONDE se pida reproceso, debe reinyectar documentos ya presentes para
ejercitar duplicado y re-fetch sin perder `contexto_linea` ni la clasificación.

## E · Formas de correr y entorno

**R19.** El sistema debe conservar las corridas por fase con entradas de los
libros, pedibles explícitamente, para aislar un defecto sin pagar el ciclo.

**R20.** Una pasada con LLM sin más es el CICLO; el determinista no cambia. El
informe declara la forma en línea parseable y solo el ciclo vale como completa.

**R21.** ANTES de inyectar nada debe comprobar Azurite, Postgres, sv2/sv3/sv5/sv6,
claves LLM, `SIGRID_API_*`, ficheros y fixtures; SI falta algo, nombra cuál y sale
NO_EVALUABLE sin gastar nada.

**R22.** El sistema debe usar sigrid-api SOLO en lectura y respetar sus topes
(1.000 filas por petición, corte a los 230 s).

## F · El coste

**R23.** `--casos` debe acotar el ciclo entero, no solo sus primeras fases.

**R24.** Debe reaprovechar una pasada anterior leyendo de la base los casos ya
completos, y reentrar por los puntos reales —re-fetch y revaloración—.

**R25.** El sistema debe volcar lo leído de cada caso fuera de git para rehacer el
informe y las fichas sin necesidad de la base.

## G · Contraste manual, caso por caso

**R26.** Debe producir por caso una FICHA legible por una persona con lo esperado,
lo obtenido y la atribución fase a fase, sin abrir JSON ni cruzar ficheros.

**R27.** Cada ficha debe mostrar la COSTURA de cada fase —qué entró y qué salió—
para señalar dónde se rompió: si IA3 valoró mal, qué recibió de IA2.

**R28.** Cada ficha identifica el papel —código, fichero original, formato,
familia— según `evals/mapa_casos.json`, con la ruta local del original.

**R29.** El sistema debe poder mostrar UN caso sin ejecutar el ciclo y sin leer
los 58 restantes, desde el volcado de una pasada ya hecha.

**R30.** Por defecto emite ficha solo de los casos no limpios; las demás, a petición.

**R31.** El informe de `progress/` NO debe traer valores del albarán ni del
contrato: solo campo, veredicto y atribución. Los valores, en las fichas y fuera
de git.

## H · Que la revisión manual no se pierda

**R32.** Debe ofrecer un registro VERSIONADO donde anotar por caso y campo la
conclusión del humano —«defecto real» o «artefacto del banco»— con nota, fecha y
pasada, y sin valores del albarán ni del contrato.

**R33.** CUANDO la conclusión es «artefacto del banco», la anotación debe nombrar
el arreglo pendiente y el informe agruparla aparte, con los dos recuentos.

**R34.** Una anotación NO debe cambiar por sí sola el veredicto de una fase ni de
la pasada: declara y agrupa, no silencia.

**R35.** SI la expectativa contra la que se anotó ha cambiado, la anotación debe
marcarse CADUCADA y volver a pendiente, nunca aplicarse en silencio.

**R36.** El informe debe listar los casos revisados y los que siguen SIN revisar,
para que se vea cuánto del banco ha pasado por ojos humanos.

## I · El informe

**R37.** Debe conservar sus ejes de hoy —no regresión frente a defecto conocido,
rojos esperados aparte, no observables y sin clasificar en secciones propias— y
sumar propios, arrastrados, indeterminados y omitidos por fase, más los fallos
agrupados por fase de ORIGEN.

**R38.** El informe debe declarar QUÉ COSTURAS NO VIGILA, para que nadie le suponga al banco una cobertura que no tiene.

## J · Verificación manual

**R39.** MANUAL: pasada acotada a familias distintas con el pipeline local
levantado, contrastando fichas contra el papel y anotando un caso en el registro.

**R40.** MANUAL: la corrida de reproceso de R18, y la pasada sobre los 59 casos,
que cuesta API real y tiempo y que decide el humano cuándo se lanza.
