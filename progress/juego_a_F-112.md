<!-- progress/juego_a_F-112.md -->
# F-112 · Juego A: fecha verdadera de los 19 documentos (leída en el papel por el líder, 2026-10-30)

Originales descargados por Graph en solo lectura (GET), con autorización del humano del 2026-10-30, al scratchpad de la
sesión (no al repositorio). Documentos activos con la fecha a más de 365 días de la recepción del correo. «IA» = la fecha
final guardada hoy; «papel» = la impresa o manuscrita en el documento.

| Doc | Proveedor | Nº | Correo | IA | Papel | Clase |
|---|---|---|---|---|---|---|
| 82be7db8 | HERMANOS SAN JUAN | 1909 B | 2026-10-14 | 2020-10-01 | 2026-10-01 («1-10-26») | año |
| 7198f5d3 | HERMANOS SAN JUAN | 1350 B | 2026-10-14 | 2023-10-21 | 2026-10-01 («1-10-26») | año y día |
| a848c4cf | HERMANOS SAN JUAN | 2910 B | 2026-10-14 | 2020-10-05 | 2026-10-05 («5/10/2026») | año |
| 25c5d647 | MACOTRAN | 455884 | 2026-09-30 | 2016-09-16 | 2026-09-16 («16-9-2026») | año |
| 55ed773f | MACOTRAN | 460978 | 2026-10-13 | 2020-10-06 | 2026-10-06 («6-10-26») | año |
| 00b6275b | MACOTRAN | 461465 | 2026-10-13 | 2020-10-13 | 2026-10-13 («13 10 26») | año |
| 3425d6b0 | MACOTRAN | 462044 | 2026-10-13 | 2023-10-17 | 2026-10-07 («7-10-26») | año y día |
| 3772aa5f | FEYMACO | 2169589 | 2026-10-07 | 2023-09-28 | 2026-09-28 | año |
| 1c2d7274 | FEYMACO | 170.675 (papel 2.170.675) | 2026-10-07 | 2006-11-02 | 2026-10-02 | año y mes |
| 2792cf3b | FEYMACO | 2.171.770 | 2026-10-15 | 2020-10-05 | 2026-10-05 | año |
| 53337da7 | FEYMACO | 2.171.153 | 2026-10-15 | 2024-10-02 | 2026-10-02 | año |
| 54b82479 | FEYMACO | 2170.688 | 2026-10-15 | 2024-10-02 | 2026-10-02 | año |
| 43fb8c2d | FEYMACO | 2168495 | 2026-09-30 | 2025-09-23 | 2026-09-23 (impresión muy débil; el nº es anterior al 2169589 del 28-09-2026) | año (casi seguro) |
| 5986ff81 | GRÚAS TRAURA | 21734 | 2026-10-13 | 2024-10-07 | 2026-10-07 («7 de 10 de 2026») | año |
| d550baa3 | ÁRIDOS ANFERSA | 1788248802 | 2026-10-21 | 2025-10-02 | se lee 02/10/2025, impresión débil | DUDOSO (lo confirma el humano) |
| 5f7de061 | CARGA Y TRANSPORTE DE CUBAS | 2990…024385 | 2026-10-22 | 2025-01-27 | 2025-01-27 («27-1-25») | antigua de verdad (fichero de prueba RES-011) |
| b147a548 | CARGA Y TRANSPORTE DE CUBAS | 2990…030366 | 2026-10-22 | 2025-08-07 | 2025-08-07 («7-8-25») | antigua de verdad (RES-019) |
| 96c37c8d | SALMEDINA | SS-0000168 | 2026-10-22 | 2024-07-03 | 2024-07-03 («3.7.24», sello 03 JUL 2024) | antigua de verdad (RES-001) |
| 862ea034 | HORMIGONES Y CEMENTOS ANDALUCES | 37515 | 2026-10-22 | 2025-09-11 | 2025-09-11 | antigua de verdad (HOR-015) |

## Conclusiones para la spec

- **14 errores de año** (13 seguros y 2168495 casi seguro), 1 dudoso (Anfersa) y **4 fechas antiguas de verdad**,
  todas de ficheros de prueba subidos el 22-10 (RES-001/011/019, HOR-015). Cierra D8: los 3 de residuos «sin patrón»
  son antiguos de verdad; la IA acertó. Son los casos de control de D4: la regla del año no debe moverlos.
- **Pista nueva para el prompt:** en 5 de los 14 la IA puso **2020**, y los partes de residuos de HERMANOS SAN JUAN y
  MACOTRAN llevan impreso «R.D. 553/2020» en la cabecera. La IA toma el año del decreto. Conviene decir en el prompt
  que el año de la fecha nunca sale de referencias normativas (R.D., Orden, Ley).
- En 3 casos falla también el día o el mes (1350 B, 462044, 170.675), siempre con año de dos cifras manuscrito. En
  170.675 también falta el «2.» del número.
