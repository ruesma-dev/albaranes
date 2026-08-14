<!-- progress/current.md -->
# Trabajo en curso

## Estado tras el cierre de F-002 (2026-08-14)

- **F-002 done** (APPROVED). Resumen en `progress/history.md`.
- **BLOQUEO deliberado de la cola**: antes de arrancar F-003 conviene que el
  humano ejecute la prueba LOCAL de F-002 (5 verificaciones MANUAL, guion en
  `progress/impl_F-002.md` §T12) — valida en real las escrituras a BBDD que
  los tests solo cubren con dobles. El despliegue de F-002 requiere su
  autorización expresa (secret de sv2 + azure-apps/albaranes.md en ese
  mismo trabajo).
- Cola siguiente: F-003..F-007 (spec_ready con decisiones) → F-013
  (registro en Sigrid, critico) → F-008/F-009/F-010.

## Pendientes del humano

- Las 5 verificaciones MANUAL locales de F-002 (obra 0937, HORPRESOL,
  fecha 2023, email_received_datetime por colas, nº de obras tras el
  filtro >0450).
- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base).
- Hallazgo lateral de F-002: el `.gitignore` de sv2 ignora `*.example` y su
  `.env.example` actualizado no entra en git — decidir si se corrige.
- Decisión de dominio de F-011 (desviación 1): ¿sv6 descarta las sintéticas
  prohibidas o basta precio null + revisión?
- Rellenar los libros de evals/ground_truth/ (con casos, la puerta de rutas
  sensibles puede subirse a `bloqueo`).
