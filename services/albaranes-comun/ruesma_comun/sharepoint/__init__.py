# ruesma_comun/sharepoint/__init__.py
"""Acceso común a SharePoint vía Microsoft Graph."""
from ruesma_comun.sharepoint.graph_client import (
    GraphSharePointClient,
    ResolvedFolder,
    SharePointMode,
)

__all__ = ["GraphSharePointClient", "ResolvedFolder", "SharePointMode"]
