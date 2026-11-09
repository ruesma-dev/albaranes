<!-- progress/spec_F-117.md -->
# F-117 · Spec: partida equivalente en la obra

Spec en `specs/F-117-partida-equivalente-en-obra/` (requirements 83 líneas, design 163, tasks 11). Rama
`feature/F-117-partida-equivalente-en-obra`, worktree `../albaranes-F-117`. Estado `spec_ready`. Rigor `critico`.
Servicios: **comun** (0.13.0 ⇒ 0.14.0, función pura) y **sv6** (normalizador de F-076). Sin sv4, sv5, sv9, DDL ni IA.

## Propuesta en una frase

Cuando la partida leída queda `fuera_de_lista`, comun propone las hojas equivalentes con dos reglas cerradas
(**letra** pegada al número solo en la hoja: `CI.03.08` ≡ `CI.03A.8`; **sufijo** de ≥ 3 segmentos: `04.01.07` ≡
`02.04.01.07`). Una sola ⇒ sv6 valora con ella, motivo `partida_equivalente:CI.03.08>CI.03A.8` y revisión no
bloqueante. Varias ⇒ como hoy más `partida_equivalente_ambigua:<cods>`. Ninguna ⇒ como hoy. Nunca almacén, nunca un
código que no sea hoja.

## Medición (producción, solo lectura, 2026-11-05)

Scripts versionados en `scripts/medicion_F-117/` (`run.ps1 <script> [-Repo <checkout con infra local y .venv>]`).
PG con `default_transaction_read_only=on` (comprobado `on`), Sigrid solo `POST /api/sql/read` con
`SQL_PARTIDAS_POR_OBRA`, ninguna respuesta truncada. Claves de Key Vault solo en variables del proceso, borradas en
`finally`. Salida completa en el scratchpad de la sesión (no versionada).

| Qué | Líneas |
|---|---|
| Con `partida_fuera_de_lista` (documentos activos; 21 documentos) | 31 |
| … que hoy ya casarían (valoradas antes de F-098; se arreglan revalorando) | 5 |
| … siguen fuera de lista | **26** |
| Regla de la letra, única (0719 `CI.03.08` ⇒ `CI.03A.8`, el caso de la petición) | 1 |
| Regla del sufijo, única (0719 `04.01.07` ⇒ `02.04.01.07`; el revisor puso a mano esa misma en las 5) | 5 |
| La letra al revés (0694 `01.03A.02` ⇒ `01.03.02`): **falso positivo**, por eso no se aplica | (1) |
| La lectura es un capítulo (0692 `CD.02`, 18 hojas; el revisor eligió `CD2.07`, que no cuelga de él) | 8 |
| Sin equivalente | 12 |
| Altas `no_admitido` por `partida_no_encontrada` (5 de `CD.02` + 1 de `CI.03.08`) | 6 ⇒ F-117 resuelve 1 |

Ambigüedad: en las 19 obras con albaranes en 120 días, 16 tienen hojas con letra y 33 de 261 esqueletos tienen 2 o
más hojas (0459: `CI.03A.n` y `CI.03P.n`, n = 1…12) ⇒ con la regla, revisión con candidatas, nunca adivinar. Hoy
ninguna lectura fuera de lista cae en ese caso. 17 esqueletos coinciden con una hoja sin letra: ahí gana la
normalización de F-076 y F-117 ni se consulta.

Hallazgo útil para el humano: la línea hermana de 0719 `CI.03.18` («grua pk 44») la corrigió un revisor a
`CI.03A.8`; la de `CI.03.08` se aprobó sin corregir. La de `CI.03.08` puede corregirse ya a mano en sv4 sin esperar.

## Decisiones para el humano (PARADA 1) — detalle en `design.md` §9

- **D1 · Levantar H1 de F-049** («nunca por sufijo ni parecido»): (a) **recomendada**, excepción acotada a las reglas
  de D2, en función aparte que propone y manda a revisión; (b) no, y F-117 se cancela.
- **D2 · Reglas**: (a) **recomendada**, letra (solo en la hoja) + sufijo ≥ 3 segmentos, única: 6/6 aciertos medidos,
  0 falsos positivos; (b) solo la letra (1 línea); (c) letra en ambos sentidos: descartada (1 falso positivo).
- **D3 · Única ⇒ ¿revisión?**: (a) **recomendada**, sí, no bloqueante (la partida va puesta); (b) sin revisión.
- **D4 · Varias**: (a) **recomendada**, revisión con candidatas en el motivo, sin IA; (b) IA de sv5 (otra feature).
- **D5 · Motivo**: (a) **recomendada**, `partida_equivalente:<leída>><cod>` (separador de F-076); (b) `->`.
- **D6 · sv4**: (a) **recomendada**, nada nuevo (traza de F-036 y ⚠ de F-077 ya lo enseñan); (b) nota en el `title`.
- **D7 · Lo valorado**: (a) **recomendada**, tras desplegar el líder lista (T9) y el humano decide qué revalorar; (b)
  revaloración masiva (no la lanza un agente).
- **D8 · Fuera de alcance**: sv4 que impida aprobar con `partida_fuera_de_lista` (el humano eligió esta vía), la
  lectura-capítulo `CD.02` y los errores de lectura: (a) **recomendada**, fuera, y feature aparte para `CD.02` si se
  quiere; (b) meter `CD.02` con IA aquí (no lo habría acertado).
- **D9 · Interruptor**: (a) **recomendada**, `PARTIDA_EQUIVALENTE_ENABLED` en sv6, defecto `true`; (b) sin interruptor.

## Riesgos

Falso positivo del sufijo en obras con numeración repetida por fase (acotado por ≥ 3 segmentos, unicidad y revisión;
T9 lo mide). IA4 puede casar con contrato donde hoy no (efecto buscado). Fusión con F-100: una línea en `settings.py` y
`composition.py`. Despliegue (humano): comun 0.14.0 ⇒ sv6 solo.
