# F-111 · Requisitos (EARS)

Residuos: tamaño de contenedor 3, 6 o 9 m³ con el precio general del contrato (parte A) y partida del capítulo de
gestión de residuos de la obra en vez de almacén (parte B). Servicios: **sv6** (reglas), **sv5** (prompts y un
endpoint de IA), **comun** (reconocer el capítulo). Reglas literales del humano (2026-10-29) en `harness/features.json`
(F-111). Medición en producción y decisiones abiertas: `design.md` §2 y §10.

Notación: «m³» = `contexto_linea.volumen_m3` de la línea; «tamaños del contrato» = los m³ que se leen de las líneas de
CONTENEDOR del contrato (tabla de Sigrid) o, si la tabla no los trae, el `contenedor_m3` que IA3 leyó del contrato.
Tolerancia de m³: 0,01 (la de hoy en `_elegir_contenedor`).

## A.1 · Tamaño estándar (el contrato no da tamaños) — sv6 `residuos_container_calc.py`

- **R1.** MIENTRAS el contrato no dé tamaños, el sistema debe elegir el contenedor estándar más pequeño en el que caben
  los m³: m³ ≤ 3 ⇒ 1 de 3; 3 < m³ ≤ 6 ⇒ 1 de 6; 6 < m³ ≤ 9 ⇒ 1 de 9. Test por tramo y en cada borde (3; 3,01; 6;
  6,01; 9; 9,01).
- **R2.** MIENTRAS el contrato no dé tamaños y los m³ pasen de 9, el sistema debe valorar `ceil(m³ / 6)` contenedores
  de 6, sin mezclar tamaños (10 ⇒ 2 de 6; 12 ⇒ 2; 12,5 ⇒ 3; 16 ⇒ 3).
- **R3.** CUANDO se aplica el tamaño estándar, el sistema debe dejar el motivo `residuos_tamano_estandar=<t>m3` (sin
  revisión) en lugar de `residuos_tamano_defecto_6m3`, que deja de escribirse.
- **R4.** El sistema debe valorar el contenedor estándar con el precio de la línea casada (el precio general del
  contrato), sea cual sea el tamaño elegido: la cantidad cambia, el precio no. Test: 4839 B (8 m³, 139 €) ⇒ 1 × 139.
- **R5.** El motivo `residuos_contenedores=<n> (m3=<m> / contenedor=<t> m3)` debe seguir escribiéndose con el mismo
  formato (sv4 y la medición lo leen).

## A.2 · El contrato da tamaños

- **R6.** MIENTRAS el contrato dé tamaños, el sistema debe elegir el más pequeño de ellos en el que caben los m³
  (1 contenedor). Con [6, 8]: 6 ⇒ 1 de 6; 7 ⇒ 1 de 8; 8 ⇒ 1 de 8.
- **R7.** SI los m³ no caben en ningún tamaño del contrato, ENTONCES el sistema debe aplicar la regla que fije D2
  (recomendada: paquetes de 6 si el contrato tiene el de 6; si no, paquetes del mayor). Test con [6, 8] y 14 m³, y con
  [8] y 14 m³.
- **R8.** El orden de las fuentes de tamaño debe ser: tabla del contrato > `contenedor_m3` de IA3 > m³ en la
  descripción de la línea casada > estándar (R1–R2). Un tamaño único se trata como lista de uno.
- **R9.** SI el tamaño elegido no es el que dice la descripción de la línea casada (cuando esta trae m³), ENTONCES el
  sistema debe dejar `residuos_tamano_distinto_de_casada=<elegido>/<casada>` y mandar la línea a revisión, sin
  cambiar la línea casada ni su precio.

## A.3 · Lo que no cambia

- **R10.** Las prioridades de F-036 R22 no cambian: contenedores explícitos > volumen > resta llevadas − retiradas;
  sin volumen ni resta, `residuos_sin_volumen_m3` y revisión; `residuos_volumen_implausible` por encima de 16 m³.
  Los tests de `test_f036_r22_contenedores_prioridades.py` siguen en verde (salvo los que fijaban el 6 por defecto,
  que se reescriben a R1–R3 y se declaran en el informe).
- **R11.** Una línea que no es de residuos debe valorarse igual que hoy (test de no regresión con hormigón).

## A.4 · IA3 — sv5 `config/prompts.yaml` (`valuation_residuos`)

- **R12.** El prompt `valuation_residuos` debe describir la regla de R1, R2, R6 y R7 y no debe contener «6 m3 por
  defecto», «ESTANDAR» referido al 6 ni «ante cualquier duda» referido al tamaño. Test sobre el YAML real.
- **R13.** El prompt debe pedir `contenedor_m3` = null CUANDO ni la tabla ni el texto del contrato dan el tamaño del
  contenedor elegido, y decir que en ese caso el tamaño lo fija otro servicio. Test sobre el YAML real.
- **R14.** El prompt debe pedir que, con varios tamaños del mismo tipo, IA3 case la línea del tamaño de R6/R7.
- **R15.** Los tests de `test_f036_r22_prompt_residuos_orden.py` y `test_f036_r16_prompt_residuos_sinteticas.py`
  deben seguir en verde sin cambiar sus aserciones.
- **R16.** `config/prompts/svc5_prompt_valuation_es.yaml` (histórico, no cargado) debe dejar de decir «el por
  defecto» para el tamaño (D1); test de texto.

## B.1 · Reconocer el capítulo de residuos — comun `ruesma_comun.sigrid.partidas`

- **R17.** El sistema debe ofrecer `candidatas_residuos(lista) -> tuple[PartidaObra, ...]`: las hojas de la obra con
  algún ANTECESOR (no la propia hoja) cuyo texto, sin tildes ni mayúsculas, contiene «GESTION» y una palabra que
  empieza por «RESIDUO» (no «RESIDUAL»), leídas de `descripcion_agregada`. Tests con las rutas medidas: 0686 «GESTIÓN
  RESIDUOS (SEGÚN EGRC)», 0694 «PLAN DE GESTIÓN DE RESIDUOS», 0711 «INSTALACION SANEAMIENTO RESIDUAL» (no).
- **R18.** `candidatas_residuos` debe excluir las hojas de ajuste (texto que empieza por «AJUSTE»: 32.99, 23.03).
- **R19.** `candidatas_residuos` no debe elegir: devuelve todas, en el orden de la lista; lista `None` o sin hojas ⇒
  tupla vacía. No cambia `casar_partida`, `resolver_partida_obra` ni la regla H1 de F-049.

## B.2 · Asignar la partida en sv6 — `application/services/partida_residuos.py`

- **R20.** CUANDO una línea `from_albaran` de familia efectiva `residuos` (la misma `familia_efectiva` del builder)
  llega sin partida leída (vacía, no `ALM`), el sistema debe buscarle partida entre `candidatas_residuos` de su obra
  ANTES de la valoración directa, de IA4 y del build (después de la normalización de F-076).
- **R21.** CUANDO hay exactamente 1 candidata, el sistema debe usarla sin llamar a la IA.
- **R22.** CUANDO hay 2 o más, el sistema debe pedir a sv5 que elija por el significado de la descripción de la línea
  (y su LER) entre las candidatas (D3); la respuesta solo vale si es el `codigo` de una candidata.
- **R23.** CUANDO se asigna una partida, el sistema debe valorar la línea con ese código como partida (en la copia del
  sobre, como F-076) y dejar el motivo `partida_residuos:<cod>` (sin revisión, D4); `codigo_partida_albaran`
  persistido vuelve a la lectura (vacía): leída ≠ decisión.
- **R24.** Las sintéticas de esa línea (incremento LER) deben heredar la partida asignada, como heredan hoy la leída.
- **R25.** SI la obra no tiene capítulo de residuos (0 candidatas), ENTONCES la línea debe ir a revisión con
  `partida_residuos_sin_capitulo` y sin `partida_action = almacen_sin_partida` (D5).
- **R26.** SI la IA no elige ninguna, elige un código que no es candidata o falla, ENTONCES la línea debe ir a revisión
  con `partida_residuos_sin_candidata` (o `partida_residuos_ia_fallo`) y las candidatas en el motivo (hasta 5 códigos).
- **R27.** SI no hay lista de la obra (sin sigrid-api, obra vacía, consulta fallida o truncada), ENTONCES la línea debe
  ir a revisión con `partida_residuos_sin_lista`, nunca a almacén; la valoración no falla.
- **R28.** Una línea de residuos CON partida leída, una línea `ALM` y las de otra familia deben valorarse como hoy.
- **R29.** DONDE `PARTIDA_RESIDUOS_ENABLED=false` (sv6, defecto `true`), el sistema debe valorar como antes de F-111
  en la parte B (vuelta atrás sin imagen). La parte A no tiene interruptor.
- **R30.** El sistema debe leer la lista de la obra una sola vez por valoración (la caché de F-076) y la obra una sola
  vez (la misma lectura que `_normalizar_partidas`).

## B.3 · Elegir entre candidatas — sv5 `POST /v1/albaranes/partida-residuos`

- **R31.** sv5 debe exponer `POST /v1/albaranes/partida-residuos` con `{document_id, lineas: [{line_ref,
  descripcion, codigo_ler}], candidatas: [{codigo, descripcion, descripcion_agregada}]}` y devolver
  `{elecciones: [{line_ref, codigo | null, confianza_pct, razon_corta}]}`, una por línea.
- **R32.** El prompt `partida_residuos_es` debe decir que elige POR SIGNIFICADO solo entre las candidatas, que
  `codigo = null` si ninguna encaja o si dos encajan igual, y que nunca inventa códigos.
- **R33.** El endpoint usa el proveedor y modelo de IA4 (`seleccionar_ia4`); sin proveedor, 503, y sv6 aplica R26.
- **R34.** sv6 debe mandar en UNA llamada todas las líneas del documento con ≥ 2 candidatas.

## C · Trazas y rastro

- **R35.** Los motivos nuevos deben tener su constante en el módulo que los escribe y un test que los congele
  (F-027 R22).
- **R36.** `docs/ARCHITECTURE.md` debe recoger la regla 3/6/9 y la partida de residuos (en la sección de dominio).
