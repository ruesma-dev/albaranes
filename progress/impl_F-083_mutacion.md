<!-- progress/impl_F-083_mutacion.md -->
# F-083 · Campaña de mutación (T16, rigor `critico`)

> **Actualización 2026-10-21 · ya hay campaña VÁLIDA:** `progress/mutacion_F-083.md`, del reviewer, sobre
> `96a59a3`, con 3 workers: **366 mutantes, 366 muertos, 0 supervivientes**, 0 timeouts, 21.907 s. Está
> en el inventario de F-039. Lo que sigue es la historia de las dos campañas anteriores, que no valen
> como evidencia.

## Resultado

**366 mutantes; 0 supervivientes en las dos campañas completas. Cada mutante sale `muerto` en al menos
una de ellas.** Pero la herramienta marca las dos como **«CAMPAÑA NO VÁLIDA»**: en las dos se agotó la
línea base de cierre. Ese tiempo es fijo, 600 s (suelo 120 × 5), y la suite no falló: se quedó sin tiempo.
Por eso estos números no bastaban para cerrar la feature: hacía falta una tercera campaña, que es la
válida del reviewer.

| Campaña | Comando | Commit | Muertos | Supervivientes | Timeouts | Duración | Veredicto de la herramienta |
|---|---|---|---|---|---|---|---|
| c1 | `python -m harness.mutacion --feature F-083 --workers 4 --salida progress/mutacion_F-083_arnes.md` | `6c40149` | 363 | **0** | 3 | 23.383 s | NO VÁLIDA: base de cierre > 600 s en `wk_3` |
| c2 | `python -m harness.mutacion --feature F-083 --workers 3 --salida progress/mutacion_F-083_arnes.md` | `0912abd` (el mismo código) | 357 | **0** | 9 | 52.053 s | NO VÁLIDA: base de cierre > 600 s en `wk_0` |

- Informes íntegros de la herramienta, tal como los escribió: `progress/impl_F-083_mutacion_c1.md` y
  `progress/impl_F-083_mutacion_c2.md`. Se renombraron desde `progress/mutacion_F-083_arnes.md` para que
  no cuenten como campaña: el inventario de F-039 no tiene veredicto para «no válida, se repetirá», y
  apuntarlas como `VÁLIDA` o `INVÁLIDA (no se repone)` sería falso.
- Veredicto de cada mutante en las dos campañas: `progress/impl_F-083_mutantes.md`.
- Alcance: el diff de la rama contra `dev` `7facc86`, 11 ficheros. Los de `evals/` se juzgan con la suite
  de la raíz y `claude_messages_client.py`, con la de comun.

## Por qué no valen: la máquina estaba compartida

Durante las dos campañas corrían a la vez las campañas de mutación y las suites de otros proyectos
(`partes` F-050, `mcp-bbdd` F-028, `porcentajes`, `datamart-seg-anual`, `postventa-incidencias`): 20–46
procesos `python.exe` de suites ajenas, vistos con `Get-CimInstance Win32_Process`.

- La línea base de c2 tardó 460–490 s con 3 workers. En c1 tardó 290 s con 4.
- Los mutantes de c2 se juzgaron a 1–6 por cada 10 min, según la carga.
- Los timeouts no se repiten de una campaña a otra:
  - los 9 de c2 son `muerto` en c1;
  - los 3 de c1 son `muerto` en c2;
  - salen en grupos de 3 seguidos (68–70 en c2, 362–365 en c1), uno por worker y a la vez.

  Eso es carga, no mutantes que cuelguen: todos son cambios que hacen fallar un test enseguida (un
  `required=False`, un `<=` → `<`, un `+=` → `-=`).

| Mutante con un timeout | c1 | c2 |
|---|---|---|
| `comparar_modelos.py:589` `return 3` → `4` | muerto | timeout |
| `comparar_modelos.py:620` `required=True` → `False` | muerto | timeout |
| `comparar_modelos.py:623` `default=1` → `2` | muerto | timeout |
| `comparar_modelos.py:638` `not` eliminado | muerto | timeout |
| `decision.py:115` `+=` → `-=` | muerto | timeout |
| `decision.py:180` `<=` → `<` y `*` → `//` | muerto | timeout |
| `decision.py:181` `<=` → `<` | muerto | timeout |
| `informe_modelos.py:67` `is None` → `is not None` | muerto | timeout |
| `sv5_valoracion.py:260` `False` → `True` | timeout | muerto |
| `sv5_valoracion.py:270` `True` → `False` | timeout | muerto |
| `sv5_valoracion.py:390` `or` → `and` | timeout | muerto |

## Antes de la campaña: pre-pasada dirigida

Script del scratchpad, `premut.py`, fuera del repo: cada mutante contra solo los `tests/test_f083_*`
que lo pueden cazar, para encontrar huecos rápido.

Encontró 56 supervivientes, todos resueltos en el commit `6c40149` antes de c1:

- **Tests nuevos `test_f083_t16_*`** para:
  - valores por defecto de `Metricas`;
  - `medir` sin repeticiones;
  - escritura de caché como entrada;
  - columnas de las tablas del informe;
  - «mantener» con otro mejor en la banda;
  - tokens con salida 0;
  - commit desconocido;
  - tope de textos;
  - caché igual a la entrada;
  - dataclasses inmutables;
  - tope exactamente igual a la estimación (R17 y R18 en la frontera);
  - restante de menos de 1 USD;
  - carpeta del resumen anidada;
  - JSON legible;
  - `--fase` obligatoria;
  - registro sin respuesta a cero;
  - carpeta del `.jsonl` anidada;
  - sv5 sin clave;
  - `sv5_valoracion.ejecutar_trabajo` con dobles;
  - clase del cliente por proveedor.
- **Formas que eliminan mutantes equivalentes**, sin cambio de comportamiento:
  - `Plan.repeticiones` y `cliente_llm` sin valores por defecto que nadie usa;
  - la preparación sin etiqueta de repetición;
  - `json.dumps` sin `ensure_ascii` en el stdin del hijo;
  - `subprocess.run` sin `text=True` redundante (ya lleva `encoding`);
  - `sys.path = [raíz, *sys.path]` en vez de `insert(0, …)`.

Los únicos que la pre-pasada dejó sin veredicto son los tres `if __name__ == "__main__"` → `!=` de los
puntos de entrada. Al importarse, lanzan `main()` y rompen la recolección; la herramienta lo resuelve
como `muerto` (base verde), y así salen en c1 y c2.

## Lo que faltaba (hecho por el reviewer el 2026-10-21)

Repetir la campaña con la máquina libre (sin campañas ni suites de otros proyectos), desde el worktree:

```
python -m harness.mutacion --feature F-083 --workers 3
```

Esa campaña sí deja `progress/mutacion_F-083.md`, que necesita su fila en
`progress/inventario_mutacion_F-039.md` (si no, `test_f039_r2_*` pone la suite en rojo).

Con la máquina en reposo, la línea base de la raíz tarda unos 150 s, lejos de los 600. La otra salida
que propone la herramienta es subir el suelo `mutacion.timeout_por_mutante_s` de `harness/rigor.json`.
Ese fichero es del arnés compartido y no lo toca esta feature: lo decide el humano.
