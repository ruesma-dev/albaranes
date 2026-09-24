# Análisis de la pasada de evals de F-048 frente a la de F-047

2026-09-24 · solo lectura (no se ha lanzado ninguna eval, ningún test y ningún LLM) · sin valores: caso, campo y si acierta o falla.
Fuentes: `progress/evals_F-048.md` (`fac6b10`, `completa`), `progress/evals_F-047.md` (`2e05499`, `ciclo`),
`evals/fixtures/IA1/*.json` de las dos ramas, `evals/salidas/2026-09-18-03/` y el código de `evals/`.

## Conclusión

1. **La obra no la mide ninguna de las dos pasadas.** `obra_codigo` (y también `obra_nombre`, `proveedor_cif`
   y `forma_pago`) está a `?` (`@@NO_COMPARAR@@`) en el ground truth de IA1 **en los 59 casos**, y en las dos ramas.
   Con estos datos no se puede afirmar ni negar que el prompt nuevo empeore la obra: el banco no la mira.
2. En el resto de la cabecera **no hay una señal que se pueda atribuir al prompt**. Casi todo el empeoramiento
   aparente viene de que las dos pasadas miden sistemas distintos (ver «Límites»). Confianza baja en los dos
   sentidos: la comparación no es de igual a igual.
3. **Para salir de dudas**: (a) declarar `obra_codigo` en el libro IA1 para 8–10 casos cuyo papel identifica la obra
   (lo hace el humano); (b) repetir solo IA1 en `completa`, con gemini y los mismos casos, en `dev` y en esta rama,
   2–3 veces en cada una, para medir cuánto varía el LLM por sí solo. Por ejemplo:
   `python -m evals.runner --con-llm --fases IA1 --casos GEN-001,GEN-009,GEN-010,HOR-003,HOR-006,FER-003,RES-005,RES-011,RES-012,RES-015 --informes <carpeta_fuera_de_progress>`
   (se factura). Como el runner de `completa` no guarda la salida en bruto de cada caso, para comparar la obra
   caso a caso también hace falta capturar `cabecera.obra_codigo` de los dos lados.

## 1. Casos omitidos

| Fase | F-048 | Motivo | F-047 |
|---|---|---|---|
| IA1 | RES-020, RES-021 | no existe el fichero del albarán | mismos dos y por lo mismo, más 16 que no llegaron al final del ciclo (plazo H3 o merge sin CIF u obra) |
| IA2 | RES-020, RES-021 | no existe el fichero del albarán | 57 (sin caso en el libro IA2 o sin llegar al final del ciclo) |

- **El JSON degenerado de IA2 no ha vuelto.** Ningún `OMITIDO` con «ERROR en IA2», ni `json_invalid`, ni fases
  `NO_EVALUABLE`: los dos omitidos son los albaranes que no se versionan. No se sabe qué caso tumbó la primera
  pasada, porque murió sin escribir informe (`progress/impl_F-048.md`). IA2 solo tiene 11 casos en su libro
  (RES-001 a RES-009, RES-020 y RES-021).

## 2. Campos de cabecera en los 41 casos que evalúan las dos pasadas

Qué se compara en la cabecera de IA1: `proveedor_nombre` y `fecha` en los 59 casos, y `numero_albaran` solo en
RES-001 a RES-007 (de esos, solo RES-005 se evaluó en F-047). El resto de los campos de cabecera está a `?`.

**`obra_codigo`: no cambia de estado ningún caso**, porque no se compara en ninguno (NO_COMPARAR). Aciertos 0/0 y
fallos 0/0 en las dos pasadas.

Casos que cambian de estado, agrupados por campo. Ninguno pasa de fallar a acertar:

| Campo | Cambio | Nº | Casos |
|---|---|---|---|
| `proveedor_nombre` | acierta → falla | 29 | FER-001, FER-002, FER-003, GEN-001, GEN-009, GRA-001, GRA-002, HOR-003, HOR-004, HOR-005, HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, HOR-016, MOR-002, MOR-003, RES-010 a RES-019 (10) |
| `fecha` | acierta → falla | 6 | FER-003, GEN-009, RES-011, RES-012, RES-015, RES-018 |
| `fecha` | falla en las dos | 4 | FER-001, RES-008, RES-013, RES-019 |
| `numero_albaran` | acierta → falla | 1 | RES-005 |

Forma de los fallos (clasificados sin sacar valores):
- `proveedor_nombre`, 39 fallos en los 57 casos de F-048: 18 son el mismo nombre con otras tildes, otra
  puntuación u otra forma jurídica; 18 son el nombre comercial frente a la razón social (uno contiene al otro);
  3 son distintos de verdad. Es lo que pasa cuando se compara lo que lee el LLM sin que sv3 lo haya
  canonizado contra Sigrid (ver «Límites»).
- `fecha` (los 6 nuevos): 4 casos RES con el año cambiado y el día y el mes bien (RES-011, RES-015, RES-018;
  RES-012 cambia varias partes), FER-003 con el mes cambiado, GEN-009 con varias partes. El prompt nuevo no
  toca nada de fechas.
- `numero_albaran`: en los 7 casos RES que lo comparan, lo leído es un trozo del esperado, al que le falta una parte.
  Solo RES-005 es comparable con F-047.

## 3. Fallos críticos por caso en IA1

- Ningún caso pasa de ROJO a VERDE. Ninguno tiene menos fallos críticos que en F-047.
- **Pasan de VERDE a ROJO 8 casos:**

| Caso | Campo que falla en F-048 | Lectura |
|---|---|---|
| GEN-001, HOR-003, HOR-006, HOR-008, HOR-011, HOR-016 | solo `proveedor_nombre` | artefacto del modo |
| GEN-009 | `fecha`, `proveedor_nombre` | fecha: sin atribuir (ver §5) |
| GEN-010 | `lineas[1].importe`, `lineas[1].precio_unitario` | probablemente el modo: sin la fase 2 ni sv3, gemini deja precio e importe donde el libro no los espera |

- Los ROJO que siguen en ROJO suben de 1 a 2 fallos críticos, casi siempre por `proveedor_nombre`. Cambian además
  la forma de algunos fallos de línea: en FER-002 (`lineas[6]`) y en RES-010 (`lineas[2]`), la fila que en F-047
  faltaba ahora existe, pero con la cantidad mal. Es el mismo defecto contado de otra manera.
- Los 16 casos sin evaluar en F-047 (ALQ-001, GEN-002, GEN-003, HOR-012 a HOR-015, HOR-017, MOR-004, RES-001 a RES-004, RES-006, RES-007 y RES-009) salen todos en ROJO en F-048, y no hay con qué compararlos.

**IA2.** RES-005 sale VERDE en las dos pasadas. **RES-008 pasa de VERDE a ROJO** (1 crítico: `contexto[1/CODIGO_LER].valor_esperado`).
Los otros 7 casos de F-048 no tienen referencia en F-047, y salen todos en VERDE con avisos laxos de filas de contexto de más.

## 4. `lectura_correo` y campos nuevos

- `lectura_correo` **no aparece en ningún sitio del informe**, ni en el detalle ni en «Campos no observables».
  No está en `OBSERVABLES` de `evals/procesos/sv2_extraccion.py` ni en el ground truth: no se compara ni mete ruido.
- «Campos no observables» es **la misma lista, campo a campo**, en las dos pasadas (17 campos). Ningún campo nuevo.
  Los avisos laxos `IA1.lineas[+]` (filas de más en GEN-006, GEN-007, RES-001, RES-004 y otros) no vienen del correo.

## 5. Límites de la comparación: qué es ruido y qué podría ser el prompt

**No miden el mismo sistema.** Esto pesa más que el prompt:
- **F-047 (`ciclo`)** compara el merge que persiste sv3 (`albaran_documents_merge`). En ese merge hay tres manos:
  gemini (fase 1), openai (la fase 2 revisa el documento entero; los crudos de 2026-09-18-03 salen con
  `provider_origin=openai` en 57 casos) y sv3, que **canoniza `proveedor_nombre` con el nombre de Sigrid**
  (`sqlalchemy_albaran_repository.py`, alrededor de la línea 1827) y resuelve la cabecera.
- **F-048 (`completa`)** compara la salida de la fase 1 de gemini, sin fase 2 y sin sv3. El informe dice
  «Proveedores invocados: gemini» en IA1 y «openai» en IA2.
- En `completa` el servicio se monta sin proveedor de obras activas, así que `{obras_activas}` llega a IA1 como
  «NO DISPONIBLE». En el pipeline sí llega la lista. Aunque el banco comparase la obra, esta pasada la mediría en
  condiciones distintas a las de producción.

**Casos:** solo son comparables los 41 que evalúa F-047 en IA1 (F-048 evalúa 57), y en IA2 solo 2 (RES-005 y RES-008).
**Variación del LLM:** una corrida por lado y sin réplicas. Un caso que cambia de estado por un campo es compatible con el azar.

**Veredicto por partes:**

| Cambio | Lo más probable | Por qué |
|---|---|---|
| `proveedor_nombre` (29 casos) | **artefacto del modo** | 36 de 39 fallos son el mismo proveedor escrito de otra manera, y en `ciclo` sv3 lo canoniza |
| `fecha` (6 casos nuevos) | **modo o ruido**, sin descartar del todo el prompt | el prompt no toca fechas. En `ciclo`, la fase 2 revisa la cabecera. Son sobre todo años mal leídos en RES |
| `numero_albaran` RES-005 | **modo** | un trozo de la cadena. Un solo caso comparable |
| GEN-010 precio/importe | **modo** | es el mismo tipo de fallo que FER-001 y FER-002 ya tenían |
| IA2 RES-008 (LER) | **ruido, con reservas** | el prompt de fase 2 lleva dentro el task entero de la fase 1 (con la sección nueva del correo), y su entrada es la salida de IA1. Pero es 1 caso y 1 campo |
| `obra_codigo` | **no medible** | NO_COMPARAR en los 59 casos |

**Efecto del prompt probado: ninguno. Ausencia de efecto probada: tampoco.** La comparación limpia es la del punto 3 de la conclusión.

## Aparte

`progress/evals_F-048.md` **lleva valores** (nombres, cantidades, precios): esta rama sale de `dev` y el informe sin valores (R31) llegó con F-047, que no está aquí.
El fichero lo ignora git (`.gitignore:46`), así que no hay fuga en el repositorio, pero no debe copiarse a ningún sitio versionado.

## 6. Comparador de obra dev/rama (2026-09-24, `progress/comparar_obra_F-048.md`)

Solo fase 1, sin correo, gemini, CON lista de obras activas (277), 10 casos × 2 prompts × 3 repeticiones.
7 casos idénticos. Los 3 que no lo son (RES-015 «difiere», RES-005 y RES-011 «inestables») tienen el mismo
patrón: **`dev` devuelve null donde la rama deduce una obra**, y en todas las repeticiones en que la rama
la deduce **coincide con la obra de `RESULTADO_FINAL`** del ground truth (`evals/fixtures/final/`). En
ninguna repetición la rama da una obra distinta de la esperada. Lectura: el prompt nuevo (R16: la obra del
papel se lee o deduce SIEMPRE) **mejora** la obra en los documentos de residuos que no la imprimen; no se
ha visto ningún empeoramiento. Muestra pequeña (10 casos, 3 réplicas): indicio, no prueba.
