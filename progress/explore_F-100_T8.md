# F-100 · T8 — Propuesta del libro IA4 rellenada por el líder

- Fichero: `albaranes-F-100/evals/salidas/emparejamiento/propuesta_IA4_20261111-191938.xlsx` (hoja `propuesta`).
  Copia previa al lado: `propuesta_IA4_20261111-191938.xlsx.bak`.
- Columnas tocadas: `concilia`, `linea_contrato_esperada`, `motivo`, `propuesto_por = lider`. `validado` vacío en
  las 110 filas. Las demás columnas, intactas.
- Fuentes: la propia propuesta (candidatas), `evals/fixtures/inputs/*.json` (líneas de contrato completas) y
  `evals/fixtures/final/*.json` (RESULTADO_FINAL con comentarios). Sin red, LLM ni BBDD.

## Recuento

| concilia | filas |
|---|---|
| SI | 66 |
| NO | 28 |
| ? | 16 |
| **total** | **110** (59 casos) |

Comprobación hecha con `evals.emparejamiento.contradicciones` de la rama, suponiendo `validado = SI` en todas las
filas: **0 contradicciones** con IA3, RESULTADO_FINAL y el libro IA4 actual. Las 110 filas llevan `motivo`.

## Formato elegido (el que acepta `volcar`)

- `concilia`: `SI` / `NO` / `?`.
- `linea_contrato_esperada`: el **`codigo_producto`** de la línea del contrato (es lo que comparan `volcar`, R18 y
  `EMP`: `_codigo_producto_de` en `sv6_build.py`). Vacía cuando es NO o `?`.
- `motivo`: la línea concreta elegida (descripción, precio, partida) o por qué ninguna.

**Limitación que conviene saber al validar:** `EMP` compara solo por código. En muchos contratos varias líneas
comparten código (`MA1512` en todos los solados de GEN-002, `MA9999` en todos los hormigones de HOR-005…017,
`SM370001` en residuos), así que el libro no distingue entre ellas aunque el `motivo` diga cuál es. Solo en RES-001…006
(C1 frente a C2/C3) el código separa de verdad las candidatas.

## Las 16 filas `?` (todas por choque con RESULTADO_FINAL)

En todas, las reglas 1–3 dan **NO** y RESULTADO_FINAL dice **SI**, salvo COM-001, donde es al revés. No he
contradicho RESULTADO_FINAL en silencio: van como `?` para que decida el humano.

| caso · línea | duda |
|---|---|
| COM-001 · 1 | Regla 1 → SI con SM370001 SUMINISTRO GASOIL A 1,23 € CI.4.1 (1,230578 a <0,01 €). FINAL dice NO (precio `deducido`). |
| GEN-007 · 1 | «Kit Victoria» no está en el contrato y la línea no trae precio → NO. FINAL dice SI («incluido en contrato»). |
| HOR-008 · 1 | HNE-150/B/30 a 76 € solo en 02.01–02.04/CI.2.8; el albarán trae 32.02.01.01 → partida distinta. |
| HOR-009 · 1 | HM-20/B/20/X0 a 80 € solo en 10.04.01; el albarán trae 32.03.02. |
| HOR-012 · 1 y 2 | HA-25 a 89,3 € e incrementos de 3 €, ninguno en 42.01 (el comentario dice que hay 2 contratos). |
| HOR-013 · 1, HOR-014 · 1 | HA-25 a 89,3 €, ninguno en 38.01.03 (2 contratos). |
| HOR-016 · 1 | H100 a 78,58 € solo en 02.02.02; el albarán trae 38.01.01 (2 contratos). |
| HOR-017 · 1 | HA-25 a 89,3 €, ninguno en 42.01. |
| MOR-001 · 1 | M-7,5 a 72 € no está en el contrato (M-7 en escocias y M-5, a 70 €). FINAL SI con 72 € de `contrato_db`. |
| RES-009 · 1 | MEZCLA OTROS RESIDUOS existe en 32.01, pero a 138 €, no a 157 €. FINAL SI con 157 € de `contrato_db`. |
| RES-019 · 2 | Madera limpia a 10 €: el contrato tiene madera a 8 € y madera con pintura a 15 €. FINAL SI con 10 € («¿de dónde sale el 10?»). |
| RES-020 · 1, RES-021 · 1 y 2 | CONTENEDOR 6 M/3 (RCD'S) a 184 € solo en 15.01.; el albarán trae 16.01. ¿Partida mal leída? |

Lectura: 9 de las 16 son el patrón **«la pieza y el precio están, pero en otra partida»** (HOR-008/009/012/013/014/
016/017, RES-020/021). Casi todas son de hormigón con el comentario «el contrato elegido estaba mal, tiene 2»: lo más
probable es que la línea de la partida buena esté en el **segundo contrato**, que no figura en INPUTS. Si es así, el
arreglo está en los INPUTS (unir los dos contratos), no en relajar la regla 1. Otras 3 son de **precio que no
casa** (MOR-001, RES-009, RES-019), con un precio final `contrato_db` que no aparece en las líneas de contrato de
INPUTS: ¿contrato de otro año o versión?

## Discrepancias con RESULTADO_FINAL

Ninguna afirmada: las 94 filas SI/NO coinciden con `casa_con_contrato` (y con `linea_contrato` = C1 en RES-001…006).
Las únicas discrepancias son las 16 `?` de arriba.

## Dónde chocan las reglas 1–3 con el libro existente

- El libro IA4 actual (`IA4_conciliacion.xlsx`) tiene **todas sus filas en `?`** (GEN-002 6–8, HOR-005 3–5, HOR-007 2,
  HOR-014 2, HOR-017 4, MOR-002 1–2, MOR-003 1–2, MOR-004 1, RES-008 1, COM-001 1, FER-001…003). No afirma ningún
  criterio, así que **no hay choque**: la propuesta pasa todas a **NO**, salvo COM-001, que sigue en `?` (ver
  arriba). `volcar` no lo trata como contradicción (un `?` no contradice nada).
  Aviso: esas filas del libro llevan `precio_unitario_esperado` y `comentario` del humano; `volcar` escribe solo
  `caso_id`, `num_linea`, `concilia`, `linea_contrato_esperada` y `motivo` con la fusión conservadora. Conviene mirar
  que no se pierdan.
- **Regla 3 y los códigos genéricos.** He leído «bolsa» por la **descripción** («Material de ferretería»,
  «Suministros ferretería Feymaco», «Varios»), no por el código. Muchas líneas concretas del contrato llevan códigos
  genéricos (`MA9999` en inodoros, hormigones y gravas; `SM370001` en residuos y gasoil; `QA9999` en la grúa;
  `MA1512` en los solados). Si el humano quería decir que **todo `MA9999`/`MA1501` es bolsa por código**, 24 filas
  SI con `MA9999` pasarían a NO (44 si también cuentan `SM370001` y `QA9999`) y contradirían RESULTADO_FINAL. Hay que confirmarlo.
- **Una ambigüedad dentro de la regla 1:** HOR-004 · 2 (INCREMENTO SIN ADITIVO, 5 €, sin partida) tiene dos
  candidatas con el mismo significado y códigos distintos: MA290205 (03.03.07, la partida del hormigón y la de FINAL)
  y MA9999 (03.03.02). Propongo MA290205; que lo revise el humano.
- Las líneas sin partida (almacén, regla 2) casan con candidatas de cualquier partida: ALQ-001, GEN-010, HOR-004 2–5,
  HOR-005 1–2, HOR-009 3, HOR-010 2, HOR-015, HOR-017 2–3, MOR-004 2, RES-001…006, RES-010…018 (líneas 2). Todas
  coinciden con FINAL SI.
