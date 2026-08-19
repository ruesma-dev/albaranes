<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **38 features**, 32 abiertas, 6 terminadas.

En curso: **F-034**.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-034 | Arnés: la mutación no muta `is`/`is not`, y dos incoherencias que la puerta de evals arrastra | 1 | en curso | estandar | `feature/F-034-mutacion-is-y-coherencia-evals` |
| F-035 | Arnés: el instalador en modo `actualizar` no puede pisar ficheros de estado del proyecto | 2 | spec lista | estandar | `feature/F-035-instalador-no-pisa-estado` |
| F-038 | Arnés: bajar el coste en tokens del ciclo SDD sin bajar el rigor | 3 | pendiente | estandar | `feature/F-038-coste-del-ciclo-sdd` |
| F-036 | La cantidad de residuos se valora sin la regla de contenedores en unos albaranes sí y en otros no, y los incrementos por LER nunca se emiten | 4 | pendiente | critico | `feature/F-036-residuos-contenedores-e-incrementos` |
| F-037 | sv4: al seleccionar un contrato, guardar directamente sin pulsar Guardar | 5 | pendiente | estandar | `feature/F-037-guardado-inmediato-contrato` |
| F-024 | La unidad de medida no se extrae: unidad_medida NULL en las líneas base de hormigón y mortero | 6 | pendiente | estandar | `feature/F-024-unidad-medida` |
| F-028 | Con dos contratos candidatos no se elige ninguno y el albarán no llega a valorarse | 7 | pendiente | critico | `feature/F-028-selector-contrato-por-partidas` |
| F-029 | Obra resuelta por texto sin detectar empates: score 1,00 a la obra equivocada | 8 | pendiente | critico | `feature/F-029-obra-empates-y-sin-cif` |
| F-030 | IA2 busca el proveedor parecido cuando el CIF leído no casa con ninguno de Sigrid | 9 | pendiente | estandar | `feature/F-030-proveedor-cif-aproximado` |
| F-031 | La partida del albarán no se usa para elegir la línea de contrato cuando la descripción no coincide | 10 | pendiente | estandar | `feature/F-031-partida-elige-linea-contrato` |
| F-032 | precio_neto no tiene semántica única y genera line_net_mismatch masivo | 11 | pendiente | estandar | `feature/F-032-semantica-precio-neto` |
| F-033 | El contrato llega a sv5 en Markdown o en PDF según el documento, sin criterio determinista | 12 | pendiente | estandar | `feature/F-033-contrato-md-o-pdf-determinista` |
| F-023 | Mortero: las sintéticas de contrato no se emiten porque IA3 y sv6 las vetan por tipo_familia | 13 | pendiente | critico | `feature/F-023-mortero-incrementos` |
| F-015 | Líneas tachadas del albarán: no se registran | 14 | pendiente | estandar | `feature/F-015-lineas-tachadas` |
| F-021 | Partida: validación contra el catálogo del contrato y elección asistida entre candidatas | 15 | pendiente | estandar | `feature/F-021-partida-catalogo-candidatas` |
| F-016 | Reparto de una línea del albarán entre varias partidas | 16 | pendiente | estandar | `feature/F-016-linea-multipartida` |
| F-026 | Guard de partida de la línea BASE antes de escribir en contrato_lines_derived | 17 | pendiente | estandar | `feature/F-026-guard-partida-base` |
| F-025 | El motivo no_quantity_in_albaran es una falsa alarma sistemática cuando se omite la conversión de unidad | 18 | pendiente | estandar | `feature/F-025-motivo-conversion-omitida` |
| F-020 | El pipeline es agnóstico al proveedor de IA: ninguna fase privilegia a OpenAI | 19 | pendiente | estandar | `feature/F-020-proveedor-agnostico` |
| F-003 | Tanda 2 — Albaranes valorados, match estricto y coherencia (G3+G4+G5) | 20 | spec lista | estandar | `feature/F-003-valorados-match-estricto` |
| F-014 | Conversor del formato plano del administrativo a fixtures de evals | 21 | pendiente | estandar | `feature/F-014-conversor-administrativo` |
| F-018 | Carga incompleta: línea siempre generada por IA2 y cantidad fijada por IA3 con mínimo por defecto 6 m³ | 22 | pendiente | estandar | `feature/F-018-carga-incompleta` |
| F-004 | Tanda 3 — Hormigón fino y veto de mortero | 23 | spec lista | estandar | `feature/F-004-hormigon-fino` |
| F-005 | Tanda 4a — Tipología bombeo | 24 | spec lista | estandar | `feature/F-005-bombeo` |
| F-006 | Tanda 4b — Residuos: lógica de pago LLEVAR/RETIRAR y canon | 25 | spec lista | estandar | `feature/F-006-residuos-pago` |
| F-007 | Tanda 5 — Partida ALM por defecto y selector de candidatas en sv4 | 26 | spec lista | estandar | `feature/F-007-partida-alm-selector` |
| F-017 | El comparativo como fuente de precio (1c) en la valoración | 27 | pendiente | estandar | `feature/F-017-comparativo-precio` |
| F-013 | Registro del albarán aprobado en Sigrid (consumidor de q-feedback) | 28 | pendiente | critico | `feature/F-013-registro-sigrid` |
| F-008 | Lifecycle de blobs de hand-off | 29 | pendiente | estandar | `feature/F-008-blob-lifecycle` |
| F-009 | Limpieza de la cola huérfana q-emails | 30 | pendiente | estandar | `feature/F-009-limpieza-q-emails` |
| F-010 | Easy Auth en el portal sv4 | 31 | pendiente | critico | `feature/F-010-easy-auth-sv4` |
| F-022 | Bandeja de portada: el concepto de las líneas del albarán sale vacío porque el JOIN de la línea derivada apunta a la tabla equivocada | 32 | pendiente | estandar | `feature/F-022-concepto-lineas-bandeja` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Test de estructura del monorepo | 1 | estandar |
| F-019 | Importe de línea: manda el unitario leído; el importe solo se despeja si faltan campos | 1 | critico |
| F-011 | Evals de IA con ground truth y puerta en el arnés | 2 | estandar |
| F-027 | Error de ×1000 en el importe: la red KG→TN de UnitConverter es código muerto | 2 | critico |
| F-012 | Campaña de mutación en paralelo | 3 | estandar |
| F-002 | Tanda 1 — Identificación de obra y proveedor (G1+G2) | 4 | estandar |

## Detalle

### F-034 · Arnés: la mutación no muta `is`/`is not`, y dos incoherencias que la puerta de evals arrastra

estado **en curso** · prioridad 1 · rigor `estandar` · SDD sí · rama `feature/F-034-mutacion-is-y-coherencia-evals`

URGENTE Y PRIMERO (decisión del humano, 2026-08-19): esto cambia la VARA DE MEDIR de todas las features, así que cada feature que se cierre antes de arreglarlo se mide con una campaña de mutación ciega en su punto más delicado. Sale de las observaciones del reviewer de F-027 (progress/review_F-027.md §12) y de la experiencia de F-019.

(1) HALLAZGO PRINCIPAL — `harness/mutacion.py` NO muta `is` / `is not`. Confirmado por el reviewer leyendo la tabla `COMPARACIONES` del propio mutador. En Python `x is None` es LA guarda de ausencia, y es justo el patrón de las guardas que han provocado los dos defectos más caros del proyecto: el `if cantidad is None` que mataba la red KG→TN (F-027, 468.763 €) y el `importe_albaran_declarado is not None` del cálculo del importe (F-019). Es un punto ciego que afecta a CUALQUIER feature de CUALQUIER proyecto con este arnés: la campaña dice «0 supervivientes» sin haber probado la línea que más importa. En F-027 obligó a una campaña MANUAL de 7 mutantes. PROPUESTA: añadir `ast.Is` / `ast.IsNot` a `COMPARACIONES` en `harness/mutacion.py`, comprobar que la campaña de F-027 y la de F-019 generan ahora mutantes en esas guardas y que MUEREN con los tests que ya existen (si alguno sobrevive, es un hueco real que hay que cerrar), y PORTARLO A `arnes-base` en el mismo trabajo (regla de propagación de CLAUDE.md).

(2) CORREGIDO EN F-034 (la premisa del enunciado era falsa): `evals/ground_truth/` SI EXISTE, con sus seis libros .xlsx, y `evals/conversor.py:39` los declara como RUTA_GROUND_TRUTH; lo que pasa es que `.gitignore` excluye *.xlsx, asi que no estan versionados y quien clona el repositorio no los ve. El defecto real es otro: `CHECKPOINTS.md` C4 ter, `harness/rutas_sensibles.json` y `progress/current.md` condicionaban la subida de la puerta a ese artefacto INVISIBLE en vez de a los fixtures VERSIONADOS de `evals/fixtures/`, que son los que consume `evals.runner`. Consecuencia práctica: la puerta de rutas sensibles lleva semanas en `aviso` «porque el ground truth está vacío» sin que nadie pueda comprobarlo sin adivinar dónde mirar. Unificar el nombre en los tres sitios.

(3) Cuando la campaña automática da 0 mutantes y se sustituye por una MANUAL, hoy el guion vive en el scratchpad de la sesión y no queda rastro reproducible en el repositorio. En F-027 bastó porque las siete sustituciones estaban escritas con su texto exacto y el reviewer pudo reproducir cuatro al pie de la letra. PROPUESTA para `CHECKPOINTS.md`: exigir que la tabla de una campaña manual incluya el TEXTO EXACTO original → mutado de cada sustitución, que es lo que la hace verificable.

ALCANCE: `harness/mutacion.py`, `CHECKPOINTS.md`, `harness/rutas_sensibles.json`, `progress/current.md`, y la propagación a `arnes-base` (que subiría a 1.6.0). NO ENTRA: rehacer el mutador ni añadir más operadores de los citados. Fuente: progress/review_F-027.md §12.

### F-035 · Arnés: el instalador en modo `actualizar` no puede pisar ficheros de estado del proyecto

estado **spec lista** · prioridad 2 · rigor `estandar` · SDD sí · rama `feature/F-035-instalador-no-pisa-estado`

Sale de un incidente real: el 2026-08-19, al actualizar el arnes de 1.5.0 a 1.5.2 con `instalar_arnes.ps1 -Modo actualizar`, el instalador ofrecio -y aplico- sobrescribir con sus PLANTILLAS GENERICAS ficheros que son ESTADO DEL PROYECTO, no arnes: `harness/features.json` paso de 34 features a 1 (el ejemplo F-001), `docs/ARCHITECTURE.md` de 183 a 37 lineas, y `progress/current.md` e `progress/history.md` perdieron 157 y 161 lineas. Nada se habia commiteado y se recupero entero desde git, y el 1.5.2 se acabo aplicando por copia quirurgica (commit 3a146cd), pero la proxima vez puede tocar a alguien que haga `git add -A` sin mirar.

EL DEFECTO no es del humano que pulso enter de mas: es que el instalador no distingue entre ficheros DEL ARNES (que puede y debe actualizar) y ficheros DE ESTADO del proyecto que solo existen porque el proyecto lleva meses trabajando. Que la GUIA diga 'casi siempre hay que conservarlos' no basta: una lista de intocables no se aplica leyendola, se aplica en el codigo.

PROPUESTA para `instalar_arnes.ps1`: (1) una lista de INTOCABLES que en modo `actualizar` ni siquiera se ofrecen -`harness/features.json`, todo `progress/`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/referencia/`, `.claude/settings.json`-, y que el resumen final cuente aparte como 'protegidos'; (2) los ficheros con marcas de adaptacion (`CLAUDE.md`, `CHECKPOINTS.md`) siguen preguntando, pero con el diff y con el default en CONSERVAR; (3) que el instalador escriba un backup de lo que va a pisar antes de pisarlo -hoy hace `Copy-Item -Force` sin red-, en una carpeta con sello de fecha fuera del repositorio; (4) revisar si el modo `actualizar` deberia negarse a correr con el arbol de trabajo sucio o sobre una rama que no sea la de integracion, que es lo que agravo este caso (se ejecuto sobre una rama de feature 25 commits por detras de dev).

ALCANCE: `instalar_arnes.ps1` y `GUIA_INSTALACION.md`, ambos EN `arnes-base` (esta feature se implementa alli y aqui solo se consume: subiria a 1.5.3). NO ENTRA: rehacer el instalador ni cambiar el modo `instalar`, que no pisa nada por diseno. Fuente: sesion 2026-08-19; copia de lo que dejo el instalador en el scratchpad de esa sesion, `backup_arnes_20260819/`.

### F-038 · Arnés: bajar el coste en tokens del ciclo SDD sin bajar el rigor

estado **pendiente** · prioridad 3 · rigor `estandar` · SDD sí · rama `feature/F-038-coste-del-ciclo-sdd`

Pedido por el humano el 2026-08-19 con cinco proyectos en marcha y consumo alto. Medicion de la sesion: los cuatro subagentes gastaron ~712.000 tokens (implementer F-034 234k, agente del arnes 1.6.0 206k, spec-author F-034 159k, spec-author F-035 113k) y progress/ acumula 12.250 lineas, con review_F-019.md en 1.365 e impl_F-019.md en 1.189. La campana de mutacion NO gasta tokens -es Python y pytest, gasta CPU-: el coste esta en el papeleo y en las repeticiones. Cada linea de spec se paga TRES veces: la escribe el spec-author, la lee el implementer y la relee el reviewer; las 978 lineas de la spec de F-035, para arreglar un script PowerShell, son casi mil lineas por tres.

CUATRO PALANCAS APROBADAS POR EL HUMANO:

(1) TOPES DE TAMANO. El arnes no dice nada del tamano y por eso los agentes escriben cuanto se les ocurre. Fijar en specs/SPECS.md y en los tres agentes: requirements.md <= 120 lineas, design.md <= 200, tasks.md sin tope duro pero una tarea por linea, informe de implementer <= 150, informe de review <= 100. Son topes, no objetivos: lo que no cabe se resume y se enlaza. Es la palanca de mas ahorro (40-50% del papeleo) y la mas barata.

(2) COSTE DE LA MUTACION en harness/rigor.json: nivel_por_defecto pasa de 'critico' a 'estandar' (hoy toda feature que no declara rigor arrastra 0 supervivientes tolerados, que es el modo mas caro), y se anade max_mutantes POR NIVEL -20 en estandar con semilla fija para que sea reproducible, sin tope en critico-. harness/mutacion.py ya acepta --max-mutantes y --semilla: falta leerlos del nivel. Acota la campana y, sobre todo, el numero de supervivientes que hay que analizar por escrito, que es lo que de verdad cuesta.

(3) UMBRAL DE REEJECUCION DEL REVIEWER de 5 minutos a 60 segundos (.claude/agents/reviewer.md y CHECKPOINTS.md C4 bis, introducidos hoy mismo en la 1.5.2). Sigue cubriendo el fraude de 'N muertos inventados' en campanas baratas y deja de duplicar el trabajo en las caras.

(4) REVIEWER INCREMENTAL POR DEFECTO. En la pasada N el reviewer solo mira `git diff <ultimo-commit-aprobado>..HEAD`, no la feature entera. Se hizo a mano en F-019 ('lo aprobado hasta acb97ee queda dado por bueno y no se vuelve a mirar') pero no esta escrito en el arnes. Debe indicar en su informe desde que commit revisa.

FUERA DE ALCANCE, DECIDIDO: (a) modelo por rol -el humano quiere Opus 5 siempre, no se toca-; (b) informes por delta en vez de reescritos, que toca el formato de todos los informes; (c) la regla de que toda feature con un numero de aceptacion lo fije en un test antes de implementar -es la que habria evitado los cuatro round trips de F-019-, que es un cambio de metodo y merece escribirse con calma aparte.

ALCANCE: harness/rigor.json, harness/mutacion.py, specs/SPECS.md, .claude/agents/*.md, CHECKPOINTS.md, y el PORTE A arnes-base como 1.6.1 en el mismo trabajo (regla de propagacion: vale para los cinco proyectos). OJO: esto vuelve a cambiar la vara de medir, asi que la entrada de GUIA_INSTALACION.md debe decir que las campanas de nivel estandar pasan a estar muestreadas y sus numeros no son comparables con los anteriores.

(5) ANADIDO EL 2026-08-19 POR EL REVIEWER DE F-034, y es requisito de fondo: HOY NO SE PUEDE MEDIR MUTACION SOBRE FICHEROS DE harness/ EN ESTE REPOSITORIO. `ejecutor_para` manda lo que no cae en ningun servicio a `python -m pytest` SIN RUTA; como la raiz no tiene configuracion de pytest (testpaths, rootdir), esa invocacion recoge services/**/tests y muere en la recoleccion. Hasta la 1.6.0 eso daba un FALSO VERDE silencioso -exit 1 = MUERTO, todos los mutantes 'muertos' sin que ningun test los juzgara-; desde la 1.6.0 la linea base lo detecta y ABORTA, que es mejor pero deja la campana sin poder ejecutarse. Arreglo propuesto: que `ejecutor_para` use `tests` como ruta para los ficheros que no caen en ningun servicio, o dar testpaths a la raiz. Afecta a TODAS las features del repositorio y en particular invalida progress/mutacion_F-012.md (61 mutantes medidos con la invocacion rota), que hay que repetir. Va aqui y no en F-034 porque es infraestructura del arnes, no alcance de aquella feature.

### F-036 · La cantidad de residuos se valora sin la regla de contenedores en unos albaranes sí y en otros no, y los incrementos por LER nunca se emiten

estado **pendiente** · prioridad 4 · rigor `critico` · SDD sí · rama `feature/F-036-residuos-contenedores-e-incrementos`

Defecto MEDIDO el 2026-08-19 sobre los 7 albaranes de SALMEDINA del lote de residuos, con obra y contrato ya seleccionados a mano por el humano y contrastados contra el Excel del administrativo. Evidencia completa en progress/revision_residuos_salmedina_20260819.md. Son DOS defectos que se suman en el mismo importe.

(1) LA REGLA DE CONTENEDORES ES INESTABLE. valuation_builder.py (bloque 4.bis) convierte los m3 del albaran en numero de contenedores, porque la cantidad que trae la linea es la CAPACIDAD del contenedor, no material. Funciona en 5 de los 7 y en 2 no: SS-0003967 y SS-0801977 salen con cantidad_convertida=null y el importe se calcula con la cantidad cruda (6), dando 6 x 120 = 720,00 EUR y 6 x 90 = 540,00 EUR frente a los 210,00 EUR que dice el ground truth en ambos. Es una SOBREVALORACION de x3,4 y x2,6 sin ninguna senal de revision que la delate. Mismo proveedor, mismo contrato (CTSU24/0228), mismo tipo de documento y misma cantidad (6) que los que si funcionan: la diferencia no esta en el dato de entrada. Segun el codigo, converter.convert() solo devuelve None si la cantidad es None, y aqui cantidad_albaran vale 6,0, asi que la rama por la que se cuela no es evidente leyendo el fichero: hay que instrumentar sv6 y reproducirlo.

(2) LOS INCREMENTOS POR LER NO SE EMITEN NUNCA. El contrato tarifa un incremento por codigo LER del residuo (170202 vidrio 120 EUR, 170302 bituminosas 30 EUR, 170604 aislamiento 90 EUR, 170802 yesos 51 EUR) que el administrativo suma SIEMPRE como segunda linea. El pipeline emite una linea por linea de albaran y no genera esa sintetica: SS-0000589 sale 120,00 EUR y debe ser 171,00 EUR (120+51). Las lineas de incremento ESTAN cargadas en contrato_lines, o sea que el dato esta y no se usa.

(3) EFECTO PERVERSO ENTRE AMBOS: en SS-0003967 el matcher eligio como linea principal el propio INCREMENTO LER 170604 (match exact_concept, 90 EUR) en vez del contenedor, porque el codigo LER aparece literal en la descripcion de la linea de incremento y eso gana al match semantico del contenedor. Es decir, el incremento no solo falta: a veces SUSTITUYE a la linea buena.

RESULTADO ACTUAL frente al ground truth (7 albaranes): 3 correctos (SS-0000168 120, SS-0003935 120, SS-0025146 136), 1 corto por falta de incremento (SS-0000589 120 vs 171), 2 disparados (SS-0003967 540 vs 210, SS-0801977 720 vs 210) y 1 con tarifa equivocada (SS-0026122 272 vs 260, que ademas debe valorarse contra OFERTA con la tarifa de contenedor de 9 M3, lo que lo hace caso de F-017).

ALCANCE: services/albaran-valoracion-persist (valuation_builder, calcular_contenedores_residuos, el matcher de linea de contrato). NO ENTRA: la fuente OFERTA (F-017) ni la eleccion de partida (F-021). RECONCILIAR CON F-006 (residuos: pago LLEVAR/RETIRAR y canon) ANTES DE ARRANCAR: hay que decidir si esto es una ampliacion de F-006 o una feature propia. Y ojo con F-024: al extraer unidad_medida, los casos que hoy aciertan por la regla de contenedores pueden pasar a valorar x6.

### F-037 · sv4: al seleccionar un contrato, guardar directamente sin pulsar Guardar

estado **pendiente** · prioridad 5 · rigor `estandar` · SDD sí · rama `feature/F-037-guardado-inmediato-contrato`

Pedido por el humano el 2026-08-19 tras corregir a mano obra y contrato en los 7 albaranes de SALMEDINA: seleccionar el contrato en el desplegable no surte efecto hasta que se pulsa Guardar, y en una sesion de revision de varios documentos eso es un paso de mas por documento, facil de olvidar y que deja el documento aparentemente arreglado pero sin persistir.

PROPUESTA: que la seleccion de contrato persista en el momento (envio inmediato al backend), con senal visual de guardado y manejo del error si falla.

A DECIDIR con el humano antes de implementar: (a) si el guardado inmediato vale solo para el contrato o tambien para obra y proveedor, que sufren el mismo paso; (b) si al guardar el contrato debe dispararse la revaloracion automaticamente o seguir siendo un acto aparte.

RIESGO QUE HAY QUE MIRAR SI O SI: cada guardado del revisor pasa por review_repository::_recalc_valuation_importes, que fue la causa del round trip 2 de F-019 (recalculaba sin descuento y pisaba en BBDD lo que sv6 habia escrito bien). Hoy esta protegido por el guardian de R24, que decide por las ENTRADAS y deja intactas las filas que nadie ha tocado. Guardar automaticamente multiplica la frecuencia con que ese camino se ejecuta, asi que la feature debe traer test que demuestre que N guardados automaticos seguidos no alteran ningun importe que el revisor no haya tocado.

ALCANCE: services/albaranes-front (plantilla del detalle y su endpoint). NO ENTRA: rehacer el formulario de revision ni cambiar el flujo de aprobacion.

### F-024 · La unidad de medida no se extrae: unidad_medida NULL en las líneas base de hormigón y mortero

estado **pendiente** · prioridad 6 · rigor `estandar` · SDD sí · rama `feature/F-024-unidad-medida`

HALLAZGO H-1 (gravedad ALTA) del informe progress/revision_hormigones_20260818.md §5.2: en los 4 albaranes del lote alvaro_17082026 (224964 y 225137 de HORMIGON SIERRA MADRID; 1167 y 1229 de PAZ DEL BARRIO) el campo albaran_lines_merge.unidad_medida sale NULL en las 4 líneas base, con field_scores_json.unidad_medida.status='both_empty_optional' — es decir, ni IA1 ni IA2 la leyeron y el merge lo dio por bueno como campo opcional vacío. Y sin embargo la unidad ESTÁ impresa en los cuatro PDFs («CANTIDAD M³» en Paz del Barrio, «M³» en Sierra Madrid) y los cuatro esperados de IA1 del ground truth piden unidad = M3.

POR QUÉ IMPORTA (no es cosmético): rompe la cadena de unidades de sv6. unidad_categoria queda 'unknown' frente al 'm3' del contrato, UnitCategoryGuard devuelve unit_category_partially_unknown y unidad_category_match=false (services/albaran-valoracion-persist/application/services/unit_category_guard.py:61); con category_match=false el builder salta la conversión (valuation_builder.py:1021-1025) y el importe se salva solo porque cae al fallback importe_using_albaran_quantity_fallback con factor 1. En este lote no duele porque contrato y albarán van ambos en m³: los importes salen bien POR SUERTE. Con un contrato en TN o en kg el importe saldría mal, y el propio UnitConverter documenta un caso real de ese tipo (árido «M 20/40», 29920 sin unidad, 298.302 €). Efecto secundario: cada línea base arrastra motivos de revisión falsos (ver F-025).

FASE QUE FALLA: IA1 (prompt de fase 1 albaran_factura_es, campo unidad_medida definido en services/albaranes-api/config/prompts.yaml:71 como «texto corto tal y como aparece»); IA2 tampoco la repone.

DOS OPCIONES A DECIDIR EN LA SPEC, no excluyentes: (A) LECTURA — en estos formatos la unidad no está en la fila sino en la ETIQUETA DE LA CASILLA / cabecera de columna, que es exactamente el patrón ya implementado y validado para residuos (§10.6 del dominio: «volumen y peso por ETIQUETA de casilla, nunca por magnitud del número», redactado en services/albaranes-api/config/prompts.yaml:356-362). Extender esa lección a los prompts de hormigón/mortero para que la unidad de la cabecera se propague a las líneas. (B) RED DETERMINISTA EN sv6 — para líneas de familia hormigón/mortero sin unidad, asumir la unidad de la línea de contrato dejando rastro con motivo propio, en vez de dejar unidad_categoria='unknown'. La opción A ataca la causa; la B es el cinturón de seguridad.

NO ENTRA: renombrar el motivo no_quantity_in_albaran, que es F-025 (aunque arreglar F-024 haga desaparecer de facto la mayoría de sus casos, la rama que lo produce seguirá existiendo para desacuerdos reales de categoría); ni tocar la conversión entre unidades, que ya existe y funciona (UnitConverter). Toca sv2 (prompts: ruta sensible → el cierre exige evals en verde) y opcionalmente sv6. Fuente: progress/revision_hormigones_20260818.md §5.2 y H-1.

AMPLIACION 2026-08-18 (instruccion del humano, literal): «En este caso la IA2 al revisar deberia darse cuenta de que un camion no puede llevar 30.000 toneladas. Si la cantidad es esa, tiene que ser kg. Debe haber una revision razonada de unidades, para casos tan claros.» La feature pasa a cubrir DOS cosas del mismo prompt y del mismo problema de raiz: (1) que la unidad se EXTRAIGA (la etiqueta de casilla / cabecera de columna, opciones A y B de arriba); y (2) que IA2 haga una REVISION RAZONADA DE UNIDADES cuando la magnitud sea fisicamente implausible para el tipo de material y el medio de transporte. Caso de referencia: albaran 58826 de MAHORSA, 30.380 sin literal de unidad con TARA 12500 impresa en el propio documento; 30.380 toneladas en un camion es imposible, luego son kg. IA2 ya lo tuvo delante y no lo cuestiono: escribio en explicacion_global «peso neto (30380)» reconociendo que es un peso, y aun asi dejo unidad_medida NULL. REQUISITOS DE LA AMPLIACION: el razonamiento debe quedar EXPLICITO Y TRAZABLE —motivo de revision con la reinterpretacion aplicada y su justificacion—, nunca un cambio silencioso del dato; y la reinterpretacion debe apoyarse en lo que el documento imprime (tara, peso bruto, familia de producto), no en una corazonada del modelo. RELACION CON OTRAS FEATURES, sin duplicar ninguna: es DEFENSA EN PROFUNDIDAD, no un sustituto. F-027 (prioridad 2) arregla la red determinista de ultima defensa en sv6 —la de `cantidad_sin_unidad_reinterpretada_kg_a_tn`, que hoy es codigo muerto—, y su spec deja escrito que esa correccion NO sustituye a esta revision de IA2: IA2 detecta arriba, sv6 protege abajo, y que la red de sv6 funcione no legitima que el dato siga llegando mal desde la extraccion. F-032 (semantica de campos) es otra cosa: alli el problema es que un campo significa cosas distintas segun quien lo lea, no que una magnitud sea imposible. Por eso F-024 sube a prioridad 3, justo detras de F-027.

### F-028 · Con dos contratos candidatos no se elige ninguno y el albarán no llega a valorarse

estado **pendiente** · prioridad 7 · rigor `critico` · SDD sí · rama `feature/F-028-selector-contrato-por-partidas`

HALLAZGO H-3 (ALTA) + INSTRUCCIÓN LITERAL DEL HUMANO (2026-08-18): «Pavimarsa tiene 2 contratos: debe elegir uno si puede». QUÉ PASA: los dos albaranes de PAVIMARSA (2026/01/007181 y 2026/01/007378, 521,07 € y 20.111,40 € esperados) **no se valoraron en absoluto**. No falló sv5 ni sv6: nunca se publicó mensaje en `q-valoracion`, porque sv3 solo dispara la valoración si hay contrato seleccionado y no lo había. Log: «[valuation-trigger][pipeline] SKIP: no hay contrato seleccionado» y «[contrato-selector] sin familia detectable en el albaran; no se auto-selecciona». Sigrid devolvió 2 contratos para el par (CIF A28800597, obra 0696): CTSU25/0317 (PED1 Parcela 4, 168 líneas, 40 partidas) y CTSU26/0187 (PED2, 48 líneas, 10 partidas). CAUSA RAÍZ: `elegir_contrato_probable` (contrato_selector.py:79-160) puntúa SOLO por familia de producto y tokens técnicos del texto; si no detecta familia devuelve None. Además `contrato_enrichment_service` NO le pasa el parámetro `tipologia` (la llamada de la línea ~466 solo envía `contratos` y `lineas_albaran`) pese a que el propio docstring del selector la llama «la señal más fuerte». LA SEÑAL DECISIVA ESTÁ EN EL ALBARÁN Y NO SE MIRA: las 7 partidas manuscritas del 007378 y las 2 del 007181 existen TODAS en CTSU25/0317 con la descripción y el precio del ground truth (comprobado en `albaran_contrato_lines_merge`, contrato_id=254), y CTSU26/0187 solo tiene 10 partidas. Un criterio de cobertura de partidas habría acertado sin ambigüedad. PROPUESTA: añadir al selector una señal de PARTIDAS (fracción de las partidas del albarán presentes en el catálogo de cada contrato) con más peso que las familias, y pasarle `tipologia` desde sv2. Si aun así hay empate, mantener el comportamiento actual de no elegir. POR QUÉ ES CRÍTICA: un documento que no se valora es peor que uno que se valora mal, porque no aparece en ninguna pantalla y nadie se entera. Son 20.632,47 € en dos documentos, y los albaranes de acabados (azulejos, carpintería, sanitarios) no tienen familia detectable por palabras, así que esto se repetirá en todo ese bloque de la obra. RELACIÓN: depende de que la partida se lea bien (F-021) pero no la bloquea: aun con lecturas parciales, la cobertura de partidas discrimina. Toca sv3. Fuente: progress/revision_resto_lote_20260818.md (revision de los 7 albaranes restantes del lote alvaro_17082026, 2026-08-18).

### F-029 · Obra resuelta por texto sin detectar empates: score 1,00 a la obra equivocada

estado **pendiente** · prioridad 8 · rigor `critico` · SDD sí · rama `feature/F-029-obra-empates-y-sin-cif`

HALLAZGO H-2 (ALTA) + INSTRUCCIÓN LITERAL DEL HUMANO (2026-08-18): «En Transportes y Grúas está mal elegida la obra y el proveedor; el CIF correcto es B84535764». QUÉ PASA: el albarán 09256 de TRANSPORTES Y GRUAS ANGEL MARTIN (1.129,00 € esperados) **no se valoró**. El papel es un «CONFORME DE SERVICIO»: no lleva número de obra (el campo está en blanco), no lleva CIF y solo dice «Valdebebas». `_match_score` (header_resolver_service.py:57-70) devuelve **1.00 si un texto contiene al otro**, y el bucle de selección (:266-284) usa `if score > best_score`, así que con varias obras empatadas a 1,00 gana la primera del listado y el empate no se registra en ningún sitio. Sigrid tiene al menos `0351 · VIV. PRADO VALDEBEBAS (UTE)` y `0686 · HOTEL CIUDAD AEROPORTUARIA VALDEBEBAS`; el log dice «obra resuelta por texto: codigo=0351 score=1.00» y el ground truth dice **0686**. La obra falsa arrastró todo lo demás: 0 proveedores en la obra 0351 → red de familia omitida → sin contrato → sin valoración. POR QUÉ ES CRÍTICA: la obra manda en toda la cadena (contratos, partidas, imputación). Una obra falsa CON CONFIANZA MÁXIMA es peor que no resolverla: el documento se queda sin contrato y además con un dato incorrecto persistido en `obra_codigo`/`obra_nombre` que el revisor puede dar por bueno. PROPUESTA: (1) detectar empates contando candidatos con `score == best_score`; con más de uno, NO resolver y dejar constancia (`obra_codigo_origen` + `review_note`); (2) sustituir el `contains → 1.00` por una puntuación que premie la cobertura del nombre completo y no la aparición de una sola palabra; (3) caso de prueba: 09256 debe quedar sin obra resuelta y a revisión, con el proveedor B84535764 como valor esperado una vez se resuelva por otra vía. RELACIÓN: el proveedor de este mismo documento lo ataca F-030 (búsqueda aproximada cuando no hay CIF o no casa). Toca sv3. Fuente: progress/revision_resto_lote_20260818.md (revision de los 7 albaranes restantes del lote alvaro_17082026, 2026-08-18).

### F-030 · IA2 busca el proveedor parecido cuando el CIF leído no casa con ninguno de Sigrid

estado **pendiente** · prioridad 9 · rigor `estandar` · SDD sí · rama `feature/F-030-proveedor-cif-aproximado`

INSTRUCCIÓN LITERAL DEL HUMANO (2026-08-18): «En Pavimarsa no ha leído bien el proveedor. Si el CIF no coincide con uno existente, debe buscar uno parecido en IA2». SITUACIÓN ACTUAL Y FRONTERA CON F-002 (importante para no reimplementar lo hecho): F-002 ya resuelve el proveedor por CIF EXACTO contra Sigrid y, cuando no casa, conserva lo leído y deja el motivo `proveedor_cif_no_casa:<cif>` con una nota `[AVISO] Proveedor`. Esta feature es el PASO SIGUIENTE: cuando el CIF extraído no case con ninguno, IA2 debe buscar el proveedor PARECIDO — por CIF aproximado (dígito mal leído, letra confundida, separadores) y por razón social — entre los proveedores con contrato en la obra, y proponerlo con confianza y motivo en vez de dejar el documento sin resolver. CASOS DE REFERENCIA: los dos Pavimarsa del lote (CIF real A28800597) y el 09256 de Transportes y Grúas, que no trae CIF impreso y cuyo proveedor correcto es **B84535764**. CRITERIO DE SEGURIDAD: la propuesta no debe pisar en silencio lo leído. Si la confianza no supera el umbral, el documento va a revisión con los candidatos listados, igual que hace F-002 con el aviso. RELACIÓN: F-029 arregla la obra del mismo documento; F-021 y F-028 usan el proveedor ya resuelto para llegar al contrato. Toca sv2 (prompt e IA2) y sv3. Fuente: progress/revision_resto_lote_20260818.md (revision de los 7 albaranes restantes del lote alvaro_17082026, 2026-08-18).

### F-031 · La partida del albarán no se usa para elegir la línea de contrato cuando la descripción no coincide

estado **pendiente** · prioridad 10 · rigor `estandar` · SDD sí · rama `feature/F-031-partida-elige-linea-contrato`

HALLAZGO H-4 (ALTA). El prompt de IA3 dice explícitamente «NO decides partida: solo casas producto y precio», y `PartidaMatcher` (partida_matcher.py:118-153) solo re-apunta a la partida del albarán si encuentra LA MISMA DESCRIPCIÓN dentro de ella; si no, crea una línea derivada con el precio de la que eligió IA3. Resultado en el 58826: IA3 casó el árido a 15,43 €/TN cuando la partida manuscrita apuntaba a la línea de contrato correcta, a 12,87. Es decir, el error de partida AQUÍ SÍ CUESTA DINERO, no es solo imputación contable. PROPUESTA: usar la partida leída como señal de primer orden para elegir la línea de contrato dentro de esa partida aunque la descripción no sea idéntica (mismo producto, redacción distinta), antes de derivar una línea nueva. RELACIÓN: F-021 valida que la partida leída existe; F-026 impide escribir derivadas con partidas inexistentes; ESTA usa la partida válida para acertar el precio. Las tres se tocan: al implementarlas, reconciliar. Toca sv5 y sv6. Fuente: progress/revision_resto_lote_20260818.md (revision de los 7 albaranes restantes del lote alvaro_17082026, 2026-08-18).

### F-032 · precio_neto no tiene semántica única y genera line_net_mismatch masivo

estado **pendiente** · prioridad 11 · rigor `estandar` · SDD sí · rama `feature/F-032-semantica-precio-neto`

HALLAZGO H-5 (MEDIA). El mismo IA1, con el mismo prompt, rellenó `precio_neto` con el IMPORTE en el albarán 2026/01/007181 (341,67 y 179,40) y con el PRECIO UNITARIO en el 007378 (14,38 en las seis primeras líneas). El validador de sv3 (albaran_confidence_service.py:377-382) marca `line_net_mismatch` y resta 12 puntos por línea: el 007378 acumula 8 marcas y baja a 67,69 de confianza, la más baja del lote, por un problema de DEFINICIÓN y no de lectura (sus cantidades y precios son todos correctos). PROPUESTA: fijar la semántica en el esquema y en el prompt de forma explícita y con ejemplo — o `precio_neto` = unitario neto tras descuento y el importe a su propio campo, o al revés, pero una sola. Barato y limpia mucho ruido de la pantalla de revisión. RELACIÓN DIRECTA CON F-019: el defecto del importe ×cantidad nació de esta misma ambigüedad (el prompt define `precio_neto` como importe de línea y el SELECT de sv5 lo trataba como unitario). F-019 alineó a los consumidores; esta feature elimina la ambigüedad en el origen para que no vuelva. Ver también F-003 R1/R2, que ya especifica un campo con nombre no ambiguo en IA1: reconciliar antes de implementar. Toca sv2 y sv3. Fuente: progress/revision_resto_lote_20260818.md (revision de los 7 albaranes restantes del lote alvaro_17082026, 2026-08-18).

### F-033 · El contrato llega a sv5 en Markdown o en PDF según el documento, sin criterio determinista

estado **pendiente** · prioridad 12 · rigor `estandar` · SDD sí · rama `feature/F-033-contrato-md-o-pdf-determinista`

HALLAZGO H-6 (BAJA). El albarán 58826 recibió el contrato CTSU25/0085 como MARKDOWN (18.005 caracteres, `attachment.kind='text_only'`) y el 58878, 23 segundos después, el MISMO contrato como PDF de 676 KB. El motivo es que `albaran_contratos_merge.md_sharepoint_relative_path` está relleno en la fila 251 y vacío en la 252. Log de sv5: «[pipeline] contrato -> MD (18005 chars); no se adjunta PDF» frente a «pdf=yes». POR QUÉ IMPORTA: dos ejecuciones del mismo caso dejan de ser comparables, lo que inutiliza el banco de pruebas de modelos (§10.9 del documento de dominio pide «mismos docs, 2 pasadas por doc»). También cambia el coste: 39.969 tokens de entrada con MD frente a 51.700 con PDF. PROPUESTA: hacer determinista la elección (siempre MD si existe) y garantizar que el MD se genera ANTES de disparar la valoración, igual que ya se hace con el PDF en el «Paso 9 — GARANTÍA de PDF» de `contrato_enrichment_service`. RELACIÓN: afecta a F-011 (evals), que necesita ejecuciones reproducibles para que la puerta tenga sentido. Toca sv3 y sv5. Fuente: progress/revision_resto_lote_20260818.md (revision de los 7 albaranes restantes del lote alvaro_17082026, 2026-08-18).

### F-023 · Mortero: las sintéticas de contrato no se emiten porque IA3 y sv6 las vetan por tipo_familia

estado **pendiente** · prioridad 13 · rigor `critico` · SDD sí · rama `feature/F-023-mortero-incrementos`

HALLAZGO (revisión del lote alvaro_17082026, informe progress/revision_hormigones_20260818.md §4.4.b, H del §7 fila 2): el albarán 1229 de FABRICACION DE HORMIGONES PAZ DEL BARRIO (MORTERO M-7,5/B/04 48H, 3 m³, contrato CTSU25/0001, fecha 2026-06-09) valoró 210,00 € frente a los 307,50 € del administrativo. De esos −97,50 €, esta feature ataca los que dependen de las sintéticas de contrato: falta la línea INCREM. PRECIO 2026 (3 × 9,00 = 27,00 €) y falta la línea CARGAS INCOMPLETAS (3 × 20,00 = 60,00 €). No es que la tarifa no exista: el contrato tarifa «INCREMENTO PRECIO MORTERO 2026» a 9,00 €/m³ en la partida P4.39.03 (línea de contrato 25921) y «INCREM. AÑO 2026» a 9,00 €/m³ en P4.99.10. Es que no se busca.

CAUSA RAÍZ — DOS VETOS ENCADENADOS POR tipo_familia. (1) PROMPT DE IA3: el Paso 7 («LÍNEAS SINTÉTICAS DE MODIFICADORES (hormigón)») dice literalmente «Se aplica SOLO cuando la línea base tiene tipo_familia='hormigon'» — services/albaran-valoracion-api/config/prompts.yaml:303-305, clave valuation_es, que es el fichero que el servicio carga de verdad (config/settings.py:214-215). OJO: la copia services/albaran-valoracion-api/config/prompts/svc5_prompt_valuation_es.yaml:304-306 dice lo mismo pero está DESACTUALIZADA (631 líneas, sin bloque M7) y NO se carga; el informe la citaba a ella. Con contexto_linea.tipo_familia='mortero' —que IA2 sí puso bien, prompt albaran_revision_fase2_mortero de services/albaranes-api/config/prompts.yaml:633— IA3 devolvió UNA sola línea y ninguna sintética. (2) RED DETERMINISTA DE RESPALDO DE sv6, con el mismo veto: `if ctx is None or getattr(ctx, "tipo_familia", None) != "hormigon": continue` en _sinteticas_m1_faltantes (services/albaran-valoracion-persist/application/services/valuation_builder.py:602) e idéntico en _sinteticas_codigo_faltantes (:686). Por eso NO basta con tocar el prompt: si solo se levanta el veto de IA3, la red determinista lo sigue bloqueando.

INSTRUCCIÓN LITERAL DEL HUMANO (2026-08-18): «en el prompt particular de mortero hay que añadir los incrementos anuales igual que en hormigón, copiando y pegando el bloque correspondiente».

QUÉ COPIAR Y DÓNDE PEGARLO (localizado para que quien implemente no tenga que buscarlo). ORIGEN: el bloque «==== M1 - INCREMENTOS POR AÑO ====» completo, sub-reglas M1.1 a M1.6, en services/albaran-valoracion-api/config/prompts.yaml líneas 454-535 (termina justo antes de «==== M2 - CONSISTENCIA DEL HORMIGÓN ====», que empieza en :536), dentro de la clave valuation_es. DESTINO: una clave NUEVA `valuation_mortero` en ese mismo fichero, siguiendo el patrón del prompt por tipología que ya existe, `valuation_residuos` (prompts.yaml:1008). Adaptaciones mínimas al pegar: en M1.5, descripcion_linea = «INCREMENTO POR AÑO {año} EN MORTERO» en vez de «EN HORMIGÓN»; el resto de M1 va tal cual (el año del contrato se deduce igual del prefijo CTSU{AA}).

TRAMPA IMPORTANTE — CREAR LA CLAVE NO BASTA. El selector de prompt por tipología de sv5 (services/albaran-valoracion-api/application/services/valuation_extraction_service.py:205-210: monta `valuation_{tipologia}` y usa esa clave si existe) llama a _derivar_tipologia_valoracion (:316-333), que SOLO devuelve 'residuos' | 'hormigon' | 'generico'. Con tipo_familia='mortero' devuelve 'generico', busca `valuation_generico` (que tampoco existe) y cae a valuation_es. Verificado en BBDD: albaran_valuations.prompt_key='valuation_es' para el 1229. Hay que añadir 'mortero' a esa derivación o el prompt nuevo no se usará nunca.

ALCANCE: (1) clave `valuation_mortero` en sv5 con el bloque M1 copiado, más el veto de familia de §10.3 del dominio (solo arena: prohibidas sintéticas de árido, aditivo, plastificante, fibras y fratasado; el tercer campo del código D-*/M-* es resistencia, no árido); (2) 'mortero' reconocida por _derivar_tipologia_valoracion; (3) levantar el veto gemelo de sv6 en valuation_builder.py:602 y :686 para que la red determinista de respaldo también emita M1 en mortero; (4) evals: la feature toca rutas sensibles (prompts + redes deterministas), así que el cierre exige evals en verde además de los tests (F-011).

NO ENTRA: el precio de la línea base del 1229 (70,00 € de la hermana MORTERO M-5 del contrato en vez de los 73,50 € de la OFERTA, −10,50 €), que es F-017 (el comparativo como fuente de precio 1c); ni que IA2 genere siempre la línea de carga incompleta, que es F-018. Relación con las vecinas: los 27,00 € del incremento de año los recupera F-023 sola; los 60,00 € de carga incompleta necesitan además F-018 (que se emita la línea) y F-017 (el precio, porque CTSU25/0001 no tarifa carga incompleta en sus 62 líneas), pero este veto es prerrequisito de ambas: mientras esté, en mortero no sale NINGUNA sintética. Solapa con F-004 (tanda 3, spec_ready): su R24 («incrementos por año también en mortero») y sus R9/R10 (prompt valuation_mortero) quedan ABSORBIDOS aquí; al arrancar F-004 hay que reconciliar su spec para no implementarlo dos veces.

VERIFICACIÓN ESPERADA AL CERRAR: revalorar el 1229 en local y ver la línea INCREMENTO POR AÑO 2026 EN MORTERO con 3 × 9,00 = 27,00 €, y albaran_valuations.prompt_key='valuation_mortero'. Toca sv5 y sv6. Fuente: progress/revision_hormigones_20260818.md.

### F-015 · Líneas tachadas del albarán: no se registran

estado **pendiente** · prioridad 14 · rigor `estandar` · SDD sí · rama `feature/F-015-lineas-tachadas`

Caso real (Feymaco 2137569, lote alvaro_17082026): una línea impresa TACHADA a mano (anulada) que el administrativo correctamente excluye. Hoy la extracción no distingue tachaduras. Comportamiento a especificar: IA1/IA2 detectan la línea anulada y no la emiten (o la emiten marcada como anulada y la persistencia la excluye con rastro); ante duda, a revisión — nunca valorarla como buena. Toca prompts de sv2 (rutas sensibles => evals) y posiblemente redes de sv3. Marcada por el humano como de bastante prioridad (2026-08-17).

### F-021 · Partida: validación contra el catálogo del contrato y elección asistida entre candidatas

estado **pendiente** · prioridad 15 · rigor `estandar` · SDD sí · rama `feature/F-021-partida-catalogo-candidatas`

Origen: prueba local del 2026-08-18 con el albarán Feymaco 2.137.569. El código de imputación manuscrito «P4/P5.36.01» se leyó primero como «PJ.36.01» y, tras F-019, como «36.01» a secas: la IA se comió el prefijo. Hoy NADIE valida que el código leído exista, así que una imputación contable inventada entra sin un solo aviso. ALCANCE EN TRES PASOS, en este orden (decisión del humano, 2026-08-18): (1) VALIDACIÓN DETERMINISTA, sin IA: comprobar el código leído contra el catálogo de partidas del contrato, que YA viaja en el contexto de sv6 a sv5 (albaran_contrato_lines_merge.codigo_partida). Comprobado en el contrato CTSU24/0454: 3 prefijos de primer nivel (P5 con 218 líneas, P4 con 188, CI con 36) y las partidas P4.36.01 y P5.36.01 EXISTEN, así que con el «36.01» leído a medias el catálogo devuelve solos los dos candidatos correctos, sin salir a ningún sistema externo. Casar por sufijo y por prefijo, no solo por igualdad. (2) ELECCIÓN ASISTIDA: solo si el código no valida y hay más de un candidato, la IA elige POR DESCRIPCIÓN entre los candidatos del catálogo, devolviendo confianza y motivo. La IA no decide en silencio: una imputación contable equivocada es un asiento mal hecho. (3) POR DEBAJO DEL UMBRAL DE CONFIANZA, la línea va al selector de candidatas de sv4, que ya especifica F-007: esta feature se apoya en aquella, no la duplica. AMPLIACIÓN FUTURA (fuera de alcance aquí): cuando el código no aparezca en el contrato, consultar las partidas de la obra en Sigrid vía sigrid-api (solo lectura); el documento de sigrid-api menciona el desglose por partidas pero no consta expuesto como endpoint. NO ENTRA: la lectura del separador «/» como reparto en varias partidas, que es F-016, ni el reparto en sí. Relación con otras features: F-016 (multipartida) depende de que el código se lea y valide bien; F-007 aporta el selector humano. Toca sv5 y sv6, con verificación en sv4. Detalle del incidente en progress/prueba_local_feymaco_20260818.md.

### F-016 · Reparto de una línea del albarán entre varias partidas

estado **pendiente** · prioridad 16 · rigor `estandar` · SDD sí · rama `feature/F-016-linea-multipartida`

Caso real (Feymaco 2137569): una línea impresa de 108 uds repartida a mano entre dos partidas (54 a P4.36.01 y 54 a P5.36.01, anotación 'P4/P5.36.01'). El pipeline actual modela una línea -> una partida. La spec debe decidir el modelo: ¿la valoración soporta líneas hijas con cantidades parciales por partida, o el reparto es una acción manual del revisor en sv4 (split de línea) previa al registro? Impacto potencial en schema (listar lectores: sv5 SQL crudo) y en el futuro registro en Sigrid (F-013).

### F-026 · Guard de partida de la línea BASE antes de escribir en contrato_lines_derived

estado **pendiente** · prioridad 17 · rigor `estandar` · SDD sí · rama `feature/F-026-guard-partida-base`

HALLAZGO H-3 (gravedad MEDIA) del informe progress/revision_hormigones_20260818.md §5.1 y §7 fila 5, MEDIDO en la BBDD local: en los 4 albaranes del lote alvaro_17082026 el código de partida manuscrito se leyó mal 4 veces de 4 (P5.03.04 → «03.04»; P5.03.09 → «PT.03.09»; P4.03.05 → «04.03.05»; P4.14.01.02.02 → «15.01.02.02»), y ninguno de los cuatro literales leídos existe en el catálogo de partidas del contrato (0 filas en albaran_contrato_lines_merge), mientras que los cuatro reales sí existen. CONSECUENCIA MEDIDA: sv6 no encuentra la partida, marca partida_action='new_line_created' y CREA 13 LÍNEAS en contrato_lines_derived (ids 389-403, origen='missing_partida') con literales de partida inexistentes en el catálogo, en vez de apuntar a la línea de contrato real, que existía y tenía el mismo precio. Es contaminación PERSISTENTE de una tabla de referencia, no un dato erróneo de una valoración concreta.

DÓNDE FALTA EL GUARD: services/albaran-valoracion-persist/application/services/partida_matcher.py. En la rama (c) del caso principal (:139-152, reasons=['ia_match_partida_missing_derived']) y en el camino sin match de la IA (:162, origen='no_ia_match') se construye la línea derivada con codigo_partida_final=partida_norm SIN comprobar antes que ese literal exista en contrato_lines[].codigo_partida. Las sintéticas heredan después esa misma partida (_partida_para_sintetica, :198-232, partida_action='inherited_from_base_line').

ALCANCE: guard determinista ANTES de derivar — si el codigo_partida de la línea BASE no existe en el catálogo de partidas del contrato, no se escribe línea en contrato_lines_derived con ese literal: se deja la partida sin fijar (o se conserva el match de la IA) y la línea se marca para revisión con un motivo propio. Incluye test que fije que contrato_lines_derived nunca recibe un literal fuera del catálogo.

FRONTERA CON LAS VECINAS (explícita, para que no se solapen). F-021 arregla la LECTURA: valida el código leído contra el catálogo del contrato y, cuando no valida, propone candidatas y deja elegir (IA por descripción, o el humano en el selector de sv4 que aporta F-007). F-026 es el ÚLTIMO CORTAFUEGOS aguas abajo: aunque la lectura siga siendo mala, o F-021 no resuelva el caso, o alguien reintroduzca el defecto, la ESCRITURA en contrato_lines_derived no se produce con un literal inválido. Y F-004 R7 veta la partida inexistente DE LAS SINTÉTICAS: no salta aquí porque la partida inválida está en la BASE y las sintéticas la heredan legítimamente — F-026 tapa ese hueco. Si F-021 se implementa antes, esta feature sigue teniendo sentido, pero su spec debe REUTILIZAR el validador contra el catálogo que aquella construya, no duplicarlo.

NO ENTRA: mejorar la lectura del código manuscrito ni la elección asistida entre candidatas (F-021); el reparto de una línea entre varias partidas por el separador «/» (F-016); el selector humano de candidatas (F-007). Toca solo sv6. Fuente: progress/revision_hormigones_20260818.md §5.1, §7 fila 5 y H-3.

### F-025 · El motivo no_quantity_in_albaran es una falsa alarma sistemática cuando se omite la conversión de unidad

estado **pendiente** · prioridad 18 · rigor `estandar` · SDD sí · rama `feature/F-025-motivo-conversion-omitida`

HALLAZGO H-2 (gravedad MEDIA) del informe progress/revision_hormigones_20260818.md §5.2 punto 2: las 4 líneas base del lote alvaro_17082026 (albaranes 224964, 225137, 1167 y 1229) llevan el motivo de revisión `no_quantity_in_albaran` TENIENDO cantidad — 4, 9, 8 y 3 m³ respectivamente, correctamente leída y persistida en albaran_line_valuations.cantidad_albaran. El motivo miente en el 100 % de las líneas del lote.

CAUSA RAÍZ: ValuationBuilder llama al conversor con cantidad=None A PROPÓSITO cuando unidad_category_match es falso — rama else de services/albaran-valoracion-persist/application/services/valuation_builder.py:1021-1025 — y UnitConverter.convert devuelve reasons=["no_quantity_in_albaran"] para cantidad None (services/albaran-valoracion-persist/application/services/unit_converter.py:64-70). O sea: el motivo describe el ARGUMENTO que le pasó el builder, no el documento que se leyó.

POR QUÉ IMPORTA: es información falsa en la pantalla del revisor. Con todas las líneas marcadas así, el revisor aprende a ignorar el motivo, que es justo lo contrario de lo que un motivo de revisión debe conseguir.

CAMBIO PROPUESTO (pequeño y de bajo riesgo): motivo propio para «conversión omitida por desacuerdo de categoría de unidad», del tipo `conversion_skipped_unit_category_mismatch`, emitido en esa rama else del builder (o por el conversor mediante un parámetro explícito que distinga «no hay cantidad» de «no convertimos a propósito»), dejando `no_quantity_in_albaran` reservado para cantidad realmente ausente. Antes de cambiar el string hay que listar quién lo consume (motivos de revisión de sv6 y su pintado en sv4) y fijar el comportamiento con un test.

NO ENTRA: la causa de fondo, que es que unidad_medida no se extrae (F-024). Las dos features son independientes y ninguna hace innecesaria a la otra: F-024 elimina la mayoría de los casos de este lote, pero la rama de conversión omitida seguirá existiendo para desacuerdos REALES de categoría (albarán en m³ contra contrato en TN), y entonces el motivo seguirá siendo falso. Tampoco entra tocar UnitCategoryGuard (unit_category_guard.py:61), que se comporta correctamente. Toca solo sv6, con verificación de los lectores en sv4. Fuente: progress/revision_hormigones_20260818.md §5.2 y H-2.

### F-020 · El pipeline es agnóstico al proveedor de IA: ninguna fase privilegia a OpenAI

estado **pendiente** · prioridad 19 · rigor `estandar` · SDD sí · rama `feature/F-020-proveedor-agnostico`

Hoy sv3 tiene los proveedores cableados por nombre: el contrato ExtractionEnvelope (services/albaranes-persistencia/domain/models/extraction_models.py:73) es «el envelope de OpenAI» + campos opcionales gemini y claude, así que quien venga en el envelope principal se registra como openai (prueba del 2026-08-18: provider_origin='openai' con model_name='gemini-3.7-flash'); el scoring premia la marca (openai_only 76 frente a gemini_only/claude_only 66, en albaran_confidence_service.py:81-83); y los topes y motivos la nombran (openai_fallback -> cap 84 % + single_provider_openai; line_only_in_openai:N). Consecuencia medida: una ejecución correcta con «FASE 1=gemini . FASE 2=gemini» queda capada al 84 %, por debajo del umbral de 80, y todo va a revisión con motivos que no describen lo ocurrido. ALCANCE (decisiones del humano, 2026-08-18): (1) sv2 declara en el meta del envelope 'provider', 'providers_used' y 'providers_expected' (application/services/phase_merge.py y application/pipelines/extract_albaran_pipeline.py); (2) el contrato pasa de «openai + gemini? + claude?» a «fuente principal + lista de fuentes adicionales», cada una con su provider, aceptando el formato antiguo para no romper mensajes en vuelo ni envelopes ya guardados; (3) sv3 puntúa por número de fuentes y no por marca: openai_only/gemini_only/claude_only se funden en un único 'single_source' con el MISMO valor para todos (76); (4) provider_origin guarda el valor real (gemini, gemini+openai...) en vez de openai_fallback; (5) SE ELIMINA el tope por número de fuentes y el motivo single_provider_openai: con una sola fuente la confianza sale del acuerdo entre campos, no de un castigo fijo. En su lugar, 'provider_missing:<esperado>' salta SOLO si providers_used < providers_expected (fallo real de un proveedor); (6) line_only_in_openai:N pasa a line_single_source:N. Los demás topes (conflicto en campo crítico, campo requerido ausente, líneas sin casar) NO cambian: penalizan hechos, no marcas. NO ENTRA: rehacer el algoritmo de merge multi-IA (se conserva primaria/secundaria/terciaria, solo cambia quién ocupa cada puesto) ni decidir si se vuelve a llamar a varios proveedores en fase 1 (es configuración). RIESGOS: no existe NINGÚN test que fije estos strings (comprobado), así que la red de seguridad se construye en la feature; los documentos ya persistidos se quedan con provider_origin='openai' y no se reescribe histórico; verificar el selector de vistas por proveedor de sv4 (infrastructure/database/review_repository.py). Toca sv2 y sv3, con verificación en sv4.

### F-003 · Tanda 2 — Albaranes valorados, match estricto y coherencia (G3+G4+G5)

estado **spec lista** · prioridad 20 · rigor `estandar` · SDD sí · rama `feature/F-003-valorados-match-estricto`

Albaranes que VIENEN valorados: transcribir, no recomponer (precio, TODOS los descuentos e importe se copian tal cual por su etiqueta de columna; prohibido derivar precio=importe×algo — caso ×120). El dto del albarán no se aplica sobre el precio de contrato. Guard aritmético: precio×cantidad(−dtos)≈importe leído y Σimportes=total albarán; si no cuadra => revisión, nunca inventar. Matching estricto: atributo sustantivo distinto (tamaño, modelo, tipo) => NO casar; mejor línea nueva sin precio a revisión (casos CETOSA, elemento base 0,5 mm, bolsa de cuñas). Toca sv5 (prompts) y sv6 (redes deterministas).

### F-014 · Conversor del formato plano del administrativo a fixtures de evals

estado **pendiente** · prioridad 21 · rigor `estandar` · SDD sí · rama `feature/F-014-conversor-administrativo`

El ground truth real lo produce el administrativo como xlsx PLANO (una fila por línea final, 19 columnas — lote de referencia: alvaro_17082026) + carpeta de PDFs con convención <proveedor>_<codigoAlbaran>.pdf (símbolos prohibidos de Windows eliminados del código, p.ej. 2026/01/007181 -> 202601007181). Ese formato pasa a ser el OFICIAL del libro maestro: el conversor de evals debe ingerirlo y generar los fixtures E2E + derivar automáticamente los esperados de IA1 (cabecera + líneas EN ALBARAN, con precio/importe solo cuando su fuente es ALBARAN) e IA2 (tipología mapeada) dejando '?' donde no sea derivable. Normalizaciones: obra a 4 dígitos (Excel pierde ceros: 696 -> 0696), descuento en fracción = porcentaje (0.4 = 40%), prefijos de partida SOLO CI/CD/CP (corrige lecturas tipo C1 -> CI), mapeo de tipos del administrativo (FERRETERIA/MATERIALES/GRAVA -> genérico-suministros; HORMIGON; MORTERO; CAMION GRUA -> decidir en spec). Barrido C3-bis antes de versionar fixtures. Con fixtures reales, valorar subir la puerta de rutas sensibles a bloqueo.

### F-018 · Carga incompleta: línea siempre generada por IA2 y cantidad fijada por IA3 con mínimo por defecto 6 m³

estado **pendiente** · prioridad 22 · rigor `estandar` · SDD sí · rama `feature/F-018-carga-incompleta`

Regla del humano (2026-08-18) que revisa el comportamiento actual de M7. HOY (prompt valuation_es de sv5, bloque M7): la línea de carga incompleta la emite IA3, SOLO si el contrato tarifa carga incompleta y SOLO ante señal (texto o cantidad < umbral), con umbral leído del PDF del contrato y sin default. REGLA NUEVA: (1) IA2 genera SIEMPRE la línea CARGA INCOMPLETA en hormigón/mortero como deducción de documento (conoce los m³ vertidos), aunque la cantidad final resulte 0; (2) IA3 fija la cantidad final contra el contrato: mínimo del contrato − m³ vertidos, con MÍNIMO POR DEFECTO 6 m³ si el contrato no lo indica; si vertidos ≥ mínimo → cantidad 0; (3) precio: el del contrato si lo tarifa; si no, a revisión (F-017 comparativo cuando exista). Caso de referencia: HSM 224964 (4 m³ → 2 m³ de carga incompleta). ATENCIÓN: F-004 (spec_ready) dice «M6/M7 solo con señal explícita»: esta feature la CONTRADICE y prevalece; al arrancar F-004 hay que reconciliar su R de M7 con esta regla. Toca sv2 (IA2, futura deducción por categoría), sv5 (prompt M7) y sv6 (builder/redes).

### F-004 · Tanda 3 — Hormigón fino y veto de mortero

estado **spec lista** · prioridad 23 · rigor `estandar` · SDD sí · rama `feature/F-004-hormigon-fino`

Re-apuntado determinista de incrementos al recurso del contrato en la partida de la línea base (solo derivar si de verdad no existe). Familia mortero (códigos D-*) separada del hormigón con veto determinista: solo arena; prohibidas sintéticas de árido, aditivo, plastificante, fibras y fratasado; el tercer campo del código es resistencia, no árido. M6/M7 (exceso de tiempo, carga incompleta) solo con señal explícita en el documento. La partida de un incremento debe existir en el contrato (o ALM/None), jamás un literal nuevo. Toca sv5 (prompts/schema) y sv6 (builder y redes).

### F-005 · Tanda 4a — Tipología bombeo

estado **spec lista** · prioridad 24 · rigor `estandar` · SDD sí · rama `feature/F-005-bombeo`

Valoración por rendimiento mínimo contractual (caso PUMPING TEAM): m³ a facturar = horas de bombeo × rendimiento mínimo del contrato (caso real: 10,5 h × 20 m³/h = 210 m³ aunque se bombeara menos). La línea de horas NO se factura aparte (embebida en el mínimo); el desplazamiento sí. Requiere prompt de familia nuevo y leer el rendimiento del contrato. Toca sv2 (contexto_linea), sv5 (prompt) y sv6 (reglas).

### F-006 · Tanda 4b — Residuos: lógica de pago LLEVAR/RETIRAR y canon

estado **spec lista** · prioridad 25 · rigor `estandar` · SDD sí · rama `feature/F-006-residuos-pago`

Solo LLEVAR => no se paga y no entra en Sigrid. RETIRAR => se paga el porte + línea de CANON DE VERTEDERO obligatoria. Ambos en el mismo albarán => solo cuenta RETIRAR. Partida del recurso del contrato, jamás inventada (caso 16.01 vs 15.01). La lectura (LER, volumen/peso por etiqueta, llevadas/retiradas separadas, cálculo de contenedores) ya está entregada; esta feature es solo la lógica de pago. Toca sv5 (prompt) y sv6 (reglas).

### F-007 · Tanda 5 — Partida ALM por defecto y selector de candidatas en sv4

estado **spec lista** · prioridad 26 · rigor `estandar` · SDD sí · rama `feature/F-007-partida-alm-selector`

Suministros NO se destinan: partida ALM (almacén) con imputación parcial mensual; indirectos SÍ se destinan a la entrada. Cuando el mismo recurso existe en varias partidas (contratos de hormigón con clones), la elección es humana: selector de partidas candidatas en sv4 + memoria por obra+producto para prerrellenar (la información de a qué tajo va el camión no está en el documento). Toca sv6 (regla ALM) y sv4 (selector + memoria).

### F-017 · El comparativo como fuente de precio (1c) en la valoración

estado **pendiente** · prioridad 27 · rigor `estandar` · SDD sí · rama `feature/F-017-comparativo-precio`

Decisión del humano (2026-08-17) que resuelve el 'OFERTA' del ground truth: el administrativo obtiene el precio unitario/importe por este orden: (1) líneas iguales ya registradas en líneas de contrato [hoy 1a], (2) contrato en papel [hoy 1b], (3) como ÚLTIMO recurso, el precio del COMPARATIVO asociado al contrato [nuevo, 1c]. Hay que añadir esa tercera fuente: la spec debe estudiar de dónde sale el comparativo (¿Sigrid vía sigrid-api? ¿documento en SharePoint?), cómo se asocia al contrato, y ampliar precio_source en sv5/sv6 (y el modelo de conciliación 1a-vs-1b) sin romper lectores. Las 3 líneas OFERTA del lote alvaro_17082026 son los casos de referencia.

### F-013 · Registro del albarán aprobado en Sigrid (consumidor de q-feedback)

estado **pendiente** · prioridad 28 · rigor `critico` · SDD sí · rama `feature/F-013-registro-sigrid`

Marcada como MUY IMPORTANTE por el humano (2026-08-13). Servicio nuevo del monorepo (la responsabilidad no cabe en ninguno existente; q-feedback está reservada para esto desde el diseño): consume q-feedback y da de alta el albarán valorado y aprobado en Sigrid vía sigrid-api sql/write (única base escribible: ruesma; el guard semántico de sigrid-api existe y la escritura está off por defecto). Excluye las líneas marcadas no_registrar_sigrid (F-006). Diseño pendiente y delicado: qué tablas de Sigrid, MAX(ide)+1 con lock, idempotencia del alta (un albarán aprobado dos veces no puede duplicarse en el ERP), y autorización expresa del humano para activar la escritura. Escribe en el ERP de producción => rigor critico y verificaciones MANUAL obligatorias.

### F-008 · Lifecycle de blobs de hand-off

estado **pendiente** · prioridad 29 · rigor `estandar` · SDD no · rama `feature/F-008-blob-lifecycle`

Los workers no borran input/ ni envelopes/ (semántica at-least-once); la limpieza es una lifecycle policy del storage que está escrita (infra/blob_lifecycle.ps1) pero sin ejecutar. Aplicarla (14 días) y verificar que queda activa.

### F-009 · Limpieza de la cola huérfana q-emails

estado **pendiente** · prioridad 30 · rigor `estandar` · SDD no · rama `feature/F-009-limpieza-q-emails`

q-emails es un resto del diseño original (intake partido en receptor+worker, colapsado en sv1): nadie la publica ni consume. Retirarla de la lista canónica de ruesma_comun.colas. Antes: grep en infra/ por si algún script la crea o referencia (create_capps, scale rules, fase1), y decisión del humano sobre borrarla del storage o dejarla morir.

### F-010 · Easy Auth en el portal sv4

estado **pendiente** · prioridad 31 · rigor `critico` · SDD sí · rama `feature/F-010-easy-auth-sv4`

sv4 es el único ingress externo y está sin autenticación (pendiente desde el despliegue). Configurar Easy Auth con Entra ID: app registration, redirect URIs, y verificación con usuarios reales del portal. Delicada: afecta a los usuarios y a las redirect URIs de Entra; verificación manual obligatoria.

### F-022 · Bandeja de portada: el concepto de las líneas del albarán sale vacío porque el JOIN de la línea derivada apunta a la tabla equivocada

estado **pendiente** · prioridad 32 · rigor `estandar` · SDD sí · rama `feature/F-022-concepto-lineas-bandeja`

SÍNTOMA (reportado por el humano, prueba local del 2026-08-18): en la BANDEJA DE PORTADA del portal de revisión (sv4), la columna «Líneas valoradas» pinta «—» en lugar de la descripción del material en las líneas que vienen del albarán; solo se ve texto en las líneas sintéticas. Reproducido con los albaranes de Feymaco (ferretería) 2.137.569 (5 líneas) y 2.139.643 (1 línea).

QUÉ VISTA ES Y DE QUÉ CAMPO TIRA. La portada es GET /documents (services/albaranes-front/interface_adapters/web/app.py:573-655) → plantilla services/albaranes-front/templates/documents_list.html, columna «Líneas valoradas» (cabecera en :107, celda en :260-273). Cada línea se pinta con `ln.concepto or '—'` (documents_list.html:265). El modelo es DocumentLineSummary (services/albaranes-front/domain/models/review_models.py:87-97) y lo rellena la consulta de líneas salmón dentro de list_documents (services/albaranes-front/infrastructure/database/review_repository.py:348-405; def en :226). Ahí, `concepto` se resuelve con COALESCE(NULLIF(lv.descripcion_linea,''), mcl.descripcion_linea, dcl.descripcion_linea) (review_repository.py:364-366) sobre dos LEFT JOIN (:375-378).

CAUSA RAÍZ (confirmada): el LEFT JOIN de la línea DERIVADA apunta a la TABLA EQUIVOCADA. En review_repository.py:377-378 se hace «LEFT JOIN albaran_contrato_lines_merge dcl ON dcl.id = lv.derived_contrato_line_id», pero las líneas de contrato derivadas viven en la tabla `contrato_lines_derived` (docs/ARCHITECTURE.md:92; y el propio front lo hace BIEN en el detalle: _fetch_derived_lines_in_session, review_repository.py:1321-1350, que además documenta que el esquema de esa tabla es distinto). Como `derived_contrato_line_id` es un id de otra secuencia, el join no casa nunca, el COALESCE se queda sin candidatos y la plantilla pinta «—».

POR QUÉ SOLO FALLA EN LAS from_albaran. `albaran_line_valuations.descripcion_linea` está a NULL POR DISEÑO en las líneas leídas del albarán: sv6 la fija explícitamente a None en la rama from_albaran (services/albaran-valoracion-persist/application/services/valuation_builder.py:1189) y sí la rellena en las sintéticas (:1528, con el texto del DTO de sv5, que lo exige: services/albaran-valoracion-api/domain/models/valuation_models.py:280-282). De ahí la impresión de que «solo sale en las sintéticas»: en ellas el PRIMER término del COALESCE ya trae texto y el join roto no se nota. En las from_albaran sin match de contrato, el texto solo está en la derivada — y ese es justamente el término que el join no encuentra.

MEDICIÓN EN LA BBDD LOCAL (2026-08-18, consultas de SOLO LECTURA). Las 6 líneas de esos dos albaranes son line_kind='from_albaran' con descripcion_linea NULL, matched_contrato_line_id NULL y derived_contrato_line_id 383..388; esos ids SÍ existen en contrato_lines_derived (origen='no_ia_match') con el texto correcto: «PAPEL HIGIENICO (SACO 108)», «LTS. JABON LIQUIDO PH NEUTRO ****», «ROLLO PAPEL IND. (P)****», «KGS ANIL ESPECIAL FEYMACO (OSYMA-MONTSERRAT)», «BOLSA BASURA 52X58 (25 BOLSAS ROLLO)» y «DISCO ESPECIAL ACERO INOX. 115X1X22 ****» — el mismo texto que albaran_lines_merge.concepto. Simulando el COALESCE de la bandeja sobre toda la base: 10 de 10 líneas from_albaran salen con concepto NULL, y las 10 tienen su descripción disponible en contrato_lines_derived; las 11 sintéticas salen bien. Es decir, el defecto afecta al 100% de las líneas del albarán, no solo a Feymaco.

RIESGO LATENTE (importante). Las dos tablas usan secuencias independientes: hoy los ids de albaran_contrato_lines_merge van por 25506..25947 y los de contrato_lines_derived por 383..403, sin solape, así que el join equivocado devuelve vacío. El día que los rangos se solapen, ese mismo join devolverá la descripción de OTRA línea de contrato cualquiera: el fallo pasaría de «falta el dato» a «dato falso» sin ningún aviso. Razón de más para corregirlo aunque el síntoma actual sea solo cosmético.

RECOMENDACIÓN RAZONADA: ARREGLO EN EL FRONT, NO EN EL DATO. Dos cambios, ambos en la consulta de review_repository.py:348-405, ninguno en sv6: (1) apuntar el LEFT JOIN `dcl` a `contrato_lines_derived` (mismo criterio que ya usa el detalle); (2) añadir un último eslabón al COALESCE — LEFT JOIN albaran_lines_merge aml ON aml.id = lv.merge_line_id, y COALESCE(..., aml.concepto) — para que una línea leída del albarán NUNCA quede sin texto aunque no tenga ni matched ni derived. Por qué NO tocar sv6: `descripcion_linea` no es «la descripción de la línea», es el OVERRIDE del revisor sobre ella (sv4 escribe ahí cuando el humano edita el concepto de una fila Sigrid sin convertirla a Nueva: review_repository.py:1225-1231, y las UPDATE de :1753, :1762, :1778, :1792), más el texto propio de la sintética. Si sv6 la rellenara siempre con el concepto del albarán se perdería la distinción «editado por el humano» vs «leído del papel», habría que reescribirla en cada revaloración (sv6 persiste por replace transaccional) y el detalle del documento —que hoy funciona— empezaría a confundir ambos casos. El dato correcto YA está en la base; es la consulta la que lo busca donde no está. Decisión final del humano.

ALCANCE: solo sv4 (services/albaranes-front), la consulta de list_documents y un test que fije el comportamiento (hoy no hay ninguno que cubra DocumentLineSummary). No toca schema, ni sv5, ni sv6.

FUERA DE ALCANCE: cambiar quién rellena descripcion_linea o el diseño de las líneas sintéticas; el detalle del documento, que ya pinta bien (la conciliación lee contrato_lines_derived y la tabla «Líneas leídas del albarán (IA)» pinta ml.concepto, document_detail.html:470); y F-019/F-021, que salieron de los mismos albaranes Feymaco pero atacan la lectura de la partida, no la descripción.

VERIFICACIÓN ESPERADA AL CERRAR: abrir /documents en local con esos dos albaranes y ver el concepto real en las 6 líneas from_albaran, con las sintéticas sin cambios.

### F-001 · Test de estructura del monorepo

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-test-estructura`

Feature trivial de calentamiento para validar el circuito completo del arnés (rama, acceptance, implementer, reviewer, cierre) sin tocar ningún servicio: un test en tests/ raíz que valida la coherencia de harness/servicios.json contra el árbol real.

### F-019 · Importe de línea: manda el unitario leído; el importe solo se despeja si faltan campos

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-019-importe-unitario-manda`

Fallo REAL detectado en la prueba local del 2026-08-18 (lote FERRETERIA, Feymaco 2.137.569 y 2.139.643): la lectura de IA1 es exacta pero el importe valorado sale multiplicado por la cantidad (139,66 € reales -> 6.238,14 € valorados; 19,41 € -> 970,50 €). CADENA: (1) el SELECT de sv5 (infrastructure/database/sqlalchemy_valuation_context_repository.py, ~100-123, comentado como «FIX jun 2026») calcula importe_albaran = cantidad × precio_neto dando por hecho que precio_neto es un unitario NETO, cuando el prompt de IA1 (services/albaranes-api/config/prompts.yaml:75) lo define como cantidad*precio*(1-descuento/100), es decir el IMPORTE de la línea (columna NETO del albarán); (2) sv6 (application/services/price_reconciler.py) da prioridad al importe sobre el unitario leído y deriva unitario = importe / (cantidad × (1-dto/100)), con lo que 3.800,52 / (108 × 0,6) = 58,65 €/ud en vez de 0,543. REGLA DEL HUMANO (2026-08-18): si el PDF trae cantidad, precio unitario y descuento, importe = cantidad × precio_unitario × (1 - descuento/100) y el unitario leído MANDA; solo si faltan esos campos y hay importe final se despeja el unitario de esa misma fórmula. Alcance: alinear la semántica de precio_neto entre el prompt de IA1 y el consumidor de sv5, y ajustar la precedencia del reconciliador de sv6. Corrigiendo solo (1) la cadena ya cuadra (derivado 0,543 = declarado), pero la precedencia debe quedar explícita. Toca sv5 y sv6; revisar si el prompt de sv2 necesita precisar el significado del campo. Detalle y números en progress/prueba_local_feymaco_20260818.md.

### F-011 · Evals de IA con ground truth y puerta en el arnés

estado **terminada** · prioridad 2 · rigor `estandar` · SDD sí · rama `feature/F-011-evals-ia`

Proceso de evaluación de las 4 fases de IA contra resultado esperado, al estilo de tests unitarios. Contrato de datos ya definido en evals/ (5 Excel: IA1-IA4 + INPUTS, pestañas por tipología; los rellena el humano). Alcance: (1) conversor xlsx -> fixtures JSON versionables, con barrido de datos sensibles C3-bis; (2) runner de evals: IA1/IA2 contra la extracción real (a demanda, cuesta llamadas LLM), IA3/IA4 con modo determinista contra las redes de sv6 además del modo real; (3) puerta del arnés: declaración de rutas sensibles (prompts, clientes LLM, schemas, redes deterministas) tal que si el diff de una feature las toca, el cierre exige evals en verde además de los tests; (4) el mecanismo genérico de la puerta (declaración de rutas -> verificación extra obligatoria) se porta a arnes-base como capacidad opcional del arnés (regla de propagación).

### F-027 · Error de ×1000 en el importe: la red KG→TN de UnitConverter es código muerto

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-027-conversion-kg-tn-muerta`

HALLAZGO H-1 (CRÍTICA). El albarán 58826 de MAHORSA se valoró en 468.763,40 € cuando el administrativo dice 390,99 €, y el 58878 en 462.282,80 € frente a 385,59 €. Son 30.380 kg × 15,43 €/TN y 29.960 kg × 15,43: un factor 1000 de unidad (el albarán da kg sin literal de unidad y el contrato tarifa en TN). CAUSA RAÍZ: la red determinista que existe EXACTAMENTE para este caso (`cantidad_sin_unidad_reinterpretada_kg_a_tn`, con `_TN_UMBRAL_CONVERTIR = 1000`) NUNCA SE EJECUTA. Cuando las categorías de unidad no casan, `ValuationBuilder` llama al conversor con `cantidad=None` (services/albaran-valoracion-persist/application/services/valuation_builder.py:1020-1030, rama else de `if category_match`), y `UnitConverter.convert` sale por la guarda `cantidad is None` (unit_converter.py:64-70) ANTES de llegar al bloque de plausibilidad de toneladas (unit_converter.py:83-101), que se añadió en julio de 2026 justo para esto. El importe cae después al fallback con la cantidad cruda. El propio código documenta el caso gemelo: árido «M 20/40», 29920 sin unidad, 298.302 €. POR QUÉ ES LO PRIMERO: es un error de tres órdenes de magnitud que llega PERSISTIDO a `albaran_valuations.total_valorado` y de ahí a la bandeja del revisor; y no es raro, porque TODO el árido a granel viene en kg sin literal de unidad. PROPUESTA: invertir el orden — convertir primero y decidir revisión después. Llamar siempre a `convert()` con la cantidad real y usar `category_match=False` solo para marcar revisión, no para anular la cantidad; alternativamente, mover la comprobación de plausibilidad de TN a un guard previo e independiente. EXIGE test de regresión con el caso real 30380 kg / contrato en TN. RELACIÓN: F-024 (la unidad no se extrae de IA1) ataca la causa aguas arriba; esta feature es la red de seguridad de sv6, que debe funcionar aunque IA1 siga sin unidad. F-025 (falsa alarma `no_quantity_in_albaran`) toca la misma rama del builder: coordinar para no pisarse. Toca sv6. Fuente: progress/revision_resto_lote_20260818.md (revision de los 7 albaranes restantes del lote alvaro_17082026, 2026-08-18).

### F-012 · Campaña de mutación en paralelo

estado **terminada** · prioridad 3 · rigor `estandar` · SDD sí · rama `feature/F-012-mutacion-paralela`

python -m harness.mutacion tarda minutos porque evalúa cada mutante en serie relanzando la suite. Paralelizarla: N workers, cada uno en su git worktree aislado, repartiéndose los mutantes; agregación de resultados en un único progress/mutacion_F-XXX.md idéntico al actual; restauración del árbol garantizada POR WORKER incluso ante excepción o Ctrl-C (la garantía actual, multiplicada); número de workers configurable en harness/rigor.json o parámetro --workers con default sensato (nº de núcleos - 2). La mejora es genérica del arnés: se porta a arnes-base en la misma feature. Criterio de éxito: mismo informe y mismos totales que la campaña en serie sobre la misma feature, en una fracción del tiempo.

### F-002 · Tanda 1 — Identificación de obra y proveedor (G1+G2)

estado **terminada** · prioridad 4 · rigor `estandar` · SDD sí · rama `feature/F-002-obra-proveedor`

La mayor fuente de albaranes inválidos del feedback (6 de 16). Obras activas de Sigrid inyectadas en el prompt de IA1 (la IA elige SOLO de esa lista) + red determinista en sv3: obra extraída inexistente => sin obra + revisión. Proveedor = razón social del bloque fiscal resuelta por CIF contra Sigrid, nunca la marca del logotipo; si el CIF no casa pero el nombre contiene un proveedor con contrato en la obra => propuesta a revisión. Guard de año: fecha_albaran a más de 1 año de la recepción del email => revisión. Casos de referencia: obra 0937 inventada, MACOTRAN en 4 obras erróneas, GRUPO OTTO HORPRESOL vs HORPRESOL S.L. Toca sv2 (prompt IA1) y sv3 (redes).
