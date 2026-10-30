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
