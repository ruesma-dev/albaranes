Revisión incremental desde 53d769b (pasada 2) hasta HEAD `faea4a2` · CR-F1..CR-F4 (pasada 1: desde 9c70de2 hasta `0b04682`)

# F-048 · Review de los menores del bloque D (CR-D2..D4) y del bloque F (T32, T33, T35)

**Veredicto final (pasada 2): APPROVED.** El bloqueante 1 y los menores 1, 2 y 3 están cerrados.
**Rigor** `critico` (declarado): exige RED, cobertura ≥ 80 %, mutación (T34, fuera de esta review) y
evals (T40).

---

## Pasada 1 (compactada) · CHANGES_REQUESTED

- **Ejecutado**: `init.sh` exit 0 (raíz 865, cobertura 99,5 % 661/664, TAMAÑO OK); sv4 a mano 244
  passed; T35 `harness.tamano` exit 0; T32 `harness.rutas_sensibles` exit 3 (`aviso`, falta evals).
- **RED de CR-D4** reproducido en una copia: `11 failed, 5 passed`, igual que el informe.
- **CR-D2 y CR-D3**: cerrados. **CR-D4**: las cuatro decisiones son correctas (el `warning` depende solo
  del motivo, sv4 no escribe, la cabecera vacía no cuenta, `normalizar_codigo` de comun, `correo_unico`
  pinta como `info`).
- **T32**: la regla 15 coincide con D5 y con el código. El `DocumentoAlbaran` de sv5 es código muerto
  (CONFIRMADO). `azure-apps/albaranes.md` está bien y no contiene secretos.
- **Bloqueante 1**: `review_models.py:918` decía «el revisor cambió la obra» también cuando la cambia sv3
  (`HeaderResolverService._resolve_obra`, con `origen='deterministic'`, ya en la primera persistencia:
  papel `O937` → cabecera `0937`). sv4 no puede distinguirlo porque `update_document` no marca
  `manual`. Se pidió: texto sin sujeto, ajustar los tests y docstrings y añadir el caso de sv3.
- **Menores**: (1) faltaba `albaran_extraction_service.py` en `rutas_sensibles.json`; (2) la cadena de
  `ARCHITECTURE.md:235-236` estaba mal; (3) `.obra-cambiada` no tenía CSS.

---

## Pasada 2 · APPROVED

### Qué se ejecutó (resultados reales)

- **`bash harness/init.sh`** tal cual: exit 0, **ENTORNO LISTO**. Raíz `865 passed in 117.25s`.
  sv4 y el resto de servicios, en verde desde la caché («árbol sin cambios desde el último verde»).
  `PUERTA COBERTURA 99.5 % (661/664, umbral 80 %, nivel critico)`. `PUERTA TAMAÑO` OK (impl 212/220).
  `[AVISO] RUTAS SENSIBLES`: **11** rutas (antes 10), como se esperaba con CR-F2.
- **sv4 a mano** (`services/albaranes-front/.venv`): `246 passed in 3.54s` (244 + 2 tests nuevos).
- `git status` limpio antes del commit de esta review.

### RED de CR-F1 reproducido (copia en el scratchpad)

`git archive HEAD services/albaranes-front` con `review_models.py`, `document_detail.html` y
`styles.css` de `53d769b`, más los tests de HEAD, ejecutado con `-k "cr_d4 or cr_f1 or cr_f4"`:
**`8 failed, 10 passed, 45 deselected`**. Los fallos son:
- 5 `cr_d4_*` del modelo: `'Obra: el revisor cambió la obra a 0999…' != 'Obra: la cabecera lleva ahora 0999…'`.
- `cr_f1_*`: `+ Obra: el revisor cambió la obra a 0937; al extraer se fijó O937, la del papel.`
- `cr_d4_*` de la plantilla: `assert 'la cabecera lleva ahora 0999…' in '<div class="alert warning…'`.
- `cr_f4_*`: `re.search(...) → None`.

Coincide con el informe (`7 failed, 10 passed` sin `cr_f4` y `1 failed` con `cr_f4`). Con HEAD, en
verde.

### Bloqueante 1: CERRADO

- **Texto** (`review_models.py:924-927`): «Obra: la cabecera lleva ahora X (cambiada después de
  extraer); al extraer se fijó Y, …». No lleva sujeto, así que es verdad tanto si la cambió el revisor
  como si fue sv3.
- **Grep de «revisor»** en `review_models.py` y en `document_detail.html`: todo lo que queda está en
  docstrings y comentarios (`:888`, `:901`, `:914`, `:941`, plantilla `:145`), que ya dicen «el revisor
  o sv3». Ninguna cadena que se renderice lo nombra. Los tests lo fijan en dos niveles:
  `assert "revisor" not in bloque` en la plantilla y `not any("revisor" in aviso …)` en el modelo.
- **Caso sv3**: `test_f048_r35_vista_modelo.py::test_f048_cr_f1_si_la_cambio_sv3_el_aviso_no_culpa_al_revisor`
  cubre `correo_fuera_de_lista` con papel `O937`, `valor_final="O937"` y cabecera `0937`. Es el caso
  exacto de la pasada 1.
- **Coherencia**: el caso `O937` → `0937` sale como cambio. Es correcto, porque `normalizar_codigo` no
  iguala una letra O con un cero y la cabecera sí es otra respecto a lo que selló la extracción.
- Los docstrings (`:899-902`, `:940-943`) y el comentario de la plantilla (`:145-148`) están ajustados.
  El `warning` sigue dependiendo solo del motivo (R34) y sv4 sigue sin escribir (R35).

### Menores: CERRADOS

1. **CR-F2**: `albaran_extraction_service.py` está en `rutas_sensibles.json:35` y en
   `RUTAS_ANADIDAS_DESPUES` (`tests/test_f011_r19_r20_declaracion.py:208`), con su motivo. He recorrido
   `git diff dev..HEAD --stat` (103 ficheros). Todo fichero de producción que cambia lo que lee la IA o
   la obra final queda cubierto (`domain/models/**`, `prompts.yaml`, `llm/**`, `correo/**`,
   `origen_datos.py`, el resolver y el servicio de extracción). Lo que queda fuera es:
   - Fontanería sin decisión: `extract_albaran_pipeline.py` solo pasa `contexto_correo` y delega
     `obras_conocidas`; también el worker, `correo_adapter.py`, `encolar_extraccion.py`, sv1 y sv4.
   - Lógica determinista que fijan los tests unitarios: `albaran_confidence_service.py` de sv3, con
     dos disparadores cubiertos por `test_f048_r29_r31_*`; y la caché y el cliente de obras.

   **No falta ninguna ruta.**
2. **CR-F3**: `ARCHITECTURE.md:235-237` dice ahora «ningún módulo de producción la importa (solo
   `revision_models.py`, al que no importa nadie, y un test de F-043)». Coincide con el grep de la
   pasada 1.
3. **CR-F4**: `styles.css:1758-1763`: `.origen-datos.obra-cambiada .origen-aviso:first-of-type`. En la
   plantilla, los avisos son los únicos `<p>` del `div`, así que `:first-of-type` coge justo la línea
   del cambio. `base.html:27` carga la hoja. El test `cr_f4_*` la fija.

### Checkpoints (pasada 2, sobre el delta)

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés. **C3 bis** N/A: no se toca `docs/referencia/`.
- **C2** [x] una sola feature en `in_progress` · [x] rama `feature/F-048-…` · [x] `current.md` al día ·
  N/A `history.md`: nada pasa a `done`.
- **C3** [x] el delta de producción es solo de sv4 (modelo, plantilla y CSS) y de la documentación ·
  [x] primera línea con la ruta en los ficheros de código · [x] sin prints, secretos ni dependencias
  nuevas · [x] sin DDL.
- **C4** [x] CR-F1..F4 con tests `test_f048_*` y `test_f011_*` en verde · [x] sin red ni BBDD.
- **C4 bis**:
  - [x] rigor `critico` declarado.
  - [x] RED real (el de CR-F1, reproducido).
  - [x] cobertura 99,5 %.
  - **N/A mutación y RM1–RM6**, por encargo del líder: la mutación es T34 y se hace sobre la feature
    completa DESPUÉS de esta review. Con el bloqueante cerrado, el alcance de sv4 ya es estable (RM1).
  - [x] «Evidencias» completas en `impl_F-048.md:207-212`.
- **C4 ter** [x] `aviso` con motivo: las 11 rutas se evalúan en T40. **Bloqueará la review final** si
  falta `evals_F-048.md`.
- **C5** [x] commits `F-048 CR-F1..F4` · [x] árbol limpio · [x] `features.json` en `in_progress`.
  Siguen abiertos T34 y los bloques E y G.

### Trazabilidad

| Requisito / cambio | Tests |
|---|---|
| CR-F1 (R32, R33) | `r35::test_f048_cr_d4_si_la_obra_cambio_tras_extraer_…` (5) y `r35::test_f048_cr_f1_…` |
| CR-F1 en la plantilla | `r32_r34::test_f048_cr_d4_la_obra_cambiada_tras_extraer_se_pinta_distinto` |
| R34 / R35 | los de la pasada 1, en verde |
| CR-F2 | `tests/test_f011_r19_r20_declaracion.py` |
| CR-F4 | `r32_r34::test_f048_cr_f4_la_hoja_de_la_ficha_distingue_la_obra_cambiada` |

### Observación (no bloquea)

El test de CR-F4 busca en el CSS cualquier regla para `.origen-datos.obra-cambiada`. No mira qué hace
la regla. Es suficiente para lo que fija el menor, que es que la clase tenga estilo.

**Automejora** (propuesta de la pasada 1, sin aplicar; vale para `arnes-base`): en C3, añadir «un texto
que atribuye una acción a alguien ("el revisor cambió…") exige recorrer TODOS los escritores del
campo».
