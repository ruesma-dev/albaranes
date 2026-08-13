<!-- progress/current.md -->
# Trabajo en curso

## F-011 — Evals de IA con ground truth y puerta en el arnés (in_progress, 2026-08-13)

- Rama: `feature/F-011-evals-ia`. Spec aprobada por el humano con sus
  decisiones incorporadas (D1–D7 en `requirements.md`).
- **Implementación terminada**: T1–T14 de `tasks.md` en `[x]`, un commit por
  tarea. Informe completo en `progress/impl_F-011.md` (ficheros tocados,
  fase RED con trazas reales, evidencias y desviaciones).
- Propagación a `arnes-base` hecha (T11): commit local `1.4.0` en
  `C:\Users\pgris\PycharmProjects\arnes-base`. **Sin push**: lo decide el
  humano.

### Desviaciones respecto a la spec (justificadas, para la PARADA 2)

1. **Las sintéticas PROHIBIDAS no desaparecen del build de sv6.** El diseño
   daba por hecho que las redes de sv6 «vetan» esas líneas y que el eval
   podía assertar que «NO aparecen en los records finales». Medido contra el
   código real: `ValuationBuilder` **no descarta ninguna línea**; a una
   sintética que el contrato no tarifa le deja el precio a `null` y la manda
   a revisión (`modifier_identified_no_tariff`), pero el record sigue ahí.
   El eval se ha implementado como dice la spec —si la prohibida aparece, el
   caso es ROJO— de modo que cuando haya casos reales el informe dirá la
   verdad en vez de estar afinado para pasar. **Decisión pendiente del
   humano**: si lo correcto es que sv6 las descarte, eso es un cambio en sv6
   (otra feature); si lo correcto es que queden a revisión, hay que relajar
   la lectura de la TABLA 3. Detalle y traza en `progress/impl_F-011.md`.
2. **Campos del ground truth no observables por el extremo-a-extremo.**
   `RESULTADO_FINAL` TABLA 1 pide obra, proveedor, CIF, fecha y nº de
   albarán, que NO salen del build de sv6 (salen de la extracción, y su eval
   es el libro IA1). No se comparan en silencio: se declaran en el informe
   como «campos no observables en esta corrida».
3. **Campaña de mutación con `PYTEST_ADDOPTS=--ignore=services`.** El arnés
   1.3.0 de este repositorio lanza la suite de la raíz sin acotar ruta, así
   que cada mutante arrastraba los ~120 s de la suite del servicio `comun`,
   que no puede cazar ningún mutante de F-011. Sin código del arnés tocado.

### Verificaciones MANUAL (humano) pendientes

- **Pasada completa de evals**: `python -m evals.runner --con-llm --feature
  F-011`. Cuesta llamadas LLM reales y hoy daría NO_EVALUABLE (los seis
  libros de `evals/ground_truth/` están sin casos). Se lanza cuando el
  humano los rellene.
- **Diff en `arnes-base`**: `git -C C:/Users/pgris/PycharmProjects/arnes-base
  diff HEAD~1` y decidir el push.
