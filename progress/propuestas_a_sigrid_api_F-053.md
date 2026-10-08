<!-- progress/propuestas_a_sigrid_api_F-053.md -->
# Propuestas de F-053 (albaranes) a sigrid-api · contrato del alta de albaranes

Escrito por el spec-author de F-053 v7 el 2026-10-06 (rama `feature/F-053-alta-sigrid`). Contra F-009 **v8** de
sigrid-api (`8a6ecab`, rama `feature/F-009-alta-albaran-compra`) y su `contrato_albaranes.md`, leídos en **solo
lectura**. Regla del humano (2026-10-06): «el contrato solo se toca para actualizar consumos». Por eso aquí no se ha
editado nada de sigrid-api: lo de la parte A lo incorpora la sesión de sigrid-api si lo acepta; lo de la parte B lo
actualiza F-053 en el contrato cuando se implemente (son columnas de consumo).

## Conclusión

**F-053 v7 no necesita nada nuevo de F-009 v8.** Todo lo que manda y todos los códigos que mapea ya existen en la
v8: `usu`, sin `almacen` ni `naturaleza`, producto de la lista blanca `["MA9999","QA9999","XA9999"]`, `referencia_linea`
≤ 24, `paride` opcional (que F-053 aún no manda), y los códigos `precio_negativo`, `obra_de_empresa_no_permitida`,
`paride_no_valido`, `analitica_no_resuelta`, `naturaleza_no_valida` y los avisos `iva_de_otro_proveedor` y
`sin_partida_en_linea_con_partida`. Las decisiones del humano sobre P1–P7 se resuelven todas dentro de albaranes.

## A. Estado de huecos que el contrato da aún por abiertos (de sigrid-api; propuesta)

| H | Texto actual del contrato | Propuesta |
|---|---|---|
| H8 | Signos en F-053: «pregunta P2» | **Decidido** (humano, 2026-10-06): signos opuestos (cantidad > 0 e importe < 0, o al revés) ⇒ `revisar` local con `signo_incoherente`, sin llamar a sigrid-api (F-053 R39). El descuento se mete a mano en Sigrid. F-053 nunca manda cantidad e importe de signo opuesto; `precio_negativo` sigue de segunda barrera |
| H17 | F-053 «pregunta P4» | **Decidido**: F-053 no manda `paride` mientras F-049 no conserve el `ide` de la partida; `partida_ambigua` ⇒ `no_admitido`. Cuando F-049 lo conserve, F-053 lo manda (evolución, sin cambio en F-009) |
| H29 | «Confirmar» | **Cerrado** (humano): las vinculadas con cantidad y sin importe no se mandan (F-053 R13) |
| H30 | «Confirmar» | **Cerrado** (humano): el ALM impreso sigue sin vincular; vincularlo sería cambio de sv6 en F-060/F-007, no de F-009 |
| H28 | Pregunta P7 de F-053 | **Cerrada** desde F-053: `XA9999` medido en T0b-ter (`tipmov` 1; cuenta = `cuacomcod` de la naturaleza) |
| §0 | «Humano … abiertos como preguntas de F-053 v6: H8 (P2), H17 (P4), H29 (P5), H30 (P6), H28 (P7)» | Todas cerradas el 2026-10-06 (F-053 v7, `spec_ready`) |
| Fuentes | F-053 «v6 … `pending` con 7 preguntas» | F-053 **v7** (2026-10-06, `spec_ready`, alineada con F-009 v8 `8a6ecab`) |

## B. Lo que F-053 actualiza en el contrato como consumo (redactado para el líder, 2026-10-08)

Implementación de F-053 terminada (fases 1 y 2, rama `feature/F-053-alta-sigrid`). Regla del humano: desde
albaranes NO se edita el contrato; estos cambios de las columnas de consumo los aplica la sesión de sigrid-api,
coordinada por el líder. Contra `contrato_albaranes.md` en `13fd99d` (v8.2). Ninguno cambia la forma de F-009.

1. §2.4 punto 3: «La familia `medios_auxiliares` … (ficha propia, F-053 P1)» ⇒ «ficha **F-061**».
2. §2.4 punto 4: «Signos incoherentes: H8» ⇒ «signos opuestos ⇒ `revisar` local `signo_incoherente` (F-053 R39)».
3. §2.4 punto 9: la validación local de formato de fecha de sv9 se llama `fecha_ilegible` (R10; antes
   `fecha_no_valida`, nombre que coincidía con el código retirado de sigrid-api en la v5.1).
4. §7, fila de R14: quitar «H9 si anular no borra» (H9 cerrado: anular borra; misma referencia tras `anulado`).
5. §3.3, columna «Estado en F-053»: sin cambios de estado; quitar las referencias a «pregunta P2/P4 de F-053 v6».
6. §2.1, fila `paride`: «F-053 v6 aún no lo manda (pregunta P4: provisionalmente `partida_ambigua` ⇒
   `no_admitido`)» ⇒ «F-053 v7 no lo manda (P4 decidida el 2026-10-06: `partida_ambigua` ⇒ `no_admitido`); lo
   mandará cuando F-049 conserve el `ide` de la partida (evolución, sin cambio en F-009)».
7. Tabla «Fuentes» (fila de albaranes F-053): «v7 (2026-10-06, `spec_ready`…)» ⇒ «v7 **implementada**
   (2026-10-08; fases 1 y 2 en `feature/F-053-alta-sigrid`, pendiente de fusionar y de las MANUAL T26–T29);
   arranca en simulación (`ALTA_SIGRID_DESDE_UTC` vacía y `ALTA_SIGRID_COMMIT=false` al crear sv9)».
8. §2.4 (o junto a la idempotencia de §7): las defensas de albaranes contra el doble alta son, además de la
   idempotencia de F-009, `reclamar` de sv9 con el merge bloqueado y el alta leída en OTRA sentencia (T24b:
   un segundo `reclamar` que esperó el cerrojo ve el `en_curso` y no vuelve a llamar), sv9 con una sola
   réplica, la grabación sin reintento automático y `incierto` sin retomar antes de la Espera.
9. §2.4 punto 1 (o la fila de `ALTA_SIGRID_DESDE_UTC`): sv4 publica el alta solo en el PASO a aprobado y no
   deja aprobar lo no valorado (F-053 R1, R2, R37); el revisor la repite desde la ficha con «Solicitar alta
   en Sigrid» (R30) y, tras anular en Sigrid, «Ya lo he anulado en Sigrid» (R28: sv9 comprueba con `sql/read`
   que el `con.ide` ya no existe).

Nada de esto pide cambios a F-009: sigue valiendo la conclusión de arriba.
