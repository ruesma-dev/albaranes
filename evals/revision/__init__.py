# evals/revision/__init__.py
"""Volcado de la revisión manual del humano al banco de evals (F-045).

De `evals_summary.xlsx` —una tabla plana, una fila por línea de albarán, que
el humano rellena a mano— a los seis libros de `evals/ground_truth/`, que es
la única puerta a los fixtures (el conversor barre datos sensibles antes de
escribir nada). Este paquete NO genera fixtures: escribe libros.

El reparto de cada columna entre IA1, IA2, IA3, IA4, `INPUTS` y
`RESULTADO_FINAL` lo fija `specs/F-045-banco-evals-revision-manual/design.md`
§3, que es normativa. Aquí solo se implementa.

Dos convenios de vacío **inversos** que conviene no confundir:

- en el **Excel**, un comentario vacío dice que ese caso salió BIEN y hay que
  seguir comprobándolo (caso de no regresión); nunca produce un `?`;
- en los **libros**, una celda vacía dice «ese dato no aparece en el albarán»
  (se compara contra `null`) y `?` dice «no compares».
"""
