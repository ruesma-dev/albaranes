<!-- specs/F-076-normalizar-partidas/requirements.md -->
# F-076 · La partida se normaliza contra las de la obra · Requisitos (v1, 2026-10-16)

Servicios: **comun**, **sv6** (normaliza al valorar) y **sv4** (solo refactor: lee la lista de comun). sv9 sin código.
Rigor `critico` (lo que sv6 fija es lo que sv9 escribe en Sigrid). Decisiones abiertas P1–P11 en
`progress/spec_F-076.md` §4; aquí va la opción por defecto de cada una.

Origen: T51 de F-053 (2026-10-16). sigrid-api rechazó con `partida_no_encontrada` todas las líneas de dos albaranes de
la obra 0678: la IA leyó `CI.04.18` y la obra tiene `CI.4.18`. Medición en producción (spec §1): 35 de 74 líneas con
partida final no existen en su obra; **29 se arreglan quitando ceros a la izquierda**; mayúsculas, espacios y
separadores, 0; ninguna ambigua; 6 sin candidata.

Vocabulario: **lista** = partidas HOJA de la obra en Sigrid (`obrparpar`, empresa 1; la del combo de sv4);
**no hoja** = código de la obra que es padre de otro; **lectura** = partida que sv6 recibe del albarán
(`codigo_partida_albaran` del sobre de sv5, que sale de `codigo_imputacion`); **clave** = `normalizar_partida(x)`.

## A. comun · `ruesma_comun.sigrid.partidas` (subconjunto APROBADO de F-049, portado)

- R1. `normalizar_partida(codigo)` debe dar la clave de F-049 R1: NFKC, mayúsculas, todo lo no alfanumérico salvo
  `/` separa, sin segmentos vacíos, sin ceros a la izquierda en segmentos solo numéricos, unidos por `.`;
  `CI.04.18` ≡ `CI.4.18` ≡ `ci 4 18`; `CI.03A.02` ≡ `CI.03A.2`; vacío o `None` ⇒ `None`.
- R2. `ListaPartidasObra.desde_filas` debe dar las hojas con la semántica de hoy de sv4 (padre 0/nulo = sin padre;
  sin `cod` fuera; ruta de capítulos; orden por código) y, aparte, los códigos no hoja.
- R3. `leer_partidas_obra(leer, obra)` debe canonizar la obra con `canonizar_codigo_obra` (F-070) y, SI queda vacía,
  ENTONCES devolver `None` sin consultar; si no, lanzar UNA consulta (`SQL_PARTIDAS_POR_OBRA`: la de sv4 más
  `con_obr.emp = 1`) con `NO_TOLERA` y `MAX_FILAS_POR_PETICION`. Los errores del lector se propagan.
- R4. `casar_partida(lista, lectura, alm)` debe conservar la semántica de F-049 R5 (`exacta`, `normalizada`,
  `compuesta`, `alm`, `sin_partida`, `fuera_de_lista`, `ambigua`). Nunca por parecido, sufijo ni distancia.
- R5. `resolver_partida_obra(lista, lectura, alm)` debe devolver `ResolucionPartida(codigo, motivo, leida)`:
  - `exacta` / `normalizada` ⇒ `codigo` = el de la lista, tal como figura en ella;
  - SI la clave de la lectura coincide con la de algún código **no hoja** de la obra y la lectura no es exacta,
    ENTONCES `fuera_de_lista` (nunca se normaliza hacia otra fila del árbol: `03.02` capítulo ≠ `3.02` hoja);
  - `compuesta` ⇒ `fuera_de_lista` (Sigrid admite una partida por línea; el reparto es de F-049);
  - `fuera_de_lista` / `ambigua` ⇒ `codigo` = la lectura sin cambios;
  - `sin_partida` / `alm` ⇒ `no_aplica`, `codigo` = la lectura sin cambios.
- R6. `CachePartidasObra(lector, ttl_s, max_obras, ttl_fallo_s, reloj)` debe dar la lista de una obra:
  N peticiones de la misma obra dentro de `ttl_s` ⇒ UNA consulta; más de `max_obras` ⇒ fuera la menos usada;
  SI la consulta falla o trunca, ENTONCES la lista caducada si la hay o, si no, `None`, y el fallo se recuerda
  `ttl_fallo_s` sin reconsultar; nunca lanza.

## B. sv6 · normalizar antes de valorar

- R7. CUANDO sv6 recibe el sobre de sv5 (también al revalorar con `force`) y `PARTIDAS_OBRA_NORMALIZAR_ENABLED` es
  `true`, ANTES de IA4, de la rama `no_contract` y de las reglas deterministas debe leer `obra_codigo` del merge
  (solo lectura), pedir la lista a la caché y resolver con R5 la lectura de cada línea del albarán del sobre. Un
  sobre sin líneas con lectura no consulta sigrid-api.
- R8. CUANDO el motivo es `exacta` o `normalizada`, la partida con la que trabajan las reglas de sv6 debe ser la de
  la lista: casar con la línea de contrato de esa partida, crear la derivada con ella, heredarla a complementarias y
  sintéticas y fijarla como `codigo_partida_final`.
- R9. CUANDO el motivo es `normalizada`, la línea valorada debe llevar el motivo
  `partida_normalizada:<leída>><lista>` SIN marcar `review_required` por ello, y su `codigo_partida_albaran` debe
  conservar la leída (regla 6 de ARCHITECTURE: leída ≠ decisión).
- R10. SI el motivo es `fuera_de_lista` o `ambigua`, ENTONCES la partida no debe cambiar y la línea debe llevar
  `partida_fuera_de_lista` o `partida_ambigua_en_obra` con `review_required = true`, y la cabecera el mismo motivo.
- R11. SI no hay lista (sin configuración de sigrid-api, obra vacía, consulta fallida o truncada, obra con 0 hojas),
  ENTONCES sv6 debe valorar exactamente como hoy, dejar un WARNING con obra y causa y el motivo de cabecera
  `partidas_obra_no_disponibles` sin `review_required`. La valoración nunca falla por la lista.
- R12. DONDE `PARTIDAS_OBRA_NORMALIZAR_ENABLED=false`, sv6 no debe consultar sigrid-api ni cambiar nada.
- R13. Una línea con lectura vacía o igual a `ALM_CODIGO_PARTIDA` no debe tocarse (F-051 intacto: almacén).
- R14. El sobre persistido (`raw_ia_envelope_json`) debe ser el que se valoró; lo leído queda en el motivo de R9.

## C. sv4 · la lista desde comun (sin copia)

- R15. `/api/sigrid/partidas` debe devolver, para las mismas filas, los mismos `items` que hoy, construidos con
  comun (sin SQL ni cálculo de hojas propios en sv4). Cambios aceptados (P7): solo partidas de la empresa 1, y SI la
  lista llega truncada, ENTONCES `ok=false`.

## D. sv9 · sin código

- R16. sv9 debe seguir enviando como `partida` exactamente `codigo_partida_final` (test de contrato: una final
  normalizada por sv6 sale tal cual en la petición; vacía ⇒ sin clave de partida).

## E. Configuración, infra, documentación y no funcionales

- R17. sv6 debe leer `SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY`, `SIGRID_API_DATABASE`,
  `SIGRID_API_TIMEOUT_S`, `PARTIDAS_OBRA_NORMALIZAR_ENABLED` (true), `PARTIDAS_OBRA_TTL_S` (21600),
  `PARTIDAS_OBRA_MAX_OBRAS` (64) y `PARTIDAS_OBRA_FALLO_TTL_S` (300); sin URL o sin clave ⇒ R11, nunca un fallo.
- R18. El cliente de sv6 debe usar solo `POST /api/sql/read`, reintentar con tenacity los fallos transitorios y no
  registrar la clave ni el cuerpo de la respuesta.
- R19. `infra/set_partidas_sv6.ps1` debe añadir de forma idempotente a `ca-sv6-valorador` el secreto `sigrid-key`
  (referencia a Key Vault `SIGRID-API-FUNCTION-KEY`) y las variables de R17, y comprobarlas al final;
  `create_capps.ps1` debe llevar lo mismo en el bloque de sv6. Sin IDs reales en lo versionado.
- R20. `docs/ARCHITECTURE.md` (regla 22 y «Acceso a datos»: sv6 lee sigrid-api y `obra_codigo` del merge),
  `services/albaran-valoracion-persist/sv6.md` y `azure-apps/albaranes.md` deben reflejar el cambio en el mismo
  trabajo.
- R21. Los tests unitarios no deben tocar red ni BBDD. Cada R tiene test `test_f076_rN_*`.
- R22. `scripts/medir_f076_partidas.py` (sv6) debe abrir PostgreSQL en solo lectura y abortar si
  `SHOW transaction_read_only` no da `on`, leer sigrid-api con `NO_TOLERA`, tomar credenciales solo del entorno e
  imprimir solo recuentos (clase de R5 × aprobado/pendiente), nunca precios ni secretos.

**Fuera de alcance**: elegir partida por parecido, sufijo o prefijo (F-049, H1); repartir compuestas (F-049);
la lista en el prompt de IA2 (F-049); normalizar en sv9 o en sv3; validar en el servidor lo que teclea el revisor
(el combo de F-065 ya solo ofrece la lista); que lo manual sobreviva a revalorar (F-058); migrar valoraciones
existentes (P5: revalorar desde sv4, a mano).
