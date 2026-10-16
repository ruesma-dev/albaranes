<!-- progress/spec_F-076.md -->
# F-076 · Normalizar partidas contra las de la obra · Spec v1 y PARADA 1 (2026-10-16)

Spec: `specs/F-076-normalizar-partidas/` (requirements 97/150, design 185/250, tasks T1–T20). Rama
`feature/F-076-normalizar-partidas`, worktree `../albaranes-F-076`, desde `dev` `148b1e9`. Sin código tocado.
`features.json`: F-076 `spec_ready`, rigor `critico`, prioridad 1, servicios comun, sv6, sv4.

## 1. Hipótesis del líder: CONFIRMADA

- **Lista de la obra** (sigrid-api `sql/read`, la consulta del combo de sv4 + `tip 42`, solo lectura): la 0678 tiene
  la hoja `CI.4.18` (imputable) y no `CI.04.18`.
- **Previa real**: el humano cambió a mano la partida a `CI.4.18` en las 5 filas de los dos albaranes de T51
  (`532affd4`, `2b9029f6`; filas guardadas, 2026-10-16 08:22) y los reaprobó: `albaran_altas_sigrid` pasó de
  `no_admitido` (`partida_no_encontrada` ×2 y ×3) a **`simulado`**, petición con `partida = CI.4.18`.
  ⇒ **Los dos albaranes de T51 ya están corregidos: no hay nada que hacer con ellos.**
- **Cómo compara sigrid-api** (`sigrid-api/application/use_cases/create_albaran_compra_use_case.py`, `_clave` y
  `resolver_partida`): `strip().casefold()` entre las IMPUTABLES de la obra (`tip 1`, `tipdes 0`, `tipvis 0/1`).
  Mayúsculas y espacios de cola ya no fallan; los ceros a la izquierda sí.

## 2. Medición (solo lectura, 2026-10-16)

### 2.1 Método
PostgreSQL `albaranes` (Azure) con `default_transaction_read_only=on` comprobado; sigrid-api `sql/read` por obra.
Universo: **todas** las líneas valoradas con partida final o leída (no hizo falta muestrear: producción tiene
50 documentos, 105 líneas valoradas, 7 obras con partida; la lista más lenta, 0678, 4,7 s). Script fuera de git
(scratchpad de la sesión); el versionado lo hace T15. Reglas candidatas probadas contra las hojas de la obra:
mayúsculas+espacios; solo ceros a la izquierda; solo separadores; la clave completa de F-049 R1.

### 2.2 Resultados (74 líneas con partida final, 29 documentos, todos activos)

| Partida final frente a su obra | Líneas |
|---|---:|
| Existe tal cual (hoja e imputable) | 38 |
| Existe pero NO es hoja ni imputable (`03.02`, obra 0720 ⇒ sigrid-api daría `partida_no_imputable`) | 1 |
| **No existe** | **35** (16 documentos) |

De las 35 que no existen, candidatas únicas entre las hojas de la obra por regla:

| Regla | 1 candidata | 0 | >1 (ambigua) |
|---|---:|---:|---:|
| Mayúsculas + espacios | 0 | 35 | 0 |
| Separadores (`.`, `-`, espacio…) | 0 | 35 | 0 |
| **Ceros a la izquierda en segmentos numéricos** | **29** | 6 | 0 |
| Clave completa F-049 R1 (todo lo anterior) | 29 | 6 | 0 |

- Las 29: `CI.04.18` ⇒ `CI.4.18` (27, en 0694, 0711, 0719, 0720, 0723) y `CI.03A.02` ⇒ `CI.03A.2` (2, 0720). Por la
  lectura (`codigo_partida_albaran`): 39 no existen y 33 se arreglan; la diferencia son las 5 de la 0678 y una
  `almacen_elegido`, cuya final ya corrigió el humano a mano, menos 2 filas `manual` sin lectura.
- Las 6 sin candidata (a revisión con F-076; tampoco las arreglaría nada «seguro»): 0694 `CI.14.18` ×2,
  `CI.14.12`, `01.03A.02`, `CI.04.01.08`; 0724 `CI.03.A`.
- En las pruebas locales de T26 (`progress/pruebas_F-053_T26_T27c.md`) las que fallaron eran de otra clase
  (`RJ.14.01.02.02`, `36.01`, `11.10.02.01`: prefijo de capítulo perdido o partida inexistente): eso es F-049, no
  normalización.
- Contrato: en la 0723 dos líneas `CI.04.18` salieron «Nueva» con la línea de contrato en `CI.4.18` al lado; con
  F-076 casarían con ella («Contrato»).

### 2.3 Lo existente afectado (para T19)

| Estado | Documentos | Líneas «no existe» | Qué se propone |
|---|---:|---:|---|
| Pendientes (no aprobados) | 12: `2792cf3b`, `53337da7`, `54b82479`, `dedf011a` (0694); `41ab0dc1` (0711); `09643c2b`, `355449d9`, `89e463a7`, `bef66bce`, `f96c6dbe` (0720); `ca609aee` (0723); `25c5d647` (0724) | 23 (17 normalizables, 6 sin candidata) | El humano los **revalora desde sv4** tras desplegar. `355449d9` tiene 6 filas guardadas: revalorar las pierde (F-058) ⇒ corregir a mano en la ficha |
| Aprobados antes de DESDE | 4: `0bd5d331`, `43fb8c2d`, `48d2e083`, `9cee5eff` | 12 (todas `CI.4.18`) | Nada: sv9 los ignora (R6 de F-053). Si se desaprueban para reaprobar, revalorar antes |
| T51 | 2 | 0 | Ya corregidos a mano y `simulado` |

## 3. Propuesta

**Dónde**: en **sv6, al valorar**, antes de sus reglas (y antes de IA4 y de la rama `no_contract`). Motivos:
(1) `codigo_partida_final` es la decisión que enseña la ficha y que manda sv9: si se normaliza ahí, lo mostrado es lo
enviado; (2) el casado con la línea de contrato mejora (§2.2); (3) cada revaloración lo reaplica, también tras
cambiar la obra en sv4; (4) no reescribe `codigo_imputacion` (lo impreso, regla 6). Coste: sv6 pasa a leer de
sigrid-api (secreto y variables nuevas en `ca-sv6-valorador`, script para el humano) y lee `obra_codigo` del merge.
Descartadas: sv9 (rompe «lo mostrado es lo enviado»), sv3 (no se reaplica al revalorar; es lo que hará F-049 en
sv2), ambos (dos sitios para una regla).

**Regla** (comun, función pura): exacta o normalizada con la clave de F-049 R1 contra las **hojas** de la obra ⇒
el código tal como figura en la lista; si la clave coincide con un código **no hoja** de la obra, no se normaliza;
0 candidatas, >1 o compuesta ⇒ no se toca, motivo de línea (`partida_fuera_de_lista` / `partida_ambigua_en_obra`) y a
revisión (no bloquea aprobar). Normalizada ⇒ sin revisión, rastro `partida_normalizada:CI.04.18>CI.4.18`; la
columna `codigo_partida_albaran` conserva la leída.

**Lista y caché**: subconjunto ya APROBADO de F-049 portado a `ruesma_comun.sigrid.partidas` (SQL de sv4 +
`emp = 1`, hojas, clave, `casar_partida`), con `leer_partidas_obra` adaptado a la canonización de F-070. Caché por
obra en la réplica: TTL 6 h, 64 obras, fallo recordado 300 s (los valores que el humano aprobó para F-049, D2).
sv4 deja su copia y lee de comun. **Sigrid caído**: se valora como hoy, WARNING y motivo de cabecera
`partidas_obra_no_disponibles` sin revisión: nunca bloquea la valoración.

**Ficheros y orden** (detalle en design §3): comun (T1–T4) → sv4 (T5) → sv6 (T6–T11) → test de contrato en sv9
(T12) → infra (T13) → docs y azure-apps (T14) → script de medición (T15) → mutación (T16) → `init.sh` (T17) →
MANUAL despliegue `set_partidas_sv6.ps1` → sv6 → sv4 (T18) → MANUAL revalorar y medir (T19) → `init.sh` (T20).

**Riesgos**: cambian valoraciones al revalorar (más «Contrato», 6 líneas a revisión); ruta sensible de sv6
(«aviso») sin evals de pago; caché de hasta 6 h; conflicto add/add con F-049 al retomarla (su `partidas.py` es
superconjunto); sv4 cambia en dos cosas (empresa 1, lista truncada ⇒ `ok=false`).

**Fuera**: elegir partida por parecido/sufijo y repartir compuestas (F-049); la lista en el prompt (F-049);
normalizar en sv9/sv3; validar en servidor lo que teclea el revisor; que lo manual sobreviva a revalorar (F-058);
migración por script.

## 4. Preguntas al humano (opción por defecto en negrita)

- **P1 · Dónde.** a) **solo sv6 al valorar**; b) sv9 antes del alta; c) sv3 al persistir; d) sv6 + sv9 de red.
- **P2 · Reglas.** a) **la clave completa de F-049 R1** (ceros, mayúsculas, separadores; hoy solo actúan los
  ceros), con la guarda de no hoja; b) solo ceros a la izquierda.
- **P3 · 0 / >1 candidatas.** **No tocar; motivo de línea `partida_fuera_de_lista` o `partida_ambigua_en_obra` y
  línea a revisión, sin bloquear aprobar.** Normalizada: **sin revisión, solo rastro**. ¿Conforme?
- **P4 · Sigrid caído.** **Valorar como hoy + motivo de cabecera sin revisión; caché 6 h / 64 obras / fallo 300 s**.
- **P5 · Lo existente.** a) **nada automático: el humano revalora los 12 pendientes de §2.3 (y `355449d9` a mano);
  aprobados y T51, nada**; b) script con `--aplicar` que corrija `codigo_partida_final` (escritura en producción:
  solo con tu autorización expresa).
- **P6 · F-049.** a) **portar ahora el subconjunto aprobado a `dev` y que F-049 rebase**; b) esperar a F-049;
  c) absorber F-076 en F-049.
- **P7 · sv4.** **Aceptar** que el combo filtre la empresa 1 (0517 y 0581 dejan de mezclar dos obras) y que una lista
  truncada dé `ok=false` (los dos los aprobaste ya para F-049, D-a/D4).
- **P8 · Evals.** **Sin evals de pago** (la exigencia de la ruta sensible es «aviso»; los tests fijan la regla);
  ¿o pasada con LLM real antes de desplegar?
- **P9 · Rigor y servicios.** **`critico`; comun, sv6 y sv4 (refactor); sv9 solo un test.**
- **P10 · Infra.** **`infra/set_partidas_sv6.ps1` lo lanzas tú antes de desplegar sv6**; interruptor
  `PARTIDAS_OBRA_NORMALIZAR_ENABLED` (true) para volver atrás sin redesplegar.
- **P11 · Rastro.** **`codigo_partida_albaran` de la valoración conserva la leída** (`CI.04.18`) y la final la de la
  lista; el motivo `partida_normalizada:…` se ve en la fila como los demás motivos (etiqueta legible: F-059).

## 5. Interacción con otras features (para el líder)

- **F-049** (`blocked`, `../albaranes-F-049`): mismo `partidas.py`; al retomarla, rebasar y quedarse su versión
  conservando `resolver_partida_obra`, `CachePartidasObra` y la guarda de no hoja (recomendada también para su
  sello); su comun pasa a 0.9.0. Su descripción en `features.json` no se ha tocado.
- **F-053**: sv9 sin código; el flujo `no_admitido` → editar → reaprobar sigue igual (lo usó el humano en T51).
- **F-065**: el combo reconocerá la final (código de la lista). **F-058**: revalorar pierde lo manual (P5).
- **F-075** (`../albaranes-F-075`, spec aprobada, sin código): su `ValoracionDirectaBuilder` copia la partida «tal
  cual»; con F-076 recibe el sobre ya normalizado (el paso va antes de la rama `no_contract`) y debe llamar a
  `NormalizadorPartidas.anotar` con sus líneas. Quien fusione segundo lo integra.
- **F-067**: sin rama ni código; sin solape. F-071–F-074: ninguna toca sv6, comun `sigrid` ni el cliente de sv4.
- Hallazgo aparte: la 0720 tiene una línea con final `03.02`, que existe pero es capítulo (no imputable): F-076 la
  manda a revisión; sigrid-api la rechazaría con `partida_no_imputable`.

## 6. PARADA 1: APROBADA (2026-10-16)

El humano aprueba la propuesta con las opciones por defecto de P1 a P11 («si. apruebo»). La implementación espera turno: máximo una feature `in_progress` (ahora F-072).
