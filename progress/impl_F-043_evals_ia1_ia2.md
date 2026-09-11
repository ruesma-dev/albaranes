<!-- progress/impl_F-043_evals_ia1_ia2.md -->
# F-043 · IA1 e IA2 del lote SALMEDINA — BLOQUEADO

**Veredicto: `blocked`.** Los siete PDF están movidos a su sitio (punto 5 del
encargo, hecho). `IA1_extraccion.xlsx` e `IA2_contexto.xlsx` **siguen vacíos**,
a propósito: el Excel de negocio y el `README`/`LEEME` de los libros **se
contradicen en cuatro de los seis campos que hay que rellenar**, y el propio
encargo manda parar en ese caso en vez de improvisar.

No se ha tocado código de producción. `bash harness/init.sh` en verde.

## 1. El hallazgo que lo cambia todo: cómo es el papel de SALMEDINA

Leí los siete PDF (son la entrada declarada de IA1). **Ninguno es un albarán
comercial con líneas y precios.** Los siete son el mismo impreso legal —
«DOCUMENTO DE IDENTIFICACIÓN / DOCUMENTO DE CONTROL (Art. 6 R.D. 553/2020)» —
con una **rejilla de 12 códigos LER preimpresos** donde el operario escribe a
mano el volumen en la fila del residuo que se lleva.

Lo que el papel SÍ imprime o trae escrito a mano:

| caso_id | Nº albarán impreso | Fecha | Fila LER marcada | VOL m³ | Dirección de obra |
|---|---|---|---|---|---|
| RES-001 | SS-0000168 | 3-7-24 | 17 02 01 Madera | 6 | M-401 S/N · Fuenlabrada |
| RES-002 | SS-0003935 | 16-7-24 | 17 01 07 Horm_Ladr_Cerám. | 6 | M-401 S/N · Fuenlabrada |
| RES-003 | SS-0000589 | 8-7-24 | 17 08 02 Mat. Yeso | 6 | Ctra. M-401 km 1'800 · Fuenlabrada |
| RES-004 | SS-0003967 | 10-07-24 | 17 06 04 Mat. Aislamiento | 6 | Ctra. 401 Madrid-Toledo p.k. 1800 · Fuenlabrada |
| RES-005 | **SS-0001977** | 18-7-24 | 17 06 04 Mat. Aislamiento | 6 | Ctra. M-401 p.k. 1'800 · Fuenlabrada |
| RES-006 | SS-0025146 | 5/11/24 | 17 09 04 Mat. Mezclados | 6 | C/ Fútbol Sala 4 · Leganés |
| RES-007 | SS-0026122 | 5/11/24 | 17 08 02 Mat. Yeso | 9 | Calle Fútbol Sala 4 · Leganés |

Los siete LER coinciden **exactamente** con la columna «LER o codigo linea o
producto» del Excel: 7 de 7. Esa parte de la fuente está confirmada por el
papel.

Lo que el papel **NO** imprime, en ninguno de los siete:

- **Ningún concepto de línea.** No aparece «CAMBIO CONTENEDOR 6M3», ni
  «CONTENEDOR DE RESIDUOS 6 M3», ni «INCREMENTO LER 170802…». Esos textos son
  **descripciones de producto del contrato**, no texto del albarán.
- **Ningún precio ni importe.** El propio Excel lo dice en sus columnas
  «unitario viene en albaran o valorado en contrato?» e «importe viene en
  albaran…»: en los siete casos dice `CONTRATO` (o `OFERTA` en RES-007),
  **nunca `ALBARAN`**. Compárese con las filas de FEYMACO del mismo libro, que
  sí dicen `ALBARAN`.
- **Ningún código de obra.** No hay «687» ni «691» en el papel: solo una
  dirección manuscrita. 687 y 691 son códigos de Sigrid.
- **Ningún CIF de cliente** (la casilla CIF/NIF está vacía en los siete). El
  único CIF legible es el del sello del gestor, y en RES-001 y RES-002 ese sello
  no es de SALMEDINA sino de «CCR LAS MULAS, S.L.U.», con otro CIF.

## 2. Las cuatro contradicciones, una a una

El `LEEME` de IA1 dice: *«el resultado ESPERADO de la extracción IA1»* y
*«Celda vacía = ese campo no aparece en el albarán»*. El encargo lo repite:
*«IA1 extrae lo que está impreso en el papel»*. Con eso y el papel delante:

| # | Campo | Lo que dice el Excel | Lo que hay en el papel | Por qué no puedo decidirlo yo |
|---|---|---|---|---|
| C1 | **Nº de líneas** | 2 líneas en RES-003/004/005/007 (cambio + incremento LER) | 1 sola fila LER marcada | El incremento **ya está sembrado como sintética** (`rol_linea = incremento_residuos`) en IA3 y en `lineas_anadidas` del maestro. Si además lo exijo en IA1, la misma línea se cuenta dos veces: IA1 tendría que extraerla y IA3 tendría que añadirla |
| C2 | **`cantidad` / `unidad`** | `1,00` / `UD` | `6` (9 en RES-007) en una columna rotulada **VOL. m³**, sin unidad escrita | `1 UD` es la cantidad **ya valorada** (1 servicio de contenedor), no lo impreso. Además contradice lo ya sembrado: `INPUTS.LINEAS_ALBARAN` tiene `cantidad 6,0` y `unidad` vacía, y F-024 fijó `unidad_medida = null` para estos siete |
| C3 | **`descripcion_esperada`** | «CAMBIO CONTENEDOR 6M3» | «Mat. Yeso» / «Madera» / … (denominación preimpresa de la fila LER) | El texto del Excel es del contrato. Pero `INPUTS.LINEAS_ALBARAN` ya sembró `descripcion = "<LER> <concepto>"` con el concepto del contrato: si IA1 espera otra cosa, la salida de IA1 deja de ser la entrada de IA3 y el extremo-a-extremo queda incoherente |
| C4 | **`obra_codigo`** | 687 / 691 | no está: solo una dirección | El encargo me dice que saque el código de obra del Excel; el `LEEME` me dice que vacío significa «no aparece en el albarán». Exigir 687 obliga al extractor a inventar un dato de Sigrid que no está en el papel |

Y un quinto punto, menor pero del mismo tipo:

- **C5 · `precio_unitario` / `importe`.** Este sí lo tengo resuelto y sin
  dudas: **vacíos (null)** en los siete, porque el propio Excel declara que
  vienen de `CONTRATO`/`OFERTA` y no del albarán. Lo dejo escrito aquí para que
  no haya que volver a razonarlo.

## 3. Un error de dato que conviene corregir de paso: RES-005

Los fixtures ya sembrados fijan `numero_albaran = "SS-0801977"`, con este
comentario: *«el Excel lo numera '1977'; se usa el numero que leyo el sistema,
SS-0801977»*.

**El papel imprime `SS - 0001977`**, en la misma tipografía roja que los otros
seis. `0801977` es una **mala lectura del sistema** que se consagró como ground
truth. Da igual para IA3 (no usa el número), pero para IA1 es letal: el campo
`numero_albaran` es justo lo que IA1 tiene que leer, y el ground truth actual
le exigiría **reproducir el error de OCR** para dar verde.

Afecta a `evals/fixtures/inputs/RES-005.json` y
`evals/fixtures/final/RES-005.json` (y a sus libros `.xlsx`). No lo he tocado:
son casos ya validados por el humano y corregirlos por mi cuenta movería el
ground truth de IA3 y del maestro.

## 4. Las dos salidas posibles (para que se decida en un mensaje)

**Opción A — IA1 = lo impreso en el papel (mi recomendación).**
Una línea por caso; `descripcion_esperada` = denominación de la fila LER
(«Mat. Yeso»); `cantidad` = 6 (9 en RES-007); `unidad` vacía o `?`;
`precio_unitario`/`importe`/`obra_codigo`/`proveedor_cif` vacíos;
`numero_albaran` el impreso (con `SS-0001977` en RES-005). El incremento LER se
queda donde ya está, en IA3 como sintética. Coherente con el `LEEME`, con
`INPUTS`, con F-024 y con el papel. Coste: hay que corregir RES-005 y asumir
que `descripcion` de IA1 ≠ `descripcion` de `INPUTS` (o alinear `INPUTS`).

**Opción B — IA1 = la vista del Excel.**
Dos líneas donde el Excel las pone, `1 UD`, conceptos del contrato, obra 687.
Es transcribir la fuente tal cual, pero convierte IA1 en un eval que **exige al
extractor inventar** texto, unidades y códigos que no están en el documento, y
duplica el incremento LER que IA3 ya añade. Mide algo, pero no mide extracción.

**IA2 depende de A/B** solo en el `num_linea`. Su contenido ya lo tengo cerrado
para los siete, en cuanto se decida: `codigo_ler` (ver §5), `volumen_m3` = 6/9,
`tamano_contenedor` = 6/9 y `tipo_familia = residuos`. El campo `movimiento`
(LLEVAR/RETIRAR) lo dejaría en `?`: los siete papeles traen **rellenas a la vez**
«Nº cont. LLEVADA» y «Nº cont. RETIRADA» —son cambios de contenedor—, así que el
papel no permite decidir un único valor y elegirlo yo sería inventarlo.

## 5. Formato del código LER (criterio, ya decidido)

El `LEEME` de IA2 lo fija sin ambigüedad: *«codigo_LER (6 dígitos sin
espacios)»*. El Excel lo trae como `17 08 02`. **Criterio aplicado: quitar los
espacios, sin más** → `170802`. Coincide con lo ya sembrado en las CONDICIONES
de `INPUTS` (`codigo_ler = "170802"`) y con los seis dígitos del catálogo LER.
No hay ceros que añadir ni quitar: los 12 LER del impreso son ya de 6 dígitos.

## 6. Líneas deducidas: cómo las traté

**No hay ninguna.** Revisadas las 11 filas de SALMEDINA del Excel, las 11 dicen
`EN ALBARAN`; ni una dice `DEDUCIDA` (sí las hay en HORMIGON y MORTERO, de otros
proveedores, que quedan fuera de este encargo). El aviso del encargo se cumple:
**el incremento por LER figura como `EN ALBARAN`**, no como deducido.

Pero `EN ALBARAN` en ese libro significa «esta línea la respalda el albarán»,
**no** «este texto está impreso en el albarán»: el papel no imprime ningún
incremento, lo imprime la rejilla LER de la que el incremento se deriva. Por eso
C1 es una decisión del humano y no una lectura del Excel.

## 7. Los PDF: dónde acabaron

Movidos (`mv`, no copiados) de `evals/fixtures/inputs/SALMEDINA_<n>.pdf` a
**`evals/inputs/albaranes/<caso_id>.pdf`**, los siete.

**Ojo: no es la ruta que decía el encargo** (`evals/fixtures/inputs/albaranes/`).
Usé la que mandan a la vez el código y la documentación:
`evals/procesos/sv2_extraccion.py:36` → `RUTA_ALBARANES = RAIZ_REPO / "evals" /
"inputs" / "albaranes"`, el `LEEME` de IA1 (*«déjalo en
evals/inputs/albaranes/»*) y el `README`. En `evals/fixtures/inputs/` el runner
no los habría encontrado nunca.

```
$ git check-ignore -v evals/inputs/albaranes/RES-001.pdf evals/inputs/albaranes/RES-007.pdf
.gitignore:16:*.pdf     evals/inputs/albaranes/RES-001.pdf
.gitignore:16:*.pdf     evals/inputs/albaranes/RES-007.pdf
$ git status --porcelain evals/     → (vacío)
```

Siguen ignorados y git no ve nada nuevo. De paso, la carpeta **versionada**
`evals/fixtures/inputs/` ya no contiene documentos de proveedor.

## 8. PARADA: hay un PDF en el índice de git (no es mío)

El encargo manda parar y decirlo. Hay **uno**, y es anterior a este trabajo:

```
$ git ls-files "*.pdf"
services/albaranes-api/worker_input/0695 - Albaranes 2026.03.09-13-16.pdf
$ git log --oneline -1 -- "services/albaranes-api/worker_input/0695 - ...pdf"
df01ef4 Importa albaranes-api desde el repo albaranes-api (rama proveedor, HEAD a8729aa)
```

Entró con la importación del repositorio `albaranes-api`, no con F-043. Es un
albarán de la obra 0695 versionado en `worker_input/`. **No lo he tocado**:
sacarlo del índice es una decisión del humano (y el historial ya lo contiene, así
que un `git rm` no lo borra del pasado). `git ls-files "*.xlsx"` sale **vacío**:
ningún libro de ground truth está versionado.

## 9. Qué falta para que T30 sea ejecutable en modo completa

**No lo es todavía.** Cuatro cosas, de las cuales esta tarea resuelve una:

1. ~~Los PDF en `evals/inputs/albaranes/<caso_id>.pdf`~~ → **hecho** (§7).
2. **`IA1_extraccion.xlsx` e `IA2_contexto.xlsx` rellenos** → bloqueado aquí.
   Sin ellos, IA1 e IA2 salen con los 7 casos `OMITIDO` = `NO_EVALUABLE`, que no
   es verde. Se desbloquea eligiendo A o B (§4); con la decisión tomada, rellenar
   los dos libros y correr el conversor es trabajo de una sesión corta.
3. **Propagar las CONDICIONES al `contexto_linea`** en
   `evals/procesos/sv6_build.py` y `evals/procesos/sv5_valoracion.py` — el
   agujero ya documentado en `progress/impl_F-043_evals_banco.md` §5, que hace
   que los importes salgan multiplicados por 6. Sigue abierto; no es de este
   encargo.
4. **Claves LLM en el entorno** y `--con-llm`, que autoriza el humano. **No se
   lanzó nada con `--con-llm`**: cero euros gastados.

## 10. Ficheros tocados

- `evals/inputs/albaranes/RES-00{1..7}.pdf` — **nuevos, NO versionados**
  (movidos desde `evals/fixtures/inputs/`).
- `progress/impl_F-043_evals_ia1_ia2.md` — este informe.
- `progress/current.md` — nota del bloqueo.

Sin cambios en `services/`, `harness/`, `evals/*.py` ni en ningún fixture JSON.
Los `.xlsx` de `ground_truth/` **no se han modificado**: su `sha256` sigue
siendo el que ya está en los `_indice.json`, así que no hay deriva libro ↔
fixtures que arreglar.

## 11. Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`bash harness/init.sh`) | **556 passed**, 0 fallos |
| Tiempo de la suite raíz | 196,69 s (3 min 16 s) |
| Cobertura de líneas cambiadas | **89,8 %** (633/705, umbral 80 %, nivel crítico) |
| Veredicto de `init.sh` | **ENTORNO LISTO** (verde; avisos preexistentes) |
| PDF leídos y transcritos | 7/7 |
| LER del Excel confirmados contra el papel | **7/7 coinciden** |
| Filas `DEDUCIDA` en las 11 filas SALMEDINA | **0** |
| Casos escritos en IA1 / IA2 | **0 / 0** (bloqueado; los índices siguen en 0) |
| `.xlsx` en el índice de git | **0** |
| `.pdf` en el índice de git | **1, preexistente** (§8) |
| Llamadas a LLM / coste | **0 / 0 €** |

**Fase RED**: no aplica — esta tarea no escribe código ni tests; su artefacto es
ground truth, y además quedó bloqueada antes de producirlo. **Mutación y
cobertura de líneas cambiadas**: no aplican, no hay líneas de Python nuevas (la
cobertura de la tabla es la del estado de la rama, no de este trabajo).

## 12. Lo que necesito del humano

Una respuesta a §4: **¿Opción A o B?** Y de paso, dos confirmaciones que van
con ella:

1. ¿Corrijo `SS-0801977` → `SS-0001977` en los fixtures de RES-005 (§3)?
2. Si es la Opción A, ¿alineo `INPUTS.LINEAS_ALBARAN.descripcion` con lo
   impreso, o lo dejo como está asumiendo que IA1 e INPUTS describen la misma
   línea con textos distintos?
