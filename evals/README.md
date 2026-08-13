<!-- evals/README.md -->
# Evals de IA — ground truth del pipeline

Banco de casos con resultado esperado para las cuatro fases de IA. La
implementación del runner y su integración con el arnés es la **feature
F-011**; esta carpeta define el contrato de datos que la alimenta.

## Estructura

- `ground_truth/IA1_extraccion.xlsx` — salida esperada de IA1 (cabecera +
  líneas) por albarán. Pestañas por tipología.
- `ground_truth/IA2_contexto.xlsx` — `contexto_linea` esperado por línea y
  tipología (formato largo campo/valor).
- `ground_truth/IA3_valoracion.xlsx` — valoración esperada: matches por
  línea, sintéticas que DEBEN emitirse y sintéticas PROHIBIDAS (vetos).
- `ground_truth/IA4_conciliacion.xlsx` — conciliación esperada de las líneas
  sin match.
- `ground_truth/INPUTS.xlsx` — entrada de los casos de IA3/IA4 (líneas de
  albarán, líneas de contrato y condiciones campo/valor).
- `inputs/albaranes/` — los ficheros de albarán (`<caso_id>.pdf`/`.jpg`) que
  son la entrada de IA1/IA2.

Cada pestaña LEEME explica cómo rellenar su libro. Convenios comunes:
celda vacía = el eval espera null; `?` = ese campo no se compara;
`caso_id` con prefijo de tipología (GEN/HOR/MOR/RES/BOM/COM/ALQ-NNN).

## Qué se versiona y qué no

Los `.xlsx` y los PDF **no se versionan** (regla del arnés: ofimática fuera
de git; además contienen datos de proveedor). Lo que entrará en git cuando
F-011 se implemente son los **fixtures convertidos** (JSON) que el runner
genere a partir de estos libros, tras el barrido de datos sensibles del
checkpoint C3 bis. Hasta entonces, los libros viven aquí en el árbol de
trabajo y en la copia de seguridad que decida el humano.

## Diseño previsto (se detalla en la spec de F-011)

1. Conversor `xlsx → fixtures JSON` (uno por caso e IA), versionados.
2. Runner de evals: para IA1/IA2 invoca la extracción real (coste: llamadas
   a LLM; se lanza a demanda, no en cada init.sh); para IA3/IA4 permite
   además modo determinista contra las redes de sv6 sin LLM.
3. **Puerta del arnés**: declaración de rutas sensibles (prompts, clientes
   LLM, schemas, redes deterministas) — si el diff de una feature las toca,
   el reviewer exige la ejecución de los evals además de los tests normales.
   El mecanismo genérico se porta a `arnes-base` (regla de propagación).
