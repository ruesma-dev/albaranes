<!-- progress/current.md -->
# Trabajo en curso

## Cierre de sesión — 2026-08-21 (sesión del 20 y 21 de agosto)

Sesión entera dedicada al **arnés**: **F-038, F-039 y F-040 cerradas**, aprobadas,
mergeadas en `dev`, subidas y portadas a `arnes-base`. El detalle de cada una
está en `progress/history.md`; aquí solo queda lo vivo.

La suite del monorepo pasó de **305 a 530 tests**; la de `arnes-base`, de 47 a
**263**.

### Lo primero al abrir la próxima sesión

1. **`git push` de `arnes-base`**: **4 commits locales** (la 1.7.2).
   `git -C C:\Users\pgris\PycharmProjects\arnes-base push origin main`.
2. **F-036 (residuos)**: lo único de toda la lista que **vale euros**, y lleva
   dos días esperando. Ver la sección de abajo; la decisión del humano del
   19-ago ya está tomada y solo falta implementarla.
3. Después, **F-041** (el quinto defecto de la campaña, `critico`, prioridad 2).

---

## Estado del arnés

| Repositorio | Versión | Estado |
|---|---|---|
| `arnes-base` | **1.7.2** | F-038 (1.7.0), F-039 (1.7.1) y F-040 (1.7.2) portadas. Las dos primeras **pusheadas**; la **1.7.2 son 4 commits locales SIN SUBIR**. Destino: 263 passed, instalador 65 verde |
| `albaranes` | **1.6.1** sellado, con el código de F-038, F-039 y F-040 dentro | **El sello miente desde hace tres features.** Le faltan la 1.6.2 y la 1.6.3, en particular **el arreglo del bytecode envenenado** (mutantes «muertos» falsos). Se arregla actualizándolo con el instalador a la 1.7.2 |
| `porcentajes`, `postventa-incidencias` | 1.5.2 | sin actualizar |
| `datamart-seg-anual` | 1.5.0 | sin actualizar |
| `partes` | 1.4.0 | sin actualizar; se saltaría **siete** versiones |

### El hilo conductor de la sesión, por si sirve de guía

Un solo defecto con **cuatro caras**, todas cerradas: la campaña de mutación
diciendo «todo bien» **sin haber juzgado nada**. La invocación sin ruta que moría
en la recolección (F-038 T0), el flake de las filas de reloj (F-038 T17), la
guarda inalcanzable de `--ficheros ","` (F-039 CR-2) y la campaña con alcance
vacío por `--feature` (F-040 D4).

**La quinta cara sigue viva y tiene ficha: F-041.** `ResultadoSuite.verde` cuenta
`PYTEST_SIN_TESTS = 5` como verde, así que un mutante cuya suite no recogió ni un
test sale SUPERVIVIENTE en vez de «no juzgado». El sesgo es el seguro —solo
produce falsos supervivientes, nunca falsos muertos—, pero **mientras viva,
ninguna campaña de una sola pasada vale como evidencia sin contraste**. Esa regla
ya se aplicó dos veces y ahorró horas de máquina.

---

## Pendientes del humano

1. **`git push` de `arnes-base`** (4 commits de la 1.7.2). Lo demás está subido:
   `albaranes` tiene `dev` y `main` al día.
2. **Actualizar `albaranes` a la 1.7.2** con el instalador, y luego los otros
   cuatro proyectos. `partes` es donde más ficheros aparecerán «distintos»;
   desde F-035 el instalador ya no puede pisar estado.
3. **Verificaciones MANUAL arrastradas**: las 4 de F-002 (liberan el merge de
   F-003, aprobada en su rama desde hace días), y las de F-019 y F-027.
4. **Reconciliar F-003 y F-004 antes de arrancarlas** (su R4 conserva el cálculo
   que F-019 corrigió).
5. **Histórico mal valorado en BBDD**: sin backfill por diseño; se sanea
   revalorando desde sv4. Falta decidir cuáles.
6. **NADA está desplegado**: producción corre imágenes del 24 de julio, o sea
   **sin F-002, F-019 ni F-027**.
7. **`evals/fixtures/inputs/` vacío**: mientras lo esté, la puerta de rutas
   sensibles se queda en `aviso`.
8. **Retirar de la F-010 del otro proyecto** las dos reglas del arnés (hoy en la
   ficha de F-038).
9. **`progress/mutacion_F-011.md` se queda invalidada** (decisión del 20-ago):
   305 mutantes y 133 supervivientes medidos con la invocación rota, no se
   repiten. Consecuencia: **la puerta de evals de F-011 no tiene hoy ninguna
   medición de mutación válida detrás**.

---

## LO QUE TOCA DINERO, y sigue sin integrar: residuos (F-036)

Informe completo en `progress/revision_residuos_salmedina_20260819.md`. Es lo
único de toda la lista que vale euros, y por eso **debería ir antes que F-038 y
que actualizar los otros proyectos**.

Siete albaranes de SALMEDINA, contrastados contra el Excel del administrativo,
con obra y contrato ya puestos a mano por el humano:

| Albarán | Sistema | Ground truth | |
|---|---|---|---|
| SS-0000168, SS-0003935 | 120,00 € | 120,00 € | correctos |
| SS-0025146 | 136,00 € | 136,00 € | correcto |
| SS-0000589 | 120,00 € | **171,00 €** | falta el incremento LER |
| SS-0026122 | 272,00 € | **260,00 €** | tarifa de 9 m³, y de OFERTA (F-017) |
| SS-0003967 | **540,00 €** | **210,00 €** | ×2,6 |
| SS-0801977 | **720,00 €** | **210,00 €** | ×3,4 |

**Causas, ya diagnosticadas:**

1. **El enrutado del prompt de fase 2 falla**: el SS-0003967 recibió
   `albaran_revision_fase2_es` (genérico) en vez de `..._residuos`. Sin
   `tipo_familia` ni `volumen_m3`, la regla de contenedores ni se invoca y el
   importe sale multiplicado por la capacidad del contenedor.
2. **El scorer del merge de contexto tira los campos de residuos**:
   `contexto_linea_merger._score_contexto()` puntúa **solo cinco campos** —los
   originales del modelo— e ignora `codigo_ler`, `volumen_m3`, `peso_toneladas`,
   `contenedores`, `contenedores_entregados`, `contenedores_retirados`,
   `carga_incompleta` y `exceso_declarado_min`. Un contexto que solo traiga
   datos de residuos puntúa **0 y se descarta entero**. Es la explicación más
   plausible del SS-0801977 (falta confirmarla en BBDD).
3. **Los incrementos por LER no se emiten nunca**, aunque están cargados en
   `contrato_lines`.
4. **Efecto perverso**: en el SS-0003967 el matcher eligió como línea principal
   el propio INCREMENTO LER (match exacto por el código LER en su descripción)
   en vez del contenedor.

**DECISIÓN DEL HUMANO, 2026-08-19, pendiente de implementar**: en
`calcular_contenedores_residuos`, **el volumen manda sobre la resta
entrada/salida**. Orden nuevo: (1) contenedores explícitos, (2)
`ceil(volumen_m3 / tamaño)`, (3) resta entregados − retirados. Hoy la resta es
la 2 y el volumen la 3. Hay que tocar `residuos_container_calc.py` (y su
docstring), el prompt de sv5 (`config/prompts.yaml` ~1024, que documenta el
orden viejo) y los tests de la prioridad 2. **Asunción por confirmar**: los
contenedores explícitos siguen siendo prioridad 1.

**Lo que sí está bien**: la regla de contenedores existe y es correcta —lee el
tamaño del contrato (6 por defecto, admite 8), redondea al entero superior—, y
IA2 extrae `volumen_m3` y `peso_toneladas` bien en 6 de 7. Ojo con **F-024**: al
extraer `unidad_medida`, los casos que hoy aciertan pueden pasar a valorar ×6.

**Sin trazabilidad**: las razones de `calcular_contenedores_residuos` no se ven
en sv4. El revisor no puede saber si la regla se aplicó ni con qué tamaño; los
720 € malos se le presentan igual que los 120 € buenos. Y los motivos de
revisión **no se recalculan**: el SS-0801977 sigue mostrando
`proveedor_cif_no_casa` con el CIF viejo después de corregirlo.

Altas relacionadas: **F-036** (los dos defectos, rigor `critico`), **F-037**
(guardado inmediato al seleccionar contrato, pedido por el humano).

---

## Notas operativas (valen para cualquier sesión)

- **Nada en paralelo**: dos suites a la vez tumban el proceso en Windows
  (`0xC0000142`). Y **una campaña de mutación muta el árbol principal**: mientras
  corra, no lanzar `init.sh` ni tests. Desde la 1.6.0 hay centinela que lo avisa.
- **Un agente que se cuelga no pierde el trabajo commiteado.** Esta sesión tuvo
  tres cuelgues (dos de watchdog, uno `ECONNRESET`) y en los tres bastó
  reanudar. Ayuda que commiteen por tarea.
- **Un agente con demasiado contexto se cuelga en bucle**: el reviewer de F-034
  murió dos veces seguidas sin escribir nada. Lanzar uno **nuevo y acotado**
  —diciéndole exactamente qué leer— lo resolvió y costó 101k en vez de 173k.
- **No ensuciar el árbol mientras un reviewer trabaja**: C5 exige árbol limpio.
  Pasó dos veces esta sesión, y una costó una pasada entera.
- **Los agentes no deben usar scripts que reescriban ficheros versionados**;
  copias en el scratchpad. Un artefacto de finales de línea provocó un cuelgue.
- **Cuidado con las rutas de Windows en heredocs de Python**: `\U` de
  `C:\Users` se interpreta como escape unicode y mata el script.

- **La máquina es compartida y se nota.** Dos veces esta sesión otra sesión
  (campañas de `datamart-seg-anual`) triplicó los tiempos: la suite pasó de 51 s
  a 149 s y las campañas se invalidaron solas. La suite **nunca estuvo roja**.
  Antes de lanzar una campaña, comprueba que no hay nada más corriendo.
- **Una campaña paralela ralentiza su propia suite**: ~51 s en reposo, 97,5 s con
  1 worker, 119-121 s con 3. Desde F-040 el timeout se deriva de esa medición, así
  que ya no hace falta pasar `--timeout` a mano; si te hace falta, es un síntoma.
- **Un comando de verificación guardado en `progress/` puede caducar**: el de la
  campaña paralela usaba `--feature F-038`, y al mergear F-038 su diff pasó a ser
  vacío. Si guardas un comando, guarda también de qué depende.

---

## Deudas menores que sobreviven (ninguna bloquea)

1. **RM2 solo dispara a 10×** y, con «Tiempo total» > 60 s, tampoco se reejecuta:
   un informe «solo» cinco veces demasiado rápido pasaría. Aire deliberado.
2. **Marcas `[ADAPTAR]` sin resolver** en las specs de F-034 y F-035 (aviso de
   `init.sh`, no bloquea).
3. **`ruff`: 1108 avisos** de deuda previa en el monorepo.
4. **sv1-email e `infra` sin directorio de tests**: nadie comprueba lo suyo.
