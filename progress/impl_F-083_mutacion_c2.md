<!-- progress/impl_F-083_mutacion_c2.md -->
# F-083 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-083` el 2026-10-21 00:01.

> ## ⚠ CAMPAÑA NO VÁLIDA
>
> La línea base de cierre EXPIRÓ en C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_nf8aebwe/wk_0: se agotaron los 600 s concedidos. Ojo, la suite NO falló y NO hay ningún test roto que buscar: se quedó sin tiempo, que es otra cosa. Aun así los números de esta campaña no valen, porque no se ha podido comprobar que la base siguiera verde al terminar.
  Qué hacer: baja los workers (--workers N: cada worker corre una suite entera y todas compiten por la misma máquina) o sube el SUELO 'mutacion.timeout_por_mutante_s' de harness/rigor.json. No toques la suite.
>
> **No cierres la feature con estos números.** Arregla la línea base y repite la campaña.

## Alcance

Origen del diff: **rama** (`7facc862439cb9c35499e33bf06b9bf5731854fb` .. `feature/F-083-comparar-modelos`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/comparar_modelos.py` | 665 |
| `evals/costes.py` | 437 |
| `evals/decision.py` | 202 |
| `evals/informe_modelos.py` | 238 |
| `evals/procesos/medidor.py` | 210 |
| `evals/procesos/sv2_extraccion.py` | 7 |
| `evals/procesos/sv2_modelos.py` | 127 |
| `evals/procesos/sv5_modelos.py` | 96 |
| `evals/procesos/sv5_valoracion.py` | 61 |
| `evals/runner.py` | 51 |
| `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 11 |
| **Total** | **2105** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 366 |
| Mutantes evaluados | 366 |
| Muertos | 357 |
| Supervivientes | 0 |
| Timeouts | 9 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 52052.9 s |
| SHA de HEAD medido | `0912abd313ef431697d6b40648ebb266cba13b97` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_nf8aebwe/wk_0` | 489.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_nf8aebwe/wk_1` | 460.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_nf8aebwe/wk_2` | 474.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_nf8aebwe/wk_2/services/albaranes-comun` | 156.2 |
| Media por mutante evaluado (s) | 142.2 |
| Timeout efectivo por mutante (s) | 980 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

- `evals/comparar_modelos.py:589` [entero] return 3 -> return 4
- `evals/comparar_modelos.py:620` [booleano] analizador.add_argument("--fase", required=True, choices=FASES) -> analizador.add_argument("--fase", required=False, choices=FASES)
- `evals/comparar_modelos.py:623` [entero] analizador.add_argument("--repeticiones", type=int, default=1, help="por defecto 1") -> analizador.add_argument("--repeticiones", type=int, default=2, help="por defecto 1")
- `evals/comparar_modelos.py:638` [not] if not opciones.lista_modelos: -> if opciones.lista_modelos:
- `evals/decision.py:115` [aritmetico] respondidas += 1 -> respondidas -= 1
- `evals/decision.py:180` [comparacion] elegido.fallos <= MEJORA_FALLOS * ref.fallos -> elegido.fallos < MEJORA_FALLOS * ref.fallos
- `evals/decision.py:180` [aritmetico] elegido.fallos <= MEJORA_FALLOS * ref.fallos -> elegido.fallos <= MEJORA_FALLOS // ref.fallos
- `evals/decision.py:181` [comparacion] and elegido.coste_por_albaran <= MEJORA_COSTE * ref.coste_por_albaran -> and elegido.coste_por_albaran < MEJORA_COSTE * ref.coste_por_albaran
- `evals/informe_modelos.py:67` [comparacion] return re.fullmatch(re.escape(pedido) + r"(-\d.*)?", servido) is None -> return re.fullmatch(re.escape(pedido) + r"(-\d.*)?", servido) is not None

