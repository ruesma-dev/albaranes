<!-- specs/F-043-clasificacion-por-ia1/requirements.md -->
# F-043 · IA1 clasifica el albarán — Requisitos (EARS)

Rigor `critico`. Servicios: sv2, sv3, sv5, sv6 (+ sv4 solo para mostrar) y
`albaranes-comun`. Decisión del humano del 2026-08-25: **la clasificación la
hace SIEMPRE la IA**; si clasifica mal se arregla el PROMPT, nunca con un `if`
aguas abajo.

## A · Catálogo de familias en un solo sitio

- **R1.** El sistema debe mantener el catálogo de familias de albarán en UN
  único módulo versionado, con `id`, `nombre`, `definicion`, `no_es` (en qué
  se diferencia de sus vecinas), `senales`, `alcance` (documento / línea),
  `prompt_fase2` y `prompt_valoracion`.
- **R2.** El sistema debe derivar del catálogo las familias válidas de
  DOCUMENTO y de LÍNEA; ningún servicio debe declarar lista propia de familias
  ni tabla propia de prompts por familia.
- **R3.** CUANDO se añade una familia al catálogo con sus dos claves de
  prompt, el sistema debe enrutarla en fase 2 y en valoración sin modificar
  código de sv2, sv5 ni sv6.
- **R4.** El sistema debe definir `generico` como CLASE LEGÍTIMA con
  definición propia —suministro de materiales o productos que no pertenece a
  ninguna familia con reglas de valoración propias—, y su definición debe
  distinguirla explícitamente de «no se pudo clasificar».
- **R5.** El catálogo debe distinguir por definición las parejas que hoy se
  confunden: hormigón frente a mortero, y residuos frente a transporte o
  alquiler de contenedor sin gestión del residuo.

## B · IA1 clasifica el documento

- **R6.** El sistema debe inyectar el catálogo renderizado (definición, en qué
  se diferencia y señales de cada familia) en el prompt de fase 1 mediante un
  marcador, igual que hoy hace con `{obras_activas}`.
- **R7.** El prompt de fase 1 debe exigir a IA1 devolver SIEMPRE un bloque
  `clasificacion` de nivel DOCUMENTO con `familia`, `confianza_pct`, `motivo`
  (por qué, citando lo leído en el documento), `mixto` y
  `familias_secundarias`.
- **R8.** El sistema debe aceptar el bloque `clasificacion` en el esquema del
  documento de fase 1 y en `documento_revisado` de fase 2, y un envelope
  anterior que no lo traiga debe seguir validando.
- **R9.** El sistema debe hacer viajar la clasificación dentro de `data`, no
  en `meta`: sv3 filtra `meta` contra un modelo estricto y hoy descarta
  `meta.tipologia` (`persistence_worker._sanear_envelope`).
- **R10.** SI IA1 devuelve una `familia` que no está en el catálogo, ENTONCES
  el sistema debe registrar `generico`, conservar el valor original dentro del
  motivo y marcar el documento a revisión; PROHIBIDO deducir la familia de
  otra señal.
- **R11.** SI el envelope no trae bloque `clasificacion`, ENTONCES el sistema
  debe registrar `familia='generico'`, `confianza_pct=0`, `origen='ausente'` y
  motivo `ia_sin_clasificacion`, y marcar el documento a revisión. PROHIBIDO
  reconstruir la familia por código LER, designación de producto, palabras
  clave, familia dominante de las líneas u override por CIF.

## C · Fin del lazo cerrado (el resolver deja de decidir)

- **R12.** El sistema debe retirar `tipologia_resolver` como DECISOR: la
  familia del documento es exactamente la que dijo la IA.
- **R13.** El sistema NO debe aplicar ninguna regla determinista que infiera o
  fuerce la familia del documento. Test: documento con código LER en todas sus
  líneas y `clasificacion.familia='generico'` ⇒ familia resuelta `generico`.
- **R14.** El sistema debe retirar el override de tipología por CIF.
- **R15.** CUANDO se elige el prompt de fase 2, el sistema debe hacerlo por
  consulta directa al catálogo con la familia dicha por la IA; SI esa clave no
  está registrada en el índice de prompts, ENTONCES cae al prompt genérico
  configurado y lo deja en el log.
- **R16.** CUANDO la fase 2 devuelve su propio bloque `clasificacion` en
  `documento_revisado`, éste debe prevalecer sobre el de fase 1 y quedar
  registrado con `origen='ia2'`.

## D · Documento o línea

- **R17.** El sistema debe tratar la clasificación como propiedad del
  DOCUMENTO, y `contexto_linea.tipo_familia` como afinado por LÍNEA que la
  fase 2 sigue rellenando.
- **R18.** CUANDO una línea no trae `tipo_familia` y el documento NO está
  marcado `mixto`, la familia efectiva de esa línea debe ser la del documento.
- **R19.** MIENTRAS el documento esté marcado `mixto=true`, el sistema NO debe
  heredar la familia del documento a las líneas sin `tipo_familia`: esas
  líneas quedan sin familia efectiva y añaden el motivo de revisión
  `linea_sin_familia_en_albaran_mixto`.
- **R20.** El sistema debe calcular la familia efectiva en UN solo punto
  compartido; sv5 y sv6 no deben duplicar el criterio.
- **R21.** El sistema NO debe escribir la familia heredada dentro de
  `contexto_linea`: lo que la IA dijo por línea se conserva intacto y la
  herencia se resuelve en lectura.

## E · Persistir el qué, el porqué y la confianza

- **R22.** sv3 debe persistir en `albaran_documents_merge` la familia, la
  confianza, el motivo, el origen, el indicador de mixto y las familias
  secundarias, con DDL idempotente.
- **R23.** sv5 debe leer esas columnas y entregarlas en `ContextoValoracion` y
  en el `context` del envelope que consume sv6.
- **R24.** sv5 debe elegir el prompt de valoración por el catálogo a partir de
  la familia del DOCUMENTO, retirando su derivación propia por líneas.
- **R25.** sv6 debe abrir sus puertas de familia —cálculo de contenedores,
  sintéticas por LER, guarda anti-incremento y sintéticas de hormigón— por la
  familia EFECTIVA de la línea.
- **R26.** CUANDO sv6 valora un albarán con clasificación de documento
  `residuos` y líneas sin `tipo_familia`, contra el contrato de SALMEDINA del
  caso SS-0003967, debe producir **210,00 €** en 2 líneas (contenedor 120 +
  incremento LER 90), no 540,00 € en 1 línea.
- **R27.** SI un envelope llega sin clasificación (documento anterior a esta
  feature), ENTONCES sv5 y sv6 deben comportarse exactamente como hoy.

## F · Que el revisor lo vea y que la duda pare

- **R28.** CUANDO `confianza_pct` es menor que un umbral configurable
  (defecto 60), sv3 debe añadir el motivo de revisión
  `clasificacion_confianza_baja` al documento.
- **R29.** CUANDO el documento viene marcado `mixto`, sv3 debe añadir el
  motivo `clasificacion_mixta`.
- **R30.** sv4 debe mostrar en la ficha del documento la familia, la confianza
  y el motivo de la clasificación, y los motivos nuevos deben aparecer en el
  bloque de motivos de revisión que ya existe (F-036 R23).

## G · Rigor (nivel `critico`)

- **R31.** Cada requisito debe tener al menos un test `test_f043_rNN_*` escrito
  en fase RED (falla antes, pasa después) con su traza en el informe.
- **R32.** Cobertura de líneas cambiadas ≥ 80 % y campaña de mutación completa
  con 0 supervivientes sin justificación aceptada por el humano.
- **R33.** Los tests corren sin red, sin BBDD y sin LLM; lo que exija BBDD o
  LLM real se marca MANUAL (humano) en `tasks.md`.
- **R34.** DONDE se tocan rutas sensibles (prompts de sv2 y sv5, schemas de
  extracción, redes deterministas de sv6 y el catálogo nuevo), el cierre exige
  evals con LLM real en verde.

## DUDAS PARA EL HUMANO (resolver antes de implementar)

1. **Alcance del catálogo.** Hoy son tipología de DOCUMENTO cuatro familias
   (`generico`, `hormigon`, `mortero`, `residuos`) y son familias de LÍNEA
   además `combustible`, `alquiler_maquinaria` y `otro`. La spec asume que el
   catálogo arranca así y que `combustible`, `alquiler_maquinaria` y `bombeo`
   NO son todavía clasificación de documento porque no tienen prompt de fase 2
   propio. ¿Correcto, o quieres que IA1 pueda devolverlas ya?
2. **`otro` como familia de línea.** ¿`tipo_familia='otro'` significa
   «genérico» o «no es de ninguna familia con reglas»? Afecta a si esa línea
   hereda o no la familia del documento (R18).
3. **Umbral de confianza baja.** La spec propone 60 % y que solo MARQUE
   revisión, sin bloquear la valoración. ¿Confirmas el número y que no
   bloquee?
4. **Albarán mixto.** La spec deja las líneas de la familia minoritaria
   leídas con el prompt de la mayoritaria (límite real de hoy) y solo lo hace
   VISIBLE con un motivo de revisión. Re-ejecutar la fase 2 con un segundo
   prompt sería otra feature. ¿De acuerdo?
5. **Backfill.** ¿Los albaranes ya persistidos se re-clasifican (re-fetch
   masivo) o solo se clasifican los nuevos y los que se revaloren a mano?
6. **Coste de evals.** ¿Cuántos casos con LLM real autorizas para el cierre y
   con qué proveedores?
