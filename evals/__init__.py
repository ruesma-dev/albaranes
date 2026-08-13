# evals/__init__.py
"""Evals de IA del monorepo: ground truth, conversor, comparador y runner.

Herramienta transversal del repositorio, como `harness/`: no es un servicio y
no aparece en `harness/servicios.json`. La lógica pura (conversor, comparador,
barrido, criticidad, informe) no importa nada de `services/`; los adaptadores
que sí componen servicios reales viven en `evals/procesos/` y se ejecutan cada
uno en su propio subproceso.
"""
