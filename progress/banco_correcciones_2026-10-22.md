# Correcciones del banco de evals de IA1 · 2026-10-22

Chore sin feature, pedido por el humano («el banco corrígelo ya sin abrir
nada»). Rama `chore/banco-correcciones` (worktree `albaranes-banco`). Sin push.
Ninguna llamada de pago, nada contra producción, `.env` sin tocar.

## Qué se tocó

| Commit | Bloque |
|---|---|
| `235db7e` | Correcciones confirmadas por el humano (1, 2, 3) |
| `77e59ef` | IA1 espera lo impreso (4, 5, 6, 7) + instantánea F-045 R17 |
| `963ecfe` | Corrector: número y partida normalizados, criticidad (8, 9, 10) + tests |
| `2cfe015` | Libro IA1: CIF, número y partida rellenos (8, 9, 10) + instantánea |

- **Libros (no versionados)**: `IA1_extraccion.xlsx`, `IA3_valoracion.xlsx` y
  `RESULTADO_FINAL.xlsx` del repo principal, editados con openpyxl (sin
  fórmulas, validaciones ni celdas combinadas; el formato es `General`).
  Copia previa de los seis libros en `evals/ground_truth/copias/*.20261022-2019.xlsx`.
- **Fixtures**: regenerados con `python -m evals.conversor --ground-truth
  <principal>\evals\ground_truth --fixtures <worktree>\evals\fixtures`. El
  barrido de datos sensibles pasó en las cuatro regeneraciones (el conversor
  aborta sin escribir si salta). Antes de editar se comprobó que los
  fixtures de `dev` coincidían byte a byte con los libros.
- **Código**: `evals/comparador.py` (normalizadores), `evals/criticidad.json`
  (dos laxos y su nota), `tests/test_evals_normalizacion_numero_partida.py`
  (nuevo), `tests/datos/afirmado_por_el_humano_RES.json` (regenerada).

## Caso a caso

**Confirmadas por el humano**
1. **FER-002 (IA1)**: 5 líneas impresas (papel, jabón, rollo, añil, bolsa)
   con las cantidades del papel, en vez de las 8 ya repartidas entre P4 y P5.
   RESULTADO_FINAL e INPUTS se quedan con las 8 (F-049 R23).
2. **GRA-001**: partida P4.22.01.03.07 en RESULTADO_FINAL (línea) e IA3
   (línea valorada). No tiene sintéticas.
3. **RES-011 y HOR-015**: partida final vacía (almacén) en las líneas y las
   añadidas de RESULTADO_FINAL y en las líneas valoradas y sintéticas de IA3
   (RES-011: 2+1 y 2+1 filas; HOR-015: 3+1 y 3+1). Comentario igual que el de
   RES-001: «F-051 (decision del humano 2026-10-22): linea sin partida
   impresa => almacen, partida final vacia; antes esperaba …, la del contrato».

**Decididas por el líder (IA1 = lo impreso)**
4. **Hormigón y mortero**: fuera de IA1 las filas 2..n de HOR-004 (4),
   HOR-005 (4), HOR-007 (1), HOR-009 (2), HOR-010 (1), HOR-014 (1), HOR-015
   (2), HOR-017 (3), MOR-002 (1), MOR-003 (1) y MOR-004 (1). El script
   comprobó antes que la línea 1 era la base con la designación y que cada
   fila quitada casaba con INCREMENTO/INCREM./ADICIÓN FIBRAS/CARGA(S)
   INCOMPLETA(S). En los 11 casos los 8 modelos leen exactamente 1 línea.
   HOR-012 conserva su línea 2 (no estaba en la lista). RESULTADO_FINAL intacto.
5. **Residuos**: fuera de IA1 la fila «RCDS. SUCIOS/VOLUMINOSOS/MADERA
   LIMPIA» de RES-010..015, 017, 018 y 019 (RES-016 solo tenía una). La
   cantidad del contenedor pasa de 1 a `?` en RES-001..019, con comentario:
   el 1 es la conversión de sv6 y el papel trae m³ y kg.
6. **Cantidades convertidas**: GRA-001 espera 30380 (kg impresos). **Extensión
   propia**: GRA-002 (mismo proveedor y formato) pasa de 29,96 a 29960; 5 de 8
   modelos leen 29960.
7. **Importes y precios impresos**: FER-001 l.1 y FER-002 l.1-5 con importe
   (los 8 modelos leen lo mismo, salvo 1 en FER-002 l.5 que lee otra fila, y
   cuadra con cantidad × precio × (1 − 40 %)). FER-003 l.1: lo que faltaba era
   el **precio** (7 de 8 leen el mismo y cuadra con el importe que ya
   estaba). GEN-002 l.8: importe a `?`, porque el valor anterior no cuadra con
   cantidad × precio y los modelos no coinciden.
8. **Proveedor**: `proveedor_nombre` es LAXO (lista `laxos` y nota en
   `_notas_laxos`). `proveedor_cif` sigue CRÍTICO (patrón `*_cif`). Estaba a
   `?` en los 59 casos: copiado de RESULTADO_FINAL en los 59.
9. **Número de albarán**: rellenado desde `mapa_casos.json` (`codigo`) en
   52 casos; RES-001..007 ya lo tenían. El corrector lo compara normalizado:
   solo dígitos y sin ceros a la izquierda.
10. **Partida en IA1** (`codigo_imputacion`): LAXA y normalizada (mayúsculas,
    sin espacios, sin ceros a la izquierda por segmento). Rellena en 58
    líneas con la `partida_final` no vacía de RESULTADO_FINAL, emparejando
    por descripción y, si no, por nº de línea. FER-002 l.1-3 se quedan a `?`
    porque su partida final está repartida entre P4 y P5.

**Corrector** (`evals/comparador.py`): `normalizar_numero_albaran`,
`normalizar_partida`, el registro `NORMALIZADORES` y `equivalentes_en`, que
`comparar` usa en las hojas. Se aplica por nombre de campo, así que el
número también se normaliza en `final.datos_generales`. La partida valorada
(`codigo_partida_final`, `partida_final`) NO se normaliza, y hay un test que
lo fija.

## Re-evaluación de la T14 de IA1, sin llamar a ningún modelo

Se usó `resultados.json` de `evals/salidas/comparar_modelos/2026-10-22-142739/`
con `runner.comparar_sv2('IA1', …)`, la criticidad del worktree y los
fixtures nuevos. El script es
`<scratchpad>\banco\reevaluar.py`. Se tomaron 59 casos por modelo; 2 salen
ERROR porque RES-020 y RES-021 no tienen albarán. «Comunes» son los pares
(caso, campo) que fallan en los 8 modelos; «propios» son el resto de fallos.

**Antes** (fixtures de `dev` + criticidad de `dev`; reproduce los 97 comunes):

| Modelo | Verdes | Rojos | Fallos | Comunes | Propios | Avisos |
|---|---|---|---|---|---|---|
| gemini-4-argon | 13 | 44 | 117 | 97 | 20 | 58 |
| gemini-3.7-flash | 12 | 45 | 126 | 97 | 29 | 58 |
| claude-opus-5-5 | 12 | 45 | 123 | 97 | 26 | 66 |
| gpt-5.4 | 14 | 43 | 124 | 97 | 27 | 95 |
| gpt-5.5 | 14 | 43 | 133 | 97 | 36 | 62 |
| gpt-6.1-sol | 9 | 48 | 135 | 97 | 38 | 65 |
| gpt-6-luna | 10 | 47 | 136 | 97 | 39 | 77 |
| gpt-5.6-luna | 9 | 48 | 144 | 97 | 47 | 74 |

**Después**:

| Modelo | Verdes | Rojos | Fallos | Comunes | Propios | Avisos |
|---|---|---|---|---|---|---|
| gemini-4-argon | 25 | 32 | 45 | 28 | 17 | 127 |
| claude-opus-5-5 | 23 | 34 | 52 | 28 | 24 | 130 |
| gpt-5.4 | 22 | 35 | 60 | 28 | 32 | 169 |
| gemini-3.7-flash | 20 | 37 | 55 | 28 | 27 | 126 |
| gpt-5.5 | 20 | 37 | 69 | 28 | 41 | 134 |
| gpt-6.1-sol | 20 | 37 | 59 | 28 | 31 | 134 |
| gpt-5.6-luna | 19 | 38 | 74 | 28 | 46 | 154 |
| gpt-6-luna | 18 | 39 | 68 | 28 | 40 | 159 |

Fallos comunes por tipo:
- **Antes (97)**: 33 filas no producidas, 28 `proveedor_nombre`,
  23 cantidades, 7 importes, 3 fechas y 3 precios.
- **Después (28)**: 14 `proveedor_cif`, 10 `numero_albaran`, 3 fechas y
  1 fila no producida.

Fallos de todos los modelos sumados, después: 140 de número, 127 de CIF,
65 de fecha, 63 de importe, 50 de precio, 22 de cantidad y 15 de filas no
producidas.

Los avisos suben porque `proveedor_nombre` (263) y `codigo_imputacion` (315)
avisan ahora en lugar de fallar o de no compararse.

## Los 28 comunes que quedan, y qué parecen

- **CIF (14), ¿del banco?**
  - Los 8 modelos devuelven `null` en ALQ-001, HOR-005..011, MOR-003,
    RES-001 y RES-002. Lo probable es que el papel no imprima el CIF del
    proveedor, o que no se lea.
  - En RES-005, 006 y 007 los 8 leen variantes erróneas. El comentario del
    humano en RES-007 ya decía «coge mal el CIF».
  - Propuesta: donde el CIF no esté impreso, IA1 debería esperar vacío. Hay
    que mirar los PDF: aquí no se pueden renderizar, porque falta `pdftoppm`.
- **Número de los Cubas (9: RES-010, 011, 013..019), del corrector.**
  - El papel imprime «Documento de Identificación nº» con 20 dígitos: NIMA,
    año y serie. Visto en la imagen de RES-010.
  - El código del humano es solo la serie final, así que con «solo dígitos»
    no casan.
  - Decisión pendiente: (a) aceptar que el leído termine en el esperado,
    (b) que IA1 o sv3 extraigan la serie, o (c) dejarlos a `?`.
- **Número de RES-008 (1).** Los 8 leen otro primer dígito («3…» en lugar de
  «9…»), y el código esperado sale del nombre del fichero. Toca mirar el papel.
- **Fechas (3).**
  - FER-001 y FER-002: los modelos leen `null` o fechas dispares. Ya estaban
    antes; parece que el papel es poco legible.
  - RES-019: 4 de 8 leen 2025-08-07 frente al 2025-07-28 del libro. Toca
    mirar el papel.
- **FER-003 l.2 (1).** La línea de devolución (−4) no la produce nadie. Es un
  fallo real conocido: la deducción no estaba planteada.

## Dónde sale mal el número (fallo crítico, nº de modelos de 8)

- 8/8: RES-008, RES-010, 011, 013, 014, 015, 016, 017, 018 y 019.
- 7/8: RES-012.
- 6/8: FER-001 (el caso de referencia: se lee 2139543 y es 2139643),
  FER-002, HOR-015, RES-007 y RES-009.
- 4/8: FER-003 y RES-005.
- 3/8: HOR-016.
- 2/8: HOR-012, HOR-014, HOR-017, RES-002 y RES-003.
- 1/8: GRA-001 y RES-004.

## Dónde sale mal la partida (aviso, nº de modelos con ≥1 aviso)

- **Los 8 leen `null` y RESULTADO_FINAL trae partida**: HOR-006..014,
  HOR-016, HOR-017 y RES-010..019. Lo más probable es que el papel no
  imprima partida y que la final salga del contrato. Son candidatos a la
  misma decisión F-051 que RES-011 y HOR-015 (almacén, partida vacía); que
  decida el humano.
- **Se lee algo, pero mal**:
  - Prefijo mal leído o ausente: HOR-001 y HOR-002 (PC/PJ por P5), GRA-002
    (PT/PJ por P5), GEN-002 (PS por P5, 7/8), MOR-001 (sin P5, 8/8),
    MOR-002 (8/8) y HOR-003 (04 por P4, 6/8).
  - Último segmento: MOR-004 lee 10.03.01 y el libro dice 10.03.04 (8/8).
  - Otros: GEN-003 (5/8), GEN-005 y GEN-007 (4/8), GEN-001, GEN-004 y
    GEN-008 (3/8), y RES-008 (4/8).
  - Aislados: COM-001, FER-002 y GRA-001 (1-2 modelos), GEN-006 (8/8) y
    GEN-009 (2/8).
- RESULTADO_FINAL guarda algunas partidas como número (5.01, 5.04, 5.02,
  42.01, 32.01): un cero final perdido en Excel no se puede recuperar.

## Tests

- **RED**: pytest no podía lanzarse porque la campaña de mutación de F-084
  (`harness.mutacion --feature F-084`, desde las 17:10) llenaba la máquina
  de suites. Se importó el módulo de test con `python` antes de escribir el
  código:
  ```
  $ PYTHONPATH=. python -c "import tests.test_evals_normalizacion_numero_partida"
  ImportError: cannot import name 'normalizar_numero_albaran' from 'evals.comparador'
  proveedor_nombre -> fallo | codigo_imputacion -> fallo
  SS-0000168 vs 0000168 -> ['fallo']
  ```
- **GREEN**: ver la sección siguiente.
- **Tests ajustados**: `tests/datos/afirmado_por_el_humano_RES.json`
  (guardián de F-045 R17).
  - Pierde las 7 `IA1.lineas[RES-00x|1].cantidad` (de 1 a `?`, punto 5).
  - Gana los 7 `IA1.cabeceras[RES-00x].proveedor_cif` (punto 8).
  - No cambia ningún valor. La degradación la decidió el **líder, no el
    humano**: que conste en la PARADA 2.

## Evidencias

- **Tests afectados**: 876 pasan y 791 quedan deseleccionados, en 202,35 s.
  - Comando: `pytest tests/ -q -k "f011 or f045 or f047 or f083 or evals or
    conversor or criticidad"`.
  - Se lanzó con el venv del repo principal y después de comprobar que ya no
    corría ningún pytest ni ningún `init.sh` de albaranes: la campaña de
    F-084 había terminado.
- **Test nuevo**: `tests/test_evals_normalizacion_numero_partida.py`, con
  30 tests. Pasan en 0,16 s.
- **Cobertura de las líneas nuevas** de `evals/comparador.py`: 100 %.
  - Medida con `coverage run --include=evals/comparador.py` sobre el test
    nuevo, `test_f011_r2_comparador.py` y `test_f045_r17_no_degradar.py`.
  - El módulo entero queda al 77 %; las líneas sin cubrir son anteriores al
    cambio.
  - No se pasó por la `PUERTA COBERTURA` de `init.sh`: el encargo pedía no
    lanzarlo.
- **Mutación**: no se lanzó. Es un chore sin nivel de rigor y la máquina
  estaba saturada de campañas.
- **`bash harness/init.sh`**: NO se ejecutó, por indicación del líder (F-084
  usaba la suite). Hay que lanzarlo antes de mergear.
- **Re-evaluación**: hecha sin coste, y la cifra de «antes» reproduce los
  97 comunes. Los ficheros con valores (no versionados) están en
  `<scratchpad>\banco\antes.json` y `despues.json`.
