<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **21 features**, 17 abiertas, 4 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-019 | Importe de línea: manda el unitario leído; el importe solo se despeja si faltan campos | 1 | spec lista | critico | `feature/F-019-importe-unitario-manda` |
| F-015 | Líneas tachadas del albarán: no se registran | 2 | pendiente | estandar | `feature/F-015-lineas-tachadas` |
| F-021 | Partida: validación contra el catálogo del contrato y elección asistida entre candidatas | 3 | pendiente | estandar | `feature/F-021-partida-catalogo-candidatas` |
| F-016 | Reparto de una línea del albarán entre varias partidas | 4 | pendiente | estandar | `feature/F-016-linea-multipartida` |
| F-020 | El pipeline es agnóstico al proveedor de IA: ninguna fase privilegia a OpenAI | 5 | pendiente | estandar | `feature/F-020-proveedor-agnostico` |
| F-003 | Tanda 2 — Albaranes valorados, match estricto y coherencia (G3+G4+G5) | 6 | spec lista | estandar | `feature/F-003-valorados-match-estricto` |
| F-014 | Conversor del formato plano del administrativo a fixtures de evals | 7 | pendiente | estandar | `feature/F-014-conversor-administrativo` |
| F-018 | Carga incompleta: línea siempre generada por IA2 y cantidad fijada por IA3 con mínimo por defecto 6 m³ | 8 | pendiente | estandar | `feature/F-018-carga-incompleta` |
| F-004 | Tanda 3 — Hormigón fino y veto de mortero | 9 | spec lista | estandar | `feature/F-004-hormigon-fino` |
| F-005 | Tanda 4a — Tipología bombeo | 10 | spec lista | estandar | `feature/F-005-bombeo` |
| F-006 | Tanda 4b — Residuos: lógica de pago LLEVAR/RETIRAR y canon | 11 | spec lista | estandar | `feature/F-006-residuos-pago` |
| F-007 | Tanda 5 — Partida ALM por defecto y selector de candidatas en sv4 | 12 | spec lista | estandar | `feature/F-007-partida-alm-selector` |
| F-017 | El comparativo como fuente de precio (1c) en la valoración | 13 | pendiente | estandar | `feature/F-017-comparativo-precio` |
| F-013 | Registro del albarán aprobado en Sigrid (consumidor de q-feedback) | 14 | pendiente | critico | `feature/F-013-registro-sigrid` |
| F-008 | Lifecycle de blobs de hand-off | 15 | pendiente | estandar | `feature/F-008-blob-lifecycle` |
| F-009 | Limpieza de la cola huérfana q-emails | 16 | pendiente | estandar | `feature/F-009-limpieza-q-emails` |
| F-010 | Easy Auth en el portal sv4 | 17 | pendiente | critico | `feature/F-010-easy-auth-sv4` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Test de estructura del monorepo | 1 | estandar |
| F-011 | Evals de IA con ground truth y puerta en el arnés | 2 | estandar |
| F-012 | Campaña de mutación en paralelo | 3 | estandar |
| F-002 | Tanda 1 — Identificación de obra y proveedor (G1+G2) | 4 | estandar |

## Detalle

### F-019 · Importe de línea: manda el unitario leído; el importe solo se despeja si faltan campos

estado **spec lista** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-019-importe-unitario-manda`

Fallo REAL detectado en la prueba local del 2026-08-18 (lote FERRETERIA, Feymaco 2.137.569 y 2.139.643): la lectura de IA1 es exacta pero el importe valorado sale multiplicado por la cantidad (139,66 € reales -> 6.238,14 € valorados; 19,41 € -> 970,50 €). CADENA: (1) el SELECT de sv5 (infrastructure/database/sqlalchemy_valuation_context_repository.py, ~100-123, comentado como «FIX jun 2026») calcula importe_albaran = cantidad × precio_neto dando por hecho que precio_neto es un unitario NETO, cuando el prompt de IA1 (services/albaranes-api/config/prompts.yaml:75) lo define como cantidad*precio*(1-descuento/100), es decir el IMPORTE de la línea (columna NETO del albarán); (2) sv6 (application/services/price_reconciler.py) da prioridad al importe sobre el unitario leído y deriva unitario = importe / (cantidad × (1-dto/100)), con lo que 3.800,52 / (108 × 0,6) = 58,65 €/ud en vez de 0,543. REGLA DEL HUMANO (2026-08-18): si el PDF trae cantidad, precio unitario y descuento, importe = cantidad × precio_unitario × (1 - descuento/100) y el unitario leído MANDA; solo si faltan esos campos y hay importe final se despeja el unitario de esa misma fórmula. Alcance: alinear la semántica de precio_neto entre el prompt de IA1 y el consumidor de sv5, y ajustar la precedencia del reconciliador de sv6. Corrigiendo solo (1) la cadena ya cuadra (derivado 0,543 = declarado), pero la precedencia debe quedar explícita. Toca sv5 y sv6; revisar si el prompt de sv2 necesita precisar el significado del campo. Detalle y números en progress/prueba_local_feymaco_20260818.md.

### F-015 · Líneas tachadas del albarán: no se registran

estado **pendiente** · prioridad 2 · rigor `estandar` · SDD sí · rama `feature/F-015-lineas-tachadas`

Caso real (Feymaco 2137569, lote alvaro_17082026): una línea impresa TACHADA a mano (anulada) que el administrativo correctamente excluye. Hoy la extracción no distingue tachaduras. Comportamiento a especificar: IA1/IA2 detectan la línea anulada y no la emiten (o la emiten marcada como anulada y la persistencia la excluye con rastro); ante duda, a revisión — nunca valorarla como buena. Toca prompts de sv2 (rutas sensibles => evals) y posiblemente redes de sv3. Marcada por el humano como de bastante prioridad (2026-08-17).

### F-021 · Partida: validación contra el catálogo del contrato y elección asistida entre candidatas

estado **pendiente** · prioridad 3 · rigor `estandar` · SDD sí · rama `feature/F-021-partida-catalogo-candidatas`

Origen: prueba local del 2026-08-18 con el albarán Feymaco 2.137.569. El código de imputación manuscrito «P4/P5.36.01» se leyó primero como «PJ.36.01» y, tras F-019, como «36.01» a secas: la IA se comió el prefijo. Hoy NADIE valida que el código leído exista, así que una imputación contable inventada entra sin un solo aviso. ALCANCE EN TRES PASOS, en este orden (decisión del humano, 2026-08-18): (1) VALIDACIÓN DETERMINISTA, sin IA: comprobar el código leído contra el catálogo de partidas del contrato, que YA viaja en el contexto de sv6 a sv5 (albaran_contrato_lines_merge.codigo_partida). Comprobado en el contrato CTSU24/0454: 3 prefijos de primer nivel (P5 con 218 líneas, P4 con 188, CI con 36) y las partidas P4.36.01 y P5.36.01 EXISTEN, así que con el «36.01» leído a medias el catálogo devuelve solos los dos candidatos correctos, sin salir a ningún sistema externo. Casar por sufijo y por prefijo, no solo por igualdad. (2) ELECCIÓN ASISTIDA: solo si el código no valida y hay más de un candidato, la IA elige POR DESCRIPCIÓN entre los candidatos del catálogo, devolviendo confianza y motivo. La IA no decide en silencio: una imputación contable equivocada es un asiento mal hecho. (3) POR DEBAJO DEL UMBRAL DE CONFIANZA, la línea va al selector de candidatas de sv4, que ya especifica F-007: esta feature se apoya en aquella, no la duplica. AMPLIACIÓN FUTURA (fuera de alcance aquí): cuando el código no aparezca en el contrato, consultar las partidas de la obra en Sigrid vía sigrid-api (solo lectura); el documento de sigrid-api menciona el desglose por partidas pero no consta expuesto como endpoint. NO ENTRA: la lectura del separador «/» como reparto en varias partidas, que es F-016, ni el reparto en sí. Relación con otras features: F-016 (multipartida) depende de que el código se lea y valide bien; F-007 aporta el selector humano. Toca sv5 y sv6, con verificación en sv4. Detalle del incidente en progress/prueba_local_feymaco_20260818.md.

### F-016 · Reparto de una línea del albarán entre varias partidas

estado **pendiente** · prioridad 4 · rigor `estandar` · SDD sí · rama `feature/F-016-linea-multipartida`

Caso real (Feymaco 2137569): una línea impresa de 108 uds repartida a mano entre dos partidas (54 a P4.36.01 y 54 a P5.36.01, anotación 'P4/P5.36.01'). El pipeline actual modela una línea -> una partida. La spec debe decidir el modelo: ¿la valoración soporta líneas hijas con cantidades parciales por partida, o el reparto es una acción manual del revisor en sv4 (split de línea) previa al registro? Impacto potencial en schema (listar lectores: sv5 SQL crudo) y en el futuro registro en Sigrid (F-013).

### F-020 · El pipeline es agnóstico al proveedor de IA: ninguna fase privilegia a OpenAI

estado **pendiente** · prioridad 5 · rigor `estandar` · SDD sí · rama `feature/F-020-proveedor-agnostico`

Hoy sv3 tiene los proveedores cableados por nombre: el contrato ExtractionEnvelope (services/albaranes-persistencia/domain/models/extraction_models.py:73) es «el envelope de OpenAI» + campos opcionales gemini y claude, así que quien venga en el envelope principal se registra como openai (prueba del 2026-08-18: provider_origin='openai' con model_name='gemini-3.7-flash'); el scoring premia la marca (openai_only 76 frente a gemini_only/claude_only 66, en albaran_confidence_service.py:81-83); y los topes y motivos la nombran (openai_fallback -> cap 84 % + single_provider_openai; line_only_in_openai:N). Consecuencia medida: una ejecución correcta con «FASE 1=gemini . FASE 2=gemini» queda capada al 84 %, por debajo del umbral de 80, y todo va a revisión con motivos que no describen lo ocurrido. ALCANCE (decisiones del humano, 2026-08-18): (1) sv2 declara en el meta del envelope 'provider', 'providers_used' y 'providers_expected' (application/services/phase_merge.py y application/pipelines/extract_albaran_pipeline.py); (2) el contrato pasa de «openai + gemini? + claude?» a «fuente principal + lista de fuentes adicionales», cada una con su provider, aceptando el formato antiguo para no romper mensajes en vuelo ni envelopes ya guardados; (3) sv3 puntúa por número de fuentes y no por marca: openai_only/gemini_only/claude_only se funden en un único 'single_source' con el MISMO valor para todos (76); (4) provider_origin guarda el valor real (gemini, gemini+openai...) en vez de openai_fallback; (5) SE ELIMINA el tope por número de fuentes y el motivo single_provider_openai: con una sola fuente la confianza sale del acuerdo entre campos, no de un castigo fijo. En su lugar, 'provider_missing:<esperado>' salta SOLO si providers_used < providers_expected (fallo real de un proveedor); (6) line_only_in_openai:N pasa a line_single_source:N. Los demás topes (conflicto en campo crítico, campo requerido ausente, líneas sin casar) NO cambian: penalizan hechos, no marcas. NO ENTRA: rehacer el algoritmo de merge multi-IA (se conserva primaria/secundaria/terciaria, solo cambia quién ocupa cada puesto) ni decidir si se vuelve a llamar a varios proveedores en fase 1 (es configuración). RIESGOS: no existe NINGÚN test que fije estos strings (comprobado), así que la red de seguridad se construye en la feature; los documentos ya persistidos se quedan con provider_origin='openai' y no se reescribe histórico; verificar el selector de vistas por proveedor de sv4 (infrastructure/database/review_repository.py). Toca sv2 y sv3, con verificación en sv4.

### F-003 · Tanda 2 — Albaranes valorados, match estricto y coherencia (G3+G4+G5)

estado **spec lista** · prioridad 6 · rigor `estandar` · SDD sí · rama `feature/F-003-valorados-match-estricto`

Albaranes que VIENEN valorados: transcribir, no recomponer (precio, TODOS los descuentos e importe se copian tal cual por su etiqueta de columna; prohibido derivar precio=importe×algo — caso ×120). El dto del albarán no se aplica sobre el precio de contrato. Guard aritmético: precio×cantidad(−dtos)≈importe leído y Σimportes=total albarán; si no cuadra => revisión, nunca inventar. Matching estricto: atributo sustantivo distinto (tamaño, modelo, tipo) => NO casar; mejor línea nueva sin precio a revisión (casos CETOSA, elemento base 0,5 mm, bolsa de cuñas). Toca sv5 (prompts) y sv6 (redes deterministas).

### F-014 · Conversor del formato plano del administrativo a fixtures de evals

estado **pendiente** · prioridad 7 · rigor `estandar` · SDD sí · rama `feature/F-014-conversor-administrativo`

El ground truth real lo produce el administrativo como xlsx PLANO (una fila por línea final, 19 columnas — lote de referencia: alvaro_17082026) + carpeta de PDFs con convención <proveedor>_<codigoAlbaran>.pdf (símbolos prohibidos de Windows eliminados del código, p.ej. 2026/01/007181 -> 202601007181). Ese formato pasa a ser el OFICIAL del libro maestro: el conversor de evals debe ingerirlo y generar los fixtures E2E + derivar automáticamente los esperados de IA1 (cabecera + líneas EN ALBARAN, con precio/importe solo cuando su fuente es ALBARAN) e IA2 (tipología mapeada) dejando '?' donde no sea derivable. Normalizaciones: obra a 4 dígitos (Excel pierde ceros: 696 -> 0696), descuento en fracción = porcentaje (0.4 = 40%), prefijos de partida SOLO CI/CD/CP (corrige lecturas tipo C1 -> CI), mapeo de tipos del administrativo (FERRETERIA/MATERIALES/GRAVA -> genérico-suministros; HORMIGON; MORTERO; CAMION GRUA -> decidir en spec). Barrido C3-bis antes de versionar fixtures. Con fixtures reales, valorar subir la puerta de rutas sensibles a bloqueo.

### F-018 · Carga incompleta: línea siempre generada por IA2 y cantidad fijada por IA3 con mínimo por defecto 6 m³

estado **pendiente** · prioridad 8 · rigor `estandar` · SDD sí · rama `feature/F-018-carga-incompleta`

Regla del humano (2026-08-18) que revisa el comportamiento actual de M7. HOY (prompt valuation_es de sv5, bloque M7): la línea de carga incompleta la emite IA3, SOLO si el contrato tarifa carga incompleta y SOLO ante señal (texto o cantidad < umbral), con umbral leído del PDF del contrato y sin default. REGLA NUEVA: (1) IA2 genera SIEMPRE la línea CARGA INCOMPLETA en hormigón/mortero como deducción de documento (conoce los m³ vertidos), aunque la cantidad final resulte 0; (2) IA3 fija la cantidad final contra el contrato: mínimo del contrato − m³ vertidos, con MÍNIMO POR DEFECTO 6 m³ si el contrato no lo indica; si vertidos ≥ mínimo → cantidad 0; (3) precio: el del contrato si lo tarifa; si no, a revisión (F-017 comparativo cuando exista). Caso de referencia: HSM 224964 (4 m³ → 2 m³ de carga incompleta). ATENCIÓN: F-004 (spec_ready) dice «M6/M7 solo con señal explícita»: esta feature la CONTRADICE y prevalece; al arrancar F-004 hay que reconciliar su R de M7 con esta regla. Toca sv2 (IA2, futura deducción por categoría), sv5 (prompt M7) y sv6 (builder/redes).

### F-004 · Tanda 3 — Hormigón fino y veto de mortero

estado **spec lista** · prioridad 9 · rigor `estandar` · SDD sí · rama `feature/F-004-hormigon-fino`

Re-apuntado determinista de incrementos al recurso del contrato en la partida de la línea base (solo derivar si de verdad no existe). Familia mortero (códigos D-*) separada del hormigón con veto determinista: solo arena; prohibidas sintéticas de árido, aditivo, plastificante, fibras y fratasado; el tercer campo del código es resistencia, no árido. M6/M7 (exceso de tiempo, carga incompleta) solo con señal explícita en el documento. La partida de un incremento debe existir en el contrato (o ALM/None), jamás un literal nuevo. Toca sv5 (prompts/schema) y sv6 (builder y redes).

### F-005 · Tanda 4a — Tipología bombeo

estado **spec lista** · prioridad 10 · rigor `estandar` · SDD sí · rama `feature/F-005-bombeo`

Valoración por rendimiento mínimo contractual (caso PUMPING TEAM): m³ a facturar = horas de bombeo × rendimiento mínimo del contrato (caso real: 10,5 h × 20 m³/h = 210 m³ aunque se bombeara menos). La línea de horas NO se factura aparte (embebida en el mínimo); el desplazamiento sí. Requiere prompt de familia nuevo y leer el rendimiento del contrato. Toca sv2 (contexto_linea), sv5 (prompt) y sv6 (reglas).

### F-006 · Tanda 4b — Residuos: lógica de pago LLEVAR/RETIRAR y canon

estado **spec lista** · prioridad 11 · rigor `estandar` · SDD sí · rama `feature/F-006-residuos-pago`

Solo LLEVAR => no se paga y no entra en Sigrid. RETIRAR => se paga el porte + línea de CANON DE VERTEDERO obligatoria. Ambos en el mismo albarán => solo cuenta RETIRAR. Partida del recurso del contrato, jamás inventada (caso 16.01 vs 15.01). La lectura (LER, volumen/peso por etiqueta, llevadas/retiradas separadas, cálculo de contenedores) ya está entregada; esta feature es solo la lógica de pago. Toca sv5 (prompt) y sv6 (reglas).

### F-007 · Tanda 5 — Partida ALM por defecto y selector de candidatas en sv4

estado **spec lista** · prioridad 12 · rigor `estandar` · SDD sí · rama `feature/F-007-partida-alm-selector`

Suministros NO se destinan: partida ALM (almacén) con imputación parcial mensual; indirectos SÍ se destinan a la entrada. Cuando el mismo recurso existe en varias partidas (contratos de hormigón con clones), la elección es humana: selector de partidas candidatas en sv4 + memoria por obra+producto para prerrellenar (la información de a qué tajo va el camión no está en el documento). Toca sv6 (regla ALM) y sv4 (selector + memoria).

### F-017 · El comparativo como fuente de precio (1c) en la valoración

estado **pendiente** · prioridad 13 · rigor `estandar` · SDD sí · rama `feature/F-017-comparativo-precio`

Decisión del humano (2026-08-17) que resuelve el 'OFERTA' del ground truth: el administrativo obtiene el precio unitario/importe por este orden: (1) líneas iguales ya registradas en líneas de contrato [hoy 1a], (2) contrato en papel [hoy 1b], (3) como ÚLTIMO recurso, el precio del COMPARATIVO asociado al contrato [nuevo, 1c]. Hay que añadir esa tercera fuente: la spec debe estudiar de dónde sale el comparativo (¿Sigrid vía sigrid-api? ¿documento en SharePoint?), cómo se asocia al contrato, y ampliar precio_source en sv5/sv6 (y el modelo de conciliación 1a-vs-1b) sin romper lectores. Las 3 líneas OFERTA del lote alvaro_17082026 son los casos de referencia.

### F-013 · Registro del albarán aprobado en Sigrid (consumidor de q-feedback)

estado **pendiente** · prioridad 14 · rigor `critico` · SDD sí · rama `feature/F-013-registro-sigrid`

Marcada como MUY IMPORTANTE por el humano (2026-08-13). Servicio nuevo del monorepo (la responsabilidad no cabe en ninguno existente; q-feedback está reservada para esto desde el diseño): consume q-feedback y da de alta el albarán valorado y aprobado en Sigrid vía sigrid-api sql/write (única base escribible: ruesma; el guard semántico de sigrid-api existe y la escritura está off por defecto). Excluye las líneas marcadas no_registrar_sigrid (F-006). Diseño pendiente y delicado: qué tablas de Sigrid, MAX(ide)+1 con lock, idempotencia del alta (un albarán aprobado dos veces no puede duplicarse en el ERP), y autorización expresa del humano para activar la escritura. Escribe en el ERP de producción => rigor critico y verificaciones MANUAL obligatorias.

### F-008 · Lifecycle de blobs de hand-off

estado **pendiente** · prioridad 15 · rigor `estandar` · SDD no · rama `feature/F-008-blob-lifecycle`

Los workers no borran input/ ni envelopes/ (semántica at-least-once); la limpieza es una lifecycle policy del storage que está escrita (infra/blob_lifecycle.ps1) pero sin ejecutar. Aplicarla (14 días) y verificar que queda activa.

### F-009 · Limpieza de la cola huérfana q-emails

estado **pendiente** · prioridad 16 · rigor `estandar` · SDD no · rama `feature/F-009-limpieza-q-emails`

q-emails es un resto del diseño original (intake partido en receptor+worker, colapsado en sv1): nadie la publica ni consume. Retirarla de la lista canónica de ruesma_comun.colas. Antes: grep en infra/ por si algún script la crea o referencia (create_capps, scale rules, fase1), y decisión del humano sobre borrarla del storage o dejarla morir.

### F-010 · Easy Auth en el portal sv4

estado **pendiente** · prioridad 17 · rigor `critico` · SDD sí · rama `feature/F-010-easy-auth-sv4`

sv4 es el único ingress externo y está sin autenticación (pendiente desde el despliegue). Configurar Easy Auth con Entra ID: app registration, redirect URIs, y verificación con usuarios reales del portal. Delicada: afecta a los usuarios y a las redirect URIs de Entra; verificación manual obligatoria.

### F-001 · Test de estructura del monorepo

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-test-estructura`

Feature trivial de calentamiento para validar el circuito completo del arnés (rama, acceptance, implementer, reviewer, cierre) sin tocar ningún servicio: un test en tests/ raíz que valida la coherencia de harness/servicios.json contra el árbol real.

### F-011 · Evals de IA con ground truth y puerta en el arnés

estado **terminada** · prioridad 2 · rigor `estandar` · SDD sí · rama `feature/F-011-evals-ia`

Proceso de evaluación de las 4 fases de IA contra resultado esperado, al estilo de tests unitarios. Contrato de datos ya definido en evals/ (5 Excel: IA1-IA4 + INPUTS, pestañas por tipología; los rellena el humano). Alcance: (1) conversor xlsx -> fixtures JSON versionables, con barrido de datos sensibles C3-bis; (2) runner de evals: IA1/IA2 contra la extracción real (a demanda, cuesta llamadas LLM), IA3/IA4 con modo determinista contra las redes de sv6 además del modo real; (3) puerta del arnés: declaración de rutas sensibles (prompts, clientes LLM, schemas, redes deterministas) tal que si el diff de una feature las toca, el cierre exige evals en verde además de los tests; (4) el mecanismo genérico de la puerta (declaración de rutas -> verificación extra obligatoria) se porta a arnes-base como capacidad opcional del arnés (regla de propagación).

### F-012 · Campaña de mutación en paralelo

estado **terminada** · prioridad 3 · rigor `estandar` · SDD sí · rama `feature/F-012-mutacion-paralela`

python -m harness.mutacion tarda minutos porque evalúa cada mutante en serie relanzando la suite. Paralelizarla: N workers, cada uno en su git worktree aislado, repartiéndose los mutantes; agregación de resultados en un único progress/mutacion_F-XXX.md idéntico al actual; restauración del árbol garantizada POR WORKER incluso ante excepción o Ctrl-C (la garantía actual, multiplicada); número de workers configurable en harness/rigor.json o parámetro --workers con default sensato (nº de núcleos - 2). La mejora es genérica del arnés: se porta a arnes-base en la misma feature. Criterio de éxito: mismo informe y mismos totales que la campaña en serie sobre la misma feature, en una fracción del tiempo.

### F-002 · Tanda 1 — Identificación de obra y proveedor (G1+G2)

estado **terminada** · prioridad 4 · rigor `estandar` · SDD sí · rama `feature/F-002-obra-proveedor`

La mayor fuente de albaranes inválidos del feedback (6 de 16). Obras activas de Sigrid inyectadas en el prompt de IA1 (la IA elige SOLO de esa lista) + red determinista en sv3: obra extraída inexistente => sin obra + revisión. Proveedor = razón social del bloque fiscal resuelta por CIF contra Sigrid, nunca la marca del logotipo; si el CIF no casa pero el nombre contiene un proveedor con contrato en la obra => propuesta a revisión. Guard de año: fecha_albaran a más de 1 año de la recepción del email => revisión. Casos de referencia: obra 0937 inventada, MACOTRAN en 4 obras erróneas, GRUPO OTTO HORPRESOL vs HORPRESOL S.L. Toca sv2 (prompt IA1) y sv3 (redes).
