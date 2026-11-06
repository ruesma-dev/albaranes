# Spec F-111 · informe del spec-author (2026-10-29/30)

Spec en `specs/F-111-residuos-contenedores-y-partida/` (requirements 107 líneas, design ~208, tasks 15 tareas).
Rama `feature/F-111-residuos-contenedores-y-partida`. No se ha lanzado `init.sh` ni ninguna suite (F-106 en campaña).
No se ha escrito en producción; no se ha cambiado el estado en `features.json`.

## 1. Qué propone (resumen)

- **A · Contenedores (sv6 + prompt de IA3).** Sin tamaños en el contrato: el menor de 3/6/9 en que caben los m³, 1
  contenedor; > 9 m³ ⇒ `ceil(m³/6)` de 6; precio de la línea casada (el general). Con tamaños: el menor del contrato
  en que caben. Motivo `residuos_tamano_estandar=<t>m3` sustituye a `residuos_tamano_defecto_6m3`. IA3 deja
  `contenedor_m3 = null` si el contrato no da el tamaño (el 6 de IA3 era lo que sv6 usaba en CTSU24/0524).
- **B · Partida (comun + sv6 + sv5).** comun reconoce el capítulo (`candidatas_residuos`: hojas con un antecesor
  «GESTION … RESIDUO», sin ajustes); sv6, tras normalizar (F-076) y antes de IA4, asigna la partida a las líneas de
  residuos sin lectura: 1 candidata ⇒ esa; ≥ 2 ⇒ IA en un endpoint nuevo de sv5 (`/v1/albaranes/partida-residuos`,
  modelo de IA4); sin capítulo/candidata/lista ⇒ revisión con motivo y sin `almacen_sin_partida`.

## 2. Medición en producción (solo lectura)

Método: PostgreSQL `albaranes` de Azure con `options=-c default_transaction_read_only=on`, comprobado `SHOW
transaction_read_only = on`; Sigrid solo por `POST /api/sql/read` de sigrid-api con `SQL_PARTIDAS_POR_OBRA` de comun
(ninguna respuesta `truncated`). Claves de Key Vault (`PG-PASSWORD`, `SIGRID-API-FUNCTION-KEY`) a variables del proceso,
borradas en `finally`, cargando `infra/00_vars.ps1` con su capa local. Scripts fuera del repo (scratchpad de la sesión:
`run.ps1`, `comun_ro.py`, `m1_residuos.py`, `m2_capitulos.py`). Para T13 basta repetirlos.

- **Contenedores:** 25 líneas de residuos valoradas, 11 por volumen (7 con 6 m³, 4 con 8 m³). Con la regla nueva
  **cambian 2 líneas en 2 documentos** (obra 0686, CTSU24/0524, contrato sin tamaño): 8 m³, de 2 × 6 a 1 × 9; −288 €
  en total. Una de ellas (139 €) está **aprobada**. Las 6 con tamaños en el contrato no cambian. Ninguna > 9 m³.
- **Sin partida:** 8 líneas de residuos sin partida final (todas `almacen_sin_partida`, sin lectura), 8 documentos
  (1 aprobado), obras 0686 (3), 0459, 0669, 0687, 0694, 0697.
- **Capítulo de residuos:** en las 17 obras con albaranes en 120 días existe un nodo «GESTIÓN DE RESIDUOS» (o
  «GESTION RESIDUOS (SEGÚN EGRC)», «PLAN DE GESTIÓN DE RESIDUOS»), nunca raíz: subcapítulo de CD en nivel 1 (`32`,
  `19`, `27`…) o 2 (`01.21`, `P4.35`, `102.08`). Lo normal es 1 hoja (`32.01`, `19.01`, `01.21.01`) y a veces una de
  ajuste (`32.99`). Varias candidatas en 0459 (18), 0669 (2 iguales), 0678 y 0693 (por fase), 0686 (32.01 y 37.06.01),
  0696, 0720, 0723. Detalle en `design.md` §2.

## 3. Decisiones abiertas para el humano (PARADA 1, `design.md` §10)

D1 corregir también el prompt histórico `svc5_prompt_valuation_es.yaml` · D2 m³ que no caben en ningún tamaño del
contrato · D3 quién elige con ≥ 2 candidatas (IA en sv5, texto, revisión) · D4 si la partida asignada va a revisión ·
D5 «nunca a almacén»: solo revisión o además bloqueo en sv4/sv9 · D6 textos en sv4 · D7 qué hacer con lo ya valorado
y el aprobado (ya en Sigrid con 278 €) · D8 caso nuevo en el banco de evals · D9 orden con F-100 (mismos ficheros de
sv6 y sv5) · D10 patrón del capítulo fijo o por entorno. Recomendación en todas: (a).

## 4. Choques

- **F-106**: sin ficheros en común en sv6 (F-106 toca repositorio, ORM y DDL); comun 0.10.0 ⇒ F-111 0.11.0.
- **F-100**: comparte `run_valuation_pipeline.py`, `composition.py`, `settings.py`, `valuation_builder.py`,
  `prompts.yaml` (`valuation_residuos`) y `app.py` de sv5. Lo resuelve D9.
- Observación: F-036 R22 y F-051 siguen vigentes; algunos tests de F-036 que fijaban el 6 por defecto se reescriben
  (R10, declarado).

## 5. Parte C · medición (líder, producción, solo lectura, 2026-11-05)

Las 8 líneas de residuos sin partida de §2, con las partidas (`codigo_partida`) de las líneas de contrato de su sobre.
Script de lectura en el scratchpad del líder (no versionado; mismo método de solo lectura que §2).

| Obra (docs) | Partidas del contrato | En capítulo residuos | Resultado esperado con la parte C |
|---|---|---|---|
| 0686 (3) | 32.01 (120 líneas), CI.03A.7 | 32.01 | 32.01 sin IA (hoy: capítulo con 2 ⇒ IA) |
| 0669 (1) | 31.01, 102.08.01, CI.03A.7 | 31.01 y 102.08.01 | IA entre esas 2 |
| 0694 (1), 0697 (1) | solo CI.03A.7 (MAQUINARIA AJENA › CONTENEDORES) | no | CI.03A.7 (paso 2) |
| 0459 (1), 0687 (1) | sin partidas | — | capítulo (0459: 19 candidatas ⇒ IA; 0687: 1 ⇒ 19.01) |

## 6. Parte C · spec (spec-author, 2026-11-06)

Petición del humano: «que mire primero en las líneas del contrato si tiene partida; si es de gestión de residuos que
coja esa, y si no que busque». PARADA 1 cerrada el 2026-11-05/06: D1=b (vale una partida del contrato fuera del
capítulo, p. ej. `CI.03A.7`), D2=a (con varias, la IA elige SOLO entre esas), D3=a.

- **Regla (sv6 `partida_residuos.py`, solo):** partidas del contrato = `codigo_partida` distintos de
  `lineas_contrato` casados con una hoja de la obra (`resolver_partida_obra`, exacta/normalizada, sin cod repetido).
  Paso 1: las que son candidatas del capítulo de residuos. Paso 2: si ninguna lo es, todas las del contrato. Paso 3:
  si el contrato no aporta ninguna, la parte B tal cual. En cada paso: 1 ⇒ esa sin IA; ≥ 2 ⇒ IA solo entre esas.
  Mismo interruptor `PARTIDA_RESIDUOS_ENABLED`; sin lista ⇒ `partida_residuos_sin_lista` (nunca sin validar).
- **Motivos nuevos (sin revisión):** `partida_residuos_contrato:<cod>` y `partida_residuos_contrato_hoja:<cod>`; el
  paso 3 sigue con `partida_residuos:<cod>`. Revisión con los motivos de B y los códigos del conjunto del paso.
- **Spec:** R37–R48, `design.md` §13 (§10 compactado: decisiones de A/B ya cerradas), T15–T21; T13 (MANUAL) al final
  con los resultados esperados de §5. No cambian pipeline, composición, settings, matcher, builder, comun ni DDL.
- **Abierto para el humano:** D-C1 (frase del prompt de sv5: (a) cambiarla, redespliegue de sv5; (b) no tocar sv5) e
  interpretaciones (i)–(iii) de `design.md` §13, copiadas en `progress/current.md`.
- No se ha lanzado ninguna suite ni escrito en producción (spec documental).

## 7. Parte C · decisiones del humano y enmienda (2026-11-06)

Textual: «dc1 a, interpretaciones, a que busque en el capitulo por semantica (IA), ok lo demas». Spec aceptada con:

- **D-C1 = (a):** se cambia la frase de candidatas del prompt `partida_residuos_es` de sv5 (R48, T18). Despliegue:
  **sv5 y sv6** (comun sin cambios).
- **(i) CAMBIA:** si en el paso 1 o 2 la IA no elige, elige fuera del conjunto o falla, la línea NO va a revisión: cae
  al paso 3 (capítulo de gestión de residuos; con varias candidatas, IA por semántica como hoy) y deja, sin revisión,
  `partida_residuos_contrato_sin_eleccion:<cods>`. Solo va a revisión si también falla el paso 3. Como mucho dos
  llamadas a la IA por documento. Enmendados R41, R43, R46, `design.md` §13 (`_resolver` extraído, campo `intento`
  en `ResultadoPartidaResiduos`, `anotar` lo escribe en la línea), T15, T17, T20 y T13.
- **(ii) y (iii) aceptadas** tal cual; la excepción a F-051 (R47, ARCHITECTURE), aceptada.
- F-111 queda `in_progress` lista para el implementer (T15–T21; T13 manual al final). F-117 no se toca.

