# domain/services/usuario_sigrid.py
"""Login candidato de Sigrid a partir de quien aprobó (F-053 v8, R47).

Puro: ni red ni BBDD. ``dbo.usu`` no tiene el correo (``ele`` vacío en todos,
T0c), así que se casa la parte antes de la @ del UPN de Easy Auth con
``dbo.usu.cod``, igual que valida sigrid-api. Quien lo comprueba en Sigrid y
decide el Respaldo es el servicio (``AltaSigridService._resolver_usuario``).
"""
from __future__ import annotations

#: Longitud máxima de ``dbo.usu.cod`` que admite el contrato (``usu``, H6).
MAX_LOGIN = 24

#: Dominio de los correos de Ruesma (sin distinguir mayúsculas).
DOMINIO_RUESMA = "ruesma.es"


def candidato_usuario(approved_by: str | None) -> str | None:
    """La parte antes de la @ si ``approved_by``, sin espacios alrededor, es
    un correo ``@ruesma.es`` con una sola @ y esa parte no está vacía ni pasa
    de :data:`MAX_LOGIN`; si no, ``None`` (texto libre, ``DEFAULT_REVIEWER``,
    invitado ``#EXT#``, otro dominio o nada). La parte local va tal cual se
    escribió: el ``cod`` que se manda es el que devuelve Sigrid."""
    texto = (approved_by or "").strip()
    if texto.count("@") != 1:
        return None
    local, dominio = texto.split("@")
    if dominio.lower() != DOMINIO_RUESMA:
        return None
    if not local or len(local) > MAX_LOGIN:
        return None
    return local
