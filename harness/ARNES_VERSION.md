<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Lo escribe `instalar_arnes.ps1`. **No lo edites a mano.**

| Dato | Valor |
|---|---|
| Version del arnes | `1.6.0` |
| Fecha de la version | 2026-08-19 |
| Instalado/actualizado el | 2026-08-19 |
| Modo | propagacion directa desde arnes-base |
| Origen | `arnes-base` |

> **AVISO de la 1.6.0 (F-034): cambia QUE se mide, no solo como se informa.**
> El mutador aprende a mutar `is` / `is not`, la guarda de ausencia de Python.
> Los informes de mutacion generados con 1.5.2 o anterior **no son comparables**
> con los posteriores: se midieron sin tocar ese operador. En este repositorio
> se remidieron F-019 (de 31 a 49 mutantes) y F-027 (de 0 a 1), y el resto de
> informes de `progress/mutacion_*.md` llevan anotado con que vara se midieron.

Para actualizar a una version posterior, desde el repositorio `arnes-base`:

```powershell
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\albaranes" -Modo actualizar
```

Antes de aceptar cambios, lee `GUIA_INSTALACION.md` en `arnes-base`: los
ficheros con marcas de adaptacion llevan contenido propio de este proyecto y
casi siempre hay que conservarlos, no sobrescribirlos.