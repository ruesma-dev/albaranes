# F-117 · Requisitos (EARS)

Petición del humano (2026-11-05): «Que la valoración proponga sola la equivalente en la obra cuando la partida del
albarán no exista». Servicios: **comun** (la regla de equivalencia, pura) y **sv6** (aplicarla al valorar, dentro de
la normalización de F-076). Sin sv4, sv5, sv9, DDL ni colas. Medición y decisiones D1–D9: `design.md` §2 y §9 y
`progress/spec_F-117.md`. Los requisitos marcados *(D2)* dependen de que el humano elija D2 = (a).

Notación:
- «lectura» = `codigo_partida_albaran` de una línea del sobre de sv5; «lista» = `ListaPartidasObra` de su obra.
- «fuera de lista» = `resolver_partida_obra(lista, lectura, alm).motivo == "fuera_de_lista"` (incluye la guarda de no
  hoja de F-076).
- «segmentos» = los de `normalizar_partida` (mayúsculas, separadores, sin ceros a la izquierda en los numéricos).
- «segmento con letra» = segmento de dígitos seguido de letras (`03A`, `12B`); su «número» son los dígitos sin ceros
  a la izquierda (`03A` ⇒ `3`). `P4`, `PJ` o `CD2` no son segmentos con letra (empiezan por letra).
- «forma de una hoja» = su cod o su código completo (F-098), cualquiera de los dos.

## A · La regla de equivalencia — comun `ruesma_comun/sigrid/partidas.py`

- **R1.** El sistema debe ofrecer `equivalentes_partida(lista, lectura, alm) -> tuple[str, ...]`: los cods de las
  hojas equivalentes a una lectura fuera de lista, sin duplicados y en el orden de `lista.hojas`.
- **R2.** (Regla de la letra) CUANDO la lectura no tiene ningún segmento con letra y una forma de una hoja tiene al
  menos uno, y al cambiar cada segmento con letra de la hoja por su número sus segmentos son los de la lectura, el
  sistema debe darla por equivalente. Test: `CI.03.08` con las hojas `CI.03A.8`, `CI.1.8`, `CI.2.8`, `CI.4.8` ⇒
  `("CI.03A.8",)`; `CI.3.8` y `CI.03.008` ⇒ lo mismo.
- **R3.** La regla de la letra no debe aplicarse al revés: SI la lectura tiene un segmento con letra (`01.03A.02`),
  ENTONCES no debe ofrecer por esa regla una hoja sin letra (`01.03.02`) (falso positivo medido, `design.md` §2).
- **R4.** *(D2)* (Regla del sufijo) CUANDO la lectura tiene 3 o más segmentos y los segmentos de una forma de una hoja
  son más y terminan, segmento a segmento, en los de la lectura, el sistema debe darla por equivalente. Test:
  `04.01.07` con la hoja `02.04.01.07` ⇒ `("02.04.01.07",)`; `14.01.07` no es sufijo de `4.01.07` ni al revés.
- **R5.** *(D2)* SI la lectura tiene menos de 3 segmentos, ENTONCES la regla del sufijo no debe aplicarse (`01.07` con
  la hoja `02.01.07` ⇒ `()`).
- **R6.** Dos formas de la misma hoja, o dos reglas que lleguen a la misma hoja, deben contar una sola vez; dos hojas
  distintas con el mismo cod cuentan un cod.
- **R7.** SI la lectura no está fuera de lista (vacía, `alm`, exacta, normalizada, completa o ambigua) o es compuesta
  (`/`), ENTONCES el sistema debe devolver `()`.
- **R8.** SI la clave de la lectura es la de un código NO hoja de la obra (su cod o su código completo, como la guarda
  de F-076: `CD.02` capítulo de 0692), ENTONCES el sistema debe devolver `()`: un capítulo no se cambia por una hoja.
- **R9.** Ninguna regla debe comparar por distancia, por prefijo ni por descripción: solo R2 y R4.
- **R10.** `casar_partida`, `resolver_partida_obra`, `normalizar_partida`, `misma_partida` y `mostrar_partida` no
  deben cambiar de comportamiento: los tests de F-049/F-076/F-098 de comun pasan sin tocarlos.
- **R11.** La docstring del módulo debe dejar escrito que `equivalentes_partida` es la excepción a H1 de F-049 que el
  humano aprobó el 2026-11-05 (D1), con sus reglas, y que lo demás del módulo sigue sin elegir.
- **R12.** comun debe subir de 0.13.0 a 0.14.0 (`pyproject.toml` y `ruesma_comun/__init__.py`) y exportar
  `equivalentes_partida` desde `ruesma_comun.sigrid`.

## B · Aplicarla al valorar — sv6 `application/services/normalizador_partidas.py`

- **R13.** CUANDO `NormalizadorPartidas.normalizar` resuelve una lectura fuera de lista con exactamente UNA
  equivalente, el sistema debe valorar con el cod de esa hoja: la copia del sobre lo lleva en
  `codigo_partida_albaran`, como F-076 hace con la normalizada (IA4, valoración directa y builder lo ven igual).
- **R14.** CUANDO `anotar` recibe esa línea, el sistema debe: devolver a `codigo_partida_albaran` la lectura (leída ≠
  decisión); añadir `partida_equivalente:<leída>><cod>` (leída sin espacios exteriores); NO añadir
  `partida_fuera_de_lista`.
- **R15.** *(D3 = a)* CUANDO una línea lleva `partida_equivalente:…`, el sistema debe marcar `review_required` en la
  línea y en la cabecera, que lleva el mismo motivo y `at_least_one_line_requires_review`. No bloquea aprobar.
- **R16.** CUANDO hay DOS o más equivalentes, el sistema debe dejar el sobre sin tocar en esa línea, poner
  `partida_fuera_de_lista` y revisión como hoy y, además, `partida_equivalente_ambigua:<c1>,<c2>…` con a lo sumo 5
  cods (si hay más, `,+N`). Test: `CI.03.08` con `CI.03A.8` y `CI.03P.8` (como en la obra 0459).
- **R17.** CUANDO no hay ninguna equivalente, el sistema debe comportarse exactamente como hoy.
- **R18.** El sistema nunca debe poner por esta vía una partida vacía, la de almacén ni un código que no sea el cod de
  una hoja de la lista. Test: el cod aplicado ∈ `lista.codigos`.
- **R19.** DONDE `PARTIDA_EQUIVALENTE_ENABLED=false` (sv6, defecto `true`), el sistema debe valorar exactamente como
  hoy: mismos registros, mismos motivos, sin llamar a `equivalentes_partida`.
- **R20.** MIENTRAS `PARTIDAS_OBRA_NORMALIZAR_ENABLED=false` o no haya lista (`partidas_obra_no_disponibles`), el
  sistema no debe buscar equivalentes (necesitan la lista de F-076).
- **R21.** `anotar` aplicado dos veces no debe duplicar motivos (como F-076).
- **R22.** El log INFO de `[partidas-obra]` debe contar también las equivalentes aplicadas y las ambiguas.
- **R23.** Las líneas sin lectura (almacén de F-051, residuos de F-111) no deben cambiar: F-117 solo mira lecturas.

## C · El caso real, de extremo a extremo (fakes, sin red ni BBDD)

- **R24.** CUANDO se valora un sobre como el del albarán de 0719 (contrato CTSB26/0373, 1 línea «grua pk 50 - montar
  muro y hormigonar», 9 UD × 60 €, lectura `CI.03.08`) con una lista reducida de 0719 (`CI.03A.1`, `CI.03A.8`,
  `CI.03A.13`, `CI.03P.9`, `CI.1.8`, `CI.2.8`, `CI.4.8`), el sistema debe persistir `codigo_partida_albaran =
  "CI.03.08"`, `codigo_partida_final = "CI.03A.8"`, el motivo `partida_equivalente:CI.03.08>CI.03A.8`, ningún
  `partida_fuera_de_lista` y el importe de hoy (540 €).
- **R25.** *(D2)* Ídem con la lectura `04.01.07` y la hoja `02.04.01.07` ⇒ `codigo_partida_final = "02.04.01.07"`.
- **R26.** La rama de valoración directa (F-075, sin contrato e importe leído) debe dejar el mismo rastro que R24.

## D · Documentación

- **R27.** `docs/ARCHITECTURE.md` (regla 23) debe recoger la excepción a «nunca por sufijo» y las reglas R2–R5, y
  `azure-apps/albaranes.md` §11 la variable `PARTIDA_EQUIVALENTE_ENABLED`.
