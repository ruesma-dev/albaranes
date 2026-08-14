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

## Pendientes del humano (heredados)

- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base: 1.4.0 + portero rápido + mutación paralela, todo revisado).
- Decisión de dominio de F-011 (desviación 1): ¿sv6 debe DESCARTAR las
  sintéticas prohibidas o basta precio null + revisión?
- Rellenar los libros de evals/ground_truth/ y lanzar la primera pasada
  real: `python -m evals.runner --con-llm`.
