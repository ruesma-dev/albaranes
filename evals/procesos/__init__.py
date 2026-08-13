# evals/procesos/__init__.py
"""Adaptadores que componen servicios reales para los evals.

Cada módulo de aquí se ejecuta en SU PROPIO subproceso: sv2, sv5 y sv6 usan
paquetes de primer nivel con el mismo nombre (`application`, `domain`…) y no
pueden convivir en un mismo intérprete. El subproceso inserta en `sys.path` la
raíz de su servicio, hace el trabajo y devuelve JSON por stdout.

Nada de esto toca la BBDD ni SharePoint: los servicios se componen por la
costura que ya tienen (contexto o envelope ya construido), como documenta
`specs/F-011-evals-ia/design.md`.
"""
