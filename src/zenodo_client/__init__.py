"""A wrapper for the Zenodo API."""

from .api import (
    Zenodo,
    create_zenodo,
    download_zenodo,
    download_zenodo_latest,
    ensure_files,
    ensure_zenodo,
    list_files,
    publish_zenodo,
    update_zenodo,
)
from .struct import (
    AccessRight,
    Community,
    Creator,
    ImageType,
    Metadata,
    PublicationType,
    UploadType,
)

__all__ = [
    "AccessRight",
    "Community",
    "Creator",
    "ImageType",
    "Metadata",
    "PublicationType",
    "UploadType",
    "Zenodo",
    "create_zenodo",
    "download_zenodo",
    "download_zenodo_latest",
    "ensure_files",
    "ensure_zenodo",
    "list_files",
    "publish_zenodo",
    "update_zenodo",
]
