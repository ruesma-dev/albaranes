# tests/f062_dobles.py
"""Dobles compartidos por los tests de F-062 (resolver de cabecera).

``RepoRed`` es el repositorio del resolver con las escrituras de la red de
proveedor registradas; con ``merge=True`` además APLICA lo que escribe
sobre un merge en memoria (CIF, nombre, origen, motivos y notas, con las
mismas funciones puras que el repositorio real), para poder encadenar
pasadas. Sin red ni BBDD.
"""
from __future__ import annotations

import json

from application.services.header_resolver_service import HeaderResolverService
from domain.models.header_resolution_models import (
    NOTA_PROVEEDOR_CORREGIDO_PREFIJO,
    MergeHeaderForResolution,
)
from infrastructure.database.sqlalchemy_albaran_repository import (
    anadir_motivo_revision,
    depurar_motivos_proveedor,
    sustituir_nota_por_prefijo,
)

DOC = "doc-f062"


class ObrasVacias:
    def search_obras(self):
        return []


class RepoRed:
    def __init__(
        self,
        *,
        cif: str | None,
        nombre: str | None,
        obra: str | None,
        origen: str | None = "ia",
        falla_aplicar: bool = False,
    ) -> None:
        self.cif = cif
        self.nombre = nombre
        self.obra = obra
        self.origen = origen
        self.review_required = False
        self.motivos: str | None = None
        self.notas: str | None = None
        self.falla_aplicar = falla_aplicar
        self.aplicadas: list[dict] = []
        self.retiradas: list[str | None] = []
        self.marcas: list[tuple[str, str, str]] = []
        self.resoluciones: list[tuple] = []
        self.canonizados: list[str] = []

    # --- lectura ---------------------------------------------------- #
    def get_merge_header_for_resolution(self, *, document_id: str):
        return MergeHeaderForResolution(
            obra_codigo=self.obra, obra_nombre=None, obra_direccion=None,
            proveedor_cif=self.cif, proveedor_nombre=self.nombre,
            proveedor_cif_origen=self.origen,
        )

    def get_merge_lines_for_scoring(self, *, document_id: str) -> list[dict]:
        return []

    # --- escrituras previas a F-062 --------------------------------- #
    def update_merge_resolved_header(
        self, *, document_id, obra_codigo_det, proveedor_cif_det,
        proveedor_origen="deterministic",
    ) -> None:
        self.resoluciones.append((obra_codigo_det, proveedor_cif_det, proveedor_origen))
        if proveedor_cif_det and self.origen != "manual":
            self.cif, self.origen = proveedor_cif_det, proveedor_origen
        elif self.cif and not self.origen:
            self.origen = "ia"

    def append_review_note(self, *, document_id: str, nota: str) -> None:
        if nota not in (self.notas or ""):
            self.notas = f"{self.notas}\n{nota}" if self.notas else nota

    def remove_review_note_prefix(self, *, document_id: str, prefijo: str) -> None:
        self.notas = sustituir_nota_por_prefijo(self.notas, prefijo=prefijo, nota=None)

    def set_merge_proveedor_nombre_canonico(self, *, document_id: str, nombre: str) -> None:
        self.canonizados.append(nombre)
        self.nombre = nombre

    def marcar_revision_cabecera(
        self, *, document_id: str, motivo: str, nota: str, nota_prefijo: str,
    ) -> None:
        self.marcas.append((motivo, nota, nota_prefijo))
        self.review_required = True
        self.motivos = anadir_motivo_revision(self.motivos, motivo)
        self.notas = sustituir_nota_por_prefijo(self.notas, prefijo=nota_prefijo, nota=nota)

    # --- escrituras de F-062 ---------------------------------------- #
    def aplicar_correccion_proveedor(
        self, *, document_id: str, cif: str, nombre: str, motivo: str, nota: str,
    ) -> None:
        if self.falla_aplicar:
            raise RuntimeError("BBDD caida")
        self.aplicadas.append({"cif": cif, "nombre": nombre, "motivo": motivo, "nota": nota})
        self.cif, self.nombre, self.origen = cif, nombre, "deterministic"
        self.review_required = True
        depurados, _ = depurar_motivos_proveedor(self.motivos, cif)
        self.motivos = anadir_motivo_revision(depurados, motivo)
        self.notas = sustituir_nota_por_prefijo(
            self.notas, prefijo=NOTA_PROVEEDOR_CORREGIDO_PREFIJO, nota=nota,
        )

    def retirar_motivos_proveedor(self, *, document_id: str, cif_actual: str | None) -> None:
        self.retiradas.append(cif_actual)
        nuevos, retiro = depurar_motivos_proveedor(self.motivos, cif_actual)
        self.motivos = nuevos
        if retiro:
            self.notas = sustituir_nota_por_prefijo(
                self.notas, prefijo=NOTA_PROVEEDOR_CORREGIDO_PREFIJO, nota=None,
            )

    # --- ayudas para los asserts ------------------------------------ #
    def lista_motivos(self) -> list[str]:
        return json.loads(self.motivos) if self.motivos else []

    def lineas_notas(self) -> list[str]:
        return (self.notas or "").splitlines()


def resolver(cliente, repo, **kwargs) -> HeaderResolverService:
    return HeaderResolverService(
        obra_client=ObrasVacias(), proveedor_client=cliente, repository=repo, **kwargs,
    )


def pasada(cliente, repo, **kwargs) -> None:
    resolver(cliente, repo, **kwargs).resolve_merge_document(merge_document_id=DOC)
