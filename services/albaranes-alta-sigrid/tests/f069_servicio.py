# tests/f069_servicio.py
"""Ayudas de los tests de F-069 sobre ``AltaSigridService`` (sin red ni BBDD).

Construyen el servicio con los dobles de F-053 y una Lista de equivalencias, y
procesan un documento aprobado por ``approved_by``. Logins, correos e ``ide``
ficticios.
"""
from __future__ import annotations

from application.alta_sigrid_service import AltaSigridService
from domain.models.alta_models import AccionAlta, ModoAlta, PeticionAlbaran
from domain.services.usuario_sigrid import leer_equivalencias
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, HOY, datos, sin_vincular, vinculada
from tests.f053_fakes import AHORA, DESDE, ESPERA, PdfFalso, RepoFalso, SigridFalso, previa_ok

RESPALDO = "pgris"
D = datos(vinculada(1), sin_vincular(2))


def peticion(usu: str = "x") -> PeticionAlbaran:
    resultado = validar_y_construir(D, CONFIG, HOY, usu)
    assert isinstance(resultado, PeticionAlbaran)
    return resultado


def sigrid(**campos) -> SigridFalso:
    """Sigrid con la previa en verde (devuelve lo pedido)."""
    return SigridFalso(previa=previa_ok(peticion()), **campos)


def servicio(sigrid_: SigridFalso, repo: RepoFalso, *, lista: str = "",
             respaldo: str = RESPALDO, modo: ModoAlta = ModoAlta.SIMULACION,
             ) -> AltaSigridService:
    return AltaSigridService(
        repo=repo, sigrid=sigrid_, pdf=PdfFalso(), config=CONFIG, usuario_respaldo=respaldo,
        modo=modo, desde=DESDE, espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset(), reloj=lambda: AHORA,
        equivalencias=leer_equivalencias(lista),
    )


def procesar(sigrid_: SigridFalso, *, approved_by: str | None = "login1@ruesma.es",
             lista: str = "", respaldo: str = RESPALDO, modo: ModoAlta = ModoAlta.SIMULACION,
             alta=None, d=D):
    repo = RepoFalso()
    doc = repo.anadir(d, alta=alta, approved_by=approved_by)
    resultado = servicio(sigrid_, repo, lista=lista, respaldo=respaldo, modo=modo).procesar(
        doc, AccionAlta.ALTA,
    )
    return repo, doc, resultado


def pedidos(sigrid_: SigridFalso, campo: str) -> list:
    """El ``campo`` de cada petición mandada a ``sigrid/albaran``."""
    return [getattr(c[1], campo) for c in sigrid_.llamadas if c[0] == "alta_albaran"]


def lecturas(sigrid_: SigridFalso, operacion: str) -> list:
    """Los argumentos de cada llamada a ``operacion`` del puerto."""
    return [c[1] for c in sigrid_.llamadas if c[0] == operacion]
