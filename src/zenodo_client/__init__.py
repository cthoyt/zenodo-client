# -*- coding: utf-8 -*-

"""A wrapper for the Zenodo API."""

from .api import (
    Zenodo,
    create_zenodo,
    download_zenodo,
    download_zenodo_latest,
    ensure_zenodo,
    publish_zenodo,
    update_zenodo,
)
from .struct import Community, Creator, Metadata

__all__ = [
    "Zenodo",
    "create_zenodo",
    "download_zenodo",
    "download_zenodo_latest",
    "ensure_zenodo",
    "publish_zenodo",
    "update_zenodo",
    "Creator",
    "Metadata",
]
