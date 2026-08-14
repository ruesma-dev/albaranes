<!-- progress/current.md -->
# Trabajo en curso

## F-002 — Identificación de obra y proveedor (in_progress, 2026-08-14)

- Rama: `feature/F-002-obra-proveedor` (recreada desde `dev` con todo el
  arnés: evals+puerta, portero con caché, mutación paralela). Spec aprobada
  con decisiones en `specs/F-002-obra-proveedor/`.
- PARADA 1 confirmada por el humano con una REGLA DURA añadida:
  **SIN DESPLIEGUE**. Nada de Azure (ni az, ni deploy.ps1, ni build de
  imágenes, ni secrets) hasta que el humano pruebe en local y lo autorice
  expresamente. Las tareas de la spec ligadas al despliegue (secret de
  sv2, azure-apps/albaranes.md) quedan marcadas como pendientes de
  despliegue, no se ejecutan.
- Primera feature que toca servicios reales (sv2 y sv3): verificación
  automática con fakes + verificaciones MANUAL del humano en el pipeline
  LOCAL (Azurite, según infra/docs/levantar-pipeline-local.md).
- Implementer lanzado.
- **Implementación TERMINADA (2026-08-14)**: T1–T8, T10 y T11 hechos; T9
  parcial (la parte de `azure-apps/albaranes.md` queda
  pendiente-de-despliegue por la regla dura, con justificación en
  `tasks.md`); T12 es MANUAL del humano. Informe completo en
  `progress/impl_F-002.md`. Pendiente el reviewer.
- `bash harness/init.sh` → **ENTORNO LISTO**. Cobertura del diff 82,1 %
  (umbral 80). Mutación: 108 mutantes, 95 muertos, 13 supervivientes, todos
  analizados en `progress/mutacion_F-002.md`.
- Puerta de rutas sensibles en **AVISO** (esperado): `prompts.yaml` de sv2 es
  ruta sensible y los libros de evals están vacíos → el runner da
  `NO_EVALUABLE` (`progress/evals_F-002.md`). No bloquea por decisión D5 de
  F-011.

### Desviaciones respecto a la spec (justificadas)

1. **Scorer propio para la propuesta de proveedor (R9).** El design fijaba
   `_match_score(nombre_leido, candidato) >= min_score`, pero con eso el caso
   de referencia de la propia R9 («GRUPO OTTO HORPRESOL» vs «HORPRESOL,
   S.L.») puntúa 0,33 y NO habría generado propuesta: el design se
   contradecía con su caso. Se añadió `_score_razon_social`, simétrico y
   tolerante a puntuación, usado SOLO en la red nueva (los caminos previos
   del resolver siguen con `_match_score`: cero regresión).
2. **`tests/conftest.py` con `sys.path` explícito**, no vacío: un conftest
   vacío en `tests/` no hace importables `application/`, `domain/` ni
   `infrastructure/` si la suite se lanza desde otro directorio.
3. **Lógica de las marcas de revisión extraída a funciones puras** en el
   repositorio, para poder probar idempotencia y dedupe sin BBDD.
4. El guard de año NO retira su nota cuando la fecha vuelve a estar en rango
   (R7 solo lo exige para obra). Límite consciente, anotado en el informe.

### Hallazgo lateral (decisión del humano)

`services/albaranes-api/.gitignore` ignora `*.example`: el `.env.example` de
sv2 se ha actualizado en disco pero NO entra en git. Parece un descuido de
ese `.gitignore`; no se ha cambiado por cuenta propia.

## Pendientes del humano (heredados)

- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base: 1.4.0 + portero rápido + mutación paralela, todo revisado).
- Decisión de dominio de F-011 (desviación 1): ¿sv6 debe DESCARTAR las
  sintéticas prohibidas o basta precio null + revisión?
- Rellenar los libros de evals/ground_truth/ y lanzar la primera pasada
  real: `python -m evals.runner --con-llm`.
